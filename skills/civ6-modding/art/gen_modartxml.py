#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_modartxml.py — Mod.Art.xml（AssetObjects..GameArtSpecification）生成器。

逻辑与数据移植自 Civ6 Modding Assistant 1.6.3（Hemmelfort，PyInstaller 反编译）：
civ6/modart.pyc 的 buildModArtXml + civ6/modart_data.pyc 的静态表。
规则：
  1. artConsumers 全量输出（49 个消费者）；
  2. relativeArtDefPaths 只列项目 Artdefs\\ 下实存的 .artdef（相对文件名）；
     特例 Clutter：无论项目有无，固定写 Clutter.artdef（原工具行为）；
  3. libraryDependencies 按静态表原样输出（可为空元素对）；
  4. loadsLibraries = 库依赖非空 ? true : false；
  5. gameLibraries 遍历静态库表，逐一匹配项目 XLPs\\*.xlp 的 <m_ClassName>，
     命中则写该 XLP 的 <m_PackageName>（原工具行为：包名取自 XLP 本身）；
  6. requiredGameArtIDs 单条：优先沿用项目现有 *.Art.xml 的 id/名/GameArtID，
     否则回退 *.civ6proj 的 Name/Guid + 默认 Civ6。

用法：
  python gen_modartxml.py <projectRoot>            # 生成结果打印到 stdout
  python gen_modartxml.py <projectRoot> --check    # 与项目现有 *.Art.xml 比对，只报告不写
  python gen_modartxml.py <projectRoot> --write    # 写回项目 Art.xml（覆盖前自动备份 .bak）
零第三方依赖（xml.etree 解析 XLP/项目文件）。
"""

import argparse
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---- 以下数据表逐字移植自 civ6\modart_data.pyc（civ6ma 1.6.3 反编译） ----

RequiredGameArtIDs = {
    'Civ6': 'cb2f71b7-843e-4af3-9ca7-992acda9c195',
    'CivRoyaleScenario': 'E05D018D-A6ED-469B-AA5E-5D122693E2EC',
    'Expansion1': '7446c8fe-29eb-44f8-801f-098f681cc5c5',
    'Expansion2': 'b1b63999-6b16-4dd2-a5b6-eb19794aa8ca',
    'Shared': '725760e3-7fc0-4be7-abf1-17bc756d5436',
}

artConsumers = {
    'AOSystem': {'libraryDependencies': [], 'relativeArtDefPaths': ["GraphicsTweaks.artdef"]},
    'Audio': {'libraryDependencies': [], 'relativeArtDefPaths': [
        'Civilizations.artdef', 'Features.artdef', 'GoodyHuts.artdef', 'Terrains.artdef',
        'Units.artdef', 'Improvements.artdef', 'Resources.artdef', 'Eras.artdef',
        'Districts.artdef', 'Leaders.artdef']},
    'Camera': {'libraryDependencies': ["CameraAnimation"], 'relativeArtDefPaths': ["Camera.artdef"]},
    'Civilizations': {'libraryDependencies': [], 'relativeArtDefPaths': ["Civilizations.artdef"]},
    'Clutter': {'libraryDependencies': ["Landmark"], 'relativeArtDefPaths': ["Clutter.artdef"]},
    'ColorKeys': {'libraryDependencies': ["ColorKey"], 'relativeArtDefPaths': []},
    'Cultures': {'libraryDependencies': [], 'relativeArtDefPaths': ["Cultures.artdef", "Civilizations.artdef"]},
    'DynamicGeometry': {'libraryDependencies': ["DynamicGeometry"], 'relativeArtDefPaths': ["Walls.artdef"]},
    'FOW': {'libraryDependencies': ["FOWSprite", "FOWTexture"], 'relativeArtDefPaths': ["FOW.artdef"]},
    'Farms': {'libraryDependencies': ["TileBase", "CityBuildings"], 'relativeArtDefPaths': ["Farms.artdef"]},
    'Features': {'libraryDependencies': [], 'relativeArtDefPaths': ["Features.artdef"]},
    'GameLighting': {'libraryDependencies': ["ColorKey", "GameLighting"],
                     'relativeArtDefPaths': ["GameLighting.artdef", "GraphicsTweaks.artdef"]},
    'GenericObject': {'libraryDependencies': [], 'relativeArtDefPaths': []},
    'IconManager': {'libraryDependencies': [], 'relativeArtDefPaths': ["IconReferences.artdef"]},
    'Improvements': {'libraryDependencies': [], 'relativeArtDefPaths': ["Improvements.artdef"]},
    'IndirectGrid': {'libraryDependencies': [], 'relativeArtDefPaths': [
        "Features.artdef", "GraphicsTweaks.artdef", "Improvements.artdef", "Terrains.artdef"]},
    'Landmarks': {'libraryDependencies': ["CityBuildings", "TileBase", "RouteDecalMaterial"],
                  'relativeArtDefPaths': ['Landmarks.artdef', 'CityGenerators.artdef', 'Eras.artdef',
                                          'Cultures.artdef', 'Civilizations.artdef',
                                          'Improvements.artdef', 'Resources.artdef']},
    'LeaderFallback': {'libraryDependencies': ["LeaderFallback"],
                       'relativeArtDefPaths': ["FallbackLeaders.artdef"]},
    'LeaderLighting': {'libraryDependencies': ["LeaderLighting", "ColorKey"],
                       'relativeArtDefPaths': ["Leaders.artdef"]},
    'Leaders': {'libraryDependencies': ["Leader", "LeaderLighting", "ColorKey"],
                'relativeArtDefPaths': ["Leaders.artdef"]},
    'Lenses': {'libraryDependencies': [], 'relativeArtDefPaths': ["Lenses.artdef"]},
    'Minimap': {'libraryDependencies': [], 'relativeArtDefPaths': ["Minimap.artdef"]},
    'Overlay': {'libraryDependencies': ["OverlayTexture", "UILensAsset"],
                'relativeArtDefPaths': ["Overlay.artdef"]},
    'RangeArrows': {'libraryDependencies': ["OverlayTexture", "UILensAsset"],
                    'relativeArtDefPaths': ["Overlay.artdef"]},
    'Resources': {'libraryDependencies': [], 'relativeArtDefPaths': ["Resources.artdef"]},
    'SkyBox': {'libraryDependencies': ["SkyBoxTexture"], 'relativeArtDefPaths': ["SkyBox.artdef"]},
    'StrategicView_Properties': {'libraryDependencies': [],
                                 'relativeArtDefPaths': ["StrategicView.artdef"]},
    'StrategicView_Route': {'libraryDependencies': ["StrategicView_Route", "StrategicView_DirectedAsset"],
                            'relativeArtDefPaths': ["StrategicView.artdef"]},
    'StrategicView_Sprite': {'libraryDependencies': ["StrategicView_Sprite", "StrategicView_DirectedAsset"],
                             'relativeArtDefPaths': ["StrategicView.artdef"]},
    'StrategicView_TerrainBlend': {
        'libraryDependencies': ["StrategicView_TerrainBlend", "StrategicView_DirectedAsset"],
        'relativeArtDefPaths': ["StrategicView.artdef"]},
    'StrategicView_TerrainBlendCorners': {
        'libraryDependencies': ["StrategicView_TerrainBlendCorners", "StrategicView_DirectedAsset"],
        'relativeArtDefPaths': ["StrategicView.artdef"]},
    'StrategicView_TerrainType': {
        'libraryDependencies': ["StrategicView_TerrainBlend", "StrategicView_TerrainBlendCorners",
                                "StrategicView_TerrainType", "StrategicView_DirectedAsset"],
        'relativeArtDefPaths': ["StrategicView.artdef"]},
    'StrategicView_Translate': {'libraryDependencies': [], 'relativeArtDefPaths': [
        'Eras.artdef', 'Terrains.artdef', 'Features.artdef', 'Routes.artdef',
        'Improvements.artdef', 'Districts.artdef', 'Buildings.artdef', 'Cities.artdef']},
    'Terrain': {'libraryDependencies': ["TerrainAsset", "TerrainElement", "TerrainMaterial"],
                'relativeArtDefPaths': ["TerrainStyle.artdef", "GraphicsTweaks.artdef"]},
    'Terrains': {'libraryDependencies': [], 'relativeArtDefPaths': ["Terrains.artdef"]},
    'UI': {'libraryDependencies': ["UITexture"], 'relativeArtDefPaths': ["UserInterface.artdef"]},
    'UILensAsset': {'libraryDependencies': ["OverlayTexture", "UILensAsset"],
                    'relativeArtDefPaths': ["Overlay.artdef"]},
    'UIPreview': {'libraryDependencies': [], 'relativeArtDefPaths': ["UIPreview.artdef"]},
    'UnitSimulation': {'libraryDependencies': [],
                       'relativeArtDefPaths': ["UnitOperations.artdef", "Improvements.artdef"]},
    'Units': {'libraryDependencies': ["Unit", "VFX", "Light"],
              'relativeArtDefPaths': ['Units.artdef', 'Unit_Bins.artdef',
                                      'Units_Great_People.artdef', 'Eras.artdef',
                                      'UnitActivities.artdef']},
    'VFX': {'libraryDependencies': ["VFX", "Light"], 'relativeArtDefPaths': ["VFX.artdef"]},
    'Water': {'libraryDependencies': ["Water", "SkyBoxTexture"], 'relativeArtDefPaths': ["Water.artdef"]},
    'Wave': {'libraryDependencies': ["Wave"], 'relativeArtDefPaths': ["Wave.artdef"]},
    'WonderMovie': {'libraryDependencies': ["WonderMovie", "TileBase", "GameLighting", "ColorKey"],
                    'relativeArtDefPaths': ["WonderMovie.artdef"]},
    'WorldViewRoutes': {'libraryDependencies': ["RouteDecalMaterial", "RouteDoodad"],
                        'relativeArtDefPaths': ["WorldViewRoutes.artdef", "Eras.artdef"]},
    'WorldView_Translate': {'libraryDependencies': [], 'relativeArtDefPaths': [
        'Districts.artdef', 'Buildings.artdef', 'Eras.artdef', 'Features.artdef',
        'Improvements.artdef', 'Resources.artdef', 'Terrains.artdef', 'Civilizations.artdef',
        'WorldViewRoutes.artdef', 'Appeal.artdef', 'Cultures.artdef', 'WaterMaterials.artdef']},
}

# gameLibraries：仅用键序遍历（原工具的包路径列表不参与生成，包名取自项目 XLP 本身）
gameLibraries = [
    'CameraAnimation', 'CityBuildings', 'ColorKey', 'DynamicGeometry', 'FOWSprite',
    'FOWTexture', 'GameLighting', 'Landmark', 'Leader', 'LeaderFallback', 'LeaderLighting',
    'Light', 'OverlayTexture', 'RouteDecalMaterial', 'RouteDoodad', 'SkyBoxTexture',
    'StrategicView_DirectedAsset', 'StrategicView_Route', 'StrategicView_Sprite',
    'StrategicView_TerrainBlend', 'StrategicView_TerrainBlendCorners',
    'StrategicView_TerrainType', 'TerrainAsset', 'TerrainElement', 'TerrainMaterial',
    'TileBase', 'UILensAsset', 'UITexture', 'Unit', 'VFX', 'Water', 'Wave', 'WonderMovie',
]


def get_xlp_class_and_package(fpath):
    """读 XLP 的 m_ClassName / m_PackageName（与原工具 getXlpClassAndPackage 一致）。"""
    try:
        content = Path(fpath).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", ""
    cls = re.findall(r'<m_ClassName text="(.*?)"/>', content)
    pkg = re.findall(r'<m_PackageName text="(.*?)"/>', content)
    return (cls[0] if cls else ""), (pkg[0] if pkg else "")


def read_existing_art_xml(project_root):
    """读项目现有 Art.xml，返回 (name, modid, gameart_id)；读不到返回 (None,)*3。"""
    for f in sorted(Path(project_root).glob("*[Aa]rt.xml")):
        try:
            tree = ET.parse(f)
        except ET.ParseError:
            continue
        r = tree.getroot()
        if not r.tag.endswith("GameArtSpecification"):
            continue
        name_el = r.find("./id/name")
        id_el = r.find("./id/id")
        art_el = r.find("./requiredGameArtIDs/Element/name")
        return (name_el.get("text") if name_el is not None else None,
                id_el.get("text") if id_el is not None else None,
                (art_el.get("text") if art_el is not None else None) or "Civ6")
    return None, None, None


def read_civ6proj(fpath):
    """读 .civ6proj 的 Name/Guid（与原工具 read_civ6proj 一致）。"""
    dic = {}
    try:
        tree = ET.parse(fpath)
    except ET.ParseError:
        return dic
    root = tree.getroot()
    m = re.match(r"\{.*\}", root.tag)
    ns = m.group(0) if m else ""
    pg = root.find(ns + "PropertyGroup")
    if pg is None:
        return dic
    name = pg.find(ns + "Name")
    guid = pg.find(ns + "Guid")
    dic["Name"] = name.text if name is not None and name.text else ""
    dic["Guid"] = guid.text if guid is not None and guid.text else ""
    return dic


def build_modart_xml(modname, modid, artdef_files, xlp_files, gameart_id):
    """与原工具 buildModArtXml 逻辑一致，tab 缩进输出（匹配项目 Art.xml 风格）。"""
    artdef_set = {Path(a).name for a in artdef_files}
    L = ['<?xml version="1.0" encoding="UTF-8" ?>',
         '<AssetObjects..GameArtSpecification>',
         '\t<id>',
         f'\t\t<name text="{modname}"/>',
         f'\t\t<id text="{modid}"/>',
         '\t</id>',
         '\t<artConsumers>']
    for cname, cval in artConsumers.items():
        L.append('\t\t<Element>')
        L.append(f'\t\t\t<consumerName text="{cname}"/>')
        L.append('\t\t\t<relativeArtDefPaths>')
        if cname == "Clutter":
            L.append('\t\t\t\t<Element text="Clutter.artdef"/>')
        else:
            # 只写项目实存的 artdef，组内按字母序（匹配项目 Art.xml 手工风格）
            for a in sorted(x for x in cval["relativeArtDefPaths"] if x in artdef_set):
                L.append(f'\t\t\t\t<Element text="{a}"/>')
        L.append('\t\t\t</relativeArtDefPaths>')
        L.append('\t\t\t<libraryDependencies>')
        for dep in cval["libraryDependencies"]:
            L.append(f'\t\t\t\t<Element text="{dep}"/>')
        L.append('\t\t\t</libraryDependencies>')
        loads = "true" if cval["libraryDependencies"] else "false"
        L.append(f'\t\t\t<loadsLibraries>{loads}</loadsLibraries>')
        L.append('\t\t</Element>')
    L.append('\t</artConsumers>')
    L.append('\t<gameLibraries>')
    for gkey in gameLibraries:
        L.append('\t\t<Element>')
        L.append(f'\t\t\t<libraryName text="{gkey}"/>')
        L.append('\t\t\t<relativePackagePaths>')
        for xlp in xlp_files:
            c, p = get_xlp_class_and_package(xlp)
            if gkey == c and p:
                L.append(f'\t\t\t\t<Element text="{p}"/>')
        L.append('\t\t\t</relativePackagePaths>')
        L.append('\t\t</Element>')
    L.append('\t</gameLibraries>')
    if gameart_id not in RequiredGameArtIDs:
        gameart_id = "Civ6"
    L.append('\t<requiredGameArtIDs>')
    L.append('\t\t<Element>')
    L.append(f'\t\t\t<name text="{gameart_id}"/>')
    L.append(f'\t\t\t<id text="{RequiredGameArtIDs[gameart_id]}"/>')
    L.append('\t\t</Element>')
    L.append('\t</requiredGameArtIDs>')
    L.append('</AssetObjects..GameArtSpecification>')
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projectRoot")
    ap.add_argument("--check", action="store_true", help="与项目现有 *.Art.xml 比对，只报告不写")
    ap.add_argument("--write", action="store_true", help="写回项目 Art.xml（覆盖前备份 .bak）")
    args = ap.parse_args()

    root = Path(args.projectRoot)
    if not root.is_dir():
        raise SystemExit(f"projectRoot 不存在: {root}")

    modname, modid, gameart = read_existing_art_xml(root)
    if modname is None:
        proj = next(iter(sorted(root.glob("*.civ6proj"))), None)
        if proj is None:
            raise SystemExit("未找到现有 Art.xml，也未找到 *.civ6proj，无法确定 mod 身份")
        dic = read_civ6proj(proj)
        modname, modid = dic.get("Name", ""), dic.get("Guid", "")
        gameart = "Civ6"
    if not modname or not modid:
        raise SystemExit(f"mod 身份不完整: name={modname!r} id={modid!r}（检查 Art.xml/civ6proj）")

    artdef_dir = root / "Artdefs"
    if not artdef_dir.is_dir():
        artdef_dir = root / "ArtDefs"  # 项目实际目录名大小写
    artdef_files = sorted(p.name for p in artdef_dir.glob("*.artdef")) if artdef_dir.is_dir() else []
    xlp_files = sorted(str(p) for p in (root / "XLPs").glob("*.xlp")) if (root / "XLPs").is_dir() else []

    xml = build_modart_xml(modname, modid, artdef_files, xlp_files, gameart)

    existing = None
    for f in sorted(root.glob("*[Aa]rt.xml")):
        try:
            if ET.parse(f).getroot().tag.endswith("GameArtSpecification"):
                existing = f
                break
        except ET.ParseError:
            continue

    if args.check:
        if existing is None:
            print("CHECK: 项目没有现有 Art.xml（生成结果见 stdout，可 --write 落盘）")
            sys.exit(2)
        cur = existing.read_text(encoding="utf-8").replace("\r\n", "\n")
        if cur == xml:
            print(f"CHECK OK: {existing.name} 与重新生成结果逐字节一致")
            sys.exit(0)
        # 宽松比对：去掉行首缩进差异后逐行比对，给出差异摘要
        gen_lines, cur_lines = xml.splitlines(), cur.splitlines()
        diff = [(i + 1, a.strip(), b.strip())
                for i, (a, b) in enumerate(zip(gen_lines, cur_lines)) if a.strip() != b.strip()]
        print(f"CHECK DIFF: {existing.name} 与生成结果不一致"
              f"（生成 {len(gen_lines)} 行 / 现有 {len(cur_lines)} 行，内容差异 {len(diff)} 行）")
        for ln, g, c in diff[:15]:
            print(f"  L{ln}: 生成 <{g!r}> vs 现有 <{c!r}>")
        if len(gen_lines) != len(cur_lines):
            tail = (gen_lines[len(cur_lines):] if len(gen_lines) > len(cur_lines)
                    else cur_lines[len(gen_lines):])
            print(f"  行数差尾部: {tail[:5]}")
        sys.exit(1)

    if args.write:
        if existing is None:
            out = root / (modname + ".Art.xml")
        else:
            out = existing
            shutil.copy2(out, out.with_suffix(out.suffix + ".bak"))
            print(f"已备份原文件: {out.name}.bak")
            # 保持原文件行尾风格（项目规范：不得改变换行风格）
            cur = existing.read_bytes()
            if b"\r\n" in cur:
                xml = xml.replace("\r\n", "\n").replace("\n", "\r\n")
            if not cur.endswith(b"\n"):
                xml = xml.rstrip("\r\n")
        out.write_text(xml, encoding="utf-8", newline="")
        print(f"已写入: {out}")
        return
    print(xml, end="")


if __name__ == "__main__":
    main()
