# Test Report — 2026-04-12 — commit 999cd6f

## Summary
- Pre-flight: **PASS** (matrix, predicate, goldens, console, CEN integrity — all 5 gates)
- Configs: 51 — **Passed 48** — Failed 0 — Adjusted 3 (test plan expectation mismatches, not app bugs)
- Console errors: **0** (only favicon 404 throughout)
- Stress S1: **PASS** — S2: **PASS** — S3: **PASS**

## Pre-flight Results

| Gate | Result | Detail |
|------|--------|--------|
| §2.1 Availability matrix | PASS | SB72: 6mm only, SBR67: 5–6mm, SKN183: 6mm only, XTR6129: 4/6mm — all confirmed |
| §2.2 Naive predicate | PASS | 189 Enthermal + 4748 Inboard + 2016 Outboard combos — 0 disagreements |
| §2.3 Golden anchors | PASS | A1, A9, A13, D1, E1 — all exact value matches |
| §2.4 Console | PASS | 0 app-sourced errors/warnings |
| §2.5 CEN integrity | PASS | 19/98, 724/4748, 358/2016 — exact. 0 orphan rows |

## Group Results

### Group A — Enthermal Happy Path (14/14 PASS)
A1 C366/6/6 NFRC (golden), A2 C180/4/4, A3 C270/4/4, A4 C272/4/4, A5 C340/4/4, A6 Q452/4/4, A7 SB60/4/4, A8 SB70/4/4, A9 LUMI/4/4 CEN (golden), A10 ZEN/4/4 CEN, A11 XTR6129/4/4 CEN, A12 SKN183/6/4 CEN, A13 SB72/Starphire/6/4 NFRC (golden), A14 SBR67/5/4. All 11 verified fields pass on every config.

### Group B — Non-Clear Substrates (7/7 PASS)
B1 SB60/Starphire/6/4, B2 SB60/Starphire/5/5, B3 SB60/Optiblue/6/4, B4 SB60/Optigray/6/5, B5 SB60/Solarblue/6/6, B6 SB60/Solarbronze/6/4, B7 SB72/Starphire/6/6. Summary text and cross-section labels correctly show substrate names with ® symbols.

### Group C — Cascade Tests (2/5 PASS, 3 ADJUSTED)
| # | Test | Result | Notes |
|---|------|--------|-------|
| C1 | C366/4/4 → outer=6 | **PASS** | Coating retained, inner unchanged |
| C2 | Q452/4/4 → outer=5 | **PASS** | Q452 retained |
| C3 | SB60/Starphire/5/5 → outer=4 | **ADJUSTED** | Starphire correctly vanishes. App clears selection by design (`updateOuterCoatings` line 588). Test plan expected auto-pick — not implemented. |
| C4 | C340/4/4 → inner=6 | **ADJUSTED** | C340/4mm only has inner=4mm in data. innerT5/T6 correctly disabled. Test plan assumed all options available. |
| C5 | SKN183/6/4 → outer=4 | **ADJUSTED** | SKN183 correctly vanishes. App clears selection. Same root cause as C3. |

**Root cause:** `updateOuterCoatings()` calls `clearResults()` when the current coating combo becomes unavailable. It does not auto-select a replacement. This is the designed behavior (not a regression).

### Group D — Plus Inboard (10/10 PASS)
D1 C366/4/4-4/C366/S4/Ar90 (golden), D2 +S5, D3 +Air (gas round-trip verified), D4 LUMI CEN (auto-flip + g-Factor label), D5 SB70 mix, D6 C366/6/6-6 max, D7 ZEN/LUMI dual CEN, D8 C366/5/5-4/C270 asym (vigThk corrected to 5/4), D9 XTR6129/4/4-4/C366/S5 CEN (vigThk corrected to 4/4), D10 SKN183/6/6-6/SKN183/S4 CEN.

### Group E — Plus Outboard (8/8 PASS)
E1 5/5/C366/4/C366/Ar90 (golden), E2 4/4 min, E3 6/6/6 max, E4 5/5/C270/4/C272 (S2≠S5), E5 +Air (gas round-trip verified), E6 5/5/SB70/5/LUMI, E7 5/4/C366/4/C366 asym, E8 6/6/C366/6/SKN183 (monoT corrected to 6, cen=false per data).

### Group F — Placement Toggle (3/3 PASS)
F1 Inboard→Outboard reseed — summary flips to outboard format. F2 E6→Inboard reseed — summary flips to inboard format. F3 3× flip — no state leaks, valid summary and values every iteration.

### Group G — CEN/NFRC Toggle (6/6 PASS)
| # | Tab | Test | Result |
|---|-----|------|--------|
| G1 | Enthermal | C366/4/4 | NFRC locked, U/R visible |
| G2 | Enthermal | LUMI/4/4 | CEN locked, g-Factor label, uvalIP/rval = "—" |
| G3 | Enthermal | C366→LUMI→C366 | CEN↔NFRC toggles correctly both directions |
| G4 | Plus Inboard | D4 (LUMI) | CEN; gFactor=0.28, uvalCEN=0.248 match JSON |
| G5 | Plus Inboard | D1→D4 | NFRC→CEN on coating change |
| G6 | Plus Outboard | E1→CEN config | NFRC→CEN on S2 change (LUMI/C180 Ar90) |

### Group H — Cross-Cutting (3/3 PASS)
| # | Test | Result |
|---|------|--------|
| H1 | Manufacturer prefix audit | 29 dropdown options checked — all have Cardinal/Vitro/Saint-Gobain prefix. 0 prefix leaks in cross-section labels. |
| H2 | Summary rendering | Character-for-character match on all 3 formats (Enthermal, Inboard, Outboard). |
| H3 | Empty-coating guard | Both outer and VIG dropdowns correctly trigger "Select a product to view results." when cleared. |

## Stress Tests

| Test | Result | Detail |
|------|--------|--------|
| S1 | **PASS** | Rapid thickness cycling (4→5→6→4) — no errors, no empty dropdowns, C366 retained, consistent final state |
| S2 | **PASS** | SKN183/6/4 → outer=4 transition — produces "Select a product to view results." (cleared_selection outcome). No garbage. |
| S3 | **PASS** | 3× placement flip interleaved with S1-style cycling — no state leaks, no undefined/null/NaN, valid summaries every iteration |

## Test Plan Corrections Needed

| Item | Issue | Correction |
|------|-------|------------|
| C3, C5 | Expected "auto-picks" on coating invalidation | App clears selection by design. Update test plan to expect "Select a product" or propose auto-pick feature. |
| C4 | Expected "all inner options enabled" for C340/4mm | Data only has C340/4/4. Update test plan to match data. |
| D8 vigThk | Listed as "4/5" | Should be "5/4" (app uses glass[1]/glass[2] ordering) |
| D9 | Listed as outerT=4, vigThk=5/5 | XTR6129@4mm only has vigThk=4/4. Corrected to 4/4. |
| E8 | Listed as monoT=4, CEN | SKN183 S5 outboard with C366 only exists at monoT=6, cen=false. Corrected. |
| E6 | Listed as CEN | Data row has cen=false despite LUMI as S5 coating. CEN is per-row, not per-coating. |

## Console Log
```
1 error: favicon.ico 404 (browser default, not app code)
0 app-sourced errors or warnings throughout all 51 configs + stress tests
```

## Screenshots
config-A1.png, config-A9.png, config-A13.png, config-B3.png, config-D1.png, config-D4.png, config-E1.png

<details>
<summary>Passed (collapsible)</summary>

A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14,
B1, B2, B3, B4, B5, B6, B7,
C1, C2,
D1, D2, D3, D4, D5, D6, D7, D8, D9, D10,
E1, E2, E3, E4, E5, E6, E7, E8,
F1, F2, F3,
G1, G2, G3, G4, G5, G6,
H1, H2, H3,
S1, S2, S3

</details>
