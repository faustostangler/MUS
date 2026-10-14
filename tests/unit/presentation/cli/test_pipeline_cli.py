"""Unit tests for pipeline CLI command verifying SPEC-002 S3."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
from typer.testing import CliRunner

from mus.presentation.cli.pipeline import app
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.stem_separation.domain.models import SeparatedStems
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)

runner = CliRunner()


def test_pipeline_run_outputs_synt_mp3_and_midi_in_genre_folder(tmp_path: Path) -> None:
    # Set up mock stem directory structure
    genre_dir = tmp_path / "stems" / "Rock"
    genre_dir.mkdir(parents=True, exist_ok=True)
    vocal_stem = genre_dir / "Band - Song - vocals.mp3"
    vocal_stem.touch()

    stems = SeparatedStems(vocals_path=vocal_stem, other_stems={})

    # Dummy parametric voice
    n_frames = 10
    n_bins = 1025
    f0 = PitchContour(np.full(n_frames, 220.0, dtype=np.float64), FramePeriod(5.0))
    sp = SpectralEnvelope(np.ones((n_frames, n_bins), dtype=np.float64))
    ap = Aperiodicity(np.zeros((n_frames, n_bins), dtype=np.float64))
    sr = SampleRate(44100)
    voice = ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=sr)

    patch_ingest = patch(
        "mus.stem_separation.application.use_cases.ingest_and_separate."
        "IngestAndSeparateTrack.execute",
        return_value=stems,
    )
    patch_decompose = patch(
        "mus.voice_modeling.application.use_cases.decompose_voice.DecomposeVoice.execute",
        return_value=voice,
    )
    patch_read = patch("mus.voice_modeling.infrastructure.soundfile_audio_io.SoundfileAudioIO.read")
    patch_resynth = patch(
        "mus.voice_modeling.application.use_cases.resynthesize_voice.ResynthesizeVoice.execute"
    )

    with (
        patch_ingest,
        patch_decompose,
        patch_read,
        patch_resynth as mock_resynth,
    ):
        result = runner.invoke(app, ["dummy_source", "--out", str(tmp_path)])
        assert result.exit_code == 0

        # Assert no _midi_preview.wav was generated
        preview_files = list(tmp_path.rglob("*_midi_preview*"))
        assert len(preview_files) == 0

        # Assert MIDI file was saved inside the genre folder
        expected_midi = genre_dir / "Band - Song - vocals.mid"
        assert expected_midi.exists()

        # Assert vocal resynthesis was called with .mp3 target inside genre folder
        mock_resynth.assert_called_once()
        cmd_arg = mock_resynth.call_args[0][0]
        assert cmd_arg.output_path == genre_dir / "Band - Song - vocals - synt.mp3"


def test_pipeline_run_skips_already_processed_track(tmp_path: Path) -> None:
    # Set up mock stem directory structure with all completed artifacts
    genre_dir = tmp_path / "stems" / "Rock"
    genre_dir.mkdir(parents=True, exist_ok=True)
    vocal_stem = genre_dir / "Band - Song - vocals.mp3"
    vocal_stem.touch()
    midi_file = genre_dir / "Band - Song - vocals.mid"
    midi_file.touch()
    synt_file = genre_dir / "Band - Song - vocals - synt.mp3"
    synt_file.touch()

    with patch(
        "mus.stem_separation.application.use_cases.ingest_and_separate."
        "IngestAndSeparateTrack.execute"
    ) as mock_ingest:
        result = runner.invoke(app, ["Band - Song", "--out", str(tmp_path)])
        assert result.exit_code == 0
        assert "[Skipped]" in result.output
        mock_ingest.assert_not_called()
