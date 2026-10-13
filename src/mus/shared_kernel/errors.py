"""Domain and architecture errors for MUS."""


class MusDomainError(Exception):
    """Base domain exception for MUS."""


class UnsupportedSampleRateError(MusDomainError):
    """Raised when an audio sample rate outside {44100, 48000} is provided."""


class SilentTakeError(MusDomainError):
    """Raised when an audio signal is empty or contains only zeros."""


class MisalignedFramesError(MusDomainError):
    """Raised when F0, SP and AP time-series have different lengths."""


class PolyphonyNotSupportedError(MusDomainError):
    """Raised when overlapping notes are introduced into a monophonic NoteSequence."""


class CorruptAudioError(MusDomainError):
    """Raised when an audio signal contains NaN or Inf values."""


class WindowOutOfRangeError(MusDomainError):
    """Raised when a time window falls outside the take duration."""


class ExternalToolMissingError(MusDomainError):
    """Raised when a required external binary (e.g., fluidsynth, musescore) is not found."""


class ConfigurationError(MusDomainError):
    """Raised when required configuration or assets (e.g. soundfont) are invalid or missing."""
