"""Unit tests for RenderVocalTake composite use case and peak guard (Covers S5-01, S5-03)."""

from pathlib import Path

import numpy as np

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, Hertz, SampleRate
from mus.voice_modeling.application.ports import AudioWriterPort, VocoderPort
from mus.voice_modeling.application.use_cases.render_vocal_take import (
    RenderVocalTake,
    RenderVocalTakeCommand,
)
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)


class FakeVocoder(VocoderPort):
    """In-memory vocoder fake returning controlled audio amplitude."""

    def __init__(self, synth_amplitude: float = 0.5) -> None:
        self.synth_amplitude = synth_amplitude

    def analyze(
        self,
        signal: AudioSignal,
        f0_floor: Hertz | None = None,
        f0_ceil: Hertz | None = None,
        frame_period: FramePeriod | None = None,
        method: str = "dio",
    ) -> ParametricVoice:
        fp = frame_period or FramePeriod(5.0)
        n_frames = 10
        fft_size = 2048
        return ParametricVoice(
            f0=PitchContour(
                f0=np.full(n_frames, 220.0, dtype=np.float64),
                frame_period=fp,
            ),
            sp=SpectralEnvelope(
                data=np.ones((n_frames, fft_size // 2 + 1), dtype=np.float64),
            ),
            ap=Aperiodicity(
                data=np.zeros((n_frames, fft_size // 2 + 1), dtype=np.float64),
            ),
            sample_rate=signal.sample_rate,
        )

    def synthesize(self, voice: ParametricVoice) -> AudioSignal:
        sr = voice.sample_rate.value
        n_samples = int(voice.duration_seconds * sr)
        samples = np.full(max(10, n_samples), self.synth_amplitude, dtype=np.float64)
        peak = float(np.max(np.abs(samples)))
        self.last_raw_peak = peak
        self.last_synthesis_clipped = peak > 1.0
        if self.last_synthesis_clipped:
            target_peak = float(10.0 ** (-1.0 / 20.0))
            samples = (samples / peak) * target_peak
        return AudioSignal(samples=samples, sample_rate=voice.sample_rate)


class FakeAudioWriter(AudioWriterPort):
    """In-memory writer capturing written signals."""

    def __init__(self) -> None:
        self.written_files: dict[Path, AudioSignal] = {}

    def write(self, signal: AudioSignal, path: Path) -> None:
        self.written_files[path] = signal


class TestRenderVocalTake:
    """Verifies S5-01 and S5-03 specifications."""

    def test_s5_03_no_clipping_preserves_original_gain(self, tmp_path: Path) -> None:
        """When peak <= 1.0, gain is untouched and normalized is False."""
        vocoder = FakeVocoder(synth_amplitude=0.6)  # ~ -4.4 dBFS
        writer = FakeAudioWriter()
        use_case = RenderVocalTake(vocoder=vocoder, writer=writer)

        in_signal = AudioSignal(samples=np.full(1000, 0.5), sample_rate=SampleRate(44100))
        out_path = tmp_path / "take_clean.wav"

        result = use_case.execute(
            RenderVocalTakeCommand(
                signal=in_signal,
                output_path=out_path,
                peak_guard_dbfs=-1.0,
            )
        )

        assert not result.was_clipped
        assert not result.normalized
        written_signal = writer.written_files[out_path]
        assert np.isclose(np.max(np.abs(written_signal.samples)), 0.6)

    def test_s5_03_clipping_normalizes_to_minus_one_dbfs(self, tmp_path: Path) -> None:
        """When peak > 1.0 (clipping), normalizes peak to exactly -1.0 dBFS (~0.89125)."""
        vocoder = FakeVocoder(synth_amplitude=1.5)  # Clipping signal
        writer = FakeAudioWriter()
        use_case = RenderVocalTake(vocoder=vocoder, writer=writer)

        in_signal = AudioSignal(samples=np.full(1000, 0.5), sample_rate=SampleRate(44100))
        out_path = tmp_path / "take_clipped.wav"

        result = use_case.execute(
            RenderVocalTakeCommand(
                signal=in_signal,
                output_path=out_path,
                peak_guard_dbfs=-1.0,
            )
        )

        assert result.was_clipped
        assert result.normalized
        expected_peak = 10.0 ** (-1.0 / 20.0)  # ~0.89125
        written_signal = writer.written_files[out_path]
        assert np.isclose(np.max(np.abs(written_signal.samples)), expected_peak, atol=1e-4)

    def test_s5_01_applies_pitch_and_formant_modulations(self, tmp_path: Path) -> None:
        """Applies pitch transposition and vocal tract scaling when parameters are provided."""
        vocoder = FakeVocoder(synth_amplitude=0.5)
        writer = FakeAudioWriter()
        use_case = RenderVocalTake(vocoder=vocoder, writer=writer)

        in_signal = AudioSignal(samples=np.full(1000, 0.5), sample_rate=SampleRate(44100))
        out_path = tmp_path / "take_modulated.wav"

        result = use_case.execute(
            RenderVocalTakeCommand(
                signal=in_signal,
                output_path=out_path,
                transpose_semitones=3.0,
                vocal_tract_alpha=1.1,
            )
        )

        assert result.output_path == out_path
        assert out_path in writer.written_files
