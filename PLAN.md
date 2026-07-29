# Build the `adversary` plugin

## Context

There is a finished specification at `~/.agent/specs/adversary-plugin/` (`SPEC.md`, `reviewers.md`)
written from a manual run of an adversarial-review workflow that actually retracted a real research
result. The spec is complete and deliberate; this task is to **turn it into a working Claude Code
plugin** — not to redesign it. The plugin implements a three-phase loop:

```
/adversary:review  →  /adversary:annotate  →  /adversary:fixplan
pick personas,        open HTML report in     read annotations,
run in parallel,      Plannotator, collect    emit tiered plan + errata,
render HTML report    reader comments         --apply patches sources inline
```

The value the plugin must preserve (spec §2) is *review that bites, not flattery*: reviewers run
**independent and in parallel** so their conclusions collide; they **verify (recompute) rather than
read**; they **construct placebo tests**; they **quote sentences to delete** and **name what
survives**. Dropping any of these turns it back into flattery — they are load-bearing, not stylistic.

Intended outcome: an installable plugin whose review pipeline is **validated against a planted-error
fixture** (a review pipeline never checked against ground truth has exactly the flaw it exists to find).

## Build location & isolation

- New standalone git repo at **`~/Projects/adversary/`** (`git init`). The spec is explicit: build
  in its own repo, *not* a research/analysis repo. `~/.agent/specs/adversary-plugin/` stays untouched
  as the source of truth.
- `/Users/mitchv34/Projects` is not a git repo, so worktree isolation does not apply; the new repo is
  inherently isolated (fresh dir, its own git history).

## Design decisions already resolved (from the two Explore passes)

**Verified plumbing:**
- **Manifest**: `.claude-plugin/plugin.json` — `name`, `version`, `description`, `author`, `license`.
- **Phase entry points = skills** (`skills/<name>/SKILL.md`, frontmatter `name` + `description` +
  `allowed-tools`), matching spec §5. Invoked as `/adversary:review` etc.
- **Personas = agents** (`agents/<name>.md`, frontmatter `name` + `description` + `tools`, body = the
  prompt). Dispatchable via the Task tool; users add their own by dropping a file in `agents/`.
- **Bundled files**: referenced as `${CLAUDE_PLUGIN_ROOT}/references/...`.

**Verified dependencies:**
- **Plannotator v0.25.0** (spec guessed v0.12.0) — the annotate/fixplan skills exploit its **full**
  surface, not just the four flags the spec assumed:
  - **Line-anchored inline annotations (the differentiator).** `annotate --gate --json --result-file`
    returns an `annotations[]` array where each item carries a **line range + the quoted passage +
    the comment** — confirmed real: the feedback on *this* plan arrived in exactly that
    `(lines X–Y) Feedback on: "…"` form. So a reader comments on **a specific finding**, not the whole
    report. The annotate skill maps each annotation back to its finding (by quoted text + nearest
    finding heading); fixplan then acts per-finding.
  - **`plannotator review` for `--apply`.** After fixplan patches sources inline, open a `review`
    diff (`plannotator review --local`) so the user reviews the applied corrections with line-level
    annotations before finalizing — a v0.25.0 capability the spec never used.
  - Keep `--gate --json --result-file`; do NOT pass `--markdown` (strips math). `--require-approval`
    (exit 1 unless approved) exists as a hard gate but we do NOT default to it — our flow proceeds to
    fixplan on `annotated`. Decision JSON `{"decision":"approved"|"annotated"|"dismissed",
    "feedback":…, "annotations":[…]}` matches the spec's contract. Do not hard-depend on the survey's
    inferred per-annotation `type`/`severity` sub-fields (unverified).
- **`visual-explainer` skill** (`~/.claude/skills/visual-explainer/`) renders self-contained HTML but
  has **no built-in MathJax** and defaults its output to `~/.agent/diagrams/`. Therefore the report
  step must *explicitly* instruct it to: include the MathJax CDN with `\(...\)` inline + `\[...\]`
  display delimiters and **not** enable `$...$` (spec §4); apply three-state semantic color; use the
  editorial section skeleton; and write to our run dir. This is the one integration wrinkle.

**Data flow (how independence + full derivations + the §7 large-write gotcha are all satisfied):**
- The review skill runs in the **main loop** (so `AskUserQuestion`, parallel `Task` dispatch, and the
  `visual-explainer` Skill call all work).
- It creates a run dir **`~/.agent/adversary/<slug>/`** holding `reviews/`, `findings.json`,
  `report.html`, `annotations.json`, `FIX_PLAN.md`, `ERRATA.md`.
- **§0 shared rules + the Finding JSON schema are baked into each persona file** (not left for the
  orchestrator to remember to append). At dispatch the Task prompt carries only: the target location,
  the run-dir path, and the 3–5 seeded suspicions. This guarantees every reviewer has the rules.
- Each reviewer **writes its full analysis (prose + derivations + a trailing ```json block) to
  `<rundir>/reviews/<persona>.md`** and returns the JSON block as its Task result. Per-reviewer files
  are naturally chunked (dodges spec §7's large single-write failure) and give the report renderer the
  full LaTeX derivations, while the returned JSON drives merge/dedup.
- Merge: dedup by `claim_invalidated`; findings reached by ≥2 reviewers get `corroborated: true` and
  lead the report (spec §6). Orchestrator optionally re-verifies the single top finding itself.

## Repo layout (target)

```
adversary/
├── .claude-plugin/plugin.json
├── skills/
│   ├── adversary-review/SKILL.md      # phase 1: select → seed → parallel dispatch → merge → render
│   ├── adversary-annotate/SKILL.md    # phase 2: thin wrapper over plannotator
│   └── adversary-fixplan/SKILL.md     # phase 3: tiered plan + errata (+ --apply)
├── agents/                            # one persona per file, §0 rules + schema baked in
│   │                                  # ~12 personas — see "Persona library & selection" below
│   ├── referee-econometrics.md   ├── auditor-security.md
│   ├── referee-measurement.md    ├── referee-statistics.md
│   ├── auditor-data-integrity.md ├── referee-domain.md
│   ├── referee-software.md       ├── critic-completeness.md
│   ├── editor-claims.md          ├── skeptic-decision-risk.md
│   └── auditor-fairness.md       └── auditor-simplicity.md
├── references/
│   ├── reviewers.md               # library + selection matrix (from spec source)
│   ├── placebo-cookbook.md        # canonical placebo designs by claim type (spec §2.4)
│   └── report-structure.md        # section skeleton + rendering constraints (spec §4)
├── fixtures/planted-error/        # validation artifact with a KNOWN flaw
└── README.md
```

## Persona library & selection (revised per feedback 2)

The preset library grows from the spec's 8 to **~12, rebalanced toward practical**. Additions are
curated against the spec's own rule — *mandates must not overlap; three is the sweet spot* — so
several survey proposals were rejected as redundant rather than piled on.

**Carried from spec (8):** `referee-econometrics`, `referee-measurement`, `auditor-data-integrity`,
`referee-software`, `auditor-security`, `referee-statistics`, `referee-domain`, `critic-completeness`.

**New practical presets (distinct attack surface):**
| Persona | Hostile mandate (one line) | Use for |
|---|---|---|
| `editor-claims` | evidence-vs-claim drift — causal language on correlational results, over-generalisation; quote the overstatement and cut/downgrade it | papers, public & product claims, grants |
| `auditor-fairness` | disparate impact & subgroup performance unmeasured; wrong fairness metric; selection bias; Goodhart on a proxy | ML/decision systems, hiring, lending, health |
| `skeptic-decision-risk` | what breaks when this ships / when a decision-maker acts on it — failure modes, rollback, blast radius, monitoring gaps | launches, migrations, production systems |
| `auditor-simplicity` | over-engineering — reinvented stdlib, speculative abstractions, needless deps (ponytail-grounded) | code review, dependency/complexity audits |

**Optional/stretch (add at persona stage if wanted):** `reviewer-cost-scale` (concentration/DEFF,
O(n²), load), `reviewer-ux-accessibility` (a11y, error UX, latency).

**Rejected as overlapping** (checks already live in an existing persona): reproducibility-ops &
numerics-reliability → `auditor-data-integrity` (units/scale/seeds); contrarian-red-team →
`referee-domain` + `critic-completeness`; taxonomy `cluster-*` → out of scope. `editor-claims` is kept
because it operationalises spec §2.5 ("demand deletions") and pairs with the "sentences to delete"
output every persona already emits.

**Selection = a two-tier layer** (feedback: recommend, but let the user pick anything):
1. From the scoped target type, pre-tick a **recommended set (~3)** in the `AskUserQuestion` multiSelect
   — but list the **entire library** as selectable options, not only the recommended few.
2. Always include a **"write your own persona"** escape.
3. Surface the recommendation *reason* per target type so the user can override knowingly.

**Recommendation matrix (academic + practical):**
| Target type | Recommended (pre-ticked) |
|---|---|
| Empirical / causal research | econometrics + measurement + data-integrity |
| Public claim / paper / grant | editor-claims + econometrics + domain |
| ML model / dataset | measurement + auditor-fairness + data-integrity |
| Data pipeline / ETL | data-integrity + statistics + software |
| Service / API / infra | software + security + skeptic-decision-risk |
| Experiment / A-B | statistics + data-integrity + measurement |
| Design doc / proposal | domain + skeptic-decision-risk + completeness |
| Code change / refactor | software + auditor-simplicity + security |

Exact final roster is confirmed at the persona-build stage (we build step by step).

## Staged execution (checkpoint between each — scope decided step by step)

Following spec §8 build order. We pause at each ▸ checkpoint to confirm before continuing.

- **Stage A — Skeleton & references.** `git init`; `plugin.json`; `README.md`; copy/adapt
  `references/reviewers.md`, author `placebo-cookbook.md` and `report-structure.md` from spec §2.4/§4.
- **Stage B — 3 core personas.** `referee-econometrics`, `referee-measurement`,
  `auditor-data-integrity` — mandate text from `reviewers.md`, with §0 shared rules + the Finding
  schema + "write full analysis to `<rundir>/reviews/<name>.md`, return the JSON" baked into each.
  ▸ *checkpoint: persona file shape.*
- **Stage C — `adversary-review` skill.** Scope target → **two-tier `AskUserQuestion` picker**
  (recommended set pre-ticked by detected type, but the *full ~12-persona library* selectable + a
  "write your own" escape) → seed suspicions → **one message, N parallel Task calls** → merge →
  `findings.json`. Cost estimate at selection, actual at end (§7). `deep` depth dispatches
  `critic-completeness` *after* the batch, reading the review files. ▸ *checkpoint: persona roster +
  dispatch/merge mechanism.*
- **Stage D — Report render.** Invoke `visual-explainer` with the explicit MathJax/color/section
  constraints above; write `report.html` to the run dir; open it.
- **Stage E — Fixture + VALIDATION RUN.** Build `fixtures/planted-error/` with a known flaw (a
  raw-score-vs-percentile scale error — the reference run's real fatal finding, which
  `referee-measurement`/`auditor-data-integrity` should catch). Run `/adversary:review` on it.
  ▸ *checkpoint: did ≥1 reviewer catch the planted flaw? PASS = pipeline works.*
- **Stage F — `adversary-annotate` skill.** Thin wrapper, but exploits **line-anchored annotations**:
  `plannotator annotate <rundir>/report.html --gate --json --result-file <rundir>/annotations.json`;
  interpret `decision` (approved→stop / dismissed→stop / annotated→proceed to fixplan) AND parse the
  `annotations[]` array, mapping each (line range + quoted text + comment) back to the finding it
  targets so fixplan can act per-finding rather than on the whole report.
- **Stage G — `adversary-fixplan` skill.** Read `findings.json` + `annotations.json`; interpret each
  finding-anchored annotation into a bucket (reject / downgrade-upgrade / expand / already-handled) —
  no syntax to learn; emit tiered `FIX_PLAN.md` (credibility-gained ÷ effort) + `ERRATA.md`. `--apply`
  patches corrected claims **inline** into source docs marked `[CORRECTED — see ERRATA <id>]` + a
  top-of-file banner (never silently overwrites a published number), then opens **`plannotator review
  --local`** so the user reviews the applied diff with line-level annotations before committing.
- **Stage H — Remaining personas.** The rest of the library beyond Stage B's core three:
  `referee-software`, `auditor-security`, `referee-statistics`, `referee-domain` (parameterised
  `{FIELD}`), `critic-completeness`, plus the new practical presets `editor-claims`, `auditor-fairness`,
  `skeptic-decision-risk`, `auditor-simplicity` (and optionally `reviewer-cost-scale`,
  `reviewer-ux-accessibility`). ▸ *checkpoint: confirm the final roster.*

## Load-bearing rules to bake in (spec §2, §7 — do not simplify away)

- Reviewers **parallel, zero shared context**; never pipeline; never let one see another's output
  (except `critic-completeness`, last).
- Every persona: **verify not read**; **construct placebos**; **quote sentences to delete**; **state
  what survives**; **one-line verdict, not a score**.
- Persona prompts: **absolute paths, no `$(...)`** (a subagent guard hook hangs on command
  substitution — spec §7).
- Build long HTML in chunks, not one heredoc (spec §7).
- Orchestrator must **not defend its own artifact**: when a reviewer is right, correct the doc.

## Verification

- **Primary (Stage E):** run `/adversary:review fixtures/planted-error/` and confirm at least one
  reviewer's `findings.json` entry names the planted scale error with the recomputed numbers. This is
  the ground-truth check the spec (§8) requires.
- **Plumbing smoke checks:** `plannotator annotate <a rendered report.html> --gate --json
  --result-file /tmp/x.json` returns a valid decision JSON; `report.html` opens with math rendered
  (no raw `\(` visible) and the light/dark toggle works.
- **Install check:** the plugin loads (`/adversary:review` etc. appear) once the local dir is
  registered — registration itself is a follow-up, not part of the build.
