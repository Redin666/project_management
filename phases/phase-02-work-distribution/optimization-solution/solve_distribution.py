from pathlib import Path
import csv
from pyomo.environ import (
    ConcreteModel,
    Set,
    Param,
    Var,
    Binary,
    Objective,
    Constraint,
    maximize,
    SolverFactory,
    value,
)

BASE = Path(__file__).resolve().parent
INPUT_FILE = BASE.parent / "optimization-formulation" / "model-input.csv"
OUTPUT_FILE = BASE / "solution.csv"

PEOPLE = ["Redin666", "Papla2016", "VladPolishuk"]

def read_input():
    tasks = []
    effort = {}
    preferences = {}

    with INPUT_FILE.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            task = row["task"]
            tasks.append(task)
            effort[task] = float(row["agreed_hours"])
            for person in PEOPLE:
                preferences[(task, person)] = float(row[person])

    return tasks, effort, preferences

def build_model(tasks, effort, preferences):
    model = ConcreteModel()

    model.TASKS = Set(initialize=tasks, ordered=True)
    model.PEOPLE = Set(initialize=PEOPLE, ordered=True)

    model.effort = Param(model.TASKS, initialize=effort)
    model.preference = Param(model.TASKS, model.PEOPLE, initialize=preferences)

    model.x = Var(model.TASKS, model.PEOPLE, domain=Binary)

    model.objective = Objective(
        expr=sum(
            model.preference[t, p] * model.x[t, p]
            for t in model.TASKS
            for p in model.PEOPLE
        ),
        sense=maximize,
    )

    def one_assignee_rule(m, t):
        return sum(m.x[t, p] for p in m.PEOPLE) == 1

    model.one_assignee = Constraint(model.TASKS, rule=one_assignee_rule)

    def min_tasks_rule(m, p):
        return sum(m.x[t, p] for t in m.TASKS) >= 2

    def max_tasks_rule(m, p):
        return sum(m.x[t, p] for t in m.TASKS) <= 3

    model.min_tasks = Constraint(model.PEOPLE, rule=min_tasks_rule)
    model.max_tasks = Constraint(model.PEOPLE, rule=max_tasks_rule)

    def min_load_rule(m, p):
        return sum(m.effort[t] * m.x[t, p] for t in m.TASKS) >= 4.0

    def max_load_rule(m, p):
        return sum(m.effort[t] * m.x[t, p] for t in m.TASKS) <= 5.5

    model.min_load = Constraint(model.PEOPLE, rule=min_load_rule)
    model.max_load = Constraint(model.PEOPLE, rule=max_load_rule)

    return model

def solve():
    tasks, effort, preferences = read_input()
    model = build_model(tasks, effort, preferences)

    solver = SolverFactory("appsi_highs")
    result = solver.solve(model)

    termination = str(result.solver.termination_condition).lower()
    if "optimal" not in termination:
        raise RuntimeError(f"Solver did not return optimal status: {termination}")

    rows = []
    for task in model.TASKS:
        assigned = None
        for person in model.PEOPLE:
            if value(model.x[task, person]) > 0.5:
                assigned = person
                break

        rows.append(
            {
                "task": task,
                "assignee": assigned,
                "effort_hours": float(value(model.effort[task])),
                "preference": float(value(model.preference[task, assigned])),
            }
        )

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["task", "assignee", "effort_hours", "preference"],
        )
        writer.writeheader()
        writer.writerows(rows)

    objective = value(model.objective)

    print("solver=Pyomo + HiGHS")
    print(f"status={termination}")
    print(f"objective_preference={objective:.1f}")

    for person in PEOPLE:
        assigned = [r for r in rows if r["assignee"] == person]
        workload = sum(float(r["effort_hours"]) for r in assigned)
        tasks_str = ", ".join(r["task"] for r in assigned)
        preference_sum = sum(float(r["preference"]) for r in assigned)
        print(
            f"{person}: {tasks_str}; "
            f"tasks={len(assigned)}; "
            f"load={workload:.1f} h; "
            f"preference={preference_sum:.1f}"
        )

if __name__ == "__main__":
    solve()
