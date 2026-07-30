---
name: adversary-annotate
description: Phase 2 of the adversary loop. Opens the rendered review report in Plannotator's browser UI for the reader to approve, annotate, or dismiss — capturing line-anchored comments on specific findings — then routes to /adversary:fixplan when changes are requested. Thin wrapper over the plannotator CLI (v0.25.0).
allowed-tools: Bash, Read, Write, Glob
---

# `/adversary:annotate [report.html]`

Phase 2 of the adversary loop. The reader reacts to the findings; Plannotator captures it as
structured, **line-anchored** feedback that Phase 3 turns into a fix plan. This skill is deliberately
thin — the CLI does the work.

---

## Step 1 — Resolve the report
- If a path is given as the argument, use it.
- Otherwise default to the **most recent** `~/.agent/adversary/<slug>/report.html` (newest by mtime).
- If there is **no `report.html`** — the review skill defers the render when `visual-explainer` is
  not installed — stop and say so plainly: Phase 2 needs a rendered artifact. Offer to render it
  first, or accept an explicit markdown/HTML path to annotate instead. `findings.json` alone is not a
  human-review surface.
- Record `<rundir>` (the report's directory). You will read `findings.json` and write outputs there.

## Step 2 — Open Plannotator (this is the whole phase)
Run, with an **absolute path**:

    plannotator annotate <rundir>/report.html --gate --json --result-file <rundir>/annotations.json

- `--gate` gives **approve / annotate / dismiss**, not just free comments.
- `--json` emits the structured decision; `--result-file` publishes it **atomically** for Phase 3.
- **Do NOT pass `--markdown`.** The report is HTML with MathJax; converting to markdown strips the
  structure and the math.
- Plannotator renders `.html` raw and captures annotations anchored to specific lines.
- This **blocks** until the reader closes the browser session. It is inherently interactive — it
  cannot complete in a fully headless run; say so if you detect no display is available.
- (Available but not used by default: `--require-approval` makes the process exit 1 unless the reader
  approves. We do **not** pass it — an `annotated` decision must flow forward to fixplan, not fail.)

## Step 3 — Interpret the decision
Read `<rundir>/annotations.json` (it mirrors stdout). The `decision` field routes:

| decision | also appears as | action |
|---|---|---|
| `approved` | literal `The user approved.` | Acknowledge and **stop**. If a `feedback` field is present, the reader approved *with notes* — carry them forward as **non-blocking** guidance; do **not** revise the report over them. |
| `dismissed` | empty output | Acknowledge and **stop** — closed without changes. |
| `annotated` | — | Changes requested. Go to Step 4, then `/adversary:fixplan`. |

## Step 4 — Localise annotations to findings *(annotated only)*
Each item in `annotations[]` carries a **line range**, the **quoted passage**, and the reader's
**comment**. For each one, resolve which finding it targets: match the quoted text (or the line range)
against the finding sections in `<rundir>/findings.json`, and attach that finding's `id`. Write the
enriched list to **`<rundir>/annotations.mapped.json`**:

```json
[{ "finding_id": "F3", "quoted": "...", "comment": "...", "line_start": 44, "line_end": 47 }]
```

Leave `"finding_id": null` when a comment is global or cannot be matched to one finding — Phase 3
treats those as review-wide directives.

**Do not interpret the comments into fix buckets here** (reject / downgrade / expand / already-handled)
— that is `/adversary:fixplan`'s job. This phase only *captures and localises*.

## Step 5 — Hand off
Report to the user: the decision; how many annotations mapped, and to which findings; and that
`/adversary:fixplan` is next (it reads `findings.json` + `annotations.mapped.json`).
