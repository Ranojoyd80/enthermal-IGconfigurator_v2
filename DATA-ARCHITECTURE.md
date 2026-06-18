# Data Architecture — Enthermal Configurator

> Decisions and specifications for the data layer powering the configurator UI.

---

## 1. Data Storage

**External JSON files** loaded via `fetch()` at runtime. Three files served alongside the HTML:

| File | Product | Rows | Size |
|---|---|---|---|
| `App_Data/enthermal.json` | Enthermal | 98 | ~71 KB |
| `App_Data/enthermal-plus-inboard.json` | Enthermal Plus (VIG inboard) | 4,748 | ~4.5 MB |
| `App_Data/enthermal-plus-outboard.json` | Enthermal Plus (VIG outboard) | 2,016 | ~1.9 MB |

**Source of truth:** these JSON files are *generated*, never hand-edited. The
authoritative data is the three CSVs in `Data_Pipeline/1_Source_CSVs/` (raw PyWinCalc/LBNL exports);
`Data_Pipeline/2_Conversion/csv_to_json.py` converts them into the trimmed, app-shaped JSON above.
To change data: edit the CSV (or the script) and regenerate — see §7.

**Why external JSON instead of embedded JS arrays:**
- Data updates don't touch UI code — drop new JSON files, done
- Clean git history — data commits separated from UI commits
- Browser caches JSON — repeat visitors skip unchanged downloads
- ~6,000 rows embedded would bloat the HTML to ~800 KB

---

## 2. JSON Schema

See `Data_Pipeline/2_Conversion/json-schema.md` for the full field reference.

Every record (all three files) has the same flat field set: a **`stack`** array
(the build makeup, exterior → interior — `glass`/`gas`/`vacuum` layers) plus scalar
metrics and colors: `totalThickness`, `uval`, `uvalIP`, `rval`, `shgc`, `tvis`,
`routVis`, `tuv`, `extL/A/B`, `intL/A/B`, `nfrc`, `cen`, `gFactor`, `uvalCEN`.

- Each `glass` layer carries `coating` (a shortcode like `C366`/`SB60`, or `null`),
  `substrate` (`Clear`, `Solargray`, …) and `thickness` (mm).
- Enthermal `stack` = 2 panes + 1 `vacuum`; Enthermal Plus = 3 panes + 1 `gas` + 1 `vacuum`.
- `gFactor`/`uvalCEN` are `null` unless the row has CEN-rated values.

---

## 3. Fields Excluded from JSON

| Field | Reason |
|---|---|
| Product Type | Implicit per file |
| Comment | Build-time only — it's the string `csv_to_json.py` parses into `stack`; not shipped |
| Coating **surface number** | Dropped from `stack`; re-derived at runtime by convention (outer→S2, middle→S4, inner→S5). Authoritative value survives only in the CSV `… Lite Low-E` suffix |
| NFRC IDs | Not displayed |
| tdwISO | Removed entirely |
| Manufacturer | JS lookup table (see below) |

---

## 4. Runtime Calculations (in HTML JS)

| Metric | Lookup Key | Notes |
|---|---|---|
| IGU Weight | Total glass thickness (mm) | Formula: `2.5 × total_glass_mm` kg/m² |
| OITC / Rw | Enthermal lite thickness pair | `ENTHERMAL_ACOUSTIC` lookup; OITC shown in NFRC mode, Rw in CEN mode |
| Embodied Carbon | Total glass thickness (8–12 mm) | `EMBODIED_CARBON` lookup table; NFRC = Cradle-Gate (A1–A3), CEN = Cradle-Grave. Enthermal Plus has no data yet → `—` |

Source values for these tables live in `Data_Pipeline/Product Data Constants.md`.
The CEN/NFRC "Standard" toggle auto-locks to each config's `cen` flag and swaps the
metric set: CEN mode shows `uvalCEN`, `gFactor` (in place of SHGC), and Rw; NFRC mode
shows `uval`/`uvalIP`, `rval`, SHGC, and OITC.

---

## 5. Coating Display Names

Three levels of coating name used in the UI:

| Context | Format | Example |
|---|---|---|
| JSON data (raw) | Coating **shortcode** in the `stack`, no surface | `C366` |
| Config panel dropdown | Manufacturer + product, no surface | `Cardinal LoE³ 366` |
| Summary bar & cross-section | Short name, no surface, no manufacturer | `LoE³ 366` |

(Shortcode → display-name mapping lives in the JS lookups in the HTML.)

**Short name rules by brand:**

| Raw Name Pattern | Short Name |
|---|---|
| LoE / LoE² / LoE³ / Quad LoE ... | Keep as-is minus surface |
| Solarban® ... | `Solarban` + model (strip ®) |
| COOL-LITE SKN 183 II ... | `SKN 183` |
| COOL-LITE XTREME 61-29 II ... | `XTREME 61-29` |
| ECLAZ II ... | `ECLAZ` |

**Manufacturer lookup:** A JS object in the HTML maps coating base names to manufacturers (Cardinal, Vitro, Saint-Gobain). If a coating loaded from JSON is not in the lookup, log `console.warn("Unknown manufacturer for coating: XYZ")`.

---

## 6. Data Flow — Filter Cascades

### Enthermal
Outer Thickness → Low-E Coating → Inner Thickness → **single row**

### Enthermal Plus — Inboard Placement
Outboard Thickness → Outboard Low-E Coating → Gas Fill (Argon/Air) → VIG Thickness → VIG Low-E Coating → Coating Surface (S4/S5) → **single row**

### Enthermal Plus — Outboard Placement
VIG Thickness → VIG Low-E Coating → Gas Fill (Argon/Air) → Inboard Thickness → Inboard Low-E Coating (always S5, no toggle) → **single row**

---

## 7. Data Update Procedure

The pipeline is **CSV → `csv_to_json.py` → JSON** (the CSVs are the source of truth):

1. PyWinCalc/LBNL run produces the dataset CSVs in `Data_Pipeline/1_Source_CSVs/` (e.g. `IG_Config_*_12-04-26.csv`)
2. Run `python Data_Pipeline/2_Conversion/csv_to_json.py` → writes the 3 files into `App_Data/` (see `Data_Pipeline/2_Conversion/json-schema.md` for the output format)
3. No HTML changes needed for data-only updates
4. If a CSV introduces a new coating or substrate token, `csv_to_json.py` **fails loudly** — register it in the `COATING_NAMES` / `SUBSTRATE_NAMES` (and manufacturer) lookups in the HTML, then regenerate
5. The JND color clustering is a downstream step that **rewrites** the JSON — `python Data_Pipeline/3_Clustering/recluster_at_jnd.py` clusters the 6,862 configs to 137 anchors and **injects an integer `cid` (anchor id) onto every record**. It is therefore the *final* writer of `App_Data/*.json`: re-running `csv_to_json.py` alone drops `cid`, so always re-run the clustering after it. See `Data_Pipeline/3_Clustering/CLUSTERING_PROCEDURE.md`.

---

## 8. Hosting & Testing

- **Production:** HTML + JSON files served from the same web host. `fetch()` uses relative paths.
- **Pre-launch testing:** GitHub Pages, Netlify Drop, or company staging server. All serve over HTTP so fetch works without CORS issues.
- **Local file://:** Not supported for fetch-based loading. Use a local server for testing (`python -m http.server`).
