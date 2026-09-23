# -*- coding: utf-8 -*-
"""归一化文本文件换行：mod 工程按「原版分层铁律」，skill 仓库一律 LF（`--repo-skill`）。

为什么需要分层（2026-09-16 原版随机抽样实测，Base / DLC / SDK Assets 各 ≤40）：

    LF  为主：.artdef(38/40) .ast .mtl .geo .env .anm .xlp .lrg .txt .tex
    CRLF 为主：.lua(40/40) .sql(17/17) .xml(40/40) .modinfo(40/40)

    → AssetEditor / cooker 输出的资产类文本一律 LF；
      Lua / SQL / XML 这类「代码与配置」原版一律 CRLF。
      混用会让「源 ↔ Mods 副本」出现永久伪差异，也让 diff 噪声淹没真实改动。

★ 真二进制扩展名（含 NUL 字节，换行无意义）必须排除，绝不按换行处理：
      .fgx(25/25) .wig(25/25) .dds .bik .bnk .wem .png
  另外逐文件做 NUL 检测：任何文件命中即跳过（防个别资产是二进制却被按文本改写）。

模式:
  ① **mod 工程**（默认）：按上面的「分层铁律」——资产类 LF、代码/配置类 CRLF。
  ② **skill 仓库**（`--repo-skill`）：**一律 LF**。skill 仓库不是 civ6 工程，
     无须迁就原版口径；两仓库 `.gitattributes` 均为 `* text=auto eol=lf`。
     该模式额外覆盖 `.md/.py/.ps1/.json/.txt/.csv` 等**分层表未定义**的扩展名
     （默认模式下它们被归入"非目标扩展名跳过"，这正是工作区 CRLF 残留的原因）。

用法:
    python normalize_eol.py <工程目录>                 # 只报告，不写盘（默认）
    python normalize_eol.py <工程目录> --fix           # 就地归一化
    python normalize_eol.py <工程目录> --fix --quiet
    python normalize_eol.py <工程目录> --only .lua,.xml
    python normalize_eol.py <工程目录> --exclude workspace,.git
    python normalize_eol.py <skill仓库> --repo-skill --fix   # skill 自身清理（全 LF）

诊断工作区漂移（推荐先用它看清单，再决定是否 --fix）:
    git -C <仓库> ls-files --eol | grep w/crlf
    # i/lf + w/crlf = 索引正确、仅工作区漂移 → 归一化不会改变已提交内容

退出码: 0 已达成目标风格（或 --fix 后全部完成）；1 仍存在偏离（报告模式）。
"""
import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── 分层规则（唯一真源；改这里即可调整策略）──────────────────────────
# 目标换行为 LF 的扩展名：原版资产系（AssetEditor / cooker 产物）
LF_EXT = {
    ".artdef", ".xlp", ".ast", ".mtl", ".geo", ".env", ".anm", ".lrg",
    ".txt", ".tex", ".blp", ".blb", ".s3d",
}
# 目标换行为 CRLF 的扩展名：原版代码/配置系
CRLF_EXT = {
    ".lua", ".sql", ".xml", ".modinfo", ".civ6proj", ".ini",
}
# ── skill 仓库自身（`--repo-skill`）：**一律 LF** ──────────────────────
# 与 mod 工程的「分层铁律」不同：skill 仓库不是 civ6 工程，无需迁就原版口径，
# 且两仓库的 .gitattributes 都声明 `* text=auto eol=lf`。这些扩展名在原版分层表里
# **没有条目**，早先会被归入"非目标扩展名跳过"，导致工作区 CRLF 长期残留
# （表现为 `git ls-files --eol` 报 `i/lf w/crlf`：索引正确、工作区漂移）。
SKILL_EXT = {
    ".md", ".py", ".ps1", ".json", ".txt", ".csv", ".jsonc", ".yml", ".yaml",
    ".toml", ".cfg", ".ini", ".sh", ".mjs", ".cjs", ".ts",
}
# 真二进制：换行概念不适用，直接排除（不参与统计）
BINARY_EXT = {
    ".fgx", ".wig", ".dds", ".bik", ".bnk", ".wem", ".png", ".jpg",
    ".jpeg", ".tga", ".ogg", ".wav", ".bk2", ".astc", ".db", ".sqlite",
}
# 默认跳过的目录
SKIP_DIRS = {"workspace", ".git", "bin", "obj", "Cooked", "__pycache__"}

TARGET = {}
for _e in LF_EXT:
    TARGET[_e] = "LF"
for _e in CRLF_EXT:
    TARGET[_e] = "CRLF"


def is_binary(raw: bytes) -> bool:
    """含 NUL 字节即视为二进制（读头部即可，足够可靠）。"""
    return b"\x00" in raw[:65536]


def eol_kind(raw: bytes) -> str:
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    if crlf and lf:
        return "MIXED"
    if crlf:
        return "CRLF"
    if lf:
        return "LF"
    return "NONE"


def to_lf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def convert(raw: bytes, target: str) -> bytes:
    """归一化换行；不动 BOM，也不增删文件末尾换行。

    注意：无换行的文件（`eol_kind == "NONE"`）不走这里 —— 调用方已直接计为符合，
    避免对单行 JSON 之类做无意义写盘。
    """
    lf = to_lf(raw)
    if target == "LF":
        return lf
    # CRLF：先把所有换行统一成 LF，再整体替换，避免二次转换产生 \r\r\n
    return lf.replace(b"\n", b"\r\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="按原版换行分层铁律归一化文本文件")
    ap.add_argument("root", help="工程根目录")
    ap.add_argument("--fix", action="store_true", help="就地写入（默认只报告）")
    ap.add_argument("--only", default=None,
                    help="只处理这些扩展名，逗号分隔（如 .lua,.xml）")
    ap.add_argument("--exclude", default=None,
                    help="额外排除的目录名，逗号分隔")
    ap.add_argument("--repo-skill", action="store_true",
                    help="按 **skill 仓库** 口径处理：目标一律 LF（含 .md/.py/.ps1/.json/.txt/.csv 等），"
                         "用于清理 skill 自身的工作区行尾漂移；不要用于 mod 工程")
    ap.add_argument("--quiet", action="store_true", help="只打印汇总")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("FAIL 目录不存在：%s" % root)
        return 2

    skip_dirs = set(SKIP_DIRS)
    if args.exclude:
        skip_dirs |= {d.strip() for d in args.exclude.split(",") if d.strip()}

    only = None
    if args.only:
        only = {"." + e.strip().lstrip(".").lower() for e in args.only.split(",") if e.strip()}

    # 目标表：默认 = 原版分层铁律；--repo-skill = skill 仓库（全 LF，含分层表未定义的扩展名）
    target_map = dict(TARGET)
    if args.repo_skill:
        for _e in SKILL_EXT:
            target_map[_e] = "LF"
        # 分层表里原本要求 CRLF 的，在 skill 仓库里也应为 LF
        for _e in CRLF_EXT:
            target_map[_e] = "LF"

    changed, ok, skipped_bin, skipped_other = [], 0, [], 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in skip_dirs]
        for fn in sorted(fns):
            ext = os.path.splitext(fn)[1].lower()
            if only is not None and ext not in only:
                continue
            if ext in BINARY_EXT:
                continue
            target = target_map.get(ext)
            if not target:
                skipped_other += 1
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root)
            try:
                with open(p, "rb") as f:
                    raw = f.read()
            except OSError as e:
                print("WARN 读取失败 %s: %s" % (rel, e))
                continue
            if is_binary(raw):
                skipped_bin.append(rel)
                continue
            kind = eol_kind(raw)
            if kind == target:
                ok += 1
                continue
            if kind == "NONE":
                # 无任何换行（如单行 JSON）：转换是 no-op，报"需归一化"只会制造噪声与
                # 无意义的写盘。计为已符合，不动文件。
                ok += 1
                continue
            new = convert(raw, target)
            changed.append((rel, kind, target, len(raw), len(new)))
            if args.fix:
                with open(p, "wb") as f:
                    f.write(new)

    if not args.quiet:
        for rel, kind, target, before, after in changed:
            print("  %-6s -> %-5s  %s" % (kind, target, rel))

    print()
    print("已符合目标 = %d" % ok)
    print("%s = %d" % ("已归一化" if args.fix else "需归一化", len(changed)))
    if skipped_bin:
        print("按二进制跳过 = %d%s" % (
            len(skipped_bin),
            "：" + ", ".join(skipped_bin[:5]) + (" ..." if len(skipped_bin) > 5 else "")
            if not args.quiet else ""))
    if skipped_other:
        print("非目标扩展名跳过 = %d" % skipped_other)

    if changed and not args.fix:
        print("\n[!] 以上 %d 个文件换行偏离目标；加 --fix 执行归一化。" % len(changed))
        return 1
    print("\n[OK] 换行风格已符合分层铁律")
    return 0


if __name__ == "__main__":
    sys.exit(main())
