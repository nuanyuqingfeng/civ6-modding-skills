# -*- coding: utf-8 -*-
"""工程核心文件夹卫生体检 —— 只允许工程文件与处理后的成品素材。

规则真源：civ6-modding/SKILL.md「工程核心文件夹卫生」与 project-setup.md「两层目录布局」。

判定分三档：

  允许    工程描述与版本控制文件、mod 成品目录、处理后可直接进 cook 的素材目录；
  禁止    中间产物与无关文件 —— workspace/ gen/ tmp/ 备份目录、Build/ Cooked/、
          .modinfo、*.log、调试脚本、临时图片、素材库副本；
  唯一例外是工程核心根顶层的 cooker.log（ModBuddy 与 cook 工具的会话日志），
  全解决方案只允许这一份；其唯一性与份数由 scan_cooker_logs() 单独判定。
  未登记  既不在允许表、也不在禁止表的顶层条目 —— 一律报出来，由人裁决。

深度 1 的检查只针对顶层目录与顶层文件（工程核心文件夹的入口）；
禁止项在任意深度的目录树里都会命中（workspace 套在子目录里同样算违规）。
--solution 模式在体检工程核心文件夹之外，另检解决方案根顶层：除「工程主体目录 + workspace +
解决方案文件」外的条目同样报出（中间产物目录／日志文件判禁止，其余列未登记）。
本检查只报告，不授权处置：核心文件夹内的既有文件不得由代理自行迁移或删除，按 AGENTS.md
「文件落盘边界与 Workspace 规范」第 2、3 条询问用户。

用法：
    python check_project_hygiene.py <工程核心文件夹>
    python check_project_hygiene.py <解决方案根> --solution

退出码：0 = 干净；1 = 有违规或未登记项；2 = 参数或目录错误。
"""
import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 允许出现在工程核心文件夹顶层的目录
ALLOWED_DIRS = {
    "Data", "Text", "Scripts", "UI", "ImportFiles",
    "Textures", "XLPs", "ArtDefs", "Assets", "Materials",
    "Geometries", "Animations", "Mod_Adaptation",
    "Behaviors", "DSGs", "EnvironmentLights", "FireFX",
    "LightRigs", "Lights", "ParticleEffects", "Platforms",
    # 版本控制目录（工程仓库根落在核心文件夹时会出现在顶层）
    ".git",
}

# 允许出现在工程核心文件夹顶层的文件后缀（工程描述与版本控制文件）
# .dep 是 ModBuddy 构建期由 <UpdateArt> 占位符展开出的美术依赖清单，
# 位于工程核心根顶层，随 <Files> 一并进入交付包（verify_mod_package.py 硬检查其存在）。
ALLOWED_FILE_EXT = {
    ".civ6proj", ".art.xml", ".dep", ".sln", ".suo",
    ".gitignore", ".gitattributes",
}

# 允许的顶层无后缀文件
ALLOWED_FILE_NAMES = {
    ".gitignore", ".gitattributes", "AGENTS.md", "CLAUDE.md", "README.md",
}

# 任何深度都禁止的目录名
FORBIDDEN_DIRS = {
    "workspace", "gen", "tmp", "Build", "Cooked", "bin", "obj",
    "__pycache__", ".vs", "_prev_mods",
}

# 任何深度都禁止的文件后缀
FORBIDDEN_FILE_EXT = {".log", ".bak", ".tmp", ".pyc"}

# 全解决方案唯一允许的日志：只许在工程核心根顶层出现一份
SANCTIONED_LOG_NAME = "cooker.log"

# 任何深度都禁止的文件名模式（备份目录与备份文件）
FORBIDDEN_NAME_PREFIX = ("_offproj_", "copy_", ".bak_")

# 解决方案根顶层允许的无后缀文件（版本控制与 Agent 规范文件可与解决方案同级）
SOLUTION_ALLOWED_FILE_NAMES = {
    ".gitignore", ".gitattributes", "AGENTS.md", "CLAUDE.md", "README.md",
}
# 解决方案根顶层允许的文件后缀
SOLUTION_ALLOWED_FILE_EXT = {".civ6sln", ".civ6suo", ".code-workspace"}
# 解决方案根顶层允许的目录名（工程主体目录另行按名放行）
SOLUTION_ALLOWED_DIRS = {"workspace", ".git"}


def scan(root):
    """返回 (禁止项, 未登记项)；两项都是 [(相对路径, 说明)]。"""
    forbidden = []
    unknown = []
    root = os.path.abspath(root)

    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        rel = name
        if os.path.isdir(path):
            if name in FORBIDDEN_DIRS:
                forbidden.append((rel + os.sep, "中间产物目录，落点应是 <解决方案根>/workspace/"))
            elif name not in ALLOWED_DIRS:
                unknown.append((rel + os.sep, "顶层目录不在允许表内"))
            continue
        low = name.lower()
        if low == SANCTIONED_LOG_NAME:
            continue
        ext = os.path.splitext(low)[1]
        if ext in FORBIDDEN_FILE_EXT or name.startswith(FORBIDDEN_NAME_PREFIX):
            forbidden.append((rel, "中间产物或备份文件，落点应是 <解决方案根>/workspace/"))
        elif name in ALLOWED_FILE_NAMES or any(low.endswith(x) for x in ALLOWED_FILE_EXT):
            continue
        else:
            unknown.append((rel, "顶层文件不在允许表内"))

    # 任意深度的禁止项（顶层已报的不重复）
    for dirpath, dirnames, filenames in os.walk(root):
        depth = os.path.relpath(dirpath, root).count(os.sep) + (0 if dirpath == root else 1)
        dirnames[:] = [d for d in dirnames if d != ".git"]
        if dirpath == root:
            dirnames[:] = [d for d in dirnames if d not in FORBIDDEN_DIRS]
            continue
        for d in sorted(dirnames):
            if d in FORBIDDEN_DIRS:
                rel = os.path.relpath(os.path.join(dirpath, d), root)
                forbidden.append((rel + os.sep, "任意深度发现的中间产物目录"))
        for fn in sorted(filenames):
            low = fn.lower()
            ext = os.path.splitext(low)[1]
            if ext in FORBIDDEN_FILE_EXT or fn.startswith(FORBIDDEN_NAME_PREFIX):
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                why = ("任意深度发现的中间产物或备份文件" if low != SANCTIONED_LOG_NAME
                       else "第二份 cooker.log —— 只允许工程核心根顶层一份")
                forbidden.append((rel, why))
    return forbidden, unknown


def scan_cooker_logs(solution_root, core_dir):
    """全解决方案的 cooker.log 唯一性：只允许 <工程核心根>/cooker.log 一份。"""
    allowed = os.path.normcase(os.path.join(os.path.abspath(core_dir), SANCTIONED_LOG_NAME))
    found = []
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(solution_root)):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.lower() == SANCTIONED_LOG_NAME:
                found.append(os.path.join(dirpath, fn))
    hits = []
    for p in sorted(found):
        if os.path.normcase(p) != allowed:
            hits.append((os.path.relpath(p, solution_root).replace(os.sep, "/"),
                         "cooker.log 只允许工程核心根顶层一份，其余位置即重复副本"))
    return hits


def scan_solution(solution_root, body_dir):
    """解决方案根顶层体检：只允许工程主体目录、workspace 与解决方案文件。"""
    forbidden = []
    unknown = []
    solution_root = os.path.abspath(solution_root)
    body_name = os.path.basename(os.path.abspath(body_dir))
    for name in sorted(os.listdir(solution_root)):
        path = os.path.join(solution_root, name)
        if os.path.isdir(path):
            if name in SOLUTION_ALLOWED_DIRS or name == body_name:
                continue
            if name in FORBIDDEN_DIRS:
                forbidden.append((name + os.sep, "解决方案根顶层中间产物目录，落点应是 <解决方案根>/workspace/"))
            else:
                unknown.append((name + os.sep, "解决方案根顶层目录不在允许表内"))
            continue
        low = name.lower()
        ext = os.path.splitext(low)[1]
        if ext in FORBIDDEN_FILE_EXT or name.startswith(FORBIDDEN_NAME_PREFIX):
            forbidden.append((name, "解决方案根顶层中间产物或备份文件，落点应是 <解决方案根>/workspace/"))
        elif name in SOLUTION_ALLOWED_FILE_NAMES or ext in SOLUTION_ALLOWED_FILE_EXT:
            continue
        else:
            unknown.append((name, "解决方案根顶层文件不在允许表内"))
    return forbidden, unknown


def main():
    ap = argparse.ArgumentParser(
        description="工程核心文件夹卫生体检：只允许工程文件与处理后的成品素材")
    ap.add_argument("root", help="工程核心文件夹（含 .civ6proj 的那一层）")
    ap.add_argument("--solution", action="store_true",
                    help="传入的是解决方案根：自动定位其中唯一的工程核心文件夹")
    ap.add_argument("--quiet", action="store_true", help="只打印汇总")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR 目录不存在：%s" % root)
        return 2

    solution_root = None
    if args.solution:
        solution_root = root
        hits = []
        for name in sorted(os.listdir(root)):
            d = os.path.join(root, name)
            if not os.path.isdir(d) or name == "workspace":
                continue
            if [f for f in os.listdir(d) if f.lower().endswith(".civ6proj")]:
                hits.append(d)
        if len(hits) != 1:
            print("ERROR 解决方案根下应恰好有 1 个含 .civ6proj 的工程核心文件夹，实际 %d 个：%s"
                  % (len(hits), "、".join(hits) or "无"))
            return 2
        root = hits[0]

    explicit_solution = solution_root is not None
    if solution_root is None:
        solution_root = (root if any(f.lower().endswith(".civ6sln") for f in os.listdir(root))
                         else os.path.dirname(root))

    forbidden, unknown = scan(root)
    cook_log_issues = scan_cooker_logs(solution_root, root)
    s_forbidden, s_unknown = [], []
    if explicit_solution:
        s_forbidden, s_unknown = scan_solution(solution_root, root)

    print("工程核心文件夹：%s" % root)
    print("")
    print("禁止项：%d" % len(forbidden))
    if not args.quiet:
        for rel, why in forbidden:
            print("    %s  —— %s" % (rel, why))
    print("未登记项：%d" % len(unknown))
    if not args.quiet:
        for rel, why in unknown:
            print("    %s  —— %s" % (rel, why))
    print("cooker.log 违规：%d" % len(cook_log_issues))
    if not args.quiet:
        for rel, why in cook_log_issues:
            print("    %s  —— %s" % (rel, why))

    if solution_root:
        print("")
        print("解决方案根：%s" % solution_root)
        print("顶层禁止项：%d" % len(s_forbidden))
        if not args.quiet:
            for rel, why in s_forbidden:
                print("    %s  —— %s" % (rel, why))
        print("顶层未登记项：%d" % len(s_unknown))
        if not args.quiet:
            for rel, why in s_unknown:
                print("    %s  —— %s" % (rel, why))

    print("")
    if forbidden or s_forbidden or cook_log_issues:
        print("FAIL %d 项中间产物或备份落在工程核心文件夹或解决方案根；落点应是 <解决方案根>/workspace/。"
              % (len(forbidden) + len(s_forbidden) + len(cook_log_issues)))
        print("     本检查只报告，不授权处置：核心文件夹内的既有文件不得由代理自行迁移或删除，"
              "按 AGENTS.md「文件落盘边界与 Workspace 规范」第 2、3 条询问用户。")
        return 1
    if unknown or s_unknown:
        print("FAIL %d 项顶层条目不在允许表内；代理不自行处置，由人确认用途后移除、登记或保留。"
              % (len(unknown) + len(s_unknown)))
        return 1
    print("PASS 工程核心文件夹与解决方案根只含工程文件与处理后的成品素材。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
