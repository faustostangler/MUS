"""JSON-backed catalog history adapter with atomic writes."""

import json
from pathlib import Path
from typing import Any

from mus.stem_separation.application.ports import CatalogHistoryPort
from mus.stem_separation.domain.models import SeparatedStems, TrackMetadata


class JsonCatalogHistory(CatalogHistoryPort):
    """Tracks processed tracks in a JSON database."""

    def __init__(self, history_file: Path) -> None:
        self._history_file = Path(history_file).resolve()
        self._cache: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Loads catalog history from file."""
        if not self._history_file.exists():
            return {"tracks": {}}
        try:
            with open(self._history_file, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "tracks" in data:
                    return data
                return {"tracks": {}}
        except Exception:
            return {"tracks": {}}

    def _save(self) -> None:
        """Atomically saves catalog history to disk."""
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self._history_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self._history_file)

    def is_completed(self, video_id: str) -> bool:
        """Checks if video_id exists in history and files exist."""
        tracks = self._cache.get("tracks", {})
        if video_id in tracks:
            entry = tracks[video_id]
            audio_path = Path(entry.get("audio_file", ""))
            return audio_path.exists()
        return False

    def get_entry(self, video_id: str) -> dict[str, Any] | None:
        """Retrieves catalog history entry for a video_id if available."""
        tracks = self._cache.get("tracks", {})
        if isinstance(tracks, dict):
            entry = tracks.get(video_id)
            if isinstance(entry, dict):
                return entry
        return None

    def record(self, metadata: TrackMetadata, stems: SeparatedStems) -> None:
        """Records a processed track into the history store."""
        tracks = self._cache.setdefault("tracks", {})
        tracks[metadata.video_id] = {
            "video_id": metadata.video_id,
            "title": metadata.title,
            "artist": metadata.artist,
            "track": metadata.track,
            "genre": metadata.genre,
            "audio_file": str(stems.vocals_path),
            "stems": {k: str(v) for k, v in stems.other_stems.items()},
        }
        self._save()
