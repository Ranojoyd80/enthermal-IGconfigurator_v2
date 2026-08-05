# Enthermal™ Configurator — Hosting Handoff

A one-page guide for the web/hosting team. Covers what the app is, how to deploy it, and the gotchas that matter.

---

## What it is

The **LuxWall Enthermal™ Product Configurator** — a client-side technical sales tool for architects and specifiers. Users select glass configuration options and the app displays thermal performance metrics (U-value, SHGC, Tvis, R-value, OITC) plus visual cross-section and color renderings. Single-page, primarily a desktop tool.

- **Stack:** Vanilla HTML5 / CSS3 / JavaScript (ES6). No React, no build step, no npm, no server-side code.
- **Backend:** None required. This is a fully static site.
- **State:** No login, cookies, `localStorage`, analytics, or user-data collection. All data is read-only reference data shipped with the app.
- **Known placeholder:** the **"Download Configuration" button is intentionally disabled** — the report format it will generate is still being designed. It is not a bug and needs no hosting-side work; it will be wired up in a later app update.

---

## How to deploy

Host as a static site on any static host — S3 + CloudFront, Netlify, Vercel, GitHub Pages, Azure Static Web Apps, or a plain Nginx/Apache directory. No Node runtime or database needed.

**Deploy the entire directory, preserving the folder structure:**

```
/ (deploy root or subpath)
├── enthermal-configurator.html   ← entry point
├── index.html                    ← redirect stub so the root URL loads the app
└── App_Data/
    ├── enthermal.json
    ├── enthermal-plus-inboard.json
    ├── enthermal-plus-outboard.json
    └── Anchor_Renders/
        ├── Overcast/     anchor_01.webp … anchor_202.webp   ← per-config exterior renders (default sky)
        └── PartlyClear/  anchor_01.webp … anchor_202.webp      (202 anchors × 2 skies = 404)
```

---

## Critical gotchas

### 1. The `App_Data/` folder must ship with the HTML ⚠️
The app is **not** a single self-contained file. On load it fetches three JSON files from the `App_Data/` folder using **relative paths** (`App_Data/enthermal.json`, etc.). If `App_Data/` is missing or moved, **the app loads blank — no data appears, no obvious error.** Always deploy `App_Data/` as a sibling of the HTML file.

### 2. Must be served over HTTP(S), not `file://`
Because of the `fetch()` calls, browsers block data loading over the `file://` protocol. Real hosting serves over `http(s)://`, so this is automatic — but **do not test by double-clicking the HTML file**; it will appear broken. Use the deployed URL or a local web server.

### 3. Only external dependency: Google Fonts
Loads "Plus Jakarta Sans" and "DM Sans" from the Google Fonts CDN. If a strict Content-Security-Policy is in place, allowlist `fonts.googleapis.com` and `fonts.gstatic.com`, or typography falls back to system fonts.

### 4. File and folder names are case-sensitive on most hosts
The app was developed on Windows (case-insensitive) and currently runs on GitHub Pages, but most Linux, S3, and CDN origins are case-sensitive. Deploy with the exact casing in the repo — `App_Data`, `Anchor_Renders`, `Overcast`, `PartlyClear`, `anchor_07.webp` — or fetches will 404 and the affected panel silently shows nothing.

### 5. Do NOT run the render images through an image-optimization pass
The 404 `.webp` renders are **lossless** by design — they are color-accurate product renderings validated against physical glass samples. Automatic asset optimizers (Cloudflare Polish, imgix, build-time image plugins, "serve as lossy WebP/AVIF" CDN features) must be **disabled** for `App_Data/Anchor_Renders/`. Recompressing them lossily visibly shifts the exterior colors the tool exists to show.

### 6. Do NOT strip or rewrite query strings on asset URLs
Every render URL carries a content-derived `?v=<hash>` cache-buster (maintained automatically by a pre-commit hook). CDNs or optimizers that "normalize" URLs by dropping query strings — or that cache while ignoring them — will serve stale images after a render batch is replaced. Query strings must pass through to the origin and be part of the cache key.

---

## Performance notes

The full deploy is **~675 MB**, dominated by the render library — but **first load is
small**: the JSON (~6 MB) plus a handful of renders (the default view, and the app
background-preloads the other sky variant and each tab's default render — roughly
5 images / ~8 MB total). Other anchor renders are fetched on demand (the current
config × active sky), each cached after first view.

| Asset | Size |
|---|---|
| `enthermal-plus-inboard.json` | ~4.2 MB |
| `enthermal-plus-outboard.json` | ~1.8 MB |
| Anchor renders (202 anchors × 2 skies, `.webp`) | **~668 MB total** (~1.65 MB each, 404 files) — loaded on demand |
| `enthermal.json` | ~71 KB |
| `enthermal-configurator.html` | ~132 KB |

Recommendations:
- **Enable gzip/Brotli compression** for the JSON and HTML (compresses ~80–90%, cutting ~6 MB to well under 1 MB). WebP is already compressed — don't expect further gain there.
- **The render library is large (~668 MB).** If you approach a host's storage or bandwidth limit (e.g. GitHub Pages' 1 GB soft cap), move the renders to a CDN or a separate assets repo. **Do not solve this by recompressing them** — see gotcha #5; the renders are lossless by design and re-encoding them lossily shifts the exterior colors the tool exists to show. Serving fewer bytes is a hosting/CDN problem, not an image-quality tradeoff. See `Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md` Part 2.
- **Set sensible Cache-Control headers** on the `App_Data/` and render assets (they change infrequently, and every render URL carries a content-derived `?v=` cache-buster that changes when a render batch is replaced — so long max-age is safe).

---

## Open questions for the hosting team

- **Hosting target?** (CDN, static host, internal server) — confirms compression/caching are configurable.
- **Root domain or subpath?** (e.g. `luxwall.com/configurator/`) — relative paths support subpaths, but worth confirming.
- **Can you enable gzip/Brotli + Cache-Control** for `App_Data/` and image assets?
- **Any CSP** that would block Google Fonts?

---

## Local preview (for testing before deploy)

From the project folder, run:

```
python serve.py
```

Then open `http://localhost:8000/enthermal-configurator.html`. (`serve.py` wraps
Python's built-in `http.server` and adds `Cache-Control: no-store`, so a normal
reload always shows the latest files during development — see `HOW-TO-RUN.txt`.
Plain `python -m http.server 8000` also works but caches aggressively.)
