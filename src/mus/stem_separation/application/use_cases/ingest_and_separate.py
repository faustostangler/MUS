"""IngestAndSeparateTrack use case managing the two-phase pipeline."""

import re
import shutil
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


def sanitize_genre(genre: str) -> str:
    """Sanitizes musical genre name for filesystem storage."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", genre).strip()
    return cleaned or "Unknown"


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
        """Executes two-phase ingestion and separation into genre-organized directory."""
        source = command.source
        base_output_dir = Path(command.output_dir).resolve()
        base_output_dir.mkdir(parents=True, exist_ok=True)

        # Fast-path: Check catalog history and existing stems to avoid re-downloading
        vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", str(source))
        video_id = vid_match.group(1) if vid_match else None
        cached_tracks = getattr(self._catalog, "_cache", {}).get("tracks", {})
        cached_entry = cached_tracks.get(video_id) if video_id else None

        if cached_entry:
            cached_genre = sanitize_genre(cached_entry.get("genre", "Unknown"))
            cached_genre_dir = base_output_dir / cached_genre
            cached_genre_dir.mkdir(parents=True, exist_ok=True)
            track_name = cached_entry.get("track", "")

            # Search for existing vocals stem in genre dir or base stems dir
            existing_vocals = list(cached_genre_dir.glob(f"*{track_name}*vocals.mp3")) or list(
                base_output_dir.glob(f"*{track_name}*vocals.mp3")
            )
            if existing_vocals:
                v_path = existing_vocals[0]
                if v_path.parent != cached_genre_dir:
                    target_v = cached_genre_dir / v_path.name
                    shutil.move(str(v_path), str(target_v))
                    v_path = target_v
                other_stems = {
                    s.stem.split(" - ")[-1]: s
                    for s in cached_genre_dir.glob(f"*{track_name}* - *.mp3")
                    if s != v_path and not s.name.endswith("- synt.mp3")
                }
                return SeparatedStems(vocals_path=v_path, other_stems=other_stems)

        # Phase 1: Ingestion & Tagging
        if isinstance(source, str) and (
            source.startswith("http://") or source.startswith("https://")
        ):
            audio_path, _video_id, raw_title = self._downloader.download(source, base_output_dir)
        else:
            audio_path = Path(source).resolve()
            raw_title = audio_path.stem

        metadata = self._tagger.tag(raw_title)

        # Transition: VRAM cleanup before invoking heavy GPU Demucs (ADR-001 D9)
        if self._vram_cleaner is not None:
            self._vram_cleaner()

        # Genre-partitioned output directory (ADR-002 D1)
        genre_name = sanitize_genre(metadata.genre)
        genre_dir = base_output_dir / genre_name
        genre_dir.mkdir(parents=True, exist_ok=True)

        # Relocate downloaded audio file into the genre directory if needed
        if audio_path.parent != genre_dir and audio_path.exists():
            target_audio_path = genre_dir / audio_path.name
            shutil.move(str(audio_path), str(target_audio_path))
            audio_path = target_audio_path

        # Phase 2: Separation (fast-path: reuse if stems already exist)
        expected_vocals = genre_dir / f"{audio_path.stem} - vocals.mp3"
        if expected_vocals.exists():
            other_stems = {
                s.stem.split(" - ")[-1]: s
                for s in genre_dir.glob(f"{audio_path.stem} - *.mp3")
                if s != expected_vocals and not s.name.endswith("- synt.mp3")
            }
            stems = SeparatedStems(vocals_path=expected_vocals, other_stems=other_stems)
        else:
            stems = self._separator.separate(audio_path, genre_dir)

        # Record into history
        self._catalog.record(metadata, stems)

        return stems
