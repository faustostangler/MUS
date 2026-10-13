"""Tests for MusSettings configuration validation."""

import pytest

from mus.config import MusSettings


def test_mus_settings_defaults_and_validation() -> None:
    """MusSettings should load valid defaults and enforce cross-field invariants."""
    settings = MusSettings()
    assert settings.SAMPLE_RATE == 44100
    assert settings.FRAME_PERIOD_MS == 5.0
    assert settings.F0_FLOOR_HZ < settings.F0_CEIL_HZ


def test_mus_settings_rejects_invalid_values() -> None:
    """Invalid configurations must fail fast."""
    with pytest.raises(ValueError):
        MusSettings(SAMPLE_RATE=22050)

    with pytest.raises(ValueError):
        MusSettings(F0_FLOOR_HZ=1000.0, F0_CEIL_HZ=500.0)

    with pytest.raises(ValueError):
        MusSettings(MAX_SEGMENT_SECONDS=-1.0)
