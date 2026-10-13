"""Backward compatibility re-export for FluidSynthCliRenderer (ADR-001 D2).

Moved to `mus.instrument_rendering.infrastructure.fluidsynth_cli_renderer`.
"""

from mus.instrument_rendering.infrastructure.fluidsynth_cli_renderer import (
    FluidSynthCliRenderer,
)

__all__ = ["FluidSynthCliRenderer"]
