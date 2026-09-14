# -*- coding: utf-8 -*-
"""核对 .civ6proj 的 <Content Include> 清单与实际磁盘内容是否闭合。

背景：ModBuddy 只把 <Content Include> 列出的文件部署到 Mods 目录；若某 SQL/XML/Lua
只被 InGameActions 引用而未进 Content 清单，就会出现「modinfo 引用它、Mods 副本里却没有」
的悬空引用（示例工程 曾踩坑：Data/Agendas_RGN.sql）。

用法:
    python check_proj_content.py <工程根目录>

输出:
    1) Content 清单里指向磁盘上不存在文件的条目（悬空清单项）
    2) 磁盘上属于「应入库」类别但不在 Content 清单里的文件（漏登记）
退出码: 0 全部闭合；1 存在问题。
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 需要进 Content 清单的类别（对齐 AGENTS.md「Project 文件同步规范」）
TRACKED_EXT = {".sql", ".xml", ".lua"}
# 引擎/工具自动处理、不要求进清单的目录与文件
#   workspace/.git/bin/obj/Cooked —— 非发布内容
#   ArtDefs/ XLPs/ —— 美术资产，走 AssetEditor/cooker 特殊流程，不按普通清单条目同步
#   *.Art.xml / *.civ6proj / *.modinfo —— 工程与美术描述文件，ModBuddy 自行处理
SKIP_DIRS = {"workspace", ".git", "bin", "obj", "Cooked", "ArtDefs", "XLPs"}
SKIP_FILE_SUFFIX = (".art.xml", ".civ6proj", ".modinfo")


def main():
    root = os.path.abspath(sys.argv[1])
    proj = None
    for name in os.listdir(root):
        if name.endswith(".civ6proj"):
            proj = os.path.join(root, name)
    if not proj:
        print("未找到 .civ6proj")
        return 1

    with open(proj, "r", encoding="utf-8-sig") as f:
        text = f.read()

    listed = set()
    for m in re.finditer(r'<Content\s+Include="([^"]+)"', text):
        listed.add(m.group(1).replace("/", "\\"))
    print(".civ6proj: %s" % os.path.basename(proj))
    print("Content 条目数: %d" % len(listed))

    # 1) 清单项 -> 磁盘
    dangling = sorted(p for p in listed if not os.path.isfile(os.path.join(root, p)))
    print("\n[1] 清单指向但磁盘缺失: %d" % len(dangling))
    for p in dangling:
        print("    - " + p)

    # 2) 磁盘 -> 清单
    on_disk = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in TRACKED_EXT:
                continue
            if fn.lower().endswith(SKIP_FILE_SUFFIX):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace("/", "\\")
            on_disk.append(rel)

    missing = sorted(p for p in on_disk if p not in listed)
    print("\n[2] 磁盘存在但未登记进 Content: %d" % len(missing))
    for p in missing:
        print("    - " + p)

    print("\n磁盘应入库文件总数: %d" % len(on_disk))
    ok = not dangling and not missing
    print("RESULT: %s" % ("闭合" if ok else "存在缺口"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
