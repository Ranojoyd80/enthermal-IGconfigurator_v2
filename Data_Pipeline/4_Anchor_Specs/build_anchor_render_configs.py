"""
Build AnchorRender_Configs.json — the build-CONFIGURATION of the 77 JND render
anchors. This is the PyWinCalc *input*: the optical stack only. It deliberately
carries NO performance or color outputs (U/SHGC/Tvis/Lab/reflectance) — PyWinCalc
computes those. Keeping the file input-only avoids shipping stale duplicates of
results the run will regenerate.

HYBRID SOURCE (by design):
  * MAKEUP comes from the live app data in ../../App_Data/*.json (the optical `stack`:
    pane order exterior->interior, substrate, coating shortcode, thickness, gaps).
  * SURFACE NUMBERS come from the Source CSVs. The app JSON dropped the Low-E surface
    suffix ("LoE 180 S2" -> face S2) when csv_to_json.py built the stack, so the face
    each coating sits on survives only in the CSV Low-E column.

Each anchor is re-joined to its exact source row by (source, source_idx), which
anchors.json carries and which indexes 1:1 into BOTH ../../App_Data/<source> and the
matching CSV (csv_to_json.py appends every row in order, no filtering). The join is
VALIDATED three ways at build time (anchor exterior Lab == data-JSON Lab == CSV Lab,
rounding-tolerant; glass-layer count == CSV present lites) — those references are
used only to verify the join, not emitted.

OPTICS KEY: each layer carries `lite_nfrc_id`, which in the Source CSVs is the
**coated-product** NFRC/IGDB id (unique per glass+coating — verified: one glass name
maps to a different id per Low-E, no id reused across coatings). Mapping
`lite_nfrc_id` -> IGSDB resolves the correct *coated* optics; the coating shortcode /
Low-E name are descriptive only. (This corrects the earlier, mistaken
"NFRC id == bare substrate" note.)

Output (Data_Pipeline/4_Anchor_Specs/AnchorRender_Configs.json): one entry per anchor
with an exterior->interior `layers` array — absolute IGU surface numbers (S1..S2N),
substrate, thickness, coating (shortcode + full Low-E name + surface + pane face),
`lite_nfrc_id`, gas/vacuum gaps — plus a one-line `surface_map`.

Run:  python build_anchor_render_configs.py
"""

import csv
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))      # Data_Pipeline/4_Anchor_Specs
PRODUCT_DATA = os.path.dirname(SCRIPT_DIR)                    # Data_Pipeline
REPO_ROOT = os.path.dirname(PRODUCT_DATA)                     # repo root
DATA_DIR = os.path.join(REPO_ROOT, 'App_Data')
CSV_DIR = os.path.join(PRODUCT_DATA, '1_Source_CSVs')

ANCHORS_JSON = os.path.join(PRODUCT_DATA, '3_Clustering', 'anchors.json')
CSV_FOR_SOURCE = {
    'enthermal.json': 'IG_Config_Enthermal_Dataset_12-04-26.csv',
    'enthermal-plus-inboard.json': 'IG_Config_EnthermalPlus_Inboard_Dataset_12-04-26.csv',
    'enthermal-plus-outboard.json': 'IG_Config_EnthermalPlus_Outboard_Dataset_12-04-26.csv',
}
PRODUCT_LABEL = {
    'enthermal.json': 'Enthermal (VIG, 2 panes)',
    'enthermal-plus-inboard.json': 'Enthermal Plus (VIG inboard)',
    'enthermal-plus-outboard.json': 'Enthermal Plus (VIG outboard)',
}

LITE_COLUMNS = ['Outer', 'Middle', 'Inner']   # optical order, exterior -> interior
SURFACE_RE = re.compile(r'\bS(\d+)\s*$')


def num(s):
    s = (s or '').strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_lowE(raw):
    """'LoE 180 S2' -> ('LoE 180', 2). '' -> (None, None)."""
    raw = (raw or '').strip()
    if not raw:
        return None, None
    m = SURFACE_RE.search(raw)
    if not m:
        return raw, None
    return raw[:m.start()].strip(), int(m.group(1))


def load_csv_rows(name):
    with open(os.path.join(CSV_DIR, name), encoding='latin-1') as fh:
        return list(csv.DictReader(fh))


def close(x, y, tol=0.02):
    return x is not None and y is not None and abs(x - y) <= tol


def main():
    anchors_doc = json.load(open(ANCHORS_JSON, encoding='utf-8'))
    data_cache = {src: json.load(open(os.path.join(DATA_DIR, src), encoding='utf-8'))
                  for src in CSV_FOR_SOURCE}
    csv_cache = {src: load_csv_rows(name) for src, name in CSV_FOR_SOURCE.items()}

    out_anchors = []
    color_mismatches = []
    layer_count_mismatches = []
    surface_flags = []

    for a in anchors_doc['anchors']:
        src, idx = a['source'], a['source_idx']
        rec = data_cache[src][idx]          # makeup: from App_Data/*.json
        row = csv_cache[src][idx]           # surfaces: from CSV

        # --- validate the join three ways on exterior color (references only; not emitted) ---
        ext = a['exterior']
        if not (close(rec.get('extL'), ext['L']) and close(rec.get('extA'), ext['a'])
                and close(rec.get('extB'), ext['b'])):
            color_mismatches.append((a['code'], 'anchor<>data', ext,
                                     (rec.get('extL'), rec.get('extA'), rec.get('extB'))))
        csv_ext = (num(row.get('Exterior Reflected Color L*')),
                   num(row.get('Exterior Reflected Color a*')),
                   num(row.get('Exterior Reflected Color b*')))
        if not (close(csv_ext[0], ext['L']) and close(csv_ext[1], ext['a'])
                and close(csv_ext[2], ext['b'])):
            color_mismatches.append((a['code'], 'anchor<>csv', ext, csv_ext))

        # --- CSV present lites in optical order, with surface suffixes ---
        present = [c for c in LITE_COLUMNS
                   if (row.get('%s Lite (Name_Thickness mm)' % c) or '').strip()]
        glass_layers = [l for l in rec['stack'] if l['type'] == 'glass']
        if len(present) != len(glass_layers):
            layer_count_mismatches.append((a['code'], len(present), len(glass_layers)))

        layers = []
        pane = 0
        gi = 0
        for layer in rec['stack']:
            if layer['type'] == 'glass':
                pane += 1
                s_out, s_in = pane * 2 - 1, pane * 2
                col = present[gi] if gi < len(present) else None
                lite_name = (row.get('%s Lite (Name_Thickness mm)' % col, '') or '').strip() if col else ''
                nfrc_id = (row.get('%s Lite NFRC ID' % col, '') or '').strip() if col else ''
                lowE_name, lowE_surface = parse_lowE(
                    row.get('%s Lite Low-E' % col, '') if col else '')
                shortcode = layer.get('coating')

                coating = None
                if shortcode:
                    if lowE_surface is None:
                        surface_flags.append((a['code'], pane, shortcode,
                                              'data has coating but CSV Low-E has no surface'))
                    elif lowE_surface not in (s_out, s_in):
                        surface_flags.append((a['code'], pane, shortcode,
                                              'CSV surface S%s is not a face of pane %d (S%d/S%d)'
                                              % (lowE_surface, pane, s_out, s_in)))
                    coating = {
                        'shortcode': shortcode,
                        'lowE_name': lowE_name,
                        'surface': lowE_surface,
                        'pane_face': ('outboard' if lowE_surface == s_out else
                                      'inboard' if lowE_surface == s_in else 'CHECK'),
                    }
                elif lowE_name:
                    surface_flags.append((a['code'], pane, lowE_name,
                                          'CSV has Low-E but data stack shows uncoated pane'))

                layers.append({
                    'kind': 'glass',
                    'pane': pane,
                    'role': (col.lower() if col else 'lite%d' % pane),
                    'surfaces': [s_out, s_in],
                    'substrate': layer.get('substrate'),
                    'thickness_mm': layer.get('thickness'),
                    'lite_name_csv': lite_name,
                    'lite_nfrc_id': nfrc_id or None,   # coated-product NFRC/IGDB id (NFRC->IGSDB)
                    'coating': coating,
                })
                gi += 1
            elif layer['type'] == 'gas':
                layers.append({'kind': 'gap', 'fill': layer.get('gasType'),
                               'thickness_mm': layer.get('thickness')})
            elif layer['type'] == 'vacuum':
                layers.append({'kind': 'vacuum_gap', 'thickness_mm': layer.get('thickness'),
                               'note': 'optical gap ~0; pillar geometry only affects U-value'})

        surface_map = '; '.join(
            'S%d/%d=%s%s' % (l['surfaces'][0], l['surfaces'][1], l['substrate'],
                             (' +%s@S%s' % (l['coating']['shortcode'], l['coating']['surface'])
                              if l['coating'] else ''))
            for l in layers if l['kind'] == 'glass')

        out_anchors.append({
            'code': a['code'],
            'cluster_id': a['cluster_id'],
            'product': PRODUCT_LABEL[src],
            'source': src,
            'source_idx': idx,
            'n_panes': pane,
            'gas_fill': rec.get('gasFill') or (
                next((l['fill'] for l in layers if l['kind'] == 'gap'), None)),
            'total_thickness_mm': rec.get('totalThickness'),
            'surface_map': surface_map,
            'layers': layers,
        })

    out = {
        'title': 'AnchorRender_Configs',
        'description': ('Build configuration (PyWinCalc input) for the 77 JND color-cluster '
                        'render anchors. Optical stack only -- NO performance/color outputs; '
                        'PyWinCalc computes those. Makeup from App_Data/*.json; coating surface '
                        'numbers joined from the Source CSVs.'),
        'optics_key': ('Per layer, lite_nfrc_id is the coated-product NFRC/IGDB id (unique per '
                       'glass+coating). Resolve via NFRC->IGSDB to get the coated optics; orient '
                       'using coating.surface / pane_face.'),
        'tolerance_dE76': anchors_doc.get('tolerance_dE76'),
        'total_configs_covered': anchors_doc.get('total_configs'),
        'anchor_count': len(out_anchors),
        'layer_order': 'exterior -> interior; surfaces S1..S2N numbered from the exterior face',
        'makeup_source': 'App_Data/*.json (live app data)',
        'surface_source': 'Data_Pipeline/1_Source_CSVs/*.csv (Low-E column suffix)',
        'anchors': out_anchors,
    }

    out_path = os.path.join(SCRIPT_DIR, 'AnchorRender_Configs.json')
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print('Anchors written        : %d' % len(out_anchors))
    print('Color join mismatches  : %d %s' % (len(color_mismatches),
                                               '' if not color_mismatches else '<-- CHECK'))
    for m in color_mismatches[:8]:
        print('   ', m)
    print('Layer-count mismatches : %d %s' % (len(layer_count_mismatches),
                                               '' if not layer_count_mismatches else '<-- CHECK'))
    for m in layer_count_mismatches[:8]:
        print('   ', m)
    print('Surface flags          : %d %s' % (len(surface_flags),
                                               '' if not surface_flags else '<-- CHECK'))
    for m in surface_flags[:12]:
        print('   ', m)
    print('\nWrote: %s' % os.path.relpath(out_path, SCRIPT_DIR))


if __name__ == '__main__':
    main()
