# -*- coding: utf-8 -*-
"""`.lua` 注册体检 —— 用「按角色判定」的规则找出真正不会被加载的脚本。

背景（2026-09 修订，见 gotchas.md §2/§3）：
  早期结论「不在任何 Action 段 = 不会执行」是**错的**。正确规则是 `.lua` 按角色分三类：

    ① UI 上下文脚本：有同名 `.xml` 且该 xml 在 `<AddUserInterfaces>` 里
       → 引擎**自动加载同名 lua**，只需在打包清单里，**不必**单列 Action。
       （`.xml` 内容允许空着，空的 <GameData></GameData> 占位也行）
    ② include 扩展件 / 官方脚本替代件（`<官方名>_<后缀>.lua`）
       → **必须进 `ImportFiles`**
    ③ GamePlay 脚本 → **必须进 `AddGameplayScripts`**

  角色判定与判据集中在 `_lua_roles.py`（与 `check_lua_context.py` 共用同一份实现）。

用法：
    python check_lua_registration.py <工程根目录> [--modinfo <构建产物.modinfo>]

参数：
    工程根目录        含 `<名>.civ6proj` 的目录
    --modinfo        可选：已构建的 `.modinfo`（默认在 Mods 目录下按工程名找），用它的 Action 段交叉复核

退出码：0 = 未发现问题；1 = 发现可疑项；2 = 参数/文件错误。
"""
import argparse
import os
import sys

import _lua_roles as R

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ACTION_TAGS = R.ACTION_TAGS


def main():
    ap = argparse.ArgumentParser(description=".lua 注册体检")
    ap.add_argument("root", help="工程根目录（含 .civ6proj）")
    ap.add_argument("--modinfo", default=None, help="已构建的 .modinfo（可选，用于交叉复核）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: 目录不存在: %s" % root)
        return 2
    loaded = R.load_project(root)
    if loaded is None:
        print("ERROR: 目录下没有 .civ6proj: %s" % root)
        return 2
    pj, actions, content, content_set, luas = loaded
    action_files = {f for v in actions.values() for f in v}

    print("=" * 78)
    print("%s   Content %d 条 / Action 文件 %d 个 / .lua %d 个"
          % (pj, len(content), len(action_files), len(luas)))
    print("=" * 78)

    issues = []
    for lua in luas:
        role, bad, why = R.classify(lua, content_set, actions, root)
        in_content = lua in content_set
        flag = []
        if bad:
            flag.append("需登记")
        if not in_content and role != R.ROLE_UI_CONTEXT:
            flag.append("★不在打包清单(不会进 Mods)")
            bad = True
        if flag:
            issues.append((lua, role, why, flag))
            print("  [%s] %-46s %s" % (",".join(flag), lua, why))
    if not issues:
        print("  ✓ 未发现问题")
    else:
        print("  --- %d 项待处理 ---" % len(issues))
    print()

    if args.modinfo:
        mp = args.modinfo
        if not os.path.isfile(mp):
            print("WARN: modinfo 不存在，跳过交叉复核: %s" % mp)
        else:
            mt = open(mp, encoding="utf-8", errors="replace").read()
            ma = R.parse_actions(mt)
            print("=== 与构建产物交叉复核 ===")
            for tag in ACTION_TAGS:
                s = set(actions.get(tag, []))
                d = set(ma.get(tag, []))
                only_s, only_d = sorted(s - d), sorted(d - s)
                if only_s or only_d:
                    print("  %s: 仅源 %d / 仅产物 %d" % (tag, len(only_s), len(only_d)))
                    for f in only_s[:5]:
                        print("      -源 %s" % f)
                    for f in only_d[:5]:
                        print("      +产物 %s" % f)
            print()

    print("总待处理项: %d" % len(issues))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
