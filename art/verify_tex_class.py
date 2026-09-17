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

    python verify_tex_class.py --project <工程根>          # 只读校验
    python verify_tex_class.py --project <工程根> --all    # 连 pantry 一起当基线统计（较慢）
    python verify_tex_class.py --project <工程根> --quiet  # 只输出结论

退出码：0 = 全过 / 1 = 有 FAIL。

> **只读**：不修改任何文件。要改 `m_ClassName` 请手工或走
> `civ6-asset-forge` 的对应类别脚本重新生成 `.tex`。
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# XLP 类 → 允许的 m_ClassName 集合（来自全 pantry + 工程实测，占比 ≥89%）
# 未列出的 XLP 类不校验
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
    """→ (xlps, texs)：xlps = [(path, class, [entryids])]，texs = [(path, name, class)]"""
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
                ents = re.findall(r'<m_EntryID text="([^"]*)"', t)
                xlps.append((p, c.group(1) if c else None, ents))
            elif low.endswith(".tex"):
                try:
                    t = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                nm = re.search(r'<m_Name text="([^"]*)"', t)
                cc = re.search(r'<m_ClassName text="([^"]*)"', t)
                texs.append((p, nm.group(1) if nm else None,
                             cc.group(1) if cc else None))
    return xlps, texs


def main():
    ap = argparse.ArgumentParser(description="校验 .tex 类别与 XLP 注册类是否匹配")
    ap.add_argument("--project", required=True)
    ap.add_argument("--baseline",
                    help="可选的基线工程（如官方 pantry 顶层目录），只用于统计报告")
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

    # 贴图名 -> 其声明的类别
    tex_class = {nm: cc for _p, nm, cc in texs if nm}
    # 贴图名 -> 它被哪些 XLP 类登记
    reg = defaultdict(set)
    for _p, cls, ents in xlps:
        if not cls:
            continue
        for e in ents:
            reg[e].add(cls)

    fails, warns, checked = [], [], 0
    stats = Counter()

    for _p, nm, cc in texs:
        if not nm:
            continue
        classes = reg.get(nm)
        if not classes:
            # 未被任何 XLP 登记 —— 由 check_proj_content / verify_icon_atlas 负责，此处只提示
            stats["未登记"] += 1
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
        # 交叉提示：同一贴图被多个 XLP 类登记且类别要求冲突
        req = {frozenset(CLASS_RULES[c]) for c in classes if c in CLASS_RULES}
        if len(req) > 1:
            inter = set.intersection(*[set(x) for x in req])
            if not inter:
                warns.append("%s: 被多个 XLP 类登记且类别要求互斥：%s"
                             % (nm, {c: sorted(CLASS_RULES[c]) for c in classes if c in CLASS_RULES}))

    print("=" * 72)
    print("`.tex` 类别 × XLP 注册类 校验：%s" % root)
    print("=" * 72)
    print("  XLP 文件: %d    .tex 文件: %d    参与校验的(贴图,XLP类)对: %d"
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
        print("  全部检查通过（类别与注册目标一致）。")
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
