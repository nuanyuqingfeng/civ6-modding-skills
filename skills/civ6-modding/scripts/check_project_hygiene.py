# -*- coding: utf-8 -*-
"""工程核心文件夹卫生体检 —— 只允许工程文件与处理后的成品素材。

规则真源：civ6-modding/SKILL.md「工程核心文件夹卫生」与 project-setup.md「两层目录布局」。

判定分三档：

  允许    工程描述与版本控制文件、mod 成品目录、处理后可直接进 cook 的素材目录；
  禁止    中间产物与无关文件 —— workspace/ gen/ tmp/ 备份目录、Build/ Cooked/、
          .modinfo、*.log、调试脚本、临时图片、素材库副本；
  未登记  既不在允许表、也不在禁止表的顶层条目 —— 一律报出来，由人裁决。

深度 1 的检查只针对顶层目录与顶层文件（工程核心文件夹的入口）；
禁止项在任意深度的目录树里都会命中（workspace 套在子目录里同样算违规）。

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
}

# 允许出现在工程核心文件夹顶层的文件后缀（工程描述与版本控制文件）
ALLOWED_FILE_EXT = {
    ".civ6proj", ".art.xml", ".sln", ".suo",
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

# 任何深度都禁止的文件名模式（备份目录与备份文件）
FORBIDDEN_NAME_PREFIX = ("_offproj_", "copy_", ".bak_")


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
                forbidden.append((rel, "任意深度发现的中间产物或备份文件"))
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

    if args.solution:
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

    forbidden, unknown = scan(root)

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

    print("")
    if forbidden:
        print("FAIL %d 项中间产物或备份落在工程核心文件夹；移到 <解决方案根>/workspace/ 后重跑。"
              % len(forbidden))
        return 1
    if unknown:
        print("FAIL %d 项顶层条目不在允许表内；确认用途后要么移除，要么登记到脚本的允许表。"
              % len(unknown))
        return 1
    print("PASS 工程核心文件夹只含工程文件与处理后的成品素材。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
