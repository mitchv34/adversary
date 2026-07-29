# Data dictionary — `postings.csv`

Metro-level extract, 2024. One row per metropolitan area.

| Column | Type | Definition |
|---|---|---|
| `metro` | string | Metropolitan area name. |
| `ai_skill_score` | float | AI skill intensity of the metro's job postings, 0–100. Constructed in-house as the share of postings requiring at least one AI-related skill, rescaled to 0–100. |
| `wage_growth_pct` | float | Year-over-year change in average advertised wage, in percentage points. |
| `wage_index` | float | Metro average annual advertised wage, in units of \$10,000. |

## Notes

- Wage figures are advertised wages from postings, not realised earnings.
- `wage_index` was produced by the wage-normalisation step in the 2024 refresh; it is
  the standard field used for cross-metro wage comparisons.
- Metros with fewer than 500 postings in the year were dropped before export.
