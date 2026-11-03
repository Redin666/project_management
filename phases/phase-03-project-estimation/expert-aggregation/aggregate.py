#!/usr/bin/env python3
"""Агрегация согласованных экспертных оценок P3-04 для P3-05."""
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "expert-estimation" / "collective-estimation.csv"
USE_CASES = HERE.parent / "use-cases" / "use-cases.csv"
GROUPS = {
    "UC-01": "Проект и scope",
    "UC-02": "Проект и scope",
    "UC-03": "Находки и взаимодействие",
    "UC-04": "Находки и взаимодействие",
    "UC-05": "Находки и взаимодействие",
    "UC-06": "Находки и взаимодействие",
    "UC-07": "Находки и взаимодействие",
    "UC-08": "Отчётность",
    "UC-09": "Отчётность",
    "UC-10": "Находки и взаимодействие",
    "UC-11": "Находки и взаимодействие",
    "UC-12": "Пользователи и роли",
}
GROUP_ORDER = [
    "Проект и scope",
    "Находки и взаимодействие",
    "Отчётность",
    "Пользователи и роли",
]


def write_csv(filename, fieldnames, rows):
    with (HERE / filename).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    with USE_CASES.open(encoding="utf-8-sig", newline="") as file:
        expected = {row["code"] for row in csv.DictReader(file)}
    if expected != set(GROUPS):
        raise ValueError("Список UC в группировке не совпадает с use-cases.csv")

    rows = []
    seen = set()
    declared_total = None
    running_total = 0
    totals = defaultdict(int)
    counts = defaultdict(int)
    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        for entry in csv.DictReader(file):
            code = entry["use_case"]
            if code == "TOTAL":
                if declared_total is not None:
                    raise ValueError("Повторная строка TOTAL")
                declared_total = int(entry["agreed_hours"])
                continue
            if code not in expected or code in seen:
                raise ValueError(f"Неизвестный или повторяющийся Use Case: {code}")
            seen.add(code)
            hours = int(entry["agreed_hours"])
            if hours < 0:
                raise ValueError(f"Отрицательная оценка: {code}")
            running_total += hours
            group = GROUPS[code]
            totals[group] += hours
            counts[group] += 1
            rows.append(dict(use_case=code, name=entry["name"], group=group,
                             agreed_hours=hours, cumulative_hours=running_total))
    if seen != expected or declared_total != running_total:
        raise ValueError("Неполный набор Use Cases или несовпадение контрольной суммы")

    write_csv("aggregation.csv",
              ["use_case", "name", "group", "agreed_hours", "cumulative_hours"],
              rows + [dict(use_case="TOTAL", name="", group="",
                           agreed_hours=running_total, cumulative_hours=running_total)])
    summary = [
        dict(group=group, use_cases=counts[group], total_hours=totals[group],
             share_percent=f"{totals[group] / running_total * 100:.2f}")
        for group in GROUP_ORDER
    ]
    summary.append(dict(group="TOTAL", use_cases=len(seen),
                        total_hours=running_total, share_percent="100.00"))
    write_csv("group-summary.csv",
              ["group", "use_cases", "total_hours", "share_percent"], summary)
    print(f"Проверено {len(seen)} Use Cases, всего {running_total} человеко-часов")


if __name__ == "__main__":
    main()
