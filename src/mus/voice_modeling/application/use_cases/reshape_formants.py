"""ReshapeFormants use case applying vocal tract scaling and vowel substitution."""

from dataclasses import dataclass

from mus.shared_kernel.errors import WindowOutOfRangeError
from mus.voice_modeling.domain.parametric_voice import ParametricVoice
from mus.voice_modeling.domain.phonetics import (
    FormantTarget,
    VocalTractScale,
    substitute_vowel,
    warp_spectral_envelope,
)


@dataclass(frozen=True, slots=True)
class ReshapeFormantsCommand:
    """Input parameters for formant manipulation."""

    voice: ParametricVoice
    tract_scale: VocalTractScale | None = None
    target_vowel: FormantTarget | None = None
    vowel_window: tuple[float, float] | None = None  # (start_seconds, end_seconds)
    crossfade_ms: float = 20.0


class ReshapeFormants:
    """Coordinates vocal tract scaling and vowel substitution on a ParametricVoice."""

    def execute(self, command: ReshapeFormantsCommand) -> ParametricVoice:
        """Transforms voice formants according to tract scale or target vowel window."""
        voice = command.voice
        sp = voice.sp
        fp = voice.f0.frame_period
        total_duration = len(voice.f0) * (fp.ms / 1000.0)

        # Apply tract scale warping if requested
        if command.tract_scale is not None:
            sp = warp_spectral_envelope(
                spectral_envelope=sp,
                tract_scale=command.tract_scale,
                sample_rate=voice.sample_rate,
            )

        # Apply vowel substitution if requested
        if command.target_vowel is not None and command.vowel_window is not None:
            start_s, end_s = command.vowel_window
            if start_s < 0.0 or end_s > total_duration + 1e-4 or start_s >= end_s:
                raise WindowOutOfRangeError(
                    f"Vowel window [{start_s:.2f}s, {end_s:.2f}s] exceeds "
                    f"take duration ({total_duration:.2f}s)."
                )

            sp = substitute_vowel(
                spectral_envelope=sp,
                target_vowel=command.target_vowel,
                start_seconds=start_s,
                end_seconds=end_s,
                frame_period=fp,
                sample_rate=voice.sample_rate,
                crossfade_ms=command.crossfade_ms,
            )

        return ParametricVoice(
            f0=voice.f0,
            sp=sp,
            ap=voice.ap,
            sample_rate=voice.sample_rate,
        )
