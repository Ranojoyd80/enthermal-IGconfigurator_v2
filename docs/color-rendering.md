# Glass Color Rendering — Current State & Plan

> How the Enthermal™ Configurator shows exterior glass appearance in the **Exterior
> Color** viz card today, and where the per-configuration photoreal pipeline is headed.

> **Heads-up:** an earlier version of this document described a `labToRgb()` →
> CSS-gradient renderer painted onto a `#fvGlass` mock window. **That code has been
> removed.** The card no longer computes color from Lab values at runtime. This
> document reflects the current implementation.

---

## 1. What the card shows today

The **Exterior Color** card (`viz-color`) displays a **static exterior sky
photograph** — a building façade scene used as a stand-in for glass appearance. It
is **not** derived from the selected configuration's color; the same image shows for
every config. Three weather variants are available via a toggle:

| Toggle option | Image | Default |
|---|---|---|
| Clear | `App_Data/Anchor_Renders/Clear_Set3.png` | |
| Overcast | `App_Data/Anchor_Renders/Overcast_Set3.png` | ✓ |
| Cloudy | `App_Data/Anchor_Renders/Cloudy_Set3.png` | |

Key DOM (`enthermal-configurator.html`):
- `#colorRenderImg` — the `<img>`; `src` swaps when the weather toggle changes (≈ line 472)
- `#skyToggle` / `.sky-toggle-option[data-img]` / `#skyThumb` — the weather toggle (≈ line 463)
- `#colorViewTitle` — header text, fixed to "Exterior Color"

This is the **"Set 3"** image set; earlier Sets 1, 2 and 4 were evaluated and removed.

---

## 2. The weather toggle

A pill toggle (`.sky-toggle`) with three options. Selecting one:

1. moves `.active` to the chosen option,
2. sets `#colorRenderImg.src` to that option's `data-img`,
3. slides `#skyThumb` under the active label (width + `translateX`).

The two outer options (Clear / Cloudy) are width-matched so the control is
symmetric; Overcast keeps its natural wider width. Widths are re-equalized on resize
and after the web font loads (glyph widths shift on font swap). See the IIFE at
`enthermal-configurator.html` ≈ line 1476.

---

## 3. The zoom lightbox

The image (or its magnifier button `#colorZoomBtn`) opens a full-screen lightbox
(`#imgZoomOverlay` / `#imgZoomFull`). Inside the lightbox the user can step through
the three sky conditions with the prev/next buttons or ← / → keys; stepping reuses
the sky-toggle options so the small card image and the lightbox stay in sync. Escape
or a backdrop click closes it. See the IIFE at `enthermal-configurator.html` ≈ line 1440.

---

## 4. Where the per-config color data lives

Every configuration still carries two CIE L\*a\*b\* reflected-color triplets in the
`App_Data/*.json` records — `extL/extA/extB` (exterior) and `intL/intA/intB` (interior),
computed by LBNL Windows 7 / PyWinCalc under D65 / 2°. These are **not currently
visualized** on the card, but they are the basis for the clustering that drives the
planned render pipeline (below), and they remain available for any future readout or
tint feature.

> **Note — Lab is not used for the cross-section tint.** Driving the cross-section
> glass-pane tint from these `extL/A/B` values was evaluated and rejected: the
> assembly-level Lab is dominated by the low-E coating, so different substrates
> collapse to nearly the same dark blue-gray and the recognizable body tint
> (bronze, green, blue) is lost. The cross-section keeps the hand-tuned
> `getGlassColor(substrate)` lookup instead.

---

## 5. The plan — per-anchor photoreal renders

Per-configuration appearance is intended to come from **pre-rendered Blender images**,
not runtime math. The 6,862 configs collapse to **77 color anchors** at ΔE ≤ 2 (JND);
each anchor is rendered against three HDR skies, and the front-end will swap in the
right image by resolving a config's Lab color → anchor code via `cluster_map.json`.

That delivery system is **designed but not yet wired into the app** — the current
static sky photo is the interim placeholder. Full detail (the clustering algorithm,
the `cluster_map.json` runtime lookup, the image-swap `updateColor()` pattern, hosting
and URL conventions) is in [CLUSTERING_PROCEDURE.md](../CLUSTERING_PROCEDURE.md).

---

## 6. Reference — code locations

| Purpose | File : approx. line |
|---|---|
| Color card markup (`viz-color`, sky toggle, `#colorRenderImg`) | enthermal-configurator.html : 461–475 |
| `.sky-toggle` styles | enthermal-configurator.html : 136–139 |
| Zoom lightbox IIFE | enthermal-configurator.html : 1440 |
| Sky-condition toggle IIFE | enthermal-configurator.html : 1476 |

*(Line numbers are approximate — the app is a single evolving file; search by ID if they've drifted.)*
