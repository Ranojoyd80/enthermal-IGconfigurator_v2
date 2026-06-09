"""
Cluster the 6,862 product configurations into a small set of render anchors.

Exterior appearance is captured by the CIELAB exterior-reflected color
(extL, extA, extB). Many configs that differ in thermal build (cavity gas,
gap, vacuum, inner pane) land at the same — or imperceptibly close — exterior
color. This script collapses all configs onto a minimal set of "anchors": one
representative real configuration per color cluster, such that EVERY config is
within ΔE ≤ TOL of its anchor's color.

Why this design (see CLUSTERING_PROCEDURE.md for the full rationale and a
worked example):

  * Cluster on pure CIELAB (extL, extA, extB), NOT routVis. routVis is redundant
    with the Lab triple (3,133 vs 3,136 distinct tuples) and its 0.06-0.23 scale
    contributes ~nothing to an unweighted ΔE.

  * ΔE = ΔE76 = sqrt(dL^2 + da^2 + db^2), matching the Lab convention already in
    docs/color-rendering.md.

  * Greedy farthest-first k-center COVER, not k-means. k-means minimizes average
    variance and can leave outliers beyond tolerance. A cover guarantees the hard
    "every config within ΔE ≤ TOL" property the JND argument depends on.

  * Each anchor is a REAL config (its full stack), so it can be rendered in
    Blender as-is.

Inputs (read-only):
  data/enthermal.json
  data/enthermal-plus-inboard.json
  data/enthermal-plus-outboard.json

Outputs (written next to this script, in ProductData/):
  anchors.csv             one row per anchor: code, color, member_count, stack
  cluster_assignments.csv every config -> cluster_id, code, is_anchor, dE
  cluster_map.json        { "L_a_b": code } for runtime front-end lookup
  clustering_report.txt   anchor count, ΔE stats, member histogram

Usage:
  python recluster_at_jnd.py
"""

import csv
import json
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, 'data')

SOURCES = [
    'enthermal.json',
    'enthermal-plus-inboard.json',
    'enthermal-plus-outboard.json',
]

# Just-Noticeable-Difference threshold. Every config is guaranteed within this
# ΔE76 of its anchor. See the plan: ΔE <= 2 pins ~73 anchors against the
# current dataset.
TOL = 2.0

# Lab values in the JSON carry 2 decimals; the runtime map and the front-end
# lookup MUST format keys identically (extL.toFixed(2), etc.).
LAB_DP = 2


def lab_key(L, a, b):
    """Stable string key for a color point. Front-end must mirror this exactly:
    `${L.toFixed(2)}_${a.toFixed(2)}_${b.toFixed(2)}`."""
    return '%.*f_%.*f_%.*f' % (LAB_DP, L, LAB_DP, a, LAB_DP, b)


def dE(p, q):
    """CIELAB ΔE76 between two (L, a, b) tuples."""
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2)


def stack_desc(stack):
    """Human-readable one-line summary of a glass stack, outer -> inner."""
    parts = []
    for layer in stack:
        t = layer.get('type')
        th = layer.get('thickness')
        if t == 'glass':
            coating = layer.get('coating')
            substrate = layer.get('substrate') or 'Clear'
            head = ('%s %s' % (coating, substrate)) if coating else substrate
            parts.append('%s %smm' % (head, th))
        elif t == 'gas':
            parts.append('%s %smm' % (layer.get('gasType'), th))
        elif t == 'vacuum':
            parts.append('Vacuum %smm' % th)
        else:
            parts.append('%s %smm' % (t, th))
    return ' / '.join(parts)


def load_records():
    """Return a flat list of records, each tagged with its source file and the
    in-file index so assignments trace back to an exact config."""
    records = []
    for source in SOURCES:
        path = os.path.join(DATA_DIR, source)
        with open(path, encoding='utf-8') as fh:
            rows = json.load(fh)
        for idx, row in enumerate(rows):
            L, a, b = row.get('extL'), row.get('extA'), row.get('extB')
            if L is None or a is None or b is None:
                continue
            records.append({
                'source': source,
                'idx': idx,
                'lab': (L, a, b),
                'key': lab_key(L, a, b),
                'stack': row.get('stack'),
            })
    return records


def unique_points(records):
    """Collapse records onto distinct color points. Returns a list of
    {key, lab, weight, rep} where rep is a representative record (deterministic:
    the earliest source/idx) used as the renderable stack if this point becomes
    an anchor."""
    by_key = {}
    for rec in records:
        slot = by_key.get(rec['key'])
        if slot is None:
            by_key[rec['key']] = {
                'key': rec['key'],
                'lab': rec['lab'],
                'weight': 1,
                'rep': rec,
            }
        else:
            slot['weight'] += 1
    # Deterministic order: sort by Lab so the farthest-first seed and all
    # tie-breaks are reproducible run to run (no RNG).
    points = list(by_key.values())
    points.sort(key=lambda p: p['lab'])
    return points


def farthest_first_cover(points, tol):
    """Greedy k-center cover. Seed deterministically with the lexicographically
    smallest Lab point, then repeatedly add the point farthest from the current
    anchor set until no point is more than `tol` away. Guarantees every point is
    within `tol` of an anchor; anchors are real points."""
    anchor_idxs = [0]  # points is pre-sorted, so index 0 is deterministic
    nearest = [dE(p['lab'], points[0]['lab']) for p in points]
    while True:
        far_i = max(range(len(points)), key=lambda i: nearest[i])
        if nearest[far_i] <= tol:
            break
        anchor_idxs.append(far_i)
        alab = points[far_i]['lab']
        for i, p in enumerate(points):
            d = dE(p['lab'], alab)
            if d < nearest[i]:
                nearest[i] = d
    return anchor_idxs


def assign(points, anchor_idxs):
    """Assign each point to its nearest anchor. Returns (labels, members) where
    labels[i] is the cluster index and members[c] is the list of point indices."""
    anchor_labs = [points[a]['lab'] for a in anchor_idxs]
    labels = [0] * len(points)
    members = [[] for _ in anchor_idxs]
    for i, p in enumerate(points):
        best_c, best_d = 0, float('inf')
        for c, alab in enumerate(anchor_labs):
            d = dE(p['lab'], alab)
            if d < best_d:
                best_c, best_d = c, d
        labels[i] = best_c
        members[best_c].append(i)
    return labels, members


def chebyshev_center(points, member_idxs):
    """Pick the member that minimizes the max ΔE to all other members (the
    discrete 1-center). This is the best real-config anchor for the cluster: it
    sits at the color center and minimizes worst-case in-cluster ΔE. Never adds
    anchors, so the cover guarantee is preserved."""
    best_i, best_radius = member_idxs[0], float('inf')
    labs = [points[m]['lab'] for m in member_idxs]
    for cand in member_idxs:
        clab = points[cand]['lab']
        radius = max(dE(clab, lab) for lab in labs)
        if radius < best_radius:
            best_i, best_radius = cand, radius
    return best_i


def repair(points, anchor_idxs, tol):
    """After recentering, guarantee the cover still holds: while any point is
    farther than `tol` from its nearest anchor, promote that point to an anchor.
    Monotonic — only adds — so it always terminates with max radius <= tol."""
    while True:
        _, members = assign(points, anchor_idxs)
        anchor_labs = [points[a]['lab'] for a in anchor_idxs]
        worst_i, worst_d = -1, tol
        for i, p in enumerate(points):
            d = min(dE(p['lab'], alab) for alab in anchor_labs)
            if d > worst_d:
                worst_i, worst_d = i, d
        if worst_i < 0:
            return anchor_idxs
        anchor_idxs = anchor_idxs + [worst_i]


def cluster(points, tol):
    """Full pipeline: cover -> recenter each cluster to its 1-center -> repair.
    Returns (anchor_idxs, labels, members) with the ΔE <= tol guarantee."""
    anchor_idxs = farthest_first_cover(points, tol)
    # Recenter: replace each anchor with its cluster's discrete 1-center.
    _, members = assign(points, anchor_idxs)
    anchor_idxs = [chebyshev_center(points, m) for m in members if m]
    # Recentering can shift membership at cluster edges; restore the guarantee.
    anchor_idxs = repair(points, anchor_idxs, tol)
    labels, members = assign(points, anchor_idxs)
    return anchor_idxs, labels, members


def code_for(cluster_id):
    return 'anchor_%02d' % cluster_id


def write_outputs(records, points, anchor_idxs, labels, members):
    anchor_set = set(anchor_idxs)
    # Map every point index -> (cluster_id, dE to its anchor).
    point_cluster = {}
    point_dE = {}
    for cid, members_list in enumerate(members):
        alab = points[anchor_idxs[cid]]['lab']
        for pi in members_list:
            point_cluster[pi] = cid
            point_dE[pi] = dE(points[pi]['lab'], alab)
    # Point index lookup by key (for joining records back to clusters).
    key_to_point = {p['key']: i for i, p in enumerate(points)}

    # --- cluster_map.json : labKey -> code (runtime front-end lookup) ---
    cluster_map = {}
    for i, p in enumerate(points):
        cluster_map[p['key']] = code_for(point_cluster[i])
    with open(os.path.join(SCRIPT_DIR, 'cluster_map.json'), 'w', encoding='utf-8') as fh:
        json.dump(cluster_map, fh, separators=(',', ':'), sort_keys=True)

    # --- anchors.csv : the Blender render list ---
    anchor_rows = []
    for cid, a_idx in enumerate(anchor_idxs):
        ap = points[a_idx]
        member_list = members[cid]
        radius = max(point_dE[pi] for pi in member_list)
        mean_d = sum(point_dE[pi] for pi in member_list) / len(member_list)
        config_count = sum(points[pi]['weight'] for pi in member_list)
        anchor_rows.append({
            'cluster_id': cid,
            'code': code_for(cid),
            'distinct_colors': len(member_list),
            'config_count': config_count,
            'extL': ap['lab'][0],
            'extA': ap['lab'][1],
            'extB': ap['lab'][2],
            'max_dE_in_cluster': round(radius, 4),
            'mean_dE_in_cluster': round(mean_d, 4),
            'source': ap['rep']['source'],
            'source_idx': ap['rep']['idx'],
            'stack_desc': stack_desc(ap['rep']['stack']),
            'stack_json': json.dumps(ap['rep']['stack'], separators=(',', ':')),
        })
    with open(os.path.join(SCRIPT_DIR, 'anchors.csv'), 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(anchor_rows[0].keys()))
        writer.writeheader()
        writer.writerows(anchor_rows)

    # --- anchors.json : same 77 anchors, structured, with the parsed renderable
    #     stack inline (Blender render list / programmatic consumers) ---
    anchors_json = {
        'tolerance_dE76': TOL,
        'anchor_count': len(anchor_idxs),
        'total_configs': sum(r['config_count'] for r in anchor_rows),
        'anchors': [],
    }
    for cid, a_idx in enumerate(anchor_idxs):
        ap = points[a_idx]
        member_list = members[cid]
        anchors_json['anchors'].append({
            'code': code_for(cid),
            'cluster_id': cid,
            'exterior': {'L': ap['lab'][0], 'a': ap['lab'][1], 'b': ap['lab'][2]},
            'config_count': sum(points[pi]['weight'] for pi in member_list),
            'distinct_colors': len(member_list),
            'max_dE_in_cluster': round(max(point_dE[pi] for pi in member_list), 4),
            'mean_dE_in_cluster': round(
                sum(point_dE[pi] for pi in member_list) / len(member_list), 4),
            'source': ap['rep']['source'],
            'source_idx': ap['rep']['idx'],
            'totalThickness': ap['rep']['stack'] and sum(
                layer.get('thickness', 0) for layer in ap['rep']['stack']),
            'stack_desc': stack_desc(ap['rep']['stack']),
            'stack': ap['rep']['stack'],
        })
    with open(os.path.join(SCRIPT_DIR, 'anchors.json'), 'w', encoding='utf-8') as fh:
        json.dump(anchors_json, fh, indent=2)

    # --- cluster_assignments.csv : every config ---
    with open(os.path.join(SCRIPT_DIR, 'cluster_assignments.csv'), 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['source', 'idx', 'extL', 'extA', 'extB',
                         'cluster_id', 'code', 'is_anchor', 'distance_to_anchor_dE'])
        for rec in records:
            pi = key_to_point[rec['key']]
            cid = point_cluster[pi]
            is_anchor = (pi in anchor_set and anchor_idxs[cid] == pi
                         and rec['source'] == points[pi]['rep']['source']
                         and rec['idx'] == points[pi]['rep']['idx'])
            writer.writerow([rec['source'], rec['idx'],
                             rec['lab'][0], rec['lab'][1], rec['lab'][2],
                             cid, code_for(cid), int(is_anchor),
                             round(point_dE[pi], 4)])

    return anchor_rows


def write_report(records, points, anchor_rows):
    total_configs = len(records)
    distinct_colors = len(points)
    n_anchors = len(anchor_rows)
    all_max = max(r['max_dE_in_cluster'] for r in anchor_rows)
    weighted_mean = (
        sum(r['mean_dE_in_cluster'] * r['config_count'] for r in anchor_rows)
        / total_configs
    )
    counts = sorted(r['config_count'] for r in anchor_rows)
    lines = []
    lines.append('JND RECLUSTERING REPORT')
    lines.append('=' * 60)
    lines.append('')
    lines.append('Tolerance (dE76)        : %.2f' % TOL)
    lines.append('Total configurations    : %d' % total_configs)
    lines.append('Distinct exterior colors: %d' % distinct_colors)
    lines.append('Anchors (renders needed): %d' % n_anchors)
    lines.append('Renders x 3 HDR variants: %d' % (n_anchors * 3))
    lines.append('')
    lines.append('GUARANTEE')
    lines.append('  Max config->anchor dE : %.4f  (must be <= %.2f)' % (all_max, TOL))
    lines.append('  Config-weighted mean dE: %.4f' % weighted_mean)
    lines.append('  Guarantee satisfied   : %s' % ('YES' if all_max <= TOL + 1e-9 else 'NO'))
    lines.append('')
    lines.append('CLUSTER SIZE (configs per anchor)')
    lines.append('  min / median / max    : %d / %d / %d'
                 % (counts[0], counts[len(counts) // 2], counts[-1]))
    lines.append('')
    lines.append('PER-ANCHOR DETAIL')
    lines.append('  %-10s %7s %7s %8s %8s  %s'
                 % ('code', 'configs', 'colors', 'maxdE', 'meandE', 'stack'))
    for r in sorted(anchor_rows, key=lambda x: -x['config_count']):
        lines.append('  %-10s %7d %7d %8.3f %8.3f  %s'
                     % (r['code'], r['config_count'], r['distinct_colors'],
                        r['max_dE_in_cluster'], r['mean_dE_in_cluster'],
                        r['stack_desc']))
    report = '\n'.join(lines) + '\n'
    with open(os.path.join(SCRIPT_DIR, 'clustering_report.txt'), 'w', encoding='utf-8') as fh:
        fh.write(report)
    return report


def main():
    records = load_records()
    points = unique_points(records)
    anchor_idxs, labels, members = cluster(points, TOL)
    anchor_rows = write_outputs(records, points, anchor_idxs, labels, members)
    report = write_report(records, points, anchor_rows)
    print(report)
    print('Wrote: anchors.csv, cluster_assignments.csv, cluster_map.json, clustering_report.txt')


if __name__ == '__main__':
    main()
