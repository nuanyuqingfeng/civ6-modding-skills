#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""verify_tex_class.py — 校验「.tex 的 m_ClassName」与其「XLP 注册类」是否匹配

## 解决什么问题

`.tex` 的 `m_ClassName` 必须与**消费它的 XLP 的 `m_ClassName`** 对应；
写错时 cooker 报
`has class 'X', but is bound to parameter 'Y' which does not accept this class`，
错误沿「材质 → 资产 → XLP 条目」传播，而 **XLP cook 仍显示 success**，
条目被静默替换成 error asset（界面空白/贴图不显示，且不报错）。

历史教训（2026-09-17）：`gen_tex.py` 曾按名字前缀判断类别，把
`FALLBACK_NEUTRAL_*_Suk`（UI 立绘，应 `UserInterface`）误写成 `Leader_Fallback`。
当时**没有任何校验器能发现**（`align_tex_format.py` 明确不碰 `m_ClassName`；
`verify_icon_atlas.py` 只走 `IconTextureAtlases` 路径；`check_pantry.py` 只查配对）。

## 规则从哪来（实测，非臆断）

对官方 pantry + 工程全部 `XLP` 与 `.tex` 做「XLP 类 × `m_ClassName`」共现统计，
取占比 ≥95% 的作为**硬规则**：

| XLP 类 | 应有 `m_ClassName` | 实测占比 |
|---|---|---|
| `UITexture` | `UserInterface`（少数 `UISliceTexture`） | 3327/3328 = 100% |
| `StrategicView_Sprite` | `StrategicView_Sprite` | 1551/1551 = 100% |
| `LeaderFallback` | `Leader_Fallback` | 46/46 = 100% |
| `OverlayTexture` | `Overlay` | 34/34 = 100% |
| `VFX` | `VFXParticle_BaseColor`（或 `Generic_BaseColor`） | 89% |
| `FOWSprite` | `FOWSprite`（或 `FOW`） | 91% |
| `TileBase` | 多值（BaseColor/AO/Gloss/Emissive/…） | 50% → **不校验** |

其余 XLP 类样本太少，一律**不校验**（避免误报）。

## 用法

    python verify_tex_class.py --project <工程根>              # 只查类别匹配
    python verify_tex_class.py --project <工程根> --full        # 全量贴图体检（见下）
    python verify_tex_class.py --project <工程根> --quiet       # 只输出结论

`--full` 额外做**非图集贴图的完整闭环**（补 `verify_icon_atlas.py` 只管
`IconTextureAtlases` 的盲区）：

  1. **装贴图的 XLP 类**（白名单见 `CLASS_RULES`）的条目 ↔ `Textures/<name>.tex`
     - **别名条目豁免**：`EntryID != ObjectName` 时指向既有资产，不要求同名 `.tex`
       （官方惯用写法，如 `<X>_4 → BARBAROSSA_4`）
     - **非贴图类 XLP 跳过**：`Leader` / `Landmark` / `TileBase` / `UILensAsset` /
       `LeaderLighting` / `Unit` 等装的是**资产条目**（几何/材质/artdef 引用），
       本就不该有同名 `.tex`
  2. 每个 `.tex` ↔ 同名 `.dds` 是否成对
  3. `.tex` 声明的 `m_Width`/`m_Height` == DDS 头部实际宽高
  4. 类别与 XLP 注册类匹配（默认行为）
  5. XLP 条目跨文件重名

**统计里的「未被XLP按同名登记」不是错误**：3D 类贴图（`Leader_BaseColor` /
`Leader_OPAC` / `Generic_BaseColor` 等）是**由材质 `.mtl` 的 `m_ObjectName` 引用**的，
不走 XLP 条目名 —— 实测本工程 32 张全部能在 `.mtl`/`.ast` 里找到引用
（如 `LEAD_RGN_Cartethyia_QYQXP_Material.mtl` 引用 `LEADER_CARTETHYIA_QYQXP_TEXTURE`）。
该计数只作参考，**不参与判定**。

退出码：0 = 全过 / 1 = 有 FAIL。

> **只读**：不修改任何文件。要改 `m_ClassName` 请走 `civ6-asset-forge` 的
> 对应类别脚本重新产出 `.tex`（`.tex` 的值字段不要手改）。
"""
import argparse
import os
import re
import struct
import sys
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# XLP 类 → 允许的 m_ClassName 集合（来自全 pantry + 工程实测，占比 ≥89%）
#
# ⚠ 本表同时也是「**哪些 XLP 类装的是贴图**」的白名单：
# 只有本表内的 XLP 类，其条目才应当是 `Textures/<name>.tex`。
# 其它 XLP 类（`Leader` / `Landmark` / `TileBase` / `UILensAsset` /
# `LeaderLighting` / `Unit` / `RouteDoodad` / `CameraAnimation` …）装的是
# **资产条目**（几何/材质/artdef 引用/行为资产），**本就不该有同名 `.tex`**。
# 实测依据：这些类在「XLP 类 × .tex 的 m_Name」共现统计中根本匹配不上，
# 强行断言其条目有 `.tex` 会产生整片误报（曾实测出 60+ 条假 FAIL）。
CLASS_RULES = {
    "UITexture": {"UserInterface", "UISliceTexture"},
    "StrategicView_Sprite": {"StrategicView_Sprite"},
    "LeaderFallback": {"Leader_Fallback"},
    "OverlayTexture": {"Overlay"},
    "VFX": {"VFXParticle_BaseColor", "Generic_BaseColor"},
    "FOWSprite": {"FOWSprite", "FOW"},
}

SKIP_DIRS = {"workspace", ".git", "Cooked", "Build", "obj", "bin", "node_modules"}


def scan_project(root):
    """→ (xlps, texs)

    xlps = [(path, xlp_class, [(entryid, objectname)])]
    texs = [(path, m_Name, m_ClassName, (w, h) or None)]
    """
    xlps, texs = [], []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = os.path.join(dp, f)
            low = f.lower()
            if low.endswith(".xlp"):
                try:
                    t = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                c = re.search(r'<m_ClassName text="([^"]*)"', t)
                pairs = re.findall(
                    r"<m_EntryID text=\"([^\"]*)\"/>\s*<m_ObjectName text=\"([^\"]*)\"", t)
                xlps.append((p, c.group(1) if c else None, pairs))
            elif low.endswith(".tex"):
                try:
                    t = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                nm = re.search(r'<m_Name text="([^"]*)"', t)
                cc = re.search(r'<m_ClassName text="([^"]*)"', t)
                mw = re.search(r"<m_Width>(\d+)", t)
                mh = re.search(r"<m_Height>(\d+)", t)
                wh = (int(mw.group(1)), int(mh.group(1))) if (mw and mh) else None
                texs.append((p, nm.group(1) if nm else None,
                             cc.group(1) if cc else None, wh))
    return xlps, texs


def dds_wh(path):
    """读 DDS 头 → (w, h) 或 None。偏移：height@12 / width@16（小端 uint32）。"""
    try:
        with open(path, "rb") as f:
            h = f.read(20)
    except OSError:
        return None
    if len(h) < 20 or h[:4] != b"DDS ":
        return None
    ht, wd = struct.unpack("<II", h[12:20])
    return wd, ht


def run_full(xlps, texs, fails, warns, stats):
    """--full：非图集贴图的完整闭环（补 verify_icon_atlas.py 只管图集的盲区）。

    1) **装贴图的 XLP 类**（见 CLASS_RULES 白名单）的条目 ↔ 同名 `.tex`
       —— **别名条目豁免**（EntryID != ObjectName 指向既有资产）；
       非贴图类 XLP（Leader / Landmark / TileBase …）**跳过**，它们装的是资产条目。
    2) .tex ↔ 同名 .dds 成对
    3) .tex 声明宽高 == DDS 实际宽高
    4) XLP 条目跨文件重名
    """
    tex_names = {nm for _p, nm, _c, _w in texs if nm}

    alias_cnt, skipped_asset_xlp = 0, 0
    for p, cls, pairs in xlps:
        base = os.path.basename(p)
        if cls not in CLASS_RULES:
            # 非贴图类 XLP：装的是资产条目（几何/材质/artdef 引用），不该有同名 .tex
            skipped_asset_xlp += 1
            continue
        for eid, obj in pairs:
            if eid != obj:
                alias_cnt += 1   # 官方惯用的「别名条目」：指向工程内/原版既有资产
                continue
            if eid not in tex_names:
                fails.append("%s: 贴图类 XLP 条目 '%s' 无同名 Textures/%s.tex（且非别名条目）"
                             % (base, eid, eid))
    stats["别名条目(豁免)"] = alias_cnt
    stats["非贴图类XLP(跳过)"] = skipped_asset_xlp

    for p, nm, _c, wh in texs:
        if not nm:
            continue
        dds = os.path.join(os.path.dirname(p), nm + ".dds")
        if not os.path.isfile(dds):
            fails.append("%s.tex: 缺同名 .dds" % nm)
            continue
        dw = dds_wh(dds)
        if dw is None:
            warns.append("%s.dds: 非合法 DDS 或非常规头（跳过尺寸比对）" % nm)
        elif wh and dw != wh:
            fails.append("%s: .tex 声明 %dx%d != DDS 实际 %dx%d"
                         % (nm, wh[0], wh[1], dw[0], dw[1]))

    seen = defaultdict(list)
    for _p, _cls, pairs in xlps:
        for eid, _obj in pairs:
            seen[eid].append(os.path.basename(_p))
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    for k, v in sorted(dups.items()):
        warns.append("XLP 条目重名 '%s' 出现在: %s" % (k, ", ".join(sorted(set(v)))))
    stats["XLP条目重名"] = len(dups)


def main():
    ap = argparse.ArgumentParser(description="校验 .tex 类别与 XLP 注册类是否匹配")
    ap.add_argument("--project", required=True)
    ap.add_argument("--full", action="store_true",
                    help="额外做非图集贴图闭环：XLP条目↔.tex（别名豁免）/ .tex↔.dds / 尺寸一致 / 条目重名")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        print("工程目录不存在：%s" % root)
        return 1

    xlps, texs = scan_project(root)
    if not texs:
        print("未发现任何 .tex：%s" % root)
        return 1

    # 贴图名 -> 它被哪些 XLP 类登记
    reg = defaultdict(set)
    for _p, cls, pairs in xlps:
        if not cls:
            continue
        for eid, _obj in pairs:
            reg[eid].add(cls)

    fails, warns, checked = [], [], 0
    stats = Counter()

    for _p, nm, cc, _w in texs:
        if not nm:
            continue
        classes = reg.get(nm)
        if not classes:
            # 未被任何 XLP「按同名」登记。可能是：
            #   - 3D 类贴图（Leader_BaseColor/Generic_BaseColor…）由 .mtl 的
            #     m_ObjectName 引用，本就不走 XLP 条目名；
            #   - 别名条目的 ObjectName。
            # 两种都合法，故**只计数不判定**。
            stats["未被XLP按同名登记(仅参考)"] += 1
            continue
        for xc in sorted(classes):
            allowed = CLASS_RULES.get(xc)
            if allowed is None:
                stats["XLP类未纳入规则:%s" % xc] += 1
                continue
            checked += 1
            if cc not in allowed:
                fails.append(
                    "%s: m_ClassName=%s，但被 XLP 类 '%s' 登记（应为 %s）"
                    % (nm, cc, xc, " 或 ".join(sorted(allowed))))
            else:
                stats["OK"] += 1
        req = {frozenset(CLASS_RULES[c]) for c in classes if c in CLASS_RULES}
        if len(req) > 1:
            inter = set.intersection(*[set(x) for x in req])
            if not inter:
                warns.append("%s: 被多个 XLP 类登记且类别要求互斥：%s"
                             % (nm, {c: sorted(CLASS_RULES[c]) for c in classes if c in CLASS_RULES}))

    if a.full:
        run_full(xlps, texs, fails, warns, stats)

    print("=" * 72)
    print("`.tex` 类别 × XLP 注册类 校验%s：%s"
          % ("（--full 全量贴图）" if a.full else "", root))
    print("=" * 72)
    print("  XLP 文件: %d    .tex 文件: %d    参与类别校验的(贴图,XLP类)对: %d"
          % (len(xlps), len(texs), checked))
    print()
    if not a.quiet:
        print("  统计：")
        for k, v in stats.most_common(12):
            print("     %-30s %d" % (k, v))
        print()
    for w in warns:
        print("  [warn] %s" % w)
    for f in fails:
        print("  [FAIL] %s" % f)
    if not fails and not warns:
        print("  全部检查通过（类别与注册目标一致%s）。" % ("、闭环完整" if a.full else ""))
    print()
    print("RESULT:", "PASS" if not fails else "FAIL (%d)" % len(fails))
    if fails:
        print()
        print("说明：类别写错时 cooker 会报 'has class X, but is bound to parameter Y'，")
        print("      且 XLP cook 仍显示 success、条目被静默替换成 error asset。")
        print("      修法：让生成该 .tex 的脚本用正确类别重新产出（不要手改值字段）。")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
