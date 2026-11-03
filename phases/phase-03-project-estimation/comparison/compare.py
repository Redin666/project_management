#!/usr/bin/env python3
"""Сопоставление COSMIC, UCP и коллективной экспертной оценки для P3-06."""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
COSMIC = ROOT / "cosmic" / "cosmic-results.csv"
UCP_DIR = ROOT / "ucp"
EXPERT = ROOT / "expert-estimation" / "collective-estimation.csv"
WORKBOOK = HERE / "P3-06_Сравнение_методов_оценки.xlsx"

# Базовая ставка UCP, принятая в P3-03, и диапазон чувствительности.
BASE_RATE = 20
RATES = [15, 20, 25, 28]


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [row for row in csv.DictReader(file) if row[next(iter(row))] != "TOTAL"]


def write_csv(filename, fieldnames, rows):
    with (HERE / filename).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ranks(values):
    """Средние ранги (1 — наибольшее значение) с учётом связок."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    result = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            result[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return result


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / (sxx * syy) ** 0.5


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def schneider_winters_rate(env_rows):
    """Правило Schneider & Winters: E1–E6 с оценкой < 3 и E7–E8 с оценкой > 3."""
    count = 0
    for row in env_rows:
        rating = float(row["rating_0_5"])
        number = int(row["factor"][1:])
        if (number <= 6 and rating < 3) or (number >= 7 and rating > 3):
            count += 1
    rate = 20 if count <= 2 else 28 if count <= 4 else None
    return count, rate


def main():
    cosmic = {row["code"]: row for row in read_rows(COSMIC)}
    ucp = {row["use_case"]: row for row in read_rows(UCP_DIR / "use-cases.csv")}
    expert = {row["use_case"]: row for row in read_rows(EXPERT)}
    if not (set(cosmic) == set(ucp) == set(expert)):
        raise ValueError("Наборы Use Cases в COSMIC, UCP и экспертной оценке не совпадают")

    actors = read_rows(UCP_DIR / "actors.csv")
    technical = read_rows(UCP_DIR / "technical-factors.csv")
    environment = read_rows(UCP_DIR / "environmental-factors.csv")
    uaw = sum(float(row["weight"]) for row in actors)
    tfactor = sum(float(row["weight"]) * float(row["rating_0_5"]) for row in technical)
    efactor = sum(float(row["weight"]) * float(row["rating_0_5"]) for row in environment)
    tcf = 0.6 + 0.01 * tfactor
    ecf = 1.4 - 0.03 * efactor
    adjust = tcf * ecf

    codes = sorted(cosmic)
    cfp = [int(cosmic[c]["cfp"]) for c in codes]
    weight = [int(ucp[c]["weight"]) for c in codes]
    hours = [int(expert[c]["agreed_hours"]) for c in codes]
    total_cfp, total_weight, total_hours = sum(cfp), sum(weight), sum(hours)
    uucp = uaw + total_weight
    ucp_total = uucp * adjust
    ucp_effort = ucp_total * BASE_RATE

    if total_cfp != 53 or round(ucp_total, 3) != 100.901 or total_hours != 68:
        raise ValueError("Итоги не совпадают с результатами P3-02, P3-03, P3-05")

    rows = []
    for i, code in enumerate(codes):
        ucp_hours = weight[i] * adjust * BASE_RATE
        rows.append({
            "use_case": code,
            "name": cosmic[code]["process"],
            "cfp": cfp[i],
            "cfp_share_pct": f"{cfp[i] / total_cfp * 100:.2f}",
            "uucw_weight": weight[i],
            "uucw_share_pct": f"{weight[i] / total_weight * 100:.2f}",
            "ucp_effort_hours": f"{ucp_hours:.2f}",
            "expert_hours": hours[i],
            "expert_share_pct": f"{hours[i] / total_hours * 100:.2f}",
            "expert_hours_per_cfp": f"{hours[i] / cfp[i]:.2f}",
            "ucp_to_expert_ratio": f"{ucp_hours / hours[i]:.1f}",
        })
    write_csv("comparison.csv", list(rows[0]), rows)

    sw_count, sw_rate = schneider_winters_rate(environment)
    summary = [
        {"metric": "COSMIC, CFP", "value": f"{total_cfp}"},
        {"metric": "UCP", "value": f"{ucp_total:.3f}"},
        {"metric": f"Трудоёмкость UCP при {BASE_RATE} ч/UCP, чел.-ч", "value": f"{ucp_effort:.2f}"},
        {"metric": "Из неё за счёт UAW (акторы), чел.-ч", "value": f"{uaw * adjust * BASE_RATE:.2f}"},
        {"metric": "Коллективная экспертная оценка, чел.-ч", "value": f"{total_hours}"},
        {"metric": "Отношение UCP-трудоёмкости к экспертной", "value": f"{ucp_effort / total_hours:.2f}"},
        {"metric": "Экспертная оценка, ч/CFP", "value": f"{total_hours / total_cfp:.3f}"},
        {"metric": "UCP-трудоёмкость, ч/CFP", "value": f"{ucp_effort / total_cfp:.3f}"},
        {"metric": "Производительность, неявно заданная экспертной оценкой, ч/UCP", "value": f"{total_hours / ucp_total:.3f}"},
        {"metric": "Spearman: CFP и экспертные часы", "value": f"{spearman(cfp, hours):.3f}"},
        {"metric": "Spearman: CFP и вес UUCW", "value": f"{spearman(cfp, weight):.3f}"},
        {"metric": "Spearman: вес UUCW и экспертные часы", "value": f"{spearman(weight, hours):.3f}"},
        {"metric": "Pearson: CFP и экспертные часы", "value": f"{pearson(cfp, hours):.3f}"},
        {"metric": "Schneider & Winters: число неблагоприятных факторов окружения", "value": f"{sw_count}"},
        {"metric": "Schneider & Winters: рекомендуемая ставка, ч/UCP", "value": f"{sw_rate}"},
    ]
    for rate in RATES:
        summary.append({
            "metric": f"Трудоёмкость UCP при {rate} ч/UCP, чел.-ч",
            "value": f"{ucp_total * rate + 1e-9:.2f}",
        })
    write_csv("summary.csv", ["metric", "value"], summary)

    build_workbook(codes, cosmic, cfp, weight, hours, uaw, tfactor, efactor)
    print(f"CFP={total_cfp} UCP={ucp_total:.3f} UCP_effort={ucp_effort:.2f} expert={total_hours}")
    print(f"ratio={ucp_effort / total_hours:.2f} rho(CFP,h)={spearman(cfp, hours):.3f} "
          f"rho(CFP,w)={spearman(cfp, weight):.3f} rho(w,h)={spearman(weight, hours):.3f} "
          f"SW={sw_count}->{sw_rate}")


def build_workbook(codes, cosmic, cfp, weight, hours, uaw, tfactor, efactor):
    bold = Font(bold=True)
    head_fill = PatternFill("solid", fgColor="DDEBF7")
    wb = Workbook()

    ws = wb.active
    ws.title = "Параметры"
    params = [
        ("UAW (сумма весов акторов, P3-03)", uaw),
        ("TFactor (P3-03)", tfactor),
        ("EFactor (P3-03)", efactor),
        ("TCF", "=0.6+0.01*B3"),
        ("ECF", "=1.4-0.03*B4"),
        ("Базовая ставка, ч/UCP", BASE_RATE),
    ]
    ws["A1"], ws["B1"] = "Параметр", "Значение"
    for r, (name, value) in enumerate(params, start=2):
        ws.cell(r, 1, name)
        ws.cell(r, 2, value)
    ws.column_dimensions["A"].width = 40

    cw = wb.create_sheet("По Use Cases")
    headers = ["Use Case", "Название", "CFP", "Доля CFP", "Вес UUCW", "Доля UUCW",
               "UCP-трудоёмкость, ч", "Экспертная, ч", "Доля экспертной",
               "Экспертная, ч/CFP", "UCP / экспертная",
               "Ранг CFP", "Ранг UUCW", "Ранг экспертной"]
    cw.append(headers)
    n = len(codes)
    last = n + 1
    total_row = last + 1
    for i, code in enumerate(codes):
        r = i + 2
        cw.append([
            code, cosmic[code]["process"], cfp[i], f"=C{r}/C${total_row}",
            weight[i], f"=E{r}/E${total_row}",
            f"=E{r}*Параметры!$B$5*Параметры!$B$6*Параметры!$B$7",
            hours[i], f"=H{r}/H${total_row}", f"=H{r}/C{r}", f"=G{r}/H{r}",
            f"=_xlfn.RANK.AVG(C{r},C$2:C${last})", f"=_xlfn.RANK.AVG(E{r},E$2:E${last})",
            f"=_xlfn.RANK.AVG(H{r},H$2:H${last})",
        ])
    cw.append(["ИТОГО", "", f"=SUM(C2:C{last})", f"=SUM(D2:D{last})", f"=SUM(E2:E{last})",
               f"=SUM(F2:F{last})", f"=SUM(G2:G{last})", f"=SUM(H2:H{last})",
               f"=SUM(I2:I{last})", f"=H{total_row}/C{total_row}", f"=G{total_row}/H{total_row}"])
    for col in (4, 6, 9):
        for r in range(2, total_row + 1):
            cw.cell(r, col).number_format = "0.0%"
    for col in (7, 10, 11):
        for r in range(2, total_row + 1):
            cw.cell(r, col).number_format = "0.00"
    for cell in cw[total_row]:
        cell.font = bold

    sm = wb.create_sheet("Сводка")
    t = total_row
    rows = [
        ("Показатель", "Значение", "Комментарий"),
        ("COSMIC, CFP", f"='По Use Cases'!C{t}", "Функциональный размер, не трудоёмкость"),
        ("UUCP", f"=Параметры!B2+'По Use Cases'!E{t}", "UAW + UUCW"),
        ("UCP", "=B3*Параметры!B5*Параметры!B6", "UUCP × TCF × ECF"),
        ("UCP-трудоёмкость, чел.-ч", "=B4*Параметры!B7", "При базовой ставке"),
        ("Экспертная оценка, чел.-ч", f"='По Use Cases'!H{t}", "Сумма согласованных оценок P3-04/P3-05"),
        ("UCP / экспертная", "=B5/B6", "Во сколько раз расходятся оценки трудоёмкости"),
        ("Экспертная, ч/CFP", "=B6/B2", "Неявная производительность экспертной оценки"),
        ("UCP, ч/CFP", "=B5/B2", "Неявная производительность UCP"),
        ("Неявная ставка экспертной оценки, ч/UCP", "=B6/B4", "Сравнить с 15–28 ч/UCP в методике"),
        ("Spearman: CFP и экспертная", f"=CORREL('По Use Cases'!L2:L{last},'По Use Cases'!N2:N{last})",
         "Корреляция рангов"),
        ("Spearman: CFP и UUCW", f"=CORREL('По Use Cases'!L2:L{last},'По Use Cases'!M2:M{last})",
         "Корреляция рангов"),
        ("Spearman: UUCW и экспертная", f"=CORREL('По Use Cases'!M2:M{last},'По Use Cases'!N2:N{last})",
         "Корреляция рангов"),
        ("Pearson: CFP и экспертная", f"=CORREL('По Use Cases'!C2:C{last},'По Use Cases'!H2:H{last})",
         "Линейная корреляция"),
    ]
    for row in rows:
        sm.append(list(row))
    for r in range(2, len(rows) + 1):
        sm.cell(r, 2).number_format = "0.000"
    sm.column_dimensions["A"].width = 42
    sm.column_dimensions["C"].width = 48

    sens = wb.create_sheet("Чувствительность")
    sens.append(["Ставка, ч/UCP", "UCP-трудоёмкость, чел.-ч", "UCP / экспертная"])
    for i, rate in enumerate(RATES, start=2):
        sens.append([rate, f"=Сводка!$B$4*A{i}", f"=B{i}/Сводка!$B$6"])
        sens.cell(i, 2).number_format = "0.00"
        sens.cell(i, 3).number_format = "0.00"
    sens.column_dimensions["B"].width = 26
    sens.column_dimensions["C"].width = 20

    for sheet in wb.worksheets:
        for cell in sheet[1]:
            cell.font = bold
            cell.fill = head_fill
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        if sheet is not ws:
            for col in range(1, sheet.max_column + 1):
                letter = get_column_letter(col)
                if sheet.column_dimensions[letter].width in (None, 13):
                    sheet.column_dimensions[letter].width = 14
    cw.column_dimensions["B"].width = 38
    cw.freeze_panes = "C2"

    chart = BarChart()
    chart.type = "col"
    chart.title = "Структура оценки по Use Cases (доли)"
    chart.y_axis.title = "Доля"
    data = Reference(cw, min_col=4, max_col=4, min_row=1, max_row=last)
    chart.add_data(data, titles_from_data=True)
    chart.add_data(Reference(cw, min_col=6, max_col=6, min_row=1, max_row=last), titles_from_data=True)
    chart.add_data(Reference(cw, min_col=9, max_col=9, min_row=1, max_row=last), titles_from_data=True)
    chart.set_categories(Reference(cw, min_col=1, min_row=2, max_row=last))
    chart.width, chart.height = 24, 10
    cw.add_chart(chart, f"A{total_row + 3}")

    wb.save(WORKBOOK)


if __name__ == "__main__":
    main()
