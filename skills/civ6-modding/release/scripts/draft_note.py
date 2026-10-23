# -*- coding: utf-8 -*-
r"""draft_note.py — 从 git 差异归纳工坊更新说明与台账行草稿

`workshop-intro.md` §三「更新记录编写流程」的执行端：取「上次上传基线」到 `HEAD` 的差异，
按目录与主题分组，产出两份草稿 —— `changeNote`（玩家视角、1~3 条编号、无路径无标识符）
与台账「历史版本」行（规模归因 + 固定小节序列）。草稿一律由人工定稿，本工具不改台账。

基线来源（按序）：`--since` > 台账 `workshop-ledger.md` 的「上传基线：commit <sha>」> 报错退出。
台账基线行形如：

    - 上传基线：commit `abc1234`｜hcontent_file `1234567890`｜time_updated `1791912340`

用法：

    python draft_note.py --project <源工程根> [--since <commit>] [--ledger <台账路径>]
    python draft_note.py --project <源工程根> --out <草稿路径> --date YYYY-MM-DD

退出码：0 成功 / 1 参数、仓库或基线错误 / 2 差异为空（无需更新说明）
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 分组顺序即台账 ① 小节的排列顺序
GROUPS = [
    ("内容与规则", (r"^Data/", r"^Mod_Adaptation/")),
    ("剧本与逻辑", (r"^Scripts/", r"^ImportFiles/")),
    ("界面", (r"^UI/",)),
    ("文本与本地化", (r"^Text/",)),
    ("美术与几何", (r"^XLPs/", r"^ArtDefs/", r"^Assets/", r"^Textures/", r"^Geometries/",
                    r"^Materials/", r"^Animations/", r"^Behaviors/", r"^DSGs/", r"^LightRigs/",
                    r"^Lights/", r"^EnvironmentLights/", r"^FireFX/", r"^ParticleEffects/")),
    ("音频与产物", (r"^Platforms/",)),
    ("工程清单", (r"\.civ6proj$", r"\.modinfo$", r"\.Art\.xml$")),
    ("文档与台账", (r"\.md$",)),
]
OTHER = "其他"

BASELINE_RE = re.compile(
    r"上传基线[：:]\s*commit\s*`?([0-9a-fA-F]{7,40})`?(?:.*?hcontent_file\s*`?(\d+)`?)?",
    re.S)


def git(project: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", project] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit("FAIL git %s 失败：%s" % (" ".join(args), proc.stderr.strip()))
    return proc.stdout


def find_ledger(project: str) -> str | None:
    for name in os.listdir(project):
        if name == "workshop-ledger.md":
            return os.path.join(project, name)
    return None


def baseline_from_ledger(path: str) -> tuple[str | None, str | None]:
    raw = open(path, encoding="utf-8", errors="replace").read()
    m = BASELINE_RE.search(raw)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def group_of(path: str) -> str:
    for name, pats in GROUPS:
        for pat in pats:
            if re.search(pat, path):
                return name
    return OTHER


def main() -> int:
    ap = argparse.ArgumentParser(description="从 git 差异归纳更新说明草稿")
    ap.add_argument("--project", required=True, help="源工程根（git 仓库内）")
    ap.add_argument("--since", default=None, help="上次上传基线的 commit；缺省读台账")
    ap.add_argument("--ledger", default=None, help="台账路径；缺省用工程根下的 workshop-ledger.md")
    ap.add_argument("--out", default=None, help="草稿输出路径；缺省打印到标准输出")
    ap.add_argument("--date", default=None, help="台账行日期，缺省取今天（本机时区）")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    since, hcontent = args.since, None
    if not since:
        ledger = args.ledger or find_ledger(project)
        if not ledger:
            raise SystemExit("FAIL 既未给 --since，工程根下也没有 workshop-ledger.md")
        since, hcontent = baseline_from_ledger(ledger)
        if not since:
            raise SystemExit(
                "FAIL 台账里没有「上传基线：commit <sha>」行（%s）。\n"
                "     首次上传时在上传成功后补录该行；本次可用 --since <commit> 指定范围。" % ledger)
        print("基线（取自台账）：%s" % since)

    head = git(project, "rev-parse", "--short", "HEAD").strip()
    log = git(project, "log", "--oneline", "%s..HEAD" % since).strip()
    name_status = git(project, "diff", "--name-status", "%s..HEAD" % since).strip()
    numstat = git(project, "diff", "--numstat", "%s..HEAD" % since).strip()

    if not name_status:
        print("自 %s 起没有文件改动（%s 与 HEAD 相同），无需更新说明。" % (since, since))
        return 2

    stats = {}
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, dele, path = parts
        stats[path] = (int(add) if add.isdigit() else 0, int(dele) if dele.isdigit() else 0)

    buckets: dict[str, list[tuple[str, str, tuple[int, int]]]] = {}
    for line in name_status.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        buckets.setdefault(group_of(path), []).append((path, status, stats.get(path, (0, 0))))

    total_files = sum(len(v) for v in buckets.values())
    added = sum(s[0] for v in buckets.values() for _, _, s in v)
    deleted = sum(s[1] for v in buckets.values() for _, _, s in v)
    date = args.date or dt.date.today().isoformat()

    lines = ["# 更新说明草稿（基线 %s → HEAD %s，%d 个提交）" % (since, head, len(log.splitlines())), ""]
    lines += ["## 提交", ""]
    lines += ["- " + x for x in log.splitlines()[:40]] or ["- (无)"]
    if len(log.splitlines()) > 40:
        lines.append("- …… 其余 %d 条从略" % (len(log.splitlines()) - 40))

    lines += ["", "## 变更分组（台账 ① 小节按此顺序展开）", ""]
    for name, _ in GROUPS + [(OTHER, ())]:
        if name not in buckets:
            continue
        lines.append("**%s（%d 个文件，+%d/−%d）**" % (
            name, len(buckets[name]),
            sum(s[0] for _, _, s in buckets[name]), sum(s[1] for _, _, s in buckets[name])))
        for path, status, (a, d) in sorted(buckets[name], key=lambda x: -(x[2][0] + x[2][1])):
            lines.append("  - [%s] %s（+%d/−%d）" % (status, path, a, d))
        lines.append("")

    lines += ["## changeNote 草稿（人工定稿：玩家视角、1~3 条、无路径无标识符）", "",
              "1、<本次面向玩家的修复或改动，用一句话说清现象与结果>",
              "2、<新增或强化>",
              "3、<平衡调整或文本与本地化>",
              "",
              "（无面向玩家的实质改动时用默认句：`Update content (%s)`；只换封面或只改介绍时用 "
              "`更新封面 / Updated cover art`。）" % date, ""]

    lines += ["## 台账「历史版本」行草稿", "",
              "- v? — %s — 内容更新（%d 文件，+%d/−%d 行，**有更新说明**，changeNote = \"…\"）："
              % (date, total_files, added, deleted),
              "  ① <本次内容改动，按上面的分组逐项写>",
              "  ② <随行既有改动（非本次任务、随包发布的内容）>",
              "  ③ <流程或策略变更>",
              "  ④ <工作区与元数据（封面、标签、依赖）>",
              "  ⑤ <校验与门禁退出码>",
              "  ⑥ <上传与验证：hcontent_file / time_updated 前后值>",
              "  ⑦ <清理结果与 Mods 本体核对>",
              "  `hcontent_file` `<旧>` → `<新>`；`time_updated` `<旧>` → `<新>`。", ""]

    if hcontent:
        lines += ["（台账登记的上次 hcontent_file：%s）" % hcontent, ""]

    text = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("已写入草稿：%s" % args.out)
    else:
        print(text)
    print("合计：%d 个文件，+%d/−%d 行，%d 个提交" % (total_files, added, deleted, len(log.splitlines())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
