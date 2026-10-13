"""Soundfile and Librosa audio I/O adapter implementing AudioReaderPort and AudioWriterPort."""

import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import SampleRate


class SoundfileAudioIO:
    """Adapter for reading and atomically writing audio files."""

    def read(self, path: Path, target_rate: SampleRate) -> AudioSignal:
        """Reads audio file, converts to mono float64, and resamples to target_rate if needed."""
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        try:
            # Read via soundfile
            data, sr_orig = sf.read(str(path), always_2d=True, dtype="float64")
        except Exception:
            # Fallback for MP3 or format edge cases via librosa
            data_mono, sr_orig = librosa.load(str(path), sr=None, mono=True)
            data = data_mono[:, np.newaxis]

        # Convert to mono if multi-channel
        samples = np.mean(data, axis=1) if data.shape[1] > 1 else data[:, 0]

        # Resample if original rate differs from target
        if sr_orig != target_rate.value:
            samples = librosa.resample(
                samples,
                orig_sr=sr_orig,
                target_sr=target_rate.value,
                res_type="soxr_hq",
            )

        c_samples = np.ascontiguousarray(samples, dtype=np.float64)
        return AudioSignal(samples=c_samples, sample_rate=target_rate)

    def write(self, signal: AudioSignal, path: Path) -> None:
        """Atomically writes an AudioSignal as 24-bit PCM WAV."""
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")

        try:
            sf.write(
                str(tmp_path),
                signal.samples,
                samplerate=signal.sample_rate.value,
                format="WAV",
                subtype="PCM_24",
            )
            os.replace(str(tmp_path), str(path))
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise e
