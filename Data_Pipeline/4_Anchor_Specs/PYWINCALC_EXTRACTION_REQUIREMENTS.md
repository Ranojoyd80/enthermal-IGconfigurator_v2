# pyWinCalc Extraction Requirements — 202-Anchor Production Run

> Contract between the pyWinCalc extraction script and the render pipeline (Stage B data conversion → Stage C Blender automation). Defines exactly what to extract, what to validate, and what to exclude. Companion to `CLAUDE_GLASS_SHADER.md` (shader consumer) and `../3_Clustering/CLUSTERING_PROCEDURE.md` (anchor definitions).

---

## 1. Scope

- **202 anchors** from `AnchorRender_Configs.json` (config-only input: per-layer stack, surface/flip, and `lite_nfrc_id`), spanning 7 manufacturer families / 14 coatings / 8 exterior-substrate families
- **Anchors come from the two-axis clustering** (CIEDE2000, substrate-partitioned): every config is within **ext ≤1.5 AND trn ≤3.0** of its anchor. `cid` is **1-based**, so anchor code / Blender frame align 1:1 (frame N = cid N = `anchor_NN`). Because transmitted color is now a clustered axis, the `transLab` extraction below is load-bearing, not just validation.
- **Face-on optical + color extraction** for all 202 (shader inputs)
- **Full angular Rfvis sweep** for all 202 — each anchor's OWN reflectance ramp (exhaustive per anchor, not sampled; there is no shared/canonical curve)
- Optical/visual quantities only. **No thermal outputs** — gap definitions in this run are nominal-air placeholders; any U-value or SHGC produced would be invalid, not merely redundant. Production thermal data already lives in the configurator JSONs.

---

## 2. Stack construction requirements

| Requirement | Detail |
|---|---|
| Solid layers | Ordered outer → inner per anchor definition |
| Coating orientation | Layer `flipped` flag set per the coating's surface suffix (S2/S4/S5 etc.). **Wrong flip is the #1 silent failure mode** — detected by the Rfvis cross-check (§4) |
| Gaps | Nominal air at nominal width. Structural placeholders only — optical results are independent of gap gas |
| Layer data source | Each layer's `lite_nfrc_id` (the **coated-product** NFRC/IGDB id from the config) mapped NFRC→IGSDB, then cached locally (IGSDB JSON or Window `.dat`) once per unique lite in `layer_cache/`, version-controlled. No live API calls inside the anchor loop — reproducibility requires a frozen cache |
| Optical standard | W5 NFRC photopic/color standard — the same standard that produced the configurator JSON reference values. Per-anchor Rfvis/Tvis are cross-checked against JSON in §3.2 |

---

## 3. Extraction set — per anchor

### 3.0 At a glance — what gets extracted (16 values/anchor)

| Group | Metric | Count | Role |
|---|---|---|---|
| Face-on θ=0° | `extLab` (L,a,b) | 3 | **Shader input** — reflected color |
| Face-on θ=0° | `transLab` (L,a,b) | 3 | **Shader input** — transmitted color |
| Face-on θ=0° | `Rfvis` | 1 | **Shader input** — ramp stop 0 (face-on reflectance) |
| Face-on θ=0° | `Tvis` | 1 | Validation-only |
| Angular θ=10–80° (10° steps) | `Rfvis(θ)` | 8 | **Shader input** — this anchor's own ramp stops 1–8 |
| **Total** | | **16** | 15 shader inputs + 1 validation |

All quantities are **front-side, specular (`direct_direct`), W5 photopic/color**. No calls at θ=0° beyond the face-on set, none at θ=90° (0° reuses the face-on `Rfvis`; 90° is pinned to 1.0 by ramp convention). **Validation references** (`routVis`, `tvis`, `extLab`) are read from the **configurator `App_Data/*.json`** (and/or the Source CSVs) — they are deliberately **not** in `AnchorRender_Configs.json`, which is config-only. Detail and exact pyWinCalc result paths follow.

### 3.1 Face-on (θ = 0°) — shader inputs

| # | Quantity | pyWinCalc result path | Downstream consumer |
|---|---|---|---|
| 1–3 | **extLab** (L, a, b) | `color().system_results.front.reflectance.direct_direct.lab` | Glossy BSDF color (Stage B: Lab → linear RGB) |
| 4–6 | **transLab** (L, a, b) | `color().system_results.front.transmittance.direct_direct.lab` | Transparent BSDF color (Stage B: Lab → linear RGB) |
| 7 | **Rfvis** | `optical_method_results("PHOTOPIC").system_results.front.reflectance.direct_direct` | Color Ramp stop 0 magnitude (face-on reflectance) |

### 3.2 Face-on — validation only (same calls, zero extra cost)

| # | Quantity | Path | Validates against | Tolerance |
|---|---|---|---|---|
| 8 | **Tvis** | photopic `...front.transmittance.direct_direct` | JSON `tvis` | ±0.002 |
| — | Rfvis (from #7) | — | JSON `routVis` | ±0.002 — **coating-flip / stack-assembly detector** |
| — | extLab (from #1–3) | — | JSON `extL/A/B` | ΔE\* sanity check; divergence with passing Rfvis indicates observer/illuminant mismatch, not stack error |

### 3.3 Angular sweep (θ = 10°–80° in 10° steps, φ = 0°) — per-anchor ramp source

| # | Quantity | Path | Purpose |
|---|---|---|---|
| 9–16 | **Rfvis(θ)** × 8 angles | `optical_method_results("PHOTOPIC", theta, phi)` → same front reflectance path | **Shader input** — this anchor's own angular reflectance ramp (stops 1–8) |

- **Each anchor has its OWN measured curve.** There is no canonical/shared curve and no scaling formula — every anchor's ramp is read directly from its own pyWinCalc sweep.
- The anchor's 10-stop Color Ramp = `[Rfvis(0°), Rfvis(10°…80°), 1.0]`: stop 0 is the face-on value (#7), stops 1–8 are these 8 measured angles, stop 9 (θ = 90°) is pinned at 1.0 by ramp convention. **No calls at either endpoint.**
- Sanity check only (not a pass/fail gate): `Rfvis(θ)` should rise monotonically with θ. A non-monotonic curve indicates a flip/stack or convention error — log it for review.

### 3.4 Totals

- 16 values × 202 anchors = **3,232 numbers**
- 202 `color()` calls + 1,818 photopic calls (9 angles × 202)

---

## 4. Explicitly NOT extracted

| Quantity | Reason |
|---|---|
| Angular Lab (ext or trans at θ > 0°) | Angular BSDF *color* ramps were tested and rejected; static face-on colors are the locked architecture. Reflectance *magnitude* is still ramped per angle — that is the `Rfvis(θ)` sweep (§3.3) — but color is not |
| Back-side quantities (`back.*`) | Exterior camera only; whole-stack front-side data is the entire optical model |
| Hemispherical / diffuse variants (`direct_hemispherical`, `diffuse_diffuse`) | Ramp convention and Window Color Properties are specular `direct_direct`; mixing conventions silently corrupts validation comparisons |
| pyWinCalc RGB output (`color().…rgb`) | Stage B performs Lab → linear RGB itself so the gamma path is explicit. Consuming pre-converted RGB reintroduces the sRGB-vs-linear ambiguity |
| Thermal results (U, SHGC, etc.) | Invalid in this run (placeholder gaps) — add a guard comment in the script |
| Trichromatic / dominant-wavelength outputs | No downstream consumer |

---

## 5. Conventions (pin in script header)

1. **θ units** — verify pyWinCalc's expected unit is degrees, not radians, before trusting the sweep: photopic front reflectance must rise monotonically with θ toward ~1.0 at grazing. A radians/degrees mix-up produces smoothly-varying garbage that passes visual inspection, so confirm the trend on one anchor first.
2. **Full precision** — write raw floats to all CSVs. No rounding anywhere in this stage; rounding happens once, at point of use (Stage B conversion or display). This also defers the Python banker's-rounding vs JS `toFixed(2)` parity question to the one place it matters (key generation), which is not this stage.
3. **φ = 0°** for all angular calls.
4. **Per-anchor ramp, no shared curve** — each anchor's 10 Color Ramp stops come straight from its own measured `Rfvis(θ)` (§3.3). Do NOT derive ramps from a canonical curve or a scaling factor; there is no canonical curve.

---

## 6. Output files

### 6.1 `anchors_optical.csv` — one row per anchor

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
| `angular_monotonic` | `Y` / `N` — sanity flag (Rfvis rises with θ); `N` = review |

### 6.2 `angular_ramps.csv` — one row per (anchor, θ): 202 × 9 = 1,818 rows

This is the per-anchor ramp data (each anchor's own measured curve), consumed by Stage B to build that anchor's Color Ramp.

| Column | Source |
|---|---|
| `anchor_id` | — |
| `family` | — |
| `theta_deg` | 0–80 (θ=0 is the face-on value; θ=90 pinned to 1.0, not stored) |
| `rfvis` | pyWinCalc measured front reflectance at θ |

### 6.3 `run_log.txt`

- Layer cache manifest (unique lites resolved, source files, fetch dates)
- Any `FAIL` face-on rows with diagnosis hint (Rfvis fail → suspect flip/stack; Lab-only fail → suspect observer/illuminant)
- Any non-monotonic angular ramps flagged for review (Rfvis should rise with θ)
- θ-unit sanity check result (monotonic rise toward ~1.0 at grazing)

---

## 7. Acceptance criteria for the run

```
[ ] All 202 anchors: face_on_status = PASS (Rfvis and Tvis within ±0.002 of JSON)
[ ] θ-unit sanity check passed (degrees not radians: Rfvis rises monotonically to ~1.0 at grazing)
[ ] All angular ramps monotonic in θ (any non-monotonic anchor reviewed and explained)
[ ] All three output files written, full precision
[ ] Layer cache committed alongside outputs
```

A single face-on `FAIL` halts trust in that anchor's Lab values too — fix the stack definition and re-run that anchor before passing data downstream.
