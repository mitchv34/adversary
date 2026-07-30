---
name: adversary-fixplan
description: Phase 3 of the adversary loop. Merges the corroborated findings with the reader's annotations into a tiered fix plan (ordered by credibility gained ÷ effort) and an errata document; with --apply, patches corrected claims inline into the source documents (marked, never silently) and opens a Plannotator review of the diff.
allowed-tools: Read, Write, Edit, Bash, Glob
---

# `/adversary:fixplan [--apply]`

Phase 3 of the adversary loop. Turns findings + annotations into an ordered plan of action and a
correctable errata record. Without `--apply` it only writes plans; with `--apply` it edits the source
documents under review.

---

## Step 1 — Load
- Resolve `<rundir>` (most recent `~/.agent/adversary/<slug>/`, or a path given as argument).
- Read `<rundir>/findings.json` (**required**).
- Read the reader's annotations if present, in this order:
  - `<rundir>/annotations.json` — the **self-annotating report's export**:
    `{ decision, annotations: [ { finding_id, verdict, comment } ] }`. The `verdict` **is** the bucket
    already (Step 2), so no free-text interpretation is needed.
  - else `<rundir>/annotations.mapped.json` — the **plannotator fallback**:
    `[ { finding_id, quoted, comment, … } ]` with free-text comments you interpret into buckets.
  - If neither exists, proceed with the findings as-is — the reader added no overrides.

## Step 2 — Apply the reader's annotations to the findings
The reader's verdicts **override** the reviewers.

**From the self-annotating report**, each annotation already carries a `verdict` — apply it directly:

| verdict | Effect on the finding |
|---|---|
| **accept** | keep as-is (the reader confirms it) |
| **reject** | drop the finding; record the reader's `comment` in the plan's *Dropped* list |
| **already-handled** | drop; note **where** the `comment` says it is handled |
| **downgrade / upgrade** | move it down / up a tier |
| **expand** | keep and promote to a **Tier-1** investigation item |

**From the plannotator fallback** (free-text comments, no `verdict`), interpret each comment into the
same buckets — do not make the user learn a syntax: *"this is wrong / false positive"* → reject;
*"done / fixed in v2 / handled in `foo.py`"* → already-handled; *"not a blocker / deprioritise"* →
downgrade, *"this is THE blocker"* → upgrade; *"needs more investigation / unsure"* → expand.

A `finding_id: null` annotation, or a top-level `decision` of `approved`/`dismissed`, is a
**review-wide directive** — apply it to the whole plan (e.g. `dismissed` → there is nothing to plan;
`approved` → produce the errata but mark the plan advisory).

**Do not defend findings that attack work you produced.** When a reviewer is right, the correction
belongs in the errata — do not argue it away.

## Step 3 — Tier the survivors
Order by **credibility gained ÷ effort**. Every row must name *what claim it unblocks*.

| Tier | Meaning |
|---|---|
| **Tier 0** | cheap **and** decisive — do before anything else |
| **Tier 1** | the validation gate — what makes the work publishable/shippable at all (includes every *expand* item) |
| **Tier 2** | rebuild work |
| **Tier 3** | reproducibility, hygiene, infrastructure |

`corroborated: true` and `fatal` findings lead within their tier.

## Step 4 — Write the two documents
**`<rundir>/FIX_PLAN.md`** — a tiered table. Each row: *action · effort · why (finding id) · the claim
it unblocks*. Add a short **Dropped** section (rejected / already-handled findings, each with the
reader's reason) and a **Survives** section (from the findings' merged `survives[]`) so the author
knows what to keep — a plan that only lists faults is unusable.

**`<rundir>/ERRATA.md`** — one row per corrected **published** claim: *id (E1, E2, …) · the wrong value
· the right value · the evidence (the number a reviewer computed) · the `file:line` where it was
published* (from the finding's `anchor`). Only findings that correct a specific published number or
claim become errata; process/method findings stay in the plan only.

## Step 5 — `--apply` (only when the flag is set)
Patch the corrected claims **into the source documents** under review (the original target — not this
run dir):

**Precondition (headless safety):** confirm a display/browser is available so the `plannotator review
--local` in step 4 can actually open. If none is, **stop before editing any source file** and deliver
the plan + errata only — never leave sources patched-but-unreviewed.

1. For each erratum, locate the published claim at its `anchor` (`file:line`).
2. Edit it in place: keep the original value **visible**, and append the correction tagged
   **`[CORRECTED — see ERRATA E#]`**. **Never silently overwrite a published number.**
3. Insert a banner at the **top of every affected file**:
   `> ⚠️ Corrected after adversarial review — see ERRATA E#(, E#…). Original values retained inline.`
4. Then open a review of the diff so the user sees exactly what changed **before** committing anything:

       plannotator review --local

   Do **not** commit or push the source changes — leave that to the user after they review the diff.

If `--apply` is **not** set, stop after Step 4 and tell the user the plan + errata are ready and that
`--apply` will patch the sources.

## Step 6 — Close out
Report: tier counts; how many findings were dropped by reader annotations (with reasons); how many
errata were produced; and — if `--apply` ran — that the source diff is open in Plannotator for review.
