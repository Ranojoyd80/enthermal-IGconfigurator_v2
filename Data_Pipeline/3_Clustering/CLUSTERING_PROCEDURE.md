# Clustering & Delivery — How 6,444 Configs Become 202 Renders

> The full render pipeline outside Blender: the algorithm that collapses every product
> configuration onto a small set of render anchors (Part 1), why the approach was revised
> — first in June 2026 (Part 1·B) and again in July 2026 (Part 1·C) — and the delivery
> system that swaps the right render into the configurator (Part 2). The clustering is
> implemented in [recluster_at_jnd.py](recluster_at_jnd.py); every number here reflects what
> that script actually produces against the current dataset.
>
> **This is the single source of truth for clustering & delivery.** (It absorbs the former
> `Data_Pipeline/3_Clustering/CLUSTERING_DECISIONS.md` revision log.)
>
> **Status:**
> - **Part 1 (clustering) — live and current.** The script produces **202 anchors** today
>   against the July 2026 dataset using the **two-axis** metric (exterior-reflected *and*
>   transmitted color). Every config carries a **1-based** integer `cid` (anchor id).
> - **Part 2 (renders + app) — DONE (July 2026).** The 202-anchor × two-sky
>   (Overcast + Partly Clear) batch has been rendered, converted to WebP, and shipped under
>   `App_Data/Anchor_Renders/{Overcast,PartlyClear}/anchor_01…anchor_202.webp` (1-based). The
>   app's sky toggle is now two options (Overcast default + Partly Clear) and its defaults
>   point at `anchor_01`. "Partly Clear" resolves to the space-free `PartlyClear/` folder via
>   each option's `data-folder` attribute.

---

## The problem in one sentence

There are **6,444 configurations** but rendering each one is wasteful, because visible appearance is far less diverse — so we want the **fewest renders** such that **every config is within ΔE ≤ 1.5 of an image we actually produce on its exterior-reflected color, AND within ΔE ≤ 3.0 on its transmitted color, in the same exterior-substrate family**.

ΔE here is **CIEDE2000**, the perceptually-uniform color difference. On that scale, **< 1.0** is imperceptible even side-by-side, **1.0–2.0** is perceptible only on close side-by-side inspection, and **> 2.0** is perceptible at a glance. A configurator user never sees their true color next to the anchor render, so the side-by-side band is rarely exercised.

---

## What we cluster on — two color axes

Each config carries **two** CIELAB colors:

- **Exterior reflected** `(extL, extA, extB)` — what the glass reflects toward the viewer. This dominates the daytime façade render (sky, clouds, surroundings), so it is held **tight: ΔE ≤ 1.5**.
- **Transmitted** `(trnL, trnA, trnB)` — what you see *through* the glass. Only faintly visible through the dark building interior in the render, so it gets a **looser guard: ΔE ≤ 3.0** — enough to kill gross see-through mismatches without exploding the anchor count.

Treat each config as a **linked pair of points**, one in each color space. Three choices define the geometry:

- **Metric = CIEDE2000, not ΔE76**, on *each* axis. Plain Euclidean ΔE76 is hue-blind — it scores a blue→gray rotation the same as an equal lightness nudge. CIEDE2000 handles hue/chroma correctly. (See *Part 1·B* for the June switch.)
- **Combined by a normalized max (`pdist`).** The two axes are combined as
  `pdist(p,q) = max( ΔE_ext/1.5 , ΔE_trn/3.0 )`. Dividing each axis by its own tolerance puts both on a common scale; the **max** encodes an **AND** — a config is covered only when it is within budget on *both* axes (`pdist ≤ 1`). The covered region is an **anisotropic box**: narrow (1.5) in reflection, wide (3.0) in transmission.
- **Hard partition by exterior substrate.** Configs are grouped by their exterior-facing glass substrate (the hue family — Clear, Optiblue, Solarbronze, …) *before* clustering, and each family is clustered independently. A config can only ever share an anchor with the **same** substrate, making "a blue tint rendered as a gray build" structurally impossible.

Why two axes: reflection and transmission are largely **independent** — configs matched on reflection can diverge by up to ΔE ~11 in transmission (a different inner low-E, a different pane count, or Enthermal 2-pane vs Plus 3-pane). Clustering on reflection alone left ~⅓ of configs with a clearly-different see-through color; the transmission guard fixes that. (See *Part 1·C*.)

---

## The procedure

The whole pipeline is **partitioned by substrate** ([`cluster_by_substrate`](recluster_at_jnd.py)): the steps below run independently within each substrate family, then the per-family anchors are concatenated and given global 1-based ids. All steps are deterministic — no randomness, identical output every run.

### Step 0 — Collapse duplicates · [`unique_points`](recluster_at_jnd.py)
6,444 configs reduce to **2,941 distinct color pairs** (many configs share an exact `(ext, trn)` pair). We deduplicate, remembering how many configs sit on each point (`weight`), and sort by `(ext, trn)` so everything downstream is reproducible.

### Step 1 — Cover the space · [`farthest_first_cover`](recluster_at_jnd.py)
The core, run per substrate. A greedy **k-center cover** (Gonzalez heuristic) under `pdist`:

1. **Seed** with one anchor (the pre-sorted first point — deterministic).
2. **Find the worst-served point**: for every point, compute `pdist` to the *nearest* current anchor; take the point **farthest** from all anchors.
3. **Within tolerance (`pdist ≤ 1`, i.e. both axes within budget)?**
   - Yes → every point is covered. **Stop.**
   - No → make that worst point a **new anchor**, update everyone's nearest-anchor distance, repeat from 2.

The loop *cannot exit* while any point exceeds tolerance on either axis — that's what makes the guarantee hold by construction. k-means is rejected: it minimizes *average* variance and would leave outliers beyond tolerance; a cover guarantees the hard per-config promise.

### Step 2 — Recenter each cluster · [`chebyshev_center`](recluster_at_jnd.py)
Farthest-first anchors sit at cluster *edges*. So for each cluster we re-pick the anchor as the member whose **worst-case `pdist` to all other members is smallest** (the discrete 1-center under the combined metric) — the most central real config in **both** color spaces at once. Lowers average error without changing cluster contents.

### Step 3 — Repair the guarantee · [`repair`](recluster_at_jnd.py)
Recentering can push a few edge points just past tolerance. So: while any point exceeds `pdist = 1` from its nearest anchor, promote it to a new anchor and re-check. This only *adds*, so it always terminates — and restores the hard two-axis guarantee.

### Step 4 — Assign, emit & inject `cid`
Every color pair (and through it, all 6,444 configs) is assigned to its nearest anchor, recording the exact per-axis ΔE. Outputs:

| File | Contents |
|---|---|
| [App_Data/*.json](../../App_Data/) | The three config files, **rewritten with a 1-based integer `cid`** on every config for direct runtime lookup. **This step is the final writer of the JSON** — see *Reproducing*. |
| [anchors.csv](anchors.csv) | The 202 render targets — each a real stack for Blender, with exterior + transmitted color and per-axis member stats |
| [anchors.json](anchors.json) | The same 202 anchors, structured, with the parsed renderable `stack` per anchor (consumed by `build_anchor_render_configs.py`) |
| [cluster_assignments.csv](cluster_assignments.csv) | All 6,444 configs → cluster_id, code, `is_anchor`, `ext_dE_to_anchor`, `trn_dE_to_anchor` |
| [cluster_map.json](cluster_map.json) | `"colorKey" → code` lookup — **debug only**; the app uses `config.cid`, not this map |
| [clustering_report.txt](clustering_report.txt) | Anchor count, per-axis ΔE stats, per-anchor breakdown |

---

## Result (current dataset)

| Metric | Value |
|---|---|
| Configurations | 6,444 |
| Distinct color pairs (ext + trn) | 2,941 |
| **Anchors (renders needed)** | **202** |
| Renders × 2 sky variants | 404 |
| **Max config→anchor ΔE2000 — exterior** | **1.4576** (≤ 1.5 ✓) |
| **Max config→anchor ΔE2000 — transmitted** | **2.8610** (≤ 3.0 ✓) |
| Config-weighted mean ΔE2000 — exterior | 0.487 |
| Config-weighted mean ΔE2000 — transmitted | 0.714 |
| Cluster size (min / median / max configs) | 3 / 28 / 170 |
| Substrate families | 8 — every cluster substrate-pure (0 mixed) |

Family sizes (anchors): Clear 109, Solargray 17, Optiblue 16, Optigray 15, Solexia 15, Solarbronze 12, Solarblue 11, Starphire 7. Anchor ids are deterministic (substrate, then exterior lightness) and **1-based**, which fixes the Blender frame order: **frame N = `cid` N** (no off-by-one).

---

## Worked example — the worst cases in the dataset

Two configs are worth tracing: the largest error on each axis. Almost everything else is far tighter (config-weighted means 0.49 ext / 0.71 trn).

### Worst exterior error — ΔE2000 1.4576
```
User's config: C366 Clear 4mm / Ar90 13.36mm / Clear 4mm / Vacuum 0.25mm / SB70 Clear 4mm
               ext (44.39, -3.11, -4.21)   (muted blue-green, Clear substrate)
Lands on cid 30 / anchor_30:
               C366 Clear 4mm / Ar90 13.45mm / C270 Clear 4mm / Vacuum 0.25mm / Clear 4mm
               ext (43.07, -2.90, -3.30)
```
A physically different build (different VIG-pane low-E: SB70 vs C270), yet its exterior reflected color is nearly identical and it is in the **same Clear family** by construction. The 1.4576 gap is almost entirely on `b` (blue↔yellow) — a slight shift, not a hue rotation. Imperceptible without the two swatches side by side, which the tool never shows.

### Worst transmitted error — ΔE2000 2.8610
```
User's config: SB60 Solarbronze 5mm / Ar90 12.58mm / Clear 4mm / Vacuum 0.25mm / SB60 Clear 4mm
Lands on cid 153 / anchor_153:
               SB60 Solarbronze 6mm / Vacuum 0.25mm / Clear 5mm / Ar90 10.07mm / C272 Clear 5mm
```
Same Solarbronze exterior, so the reflected façade matches tightly; the 2.86 difference is in what you'd see *through* the glass — held under the 3.0 transmission guard, and barely visible anyway through the dark interior.

### What the user experiences
1. They configure their exact build.
2. The readout shows **their** true numbers — U-value, their exact Lab — drawn straight from the JSON. *These are never approximated.*
3. The config's `cid` resolves directly to `anchor_<cid>` (e.g. cid 30 → `anchor_30`).
4. The browser loads `App_Data/Anchor_Renders/<Sky>/anchor_30.webp` — the cluster's central build. Indistinguishable.

Across all 202 anchors, 6,444 configs collapse to 202 renders with no perceptible compromise and **no wrong-family renders** (0 configs rendered by a different substrate).

---

# Part 1·B — Why the design was revised (June 2026)

The original design (v1) and the June design (v2) differ as follows:

| | Original (v1) | June (v2) |
|---|---|---|
| Color metric | ΔE76 (Euclidean CIELAB) | **CIEDE2000** (perceptually uniform) |
| Cross-substrate mixing | allowed | **forbidden — partitioned by exterior substrate** |
| Tolerance | ΔE76 ≤ 2.0 | **ΔE2000 ≤ 1.5** (exterior only) |
| Anchors (renders) | 77 | **137** |
| Runtime lookup | Lab string key → `cluster_map.json` | **`config.cid`** (integer anchor id) |

### The defect we found
In the app, the **SB60 / Optiblue 6/6** config looked wrong — a blue glass that rendered grayish. That config (Lab `[33.51, −0.42, −5.08]`) was assigned under v1 to an anchor whose representative build was **SB70 Solargray** (Lab `[32.82, −0.35, −4.05]`), ΔE76 ≈ 1.24 apart — *inside* tolerance — yet one is blue and the other gray. Not isolated: **1,316 of 6,862 configs (19%)** were rendered by a *different exterior substrate*; stripping the benign Starphire→Clear case, **~251** were saturated tints rendered as gray or clear.

### Root cause — three layers
- **ΔE76 is hue-blind.** On the 251 problem configs the error was **1.5 : 1 hue-vs-lightness** with chroma barely changing — the renders were **pointed at the wrong hue**, and ΔE76 scored those rotations as "≤ 2, fine."
- **The dataset is neutral-dominated.** Most configs are Clear glass near the neutral axis, pulling each cluster center toward neutral and stranding saturated tints on the rim with a near-neutral representative.
- **We validated against the metric that caused it.** "Every config ΔE76 ≤ 2" was self-referential. The first real test was a human eye on the Optiblue card.

### The fixes
- **CIEDE2000** (`dE()`, zero-dependency) scores blue→gray as the large difference it visually is.
- **Hard substrate partition** (`cluster_by_substrate`) makes wrong-family renders structurally impossible.
- **`cid` lookup** replaces the Lab-string-key contract, removing a class of cross-language formatting bugs (including the signed-zero bug below).

### The signed-zero bug (historical, now moot)
On the old Lab-key design: Python `'%.2f' % -0.0` → `'-0.00'` but JS `(-0).toFixed(2)` → `'0.00'`, so configs with a negative-zero Lab component missed their lookup. The `cid` design removes runtime key formatting entirely. `_fmt()`/`lab_key()` survive only for internal dedup and the debug `cluster_map`.

---

# Part 1·C — Two-axis revision (July 2026)

Two changes landed together on the July 2026 dataset:

| | June (v2) | July (v3) |
|---|---|---|
| Dataset | 6,862 configs | **6,444** (new source CSVs; transmitted color added, interior-reflected dropped) |
| Clustered on | exterior reflected only | **exterior reflected + transmitted** (two-axis `pdist`) |
| Tolerance | ext ≤ 1.5 | **ext ≤ 1.5 AND trn ≤ 3.0** |
| Anchors | 137 | **202** (ext-only on the new data would have been 129) |
| `cid` numbering | 0-based (`anchor_00…`) | **1-based (`anchor_01…`)** — frame N = cid N |
| Skies | Clear / Overcast / Cloudy (3) | **Overcast + Partly Clear (2)** |

### Why transmission was added
The June design clustered on exterior reflection alone. Measuring the *transmitted*-color spread inside each reflection cluster showed the two axes are largely independent: **~⅓ of configs (2,139)** were served a render whose transmitted color differed by ΔE > 3, with the worst at **11.45** — a clearly-different see-through appearance for the same reflected façade. Adding transmission as a second, looser gate (`trn ≤ 3.0`) pulls every config's transmitted color under 3.0 (worst now 2.86) for **+73 anchors** (129 → 202), far cheaper than a symmetric two-axis tolerance (~277) because reflection stays tight while transmission only needs a coarse guard.

### Why 1-based `cid`
Blender frames are 1-indexed; anchors were 0-indexed, forcing a `frame = cid + 1` bridge and the ever-present off-by-one risk. `CID_BASE = 1` in the script makes **frame N render `cid` N** directly — `anchor_01.webp` is frame 1. Internal cluster arrays stay 0-based; the offset is applied only where a `cid` is emitted.

### Why the `max` combination (not a sum/average)
An average would let a config be egregiously wrong on transmission yet "pass" by being perfect on reflection — exactly the failure we're preventing. The normalized `max` forces both axes individually under tolerance. See *What we cluster on*.

---

## Why not the alternatives

- **k-means:** minimizes *average* variance and would leave outliers at ΔE 4–5. Farthest-first optimizes the **worst case** — the JND promise.
- **One render per outer coating+substrate family:** breaks tolerance for many configs, because the inner pane shifts exterior color via back-reflection. Per-color clustering catches this.
- **Symmetric two-axis tolerance (ext ≤ 1.5 AND trn ≤ 1.5):** ~277 anchors — buys transmission fidelity the dark-interior render can't show. The asymmetric guard (trn ≤ 3.0) gets the benefit at 202.
- **Blending reflection + transmission into one "perceived" color:** only meaningful for a dusk/lit-interior render, which the app does not show; the two daytime skies are reflection-dominated.

---

## Reproducing

```
python Data_Pipeline/3_Clustering/recluster_at_jnd.py
```
Reads the three `App_Data/*.json` files; writes the outputs above into this directory **and rewrites `App_Data/*.json` with `cid` injected.** No dependencies beyond the Python standard library. Deterministic — re-running produces byte-identical output.

**Build order matters.** `recluster_at_jnd.py` is the **final writer** of `App_Data/*.json`:
```
1_Source_CSVs/*.csv
  → 2_Conversion/csv_to_json.py        # writes App_Data/*.json (base, no cid)
  → 3_Clustering/recluster_at_jnd.py   # clusters + INJECTS cid into App_Data/*.json
  → 4_Anchor_Specs/build_anchor_render_configs.py   # PyWinCalc/Blender build specs + render_manifest.csv
```
Re-running `csv_to_json.py` alone **drops `cid`** — always re-run the clustering after it. To change tolerances / metric / constraint, edit `TOL_EXT` / `TOL_TRN`, `dE()` / `pdist()`, or `cluster_by_substrate()`, re-run the script, then re-run the anchor-spec builder, then re-render.

---

# Part 2 — Delivery: getting renders to the browser

Part 1 produces 202 anchor images per sky. Part 2 is how the configurator shows the right one.

> **Status note (July 2026):** DONE. The delivery *mechanism* (`config.cid` → `anchor_<cid>.webp`)
> and the shipped assets + app sky toggle are all on the **202-anchor / two-sky (Overcast +
> Partly Clear) / 1-based** layout described below. The former *pending* items are complete.

## The data card stays 1:1; only the image is shared

A user always sees the **exact** optical numbers (`uval`, `routVis`, `tvis`, Lab values) for *their* specific selection, drawn from the JSON — never anchor numbers. What's shared is only the *image*, imperceptibly close by construction, so it stands in unmodified (no runtime color correction).

## Resolving a config to its render — the `cid`

[CLAUDE.md](../../CLAUDE.md) forbids hand-editing `App_Data/*.json`, but the clustering script *is* the generator of that JSON, so it injects a 1-based integer **`cid`** onto every record at build time. The front-end reads `cid` directly:

```js
// enthermal-configurator.html — setAnchorImages()
function setAnchorImages(cid){
  if(cid==null) return;                                  // keep last image rather than 404
  var code = 'anchor_' + String(cid).padStart(2,'0');    // 1 -> anchor_01, 202 -> anchor_202
  document.querySelectorAll('.sky-toggle-option').forEach(function(opt){
    var folder = opt.getAttribute('data-folder') || opt.textContent.trim();  // Overcast | PartlyClear
    opt.setAttribute('data-img', 'App_Data/Anchor_Renders/'+folder+'/'+code+'.webp');
  });
  var active = document.querySelector('.sky-toggle-option.active');
  if(active) document.getElementById('colorRenderImg').src = active.getAttribute('data-img');
}
```
`setAnchorImages(match.cid)` is called whenever the configuration changes; the sky toggle and zoom lightbox both read `data-img`. The 1-based `cid` needs no code change here (`padStart(2,'0')` already yields `anchor_01`).

## Asset layout & the sky toggle (target)

The 404 renders are organized by sky, filename keyed on the anchor code:
```
App_Data/Anchor_Renders/
  Overcast/    anchor_01.webp … anchor_202.webp   (202)   ← default
  PartlyClear/ anchor_01.webp … anchor_202.webp   (202)
```
There is **no `anchor_00`** under 1-based numbering. The **Exterior Color** card's pill toggle is **two** options (Overcast / Partly Clear, default Overcast). The folder is space-free (`PartlyClear`); the toggle shows "Partly Clear" as the display label and resolves the folder via each option's `data-folder` attribute.

**Done for Part 2 (July 2026):**
1. Rendered the 202 anchors × 2 skies (frame N = cid N); Overcast = Overcast/Exp090, Partly Clear = ClearSky/Exp075.
2. Converted PNG → lossless WebP via [png_to_webp.py](../4_Anchor_Specs/png_to_webp.py) and replaced `App_Data/Anchor_Renders/` with the two-sky, 1-based set.
3. Updated the app: sky toggle from three options (Clear/Overcast/Cloudy) to two (Overcast/Partly Clear), and repointed the placeholder defaults from `anchor_00.webp` to `anchor_01.webp`.

## Format & hosting

- **Format:** WebP — universal support, already compressed.
- **Hosting:** renders ship **in-repo** under `App_Data/Anchor_Renders/`, loaded via relative paths (same `fetch()`/HTTP requirement as the rest of the app; no `file://`). Only one render is fetched at a time (current config × active sky).
- **If this becomes a public high-traffic tool:** move the asset set to a CDN and point the `data-img` base at it. Version by **path segment** (`/renders/v3/…`), never a query string (query strings defeat edge caching).

## Open items

| # | Item | Status |
|---|---|---|
| 1 | Run clustering against current data; pin anchor count | **done — 202 anchors, max ΔE ext 1.4576 / trn 2.8610** |
| 2 | Config → render resolution | **done — per-config 1-based `cid` → `anchor_<cid>.webp`** |
| 3 | Render the anchor × sky batch (202 × 2) | **done — Overcast (Exp090) + Partly Clear (Exp075), 1-based** |
| 4 | Update app to two-sky toggle + repoint placeholders | **done — `data-folder` map, `anchor_01` defaults** |
| 5 | Move assets to a CDN if traffic warrants | not started (in-repo today) |

## Superseded decisions (kept for reference)

- **ΔE76 metric / 77 anchors / ΔE ≤ 2.** Replaced by CIEDE2000 + substrate partition (June) — ΔE76 rendered saturated tints as gray (*Part 1·B*).
- **Single-axis (exterior-only) clustering.** Replaced by the two-axis ext+trn metric (July) — reflection-only left ~⅓ of configs with a visibly-different transmitted color (*Part 1·C*).
- **0-based `cid` (`anchor_00…`).** Replaced by 1-based so Blender frame N = cid N (*Part 1·C*).
- **Three-sky set (Clear / Overcast / Cloudy).** Replaced by two skies (Overcast / Partly Clear).
- **Lab-string-key runtime lookup via `cluster_map.json`.** Replaced by per-config `cid`; `cluster_map.json` retained as debug output only.
- **k-means clustering.** Replaced by farthest-first k-center cover.
- **Static placeholder sky photo (`*_Set3.png`).** Replaced by per-config anchor renders.
- **Delta-tint runtime correction / `mix-blend-mode: multiply`.** Deleted — at this tolerance there is no perceptible gap to correct.
