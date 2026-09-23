#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""pick_vanilla_background.py — 「借用原版领袖背景」的量化挑选 + 接线产出

配套 `reference/frontend-portrait.md` §三。解决：**mod 领袖没有自有背景素材时，
从官方已装的领袖背景里按整体色调近似程度挑一张复用**。

## 机制（官方自己的做法：XLP 别名条目）

XLP 条目的 `m_EntryID` 与 `m_ObjectName` 可以不同 —— 后者才是真正的贴图名。
官方实测别名（`Shell_Loading.xlp` 2 条、`UI_Leaders.xlp` 2 条、`UI_LeaderScenes.xlp` 23 条）：
    <m_EntryID  text="LEADER_CATHERINE_DE_MEDICI_BACKGROUND"/>
    <m_ObjectName text="LEADER_CATHERINE_BACKGROUND"/>
→ 所以 `Players.PortraitBackground` **可以直接填别人的 `LEADER_*_BACKGROUND`**，零素材复制。

## 选取口径（本 skill 新增约定，非原版事实）

官方**没有**任何跨领袖背景借用（全表扫描证实），所以规则由本工具定义：

  硬条件：候选 `pack` ∈ 目标工程已依赖的 DLC（`--allow-pack`，默认 Base + Expansion1 + Expansion2）
  软条件：score = 环形色相距离/180 * 0.7 + |Δ亮度|/255 * 0.3，取最小；Δh > 60° 判为不相似

色相用「饱和度×明度加权的圆平均」（排除 S·V < 0.02 的近黑像素），
比朴素平均更贴近人眼对"整体色调"的感知，且天然规避跨 0° 的暖色断档。

## 调色板缓存

`reference/vanilla-leader-backgrounds.json`（随 skill 分发）。缺失或 `--rebuild` 时，
从本机 SDK pantry 现场重建（需要 Pillow + 已安装的游戏 SDK Assets）。

## 用法

    # ① 列出全部官方背景的色相/亮度（人工挑选用）
    python pick_vanilla_background.py --list

    # ② 给参考图，推荐 top-N（只读，不写盘）
    python pick_vanilla_background.py --reference <立绘.png> --top 5

    # ③ 预演接线（不写盘）
    python pick_vanilla_background.py --project <工程根> --leader LEADER_X_QYQXP \
        --reference <立绘.png> --check

    # ④ 落盘：写别名 XLP 条目 + 打印 Players/LoadingInfo 该填什么
    python pick_vanilla_background.py --project <工程根> --leader LEADER_X_QYQXP \
        --reference <立绘.png> --write

    # ⑤ 手动指定（跳过挑选，直接接线）
    python pick_vanilla_background.py --project <工程根> --leader LEADER_X_QYQXP \
        --pick LEADER_HOJO_BACKGROUND --write

退出码：0 成功 / 1 参数或数据错误 / 2 有告警（可继续）。

## 铁律

本 skill 通用铁律一：**素材决策必须先问用户**。本工具默认 `--check` 只预演；
`--write` 必须由调用方（AI）在**用户确认候选后**才加。
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE_JSON = os.path.join(SKILL_DIR, "reference", "vanilla-leader-backgrounds.json")

# 官方背景所在 pantry 目录 → pack 名（决定"装了没装"）
def _pantry_dirs(sdk_assets: str):
    c = os.path.join(sdk_assets, "Civ6")
    return [
        ("Base", os.path.join(c, "pantry", "Textures")),
        ("Expansion1", os.path.join(c, "DLC", "Expansion1", "pantry", "Textures")),
        ("Expansion2", os.path.join(c, "DLC", "Expansion2", "pantry", "Textures")),
        ("CivRoyaleScenario", os.path.join(c, "DLC", "CivRoyaleScenario", "pantry", "Textures")),
    ]


def _sdk_assets():
    """优先用 civ6-modding/tools/_paths.py 的解析（路径单一真源）。"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(SKILL_DIR), "civ6-modding", "tools"))
        import _paths  # type: ignore
        p = _paths.get("sdk_assets")
        if p:
            return p
    except Exception:
        pass
    for cand in (r"F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets",
                 r"C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets"):
        if os.path.isdir(cand):
            return cand
    return None


# ---------------------------------------------------------------- 颜色统计

def image_stats(path: str, down: int = 96) -> dict:
    """→ {width,height,mean,median,hue}。hue = 饱和度×明度加权的圆平均色相。"""
    from PIL import Image
    import colorsys
    import cmath

    im = Image.open(path).convert("RGB")
    w, h = im.size
    im.thumbnail((down, down), Image.LANCZOS)
    px = list(im.getdata())
    n = len(px)
    if not n:
        raise ValueError("空图：%s" % path)

    acc = 0j
    wsum = 0.0
    for (r, g, b) in px:
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        wgt = ss * vv
        if wgt < 0.02:          # 近黑/近灰：噪声与暗边，不参与色相
            continue
        acc += wgt * cmath.exp(1j * math.radians(hh * 360.0))
        wsum += wgt
    hue = (math.degrees(cmath.phase(acc)) % 360.0) if wsum > 0 else 0.0

    rs = sorted(p[0] for p in px)
    gs = sorted(p[1] for p in px)
    bs = sorted(p[2] for p in px)
    return {
        "width": w, "height": h,
        "mean": [sum(p[0] for p in px) // n, sum(p[1] for p in px) // n, sum(p[2] for p in px) // n],
        "median": [rs[n // 2], gs[n // 2], bs[n // 2]],
        "hue": round(hue, 1),
    }


def luminance(mean) -> float:
    """BT.601 亮度（0..255）。"""
    return 0.299 * mean[0] + 0.587 * mean[1] + 0.114 * mean[2]


def hue_distance(a: float, b: float) -> float:
    """环形色相距离，返回 0..180。"""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def score(cand_hue, cand_mean, ref_hue, ref_lum) -> float:
    """0 = 完全一致。色相权重 0.7、亮度权重 0.3。"""
    dh = hue_distance(cand_hue, ref_hue) / 180.0
    dl = abs(luminance(cand_mean) - ref_lum) / 255.0
    return dh * 0.7 + dl * 0.3


# ---------------------------------------------------------------- 调色板

def load_palette(rebuild: bool = False) -> dict:
    if not rebuild and os.path.isfile(PALETTE_JSON):
        with open(PALETTE_JSON, encoding="utf-8") as f:
            return json.load(f)
    return rebuild_palette()


def rebuild_palette() -> dict:
    sdk = _sdk_assets()
    if not sdk:
        raise SystemExit("找不到 SDK Assets 路径；请先配置 civ6-modding/local_paths.json 的 sdk_assets。")
    out = {}
    for pack, d in _pantry_dirs(sdk):
        for f in glob.glob(os.path.join(d, "LEADER_*_BACKGROUND.dds")):
            nm = os.path.basename(f)[:-4]
            if nm in out:      # 同名跨 DLC：先到先得（顺序 Base → Exp1 → Exp2 → Royale）
                continue
            try:
                s = image_stats(f)
            except Exception as e:
                print("WARN 跳过 %s：%s" % (nm, e), file=sys.stderr)
                continue
            s["pack"] = pack
            out[nm] = s
    os.makedirs(os.path.dirname(PALETTE_JSON), exist_ok=True)
    # newline="\n"：Windows 下默认会把 \n 翻成 CRLF，与 skill 内其它文本（统一 LF）不一致
    with open(PALETTE_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("已重建调色板：%s（%d 张）" % (PALETTE_JSON, len(out)), file=sys.stderr)
    return out


# ---------------------------------------------------------------- 挑选

DEFAULT_PACKS = ("Base", "Expansion1", "Expansion2")


def rank(palette: dict, ref: dict, packs, top: int):
    ref_hue = ref["hue"]
    ref_lum = luminance(ref["mean"])
    rows = []
    for nm, s in palette.items():
        if packs and s.get("pack") not in packs:
            continue
        dh = hue_distance(s["hue"], ref_hue)
        rows.append({
            "name": nm, "pack": s.get("pack"), "hue": s["hue"], "mean": s["mean"],
            "d_hue": round(dh, 1),
            "score": round(score(s["hue"], s["mean"], ref_hue, ref_lum), 4),
            "similar": dh <= 60.0,
        })
    rows.sort(key=lambda r: r["score"])
    return rows[:top] if top else rows


# ---------------------------------------------------------------- 接线

_OFFICIAL_CACHE = None


def _official_texture_names():
    """官方 pantry 里全部贴图名（不含扩展名）。带缓存。找不到 SDK 时返回空集。"""
    global _OFFICIAL_CACHE
    if _OFFICIAL_CACHE is not None:
        return _OFFICIAL_CACHE
    names = set()
    sdk = _sdk_assets()
    if sdk:
        base = os.path.join(sdk, "Civ6")
        for d in (os.path.join(base, "pantry"), os.path.join(base, "DLC")):
            for dp, _dn, fn in os.walk(d):
                for f in fn:
                    if f.endswith((".dds", ".tex")):
                        names.add(os.path.splitext(f)[0])
    _OFFICIAL_CACHE = names
    return names


def xlp_path(project: str, prefer: str):
    """在工程 XLPs/ 里找目标 XLP（默认 UILeaders.xlp；不存在则 Shell_Loading.xlp）。"""
    xlps = glob.glob(os.path.join(project, "XLPs", "*.xlp"))
    for p in xlps:
        if os.path.basename(p).lower() == prefer.lower():
            return p
    return None


def alias_entry(entry_id: str, object_name: str, indent: str = "\t\t") -> str:
    """生成一个 <Element> 别名块（缩进与 <m_Entries> 内其余条目对齐）。"""
    i2 = indent + "\t"
    return (indent + "<Element>\n"
            + i2 + '<m_EntryID text=\"%s\"/>\n' % entry_id
            + i2 + '<m_ObjectName text=\"%s\"/>\n' % object_name
            + indent + "</Element>\n")


def insert_alias(xlp_file: str, entry_id: str, object_name: str, write: bool):
    """幂等：EntryID 已存在则跳过（返回 'exists'）。XLP 是 LF + 无 BOM。"""
    raw = open(xlp_file, encoding="utf-8").read()
    if re.search(r'<m_EntryID text="%s"\s*/>' % re.escape(entry_id), raw):
        return "exists"
    if "</m_Entries>" not in raw:
        raise SystemExit("XLP 结构异常（缺 </m_Entries>）：%s" % xlp_file)
    # 锚点含行首缩进，避免与文件里 </m_Entries> 前的 "\t" 叠加导致多一级缩进
    anchor = "\n\t</m_Entries>"
    if anchor in raw:
        new = raw.replace(anchor, "\n" + alias_entry(entry_id, object_name) + "\t</m_Entries>", 1)
    else:
        new = raw.replace("</m_Entries>", alias_entry(entry_id, object_name) + "\t</m_Entries>", 1)
    if write:
        with open(xlp_file, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return "added"


def main():
    ap = argparse.ArgumentParser(description="按色调近似挑选可复用的原版领袖背景")
    ap.add_argument("--list", action="store_true", help="列出调色板全部条目后退出")
    ap.add_argument("--reference", help="参考图（主角立绘 / 已有背景），用于计算目标色相")
    ap.add_argument("--reference-hue", type=float, help="直接给色相（0-360），免参考图")
    ap.add_argument("--top", type=int, default=5, help="推荐条数（默认 5）")
    ap.add_argument("--pick", help="手动指定原版背景名（跳过挑选）")
    ap.add_argument("--project", help="工程根（产出接线时需要）")
    ap.add_argument("--leader", help="目标 LeaderType，如 LEADER_CARTETHYIA_QYQXP")
    ap.add_argument("--allow-pack", default=",".join(DEFAULT_PACKS),
                    help="允许的 pack 列表，逗号分隔（默认 Base,Expansion1,Expansion2）")
    ap.add_argument("--xlp", default="UILeaders.xlp", help="写入别名条目的 XLP（默认 UILeaders.xlp）")
    ap.add_argument("--rebuild", action="store_true", help="强制从本机 pantry 重建调色板缓存")
    ap.add_argument("--check", action="store_true", help="预演，不写盘（默认行为）")
    ap.add_argument("--write", action="store_true", help="实际写盘")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    a = ap.parse_args()

    packs = tuple(x.strip() for x in a.allow_pack.split(",") if x.strip())
    palette = load_palette(a.rebuild)

    if a.list:
        rows = rank(palette, {"hue": 0.0, "mean": [0, 0, 0]}, packs, 0)
        rows.sort(key=lambda r: r["hue"])
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            print("%-42s %-16s %7s  %-16s" % ("背景名", "pack", "hue", "mean"))
            for r in rows:
                print("%-42s %-16s %7.1f  %s" % (r["name"], r["pack"], r["hue"], r["mean"]))
            print("\n共 %d 张（已按 --allow-pack=%s 过滤）" % (len(rows), ",".join(packs)))
        return 0

    warns = []
    if a.pick:
        if a.pick not in palette:
            raise SystemExit("调色板里没有 %s；用 --list 看可用项。" % a.pick)
        chosen = {"name": a.pick, **palette[a.pick], "d_hue": None, "score": None, "similar": True}
        ranked = [chosen]
    else:
        if a.reference:
            if not os.path.isfile(a.reference):
                raise SystemExit("参考图不存在：%s" % a.reference)
            ref = image_stats(a.reference)
        elif a.reference_hue is not None:
            ref = {"hue": a.reference_hue, "mean": [128, 128, 128]}
        else:
            raise SystemExit("需要 --reference / --reference-hue / --pick 之一。")
        ranked = rank(palette, ref, packs, a.top)
        if not ranked:
            raise SystemExit("没有候选（检查 --allow-pack）。")
        chosen = ranked[0]
        if a.json:
            print(json.dumps({"reference": {"hue": ref["hue"], "lum": round(luminance(ref["mean"]), 1)},
                              "ranked": ranked}, ensure_ascii=False, indent=1))
        else:
            print("参考色相 %.1f / 亮度 %.1f → 候选：" % (ref["hue"], luminance(ref["mean"])))
            for r in ranked:
                flag = "OK " if r["similar"] else "远 "
                print("  %s %-42s pack=%-16s Δh=%5.1f  score=%.4f" %
                      (flag, r["name"], r["pack"], r["d_hue"], r["score"]))
        if not chosen["similar"]:
            warns.append("最佳候选 Δh=%.1f° > 60°，判为**不相似**——建议自建背景或人工指定 --pick。"
                         % chosen["d_hue"])

    if not a.project or not a.leader:
        if warns:
            for w in warns:
                print("WARN " + w, file=sys.stderr)
            return 2
        return 0

    if not re.match(r"^LEADER_[A-Z0-9_]+$", a.leader):
        raise SystemExit("--leader 必须是 LEADER_<大写> 形式：%s" % a.leader)

    key = a.leader[len("LEADER_"):]
    bg_entry = "LEADER_%s_BACKGROUND" % key          # 环境 A 背景（Players.PortraitBackground）
    fg_entry = "LEADER_%s_NEUTRAL" % key             # 环境 A/B 前景（Players.Portrait / LoadingInfo.ForegroundImage）
    target_xlp = xlp_path(a.project, a.xlp)

    print("\n=== 接线方案（leader=%s）===" % a.leader)
    print("复用官方背景：%s（pack=%s, hue=%.1f）" % (chosen["name"], chosen.get("pack"), chosen["hue"]))
    print("\n[1] XLP 别名条目（写进 %s）——四环境里凡是查这两个名字的地方都会命中：" %
          (os.path.basename(target_xlp) if target_xlp else a.xlp))
    print("    EntryID=%-42s ObjectName=%s" % (fg_entry, chosen["name"].replace("_BACKGROUND", "_NEUTRAL")))
    print("    EntryID=%-42s ObjectName=%s" % (bg_entry, chosen["name"]))
    print("\n[2] FrontEnd（Config 库，FrontEndActions→UpdateDatabase）：")
    print("    UPDATE Players SET Portrait='%s', PortraitBackground='%s'" % (fg_entry, bg_entry))
    print("      WHERE LeaderType='%s';" % a.leader)
    print("    ⚠ 背景是 **1920×960 横版**，而控件 LeaderBG 是 328×935 且 StretchMode=\"None\"")
    print("      → 只显示左上角一块。若要满幅，需自建 328×935 竖版（见 reference/frontend-portrait.md §1.4）。")
    print("\n[3] InGame（Gameplay 库，InGameActions→UpdateDatabase）加载界面：")
    print("    INSERT OR REPLACE INTO LoadingInfo (LeaderType, ForegroundImage, BackgroundImage, PlayDawnOfManAudio)")
    print("      VALUES ('%s', '%s', '%s', 1);" % (a.leader, fg_entry, bg_entry))

    if not target_xlp:
        warns.append("工程 XLPs/ 下找不到 %s —— 别名条目未写；请手动登记。" % a.xlp)
    else:
        # 前景别名源：官方 <X>_NEUTRAL —— 需在**官方 pantry** 里确认它存在
        # （不在工程 XLP 里：官方贴图登记在 SDK 的 UI_Leaders.xlp）。
        fg_src = chosen["name"].replace("_BACKGROUND", "_NEUTRAL")
        fg_ok = fg_src in _official_texture_names()
        pairs = [(bg_entry, chosen["name"])] + ([(fg_entry, fg_src)] if fg_ok else [])
        if not fg_ok:
            warns.append("官方 pantry 里没有 %s（前景别名源）——前景需自建，"
                         "或改用 --pick 指定一位有 _NEUTRAL 的领袖。" % fg_src)
        for eid, obj in pairs:
            try:
                st = insert_alias(target_xlp, eid, obj, write=a.write)
            except SystemExit as e:
                print("ERROR " + str(e), file=sys.stderr)
                return 1
            print("    %s → %s : %s" % (eid, obj, st))
        if not a.write:
            print("\n（预演模式，未写盘；确认候选后加 --write）")

    for w in warns:
        print("WARN " + w, file=sys.stderr)
    return 2 if warns else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    raise SystemExit(main())
