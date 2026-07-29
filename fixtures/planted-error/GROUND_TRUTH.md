# Ground truth — planted-error fixture

> **Do NOT include this file, or `make_fixture.py`, in the review target.** Dispatch reviewers at
> `fixtures/planted-error/target/` only. A reviewer that reads this file has been handed the answers
> and the validation run is void.

This fixture exists to answer one question the spec (§8) insists on: *does the review pipeline
actually find a flaw we know is there?* A review pipeline never tested against ground truth has
exactly the problem it exists to detect.

## What is planted

### Flaw 1 — scale error: a percentile rank interpreted as dollars *(fatal)*

`wage_index` is a **percentile rank in [0,1]**, not a wage level. `data/DICTIONARY.md` documents it
as "metro average annual advertised wage, in units of \$10,000", and `analysis.py:44-48` converts
the fitted slope to dollars by multiplying by 10,000. The variable carries **ordering only, no
magnitude**, so every dollar figure derived from it is meaningless — including the headline.

**Signature a reviewer should catch:** `wage_index` has **mean = 0.5000, sd = 0.2886**, min 0.0083,
max 0.9917 — the fingerprint of a uniform rank (`Uniform(0,1)` has sd `1/√12 ≈ 0.2887`). It is also
absurd on its face: 0.5 in "$10,000 units" is a $5,000 average annual wage.

**Expected personas:** `referee-measurement` (scale compatibility is an explicit named check, with
the 0.5/0.2887 signature in its mandate), `auditor-data-integrity` (units and scale — "the
highest-yield check").

**Placebo that kills it:** rescale to correct units. There is no dollar scale recoverable from a
rank, so the correct conclusion is that the magnitude claim cannot be made at all — only an ordering
claim survives.

### Flaw 2 — tie-out failures: writeup numbers do not match the code *(high)*

`FINDINGS.md` reports three numbers that `analysis.py` does not produce:

| Claim in `FINDINGS.md` | Stated | Actual (`python3 analysis.py`) |
|---|---|---|
| Number of metros | **75** metropolitan areas | **60** rows in `postings.csv` |
| Dollars per 10-point AI increase | **$1,240** | **$743** |
| Correlation, AI intensity vs wage level | **0.61** | **0.4062** |

There is also an **internal** inconsistency: the brief says "$124 per year" per point and "$1,240"
per 10 points (consistent with each other), but then claims **$3,900** for a 25th→75th percentile
move. The interquartile range of `ai_skill_score` is **25.58** points (p25 = 29.59, p75 = 55.17),
which at $124/point is **$3,172** — a 23% overstatement. Detecting this needs the data (for the IQR)
but not the analysis code; the $124 ↔ $1,240 ↔ per-10-point chain can be checked with neither.

**Expected personas:** `auditor-tie-out` — Phase 1 (zero-access) should catch the internal
$124/$1,240/$3,900 inconsistency; Phase 2 (recompute-and-diff) should catch all three code-vs-writeup
mismatches. `auditor-data-integrity` may independently catch the row-count mismatch.

## What must SURVIVE

A review that condemns everything is miscalibrated. The **wage-growth** result is genuine and its
reported numbers tie out exactly:

- slope **0.035 pp** of additional YoY wage growth per AI point — matches `analysis.py` (0.03537);
- correlation **0.46** — matches (0.4624);
- the relationship is real in the data-generating process (`make_fixture.py` builds
  `wage_growth_pct = 1.6 + 0.035 * ai_skill_score + N(0, 1.1)`).

A reviewer should name this as safe to build on. Note it is still **correlational** — `editor-claims`
flagging "is a strong predictor" or the causal framing of the recommendation is a *legitimate*
finding, not a false positive.

## PASS criteria for the validation run

**PASS** requires, in the merged `findings.json`:

1. **At least one** finding naming the raw-vs-percentile scale error, **with recomputed numbers**
   (the mean ≈ 0.5 / sd ≈ 0.2887 signature, or the absurdity of the dollar conversion) — this is the
   primary gate from spec §8; and
2. **at least one** finding naming at least one of the tie-out mismatches with both the stated and
   the actual value.

**Strong pass** additionally has:

3. the scale error marked `corroborated: true` (reached independently by ≥2 reviewers);
4. the wage-growth result named in `survives[]`;
5. every finding carrying a usable `anchor`.

**FAIL** is any run where the scale error is not found. That is the flaw the reference run was built
around, and the personas name its exact signature — if the pipeline misses it, the pipeline is
broken, not the fixture.

## Regenerating

```bash
python3 fixtures/planted-error/make_fixture.py   # deterministic, seed 20260729, stdlib only
```

Regenerating rewrites `target/data/postings.csv` only. If you change the seed or the parameters, the
numbers in this file and in `target/FINDINGS.md` must be updated to match — the tie-out flaw depends
on `FINDINGS.md` disagreeing with the code by a *known* amount.
