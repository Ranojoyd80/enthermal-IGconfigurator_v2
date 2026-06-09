# Clustering & Delivery — How 6,862 Configs Become 77 Renders

> The full render pipeline outside Blender: the algorithm that collapses every product configuration onto a small set of render anchors (Part 1), and how the configurator swaps the right render in (Part 2). The clustering is implemented in [recluster_at_jnd.py](ProductData/recluster_at_jnd.py); the numbers here reflect what that script actually produces against the current dataset.

---

## The problem in one sentence

There are **6,862 configurations** but rendering each one is wasteful, because exterior appearance is far less diverse — so we want the **fewest renders** such that **every config is within ΔE ≤ 2 of an image we actually produce**.

ΔE ≤ 2 is the **Just-Noticeable Difference (JND)** ceiling: under real viewing conditions (a single render in a browser, no reference swatch), no user can perceive the gap between their exact selection and the anchor image standing in for it. ΔE ≈ 1 is the strict ideal-conditions JND; 2 gives a safety margin while roughly halving the render count, and is safe precisely because a configurator user never sees two colors side by side.

---

## What we cluster on

Each config carries an exterior-reflected color in CIELAB: `extL` (lightness), `extA` (green↔red), `extB` (blue↔yellow). Treat each config as a **point in 3D color space**. Distance between two points is **ΔE76**:

```
ΔE = √( (ΔL)² + (Δa)² + (Δb)² )
```

Two important choices:

- **We cluster on `(extL, extA, extB)` only — not `routVis`.** routVis is redundant (3,133 distinct Lab tuples vs. 3,136 when routVis is added) and its 0.06–0.23 scale contributes ~nothing to an unweighted ΔE.
- **What physically drives the color is irrelevant to the math.** Two completely different glass builds (different coatings, gaps, layer order) that happen to look the same from outside are the same point. This is why per-family rendering fails (see *Why not the alternatives*) — clustering on the actual Lab vector captures appearance regardless of cause.

---

## The procedure

Five steps, all deterministic (no randomness — identical output every run). Function names link to the implementation.

### Step 1 — Collapse duplicates · [`unique_points`](ProductData/recluster_at_jnd.py)
6,862 configs reduce to **3,133 distinct colors** (many configs share an exact exterior color). We deduplicate, remembering how many configs sit on each point (`weight`), and sort by Lab so everything downstream is reproducible.

### Step 2 — Cover the space · [`farthest_first_cover`](ProductData/recluster_at_jnd.py)
The core. A greedy **k-center cover** (Gonzalez heuristic):

1. **Seed** with one anchor (the lexicographically smallest point — deterministic).
2. **Find the worst-served point**: for all 3,133 points, compute distance to the *nearest* current anchor; take the point that is **farthest** from all anchors — the most poorly-represented color.
3. **Within ΔE 2?**
   - Yes → every point is covered. **Stop.**
   - No → make that worst point a **new anchor**, update everyone's nearest-anchor distance, repeat from 2.

It keeps planting an anchor on whatever color is currently most uncovered. Because each new anchor targets the worst offender, anchors spread efficiently. The loop *cannot exit* while any point exceeds ΔE 2 — that's what makes the guarantee hold by construction. Lands ~73 anchors.

### Step 3 — Recenter each cluster · [`chebyshev_center`](ProductData/recluster_at_jnd.py)
Farthest-first anchors tend to sit at cluster *edges* (they were chosen for being extreme). An edge anchor still satisfies the guarantee but is a poor representative image. So for each cluster we re-pick the anchor as the member whose **worst-case distance to all other members is smallest** (the discrete 1-center) — the most central real config, the best single stand-in. Lowers average error without changing cluster contents.

### Step 4 — Repair the guarantee · [`repair`](ProductData/recluster_at_jnd.py)
Recentering can shift which anchor is nearest for a few edge points and, rarely, push one just past ΔE 2. So: while any point exceeds 2.0 from its nearest anchor, promote it to a new anchor and re-check. This only *adds*, so it always terminates — and restores the hard guarantee. This step is why the final count is **77, not 73**: 4 extra anchors bought to keep the promise airtight.

### Step 5 — Assign & emit
Every color (and through it, all 6,862 configs) is assigned to its nearest anchor, recording the exact ΔE. Outputs:

| File | Contents |
|---|---|
| [anchors.csv](ProductData/anchors.csv) | The 77 render targets — each a real stack for Blender, with color + member stats |
| [cluster_assignments.csv](ProductData/cluster_assignments.csv) | All 6,862 configs → cluster_id, code, `is_anchor`, `distance_to_anchor_dE` |
| [cluster_map.json](ProductData/cluster_map.json) | `"L_a_b" → code` lookup the front-end uses at runtime |
| [clustering_report.txt](ProductData/clustering_report.txt) | Anchor count, ΔE stats, per-anchor breakdown |

---

## Result (current dataset)

| Metric | Value |
|---|---|
| Configurations | 6,862 |
| Distinct exterior colors | 3,133 |
| **Anchors (renders needed)** | **77** |
| Renders × 3 HDR variants | 231 |
| **Max config→anchor ΔE** | **1.89** (≤ 2.0 ✓) |
| Config-weighted mean ΔE | 0.86 |
| Cluster size (min / median / max configs) | 3 / 69 / 463 |

---

## Worked example — the worst case in the dataset

The most instructive config to trace is the one with the **largest** error anywhere — it shows the maximum the system ever tolerates. (Almost everything else is far tighter.)

### The config a user selects
```
Stack:  SB70 Clear 6mm / Ar90 7.49mm / SKN183 Clear 6mm / Vacuum 0.25mm / Clear 6mm
Color:  extL = 46.13   extA = -4.44   extB = -6.33   (muted blue-green)
Specs:  U-value 0.2541   SHGC 0.2030   Tvis 0.5404
```
A specific triple-glazed Enthermal Plus build — one point in Lab space.

### The anchor it lands on — `anchor_57`
```
Stack:  SKN183 Clear 6mm / Vacuum 0.25mm / Clear 4mm / Ar90 11.25mm / C270 Clear 4mm
Color:  extL = 46.42   extA = -5.96   extB = -5.24
```
A **completely different physical build** — different coatings, layer order, and gaps — whose *exterior color* is nearly identical. The clustering matched them on appearance, not construction.

### The distance
```
ΔE = 1.8928          ← the largest error anywhere in all 6,862 configs
per-axis:  ΔL = -0.29   Δa = +1.52   Δb = -1.09
```
The worst-served user in the entire product line sees an image **1.89 ΔE** from their true selection — still under the JND ceiling, imperceptible in a browser. The gap is mostly in `a` (a hair less green); invisible without the two swatches side by side.

### Why this anchor and not another
```
configs sharing anchor_57: 48   (22 distinct colors collapse here)
next-nearest anchor (anchor_20): ΔE = 1.940
```
`anchor_57` is this config's closest anchor; `anchor_20` is 1.94 away, even farther — so `anchor_57` is the right home. This config sits in a sparse region where anchors are ~2 apart: 1.89 to its best, 1.94 to its second-best. It is exactly the kind of point **Step 4 (repair)** guards — had no anchor been within 2.0, this config itself would have been promoted to anchor #78.

### What the user experiences
1. They configure this exact SB70 / SKN183 triple-glaze build.
2. The readout shows **their** true numbers — U-value 0.2541, their exact Lab — drawn straight from the JSON. *These are never approximated.*
3. `cluster_map.json` resolves their color `46.13_-4.44_-6.33` → `anchor_57`.
4. The browser loads `anchor_57_overcast.webp` — a render of a different build that looks 1.89 ΔE away. Indistinguishable.

48 configs (22 distinct colors) share this one image, and the person who picks the worst-fitting of them still can't tell. Across all 77 anchors, 6,862 configs collapse to 77 renders with no perceptible compromise.

---

## Why not the alternatives

- **k-means** (the original spec): minimizes *average* variance and would leave outliers at ΔE 4–5 — a visible error for those configs. It optimizes the wrong quantity. Farthest-first optimizes the **worst case**, which is exactly the JND promise.
- **One render per outer coating+substrate family (27 groups):** tested — breaks ΔE 2 for **25% of configs** (worst 5.6 ΔE), because the inner pane shifts exterior color via back-reflection off interior Low-E surfaces. Per-color clustering catches this; per-family does not. Also strictly dominated: family-based is 81 renders, while ΔE ≤ 3 clustering is 111 renders *with* a bounded guarantee, and ΔE ≤ 4 is just 57.

---

## Reproducing

```
python ProductData/recluster_at_jnd.py
```
Reads the three `data/*.json` files, writes the four outputs into [ProductData/](ProductData/). No dependencies beyond the Python standard library. Deterministic — re-running produces byte-identical output. To re-pin the anchor count after a data change, regenerate the JSON ([csv_to_json.py](ProductData/csv_to_json.py)) and re-run this script.

To target a different tolerance, change `TOL` at the top of the script. **ΔE 2 → 77** is the verified full-pipeline figure (cover + recenter + repair). For rough scale at other tolerances, the bare greedy cover gives ΔE 4 → 19 · ΔE 3 → 37 · ΔE 1.5 → 119 (recenter+repair would nudge each up a few); re-run the script at the chosen `TOL` to pin the exact number.

---

# Part 2 — Delivery: getting renders to the browser

Part 1 produces 77 anchor images. Part 2 is how the configurator shows the right one. The two halves are independent — they meet only at the **cluster code** (`anchor_57`) and the **URL convention**. Front-end work and render work can proceed in parallel.

## The data card stays 1:1; only the image is shared

A user always sees the **exact** optical numbers (`uval`, `routVis`, `tvis`, Lab values) for *their* specific selection, drawn from the relevant JSON file — never anchor numbers. What's shared is only the *image*. At ΔE ≤ 2 no runtime color correction is applied: the anchor image is imperceptibly close by construction (Part 1), so it stands in unmodified. The browser paints the CDN bytes verbatim.

## Resolving a config to its code — runtime map, no JSON edits

[CLAUDE.md](CLAUDE.md) forbids hand-editing `data/*.json`, so the code is **not** stored per-record. Instead the front-end fetches [cluster_map.json](ProductData/cluster_map.json) once and looks the code up by the record's own Lab values:

```js
// labKey MUST match the script's format exactly: '%.2f_%.2f_%.2f'
function labKey(m) {
  return `${m.extL.toFixed(2)}_${m.extA.toFixed(2)}_${m.extB.toFixed(2)}`;
}
const code = clusterMap[labKey(match)];   // e.g. "anchor_57"
```

This keeps the JSON untouched and fully regenerable: re-run the clustering script and `cluster_map.json` updates itself. (The earlier design embedded a `code` field in `DATA`; the runtime map supersedes it to avoid mutating the JSON.)

## URL convention

Each anchor is rendered against **three HDR backgrounds** (Overcast Kloofendal 38, Partly Cloudy Kloofendal 38, Partly Cloudy Kloofendal 48 — see `POST_PROCESSING_PRIMER.md` for the HDR locks). The URL encodes both the anchor code and the HDR variant:

```js
const RENDER_BASE = 'https://ranojoyd80.github.io/luxwall-glass-assets/renders/v1';

// hdr is one of: 'overcast' | 'pc38' | 'pc48'
function buildRenderUrl(code, hdr) {
  return `${RENDER_BASE}/${code}_${hdr}.webp`;   // .../anchor_57_overcast.webp
}
```

Version lives in the **path segment** (`/renders/v1/`), not a query string — query strings defeat browser and CDN edge caching. A new batch becomes `/renders/v2/` and `buildRenderUrl()` is the only function that changes.

> **Open UI decision:** how does the configurator pick which HDR to show? (a) fixed default, (b) user toggle/dropdown, (c) slow animated cycle. The URL convention accommodates all three; the choice affects only the UI, not the asset pipeline.

## Front-end image swap pattern

The configurator's `updateColor()` previously painted a CSS gradient onto a window mock. The new pattern swaps a pre-rendered `<img>` `src` with a cross-fade — no canvas, no pixel math. Two stacked `<img>` layers plus a gradient fallback `<div>`; one visible at a time via a `.visible` opacity transition.

```html
<div class="glass-stage">
  <img id="renderA" class="render-layer" alt="">
  <img id="renderB" class="render-layer" alt="">
  <div id="glassFallback" class="render-layer fallback"></div>
  <div id="glassLoading" class="loading-spinner"></div>
</div>
```
```css
.render-layer { position: absolute; inset: 0; opacity: 0; transition: opacity 500ms ease; }
.render-layer.visible { opacity: 1; }
```

`updateColor()` swaps the next layer's `src` and cross-fades. If the image 404s (render not yet produced), `onerror` calls `paintGradientFallback()` — the original gradient logic, kept as the fallback path. The front-end can therefore ship **before any renders exist**; each product upgrades from gradient to photo as renders land.

```js
let activeLayer = 'a';
let currentHdr = 'overcast'; // or driven by UI control once decided

function updateColor(match) {
  if (!match) match = findMatch();
  if (!match) return;

  // Lab readout — unchanged, always reflects the user's exact selection
  const L = showInterior ? match.intL : match.extL;
  // ... a, b likewise

  const code = clusterMap[labKey(match)];      // runtime lookup (above)
  const url = buildRenderUrl(code, currentHdr);
  const nextId = activeLayer === 'a' ? 'renderB' : 'renderA';
  const prevId = activeLayer === 'a' ? 'renderA' : 'renderB';
  const next = document.getElementById(nextId);
  const prev = document.getElementById(prevId);
  const fallback = document.getElementById('glassFallback');

  next.onload = () => {
    next.classList.add('visible');
    prev.classList.remove('visible');
    fallback.classList.remove('visible');
    activeLayer = activeLayer === 'a' ? 'b' : 'a';
  };
  next.onerror = () => {
    paintGradientFallback(L, a, b, fallback);
    fallback.classList.add('visible');
    next.classList.remove('visible');
    prev.classList.remove('visible');
  };
  next.src = url;
}
```

## Hosting — GitHub Pages, public assets repo

- **Repository:** `luxwall-glass-assets` (public, separate from the configurator HTML repo)
- **Path:** `/renders/v1/{code}_{hdr}.webp`
- **Format:** WebP — universal browser support, ~25% of equivalent PNG size.

### Storage budget

At ~200 KB per WebP and three HDR variants per anchor, the pinned **77 anchors** are the real figure:

| Anchor count | Total renders | Approx. library size |
|---|---|---|
| **77 (pinned, ΔE ≤ 2)** | **231** | **~46 MB** |
| 19 (if ΔE ≤ 4) | 57 | ~11 MB |
| 119 (if ΔE ≤ 1.5) | 357 | ~70 MB |

GitHub Pages soft limits are 1 GB stored / 100 GB bandwidth per month — comfortably below both.

- **Don't preload.** First load per (code, HDR) is one roundtrip (~50–100 ms); the browser caches it, so repeat views are instant.

### Versioning

Keep only `v_current/` and `v_previous/`: on rebuild, rename `v_current/` → `v_previous/` and write a fresh `v_current/`. Caps storage at ~90 MB regardless of release count and gives instant rollback. Numbered dirs (`v1/`, `v2/`, …) accumulate forever — avoided.

### Migration path

If this becomes a public high-traffic marketing tool, Cloudflare R2 ($0/month at low traffic, real CDN) is the upgrade target. GitHub Pages is right for current scale.

## Integration order

1. **Set up the assets repo** — empty `luxwall-glass-assets`, Pages enabled.
2. **Ship `cluster_map.json`** — generated by the clustering script; fetched at runtime.
3. **Resolve the HDR UI decision** — fixed default, toggle, or cycle.
4. **Drop in the new `updateColor()`** — fetches from `RENDER_BASE`, falls back to gradient when nothing is there.
5. **Ship the front-end** — every product shows a gradient because the assets repo is empty.
6. **Render the 77 anchors in Blender** — overnight to two-day batch depending on farm.
7. **Upload renders** — each code instantly upgrades from gradient to photo, no front-end change.

## Open items

| # | Item | Status |
|---|---|---|
| 1 | Run clustering against current data; pin anchor count | **done — 77 anchors, max ΔE 1.89** |
| 2 | Config → code resolution strategy | **done — runtime `cluster_map.json` lookup** |
| 3 | Create `luxwall-glass-assets` repo + enable Pages | not started |
| 4 | Decide HDR UI model — fixed / toggle / cycle | not started |
| 5 | Render the anchor × HDR batch | gated on shader validation (`CLAUDE_GLASS_SHADER.md`) and farm selection |

## Superseded decisions (kept for reference)

- **ΔE = 6 / 32 clusters.** Replaced by ΔE ≤ 2 / JND (77 anchors). The looser tolerance required runtime correction; the tighter one does not.
- **Delta-tint runtime correction via `mix-blend-mode: multiply`.** Deleted — at JND there is no perceptible gap to correct.
- **k-means clustering.** Replaced by farthest-first k-center cover (see Part 1) — k-means leaves outliers beyond tolerance.
- **Embedded `code` field in `DATA`.** Replaced by the runtime `cluster_map.json` lookup, so the JSON is never hand-edited.
- **Single image per anchor.** Replaced by three images per anchor (one per locked HDR variant).
