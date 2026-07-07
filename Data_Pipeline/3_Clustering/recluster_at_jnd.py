"""
Cluster the ~6,444 product configurations into a small set of render anchors.

Appearance is captured on TWO CIELAB axes: the exterior-reflected color
(extL, extA, extB) and the transmitted color (trnL, trnA, trnB). Many configs
that differ in thermal build (cavity gas, gap, vacuum, inner pane) land at the
same — or imperceptibly close — appearance. This script collapses all configs
onto a minimal set of "anchors": one representative real configuration per
cluster, such that EVERY config is within TOL_EXT of its anchor's reflected
color AND within TOL_TRN of its anchor's transmitted color.

Why this design (see CLUSTERING_PROCEDURE.md for the full rationale, the
ΔE76 -> CIEDE2000 history, the substrate-partition decision, and the earlier
single-axis exterior-only version):

  * Two-axis metric (pdist). Exterior reflection dominates the daytime facade
    render, so it is held tight (TOL_EXT=1.5). Transmission is only faintly
    visible through the dark interior, but the two axes are largely independent —
    configs matched on reflection can diverge up to ΔE~11 in transmission — so a
    looser transmission guard (TOL_TRN=3.0) is added to kill gross see-through
    mismatches without doubling the anchor count. Distance is the per-axis
    CIEDE2000 normalized by each tolerance, combined by max (an AND constraint).

  * ΔE = CIEDE2000 on each axis, the perceptually-uniform color difference.
    (Earlier versions used ΔE76, which is hue-blind. See git history.)

  * Clustering is PARTITIONED by exterior-facing substrate (the hue family).
    Configs only ever share an anchor with the same substrate, so a blue / green
    / bronze tint can never be represented by a clear or gray render.

  * Greedy farthest-first k-center COVER, not k-means. k-means minimizes average
    variance and can leave outliers beyond tolerance. A cover guarantees the hard
    "every config within tolerance on both axes" property the JND argument needs.

  * Each anchor is a REAL config (its full stack), so it can be rendered in
    Blender as-is.

Inputs:
  App_Data/enthermal.json, enthermal-plus-inboard.json, enthermal-plus-outboard.json

Outputs:
  App_Data/*.json         the three config files, REWRITTEN with a `cid` (integer
                          anchor id) injected onto every config for direct
                          runtime lookup (config.cid -> anchor_<cid>.webp)
  3_Clustering/anchors.csv / anchors.json   per-anchor render specs (Blender list)
  3_Clustering/cluster_assignments.csv      every config -> cid, dE
  3_Clustering/cluster_map.json             { "L_a_b": code } (debug only; the app
                          uses config.cid now, not this map)
  3_Clustering/clustering_report.txt        stats

BUILD ORDER: run AFTER csv_to_json.py. This script is the FINAL writer of the
App_Data JSON (it injects `cid`); re-running csv_to_json.py alone drops `cid`.

Usage:
  python recluster_at_jnd.py
"""

import csv
import json
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))      # Data_Pipeline/3_Clustering
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))     # up two: 3_Clustering -> Data_Pipeline -> repo
DATA_DIR = os.path.join(REPO_ROOT, 'App_Data')
# Outputs (anchors.*, cluster_*, clustering_report.txt) are written next to this
# script, i.e. into 3_Clustering/.

SOURCES = [
    'enthermal.json',
    'enthermal-plus-inboard.json',
    'enthermal-plus-outboard.json',
]

# Two-axis Just-Noticeable-Difference thresholds. Every config is guaranteed
# within TOL_EXT (CIEDE2000) of its anchor's EXTERIOR reflected color AND within
# TOL_TRN of its anchor's TRANSMITTED color. Reflection is held tight because it
# dominates the daytime facade render; transmission gets a looser guard (barely
# visible through the dark interior) purely to kill gross mismatches without
# doubling the render count. ext<=1.5 + trn<=3.0 pins ~194 anchors against the
# current dataset. See CLUSTERING_PROCEDURE.md for the single-axis history.
TOL_EXT = 1.5
TOL_TRN = 3.0

# Lab values in the JSON carry 2 decimals; the runtime map and the front-end
# lookup MUST format keys identically (extL.toFixed(2), etc.).
LAB_DP = 2

# Anchor ids (cid) are 1-based so they line up 1:1 with Blender frame numbers
# (frame N renders cid N, no off-by-one). Internal cluster array indices stay
# 0-based; this offset is applied only where a cid is emitted. code_for()
# zero-pads to >=2 digits, so cid 1 -> anchor_01.
CID_BASE = 1


def _fmt(x):
    """Format one Lab component to LAB_DP decimals. Canonicalize signed zero:
    Python '%.2f' % -0.0 -> '-0.00', but JS (-0).toFixed(2) -> '0.00'. The
    front-end fmtLab() applies the identical '-0.00' -> '0.00' guard so keys
    match byte-for-byte."""
    s = '%.*f' % (LAB_DP, x)
    return '0.00' if s == '-0.00' else s


def lab_key(L, a, b):
    """Stable string key for a color point. Front-end must mirror this exactly:
    `${fmtLab(L)}_${fmtLab(a)}_${fmtLab(b)}` (see fmtLab in the HTML)."""
    return '%s_%s_%s' % (_fmt(L), _fmt(a), _fmt(b))


_POW25_7 = 25.0 ** 7


def dE(p, q):
    """CIEDE2000 color difference between two (L, a, b) tuples.

    Perceptually uniform: down-weights lightness and handles hue/chroma
    correctly, unlike the old ΔE76 Euclidean distance. This is the distance the
    whole cover/recenter/repair pipeline runs on."""
    L1, a1, b1 = p
    L2, a2, b2 = q
    C1 = math.hypot(a1, b1)
    C2 = math.hypot(a2, b2)
    Cbar = (C1 + C2) / 2.0
    Cbar7 = Cbar ** 7
    G = 0.5 * (1 - math.sqrt(Cbar7 / (Cbar7 + _POW25_7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360.0
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180:
            dhp -= 360
        elif dhp < -180:
            dhp += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2.0
    Cbp = (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hbp = h1p + h2p
    else:
        hbp = h1p + h2p
        if abs(h1p - h2p) > 180:
            hbp = hbp + 360 if hbp < 360 else hbp - 360
        hbp /= 2.0
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dtheta = 30 * math.exp(-(((hbp - 275) / 25.0) ** 2))
    Cbp7 = Cbp ** 7
    Rc = 2 * math.sqrt(Cbp7 / (Cbp7 + _POW25_7))
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


def pdist(p, q):
    """Combined two-axis distance between two color points, each carrying an
    exterior-reflected 'ext' Lab triple and a transmitted 'trn' Lab triple.
    Each axis uses CIEDE2000, normalized by its own tolerance; the max encodes
    an AND constraint -- a point is covered only when it is within BOTH
    tolerances (pdist <= 1.0). Anisotropic: the covered region is an axis-aligned
    box, narrow in reflection (TOL_EXT) and wide in transmission (TOL_TRN)."""
    return max(dE(p['ext'], q['ext']) / TOL_EXT,
               dE(p['trn'], q['trn']) / TOL_TRN)


def exterior_substrate(stack):
    """The substrate of the exterior-facing glass (first glass layer, stack is
    ordered exterior -> interior). This is the hue family the render must match."""
    for layer in stack or ():
        if layer.get('type') == 'glass':
            return layer.get('substrate') or 'Clear'
    return 'Clear'


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
            eL, eA, eB = row.get('extL'), row.get('extA'), row.get('extB')
            tL, tA, tB = row.get('trnL'), row.get('trnA'), row.get('trnB')
            if None in (eL, eA, eB, tL, tA, tB):
                continue
            records.append({
                'source': source,
                'idx': idx,
                'ext': (eL, eA, eB),
                'trn': (tL, tA, tB),
                'key': lab_key(eL, eA, eB) + '|' + lab_key(tL, tA, tB),
                'stack': row.get('stack'),
                'substrate': exterior_substrate(row.get('stack')),
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
                'ext': rec['ext'],
                'trn': rec['trn'],
                'weight': 1,
                'rep': rec,
                'substrate': rec['substrate'],
            }
        else:
            # The substrate partition relies on each (ext, trn) color pair
            # belonging to a single exterior substrate.
            if slot['substrate'] != rec['substrate']:
                raise ValueError(
                    'Color key %s shared by substrates %s and %s.'
                    % (rec['key'], slot['substrate'], rec['substrate']))
            slot['weight'] += 1
    # Deterministic order: sort by (ext, trn) so the farthest-first seed and all
    # tie-breaks are reproducible run to run (no RNG).
    points = list(by_key.values())
    points.sort(key=lambda p: (p['ext'], p['trn']))
    return points


def farthest_first_cover(points, tol=1.0):
    """Greedy k-center cover under the combined two-axis pdist. Seed
    deterministically with the pre-sorted first point, then repeatedly add the
    point farthest (largest pdist) from the current anchor set until no point is
    more than `tol` away. Because pdist is normalized by per-axis tolerance,
    tol=1.0 means every point is within BOTH TOL_EXT and TOL_TRN of an anchor;
    anchors are real points."""
    anchor_idxs = [0]  # points is pre-sorted, so index 0 is deterministic
    nearest = [pdist(p, points[0]) for p in points]
    while True:
        far_i = max(range(len(points)), key=lambda i: nearest[i])
        if nearest[far_i] <= tol:
            break
        anchor_idxs.append(far_i)
        a = points[far_i]
        for i, p in enumerate(points):
            d = pdist(p, a)
            if d < nearest[i]:
                nearest[i] = d
    return anchor_idxs


def assign(points, anchor_idxs):
    """Assign each point to its nearest anchor. Returns (labels, members) where
    labels[i] is the cluster index and members[c] is the list of point indices."""
    anchor_pts = [points[a] for a in anchor_idxs]
    labels = [0] * len(points)
    members = [[] for _ in anchor_idxs]
    for i, p in enumerate(points):
        best_c, best_d = 0, float('inf')
        for c, ap in enumerate(anchor_pts):
            d = pdist(p, ap)
            if d < best_d:
                best_c, best_d = c, d
        labels[i] = best_c
        members[best_c].append(i)
    return labels, members


def chebyshev_center(points, member_idxs):
    """Pick the member that minimizes the max pdist to all other members (the
    discrete 1-center under the combined metric). This is the best real-config
    anchor for the cluster: central in BOTH color spaces at once, minimizing
    worst-case in-cluster distance. Never adds anchors, so the cover guarantee
    is preserved."""
    best_i, best_radius = member_idxs[0], float('inf')
    mem = [points[m] for m in member_idxs]
    for cand in member_idxs:
        cp = points[cand]
        radius = max(pdist(cp, mp) for mp in mem)
        if radius < best_radius:
            best_i, best_radius = cand, radius
    return best_i


def repair(points, anchor_idxs, tol=1.0):
    """After recentering, guarantee the cover still holds under pdist: while any
    point is farther than `tol` from its nearest anchor, promote it to an anchor.
    Monotonic — only adds — so it always terminates with max pdist <= tol (both
    axes within their tolerance)."""
    while True:
        anchor_pts = [points[a] for a in anchor_idxs]
        worst_i, worst_d = -1, tol
        for i, p in enumerate(points):
            d = min(pdist(p, ap) for ap in anchor_pts)
            if d > worst_d:
                worst_i, worst_d = i, d
        if worst_i < 0:
            return anchor_idxs
        anchor_idxs = anchor_idxs + [worst_i]


def cluster(points, tol=1.0):
    """Full pipeline: cover -> recenter each cluster to its 1-center -> repair.
    Returns (anchor_idxs, labels, members) with the pdist <= tol guarantee (every
    config within TOL_EXT reflection AND TOL_TRN transmission of its anchor)."""
    anchor_idxs = farthest_first_cover(points, tol)
    # Recenter: replace each anchor with its cluster's discrete 1-center.
    _, members = assign(points, anchor_idxs)
    anchor_idxs = [chebyshev_center(points, m) for m in members if m]
    # Recentering can shift membership at cluster edges; restore the guarantee.
    anchor_idxs = repair(points, anchor_idxs, tol)
    labels, members = assign(points, anchor_idxs)
    return anchor_idxs, labels, members


def cluster_by_substrate(points, tol=1.0):
    """Partition points by exterior substrate, cluster each family independently,
    then assign deterministic global cluster ids (cids). Ordering: by substrate
    (alphabetical), then by anchor exterior Lab. This fixes the Blender frame
    sequence (frame N = cid N-1) reproducibly.

    Returns (anchor_idxs, labels, members) in GLOBAL point-index space, exactly
    the shape write_outputs() expects."""
    groups = {}
    for i, p in enumerate(points):
        groups.setdefault(p['substrate'], []).append(i)

    clusters = []  # each: {anchor: global_idx, members: [global_idx...], sub}
    for sub in sorted(groups):
        gidx = groups[sub]
        subpts = [points[i] for i in gidx]
        sub_anchor_idxs, _, sub_members = cluster(subpts, tol)
        for c, mlist in enumerate(sub_members):
            if not mlist:
                continue
            clusters.append({
                'anchor': gidx[sub_anchor_idxs[c]],
                'members': [gidx[j] for j in mlist],
                'sub': sub,
            })

    # Deterministic cid order: substrate, then anchor exterior Lab (L, a, b).
    clusters.sort(key=lambda cl: (cl['sub'], points[cl['anchor']]['ext']))

    anchor_idxs = [cl['anchor'] for cl in clusters]
    members = [cl['members'] for cl in clusters]
    labels = [0] * len(points)
    for cid, cl in enumerate(clusters):
        for pidx in cl['members']:
            labels[pidx] = cid
    return anchor_idxs, labels, members


def code_for(cluster_id):
    return 'anchor_%02d' % cluster_id


def write_outputs(records, points, anchor_idxs, labels, members):
    anchor_set = set(anchor_idxs)
    # Map every point index -> (cluster_id, per-axis dE to its anchor).
    point_cluster = {}
    point_ext_dE = {}
    point_trn_dE = {}
    # point_cluster stores the 0-based array index k; the 1-based cid is k+CID_BASE.
    for k, members_list in enumerate(members):
        ap = points[anchor_idxs[k]]
        for pi in members_list:
            point_cluster[pi] = k
            point_ext_dE[pi] = dE(points[pi]['ext'], ap['ext'])
            point_trn_dE[pi] = dE(points[pi]['trn'], ap['trn'])
    # Point index lookup by key (for joining records back to clusters).
    key_to_point = {p['key']: i for i, p in enumerate(points)}

    # --- cluster_map.json : colorKey -> code (debug only; app uses config.cid) ---
    cluster_map = {}
    for i, p in enumerate(points):
        cluster_map[p['key']] = code_for(point_cluster[i] + CID_BASE)
    with open(os.path.join(SCRIPT_DIR, 'cluster_map.json'), 'w', encoding='utf-8') as fh:
        json.dump(cluster_map, fh, separators=(',', ':'), sort_keys=True)

    # --- anchors.csv : the Blender render list ---
    anchor_rows = []
    for k, a_idx in enumerate(anchor_idxs):
        cid = k + CID_BASE
        ap = points[a_idx]
        member_list = members[k]
        ext_radius = max(point_ext_dE[pi] for pi in member_list)
        ext_mean = sum(point_ext_dE[pi] for pi in member_list) / len(member_list)
        trn_radius = max(point_trn_dE[pi] for pi in member_list)
        trn_mean = sum(point_trn_dE[pi] for pi in member_list) / len(member_list)
        config_count = sum(points[pi]['weight'] for pi in member_list)
        anchor_rows.append({
            'cluster_id': cid,
            'code': code_for(cid),
            'distinct_colors': len(member_list),
            'config_count': config_count,
            'extL': ap['ext'][0],
            'extA': ap['ext'][1],
            'extB': ap['ext'][2],
            'trnL': ap['trn'][0],
            'trnA': ap['trn'][1],
            'trnB': ap['trn'][2],
            'max_dE_in_cluster': round(ext_radius, 4),
            'mean_dE_in_cluster': round(ext_mean, 4),
            'max_trn_dE_in_cluster': round(trn_radius, 4),
            'mean_trn_dE_in_cluster': round(trn_mean, 4),
            'source': ap['rep']['source'],
            'source_idx': ap['rep']['idx'],
            'stack_desc': stack_desc(ap['rep']['stack']),
            'stack_json': json.dumps(ap['rep']['stack'], separators=(',', ':')),
        })
    with open(os.path.join(SCRIPT_DIR, 'anchors.csv'), 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(anchor_rows[0].keys()))
        writer.writeheader()
        writer.writerows(anchor_rows)

    # --- anchors.json : structured anchors, with the parsed renderable stack
    #     inline (Blender render list / programmatic consumers) ---
    anchors_json = {
        'tolerance_ext_dE2000': TOL_EXT,
        'tolerance_trn_dE2000': TOL_TRN,
        'metric': 'CIEDE2000 (two-axis: exterior-reflected + transmitted)',
        'partitioned_by': 'exterior_substrate',
        'anchor_count': len(anchor_idxs),
        'total_configs': sum(r['config_count'] for r in anchor_rows),
        'anchors': [],
    }
    for k, a_idx in enumerate(anchor_idxs):
        cid = k + CID_BASE
        ap = points[a_idx]
        member_list = members[k]
        anchors_json['anchors'].append({
            'code': code_for(cid),
            'cluster_id': cid,
            'substrate': ap['substrate'],
            'exterior': {'L': ap['ext'][0], 'a': ap['ext'][1], 'b': ap['ext'][2]},
            'transmitted': {'L': ap['trn'][0], 'a': ap['trn'][1], 'b': ap['trn'][2]},
            'config_count': sum(points[pi]['weight'] for pi in member_list),
            'distinct_colors': len(member_list),
            'max_dE_in_cluster': round(max(point_ext_dE[pi] for pi in member_list), 4),
            'mean_dE_in_cluster': round(
                sum(point_ext_dE[pi] for pi in member_list) / len(member_list), 4),
            'max_trn_dE_in_cluster': round(max(point_trn_dE[pi] for pi in member_list), 4),
            'mean_trn_dE_in_cluster': round(
                sum(point_trn_dE[pi] for pi in member_list) / len(member_list), 4),
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
        writer.writerow(['source', 'idx', 'extL', 'extA', 'extB', 'trnL', 'trnA', 'trnB',
                         'cluster_id', 'code', 'is_anchor',
                         'ext_dE_to_anchor', 'trn_dE_to_anchor'])
        for rec in records:
            pi = key_to_point[rec['key']]
            k = point_cluster[pi]
            cid = k + CID_BASE
            is_anchor = (pi in anchor_set and anchor_idxs[k] == pi
                         and rec['source'] == points[pi]['rep']['source']
                         and rec['idx'] == points[pi]['rep']['idx'])
            writer.writerow([rec['source'], rec['idx'],
                             rec['ext'][0], rec['ext'][1], rec['ext'][2],
                             rec['trn'][0], rec['trn'][1], rec['trn'][2],
                             cid, code_for(cid), int(is_anchor),
                             round(point_ext_dE[pi], 4), round(point_trn_dE[pi], 4)])

    return anchor_rows


def write_report(records, points, anchor_rows):
    total_configs = len(records)
    distinct_colors = len(points)
    n_anchors = len(anchor_rows)
    ext_max = max(r['max_dE_in_cluster'] for r in anchor_rows)
    trn_max = max(r['max_trn_dE_in_cluster'] for r in anchor_rows)
    ext_wmean = (
        sum(r['mean_dE_in_cluster'] * r['config_count'] for r in anchor_rows)
        / total_configs
    )
    trn_wmean = (
        sum(r['mean_trn_dE_in_cluster'] * r['config_count'] for r in anchor_rows)
        / total_configs
    )
    counts = sorted(r['config_count'] for r in anchor_rows)
    ok = ext_max <= TOL_EXT + 1e-9 and trn_max <= TOL_TRN + 1e-9
    lines = []
    lines.append('JND RECLUSTERING REPORT (two-axis)')
    lines.append('=' * 60)
    lines.append('')
    lines.append('Metric                  : CIEDE2000, exterior-reflected + transmitted')
    lines.append('Partitioned by          : exterior substrate')
    lines.append('Tolerance ext (dE2000)  : %.2f' % TOL_EXT)
    lines.append('Tolerance trn (dE2000)  : %.2f' % TOL_TRN)
    lines.append('Total configurations    : %d' % total_configs)
    lines.append('Distinct color pairs    : %d' % distinct_colors)
    lines.append('Anchors (renders needed): %d' % n_anchors)
    lines.append('Renders x 2 skies       : %d' % (n_anchors * 2))
    lines.append('')
    lines.append('GUARANTEE')
    lines.append('  Max ext config->anchor dE: %.4f  (must be <= %.2f)' % (ext_max, TOL_EXT))
    lines.append('  Max trn config->anchor dE: %.4f  (must be <= %.2f)' % (trn_max, TOL_TRN))
    lines.append('  Config-weighted mean ext : %.4f' % ext_wmean)
    lines.append('  Config-weighted mean trn : %.4f' % trn_wmean)
    lines.append('  Guarantee satisfied      : %s' % ('YES' if ok else 'NO'))
    lines.append('')
    lines.append('CLUSTER SIZE (configs per anchor)')
    lines.append('  min / median / max    : %d / %d / %d'
                 % (counts[0], counts[len(counts) // 2], counts[-1]))
    lines.append('')
    lines.append('PER-ANCHOR DETAIL')
    lines.append('  %-10s %7s %7s %8s %8s %8s %8s  %s'
                 % ('code', 'configs', 'colors', 'maxExt', 'meanExt', 'maxTrn', 'meanTrn', 'stack'))
    for r in sorted(anchor_rows, key=lambda x: -x['config_count']):
        lines.append('  %-10s %7d %7d %8.3f %8.3f %8.3f %8.3f  %s'
                     % (r['code'], r['config_count'], r['distinct_colors'],
                        r['max_dE_in_cluster'], r['mean_dE_in_cluster'],
                        r['max_trn_dE_in_cluster'], r['mean_trn_dE_in_cluster'],
                        r['stack_desc']))
    report = '\n'.join(lines) + '\n'
    with open(os.path.join(SCRIPT_DIR, 'clustering_report.txt'), 'w', encoding='utf-8') as fh:
        fh.write(report)
    return report


def write_cids(records, points, labels):
    """Inject `cid` (1-based integer anchor id) onto every config in the App_Data
    JSON. This is the runtime lookup field: the front-end does config.cid ->
    anchor_<cid>.webp, with no Lab-key formatting. cid = label + CID_BASE so it
    matches the Blender frame number 1:1. Re-writes each file with the SAME
    json.dump params csv_to_json.py uses (ensure_ascii=False, indent=2) so the
    only diff is the added `cid` lines."""
    key_to_point = {p['key']: i for i, p in enumerate(points)}
    rec_cid = {}  # (source, idx) -> cid
    for rec in records:
        rec_cid[(rec['source'], rec['idx'])] = labels[key_to_point[rec['key']]] + CID_BASE

    for source in SOURCES:
        path = os.path.join(DATA_DIR, source)
        with open(path, encoding='utf-8') as fh:
            rows = json.load(fh)
        for idx, row in enumerate(rows):
            cid = rec_cid.get((source, idx))
            if cid is not None:
                row['cid'] = cid
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)


def main():
    records = load_records()
    points = unique_points(records)
    anchor_idxs, labels, members = cluster_by_substrate(points)
    anchor_rows = write_outputs(records, points, anchor_idxs, labels, members)
    write_cids(records, points, labels)
    report = write_report(records, points, anchor_rows)
    print(report)
    print('Wrote: App_Data/*.json (+cid), anchors.csv, anchors.json, '
          'cluster_assignments.csv, cluster_map.json, clustering_report.txt')


if __name__ == '__main__':
    main()
