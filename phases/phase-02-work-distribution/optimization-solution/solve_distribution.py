from pathlib import Path
import csv
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

BASE = Path(__file__).resolve().parent
EFFORT_FILE = BASE.parent / "effort-estimation" / "effort-estimation.csv"
PREFERENCES_FILE = BASE.parent / "preferences" / "preferences.csv"
OUTPUT_FILE = BASE / "solution.csv"

PEOPLE = ["Redin666", "Papla2016", "VladPolishuk"]

def read_effort():
    effort = {}
    with EFFORT_FILE.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["task"] == "TOTAL":
                continue
            effort[row["task"]] = float(row["agreed_hours"])
    return effort

def read_preferences():
    preferences = {}
    with PREFERENCES_FILE.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            task = row["task"]
            preferences[task] = {person: float(row[person]) for person in PEOPLE}
    return preferences

def solve():
    effort_map = read_effort()
    pref_map = read_preferences()

    tasks = list(pref_map.keys())
    n_tasks = len(tasks)
    n_people = len(PEOPLE)
    n_vars = n_tasks * n_people

    effort = np.array([effort_map[t] for t in tasks], dtype=float)
    preferences = np.array(
        [[pref_map[t][p] for p in PEOPLE] for t in tasks],
        dtype=float,
    )

    c = -preferences.reshape(-1)

    rows = []
    lower = []
    upper = []

    for i in range(n_tasks):
        row = np.zeros(n_vars)
        for j in range(n_people):
            row[i * n_people + j] = 1
        rows.append(row)
        lower.append(1)
        upper.append(1)

    for j in range(n_people):
        row = np.zeros(n_vars)
        for i in range(n_tasks):
            row[i * n_people + j] = 1
        rows.append(row)
        lower.append(2)
        upper.append(3)

    for j in range(n_people):
        row = np.zeros(n_vars)
        for i in range(n_tasks):
            row[i * n_people + j] = effort[i]
        rows.append(row)
        lower.append(4.0)
        upper.append(5.5)

    result = milp(
        c=c,
        integrality=np.ones(n_vars),
        bounds=Bounds(np.zeros(n_vars), np.ones(n_vars)),
        constraints=LinearConstraint(
            np.array(rows),
            np.array(lower),
            np.array(upper),
        ),
    )

    if not result.success:
        raise RuntimeError(result.message)

    x = np.rint(result.x).astype(int).reshape(n_tasks, n_people)

    rows_out = []
    for i, task in enumerate(tasks):
        for j, person in enumerate(PEOPLE):
            if x[i, j] == 1:
                rows_out.append(
                    {
                        "task": task,
                        "assignee": person,
                        "effort_hours": effort[i],
                        "preference": preferences[i, j],
                    }
                )

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["task", "assignee", "effort_hours", "preference"],
        )
        writer.writeheader()
        writer.writerows(rows_out)

    total_preference = sum(float(r["preference"]) for r in rows_out)
    print(f"status=optimal")
    print(f"objective_preference={total_preference:.1f}")

    for person in PEOPLE:
        assigned = [r for r in rows_out if r["assignee"] == person]
        workload = sum(float(r["effort_hours"]) for r in assigned)
        tasks_str = ", ".join(r["task"] for r in assigned)
        print(f"{person}: {tasks_str}; load={workload:.1f} h")

if __name__ == "__main__":
    solve()
