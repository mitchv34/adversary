# adversary

A Claude Code plugin for **adversarial review that bites, not flattery**. It turns "I think this
work might be wrong" into a prioritised, evidence-backed fix plan.

The failure mode it targets is *plausible but wrong* — research code, data pipelines, empirical
claims, design docs — not "throws an exception". It is not a linter, not a test runner, not a CI
gate, and not a replacement for human review. It is a machine for **generating the agenda** for
human review.

## The three-phase loop

```
  /adversary:review  ─────────►  /adversary:annotate  ─────────►  /adversary:fixplan
  pick reviewers,                open the HTML report in           read the annotations,
  run them in parallel,          Plannotator, collect              emit a tiered plan +
  render an HTML report          the reader's comments             patch the source docs
```

- **`/adversary:review`** — pick N reviewer personas (or accept the recommended set for the target
  type). Each runs as an *independent, parallel* subagent with its own hostile mandate. Findings are
  merged, deduplicated, and — where the renderer is available — rendered as a self-contained HTML
  report with LaTeX derivations.
- **`/adversary:annotate`** — open the report in [Plannotator]'s annotation UI and comment on
  specific findings. *(Phase 2 — not built yet.)*
- **`/adversary:fixplan`** — merge annotations with findings into a tiered action plan ordered by
  (credibility gained) / (effort), plus an errata document. *(Phase 3 — not built yet.)*

## Why it works (the load-bearing rules)

These are the non-obvious lessons from the manual run the plugin is derived from. Drop any and it
produces flattery instead of review:

1. **Independence is the whole mechanism.** Reviewers run in parallel with *no shared context* and
   never see each other's output. Value comes from *collision* — two mandates independently reaching
   the same conclusion establishes it.
2. **Verify, don't read.** Every persona recomputes the numbers it relies on and shows its work. A
   reviewer that only reads produces opinions; one that recomputes produces findings.
3. **The placebo test is the highest-value technique.** Feed the analysis noise / a shuffled input /
   corrected units and check whether the result politely disappears. If it survives randomisation, it
   was never in the data.
4. **Demand deletions, not suggestions.** Personas quote the exact sentences they would force the
   author to delete or soften.
5. **Require the survivors.** Every persona states what passed scrutiny and is safe to build on — the
   honesty check on the reviewer.
6. **Verdict, not a score.** One line naming what is publishable/shippable versus what is not.

## Current status

This repo is being built in stages. **Phase 1 (`/adversary:review`) core pipeline** is the current
scope: reviewer selection, parallel dispatch, merge to `findings.json`, validated against a
planted-error fixture. The HTML render delegates to the `visual-explainer` skill when it is
installed. Phases 2–3 and the remaining persona library are planned but not yet built — see
`specs/SPEC.md` for the full design.

## Layout

```
adversary/
├── .claude-plugin/plugin.json
├── skills/adversary-review/SKILL.md   # phase 1 orchestrator
├── agents/                            # one hostile persona per file
├── references/                        # persona library, placebo cookbook, report structure
└── fixtures/planted-error/            # ground-truth validation artifact
```

## Install

Register this directory as a local plugin in Claude Code, then `/adversary:review` (and, once built,
`:annotate` / `:fixplan`) become available. Users can add their own personas by dropping an agent
file in `agents/`.

[Plannotator]: #
