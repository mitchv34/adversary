---
name: adversary-review
description: Run an adversarial review of analytical work. Selects hostile reviewer personas, dispatches them as independent parallel subagents that verify rather than read, merges and corroborates their findings, and renders a report. Use when you suspect work may be plausible but wrong — research code, data pipelines, empirical claims, client reports, design docs.
allowed-tools: Read, Grep, Glob, Bash, Task, AskUserQuestion, Skill, Write
---

# `/adversary:review [target] [--reviewers a,b,c] [--depth quick|standard|deep]`

Phase 1 of the adversary loop. Turns "I think this might be wrong" into a corroborated, evidence-backed
findings set.

**Target** may be a directory, a set of documents, a PR/diff, or a free-text description of the claim
under review. If omitted, infer from the conversation.

> **You are the orchestrator. You run in the main loop** — `AskUserQuestion`, parallel `Task`
> dispatch, and the `Skill` call all require it. Do not delegate this skill's own logic to a subagent.

---

## The rules that make this work — do not optimise them away

These are not stylistic. Each was learned from a run where dropping it produced flattery instead of
review.

1. **Independence is the whole mechanism.** Dispatch every reviewer in **one message with N
   concurrent `Task` calls**. Never pipeline. Never let reviewer N see reviewer N−1's output. The
   value comes from *collision* — when two mandates independently reach the same conclusion, the
   finding is established rather than arguable.
2. **Seed the suspicions.** You usually know where the bodies are buried. Hand each reviewer 3–5
   target-specific things to attack. This does not bias the review; it stops reviewers burning
   budget on easy wins and missing the fatal one.
3. **Do not defend your own artifact.** If you produced the work under review, you will be tempted to
   rationalise. When a reviewer is right, correct the document — do not argue. In the reference run
   the orchestrator's own headline result was retracted, and that was the correct outcome.
4. **Report the cost.** Estimate at selection time, report actual at the end.

---

## Step 1 — Scope the target

Read *enough* to identify:
- **(a) its type** — empirical/causal, LLM-coded dataset, predictive model, data pipeline, client
  report/deck, public release, published data product, code/service, design doc;
- **(b) the 3–5 claims that carry the most weight** — the ones that, if wrong, invalidate the work.

Keep this cheap. It is orientation, not analysis. Do not start reviewing here.

Note also whether a **prior specification exists** (preregistration, design doc, ticket, PRD) — if so,
`auditor-protocol-adherence` becomes near-deterministic and should be recommended.

---

## Step 2 — Select reviewers

**Do not skip this.** The choice of adversary is the user's most important lever.

### Build the candidate list from disk, not from memory
List `${CLAUDE_PLUGIN_ROOT}/agents/*.md` and read each file's frontmatter `name` + `description`.
This is the roster. A user who drops their own persona file into `agents/` gets it in the picker
automatically — that is the point of personas being agent files. Never offer a persona that has no
agent file; consult `${CLAUDE_PLUGIN_ROOT}/references/reviewers.md` for the selection matrix and the
family groupings.

### Present a family-grouped picker
`AskUserQuestion` allows **at most 4 questions × 4 options each**, so a flat list of the whole library
does not fit and would read badly anyway. Instead:

- Ask **one question per relevant family** (usually 2–3 families, never more than 4), each
  `multiSelect: true`, with ≤4 personas as options.
- Choose which families to surface from the detected target type. Reviewing a client deck should not
  surface engineering personas.
- **There is no "pre-tick" capability.** Convey the recommendation by putting recommended personas
  **first** in the option list and appending **`(Recommended)`** to the label. Say *why* in the option
  `description` so the user can override knowingly.
- The tool supplies an **"Other"** escape automatically — that is the "write your own persona" path.
  If the user takes it, treat their text as a custom mandate: assemble it with §0 (from
  `references/reviewers.md`) and dispatch it as a general-purpose `Task` rather than a named agent.

### Recommended sets by target type
| Target type | Recommended |
|---|---|
| Empirical / causal research | econometrics + measurement + data-integrity |
| Client report / deck / brief | tie-out + summary-fidelity + visual-argument |
| Public release / press / policy brief | hostile-reader + summary-fidelity + editor-claims |
| LLM-coded dataset → statistics | surrogate-labels + measurement + data-integrity |
| Predictive model / benchmark claim | leakage + surrogate-labels + fragility |
| Data pipeline / ETL | data-integrity + leakage + statistics |
| Published tables / public data product | disclosure + tie-out + data-integrity |
| Commissioned / stakeholder-facing analysis | motivated-analysis + fragility + editor-claims |
| Preregistered study / analysis with a spec | protocol-adherence + fragility + econometrics |
| Literature review / evidence brief | citation-integrity + domain + editor-claims |
| Service / API / infrastructure | software + security + operability |
| Code change / refactor | software + simplicity + security |

**Three is the sweet spot.** Two rarely collide; five is mostly redundant unless the artifact is large.
If two selected personas would attack the same surface, say so and suggest dropping one — overlapping
mandates produce duplicate findings and make the review *worse*.

`auditor-tie-out` is near-free on any deliverable — its Phase 1 needs no data or code access at all.
Mention it when the target contains reported numbers.

### If `--reviewers` was passed
Skip the picker, but validate each name against the agents directory and warn on any that don't exist.

### Depth
| `--depth` | Reviewers | Extras |
|---|---|---|
| `quick` | 2 | findings only |
| `standard` *(default)* | 3 | + orchestrator verification of the top finding |
| `deep` | 4–5 | + verification + `critic-completeness` synthesis pass, run **last** |

### Cost estimate
Before dispatching, tell the user roughly what this will cost: reviewers × depth. Multi-agent reviews
are expensive and the user should get to reconsider at this point.

---

## Step 3 — Create the run dir and seed suspicions

Create `~/.agent/adversary/<slug>/` with a `reviews/` subdirectory, where `<slug>` is a short
kebab-case name derived from the target. Use an **absolute path** — you will hand it to subagents, and
they must not need to resolve it.

For each selected persona, write **3–5 target-specific suspicions** drawn from Step 1, matched to that
persona's mandate. Be concrete and falsifiable:

> ✅ "Check whether `score` in `merged.csv` is on the same scale as `benchmark_pct` — if one is a raw
> score and the other a percentile, the regression in `analysis.py:88` is invalid."
> ❌ "Look for measurement problems."

Do **not** give a persona suspicions belonging to another persona's mandate.

---

## Step 4 — Dispatch, in parallel, in one message

Issue **all** reviewer `Task` calls **in a single message** so they run concurrently and cannot see one
another. Each Task uses `subagent_type` = the persona's agent name.

The Task prompt carries **only three things** — the persona's mandate, the §0 shared rules, and the
Finding schema are already baked into its agent file, so do not repeat them:

```
TARGET: <absolute path or description of what to review>
RUN DIR: <absolute path to ~/.agent/adversary/<slug>/>
  Write your full analysis to <RUN DIR>/reviews/<persona-name>.md and return only the JSON block.

SEEDED SUSPICIONS (attack these first, then range freely):
1. ...
2. ...
3. ...
```

Reminders that belong in the prompt if the environment warrants: use absolute paths, no `$(...)`
command substitution (a guard hook can hang an unattended subagent), and do not modify the target.

**`--depth deep` only:** after the parallel batch completes, dispatch `critic-completeness` as a
second, separate call, giving it the paths to the completed `reviews/*.md` files. It is the one
persona allowed to see the others' output, and it must run last.

---

## Step 5 — Merge

Collect the returned JSON from each reviewer.

1. **Deduplicate by `claim_invalidated`.** Two findings that kill the same quoted claim are one
   finding with two sources.
2. **Mark corroboration.** Any finding reached by **≥2 reviewers** gets `corroborated: true` and
   leads the report. *This is the plugin's core quality signal* — independent mandates converging is
   the strongest evidence the pipeline produces.
3. **Drop unanchored findings.** Any finding whose `anchor` is missing or vague is generic criticism;
   discard it and note the count.
4. **Preserve severity.** If `critic-completeness` ran, it may add findings and supply its own
   `criticality` rank for triage, but it may **not** edit, downgrade, or delete another reviewer's
   `severity`, and every original finding is retained. The synthesiser is the only component that
   sees everything and therefore the only one able to quietly soften the review — do not let it.
5. Write the merged set to `<RUN DIR>/findings.json`, ordered: corroborated first, then by severity.

---

## Step 6 — Verify the top finding yourself

If it is cheap to do so, **re-run the single most damaging finding's check yourself** before writing
it up. In the reference run this converted a reviewer assertion into an established fact. Record what
you did and what you got in the merged findings.

If the top finding attacks something *you* produced, correct it. Do not argue with it.

---

## Step 7 — Render the report

**Render it yourself from the bundled shell — no external skill required.** Copy
`${CLAUDE_PLUGIN_ROOT}/references/report-shell.html` to `<RUN DIR>/report.html`, then fill it per
`${CLAUDE_PLUGIN_ROOT}/references/report-structure.md`: the masthead, the nav, and the §skeleton
sections (verdict → how it ran → one section per finding **with the derivation** → what survives → the
fix-plan placeholder → closing note), drawing the full LaTeX derivations from the per-reviewer files in
`<RUN DIR>/reviews/`. Build the body in chunks (append sections), not one giant write.

**Make it self-annotating** (this is Phase 2's annotation surface): give every finding block
`class="finding invalid|caveat" data-fid="<finding id from findings.json>"`, and embed
`${CLAUDE_PLUGIN_ROOT}/references/annotation-layer.html` at the two `EMBED annotation-layer` markers in
the shell — paste its toolbar, `<style>`, and `<script>`, and replace `__RUN_SLUG__` with the run slug.
Then open `<RUN DIR>/report.html`.

**`visual-explainer` is an OPTIONAL enhancer, not a dependency.** If that skill is installed you may
delegate to it for richer styling — but pass it the same report-structure.md constraints *and* the
annotation-layer requirement. If it is absent, do **not** skip the render: the bundled shell above is
the default and produces the full annotated report with zero external dependencies.

Only if you genuinely cannot author HTML at all, fall back to leaving `findings.json` as the deliverable
and say so plainly — the review is still valid, but that is the true last resort, **not** the
absent-`visual-explainer` path.

---

## Step 8 — Close out

Report to the user:
- the corroborated findings first, with the numbers the reviewers computed;
- what **survives** — the safe-to-build-on list, merged across reviewers. A review that only lists
  faults is unusable because the author cannot tell what to keep;
- how many findings were discarded as unanchored;
- **actual cost**;
- the run dir path, and that `/adversary:annotate` is the next phase.
