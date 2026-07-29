# `adversary` — a plugin for adversarial review → annotated report → fix plan

**Status:** specification only. Nothing built. Written 2026-07-29 from a session that ran this
workflow manually and end-to-end against a real research pipeline; every design choice below is
derived from what actually worked or actually broke in that run.

**Build this in a fresh session, in its own repo** — not in a research/analysis repo.

---

## 1. What it does

A three-phase loop that turns "I think this work might be wrong" into a prioritised, evidence-backed fix plan.

```
  /adversary:review  ─────────►  /adversary:annotate  ─────────►  /adversary:fixplan
  pick reviewers,                open the HTML report in           read the annotations,
  run them in parallel,          Plannotator, collect              emit a tiered plan +
  render an HTML report          the reader's comments             patch the source docs
```

**Phase 1 — Review.** The user picks N reviewer personas from a library (or accepts a recommended
set for the target type). Each persona is dispatched as an *independent, parallel* subagent with its
own attack surface. Their findings are merged, deduplicated, and rendered as a self-contained HTML
report with LaTeX derivations.

**Phase 2 — Annotate.** The report is opened in Plannotator's annotation UI. The user comments on
specific findings — *"this one is wrong, we already handle it"*, *"this is the real blocker"*,
*"deprioritise"*, *"expand this"*. Plannotator returns structured feedback.

**Phase 3 — Fix plan.** The annotations are merged with the findings to produce a tiered action
plan, ordered by (credibility gained) / (effort), plus an errata document that patches the
corrected claims back into the source material.

### Non-goals
- Not a linter, not a test runner, not a CI gate. This is for *analytical* work — research code,
  data pipelines, empirical claims, design docs — where the failure mode is "plausible but wrong",
  not "throws an exception".
- Not a replacement for human review. It is a machine for *generating the agenda* for human review.

---

## 2. Why this works (the lessons that must survive into the build)

These are the non-obvious findings from the manual run. **If the implementation drops these, it
produces flattery instead of review.**

### 2.1 Independence is the whole mechanism
Reviewers must run **in parallel, with no shared context**, and must not see each other's output.
The value comes from *collision*: when two reviewers with different mandates and different methods
independently reach the same conclusion, that finding is established rather than arguable. In the
reference run, two reviewers killed the same headline result using **two different placebo designs
they each invented**. Neither alone would have been decisive.

> **Implementation:** dispatch all reviewers in a single message with multiple concurrent agent
> calls. Never pipeline them. Never let reviewer N see reviewer N−1's findings.

### 2.2 Reviewers must VERIFY, not READ
A reviewer that only reads documents produces opinions. A reviewer that recomputes the numbers
produces findings. Every persona prompt must require: *"verify empirically against the artifacts;
show the numbers you computed."* In the reference run the decisive evidence was always a number the
reviewer computed themselves, never a number they were shown.

### 2.3 Seed the suspected weak points — don't rely on discovery alone
The orchestrator usually *knows* where the bodies are buried. Explicitly hand each reviewer the
suspicions relevant to its mandate ("check whether X is on the same scale as Y — if not the
regression is invalid"). This does not bias the review; it prevents reviewers from burning their
budget on easy wins and missing the fatal one. Findings the orchestrator did not seed still emerge —
in the reference run, the most damaging finding (prompt contamination determining 42% of a corpus)
was *not* seeded.

### 2.4 The placebo test is the highest-value single technique
Three of five fatal findings in the reference run were caught only by placebo: feed the analysis
noise, or a neutralised input, and check whether the result politely disappears. **If it survives
randomisation, it was never in the data.** Every quantitative persona must be explicitly instructed
to construct placebos.

Canonical forms worth naming in the prompts:
- **Shuffle the treatment** within the suspect block — does the effect persist?
- **Neutralise the outcome** to its baseline — does the effect vanish?
- **Rescale to the correct units** — does the effect survive?
- **Swap in a random covariate** of the same shape.

### 2.5 Demand deletions, not suggestions
Vague criticism is unactionable. Persona prompts must require: *"quote the exact sentences you would
force the author to delete or soften."* The reference run produced a table of twelve quoted
sentences with verdicts — that table became the errata document almost verbatim.

### 2.6 Require the survivors
A review that only lists faults is unusable, because the author cannot tell what to keep. Every
persona must end with *"state explicitly what SURVIVES your scrutiny and is safe to build on."*
This is also the honesty check on the reviewer: a persona that finds everything wrong is
miscalibrated.

### 2.7 Ask for a verdict, not a score
Numeric quality scores are noise. Ask each reviewer for a one-line verdict naming what is
publishable/shippable versus what is not.

---

## 3. Commands

### `/adversary:review [target] [--reviewers a,b,c] [--depth quick|standard|deep]`

**Target** may be: a directory, a set of documents, a PR/diff, or a free-text description of the
claim under review. If omitted, infer from the conversation.

**Flow:**
1. **Scope.** Read enough of the target to identify (a) its type — empirical/statistical, software,
   ML/measurement, design/architecture, security — and (b) the 3–5 claims that carry the most
   weight. Keep this cheap; it is orientation, not analysis.
2. **Select reviewers.** Use `AskUserQuestion` with a `multiSelect` list drawn from
   `reviewers.md`, pre-ticking the recommended set for the detected type. Always include an
   "add your own persona" escape. **Do not skip this** — the choice of adversary is the user's
   most important lever.
3. **Seed suspicions.** For each selected persona, write 3–5 target-specific things to attack,
   derived from step 1. Persona prompt = generic mandate (from library) + seeded suspicions +
   the shared rules in §2.
4. **Dispatch in parallel.** One message, N concurrent agent calls, `run_in_background` where the
   harness supports it.
5. **Merge.** Collect findings; deduplicate by claim-invalidated; mark any finding reached by ≥2
   reviewers as `corroborated: true` (these lead the report).
6. **Verify the top finding yourself** if it is cheap to do so. In the reference run the
   orchestrator re-measured the single most damaging claim before writing it up; that converted a
   reviewer assertion into an established fact.
7. **Render.** Emit the HTML report (§4) and open it.

**Depth:** `quick` = 2 reviewers, findings only. `standard` = 3 reviewers + orchestrator
verification. `deep` = 4–5 reviewers + verification + a synthesis pass that looks for what all
reviewers missed.

### `/adversary:annotate [report.html]`

Thin wrapper over Plannotator. Defaults to the most recent report in the session's output directory.

```bash
plannotator annotate <report.html> --gate --json --result-file <tmp>/annotations.json
```

Return contract (from the installed CLI, v0.12.0):
| stdout | meaning | action |
|---|---|---|
| `The user approved.` or `{"decision":"approved"}` | accepted as-is | acknowledge, stop. If a `feedback` field is present, carry it forward as non-blocking guidance |
| empty or `{"decision":"dismissed"}` | closed without comment | acknowledge, stop |
| `{"decision":"annotated","feedback":...}` | comments returned | proceed to `/adversary:fixplan` |

Notes that matter:
- `plannotator annotate` **accepts `.html` natively** and renders it raw. Do **not** pass
  `--markdown` — it would strip the report's structure and math.
- `--result-file` publishes the JSON atomically, which is what makes the phase-3 handoff reliable.
- `--gate` adds the Approve button, giving approve/annotate/dismiss rather than just comments.

### `/adversary:fixplan [--apply]`

Consumes findings + annotations and emits:
1. **`FIX_PLAN.md`** — tiered table, ordered by credibility-gained ÷ effort:
   - **Tier 0** — cheap and decisive; do before anything else.
   - **Tier 1** — the validation gate; things that make the work publishable/shippable at all.
   - **Tier 2** — rebuild work.
   - **Tier 3** — reproducibility, hygiene, infrastructure.
   Each row: action, effort estimate, why (with the finding id), and — critically — *what claim it
   unblocks*.
2. **`ERRATA.md`** — every corrected claim, with the wrong value, the right value, the evidence,
   and the file:line where it was published.
3. With `--apply`: patch the corrected claims **inline into the source documents**, each marked
   `[CORRECTED — see ERRATA <id>]`, and insert a banner at the top of every affected file. Never
   silently overwrite a published number; always leave the correction visible.

**Annotation semantics.** User comments must be able to override reviewer findings. Support at
minimum: *reject* (finding is wrong — record why, drop it), *downgrade/upgrade* (change tier),
*expand* (needs more investigation — becomes a Tier-1 item), *already handled* (drop, note where).
Interpret free text into these buckets; do not require the user to learn a syntax.

---

## 4. The report format

Rendered by the existing `visual-explainer` skill — **delegate to it, do not reimplement**. Pass it
the findings and these constraints:

- **Self-contained HTML**, CDN links only. Written to a stable output dir; opened in the browser.
- **MathJax** with `\(...\)` inline and `\[...\]` display delimiters. **Do not enable `$...$`** —
  review documents are full of dollar amounts and it breaks parsing.
- **Semantic colour**, consistently: retracted/invalid, weakened/caveat, survives. Three states,
  used everywhere (status pills, table row highlights, KPI card borders).
- **Editorial/journal aesthetic.** This is a referee report; serif headlines and generous whitespace
  read as authoritative. Avoid dashboard styling.
- **Light/dark toggle** — OS-default via `prefers-color-scheme`, manual override via a `data-theme`
  attribute, persisted in `localStorage`. (Pattern: `:root:not([data-theme])` inside the media query,
  plus `[data-theme="dark"]` for the override.)
- **Sticky section nav** with scroll-spy for 4+ sections.

**Section skeleton that worked:**
1. **Verdict at a glance** — KPI row + a pipeline strip showing *where in the process each failure
   entered*. This single graphic did more explanatory work than any table.
2. **How the review was run** — reviewers, mandates, what each caught. Establishes independence.
3. **One section per major finding**, each structured: *the claim* → *the mechanism (with math)* →
   *the evidence table* → *what must be withdrawn*.
4. **What survives** — the safe-to-build-on table.
5. **The fix plan** — tiered.
6. **Closing note** on method.

**Write the derivation, not just the verdict.** The reference report's most valuable property was
that it showed *why* each failure was inevitable given the construction — e.g. deriving the leverage
formula for appending a block of points to a regression, then showing that the algebra
*predicted both placebo outcomes in advance*. A reader who follows the derivation can check the
reviewer. A reader given only a verdict must trust it.

---

## 5. Repo layout

```
adversary/
├── .claude-plugin/plugin.json
├── skills/
│   ├── adversary-review/SKILL.md        # phase 1 orchestrator
│   ├── adversary-annotate/SKILL.md      # phase 2, wraps plannotator
│   └── adversary-fixplan/SKILL.md       # phase 3
├── agents/
│   ├── referee-econometrics.md          # persona definitions, one per file
│   ├── referee-measurement.md
│   ├── auditor-data-integrity.md
│   ├── auditor-security.md
│   ├── referee-software.md
│   └── ...                              # see reviewers.md
├── references/
│   ├── reviewers.md                     # the library + selection guidance
│   ├── placebo-cookbook.md              # canonical placebo designs by claim type
│   └── report-structure.md              # section skeleton + rendering constraints
└── README.md
```

Personas as **agent definitions** (not inline prompts) so users can add their own by dropping a file
in `agents/`.

---

## 6. Data contracts

**Finding** (what each reviewer returns — enforce with a schema):
```json
{
  "id": "F3",
  "severity": "fatal | high | medium | low",
  "claim_invalidated": "verbatim quote of the claim this kills",
  "location": "file:line or doc §",
  "mechanism": "why it fails, 1-3 sentences",
  "evidence": "the numbers the reviewer computed",
  "placebo": "the test performed and its result, if applicable",
  "fix": "concrete action",
  "effort": "15min | 1hr | 1day | 1week",
  "confidence": "certain | likely | possible"
}
```
Plus, per reviewer: `survives[]` (what passed scrutiny), `delete_sentences[]` (quoted, with verdict),
and a one-line `verdict`.

**Corroboration.** After merge, any finding whose `claim_invalidated` matches another reviewer's
gets `corroborated: true` and leads the report. This is the plugin's core quality signal.

---

## 7. Known gotchas (cost real time in the reference run)

- **Subagent Bash and command substitution.** In the reference environment a `PreToolUse` guard hook
  prompted for confirmation on `$(...)` in subagent commands, which **hangs unattended runs** (the
  subagent cannot answer the prompt). Persona prompts must instruct: *use explicit absolute paths,
  no `$(...)` command substitution.* Main-loop Bash was unaffected. Any long-running or headless
  invocation must assume subagent tool calls can be gated.
- **Very large heredocs / single-file writes can fail.** Build long HTML in chunks (write the shell
  first, append sections), not in one shot.
- **Don't let the orchestrator defend its own work.** If the orchestrator produced the artifact under
  review, it will be tempted to rationalise. The skill should state plainly: *when a reviewer is
  right, correct the document — do not argue.* In the reference run the orchestrator's own headline
  result was retracted, and that was the correct outcome.
- **Report the cost.** Multi-agent reviews are expensive. Surface an estimate at selection time
  (roughly: reviewers × depth) and the actual spend at the end.

---

## 8. Build order

1. `reviewers.md` + 3 agent definitions (econometrics, measurement, data-integrity). These are the
   asset; everything else is plumbing.
2. `/adversary:review` with hardcoded 3-reviewer dispatch → findings JSON. Test on a known-flawed
   artifact and confirm it finds the flaw.
3. Report rendering via `visual-explainer`.
4. Reviewer selection UI (`AskUserQuestion`).
5. `/adversary:annotate` (thin — the CLI does the work).
6. `/adversary:fixplan`, then `--apply`.
7. Remaining personas.

**Validation target:** run it against an artifact with a *known planted* error and confirm the
review finds it. A review pipeline that has never been tested against ground truth has exactly the
problem it exists to detect.
