"""Unit tests for IngestAndSeparateTrack use case using fakes."""

from pathlib import Path

from mus.stem_separation.application.ports import (
    AudioDownloaderPort,
    CatalogHistoryPort,
    MetadataTaggerPort,
    StemSeparatorPort,
)
from mus.stem_separation.application.use_cases.ingest_and_separate import (
    IngestAndSeparateCommand,
    IngestAndSeparateTrack,
)
from mus.stem_separation.domain.models import SeparatedStems, TrackMetadata


class FakeDownloader(AudioDownloaderPort):
    def download(self, url: str, output_dir: Path) -> tuple[Path, str, str]:
        audio_file = output_dir / "downloaded.mp3"
        audio_file.touch()
        return audio_file, "vid_123", "Sinatra - My Way"


class FakeTagger(MetadataTaggerPort):
    def tag(self, raw_title: str) -> TrackMetadata:
        return TrackMetadata(
            video_id="vid_123",
            title=raw_title,
            artist="Frank Sinatra",
            track="My Way",
            genre="Jazz",
        )


class FakeSeparator(StemSeparatorPort):
    def separate(self, audio_path: Path, output_dir: Path) -> SeparatedStems:
        vocals = output_dir / "vocals.mp3"
        vocals.touch()
        return SeparatedStems(vocals_path=vocals, other_stems={})


class FakeCatalog(CatalogHistoryPort):
    def __init__(self) -> None:
        self.records: dict[str, TrackMetadata] = {}

    def is_completed(self, video_id: str) -> bool:
        return video_id in self.records

    def get_entry(self, video_id: str) -> dict[str, str] | None:
        return None

    def record(self, metadata: TrackMetadata, stems: SeparatedStems) -> None:
        self.records[metadata.video_id] = metadata


def test_ingest_and_separate_track_executes_pipeline(tmp_path: Path) -> None:
    downloader = FakeDownloader()
    tagger = FakeTagger()
    separator = FakeSeparator()
    catalog = FakeCatalog()

    use_case = IngestAndSeparateTrack(
        downloader=downloader,
        tagger=tagger,
        separator=separator,
        catalog=catalog,
    )

    cmd = IngestAndSeparateCommand(
        source="https://youtube.com/watch?v=vid_123",
        output_dir=tmp_path,
    )

    result = use_case.execute(cmd)

    assert result.vocals_path.exists()
    assert result.vocals_path.parent == tmp_path / "jazz" / "Frank Sinatra - My Way"
    assert (tmp_path / "jazz" / "Frank Sinatra - My Way.mp3").exists()
    assert "vid_123" in catalog.records


def test_ingest_and_separate_track_sanitizes_genre_and_handles_empty(tmp_path: Path) -> None:
    downloader = FakeDownloader()
    separator = FakeSeparator()
    catalog = FakeCatalog()

    class CustomTagger(MetadataTaggerPort):
        def __init__(self, genre: str) -> None:
            self._genre = genre

        def tag(self, raw_title: str) -> TrackMetadata:
            return TrackMetadata(
                video_id="vid_456",
                title=raw_title,
                artist="Artist",
                track="Track",
                genre=self._genre,
            )

    # Test sanitized slash in genre
    use_case = IngestAndSeparateTrack(
        downloader=downloader,
        tagger=CustomTagger("Pop/Rock"),
        separator=separator,
        catalog=catalog,
    )
    cmd = IngestAndSeparateCommand(source="http://yt/1", output_dir=tmp_path)
    result = use_case.execute(cmd)
    assert result.vocals_path.parent == tmp_path / "pop-rock" / "Artist - Track"
    assert (tmp_path / "pop-rock" / "Artist - Track.mp3").exists()

    # Test empty genre falls back to unknown
    use_case_empty = IngestAndSeparateTrack(
        downloader=downloader,
        tagger=CustomTagger("   "),
        separator=separator,
        catalog=catalog,
    )
    cmd_empty = IngestAndSeparateCommand(source="http://yt/2", output_dir=tmp_path)
    result_empty = use_case_empty.execute(cmd_empty)
    assert result_empty.vocals_path.parent == tmp_path / "unknown" / "Artist - Track"
    assert (tmp_path / "unknown" / "Artist - Track.mp3").exists()


def test_ingest_and_separate_downloads_to_staging_before_tagging_and_moving(tmp_path: Path) -> None:
    events: list[str] = []

    class EventRecordingDownloader(AudioDownloaderPort):
        def download(self, url: str, output_dir: Path) -> tuple[Path, str, str]:
            events.append(f"download:{output_dir.name}")
            assert output_dir == tmp_path / ".staging"
            f = output_dir / "raw.mp3"
            f.touch()
            return f, "yt_999", "Queen - Bohemian Rhapsody"

    class EventRecordingTagger(MetadataTaggerPort):
        def tag(self, raw_title: str) -> TrackMetadata:
            events.append("tag_metadata")
            # Verify that the destination file has NOT yet been created/moved
            assert not (tmp_path / "rock" / "Queen - Bohemian Rhapsody.mp3").exists()
            return TrackMetadata(
                video_id="yt_999",
                title=raw_title,
                artist="Queen",
                track="Bohemian Rhapsody",
                genre="Rock",
            )

    class EventRecordingSeparator(StemSeparatorPort):
        def separate(self, audio_path: Path, output_dir: Path) -> SeparatedStems:
            events.append("separate")
            assert audio_path == tmp_path / "rock" / "Queen - Bohemian Rhapsody.mp3"
            assert output_dir == tmp_path / "rock" / "Queen - Bohemian Rhapsody"
            v = output_dir / "vocals.mp3"
            v.touch()
            return SeparatedStems(vocals_path=v, other_stems={})

    catalog = FakeCatalog()
    use_case = IngestAndSeparateTrack(
        downloader=EventRecordingDownloader(),
        tagger=EventRecordingTagger(),
        separator=EventRecordingSeparator(),
        catalog=catalog,
    )

    cmd = IngestAndSeparateCommand(
        source="https://youtube.com/watch?v=yt_999",
        output_dir=tmp_path,
    )

    stems = use_case.execute(cmd)
    assert events == ["download:.staging", "tag_metadata", "separate"]
    assert (tmp_path / "rock" / "Queen - Bohemian Rhapsody.mp3").exists()
    assert stems.vocals_path.parent == tmp_path / "rock" / "Queen - Bohemian Rhapsody"
    assert "yt_999" in catalog.records
