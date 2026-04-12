# Product Data Constants

Runtime lookup values that are not stored in the per-configuration JSON files. These are applied by the configurator at display time based on the current selection.

---

## Embodied Carbon

Lookup by total unit thickness.

### Enthermal™

| Total Thickness | Embodied Carbon (kg CO₂e/m²) |
|---|---|
| 8 mm | _TBD_ |
| 9 mm | _TBD_ |
| 10 mm | **38.6** |
| 11 mm | _TBD_ |
| 12 mm | _TBD_ |

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
