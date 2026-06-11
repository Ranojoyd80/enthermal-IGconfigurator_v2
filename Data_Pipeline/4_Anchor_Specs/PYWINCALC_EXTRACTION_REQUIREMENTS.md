# pyWinCalc Extraction Requirements — 77-Anchor Production Run

> Contract between the pyWinCalc extraction script and the render pipeline (Stage B data conversion → Stage C Blender automation). Defines exactly what to extract, what to validate, and what to exclude. Companion to `CLAUDE_GLASS_SHADER.md` (shader consumer) and `CLUSTERING_AND_DELIVERY.md` (anchor definitions).

---

## 1. Scope

- **77 anchors** from `AnchorRender_Configs.json` (config-only input: per-layer stack, surface/flip, and `lite_nfrc_id`), spanning 7 manufacturer families / 14 coatings
- **Face-on optical + color extraction** for all 77 (shader inputs)
- **Full angular Rfvis sweep** for all 77 (scaling-formula validation — exhaustive, not sampled)
- Optical/visual quantities only. **No thermal outputs** — gap definitions in this run are nominal-air placeholders; any U-value or SHGC produced would be invalid, not merely redundant. Production thermal data already lives in the configurator JSONs.

---

## 2. Stack construction requirements

| Requirement | Detail |
|---|---|
| Solid layers | Ordered outer → inner per anchor definition |
| Coating orientation | Layer `flipped` flag set per the coating's surface suffix (S2/S4/S5 etc.). **Wrong flip is the #1 silent failure mode** — detected by the Rfvis cross-check (§4) |
| Gaps | Nominal air at nominal width. Structural placeholders only — optical results are independent of gap gas |
| Layer data source | Each layer's `lite_nfrc_id` (the **coated-product** NFRC/IGDB id from the config) mapped NFRC→IGSDB, then cached locally (IGSDB JSON or Window `.dat`) once per unique lite in `layer_cache/`, version-controlled. No live API calls inside the anchor loop — reproducibility requires a frozen cache |
| Optical standard | W5 NFRC photopic/color standard, identical to the configuration that produced the anchor #0 match (pyWinCalc Rfvis 0.15252 vs JSON routVis 0.1525) |

---

## 3. Extraction set — per anchor

### 3.0 At a glance — what gets extracted (16 values/anchor)

| Group | Metric | Count | Role |
|---|---|---|---|
| Face-on θ=0° | `extLab` (L,a,b) | 3 | **Shader input** — reflected color |
| Face-on θ=0° | `transLab` (L,a,b) | 3 | **Shader input** — transmitted color |
| Face-on θ=0° | `Rfvis` | 1 | **Shader input** — ramp stop 0 + scaling factor |
| Face-on θ=0° | `Tvis` | 1 | Validation-only |
| Angular θ=10–80° (10° steps) | `Rfvis(θ)` | 8 | Validation-only — ramp-formula check |
| **Total** | | **16** | 7 shader inputs + 9 validation |

All quantities are **front-side, specular (`direct_direct`), W5 photopic/color**. No calls at θ=0° beyond the face-on set, none at θ=90° (0° reuses the face-on `Rfvis`; 90° is pinned to 1.0 by ramp convention). **Validation references** (`routVis`, `tvis`, `extLab`) are read from the **configurator `App_Data/*.json`** (and/or the Source CSVs) — they are deliberately **not** in `AnchorRender_Configs.json`, which is config-only. Detail and exact pyWinCalc result paths follow.

### 3.1 Face-on (θ = 0°) — shader inputs

| # | Quantity | pyWinCalc result path | Downstream consumer |
|---|---|---|---|
| 1–3 | **extLab** (L, a, b) | `color().system_results.front.reflectance.direct_direct.lab` | Glossy BSDF color (Stage B: Lab → linear RGB) |
| 4–6 | **transLab** (L, a, b) | `color().system_results.front.transmittance.direct_direct.lab` | Transparent BSDF color (Stage B: Lab → linear RGB) |
| 7 | **Rfvis** | `optical_method_results("PHOTOPIC").system_results.front.reflectance.direct_direct` | Color Ramp stop 0 magnitude; scaling factor `Rfvis / 0.1525` |

### 3.2 Face-on — validation only (same calls, zero extra cost)

| # | Quantity | Path | Validates against | Tolerance |
|---|---|---|---|---|
| 8 | **Tvis** | photopic `...front.transmittance.direct_direct` | JSON `tvis` | ±0.002 |
| — | Rfvis (from #7) | — | JSON `routVis` | ±0.002 — **coating-flip / stack-assembly detector** |
| — | extLab (from #1–3) | — | JSON `extL/A/B` | ΔE\* sanity check; divergence with passing Rfvis indicates observer/illuminant mismatch, not stack error |

### 3.3 Angular sweep (θ = 10°–80° in 10° steps, φ = 0°) — validation only

| # | Quantity | Path | Purpose |
|---|---|---|---|
| 9–16 | **Rfvis(θ)** × 8 angles | `optical_method_results("PHOTOPIC", theta, phi)` → same front reflectance path | Per-anchor validation of ramp scaling formula |

- θ = 0° reuses value #7; θ = 90° is pinned at 1.0 by ramp convention. **No calls at either endpoint.**
- Per-anchor prediction: `predicted(θ) = canonical_anchor0(θ) × Rfvis_anchor / 0.1525` using the canonical 10-stop curve in `CLAUDE_GLASS_SHADER.md` Decision 1.
- Per-anchor metric: `max_abs_deviation = max over θ of |measured − predicted|`.

**Three-tier verdict per anchor:**

| max_abs_deviation | Verdict | Action |
|---|---|---|
| ≤ 0.014 | `CONFIRMED` | Formula generates this anchor's ramp (default path) |
| ≤ 0.03 | `DOCUMENTED` | Formula still used; deviation logged |
| > 0.03 | `FLAGGED` | Anchor's measured curve becomes its ramp source (exception path) — Stage B handles per-anchor override |

> **Architectural note:** the measured angular curves validate the ramps; they do not replace them. The formula-generated ramp remains the default per the locked Stage 2 decision (`CLAUDE_GLASS_SHADER.md` Decision 4). Measured curves are evidence, and the exception path only for `FLAGGED` anchors.

### 3.4 Totals

- 16 values × 77 anchors = **1,232 numbers**
- 77 `color()` calls + 693 photopic calls (9 angles × 77)

---

## 4. Explicitly NOT extracted

| Quantity | Reason |
|---|---|
| Angular Lab (ext or trans at θ > 0°) | Angular BSDF Color ramps tested and rejected (Decision 4). Static face-on colors are the locked architecture |
| Back-side quantities (`back.*`) | Exterior camera only; whole-stack front-side data is the entire optical model |
| Hemispherical / diffuse variants (`direct_hemispherical`, `diffuse_diffuse`) | Ramp convention and Window Color Properties are specular `direct_direct`; mixing conventions silently corrupts validation comparisons |
| pyWinCalc RGB output (`color().…rgb`) | Stage B performs Lab → linear RGB itself so the gamma path is explicit. Consuming pre-converted RGB reintroduces the sRGB-vs-linear ambiguity |
| Thermal results (U, SHGC, etc.) | Invalid in this run (placeholder gaps) — add a guard comment in the script |
| Trichromatic / dominant-wavelength outputs | No downstream consumer |

---

## 5. Conventions (pin in script header)

1. **θ units** — verify pyWinCalc's expected unit (degrees assumed) against anchor #0 before the batch: `color(60, 0)` / photopic at 60° must reproduce the known anchor #0 value Rfvis(60°) ≈ 0.279. A radians/degrees mix-up produces smoothly-varying garbage that passes visual inspection.
2. **Full precision** — write raw floats to all CSVs. No rounding anywhere in this stage; rounding happens once, at point of use (Stage B conversion or display). This also defers the Python banker's-rounding vs JS `toFixed(2)` parity question to the one place it matters (key generation), which is not this stage.
3. **φ = 0°** for all angular calls.
4. **Single source of truth for the canonical curve** — the anchor #0 10-stop table from `CLAUDE_GLASS_SHADER.md` Decision 1, embedded once as a constant.

---

## 6. Output files

### 6.1 `anchors_77_optical.csv` — one row per anchor

| Column | Source |
|---|---|
| `anchor_id` | `AnchorRender_Configs.json` (`code`) |
| `product_code` | `AnchorRender_Configs.json` (`code` → render filename stem) |
| `family` | coating family label |
| `extL, extA, extB` | §3.1 #1–3 |
| `transL, transA, transB` | §3.1 #4–6 |
| `rfvis` | §3.1 #7 |
| `tvis` | §3.2 #8 |
| `routvis_json` | configurator JSON (reference) |
| `tvis_json` | configurator JSON (reference) |
| `delta_rfvis` | `rfvis − routvis_json` |
| `delta_tvis` | `tvis − tvis_json` |
| `face_on_status` | `PASS` / `FAIL` per ±0.002 tolerances |
| `max_abs_deviation` | §3.3 angular metric |
| `angular_verdict` | `CONFIRMED` / `DOCUMENTED` / `FLAGGED` |

### 6.2 `angular_validation.csv` — one row per (anchor, θ): 77 × 9 = 693 rows

| Column | Source |
|---|---|
| `anchor_id` | — |
| `family` | — |
| `theta_deg` | 0–80 |
| `rfvis_measured` | pyWinCalc |
| `rfvis_predicted` | scaling formula |
| `deviation` | `measured − predicted` |

### 6.3 `run_log.txt`

- Layer cache manifest (unique lites resolved, source files, fetch dates)
- Any `FAIL` face-on rows with diagnosis hint (Rfvis fail → suspect flip/stack; Lab-only fail → suspect observer/illuminant)
- Verdict summary: count per tier, sorted worst-first list of `max_abs_deviation`
- θ-unit verification result (anchor #0 60° check)

---

## 7. Acceptance criteria for the run

```
[ ] All 77 anchors: face_on_status = PASS (Rfvis and Tvis within ±0.002 of JSON)
[ ] θ-unit verification passed (anchor #0 at 60° ≈ 0.279)
[ ] FLAGGED tier empty (expected) — else Stage B per-anchor override list produced
[ ] All three output files written, full precision
[ ] Layer cache committed alongside outputs
```

A single face-on `FAIL` halts trust in that anchor's Lab values too — fix the stack definition and re-run that anchor before passing data downstream.
