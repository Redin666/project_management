#!/usr/bin/env python3
"""Create P3-03 UCP workbook from versioned CSV files using the Python standard library."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import html
import re

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "P3-03_UCP.xlsx"

def read_csv(name):
    with (ROOT / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))

actors = read_csv("actors.csv")
use_cases = read_csv("use-cases.csv")
technical = read_csv("technical-factors.csv")
environment = read_csv("environmental-factors.csv")

def col_name(index):
    s = ""
    while index:
        index, digit = divmod(index - 1, 26)
        s = chr(65 + digit) + s
    return s

def cell_xml(row, col, value):
    ref = f"{col_name(col)}{row}"
    if isinstance(value, str) and value.startswith("="):
        return f'<c r="{ref}"><f>{html.escape(value[1:])}</f></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(str(value))}</t></is></c>'

def sheet_xml(rows, widths=None):
    lines = []
    for r, values in enumerate(rows, 1):
        cells = "".join(cell_xml(r, c, value) for c, value in enumerate(values, 1) if value is not None)
        lines.append(f'<row r="{r}">{cells}</row>')
    cols = ""
    for i, width in enumerate(widths or [], 1):
        cols += f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>'
    col_node = f"<cols>{cols}</cols>" if cols else ""
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            + col_node + '<sheetData>' + "".join(lines) + '</sheetData></worksheet>')

sheets = [
    ("Summary", [
        ["P3-03 - Use Case Points"],
        [],
        ["Показатель", "Значение", "Параметр", "Значение"],
        ["UAW", "=SUM(Actors!D5:D8)", "TCF base", 0.6],
        ["UUCW", "=SUM('Use Cases'!E5:E16)", "TCF rate", 0.01],
        ["UUCP", "=B4+B5", "ECF base", 1.4],
        ["TFactor", "=Technical!E18", "ECF rate", -0.03],
        ["TCF", "=D4+D5*B7", "Hours per UCP", 20],
        ["EFactor", "=Environment!E13", "Low hours per UCP", 15],
        ["ECF", "=D6+D7*B9", "High hours per UCP", 25],
        ["UCP", "=B6*B8*B10"],
        ["Hours per UCP", "=D8"],
        ["Effort, person-hours", "=B11*B12"],
        ["Low scenario, hours", "=B11*D9"],
        ["High scenario, hours", "=B11*D10"],
    ], [33, 24, 28, 17]),
    ("Actors", [
        ["UAW - actors"], [], [], ["Актор", "Интерфейс", "Класс", "Вес", "Обоснование"],
        *[[row["actor"], row["interface"], row["complexity"], int(row["weight"]), row["rationale"]] for row in actors],
        [], ["", "", "UAW", "=SUM(D5:D8)"]
    ], [40, 24, 15, 12, 65]),
    ("Use Cases", [
        ["UUCW - use cases"], [], [],
        ["Код", "Сценарий", "Транзакции", "Класс", "Вес", "Основание"],
        *[[row["use_case"], row["name"], int(row["transactions"]), row["complexity"],
           f'=IF(C{r}<=3,5,IF(C{r}<=7,10,15))', row["transaction_breakdown"]]
          for r, row in enumerate(use_cases, 5)],
        ["", "", "", "UUCW", "=SUM(E5:E16)"],
    ], [12, 42, 15, 17, 12, 85]),
    ("Technical", [
        ["TCF - technical factors"], [], [],
        ["Фактор", "Описание", "Вес", "Оценка", "Баллы", "Обоснование"],
        *[[row["factor"], row["description"], float(row["weight"]), int(row["rating_0_5"]),
           f"=C{r}*D{r}", row["rationale"]]
          for r, row in enumerate(technical, 5)],
        ["", "", "", "TFactor", "=SUM(E5:E17)"],
    ], [12, 46, 12, 12, 12, 85]),
    ("Environment", [
        ["ECF - environmental factors"], [], [],
        ["Фактор", "Описание", "Вес", "Оценка", "Баллы", "Обоснование"],
        *[[row["factor"], row["description"], float(row["weight"]), int(row["rating_0_5"]),
           f"=C{r}*D{r}", row["rationale"]]
          for r, row in enumerate(environment, 5)],
        ["", "", "", "EFactor", "=SUM(E5:E12)"],
    ], [12, 46, 12, 12, 12, 85]),
]

ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
pkg_ns = "http://schemas.openxmlformats.org/package/2006/relationships"

workbook_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<workbook xmlns="{ns}" xmlns:r="{rel_ns}"><bookViews><workbookView/></bookViews><sheets>'
    + "".join(f'<sheet name="{html.escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
              for i, (name, _, _) in enumerate(sheets, 1))
    + '</sheets><calcPr fullCalcOnLoad="1"/></workbook>'
)
workbook_rels = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{pkg_ns}">'
    + "".join(f'<Relationship Id="rId{i}" Type="{rel_ns}/worksheet" Target="worksheets/sheet{i}.xml"/>'
              for i in range(1, len(sheets) + 1))
    + '</Relationships>'
)
root_rels = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{pkg_ns}"><Relationship Id="rId1" '
    f'Type="{rel_ns}/officeDocument" Target="xl/workbook.xml"/></Relationships>'
)
content_types = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
              'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
              for i in range(1, len(sheets) + 1))
    + '</Types>'
)
with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
    archive.writestr("[Content_Types].xml", content_types)
    archive.writestr("_rels/.rels", root_rels)
    archive.writestr("xl/workbook.xml", workbook_xml)
    archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
    for i, (_, rows, widths) in enumerate(sheets, 1):
        archive.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows, widths))

print(f"Saved {OUTPUT}")
