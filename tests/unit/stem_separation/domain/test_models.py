"""Unit tests for stem separation domain models."""

from pathlib import Path

import pytest

from mus.stem_separation.domain.models import (
    SeparatedStems,
    TrackMetadata,
)


def test_track_metadata_invariants() -> None:
    meta = TrackMetadata(
        video_id="abc123xyz",
        title="Frank Sinatra - My Way",
        artist="Frank Sinatra",
        track="My Way",
        genre="Jazz",
    )
    assert meta.artist == "Frank Sinatra"
    assert meta.track == "My Way"
    assert meta.genre == "Jazz"


def test_separated_stems_vocal_path_access(tmp_path: Path) -> None:
    vocals = tmp_path / "vocals.mp3"
    vocals.touch()
    drums = tmp_path / "drums.mp3"
    drums.touch()

    stems = SeparatedStems(
        vocals_path=vocals,
        other_stems={"drums": drums},
    )
    assert stems.vocals_path == vocals
    assert "drums" in stems.other_stems


def test_separated_stems_missing_vocals_raises(tmp_path: Path) -> None:
    non_existent = tmp_path / "vocals_non_existent.mp3"
    with pytest.raises(FileNotFoundError, match="Vocals stem file does not exist"):
        SeparatedStems(
            vocals_path=non_existent,
            other_stems={},
        )
