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

本脚本按此规则判定，只报「真的会不生效」的组合。

用法：
    python check_lua_registration.py <工程根目录> [--modinfo <构建产物.modinfo>]

参数：
    工程根目录        含 `<名>.civ6proj` 的目录
    --modinfo        可选：已构建的 `.modinfo`（默认在 Mods 目录下按工程名找），用它的 Action 段交叉复核

退出码：0 = 未发现问题；1 = 发现可疑项；2 = 参数/文件错误。
"""
import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ACTION_TAGS = ("AddUserInterfaces", "ImportFiles", "AddGameplayScripts",
               "UpdateDatabase", "UpdateText", "UpdateIcons", "UpdateColors",
               "UpdateArt", "UpdateAudio", "ReplaceUIScript")

# include 扩展件 / 官方脚本替代件的命名特征：
#   <官方名>_<后缀>.lua —— 靠官方 include("<官方名>_", true) 通配拉入
# 官方常用基名（非穷举，仅作提示）
OFFICIAL_STEMS = (
    "CityBannerManager", "NotificationPanel", "TechAndCivicUnlockables",
    "GreatWorkShowcase", "SecretSocietyPopup", "RockBandMoviePopup",
    "UnitPanel", "CityPanel", "WorldTracker", "TechCivicCompletedPopup",
    "GovernorAssignmentChooser", "PlotTooltip", "UnitFlagManager",
    "GreatPeoplePopup", "CivilopediaPage",
)


def norm(p):
    return p.replace("\\", "/").lstrip("./")


def parse_actions(text):
    """返回 {tag: [files...]}（同名 tag 合并）。

    ★ 实现注意：**不要**用 `<Tag ...>…</Tag>` 成对匹配。
    `.civ6proj` / `.modinfo` 里存在**自闭合**的动作标签（如 `<UpdateAudio id="Audio" />`），
    成对匹配会让它一路吞到下一个同名闭合标签，把中间夹着的其它动作整块吃掉
    （实测踩过：`UpdateAudio` 吞掉了紧随其后的 `ImportFiles` 与 `AddUserInterfaces`，
    导致这两个动作的文件全部漏判 → 假阳性）。

    改用**边界法**：动作段 = 本动作开标签 → 下一个动作开标签之间的文本。
    这对自闭合标签、嵌套结构都稳健，且与文件的实际书写方式一致。
    """
    opens = list(re.finditer(r'<(%s)\b[^>]*?/?>' % "|".join(ACTION_TAGS), text, re.I))
    out = {}
    for i, m in enumerate(opens):
        tag = m.group(1)
        start = m.end()
        end = opens[i + 1].start() if i + 1 < len(opens) else len(text)
        body = text[start:end]
        files = [norm(x.strip()) for x in re.findall(r'<File>\s*([^<]+?)\s*</File>', body, re.I)]
        out.setdefault(tag, []).extend(files)
    return out


def parse_content(text):
    return [norm(x.strip()) for x in
            re.findall(r'<Content\s+Include="([^"]+)"', text, re.I)]


def classify(lua, content_set, actions, project_root):
    """判断这个 `.lua` 有没有**有效加载路径**。

    有效路径只有三条（对应 gotchas.md §2/§3 的角色划分）：
      (a) 在 `AddGameplayScripts` 里            → GamePlay 脚本
      (b) 在 `ImportFiles` 里                   → include 可见 / 官方脚本替代件
      (c) 有**同名 `.xml` 且该 xml 在 `AddUserInterfaces` 里** → 引擎自动加载

    ★ 注意判定次序：(b) 必须先于 (c)。官方/工程的「同名 xml + lua 一起放进 `ImportFiles`」
    是**整体替换**写法（如 `GovernorAssignmentChooser`），同样满足 (b)，
    不能因为「xml 不在 AddUserInterfaces」就误报 —— 那是我第一版犯过的假阳性。

    返回 (角色编号, 是否为问题, 说明)
    """
    stem = lua[:-4]
    xml = stem + ".xml"
    has_xml = (xml in content_set) or os.path.isfile(
        os.path.join(project_root, xml.replace("/", os.sep)))
    in_add_xml = xml in actions.get("AddUserInterfaces", [])
    in_import = lua in actions.get("ImportFiles", [])
    in_gp = lua in actions.get("AddGameplayScripts", [])
    in_any_action = any(lua in v for v in actions.values())

    base = os.path.basename(lua)
    looks_extension = any(base.startswith(s + "_") for s in OFFICIAL_STEMS)

    # (a) GamePlay
    if in_gp:
        return 3, False, "GamePlay 脚本（已在 AddGameplayScripts）"
    # (b) ImportFiles —— 优先判定，覆盖「整体替换」写法
    if in_import:
        return 2, False, "已在 ImportFiles（include 可见 / 官方脚本替代件）"
    # (c) 同名 xml 在 AddUserInterfaces → 引擎自动加载同名 lua
    if has_xml and in_add_xml:
        return 1, False, "UI 上下文脚本（同名 xml 已在 AddUserInterfaces）→ 引擎自动加载"
    # 以下都是「找不到有效路径」
    if has_xml:
        return 1, True, ("有同名 xml，但该 xml **不在** AddUserInterfaces、本 lua 也不在 ImportFiles"
                         " → 无有效加载路径")
    if looks_extension:
        return 2, True, "★ 形如 include 扩展件 / 官方脚本替代件，但**不在 ImportFiles** → 不生效"
    if in_any_action:
        return 0, False, "已在其它动作段（非 GP/ImportFiles，通常无加载效果，请人工确认）"
    return 3, True, "★ 无同名 xml、不在任何加载段 → 需人工确认它的加载方式"


def main():
    ap = argparse.ArgumentParser(description=".lua 注册体检")
    ap.add_argument("root", help="工程根目录（含 .civ6proj）")
    ap.add_argument("--modinfo", default=None, help="已构建的 .modinfo（可选，用于交叉复核）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: 目录不存在: %s" % root)
        return 2
    projs = [f for f in os.listdir(root) if f.lower().endswith(".civ6proj")]
    if not projs:
        print("ERROR: 目录下没有 .civ6proj: %s" % root)
        return 2

    total_issues = 0
    for pj in sorted(projs):
        text = open(os.path.join(root, pj), encoding="utf-8", errors="replace").read()
        actions = parse_actions(text)
        content = parse_content(text)
        content_set = set(content)
        action_files = {f for v in actions.values() for f in v}

        luas = sorted({f for f in content if f.lower().endswith(".lua")})
        luas += sorted({f for f in action_files if f.lower().endswith(".lua")})
        luas = sorted(set(luas))

        print("=" * 78)
        print("%s   Content %d 条 / Action 文件 %d 个 / .lua %d 个"
              % (pj, len(content), len(action_files), len(luas)))
        print("=" * 78)

        issues = []
        for lua in luas:
            role, bad, why = classify(lua, content_set, actions, root)
            in_content = lua in content_set
            flag = []
            if bad:
                flag.append("需登记")
            if not in_content and role != 1:
                flag.append("★不在打包清单(不会进 Mods)")
                bad = True
            if flag:
                issues.append((lua, role, why, flag))
                print("  [%s] %-46s %s" % (",".join(flag), lua, why))
        if not issues:
            print("  ✓ 未发现问题")
        else:
            print("  --- %d 项待处理 ---" % len(issues))
        total_issues += len(issues)
        print()

    # 可选：与构建产物交叉复核
    if args.modinfo:
        mp = args.modinfo
        if not os.path.isfile(mp):
            print("WARN: modinfo 不存在，跳过交叉复核: %s" % mp)
        else:
            mt = open(mp, encoding="utf-8", errors="replace").read()
            ma = parse_actions(mt)
            mfiles = set(f for v in ma.values() for f in v)
            print("=== 与构建产物交叉复核 ===")
            for tag in ACTION_TAGS:
                s = set(parse_actions(open(os.path.join(root, [f for f in os.listdir(root) if f.lower().endswith('.civ6proj')][0]), encoding='utf-8', errors='replace').read()).get(tag, []))
                d = set(ma.get(tag, []))
                only_s, only_d = sorted(s - d), sorted(d - s)
                if only_s or only_d:
                    print("  %s: 仅源 %d / 仅产物 %d" % (tag, len(only_s), len(only_d)))
                    for f in only_s[:5]:
                        print("      -源 %s" % f)
                    for f in only_d[:5]:
                        print("      +产物 %s" % f)
            print()

    print("总待处理项: %d" % total_issues)
    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main())
