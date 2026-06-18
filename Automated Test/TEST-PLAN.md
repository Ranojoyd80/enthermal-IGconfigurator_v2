# Test Plan — Enthermal Configurator UI Regression

> Unified plan (supersedes v1/v2/v3). Incorporates corrections from the two test runs on 2026-04-12 (commit 999cd6f) and 2026-04-14 (commit 45fc962).

## 0. Goals

Verify CSV → JSON → stack-based UI produces correct filter, match, and display output across the full product catalog. Focus areas:

- IG_Config 12-04-26 dataset migration (98 / 4748 / 2016 rows across enthermal / plus-inboard / plus-outboard)
- Data-driven CEN/NFRC toggle — **per-row `cen` field**, deterministically driven by whether the Saint-Gobain coating sits on Surface 2
- Simplified Comment format (2-token coatings on implied Clear, bare `Argon`/`Air`)
- New products: Optiblue substrate, Air gas-fill data
- Updated Plus summary format (exterior-to-interior reading order)
- **Cleared-selection behavior** when upstream changes invalidate the current combo (§3a)

## 1. Tooling & Setup

- **MCP server:** Chrome DevTools MCP, headed mode (default)
- **Server:** `python -m http.server --bind 127.0.0.1 8000` in repo root (separate terminal — must stay running)
- **Target:** `http://127.0.0.1:8000/enthermal-configurator.html`
- **Ready check:** `document.querySelector('#outerCoating').options.length > 1`
- **Data access note:** `DATA`, `DATA_PLUS_IN`, `DATA_PLUS_OUT` are declared with `let` at top level and do not attach to `window`. Use `eval('DATA')` from inside an injected function to access them.

## 2. Pre-flight (gates the suite — any failure aborts)

1. **Availability matrix dump** for restricted-thickness products (SB72: 6mm only / Starphire only; SBR67: 5–6mm / Clear; SKN183: 6mm only / Clear / all CEN; XTR6129: 4 & 6mm / Clear / all CEN; LUMI: 4/5/6mm / Clear / all CEN; ZEN: 4/5/6mm / Clear / all CEN).

2. **Full-matrix config validation.** For every config in §4, the naive predicate must return a non-empty match against the JSON. Any config referencing a non-existent `(thickness, coating, substrate, gas, surface)` tuple aborts the run before any UI interaction. This closes the gap where runs silently "adjusted" expectations mid-run instead of catching mismatched matrix entries at the gate.

3. **Independent predicate cross-check.** Naive reimplementation must agree with the app's predicate on **every row** in all three JSONs (6,862 rows total, not just §4 configs). Mismatches: acceptable only for plus-outboard, where the tuple `(s2, outT, inT, monoT, s5, gas, surf)` is non-unique across 8 VIG-outer substrate variants (Clear, Starphire, Solexia, Solarbronze, Solargray, Optigray, Solarblue, Optiblue). Resolved by keying on `glass[0].substrate` — always `Clear` for §4 Group E configs.

4. **Golden-file anchors** (`Automated Test/golden.json`):
   - **NFRC anchors (A1, A13, D1, E1):** `uval`, `uvalIP`, `rval`, `shgc`, label `"SHGC"`, toggle `"NFRC"`, summary string.
   - **CEN anchor (A9):** `uvalCEN`, `gFactor`, label `"g-Factor"`, toggle `"CEN, locked"`, summary string. Do **not** record `uval`/`shgc` — the runner asserts those display as `"—"`.

5. **Console subscription armed.** Filter to `enthermal-configurator.html` source URL only. `error` and `warn` from app code fail the run. Whitelisted: browser favicon 404; the "No label associated with a form field" a11y info message (non-blocking, not from app logic).

6. **CEN field presence + integrity:**
   - Counts: enthermal **19/98**, plus-inboard **724/4748**, plus-outboard **358/2016**. Any deviation aborts.
   - Every row must satisfy `gFactor != null ⟺ uvalCEN != null`. Orphans = data bug, abort.
   - Every row must satisfy `row.cen === (uvalCEN != null)` — i.e. the `cen` flag is redundant with populated CEN values. Deviations = data bug, abort.
   - **CEN rule (tight form, verified 0 violations across 2016 plus-outboard rows):** `row.cen === (glass[0].coating ∈ {LUMI, ZEN, SKN183, XTR6129})`. Equivalently: CEN is true **iff** a Saint-Gobain coating sits on Surface 2. Coatings on S4 or S5 do not affect `cen`.

## 3. Per-config cycle

1. Narrate config. 2. Drive UI. 3. Read back via DevTools evaluate. 4. Compare to naive predicate + golden anchor. 5. Screenshot to `Automated Test/config-NN.png`. 6. Report-buffer entry.

### 3a. Cleared-selection contract

When an upstream change (outer thickness, substrate) invalidates the currently selected combination, `updateOuterCoatings()` **clears** the selection rather than auto-picking a replacement. The summary shows `"Select a product to view results."` and metric fields go blank.

This is the intended behavior. Group C and stress test S2 assert against this contract. If product owners later decide auto-pick is desired, this section and Group C must be updated together — they are the single source of truth for the expected UX of an invalidated selection.

**Important corollary (from run on 2026-04-14):** for *inner*-thickness changes, the app pre-disables invalid inner-thickness radios — the user cannot execute the invalid action in the first place. So the cleared-selection path is only reachable via outer-thickness changes. Group C verifies both behaviors: C1/C2 (valid upstream change retained), C3/C5 (outer change → cleared), C4 (inner radios correctly disabled — action unreachable).

**Verified fields**

| Field | Source of truth |
|---|---|
| Summary innerHTML | `match.stack` + display helpers |
| U-value SI (3 dec) | `match.uvalCEN` if `match.cen`, else `match.uval` |
| U-value IP / R-value | `match.uvalIP` / `match.rval` — must show `"—"` when `match.cen` |
| SHGC / g-Factor value | `match.gFactor` if `match.cen`, else `match.shgc` |
| SHGC label text | `"g-Factor"` if `match.cen`, `"SHGC"` if not |
| OITC / Rw values | Dual static columns (no label switch). `ENTHERMAL_ACOUSTIC` lookup; OITC value populated & Rw `"—"` in NFRC, reversed in CEN |
| Tvis %, RoutVis %, T-UV % | corresponding `match.*` |
| CEN/NFRC toggle | `checked` matches `match.cen`; `.locked` present when `match.cen` |
| Gas-fill round-trip | `match.gas` matches radio selection (catches silent Air→Argon fallback) |
| Cross-section labels | from `match.glass[i]` |
| Color card | Per-config render (`#colorRenderImg`) — `setAnchorImages(match.cid)` points it at `Anchor_Renders/<Sky>/anchor_<cid>.webp`; the sky toggle swaps `src` among Clear/Overcast/Cloudy for that `cid` (default Overcast). **No per-config L/a/b readout or flip** — that UI was removed. |
| Dropdown option set | unique coatings at current thickness |
| Cascade disabled state | predicate |

---

## 4. Test Matrix — 52 configs in 8 groups

All matrix entries are validated against the JSON during pre-flight (§2.2). Historical errors caught by prior runs and corrected here: E7 (was 4/5 — no such asymmetric VIG in data), D8 vigThk (5/4 not 4/5), D9 vigThk (4/4 not 5/5), E6 CEN expectation (NFRC, not CEN — S2=SB70 is not SSG), E8 monoT + CEN expectation (monoT=6, NFRC).

### Group A — Enthermal happy path (14)

A1 C366 6/6 NFRC **golden** • A2 C180 4/4 • A3 C270 4/4 • A4 C272 4/4 • A5 C340 4/4 • A6 Q452 4/4 • A7 SB60 4/4 • A8 SB70 4/4 • **A9 LUMI 4/4 CEN golden** • A10 ZEN 4/4 CEN • A11 XTR6129 4/4 CEN • A12 SKN183 6/4 CEN (6mm only) • **A13 SB72 6/4 NFRC golden** (Starphire, 6mm only) • A14 SBR67 5/4 (5–6mm only).

### Group B — Enthermal non-Clear substrates (7)

B1 SB60/Starphire 6/4 • B2 SB60/Starphire 5/5 • B3 SB60/Optiblue 6/4 • B4 SB60/Optigray 6/5 • B5 SB60/Solarblue 6/6 • B6 SB60/Solarbronze 6/4 • B7 SB72/Starphire 6/6.

### Group C — Cleared-selection cascade (5)

| # | Setup | Action | Expected (per §3a contract) |
|---|---|---|---|
| C1 | C366/4/4 | outer→6 | Combo still valid → C366 retained, inner unchanged, summary populated |
| C2 | Q452/4/4 | outer→5 | Combo still valid → Q452 retained, summary populated |
| C3 | SB60/Starphire/5/5 | outer→4 | Combo invalid → **selection cleared**, summary shows `"Select a product to view results."`, metrics blank, no console errors |
| C4 | C340/4/4 | *attempt* inner→5 | Action unreachable: inner=5 and inner=6 radios are disabled by the app (C340/4 only exists at inner=4). Test asserts `inner.disabled === true` for the invalid options — **verifies the UI's upstream-disable defense**, which prevents the cleared-selection path from being reached via inner-thickness changes. |
| C5 | SKN183/6/4 | outer→4 | Combo invalid (SKN183 is 6mm-only) → **selection cleared**, same expectations as C3 |

### Group D — Plus Inboard (10)

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

### Group E — Plus Outboard (8) — VIG-outer substrate implicitly Clear for all entries

| # | VIG | S2 | mono t | S5 | Gas | CEN expect | Notes |
|---|---|---|---|---|---|---|---|
| E1 | 5/5 | C366 | 4 | C366 | Ar90 | NFRC | **golden** |
| E2 | 4/4 | C366 | 4 | C366 | Ar90 | NFRC | min |
| E3 | 6/6 | C366 | 6 | C366 | Ar90 | NFRC | max |
| E4 | 5/5 | C270 | 4 | C272 | Ar90 | NFRC | S2≠S5 |
| E5 | 5/5 | C366 | 4 | C366 | Air | NFRC | gas round-trip |
| E6 | 5/5 | SB70 | 5 | LUMI | Ar90 | NFRC | S2 not SSG → NFRC despite LUMI on S5 |
| E7 | 5/4 | C366 | 4 | C366 | Ar90 | NFRC | asym VIG (outer ≥ inner; only 5/4, 6/4, 6/5 exist) |
| E8 | 6/6 | C366 | 6 | SKN183 | Ar90 | NFRC | only exists at monoT=6; S2 not SSG → NFRC |

### Group F — Placement toggle (3)

F1 Inboard→Outboard reseed • F2 E6→Inboard reseed • F3 3× flip (state-leak only).

**Harness requirement:** the placement toggle uses a **150ms `setTimeout` fade** ([enthermal-configurator.html:1313](../enthermal-configurator.html#L1313)) before re-seeding the cascade. A synchronous DOM read after clicking `posToggleInput` captures stale state. Wait **≥250ms** after any placement flip before reading the summary/metrics.

### Group G — CEN/NFRC toggle (7)

The §3a clarification states CEN is driven by the matched row's `cen` field, which equivalently is driven by whether the S2 coating is Saint-Gobain. G6 is a **negative test** (no-flip on coating identity alone when S2 is not SSG). G7 is the **positive test** using a row where S2 genuinely carries an SSG coating.

| # | Tab | Test | Expected |
|---|---|---|---|
| G1 | Enthermal | C366/4/4 | NFRC, locked; U/R visible |
| G2 | Enthermal | LUMI/4/4 | S2 SSG → CEN locked; `"g-Factor"` label; uvalIP/rval = `"—"` |
| G3 | Enthermal | C366→LUMI→C366 | NFRC↔CEN both directions, driven by per-row `cen` |
| G4 | Plus Inboard | D4 (LUMI S2) | S2 SSG → CEN locked, g-Factor |
| G5 | Plus Inboard | D1→D4 | NFRC→CEN on S2 change (C366→LUMI) |
| **G6** | **Plus Outboard** | **E1 → E6** | **No flip expected** — both rows have S2 ∉ SSG set (C366 / SB70). **Negative test:** toggle must NOT flip on S5 LUMI alone. If it flips, coating-identity-vs-S2-driven logic is broken. |
| **G7** | **Plus Outboard** | **E1 → (VIG 4/4, S2=LUMI, S5=LUMI, mono 4mm, Ar90, Clear)** (plus-outboard.json idx=62) | **Positive test:** toggle flips to CEN. Confirms outboard auto-flip works when S2 is genuinely SSG. Row's `uvalCEN=0.325017`. |

### Group H — Cross-cutting (3)

| # | Purpose |
|---|---|
| H1 | Manufacturer prefix audit — all dropdown entries match `/^(Cardinal\|Vitro\|Saint-Gobain) /`; cross-section spans must NOT match (they show bare names like "Clear 4mm" or "LoE³ 366"). |
| H2 | Summary rendering — Enthermal, Inboard, Outboard, character-for-character against expected innerHTML. |
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
Pass: result must be `"Select a product to view results."` — asserts the §3a contract, not "either/or".

**S3 — Placement-toggle interleave:** Re-run S1 3× with placement flipped between iterations. Must wait ≥250ms after each placement flip (see Group F harness note). Pass: no cleared states, no stale summaries, uval populated throughout.

---

## 6. Report Format

```markdown
# Test Report — <ISO date> — commit <sha>
## Summary
- Pre-flight: PASS/FAIL (matrix, full-matrix validation, predicate, goldens, console, CEN integrity)
- Configs: 52 — Passed N — Failed N — Plan corrections needed: N
- Console errors: N (favicon + a11y-label whitelisted)
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

**Catches:** filter predicate bugs (naive + golden, independently); display drift; cascade resets; S4/S5 surface; placement state leaks; CEN auto-flip driven by S2 SSG identity; CEN value display; SHGC↔g-Factor label switch and OITC/Rw value-blanking by mode; silent gas-fill fallback; Air/Argon coverage; empty-coating guard (via cascade-clear path); cleared-selection contract violations; upstream-disable defense (C4); unreachable new products; runtime JS errors; manufacturer prefix; glass color fallback; CEN data integrity; matrix entries that reference nonexistent combinations (caught at pre-flight, not mid-run); coating-identity vs S2-driven CEN flip bugs (G6 negative test).

**Doesn't catch:** visual fidelity, color perception, font/layout; CEN dimmed-label opacity; true render-loop races (S2/S3 approximate); print styles; animation timing; alternate viewports; whether cleared-selection is the *desired* UX (the plan asserts it as the contract — that's a product decision).

## 8. Coverage sanity check

52 configs + pre-flight + 3 stress sub-cases exercise: every coating shortcode (14); every substrate (8 inc. Optiblue); every manufacturer (3, in H1); all 4 Plus cascade nodes as both upstream and downstream; every toggle flipped ≥2×; CEN auto-flip in all three tabs (G3/G5/G7); CEN negative test in outboard (G6); CEN values for 4 Saint-Gobain coatings; Air and Ar90 round-trip-verified in both Plus cascades; every thickness-restricted coating; both cascade directions; empty-coating guard (transitive); both summary formats; cleared-selection contract; upstream-disable defense.

## 9. Operational notes

**Estimated runtime:** ~13–16 minutes headed (52 configs + stricter pre-flight + placement-flip waits).

**Recommended phasing:**
1. **Phase 1** — Pre-flight only. **Human review checkpoint:** confirm §2.2 full-matrix validation output and G7's identified row before proceeding.
2. **Phase 2** — Single-config dry run (A1).
3. **Phase 3a** — Groups A, B, C, D.
4. **Phase 3b** — Groups E, F, G, H, then §5, then §6 assembly.

`/clear` between 3a and 3b if context pressure is visible.

**Spot-check protocol:** before trusting the final report, manually open three random screenshots and confirm they show what the report claims.

**Harness requirements:**
1. Chrome DevTools MCP installed
2. `python -m http.server --bind 127.0.0.1 8000` in repo root (separate terminal)
3. `Automated Test/golden.json` populated (A9 uses CEN schema)
4. Naive predicate reimplementation in test runner
5. Color card is a per-config render — `setAnchorImages(match.cid)` sets `#colorRenderImg.src` to `Anchor_Renders/<Sky>/anchor_<cid>.webp`; assert the `src` reflects `match.cid` and swaps among Clear/Overcast/Cloudy per toggle option (default Overcast). The old per-config L/a/b readout and flip have been removed.
6. ≥250ms wait after any placement toggle flip (150ms intentional fade)
7. Plus-outboard predicate must key on `glass[0].substrate` (default Clear for Group E)
