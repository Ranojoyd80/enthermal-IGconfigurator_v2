# JSON Schema for Enthermal Configurator

Generated from the source CSVs in `../1_Source_CSVs/` by `csv_to_json.py` (in this
folder). Never hand-edit the output — change the CSV or the script and regenerate.

## Output Files

| File | Product | Rows | Glass panes |
|---|---|---|---|
| `App_Data/enthermal.json` | Enthermal (VIG) | 98 | 2 |
| `App_Data/enthermal-plus-inboard.json` | Enthermal Plus (VIG inboard) | 4,748 | 3 |
| `App_Data/enthermal-plus-outboard.json` | Enthermal Plus (VIG outboard) | 2,016 | 3 |

Each file is a JSON array of objects. All numeric values are stored as numbers (or
`null` when the source cell is blank), never as strings.

---

## Record schema

Every record — all three files — has the same flat field set. The build makeup
lives in the `stack` array; everything else is a scalar metric or color.

```json
{
  "stack": [
    { "type": "glass", "coating": "SB60", "substrate": "Solargray", "thickness": 6 },
    { "type": "gas", "gasType": "Ar90", "thickness": 8.05 },
    { "type": "glass", "coating": "SB60", "substrate": "Clear", "thickness": 6 },
    { "type": "vacuum", "thickness": 0.25 },
    { "type": "glass", "coating": null, "substrate": "Clear", "thickness": 6 }
  ],
  "totalThickness": 25.5,
  "uval": 0.3024,
  "uvalIP": 0.0533,
  "rval": 18.78,
  "shgc": 0.1504,
  "tvis": 0.2781,
  "routVis": 0.0635,
  "tuv": 0.0274,
  "extL": 30.27,
  "extA": -0.14,
  "extB": -2.42,
  "intL": 42.86,
  "intA": -4.25,
  "intB": 2.95,
  "nfrc": true,
  "cen": false,
  "gFactor": null,
  "uvalCEN": null,
  "cid": 27
}
```

Enthermal records have the same shape but a 2-pane `stack` (a single `vacuum`
gap, no `gas`) and typically `gFactor`/`uvalCEN` = `null`.

---

## The `stack` array

Parsed from the CSV `Comment` column by `parse_stack` / `parse_layer`. Layers are
in **optical order, exterior → interior**. Three layer kinds:

| `type` | Fields | Notes |
|---|---|---|
| `glass` | `coating`, `substrate`, `thickness` | `coating` is a shortcode (e.g. `SB60`, `C270`, `LUMI`) or `null` if uncoated. `substrate` is a name (`Clear`, `Solargray`, `Starphire`, …). `thickness` is an integer mm. |
| `gas` | `gasType`, `thickness` | `gasType` is `"Ar90"` or `"Air"`. `thickness` is mm (float). |
| `vacuum` | `thickness` | The VIG vacuum gap, ~`0.25` mm. |

`coating` and `substrate` shortcodes must be registered in `COATING_NAMES` /
`SUBSTRATE_NAMES` in `enthermal-configurator.html`; `csv_to_json.py` raises on any
unknown token so new products fail loudly instead of silently mislabeling.

> **Surface numbers are NOT stored.** The `stack` records *which pane* carries a
> coating, not which face. The front-end re-derives the surface at load time by a
> fixed positional convention in `postProcessData()` — outer-pane coating → S2,
> middle-pane → S4, inner-pane → S5. (Verified against the CSV Low-E suffixes for
> all 137 render anchors: 0 mismatches; only S2/S4/S5 ever occur.) The authoritative
> surface number survives only in the CSV `… Lite Low-E` column suffix.

---

## Scalar field reference

| Field | Type | Unit | Description |
|---|---|---|---|
| `totalThickness` | number | mm | Total IGU thickness |
| `uval` | number | W/m²K | U-value (NFRC, SI) |
| `uvalIP` | number | BTU/hr·ft²·°F | U-value (NFRC, IP) |
| `rval` | number | hr·ft²·°F/BTU | R-value (NFRC) |
| `shgc` | number | — | Solar Heat Gain Coefficient |
| `tvis` | number | — | Visible Transmittance |
| `routVis` | number | — | Exterior Visible Reflectance |
| `tuv` | number | — | UV Transmittance |
| `extL` / `extA` / `extB` | number | — | Exterior Reflected Color CIE L\*a\*b\* |
| `intL` / `intA` / `intB` | number | — | Interior Reflected Color CIE L\*a\*b\* |
| `nfrc` | boolean | — | `true` if the row is an NFRC-rated configuration |
| `cen` | boolean | — | `true` iff a Saint-Gobain coating sits on Surface 2 |
| `gFactor` | number \| null | — | CEN solar factor (g); `null` when not provided |
| `uvalCEN` | number \| null | W/m²K | U-value (CEN); `null` when not provided |
| `cid` | integer | — | Color-cluster anchor id → exterior render `anchor_<cid>.webp`. **Not from the CSV** — injected by `3_Clustering/recluster_at_jnd.py`, which runs after `csv_to_json.py` and is the final writer of this JSON. See `../3_Clustering/CLUSTERING_PROCEDURE.md`. |

---

## Notes

- Numeric blanks in the CSV become `null`, not `0` or `""`.
- `coating` is `null` (not `""`) for an uncoated lite.
- Preserve Unicode in source/display names: ² ³ ® (handled in the HTML name maps).
- Fields intentionally NOT carried per-record (looked up elsewhere at display time):
  Product Type, the raw Comment string, NFRC IDs, surface numbers, manufacturer,
  OITC, Rw, IGU Weight, Embodied Carbon. See `../Product Data Constants.md`.
