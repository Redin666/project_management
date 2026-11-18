import csv
import math
import random
import statistics
from pathlib import Path

SEED = 42
ITERATIONS = 100_000

base = Path(__file__).resolve().parent
history_path = base.parent / "history" / "weekly-history.csv"
estimates_path = base.parent / "three-point-estimates" / "estimates.csv"

with history_path.open(encoding="utf-8") as f:
    weekly_hours = [float(r["recorded_person_hours"]) for r in csv.DictReader(f)]

with estimates_path.open(encoding="utf-8") as f:
    estimates = list(csv.DictReader(f))

rng = random.Random(SEED)
durations = []
required_hours = []

for _ in range(ITERATIONS):
    required = sum(
        rng.triangular(
            float(r["optimistic_h"]),
            float(r["pessimistic_h"]),
            float(r["most_likely_h"]),
        )
        for r in estimates
    )
    required_hours.append(required)

    available = 0.0
    weeks = 0
    while available < required:
        available += rng.choice(weekly_hours)
        weeks += 1
    durations.append(weeks)

durations.sort()
required_hours.sort()

def percentile(values, p):
    return values[math.ceil(p * len(values)) - 1]

print("iterations =", ITERATIONS)
print("mean required hours =", round(statistics.mean(required_hours), 3))
print("mean weeks =", round(statistics.mean(durations), 3))
print("median weeks =", statistics.median(durations))
print("P80 weeks =", percentile(durations, 0.80))
print("P90 weeks =", percentile(durations, 0.90))
