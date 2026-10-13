"""IngestAndSeparateTrack use case managing the two-phase pipeline."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from mus.stem_separation.application.ports import (
    AudioDownloaderPort,
    CatalogHistoryPort,
    MetadataTaggerPort,
    StemSeparatorPort,
)
from mus.stem_separation.domain.models import SeparatedStems


@dataclass(frozen=True, slots=True)
class IngestAndSeparateCommand:
    """Input parameters for track ingestion and stem separation."""

    source: str | Path  # URL or local file path
    output_dir: Path
    model_name: str = "htdemucs_6s"


class IngestAndSeparateTrack:
    """Coordinates downloading, AI metadata tagging, VRAM transition, and stem separation."""

    def __init__(
        self,
        downloader: AudioDownloaderPort,
        tagger: MetadataTaggerPort,
        separator: StemSeparatorPort,
        catalog: CatalogHistoryPort,
        vram_cleaner: Callable[[], None] | None = None,
    ) -> None:
        self._downloader = downloader
        self._tagger = tagger
        self._separator = separator
        self._catalog = catalog
        self._vram_cleaner = vram_cleaner

    def execute(self, command: IngestAndSeparateCommand) -> SeparatedStems:
        """Executes two-phase ingestion and separation."""
        source = command.source
        output_dir = Path(command.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Ingestion & Tagging
        if isinstance(source, str) and (
            source.startswith("http://") or source.startswith("https://")
        ):
            audio_path, _video_id, raw_title = self._downloader.download(source, output_dir)
        else:
            audio_path = Path(source).resolve()
            raw_title = audio_path.stem

        metadata = self._tagger.tag(raw_title)

        # Transition: VRAM cleanup before invoking heavy GPU Demucs (ADR-001 D9)
        if self._vram_cleaner is not None:
            self._vram_cleaner()

        # Phase 2: Separation
        stems = self._separator.separate(audio_path, output_dir)

        # Record into history
        self._catalog.record(metadata, stems)

        return stems
