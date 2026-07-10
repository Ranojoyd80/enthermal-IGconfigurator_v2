# Test Report — 2026-07-11 — app commit 5273ebb, plan commit 474dac3

> Run 3 of the UI regression suite, first run against the revised plan (07-07-26 dataset,
> corrected CEN maker-set rule, extended §3a contract). Runner: Chrome DevTools MCP,
> headed, `python serve.py`. Prior runs are documented in [TEST-REPORT.md](TEST-REPORT.md)
> (historical record).

## Summary

- **Pre-flight: PASS** — `preflight.py` 20/20 gates (counts, CEN rule + covariance, match-key uniqueness, cid/render inventory, 45-entry matrix validation incl. per-entry CEN expectation, golden-vs-data anchors). Console subscription armed.
- **Cases: 64 — Passed 64 — Failed 0** — App failures: **0** — Data failures: **0** — Plan corrections needed: **0**
- **Runner-harness corrections: 2** (naive-predicate bugs in the test harness itself; documented below, plan clarified for one)
- **Console errors: 0** from app code across the whole run (only the whitelisted a11y label issue, count 4 — the radio-group captions)
- **Stress S1/S2/S3: PASS / PASS / PASS**

## Group results

| Group | Cases | Result | Notes |
|---|---|---|---|
| A — Enthermal happy path | 14 | 14 PASS | A1/A9/A13 also matched golden.json exactly (values, display strings, summary, toggle state, cid) |
| B — non-Clear substrates | 9 | 9 PASS | Incl. new B8 Solexia / B9 Solargray. Starphire display contract verified (inboard label "Starphire 4mm", B1) |
| C — cleared-selection cascade | 5 | 5 PASS | C3/C5 verified the **extended §3a contract**: summary + metrics + render placeholder + cross-section labels all clear; C5 recovery restores everything. C4 upstream-disable defense holds |
| D — Plus Inboard | 11 | 11 PASS | Incl. D11 coated-lite label on unequal 5/4 VIG: "Clear 5mm" under S4, "Clear 4mm" under S5. D1 golden matched. Gas round-trip verified (D3) |
| E — Plus Outboard | 8 | 8 PASS | **E8 confirmed CEN in the live UI** — the corrected maker-set expectation held. E1 golden matched. Gas round-trip verified (E5) |
| F — placement & tab state | 5 | 5 PASS | Incl. the two 2026-07-11 regressions: F4 S4/S5 round-trip desync (toggle==radio==summary after Inboard→Outboard→Inboard) and F5 Vitro VIG retention across a tab round-trip |
| G — CEN/NFRC toggle | 9 | 9 PASS | G2b manual CEN↔NFRC flip round-trip; G6 Vitro-block negative (no flip); G7 uvalCEN 0.325 confirmed; **G8 S5-SG-alone flipped to CEN (0.253 / g 0.252)** — the discriminator that proves the maker-set rule is what the app implements |
| H — cross-cutting | 3 | 3 PASS | H1 manufacturer prefixes in all 3 dropdowns, bare names in cross-section; H2 all three summary formats char-for-char vs goldens (also asserted on every individual config); H3 placeholder options disabled |

## Stress

- **S1** rapid outer-thickness cycling (no awaits): final state internally consistent, dropdowns populated, no errors.
- **S2** synchronous cleared-selection read: summary is exactly `"Select a product to view results."` at the synchronous read; follow-up read confirmed the full extended contract (render placeholder shown, cross-section labels `"—"`).
- **S3** rapid mono-thickness cycling × 3 with placement flips between iterations: no cleared states, no blank metrics, no stale summaries.

## Failure categorization (per §6 discipline)

No app or data failures. Two mid-run mismatches were **runner-harness bugs**, fixed in the harness and re-run — the plan matrix itself needed no corrections:

1. **B3–B6/B8/B9 summary expectation (harness):** the naive formatter labeled the inboard lite with the *config's* substrate; the app (correctly, per data) shows the matched row's inner-lite substrate, which is Clear for every tinted-exterior config. Data confirmed inner lites are Clear on all six; expectations regenerated from the matched row; all pass.
2. **Group E surface-control assertion (harness, plan now clarified):** the runner asserted a "locked S5 toggle" in Outboard; the app hides the Coating Surface field entirely and forces the hidden radio to S5. All other assertions in the affected cases had already passed. Plan §4 Group E now documents the correct assertion.

## Golden anchors

All five (A1, A9, A13, D1, E1) matched on every recorded field: JSON-precision values, display strings, summary innerHTML, toggle state/enablement, and render `cid` (A1→anchor_07, A9→anchor_10, A13→anchor_198, D1/E1→anchor_19).

## Operational notes

- CDP `Page.captureScreenshot` timed out intermittently on the long-lived mutated page; captured `run-2026-07-11/config-A1.png` and `default-postrun.png`, but per-config screenshots were skipped for most cases. All pass/fail evidence is DOM-read assertions (values quoted above), not visual. If per-config screenshots matter for the archive, re-run with a fresh page per group.
- Runtime ≈ 9 minutes (in-page harness batches per group; faster than the ~15-18 min estimate).
- The `let DATA` / `eval('DATA')` access note in §1 was not needed — the harness fetched the JSON independently (same-origin), which is also the stronger independence guarantee.
