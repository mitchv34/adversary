# Placebo cookbook

The placebo test is the highest-value single technique in adversarial review. Three of five fatal
findings in the reference run were caught only by placebo. The principle:

> **Feed the analysis noise, a neutralised input, or corrected units, and check whether the result
> politely disappears. If it survives randomisation, it was never in the data.**

But a placebo alone only proves the pipeline **can** return nothing. The complete discipline is:

> **Noise in → null out. AND signal in → signal out.**

A pipeline that cannot recover a *planted* effect cannot be trusted when it reports a real one. Run
both directions. Every quantitative persona must construct at least one of each for any headline
claim, and should *predict the outcome in advance* from the construction — a placebo whose result you
derived beforehand is the strongest evidence there is.

---

## Part 1 — The four canonical placebos

### 1. Shuffle the treatment
Permute the treatment/key variable **within the suspect block** (or globally), holding everything
else fixed, and re-run.
- **Kills:** effects driven by the *structure* of appending/merging a block rather than by the
  treatment's values; mechanical artifacts of leverage or sample composition.
- **Under a real effect:** the coefficient collapses toward zero.
- **Under an artifact:** the coefficient *survives* the shuffle — the tell that the treatment's value
  never mattered.

### 2. Neutralise the outcome
Replace the outcome with its baseline, a constant, or its group mean — remove the signal, keep the
apparatus — and re-run.
- **Kills:** effects carried by an assigned or imputed outcome level rather than real variation.
- **Reference run:** neutralising an assigned outcome level made 90% of the claimed effect vanish
  while everything else was held fixed.

### 3. Rescale to the correct units
When two quantities are combined, compared, or regressed, put them on the **same scale** and re-run.
- **Kills:** raw-score-vs-percentile / level-vs-change / share-vs-count / different-denominator
  errors — the most common fatal class.
- **Tell-tale signature:** a variable with **mean ≈ 0.5 and sd ≈ 0.2887** is a uniform rank
  (`Uniform(0,1)` has sd `1/√12 ≈ 0.2887`), not a raw score — it carries ordering, no magnitude.
- **Under a scale error:** the effect changes sign, magnitude, or vanishes once both sides match.

### 4. Swap in a random covariate of the same shape
Replace the key regressor with a random variable of matching shape and support, and re-run.
- **Kills:** effects any variable of that shape would produce (overfitting, off-support
  extrapolation, degrees-of-freedom artifacts).

---

## Part 2 — The inverse: positive controls

**Signal implantation.** Implant an effect of *known magnitude* into synthetic or scrambled data and
verify the pipeline recovers the right sign, roughly the right magnitude, and nominal CI coverage.
- **Catches:** sign errors, unit errors, silent join breakage, dead code paths, over-aggressive
  filtering — a pipeline that *cannot find anything*.
- Always paired with Part 1. A pipeline that passes the placebo but fails the positive control is
  broken in the opposite direction, and nobody would have noticed.

**Null-model / do-nothing baseline.** Submit the most degenerate possible input and see what score it
earns: an agent that takes no action, the empty string, a constant response, majority class,
metadata-only prediction. **Any non-trivial score is a hard stop** — the metric is measuring
something other than the capability claimed.
- *Evidence it works:* a do-nothing agent passes 38% of TAU-bench airline tasks; a constant
  instruction-ignoring response reaches 86.5% length-controlled win rate on AlpacaEval 2.0.

**Negative-control outcome / exposure.** Substitute an outcome the mechanism *cannot plausibly
affect* (or an exposure that cannot cause the outcome), change nothing else, and report the estimate
beside the main one.
- **Beats a random-noise placebo** precisely because the negative control **shares the confounding
  structure** — a nonzero estimate indicts the design in a way noise never will.

---

## Part 3 — Randomisation done correctly

**Full-pipeline permutation.** Permute the outcome/label/assignment B ≥ 1,000 times and, for **each**
permutation, re-run the *entire* pipeline — including preprocessing, feature selection,
hyperparameter search, and any tuning. The empirical p-value is the fraction of permutations scoring
at least as well as the observed result.

> **The critical detail:** anything left outside the loop leaks into the null and makes the test pass
> spuriously. A permutation test that only re-runs the final model is not a permutation test.

Report the permutation p alongside the model p; a large gap is itself the finding.

**Drop-a-little-data (AMIP).** Compute the smallest fraction of observations or clusters whose removal
flips the sign, kills significance, or changes the decision. Report that fraction as a headline
statistic.
- **Benchmark:** several published economics results overturn on **<1%** of the sample. This
  sensitivity does *not* shrink asymptotically and is invisible in the standard errors.

**Specification curve / multiverse.** Enumerate the theoretically justified, statistically valid,
non-redundant specifications; plot the ordered estimates with the decision matrix beneath so the
consequential fork is visible; test jointly against a permutation null. The deliverable becomes the
curve, not the point.

**Uniformity of null p-values.** Collect every comparison that *should* be null — baseline balance
tables, A/A splits, pre-period differences, placebo cells — combine them (Stouffer/Fisher) and test
for uniformity. **Suspicion attaches to both tails:** an excess near 0 means the split is broken; an
excess near 1 means the variation is too small to be real sampling.

**A/A test + sample-ratio-mismatch.** Run the whole pipeline on two random halves of the *same*
condition and require the null — the literal placebo test of measurement infrastructure. Separately,
chi-square the observed allocation against the intended one. SRM appears in **6–10% of all A/B
tests**.

---

## Part 4 — Perturbation and ablation

**Mutation / perturb-an-input** *(the engineering twin of the placebo)*. Deliberately corrupt one
thing — flip a sign, scale a column by 10, null a required field, shuffle a key — and check whether
**any** test, alert, dashboard, or reported number moves. If nothing moves, every check downstream of
it is decorative. Coverage cannot detect this; perturbation can.

**Cue ablation, both directions.** (a) Remove or mask the feature the story depends on and confirm the
result *dies*; (b) run using **only** the suspected nuisance cue (source, length, formatting,
timestamp, ID) and confirm it *cannot* reproduce the result. Both are required — either alone is easy
to pass.

**Split-swap re-evaluation.** Re-split strictly by time (train ≤ t, test > t) and separately by group
key (firm, person, document family), re-run end to end, and report the delta against the original
split. A large drop is the leak. These are the two leakage types that most reliably survive code
review.

**Seed-only ensemble.** Re-run k ≥ 10 times varying only the random seed, confirm iid performance is
near-identical, then evaluate all k on the stress/subgroup condition and report the **spread on the
stress condition**, not the iid mean.

---

## Part 5 — Artifact-level analogues (no source data required)

These are the client-facing and forensic twins of the placebo — procedures whose output is a **diff**,
not an opinion.

**Internal-consistency recomputation.** Recompute every derived figure from its own displayed
components — shares from counts, growth from levels, per-capita from numerator and denominator, index
from base, means from N. Foot and cross-foot every table. Check that a reported mean is arithmetically
*reachable* given N and scale granularity, and that test-statistic/df/p triples reconcile. **Requires
zero data or code access** — run it on a PDF before touching the repo.

**Recompute-and-diff (the tie-out).** Enumerate every numeral into a register of
`{value, location, claimed source}`, re-execute each named computation in a clean environment, and
diff at the displayed precision. A number with no named source is an automatic finding.

**Honest replot and impression diff.** Re-render the chart with zero baseline, full available series,
single axis, neutral aspect ratio. Write the one-sentence takeaway from each version and **diff the
sentences, not the images**. Do not accept "we labelled the truncation" as mitigation — the perceptual
effect survives explicit indicators.

**Title-blind / data-blind split read.** Produce two stripped versions of each exhibit — encoding with
the title removed, title with the encoding removed — and elicit a takeaway from each independently.
Any divergence is a finding, and the *title's* version is what readers retain.

**Qualifier survival trace.** Build a matrix: rows = every qualifier attached to the finding where it
is first stated; columns = methods → results → body → exec summary → deck → press release. Mark each
cell present/absent. Every qualifier that dies before the last populated column is a finding, ranked
by whether its absence changes the reader's decision.

**Differencing attack on published cells.** For every suppressed cell, attempt reconstruction four
ways: subtract published cells from published margins; combine two tables sharing a dimension;
difference this release against a prior release; difference two published cuts of the same universe.
Any success means complementary suppression is insufficient.

**Clean-room regeneration.** From the shipped artifact only, with no contact with the author,
regenerate every reported number. Time-box it and **record exactly where you stalled — the stall point
is the defect**, not the eventual success.

**Worst-faith read.** Adopt a hostile outlet with a word limit and produce three headlines and three
pull-quotes that are verbatim accurate and in context. For each, write the correction the institution
would have to issue. This is the only technique here whose output is a *prediction* rather than a
diff, so it requires the strictest "quote the exact source sentence" discipline to stay falsifiable.

---

## Using a placebo as evidence

1. **State the design before running it** — which variable is neutralised, at what scale, over which
   block.
2. **Derive the expected outcome** from the construction where you can. A placebo whose result was
   predicted in advance converts an assertion into a proof.
3. **Report the number**, not the verdict: "with the treatment shuffled 1000×, the coefficient was
   0.02 (95% CI −0.11, 0.14) vs the claimed 0.31."
4. **Run the positive control too**, and say so. "Noise in → null out" alone is half a proof.
5. A result that **survives** a correct placebo is genuinely strengthened — placebos protect the
   survivors, not just the retractions.
