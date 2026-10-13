"""Domain and infrastructure telemetry and metrics collection (SPEC-001 Section 7)."""

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class MetricSummary:
    """Summary statistics for metric observations."""

    count: int = 0
    total: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")

    def observe(self, value: float) -> None:
        """Records a new observation."""
        self.count += 1
        self.total += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)

    @property
    def average(self) -> float:
        """Returns the mean value of observations."""
        return self.total / self.count if self.count > 0 else 0.0


class MetricsRegistry:
    """In-memory metrics collector for Prometheus Golden Signals and domain metrics."""

    def __init__(self) -> None:
        self.counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)
        self.gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self.histograms: dict[tuple[str, tuple[tuple[str, str], ...]], MetricSummary] = defaultdict(
            MetricSummary
        )

    def increment(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increments a counter metric."""
        lbl = tuple(sorted((labels or {}).items()))
        self.counters[(name, lbl)] += value

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Sets the current value of a gauge metric."""
        lbl = tuple(sorted((labels or {}).items()))
        self.gauges[(name, lbl)] = value

    def observe(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Records an observation into a histogram/summary metric."""
        lbl = tuple(sorted((labels or {}).items()))
        self.histograms[(name, lbl)].observe(value)

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> int:
        """Retrieves current counter value."""
        lbl = tuple(sorted((labels or {}).items()))
        return self.counters.get((name, lbl), 0)

    def get_gauge(self, name: str, labels: dict[str, str] | None = None) -> float | None:
        """Retrieves current gauge value."""
        lbl = tuple(sorted((labels or {}).items()))
        return self.gauges.get((name, lbl))

    def get_summary(self, name: str, labels: dict[str, str] | None = None) -> MetricSummary | None:
        """Retrieves observation summary for a histogram metric."""
        lbl = tuple(sorted((labels or {}).items()))
        return self.histograms.get((name, lbl))

    def reset(self) -> None:
        """Resets all metrics in registry."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()


_GLOBAL_REGISTRY = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    """Returns singleton metrics registry."""
    return _GLOBAL_REGISTRY
