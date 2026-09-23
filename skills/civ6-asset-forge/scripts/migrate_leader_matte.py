#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""migrate_leader_matte.py — 把 2D 领袖纸片材质从 PBR 人物类 Leader 迁到平面类 Leader_Matte

## 为什么迁

2D 领袖纸片是**一张 4 顶点 / 2 图元的平面四边形**（geo 的 <m_Meshes> 里只有 Plane），
但历史模板给它套的是 m_ClassName="Leader" —— 那是**原版 3D 人物服装/皮肤**用的 PBR 着色器类，
并附带 TranslucencyColor=RGB(150,20,7) 与 ForceTransparency=true。

实测后果（黑海岸守岸人 vs 同 mod 的椿，SIFT 单应配准到逐像素 r=0.989 后分解）：

    人物区域   3D = 0.898 x 2D + 20.5   (sRGB)   <- 暗部 +18~19、亮部 -2~3
    背景区域   3D = 1.0002 x 2D + 0.16           <- 逐像素不变（63.9~66% |d|<2）

即：**抬黑位 + 压对比**只发生在领袖那张纸片上，等效给纸片叠了一层
「不透明度 0.90、雾色 ~202」的灰纱；另叠加等效高斯 sigma≈0.8px 的低通模糊
（频谱低频比 1.02 / 高频比 0.42 —— 低通卷积，不是 mip 掉级）。

原版统计（pantry/Materials/*.mtl，363 个领袖类材质）：

| 检查 | 原版事实 |
|---|---|
| ForceTransparency=true | **仅 2/363**，且两者**都绑定了 Translucency 贴图** |
| 平面四边形用什么类 | Leader_Matte（19 个）—— 全部是平面背景板 |
| 参照物 | Hojo_flatBackground_Placeholder.geo 同样是 **4 顶点 / 2 图元**平面，类 Leader，材质类 Leader_Matte |
| Leader_Matte 的参数集 | 只填 BaseColor (+Opacity) |

一句话：**用 PBR 人物服装着色器去画一张平面贴图**，其 albedo x L + ambient
响应天然同时产生「增益<1 + 加性抬黑」与低通软化 —— 与本项目实测完全吻合。

## 改成什么

    m_ClassName           : Leader -> Leader_Matte
    参数槽                : 只保留 Opacity + BaseColor，移除 Normal/SpecTint/Metalness/
                            AO/Anisotropy/Tangent/Fuzz/FuzzTint/Gloss/Translucency
    移除                  : TranslucencyColor(150,20,7)、ForceTransparency
    m_Version             : 对齐原版 Leader_Matte 的 3.0.176.703
    m_Tags                : Leader_Matte / Leader / Matte

对齐样本：pantry/Materials/LEAD_JAPA_Hojo_Background_Material.mtl（原版平面背景板材质）。

## 用法

    python migrate_leader_matte.py <工程根>                 # 预演（默认，不写盘）
    python migrate_leader_matte.py <工程根> --check         # 只体检：有待迁移项则 exit 2
    python migrate_leader_matte.py <工程根> --write         # 实际执行
    python migrate_leader_matte.py <根目录1> <根目录2> ... --write   # 批量

    --all-siblings        扫描 <Civ6 工程父目录> 下全部兄弟工程

## 识别规则（只动「领袖纸片材质」）

命中需**同时**满足，避免误伤忠诚度/宗教图标等其它 Leader 类材质：

1. <m_ClassName text="Leader"/>；
2. 含 TranslucencyColor **或** ForceTransparency（这是历史模板的指纹）；
3. 文件名不含 Loyalty / Religion / Pressure / Overlay。

★ 本工具**不**负责 cook 与同步 Mods 副本：改完必须在 AssetEditor 重新 cook 才生效。

退出码：0 无需迁移或已成功 / 1 错误 / 2 --check 发现待迁移项
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_DIRS = {"workspace", ".git", "__pycache__", "Cooked", "Build", "Platforms"}
EXCLUDE_NAME = re.compile(r"(Loyalty|Religion|Pressure|Overlay|StrategicView)", re.I)

TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8" ?>\n'
    '<AssetObjects..MaterialInstance>\n'
    '\t<m_CookParams>\n'
    '\t\t<m_Values>\n'
    '\t\t\t<Element class="AssetObjects..ObjectValue">\n'
    '\t\t\t\t<m_ObjectName text="{OPAC}"/>\n'
    '\t\t\t\t<m_eObjectType>TEXTURE</m_eObjectType>\n'
    '\t\t\t\t<m_ParamName text="Opacity"/>\n'
    '\t\t\t</Element>\n'
    '\t\t\t<Element class="AssetObjects..ObjectValue">\n'
    '\t\t\t\t<m_ObjectName text="{TEX}"/>\n'
    '\t\t\t\t<m_eObjectType>TEXTURE</m_eObjectType>\n'
    '\t\t\t\t<m_ParamName text="BaseColor"/>\n'
    '\t\t\t</Element>\n'
    '\t\t</m_Values>\n'
    '\t</m_CookParams>\n'
    '\t<m_Version>\n'
    '\t\t<major>3</major>\n'
    '\t\t<minor>0</minor>\n'
    '\t\t<build>176</build>\n'
    '\t\t<revision>703</revision>\n'
    '\t</m_Version>\n'
    '\t<m_ClassName text="Leader_Matte"/>\n'
    '\t<m_DataFiles/>\n'
    '\t<m_Name text="{NAME}"/>\n'
    '\t<m_Description text=""/>\n'
    '\t<m_Tags>\n'
    '\t\t<Element text="Leader_Matte"/>\n'
    '\t\t<Element text="Leader"/>\n'
    '\t\t<Element text="Matte"/>\n'
    '\t</m_Tags>\n'
    '\t<m_Groups/>\n'
    '</AssetObjects..MaterialInstance>\n'
)


def field(text, tag):
    m = re.search(r'<%s text="([^"]*)"' % tag, text)
    return m.group(1) if m else ""


def analyze(path):
    """返回 (是否需要迁移, 详情 dict)；不写盘。"""
    raw = io.open(path, encoding="utf-8", errors="replace", newline="").read()
    cls = field(raw, "m_ClassName")
    name = field(raw, "m_Name")
    slots = re.findall(r'<m_ParamName text="([^"]*)"/>', raw)
    has_tc = "TranslucencyColor" in raw
    has_ft = "m_bValue>true</m_bValue>" in raw and "ForceTransparency" in raw
    base = ""
    opac = ""
    for blk in re.findall(r'<Element class="AssetObjects\.\.ObjectValue">(.*?)</Element>', raw, re.S):
        obj = re.search(r'<m_ObjectName text="([^"]*)"/>', blk)
        par = re.search(r'<m_ParamName text="([^"]*)"/>', blk)
        if not obj or not par:
            continue
        if par.group(1) == "BaseColor":
            base = obj.group(1)
        elif par.group(1) == "Opacity":
            opac = obj.group(1)
    need = (cls == "Leader") and (has_tc or has_ft) and not EXCLUDE_NAME.search(os.path.basename(path))
    return need, dict(cls=cls, name=name, slots=slots, base=base, opac=opac, has_tc=has_tc, has_ft=has_ft)


def collect(roots, all_siblings):
    roots = list(roots)
    if all_siblings:
        for r in list(roots):
            for d in sorted(os.listdir(r)):
                p = os.path.join(r, d, d)
                if os.path.isdir(os.path.join(p, "Materials")):
                    roots.append(p)
    files = []
    for root in roots:
        root = os.path.abspath(root)
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            if os.path.basename(dp) != "Materials":
                continue
            for f in fn:
                if f.endswith(".mtl"):
                    files.append(os.path.join(dp, f))
    return sorted(set(files))


def main():
    ap = argparse.ArgumentParser(description="2D 领袖纸片材质 Leader -> Leader_Matte 迁移器")
    ap.add_argument("roots", nargs="+", help="工程根目录（可多个）")
    ap.add_argument("--write", action="store_true", help="实际写盘（默认只预演）")
    ap.add_argument("--check", action="store_true", help="只体检：有待迁移项则 exit 2")
    ap.add_argument("--all-siblings", action="store_true", help="把 roots 当作父目录，扫描全部兄弟工程")
    args = ap.parse_args()

    files = collect(args.roots, args.all_siblings)
    todo = []
    for p in files:
        try:
            need, info = analyze(p)
        except Exception as e:
            print("  !! 读取失败 %s: %s" % (p, e))
            continue
        if need:
            todo.append((p, info))

    print("扫描 .mtl: %d 个，待迁移(领袖纸片材质): %d 个" % (len(files), len(todo)))
    for p, i in todo:
        print("   %s" % p)
        print("      class=%s  TC=%s  FT=%s  槽位=%d -> 2" % (i["cls"], i["has_tc"], i["has_ft"], len(i["slots"])))

    if args.check:
        return 2 if todo else 0
    if not todo:
        print("无需迁移。")
        return 0
    if not args.write:
        print("\n[预演] 未写盘。加 --write 执行。")
        return 0

    ok = 0
    for p, i in todo:
        if not i["base"]:
            print("   !! 跳过（BaseColor 为空）: %s" % p)
            continue
        text = TEMPLATE.replace("{OPAC}", i["opac"]).replace("{TEX}", i["base"]).replace("{NAME}", i["name"])
        try:
            ET.fromstring(text)
        except Exception as e:
            print("   !! 跳过（模板 XML 非法）: %s %s" % (p, e))
            continue
        raw = open(p, "rb").read()
        nl = "\r\n" if raw.count(b"\r\n") > raw.count(b"\n") / 2 else "\n"
        out = text if nl == "\n" else text.replace("\n", "\r\n")
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write(out)
        ok += 1
        print("   已迁移 %s" % p)
    print("\n完成：%d/%d 个材质已迁到 Leader_Matte。请在 AssetEditor 重新 cook 后验证。" % (ok, len(todo)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
