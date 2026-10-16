"""Ollama LLM metadata tagger with deterministic heuristic fallback."""

import json
import re
import urllib.error
import urllib.request

from mus.stem_separation.application.ports import MetadataTaggerPort
from mus.stem_separation.domain.models import TrackMetadata


def parse_fallback_title(raw_title: str) -> TrackMetadata:
    """Extracts artist and track using regex heuristic cleaning."""
    clean = re.sub(
        r"[\(\[\{].*?(official|video|audio|lyrics|hd|4k|remastered|version).*?[\)\]\}]",
        "",
        raw_title,
        flags=re.IGNORECASE,
    ).strip()

    if " - " in clean:
        parts = clean.split(" - ", 1)
        artist = parts[0].strip()
        track = parts[1].strip()
    else:
        artist = "Unknown Artist"
        track = clean

    return TrackMetadata(
        video_id=re.sub(r"[^\w\-]", "_", raw_title)[:32],
        title=raw_title,
        artist=artist,
        track=track,
        genre="Other",
    )


class OllamaMetadataTagger(MetadataTaggerPort):
    """Tags musical tracks using Ollama LLM, falling back to heuristics."""

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "qwen2.5:latest",
        timeout: float = 120.0,
    ) -> None:
        self._host = ollama_host.rstrip("/")
        self._model = model
        self._timeout = timeout

    def tag(self, raw_title: str) -> TrackMetadata:
        """Queries Ollama for track metadata, with instant heuristic fallback."""
        prompt = (
            f"Analyze this music video title: '{raw_title}'. "
            "Output JSON only with keys 'artist', 'track', 'genre'. "
            'Example: {"artist": "Queen", "track": "Bohemian Rhapsody", "genre": "Rock"}'
        )
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{self._host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                response_text = result.get("response", "{}")
                parsed = json.loads(response_text)
                return TrackMetadata(
                    video_id=re.sub(r"[^\w\-]", "_", raw_title)[:32],
                    title=raw_title,
                    artist=parsed.get("artist", "Unknown Artist"),
                    track=parsed.get("track", raw_title),
                    genre=parsed.get("genre", "Other"),
                )
        except Exception:
            return parse_fallback_title(raw_title)

    def unload_vram(self) -> None:
        """Unloads the model from GPU VRAM via Ollama API and empties PyTorch CUDA cache."""
        payload = json.dumps(
            {
                "model": self._model,
                "keep_alive": 0,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{self._host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=3.0):
                pass
        except Exception:
            pass

        try:
            import torch  # noqa: PLC0415

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
