"""Audio downloader adapter utilizing yt-dlp."""

from pathlib import Path
from typing import Any

from mus.stem_separation.application.ports import AudioDownloaderPort


class YtDlpAudioDownloader(AudioDownloaderPort):
    """Downloads audio tracks using yt-dlp."""

    def download(self, url: str, output_dir: Path) -> tuple[Path, str, str]:
        """Downloads audio as 320 kbps MP3 and returns (file_path, video_id, title)."""
        try:
            import yt_dlp  # noqa: PLC0415
        except ImportError as err:
            raise RuntimeError(
                "yt-dlp is not installed in the active environment. "
                "Install with 'uv sync --extra legacy'."
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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = str(info.get("id", "unknown_id"))
            title = str(info.get("title", "unknown_title"))
            filename = ydl.prepare_filename(info)
            audio_path = Path(filename).with_suffix(".mp3")

        return audio_path, video_id, title
