"""Unit tests for Observability telemetry and metrics collection (SPEC-001 Section 7)."""

import pytest

from mus.observability.telemetry import MetricsRegistry, get_metrics_registry


class TestObservabilityTelemetry:
    """Verifies in-memory metrics registry for Golden Signals."""

    def test_counter_increments_and_labels(self) -> None:
        """Counters record stage outcomes with labels."""
        registry = MetricsRegistry()
        registry.increment(
            "mus_takes_processed_total", labels={"stage": "decompose", "outcome": "success"}
        )
        registry.increment(
            "mus_takes_processed_total", labels={"stage": "decompose", "outcome": "success"}
        )
        registry.increment(
            "mus_takes_processed_total", labels={"stage": "decompose", "outcome": "failure"}
        )

        assert (
            registry.get_counter(
                "mus_takes_processed_total", labels={"stage": "decompose", "outcome": "success"}
            )
            == 2
        )
        assert (
            registry.get_counter(
                "mus_takes_processed_total", labels={"stage": "decompose", "outcome": "failure"}
            )
            == 1
        )
        assert (
            registry.get_counter(
                "mus_takes_processed_total", labels={"stage": "render", "outcome": "success"}
            )
            == 0
        )

    def test_gauge_recording(self) -> None:
        """Gauges record floating point values like voiced_ratio and peak level."""
        registry = MetricsRegistry()
        registry.set_gauge("mus_voiced_ratio", 0.852)
        registry.set_gauge("mus_peak_level_dbfs", -1.0)

        assert registry.get_gauge("mus_voiced_ratio") == pytest.approx(0.852)
        assert registry.get_gauge("mus_peak_level_dbfs") == pytest.approx(-1.0)
        assert registry.get_gauge("unknown_metric") is None

    def test_summary_duration_observations(self) -> None:
        """Histograms/summaries compute count, total, average, min, and max."""
        registry = MetricsRegistry()
        registry.observe("mus_stage_duration_seconds", 0.12, labels={"stage": "transcribe"})
        registry.observe("mus_stage_duration_seconds", 0.28, labels={"stage": "transcribe"})

        summary = registry.get_summary("mus_stage_duration_seconds", labels={"stage": "transcribe"})
        assert summary is not None
        assert summary.count == 2
        assert summary.total == pytest.approx(0.40)
        assert summary.average == pytest.approx(0.20)
        assert summary.min == pytest.approx(0.12)
        assert summary.max == pytest.approx(0.28)

    def test_global_singleton_reset(self) -> None:
        """Global registry maintains state and can be reset."""
        reg = get_metrics_registry()
        reg.increment("test_counter", 5)
        assert reg.get_counter("test_counter") >= 5
        reg.reset()
        assert reg.get_counter("test_counter") == 0
