# Enthermal™ Configurator — Hosting Handoff

A one-page guide for the web/hosting team. Covers what the app is, how to deploy it, and the gotchas that matter.

---

## What it is

The **LuxWall Enthermal™ Product Configurator** — a client-side technical sales tool for architects and specifiers. Users select glass configuration options and the app displays thermal performance metrics (U-value, SHGC, Tvis, R-value, OITC) plus visual cross-section and color renderings. Single-page, primarily a desktop tool.

- **Stack:** Vanilla HTML5 / CSS3 / JavaScript (ES6). No React, no build step, no npm, no server-side code.
- **Backend:** None required. This is a fully static site.
- **State:** No login, cookies, `localStorage`, analytics, or user-data collection. All data is read-only reference data shipped with the app.

---

## How to deploy

Host as a static site on any static host — S3 + CloudFront, Netlify, Vercel, GitHub Pages, Azure Static Web Apps, or a plain Nginx/Apache directory. No Node runtime or database needed.

**Deploy the entire directory, preserving the folder structure:**

```
/ (deploy root or subpath)
├── enthermal-configurator.html   ← entry point
└── App_Data/
    ├── enthermal.json
    ├── enthermal-plus-inboard.json
    ├── enthermal-plus-outboard.json
    └── Anchor_Renders/
        ├── Clear/      anchor_00.webp … anchor_136.webp   ← per-config exterior renders
        ├── Overcast/   anchor_00.webp … anchor_136.webp      (137 anchors × 3 skies = 411)
        └── Cloudy/     anchor_00.webp … anchor_136.webp
```

---

## Critical gotchas

### 1. The `App_Data/` folder must ship with the HTML ⚠️
The app is **not** a single self-contained file. On load it fetches three JSON files from the `App_Data/` folder using **relative paths** (`App_Data/enthermal.json`, etc.). If `App_Data/` is missing or moved, **the app loads blank — no data appears, no obvious error.** Always deploy `App_Data/` as a sibling of the HTML file.

### 2. Must be served over HTTP(S), not `file://`
Because of the `fetch()` calls, browsers block data loading over the `file://` protocol. Real hosting serves over `http(s)://`, so this is automatic — but **do not test by double-clicking the HTML file**; it will appear broken. Use the deployed URL or a local web server.

### 3. Only external dependency: Google Fonts
Loads "Plus Jakarta Sans" and "DM Sans" from the Google Fonts CDN. If a strict Content-Security-Policy is in place, allowlist `fonts.googleapis.com` and `fonts.gstatic.com`, or typography falls back to system fonts.

---

## Performance notes

The full deploy is **~643 MB**, dominated by the render library — but **first load is
small**: the JSON (~6.5 MB) plus the single default render. Each anchor render is fetched
on demand (the current config × active sky), so a session pulls only a handful of images,
each cached after first view.

| Asset | Size |
|---|---|
| `enthermal-plus-inboard.json` | ~4.5 MB |
| `enthermal-plus-outboard.json` | ~1.9 MB |
| Anchor renders (137 anchors × 3 skies, `.webp`) | **~637 MB total** (~1.6 MB each, 411 files) — loaded one at a time on demand |
| `enthermal.json` | ~71 KB |
| `enthermal-configurator.html` | ~104 KB |

Recommendations:
- **Enable gzip/Brotli compression** for the JSON and HTML (compresses ~80–90%, cutting ~6 MB to well under 1 MB). WebP is already compressed — don't expect further gain there.
- **The render library is large (~637 MB).** Consider a recompression pass on the high-res WebP, and/or hosting the renders on a CDN/separate assets repo if you approach a host's storage or bandwidth limit (e.g. GitHub Pages' 1 GB soft cap). See `Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md` Part 2.
- **Set sensible Cache-Control headers** on the `App_Data/` and render assets (they change infrequently).
- **Optimize the PNGs** if first-load performance matters (WebP conversion / resizing) — they're large and uncompressed.

---

## Open questions for the hosting team

- **Hosting target?** (CDN, static host, internal server) — confirms compression/caching are configurable.
- **Root domain or subpath?** (e.g. `luxwall.com/configurator/`) — relative paths support subpaths, but worth confirming.
- **Can you enable gzip/Brotli + Cache-Control** for `App_Data/` and image assets?
- **Any CSP** that would block Google Fonts?

---

## Local preview (for testing before deploy)

From the project folder, run any static server, e.g.:

```
python -m http.server 8000
```

Then open `http://localhost:8000/enthermal-configurator.html`.
