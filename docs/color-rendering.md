# Glass Color Rendering — Current State

> How the Enthermal™ Configurator shows exterior glass appearance in the **Exterior
> Color** viz card. The card now shows a **per-configuration photoreal render**; the
> earlier `labToRgb()` gradient and the interim static-sky placeholder are both gone.

> **History:** two designs have been retired here. (1) A `labToRgb()` → CSS-gradient
> renderer painted onto a `#fvGlass` mock window — removed. (2) An interim **static**
> exterior sky photo (`*_Set3.png`), the same image for every config — also removed now
> that the per-anchor render batch exists. This document reflects the current `cid`-driven
> implementation.

---

## 1. What the card shows today

The **Exterior Color** card (`viz-color`) displays a **per-configuration photoreal
render**, selected by the config's `cid` (integer anchor id). Three weather variants are
available via a toggle, all for the *same* config:

| Toggle option | Image | Default |
|---|---|---|
| Clear | `App_Data/Anchor_Renders/Clear/anchor_<cid>.webp` | |
| Overcast | `App_Data/Anchor_Renders/Overcast/anchor_<cid>.webp` | ✓ |
| Cloudy | `App_Data/Anchor_Renders/Cloudy/anchor_<cid>.webp` | |

The 6,862 configs collapse to **137 color anchors** (CIEDE2000 ≤ 1.5, partitioned by
exterior substrate), so the render is imperceptibly close to — and the same hue family as
— the user's exact selection. Full algorithm and delivery detail:
[CLUSTERING_PROCEDURE.md](../Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md).

Key DOM / JS (`enthermal-configurator.html`):
- `#colorRenderImg` — the `<img>`; `src` is set per config and swaps on weather toggle (≈ line 492)
- `#skyToggle` / `.sky-toggle-option[data-img]` / `#skyThumb` — the weather toggle (≈ line 483)
- `setAnchorImages(cid)` — repoints all three sky options' `data-img` + the visible image for the current config (≈ line 673); called from `updateResults()` / the Plus updater on every config change
- `#colorViewTitle` — header text, fixed to "Exterior Color"

---

## 2. How a config resolves to its render — the `cid`

`CLAUDE.md` forbids hand-editing `App_Data/*.json`, but the clustering script is the
*generator* of that JSON, so it injects an integer **`cid`** onto every record at build
time (`Data_Pipeline/3_Clustering/recluster_at_jnd.py`). The front-end reads `cid`
directly — no runtime Lab-key string formatting, no `cluster_map.json` fetch:

```js
function setAnchorImages(cid){
  if(cid==null) return;                                   // keep last image rather than 404
  var code = 'anchor_' + String(cid).padStart(2,'0');     // 5 -> anchor_05, 135 -> anchor_135
  document.querySelectorAll('.sky-toggle-option').forEach(function(opt){
    var sky = opt.textContent.trim();                     // Clear | Overcast | Cloudy
    opt.setAttribute('data-img', 'App_Data/Anchor_Renders/'+sky+'/'+code+'.webp');
  });
  var active = document.querySelector('.sky-toggle-option.active');
  if(active) document.getElementById('colorRenderImg').src = active.getAttribute('data-img');
}
```

The data card itself stays 1:1: the user always sees the **exact** optical numbers and Lab
values for *their* selection from the JSON — only the *image* is shared across a cluster.

---

## 3. The weather toggle

A pill toggle (`.sky-toggle`) with three options. Selecting one:

1. moves `.active` to the chosen option,
2. sets `#colorRenderImg.src` to that option's `data-img` (already repointed to the current `cid` by `setAnchorImages`),
3. slides `#skyThumb` under the active label (width + `translateX`).

The two outer options (Clear / Cloudy) are width-matched so the control is symmetric;
Overcast keeps its natural wider width. Widths are re-equalized on resize and after the web
font loads (glyph widths shift on font swap). See the IIFE at
`enthermal-configurator.html` ≈ line 1476.

---

## 4. The zoom lightbox

The image (or its magnifier button `#colorZoomBtn`) opens a full-screen lightbox
(`#imgZoomOverlay` / `#imgZoomFull`). Inside, the user can step through the three sky
conditions with the prev/next buttons or ← / → keys; stepping reuses the sky-toggle options
(which already carry the current config's `cid`), so the small card image and the lightbox
stay in sync. Escape or a backdrop click closes it. See the IIFE at
`enthermal-configurator.html` ≈ line 1440.

---

## 5. Where the per-config color data lives

Every configuration carries two CIE L\*a\*b\* reflected-color triplets in the
`App_Data/*.json` records — `extL/extA/extB` (exterior) and `intL/intA/intB` (interior),
computed by LBNL Windows 7 / PyWinCalc under D65 / 2°. `extL/A/B` is what the **clustering**
runs on to assign each config its `cid` (see [CLUSTERING_PROCEDURE.md](../Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md));
the values are not otherwise drawn on the card today but remain available for any future readout.

> **Note — Lab is not used for the cross-section tint.** Driving the cross-section
> glass-pane tint from these `extL/A/B` values was evaluated and rejected: the
> assembly-level Lab is dominated by the low-E coating, so different substrates collapse to
> nearly the same dark blue-gray and the recognizable body tint (bronze, green, blue) is
> lost. The cross-section keeps the hand-tuned `getGlassColor(substrate)` lookup instead.

---

## 6. Reference — code locations

| Purpose | File : approx. line |
|---|---|
| Color card markup (`viz-color`, sky toggle, `#colorRenderImg`) | enthermal-configurator.html : 481–497 |
| `setAnchorImages(cid)` per-config render lookup | enthermal-configurator.html : 666–682 |
| `.sky-toggle` styles | enthermal-configurator.html : ~136 |
| Zoom lightbox IIFE | enthermal-configurator.html : 1440 |
| Sky-condition toggle IIFE | enthermal-configurator.html : 1476 |

*(Line numbers are approximate — the app is a single evolving file; search by ID if they've drifted.)*
