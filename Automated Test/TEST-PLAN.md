# Test Plan — Enthermal Configurator UI Regression

> Unified plan (supersedes v1/v2/v3). Incorporates corrections from the two test runs on 2026-04-12 (commit 999cd6f) and 2026-04-14 (commit 45fc962).
> **Revised 2026-07-11 (commit 5273ebb, dataset 07-07-26):** row/CEN counts re-derived; CEN rule replaced with the corrected maker-set rule (the old "SSG on S2" form is wrong for current data — 636 rows differ); E8 expectation corrected to CEN; std-toggle contract updated (CEN rows are now *enabled*, not locked); §3a contract extended (render + cross-section also clear); goldens re-captured (incl. per-config `cid`); B8/B9, D11, F4/F5, G2b, G8 added; §2 is now executable (`preflight.py`).

## 0. Goals

Verify CSV → JSON → stack-based UI produces correct filter, match, and display output across the full product catalog. Focus areas:

- IG_Config 07-07-26 dataset (98 / 4470 / 1876 rows across enthermal / plus-inboard / plus-outboard)
- Data-driven CEN/NFRC toggle — **per-row `cen` field**, driven by the corrected rule: CEN ⇔ a Saint-Gobain coating is present anywhere in the assembly AND no Vitro coating is present (rule corrected 2026-07-09)
- Simplified Comment format (2-token coatings on implied Clear, bare `Argon`/`Air`)
- Per-config anchor renders (`cid` → `anchor_<cid>.webp`, Overcast/PartlyClear)
- Updated Plus summary formats (outboard mono lite is thickness-only as of 2026-07-11)
- **Cleared-selection behavior** when upstream changes invalidate the current combo (§3a — contract extended 2026-07-11: render and cross-section clear too)

## 1. Tooling & Setup

- **MCP server:** Chrome DevTools MCP, headed mode (default)
- **Server:** `python serve.py` in repo root (separate terminal — must stay running; serve.py adds `Cache-Control: no-store`, so no hard-refresh needed between app edits)
- **Target:** `http://localhost:8000/enthermal-configurator.html`
- **Ready check:** `document.querySelector('#outerCoating').options.length > 1`
- **Data access note:** `DATA`, `DATA_PLUS_IN`, `DATA_PLUS_OUT` are declared with `let` at top level and do not attach to `window`. Use `eval('DATA')` from inside an injected function to access them.

## 2. Pre-flight (gates the suite — any failure aborts)

> **Executable:** `python "Automated Test/preflight.py"` implements items 1–4 and 6 (20 gates; exit 1 = abort). Item 5 (console subscription) is a runner responsibility. Last clean run: 2026-07-11, 20/20 PASS.

1. **Availability matrix dump** for restricted-thickness products, re-derived from the 07-07-26 dataset (unchanged from the prior dataset): SB72: 6mm only / Starphire only; SBR67: 5–6mm / Clear; SKN183: 6mm only / Clear / all CEN; XTR6129: 4 & 6mm / Clear / all CEN; LUMI: 4/5/6mm / Clear / all CEN; ZEN: 4/5/6mm / Clear / all CEN. SB60 carries all 8 substrates (tinted ones at 6mm outer only).

2. **Full-matrix config validation.** Every §4 entry must resolve to **exactly one** JSON row (uniqueness now asserted, not just non-emptiness) AND that row's `cen` flag must equal the matrix's "CEN expect" column. Any deviation aborts before UI interaction — this is what catches plan-vs-data drift like the E8 correction.

3. **Independent predicate cross-check.** Naive reimplementation must agree with the app's predicate on **every row** in all three JSONs (6,444 rows total, not just §4 configs). The UI match keys are verified globally unique per file (preflight gate 3), so `filtered[0]` in the app is always the single record. Plus-outboard predicates must key on `glass[0].substrate` — always `Clear` for §4 Group E configs.

4. **Golden-file anchors** (`Automated Test/golden.json`, re-captured 2026-07-11 from commit 5273ebb):
   - **NFRC anchors (A1, A13, D1, E1):** `uval`, `uvalIP`, `rval`, `shgc`, display strings, label `"SHGC"`, toggle `"NFRC"` **locked**, summary string, `cid`.
   - **CEN anchor (A9):** `uvalCEN`, `gFactor`, label `"g-Factor"`, toggle `"CEN"` **enabled** (see §3 — CEN rows are flippable now, not locked), summary string, `cid`. Do **not** record `uval`/`shgc` — the runner asserts `uvalIP`/`rval` display as `"—"` while CEN is shown.

5. **Console subscription armed.** Filter to `enthermal-configurator.html` source URL only. `error` and `warn` from app code fail the run. Whitelisted: browser favicon 404; the "No label associated with a form field" a11y issue (down to 4 as of 2026-07-11 — the remaining radio-group captions; the 4 select captions now carry `for=`).

6. **CEN field presence + integrity:**
   - Counts: enthermal **19/98**, plus-inboard **752/4470**, plus-outboard **366/1876**. Any deviation aborts.
   - Every row must satisfy `gFactor != null ⟺ uvalCEN != null ⟺ row.cen`. Orphans = data bug, abort.
   - **CEN rule (corrected 2026-07-09, verified 0 violations across all 6,444 rows on 2026-07-11):** `row.cen === (makers(assembly) ∩ {Saint-Gobain} ≠ ∅ AND makers(assembly) ∩ {Vitro} = ∅)`, where makers() is over every coating on any lite. **The old "SSG on Surface 2" tight form is wrong for current data** — 428 inboard + 208 outboard rows have `cen=true` with a non-SG S2 (SG coating on S4/S5, no Vitro). A Vitro coating anywhere blocks CEN even when SG is present (232 outboard rows, all `cen=false`).

## 3. Per-config cycle

1. Narrate config. 2. Drive UI. 3. Read back via DevTools evaluate. 4. Compare to naive predicate + golden anchor. 5. Screenshot to `Automated Test/config-NN.png`. 6. Report-buffer entry.

### 3a. Cleared-selection contract

When an upstream change (outer thickness, substrate) invalidates the currently selected combination, `updateOuterCoatings()` **clears** the selection rather than auto-picking a replacement. The full cleared state (extended 2026-07-11 — one shared `clearResults()` for both tabs and the Plus no-match branch):

- Summary shows `"Select a product to view results."`; all 9 metric fields show `"—"`.
- **Exterior render drops to the honest placeholder** (`#colorRenderImg` hidden, `#colorRenderFallback` visible, zoom button hidden) — the previous config's facade must NOT stay up.
- **Both tabs' cross-section text labels reset to `"—"`** (`csThicknessVal`, `csOuterDetail/Sub`, `csInnerDetail`, `csThicknessValPlus`, `csPlusOuterDetail/Coating`, `csPlusVigCoatingLabel`, `csPlusRightCoating`, `csPlusArgonLabel`, `csIGUWeight`, `csECarbon`).
- Recovery: selecting any valid combo restores metrics, labels, and the render (the image `load` event clears the placeholder).

This is the intended behavior. Group C and stress test S2 assert against this contract. If product owners later decide auto-pick is desired, this section and Group C must be updated together — they are the single source of truth for the expected UX of an invalidated selection.

**Important corollary (from run on 2026-04-14):** for *inner*-thickness changes, the app pre-disables invalid inner-thickness radios — the user cannot execute the invalid action in the first place. So the cleared-selection path is only reachable via outer-thickness changes. Group C verifies both behaviors: C1/C2 (valid upstream change retained), C3/C5 (outer change → cleared), C4 (inner radios correctly disabled — action unreachable).

**Verified fields**

**Standard-display contract (changed since April):** let `cenShown = stdToggleInput.checked`. On row change, `cenShown` defaults to `match.cen`; on CEN rows the toggle is **enabled** and the user may flip `cenShown` freely (a manual flip survives same-row re-renders via `stdUserFlip`, which is consumed per render and cleared on early returns). On non-CEN rows the toggle is **disabled and forced to NFRC**. All CEN/NFRC-dependent fields key off `cenShown`, not `match.cen`.

| Field | Source of truth |
|---|---|
| Summary innerHTML | `match.stack` + display helpers |
| U-value SI (3 dec) | `match.uvalCEN` if `cenShown`, else `match.uval` |
| U-value IP / R-value | `match.uvalIP` / `match.rval` — must show `"—"` when `cenShown` |
| SHGC / g-Factor value | `match.gFactor` if `cenShown`, else `match.shgc` |
| SHGC label text | `"g-Factor"` if `cenShown`, `"SHGC"` if not |
| OITC / Rw values | Dual static columns (no label switch). `ENTHERMAL_ACOUSTIC` lookup; OITC value populated & Rw `"—"` when NFRC shown, reversed when CEN shown. Plus tab: both `"—"` (no acoustic data) |
| Tvis %, RoutVis %, T-UV % | corresponding `match.*` |
| CEN/NFRC toggle | `disabled === !match.cen`; `checked` defaults to `match.cen` on row change; user-flippable only when `match.cen` |
| Inboard cross-section coated-lite label | `#csPlusRightCoating` shows the substrate+thickness of the lite the S4/S5 coating is **on**: Inboard+S4 → `glass[1]`, otherwise `glass[2]` (fixed 2026-07-11; regression D11) |
| Gas-fill round-trip | `match.gas` matches radio selection (catches silent Air→Argon fallback) |
| Cross-section labels | from `match.glass[i]` |
| Color card | Per-config render (`#colorRenderImg`) — `setAnchorImages(match.cid)` points it at `Anchor_Renders/<Folder>/anchor_<cid>.webp` (`cid` 1-based, folder from `data-folder`); the sky toggle swaps `src` between Overcast/PartlyClear for that `cid` (default Overcast). **No per-config L/a/b readout or flip** — that UI was removed. |
| Dropdown option set | unique coatings at current thickness |
| Cascade disabled state | predicate |

---

## 4. Test Matrix — 64 cases in 8 groups (A14 B9 C5 D11 E8 F5 G9 H3)

All matrix entries are validated against the JSON during pre-flight (§2.2 / `preflight.py`, incl. per-entry CEN expectation). Historical corrections from prior runs: E7 (was 4/5 — no such asymmetric VIG in data), D8 vigThk (5/4 not 4/5), D9 vigThk (4/4 not 5/5), E6 CEN expectation (NFRC — Vitro S2 blocks CEN). **2026-07-11 corrections:** E8 flipped to **CEN** (S5=SKN183, no Vitro — the old NFRC expectation followed the wrong S2-only rule); B8/B9 added (Solexia/Solargray were uncovered); D11 added (coated-lite label regression); F4/F5 added (state-desync regressions from the 2026-07-11 audit); G8 added (S5-SG-alone positive CEN case that distinguishes the corrected rule from the old one). Data note: inboard VIG pairs are 4/4, 5/4, 5/5, 6/5, 6/6 — **no 6/4** (the 6/4 select option must be disabled in Inboard mode); outboard has all six pairs.

### Group A — Enthermal happy path (14)

A1 C366 6/6 NFRC **golden** • A2 C180 4/4 • A3 C270 4/4 • A4 C272 4/4 • A5 C340 4/4 • A6 Q452 4/4 • A7 SB60 4/4 • A8 SB70 4/4 • **A9 LUMI 4/4 CEN golden** • A10 ZEN 4/4 CEN • A11 XTR6129 4/4 CEN • A12 SKN183 6/4 CEN (6mm only) • **A13 SB72 6/4 NFRC golden** (Starphire, 6mm only) • A14 SBR67 5/4 (5–6mm only).

### Group B — Enthermal non-Clear substrates (9)

B1 SB60/Starphire 6/4 • B2 SB60/Starphire 5/5 • B3 SB60/Optiblue 6/4 • B4 SB60/Optigray 6/5 • B5 SB60/Solarblue 6/6 • B6 SB60/Solarbronze 6/4 • B7 SB72/Starphire 6/6 • **B8 SB60/Solexia 6/4 • B9 SB60/Solargray 6/4** (added 2026-07-11 — completes all 8 substrates).

Starphire display contract (B1/B2/B7/A13): the assembly is all-Starphire, so the **inboard cross-section label and summary read "Starphire Xmm"**, not "Clear Xmm", and every pane gets the Starphire tint.

### Group C — Cleared-selection cascade (5)

| # | Setup | Action | Expected (per §3a contract) |
|---|---|---|---|
| C1 | C366/4/4 | outer→6 | Combo still valid → C366 retained, inner unchanged, summary populated |
| C2 | Q452/4/4 | outer→5 | Combo still valid → Q452 retained, summary populated |
| C3 | SB60/Starphire/5/5 | outer→4 | Combo invalid → **selection cleared per the full §3a contract** (summary, metrics, render placeholder, cross-section labels), no console errors |
| C4 | C340/4/4 | *attempt* inner→5 | Action unreachable: inner=5 and inner=6 radios are disabled by the app (C340/4 only exists at inner=4). Test asserts `inner.disabled === true` for the invalid options — **verifies the UI's upstream-disable defense**, which prevents the cleared-selection path from being reached via inner-thickness changes. |
| C5 | SKN183/6/4 | outer→4 | Combo invalid (SKN183 is 6mm-only) → **selection cleared**, same expectations as C3, then recovery: re-select a valid coating → metrics, labels, and render all restore |

### Group D — Plus Inboard (11)

| # | mono t | S2 | VIG | VIG coat | Srf | Gas | CEN expect | Notes |
|---|---|---|---|---|---|---|---|---|
| D1 | 4 | C366 | 4/4 | C366 | S4 | Ar90 | NFRC | **golden** |
| D2 | 4 | C366 | 4/4 | C366 | S5 | Ar90 | NFRC | S5 toggle |
| D3 | 4 | C366 | 4/4 | C366 | S4 | Air | NFRC | gas round-trip |
| D4 | 4 | LUMI | 4/4 | C366 | S4 | Ar90 | CEN | S2 SSG drives CEN |
| D5 | 4 | SB70 | 4/4 | C366 | S4 | Ar90 | NFRC | mix |
| D6 | 6 | C366 | 6/6 | C366 | S4 | Ar90 | NFRC | max |
| D7 | 4 | ZEN | 4/4 | LUMI | S4 | Ar90 | CEN | dual Saint-Gobain |
| D8 | 5 | C366 | 5/4 | C270 | S4 | Ar90 | NFRC | vigThk uses glass[1]/glass[2] order |
| D9 | 4 | XTR6129 | 4/4 | C366 | S5 | Ar90 | CEN | XTR6129@4mm only exists at 4/4 |
| D10 | 6 | SKN183 | 6/6 | SKN183 | S4 | Ar90 | CEN | 6mm only |
| D11 | 5 | C180 | 5/4 | C180 | S4→S5 | Ar90 | NFRC | **Coated-lite label regression (fixed 2026-07-11):** unequal VIG panes; assert `#csPlusRightCoating` = "Clear **5**mm" under S4 (coating on `glass[1]`) and "Clear **4**mm" under S5 (coating on `glass[2]`). Both surface rows exist (validated as D11a/D11b in preflight). |

### Group E — Plus Outboard (8) — VIG-outer substrate implicitly Clear for all entries

> **Surface-control presentation in Outboard (clarified by 2026-07-11 run):** the Coating Surface field (`#plusCoatingSurfaceField`) is **hidden** entirely and the hidden radio is forced to S5 — there is no visible locked toggle. Assert `field.offsetParent === null` and `plusSrf5.checked === true`.

| # | VIG | S2 | mono t | S5 | Gas | CEN expect | Notes |
|---|---|---|---|---|---|---|---|
| E1 | 5/5 | C366 | 4 | C366 | Ar90 | NFRC | **golden** |
| E2 | 4/4 | C366 | 4 | C366 | Ar90 | NFRC | min |
| E3 | 6/6 | C366 | 6 | C366 | Ar90 | NFRC | max |
| E4 | 5/5 | C270 | 4 | C272 | Ar90 | NFRC | S2≠S5 |
| E5 | 5/5 | C366 | 4 | C366 | Air | NFRC | gas round-trip |
| E6 | 5/5 | SB70 | 5 | LUMI | Ar90 | NFRC | **Vitro blocks CEN** — SB70 present, so `cen=false` despite LUMI on S5 (same expectation as before, corrected rationale) |
| E7 | 5/4 | C366 | 4 | C366 | Ar90 | NFRC | asym VIG (outer ≥ inner; asym pairs 5/4, 6/4, 6/5 all exist in outboard) |
| E8 | 6/6 | C366 | 6 | SKN183 | Ar90 | **CEN** | only exists at monoT=6. **Corrected 2026-07-11:** SKN183 on S5 with no Vitro anywhere → `cen=true` under the corrected rule (old plan expected NFRC per the wrong S2-only rule; data confirms `cen=true`) |

### Group F — Placement toggle & tab-switch state (5)

F1 Inboard→Outboard reseed • F2 E6→Inboard reseed • F3 3× flip (state-leak only).

**F4 — S4/S5 round-trip desync regression (critical bug fixed 2026-07-11):** Inboard, flip Coating Surface to S5, placement→Outboard, placement→Inboard. Assert the surface toggle **visual**, the hidden radio, and the summary's `(S4)` all agree (seed resets to S4). Before the fix the toggle showed S5 while results were S4.

**F5 — Vitro VIG retention on tab re-click (fixed 2026-07-11):** Inboard, exterior = any Saint-Gobain (e.g. XTR6129), manually select a Vitro VIG coating (SB60), switch to the Enthermal™ tab and back. Assert `#plusVigCoating` still holds SB60 (the gap-toggle resizer used to re-run the cascade and `pickPlusVigDefault` silently swapped it).

**Harness requirement:** the placement toggle uses a **150ms `setTimeout` fade** (the `wrap.style.opacity='0'` block in the placement-toggle IIFE, ~line 1600) before re-seeding the cascade. A synchronous DOM read after clicking `posToggleInput` captures stale state. Wait **≥250ms** after any placement flip before reading the summary/metrics.

### Group G — CEN/NFRC toggle (9)

CEN is driven by the matched row's `cen` field, which follows the **corrected maker-set rule** (§2.6): SG coating present anywhere AND no Vitro coating. The toggle contract also changed: CEN rows arrive showing CEN with the toggle **enabled** (user may flip to NFRC and back); non-CEN rows are **locked** to NFRC. G6 is the **negative test** (Vitro blocks CEN even with SG present). G7 and G8 are **positive tests** — G7 with SG on S2, G8 with SG *only* on S5, which is exactly the case the old S2-only rule got wrong.

| # | Tab | Test | Expected |
|---|---|---|---|
| G1 | Enthermal | C366/4/4 | NFRC shown, toggle **locked**; U-IP/R visible |
| G2 | Enthermal | LUMI/4/4 | CEN row → CEN shown by default, toggle **enabled**; `"g-Factor"` label; uvalIP/rval = `"—"` |
| G2b | Enthermal | LUMI/4/4, user flips to NFRC | NFRC values display (`uval`/`shgc`, `"SHGC"` label, U-IP/R restored); flip back → CEN values; the manual flip must survive a same-row re-render |
| G3 | Enthermal | C366→LUMI→C366 | NFRC↔CEN both directions, driven by per-row `cen` |
| G4 | Plus Inboard | D4 (LUMI S2) | CEN shown by default, toggle enabled, g-Factor |
| G5 | Plus Inboard | D1→D4 | NFRC→CEN on S2 change (C366→LUMI) |
| **G6** | **Plus Outboard** | **E1 → E6** | **No flip expected** — E6 has LUMI on S5 but SB70 (Vitro) on S2, and **Vitro anywhere blocks CEN**. If it flips, the maker-set rule is implemented wrong. |
| **G7** | **Plus Outboard** | **E1 → (VIG 4/4, S2=LUMI, S5=LUMI, mono 4mm, Ar90, Clear)** | **Positive (SG on S2):** flips to CEN. Row re-validated 2026-07-11: `uvalCEN=0.325017`. (Do not key on file index — locate by tuple.) |
| **G8** | **Plus Outboard** | **E1 → (VIG 5/5, S2=C366, S5=LUMI, mono 4mm, Ar90, Clear)** | **Positive (SG on S5 only, no Vitro) — new-rule discriminator:** flips to CEN (`uvalCEN=0.252766`, `gFactor=0.251719`). Under the old S2-only rule this row would be NFRC; 208 outboard + 428 inboard rows are in this class. |

### Group H — Cross-cutting (3)

| # | Purpose |
|---|---|
| H1 | Manufacturer prefix audit — all dropdown entries match `/^(Cardinal\|Vitro\|Saint-Gobain) /`; cross-section spans must NOT match (they show bare names like "Clear 4mm" or "LoE³ 366"). |
| H2 | Summary rendering — Enthermal, Inboard, Outboard, character-for-character against expected innerHTML. Current formats (2026-07-11): Enthermal `<coating[ on Sub]> on <N>mm outboard and <Sub> <N>mm inboard.`; Inboard `<s2> (S2) on <N>mm with <A/B mm> Enthermal <coat> (S4\|S5) inboard`; Outboard `<A/B mm> Enthermal <s2> (S2) outboard with <coat> (S5) on <N>mm` — **outboard mono lite is thickness-only** (its substrate is Clear everywhere except all-Starphire rows, where the S2 combo already names Starphire). Goldens carry one exact string per format. |
| H3 | Empty-coating guard — the Low-E dropdown cannot be set to empty via the UI (empty option is disabled). The guard is verified transitively: when the cascade clears the selection (C3, C5, S2), the summary must show `"Select a product to view results."`. H3 asserts this on the resulting state of C3 or C5. |

---

## 5. Stress test (JS-injected, no awaits)

**S1 — Rapid thickness cycling:**
```js
for (const v of [4,5,6,4]) {
  document.querySelector(`input[name="outerThickness"][value="${v}"]`).click();
}
```
Pass: no errors, no empty dropdowns, internally consistent final state. Note: if prior state had a thickness-restricted coating selected (e.g. SKN183 at 6mm), final state at 4mm will cleared per §3a — this is correct behavior, not a failure.

**S2 — Cleared-selection transition (per §3a contract):** set up SKN183/6/4, then in one evaluate:
```js
document.querySelector('input[name="outerThickness"][value="4"]').click();
return document.querySelector('#summaryText').innerHTML;
```
Pass: result must be `"Select a product to view results."` — asserts the §3a contract, not "either/or". A follow-up read (after a normal await) must also find the render placeholder visible and cross-section labels `"—"` (extended contract).

**S3 — Placement-toggle interleave:** Re-run S1 3× with placement flipped between iterations. Must wait ≥250ms after each placement flip (see Group F harness note). Pass: no cleared states, no stale summaries, uval populated throughout.

---

## 6. Report Format

```markdown
# Test Report — <ISO date> — commit <sha>
## Summary
- Pre-flight: PASS/FAIL (preflight.py 20 gates + console subscription)
- Cases: 64 — Passed N — Failed N — Plan corrections needed: N
- Console errors: N (favicon + 4 remaining a11y-label issues whitelisted)
- Stress S1/S2/S3: PASS/FAIL each
```

**Reporting rule:** "Plan corrections needed" must appear in the top-line summary, not buried in a section.

If a config produces unexpected output, the agent must categorize as exactly one of:
- **App failure** — code does the wrong thing relative to the plan and the data both agreeing
- **Data failure** — JSON missing or wrong row
- **Plan correction needed** — plan expectation is wrong; code and data are consistent

The agent does **not** silently rewrite the plan mid-run. Each correction goes in the corrections list and the run continues with the original expectation marked as such.

---

## 7. Catches / doesn't catch

**Catches:** filter predicate bugs (naive + golden, independently); display drift; cascade resets; S4/S5 surface; placement state leaks **incl. the toggle-vs-radio desync (F4) and Vitro-swap-on-tab-click (F5)**; CEN auto-flip driven by the maker-set rule — Vitro-blocking negative (G6) and S5-SG-alone positive (G8); manual CEN↔NFRC flip persistence (G2b); CEN value display; SHGC↔g-Factor label switch and OITC/Rw value-blanking by displayed standard; coated-lite label correctness on unequal VIG panes (D11); silent gas-fill fallback; Air/Argon coverage; empty-coating guard (via cascade-clear path); full cleared-selection contract incl. render placeholder and label reset; upstream-disable defense (C4); disabled 6/4 VIG option in Inboard; unreachable new products; runtime JS errors; manufacturer prefix; all-Starphire display contract; CEN data integrity; matrix entries that reference nonexistent combinations or stale CEN expectations (caught at pre-flight by `preflight.py`, not mid-run).

**Doesn't catch:** visual fidelity, color perception, font/layout; CEN dimmed-label opacity; true render-loop races (S2/S3 approximate); print styles; animation timing; alternate viewports; whether cleared-selection is the *desired* UX (the plan asserts it as the contract — that's a product decision).

## 8. Coverage sanity check

64 cases + pre-flight + 3 stress sub-cases exercise: every coating shortcode (14); **every substrate in the data (8 — B8/B9 close the Solexia/Solargray gap; OptiblueZ50/Z75 exist only in the app's name map, not in any dataset)**; every manufacturer (3, in H1); all 4 Plus cascade nodes as both upstream and downstream; every toggle flipped ≥2× **plus the two 2026-07-11 state regressions (F4/F5)**; CEN auto-flip in all three tabs (G3/G5/G7); both maker-rule edges in outboard (G6 Vitro-block negative, G8 S5-SG-alone positive); manual flip persistence (G2b); CEN values for 4 Saint-Gobain coatings; Air and Ar90 round-trip-verified in both Plus cascades; every thickness-restricted coating; both cascade directions; empty-coating guard (transitive); all three summary formats character-for-character; full cleared-selection contract with recovery; upstream-disable defense; coated-lite label on unequal VIG panes (D11); all-Starphire display contract.

## 9. Operational notes

**Estimated runtime:** ~15–18 minutes headed (64 cases + stricter pre-flight + placement-flip waits).

**Recommended phasing:**
1. **Phase 1** — `python "Automated Test/preflight.py"` (20 gates, no browser). **Human review checkpoint:** confirm the gate output and the G7/G8 rows before proceeding. (Run of 2026-07-11: 20/20 PASS.)
2. **Phase 2** — Single-config dry run (A1).
3. **Phase 3a** — Groups A, B, C, D.
4. **Phase 3b** — Groups E, F, G, H, then §5, then §6 assembly.

`/clear` between 3a and 3b if context pressure is visible.

**Spot-check protocol:** before trusting the final report, manually open three random screenshots and confirm they show what the report claims.

**Harness requirements:**
1. Chrome DevTools MCP installed
2. `python serve.py` in repo root (separate terminal)
3. `Automated Test/golden.json` populated (2026-07-11 capture; A9 uses the CEN schema with `toggleEnabled: true`; goldens now carry `cid` and `display_*` strings)
4. Naive predicate reimplementation in test runner (`preflight.py` has one to reuse)
5. Color card is a per-config render — `setAnchorImages(match.cid)` sets `#colorRenderImg.src` to `Anchor_Renders/<Folder>/anchor_<cid>.webp?v=<RENDER_V>` (`cid` 1-based zero-padded to ≥2; folder = the option's `data-folder`, `Overcast` or `PartlyClear`); assert the `src` reflects the golden `cid` and swaps between Overcast/Partly Clear per toggle option (default Overcast). On cleared selection the render must show the placeholder (§3a).
6. ≥250ms wait after any placement toggle flip (150ms intentional fade)
7. Plus-outboard predicate must key on `glass[0].substrate` (default Clear for Group E)
