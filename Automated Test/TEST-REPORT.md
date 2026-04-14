# Test Report — Enthermal Configurator UI Regression

> Consolidated report covering two runs of the plan. Run 1 used the v2 plan and surfaced the plan corrections that produced v3; Run 2 used v3 (now the unified TEST-PLAN.md) and surfaced a further two plan corrections, now baked into the plan.

## Overview

| Run | Date | Commit | Plan | Configs | Pass | Plan corrections surfaced |
|---|---|---|---|---|---|---|
| 1 | 2026-04-12 | 999cd6f | v2 | 51 | 48 | 6 (C3/C4/C5 expectations; D8 vigThk; D9 vigThk; E8 monoT; E6 CEN) |
| 2 | 2026-04-14 | 45fc962 | v3 | 52 | 50 | 3 (E7 VIG pair; C4 unreachable; H3 unreachable) |

Both runs: **0 app failures, 0 data failures, 0 app-sourced console errors.** Every "failure" flagged by either run was a plan-expectation mismatch, not an app or data defect. Every correction has been rolled into the unified [TEST-PLAN.md](TEST-PLAN.md).

---

## Run 1 — 2026-04-12 — commit 999cd6f (plan v2)

### Summary
- Pre-flight: **PASS** (matrix, predicate, goldens, console, CEN integrity — all 5 gates)
- Configs: 51 — **Passed 48** — Failed 0 — Adjusted 3 (test plan expectation mismatches, not app bugs)
- Console errors: **0** (only favicon 404 throughout)
- Stress S1 / S2 / S3: **PASS / PASS / PASS**

### Pre-flight

| Gate | Result | Detail |
|---|---|---|
| §2.1 Availability matrix | PASS | SB72 6mm only, SBR67 5–6mm, SKN183 6mm only, XTR6129 4/6mm — all confirmed |
| §2.2 Naive predicate | PASS | 189 Enthermal + 4748 Inboard + 2016 Outboard combos — 0 disagreements |
| §2.3 Golden anchors | PASS | A1, A9, A13, D1, E1 — all exact value matches |
| §2.4 Console | PASS | 0 app-sourced errors/warnings |
| §2.5 CEN integrity | PASS | 19/98, 724/4748, 358/2016 — exact. 0 orphan rows |

### Group results

**Group A (14/14 PASS):** A1 C366/6/6 NFRC (golden), A2–A8 Cardinal/Vitro series, A9 LUMI/4/4 CEN (golden), A10–A12 CEN coatings, A13 SB72/Starphire/6/4 NFRC (golden), A14 SBR67/5/4. All 11 verified fields pass on every config.

**Group B (7/7 PASS):** All non-Clear substrates. Summary text and cross-section labels correctly show substrate names with ® symbols.

**Group C (2/5 PASS, 3 ADJUSTED):**

| # | Test | Result | Notes |
|---|---|---|---|
| C1 | C366/4/4 → outer=6 | **PASS** | Coating retained, inner unchanged |
| C2 | Q452/4/4 → outer=5 | **PASS** | Q452 retained |
| C3 | SB60/Starphire/5/5 → outer=4 | **ADJUSTED** | Starphire correctly vanishes. App clears selection by design. Plan expected auto-pick — not implemented. |
| C4 | C340/4/4 → inner=6 | **ADJUSTED** | C340/4mm only has inner=4mm in data. innerT5/T6 correctly disabled. |
| C5 | SKN183/6/4 → outer=4 | **ADJUSTED** | SKN183 correctly vanishes. App clears selection. Same root cause as C3. |

Root cause: `updateOuterCoatings()` calls `clearResults()` when the current coating combo becomes unavailable. No auto-replacement. → **This finding became §3a Cleared-selection contract in v3.**

**Group D (10/10 PASS):** D1 golden, D2 S5 toggle, D3 Air round-trip, D4 LUMI CEN (auto-flip + g-Factor label), D5–D7, D8 C366/5/5-4/C270 asym (vigThk corrected to 5/4 — plan listed 4/5), D9 XTR6129/4/4-4/C366/S5 CEN (vigThk corrected to 4/4 — plan listed 5/5), D10 SKN183 CEN.

**Group E (8/8 PASS):** E1 golden through E7, E8 corrected (monoT=6 not 4; cen=false per data — plan listed CEN). E6: row has `cen=false` despite LUMI on S5 — **finding: CEN is per-row, not per-coating → became §3a clarification in v3.**

**Group F (3/3 PASS):** Inboard↔Outboard reseeds and 3× flip all consistent.

**Group G (6/6 PASS):** G1 Enthermal NFRC, G2 Enthermal CEN, G3 round-trip, G4 D4 CEN, G5 D1→D4 flip, G6 Plus Outboard NFRC→CEN on S2 change.

**Group H (3/3 PASS):** Manufacturer prefix audit (29 options, 0 leaks in cross-section), summary rendering char-for-char match, empty-coating guard.

**Stress S1/S2/S3:** All PASS. S1 rapid thickness cycling retained C366 with consistent final state; S2 cleared-selection transition produced `"Select a product to view results."`; S3 3× placement flip with no state leaks.

### Plan corrections from Run 1 (folded into v3)

| Item | Issue | Correction |
|---|---|---|
| C3, C5 | Expected "auto-picks" on coating invalidation | App clears selection by design → **v3 §3a contract** |
| C4 | Expected "all inner options enabled" for C340/4mm | Data only has C340/4/4 → inner=5, inner=6 correctly disabled |
| D8 vigThk | Listed as "4/5" | Should be "5/4" (app uses glass[1]/glass[2] ordering) |
| D9 | Listed as outerT=4, vigThk=5/5 | XTR6129@4mm only has vigThk=4/4 |
| E8 | Listed as monoT=4, CEN | SKN183 S5 outboard with C366 only exists at monoT=6, cen=false |
| E6 | Listed as CEN | Data row has cen=false despite LUMI as S5 — **v3 §3a clarification: per-row, not per-coating** |

### Artifacts (Run 1)

Screenshots: `config-A1.png`, `config-A9.png`, `config-A13.png`, `config-B3.png`, `config-D1.png`, `config-D4.png`, `config-E1.png`.

---

## Run 2 — 2026-04-14 — commit 45fc962 (plan v3)

### Summary
- **Pre-flight: PASS** (availability matrix, full-matrix validation w/ 1 plan correction, predicate cross-check, goldens, console, CEN integrity — all 6 gates)
- **Configs: 52 — Passed 50 — Failed 0 — Plan corrections needed: 2** (C4, H3)
- **Console errors: 0** (favicon 404 + "no label on form field" a11y info, both whitelisted)
- **Stress S1 / S2 / S3: PASS / PASS / PASS**

### Pre-flight

| Check | Result | Detail |
|---|---|---|
| §2.1 Availability matrix | ✓ | SB72 6mm/Starphire-only (3 rows), SBR67 5–6mm/Clear (5), SKN183 6mm/Clear (3, all CEN), XTR6129 4&6mm/Clear (4, all CEN), LUMI 4/5/6mm (6, all CEN), ZEN 4/5/6mm (6, all CEN) |
| §2.2 Full-matrix validation | ⚠ | 51/52 configs exist in JSON. **E7 (4/5 VIG) not in data** — only 5/4, 6/4, 6/5 asymmetric VIGs exist. **Corrected to 5/4** before run. |
| §2.3 Predicate cross-check | ✓ | E=0, PI=0 mismatches across all rows. PO=13 apparent mismatches resolved by keying on `glass[0].substrate` (8 VIG-outer substrate variants: Clear/Starphire/Solexia/Solarbronze/Solargray/Optigray/Solarblue/Optiblue). |
| §2.4 Golden anchors | ✓ | A1, A9, A13, D1, E1 match JSON exactly |
| §2.5 Console | ✓ | 0 errors from app; favicon 404 + a11y info whitelisted |
| §2.6 CEN counts | ✓ | 19/98, 724/4748, 358/2016 exact |
| §2.6 Orphan check | ✓ | `gFactor ↔ uvalCEN` holds on all 6,862 rows |
| §2.6 cen flag vs populated | ✓ | 0 deviations |
| G7 row pinned | ✓ | plus-outboard idx=62: S2=LUMI, S5=LUMI, VIG 4/4, mono 4mm, Ar90, Clear, `cen=true`, `uvalCEN=0.325017` |
| CEN rule verified | ✓ | `row.cen === (glass[0].coating is Saint-Gobain)` — 0 violations across 2016 PO rows |

### Group results

**Group A (14/14 ✓):** A1 C366 6/6 (NFRC golden), A2 C180 4/4, A3 C270 4/4, A4 C272 4/4, A5 C340 4/4, A6 Q452 4/4, A7 SB60 4/4, A8 SB70 4/4, A9 LUMI 4/4 (CEN golden), A10 ZEN 4/4 (CEN), A11 XTR6129 4/4 (CEN), A12 SKN183 6/4 (CEN), A13 SB72/Starphire 6/4 (NFRC golden), A14 SBR67 5/4.

All 14 verified fields matched predicted values (uval, uvalIP, rval, shgc, shgcLabel, tvis, routVis, tuv, oitcLabel, colorInfo L*a*b*, summary innerHTML, toggleChecked, toggleLocked).

**Group B (7/7 ✓):** All non-Clear substrates pass.

**Group C (4/5 ✓, 1 plan correction):**

- C1 C366/4/4 → outer=6 — retained ✓
- C2 Q452/4/4 → outer=5 — retained ✓
- C3 SB60/Starphire/5/5 → outer=4 — cleared ✓
- **C4 C340/4/4 → inner=5 — plan correction needed.** App disables inner=5 and inner=6 radios when the current combo would be invalidated. User cannot execute the action; the cleared-selection contract is never reachable via inner-thickness change in Enthermal. Category: Plan correction. Code and data are consistent. C3 and C5 adequately cover the cleared-selection contract via outer-thickness (which is never disabled). → **Folded into unified plan as "upstream-disable defense" test** ([TEST-PLAN.md §4 Group C C4](TEST-PLAN.md)).
- C5 SKN183/6/4 → outer=4 — cleared ✓

**Group D (10/10 ✓):** D1 NFRC golden, D2 S5, D3 Air, D4 LUMI S2 CEN, D5 SB70, D6 6/6 max, D7 ZEN/LUMI dual SSG, D8 5/4 C270, D9 XTR6129 S5 CEN, D10 SKN183 both sides CEN.

**Group E (8/8 ✓):** E1 NFRC golden, E2 min, E3 max, E4 asym coatings, E5 Air, E6 SB70/LUMI NFRC (S2 not SSG), **E7 corrected 5/4**, E8 C366/SKN183 NFRC (S2 not SSG).

**Group F (3/3 ✓):** First attempt failed because placement-toggle re-render uses `setTimeout(..., 150)` ([enthermal-configurator.html:1313](../enthermal-configurator.html#L1313)). Runner originally read DOM synchronously and missed the update. After adding 250ms wait: F1 Inboard→Outboard, F2 Outboard→Inboard, F3 3× flip all pass. → **Folded into unified plan as a harness requirement**.

**Group G (7/7 ✓):**

- G1 Enthermal C366/4/4 → NFRC locked ✓
- G2 Enthermal LUMI/4/4 → CEN locked ✓
- G3 C366→LUMI→C366 round-trip ✓
- G4 Plus-Inboard LUMI S2 → CEN ✓
- G5 Plus-Inboard D1→D4 → flips correctly ✓
- **G6 Plus-Outboard E1→E6 (negative test):** Neither has SSG on S2; toggle stays NFRC for both ✓ **Catches the coating-identity-vs-row-driven bug class.**
- **G7 Plus-Outboard E1→idx=62 (positive test):** LUMI/LUMI — toggle flips to CEN locked, g-Factor label ✓

**Group H (2/3 ✓, 1 plan correction):**

- H1 Manufacturer prefix audit ✓ — all dropdown entries correctly prefixed; no prefix leaks in cross-section labels (which show `"Clear 4mm"`)
- H2 Summary rendering ✓ — Enthermal, Inboard, Outboard summaries match expected innerHTML char-for-char
- **H3 Empty-coating guard — plan correction needed.** Cannot force Low-E dropdown to empty via UI (empty option is disabled; `sel.value=''` + `change` is no-op). The guard is verified transitively: C3 and C5 both exercise `"Select a product to view results."` when the cascade clears. → **Folded into unified plan as "verified transitively via C3/C5"**.

### Stress tests

- **S1** ✓ — 4→5→6→4 thickness cycling. Final state cleared (SKN183 carried from prior group, not available at 4mm) — confirms §3a contract under stress. No errors, 11 valid options at 4mm.
- **S2** ✓ — SKN183/6/4 → outer=4 yields exactly `"Select a product to view results."`.
- **S3** ✓ — 3 iterations of cycling with inboard/outboard flips. All states populated, no leaks, uval alternates correctly.

### Plan corrections from Run 2 (folded into unified plan)

| Item | Issue | Resolution in unified plan |
|---|---|---|
| E7 | Plan said VIG `4/5`; data has no 4/5 asymmetric outboard VIGs | Corrected to `5/4` (only 5/4, 6/4, 6/5 exist; outer ≥ inner) |
| C4 | Action `inner=5` unreachable — app pre-disables invalid inner radios | Reframed as the upstream-disable-defense test (asserts radios are correctly disabled, no action attempted) |
| H3 | Cannot force empty Low-E via UI (option is disabled) | Reframed as "verified transitively via C3/C5 cleared-selection" |

### New findings from Run 2 (folded into unified plan)

| Finding | Where folded |
|---|---|
| CEN tight rule: `row.cen ⟺ (glass[0].coating ∈ {LUMI, ZEN, SKN183, XTR6129})` — 0 violations across 2016 PO rows | §2.6 CEN integrity, §3a corollary |
| Placement toggle uses 150ms setTimeout fade — synchronous DOM read captures stale state | §4 Group F harness note, §5 S3, §9 Harness requirement #6 |
| Plus-outboard tuple non-unique over 8 VIG-outer substrate variants | §2.3 predicate cross-check note, §4 Group E (implicit Clear), §9 Harness requirement #7 |
| Color display uses NBSP `\xa0` separators between L*/a*/b* values, not plain spaces | §3 Verified fields note, §9 Harness requirement #5 |
| Data globals `DATA`, `DATA_PLUS_IN`, `DATA_PLUS_OUT` are `let`-declared and do not attach to `window` — use `eval('DATA')` from within an injected function | §1 Tooling & Setup note |

### Artifacts (Run 2)

Screenshot: `config-A1.png` (Phase 2 dry run). Per-config screenshots not captured during Phase 3a/3b batch execution (runner operated via JS-injected state reads for speed). Per-config screenshots can be added by re-invoking the runner individually.

---

## Trajectory

Run 1 (v2) → Run 2 (v3) → unified plan: the plan grew stricter each iteration, not looser. Run 1's adjustments all surfaced product-behavior-vs-plan-expectation mismatches that the app was correct about. Run 2's stricter pre-flight gate (§2.2 full-matrix validation) caught one of those (E7) before any UI interaction, exactly as designed. Run 2's remaining corrections (C4, H3) are cases where the UI prevents the scenario the plan asks the test to induce — resolvable by reframing, not by a behavior change.

**Zero app or data defects surfaced across both runs.** The app's cleared-selection and upstream-disable behaviors are consistent, intentional, and — as verified — catch exactly the invalidation cases the §3a contract describes.

## Console log (both runs)

```
Run 1: 1 error  — favicon.ico 404 (browser default, not app code)
       0 app-sourced errors or warnings across 51 configs + stress tests
Run 2: 1 error  — favicon.ico 404 (whitelisted)
       1 issue  — "No label associated with a form field" (a11y, not app logic)
       0 app-sourced errors or warnings across 52 configs + stress tests
```
