---
name: stripe-designer
description: Guide the user to design, specify, validate, and construct emblems, shields, and flags following the Stripe Design System Manual. Always use this skill when the user wants to create a visual identity, design a logo/flag/emblem, define corporate layouts/colors, or mentions the Stripe Design System, geometries, heraldic divisions, or custom visual branding.
---

# Stripe Design System: Emblem Designer Skill

Use this skill to guide the user in designing structurally sound, harmoniously colored, and accessible emblems, flags, or logos based on the **Stripe Design System Manual** (located at [stripe_design_system_manual.md](references/stripe_design_system_manual.md)).

---

## 1. The Operational Workflow

The design process must strictly follow a **two-phase workflow**:

1.  **Phase 1: The Grilling Session (Interactive Interview)**: You must ask the user targeted, step-by-step questions to determine the exact requirements of the emblem. You must resolve dependencies in order (e.g., color complexity depends on geometric complexity). Do not generate any code or visual layout until Phase 1 is complete and approved by the user.
2.  **Phase 2: Emblem Specification & Code Generation**: Generate the final design specification code, verification report (contrast, rules), and high-fidelity SVG code.

---

## 2. Phase 1: The Grilling Script (Step-by-Step Interview)

To avoid cognitive overload, **ask no more than 2-3 questions per turn**. Provide recommendations based on the brand context the user provides.

### Step 1: Bounded Context & Brand Identity
*   *Question 1*: What is the brand's primary industry, core purpose, and target audience?
*   *Question 2*: What are the primary values or duality of the brand (e.g., Security & Speed, Innovation & Heritage)?
*   *Recommendation*: If there is a strong duality, recommend using a heraldic division (e.g., `D-01 Per Pale`).

### Step 2: Heraldic Field Divisions & Geometries
*   *Question 3*: Should the background canvas be split into different fields or keep a single background?
    *   *Options*: Single Field (Solid) vs. Split Field (e.g., `D-01 Per Pale`, `D-02 Per Fess`, `D-03 Per Bend`, `D-04 Per Chevron`, `D-05 Per Saltire`, `D-06 Gyronny`, `D-07 Per Pall`).
*   *Question 4*: Which Stripe Geometry family aligns best with the brand's visual rhythm?
    *   *Options*:
        *   `V-Mono` (Vertical Monochromatic: height, structure, tech rhythm).
        *   `H-Mono` (Horizontal Monochromatic: landscape layers, stability).
        *   `C-Flag` (Chromatic Tri-Bands & Flags: high contrast, classic authority).
        *   `M-Seq` (Complex Asymmetric/Modulated Sequences: kinetic energy, mathematical progression, Fibonacci).
        *   *None* (Only field division and central charge).
*   *Question 5*: Which specific code from the manual will represent the geometry (e.g., `G-VM-02` Barcode, `G-MS-02-B` Nordic Cross, etc.)?

### Step 3: Boundaries, Diminutives & Curvatures
*   *Question 6*: What type of partition line defines the boundary between the stripes or fields?
    *   *Options*:
        *   `B-01 Straight` (Rigorous minimalism).
        *   `B-02 Wavy` (Fluidity, flow, frequency).
        *   `B-03 Indented` / `B-13 Dancetty` (Energy, power, peak spikes).
        *   `B-04 Embattled` / `B-12 Urdy` (Security, fortification, blocks).
        *   `B-08 Dovetailed` (Engineering, API sync, precision integration).
        *   *Other* (Nebuly, Engrailed, Invected, Raguly, Potenty/Trefly).
*   *Question 7*: Are there any secondary accent lines (Diminutives) or curvature modifications?
    *   *Options*: No Diminutives or Curvatures vs. specific codes (e.g., `G-DIM-03 Cotise` flanking a diagonal, `G-CURV-01 Arched` horizon, `G-CURV-03 Nowy` central dome).

### Step 4: Textures & Containers
*   *Question 8*: Does the background/stripe require a repeating geometric texture or fur?
    *   *Options*: Solid Fields vs. Heraldic Fur (e.g., `T-Fur-01 Ermine` for luxury, `T-Fur-02 Vair` for tiles, `T-Fur-03 Potent` for encryption/locks) vs. Field Variation (e.g., `T-Var-05 Chequy` chess matrix, `T-Var-11 Masoned` brickwork, `T-Var-12 Fretty` lattice).
*   *Question 9*: Does the emblem need a geometric container/frame to isolate the central charge?
    *   *Options*: No Frame vs. `F-01 Bordure` (outer border), `F-02 Orle` (inner floating frame), `F-03 Inescutcheon` (center shield).

### Step 5: Color Palette & Harmonies
*   *Question 10*: What type of color harmony should represent the brand?
    *   *Options*:
        *   `2-Color Hybrid` (1 Saturated Hue + 1 Achromatic neutral - maximum contrast).
        *   `2-Color Pure` (Monochromatic dark/light, Analogous, or Complementary).
        *   `3-Color Hybrid` (2 Saturated Hues + 1 Achromatic neutral).
        *   `3-Color Pure` (Triadic or Split-Complementary).
*   *Question 11*: What are the specific HSL color coordinates for the primary and secondary colors? (e.g., `hsl(210, 80%, 45%)` Steel Blue and `hsl(0, 0%, 100%)` White).

### Step 6: Central Iconographic Charge & LOD Rules
*   *Question 12*: What is the primary complex symbol/charge ($I$) for the emblem at large scales (LOD-1/LOD-2)? (e.g., Astrolabe, Double-Headed Eagle, Castle, Lion, Trident, Ouroboros).
*   *Question 13*: How should this charge behave at small scales (LOD-3, 16px to 32px)?
    *   *Options*:
        *   `Policy A (Omission)`: Set $I = \emptyset$ (omitted completely, rendering only stripes and colors).
        *   `Policy B (Geometric Primitive Substitution)`: Replaced 1:1 with an abstract geometric primitive (e.g., Eagle -> Greek Cross `G-MS-02-A`, Astrolabe -> Bezant `T-05`, Castle -> Billet, Lion -> Chevron `G-MS-03`).

---

## 3. The Design System Constraints & Validation

Before outputting any design or code, you must programmatically run a validation check against these three core rules of the manual:

1.  **The Rule of Tincture**: Saturated bands ($S \ge 50\%$) must be separated by a neutral buffer stripe ($S \le 10\%$, such as White, Light Grey, or Dark Slate) OR exhibit a lightness difference of $\Delta L \ge 40\%$ to prevent visual vibration.
2.  **WCAG 2.2 Compliance**: The contrast ratio between any overlaying components (e.g., the charge $I$ against its background field) must be at least **3:1** for graphical components (recommended **4.5:1**).
3.  **Mutual Complexity Exclusion Rule**:
    *   *High Geometry Complexity* (e.g., non-linear boundaries like Dovetailed, field patterns like Gyronny/Masoned) $\implies$ Color Palette **must** be restricted to Achromatic, Monochromatic, or Hybrid 2-Color.
    *   *High Color Complexity* (e.g., saturated Triadic or Complementary) $\implies$ Geometry **must** be restricted to Flat Straight Divisions (`B-01`) and simple symmetrical layouts (`G-VM-01`).

---

## 4. Phase 2: Expected Output Formats

Once the user approves the answers, generate the response in the following structured formats:

### 1. The Spec Code (Unified System Descriptor)
Provide a standardized code summarizing the design elements. Format:
`G-[GeometryCode]-[BoundaryCode]-D-[FieldDivisionCode]-T-[TextureCode]-F-[FrameCode]-P-[PaletteType]-[HSLCoords]-I-[ChargeCode]-[LOD3Policy]`

*Example*: `G-VM-02-B-08-D-01-T-Solid-F-02-P-Hybrid2-H210S80L45-I-Eagle-PolicyB`

### 2. Validation & Compliance Report
Present a table checking each rule:

| Constraint | Status | Details |
| :--- | :--- | :--- |
| **Rule of Tincture** | PASS / FAIL | [Details on adjacent saturation / light difference] |
| **WCAG 2.2 Contrast** | PASS / FAIL | [Luminance contrast ratio calculation, e.g. 5.2:1] |
| **Mutual Complexity Exclusion** | PASS / FAIL | [Check of complexity mapping] |
| **Gravitational Anchoring** | PASS / FAIL | [Left/Base weight check] |

### 3. Responsive SVG Code (LOD-1, LOD-2, LOD-3)
Generate a single responsive SVG file or three distinct SVG structures representing:
*   **LOD-1 (Majestic - Web)**: Full complex geometries, textured boundaries, highly detailed vector charge.
*   **LOD-2 (Graphic - Standard UI)**: 5-band limits, smoothed boundaries, flat silhouette charge (no interior details).
*   **LOD-3 (Symbolic - Favicon/16px)**: Capped at 3 stripes, flat boundaries (`B-01`), and either charge omission ($I = \emptyset$) or primitive substitution.
