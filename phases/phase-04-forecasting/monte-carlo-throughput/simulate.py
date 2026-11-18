import csv
import math
import random
import statistics
from pathlib import Path

SEED = 42
ITERATIONS = 100_000
TASKS = 10

base = Path(__file__).resolve().parent
history = base.parent / "history" / "weekly-history.csv"

with history.open(encoding="utf-8") as f:
    throughput = [int(r["completed_tasks"]) for r in csv.DictReader(f)]

rng = random.Random(SEED)
durations = []

for _ in range(ITERATIONS):
    done = 0
    weeks = 0
    while done < TASKS:
        done += rng.choice(throughput)
        weeks += 1
    durations.append(weeks)

durations.sort()

def percentile(p):
    return durations[math.ceil(p * len(durations)) - 1]

print("iterations =", ITERATIONS)
print("median =", statistics.median(durations))
print("mean =", round(statistics.mean(durations), 3))
print("P80 =", percentile(0.80))
print("P90 =", percentile(0.90))
