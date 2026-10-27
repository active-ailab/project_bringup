#!/usr/bin/env python3
"""Phase 1: clone HMOS product skeleton (BASE -> NEW) and wire board symbol.

  python3 scripts/phase1_clone_product.py \\
    --repo-root <HMOS_ROOT> --platform apollo5 \\
    --base fuji --new testfuji --dry-run

  python3 scripts/phase1_clone_product.py \\
    --repo-root <HMOS_ROOT> --platform mhs003 \\
    --base rimo --new testrimo --dry-run

  python3 scripts/phase1_clone_product.py \\
    --repo-root <HMOS_ROOT> --platform mhs003s \\
    --base oslo --new testoslo --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

TEXT_SUFFIXES = {".h", ".c", ".cfg", ".json", ".txt", ".md", ".in", ".xml"}

# platform -> (board_dir, cfg_dir, board_sym_prefix, main_defconfig_fmt)
PLATFORM = {
    "apollo5": (
        "platform/board/apollo5",
        "configs/apollo5",
        "HMI_BOARD_APOLLO330P_",
        "apollo330_{new}_defconfig",
    ),
    "mhs003": (
        "platform/board/mhs003",
        "configs/mhs003",
        "HMI_BOARD_MHS003_",
        "mhs003_{new}_defconfig",
    ),
    "mhs003s": (
        "platform/board/mhs003s",
        "configs/mhs003s",
        "HMI_BOARD_MHS003S_",
        "mhs003s_{new}_defconfig",
    ),
}


@dataclass
class Plan:
    copies: List[Tuple[Path, Path]] = field(default_factory=list)
    writes: List[Tuple[Path, str, str]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def plan_write(plan: Plan, path: Path, text: str, encoding: str = "utf-8") -> None:
    plan.writes.append((path, text, encoding))


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def board_sym(platform: str, product: str) -> str:
    if platform not in PLATFORM:
        die(f"unsupported platform: {platform}")
    return PLATFORM[platform][2] + product.upper()


def product_token_re(product: str) -> re.Pattern:
    return re.compile(rf"(^|[^A-Za-z0-9]){re.escape(product)}([^A-Za-z0-9]|$)")


def config_belongs_to_product(name: str, product: str) -> bool:
    return product_token_re(product).search(name) is not None


def rename_config_name(name: str, base: str, new: str) -> str:
    return product_token_re(base).sub(rf"\g<1>{new}\g<2>", name)


def read_text_with_encoding(path: Path) -> Tuple[str, str]:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    die(f"cannot decode: {path}")


def read_text(path: Path) -> str:
    return read_text_with_encoding(path)[0]


def try_read_text_with_encoding(path: Path) -> Optional[Tuple[str, str]]:
    try:
        return read_text_with_encoding(path)
    except SystemExit:
        return None
    except OSError:
        return None


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.endswith(".cfg")


def transform_defconfig(
    text: str, platform: str, base: str, new: str, base_sym: str, new_sym: str
) -> str:
    out = text.replace(base_sym, new_sym)
    out = out.replace(
        f'HMI_PRODUCT_CUSTOMIZE_DIR="{base}"',
        f'HMI_PRODUCT_CUSTOMIZE_DIR="{new}"',
    )
    out = re.sub(
        rf'(PRODUCT_DEVICE_NAME="){re.escape(base)}(")',
        rf"\g<1>{new}\g<2>",
        out,
    )
    out = re.sub(
        rf'(BUILD_PROJECT_PATH_NAME="){re.escape(base)}(")',
        rf"\g<1>{new}\g<2>",
        out,
    )
    out = out.replace(f"ramdump_{base}@", f"ramdump_{new}@")

    if platform == "apollo5":
        out = out.replace(
            f'BX_CHIP_APOLLO330B_BIN_FOLDER="{base}"',
            f'BX_CHIP_APOLLO330B_BIN_FOLDER="{new}"',
        )
        out = out.replace(f"apollo330_{base}_sku", f"apollo330_{new}_sku")
    elif platform in ("mhs003", "mhs003s"):
        out = out.replace(
            f'BX_CHIP_RTL8763EFL_BIN_FOLDER="{base}"',
            f'BX_CHIP_RTL8763EFL_BIN_FOLDER="{new}"',
        )
        out = out.replace(f"{platform}_{base}_sku", f"{platform}_{new}_sku")
    return out


def patch_fal_cfg(text: str, base: str, new: str) -> str:
    return text.replace(f"fal_part_table.py {base}", f"fal_part_table.py {new}")


def insert_config_in(
    text: str, platform: str, base: str, new: str, base_sym: str, new_sym: str
) -> str:
    if new_sym in text:
        return text
    m = re.search(
        rf"(config {re.escape(base_sym)}\r?\n(?:.*\r?\n)*?)(?=config |endchoice)",
        text,
    )
    if not m:
        die(f"Config.in: cannot find {base_sym} block")

    if platform == "apollo5":
        block = (
            f"config {new_sym}\n"
            f'    bool "apollo330p {new}"\n'
            f"    ---help---\n"
            f"        apollo330p {new} (cloned from {base})\n"
            f"\n"
        )
    elif platform == "mhs003":
        block = (
            f"config {new_sym}\n"
            f'    bool "{new} board powered by MHS003"\n'
            f"        ---help---\n"
            f"        enable board sub type of {new} (cloned from {base})\n"
            f"\n"
        )
    else:
        block = (
            f"config {new_sym}\n"
            f'    bool "{new} board powered by MHS003S"\n'
            f"        ---help---\n"
            f"        enable board sub type of {new} (cloned from {base})\n"
            f"\n"
        )

    text = text[: m.end()] + block + text[m.end() :]
    default_line = f'    default "{base}" if {base_sym}\n'
    new_default = f'    default "{new}" if {new_sym}\n'
    if new_default not in text:
        if default_line not in text:
            die(f'Config.in: missing default "{base}" if {base_sym}')
        text = text.replace(default_line, default_line + new_default, 1)
    return text


def or_in_condition(text: str, base_sym: str, new_sym: str) -> str:
    pattern = re.compile(
        rf"\b{re.escape(base_sym)}\b(?!\s*\|\|\s*{re.escape(new_sym)})"
    )
    lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if (
            stripped.startswith(("#if", "#elif"))
            and base_sym in line
            and new_sym not in line
        ):
            if re.search(rf"#elif\s*\(\s*{re.escape(base_sym)}\s*\)", line):
                lines.append(line)
                continue
            if re.search(rf"defined\(\s*{re.escape(base_sym)}\s*\)", line):
                line = re.sub(
                    rf"defined\(\s*{re.escape(base_sym)}\s*\)",
                    f"defined({base_sym}) || defined({new_sym})",
                    line,
                )
            else:
                line = pattern.sub(f"{base_sym} || {new_sym}", line)
        lines.append(line)
    return "".join(lines)


def or_symbol_anywhere(text: str, base_sym: str, new_sym: str) -> str:
    text = re.sub(
        rf"defined\(\s*{re.escape(base_sym)}\s*\)(?!\s*\|\|\s*defined\(\s*{re.escape(new_sym)}\s*\))",
        f"defined({base_sym}) || defined({new_sym})",
        text,
    )
    return re.sub(
        rf"(?<!defined\()\b{re.escape(base_sym)}\b(?!\s*\|\|\s*{re.escape(new_sym)})",
        f"{base_sym} || {new_sym}",
        text,
    )


def insert_sport_elif(
    text: str, base_sym: str, new_sym: str, include_name: str
) -> str:
    if new_sym in text:
        return text
    m = re.search(
        rf"(#elif\s*\([^)]*{re.escape(base_sym)}[^)]*\)\r?\n"
        rf"#\s*include\s+\"[^\"]+\"\r?\n)",
        text,
    )
    if not m:
        die(f"cannot insert sport elif for {new_sym} / {include_name}")
    second = m.group(0).splitlines()[1]
    if "#   include" in second:
        add = f'#elif ({new_sym})\n#   include "{include_name}"\n'
    else:
        add = f'#elif ({new_sym})\n#include "{include_name}"\n'
    return text[: m.end()] + add + text[m.end() :]


def insert_makefile_board_block(
    text: str, base_sym: str, new_sym: str, replacer: Callable[[str], str]
) -> str:
    """Duplicate one ifeq/else-ifeq arm that references base_sym for new_sym.

    Handles both standalone `ifeq ... endif` and long `else ifeq` chains:
    only the single arm for base_sym is cloned (not through the chain endif).
    """
    if new_sym in text:
        return text
    # one arm: (else )?ifeq ($(SYM),y)\n<body lines until next else/ifeq/endif>
    pat = re.compile(
        rf"((?:else )?ifeq \(\$\({re.escape(base_sym)}\),y\)\n)"
        rf"((?:(?!(?:else )?ifeq |endif).*\n)*)"
    )
    out = text
    for m in list(pat.finditer(text)):
        header = m.group(1).replace(base_sym, new_sym)
        body = replacer(m.group(2))
        block = header + body
        out = out.replace(m.group(0), m.group(0) + block, 1)
    return out


def patch_version_record(text: str, base: str, new: str) -> str:
    if f"[{new}]" in text:
        return text
    m = re.search(
        rf"\[{re.escape(base)}\]\r?\n.*?(?=\r?\n\[|\Z)", text, flags=re.S
    )
    if not m:
        return text
    section = m.group(0).rstrip("\n") + "\n"
    cloned = section.replace(f"[{base}]", f"[{new}]", 1)
    insert_at = m.end()
    prefix = text[:insert_at].rstrip("\n") + "\n\n"
    suffix = text[insert_at:].lstrip("\n")
    return prefix + cloned + (("\n" + suffix) if suffix else "")


def plan_copy_tree(
    plan: Plan,
    src_root: Path,
    dst_root: Path,
    *,
    fal_base: str = "",
    fal_new: str = "",
    rename_base: str = "",
    rename_new: str = "",
) -> None:
    if not src_root.is_dir():
        die(f"missing: {src_root}")
    if dst_root.exists():
        die(f"target exists: {dst_root}")
    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(src_root)
        if rename_base and rename_new:
            parts = []
            for part in rel.parts:
                parts.append(
                    rename_config_name(part, rename_base, rename_new)
                    if config_belongs_to_product(part, rename_base)
                    else part
                )
            rel = Path(*parts) if parts else rel
        dst = dst_root / rel
        if fal_base and is_text_file(src) and src.name.endswith(".cfg"):
            text, enc = read_text_with_encoding(src)
            plan_write(plan, dst, patch_fal_cfg(text, fal_base, fal_new), enc)
        else:
            plan.copies.append((src, dst))


def transform_manifest(text: str, base: str, new: str) -> str:
    """Rename product tokens in repo manifest XML (filename handled separately)."""
    out = re.sub(
        rf"(releases/){re.escape(base)}(/)",
        rf"\g<1>{new}\g<2>",
        text,
    )
    out = product_token_re(base).sub(rf"\g<1>{new}\g<2>", out)
    return out


def plan_copy_manifests(plan: Plan, repo: Path, base: str, new: str) -> int:
    """Copy `.repo/manifests` product XMLs (e.g. rimo.xml → testrimo.xml).

    Content replaces product path tokens (incl. releases/<base>/ → releases/<new>/).
    Remote git branches for NEW still need architect/CI to create; files are skeleton.
    """
    man = repo / ".repo" / "manifests"
    if not man.is_dir():
        plan.notes.append("manifests: skip (.repo/manifests missing)")
        return 0
    srcs = sorted(
        p
        for p in man.iterdir()
        if p.is_file()
        and p.suffix.lower() == ".xml"
        and config_belongs_to_product(p.name, base)
    )
    if not srcs:
        plan.notes.append(f"manifests: none for '{base}'")
        return 0
    n = 0
    for src in srcs:
        dst_name = rename_config_name(src.name, base, new)
        dst = man / dst_name
        if dst.exists():
            plan.notes.append(f"manifest exists, skip: {dst.name}")
            continue
        raw, enc = read_text_with_encoding(src)
        plan_write(plan, dst, transform_manifest(raw, base, new), enc)
        n += 1
    plan.notes.append(f"manifests: {n} file(s)")
    return n


def plan_copy_mcu_named(plan: Plan, repo: Path, base: str, new: str) -> int:
    """Copy product-named files under platform/mcu (if any); skip bulky sdk trees."""
    mcu = repo / "platform/mcu"
    if not mcu.is_dir():
        return 0
    n = 0
    for src in mcu.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(mcu).as_posix()
        if "/sdk/" in f"/{rel}/" and not config_belongs_to_product(src.name, base):
            continue
        if not (
            config_belongs_to_product(src.name, base)
            or product_token_re(base).search(rel)
        ):
            continue
        parts = []
        for part in Path(rel).parts:
            parts.append(
                rename_config_name(part, base, new)
                if config_belongs_to_product(part, base)
                else part
            )
        dst = mcu / Path(*parts)
        if dst.exists():
            continue
        if is_text_file(src):
            text, enc = read_text_with_encoding(src)
            plan_write(
                plan,
                dst,
                product_token_re(base).sub(rf"\g<1>{new}\g<2>", text),
                enc,
            )
        else:
            plan.copies.append((src, dst))
        n += 1
    if n:
        plan.notes.append(f"mcu named files: {n}")
    return n


def plan_copy_configs(
    plan: Plan,
    cfg_dir: Path,
    platform: str,
    base: str,
    new: str,
    base_sym: str,
    new_sym: str,
) -> None:
    if not cfg_dir.is_dir():
        die(f"missing: {cfg_dir}")
    cfg_files = sorted(
        p
        for p in cfg_dir.iterdir()
        if p.is_file() and config_belongs_to_product(p.name, base)
    )
    if not cfg_files:
        die(f"no configs for '{base}' under {cfg_dir}")
    for src in cfg_files:
        dst_name = rename_config_name(src.name, base, new)
        dst = cfg_dir / dst_name
        if dst.exists():
            die(f"config exists: {dst}")
        raw = read_text(src)
        if src.suffix == ".json":
            plan_write(plan, dst, raw)
        else:
            plan_write(
                plan,
                dst,
                transform_defconfig(raw, platform, base, new, base_sym, new_sym),
            )


SPORT_HEADER_SPECS = [
    # (src_rel_with_{base}, include_basename_with_{new}, dispatcher_rel)
    (
        "packages/services/sport/config/sport_system_settings_{base}.h",
        "sport_system_settings_{new}.h",
        "packages/services/sport/config/sport_system_settings_default.h",
    ),
    (
        "packages/services/sport/config/sport_list_default_{base}.h",
        "sport_list_default_{new}.h",
        "packages/services/sport/config/sport_list_default.h",
    ),
    (
        "packages/services/sport/config/sport_settings_default_{base}.h",
        "sport_settings_default_{new}.h",
        "packages/services/sport/config/sport_settings_default.h",
    ),
    (
        "packages/services/sport/include/public/sport_type_in_{base}.h",
        "sport_type_in_{new}.h",
        "packages/services/sport/config/sport_type_in_default.h",
    ),
    (
        "packages/services/sport/config/special_config/sport_special_config_{base}.h",
        "sport_special_config_{new}.h",
        "packages/services/sport/src/sport_service_capability.c",
    ),
    (
        "packages/services/sport/config/sport_special_config_{base}.h",
        "sport_special_config_{new}.h",
        "packages/services/sport/src/sport_service_capability.c",
    ),
    (
        "framework/engine/sportEngine/common/sport_rt_attr_config/sport_rt_attr_{base}.h",
        "sport_rt_attr_{new}.h",
        "framework/engine/sportEngine/common/sport_rt_attr_config/sport_rt_attr_auto.c",
    ),
]


def plan_sport(
    plan: Plan, repo: Path, base: str, new: str, base_sym: str, new_sym: str
) -> int:
    """Copy existing sport headers and insert dispatchers. Returns count of headers copied."""
    copied = 0
    dispatchers: dict = {}
    seen_src = set()
    for src_fmt, inc_fmt, disp_rel in SPORT_HEADER_SPECS:
        src = repo / src_fmt.format(base=base)
        if not src.is_file() or src in seen_src:
            continue
        seen_src.add(src)
        dst = src.with_name(src.name.replace(base, new))
        if dst.exists():
            die(f"sport target exists: {dst}")
        plan.copies.append((src, dst))
        copied += 1
        disp = repo / disp_rel
        inc = inc_fmt.format(new=new)
        if disp not in dispatchers:
            dispatchers[disp] = read_text(disp)
        dispatchers[disp] = insert_sport_elif(
            dispatchers[disp], base_sym, new_sym, inc
        )
    for path, text in dispatchers.items():
        plan_write(plan, path, text)
    return copied

def plan_or_scan(
    plan: Plan,
    repo: Path,
    base_sym: str,
    new_sym: str,
    roots: Sequence[Path],
    *,
    anywhere: bool,
) -> int:
    n = 0
    seen = set()
    for root in roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".c", ".h", ".mk"} and path.name != "module.mk":
                continue
            if path in seen:
                continue
            seen.add(path)
            if any(p == path for p, _, _ in plan.writes):
                continue
            decoded = try_read_text_with_encoding(path)
            if not decoded:
                continue
            raw, enc = decoded
            if base_sym not in raw or new_sym in raw:
                continue
            if path.name == "Config.in":
                continue
            patched = (
                or_symbol_anywhere(raw, base_sym, new_sym)
                if anywhere
                else or_in_condition(raw, base_sym, new_sym)
            )
            if patched != raw:
                plan_write(plan, path, patched, enc)
                n += 1
    return n


def plan_ui_projects(plan: Plan, repo: Path, base: str, new: str) -> int:
    ui = repo / "ui"
    if not ui.is_dir():
        return 0
    n = 0
    for path in ui.rglob("config.json"):
        decoded = try_read_text_with_encoding(path)
        if not decoded:
            continue
        raw, enc = decoded
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        projects = data.get("projects")
        if not isinstance(projects, dict) or base not in projects:
            continue
        if new in projects:
            continue
        projects[new] = deepcopy(projects[base])
        plan_write(
            plan,
            path,
            json.dumps(data, ensure_ascii=False, indent=4) + "\n",
            enc,
        )
        n += 1
    return n


def plan_apollo5(repo: Path, base: str, new: str) -> Plan:
    plan = Plan()
    base_sym, new_sym = board_sym("apollo5", base), board_sym("apollo5", new)
    board = repo / "platform/board/apollo5"
    plan_copy_tree(
        plan, board / "products" / base, board / "products" / new, fal_base=base, fal_new=new
    )
    plan_copy_configs(
        plan, repo / "configs/apollo5", "apollo5", base, new, base_sym, new_sym
    )
    plan_copy_manifests(plan, repo, base, new)
    plan_copy_mcu_named(plan, repo, base, new)
    plan_write(
        plan,
        board / "Config.in",
        insert_config_in(read_text(board / "Config.in"), "apollo5", base, new, base_sym, new_sym),
    )

    sport_n = plan_sport(plan, repo, base, new, base_sym, new_sym)
    plan.notes.append(f"sport headers: {sport_n}")

    # ramdump (nor/emmc/nand product trees)
    for ram_root in board.glob("ramdump/*/" + base):
        if ram_root.is_dir():
            plan_copy_tree(
                plan,
                ram_root,
                ram_root.parent / new,
                rename_base=base,
                rename_new=new,
            )

    # hal sensor include dir
    sens = repo / "components/hal/sensor/include" / base
    if sens.is_dir():
        plan_copy_tree(plan, sens, repo / "components/hal/sensor/include" / new)
        mk = repo / "components/hal/module.mk"
        text = read_text(mk)
        text = insert_makefile_board_block(
            text, base_sym, new_sym, lambda b: b.replace(f"/{base}/", f"/{new}/")
        )
        plan_write(plan, mk, text)

    n = plan_or_scan(
        plan,
        repo,
        base_sym,
        new_sym,
        [
            board / "board.c",
            board / "bsd_batt_misc.c",
            board / "config/board_mpu.h",
            repo / "platform/mcu/apollo5/hmos/drivers/flash",
            repo / "drivers/battery",
            repo / "components/hal/module.mk",
        ],
        anywhere=False,
    )
    # also OR any remaining preprocessor hits under board/
    n += plan_or_scan(
        plan, repo, base_sym, new_sym, [board], anywhere=False
    )

    ver = repo / (
        "framework/bluebox/stack_wrapper/vendor/apollo330b/bin/"
        "cm4_ble_controller_fw_version_record.txt"
    )
    if ver.is_file() and f"[{base}]" in read_text(ver):
        plan_write(plan, ver, patch_version_record(read_text(ver), base, new))

    plan.notes.append(f"wire OR patches: {n}")
    return plan


def plan_mhs_family(repo: Path, platform: str, base: str, new: str) -> Plan:
    plan = Plan()
    base_sym, new_sym = board_sym(platform, base), board_sym(platform, new)
    board_rel, cfg_rel, _, _ = PLATFORM[platform]
    board = repo / board_rel

    plan_copy_tree(plan, board / "products" / base, board / "products" / new)
    plan_copy_configs(
        plan, repo / cfg_rel, platform, base, new, base_sym, new_sym
    )
    plan_copy_manifests(plan, repo, base, new)
    plan_copy_mcu_named(plan, repo, base, new)
    if base_sym not in read_text(board / "Config.in"):
        die(f"{base_sym} missing in {board / 'Config.in'}")
    plan_write(
        plan,
        board / "Config.in",
        insert_config_in(
            read_text(board / "Config.in"), platform, base, new, base_sym, new_sym
        ),
    )

    sport_n = plan_sport(plan, repo, base, new, base_sym, new_sym)
    plan.notes.append(f"sport headers: {sport_n}")

    # sensor / gnss json
    for src in [
        repo / f"components/hal/sensor/config/{base}_sensor_config.json",
        repo
        / f"framework/gnssAdapter/gnss_modern/gnss_airoha/fw/double/ag3353/gnss_{base}_config.json",
        repo
        / f"framework/gnssAdapter/gnss_modern/gnss_airoha/fw/double/ag3353_3M/gnss_{base}_config.json",
        repo
        / f"framework/gnssAdapter/gnss_classic/ag33xxx/fw/double/ag3353/gnss_{base}_config.json",
    ]:
        if src.is_file():
            dst = src.with_name(src.name.replace(base, new, 1))
            if not dst.exists():
                plan.copies.append((src, dst))

    # ramdump tree
    for ram_root in [
        board / "ramdump/emmc" / base,
        board / "ramdump/nand" / base,
    ]:
        if ram_root.is_dir():
            plan_copy_tree(
                plan,
                ram_root,
                ram_root.parent / new,
                rename_base=base,
                rename_new=new,
            )

    # makefile board blocks (hal + gnss)
    for mk in [
        repo / "components/hal/module.mk",
        repo / "framework/gnssAdapter/gnss_modern/module.mk",
        repo / "framework/gnssAdapter/gnss_classic/module.mk",
    ]:
        if not mk.is_file():
            continue
        text = read_text(mk)
        if base_sym not in text:
            continue
        new_text = insert_makefile_board_block(
            text,
            base_sym,
            new_sym,
            lambda b, b0=base, n0=new: b.replace(b0, n0),
        )
        if new_text != text:
            plan_write(plan, mk, new_text)

    # OR wire: NFC, logo, applist, sport_data, mcu, remaining sport if needed
    mcu_plat = repo / "platform/mcu" / ("mhs003s" if platform == "mhs003s" else "mhs003")
    n = plan_or_scan(
        plan,
        repo,
        base_sym,
        new_sym,
        [
            repo / "drivers/nfc",
            repo / "drivers/display/amazfit_logo.h",
            repo / "packages/apps/applist",
            repo / "packages/apps/sports",
            repo / "packages/services/sport",
            repo / "uiframework",
            repo / "ui/WaterDrainage",
            mcu_plat,
            board,
        ],
        anywhere=True,
    )
    plan.notes.append(f"wire OR patches: {n}")

    ui_n = plan_ui_projects(plan, repo, base, new)
    plan.notes.append(f"ui projects.{new}: {ui_n} files")
    return plan


def apply_plan(plan: Plan, dry_run: bool) -> None:
    print("=== Phase1 plan ===")
    for src, dst in plan.copies:
        print(f"COPY  {src} -> {dst}")
    for path, _t, _e in plan.writes:
        print(f"WRITE {path}")
    for note in plan.notes:
        print(f"NOTE  {note}")
    print(f"TOTAL copies={len(plan.copies)} writes={len(plan.writes)}")
    if dry_run:
        print("DRY-RUN: no changes written")
        return
    for src, dst in plan.copies:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for path, text, enc in plan.writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=enc)
    print("APPLY: done")


def validate(repo: Path, platform: str, new: str) -> None:
    board_rel, cfg_rel, _, main_fmt = PLATFORM[platform]
    products = repo / board_rel / "products" / new
    defconfig = repo / cfg_rel / main_fmt.format(new=new)
    sym = board_sym(platform, new)
    errs = []
    if not products.is_dir():
        errs.append(f"missing {products}")
    if not defconfig.is_file():
        errs.append(f"missing {defconfig}")
    if sym not in read_text(repo / board_rel / "Config.in"):
        errs.append(f"{sym} not in Config.in")
    cfg = read_text(defconfig)
    if f'HMI_PRODUCT_CUSTOMIZE_DIR="{new}"' not in cfg and f"{sym}=y" not in cfg:
        errs.append("defconfig missing board/customize markers")
    if f"{sym}=y" not in cfg:
        errs.append(f"defconfig missing {sym}=y")
    if errs:
        die("validate failed:\n  " + "\n  ".join(errs))
    print("VALIDATE: ok")


def main() -> None:
    ap = argparse.ArgumentParser(description="HMOS project bringup Phase1 clone")
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--platform", required=True, choices=sorted(PLATFORM))
    ap.add_argument("--base", required=True)
    ap.add_argument("--new", required=True, dest="new_product")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    if not repo.is_dir():
        die(f"repo root not found: {repo}")
    if args.base == args.new_product:
        die("base and new must differ")
    # Identity is caller-supplied; do not lowercase or respell.

    if args.platform == "apollo5":
        plan = plan_apollo5(repo, args.base, args.new_product)
    else:
        plan = plan_mhs_family(repo, args.platform, args.base, args.new_product)

    if args.new_product != args.new_product.lower():
        plan.notes.append(
            f"NEW {args.new_product!r} kept as-is (do not lowercase); "
            f"board symbol={board_sym(args.platform, args.new_product)}"
        )

    apply_plan(plan, dry_run=args.dry_run)
    if not args.dry_run and not args.skip_validate:
        validate(repo, args.platform, args.new_product)


if __name__ == "__main__":
    main()
