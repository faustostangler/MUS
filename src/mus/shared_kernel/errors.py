"""Domain and architecture errors for MUS."""


class MusDomainError(Exception):
    """Base domain exception for MUS."""


class UnsupportedSampleRateError(MusDomainError):
    """Raised when an audio sample rate outside {44100, 48000} is provided."""


class SilentTakeError(MusDomainError):
    """Raised when an audio signal is empty or contains only zeros."""


class MisalignedFramesError(MusDomainError):
    """Raised when F0, SP and AP time-series have different lengths."""
