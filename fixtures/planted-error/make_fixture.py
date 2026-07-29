#!/usr/bin/env python3
"""Regenerate the planted-error fixture data. NOT part of the reviewed target.

Lives outside target/ deliberately: it documents that `wage_index` is a percentile
rank, which is exactly the fact the review is supposed to discover on its own.

Deterministic (fixed seed), stdlib only.
"""
import csv
import os
import random

SEED = 20260729
N_METROS = 60
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "target", "data", "postings.csv")

METRO_STEMS = [
    "Akron", "Albany", "Albuquerque", "Allentown", "Atlanta", "Augusta", "Austin",
    "Bakersfield", "Baltimore", "Baton Rouge", "Birmingham", "Boise", "Boston",
    "Buffalo", "Charleston", "Charlotte", "Chattanooga", "Chicago", "Cincinnati",
    "Cleveland", "Colorado Springs", "Columbia", "Columbus", "Dallas", "Dayton",
    "Denver", "Des Moines", "Detroit", "Durham", "El Paso", "Fresno", "Grand Rapids",
    "Greensboro", "Greenville", "Harrisburg", "Hartford", "Houston", "Indianapolis",
    "Jacksonville", "Kansas City", "Knoxville", "Las Vegas", "Lexington", "Little Rock",
    "Louisville", "Madison", "Memphis", "Miami", "Milwaukee", "Minneapolis",
    "Nashville", "New Orleans", "Oklahoma City", "Omaha", "Orlando", "Phoenix",
    "Pittsburgh", "Portland", "Providence", "Raleigh",
]


def main():
    rng = random.Random(SEED)
    metros = METRO_STEMS[:N_METROS]

    rows = []
    for m in metros:
        # AI skill intensity: raw 0-100 score, the analyst's own constructed measure.
        ai = max(0.0, min(100.0, rng.gauss(45, 16)))

        # Wage GROWTH: genuinely (modestly) related to AI intensity. This relationship
        # is REAL and must survive review — a fixture where everything is wrong would
        # not test calibration.
        growth = 1.6 + 0.035 * ai + rng.gauss(0, 1.1)

        # Wage LEVEL, stored as a PERCENTILE RANK in [0,1] -- the planted trap.
        # Genuinely ORDERED by AI intensity (so the analyst sees a real-looking effect),
        # but the stored value carries ordering only -- no magnitude. The data dictionary
        # nonetheless documents it as "$10k units", inviting a dollar interpretation
        # that the variable cannot support.
        level_latent = 0.30 * ai + rng.gauss(0, 7)
        rows.append([m, round(ai, 2), round(growth, 3), level_latent])

    # Convert the latent wage level to a percentile rank -> Uniform(0,1):
    # mean ~= 0.5, sd ~= 1/sqrt(12) ~= 0.2887. That signature is the tell.
    order = sorted(range(len(rows)), key=lambda i: rows[i][3])
    for rank, i in enumerate(order):
        rows[i][3] = round((rank + 0.5) / len(rows), 4)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metro", "ai_skill_score", "wage_growth_pct", "wage_index"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
