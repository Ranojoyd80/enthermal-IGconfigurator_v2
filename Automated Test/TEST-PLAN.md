# Test Plan — Enthermal Configurator UI Regression

## 0. Goals
Verify CSV → JSON → stack-based UI produces correct filter, match, and display output across the full product catalog. Focus areas:
- IG_Config 12-04-26 dataset migration (98/4748/2016 rows)
- Data-driven CEN/NFRC toggle (auto-flip, locked, real CEN values) across **all three tabs**
- Simplified Comment format (2-token coatings on implied Clear, bare `Argon`/`Air`)
- New products: Optiblue substrate, Air gas fill data
- Updated Plus summary format (exterior-to-interior reading order)

## 1. Tooling & Setup
- **MCP server:** Chrome DevTools MCP, headed mode (default).
- **Server:** `python -m http.server --bind 127.0.0.1 8000` in repo root (separate terminal — must stay running).
- **Target:** `http://127.0.0.1:8000/enthermal-configurator.html`.
- **Ready check:** `document.querySelector('#outerCoating').options.length > 1`.

## 2. Pre-flight (gates the suite — any failure aborts)
1. **Availability matrix dump** for restricted-thickness products (SB72: 6mm only, SBR67: 5–6mm, SKN183: 6mm only, XTR6129: 4/6mm) and CEN-enabled coatings (LUMI, ZEN, SKN183, XTR6129).
2. **Independent predicate cross-check.** Naive reimplementation (linear scan, explicit if-statements) must agree with the app's predicate on every Section 4 config. Disagreement = abort.
3. **Golden-file anchors** (`test/golden.json`):
   - **NFRC anchors (A1, A13, D1, E1):** `uval`, `uvalIP`, `rval`, `shgc`, label `"SHGC"`, toggle `"NFRC"`, summary string.
   - **CEN anchor (A9):** `uvalCEN`, `gFactor`, label `"g-Factor"`, toggle `"CEN, locked"`, summary string. Do **not** record `uval`/`shgc` — runner asserts those display as `"—"`.
4. **Console subscription armed.** Filter to `enthermal-configurator.html` source URL only. `error` and `warn` from app code fail the run.
5. **CEN field presence + integrity:**
   - Counts: enthermal **19/98**, plus-inboard **724/4748**, plus-outboard **358/2016**. Deviation = abort.
   - Assert: for every row, `gFactor != null` ⟺ `uvalCEN != null`. Orphans = data bug, abort.

## 3. Per-config cycle
1. Narrate config. 2. Drive UI. 3. Read back via DevTools evaluate. 4. Compare to naive predicate + golden anchor. 5. Screenshot to `test-results/config-NN.png`. 6. Report-buffer entry.

**Verified fields**

| Field | Source of truth |
|---|---|
| Summary innerHTML | `match.stack` + display helpers |
| U-value SI (3 dec) | `match.uvalCEN` if CEN, else `match.uval` |
| U-value IP / R-value | `match.uvalIP` / `match.rval` — must show `"—"` when CEN |
| SHGC / g-Factor value | `match.gFactor` if CEN, else `match.shgc` |
| SHGC label text | `"g-Factor"` if CEN, `"SHGC"` if NFRC |
| OITC label text | `"Rw"` if CEN, `"OITC"` if NFRC |
| Tvis %, RoutVis %, T-UV % | corresponding `match.*` |
| OITC/Rw value | `ENTHERMAL_ACOUSTIC` lookup |
| CEN/NFRC toggle | `checked` matches `match.cen`; `.locked` present for CEN-only |
| **Gas-fill round-trip** | `match.gas` matches radio selection — fail if mismatched even when u-value plausible. Catches silent Air→Argon fallback. |
| Cross-section labels | from `match.glass[i]` |
| Color card L/a/b | `match.extL/A/B` (or `intL/A/B` flipped) |
| Dropdown option set | unique coatings at current thickness |
| Cascade disabled state | predicate |

---

## 4. Test Matrix — 51 configs in 8 groups

### Group A — Enthermal happy path (14)
A1 C366 6/6 NFRC **golden** • A2 C180 4/4 • A3 C270 4/4 • A4 C272 4/4 • A5 C340 4/4 • A6 Q452 4/4 • A7 SB60 4/4 • A8 SB70 4/4 • **A9 LUMI 4/4 CEN golden** • A10 ZEN 4/4 CEN • A11 XTR6129 4/4 CEN • A12 SKN183 6/4 CEN (6mm only) • **A13 SB72 6/4 NFRC golden** (Starphire, 6mm only) • A14 SBR67 5/4 (5–6mm only).

### Group B — Enthermal non-Clear substrates (7)
B1 SB60/Starphire 6/4 • B2 SB60/Starphire 5/5 • B3 SB60/Optiblue 6/4 • B4 SB60/Optigray 6/5 • B5 SB60/Solarblue 6/6 • B6 SB60/Solarbronze 6/4 • B7 SB72/Starphire 6/6.

### Group C — Enthermal cascade (5) — C5 transition moved to §5
| # | Setup | Action | Expected |
|---|---|---|---|
| C1 | C366/4/4 | outer→6 | C366 retained; inner unchanged |
| C2 | Q452/4/4 | outer→5 | Q452 still available |
| C3 | SB60/Starphire/5/5 | outer→4 | Starphire vanishes → auto-picks Clear (post-state) |
| C4 | C340/4/4 | inner→6 | all inner options enabled |
| C5 | SKN183/6/4 | outer→4 | SKN183 vanishes → valid coating + populated summary + no errors (post-state only) |

### Group D — Plus Inboard (10)
D1 4/C366/4/4/C366/S4/Ar90 **golden** • D2 same +S5 • D3 same +Air (gas round-trip) • D4 4/LUMI/4/4/C366/S4/Ar90 **CEN** • D5 4/SB70/... mix • D6 6/C366/6/6/C366 max • D7 4/ZEN/4/4/LUMI **CEN** • D8 5/C366/4/5/C270 asym • D9 4/XTR6129/5/5/C366/S5 **CEN** • D10 6/SKN183/6/6/SKN183/S4 **CEN**.

### Group E — Plus Outboard (8)
E1 5/5/C366/4/C366/Ar90 **golden** • E2 4/4 min • E3 6/6/6 max • E4 5/5/C270/4/C272 (S2≠S5) • E5 5/5/C366/4/C366 +Air (gas round-trip) • E6 5/5/SB70/5/LUMI **CEN** • E7 4/5/C366/4/C366 asym • E8 6/6/C366/4/SKN183 **CEN**.

### Group F — Placement toggle (3)
F1 Inboard→Outboard reseed • F2 E6→Inboard reseed + CEN updates • F3 3× flip (state-leak only — see §5).

### Group G — CEN/NFRC toggle (6) — covers all three tabs
| # | Tab | Config | Expected |
|---|---|---|---|
| G1 | Enthermal | C366/4/4 | NFRC, locked; U/R visible |
| G2 | Enthermal | LUMI/4/4 | auto-CEN, locked; `"g-Factor"`; uvalIP/rval = `"—"` |
| G3 | Enthermal | C366→LUMI→C366 | CEN↔NFRC both directions |
| G4 | Plus Inboard | D4 | CEN; gFactor matches JSON |
| G5 | Plus Inboard | D1→D4 | NFRC→CEN on coating change |
| **G6** | **Plus Outboard** | **E1→E6** | **NFRC→CEN on S2 change. Closes Outboard auto-flip gap (separate seeding from Inboard).** |

### Group H — Cross-cutting (3)
| # | Purpose |
|---|---|
| H1 | **Manufacturer prefix audit (data-driven).** One JS evaluate dumps all three dropdowns' options. Assert `/^(Cardinal\|Vitro\|Saint-Gobain) /`. Cross-section spans must NOT match the prefix regex. |
| H2 | **Summary rendering** — one Enthermal, one Inboard, one Outboard, character-for-character. Inboard format: `<S2> (S2) on <Xmm> with <VIG> mm Enthermal <VIGcoat> (SN) inboard`. Outboard format: `<VIG> mm Enthermal <S2> (S2) outboard with <S5> (S5) on <Xmm>`. |
| H3 | **Empty-coating guard** — switch Plus thickness to trigger repopulation. Summary must show `"Select a product to view results."` when either Low-E dropdown is empty. |

---

## 5. Stress test (JS-injected, no awaits)

**S1 — Rapid thickness cycling:**
```js
for (const v of [4,5,6,4]) {
  document.querySelector(`#outerThickness input[value="${v}"]`).click();
}
```
Pass: no errors, no empty dropdowns, internally consistent final state.

**S2 — C5 transition capture:** Set up SKN183/6/4, then in one evaluate:
```js
document.querySelector('#outerThickness input[value="4"]').click();
return document.querySelector('#summaryBar').innerHTML;
```
Pass: result is either `"Select a product"` OR the post-pick valid summary. Document which — assert it's one or the other, not garbage.

**S3 — Placement-toggle interleave:** Re-run S1 3× with placement flipped between iterations.

---

## 6. Report Format
```markdown
# Test Report — <ISO date> — commit <sha>
## Summary
- Pre-flight: PASS/FAIL (matrix, predicate, goldens, console, CEN integrity)
- Configs: 51 — Passed N — Failed N
- Console errors: N
- Stress S1/S2/S3: PASS/FAIL each
## Failures
### Config D4 — Plus Inboard / 4mm / LUMI S2 / 4/4 / C366 S4 / Ar90
**Expected toggle:** CEN (locked) | **Actual:** NFRC
**Expected U-value:** 0.411 (uvalCEN) | **Actual:** 0.393 (uval — wrong source)
**Expected label:** g-Factor | **Actual:** SHGC
**Adjacent fields that also failed:** shgcUnit text
**Screenshot:** test-results/config-D4.png
## Passed (collapsible) <details>...</details>
## Console log
```

---

## 7. Catches / doesn't catch

**Catches:** filter predicate bugs (naive + golden, independently); display drift; cascade resets; S4/S5 surface; placement state leaks; CEN auto-flip and lock **across all three tabs**; CEN value display; label switching (SHGC↔g-Factor, OITC↔Rw); **silent gas-fill fallback**; Air/Argon coverage; empty-coating guard; unreachable new products; runtime JS errors and app warnings; manufacturer prefix; glass color fallback (Optiblue); CEN data integrity (orphan rows).

**Doesn't catch:** visual fidelity, color perception, font/layout; CEN dimmed-label opacity; true render-loop races (S2/S3 approximate but don't guarantee); print styles; animation; alternate viewports.

## 8. Coverage sanity check
51 configs + pre-flight + 3 stress sub-cases exercise: every coating shortcode (14); every substrate (8 inc. Optiblue); every manufacturer (3, in H1); all 4 Plus cascade nodes as both upstream and downstream; every toggle flipped ≥2×; CEN auto-flip in **all three tabs** (G3/G5/G6); CEN values for 4 Saint-Gobain coatings; Air and Ar90 round-trip-verified in both Plus cascades; every thickness-restricted coating individually; both cascade directions; empty-coating guard; both summary formats.

## 9. Operational notes

**Estimated runtime:** ~12–15 minutes headed (revised up). 51 configs + Group G transitions + 3 stress sub-cases push tool-call count past 120; 300 ms inter-action pacing dominates.

**Recommended phasing — do not run as one prompt:**
1. **Phase 1** — Pre-flight only. Stop at golden-file checkpoint for human review.
2. **Phase 2** — Single-config dry run (A1) end-to-end. Catches integration issues (paths, screenshot dir, report buffer).
3. **Phase 3a** — Groups A, B, C, D.
4. **Phase 3b** — Groups E, F, G, H, then §5, then §6 assembly.

`/clear` between 3a and 3b if context pressure is visible. Re-load `TEST-PLAN.md` and `test/golden.json` at start of 3b.

**Spot-check protocol:** before trusting the final report, manually open three random screenshots and confirm they show what the report claims. Cheapest defense against fabricated success.

**Prerequisites:**
1. Chrome DevTools MCP installed
2. `python -m http.server --bind 127.0.0.1 8000` in repo root (separate terminal, must stay open)
3. `test/golden.json` populated by hand (A9 uses CEN schema)
4. Naive predicate reimplementation in test runner
