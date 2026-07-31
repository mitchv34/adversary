# adversary

A Claude Code plugin for **adversarial review that bites, not flattery**. It turns "I think this
work might be wrong" into a prioritised, evidence-backed fix plan.

The failure mode it targets is *plausible but wrong* — research code, data pipelines, empirical
claims, reports, design docs — not "throws an exception". It is not a linter, not a test runner, not a
CI gate, and not a replacement for human review. It is a machine for **generating the agenda** for
human review.

## The three-phase loop

```
  /adversary:review  ─────────►  /adversary:annotate  ─────────►  /adversary:fixplan
  pick reviewers,                annotate findings in the         read the annotations,
  run them in parallel,          self-annotating report,          emit a tiered plan + errata,
  render an HTML report          export annotations.json          (--apply patches the sources)
```

- **`/adversary:review [target] [--reviewers a,b,c] [--depth quick|standard|deep]`** — pick reviewer
  personas (or accept the recommended set for the detected target type). Each runs as an *independent,
  parallel* subagent with its own hostile mandate; findings are merged, corroboration-marked, and
  rendered as a self-contained HTML report with LaTeX derivations from a **bundled template** —
  no external skill required.
- **`/adversary:annotate [report.html]`** — the report is **self-annotating**: per-finding verdict
  chips (`accept · reject · already-handled · downgrade · upgrade · expand`) + comments, exported as
  `annotations.json`. `plannotator` is a fallback for line-anchored comments on arbitrary passages.
- **`/adversary:fixplan [--apply]`** — merge annotations with findings into a tiered action plan
  ordered by (credibility gained) ÷ (effort), plus an `ERRATA.md`. `--apply` patches corrected claims
  inline into the source docs (marked `[CORRECTED — see ERRATA E#]`, never silently) and opens a
  review of the diff.

## Why it works (the load-bearing rules)

Drop any of these and it produces flattery instead of review:

1. **Independence is the whole mechanism.** Reviewers run in parallel with *no shared context* and
   never see each other's output. Value comes from *collision* — two mandates independently reaching
   the same conclusion **corroborates** it (a strong signal, not proof).
2. **Verify, don't read.** Every persona recomputes the numbers it relies on and shows its work.
3. **Placebo + positive control.** Feed the analysis noise / a shuffled input / corrected units and
   check the result disappears; then confirm a *planted* effect is recovered. Noise in → null out
   **and** signal in → signal out.
4. **Demand deletions, not suggestions.** Personas quote the exact sentences to delete or soften.
5. **Require the survivors.** Every persona states what is safe to build on — the honesty check.
6. **Verdict, not a score.** One line naming what is publishable/shippable versus what is not.

## Personas

22 hostile personas across six families (quantitative/inferential, data/measurement/ML, claims &
deliverable, exposure & risk, engineering, domain & synthesis) — see `references/reviewers.md` for the
library and the target-type → recommended-set matrix. Each persona is an agent file, so **you can add
your own** by dropping a `<name>.md` into `agents/`; it appears in the picker automatically.

## Status & validation

All three phases and the 22-persona library are built. The pipeline is exercised against a
**planted-error fixture** (`fixtures/planted-error/`) with a known raw-vs-percentile scale error. On
the recorded run an **un-seeded** reviewer (`auditor-data-integrity`, whose mandate does not name the
flaw's fingerprint) discovered the error cold; a **seeded** reviewer (`referee-measurement`, whose
mandate does name the `mean 0.5 / sd 0.2887` signature) serves as a *positive control*. The discovery
claim rests on the un-seeded catch — the seeded catch only proves the plumbing.

The plugin has also been run **on its own repo** (dogfood): three blind reviewers found real bugs,
including a fatal annotation-handoff defect, which were then fixed. See `specs/SPEC.md` for the full
design; the manual "reference run" it cites was an un-committed session (recollection, not in-repo
evidence).

## Layout

```
adversary/
├── .claude-plugin/plugin.json + marketplace.json
├── skills/
│   ├── adversary-review/SKILL.md      # phase 1 orchestrator
│   ├── adversary-annotate/SKILL.md    # phase 2 (self-annotating report; plannotator fallback)
│   └── adversary-fixplan/SKILL.md     # phase 3 (tiered plan + errata, --apply)
├── agents/                            # 22 hostile personas, one per file (§0 shared rules baked in)
├── references/                        # reviewers.md, placebo-cookbook.md, report-structure.md, report-shell.html, annotation-layer.html
├── fixtures/planted-error/            # ground-truth validation artifact
└── scripts/check_shared_rules.py      # asserts §0 is identical across all personas
```

## Install (local)

The repo doubles as a single-plugin marketplace (`.claude-plugin/marketplace.json`). In Claude Code:

```
/plugin marketplace add ~/Projects/adversary
/plugin install adversary@adversary
```

Then `/adversary:review`, `/adversary:annotate`, `/adversary:fixplan` are available. To share with a
colleague, push the repo and have them `/plugin marketplace add <git-url>` then the same install.

**No external dependencies for the full loop.** The HTML report and its self-annotating layer render
from a bundled shell (`references/report-shell.html` + `annotation-layer.html`). Optional *enhancers*:
the `visual-explainer` skill (richer report styling) and the `plannotator` CLI (line-anchored
annotation fallback) — install neither to get the complete review → annotate → fixplan loop.

## Verifying the build

```
python3 scripts/check_shared_rules.py          # §0 identical across all 22 personas
python3 fixtures/planted-error/make_fixture.py  # regenerate the fixture (deterministic)
```
