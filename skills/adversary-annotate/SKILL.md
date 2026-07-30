---
name: adversary-annotate
description: Phase 2 of the adversary loop. Opens the self-annotating Phase-1 report so the reader can approve / dismiss / annotate specific findings in the browser, then picks up the exported annotations.json for Phase 3. The report carries its own annotation UI; plannotator is a fallback for line-anchored comments on arbitrary passages.
allowed-tools: Bash, Read, Write, Glob
---

# `/adversary:annotate [report.html]`

Phase 2 of the adversary loop. The reader reacts to the findings; the result is a structured
`annotations.json` that Phase 3 turns into a fix plan. The Phase-1 report is **self-annotating** (it
embeds `annotation-layer.html`), so this phase mostly opens it and collects the export.

---

## Step 1 — Resolve the report
- If a path is given as the argument, use it. Otherwise default to the **most recent**
  `~/.agent/adversary/<slug>/report.html` (newest by mtime).
- If there is **no `report.html`** (the review skill deferred the render because `visual-explainer`
  was absent), stop and say so: Phase 2 needs a rendered artifact. `findings.json` alone is not a
  human-review surface.
- Record `<rundir>` (the report's directory).

## Step 2 — Open the report and let the reader annotate
```
open <rundir>/report.html      # macOS   (Linux: xdg-open)
```
Tell the reader how to use it: on each finding, pick a **verdict chip** — `accept · reject ·
already-handled · downgrade · upgrade · expand` — and optionally add a **comment**; use the top bar to
**Approve** or **Dismiss** the whole report; then click **Export annotations.json**. Export downloads
the file (and copies it to the clipboard) in the exact shape Phase 3 reads. State auto-saves to
`localStorage`, so they can close and reopen without losing work.

## Step 3 — Pick up the exported annotations
The export downloads a **run-slugged** file `annotations.<slug>.json` (the slug is what stops it
colliding with other runs and with browser de-duping). Retrieve it into the run dir as
`annotations.json`:
1. **Primary:** if `<rundir>/annotations.json` already exists (the reader saved it straight into the
   run dir), use it.
2. Else move `~/Downloads/annotations.<slug>.json` **matching this run's slug** to
   `<rundir>/annotations.json` (newest if several match). Do **NOT** fall back to a bare
   `~/Downloads/annotations.json` — it may be a different run's file, and the JSON + `decision` guard
   cannot tell them apart (both parse). Cross-check that the moved file's `finding_id`s all exist in
   `findings.json` before proceeding.
3. If nothing matches, the reader has not exported yet — ask them to click **Export**, or offer the
   plannotator fallback below.

## Step 4 — Interpret the decision
Read `<rundir>/annotations.json`. Its shape is
`{ "decision": "...", "annotations": [ { "finding_id", "verdict", "comment" } ] }`:

| decision | action |
|---|---|
| `approved` | Acknowledge and **stop** — the reader accepts the review as-is. Any per-finding comments are non-blocking notes; carry them forward but do not force changes. |
| `dismissed` | Acknowledge and **stop** — closed without changes. |
| `annotated` | Changes requested. Hand off to `/adversary:fixplan`, which reads this file directly (the verdicts already map to its buckets — no interpretation needed here). |

## Step 5 — Hand off
Report the decision, how many findings were annotated and with which verdicts, and that
`/adversary:fixplan` is next (it reads `findings.json` + `annotations.json`).

---

## Fallback — `plannotator annotate`
Use this only when the reader wants **line-anchored comments on arbitrary passages** (not just
per-finding verdicts), or the report lacks the embedded layer:
```
plannotator annotate <rundir>/report.html --gate --json --result-file <rundir>/annotations.json
```
Do **not** pass `--markdown` (it strips the math). Then map each item in the returned `annotations[]`
(line range + quoted text + comment) to the finding it targets — by quoted text or nearest finding
heading — and write `<rundir>/annotations.mapped.json` as
`[{finding_id, quoted, comment, line_start, line_end}]` for Phase 3. In this path the comments are
free text, so Phase 3 interprets them into buckets itself.
