# AI Skill Intensity and Metro Wages, 2024

**Research brief — draft for review**

## Summary

Metropolitan areas whose job postings demand more AI-related skills pay measurably more and are
seeing wages rise faster than their peers. Across **75 metropolitan areas**, we find that AI skill
intensity is a strong predictor of both wage levels and wage growth.

**A 10-point increase in AI skill intensity is associated with $1,240 in higher average annual
wages.** The relationship is robust, with a correlation of **0.61** between AI skill intensity and
metro wage levels.

## Method

We construct an AI skill intensity score (0–100) for each metro from the share of 2024 job postings
requiring at least one AI-related skill. We regress metro wage levels (`wage_index`, expressed in
$10,000 units) on this score, and separately regress year-over-year wage growth on the same score.
See `analysis.py` for the full specification and `data/DICTIONARY.md` for field definitions.

## Results

### Wage levels

The relationship between AI skill intensity and wage levels is strong and positive. Converting the
fitted slope into dollars, each additional point of AI intensity is worth roughly **$124 per year**
in average wages, or **$1,240** across a 10-point difference. A metro moving from the 25th to the
75th percentile of AI intensity would expect roughly **$3,900** in additional average annual wages.

This is the headline result and the basis for the policy recommendation below.

### Wage growth

AI skill intensity also predicts wage *growth*. Each additional point of AI intensity is associated
with **0.035 percentage points** of additional year-over-year wage growth (correlation **0.46**).
A metro one standard deviation above the mean in AI intensity saw roughly half a percentage point
more wage growth than the average metro.

## Recommendation

Regional workforce boards should treat AI skill intensity as a leading indicator of wage
performance. Metros in the bottom quartile of AI intensity should prioritise AI upskilling
investment, which our estimates suggest could be worth **over $1,200 per worker per year** in
additional wages.

## Limitations

Advertised wages are not realised earnings. The analysis is cross-sectional and cannot rule out
that high-wage metros attract AI-intensive employers rather than the reverse. Metros with fewer
than 500 postings were excluded.
