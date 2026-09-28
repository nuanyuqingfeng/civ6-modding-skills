# -*- coding: utf-8 -*-
"""`.lua` 角色判定单一真源。

被 `check_lua_registration.py`（判加载路径）与 `check_lua_context.py`（判跨上下文可达性）共同 import，
禁止在调用方复制第二份判定逻辑。

判定规则见 gotchas.md §2/§3：① UI 上下文脚本 / ② include 扩展件 / ③ GamePlay 脚本。
"""
import os
import re

ACTION_TAGS = ("AddUserInterfaces", "ImportFiles", "AddGameplayScripts",
               "UpdateDatabase", "UpdateText", "UpdateIcons", "UpdateColors",
               "UpdateArt", "UpdateAudio", "ReplaceUIScript")

# include 扩展件 / 官方脚本替代件的命名特征：
#   <官方名>_<后缀>.lua —— 靠官方 include("<官方名>_", true) 通配拉入
OFFICIAL_STEMS = (
    "CityBannerManager", "NotificationPanel", "TechAndCivicUnlockables",
    "GreatWorkShowcase", "SecretSocietyPopup", "RockBandMoviePopup",
    "UnitPanel", "CityPanel", "WorldTracker", "TechCivicCompletedPopup",
    "GovernorAssignmentChooser", "PlotTooltip", "UnitFlagManager",
    "GreatPeoplePopup", "CivilopediaPage",
)

ROLE_UI_CONTEXT = 1
ROLE_INCLUDE_LIB = 2
ROLE_GAMEPLAY = 3
ROLE_UNKNOWN = 0

ROLE_NAMES = {
    ROLE_UI_CONTEXT: "UI 上下文脚本",
    ROLE_INCLUDE_LIB: "include 共享库 / 官方脚本替代件",
    ROLE_GAMEPLAY: "GamePlay 脚本",
    ROLE_UNKNOWN: "未分类",
}


def norm(p):
    return p.replace("\\", "/").lstrip("./")


def parse_actions(text):
    """返回 {tag: [files...]}（同名 tag 合并）。

    ★ 实现注意：**不要**用 `<Tag ...>…</Tag>` 成对匹配。
    `.civ6proj` / `.modinfo` 里存在**自闭合**的动作标签（如 `<UpdateAudio id="Audio" />`），
    成对匹配会让它一路吞到下一个同名闭合标签，把中间夹着的其它动作整块吃掉
    （实测踩过：`UpdateAudio` 吞掉了紧随其后的 `ImportFiles` 与 `AddUserInterfaces`）。
    改用**边界法**：动作段 = 本动作开标签 → 下一个动作开标签之间的文本。
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
    return [norm(x.strip()) for x in re.findall(r'<Content\s+Include="([^"]+)"', text, re.I)]


def find_project(root):
    projs = sorted(f for f in os.listdir(root) if f.lower().endswith(".civ6proj"))
    return projs[0] if projs else None


def load_project(root):
    """读工程，返回 (civ6proj 名, actions, content 列表, content 集合, 工程内全部 .lua 相对路径)。"""
    pj = find_project(root)
    if pj is None:
        return None
    text = open(os.path.join(root, pj), encoding="utf-8", errors="replace").read()
    actions = parse_actions(text)
    content = parse_content(text)
    action_files = {f for v in actions.values() for f in v}
    luas = set(f for f in content if f.lower().endswith(".lua"))
    luas |= set(f for f in action_files if f.lower().endswith(".lua"))
    return pj, actions, content, set(content), sorted(luas)


def classify(lua, content_set, actions, project_root):
    """判断一个 `.lua` 的角色与加载路径有效性。

    有效路径只有三条：
      (a) 在 `AddGameplayScripts` 里            → GamePlay 脚本
      (b) 在 `ImportFiles` 里                   → include 可见 / 官方脚本替代件
      (c) 有**同名 `.xml` 且该 xml 在 `AddUserInterfaces` 里** → 引擎自动加载

    ★ 判定次序：(b) 必须先于 (c)。官方/工程的「同名 xml + lua 一起放进 `ImportFiles`」
    是**整体替换**写法（如 `GovernorAssignmentChooser`），同样满足 (b)，
    不能因为「xml 不在 AddUserInterfaces」就误报。

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

    if in_gp:
        return ROLE_GAMEPLAY, False, "GamePlay 脚本（已在 AddGameplayScripts）"
    if in_import:
        return ROLE_INCLUDE_LIB, False, "已在 ImportFiles（include 可见 / 官方脚本替代件）"
    if has_xml and in_add_xml:
        return ROLE_UI_CONTEXT, False, "UI 上下文脚本（同名 xml 已在 AddUserInterfaces）→ 引擎自动加载"
    if has_xml:
        return ROLE_UI_CONTEXT, True, ("有同名 xml，但该 xml **不在** AddUserInterfaces、本 lua 也不在 ImportFiles"
                                       " → 无有效加载路径")
    if looks_extension:
        return ROLE_INCLUDE_LIB, True, "★ 形如 include 扩展件 / 官方脚本替代件，但**不在 ImportFiles** → 不生效"
    if in_any_action:
        return ROLE_UNKNOWN, False, "已在其它动作段（非 GP/ImportFiles，通常无加载效果，请人工确认）"
    return ROLE_GAMEPLAY, True, "★ 无同名 xml、不在任何加载段 → 需人工确认它的加载方式"


def read_lua(project_root, rel):
    path = os.path.join(project_root, rel.replace("/", os.sep))
    if not os.path.isfile(path):
        return None
    return open(path, encoding="utf-8", errors="replace").read()
