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
from mus.stem_separation.domain.models import SeparatedStems, TrackMetadata


def sanitize_genre(genre: str) -> str:
    """Sanitizes musical genre name into a lowercase slug (e.g. 'samba-reggae')."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", genre.strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "unknown"


def build_canonical_title(artist: str, track: str, default: str = "") -> str:
    """Builds standardized '{artist} - {track}' naming."""
    artist_clean = artist.strip()
    track_clean = track.strip()
    if artist_clean and artist_clean.lower() != "unknown artist":
        if not track_clean.lower().startswith(f"{artist_clean.lower()} - "):
            return f"{artist_clean} - {track_clean}"
        return track_clean
    return track_clean or default


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

    def _resolve_cached_stems(
        self, source: str | Path, base_output_dir: Path
    ) -> SeparatedStems | None:
        """Attempts to recover previously separated stems from catalog history and track folder."""
        vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", str(source))
        video_id = vid_match.group(1) if vid_match else None
        cached_tracks = getattr(self._catalog, "_cache", {}).get("tracks", {})
        cached_entry = cached_tracks.get(video_id) if video_id else None
        if not cached_entry:
            return None

        cached_genre = sanitize_genre(cached_entry.get("genre", "unknown"))
        cached_genre_dir = base_output_dir / cached_genre
        cached_genre_dir.mkdir(parents=True, exist_ok=True)
        artist = cached_entry.get("artist", "")
        track_name = cached_entry.get("track", "")
        canonical_name = build_canonical_title(artist, track_name, default=track_name)
        cached_track_dir = cached_genre_dir / canonical_name

        existing_vocals = (
            list(cached_track_dir.glob(f"*{canonical_name}*vocals.mp3"))
            or list(cached_track_dir.glob(f"*{track_name}*vocals.mp3"))
            or list(cached_genre_dir.glob(f"*{canonical_name}*vocals.mp3"))
            or list(cached_genre_dir.glob(f"*{track_name}*vocals.mp3"))
            or list(base_output_dir.rglob(f"*{canonical_name}*vocals.mp3"))
            or list(base_output_dir.rglob(f"*{track_name}*vocals.mp3"))
        )
        if not existing_vocals:
            return None

        v_path = existing_vocals[0]
        cached_track_dir.mkdir(parents=True, exist_ok=True)
        if v_path.parent != cached_track_dir:
            source_dir = v_path.parent
            for s in list(source_dir.glob(f"*{canonical_name}*")) + list(
                source_dir.glob(f"*{track_name}*")
            ):
                target_s = cached_track_dir / s.name
                if not target_s.exists():
                    shutil.move(str(s), str(target_s))
            v_path = cached_track_dir / v_path.name
            # Migrate master full track mp3 if found in old parent
            for m in [
                source_dir.parent / f"{canonical_name}.mp3",
                source_dir.parent / f"{track_name}.mp3",
                source_dir / f"{canonical_name}.mp3",
                source_dir / f"{track_name}.mp3",
            ]:
                if m.exists() and m != cached_genre_dir / f"{canonical_name}.mp3":
                    shutil.move(str(m), str(cached_genre_dir / f"{canonical_name}.mp3"))

        other_stems = {
            s.stem.split(" - ")[-1]: s
            for s in cached_track_dir.glob(f"*{track_name}* - *.mp3")
            if s != v_path
            and not s.name.endswith("- mid.mp3")
            and not s.name.endswith("- synt.mp3")
        }
        return SeparatedStems(vocals_path=v_path, other_stems=other_stems)

    def _download_or_resolve_source(
        self, source: str | Path, staging_dir: Path
    ) -> tuple[Path, str, str]:
        """Resolves source into local audio file, video_id, and raw title."""
        if isinstance(source, str) and (
            source.startswith("http://") or source.startswith("https://")
        ):
            return self._downloader.download(source, staging_dir)

        audio_path = Path(source).resolve()
        raw_title = audio_path.stem
        vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", str(source))
        video_id = vid_match.group(1) if vid_match else re.sub(r"[^\w\-]", "_", raw_title)[:32]
        return audio_path, video_id, raw_title

    def _resolve_metadata(self, video_id: str, raw_title: str) -> TrackMetadata:
        """Resolves TrackMetadata using catalog history first, then metadata tagger."""
        catalog_entry = None
        if hasattr(self._catalog, "get_entry"):
            catalog_entry = self._catalog.get_entry(video_id)

        if catalog_entry:
            c_genre = str(catalog_entry.get("genre") or "").strip().lower()
            c_artist = str(catalog_entry.get("artist") or "").strip().lower()
            if c_genre and c_genre != "other" and c_artist and c_artist != "unknown artist":
                return TrackMetadata(
                    video_id=video_id,
                    title=str(catalog_entry.get("title") or raw_title),
                    artist=str(catalog_entry.get("artist") or "Unknown Artist"),
                    track=str(catalog_entry.get("track") or raw_title),
                    genre=str(catalog_entry.get("genre") or "Other"),
                )

        tagger_meta = self._tagger.tag(raw_title)
        return TrackMetadata(
            video_id=video_id,
            title=tagger_meta.title,
            artist=tagger_meta.artist,
            track=tagger_meta.track,
            genre=tagger_meta.genre,
        )

    def _resolve_stems_output(
        self,
        audio_path: Path,
        track_stems_dir: Path,
        genre_dir: Path,
        canonical_title: str,
    ) -> SeparatedStems:
        """Resolves existing stems or runs separator."""
        expected_vocals = track_stems_dir / f"{canonical_title} - vocals.mp3"
        legacy_vocals = track_stems_dir / f"{audio_path.stem} - vocals.mp3"
        fallback_vocals = genre_dir / f"{audio_path.stem} - vocals.mp3"

        if expected_vocals.exists():
            other_stems = {
                s.stem.split(" - ")[-1]: s
                for s in track_stems_dir.glob(f"{canonical_title} - *.mp3")
                if s != expected_vocals
                and not s.name.endswith("- mid.mp3")
                and not s.name.endswith("- synt.mp3")
            }
            return SeparatedStems(vocals_path=expected_vocals, other_stems=other_stems)

        if legacy_vocals.exists():
            other_stems = {
                s.stem.split(" - ")[-1]: s
                for s in track_stems_dir.glob(f"{audio_path.stem} - *.mp3")
                if s != legacy_vocals
                and not s.name.endswith("- mid.mp3")
                and not s.name.endswith("- synt.mp3")
            }
            return SeparatedStems(vocals_path=legacy_vocals, other_stems=other_stems)

        if fallback_vocals.exists():
            for f in genre_dir.glob(f"{audio_path.stem} - *"):
                shutil.move(str(f), str(track_stems_dir / f.name))
            target_v = track_stems_dir / fallback_vocals.name
            other_stems = {
                s.stem.split(" - ")[-1]: s
                for s in track_stems_dir.glob(f"{audio_path.stem} - *.mp3")
                if s != target_v
                and not s.name.endswith("- mid.mp3")
                and not s.name.endswith("- synt.mp3")
            }
            return SeparatedStems(vocals_path=target_v, other_stems=other_stems)

        return self._separator.separate(audio_path, track_stems_dir)

    def execute(self, command: IngestAndSeparateCommand) -> SeparatedStems:
        """Executes two-phase ingestion and separation into genre-organized directory."""
        source = command.source
        base_output_dir = Path(command.output_dir).resolve()
        base_output_dir.mkdir(parents=True, exist_ok=True)

        cached_stems = self._resolve_cached_stems(source, base_output_dir)
        if cached_stems is not None:
            return cached_stems

        staging_dir = base_output_dir / ".staging"
        staging_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Download to staging before genre determination
        audio_path, video_id, raw_title = self._download_or_resolve_source(source, staging_dir)
        metadata = self._resolve_metadata(video_id, raw_title)

        # Transition: VRAM cleanup before invoking heavy GPU Demucs (ADR-001 D9)
        if self._vram_cleaner is not None:
            self._vram_cleaner()

        # Genre-partitioned output directory in lowercase slug format (e.g. 'samba-reggae')
        genre_name = sanitize_genre(metadata.genre)
        genre_dir = base_output_dir / genre_name
        genre_dir.mkdir(parents=True, exist_ok=True)

        canonical_title = build_canonical_title(metadata.artist, metadata.track, default=raw_title)
        target_audio_path = genre_dir / f"{canonical_title}.mp3"

        # Relocate and rename downloaded audio file from staging into the genre directory
        if audio_path != target_audio_path and audio_path.exists():
            shutil.move(str(audio_path), str(target_audio_path))
            audio_path = target_audio_path

        # Clean up empty staging directory
        if staging_dir.exists():
            try:
                if not any(staging_dir.iterdir()):
                    staging_dir.rmdir()
            except Exception:
                pass

        # Phase 2: Separation into track-encapsulated directory
        track_stems_dir = genre_dir / canonical_title
        track_stems_dir.mkdir(parents=True, exist_ok=True)

        stems = self._resolve_stems_output(audio_path, track_stems_dir, genre_dir, canonical_title)

        # Record into history
        self._catalog.record(metadata, stems)

        return stems
