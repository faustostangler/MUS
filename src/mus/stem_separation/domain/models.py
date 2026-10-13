"""Domain models for stem separation and audio ingestion."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TrackMetadata:
    """Standardized metadata for a musical track."""

    video_id: str
    title: str
    artist: str
    track: str
    genre: str


@dataclass(frozen=True, slots=True)
class SeparatedStems:
    """Isolated musical stems produced by source separation."""

    vocals_path: Path
    other_stems: dict[str, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vocals_path.exists():
            raise FileNotFoundError(f"Vocals stem file does not exist at: {self.vocals_path}")
