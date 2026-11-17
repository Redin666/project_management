#!/usr/bin/env python3
"""P3-07: воспроизводимый сценарный расчёт срока реализации проекта.

Читает результаты P3-06 и предварительные сценарии P3-08.
Не требует сторонних библиотек.
"""
import csv
import io
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHASE = HERE.parent
SUMMARY = PHASE / "comparison" / "summary.csv"
SCOPE = PHASE / "scope-reduction" / "scenarios.csv"
OUTPUT = HERE / "schedule.csv"

RATES = (15, 20, 25, 28)  # человеко-часов на UCP, P3-06
TEAM_SIZES = (3, 4, 5)    # FTE, а не обязательно число людей
GROSS_HOURS_PER_WEEK = Decimal("40")
PRODUCTIVE_SHARE = Decimal("0.70")
SCHEDULE_RESERVE = Decimal("0.15")
WEEKS_PER_MONTH = Decimal("4.345")

COLUMNS = (
    "scenario", "use_cases", "ucp", "rate_hours_per_ucp", "fte",
    "effort_hours", "productive_hours_per_week", "reserve_pct",
    "calendar_weeks", "calendar_months",
)


def to_2(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def calculate() -> str:
    summary = {row["metric"]: row["value"] for row in read_csv(SUMMARY)}
    scenarios = read_csv(SCOPE)
    if len(scenarios) != 3:
        raise ValueError("Ожидались три сценария P3-08: базовый, A, B")
    names = ("Базовый MVP", "A", "B")
    ids = ("base", "A", "B")
    for row, prefix in zip(scenarios, names):
        if not row["scenario"].startswith(prefix):
            raise ValueError("Порядок сценариев в P3-08 изменился")

    base_ucp = Decimal(scenarios[0]["ucp"])
    if base_ucp != Decimal(summary["UCP"]):
        raise ValueError("Базовый UCP не совпадает с данными P3-06")
    base_effort = base_ucp * Decimal(20)
    comparison_effort = Decimal(summary["Трудоёмкость UCP при 20 ч/UCP, чел.-ч"])
    if to_2(base_effort) != to_2(comparison_effort):
        raise ValueError("Базовая трудоёмкость не совпадает с данными P3-06")

    result = io.StringIO(newline="")
    writer = csv.writer(result, lineterminator="\n")
    writer.writerow(COLUMNS)
    for item, scenario_id in zip(scenarios, ids):
        ucp = Decimal(item["ucp"])
        use_cases = int(item["use_cases"])
        for rate in RATES:
            effort = ucp * Decimal(rate)
            for fte in TEAM_SIZES:
                weekly_capacity = (
                    Decimal(fte) * GROSS_HOURS_PER_WEEK * PRODUCTIVE_SHARE
                )
                weeks = (
                    effort / weekly_capacity * (Decimal(1) + SCHEDULE_RESERVE)
                )
                months = weeks / WEEKS_PER_MONTH
                writer.writerow((
                    scenario_id, use_cases, item["ucp"], rate, fte,
                    to_2(effort), to_2(weekly_capacity), "15",
                    to_2(weeks), to_2(months),
                ))
    return result.getvalue()


def main() -> None:
    if sys.argv[1:] not in ([], ["--check"]):
        raise SystemExit("Использование: python3 estimate.py [--check]")
    expected = calculate()
    if sys.argv[1:] == ["--check"]:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            raise SystemExit("schedule.csv устарел: запустите python3 estimate.py")
        print("OK: schedule.csv согласован с P3-06 и P3-08")
    else:
        OUTPUT.write_text(expected, encoding="utf-8")
        print(f"Создан {OUTPUT.name}: {len(expected.splitlines()) - 1} сценариев")


if __name__ == "__main__":
    main()
