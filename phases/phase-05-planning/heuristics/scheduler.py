import csv
import random
from collections import defaultdict, deque
from pathlib import Path

BASE = Path(__file__).resolve().parent
TASKS_FILE = BASE.parent / "project-decomposition" / "tasks.csv"
CAPACITY = {"backend": 2, "frontend": 1, "qa_devops": 1}

with TASKS_FILE.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

tasks = {}
for r in rows:
    r["duration_days"] = int(r["duration_days"])
    for k in CAPACITY:
        r[k] = int(r[k])
    r["predecessors"] = [x for x in r["predecessors"].split(";") if x]
    tasks[r["id"]] = r

succ = defaultdict(list)
indegree = {}
for tid, t in tasks.items():
    indegree[tid] = len(t["predecessors"])
    for p in t["predecessors"]:
        succ[p].append(tid)

q = deque([i for i, d in indegree.items() if d == 0])
topo = []
while q:
    x = q.popleft()
    topo.append(x)
    for y in succ[x]:
        indegree[y] -= 1
        if indegree[y] == 0:
            q.append(y)

ES, EF = {}, {}
for i in topo:
    ES[i] = max((EF[p] for p in tasks[i]["predecessors"]), default=0)
    EF[i] = ES[i] + tasks[i]["duration_days"]

critical_lb = max(EF.values())

LF, LS = {}, {}
for i in reversed(topo):
    LF[i] = min((LS[s] for s in succ[i]), default=critical_lb)
    LS[i] = LF[i] - tasks[i]["duration_days"]

slk = {i: LS[i] - ES[i] for i in tasks}
free = {
    i: min((ES[s] for s in succ[i]), default=critical_lb) - EF[i]
    for i in tasks
}
grpw = {
    i: tasks[i]["duration_days"] + sum(tasks[s]["duration_days"] for s in succ[i])
    for i in tasks
}
mis = {i: len(succ[i]) for i in tasks}
grwc = {i: sum(tasks[i][r] for r in CAPACITY) for i in tasks}
grd = {i: tasks[i]["duration_days"] * grwc[i] for i in tasks}
gcrwc = {i: grwc[i] + sum(grwc[s] for s in succ[i]) for i in tasks}
rot = {
    i: sum(tasks[i][r] / CAPACITY[r] for r in CAPACITY) / tasks[i]["duration_days"]
    for i in tasks
}

def order_for(name):
    if name == "SLK": data, reverse = slk, False
    elif name == "FREE": data, reverse = free, False
    elif name == "LST": data, reverse = LS, False
    elif name == "LFT": data, reverse = LF, False
    elif name == "LSTLFT": data, reverse = {i: LS[i] + LF[i] for i in tasks}, False
    elif name == "GRPW": data, reverse = grpw, True
    elif name == "LPT": data, reverse = {i: tasks[i]["duration_days"] for i in tasks}, True
    elif name == "MIS": data, reverse = mis, True
    elif name == "GRD": data, reverse = grd, True
    elif name == "GRWC": data, reverse = grwc, True
    elif name == "GCRWC": data, reverse = gcrwc, True
    elif name == "ROT": data, reverse = rot, True
    else: raise ValueError(name)
    return sorted(tasks, key=lambda i: (data[i], i), reverse=reverse)

def schedule(order):
    horizon = 500
    usage = {r: [0] * horizon for r in CAPACITY}
    start, finish = {}, {}
    done = set()
    rank = {tid: pos for pos, tid in enumerate(order)}

    while len(done) < len(tasks):
        eligible = [
            i for i in tasks
            if i not in done and all(p in done for p in tasks[i]["predecessors"])
        ]
        tid = min(eligible, key=lambda x: rank[x])
        s = max((finish[p] for p in tasks[tid]["predecessors"]), default=0)
        d = tasks[tid]["duration_days"]

        while True:
            feasible = all(
                all(usage[r][day] + tasks[tid][r] <= CAPACITY[r] for r in CAPACITY)
                for day in range(s, s + d)
            )
            if feasible:
                break
            s += 1

        start[tid] = s
        finish[tid] = s + d
        for day in range(s, s + d):
            for r in CAPACITY:
                usage[r][day] += tasks[tid][r]
        done.add(tid)

    return max(finish.values()), start, finish

heuristics = ["SLK","FREE","LST","LFT","LSTLFT","GRPW","LPT","MIS","GRD","GRWC","GCRWC","ROT"]
results = {}

for h in heuristics:
    results[h] = schedule(order_for(h))[0]

rng = random.Random(42)
best_random = 10**9
for _ in range(5000):
    order = list(tasks)
    rng.shuffle(order)
    makespan, _, _ = schedule(order)
    best_random = min(best_random, makespan)

best_name = min(results, key=results.get)
makespan, start, finish = schedule(order_for(best_name))

print("critical-path lower bound:", critical_lb)
for h in heuristics:
    print(h, results[h])
print("best random:", best_random)
print("selected:", best_name, makespan)
