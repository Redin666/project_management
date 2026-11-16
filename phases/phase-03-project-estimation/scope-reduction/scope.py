#!/usr/bin/env python3
"""Оценка вклада функций-кандидатов на исключение из MVP для P3-08."""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

HERE = Path(__file__).resolve().parent
COMPARISON = HERE.parent / "comparison" / "comparison.csv"
UCP_DIR = HERE.parent / "ucp"
WORKBOOK = HERE / "P3-08_Сокращение_функциональности.xlsx"
RATE = 20

# Решение по каждому UC: критичность для MVP и предлагаемое действие.
DECISIONS = {
    "UC-01": ("Высокая", "Оставить", "Без проекта нет контекста работ"),
    "UC-02": ("Высокая", "Оставить", "Scope ограничивает регистрацию находок (негативный сценарий UC-03)"),
    "UC-03": ("Высокая", "Оставить", "Основная ценность системы"),
    "UC-04": ("Высокая", "Оставить", "Жизненный цикл находки, на нём держится re-test"),
    "UC-05": ("Высокая", "Оставить", "Доказательства обязательны для результатов пентеста"),
    "UC-06": ("Низкая", "Исключить (сценарий B)", "Ответственный можно вести полем находки в UC-04"),
    "UC-07": ("Средняя", "Упростить", "Хватает списка с сортировкой; комбинированные фильтры — после MVP"),
    "UC-08": ("Высокая", "Упростить", "Отчёт — итоговый продукт пентеста; один шаблон без версионирования"),
    "UC-09": ("Низкая", "Исключить (сценарий A)", "Отчёт сразу формируется в одном формате в UC-08"),
    "UC-10": ("Низкая", "Исключить (сценарий A)", "Убирает внешнего актора и внешний доступ заказчика"),
    "UC-11": ("Средняя", "Исключить (сценарий A)", "Повторная проверка выражается статусом UC-04 и доказательством UC-05"),
    "UC-12": ("Высокая", "Оставить", "Ролевая модель — требование безопасности T11; роли фиксированные"),
}
SCENARIOS = {
    "Базовый MVP": [],
    "A — исключить UC-09, UC-10, UC-11": ["UC-09", "UC-10", "UC-11"],
    "B — A + исключить UC-06": ["UC-06", "UC-09", "UC-10", "UC-11"],
}
# Актор удаляется из UAW, если исключены все UC, где он основной.
ACTOR_ONLY_UC = {"Представитель заказчика": {"UC-10"}}


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(filename, fieldnames, rows):
    with (HERE / filename).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    uc = {row["use_case"]: row for row in read_rows(COMPARISON)}
    if set(uc) != set(DECISIONS):
        raise ValueError("Перечень UC не совпадает с P3-06")
    actors = read_rows(UCP_DIR / "actors.csv")
    tfactor = sum(float(r["weight"]) * float(r["rating_0_5"]) for r in read_rows(UCP_DIR / "technical-factors.csv"))
    efactor = sum(float(r["weight"]) * float(r["rating_0_5"]) for r in read_rows(UCP_DIR / "environmental-factors.csv"))
    adjust = (0.6 + 0.01 * tfactor) * (1.4 - 0.03 * efactor)

    candidates = []
    for code in sorted(uc):
        row = uc[code]
        criticality, action, reason = DECISIONS[code]
        candidates.append({
            "use_case": code,
            "name": row["name"],
            "cfp": row["cfp"],
            "uucw_weight": row["uucw_weight"],
            "expert_hours": row["expert_hours"],
            "mvp_criticality": criticality,
            "action": action,
            "reason": reason,
        })
    write_csv("candidates.csv", list(candidates[0]), candidates)

    scenarios = []
    base = None
    for name, excluded in SCENARIOS.items():
        kept = [c for c in sorted(uc) if c not in excluded]
        cfp = sum(int(uc[c]["cfp"]) for c in kept)
        uucw = sum(int(uc[c]["uucw_weight"]) for c in kept)
        hours = sum(int(uc[c]["expert_hours"]) for c in kept)
        uaw = sum(
            float(a["weight"]) for a in actors
            if a["actor"] not in ACTOR_ONLY_UC or not ACTOR_ONLY_UC[a["actor"]] <= set(excluded)
        )
        ucp = (uaw + uucw) * adjust
        effort = ucp * RATE
        if base is None:
            base = (cfp, ucp, effort, hours)
            if cfp != 53 or round(ucp, 3) != 100.901 or hours != 68:
                raise ValueError("Базовый сценарий не совпадает с P3-02, P3-03, P3-05")
        scenarios.append({
            "scenario": name,
            "excluded": ";".join(excluded),
            "use_cases": len(kept),
            "cfp": cfp,
            "cfp_reduction_pct": f"{(1 - cfp / base[0]) * 100:.1f}",
            "uaw": f"{uaw:g}",
            "uucw": uucw,
            "ucp": f"{ucp:.3f}",
            "ucp_effort_hours": f"{effort + 1e-9:.2f}",
            "ucp_effort_reduction_pct": f"{(1 - effort / base[2]) * 100:.1f}",
            "expert_hours": hours,
            "expert_reduction_pct": f"{(1 - hours / base[3]) * 100:.1f}",
        })
    write_csv("scenarios.csv", list(scenarios[0]), scenarios)
    build_workbook(candidates, scenarios)
    for s in scenarios:
        print(s)


def build_workbook(candidates, scenarios):
    bold = Font(bold=True)
    fill = PatternFill("solid", fgColor="DDEBF7")
    wb = Workbook()
    ws = wb.active
    ws.title = "Кандидаты"
    ws.append(["Use Case", "Название", "CFP", "Вес UUCW", "Экспертная, ч",
               "Критичность для MVP", "Решение", "Обоснование"])
    for c in candidates:
        ws.append([c["use_case"], c["name"], int(c["cfp"]), int(c["uucw_weight"]),
                   int(c["expert_hours"]), c["mvp_criticality"], c["action"], c["reason"]])
    last = len(candidates) + 1
    ws.append(["ИТОГО", "", f"=SUM(C2:C{last})", f"=SUM(D2:D{last})", f"=SUM(E2:E{last})"])
    for col, width in zip("ABCDEFGH", (10, 38, 8, 10, 13, 18, 24, 70)):
        ws.column_dimensions[col].width = width

    sc = wb.create_sheet("Сценарии")
    sc.append(["Сценарий", "Исключены", "UC", "CFP", "Снижение CFP", "UAW", "UUCW",
               "UCP", "UCP-трудоёмкость, ч", "Снижение UCP", "Экспертная, ч", "Снижение экспертной"])
    for r, s in enumerate(scenarios, start=2):
        sc.append([s["scenario"], s["excluded"], s["use_cases"], s["cfp"], f"=1-D{r}/D$2",
                   float(s["uaw"]), s["uucw"], float(s["ucp"]), float(s["ucp_effort_hours"]),
                   f"=1-I{r}/I$2", s["expert_hours"], f"=1-K{r}/K$2"])
        for col in (5, 10, 12):
            sc.cell(r, col).number_format = "0.0%"
    sc.column_dimensions["A"].width = 36
    sc.column_dimensions["B"].width = 26
    for sheet in wb.worksheets:
        for cell in sheet[1]:
            cell.font = bold
            cell.fill = fill
    for cell in ws[last + 1]:
        cell.font = bold
    wb.save(WORKBOOK)


if __name__ == "__main__":
    main()
