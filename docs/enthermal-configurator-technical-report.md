# Enthermalâ„¢ Product Configurator â€” Technical Report

## 1. How Was This App Developed?

The configurator was developed iteratively through a conversational AI-assisted workflow using Claude. Early versions (V1â€“V22) built out the core UI, cascade logic, cross-section diagrams, and metric cards. Subsequent work migrated the data layer from embedded JS arrays to external JSON files loaded via `fetch()`, expanded the product catalog from ~96 to ~6,862 configurations, and added features such as the CEN/NFRC standard toggle, Inboard/Outboard placement toggle, Air/Argon gas fill selector, and data-driven coating shortcodes.

### Development Timeline (Selected Milestones)

| Version | Key Changes |
|---------|------------|
| V1 | Core layout, dual-value metric cards, centered cross-section diagram, typography system |
| V2 | Full CSV data ingestion (60 Enthermal configs), T-UV metric card, substrate/coating dropdown split |
| V3 | Enthermal Plus tab with config panel, argon gap visualization, coating surface selector (S4/S5) |
| V7 | Smart cascading filters for both tabs â€” invalid selections are prevented, no-match messages eliminated |
| V12 | Dead CSS removed, font scale consolidated to 6 sizes (9Â·11Â·13Â·15Â·25Â·32 px) |
| V16 | Expanded Enthermal data to 60 records, Plus data to 36 records |
| V21 | NFRC/CEN standard toggle, S4/S5 surface toggle redesigned as slider, OITC metric card, Embodied Carbon and IGU Weight info bar |
| V22 | Centering bug fix â€” synchronous reflow (`void cs.offsetWidth`), S4/S5 opacity transitions |
| Post-V22 | Migrated data from embedded JS arrays to external JSON files (`App_Data/*.json`). Stack-based data schema with `glass[]`, `vacuum`, `gas` layers. Coating shortcodes (C366, SB70, etc.) with display name lookups. |
| Current | IG_Config dataset migration â€” 98 Enthermal + 4,748 Plus Inboard + 2,016 Plus Outboard rows. 14 coatings, 10 substrates. Inboard/Outboard placement toggle with separate cascade logic. Air/Argon gas fill toggle. CEN auto-flip with per-row `cen`/`gFactor`/`uvalCEN` fields. |

### Data Validation

All data is sourced from LBNL Windows 7 / PyWinCalc calculations and cross-checked against official LuxWall product data sheets:

- **Enthermal (LW00041.6)**: 98 configurations across 14 coatings and 10 substrates â€” 98%+ match rate.
- **Enthermal Plus (LW00054.4)**: 6,764 configurations across Inboard and Outboard placement modes â€” validated via automated test suite (51 configs, 3 stress tests, 0 failures).

---

## 2. Technology & Architecture

### Stack

| Layer | Technology |
|-------|-----------|
| Language | Vanilla HTML5, CSS3, JavaScript (ES6) |
| Framework | None â€” zero dependencies, no build step |
| Typography | Google Fonts: Plus Jakarta Sans (display), DM Sans (body) |
| Data | External JSON files loaded via `fetch()` at startup |
| Hosting | Static file hosting â€” HTML + `App_Data/` folder |
| External deps | Google Fonts CDN only |

### File Structure

```
enthermal-configurator.html    â€” ~125 KB
â”œâ”€â”€ <style>     â€” CSS (design tokens + component styles)
â”œâ”€â”€ <body>      â€” semantic HTML
â””â”€â”€ <script>    â€” named functions + IIFEs (vanilla ES6)

App_Data/
â”œâ”€â”€ enthermal.json             â€” 98 Enthermal configs (~73 KB)
â”œâ”€â”€ enthermal-plus-inboard.json â€” 4,470 Plus Inboard configs (~4.2 MB)
â”œâ”€â”€ enthermal-plus-outboard.json â€” 1,876 Plus Outboard configs (~1.8 MB)
â””â”€â”€ Anchor_Renders/
    â”œâ”€â”€ Overcast/     anchor_01.webp â€¦ anchor_202.webp  â€” per-config exterior renders (default)
    â””â”€â”€ PartlyClear/  anchor_01.webp â€¦ anchor_202.webp    (202 anchors Ã— 2 skies = 404)
```

*(Per-section line counts drift as the single file evolves; treat the function lists below as a guide, not an exact inventory.)*

### CSS Architecture

- **CSS custom properties** for consistent theming under `:root`
- Key tokens: `--lw-dark`, `--lw-teal`, `--lw-gray-*`, `--font-display`, `--font-body`
- **6-size type scale**: 9Â·11Â·13Â·15Â·25Â·32 px (consolidated from 9 sizes in V12)
- Responsive breakpoint at 1120px (single-column stack for tablet/mobile)
- Print media query hides header, hero, tabs, and download button
- Cross-section glass panes use CSS gradients and box-shadows (no images)
- Cross-section height uses pure CSS flex layout (no JS calculations since V11)
- Desiccant beads rendered via 96 CSS `radial-gradient()` layers
- Animations: `fadeIn` for metric cards, `pulse` for vacuum indicator
- S4/S5 coating lines use `opacity` with 250ms CSS transitions for smooth switching

### JavaScript Architecture

43 named functions + 3 IIFEs organized into five concerns:

**Data & Display Helpers (9 functions)**

| Function | Purpose |
|----------|---------|
| `coatingName(code)` | Map shortcode to display name (e.g., `C366` â†’ `LoEÂ³ 366`) |
| `substrateName(code)` | Map substrate to display name (e.g., `Optiblue` â†’ `OptiblueÂ®`) |
| `coatingNameWithMaker(code)` | Prepend manufacturer prefix for dropdowns (e.g., `Cardinal LoEÂ³ 366`) |
| `layerDisplay(layer, nameFn)` | Format a glass layer for display â€” coating only for Clear, "coating on substrate" for branded |
| `postProcessData()` | Attach `glass[]`, `gasType`, `secondCoating`, `secondSurface` accessors to each data row |
| `getGlassColor(substrate)` | Map a substrate to a tint color for the **cross-section** glass panes (not the color card). Drives the exterior lite tint on both the Enthermal and Enthermal Plus cross-sections |
| `unique(arr)` | Return unique sorted values |
| `getVal(name)` | Get checked radio button value by name attribute |
| `populateSelect(el, items, placeholder, nameFn)` | Populate a `<select>` with options |

**Enthermal Tab (9 functions)**

| Function | Purpose |
|----------|---------|
| `comboKey(layer)` | Encode glass layer as `"coating|substrate"` key |
| `parseComboKey(val)` | Decode combo key back to `{coating, substrate}` |
| `updateOuterCoatings()` | Populate outer coating dropdown filtered by outer thickness |
| `updateInnerThickness()` | Enable/disable inboard radios based on available data; auto-select first valid |
| `findMatch()` | Look up exact config match from `DATA` array |
| `acousticKey(a, b)` | Compute `"min/max"` key for OITC/Rw lookup |
| `iguWeight(totalGlassMM)` | Compute IGU weight as `(2.5 * mm).toFixed(1)` |
| `clearResults()` | Reset all metric cards and summary to blank state |
| `updateResults()` | Populate all metric cards, cross-section, summary, and CEN/NFRC toggle |

**Enthermal Plus Tab â€” Inboard Cascade (8 functions)**

| Function | Purpose |
|----------|---------|
| `getActivePlusData()` | Return `DATA_PLUS_IN` or `DATA_PLUS_OUT` based on placement toggle |
| `getVigComboKey(d, isOutboard)` | Compute VIG thickness combo string (e.g., `"4/4"`) |
| `filterPlusData()` | Apply all active filters to Plus dataset |
| `initPlusConfig()` | Initialize Plus tab â€” enable valid outer thickness radios |
| `updatePlusOuterCoatings()` | Populate Plus outer coating (S2) dropdown |
| `updatePlusVigThickness()` | Filter and populate VIG thickness dropdown |
| `updatePlusVigCoatings()` | Populate VIG coating dropdown for inboard mode |
| `updatePlusSurfaces()` | Handle S4/S5 toggle enable/disable and auto-selection |

**Enthermal Plus Tab â€” Outboard Cascade (6 functions)**

| Function | Purpose |
|----------|---------|
| `_plusOutboardData()` | Filter active Plus dataset by current gas selection |
| `updatePlusVigThicknessOutboard()` | Root of outboard cascade â€” enables all VIG thickness options |
| `updatePlusS2CoatingOutboard()` | Filter S2 (VIG outer) coatings by VIG thickness |
| `updatePlusInboardThicknessOutboard()` | Filter mono inboard thickness radios by VIG thickness |
| `updatePlusS5CoatingOutboard()` | Filter S5 (mono inboard) coatings by mono thickness |
| `seedPlusOutboardDefaults()` | Set default selections when switching to outboard mode |

**Plus Shared & Results (6 functions)**

| Function | Purpose |
|----------|---------|
| `seedPlusInboardDefaults()` | Set default selections when switching to inboard mode |
| `findPlusMatch()` | Look up exact Plus config match from active dataset |
| `updatePlusResults(surfaceOnly)` | Populate metrics, cross-section, summary. `surfaceOnly=true` skips fade-in animation |
| `_plusIsOutboard()` | Return placement toggle state |
| `repositionPlusToggles()` | Reposition all Plus toggle thumbs after tab becomes visible |

**Layout (4 functions):** `centerCrossSection()`, `centerPlusCrossSection()`, `alignCrossSection()`, `alignPlusCrossSection()`

**Toggle IIFEs (3 closures)**

| IIFE | Purpose |
|------|---------|
| NFRC/CEN toggle | Standard toggle with auto-flip, locking, label switching (SHGCâ†”g-Factor; OITC/Rw values blank by mode) |
| S4/S5 surface toggle | Coating surface toggle with auto-disable when only one surface is valid |
| Placement toggle | Inboard/Outboard mode switching with UI reorder, reseed, and cross-section rearrangement |
| Gas fill toggle | Argon/Air toggle with cascade update |
| Sky-condition toggle | Swaps the color-card image between Overcast / Partly Clear renders for the current config's `cid` |
| Image zoom lightbox | Full-screen viewer; steps through the two sky conditions |

### Smart Filtering Logic

All tabs implement cascading constraint propagation â€” each selection filters downstream options so that **every possible user selection leads to valid data**:

**Enthermal:** Outer Thickness â†’ Low-E Coating (combined coating+substrate dropdown) â†’ Inner Thickness (auto-constrained) â†’ Results

**Plus Inboard:** Outer Thickness â†’ S2 Coating â†’ Gas Fill â†’ VIG Thickness â†’ VIG Coating â†’ S4/S5 Surface â†’ Results

**Plus Outboard:** VIG Thickness (root) â†’ S2 Coating + Mono Thickness (parallel branches) â†’ S5 Coating â†’ Results

Invalid options are visually disabled (35% opacity, `not-allowed` cursor). For inner thickness radios and Plus surfaces, auto-selection of the first valid option occurs when the current selection becomes invalid. For the coating dropdown, the app clears the selection and shows "Select a product to view results."

### CEN/NFRC Standard Toggle

The toggle auto-flips based on the matched data row's `cen` field. CEN-enabled coatings (LUMI, ZEN, SKN183, XTR6129) have per-row `gFactor` and `uvalCEN` values. When CEN is active:
- U-value displays `uvalCEN` instead of `uval`
- SHGC displays `gFactor`, label changes to "g-Factor"
- U-Factor (IP) and R-value show "â€”"
- The acoustic card shows R<sub>w</sub> (its value populated) while the OITC value blanks to "â€”"; in NFRC mode it's the reverse
- Toggle is always locked (user cannot manually override)

---

## 3. Data Schema & Storage

### Storage Method

Data is stored in **three external JSON files** loaded at startup via `Promise.all()` with `fetch()`. The three datasets total approximately 6,862 configurations.

### Data Source

Source data comes from LBNL Windows 7 / PyWinCalc calculations exported to CSV, processed via Python scripts, and output as JSON. The JSON files use a **stack-based schema** where each row contains a `stack` array describing the physical layer sequence (glass, vacuum, gas).

### Data Loading

```javascript
Promise.all([
  fetch('App_Data/enthermal.json').then(r => r.json()),
  fetch('App_Data/enthermal-plus-inboard.json').then(r => r.json()),
  fetch('App_Data/enthermal-plus-outboard.json').then(r => r.json())
]).then(results => {
  DATA = results[0];           // 98 rows
  DATA_PLUS_IN = results[1];   // 4,748 rows
  DATA_PLUS_OUT = results[2];  // 2,016 rows
  postProcessData();
  dataLoaded = true;
});
```

### Stack-Based Schema (all datasets)

Each record contains a `stack` array of layers plus performance metrics:

**Stack layers:**

| Layer type | Fields | Example |
|-----------|--------|---------|
| `glass` | `coating`, `substrate`, `thickness` | `{"type":"glass","coating":"C366","substrate":"Clear","thickness":6}` |
| `vacuum` | `thickness` | `{"type":"vacuum","thickness":0.25}` |
| `gas` | `gasType`, `thickness` | `{"type":"gas","gasType":"Ar90","thickness":13.45}` |

**Enthermal stack:** `[glass, vacuum, glass]` (2 panes)
**Plus Inboard stack:** `[glass(mono), gas, glass(VIG outer), vacuum, glass(VIG inner)]` (3 panes)
**Plus Outboard stack:** `[glass(VIG outer), vacuum, glass(VIG inner), gas, glass(mono)]` (3 panes)

**Performance metrics (all rows):**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `totalThickness` | float | Overall IGU thickness in mm | `25.4` |
| `uval` | float | U-value in W/mÂ²Â·K (NFRC) | `0.2391` |
| `uvalIP` | float | U-value in BTU/hrÂ·ftÂ²Â·Â°F | `0.0421` |
| `rval` | float | R-value (insulation) | `23.75` |
| `shgc` | float | Solar Heat Gain Coefficient (0â€“1) | `0.1777` |
| `tvis` | float | Visible Light Transmittance (0â€“1) | `0.4612` |
| `routVis` | float | Exterior Visible Reflectance (0â€“1) | `0.1266` |
| `tuv` | float | UV Transmittance (0â€“1) | `0.0045` |
| `nfrc` | bool | Has NFRC values | `true` |
| `cen` | bool | Has CEN values | `false` |
| `gFactor` | float\|null | CEN g-Factor (null if NFRC-only) | `0.637426` |
| `uvalCEN` | float\|null | CEN U-value (null if NFRC-only) | `0.411255` |
| `extL`, `extA`, `extB` | float | Exterior reflected color CIE L\*a\*b\* | `42.22, -2.0, -3.67` |
| `intL`, `intA`, `intB` | float | Interior transmitted color CIE L\*a\*b\* | `44.4, -0.25, -0.79` |

**Derived fields** (computed by `postProcessData()` at runtime):
- `glass[]` â€” array of glass-type layers extracted from `stack`
- `gasType` â€” gas fill type (`"Ar90"` or `"Air"`) from gas layer
- `secondCoating` â€” the non-S2 coating (Plus only)
- `secondSurface` â€” `"S4"` or `"S5"` based on which glass pane holds the second coating

### Configuration Coverage

**Enthermal** (98 configs):
- 14 coatings: Cardinal (C180, C270, C272, C340, C366, Q452), Vitro (SB60, SB70, SB72, SBR67), Saint-Gobain (SKN183, XTR6129, LUMI, ZEN)
- 10 substrates: Clear, StarphireÂ®, OptiblueÂ®, OptigrayÂ®, SolarblueÂ®, SolarbronzeÂ®, SolargrayÂ®, SolexiaÂ®, OptiblueÂ® (z50), OptiblueÂ® (z75)
- 3 outer thicknesses: 4mm, 5mm, 6mm (some coatings restricted â€” SB72/SKN183: 6mm only, SBR67: 5â€“6mm, XTR6129: 4/6mm)
- 3 inner thicknesses: 4mm, 5mm, 6mm (constrained by outer selection)
- 19 CEN-enabled rows (LUMI, ZEN, SKN183, XTR6129 coatings)

**Enthermal Plus Inboard** (4,748 configs):
- 3 pane configuration: mono outboard + argon gap + VIG (2-pane)
- VIG thickness combos: 4/4, 5/4, 5/5, 6/5, 6/6 mm
- S4/S5 surface toggle for second coating placement
- Gas fill: 90% Argon or 100% Air
- 724 CEN-enabled rows

**Enthermal Plus Outboard** (2,016 configs):
- 3 pane configuration: VIG (2-pane) + argon gap + mono inboard
- Same VIG thickness combos and gas fill options
- Surface always S5 (toggle disabled)
- 358 CEN-enabled rows

### Color Rendering (current state)

The **Exterior Appearance** card shows a **per-configuration photoreal render** with an
Overcast / Partly Clear weather toggle (default Overcast) and a zoom lightbox. Each config carries an
integer `cid` (anchor id) injected into the JSON by the clustering script, and
`setAnchorImages(cid)` points the card at
`App_Data/Anchor_Renders/<Sky>/anchor_<cid>.webp`. The 6,444 configs collapse to
**202 color anchors** (two-axis CIEDE2000: exterior â‰¤ 1.5 + transmitted â‰¤ 3.0, partitioned by exterior substrate; 1-based `cid`s), so the
image is imperceptibly close to â€” and the same hue family as â€” the exact selection.
The earlier runtime `labToRgb()` Labâ†’sRGB gradient renderer (and the flip /
Lab-readout UI), and the interim static `*_Set3.png` placeholder sky, have both been
removed. A disclaimer below the image notes that on-screen color is representational
and varies with display, and that final color should be confirmed with physical samples.

The render panel is a four-state machine (`setRenderState`: `image` / `loading` /
`cleared` / `unavailable`): a first-time download shows a neutral "Loading exterior
renderâ€¦" panel, a cleared selection shows its own neutral prompt, and the
"unavailable" wording is reserved for an actual image error or a config with no
`cid`. While a render is already on screen, config changes swap silently (the
previous render stays up until the new one loads). The app background-preloads the
inactive sky variant on every config change and each tab's default render (both
skies) at startup, so first tab switches and sky flips are near-instant.

The per-config CIE L\*a\*b\* values (`extL/A/B`, `intL/A/B`) remain in the data and
drive the JND color clustering that assigns each config its `cid` (see
[color-rendering.md](color-rendering.md) and
[CLUSTERING_PROCEDURE.md](../Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md)). The cross-section panes are
still tinted from substrate color via `getGlassColor()` â€” on both tabs, the exterior
lite (`glass[0]`) is tinted from its substrate, while the always-Clear inner lites
keep their default styling. (The assembly-level Lab values are coating-dominated and
do not encode the recognizable per-substrate body tint, so the hand-tuned
`getGlassColor()` lookup is used for the cross-section rather than a Labâ†’sRGB
conversion.)

---

## 4. How Can the Data Be Updated or Modified?

### Current State

Data is fully separated from the application. The three JSON files in the `App_Data/` folder can be updated independently without modifying the HTML file. The UI automatically discovers available coatings, substrates, and thickness combinations from the data at runtime.

### Data Pipeline

```
PyWinCalc â†’ CSV export â†’ Python transform script â†’ JSON files â†’ Deploy
```

The Python transform scripts in the `Data_Pipeline/` folder handle:
1. Reading PyWinCalc CSV output
2. Parsing the Comment column for coating shortcodes and substrate names
3. Building the stack-based JSON schema with glass/vacuum/gas layers
4. Computing CEN fields (`gFactor`, `uvalCEN`) where applicable
5. Outputting the three JSON files

### Adding New Products or Coatings

To add a new coating (e.g., a new Cardinal or Solarban variant):
1. Run the new glass configuration through PyWinCalc
2. Append the results to the CSV
3. Add the coating shortcode to `COATING_NAMES`, `COATING_MAKERS`, and (if applicable) `SUBSTRATE_NAMES` in the HTML
4. Re-run the transform script to regenerate JSON
5. Deploy â€” the UI automatically picks up new coatings in the dropdowns

To add an Enthermal Spandrel product (there is currently **no** Spandrel tab â€” an
earlier placeholder tab was removed; the app now ships two tabs, Enthermal and
Enthermal Plus):
1. Create a `App_Data/enthermal-spandrel.json` with the stack-based schema
2. Add a `DATA_SPANDREL` array and corresponding filter/display functions
3. Add and wire up a third `.product-tab` button (`data-tab="enthermal-spandrel"`)

---

## 5. How Can This App Be Hosted on a Website?

### Option A: Static File Hosting (Simplest)

Since the app is a single HTML file with no server-side requirements, it can be hosted on any static file server:

| Platform | Deployment Method | Cost |
|----------|------------------|------|
| **AWS S3 + CloudFront** | Upload file to S3 bucket, serve via CloudFront CDN | ~$1/month |
| **Netlify** | Drag-and-drop deploy or Git integration | Free tier available |
| **Vercel** | Git push to deploy | Free tier available |
| **GitHub Pages** | Push to repo, enable Pages | Free |
| **Azure Static Web Apps** | Git integration or CLI deploy | Free tier available |
| **Company web server** | Upload to existing IIS/Apache/Nginx server | Existing infrastructure |

**Deployment is two items** â€” upload `enthermal-configurator.html` and the `App_Data/` folder. No Node.js, no PHP, no database server.

### Option B: Embed in Existing LuxWall Website

The configurator can be embedded into an existing page via an `<iframe>`:

```html
<iframe src="/tools/enthermal-configurator.html" 
        width="100%" height="900px" 
        frameborder="0" style="border:none">
</iframe>
```

Or the HTML/CSS/JS can be extracted and integrated directly into the site's CMS or template system (WordPress, HubSpot, custom CMS, etc.).

### Option C: Progressive Web App (PWA)

For offline access (useful for sales teams at job sites), add a service worker and manifest to make it installable:

```json
// manifest.json
{
  "name": "Enthermal Configurator",
  "short_name": "Enthermal",
  "start_url": "/configurator/",
  "display": "standalone",
  "background_color": "#0a0f1a",
  "theme_color": "#0d9488"
}
```

This allows the app to work without an internet connection after the first visit.

### DNS & Custom Domain

For a dedicated URL like `configure.luxwall.com`:
1. Create a CNAME DNS record pointing to the hosting provider
2. Enable HTTPS via the provider's SSL certificate (free with Let's Encrypt on most platforms)
3. Deploy the file(s) to the hosting provider

---

## 6. Security Hardening for Production

### Threat Model

The primary concern is **unauthorized modification** of the app after deployment â€” ensuring that the performance data shown to customers, architects, and specifiers is accurate and has not been tampered with.

### Recommended Security Measures

#### A. Content Security Policy (CSP)

Add HTTP headers (via server config or `<meta>` tag) to prevent injection of unauthorized scripts:

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src https://fonts.gstatic.com;
  img-src 'self' data:;
  connect-src 'self';
">
```

This blocks external scripts, prevents `eval()` injection, and restricts network requests to the same origin.

#### B. Subresource Integrity (SRI)

If the data is moved to external JSON files, add integrity hashes to verify the files have not been modified:

```html
<script>
fetch('App_Data/enthermal.json')
  .then(r => r.text())
  .then(text => {
    // Verify SHA-256 hash before parsing
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
      .then(hash => {
        const hex = Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2,'0')).join('');
        if (hex !== EXPECTED_HASH) throw new Error('Data integrity check failed');
        return JSON.parse(text);
      });
  });
</script>
```

#### C. HTTPS Enforcement

Always serve over HTTPS to prevent man-in-the-middle modifications. Configure the server to redirect all HTTP requests to HTTPS and add the HSTS header:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

#### D. File Integrity Monitoring

On the hosting server, implement file integrity monitoring to detect unauthorized changes:

- **AWS S3**: Enable versioning and object lock (WORM â€” Write Once Read Many) to prevent modification of deployed files
- **Netlify/Vercel**: Deploy only from a protected Git branch (e.g., `main` with branch protection rules requiring PR approval)
- **Self-hosted**: Use file integrity monitoring tools (OSSEC, Tripwire, or simple cron-based `sha256sum` checks)

#### E. Access Control for Updates

Restrict who can modify the deployed application:

- **Git-based deploy**: Require pull request reviews from at least one product engineer before merging data or code changes
- **AWS S3**: Use IAM policies to restrict write access to a CI/CD service account only
- **Admin panel**: If a CMS is used, restrict editing permissions to authorized personnel with MFA enabled

#### F. Read-Only Data Validation

Add a runtime check that verifies the data hasn't been altered since build time:

```javascript
// Generated at build time
const DATA_CHECKSUM = "a3f2b8c1...";

// Verified at runtime
const computed = computeChecksum(JSON.stringify(DATA));
if (computed !== DATA_CHECKSUM) {
  document.body.innerHTML = '<h1>Data integrity error. Contact IT.</h1>';
}
```

#### G. Disable Browser Developer Tools Modifications

While it's impossible to fully prevent client-side modification (the browser is an untrusted environment), you can deter casual tampering:

- **Obfuscate/minify** the production build to make editing difficult
- **Add a visible "Verified Data" badge** that validates against a checksum on load
- **Log access** with a simple analytics beacon to detect unusual access patterns

### Summary of Security Layers

| Layer | Protects Against | Priority |
|-------|-----------------|----------|
| HTTPS + HSTS | Man-in-the-middle attacks | **Critical** |
| Content Security Policy | Script injection, XSS | **Critical** |
| Git branch protection | Unauthorized code/data changes | **High** |
| S3 object lock or deploy pipeline | File tampering on server | **High** |
| Subresource integrity hashes | Data file modification | **Medium** |
| Runtime checksum validation | Client-side data tampering | **Medium** |
| Minification/obfuscation | Casual reverse engineering | **Low** |

> **Note:** No client-side application can be made fully tamper-proof â€” anyone can inspect and modify what runs in their browser. The security measures above protect the **deployed source of truth** so that the data served to all users is accurate. For regulatory or contractual scenarios requiring certified performance data, consider generating signed PDF reports server-side.
