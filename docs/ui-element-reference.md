# Enthermal™ Configurator — UI Element Reference Guide — REV7

---

## Header Bar

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Logo | Official LuxWall SVG logo (white on dark background) | `.header svg` |
| Product Badge | "Product Configurator" pill badge | `.header-badge` |

## Hero Section

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Hero Title | Configure Your Enthermal™ *Transparent Insulation* | `.hero h1` |
| Hero Subtitle | Description text below the title | `.hero-sub` |

---

## Config Panel (Left Column)

### Product Tabs

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Product Tabs | Enthermal™ / Enthermal Plus™ / Enthermal Spandrel tabs | `.product-tab` |

### Config Panel — Enthermal™

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Outboard Section | Section header for outboard glass settings | `.config-section-label` |
| Thickness Radios (Outer) | 4mm / 5mm / 6mm radio buttons for outer lite | `input[name='outerThickness']` |
| Low-E Coating Dropdown | Combined coating + substrate color dropdown (e.g., "Cardinal LoE3-366 on Clear") | `#outerCoating` |
| Gap Section | Vacuum indicator with green pulsing dot | `.vacuum-indicator` |
| Vacuum Text | 0.25 mm — Sealed vacuum | `.vacuum-text` |
| Inboard Section | Section header for inboard glass settings | `.config-section-label` |
| Thickness Radios (Inner) | 4mm / 5mm / 6mm radio buttons for inner lite | `input[name='innerThickness']` |

### Config Panel — Enthermal Plus™

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Enthermal Placement Toggle | Inboard / Outboard slider toggle | `#posToggle`, `#posToggleInput` |
| Inboard Label | "Inboard" text left of placement toggle | `#posLabelInboard` |
| Outboard Label | "Outboard" text right of placement toggle | `#posLabelOutboard` |
| Glass Section Label | Dynamic label ("Outboard" or "Inboard" based on placement) | `#plusGlassLabel` |
| Outer Thickness Radios | 4mm / 5mm / 6mm (availability depends on data; some coatings restrict to 6mm only) | `input[name='plusOuterThickness']`, IDs: `plusOuterT4`, `plusOuterT5`, `plusOuterT6` |
| Outer Low-E Coating | Outer coating dropdown (S2 surface). Values are bare shortcodes (e.g., `"C366"`) | `#plusOuterCoating` |
| Gap Fill Toggle | 90% Argon / 100% Air slider toggle | `#gapToggle`, `#gapToggleInput` |
| Argon Label | "Argon" text left of gas toggle | `#gapLabelArgon` |
| Air Label | "Air" text right of gas toggle | `#gapLabelAir` |
| Enthermal Section Label | "Enthermal" section header | `.config-section-label` |
| VIG Thickness Dropdown | VIG glass thickness: 4/4, 5/4, 5/5, 6/5, 6/6 mm | `#plusVigThickness` |
| VIG Low-E Coating | Enthermal VIG coating dropdown | `#plusVigCoating` |
| Coating Surface Toggle | S4 (Middle) / S5 (Inboard) slider toggle. Disabled and forced to S5 in Outboard mode. | `#srfToggle`, `#srfToggleInput` |
| S4 Label | "Middle (S4)" text left of toggle | `#srfLabelS4` |
| S5 Label | "Inboard (S5)" text right of toggle | `#srfLabelS5` |
| Toggle Thumb | Teal circular sliding indicator | `#srfThumb` |
| Coating Surface Field | Container for S4/S5 toggle — hidden in Outboard mode | `#plusCoatingSurfaceField` |
| Hidden Radios | Hidden radio inputs synced by the surface toggle | `#plusSrf4` (S4), `#plusSrf5` (S5), `name='plusCoatingSurface'` |

---

## Config Summary & Standards

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Summary Text | Full configuration description | `#summaryText` |
| Standard Toggle | NFRC / CEN sliding toggle | `#stdToggle`, `#stdToggleInput` |
| NFRC Label | NFRC option in toggle | `#stdOptISO` |
| CEN Label | CEN option in toggle | `#stdOptCEN` |
| Toggle Thumb | Teal sliding pill indicator | `#stdThumb` |
| Download Button | Print/download button with icon | `#printBtn` |

### Summary Text Formats

**Enthermal™:**
`<strong>[coating display]</strong> on <strong>[outerMM]mm</strong> outboard and <strong>Clear [innerMM]mm</strong> inboard.`
Example: **LoE³ 366** on **6mm** outboard and **Clear 6mm** inboard.

**Enthermal Plus™ — Inboard:**
`<strong>[S2 display]</strong> (S2) on <strong>[monoMM]mm</strong> with <strong>[vigCombo] mm</strong> Enthermal <strong>[secondCoating]</strong> ([surface]) inboard`
Example: **LoE³ 366** (S2) on **4mm** with **4/4 mm** Enthermal **LoE³ 366** (S4) inboard

**Enthermal Plus™ — Outboard:**
`<strong>[vigCombo] mm</strong> Enthermal <strong>[S2 display]</strong> (S2) outboard with <strong>[secondCoating]</strong> (S5) on <strong>[monoMM]mm</strong>`
Example: **5/5 mm** Enthermal **LoE³ 366** (S2) outboard with **LoE³ 366** (S5) on **4mm**

---

## Value Cards (Metrics Bar)

| Element | Description | CSS / ID |
|---------|-------------|----------|
| U-Value Card | Dual-value card: U-Value (SI) left, U-Factor (IP) right | `.metric-card` (1st) |
| U-Value (SI) | Value in W/m²·K | `#metricU` |
| U-Factor (IP) | Value in Btu/hr·ft²·°F — shows "—" in CEN mode | `#metricUIP` |
| U-Factor Section | Container for U-Factor label, value, unit | `#uFactorSection` |
| R-Value / SHGC Card | Dual-value card: R-value left, SHGC right | `.metric-card` (2nd) |
| R-Value | Insulation value — shows "—" in CEN mode | `#metricR` |
| R-Value Section | Container for R-Value label, value, unit | `#rValueSection` |
| SHGC | Solar Heat Gain Coefficient (relabeled "g-factor" in CEN) | `#metricSHGC` |
| SHGC Label | "SHGC" or "g-factor" (CEN) | `#shgcLabel` |
| SHGC Unit | "Solar Heat Gain" or "Solar Factor" (CEN) | `#shgcUnit` |
| Tvis / Rout,vis / TUV | Triple-value card: transmittance, reflectance, UV | `.metric-card` (3rd) |
| Tvis | Visible Transmittance (%) | `#metricTvis` |
| Rout,vis | Exterior Visible Reflectance (%) | `#metricRoutVis` |
| TUV | UV Transmittance (%) — right-justified, two-line unit text | `#metricTuv` |
| OITC Card | Outside-Inside Transmission Class (relabeled "Rw" in CEN) | `.metric-card` (4th) |
| OITC Value | Acoustic rating value | `#metricTdw` |
| OITC Label | "OITC" or "Rw" (CEN) | `#oitcLabel` |
| OITC Unit | "Outside-Inside Transmission" or "Weighted Sound Reduction" (CEN) | `#oitcUnit` |
| Card Label | Gray header text above each value | `.metric-label` |
| Card Value | Blue gradient number (25px) — fade animation on update | `.metric-value` |
| Card Unit | Small gray unit text below value | `.metric-unit` |
| Center Divider | 1px gray vertical line splitting card sections | inline style |

---

## Cross-Section Card — Enthermal™

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Card Header | "Cross-Section View" | `.viz-card-header` |
| Overall Thickness | Text showing total IGU thickness in mm | `#csOverallThickness` |
| Thickness Value | The mm value (navy color) | `#csThicknessVal` |
| Outboard Label | OUTBOARD title (left side of panes) | `.cs-pane-info-title` |
| Outboard Detail | Coating name (line 1, e.g., "Cardinal LoE3-366") | `#csOuterDetail` |
| Outboard Sub | Glass color + thickness (line 2, e.g., "Clear 6mm") | `#csOuterSub` |
| Inboard Label | INBOARD title (right side of panes) | `.cs-pane-info-title` |
| Inboard Detail | Glass type + thickness (e.g., "Clear 6mm") | `#csInnerDetail` |
| Outer Pane | Left glass pane element | `#csPaneOuter` |
| Inner Pane | Right glass pane element | `#csPaneInner` |
| Low-E Coating Line | Thin orange line on inner surface of outer pane | `#csCoatingLine` |
| Vacuum Gap | Thin 4px gap between panes | `#csVacuum` |
| Black Spacer | 54px black rectangle at base of gap | `.cs-spacer` |
| Callout: Vacuum | Circle + line + "Vacuum Cavity" label | `#csCalloutVacuum` |
| Callout: Low-E | Circle + line + "Low-E Coating" label | `#csCalloutCoating`, `#csCoatingLabel` |

---

## Cross-Section Card — Enthermal Plus™

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Overall Thickness (Plus) | Text showing total IGU thickness in mm | `#csOverallThicknessPlus` |
| Thickness Value (Plus) | The mm value (navy color) | `#csThicknessValPlus` |
| Left Info Title | "Outboard" or "Enthermal" (changes with placement toggle) | `#csPlusLeftInfoTitle` |
| Left Info Detail | Coating name (outboard: vigCoating, inboard: outerCoating) | `#csPlusOuterDetail` |
| Left Info Sub | Glass info — "Clear 4mm" or VIG thickness (e.g., "4/4 mm") | `#csPlusOuterCoating` |
| Right Info Title | "Enthermal" or "Inboard" (changes with placement toggle) | `#csPlusRightInfoTitle` |
| Right Info Detail | Coating name (outboard: outerCoating, inboard: vigCoating) | `#csPlusVigCoatingLabel` |
| Right Info Sub | VIG thickness (e.g., "4/4 mm") or "Clear 4mm" | `#csPlusRightCoating` |
| Mono Pane | Monolithic glass pane (outboard glass) | `#csPlusMonoPane` |
| Mono S2 Coating | Orange coating line on right edge of mono pane | `#csPlusMonoS2` |
| Mono S5 Coating | Orange coating line on left edge of mono pane | `#csPlusMonoS5` |
| VIG Outer Pane | Middle lite (left VIG pane) | `#csPlusVigOuter` |
| VIG Inner Pane | Inboard lite (right VIG pane) | `#csPlusVigInner` |
| Argon Gap | 50px wide gap with desiccant bead pattern | `#csPlusArgonGap` |
| S4 Coating Line | Orange line on right edge of VIG outer pane (opacity transition) | `#csPlusCoatingS4` |
| S5 Coating Line | Orange line on left edge of VIG inner pane (opacity transition) | `#csPlusCoatingS5` |
| Callout: Argon Fill | Circle + line + "12.7 MM ARGON FILL" (or "AIR FILL") | `#csPlusCalloutArgon`, `#csPlusArgonLabel` |
| Callout: Vacuum | Circle + line + "VACUUM CAVITY" | `#csPlusCalloutVacuum` |
| Callout: Low-E | Circle + line + "LOW-E (S4)" or "LOW-E (S5)" | `#csPlusCalloutCoating`, `#csPlusCoatingLabel` |
| Callout: S2 | Circle + line + "LOW-E (S2)" (exterior/left side) | `#csPlusCalloutS2`, `#csPlusS2Label` |

### Cross-Section Layout Modes

**Outboard mode:** VIG outer → vacuum → VIG inner → argon gap → mono pane (left to right)
- S2 on VIG outer right edge, S5 on mono pane left edge
- Left label: "Enthermal" + vigCoating + VIG thickness
- Right label: "Inboard" + outerCoating + "Clear 4mm"

**Inboard mode:** Mono pane → argon gap → VIG outer → vacuum → VIG inner (left to right)
- S2 on mono pane right edge, S4 or S5 on VIG (toggle-controlled)
- Left label: "Outboard" + outerCoating + "Clear 4mm"
- Right label: "Enthermal" + vigCoating + VIG thickness

---

## Cross-Section Info Bar

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Embodied Carbon | kg CO₂e/m² value | `#csECarbon` |
| IGU Weight | kg/m² value | `#csIGUWeight` |
| Info Bar Container | Bottom bar with border-top divider | `.cs-info-bar` |

---

## Color Card

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Card Header | "Exterior Reflected Color" or "Interior Transmitted Color" | `#colorViewTitle` |
| Flat Window | Rectangle with dark frame showing glass color | `.window-flat` |
| Glass Fill | Gradient-colored glass area (from L\*a\*b\* data) | `#fvGlass` |
| Color Info | L\*a\*b\* values text | `#colorInfo` |
| Flip Button | Toggle between Reflected / Transmitted color | `#flipBtn` |
| Flip Label | "FLIP" text below the button | `.flip-label` |

---

## CEN Mode Behavior

The CEN/NFRC toggle **auto-flips** based on the matched data row's `cen` field and is always **locked** (user cannot manually override). CEN-enabled coatings: LUMI (ECLAZ II), ZEN (ECLAZ ONE II), SKN183 (COOL-LITE SKN 183 II), XTR6129 (COOL-LITE XTREME 61-29 II).

When CEN is active:
- U-value (SI) displays `uvalCEN` instead of `uval`
- U-Factor (IP) value shows "—" (metric remains visible, value blanked)
- R-Value shows "—" (metric remains visible, value blanked)
- SHGC label → "g-Factor", value displays `gFactor`, unit → "Solar Factor"
- OITC label → "R<sub>w</sub>", unit → "Weighted Sound Reduction", value uses `rw` from acoustic lookup
- Selecting a non-CEN coating automatically flips back to NFRC and restores all original values and labels

## Placement Toggle Behavior (Plus Tab)

The Inboard/Outboard placement toggle controls the physical arrangement of the VIG relative to the IGU:

**Inboard mode** (toggle unchecked — default):
- Mono outboard glass → argon gap → VIG inboard
- Config order: Glass section (order 1) → Gap (order 2) → Enthermal (order 3)
- S4/S5 surface toggle enabled
- Cascade: outerThickness → outerCoating → gas → vigThickness → vigCoating → surface

**Outboard mode** (toggle checked):
- VIG outboard → argon gap → mono inboard glass
- Config order: Enthermal section (order 1) → Gap (order 2) → Glass section (order 3)
- S4/S5 surface toggle hidden (always S5)
- Cascade: vigThickness (root) → S2 coating + monoThickness → S5 coating
- Glass section label changes to "Inboard"

Switching modes triggers a reseed to defaults (C366 where available) and cross-section pane reorder.

---

## Key CSS Variables

| Variable | Description | Value |
|----------|-------------|-------|
| `--lw-dark` | Near-black for text, header background | `#0a0f1a` |
| `--lw-dark-2` | Dark background variant | `#111827` |
| `--lw-dark-3` | Hero gradient end | `#1a2236` |
| `--lw-navy` | Primary dark blue for values and headings | `#0f2a4a` |
| `--lw-teal` | Accent teal/green | `#0d9488` |
| `--lw-teal-light` | Lighter teal for header badge | `#14b8a6` |
| `--lw-white` | Card backgrounds | `#ffffff` |
| `--lw-gray-50` | Lightest gray (page bg, color card bg) | `#f8fafc` |
| `--lw-gray-100` | Tab background, row dividers | `#f1f5f9` |
| `--lw-gray-200` | Card borders, divider lines, toggle bg | `#e2e8f0` |
| `--lw-gray-300` | Hover borders | `#cbd5e1` |
| `--lw-gray-400` | Callout lines, unit text, section labels | `#94a3b8` |
| `--lw-gray-500` | Labels, secondary text | `#64748b` |
| `--lw-gray-600` | Summary text | `#475569` |
| `--lw-gray-700` | Dark gray | `#334155` |
| `--font-display` | Heading/value font stack | `Plus Jakarta Sans, sans-serif` |
| `--font-body` | Body text font stack | `DM Sans, sans-serif` |
