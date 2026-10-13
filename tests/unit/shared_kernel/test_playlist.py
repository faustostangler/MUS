"""Unit tests for playlist parsing and YouTube regex extraction."""

from pathlib import Path

import pytest

from mus.shared_kernel.playlist import (
    YOUTUBE_URL_REGEX,
    extract_youtube_urls_from_text,
    load_youtube_playlist,
)


def test_youtube_regex_matches_various_formats() -> None:
    valid_urls = [
        "https://music.youtube.com/watch?v=YlVTh_b4af4",
        "https://www.youtube.com/watch?v=1UjLFMg18cY",
        "http://youtube.com/watch?v=iX_TFkut1PM",
        "https://youtu.be/c0dvabcWVo0",
        "https://m.youtube.com/watch?v=SuRCxakQt-c",
        "https://youtube.com/shorts/8XbHp0HWJtk",
    ]
    for url in valid_urls:
        assert YOUTUBE_URL_REGEX.match(url) is not None, f"Expected match for {url}"


def test_youtube_regex_rejects_invalid_urls() -> None:
    invalid_urls = [
        "ftp://youtube.com/watch?v=123",
        "www.youtube.com/watch?v=123",
        "https://vimeo.com/123456",
        "https://spotify.com/track/123",
        "not_a_url",
        "",
    ]
    for url in invalid_urls:
        assert YOUTUBE_URL_REGEX.match(url) is None, f"Expected reject for {url}"


def test_extract_youtube_urls_filters_and_ignores_comments() -> None:
    sample_text = """
    # My Playlist
    https://music.youtube.com/watch?v=track1

    # Another comment
    https://spotify.com/invalid
    https://youtu.be/track2
    """
    urls = extract_youtube_urls_from_text(sample_text)
    assert urls == [
        "https://music.youtube.com/watch?v=track1",
        "https://youtu.be/track2",
    ]


def test_load_youtube_playlist_from_file(tmp_path: Path) -> None:
    playlist_file = tmp_path / "test_playlist.txt"
    playlist_file.write_text(
        "https://music.youtube.com/watch?v=aaa\nhttps://www.youtube.com/watch?v=bbb\n# comment\n",
        encoding="utf-8",
    )

    urls = load_youtube_playlist(playlist_file)
    assert len(urls) == 2
    assert urls[0] == "https://music.youtube.com/watch?v=aaa"
    assert urls[1] == "https://www.youtube.com/watch?v=bbb"


def test_load_youtube_playlist_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_youtube_playlist(Path("/nonexistent/playlist.txt"))
