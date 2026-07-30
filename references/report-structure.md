# Report structure & render constraints

The Phase-1 HTML report is rendered by the existing **`visual-explainer` skill** — delegate to it,
do not reimplement. The `adversary-review` skill passes it the merged findings plus the constraints
below. When `visual-explainer` is not installed (e.g. a headless container), the render is skipped
and `findings.json` stands as the deliverable — see the skill's render step.

## Render constraints (pass these to visual-explainer verbatim)

- **Self-contained HTML**, CDN links only. Written to the run dir; opened in the browser.
- **MathJax** with `\(...\)` inline and `\[...\]` display delimiters. **Do NOT enable `$...$`** —
  review documents are full of dollar amounts and it breaks parsing. `visual-explainer` has no
  built-in MathJax, so the report must include the MathJax CDN explicitly with these delimiters.
- **Semantic colour, three states, used everywhere** (status pills, table-row highlights, KPI card
  borders):
  - `retracted / invalid` — the claim does not survive.
  - `weakened / caveat` — survives only with a correction or narrower scope.
  - `survives` — safe to build on.
- **Editorial / journal aesthetic.** This is a referee report: serif headlines, generous whitespace.
  Avoid dashboard styling.
- **Light/dark toggle** — OS default via `prefers-color-scheme`, manual override via a `data-theme`
  attribute persisted in `localStorage`. Pattern: `:root:not([data-theme])` inside the media query,
  plus `[data-theme="dark"]` for the override.
- **Sticky section nav** with scroll-spy for 4+ sections.
- **Self-annotating.** Give every finding section `class="finding" data-fid="<id>"` — the `<id>` MUST
  match the finding `id` in `findings.json` so fixplan can join on it — and embed the annotation layer
  (see below). This puts the Phase-2 UI *inside* the report.
- **Build long HTML in chunks**, not one heredoc / single write — large single writes fail
  (spec §7). Write the shell first, append sections.

## Section skeleton (the one that worked in the reference run)

1. **Verdict at a glance** — KPI row + a *pipeline strip* showing where in the process each failure
   entered. This single graphic did more explanatory work than any table.
2. **How the review was run** — reviewers, mandates, what each caught. Establishes independence.
3. **One section per major finding**, each structured:
   *the claim* → *the mechanism (with math)* → *the evidence table* → *what must be withdrawn*.
   Lead with `corroborated` findings (reached by ≥2 reviewers).
4. **What survives** — the safe-to-build-on table.
5. **The fix plan** — tiered *(populated by `/adversary:fixplan`; a placeholder in Phase 1)*.
6. **Closing note** on method.

## Annotation layer (self-annotating report)

The report carries its own Plannotator-style annotation UI, so Phase 2 needs no external tool. Embed
`${CLAUDE_PLUGIN_ROOT}/references/annotation-layer.html` verbatim (replace `__RUN_SLUG__` with the run
slug): a sticky toolbar (**Approve / Dismiss / Export / Reset**) plus, injected into every
`.finding[data-fid]`, a row of verdict chips — `accept · reject · already-handled · downgrade ·
upgrade · expand` — and a comment box. State persists in `localStorage`; **Export** downloads an
`annotations.json` in the exact shape `/adversary:fixplan` reads:
`{ decision, annotations: [ { finding_id, verdict, comment } ] }`. The verdicts map 1:1 to the fixplan
buckets, so no free-text interpretation is required. `plannotator annotate` remains a **fallback** —
for line-anchored comments on arbitrary passages, or a report without the embedded layer.

## Write the derivation, not just the verdict

The reference report's most valuable property was that it showed *why* each failure was inevitable
given the construction — e.g. deriving the leverage formula for appending a block of points to a
regression, then showing the algebra *predicted both placebo outcomes in advance*. A reader who
follows the derivation can check the reviewer; a reader given only a verdict must trust it. Each
per-reviewer file under `reviews/<persona>.md` carries the full LaTeX derivation for the renderer to
draw on.
