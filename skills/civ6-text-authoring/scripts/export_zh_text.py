#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_zh_text.py — 从本机游戏安装提取「风云变幻为准」的简体中文有效文本

本脚本是 civ6-text-authoring 的数据底座管线，产出 `reference/zh_effective.json`
（常规类）或 `reference/zh_mode_effective.json`（模式类）+ 差异报告 + tombstone。
语料权威口径见本 skill `SKILL.md` §0。

口径
----
以 Expansion2（风云变幻）为唯一检验标准：
  · 分层 EXP2 > EXP1 > base；各领袖/文明 DLC 对 EXP2 只补缺不覆盖（常规类）
  · **按引擎加载顺序单遍扫描**，包内 <RemoveText>(Priority=2) 先于 <Translations>
  · <Delete> 无 Language 属性 = 全局删除（对 zh_Hans_CN 同样生效）→ tombstone
  · 仅 zh_Hans_CN

两个类别（--class）：
  · main（常规，默认）：本体 + EXP1 + EXP2 + 全部领袖/文明 DLC；**排除** Mode 与 Scenario
    → 对应 SKILL.md 六大分类
  · mode（模式，仅供「模式模块」仅路由使用）：8 个 GAMEMODE 的文本（多在 <包>..._Translations_Text_MODE.xml）
    → ⚠ 官方简体中文大量缺失（值为 `TRANSLATION MISSING`），见 mode-text.md

复用 civ6-modding 的 build_localization.Segment（分段/文件枚举权威实现），不改动既有工具与库。
用法：
    python scripts/export_zh_text.py [--class {main,mode}] [--game <游戏根>] [--out <输出目录>]
退出码：0 = 成功；2 = 找不到游戏或依赖。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAMILY = os.path.dirname(SKILL_ROOT)
DEFAULT_OUT = os.path.join(SKILL_ROOT, "reference")
ZH = "zh_Hans_CN"


def _load_build_localization():
    """定位 civ6-modding 的 build_localization.py（分段权威实现）。"""
    cand = os.path.join(FAMILY, "civ6-modding")
    if not os.path.isdir(cand):
        print("ERROR: 找不到同级 civ6-modding skill（分段实现依赖它）：%s" % cand)
        return None
    scripts = os.path.join(cand, "database", "scripts")
    sys.path.insert(0, os.path.join(cand, "tools"))
    sys.path.insert(0, scripts)
    p = os.path.join(scripts, "build_localization.py")
    if not os.path.isfile(p):
        print("ERROR: 缺少 %s" % p)
        return None
    spec = importlib.util.spec_from_file_location("build_localization", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _game_root(BL, arg: str | None) -> str | None:
    if arg:
        return arg
    try:
        if BL is not None:
            import _paths  # type: ignore
            g = _paths.get("game")
            if g:
                return g
    except Exception:
        pass
    return None


def effective_zh(BL, seg, cls: str) -> tuple[dict, list, dict]:
    """单遍生成有效 zh 文本 → (state{tag:(text,gender,plur,tier,src)}, tombstone, tier_stat)。"""
    event_re = re.compile(
        r'(?P<del><Delete\s+Tag="(?P<del_tag>[^"]+)"(?P<del_lang>\s+Language="[^"]+")?\s*/?>)'
        r'|(?P<rep><Replace\s+Tag="(?P<rep_tag>[^"]+)"(?P<rep_lang>\s+Language="[^"]+")?\s*>(?P<rep_body>.*?)</Replace>)'
        r'|(?P<row><Row\s+Tag="(?P<row_tag>[^"]+)"\s*>(?P<row_body>.*?)</Row>)',
        re.S)
    lang_re = re.compile(r'Language="([^"]+)"')
    txt_re = BL._TEXT_RE
    gender_re = BL._GENDER_RE
    plur_re = BL._PLUR_RE
    langdir_re = BL._LANGDIR_RE

    def aliased(lang: str) -> str:
        return BL.LANG_ALIAS.get(lang.strip(), lang.strip())

    files = []
    for dlc, rel, pr in seg.disk_files(cls):
        files.append((seg.tier_of(dlc), pr, rel, dlc))
    files.sort(key=lambda t: (t[0], -t[1], t[2]))   # 与 build_localization 一致

    state: dict[str, tuple] = {}
    deleted: set[str] = set()
    tier_stat = {"base": 0, "exp1": 0, "exp2": 0, "dlc": 0}
    for tier, pr, rel, dlc in files:
        path = seg.file_path(dlc, rel)
        try:
            s = open(path, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        if "LocalizedText" not in s and "<Delete" not in s and "<Row" not in s:
            continue
        d = os.path.basename(os.path.dirname(path))
        dir_lang = aliased(d) if langdir_re.match(d) else None
        tier_name = BL.RANK_NAME.get(tier, "dlc")
        for m in event_re.finditer(s):
            if m.group("del"):
                lang = lang_re.search(m.group("del_lang") or "")
                lv = aliased(lang.group(1)) if lang else None
                if lv not in (None, ZH):
                    continue
                tag = m.group("del_tag").strip()
                state.pop(tag, None)
                deleted.add(tag)
            else:
                if m.group("rep"):
                    tag = m.group("rep_tag").strip()
                    body = m.group("rep_body")
                    lang = lang_re.search(m.group("rep_lang") or "")
                    lv = aliased(lang.group(1)) if lang else dir_lang
                else:
                    tag = m.group("row_tag").strip()
                    body = m.group("row_body")
                    lv = dir_lang
                if lv not in (None, ZH):
                    continue
                t = txt_re.search(body)
                if not t:
                    continue
                text = "" if t.group(1) is None else t.group(1)
                g = gender_re.search(body)
                p = plur_re.search(body)
                prev = state.get(tag)
                # 常规类：EXP2 已定值时，落后来的领袖 DLC 只补缺不覆盖
                if (cls == "main" and prev is not None
                        and prev[3] == BL.RANK_EXP2 and tier == BL.RANK_DLC):
                    continue
                state[tag] = (text, (g.group(1).strip() if g else None),
                              (p.group(1).strip() if p else None), tier, dlc)
                tier_stat[tier_name] += 1
    return state, sorted(t for t in deleted if t not in state), tier_stat


def _diff_base(cls: str) -> str:
    """比对基准库：常规类用 DebugLocalization.sqlite；模式类用 Localization_Mode.sqlite。"""
    db = "Localization_Mode.sqlite" if cls == "mode" else "DebugLocalization.sqlite"
    return os.path.join(FAMILY, "civ6-modding", "database", db)


def main() -> int:
    ap = argparse.ArgumentParser(description="提取风云变幻口径的简体中文有效文本")
    ap.add_argument("--class", dest="cls", choices=("main", "mode"), default="main",
                    help="main=常规（默认）；mode=模式（模式模块专用）")
    ap.add_argument("--game", default=None, help="游戏安装根（默认按 civ6-modding 的 _paths.py）")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出目录（默认本 skill reference/）")
    args = ap.parse_args()
    cls = args.cls
    prefix = "zh_" if cls == "main" else "zh_mode_"

    BL = _load_build_localization()
    if BL is None:
        return 2
    game = _game_root(BL, args.game)
    if not game or not os.path.isdir(game):
        print("ERROR: 找不到游戏安装目录（用 --game 指定）")
        return 2

    seg = BL.Segment(game)
    seg.report()
    state, tomb, tier_stat = effective_zh(BL, seg, cls)
    miss = sum(1 for t, v in state.items() if "TRANSLATION MISSING" in (v[0] or ""))
    print("\n[%s] 有效 zh 文本: %d tag" % (cls, len(state)))
    print("  tier 累计写入次数: %s" % tier_stat)
    print("  tombstone（删且未复现）: %d" % len(tomb))
    if cls == "mode":
        print("  ⚠ 官方简体中文缺失（TRANSLATION MISSING）: %d / 可用 %d" % (miss, len(state) - miss))

    base_db = _diff_base(cls)
    old = {}
    if os.path.isfile(base_db):
        import sqlite3
        con = sqlite3.connect("file:%s?mode=ro" % base_db.replace("\\", "/"), uri=True)
        try:
            old = {r[0]: (r[1] or "") for r in
                   con.execute("SELECT Tag,Text FROM LocalizedText WHERE Language=?", (ZH,))}
        except sqlite3.OperationalError:
            old = {}
        con.close()
    only_new = sorted(set(state) - set(old))
    only_old = sorted(set(old) - set(state))
    changed = sorted(t for t in (set(state) & set(old))
                     if (state[t][0] or "").strip() != (old[t] or "").strip())
    print("\n比对基准 %s: %d tag" % (os.path.basename(base_db), len(old)))
    print("  本导出独有 %d / 基准独有 %d / 实质不同 %d" % (len(only_new), len(only_old), len(changed)))

    os.makedirs(args.out, exist_ok=True)
    dump = {t: {"text": v[0], "gender": v[1], "plurality": v[2],
                "tier": BL.RANK_NAME.get(v[3], "dlc"), "src": v[4]}
            for t, v in sorted(state.items())}
    with open(os.path.join(args.out, prefix + "effective.json"), "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1)
    with open(os.path.join(args.out, prefix + "tombstones.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tomb))
    with open(os.path.join(args.out, prefix + "diff_report.txt"), "w", encoding="utf-8") as f:
        f.write("本导出独有 (%d):\n%s\n\n基准独有 (%d):\n%s\n\n实质不同 (%d):\n%s\n" % (
            len(only_new), "\n".join(only_new), len(only_old), "\n".join(only_old),
            len(changed), "\n".join("%s\t%s\t%s" % (t, state[t][0], old[t]) for t in changed)))
    print("\n产物: %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
