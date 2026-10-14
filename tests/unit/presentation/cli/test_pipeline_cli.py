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


def test_pipeline_run_transcribes_and_synthesizes_all_stems(tmp_path: Path) -> None:
    genre_dir = tmp_path / "stems" / "Jazz"
    genre_dir.mkdir(parents=True, exist_ok=True)
    vocal_stem = genre_dir / "Artist - Tune - vocals.mp3"
    vocal_stem.touch()
    bass_stem = genre_dir / "Artist - Tune - bass.mp3"
    bass_stem.touch()
    drums_stem = genre_dir / "Artist - Tune - drums.mp3"
    drums_stem.touch()

    stems = SeparatedStems(
        vocals_path=vocal_stem,
        other_stems={"bass": bass_stem, "drums": drums_stem},
    )

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
    patch_transcribe_stem = patch(
        "mus.music_transcription.application.use_cases.transcribe_all_stems.TranscribeStem.execute"
    )
    patch_synth_stem = patch(
        "mus.music_transcription.application.use_cases.transcribe_all_stems.SynthesizeStemMidi.execute"
    )

    with (
        patch_ingest,
        patch_decompose,
        patch_read,
        patch_resynth,
        patch_transcribe_stem as mock_transcribe_stem,
        patch_synth_stem as mock_synth_stem,
    ):
        result = runner.invoke(app, ["dummy_jazz", "--out", str(tmp_path)])
        assert result.exit_code == 0

        # Assert TranscribeStem was called for each non-vocal stem
        transcribed_stems = [call[0][0].stem_name for call in mock_transcribe_stem.call_args_list]
        assert "bass" in transcribed_stems
        assert "drums" in transcribed_stems

        # Assert SynthesizeStemMidi was called for each non-vocal stem
        synthesized_outputs = [call[0][0].output_path for call in mock_synth_stem.call_args_list]
        assert genre_dir / "Artist - Tune - bass - synt.mp3" in synthesized_outputs
        assert genre_dir / "Artist - Tune - drums - synt.mp3" in synthesized_outputs


def test_pipeline_does_not_skip_if_other_stems_incomplete(tmp_path: Path) -> None:
    genre_dir = tmp_path / "stems" / "Rock"
    genre_dir.mkdir(parents=True, exist_ok=True)
    vocal_stem = genre_dir / "Band - Song - vocals.mp3"
    vocal_stem.touch()
    (genre_dir / "Band - Song - vocals.mid").touch()
    (genre_dir / "Band - Song - vocals - synt.mp3").touch()

    # Bass stem exists as mp3, but neither bass.mid nor bass - synt.mp3 exist yet
    bass_stem = genre_dir / "Band - Song - bass.mp3"
    bass_stem.touch()

    with patch(
        "mus.stem_separation.application.use_cases.ingest_and_separate."
        "IngestAndSeparateTrack.execute"
    ) as mock_ingest:
        mock_ingest.side_effect = RuntimeError("Invoked because not skipped")
        result = runner.invoke(app, ["Band - Song", "--out", str(tmp_path)])
        # Must not skip; it attempts to execute ingest/pipeline
        assert "[Skipped]" not in result.output
        mock_ingest.assert_called_once()
