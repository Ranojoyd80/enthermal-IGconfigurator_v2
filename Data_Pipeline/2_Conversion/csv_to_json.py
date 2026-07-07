"""
Convert IG_Config CSV exports to JSON for the Enthermal Configurator.

Source of truth is the CSV's `Comment` column, which encodes the full glass
stack in a structured, hand-normalized form:

  Enthermal:      C180 4mm / Vacuum 0.25mm / Clear 4mm
  Plus Inboard:   C180 4mm / Argon 13.45mm / C180 4mm / Vacuum 0.25mm / Clear 4mm
  Plus Outboard:  C180 4mm / Vacuum 0.25mm / Clear 4mm / Argon 13.45mm / C180 4mm

Each ` / `-delimited layer is one of:
  <code> <substrate> <thickness>mm   — coated glass on branded substrate
  <code> <thickness>mm               — coated glass on implied Clear substrate
  <substrate> <thickness>mm          — uncoated glass lite
  Vacuum <thickness>mm               — vacuum gap
  Air|Argon <thickness>mm            — gas-filled gap

The per-lite name columns and Low-E columns are ignored — they bring back the
old naming mess (SGG prefixes, ®/™, variable thickness position). Everything
the UI needs is in the stack.

Outputs:
  App_Data/enthermal.json
  App_Data/enthermal-plus-inboard.json
  App_Data/enthermal-plus-outboard.json

Usage:
  python csv_to_json.py
"""

import csv
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))      # Data_Pipeline/2_Conversion
PRODUCT_DATA = os.path.dirname(SCRIPT_DIR)                    # Data_Pipeline
REPO_ROOT = os.path.dirname(PRODUCT_DATA)                     # repo root
OUTPUT_DIR = os.path.join(REPO_ROOT, 'App_Data')
HTML_PATH = os.path.join(REPO_ROOT, 'enthermal-configurator.html')

CSV_DIR = os.path.join(PRODUCT_DATA, '1_Source_CSVs')
ENTHERMAL_CSV = os.path.join(CSV_DIR, 'IG_Config_Enthermal_Dataset_07-07-26.csv')
PLUS_INBOARD_CSV = os.path.join(CSV_DIR, 'IG_Config_EnthermalPlus_Inboard_Dataset_07-07-26.csv')
PLUS_OUTBOARD_CSV = os.path.join(CSV_DIR, 'IG_Config_EnthermalPlus_Outboard_Dataset_07-07-26.csv')

# Rewrites applied to coating shortcodes during import. Keep the CSV's raw
# codes on the left; the canonical set the app consumes is on the right.
CSV_SHORTCODE_REWRITES = {
    'SB67': 'SBR67',      # preserves the "R" in Vitro's Solarban R67
    'XTREME': 'XTR6129',  # adds the 61-29 number to COOL-LITE XTREME
}


def load_html_lookups():
    """Read COATING_NAMES and SUBSTRATE_NAMES from the HTML so the converter
    validates against whatever the runtime actually knows about. Any CSV
    shortcode missing from these tables is a new product that needs to be
    added to the HTML before the JSON can be regenerated.
    """
    try:
        with open(HTML_PATH, encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise ValueError(f'Cannot find HTML at {HTML_PATH} to validate product names')

    def extract(name):
        m = re.search(
            r'const ' + name + r'\s*=\s*\{(.*?)\};',
            content,
            re.DOTALL,
        )
        if not m:
            raise ValueError(f'Could not locate "const {name} = {{...}};" in {HTML_PATH}')
        # Parse 'KEY': 'VALUE' pairs (JS string literals in single quotes).
        return dict(re.findall(r"'([^']+)'\s*:\s*'([^']*)'", m.group(1)))

    coatings = extract('COATING_NAMES')
    substrates = extract('SUBSTRATE_NAMES')
    if not coatings:
        raise ValueError('COATING_NAMES lookup in HTML appears empty')
    if not substrates:
        raise ValueError('SUBSTRATE_NAMES lookup in HTML appears empty')
    return set(coatings.keys()), set(substrates.keys())


# Populated from HTML at main() time (not import time — keeps the module
# side-effect-free for testing).
KNOWN_COATINGS = set()
KNOWN_SUBSTRATES = set()

# Pre-parse segment rewrites for multi-token substrates that the whitespace
# splitter can't handle. Applied to each segment before token counting.
# Paired with CSV_SHORTCODE_REWRITES as the two "raw CSV -> canonical" passes.
SEGMENT_REWRITES = [
    (re.compile(r'Optiblue \(Solarban z(\d+)\)'), r'OptiblueZ\1'),
]

GAS_TOKENS = {'Vacuum', 'Air', 'Argon', 'Argon90'}


def parse_float(val):
    val = val.strip()
    return float(val) if val else None


def parse_layer(segment, row_index, csv_name):
    """Parse one ` / `-delimited segment of a Comment into a layer dict."""
    for pattern, replacement in SEGMENT_REWRITES:
        segment = pattern.sub(replacement, segment)
    tokens = segment.split()

    if len(tokens) == 2:
        name, thickness_str = tokens
        thickness = float(thickness_str.rstrip('mm'))
        if name == 'Vacuum':
            return {'type': 'vacuum', 'thickness': thickness}
        if name in GAS_TOKENS:
            gas_type = 'Ar90' if name in ('Argon90', 'Argon') else name
            return {'type': 'gas', 'gasType': gas_type, 'thickness': thickness}
        # 2-token coated glass — coating on implied Clear substrate
        code = CSV_SHORTCODE_REWRITES.get(name, name)
        if code in KNOWN_COATINGS:
            return {'type': 'glass', 'coating': code, 'substrate': 'Clear', 'thickness': int(thickness)}
        # 2-token uncoated glass
        if name not in KNOWN_SUBSTRATES:
            raise ValueError(
                f'{csv_name} row {row_index}: NEW SUBSTRATE "{name}" in segment "{segment}"\n'
                f'  -> Add "{name}": "<display name>" to SUBSTRATE_NAMES in enthermal-configurator.html'
            )
        return {'type': 'glass', 'coating': None, 'substrate': name, 'thickness': int(thickness)}

    if len(tokens) == 3:
        code, substrate, thickness_str = tokens
        raw_code = code
        code = CSV_SHORTCODE_REWRITES.get(code, code)
        if code not in KNOWN_COATINGS:
            hint = f' (rewritten from CSV "{raw_code}")' if raw_code != code else ''
            raise ValueError(
                f'{csv_name} row {row_index}: NEW COATING "{code}"{hint} in segment "{segment}"\n'
                f'  -> Add "{code}": "<display name>" to COATING_NAMES in enthermal-configurator.html'
            )
        if substrate not in KNOWN_SUBSTRATES:
            raise ValueError(
                f'{csv_name} row {row_index}: NEW SUBSTRATE "{substrate}" in segment "{segment}"\n'
                f'  -> Add "{substrate}": "<display name>" to SUBSTRATE_NAMES in enthermal-configurator.html'
            )
        thickness = int(thickness_str.rstrip('mm'))
        return {'type': 'glass', 'coating': code, 'substrate': substrate, 'thickness': thickness}

    raise ValueError(
        f'{csv_name} row {row_index}: unexpected layer token count ({len(tokens)}) in segment "{segment}"'
    )


def parse_stack(comment, row_index, csv_name):
    segments = [s.strip() for s in comment.split(' / ')]
    return [parse_layer(s, row_index, csv_name) for s in segments]


def _col(row, prefix):
    """Find a column by prefix, tolerating encoding variants of ² in headers."""
    for key in row:
        if key.startswith(prefix):
            return row[key]
    return ''


def convert(csv_path):
    csv_name = os.path.basename(csv_path)
    rows = []
    with open(csv_path, encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader, start=2):  # start=2: header is row 1
            rows.append({
                'stack': parse_stack(r['Comment'], i, csv_name),
                'totalThickness': parse_float(r['Total Thickness (mm)']),
                'uval': parse_float(_col(r, 'U-value NFRC (W/')),
                'uvalIP': parse_float(_col(r, 'U-value NFRC (BTU')),
                'rval': parse_float(r['R-value NFRC']),
                'shgc': parse_float(r['SHGC']),
                'tvis': parse_float(r['Tvis (Visible Transmittance)']),
                'routVis': parse_float(r['Exterior Visible Reflectance']),
                'tuv': parse_float(r['T-UV']),
                'extL': parse_float(r['Exterior Reflected Color L*']),
                'extA': parse_float(r['Exterior Reflected Color a*']),
                'extB': parse_float(r['Exterior Reflected Color b*']),
                # The 07-07-26 datasets replaced the Interior Reflected Color
                # columns with Transmitted Color. Exterior Reflected still drives
                # anchor clustering; transmitted color is carried through as trn*.
                'trnL': parse_float(r['Transmitted Color L*']),
                'trnA': parse_float(r['Transmitted Color a*']),
                'trnB': parse_float(r['Transmitted Color b*']),
                'nfrc': r.get('NFRC', '').strip() == 'Yes',
                'cen': r.get('CEN', '').strip() == 'Yes',
                'gFactor': parse_float(r.get('g-factor', '')),
                'uvalCEN': parse_float(_col(r, 'U-value CEN')),
            })
    return rows


def write_json(rows, name):
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f'{name}: {len(rows)} rows')


def main():
    global KNOWN_COATINGS, KNOWN_SUBSTRATES
    KNOWN_COATINGS, KNOWN_SUBSTRATES = load_html_lookups()
    print(f'Validating against HTML lookup: {len(KNOWN_COATINGS)} coatings, {len(KNOWN_SUBSTRATES)} substrates')

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seen_coatings = set()
    seen_substrates = set()
    try:
        for csv_path, out_name in (
            (ENTHERMAL_CSV, 'enthermal.json'),
            (PLUS_INBOARD_CSV, 'enthermal-plus-inboard.json'),
            (PLUS_OUTBOARD_CSV, 'enthermal-plus-outboard.json'),
        ):
            rows = convert(csv_path)
            write_json(rows, out_name)
            for row in rows:
                for layer in row['stack']:
                    if layer['type'] == 'glass':
                        if layer['coating']:
                            seen_coatings.add(layer['coating'])
                        seen_substrates.add(layer['substrate'])
    except ValueError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'\nCoating shortcodes seen ({len(seen_coatings)}): {sorted(seen_coatings)}')
    print(f'Substrates seen ({len(seen_substrates)}): {sorted(seen_substrates)}')


if __name__ == '__main__':
    main()
