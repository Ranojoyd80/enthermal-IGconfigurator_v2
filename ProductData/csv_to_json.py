"""
Convert PyWinCalc CSV exports to JSON for the Enthermal Configurator.

Outputs:
  data/enthermal.json
  data/enthermal-plus-inboard.json
  data/enthermal-plus-outboard.json

Usage:
  python csv_to_json.py
"""

import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')

# CSV file paths
ENTHERMAL_CSV = os.path.join(SCRIPT_DIR, 'PyWinCalc_Enthermal_10-04-26.csv')
PLUS_INBOARD_CSV = os.path.join(SCRIPT_DIR, 'PyWinCalc_EnthermalPlus_Inboard_10-04-26.csv')
PLUS_OUTBOARD_CSV = os.path.join(SCRIPT_DIR, 'PyWinCalc_EnthermalPlus_Outboard_10-04-26.csv')


def parse_float(val):
    """Convert string to float, return None if empty."""
    val = val.strip()
    if not val:
        return None
    return float(val)


def normalize_coating(val):
    """Normalize coating name strings (collapse double spaces)."""
    import re
    return re.sub(r'  +', ' ', val)


def normalize_lite_name(raw_name, nominal_mm=None):
    """Normalize a lite name to standard "Name Xmm" format.

    Handles all known CSV variants in one place:
      "4mm Clear"               -> "Clear 4mm"       (flip leading thickness)
      "4 mm Clear"              -> "Clear 4mm"        (fix spacing + flip)
      "Clear Float Glass"       -> "Clear 4mm"        (generic, thickness from Comment)
      "Float Glass"             -> "Clear 4mm"        (generic, thickness from Comment)
      "Float Glass - 4mm"       -> "Clear 4mm"        (generic with thickness)
      "Clear Float Glass - 4mm" -> "Clear 4mm"        (generic with thickness)
      "Optigray®  6mm"          -> "Optigray® 6mm"    (collapse double spaces)
      "SGG ECLAZ II 4mm"        -> "SGG ECLAZ II 4mm" (already correct)
    """
    import re
    val = raw_name.strip()
    # Collapse double spaces
    val = re.sub(r'  +', ' ', val)

    # Generic clear glass without thickness — use nominal_mm from Comment
    if val in ('Clear Float Glass', 'Float Glass') and nominal_mm is not None:
        return f'Clear {nominal_mm}mm'

    # Generic clear glass with thickness: "Float Glass - 4mm", "Clear Float Glass - 4mm"
    m = re.match(r'^(?:Clear )?Float Glass\s*-\s*(\d+mm)$', val)
    if m:
        return f'Clear {m.group(1)}'

    # Leading thickness with space before mm: "4 mm Clear" -> "Clear 4mm"
    m = re.match(r'^(\d+)\s+mm\s+(.+)$', val)
    if m:
        return f'{m.group(2)} {m.group(1)}mm'

    # Leading thickness: "4mm Clear" -> "Clear 4mm"
    m = re.match(r'^(\d+mm)\s+(.+)$', val)
    if m:
        return f'{m.group(2)} {m.group(1)}'

    return val


def parse_lite_thicknesses_from_comment(comment):
    """Extract nominal thickness for each lite from the Comment field.

    Comment formats:
      Enthermal:      "SB60 4mm / Vacuum 0.25mm / Clear 4mm"
      Plus Inboard:   "C180 4mm / Argon 13.36mm / SB60 4mm / Vacuum 0.25mm / Clear 4mm"
      Plus Outboard:  "SB60 4mm / Vacuum 0.25mm / Clear 4mm / Argon 13.36mm / C180 4mm"

    Returns a list of lite thicknesses in order (excluding Vacuum and Argon segments).
    """
    import re
    parts = [p.strip() for p in comment.split('/')]
    thicknesses = []
    for part in parts:
        # Skip Vacuum, Argon, and Air gap segments
        low = part.lower()
        if low.startswith('vacuum') or low.startswith('argon') or low.startswith('air'):
            continue
        # Match nominal thickness: "SB60 4mm" -> 4, "Clear 6mm" -> 6
        # Use word-boundary match to avoid picking up decimals like "13.45mm"
        m = re.search(r'(?<!\.)(\d+)mm', part)
        if m:
            thicknesses.append(int(m.group(1)))
        else:
            thicknesses.append(None)
    return thicknesses


def convert_enthermal(csv_path):
    """Convert Enthermal CSV to JSON array."""
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Parse nominal thicknesses from Comment: "SB60 4mm / Vacuum 0.25mm / Clear 4mm"
            # Gives [outer_mm, inner_mm]
            thicknesses = parse_lite_thicknesses_from_comment(r['Comment'])
            inner_mm = thicknesses[1] if len(thicknesses) > 1 else None
            rows.append({
                'outerLite': normalize_lite_name(r['Outer Lite (Name_Thickness mm)']),
                'outerLowE': normalize_coating(r['Outer Lite Low-E'].strip()),
                'innerLite': normalize_lite_name(r['Inner Lite (Name_Thickness mm)'], inner_mm),
                'totalThickness': parse_float(r['Total Thickness (mm)']),
                'uval': parse_float(r['U-value NFRC (W/m²K)']),
                'uvalIP': parse_float(r['U-value NFRC (BTU/hrftF)']),
                'rval': parse_float(r['R-value NFRC']),
                'shgc': parse_float(r['SHGC']),
                'tvis': parse_float(r['Tvis (Visible Transmittance)']),
                'routVis': parse_float(r['Exterior Visible Reflectance']),
                'tuv': parse_float(r['T-UV']),
                'extL': parse_float(r['Exterior Reflected Color L*']),
                'extA': parse_float(r['Exterior Reflected Color a*']),
                'extB': parse_float(r['Exterior Reflected Color b*']),
                'intL': parse_float(r['Interior Reflected Color L*']),
                'intA': parse_float(r['Interior Reflected Color a*']),
                'intB': parse_float(r['Interior Reflected Color b*']),
            })
    return rows


def convert_plus(csv_path):
    """Convert Enthermal Plus CSV to JSON array."""
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Parse nominal thicknesses from Comment:
            #   Inboard:  "C180 4mm / Argon 13.36mm / SB60 4mm / Vacuum 0.25mm / Clear 4mm"
            #             -> [outer, middle, inner]
            #   Outboard: "SB60 4mm / Vacuum 0.25mm / Clear 4mm / Argon 13.36mm / C180 4mm"
            #             -> [outer, middle, inner]
            thicknesses = parse_lite_thicknesses_from_comment(r['Comment'])
            outer_mm = thicknesses[0] if len(thicknesses) > 0 else None
            middle_mm = thicknesses[1] if len(thicknesses) > 1 else None
            inner_mm = thicknesses[2] if len(thicknesses) > 2 else None

            rows.append({
                'outerLite': normalize_lite_name(r['Outer Lite (Name_Thickness mm)'], outer_mm),
                'outerLowE': normalize_coating(r['Outer Lite Low-E'].strip()),
                'middleLite': normalize_lite_name(r['Middle Lite (Name_Thickness mm)'], middle_mm),
                'middleLowE': normalize_coating(r['Middle Lite Low-E'].strip()),
                'innerLite': normalize_lite_name(r['Inner Lite (Name_Thickness mm)'], inner_mm),
                'innerLowE': normalize_coating(r['Inner Lite Low-E'].strip()),
                'gasFill': r['Gas Fill'].strip(),
                'totalThickness': parse_float(r['Total Thickness (mm)']),
                'uval': parse_float(r['U-value NFRC (W/m²K)']),
                'uvalIP': parse_float(r['U-value NFRC (BTU/hrftF)']),
                'rval': parse_float(r['R-value NFRC']),
                'shgc': parse_float(r['SHGC']),
                'tvis': parse_float(r['Tvis (Visible Transmittance)']),
                'routVis': parse_float(r['Exterior Visible Reflectance']),
                'tuv': parse_float(r['T-UV']),
                'extL': parse_float(r['Exterior Reflected Color L*']),
                'extA': parse_float(r['Exterior Reflected Color a*']),
                'extB': parse_float(r['Exterior Reflected Color b*']),
                'intL': parse_float(r['Interior Reflected Color L*']),
                'intA': parse_float(r['Interior Reflected Color a*']),
                'intB': parse_float(r['Interior Reflected Color b*']),
            })
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Convert Enthermal
    enthermal = convert_enthermal(ENTHERMAL_CSV)
    out_path = os.path.join(OUTPUT_DIR, 'enthermal.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(enthermal, f, ensure_ascii=False, indent=2)
    print(f'enthermal.json: {len(enthermal)} rows')

    # Convert Plus Inboard
    plus_inboard = convert_plus(PLUS_INBOARD_CSV)
    out_path = os.path.join(OUTPUT_DIR, 'enthermal-plus-inboard.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(plus_inboard, f, ensure_ascii=False, indent=2)
    print(f'enthermal-plus-inboard.json: {len(plus_inboard)} rows')

    # Convert Plus Outboard
    plus_outboard = convert_plus(PLUS_OUTBOARD_CSV)
    out_path = os.path.join(OUTPUT_DIR, 'enthermal-plus-outboard.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(plus_outboard, f, ensure_ascii=False, indent=2)
    print(f'enthermal-plus-outboard.json: {len(plus_outboard)} rows')

    # Report all unique coatings found
    all_coatings = set()
    for row in enthermal:
        all_coatings.add(row['outerLowE'])
    for row in plus_inboard + plus_outboard:
        all_coatings.add(row['outerLowE'])
        if row['middleLowE']:
            all_coatings.add(row['middleLowE'])
        if row['innerLowE']:
            all_coatings.add(row['innerLowE'])

    print(f'\nUnique coatings found ({len(all_coatings)}):')
    for c in sorted(all_coatings):
        print(f'  {c}')


if __name__ == '__main__':
    main()
