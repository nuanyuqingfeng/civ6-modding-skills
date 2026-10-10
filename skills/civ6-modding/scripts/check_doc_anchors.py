# -*- coding: utf-8 -*-
"""跨上下文口径的文档指针一致性体检。

真源：`civ6-modding/reference/context-matrix.md`（矩阵、术语、症状表全在那里）。

两条规则：
  规则一  「结论行」必须带 context-matrix.md 指针。结论行的判据：出现跨上下文 / 跨端 /
          跨脚本 / 同端 这类关系词，或同一行命中两个以上 API 关键词（EXECUTE_SCRIPT /
          ReportingEvents / ExposedMembers / LuaEvents）。单纯调用 API 的行不算结论行。
          指针可以落在结论行本身，或它的前两行 / 后两行内（标题、代码块放不下指针）。
  规则二  带指针且提到 LuaEvents 的结论行，必须同时含「不可达」「只有」「唯一」这类排他
          结论词，防止指针退化成一句空链接。

豁免用**显式表格**声明（文件名 + 理由），命中即跳过并在末尾列出，不静默跳过。
历史记录、事故复盘、实测数据文件天然保留当时的措辞，属于豁免范围。

用法：
    python check_doc_anchors.py [--skills <skills 根目录>]

退出码：0 = 未发现问题；1 = 发现违规行；2 = 参数/文件错误。
"""
import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

POINTER = "context-matrix.md"

SKILL_DIRS = ("civ6-modding", "civ6-tuner", "civ6-asset-forge", "civ6-art-reference", "civ6-audio-pipeline")

KEYWORDS = ("EXECUTE_SCRIPT", "ReportingEvents", "ExposedMembers", "LuaEvents")

# 关系词：出现这些词的才是「结论行」；单纯使用 API（LuaEvents.X.Add 之类）不算
RELATION = ("跨上下文", "跨端", "跨脚本", "跨文件", "跨 Lua", "同端", "不跨")
# 工具名录表格行（skill_manifest.py 生成的清单）不算结论行
RE_MANIFEST_ROW = re.compile(r"^\|\s*`?scripts?/")

# L0 检索命令与词表行本身必然包含全部关键词，不算结论行
RE_SEARCH_CMD = re.compile(r"Select-String\s+-Path|--pattern|Pattern\s*=\s*\"")

# 强关系词：单独出现即判定为结论行，裸「跨文件」不算（它在别的语境里也用）
STRONG_RELATION = ("跨上下文", "跨端", "跨脚本", "同端", "不跨")

EXCLUSIVE = ("不可达", "只有", "唯一", "不跨端", "禁止跨端", "不达", "副本", "不是同一实例", "两个不同实例")

# 指针可以落在结论行的同一行、前两行或后两行内（标题、代码块这类行放不下指针）
WINDOW_BEFORE = 2
WINDOW_AFTER = 2

# 关键词必须带指针的文件豁免（文件名子串 → 理由）
EXEMPT_FILES = {
    "reference/context-matrix.md": "真源自身",
    "CHANGELOG.md": "变更记录，保留当时措辞",
    "history.md": "历史沿革记录",
    "CALIBRATION_LOG_2026-08.md": "校准日志",
    "审核清单.md": "人工审核记录",
    "API范围验证报告.md": "实测报告，记录当时原文",
    "实装记录.md": "实装记录",
}

SKIP_PARTS = ("\\.git", "node_modules", "workspace", "api-verification-2026-09-08")


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description="跨上下文文档指针一致性体检")
    ap.add_argument("--skills", default=os.path.expanduser("~/.agents/skills"),
                    help="skills 根目录，默认 ~/.agents/skills")
    ap.add_argument("--only", default=None, help="只查这一个 skill 目录（调试用）")
    args = ap.parse_args()

    base = os.path.abspath(args.skills)
    if not os.path.isdir(base):
        print("ERROR: skills 根目录不存在: %s" % base)
        return 2
    targets = [args.only] if args.only else list(SKILL_DIRS)

    violations, exempt_hits = [], []
    scanned = 0

    for sk in targets:
        root = os.path.join(base, sk)
        if not os.path.isdir(root):
            print("WARN: 跳过不存在的 skill: %s" % sk)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__", "workspace")]
            for fn in filenames:
                if not fn.lower().endswith(".md"):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, base).replace(os.sep, "/")
                if any(p in rel for p in SKIP_PARTS):
                    continue
                reason = next((v for k, v in EXEMPT_FILES.items() if rel.endswith(k)), None)
                scanned += 1
                if reason:
                    exempt_hits.append((rel, reason))
                    continue
                all_lines = read_text(path).splitlines()
                for i, line in enumerate(all_lines, 1):
                    if RE_MANIFEST_ROW.match(line.strip()) or RE_SEARCH_CMD.search(line):
                        continue
                    hits = sum(1 for k in KEYWORDS if k in line)
                    strong = any(r in line for r in STRONG_RELATION)
                    if hits < 2 and not strong:
                        continue
                    window = "\n".join(all_lines[max(0, i - 1 - WINDOW_BEFORE):i + WINDOW_AFTER])
                    has_ptr = POINTER in window
                    if not has_ptr:
                        violations.append((rel, i, "规则一", "有关键词但无指针: " + line.strip()[:110]))
                    elif "LuaEvents" in line and not any(x in window for x in EXCLUSIVE):
                        violations.append((rel, i, "规则二", "有指针但无排他结论: " + line.strip()[:110]))

    print("=" * 78)
    print("扫描 %d 个 .md（%s）" % (scanned, ", ".join(targets)))
    print("=" * 78)
    for rel, ln, rule, msg in violations:
        print("  %s:%d  [%s] %s" % (rel, ln, rule, msg))
    if not violations:
        print("  ✓ 指针与结论一致")
    if exempt_hits:
        print()
        print("  文件级豁免:")
        for rel, reason in sorted(set(exempt_hits)):
            print("    %s  —— %s" % (rel, reason))
    print()
    print("违规行: %d / 豁免文件: %d" % (len(violations), len(set(r for r, _ in exempt_hits))))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
