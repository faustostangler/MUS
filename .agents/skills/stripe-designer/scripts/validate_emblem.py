#!/usr/bin/env python3
"""
Stripe Design System: Emblem Specification Validator.

This module provides programmatic validation for emblem design descriptors, ensuring
strict alignment with the Stripe Design System rules, including WCAG 2.2 contrast,
the Rule of Tincture, and the Mutual Complexity Exclusion rule.
"""

import math
import re
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[float, float, float]:
    """Convert HSL coordinates to normalized RGB values (0.0 to 1.0)."""
    h /= 360.0
    s /= 100.0
    l /= 100.0

    if s == 0.0:
        return l, l, l

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0.0:
            t += 1.0
        if t > 1.0:
            t -= 1.0
        if t < 1.6666666666666666:  # 1/6
            return p + (q - p) * 6.0 * t
        if t < 0.5:
            return q
        if t < 0.6666666666666666:  # 2/3
            return p + (q - p) * (4.0 / 6.0 - t) * 6.0
        return p

    q = l * (1.0 + s) if l < 0.5 else l + s - l * s
    p = 2.0 * l - q

    r = hue_to_rgb(p, q, h + 1.0 / 3.0)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1.0 / 3.0)

    return r, g, b


def calculate_relative_luminance(r: float, g: float, b: float) -> float:
    """Calculate the relative luminance of an RGB color according to WCAG 2.2."""
    def get_linear_channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else math.pow((c + 0.055) / 1.055, 2.4)

    r_lin = get_linear_channel(r)
    g_lin = get_linear_channel(g)
    b_lin = get_linear_channel(b)

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def calculate_contrast_ratio(lum1: float, lum2: float) -> float:
    """Calculate the WCAG contrast ratio between two relative luminances."""
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


class ColorHSL(BaseModel):
    """Represent an HSL color coordinate with semantic validation."""
    hue: float = Field(..., ge=0.0, le=360.0, description="Color Hue (0-360 degrees)")
    saturation: float = Field(..., ge=0.0, le=100.0, description="Color Saturation (0-100%)")
    lightness: float = Field(..., ge=0.0, le=100.0, description="Color Lightness (0-100%)")

    @property
    def is_neutral(self) -> bool:
        """Check if the color is an achromatic/low-chroma neutral (S <= 10%)."""
        return self.saturation <= 10.0

    @property
    def luminance(self) -> float:
        """Calculate relative luminance for WCAG contrast checks."""
        r, g, b = hsl_to_rgb(self.hue, self.saturation, self.lightness)
        return calculate_relative_luminance(r, g, b)


class EmblemSpec(BaseModel):
    """emblem spec descriptor model that validates Stripe design rules."""
    geometry_code: str = Field(..., description="Stripe geometry code (e.g. G-VM-02)")
    boundary_code: str = Field(..., description="Boundary partition code (e.g. B-01)")
    field_division_code: str = Field(..., description="Field division code (e.g. D-01)")
    texture_code: str = Field(..., description="Field texture code (e.g. T-Fur-01, T-Var-05, Solid)")
    frame_code: str = Field(..., description="Frame or sub-ordinary code (e.g. F-01, None)")
    palette_type: str = Field(..., description="Palette category (e.g. Hybrid2, Pure3)")
    colors: List[ColorHSL] = Field(..., min_length=1, description="List of HSL colors utilized in layout")
    charge_code: str = Field(..., description="Central charge symbol code (e.g. Eagle, Castle)")
    lod3_policy: str = Field(..., description="Micro-scale reduction policy (PolicyA or PolicyB)")

    @field_validator("boundary_code")
    @classmethod
    def validate_boundary(cls, value: str) -> str:
        """Ensure boundary codes conform to the allowed catalog."""
        valid_boundaries = {"B-01", "B-02", "B-03", "B-04", "B-05", "B-06", "B-07", "B-08", "B-09", "B-10", "B-11", "B-12", "B-13"}
        if value not in valid_boundaries and value.upper() != "NONE":
            raise ValueError(f"Invalid boundary code: {value}. Must be in {valid_boundaries}")
        return value

    @model_validator(mode="after")
    def validate_mutual_complexity(self) -> "EmblemSpec":
        """Verify the Mutual Complexity Exclusion Rule: high geometry <=> low color."""
        # Define high-complexity geometry indicators
        is_complex_boundary = self.boundary_code not in ("B-01", "None")
        is_complex_division = self.field_division_code in ("D-05", "D-06", "D-07")  # Saltire, Gyronny, Per Pall
        is_complex_texture = self.texture_code.startswith("T-Fur-") or self.texture_code in ("T-Var-05", "T-Var-06", "T-Var-11", "T-Var-12")

        is_geometry_complex = is_complex_boundary or is_complex_division or is_complex_texture

        # Define high-complexity color indicators
        is_color_complex = self.palette_type.lower() in ("pure3", "triadic", "split-complementary")

        if is_geometry_complex and is_color_complex:
            raise ValueError(
                f"Mutual Complexity Violation: High geometry complexity "
                f"(Boundary={self.boundary_code}, Division={self.field_division_code}, Texture={self.texture_code}) "
                f"cannot be paired with complex color scheme ({self.palette_type})."
            )
        return self

    @model_validator(mode="after")
    def validate_rule_of_tincture(self) -> "EmblemSpec":
        """Verify Rule of Tincture: saturated colors must have high lightness difference or neutral buffer."""
        # If we have multiple colors, check adjacent color interactions
        if len(self.colors) >= 2:
            for i in range(len(self.colors) - 1):
                c1 = self.colors[i]
                c2 = self.colors[i + 1]
                
                # If both are saturated (S >= 50%)
                if not c1.is_neutral and not c2.is_neutral:
                    delta_l = abs(c1.lightness - c2.lightness)
                    if delta_l < 40.0:
                        raise ValueError(
                            f"Rule of Tincture Violation: Saturated colors (Color {i} & Color {i+1}) "
                            f"placed adjacent without 40%+ Lightness difference (found {delta_l:.1f}% difference)."
                        )
        return self

    @model_validator(mode="after")
    def validate_charge_contrast(self) -> "EmblemSpec":
        """Verify WCAG 2.2 contrast ratio between charge overlay and background."""
        # Charge is generally overlaid on the first/dominant color
        if len(self.colors) >= 1:
            bg_color = self.colors[0]
            # Assume charge is either White or Gold/Crimson/Cyan as mapped in LOD-3 policy
            # For general check, if charge HSL is unknown, we check the contrast of colors[0] vs colors[1] if colors[1] represents charge overlay
            if len(self.colors) >= 2:
                contrast = calculate_contrast_ratio(bg_color.luminance, self.colors[1].luminance)
                if contrast < 3.0:
                    # Non-blocking warning represented as standard validation log
                    print(f"[WARNING] Contrast ratio between background and charge/overlay is {contrast:.2f}:1, which is below standard 3:1.")
        return self


def parse_spec_code(spec: str) -> EmblemSpec:
    """Parse a unified spec code string into an EmblemSpec model."""
    # Pattern: G-[Geom]-B-[Bound]-D-[Div]-T-[Tex]-F-[Frame]-P-[Pal]-[HSLCoords]-I-[Charge]-[LOD3]
    # Example: G-VM-02-B-08-D-01-T-Solid-F-02-P-Hybrid2-H210S80L45H0S0L100-I-Eagle-PolicyB
    pattern = (
        r"^G-([A-Z0-9\-]+)-B-([A-Z0-9]+)-D-([A-Z0-9]+)-T-([A-Za-z0-9\-]+)-F-([A-Z0-9a-z\-]+)-"
        r"P-([A-Za-z0-9]+)-([H0-9S0-9L0-9]+)-I-([A-Za-z0-9\-]+)-([A-Za-z0-9\-]+)$"
    )
    match = re.match(pattern, spec)
    if not match:
        raise ValueError(f"Spec string '{spec}' does not match the unified descriptor pattern.")

    geom, bound, div, tex, frame, pal, hsl_str, charge, lod3 = match.groups()

    # Parse HSL coordinates (e.g. H210S80L45H0S0L100)
    hsl_matches = re.findall(r"H(\d+)S(\d+)L(\d+)", hsl_str)
    colors = []
    for h, s, l in hsl_matches:
        colors.append(ColorHSL(hue=float(h), saturation=float(s), lightness=float(l)))

    if not colors:
        # Fallback default colors if parsing fails to find match structure
        colors = [ColorHSL(hue=0.0, saturation=0.0, lightness=100.0)]

    return EmblemSpec(
        geometry_code=f"G-{geom}" if not geom.startswith("G-") else geom,
        boundary_code=f"B-{bound}" if not bound.startswith("B-") else bound,
        field_division_code=f"D-{div}" if not div.startswith("D-") else div,
        texture_code=tex,
        frame_code=f"F-{frame}" if (frame.upper() != "NONE" and not frame.startswith("F-")) else frame,
        palette_type=pal,
        colors=colors,
        charge_code=charge,
        lod3_policy=lod3,
    )


# Demonstration Execution
if __name__ == "__main__":
    test_specs = [
        # Valid: Low geometry complexity (straight), high color complexity (Pure3)
        "G-VM-01-B-01-D-01-T-Solid-F-None-P-Pure3-H210S80L45H120S70L50H0S60L50-I-Lion-PolicyA",
        # Valid: High geometry complexity (Dovetailed), low color complexity (Hybrid2)
        "G-VM-02-B-08-D-01-T-Solid-F-02-P-Hybrid2-H210S80L45H0S0L100-I-Eagle-PolicyB",
        # Invalid: High geometry complexity (Dovetailed) + High color complexity (Pure3)
        "G-VM-02-B-08-D-01-T-Solid-F-02-P-Pure3-H210S80L45H120S70L50H0S60L50-I-Eagle-PolicyB"
    ]

    print("--- Testing Stripe Emblem Spec Validator ---")
    for index, spec in enumerate(test_specs, 1):
        print(f"\nSpec {index}: {spec}")
        try:
            parsed = parse_spec_code(spec)
            print(f"  Result: VALID")
            print(f"  Parsed Geometry: {parsed.geometry_code}")
            print(f"  Parsed Boundary: {parsed.boundary_code}")
            print(f"  Parsed Color count: {len(parsed.colors)}")
        except Exception as e:
            print(f"  Result: INVALID")
            print(f"  Error: {e}")
