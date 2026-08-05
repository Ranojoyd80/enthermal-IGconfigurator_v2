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
| Product Tabs | Enthermal™ / Enthermal Plus™ (two tabs; the Spandrel tab has been removed) | `.product-tab`, `data-tab="enthermal"` / `data-tab="enthermal-plus"` |

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
| Outer Low-E Coating | S2 coating dropdown. Parent section swaps with placement: sits under "Outboard" (the mono lite) in Inboard mode and under "Enthermal" (the VIG) in Outboard mode. Values are bare shortcodes (e.g., `"C366"`) | `#plusOuterCoating` |
| Gap Fill Toggle | 90% Argon / 100% Air slider toggle | `#gapToggle`, `#gapToggleInput` |
| Argon Label | "Argon" text left of gas toggle | `#gapLabelArgon` |
| Air Label | "Air" text right of gas toggle | `#gapLabelAir` |
| Enthermal Section Label | "Enthermal" section header | `.config-section-label` |
| VIG Thickness Dropdown | VIG glass thickness: 4/4, 5/4, 5/5, 6/5, 6/6 mm | `#plusVigThickness` |
| VIG Low-E Coating | S4/S5 coating dropdown. Parent section swaps with placement: sits under "Enthermal" (VIG S4/S5) in Inboard mode and under "Inboard" (mono S5) in Outboard mode | `#plusVigCoating` |
| Coating Surface Toggle | S4 (Middle) / S5 (Inboard) slider toggle. Disabled and forced to S5 in Outboard mode. | `#srfToggle`, `#srfToggleInput` |
| S4 Label | "Middle (S4)" text left of toggle | `#srfLabelS4` |
| S5 Label | "Inboard (S5)" text right of toggle | `#srfLabelS5` |
| Toggle Thumb | Teal circular sliding indicator | `#srfThumb` |
| Coating Surface Field | Container for S4/S5 toggle — hidden in Outboard mode | `#plusCoatingSurfaceField` |
| Hidden Radios | Hidden radio inputs synced by the surface toggle | `#plusSrf4` (S4), `#plusSrf5` (S5), `name='plusCoatingSurface'` |

### Unresolved-Coating Attention Ring

When a coating dropdown is sitting on its `"Select coating…"` placeholder (`value === ''`),
it gets a **red attention ring** so the blocked cascade is visible rather than silent.

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Attention ring | Red border + halo on an unresolved coating select | `.config-field select.select-attn` |
| Pulse keyframes | Halo expands 3px → 6px and back | `@keyframes attnPulse` |
| Flag function | Adds/removes `.select-attn` across all three coating selects | `flagUnresolvedCoatings()` |

Behavior:

- **3-cycle pulse, then a steady ring.** `animation: attnPulse 1.2s ease-in-out 3` runs
  three times and stops; the class's own `border-color: var(--lw-red)` + `box-shadow`
  remain until the pick resolves. The ring is a persistent state, not just an animation.
- **The class is added only on the transition into the unresolved state**, so the pulse
  doesn't restart on every render pass.
- **Covers all three coating selects:** `#outerCoating`, `#plusOuterCoating`, `#plusVigCoating`.
- **Cleared as soon as the cascade resolves the pick** (`el.value !== ''`).
- **Ordered after `:focus` in the stylesheet** so the red keeps priority while the user
  is inside the field.
- **Re-evaluated on every render/clear path** — `flagUnresolvedCoatings()` is called from
  `refreshMetricMuted()`, which every update and clear path already runs.

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

> **Coating names in the summary are shortened.** The summary bar uses
> `summaryCoatingName(code)` — `coatingName(code)` with a leading `"COOL-LITE "`
> stripped — so Saint-Gobain products read `SKN 183 II` rather than
> `COOL-LITE SKN 183 II`. **This applies to the summary text only**; the config-panel
> dropdowns and the cross-section labels keep the full name. The shortening exists to
> stop long Plus summaries from wrapping a single orphan word onto a second line.
>
> The summary element also carries `text-wrap: balance` (`.config-summary-text`), which
> evens out line lengths when it does wrap. Together these clear all orphan-wrapping
> Plus configs at full width (verified 0 of 3,173 distinct summaries wrap).

**Enthermal™:**
`<strong>[coating display]</strong> on <strong>[outerMM]mm</strong> outboard and <strong>[inner substrate] [innerMM]mm</strong> inboard.`
Example: **LoE³ 366** on **6mm** outboard and **Clear 6mm** inboard.

The inboard lite is named with its **actual substrate**, not a hardcoded "Clear" — on an
all-Starphire assembly it reads **Starphire 6mm**. (See the Starphire display contract in
`Automated Test/TEST-PLAN.md` §4 Group B.)

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
| OITC / Rw Card | Dual-value acoustic card with two **static** columns: OITC (left) and R<sub>w</sub> (right). Both labels always show; the value of whichever standard is inactive blanks to "—" | `.metric-card` (4th) |
| OITC Value | Outside-Inside Transmission Class — populated in NFRC mode, "—" in CEN | `#metricTdw` |
| Rw Value | Weighted Sound Reduction — populated in CEN mode, "—" in NFRC | `#metricRw` |
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
| Outer Pane | Left glass pane element; tinted from the outer substrate via `getGlassColor()` | `#csPaneOuter` |
| Inner Pane | Right glass pane element | `#csPaneInner` |
| Low-E Coating Line | Thin orange line on inner surface of outer pane | `#csCoatingLine` |
| Vacuum Gap | Thin 4px gap between panes | `#csVacuum` |
| Black Spacer | 54px black rectangle at base of gap | `.cs-spacer` |
| Callout: Vacuum | Circle + line + "Vacuum Cavity" label | `#csCalloutVacuum` |
| Callout: Low-E | Circle + line + "Low-E Coating" label | `#csCalloutCoating`, `#csCoatingLabel` |
| Callout: Hermetic Seal | Circle + line + "Hermetic Seal" label, points at the black spacer; left-side label, vertically centered on the spacer | `#csCalloutHermetic` |

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
| Mono Pane | Monolithic glass pane (`glass[0]`, the exterior lite). Tinted from its substrate via `getGlassColor()` in Inboard mode (it is the exterior lite); reset to clear in Outboard mode (where the VIG outer becomes the exterior lite) | `#csPlusMonoPane` |
| Mono S2 Coating | Orange coating line on right edge of mono pane | `#csPlusMonoS2` |
| Mono S5 Coating | Orange coating line on left edge of mono pane | `#csPlusMonoS5` |
| VIG Outer Pane | Middle lite (left VIG pane). Tinted from `glass[0]`'s substrate via `getGlassColor()` in Outboard mode (it becomes the exterior lite); reset to clear in Inboard mode | `#csPlusVigOuter` |
| VIG Inner Pane | Inboard lite (right VIG pane) | `#csPlusVigInner` |
| Argon Gap | 50px wide gap with desiccant bead pattern | `#csPlusArgonGap` |
| S4 Coating Line | Orange line on right edge of VIG outer pane (opacity transition) | `#csPlusCoatingS4` |
| S5 Coating Line | Orange line on left edge of VIG inner pane (opacity transition) | `#csPlusCoatingS5` |
| Callout: Argon Gap | Circle + line + dynamic label "<gap> MM ARGON GAP" (or "AIR GAP"), thickness from matched row's gas layer | `#csPlusCalloutArgon`, `#csPlusArgonLabel` |
| Callout: Vacuum | Circle + line + "VACUUM CAVITY" | `#csPlusCalloutVacuum` |
| Callout: Low-E | Circle + line + "LOW-E (S4)" or "LOW-E (S5)" | `#csPlusCalloutCoating`, `#csPlusCoatingLabel` |
| Callout: S2 | Circle + line + "LOW-E (S2)" (exterior/left side) | `#csPlusCalloutS2`, `#csPlusS2Label` |
| Callout: Hermetic Seal | Circle + line + "Hermetic Seal", points at the VIG vacuum spacer. Placed on the spacer's own side (left in Outboard where the VIG is exterior, right in Inboard); vertically centered on the spacer | `#csPlusCalloutHermetic` |
| Callout: Metal Spacer | Circle + line + "Metal Spacer", points at the warm-edge spacer at the base of the argon gap. Placed on the spacer's own side (right in Outboard, left in Inboard); vertically centered on the spacer | `#csPlusCalloutMetal` |

### Cross-Section Layout Modes

**Outboard mode:** VIG outer → vacuum → VIG inner → argon gap → mono pane (left to right)
- S2 on VIG outer right edge, S5 on mono pane left edge
- Left label: "Enthermal" + vigCoating + VIG thickness
- Right label: "Inboard" + outerCoating + "Clear 4mm"
- Exterior lite (`glass[0]`) is the VIG outer pane → it carries the substrate tint
- Spacer callouts: Hermetic Seal on the left (VIG vacuum is exterior), Metal Spacer on the right

**Inboard mode:** Mono pane → argon gap → VIG outer → vacuum → VIG inner (left to right)
- S2 on mono pane right edge, S4 or S5 on VIG (toggle-controlled)
- Left label: "Outboard" + outerCoating + "Clear 4mm"
- Right label: "Enthermal" + vigCoating + VIG thickness
- Exterior lite (`glass[0]`) is the mono pane → it carries the substrate tint
- Spacer callouts: Metal Spacer on the left (argon gap is exterior-side), Hermetic Seal on the right

The pane reordering uses CSS flex `order`; the substrate tint and spacer callouts follow `glass[0]` and the live spacer positions, so each renders on the correct pane/side in both modes.

---

## Cross-Section Info Bar

Both stats are **standard-aware** — the active NFRC/CEN standard changes the caption
and the unit, not just the number.

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Embodied Carbon | Value in kg CO₂e/m² — the unit stays SI in both standards, per EPD practice | `#csECarbon` |
| Embodied Carbon Caption | Life-cycle scope: **"Cradle to Gate"** in NFRC, **"Cradle to Grave"** in CEN | `#csECarbonCaption` |
| IGU Weight | Numeric value; recomputed per standard by `iguWeight(mm, cenActive)` | `#csIGUWeight` |
| IGU Weight Unit | **"lb/ft²"** in NFRC, **"kg/m²"** in CEN (1 kg/m² = 0.204816 lb/ft²) | `#csIGUWeightUnit` |
| Info Bar Container | Bottom bar with border-top divider | `.cs-info-bar` |

Both stats grey out via `.metric-muted` when their value is `"—"` — `refreshMetricMuted()`
runs the same pass over the info bar as over the metric cards. Enthermal Plus has no
embodied-carbon data yet, so that stat is permanently muted on the Plus tab.

---

## Color Card (Exterior Appearance)

The card shows a **per-configuration photoreal render** with a weather toggle and a
zoom lightbox — not a computed Lab→RGB gradient. The config's `cid` selects the image
(`App_Data/Anchor_Renders/<Sky>/anchor_<cid>.webp`) via `setAnchorImages(cid)`. (The old
`#fvGlass` gradient, flip button, and `#colorInfo` Lab readout have been removed.) See
[color-rendering.md](color-rendering.md) for full detail.

| Element | Description | CSS / ID |
|---------|-------------|----------|
| Card Header | "Exterior Appearance" (static) | `#colorViewTitle` |
| Sky Toggle | Pill toggle: Overcast / Partly Clear sky backdrop (default Overcast; folder from `data-folder`) | `#skyToggle`, `.sky-toggle-option[data-img]` |
| Toggle Thumb | Teal sliding pill behind the active option | `#skyThumb` |
| Render Image | The per-config render (`Anchor_Renders/<Sky>/anchor_<cid>.webp`); `src` set per config and swaps with the toggle | `#colorRenderImg` |
| Fallback Panel | Replaces the image when it can't be shown — `setRenderState`: "Loading exterior render…" (in-flight download with nothing else on screen), "Select a product…" (cleared selection), "Exterior render unavailable…" (image error / missing `cid`). While a render is showing, config changes swap silently. | `#colorRenderFallback` |
| Zoom Button | Magnifier button to open the lightbox (hidden whenever the fallback panel is shown) | `#colorZoomBtn` |
| Zoom Lightbox | Full-screen overlay; prev/next or ←/→ step through the two sky conditions | `#imgZoomOverlay`, `#imgZoomFull`, `#imgZoomPrev`, `#imgZoomNext`, `#imgZoomClose` |
| Disclaimer Note | "On-screen color is representational and varies with display. Confirm final color with physical samples." | italic caption under the image |

---

## CEN Mode Behavior

The CEN/NFRC toggle **defaults** from the matched data row's `cen` field on every row change. On CEN-capable rows the toggle is **enabled** and the user may flip it freely (a manual flip survives same-row re-renders via `stdUserFlip`); on non-CEN rows it is **disabled and forced to NFRC**. CEN capability follows the maker-set rule: a Saint-Gobain coating present AND no Vitro coating (e.g. LUMI/ECLAZ II, ZEN/ECLAZ ONE II, SKN183, XTR6129).

When CEN is active:
- U-value (SI) displays `uvalCEN` instead of `uval`
- U-Factor (IP) value shows "—" (metric remains visible, value blanked)
- R-Value shows "—" (metric remains visible, value blanked)
- SHGC label → "g-Factor", value displays `gFactor`, unit → "Solar Factor"
- OITC value blanks to "—"; the R<sub>w</sub> column (always present) is populated from the `rw` acoustic lookup. (NFRC mode is the reverse: OITC shown, R<sub>w</sub> blank.)
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

Switching modes triggers a reseed to defaults and a cross-section pane reorder. The two
seed functions set **featured** configurations, not just the first valid option:

| Mode | Seeded by | Defaults |
|---|---|---|
| Inboard | `seedPlusInboardDefaults()` | **6 mm mono** exterior lite + **4/4 VIG**, C366 throughout, surface S4 |
| Outboard | `seedPlusOutboardDefaults()` | **5/5 VIG** + **5 mm mono** inboard lite, C366 throughout (S5 forced) |

The presets are applied **before** the cascades run, so the keep-if-valid logic in
`updatePlusVigThickness()` / `updatePlusInboardThicknessOutboard()` retains them where
they're valid and falls back to the first valid option otherwise (graceful fallback, not
a hard requirement that the preset exist).

A `plusSeeding` flag suppresses the transient `clearResults()` calls that fire while a
seed function is rebuilding the dropdowns in half-seeded states — without it, the render
already on screen would be hidden and the card would drop to the loading panel instead of
swapping silently. A genuinely unresolvable selection still clears, because the post-seed
`updatePlusResults()` runs with the flag down.

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
| `--lw-red` | Attention ring on an unresolved coating dropdown | `#dc2626` |
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
| `--tab-row-height` | Product-tab row height (layout metric, not a color) | `53px` |

*(This table mirrors `:root` in the HTML. If you add a token, add it here and to CLAUDE.md §2 — that file mandates using only listed tokens, so an unlisted one is effectively invisible to future work.)*
