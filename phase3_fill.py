#!/usr/bin/env python3
"""Phase3: fill Bringup report XML. Global {{KEY}} replace; expand table rows.

Does not invent values. Caller supplies replacements from Phase1/2.
Exits non-zero if any {{PLACEHOLDER}} remains.

  python3 scripts/phase3_fill.py \\
    --template templates/phase3_bringup_report.xml \\
    --json replacements.json --out filled.xml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping


PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def xml_text(s: Any) -> str:
    t = "" if s is None else str(s)
    return (
        t.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def link_or_text(value: str) -> str:
    v = value.strip()
    if v.startswith("http://") or v.startswith("https://"):
        return f'<a href="{xml_text(v)}">{xml_text(v)}</a>'
    return xml_text(v)


def yellow_td(inner: str) -> str:
    return f'<td background-color="light-yellow"><p>{inner}</p></td>'


def orange_td(inner: str) -> str:
    return f'<td background-color="rgb(255,200,140)"><p>{inner}</p></td>'


def expand_chg_rows(rows: List[Mapping[str, Any]]) -> str:
    parts: List[str] = []
    for r in rows:
        parts.append(
            "<tr>\n"
            + yellow_td(xml_text(r.get("name", "")))
            + "\n"
            + yellow_td(xml_text(r.get("base", "")))
            + "\n"
            + yellow_td(xml_text(r.get("new", "")))
            + "\n"
            + yellow_td(xml_text(r.get("firmware", "")))
            + "\n"
            + orange_td("待填（如功耗/存储…）")
            + "\n"
            + yellow_td(xml_text(r.get("action", "")))
            + "\n"
            + orange_td("待填")
            + "\n"
            + orange_td("待填（完成/未完成）")
            + "\n</tr>"
        )
    return "\n".join(parts)


def expand_gpio_rows(rows: List[Mapping[str, Any]]) -> str:
    parts: List[str] = []
    for r in rows:
        parts.append(
            "<tr>\n"
            + yellow_td(xml_text(r.get("pin", "")))
            + "\n"
            + yellow_td(xml_text(r.get("base", "")))
            + "\n"
            + yellow_td(xml_text(r.get("new", "")))
            + "\n"
            + yellow_td(xml_text(r.get("file", "")))
            + "\n"
            + yellow_td(xml_text(r.get("result", "")))
            + "\n"
            + orange_td("待填")
            + "\n"
            + yellow_td(xml_text(r.get("note", "")))
            + "\n</tr>"
        )
    return "\n".join(parts)


def expand_macro_rows(rows: List[Mapping[str, Any]]) -> str:
    parts: List[str] = []
    for r in rows:
        parts.append(
            "<tr>\n"
            + yellow_td(xml_text(r.get("path", "")))
            + "\n"
            + yellow_td(xml_text(r.get("desc", "")))
            + "\n"
            + orange_td("待填")
            + "\n"
            + orange_td("待填")
            + "\n</tr>"
        )
    return "\n".join(parts)


def replace_first_tr_containing(xml: str, needle: str, replacement: str) -> str:
    tr_re = re.compile(r"<tr>.*?</tr>", re.S)
    for m in tr_re.finditer(xml):
        if needle in m.group(0):
            return xml[: m.start()] + replacement + xml[m.end() :]
    die(f"cannot find table row containing {needle}")
    return xml


def expand_risk_rows(rows: List[Any]) -> str:
    parts: List[str] = []
    for i, r in enumerate(rows, 1):
        text = r if isinstance(r, str) else r.get("text", "")
        parts.append(
            "<tr>\n"
            + yellow_td(xml_text(i))
            + "\n"
            + yellow_td(xml_text(text))
            + "\n</tr>"
        )
    return "\n".join(parts) if parts else (
        "<tr>\n" + yellow_td("1") + "\n" + yellow_td("无") + "\n</tr>\n"
        "<tr>\n" + yellow_td("2") + "\n" + yellow_td("无") + "\n</tr>"
    )


def sanitize_callout(xml: str) -> str:
    """Project reports: title 'Skill Phase3 导出' + 填色 only; drop 占位清单."""
    xml = re.sub(
        r"<p>占位：.*?</p>\s*",
        "",
        xml,
        flags=re.S,
    )
    xml = re.sub(
        r"(<callout[^>]*>\s*)<p>.*?</p>",
        r"\1<p><b>Skill Phase3 导出</b></p>",
        xml,
        count=1,
        flags=re.S,
    )
    return xml


def fill(xml: str, data: Dict[str, Any]) -> str:
    xml = sanitize_callout(xml)
    chg = data.get("CHG_ROWS")
    gpio = data.get("GPIO_ROWS")
    macros = data.get("MACRO_ROWS")
    risks = data.get("RISK_ROWS")
    if chg:
        xml = replace_first_tr_containing(xml, "{{CHG_NAME_1}}", expand_chg_rows(chg))
    if gpio:
        xml = replace_first_tr_containing(xml, "{{GPIO_PIN_1}}", expand_gpio_rows(gpio))
    if macros:
        xml = replace_first_tr_containing(xml, "{{MACRO_PATH_1}}", expand_macro_rows(macros))
    if risks:
        xml = replace_first_tr_containing(xml, "{{RISK_1}}", expand_risk_rows(risks))
        xml = re.sub(
            r"<tr>(?:(?!</tr>).)*\{\{RISK_2\}\}(?:(?!</tr>).)*</tr>\s*",
            "",
            xml,
            count=1,
            flags=re.S,
        )

    skip = {
        "CHG_ROWS",
        "GPIO_ROWS",
        "MACRO_ROWS",
        "RISK_ROWS",
        "HW_DOC_TEXT",
        "GPIO_DOC_TEXT",
    }
    for key, value in data.items():
        if key in skip or not isinstance(value, (str, int)):
            continue
        token = "{{" + key + "}}"
        raw = str(value)
        if key in ("HW_DOC", "GPIO_DOC") and (
            raw.startswith("http://") or raw.startswith("https://")
        ):
            label_key = "HW_DOC_TEXT" if key == "HW_DOC" else "GPIO_DOC_TEXT"
            label = str(data.get(label_key) or raw)
            linked = f'<a href="{xml_text(raw)}">{xml_text(label)}</a>'
            xml = xml.replace(f"<p>{token}</p>", f"<p>{linked}</p>")
            xml = xml.replace(token, xml_text(raw))
        else:
            xml = xml.replace(token, xml_text(raw))
    return xml


def main() -> None:
    ap = argparse.ArgumentParser(description="Fill Phase3 Bringup report XML")
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--json", type=Path, required=True, help="replacements JSON")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if not args.template.is_file():
        die(f"template not found: {args.template}")
    if not args.json.is_file():
        die(f"json not found: {args.json}")

    data = json.loads(args.json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        die("replacements JSON must be an object")

    xml = args.template.read_text(encoding="utf-8")
    xml = fill(xml, data)
    leftover = sorted(set(PLACEHOLDER_RE.findall(xml)))
    if leftover:
        die("unreplaced placeholders: " + ", ".join(leftover))
    if not xml.endswith("\n"):
        xml += "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(xml, encoding="utf-8")
    print(f"wrote {args.out} bytes={args.out.stat().st_size}")


if __name__ == "__main__":
    main()
