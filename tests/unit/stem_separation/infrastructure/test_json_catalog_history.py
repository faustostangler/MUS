"""Unit tests for JsonCatalogHistory adapter."""

from pathlib import Path

from mus.stem_separation.domain.models import SeparatedStems, TrackMetadata
from mus.stem_separation.infrastructure.json_catalog_history import JsonCatalogHistory


def test_json_catalog_history_roundtrip(tmp_path: Path) -> None:
    history_file = tmp_path / "history.json"
    catalog = JsonCatalogHistory(history_file=history_file)

    assert not catalog.is_completed("vid_1")

    vocals = tmp_path / "vocals.mp3"
    vocals.touch()
    meta = TrackMetadata(
        video_id="vid_1",
        title="Sinatra - My Way",
        artist="Frank Sinatra",
        track="My Way",
        genre="Jazz",
    )
    stems = SeparatedStems(vocals_path=vocals, other_stems={})

    catalog.record(meta, stems)

    assert catalog.is_completed("vid_1")

    # Re-instantiate to verify disk persistence
    catalog_reloaded = JsonCatalogHistory(history_file=history_file)
    assert catalog_reloaded.is_completed("vid_1")
