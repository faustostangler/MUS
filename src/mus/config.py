from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MusSettings(BaseSettings):
    """Global system configuration adhering to 12-Factor App and fail-fast validation."""

    model_config = SettingsConfigDict(
        env_prefix="MUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LIBRARY_DIR: Path = Path("./outputs/library")
    HISTORY_FILE: Path = Path("./data/history.json")
    PLAYLIST_FILE: Path = Path(__file__).resolve().parent / "data" / "playlist.txt"
    OUTPUT_DIR: Path = Path("./outputs")

    SAMPLE_RATE: int = 44100
    FRAME_PERIOD_MS: float = 5.0
    F0_ESTIMATOR: str = "dio"
    F0_FLOOR_HZ: float = 65.0
    F0_CEIL_HZ: float = 1100.0

    MAX_SEGMENT_SECONDS: float = 30.0
    SILENCE_DBFS: float = -50.0
    WORKERS: int = 1

    SOUNDFONT_PATH: Path = Path("/usr/share/sounds/sf2/FluidR3_GM.sf2")
    FLUIDSYNTH_BIN: str = "fluidsynth"
    MUSESCORE_BIN: str = "musescore"

    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:latest"

    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def validate_invariants(self) -> "MusSettings":
        """Validates configuration consistency at startup."""
        if self.SAMPLE_RATE not in (44100, 48000):
            raise ValueError(f"SAMPLE_RATE must be 44100 or 48000, got {self.SAMPLE_RATE}.")

        if not (self.F0_FLOOR_HZ < self.F0_CEIL_HZ):
            raise ValueError(
                f"F0_FLOOR_HZ ({self.F0_FLOOR_HZ}) must be < F0_CEIL_HZ ({self.F0_CEIL_HZ})."
            )

        if self.MAX_SEGMENT_SECONDS <= 0:
            raise ValueError("MAX_SEGMENT_SECONDS must be positive.")

        return self


@lru_cache(maxsize=1)
def get_settings() -> MusSettings:
    """Returns the cached singleton instance of MusSettings."""
    return MusSettings()
