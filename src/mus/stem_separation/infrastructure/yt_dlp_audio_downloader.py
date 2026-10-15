"""Audio downloader adapter utilizing yt-dlp with cookie management and JS challenge solving."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from mus.config import get_settings
from mus.stem_separation.application.ports import AudioDownloaderPort
from mus.stem_separation.infrastructure.cookie_extractor import ensure_cookies_file

logger = logging.getLogger(__name__)


class YtDlpAudioDownloader(AudioDownloaderPort):
    """Downloads audio tracks using yt-dlp with automated cookie handling and challenge solving."""

    def __init__(
        self,
        cookie_file: Path | None = None,
        browser: str | None = None,
        auto_extract_cookies: bool | None = None,
    ) -> None:
        settings = get_settings()
        self._cookie_file = cookie_file if cookie_file is not None else settings.COOKIES_FILE
        self._browser = browser if browser is not None else settings.BROWSER_COOKIES
        auto_extract = settings.AUTO_EXTRACT_COOKIES
        self._auto_extract = (
            auto_extract_cookies if auto_extract_cookies is not None else auto_extract
        )
        self._cache_hours = settings.COOKIE_CACHE_HOURS

    @staticmethod
    def _detect_js_runtime() -> str | None:
        """Detect available JavaScript runtime for yt-dlp signature and n-sig challenges."""
        for candidate in ("node", "deno", "bun", "quickjs"):
            if shutil.which(candidate):
                return candidate
        return None

    def _resolve_cookie_file(self, target_dir: Path) -> Path | None:
        """Resolves existing or extracted Netscape cookie file path."""
        if (
            self._cookie_file
            and self._cookie_file.exists()
            and self._cookie_file.stat().st_size > 0
        ):
            return self._cookie_file

        if not self._auto_extract:
            return None

        # Default cached cookie path in workspace data or output dir
        candidate_cache = Path("./data/cookies.txt").resolve()
        return ensure_cookies_file(
            output_file=candidate_cache,
            browser=self._browser,
            max_age_hours=self._cache_hours,
        )

    def download(self, url: str, output_dir: Path) -> tuple[Path, str, str]:
        """Downloads audio as 320 kbps MP3 and returns (file_path, video_id, title)."""
        try:
            import yt_dlp  # noqa: PLC0415
            from yt_dlp.utils import DownloadError, ExtractorError  # noqa: PLC0415
        except ImportError as err:
            raise RuntimeError(
                "yt-dlp is not installed in the active environment. Install with 'uv sync'."
            ) from err

        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        out_template = str(output_dir / "%(title)s.%(ext)s")
        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }

        # Inject cookie file if available
        cookie_path = self._resolve_cookie_file(output_dir)
        if cookie_path and cookie_path.exists() and cookie_path.stat().st_size > 0:
            ydl_opts["cookiefile"] = str(cookie_path)

        # Inject JavaScript runtime for YouTube n-sig / challenge solving
        js_runtime = self._detect_js_runtime()
        if js_runtime:
            runtime_cfg: dict[str, Any] = {}
            ydl_opts["js_runtimes"] = {js_runtime: runtime_cfg}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_id = str(info.get("id", "unknown_id"))
                title = str(info.get("title", "unknown_title"))
                filename = ydl.prepare_filename(info)
                audio_path = Path(filename).with_suffix(".mp3")
        except (DownloadError, ExtractorError) as exc:
            msg = str(exc)
            if "confirm you're not a bot" in msg or "confirm you" in msg or "bot" in msg.lower():
                err_detail = f"Ensure valid browser cookies are exported: {msg}"
                raise RuntimeError(
                    f"YouTube bot-detection challenge triggered. {err_detail}"
                ) from exc
            raise

        return audio_path, video_id, title
