# Glass Color Rendering — Current State

> How the Enthermal™ Configurator shows exterior glass appearance in the **Exterior
> Appearance** viz card. The card now shows a **per-configuration photoreal render**; the
> earlier `labToRgb()` gradient and the interim static-sky placeholder are both gone.

> **History:** two designs have been retired here. (1) A `labToRgb()` → CSS-gradient
> renderer painted onto a `#fvGlass` mock window — removed. (2) An interim **static**
> exterior sky photo (`*_Set3.png`), the same image for every config — also removed now
> that the per-anchor render batch exists. This document reflects the current `cid`-driven
> implementation.

---

## 1. What the card shows today

The **Exterior Appearance** card (`viz-color`) displays a **per-configuration photoreal
render**, selected by the config's `cid` (1-based integer anchor id). Two sky variants are
available via a toggle, all for the *same* config:

| Toggle option (label) | Folder (`data-folder`) | Image | Default |
|---|---|---|---|
| Overcast | `Overcast` | `App_Data/Anchor_Renders/Overcast/anchor_<cid>.webp` | ✓ |
| Partly Clear | `PartlyClear` | `App_Data/Anchor_Renders/PartlyClear/anchor_<cid>.webp` | |

The display label "Partly Clear" carries a space; the on-disk folder (`PartlyClear`) is
space-free, so each option carries a `data-folder` attribute that `setAnchorImages()` uses
to build the path (falling back to the label text if absent).

The 6,444 configs collapse to **202 color anchors** (two-axis CIEDE2000: exterior reflected ≤ 1.5 **and** transmitted ≤ 3.0; 1-based `cid`s; partitioned by
exterior substrate), so the render is imperceptibly close to — and the same hue family as
— the user's exact selection. Full algorithm and delivery detail:
[CLUSTERING_PROCEDURE.md](../Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md).

Key DOM / JS (`enthermal-configurator.html`):
- `#colorRenderImg` — the `<img>`; `src` is set per config and swaps on weather toggle (≈ line 492)
- `#skyToggle` / `.sky-toggle-option[data-img]` / `#skyThumb` — the weather toggle (≈ line 483)
- `setAnchorImages(cid)` — repoints both sky options' `data-img` + the visible image for the current config (≈ line 673); called from `updateResults()` / the Plus updater on every config change
- `#colorViewTitle` — header text, fixed to "Exterior Appearance"

---

## 2. How a config resolves to its render — the `cid`

`CLAUDE.md` forbids hand-editing `App_Data/*.json`, but the clustering script is the
*generator* of that JSON, so it injects an integer **`cid`** onto every record at build
time (`Data_Pipeline/3_Clustering/recluster_at_jnd.py`). The front-end reads `cid`
directly — no runtime Lab-key string formatting, no `cluster_map.json` fetch:

```js
// Cache-buster token — maintained by .githooks/sync_render_version.py, never by hand.
var RENDER_V='?v=54e29159';

function anchorUrl(folder,cid){
  return 'App_Data/Anchor_Renders/'+folder+'/anchor_'+String(cid).padStart(2,'0')+'.webp'+RENDER_V;
}

function setAnchorImages(cid){
  if(cid==null){                                          // honest failure, not a stale facade
    console.error('setAnchorImages: config has no cid — showing render-unavailable state');
    setRenderState('unavailable');
    return;
  }
  var inactiveUrls=[];
  document.querySelectorAll('.sky-toggle-option').forEach(function(opt){
    var folder=opt.getAttribute('data-folder')||opt.textContent.trim(); // Overcast | PartlyClear
    opt.setAttribute('data-img',anchorUrl(folder,cid));
    if(!opt.classList.contains('active'))inactiveUrls.push(opt.getAttribute('data-img'));
  });
  // …sets #colorRenderImg.src from the active option, then background-preloads
  // the inactive sky so the toggle is instant. See the file for the full body.
}
```

Three things in this function are load-bearing and easy to get wrong:

- **A `null` cid is a failure, not a no-op.** An earlier build returned early and left
  the previous config's façade on screen. That is exactly the wrong behavior — the card
  would silently show another configuration's glass. It now logs and drops to the
  `unavailable` state.
- **Every URL carries `RENDER_V`.** Render batches replace `.webp` files under identical
  names, so a JS-assigned `img.src` hits the HTTP cache and serves the old pixels even
  after Ctrl+Shift+R. The token is content-derived and rewritten by the pre-commit hook —
  never hand-edit it, never bypass the hook.
- **The inactive sky is preloaded** on every config change, which is what makes the sky
  toggle feel instant.

The data card itself stays 1:1: the user always sees the **exact** optical numbers and Lab
values for *their* selection from the JSON — only the *image* is shared across a cluster.

---

## 3. The weather toggle

A pill toggle (`.sky-toggle`) with two options (Overcast / Partly Clear). Selecting one:

1. moves `.active` to the chosen option,
2. sets `#colorRenderImg.src` to that option's `data-img` (already repointed to the current `cid` by `setAnchorImages`),
3. slides `#skyThumb` under the active label (width + `translateX`).

Both options are width-matched to the wider one so the control is symmetric and the thumb
travels a consistent width. Widths are re-equalized on resize and after the web font loads
(glyph widths shift on font swap). See the IIFE at `enthermal-configurator.html` ≈ line 1476.

---

## 4. The zoom lightbox

The image (or its magnifier button `#colorZoomBtn`) opens a full-screen lightbox
(`#imgZoomOverlay` / `#imgZoomFull`). Inside, the user can step through the two sky
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
