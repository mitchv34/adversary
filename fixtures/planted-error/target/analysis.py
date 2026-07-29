#!/usr/bin/env python3
"""
Metro AI-skill intensity and wages, 2024.

Q1: Do metros with higher AI skill intensity in postings have higher wage levels?
Q2: Do metros with higher AI skill intensity see faster wage growth?

Run:  python3 analysis.py
"""
import csv
import os
import statistics as st

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "postings.csv")


def load():
    with open(DATA, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def ols(xs, ys):
    """Slope, intercept, and Pearson r for a simple bivariate regression."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    slope = sxy / sxx
    return slope, my - slope * mx, sxy / (sxx * syy) ** 0.5


def main():
    rows = load()
    ai = [float(r["ai_skill_score"]) for r in rows]
    wage = [float(r["wage_index"]) for r in rows]
    growth = [float(r["wage_growth_pct"]) for r in rows]

    print(f"n metros = {len(rows)}")

    # ---- Q1: AI intensity -> wage level -------------------------------------
    # wage_index is the metro average annual wage in $10k units (see data dictionary),
    # so a slope of s means a 1-point rise in AI intensity is worth s * $10,000.
    slope, intercept, r = ols(ai, wage)
    print("\n[Q1] wage_index ~ ai_skill_score")
    print(f"  slope     = {slope:.5f}   (=> ${slope * 10000:,.0f} per AI point)")
    print(f"  intercept = {intercept:.4f}")
    print(f"  r         = {r:.4f}")
    print(f"  10-point AI increase => ${slope * 10 * 10000:,.0f}")

    # ---- Q2: AI intensity -> wage growth ------------------------------------
    g_slope, _, g_r = ols(ai, growth)
    print("\n[Q2] wage_growth_pct ~ ai_skill_score")
    print(f"  slope = {g_slope:.5f}  (pp per AI point)")
    print(f"  r     = {g_r:.4f}")

    # ---- descriptives -------------------------------------------------------
    print("\n[descriptives]")
    for name, v in (("ai_skill_score", ai), ("wage_index", wage), ("wage_growth_pct", growth)):
        print(f"  {name:<16} mean={st.mean(v):.4f}  sd={st.pstdev(v):.4f}  "
              f"min={min(v):.4f}  max={max(v):.4f}")


if __name__ == "__main__":
    main()
