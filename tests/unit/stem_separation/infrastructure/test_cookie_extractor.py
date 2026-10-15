"""Unit tests for YouTube cookie extraction and cache management."""

import os
import time
from http.cookiejar import Cookie
from pathlib import Path
from unittest.mock import patch

from mus.stem_separation.infrastructure.cookie_extractor import (
    ensure_cookies_file,
    export_cookies_auto,
    export_cookies_from_browser,
    has_valid_auth_cookies,
)


def _make_dummy_cookie(
    name: str, domain: str, value: str = "mock_val", expires: int | None = None
) -> Cookie:
    """Helper to instantiate mock Cookie objects."""
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=domain.startswith("."),
        path="/",
        path_specified=True,
        secure=True,
        expires=expires or int(time.time() + 86400),
        discard=False,
        comment=None,
        comment_url=None,
        rest={},
    )


def test_has_valid_auth_cookies_returns_false_when_missing_or_empty(tmp_path: Path) -> None:
    non_existent = tmp_path / "non_existent.txt"
    assert has_valid_auth_cookies(non_existent) is False

    empty = tmp_path / "empty.txt"
    empty.touch()
    assert has_valid_auth_cookies(empty) is False


def test_has_valid_auth_cookies_identifies_auth_tokens(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"

    # Only guest cookies -> False
    guest_cookie = (
        "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t2147483647\tPREF\tf1=5\n"
    )
    cookie_file.write_text(guest_cookie)
    assert has_valid_auth_cookies(cookie_file) is False

    # Contains LOGIN_INFO -> True
    cookie_file.write_text(
        "# Netscape HTTP Cookie File\n"
        ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tLOGIN_INFO\taf87dsf6a78sd6f7as6df78as6df\n"
    )
    assert has_valid_auth_cookies(cookie_file) is True


def test_export_cookies_from_browser_filters_and_persists(tmp_path: Path) -> None:
    out_file = tmp_path / "out_cookies.txt"
    mock_jar = [
        _make_dummy_cookie("LOGIN_INFO", ".youtube.com", "token123"),
        _make_dummy_cookie("SID", ".google.com", "sid456"),
        _make_dummy_cookie("OTHER", "docs.google.com", "ignored"),
        _make_dummy_cookie("EXTERNAL", "facebook.com", "ignored"),
    ]

    with patch(
        "mus.stem_separation.infrastructure.cookie_extractor._extract_raw_cookies",
        return_value=mock_jar,
    ):
        success = export_cookies_from_browser("firefox", out_file)
        assert success is True
        assert out_file.exists()
        content = out_file.read_text()
        assert "LOGIN_INFO" in content
        assert "SID" in content
        assert "facebook.com" not in content
        assert "docs.google.com" not in content


def test_export_cookies_from_browser_returns_false_on_empty(tmp_path: Path) -> None:
    out_file = tmp_path / "empty_out.txt"
    with patch(
        "mus.stem_separation.infrastructure.cookie_extractor._extract_raw_cookies",
        return_value=None,
    ):
        assert export_cookies_from_browser("firefox", out_file) is False
        assert not out_file.exists()


def test_export_cookies_auto_tries_browsers_in_priority(tmp_path: Path) -> None:
    out_file = tmp_path / "auto_cookies.txt"
    with patch(
        "mus.stem_separation.infrastructure.cookie_extractor.export_cookies_from_browser",
        side_effect=[False, True],
    ) as mock_export:
        success = export_cookies_auto(out_file, preferred_browser="firefox")
        assert success is True
        assert mock_export.call_count == 2
        # First call was firefox, second call was chrome
        assert mock_export.call_args_list[0].kwargs["browser"] == "firefox"
        assert mock_export.call_args_list[1].kwargs["browser"] == "chrome"


def test_ensure_cookies_file_reuses_valid_cache(tmp_path: Path) -> None:
    cached_file = tmp_path / "cached_cookies.txt"
    cached_file.write_text(
        "# Netscape HTTP Cookie File\n"
        ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tLOGIN_INFO\taf87dsf6a78sd6f7as6df78as6df\n"
    )
    with patch(
        "mus.stem_separation.infrastructure.cookie_extractor.export_cookies_from_browser"
    ) as mock_export:
        res = ensure_cookies_file(cached_file, browser="firefox", max_age_hours=12)
        assert res == cached_file
        mock_export.assert_not_called()


def test_ensure_cookies_file_refreshes_when_expired(tmp_path: Path) -> None:
    expired_file = tmp_path / "expired_cookies.txt"
    expired_file.write_text(
        "# Netscape HTTP Cookie File\n"
        ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tLOGIN_INFO\taf87dsf6a78sd6f7as6df78as6df\n"
    )
    past_time = time.time() - 20 * 3600
    os.utime(expired_file, (past_time, past_time))

    with patch(
        "mus.stem_separation.infrastructure.cookie_extractor.export_cookies_from_browser",
        return_value=True,
    ) as mock_export:
        res = ensure_cookies_file(expired_file, browser="firefox", max_age_hours=12)
        assert res == expired_file
        mock_export.assert_called_once()
