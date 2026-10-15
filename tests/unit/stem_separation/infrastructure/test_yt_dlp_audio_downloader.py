"""Unit tests for YtDlpAudioDownloader infrastructure adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from mus.stem_separation.infrastructure.yt_dlp_audio_downloader import YtDlpAudioDownloader


def test_downloader_injects_cookiefile_when_present(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n")

    downloader = YtDlpAudioDownloader(cookie_file=cookie_file, auto_extract_cookies=False)

    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {"id": "123", "title": "Test Title"}
    mock_ydl.prepare_filename.return_value = str(tmp_path / "Test Title.mp3")

    with (
        patch("yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("shutil.which", return_value="/usr/bin/node"),
    ):
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        downloader.download("https://www.youtube.com/watch?v=123", tmp_path)

        ydl_opts = mock_ydl_cls.call_args[0][0]
        assert ydl_opts["cookiefile"] == str(cookie_file)
        assert ydl_opts["js_runtimes"] == {"node": {}}


def test_downloader_auto_extracts_cookies_if_configured(tmp_path: Path) -> None:
    expected_cookie = tmp_path / "auto_cookies.txt"
    expected_cookie.write_text("# Netscape HTTP Cookie File\n")

    downloader = YtDlpAudioDownloader(
        cookie_file=None,
        browser="firefox",
        auto_extract_cookies=True,
    )

    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {"id": "456", "title": "Auto Track"}
    mock_ydl.prepare_filename.return_value = str(tmp_path / "Auto Track.mp3")

    with (
        patch(
            "mus.stem_separation.infrastructure.yt_dlp_audio_downloader.ensure_cookies_file",
            return_value=expected_cookie,
        ) as mock_ensure,
        patch("yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("shutil.which", return_value=None),
    ):
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        downloader.download("https://www.youtube.com/watch?v=456", tmp_path)

        mock_ensure.assert_called_once()
        ydl_opts = mock_ydl_cls.call_args[0][0]
        assert ydl_opts["cookiefile"] == str(expected_cookie)
        assert "js_runtimes" not in ydl_opts


def test_downloader_handles_bot_challenge_with_clear_error(tmp_path: Path) -> None:
    downloader = YtDlpAudioDownloader(auto_extract_cookies=False)

    mock_ydl = MagicMock()
    mock_ydl.extract_info.side_effect = DownloadError("Sign in to confirm you're not a bot")

    with (
        patch("yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("shutil.which", return_value=None),
    ):
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        with pytest.raises(RuntimeError) as exc_info:
            downloader.download("https://www.youtube.com/watch?v=botcheck", tmp_path)

        assert "YouTube bot-detection challenge triggered" in str(exc_info.value)
