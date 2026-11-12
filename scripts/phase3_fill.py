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


# 与母版浅黄格一致；「待定/未改完」用深黄（表头说明）
YELLOW = "rgb(254,255,240)"
DEEP_YELLOW = "rgb(255,213,79)"
ORANGE = "rgb(255,200,140)"


def _pending_text(s: str) -> bool:
    return any(k in s for k in ("待定", "未改完", "未改", "保留冲突"))


def cell_paragraphs(text: str) -> str:
    """Support multi-line cell text as multiple <p> (Feishu)."""
    lines = [ln.strip() for ln in str(text).replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln != ""]
    if not lines:
        return "<p></p>"
    return "".join(f"<p>{xml_text(ln)}</p>" for ln in lines)


def colored_td(inner: str, color: str, *, raw_html: bool = False) -> str:
    body = inner if raw_html else f"<p>{inner}</p>"
    return f'<td background-color="{color}">{body}</td>'


def yellow_td(inner: str) -> str:
    return colored_td(inner, YELLOW)


def yellow_td_multiline(text: str) -> str:
    return colored_td(cell_paragraphs(text), YELLOW, raw_html=True)


def deep_yellow_td(inner: str) -> str:
    return colored_td(inner, DEEP_YELLOW)


def orange_td(inner: str) -> str:
    return colored_td(inner, ORANGE)


def auto_or_pending_td(text: str) -> str:
    """自动列：含待定/未改完/保留冲突 → 深黄，否则浅黄。"""
    return deep_yellow_td(xml_text(text)) if _pending_text(text) else yellow_td(xml_text(text))


def expand_chg_rows(rows: List[Mapping[str, Any]]) -> str:
    parts: List[str] = []
    for r in rows:
        action = str(r.get("action", ""))
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
            + auto_or_pending_td(action)
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
        result = str(r.get("result", ""))
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
            + auto_or_pending_td(result)
            + "\n"
            + orange_td("待填")
            + "\n"
            + yellow_td(xml_text(r.get("note", "")))
            + "\n</tr>"
        )
    return "\n".join(parts)


def expand_macro_rows(rows: List[Mapping[str, Any]]) -> str:
    """One row per git repo: path lists files; desc is merged summary."""
    parts: List[str] = []
    for r in rows:
        parts.append(
            "<tr>\n"
            + yellow_td_multiline(r.get("path", ""))
            + "\n"
            + yellow_td_multiline(r.get("desc", ""))
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
    """Keep母版 callout（含「项目Bringup SKILL」cite）；只去掉占位清单段。"""
    return re.sub(
        r"<p>占位：.*?</p>\s*",
        "",
        xml,
        flags=re.S,
    )


# 母版给 Agent 的填表备注；项目报告中不得残留
AGENT_FILL_HINTS = ("(填实际路径)", "(全大写)")


# 与 SKILL / profiles 板型前缀一致；禁止用 PLATFORM.upper() 硬拼（apollo5≠APOLLO5）
BOARD_SYM_PREFIX = {
    "mhs003": "HMI_BOARD_MHS003_",
    "mhs003s": "HMI_BOARD_MHS003S_",
    "apollo5": "HMI_BOARD_APOLLO330P_",
}


def board_sym(platform: str, product: str) -> str:
    p = platform.strip()
    name = product.strip().upper()
    prefix = BOARD_SYM_PREFIX.get(p)
    if prefix:
        return f"{prefix}{name}"
    # 未知平台：退回通用拼法，仍全大写
    return f"HMI_BOARD_{p.upper()}_{name}"


def ensure_board_fields(data: Dict[str, Any]) -> None:
    """补齐板级目录 / 板型宏；宏名全大写。"""
    platform = str(data.get("PLATFORM") or "").strip()
    new = str(data.get("NEW") or "").strip()
    base = str(data.get("BASE") or "").strip()
    if platform and new and not data.get("BOARD_DIR"):
        data["BOARD_DIR"] = f"platform/board/{platform}/products/{new}"
    if platform and new:
        if data.get("NEW_BOARD_SYM"):
            data["NEW_BOARD_SYM"] = str(data["NEW_BOARD_SYM"]).upper()
        else:
            data["NEW_BOARD_SYM"] = board_sym(platform, new)
    if platform and base:
        if data.get("BASE_BOARD_SYM"):
            data["BASE_BOARD_SYM"] = str(data["BASE_BOARD_SYM"]).upper()
        else:
            data["BASE_BOARD_SYM"] = board_sym(platform, base)


def strip_agent_fill_hints(xml: str) -> str:
    """去掉母版 Agent 备注；并对残留 HMI_BOARD_xxx(全大写) 做全大写替换。"""
    xml = re.sub(
        r"(HMI_BOARD_[A-Za-z0-9_]+)\(全大写\)",
        lambda m: m.group(1).upper(),
        xml,
    )
    for hint in AGENT_FILL_HINTS:
        xml = xml.replace(hint, "")
    return xml


def fill(xml: str, data: Dict[str, Any]) -> str:
    ensure_board_fields(data)
    xml = sanitize_callout(xml)
    # 若直接用母版原文：先把带备注的单元格改成占位符
    xml = xml.replace(
        "platform/board/{{PLATFORM}}/products/{{NEW}}(填实际路径)",
        "{{BOARD_DIR}}",
    )
    xml = xml.replace(
        "HMI_BOARD_{{PLATFORM}}_{{NEW}}(全大写)",
        "{{NEW_BOARD_SYM}}",
    )
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
            # 母版可能是独立 <p>{{HW_DOC}}</p>，也可能是「硬件配置表：{{HW_DOC}}」行内占位
            linked = f'<a href="{xml_text(raw)}">{xml_text(label)}</a>'
            xml = xml.replace(f"<p>{token}</p>", f"<p>{linked}</p>")
            xml = xml.replace(token, linked)
        else:
            xml = xml.replace(token, xml_text(raw))
    return strip_agent_fill_hints(xml)


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
