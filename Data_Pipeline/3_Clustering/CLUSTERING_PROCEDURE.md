# Clustering & Delivery — How 6,862 Configs Become 137 Renders

> The full render pipeline outside Blender: the algorithm that collapses every product
> configuration onto a small set of render anchors (Part 1), why the approach was revised
> in June 2026 (Part 1·B), and the delivery system that swaps the right render into the
> configurator (Part 2). The clustering is implemented in
> [recluster_at_jnd.py](recluster_at_jnd.py); every number here
> reflects what that script actually produces against the current dataset.
>
> **This is the single source of truth for clustering & delivery.** (It absorbs the former
> `Data_Pipeline/3_Clustering/CLUSTERING_DECISIONS.md` revision log.)
>
> **Status:** Part 1 is live — the script produces the 137 anchors today. Part 2 is **now
> live too**: every config carries an integer `cid` (anchor id), the 137 anchors are
> rendered against three skies, and the app loads `App_Data/Anchor_Renders/<Sky>/anchor_<cid>.webp`
> per configuration. The earlier "static placeholder sky / not yet wired" state is gone.

---

## The problem in one sentence

There are **6,862 configurations** but rendering each one is wasteful, because exterior appearance is far less diverse — so we want the **fewest renders** such that **every config is within ΔE ≤ 1.5 of an image we actually produce, in the same exterior-substrate family**.

ΔE here is **CIEDE2000**, the perceptually-uniform color difference. On that scale, **< 1.0** is imperceptible even side-by-side, **1.0–2.0** is perceptible only on close side-by-side inspection, and **> 2.0** is perceptible at a glance. A configurator user never sees their true color next to the anchor render, so the side-by-side band is rarely exercised; **1.5** keeps the worst case inside it while roughly halving the render count versus a 1.0 ceiling.

---

## What we cluster on

Each config carries an exterior-reflected color in CIELAB: `extL` (lightness), `extA` (green↔red), `extB` (blue↔yellow). Treat each config as a **point in 3D color space**. Two choices define the geometry:

- **Metric = CIEDE2000, not ΔE76.** Plain Euclidean ΔE76 is hue-blind — it scores a blue→gray hue rotation the same as an equal-magnitude lightness nudge, even though the eye is far more sensitive to the rotation. CIEDE2000 down-weights lightness and handles hue/chroma correctly. (The original design used ΔE76; the switch is the central change in the June-2026 revision — see *Part 1·B*.)
- **Hard partition by exterior substrate.** Configs are grouped by their **exterior-facing glass substrate** (the hue family — Clear, Optiblue, Solarbronze, …) *before* clustering, and each family is clustered independently. A config can therefore only ever share an anchor with the **same** substrate, making "a blue tint rendered as a gray build" structurally impossible.
- **We cluster on `(extL, extA, extB)` only — not `routVis`.** routVis is redundant (3,133 distinct Lab tuples vs. 3,136 when routVis is added) and its 0.06–0.23 scale contributes ~nothing to an unweighted ΔE.

Safe to partition because the runtime key (the exterior Lab triple) has **zero cross-substrate collisions** — every Lab value belongs to exactly one substrate — so the partition never forces two different renders onto one lookup key.

---

## The procedure

The whole pipeline is **partitioned by substrate** ([`cluster_by_substrate`](recluster_at_jnd.py)): the four steps below run independently within each substrate family, then the per-family anchors are concatenated and given global ids. All steps are deterministic — no randomness, identical output every run.

### Step 0 — Collapse duplicates · [`unique_points`](recluster_at_jnd.py)
6,862 configs reduce to **3,133 distinct colors** (many configs share an exact exterior color). We deduplicate, remembering how many configs sit on each point (`weight`), and sort by Lab so everything downstream is reproducible.

### Step 1 — Cover the space · [`farthest_first_cover`](recluster_at_jnd.py)
The core, run per substrate. A greedy **k-center cover** (Gonzalez heuristic):

1. **Seed** with one anchor (the lexicographically smallest point — deterministic).
2. **Find the worst-served point**: for every point in the family, compute distance to the *nearest* current anchor; take the point **farthest** from all anchors — the most poorly-represented color.
3. **Within ΔE 1.5?**
   - Yes → every point is covered. **Stop.**
   - No → make that worst point a **new anchor**, update everyone's nearest-anchor distance, repeat from 2.

The loop *cannot exit* while any point exceeds ΔE 1.5 — that's what makes the guarantee hold by construction. k-means is rejected here because it minimizes *average* variance and would leave outliers beyond tolerance; a cover guarantees the hard per-config promise.

### Step 2 — Recenter each cluster · [`chebyshev_center`](recluster_at_jnd.py)
Farthest-first anchors tend to sit at cluster *edges* (they were chosen for being extreme). An edge anchor still satisfies the guarantee but is a poor representative image. So for each cluster we re-pick the anchor as the member whose **worst-case distance to all other members is smallest** (the discrete 1-center) — the most central real config, the best single stand-in. Lowers average error without changing cluster contents.

### Step 3 — Repair the guarantee · [`repair`](recluster_at_jnd.py)
Recentering can shift which anchor is nearest for a few edge points and, rarely, push one just past ΔE 1.5. So: while any point exceeds 1.5 from its nearest anchor, promote it to a new anchor and re-check. This only *adds*, so it always terminates — and restores the hard guarantee.

### Step 4 — Assign, emit & inject `cid`
Every color (and through it, all 6,862 configs) is assigned to its nearest anchor, recording the exact ΔE. Outputs:

| File | Contents |
|---|---|
| [App_Data/*.json](../../App_Data/) | The three config files, **rewritten with an integer `cid`** (anchor id) on every config for direct runtime lookup. **This step is the final writer of the JSON** — see *Reproducing*. |
| [anchors.csv](anchors.csv) | The 137 render targets — each a real stack for Blender, with color + member stats |
| [anchors.json](anchors.json) | The same 137 anchors, structured, with the parsed renderable `stack` per anchor (consumed by `build_anchor_render_configs.py`) |
| [cluster_assignments.csv](cluster_assignments.csv) | All 6,862 configs → cluster_id, code, `is_anchor`, `distance_to_anchor_dE` |
| [cluster_map.json](cluster_map.json) | `"L_a_b" → code` lookup — **debug only**; the app uses `config.cid`, not this map |
| [clustering_report.txt](clustering_report.txt) | Anchor count, ΔE stats, per-anchor breakdown |

---

## Result (current dataset)

| Metric | Value |
|---|---|
| Configurations | 6,862 |
| Distinct exterior colors | 3,133 |
| **Anchors (renders needed)** | **137** |
| Renders × 3 sky variants | 411 |
| **Max config→anchor ΔE2000** | **1.4164** (≤ 1.5 ✓) |
| Config-weighted mean ΔE2000 | 0.604 |
| Cluster size (min / median / max configs) | 3 / 38 / 262 |
| Substrate families | 8 — every cluster substrate-pure (0 mixed) |

Family sizes (anchors): Clear 66, Starphire 15, Solexia 12, Optiblue 10, Solargray 10, Optigray 9, Solarblue 8, Solarbronze 7. Anchor ids are deterministic (substrate, then lightness), which fixes the Blender frame order: **frame N = `cid` N−1**.

---

## Worked example — the worst case in the dataset

The most instructive config to trace is the one with the **largest** error anywhere — it shows the maximum the system ever tolerates. (Almost everything else is far tighter; the config-weighted mean is 0.60.)

### The config a user selects
```
Stack:  C270 Clear 6mm / Ar90 7.49mm / SKN183 Clear 6mm / Vacuum 0.25mm / Clear 6mm
Color:  extL = 43.65   extA = -4.41   extB = -3.57   (muted blue-green, Clear substrate)
```
A triple-glazed Enthermal Plus build whose exterior pane is a low-E-coated **Clear** lite.

### The anchor it lands on — `anchor_27`
```
Stack:  C270 Clear 6mm / Ar90 7.45mm / SKN183 Clear 6mm / Vacuum 0.25mm / Clear 6mm
Color:  extL = 44.58   extA = -4.21   extB = -4.84
```
The most central real config in its cluster (80 configs, 40 distinct colors) — **same Clear substrate family**, by construction.

### The distance
```
ΔE2000 = 1.4164          ← the largest error anywhere in all 6,862 configs
per-axis:  ΔL = -0.93   Δa = -0.20   Δb = +1.27
```
The worst-served user in the entire product line sees an image **1.4164 ΔE2000** from their true selection. The gap is almost entirely on the `b` (blue↔yellow) axis within the same hue family — a slight blue/yellow shift, not a hue rotation. Imperceptible without the two swatches side by side, which the tool never shows.

### What the user experiences
1. They configure this exact C270 / SKN183 triple-glaze build.
2. The readout shows **their** true numbers — U-value, their exact Lab — drawn straight from the JSON. *These are never approximated.*
3. The config's `cid` (27) resolves directly to `anchor_27`.
4. The browser loads `App_Data/Anchor_Renders/Overcast/anchor_27.webp` — a render of the cluster's central build, 1.42 ΔE away. Indistinguishable.

Across all 137 anchors, 6,862 configs collapse to 137 renders with no perceptible compromise and **no wrong-family renders** (0 configs rendered by a different substrate).

---

# Part 1·B — Why the design was revised (June 2026)

The original design (v1) and the current design (v2) differ as follows:

| | Original (v1) | Current (v2, 2026-06) |
|---|---|---|
| Color metric | ΔE76 (Euclidean CIELAB) | **CIEDE2000** (perceptually uniform) |
| Cross-substrate mixing | allowed | **forbidden — partitioned by exterior substrate** |
| Tolerance | ΔE76 ≤ 2.0 | **ΔE2000 ≤ 1.5** |
| Anchors (renders) | 77 | **137** |
| Worst-case config error | ΔE76 1.89 | **ΔE2000 1.4164** |
| Runtime lookup | Lab string key → `cluster_map.json` | **`config.cid`** (integer anchor id) |

### The defect we found
In the app, the **SB60 / Optiblue 6/6** config looked wrong on the color card — a blue glass that rendered grayish. Tracing it: that config (Lab `[33.51, −0.42, −5.08]`) was assigned under v1 to an anchor whose representative build was **SB70 Solargray** (Lab `[32.82, −0.35, −4.05]`). The two are ΔE76 ≈ 1.24 apart — *inside* the ≤ 2 tolerance — yet one is blue and the other a gray build. It was not isolated: **1,316 of 6,862 configs (19%)** were rendered by a *different exterior substrate*; stripping the benign Starphire→Clear case (low-iron reads as clear), **~251** were saturated tints (Optiblue, Solexia, Solarbronze, Optigray, Solarblue) rendered as gray or clear.

### Root cause — three layers
- **ΔE76 is hue-blind.** On the 251 problem configs the error was **1.5 : 1 hue-vs-lightness** with chroma barely changing (Δchroma ≈ 0.01) — the renders were not washed out, they were **pointed at the wrong hue**. ΔE76 scored those rotations as "≤ 2, fine."
- **The dataset is neutral-dominated.** ~4,000 of 6,862 configs are Clear glass clustered near the neutral axis, so each cluster's center is pulled toward neutral, stranding the few saturated tints on the rim where they inherit a near-neutral representative.
- **We validated against the metric that caused it.** "Every config ΔE76 ≤ 2" was self-referential — it proved the cover satisfied ΔE76, never that ΔE76 predicted *rendered* appearance. The first real test was a human eye on the Optiblue card.

### The fixes
- **CIEDE2000** (`dE()`, zero-dependency; cross-checked against an independent JS implementation, worst case agreed to 1.4164 on both) scores blue→gray as the large difference it visually is.
- **Hard substrate partition** (`cluster_by_substrate`) makes wrong-family renders structurally impossible; verified 0 of 137 clusters mix more than one substrate.
- **`cid` lookup** replaces the Lab-string-key contract (§ below), removing a whole class of cross-language formatting bugs.
- **Tolerance ΔE2000 ≤ 1.5** chosen over 1.0: with the substrate constraint the worst case (1.4164) is a *same-family* shift, not a hue error, and the tool never invites side-by-side scrutiny. Tightening to 1.0 nearly doubles renders (~242) to eliminate a difference only visible under scrutiny that never happens. ΔE2000 ≤ 2.0 would give ~93 anchors.
- **Starphire kept as its own family (15 anchors / 486 configs).** It is **low-iron** "water-white" glass; although Starphire↔Clear is benign by raw ΔE, the uniform substrate constraint renders it on its own substrate so the no-green-tint look a specifier pays for is preserved.

### The signed-zero bug (historical, now moot)
While still on the Lab-key design: Python `'%.2f' % -0.0` → `'-0.00'` but JS `(-0).toFixed(2)` → `'0.00'`, so eight configs with a negative-zero Lab component missed their lookup. The `cid` design removes runtime key formatting entirely, so this class of bug can no longer occur. `_fmt()`/`lab_key()` survive only for internal dedup and the debug `cluster_map`.

---

## Why not the alternatives

- **k-means** (the original spec): minimizes *average* variance and would leave outliers at ΔE 4–5 — a visible error for those configs. Farthest-first optimizes the **worst case**, which is exactly the JND promise.
- **One render per outer coating+substrate family:** tested under v1 — breaks tolerance for a large fraction of configs, because the inner pane shifts exterior color via back-reflection off interior low-E surfaces. Per-color clustering catches this; per-family does not.
- **ΔE76 without substrate partition (v1):** shipped, then failed on saturated tints — see *Part 1·B*.

---

## Reproducing

```
python Data_Pipeline/3_Clustering/recluster_at_jnd.py
```
Reads the three `App_Data/*.json` files; writes the outputs above into this directory (`Data_Pipeline/3_Clustering/`) **and rewrites `App_Data/*.json` with `cid` injected.** No dependencies beyond the Python standard library. Deterministic — re-running produces byte-identical output.

**Build order matters.** `recluster_at_jnd.py` is the **final writer** of `App_Data/*.json`:
```
1_Source_CSVs/*.csv
  → 2_Conversion/csv_to_json.py        # writes App_Data/*.json (base, no cid)
  → 3_Clustering/recluster_at_jnd.py   # clusters + INJECTS cid into App_Data/*.json
  → 4_Anchor_Specs/build_anchor_render_configs.py   # PyWinCalc/Blender build specs
```
Re-running `csv_to_json.py` alone **drops `cid`** — always re-run the clustering after it. To change tolerance / metric / constraint, edit `TOL`, `dE()`, or `cluster_by_substrate()`, re-run the script, then re-run the anchor-spec builder, then re-render.

---

# Part 2 — Delivery: getting renders to the browser

Part 1 produces 137 anchor images per sky. Part 2 is how the configurator shows the right one. **This is now implemented in the app** (it was a forward-looking plan in earlier revisions of this doc).

## The data card stays 1:1; only the image is shared

A user always sees the **exact** optical numbers (`uval`, `routVis`, `tvis`, Lab values) for *their* specific selection, drawn from the JSON — never anchor numbers. What's shared is only the *image*, and at ΔE2000 ≤ 1.5 within the same substrate family no runtime color correction is applied: the anchor image is imperceptibly close by construction, so it stands in unmodified.

## Resolving a config to its render — the `cid`

[CLAUDE.md](../../CLAUDE.md) forbids hand-editing `App_Data/*.json`, but the clustering script *is* the generator of that JSON, so it injects an integer **`cid`** (anchor id) onto every record at build time. The front-end reads `cid` directly — no Lab-key string formatting, no `cluster_map.json` fetch:

```js
// enthermal-configurator.html — setAnchorImages()
function setAnchorImages(cid){
  if(cid==null) return;                                  // keep last image rather than 404
  var code = 'anchor_' + String(cid).padStart(2,'0');    // 5 -> anchor_05, 135 -> anchor_135
  document.querySelectorAll('.sky-toggle-option').forEach(function(opt){
    var sky = opt.textContent.trim();                    // Clear | Overcast | Cloudy
    opt.setAttribute('data-img', 'App_Data/Anchor_Renders/'+sky+'/'+code+'.webp');
  });
  var active = document.querySelector('.sky-toggle-option.active');
  if(active) document.getElementById('colorRenderImg').src = active.getAttribute('data-img');
}
```
`setAnchorImages(match.cid)` is called whenever the configuration changes. The sky toggle and the zoom lightbox both read `data-img`, so they follow automatically. (The earlier design recomputed a `L_a_b` string key in JS and looked it up in `cluster_map.json`; that required byte-identical Python↔JS formatting and produced the signed-zero bug. The `cid` supersedes it.)

## Asset layout & the sky toggle

The 411 renders are organized by sky condition, filename keyed on the anchor code:
```
App_Data/Anchor_Renders/
  Clear/    anchor_00.webp … anchor_136.webp   (137)
  Overcast/ anchor_00.webp … anchor_136.webp   (137)   ← default
  Cloudy/   anchor_00.webp … anchor_136.webp   (137)
```
The **Exterior Color** card's three-option pill toggle (Clear / Overcast / Cloudy, default Overcast) swaps the visible `<img>` among the three skies for the current `cid`. The same image is reachable full-screen via the zoom lightbox (← / → step through skies).

## Format & hosting

- **Format:** WebP — universal browser support, already compressed (gzip/Brotli won't shrink it further).
- **Current hosting:** the renders ship **in-repo** under `App_Data/Anchor_Renders/`, loaded via relative paths alongside the JSON — same `fetch()`/HTTP requirement as the rest of the app (no `file://`). The set is **~637 MB** (411 files, ~1.6 MB each); only one render is fetched at a time (the current config × active sky), so first-load cost is one image, but the full deploy is large.
- **If this becomes a public high-traffic tool:** move the asset set to a CDN (e.g. GitHub Pages on a separate `luxwall-glass-assets` repo, or Cloudflare R2) and point the `data-img` base at it. At ~637 MB the set is near GitHub Pages' 1 GB soft storage limit and would benefit from a recompression pass (the current renders are high-resolution). Version by **path segment** (`/renders/v2/…`), never a query string (query strings defeat edge caching).

## Open items

| # | Item | Status |
|---|---|---|
| 1 | Run clustering against current data; pin anchor count | **done — 137 anchors, max ΔE2000 1.4164** |
| 2 | Config → render resolution | **done — per-config `cid` → `anchor_<cid>.webp`** |
| 3 | Render the anchor × sky batch | **done — 137 × 3 = 411 webp in `App_Data/Anchor_Renders/`** |
| 4 | Wire renders into the app (per-config swap + sky toggle + lightbox) | **done — `setAnchorImages()`** |
| 5 | Move assets to a CDN if traffic warrants | not started (in-repo today) |

## Superseded decisions (kept for reference)

- **ΔE76 metric / 77 anchors / ΔE ≤ 2.** Replaced by CIEDE2000 + substrate partition / 137 anchors / ΔE2000 ≤ 1.5 — ΔE76 rendered saturated tints as gray (see *Part 1·B*).
- **Lab-string-key runtime lookup via `cluster_map.json`.** Replaced by the per-config `cid`; `cluster_map.json` is retained as debug output only.
- **k-means clustering.** Replaced by farthest-first k-center cover — k-means leaves outliers beyond tolerance.
- **Static placeholder sky photo (`*_Set3.png`), same image for every config.** Replaced by per-config anchor renders now that the 411-image batch exists.
- **Delta-tint runtime correction / `mix-blend-mode: multiply`.** Deleted — at this tolerance there is no perceptible gap to correct.
