#!/usr/bin/env python3
"""
Stripe Design System: SVG Asset Generator.

This script outputs three levels of detail (LOD-1, LOD-2, LOD-3) for both
the shield-shaped emblem and the vertical flag on a Deep Green and White field.
"""

import os

# Define color hexes corresponding to the HSL values
GREEN_HEX = "#0f3d27"  # hsl(150, 60%, 15%) - Dark Emerald
GOLD_HEX = "#e6b831"   # hsl(45, 80%, 55%) - Warm Gold
WHITE_HEX = "#ffffff"  # hsl(0, 0%, 100%) - Pure White
SLATE_HEX = "#4d6673"  # hsl(210, 20%, 38%) - Dark Slate

# --- SHIELD EMBLEM SVGs ---

SHIELD_LOD1 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <!-- Heater Shield Base Canvas -->
  <path d="M 256, 32 C 384, 32 448, 64 448, 128 C 448, 288 384, 416 256, 480 C 128, 416 64, 288 64, 128 C 64, 64 128, 32 256, 32 Z" fill="{GREEN_HEX}" stroke="{GOLD_HEX}" stroke-width="4"/>

  <!-- LOD-1: Majestic Level Bionic Features (Microchip Circuit Traces) -->
  <g stroke="{GOLD_HEX}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.85">
    <!-- Left PCB traces -->
    <path d="M 128, 256 H 90 L 70, 236 H 50" />
    <path d="M 128, 256 H 100 L 80, 276 H 55" />
    <circle cx="50" cy="236" r="4" fill="{GOLD_HEX}" stroke="none"/>
    <circle cx="55" cy="276" r="4" fill="{GOLD_HEX}" stroke="none"/>

    <!-- Right PCB traces -->
    <path d="M 384, 256 H 422 L 442, 236 H 462" />
    <path d="M 384, 256 H 412 L 432, 276 H 457" />
    <circle cx="462" cy="236" r="4" fill="{GOLD_HEX}" stroke="none"/>
    <circle cx="457" cy="276" r="4" fill="{GOLD_HEX}" stroke="none"/>

    <!-- Scanning Reticle Rings -->
    <circle cx="256" cy="256" r="110" stroke="{GOLD_HEX}" stroke-dasharray="8 6" stroke-width="1.5"/>
    <circle cx="256" cy="256" r="92" stroke="{WHITE_HEX}" stroke-dasharray="2 4" stroke-width="2" opacity="0.6"/>
  </g>

  <!-- Eye Sclera (White base shape) -->
  <path d="M 128, 256 C 128, 256 192, 160 256, 160 C 320, 160 384, 256 384, 256 C 384, 256 320, 352 256, 352 C 192, 352 128, 256 128, 256 Z" fill="{WHITE_HEX}" stroke="{GOLD_HEX}" stroke-width="4"/>

  <!-- Iris (Gold circular body representing the bionic camera sensor) -->
  <circle cx="256" cy="256" r="64" fill="{GOLD_HEX}" stroke="{SLATE_HEX}" stroke-width="3"/>

  <!-- Microchip Pins on Iris Edge -->
  <g stroke="{SLATE_HEX}" stroke-width="2" opacity="0.75">
    <line x1="256" y1="192" x2="256" y2="198"/>
    <line x1="256" y1="320" x2="256" y2="314"/>
    <line x1="192" y1="256" x2="198" y2="256"/>
    <line x1="320" y1="256" x2="314" y2="256"/>
    <line x1="211" y1="211" x2="216" y2="216"/>
    <line x1="301" y1="301" x2="296" y2="296"/>
    <line x1="211" y1="301" x2="216" y2="296"/>
    <line x1="301" y1="211" x2="296" y2="216"/>
  </g>

  <!-- Pupil (Dark Slate central core) -->
  <circle cx="256" cy="256" r="32" fill="{SLATE_HEX}"/>

  <!-- Central Medical Greek Cross (Achromatic White for maximum contrast and clinical signifier) -->
  <path d="M 251, 240 H 261 V 251 H 272 V 261 H 261 V 272 H 251 V 261 H 240 V 251 H 251 Z" fill="{WHITE_HEX}"/>
</svg>
"""

SHIELD_LOD2 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <!-- Heater Shield Base Canvas -->
  <path d="M 256, 32 C 384, 32 448, 64 448, 128 C 448, 288 384, 416 256, 480 C 128, 416 64, 288 64, 128 C 64, 64 128, 32 256, 32 Z" fill="{GREEN_HEX}" stroke="{GOLD_HEX}" stroke-width="4"/>

  <!-- LOD-2: Simplified Circuit Lines -->
  <g stroke="{GOLD_HEX}" stroke-width="4" fill="none" stroke-linecap="round">
    <path d="M 128, 256 H 60" />
    <path d="M 384, 256 H 452" />
  </g>

  <!-- Eye Shape -->
  <path d="M 128, 256 C 128, 256 192, 164 256, 164 C 320, 164 384, 256 384, 256 C 384, 256 320, 348 256, 348 C 192, 348 128, 256 128, 256 Z" fill="{WHITE_HEX}" stroke="{GOLD_HEX}" stroke-width="4"/>

  <!-- Iris -->
  <circle cx="256" cy="256" r="60" fill="{GOLD_HEX}"/>

  <!-- Pupil -->
  <circle cx="256" cy="256" r="28" fill="{SLATE_HEX}"/>

  <!-- Medical Cross -->
  <path d="M 252, 242 H 260 V 252 H 270 V 260 H 260 V 270 H 252 V 260 H 242 V 252 H 252 Z" fill="{WHITE_HEX}"/>
</svg>
"""

SHIELD_LOD3 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="100%" height="100%">
  <!-- Background Canvas Shield (Simplified for 32px viewport) -->
  <path d="M 16, 2 C 24, 2 28, 4 28, 8 C 28, 18 24, 26 16, 30 C 8, 26 4, 18 4, 8 C 4, 4 8, 2 16, 2 Z" fill="{GREEN_HEX}"/>

  <!-- LOD-3: Geometric Primitive Substitution (Bezant/Circle representing eye, in Gold) -->
  <circle cx="16" cy="16" r="7" fill="{GOLD_HEX}"/>

  <!-- Nested White Circle for Contrast -->
  <circle cx="16" cy="16" r="4.5" fill="{WHITE_HEX}"/>

  <!-- Micro-scale Greek Cross in Green for core health identifier -->
  <path d="M 15, 13 H 17 V 15 H 19 V 17 H 17 V 19 H 15 V 17 H 13 V 15 H 15 Z" fill="{GREEN_HEX}"/>
</svg>
"""

# --- VERTICAL FLAG SVGs (G-CF-01) ---

FLAG_LOD1 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" height="100%">
  <!-- G-CF-01 vertical bands (20% Green, 60% White, 20% Green) -->
  <rect x="0" y="0" width="160" height="500" fill="{GREEN_HEX}"/>
  <rect x="160" y="0" width="480" height="500" fill="{WHITE_HEX}"/>
  <rect x="640" y="0" width="160" height="500" fill="{GREEN_HEX}"/>

  <!-- Metal Gold lines separating Green and White fields (8px width for prominent separation) -->
  <rect x="156" y="0" width="8" height="500" fill="{GOLD_HEX}"/>
  <rect x="636" y="0" width="8" height="500" fill="{GOLD_HEX}"/>

  <!-- LOD-1: Majestic Level Bionic Features (Green circuit traces on White field with Gold pads) -->
  <g stroke="{GREEN_HEX}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.9">
    <!-- Left PCB traces extending from the Cross -->
    <path d="M 310, 220 H 260 L 240, 200 H 200" />
    <path d="M 310, 280 H 260 L 240, 300 H 200" />
    <!-- Left trace pads (vias in Gold) -->
    <circle cx="200" cy="200" r="4.5" fill="{GOLD_HEX}" stroke="none"/>
    <circle cx="200" cy="300" r="4.5" fill="{GOLD_HEX}" stroke="none"/>

    <!-- Right PCB traces extending from the Cross -->
    <path d="M 490, 220 H 540 L 560, 200 H 600" />
    <path d="M 490, 280 H 540 L 560, 300 H 600" />
    <!-- Right trace pads (vias in Gold) -->
    <circle cx="600" cy="200" r="4.5" fill="{GOLD_HEX}" stroke="none"/>
    <circle cx="600" cy="300" r="4.5" fill="{GOLD_HEX}" stroke="none"/>

    <!-- Scanning Reticle Rings in Green/Gold -->
    <circle cx="400" cy="250" r="120" stroke="{GOLD_HEX}" stroke-dasharray="6 4" stroke-width="1.5" />
    <circle cx="400" cy="250" r="100" stroke="{GREEN_HEX}" stroke-dasharray="2 2" stroke-width="1.5" opacity="0.6" />
  </g>

  <!-- Central Charge: Stylized Bionic Greek Cross (Yellow/Gold body with Deep Green outline for high contrast) -->
  <path d="M 370, 160 H 430 V 220 H 490 V 280 H 430 V 340 H 370 V 280 H 310 V 220 H 370 Z" fill="{GOLD_HEX}" stroke="{GREEN_HEX}" stroke-width="5" stroke-linejoin="round"/>

  <!-- Microchip CPU Central Hub inside the Cross (Green Circle) -->
  <circle cx="400" cy="250" r="20" fill="{GREEN_HEX}" stroke="{GOLD_HEX}" stroke-width="2"/>
  <circle cx="400" cy="250" r="12" fill="{GOLD_HEX}"/>
  <circle cx="400" cy="250" r="4" fill="{WHITE_HEX}"/>

  <!-- Central Hub Connections (Microchip Pins in Gold) -->
  <g stroke="{GOLD_HEX}" stroke-width="2" opacity="0.8">
    <line x1="400" y1="220" x2="400" y2="230"/>
    <line x1="400" y1="280" x2="400" y2="270"/>
    <line x1="370" y1="250" x2="380" y2="250"/>
    <line x1="430" y1="250" x2="420" y2="250"/>
  </g>
</svg>
"""

FLAG_LOD2 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="100%" height="100%">
  <!-- G-CF-01 vertical bands -->
  <rect x="0" y="0" width="160" height="500" fill="{GREEN_HEX}"/>
  <rect x="160" y="0" width="480" height="500" fill="{WHITE_HEX}"/>
  <rect x="640" y="0" width="160" height="500" fill="{GREEN_HEX}"/>

  <!-- Metal Gold lines separating Green and White fields -->
  <rect x="157" y="0" width="6" height="500" fill="{GOLD_HEX}"/>
  <rect x="637" y="0" width="6" height="500" fill="{GOLD_HEX}"/>

  <!-- LOD-2: Simplified PCB trace lines -->
  <g stroke="{GREEN_HEX}" stroke-width="4" fill="none" stroke-linecap="round">
    <path d="M 310, 250 H 210" />
    <path d="M 490, 250 H 590" />
  </g>

  <!-- Central Cross (Yellow/Gold with Green stroke) -->
  <path d="M 370, 160 H 430 V 220 H 490 V 280 H 430 V 340 H 370 V 280 H 310 V 220 H 370 Z" fill="{GOLD_HEX}" stroke="{GREEN_HEX}" stroke-width="5" stroke-linejoin="round"/>

  <!-- Center green pin circle -->
  <circle cx="400" cy="250" r="12" fill="{GREEN_HEX}"/>
</svg>
"""

FLAG_LOD3 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="100%" height="100%">
  <!-- Vertical Flag Layout for 32px -->
  <rect x="0" y="0" width="6" height="32" fill="{GREEN_HEX}"/>
  <rect x="6" y="0" width="20" height="32" fill="{WHITE_HEX}"/>
  <rect x="26" y="0" width="6" height="32" fill="{GREEN_HEX}"/>

  <!-- Metal Gold lines separating Green and White fields -->
  <rect x="5" y="0" width="1" height="32" fill="{GOLD_HEX}"/>
  <rect x="26" y="0" width="1" height="32" fill="{GOLD_HEX}"/>

  <!-- LOD-3: Geometric Primitive Substitution (Green circle representing eye/cross container) -->
  <circle cx="16" cy="16" r="7" fill="{GREEN_HEX}"/>

  <!-- Yellow/Gold medical cross inside the green circle -->
  <path d="M 15, 12 H 17 V 15 H 20 V 17 H 17 V 20 H 15 V 17 H 12 V 15 H 15 Z" fill="{GOLD_HEX}"/>
</svg>
"""

def main():
    output_dir = "/home/stangler/gamer_d/Fausto Stangler/Documentos/Python/PES/playground/stripes"
    os.makedirs(output_dir, exist_ok=True)

    # Write Emblem SVGs
    with open(os.path.join(output_dir, "emblem_lod1.svg"), "w") as f:
        f.write(SHIELD_LOD1.strip())
    with open(os.path.join(output_dir, "emblem_lod2.svg"), "w") as f:
        f.write(SHIELD_LOD2.strip())
    with open(os.path.join(output_dir, "emblem_lod3.svg"), "w") as f:
        f.write(SHIELD_LOD3.strip())

    # Write Flag SVGs
    with open(os.path.join(output_dir, "flag_lod1.svg"), "w") as f:
        f.write(FLAG_LOD1.strip())
    with open(os.path.join(output_dir, "flag_lod2.svg"), "w") as f:
        f.write(FLAG_LOD2.strip())
    with open(os.path.join(output_dir, "flag_lod3.svg"), "w") as f:
        f.write(FLAG_LOD3.strip())

    print(f"Successfully generated LOD-1, LOD-2, and LOD-3 SVGs for Emblem & Flag in {output_dir}")

if __name__ == "__main__":
    main()
