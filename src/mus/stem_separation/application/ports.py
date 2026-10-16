"""Ports for stem separation, metadata tagging, and catalog history."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from mus.stem_separation.domain.models import SeparatedStems, TrackMetadata


class AudioDownloaderPort(ABC):
    """Port for downloading audio from external URLs (e.g. YouTube)."""

    @abstractmethod
    def download(self, url: str, output_dir: Path) -> tuple[Path, str, str]:
        """Downloads audio and returns (audio_file_path, video_id, raw_title)."""


class MetadataTaggerPort(ABC):
    """Port for identifying track metadata (artist, title, genre) via LLM or heuristics."""

    @abstractmethod
    def tag(self, raw_title: str) -> TrackMetadata:
        """Parses and enriches raw track title into structured TrackMetadata."""


class StemSeparatorPort(ABC):
    """Port for decomposing audio into isolated stems (e.g. HTDemucs)."""

    @abstractmethod
    def separate(self, audio_path: Path, output_dir: Path) -> SeparatedStems:
        """Separates an audio file into stems and returns SeparatedStems."""


class CatalogHistoryPort(ABC):
    """Port for tracking and persisting processed tracks in local history."""

    @abstractmethod
    def is_completed(self, video_id: str) -> bool:
        """Returns True if the track was already processed and verified on disk."""

    @abstractmethod
    def get_entry(self, video_id: str) -> dict[str, Any] | None:
        """Retrieves catalog history entry for a video_id if available."""

    @abstractmethod
    def record(self, metadata: TrackMetadata, stems: SeparatedStems) -> None:
        """Records a successfully processed track into the history store."""
