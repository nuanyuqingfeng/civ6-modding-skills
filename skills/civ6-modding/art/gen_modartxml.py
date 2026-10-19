#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_modartxml.py — Mod.Art.xml（AssetObjects..GameArtSpecification）生成器。

逻辑与数据移植自 Civ6 Modding Assistant 1.6.3（Hemmelfort，PyInstaller 反编译）：
civ6/modart.pyc 的 buildModArtXml + civ6/modart_data.pyc 的静态表。
规则：
  1. artConsumers 全量输出（46 个消费者）；
  2. relativeArtDefPaths 只列项目 Artdefs\\ 下实存的 .artdef（相对文件名）；
     特例 Clutter：无论项目有无，固定写 Clutter.artdef（原工具行为）；
  3. libraryDependencies 按静态表原样输出（可为空元素对）；
  4. loadsLibraries = 库依赖非空 ? true : false；
  5. gameLibraries 遍历静态库表，逐一匹配项目 XLPs\\*.xlp 的 <m_ClassName>，
     命中则写该 XLP 的 <m_PackageName>（原工具行为：包名取自 XLP 本身）；
  6. requiredGameArtIDs 保留项目现有 *.Art.xml 的全部条目（不折叠成首条）；
     文件缺失时取 *.civ6proj 的 Guid 作 id、文件名作 name、默认 Civ6 作包。
  7. --ensure 系列为增量编辑：只做加法，不删除、不重排、不改写既有条目；
     已有文件内容有变化时改写结果落 <解决方案根>/workspace/gen/，由 AI 用文件编辑工具写入工程。

用法：
  python gen_modartxml.py <projectRoot>            # 生成结果打印到 stdout
  python gen_modartxml.py <projectRoot> --check    # 与项目现有 *.Art.xml 比对，只报告不写
  python gen_modartxml.py <projectRoot> --write    # 全量重生成（改写走 workspace/gen 守卫）
  python gen_modartxml.py <projectRoot> --ensure-consumer "Overlay=Overlay.artdef"
  python gen_modartxml.py <projectRoot> --ensure-library "UILensAsset=UILensAssets"
  python gen_modartxml.py <projectRoot> --ensure-required Expansion2
零第三方依赖（xml.etree 解析 XLP/项目文件）。
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from _projwrite import finish, write_project_file  # noqa: E402

# ArtSpecification 的解析复用 tools/cook_assets.py 的实现：官方 Shared.Art.xml 有两处
# 不合规（根标签 <AssetObjects::GameArtSpecification> 与文件尾 NUL），标准解析器会拒绝，
# 归一化只有 load_art_spec 一处实现。art/ 与 tools/ 同属 civ6-modding。
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "tools"))
import cook_assets  # noqa: E402

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


def find_art_xml(project_root):
    """定位工程里的 *.Art.xml，返回 Path；找不到返回 None。

    解析统一走 cook_assets.load_art_spec（含官方两处不合规写法的归一化）。
    """
    for f in sorted(Path(project_root).glob("*[Aa]rt.xml")):
        try:
            root = cook_assets.load_art_spec(str(f))
        except ET.ParseError:
            continue
        if root.tag.endswith("GameArtSpecification"):
            return f
    return None


def read_art_identity(path):
    """读现有 Art.xml 的 (name, modid, required 包名列表)。required 全量读取，不折叠。"""
    root = cook_assets.load_art_spec(str(path))
    name_el = root.find("./id/name")
    id_el = root.find("./id/id")
    req = [e.get("text") for e in root.findall("./requiredGameArtIDs/Element/name")
           if e.get("text")]
    return (name_el.get("text") if name_el is not None else None,
            id_el.get("text") if id_el is not None else None,
            req)


def read_civ6proj(fpath):
    """读 .civ6proj 的 Guid / AssemblyName / 文件名 stem。

    **不读 <Name>**：该列是本地化键（如 LOC_RAGUNNA_PACK_QYQXP_MOD_TITLE），不是 mod 名。
    mod 名的真源是 Art.xml 的 <id><name>；文件缺失时取 .civ6proj 的文件名 stem，
    与 modinfo_build.project_mod_name 的回落口径一致（两处各按各的取会分裂出两个 Mods 目录）。
    """
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
    guid = pg.find(ns + "Guid")
    asm = pg.find(ns + "AssemblyName")
    dic["Guid"] = guid.text if guid is not None and guid.text else ""
    dic["AssemblyName"] = asm.text if asm is not None and asm.text else ""
    dic["Stem"] = Path(fpath).stem
    return dic


def resolve_identity(root):
    """定出 (art_xml_path|None, modname, modid, required 列表)。

    有 Art.xml：身份与其 required 列表原样沿用（不折叠成首条）。
    没有：取 .civ6proj 的 Guid 作 id、文件名 stem 作 name、required 为空表。
    """
    path = find_art_xml(root)
    if path is not None:
        name, modid, req = read_art_identity(path)
        if not name or not modid:
            raise SystemExit(f"Art.xml 身份不完整: name={name!r} id={modid!r}：{path}")
        return path, name, modid, req
    proj = next(iter(sorted(root.glob("*.civ6proj"))), None)
    if proj is None:
        raise SystemExit("未找到现有 Art.xml，也未找到 *.civ6proj，无法确定 mod 身份")
    dic = read_civ6proj(proj)
    modname = dic.get("Stem", "")
    modid = dic.get("Guid", "")
    if not modname or not modid:
        raise SystemExit(f".civ6proj 身份不完整: name={modname!r} id={modid!r}：{proj}")
    return None, modname, modid, []


def build_modart_xml(modname, modid, artdef_files, xlp_files, required):
    """全量生成（原工具 buildModArtXml 逻辑），tab 缩进输出（匹配项目 Art.xml 风格）。

    `required` 是 <requiredGameArtIDs> 的包名列表，按给定顺序逐条输出；
    调用方传入现有文件的全部条目（不折叠成首条）。
    """
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
    L.append('\t<requiredGameArtIDs>')
    for pkg in required:
        if pkg not in RequiredGameArtIDs:
            raise SystemExit("未知的游戏美术包：%s（可选：%s）"
                             % (pkg, ", ".join(sorted(RequiredGameArtIDs))))
        L.append('\t\t<Element>')
        L.append(f'\t\t\t<name text="{pkg}"/>')
        L.append(f'\t\t\t<id text="{RequiredGameArtIDs[pkg]}"/>')
        L.append('\t\t</Element>')
    L.append('\t</requiredGameArtIDs>')
    L.append('</AssetObjects..GameArtSpecification>')
    return "\n".join(L) + "\n"


def _ind(line):
    """行首缩进（制表符）。"""
    return line[:len(line) - len(line.lstrip())]


def ensure_consumer(text, consumer, artdef):
    """确保 consumer 的 relativeArtDefPaths 含 artdef；返回 (新文本, 插入条数)。

    判定看结构，落位做行插入：自闭合容器先展开成对形式。只加不删。
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if f'<consumerName text="{consumer}"/>' not in line:
            continue
        j = i + 1
        while j < len(lines) and "relativeArtDefPaths" not in lines[j]:
            j += 1
        if j >= len(lines):
            return text, 0
        tail = lines[j].split("relativeArtDefPaths", 1)[1]
        if "/>" in tail:
            ind = _ind(lines[j])
            lines[j:j + 1] = [ind + "<relativeArtDefPaths>",
                              ind + "\t" + f'<Element text="{artdef}"/>',
                              ind + "</relativeArtDefPaths>"]
            return "\n".join(lines), 1
        k = j + 1
        while k < len(lines) and "</relativeArtDefPaths>" not in lines[k]:
            if f'<Element text="{artdef}"/>' in lines[k]:
                return text, 0
            k += 1
        ind = _ind(lines[j]) + "\t"
        lines.insert(k, ind + f'<Element text="{artdef}"/>')
        return "\n".join(lines), 1
    return text, 0


def ensure_library(text, library, package):
    """确保每一处同名 library 的 relativePackagePaths 都含 package（官方有同名多元素先例）。

    只加不删；同名元素逐个处理，任一缺失即插入。
    """
    lines = text.split("\n")
    changed = 0
    i = 0
    while i < len(lines):
        if f'<libraryName text="{library}"/>' not in lines[i]:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and "relativePackagePaths" not in lines[j]:
            j += 1
        if j >= len(lines):
            break
        tail = lines[j].split("relativePackagePaths", 1)[1]
        if "/>" in tail:
            ind = _ind(lines[j])
            lines[j:j + 1] = [ind + "<relativePackagePaths>",
                              ind + "\t" + f'<Element text="{package}"/>',
                              ind + "</relativePackagePaths>"]
            changed += 1
            i = j + 3
            continue
        k = j + 1
        found = False
        while k < len(lines) and "</relativePackagePaths>" not in lines[k]:
            if f'<Element text="{package}"/>' in lines[k]:
                found = True
            k += 1
        if not found:
            ind = _ind(lines[j]) + "\t"
            lines.insert(k, ind + f'<Element text="{package}"/>')
            changed += 1
            k += 1
        i = k
    return "\n".join(lines), changed


def ensure_required(text, package):
    """确保 requiredGameArtIDs 含该包；返回 (新文本, 插入条数)。自闭合容器先展开。"""
    if package not in RequiredGameArtIDs:
        raise SystemExit("未知的游戏美术包：%s（可选：%s）"
                         % (package, ", ".join(sorted(RequiredGameArtIDs))))
    lines = text.split("\n")
    start = None
    for idx, line in enumerate(lines):
        if "<requiredGameArtIDs" in line:
            start = idx
            break
    if start is None:
        return text, 0
    if "/>" in lines[start].split("requiredGameArtIDs", 1)[1]:
        ind = _ind(lines[start])
        entry = [ind + "\t" + "<Element>",
                 ind + "\t\t" + f'<name text="{package}"/>',
                 ind + "\t\t" + f'<id text="{RequiredGameArtIDs[package]}"/>',
                 ind + "\t" + "</Element>"]
        lines[start:start + 1] = ([ind + "<requiredGameArtIDs>"] + entry
                                  + [ind + "</requiredGameArtIDs>"])
        return "\n".join(lines), 1
    end = start + 1
    while end < len(lines) and "</requiredGameArtIDs>" not in lines[end]:
        if f'<name text="{package}"/>' in lines[end]:
            return text, 0
        end += 1
    if end >= len(lines):
        return text, 0
    ind = _ind(lines[end])
    entry = [ind + "\t" + "<Element>",
             ind + "\t\t" + f'<name text="{package}"/>',
             ind + "\t\t" + f'<id text="{RequiredGameArtIDs[package]}"/>',
             ind + "\t" + "</Element>"]
    lines[end:end] = entry
    return "\n".join(lines), 1


def _stage(out, text, root, existing):
    """按既有文件的换行风格交给写入守卫；返回 NEW/SAME/STAGED。"""
    if existing is not None:
        cur = Path(existing).read_bytes()
        if b"\r\n" in cur:
            text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        if not cur.endswith(b"\n"):
            text = text.rstrip("\r\n")
    return write_project_file(str(out), text, str(root))


def _pair(spec):
    if "=" not in spec:
        raise SystemExit(f"参数格式应为 名称=值：{spec!r}")
    a, b = spec.split("=", 1)
    a, b = a.strip(), b.strip()
    if not a or not b:
        raise SystemExit(f"参数格式应为 名称=值：{spec!r}")
    return a, b


def _result_line(result, out):
    """把守卫返回值翻成一行说明。"""
    if result in ("NEW", "OVERWRITE"):
        return f"已写入: {out}"
    if result == "SAME":
        return f"无需改动: {out}"
    return f"改写结果已写到 workspace/gen/：{out}"


def ensure(project_root, consumers=(), libraries=(), required=()):
    """程序化增量接线，返回 (退出码, 输出行列表)。

    退出码 0 = 无需改动；1 = 无美术工程拒绝创建；2 = 改写结果已入位 workspace/gen。
    与命令行的 --ensure-* 走同一套实现（main 也调它）。
    """
    root = Path(project_root)
    if not root.is_dir():
        raise SystemExit(f"projectRoot 不存在: {root}")
    art_xml, modname, modid, req0 = resolve_identity(root)
    artdef_dir = root / "Artdefs"
    if not artdef_dir.is_dir():
        artdef_dir = root / "ArtDefs"
    artdef_files = sorted(p.name for p in artdef_dir.glob("*.artdef")) if artdef_dir.is_dir() else []
    xlp_files = sorted(str(p) for p in (root / "XLPs").glob("*.xlp")) if (root / "XLPs").is_dir() else []
    lines = []

    if art_xml is None:
        # 创建路径：工程完全没有 Art.xml 时全量生成后直写
        if not any((root / d).is_dir() for d in ("ArtDefs", "Artdefs", "XLPs", "Textures")):
            return 1, ["工程内没有 ArtDefs / XLPs / Textures，判定为无美术工程，"
                       "不创建必然悬空的 *.Art.xml"]
        req = list(req0)
        for pkg in required:
            pkg = pkg.strip()
            if pkg and pkg not in req:
                req.append(pkg)
        xml = build_modart_xml(modname, modid, artdef_files, xlp_files, req or ["Civ6"])
        out = root / (modname + ".Art.xml")
        result = write_project_file(str(out), xml, str(root))
        lines.append(_result_line(result, out))
        return (2 if result == "STAGED" else 0), lines

    text = art_xml.read_text(encoding="utf-8")
    changed = 0
    for consumer, artdef in consumers:
        text, n = ensure_consumer(text, consumer, artdef)
        if n == 0:
            lines.append(f"未变   consumer {consumer} 已含 {artdef}")
        changed += n
    for library, package in libraries:
        text, n = ensure_library(text, library, package)
        if n == 0:
            lines.append(f"未变   library {library} 已含 {package}")
        changed += n
    for package in required:
        package = package.strip()
        text, n = ensure_required(text, package)
        if n == 0:
            lines.append(f"未变   requiredGameArtIDs 已含 {package}")
        changed += n
    if changed == 0:
        lines.append(f"无需改动: {art_xml}")
        return 0, lines
    result = _stage(art_xml, text, root, art_xml)
    lines.append(_result_line(result, art_xml))
    return (2 if result == "STAGED" else 0), lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projectRoot")
    ap.add_argument("--check", action="store_true", help="与项目现有 *.Art.xml 比对，只报告不写")
    ap.add_argument("--write", action="store_true", help="全量重生成（改写走 workspace/gen 守卫）")
    ap.add_argument("--ensure-consumer", action="append", default=[], metavar="NAME=ARTDEF",
                    help="增量：确保该 consumer 的 relativeArtDefPaths 含该 artdef（可重复）")
    ap.add_argument("--ensure-library", action="append", default=[], metavar="LIB=PACKAGE",
                    help="增量：确保该 library 的 relativePackagePaths 含该包（可重复）")
    ap.add_argument("--ensure-required", action="append", default=[], metavar="PACKAGE",
                    help="增量：确保 requiredGameArtIDs 含该包（可重复）")
    args = ap.parse_args()

    root = Path(args.projectRoot)
    if not root.is_dir():
        raise SystemExit(f"projectRoot 不存在: {root}")

    if args.ensure_consumer or args.ensure_library or args.ensure_required:
        # 增量一律走 ensure()：命令行与程序调用是同一套实现
        rc, lines = ensure(
            root,
            consumers=[_pair(s) for s in args.ensure_consumer],
            libraries=[_pair(s) for s in args.ensure_library],
            required=[p.strip() for p in args.ensure_required if p.strip()])
        for line in lines:
            print("  " + line)
        if rc == 1:
            sys.exit(1)
        sys.exit(finish())

    art_xml, modname, modid, required = resolve_identity(root)

    artdef_dir = root / "Artdefs"
    if not artdef_dir.is_dir():
        artdef_dir = root / "ArtDefs"  # 项目实际目录名大小写
    artdef_files = sorted(p.name for p in artdef_dir.glob("*.artdef")) if artdef_dir.is_dir() else []
    xlp_files = sorted(str(p) for p in (root / "XLPs").glob("*.xlp")) if (root / "XLPs").is_dir() else []

    if art_xml is None:
        # 创建路径：工程完全没有 Art.xml 时全量生成后直写
        if not any((root / d).is_dir() for d in ("ArtDefs", "Artdefs", "XLPs", "Textures")):
            raise SystemExit("工程内没有 ArtDefs / XLPs / Textures，判定为无美术工程，"
                             "不创建必然悬空的 *.Art.xml")
        xml = build_modart_xml(modname, modid, artdef_files, xlp_files, required or ["Civ6"])
        out = root / (modname + ".Art.xml")
        if args.check:
            print("CHECK: 项目没有现有 Art.xml（生成结果见 stdout，可 --write 落盘）")
            print(xml, end="")
            sys.exit(2)
        print(_result_line(write_project_file(str(out), xml, str(root)), out))
        sys.exit(finish())

    text = art_xml.read_text(encoding="utf-8")

    xml = build_modart_xml(modname, modid, artdef_files, xlp_files, required or ["Civ6"])

    if args.check:
        cur = text.replace("\r\n", "\n")
        if cur == xml:
            print(f"CHECK OK: {art_xml.name} 与重新生成结果逐字节一致")
            sys.exit(0)
        # 宽松比对：去掉行首缩进差异后逐行比对，给出差异摘要
        gen_lines, cur_lines = xml.splitlines(), cur.splitlines()
        diff = [(i + 1, a.strip(), b.strip())
                for i, (a, b) in enumerate(zip(gen_lines, cur_lines)) if a.strip() != b.strip()]
        print(f"CHECK DIFF: {art_xml.name} 与生成结果不一致"
              f"（生成 {len(gen_lines)} 行 / 现有 {len(cur_lines)} 行，内容差异 {len(diff)} 行）")
        for ln, g, c in diff[:15]:
            print(f"  L{ln}: 生成 <{g!r}> vs 现有 <{c!r}>")
        if len(gen_lines) != len(cur_lines):
            tail = (gen_lines[len(cur_lines):] if len(gen_lines) > len(cur_lines)
                    else cur_lines[len(gen_lines):])
            print(f"  行数差尾部: {tail[:5]}")
        sys.exit(1)

    if not args.write:
        print(xml, end="")
        return

    result = _stage(art_xml, xml, root, art_xml)
    if result == "SAME":
        print(f"无需改动: {art_xml}")
    elif result == "STAGED":
        print(f"改写结果已写到 workspace/gen/：{art_xml}")
    else:
        print(f"已写入: {art_xml}")
    sys.exit(finish())


if __name__ == "__main__":
    main()
