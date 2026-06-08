# Product Data Constants

Runtime lookup values that are not stored in the per-configuration JSON files. These are applied by the configurator at display time based on the current selection.

---

## Embodied Carbon

Lookup by total unit thickness.

### Enthermal™

Cradle-Gate (A1–A3) is shown in NFRC mode; Cradle-Grave (full life cycle) is shown in CEN mode.

| Total Thickness | Cradle-Gate A1–A3 (kg CO₂e/m²) | Cradle-Grave Full Life Cycle (kg CO₂e/m²) |
|---|---|---|
| 8 mm | 29.3 _(calculated)_ | 34.6 _(calculated)_ |
| 9 mm | 33.9 _(interpolated)_ | 39.6 _(interpolated)_ |
| 10 mm | **38.4** _(published)_ | **44.6** _(published)_ |
| 11 mm | 43.7 _(interpolated)_ | 50.7 _(interpolated)_ |
| 12 mm | 49.0 _(calculated)_ | 56.7 _(calculated)_ |

_9 mm and 11 mm values are linear midpoints between adjacent published/calculated points._

### Enthermal Plus™

_TBD_

---

## Acoustic Insulation (OITC / Rw)

Lookup by unit thickness. OITC is shown in NFRC mode; Rw is shown in CEN mode.

### Enthermal™

| Unit Thickness | Rw (dB) | OITC (dB) |
|---|---|---|
| 8-mm (4/4) Enthermal | 35 | 31 |
| 9-mm (4/5) Enthermal | 35 | 31 |
| 10-mm (5/5) Enthermal | 35 | 30 |
| 10-mm (4/6) Enthermal | 34 | 31 |
| 11-mm (5/6) Enthermal | 35 | 32 |
| 12-mm (6/6) Enthermal | 36 | 32 |

_Note: Rw, Rw(C), Rw(Ctr) per ISO 717-1. OITC per ASTM E1332._

---

## IGU Weight

Calculated from total glass thickness (sum of all lites, excluding the vacuum gap).

**Formulas:**
- Metric: `weight (kg/m²) = 2.5 × total_glass_thickness_mm`
- Imperial: `weight (lb/ft²) = 0.512 × total_glass_thickness_mm`

### Examples

| Configuration | Glass Thickness | Weight (kg/m²) | Weight (lb/ft²) |
|---|---|---|---|
| 4/4 | 8 mm | 20.0 | 4.10 |
| 4/5 | 9 mm | 22.5 | 4.61 |
| 5/5 | 10 mm | 25.0 | 5.12 |
| 4/6 | 10 mm | 25.0 | 5.12 |
| 5/6 | 11 mm | 27.5 | 5.63 |
| 6/6 | 12 mm | 30.0 | 6.14 |
