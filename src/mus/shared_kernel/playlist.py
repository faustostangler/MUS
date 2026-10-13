"""Playlist parsing and YouTube link extraction utilities (ADR-001)."""

import re
from pathlib import Path

# Strict Regex: Starts with http:// or https://,
# followed by YouTube domains (music., www., m., youtu.be, etc.)
YOUTUBE_URL_REGEX = re.compile(
    r"^https?:\/\/(?:[a-zA-Z0-9-]+\.)?(?:youtube\.com|youtu\.be)\/\S+"
)


def extract_youtube_urls_from_text(content: str) -> list[str]:
    """Extracts valid YouTube URLs from multiline string content.

    Ignores blank lines, lines starting with comments (#), and non-YouTube URLs.

    Args:
        content: Raw text content from playlist file.

    Returns:
        List of matching YouTube URLs.
    """
    urls: list[str] = []
    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed and not trimmed.startswith("#") and YOUTUBE_URL_REGEX.match(trimmed):
            urls.append(trimmed)
    return urls


def load_youtube_playlist(playlist_path: str | Path) -> list[str]:
    """Reads a text playlist file and returns all valid YouTube URLs.

    Args:
        playlist_path: File system path to the playlist.txt file.

    Returns:
        List of validated YouTube URLs.

    Raises:
        FileNotFoundError: If the specified playlist file does not exist.
    """
    path = Path(playlist_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Playlist file not found: {path}")

    return extract_youtube_urls_from_text(path.read_text(encoding="utf-8"))
