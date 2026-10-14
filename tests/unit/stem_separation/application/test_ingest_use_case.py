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
    assert result.vocals_path.parent == tmp_path / "Jazz"
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
    assert result.vocals_path.parent == tmp_path / "Pop_Rock"

    # Test empty genre falls back to Unknown
    use_case_empty = IngestAndSeparateTrack(
        downloader=downloader,
        tagger=CustomTagger("   "),
        separator=separator,
        catalog=catalog,
    )
    cmd_empty = IngestAndSeparateCommand(source="http://yt/2", output_dir=tmp_path)
    result_empty = use_case_empty.execute(cmd_empty)
    assert result_empty.vocals_path.parent == tmp_path / "Unknown"
