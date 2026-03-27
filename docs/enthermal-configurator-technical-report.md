# Enthermal™ Product Configurator — Technical Report

## 1. How Was This App Developed?

The configurator was developed iteratively over 22 versions (V1–V22) through a conversational AI-assisted workflow using Claude. Each version added features, refined the UI, and validated data against official LuxWall product data sheets.

### Development Timeline

| Version | Key Changes |
|---------|------------|
| V1 | Core layout, dual-value metric cards, centered cross-section diagram, typography system |
| V2 | Full CSV data ingestion (60 Enthermal configs), T-UV metric card, substrate/coating dropdown split |
| V3 | Enthermal Plus tab with config panel, argon gap visualization, coating surface selector (S4/S5) |
| V4 | Plus cross-section diagram, color card exterior/interior flip, smooth tab switching with requestAnimationFrame |
| V5 | Detailed aluminum spacer bar with desiccant beads (CSS radial-gradient), callout dot alignment fixes |
| V6 | Typography audit and consistency pass, disabled Spandrel tab, Download button, config summary state messages |
| V7 | Smart cascading filters for both tabs — invalid selections are prevented, no-match messages eliminated |
| V8 | Download button repositioned to metrics grid, teal accent label |
| V9 | Cross-section height alignment with color card, amber argon gap, vertical fine-tuning |
| V10 | Hero cleanup — removed duplicate "Product Configurator" label, teal header badge, white hero title |
| V11 | Color card declutter — removed swatch and RGB, added disclaimer note, L\*a\*b\* and flip button aligned to window width, cross-section uses pure CSS flex layout (no JS alignment) |
| V12 | Dead CSS removed (.hero-label, .metric-sub), indicator dot consistency (argon matches vacuum class), font scale consolidated from 9 sizes to 6 (9·11·13·15·25·32 px), metric card hover removed |
| V14 | Default configurations set — Enthermal: 6mm Clear/LoĒ³-366/6mm Clear; Plus: 4mm Clear/LoĒ³-366/VIG LoĒ³-366 S4 |
| V15 | Terminology update — Outer Lite→Outboard, Inner Lite→Inboard, Middle Lite→Middle. Default color card changed to Exterior Reflected |
| V16 | Expanded Enthermal data to 60 records (added COOL-LITE SKN 183, ECLAZ ZEN II coatings), Enthermal Plus data expanded to 36 records with Solarban 60/70 outer coatings |
| V21 | Cross-section centering refinement, NFRC/CEN standard toggle, S4/S5 surface toggle redesigned as slider, OITC metric card added, Embodied Carbon and IGU Weight info bar below cross-section |
| V22 | Centering bug fix — replaced async getBoundingClientRect with synchronous reflow (`void cs.offsetWidth`) for deterministic positioning. S4/S5 flicker fix — coating lines use opacity transitions instead of display toggle, surfaceOnly flag skips metric card fade-in animation |

### Data Validation

All embedded data was cross-checked against official LuxWall product data sheets:

- **Enthermal (LW00041.6)**: 48 metrics checked across 9 coatings, 47 match (98%). One U-factor discrepancy found on LoĒ³-366.
- **Enthermal Plus (LW00054.4)**: 288 metrics checked across 36 configurations, 281 match (97.6%). Four likely PDF errors identified and documented.

---

## 2. Technology & Architecture

### Stack

| Layer | Technology |
|-------|-----------|
| Language | Vanilla HTML5, CSS3, JavaScript (ES6) |
| Framework | None — zero dependencies, no build step |
| Typography | Google Fonts: Plus Jakarta Sans (display), DM Sans (body) |
| Hosting | Static single-file HTML — deployable anywhere |
| External deps | Google Fonts CDN only |

### File Structure

The entire application is a **single self-contained HTML file** (~99 KB):

```
enthermal-configurator-V22.html
├── <style>     — ~13.5 KB  (129 lines of CSS)
├── <body>      — ~35.5 KB  (303 lines of semantic HTML)
└── <script>    — ~51.5 KB  (450 lines)
    ├── Embedded data  — ~30 KB  (57% of JS — 96 JSON records)
    └── Application logic — ~21.5 KB  (24 functions)
```

### CSS Architecture

- **CSS custom properties** for consistent theming under `:root`
- Key tokens: `--lw-dark`, `--lw-teal`, `--lw-gray-*`, `--font-display`, `--font-body`
- **6-size type scale**: 9·11·13·15·25·32 px (consolidated from 9 sizes in V12)
- Responsive breakpoint at 1024px (single-column stack for tablet/mobile)
- Print media query hides header, hero, tabs, and download button
- Cross-section glass panes use CSS gradients and box-shadows (no images)
- Cross-section height uses pure CSS flex layout (no JS calculations since V11)
- Desiccant beads rendered via 96 CSS `radial-gradient()` layers
- Animations: `fadeIn` for metric cards, `pulse` for vacuum indicator
- S4/S5 coating lines use `opacity` with 250ms CSS transitions for smooth switching

### JavaScript Architecture

24 functions organized into three concerns:

**Enthermal Tab (8 functions)**

| Function | Purpose |
|----------|---------|
| `updateOuterColors()` | Filter substrate colors by selected thickness |
| `updateOuterCoatings()` | Filter coatings by thickness + color |
| `updateInnerThickness()` | Enable/disable inboard radio buttons based on available data |
| `findMatch()` | Look up exact config match from DATA array |
| `updateResults()` | Populate all metric cards + cross-section + summary |
| `clearResults()` | Reset all outputs to default/blank state |
| `updateColor()` | Compute RGB from CIE L\*a\*b\* and update glass color + L\*a\*b\* display |
| `labToRgb()` | CIE L\*a\*b\* → sRGB conversion (D65 illuminant) |

**Enthermal Plus Tab (5 functions)**

| Function | Purpose |
|----------|---------|
| `initPlusConfig()` | Populate outer coating dropdown, disable unavailable thicknesses |
| `updatePlusVigCoatings()` | Filter VIG coatings based on selected outer coating |
| `updatePlusSurfaces()` | Enable/disable S4/S5 toggle based on outer + VIG combo |
| `findPlusMatch()` | Look up exact Plus config match from DATA_PLUS array |
| `updatePlusResults(surfaceOnly)` | Populate metrics, cross-section, summary for Plus. When `surfaceOnly=true`, skips metric fade-in animation and re-centering for smoother S4/S5 toggle |

**Layout & centering (4 functions)**

| Function | Purpose |
|----------|---------|
| `centerCrossSection()` | Center Enthermal cross-section vacuum gap in card using synchronous reflow + getBoundingClientRect |
| `centerPlusCrossSection()` | Center Enthermal Plus cross-section vacuum gap in card (same technique) |
| `alignCrossSection()` | Align Enthermal cross-section pane height with color card |
| `alignPlusCrossSection()` | Align Plus cross-section pane height with color card |

**Toggle IIFEs (2 closures)**

| Function | Purpose |
|----------|---------|
| ISO/CEN toggle IIFE | NFRC/CEN standard toggle with sliding thumb animation |
| S4/S5 surface toggle IIFE | Coating surface toggle with auto-disable when only one surface is valid |

**Shared utilities**: `unique()`, `getVal()`, `populateSelect()`, `getGlassColor()`

### Smart Filtering Logic

Both tabs implement cascading constraint propagation — each dropdown/radio selection filters downstream options so that **every possible user selection leads to valid data**:

**Enthermal**: Outer Thickness → Low-E Coating → Substrate Color → Inner Thickness (auto-constrained) → Results

**Plus**: Outer Coating → VIG Coating (filtered) → Coating Surface S4/S5 (auto-constrained) → Results

Invalid options are visually disabled (30% opacity, `not-allowed` cursor). If the current selection becomes invalid after an upstream change, the first valid option is auto-selected.

### Cross-Section Centering (V22 Fix)

The cross-section diagrams are centered so the vacuum gap aligns with the horizontal center of the card. The centering algorithm:

1. Set `transform: none` on the `cs-container`
2. Force synchronous reflow via `void cs.offsetWidth`
3. Measure card center and vacuum gap center with `getBoundingClientRect()`
4. Apply `translateX(offset)` to shift the container

The `void cs.offsetWidth` call is critical — without it, `getBoundingClientRect()` may return stale positions based on the previous transform, causing cumulative drift on repeated calls.

---

## 3. Data Schema & Storage

### Storage Method

All data is **embedded directly in the HTML file as JavaScript object arrays**. There is no database, no API calls, and no external data files. The 96 records total approximately 30 KB of inline JSON.

### Data Source

The source data comes from `All_VIG_PyWinCalc_Data.csv` — a CSV file containing performance metrics calculated using the LBNL Windows 7 / PyWinCalc program. Data was processed via Python scripts during development and embedded as JS literals.

### Enthermal Schema (60 records)

Each record represents one VIG configuration (outer lite + coating + inner lite):

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `outerGlass` | string | Outboard substrate + thickness | `"Clear 4mm"` |
| `coating` | string | Low-E coating name | `"Cardinal LoĒ³-366®"` |
| `innerGlass` | string | Inboard substrate + thickness | `"Clear 4mm"` |
| `thickness` | float | Overall VIG thickness in mm | `8.05` |
| `uval` | float | U-value in W/m²·K | `0.3752` |
| `uvalIP` | float | U-value in BTU/hr·ft²·°F | `0.0661` |
| `rval` | float | R-value (insulation) | `15.13` |
| `shgc` | float | Solar Heat Gain Coefficient (0–1) | `0.4004` |
| `tvis` | float | Visible Light Transmittance (0–1) | `0.7146` |
| `routVis` | float | Exterior Visible Reflectance (0–1) | `0.1074` |
| `tdwISO` | float | Damage-Weighted UV Transmittance ISO (0–1) | `0.5431` |
| `tuv` | float | UV Transmittance (0–1) | `0.1576` |
| `extL`, `extA`, `extB` | float | Exterior reflected color in CIE L\*a\*b\* | `39.14, -0.81, -2.23` |
| `intL`, `intA`, `intB` | float | Interior transmitted color in CIE L\*a\*b\* | `87.65, -2.54, 2.55` |

**Derived fields** (computed at runtime from `outerGlass`): `outerThickness`, `outerColorName`, `innerThickness`

### Enthermal Plus Schema (36 records)

Each record represents one triple-pane IGU configuration:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `outerCoating` | string | Outboard Low-E coating | `"Cardinal LoĒ²-272®"` |
| `vigCoating` | string | Enthermal VIG interior coating | `"Cardinal LoĒ-180™"` |
| `vigSurface` | string | Coating surface position | `"S4"` or `"S5"` |
| `thickness` | float | Overall IGU thickness in mm | `24.65` |
| `uval` | float | U-value in W/m²·K | `0.3036` |
| `uvalIP` | float | U-value in BTU/hr·ft²·°F | `0.0535` |
| `rval` | float | R-value | `18.7` |
| `shgc` | float | Solar Heat Gain Coefficient | `0.3364` |
| `tvis` | float | Visible Light Transmittance | `0.5678` |
| `routVis` | float | Exterior Visible Reflectance | `0.1296` |
| `tdwISO` | float | Damage-Weighted UV ISO | `0.3948` |
| `tuv` | float | UV Transmittance | `0.0528` |
| `extL`, `extA`, `extB` | float | Exterior color CIE L\*a\*b\* | `42.66, -2.06, -0.9` |
| `intL`, `intA`, `intB` | float | Interior color CIE L\*a\*b\* | `79.94, -3.81, 4.58` |

### Configuration Coverage

**Enthermal** (60 configs):
- 9 coatings: LoĒ-180, LoĒ²-270, LoĒ²-272, LoĒ³-340, LoĒ³-366, Solarban 60, Solarban 70, COOL-LITE SKN 183, ECLAZ ZEN II
- 7 substrates: Clear, Optiblue®, Optigray®, Solarbronze®, Solargray®, Solarblue®, Solexia®
- 3 outer thicknesses: 4mm, 5mm, 6mm
- 3 inner thicknesses: 4mm, 5mm, 6mm (constrained by outer selection)

**Enthermal Plus** (36 configs):
- 6 outer coatings: LoĒ-180, LoĒ²-270, LoĒ²-272, LoĒ³-366, Solarban 60, Solarban 70
- 4 VIG coatings × 1–2 surface positions
- All configs use 4mm clear lites (4mm outer + 4mm middle + 4mm inner)
- Fixed 12.7mm argon gap (90% Argon / 10% Air)

### Color Rendering Pipeline

Glass colors are stored as CIE L\*a\*b\* values and converted to sRGB at runtime:

```
CIE L*a*b* → XYZ (D65 illuminant) → Linear sRGB → Gamma correction → 8-bit RGB
```

The resulting RGB is used for the flat window display (with a 3-stop gradient for depth) and the displayed L\*a\*b\* values. The flip button toggles between exterior reflected (default) and interior transmitted color for the same configuration. A disclaimer note below the window reminds users that screen colors should not be used as a substitute for a mock-up.

---

## 4. How Can the Data Be Updated or Modified?

### Current State

All performance data is hardcoded as JavaScript object literals inside the HTML file. To update data today, you must edit the `const DATA = [...]` and `const DATA_PLUS = [...]` arrays directly in the source file. This is manageable for small changes but does not scale well.

### Recommended Approach: External JSON Data Files

Separate the data from the application by moving the arrays into standalone JSON files:

```
/configurator/
├── index.html              ← Application (UI + logic only)
├── data/
│   ├── enthermal.json      ← Enthermal configs (60 records)
│   └── enthermal-plus.json ← Enthermal Plus configs (36 records)
```

The app would load data at startup via `fetch()`:

```javascript
Promise.all([
  fetch('data/enthermal.json').then(r => r.json()),
  fetch('data/enthermal-plus.json').then(r => r.json())
]).then(([enthermal, plus]) => {
  DATA = enthermal;
  DATA_PLUS = plus;
  initApp();
});
```

**Benefits:**
- Product engineers can update JSON files without touching application code
- JSON files can be generated automatically from the PyWinCalc CSV pipeline
- Version control shows clear diffs when data changes
- Multiple environments (staging, production) can use different data files

### Automated Data Pipeline

For ongoing updates, build a simple pipeline:

```
PyWinCalc → CSV export → Python transform script → JSON files → Deploy
```

The Python transform script would:
1. Read `All_VIG_PyWinCalc_Data.csv`
2. Filter by product type (Enthermal / EnthermalPlus)
3. Map CSV column names to the JSON schema fields
4. Compute derived fields (R-value from U-value, etc.)
5. Output `enthermal.json` and `enthermal-plus.json`

This script already exists conceptually in the data processing done during V2 development and can be formalized into a reusable tool.

### Adding New Products or Coatings

To add a new coating (e.g., a new Cardinal or Solarban variant):
1. Run the new glass configuration through PyWinCalc
2. Append the results to the CSV
3. Re-run the transform script to regenerate JSON
4. Deploy — the UI automatically picks up new coatings in the dropdowns (no code changes needed)

To add Enthermal Spandrel (the currently disabled third tab):
1. Create a `data/enthermal-spandrel.json` with the appropriate schema
2. Add a `DATA_SPANDREL` array and corresponding filter/display functions
3. Enable the Spandrel tab button

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

**Deployment is literally one file** — upload `enthermal-configurator.html` and it works. No Node.js, no PHP, no database server.

If the data is separated into JSON files (recommended), upload the `data/` folder alongside the HTML file.

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

The primary concern is **unauthorized modification** of the app after deployment — ensuring that the performance data shown to customers, architects, and specifiers is accurate and has not been tampered with.

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
fetch('data/enthermal.json')
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

- **AWS S3**: Enable versioning and object lock (WORM — Write Once Read Many) to prevent modification of deployed files
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

> **Note:** No client-side application can be made fully tamper-proof — anyone can inspect and modify what runs in their browser. The security measures above protect the **deployed source of truth** so that the data served to all users is accurate. For regulatory or contractual scenarios requiring certified performance data, consider generating signed PDF reports server-side.
