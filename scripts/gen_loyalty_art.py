#!/usr/bin/env python3
"""文明6 忠诚度图标注册链生成：XLP / ArtDef / mtl / ast + Art.xml、civ6proj 补注册。

用法：
  python gen_loyalty_art.py --project "<工程路径>" --civ-types CIVILIZATION_RAGUNNA_QYQXP[,CIVILIZATION_X2...]

生成/更新的文件：
  XLPs/UILensModels.xlp            UILensAsset 条目包（2 条/文明）
  XLPs/StrategicView_UILenses.xlp  StrategicView_Sprite 条目包（追加 2 条/文明）
  ArtDefs/Overlay.artdef           LoyaltyLensArrows + LoyaltyWarning（聚合）
  ArtDefs/StrategicView.artdef     UILenses + UILensEntries（聚合）
  Materials/Loyalty_{Overlay,Pressure}_{S}_material.mtl
  Assets/Loyalty_{Overlay,Pressure}_{S}_Box.ast
  示例工程.Art.xml             consumer/library 接线（幂等补齐）
  <工程>.civ6proj                  Content 条目（幂等补齐）

不生成 .tex/.dds（素材审核通过后走 civ6-modding art-pipeline 转换）。
"""

import argparse
import re
import sys
from pathlib import Path

XML_DECL = '<?xml version="1.0" encoding="UTF-8" ?>\n'
XLP_HEAD = """{xml}<AssetObjects..XLP>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_ClassName text="{cls}"/>
\t<m_PackageName text="{pkg}"/>
\t<m_Entries>
{entries}\t</m_Entries>
\t<m_AllowedPlatforms>
\t\t<Element>WINDOWS</Element>
\t</m_AllowedPlatforms>
</AssetObjects..XLP>
"""

XLP_ENTRY = """\t\t<Element>
\t\t\t<m_EntryID text="{eid}"/>
\t\t\t<m_ObjectName text="{eid}"/>
\t\t</Element>
"""

# ---------------------------------------------------------------- Overlay.artdef

LENSMODEL_CHILD = """\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Fields>
\t\t\t\t\t\t\t<m_Values>
\t\t\t\t\t\t\t\t<Element class="AssetObjects..BLPEntryValue">
\t\t\t\t\t\t\t\t\t<m_EntryName text="{box}"/>
\t\t\t\t\t\t\t\t\t<m_XLPClass text="UILensAsset"/>
\t\t\t\t\t\t\t\t\t<m_XLPPath text="uilensmodels.xlp"/>
\t\t\t\t\t\t\t\t\t<m_BLPPackage text="UILensAssets"/>
\t\t\t\t\t\t\t\t\t<m_LibraryName text="UILensAsset"/>
\t\t\t\t\t\t\t\t\t<m_ParamName text="BaseModel"/>
\t\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Fields>
\t\t\t\t\t\t<m_ChildCollections/>
\t\t\t\t\t\t<m_Name text="{child}"/>
\t\t\t\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t\t\t\t</Element>
"""

EMPTY_COLL = """\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="{name}"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t\t\t</Element>
"""

def overlay_artdef(civs: list[str]) -> str:
    """Overlays 集合：每文明两个元素（LoyaltyLensArrows 内的 civ 子集合 + LoyaltyWarning）。"""
    elements = ""
    for civ in civs:
        s = suffix(civ)
        lm_arrow = LENSMODEL_CHILD.format(box=f"Loyalty_Pressure_{s}_Box", child=civ)
        lm_warn = LENSMODEL_CHILD.format(box=f"Loyalty_Overlay_{s}_Box", child="LensModel")
        elements += f"""\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values/>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections>
{EMPTY_COLL.format(name="Filled")}{EMPTY_COLL.format(name="Texture")}{EMPTY_COLL.format(name="Model")}{EMPTY_COLL.format(name="SplineBorder")}\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="LensModel"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{lm_arrow}\t\t\t\t</Element>
\t\t\t</m_ChildCollections>
\t\t\t<m_Name text="LoyaltyLensArrows"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values/>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections>
{EMPTY_COLL.format(name="Filled")}{EMPTY_COLL.format(name="Texture")}{EMPTY_COLL.format(name="Model")}{EMPTY_COLL.format(name="SplineBorder")}\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="LensModel"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{lm_warn}\t\t\t\t</Element>
\t\t\t</m_ChildCollections>
\t\t\t<m_Name text="LoyaltyWarning_{civ}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""
    return XML_DECL + """<AssetObjects..ArtDefSet>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_TemplateName text="Overlay"/>
\t<m_RootCollections>
\t\t<Element>
\t\t\t<m_CollectionName text="Overlays"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{elements}\t\t</Element>
\t</m_RootCollections>
</AssetObjects..ArtDefSet>
""".format(elements=elements)

# ---------------------------------------------------------------- StrategicView.artdef

# 占位符约定：{civ} = 完整文明类型（仅用于元素名 LoyaltyWarning_{civ} / {civ}）；
# {s} = 短后缀。UILensEntries 条目名与 SV_LENS_WARNING/SV_LENS_CIV 里的引用名必须同为
# {s}——引用名若误用 {civ} 会产生悬空引用，游戏不报错但图标静默不显示。
SV_LENS_WARNING = """\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values>
\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t\t\t<m_ParamName text="RotateToAlign"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..StringValue">
\t\t\t\t\t\t<m_Value text="FADE_LOOP"/>
\t\t\t\t\t\t<m_ParamName text="AnimType"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t\t\t<m_fValue>1.000000</m_fValue>
\t\t\t\t\t\t<m_ParamName text="AnimDuration"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t<m_bValue>true</m_bValue>
\t\t\t\t\t\t<m_ParamName text="Render"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t<m_ElementName text="LoyaltyWarning"/>
\t\t\t\t\t\t<m_RootCollectionName text="PlacementRules"/>
\t\t\t\t\t\t<m_ArtDefPath text="StrategicView_Shared.artdef"/>
\t\t\t\t\t\t<m_CollectionIsLocked>true</m_CollectionIsLocked>
\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t<m_ParamName text="PlacementRule"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t<m_ElementName text="1_Center"/>
\t\t\t\t\t\t<m_RootCollectionName text="PositionSets"/>
\t\t\t\t\t\t<m_ArtDefPath text="StrategicView.artdef"/>
\t\t\t\t\t\t<m_CollectionIsLocked>true</m_CollectionIsLocked>
\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t<m_ParamName text="PositionSet"/>
\t\t\t\t\t</Element>
\t\t\t\t</m_Values>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections>
\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="Entries"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Fields>
\t\t\t\t\t\t\t<m_Values>
\t\t\t\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t\t\t\t<m_ElementName text="LoyaltyOverlayIcon_{s}"/>
\t\t\t\t\t\t\t\t\t<m_RootCollectionName text="UILensEntries"/>
\t\t\t\t\t\t\t\t\t<m_ArtDefPath text="StrategicView.artdef"/>
\t\t\t\t\t\t\t\t\t<m_CollectionIsLocked>false</m_CollectionIsLocked>
\t\t\t\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t\t\t\t<m_ParamName text="ArtDefEntry"/>
\t\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Fields>
\t\t\t\t\t\t<m_ChildCollections/>
\t\t\t\t\t\t<m_Name text="Entries"/>
\t\t\t\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t\t\t\t</Element>
\t\t\t\t</Element>
\t\t\t</m_ChildCollections>
\t\t\t<m_Name text="LoyaltyWarning_{civ}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""

SV_LENS_CIV = """\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values>
\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t<m_ElementName text="1_Center"/>
\t\t\t\t\t\t<m_RootCollectionName text="PositionSets"/>
\t\t\t\t\t\t<m_ArtDefPath text="StrategicView.artdef"/>
\t\t\t\t\t\t<m_CollectionIsLocked>true</m_CollectionIsLocked>
\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t<m_ParamName text="PositionSet"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t<m_ElementName text="LoyaltyPressure"/>
\t\t\t\t\t\t<m_RootCollectionName text="PlacementRules"/>
\t\t\t\t\t\t<m_ArtDefPath text="StrategicView_Shared.artdef"/>
\t\t\t\t\t\t<m_CollectionIsLocked>true</m_CollectionIsLocked>
\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t<m_ParamName text="PlacementRule"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t<m_bValue>true</m_bValue>
\t\t\t\t\t\t<m_ParamName text="Render"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t\t\t<m_fValue>0.000000</m_fValue>
\t\t\t\t\t\t<m_ParamName text="AnimDuration"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..StringValue">
\t\t\t\t\t\t<m_Value text="NONE"/>
\t\t\t\t\t\t<m_ParamName text="AnimType"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t\t\t<m_ParamName text="RotateToAlign"/>
\t\t\t\t\t</Element>
\t\t\t\t</m_Values>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections>
\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="Entries"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Fields>
\t\t\t\t\t\t\t<m_Values>
\t\t\t\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t\t\t\t<m_ElementName text="ReligionPressureArrow_ReligionPressureArrow"/>
\t\t\t\t\t\t\t\t\t<m_RootCollectionName text="UILensEntries"/>
\t\t\t\t\t\t\t\t\t<m_ArtDefPath text="StrategicView.artdef"/>
\t\t\t\t\t\t\t\t\t<m_CollectionIsLocked>false</m_CollectionIsLocked>
\t\t\t\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t\t\t\t<m_ParamName text="ArtDefEntry"/>
\t\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Fields>
\t\t\t\t\t\t<m_ChildCollections/>
\t\t\t\t\t\t<m_Name text="Arrow"/>
\t\t\t\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Fields>
\t\t\t\t\t\t\t<m_Values>
\t\t\t\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t\t\t\t<m_ElementName text="LoyaltyPressureIcon_{s}"/>
\t\t\t\t\t\t\t\t\t<m_RootCollectionName text="UILensEntries"/>
\t\t\t\t\t\t\t\t\t<m_ArtDefPath text="StrategicView.artdef"/>
\t\t\t\t\t\t\t\t\t<m_CollectionIsLocked>false</m_CollectionIsLocked>
\t\t\t\t\t\t\t\t\t<m_TemplateName text="StrategicView"/>
\t\t\t\t\t\t\t\t\t<m_ParamName text="ArtDefEntry"/>
\t\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Fields>
\t\t\t\t\t\t<m_ChildCollections/>
\t\t\t\t\t\t<m_Name text="Icon"/>
\t\t\t\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t\t\t\t</Element>
\t\t\t\t</Element>
\t\t\t</m_ChildCollections>
\t\t\t<m_Name text="{civ}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""

SV_LENS_ENTRY = """\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values>
\t\t\t\t\t<Element class="AssetObjects..BLPEntryValue">
\t\t\t\t\t\t<m_EntryName text="{sprite}"/>
\t\t\t\t\t\t<m_XLPClass text="StrategicView_Sprite"/>
\t\t\t\t\t\t<m_XLPPath text="strategicview_uilenses.xlp"/>
\t\t\t\t\t\t<m_BLPPackage text="strategicview/strategicview_uilenses"/>
\t\t\t\t\t\t<m_LibraryName text="StrategicView_Sprite"/>
\t\t\t\t\t\t<m_ParamName text="Visible_XLPEntry"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t\t\t<m_ParamName text="Visible_TopLeft"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t\t\t<m_ParamName text="Visible_BottomRight"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..BLPEntryValue">
\t\t\t\t\t\t<m_EntryName text="{sprite}"/>
\t\t\t\t\t\t<m_XLPClass text="StrategicView_Sprite"/>
\t\t\t\t\t\t<m_XLPPath text="strategicview_uilenses.xlp"/>
\t\t\t\t\t\t<m_BLPPackage text="strategicview/strategicview_uilenses"/>
\t\t\t\t\t\t<m_LibraryName text="StrategicView_Sprite"/>
\t\t\t\t\t\t<m_ParamName text="Revealed_XLPEntry"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t\t\t<m_ParamName text="Revealed_TopLeft"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t\t\t<m_ParamName text="Revealed_BottomRight"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..RGBValue">
\t\t\t\t\t\t<m_r>255.000000</m_r>
\t\t\t\t\t\t<m_g>255.000000</m_g>
\t\t\t\t\t\t<m_b>255.000000</m_b>
\t\t\t\t\t\t<m_ParamName text="TintColor"/>
\t\t\t\t\t</Element>
\t\t\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t\t\t<m_fValue>1.000000</m_fValue>
\t\t\t\t\t\t<m_ParamName text="Scale"/>
\t\t\t\t\t</Element>
\t\t\t\t</m_Values>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections/>
\t\t\t<m_Name text="{name}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""

def strategicview_artdef(civs: list[str]) -> str:
    lenses = ""
    entries = ""
    for civ in civs:
        s = suffix(civ)
        lenses += SV_LENS_WARNING.format(civ=civ, s=s)
        lenses += SV_LENS_CIV.format(civ=civ, s=s)
        entries += SV_LENS_ENTRY.format(
            sprite=f"StrategicView_Loyalty_Overlay_{s}",
            name=f"LoyaltyOverlayIcon_{s}")
        entries += SV_LENS_ENTRY.format(
            sprite=f"StrategicView_Loyalty_Pressure_{s}",
            name=f"LoyaltyPressureIcon_{s}")
    return XML_DECL + """<AssetObjects..ArtDefSet>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_TemplateName text="StrategicView"/>
\t<m_RootCollections>
\t\t<Element>
\t\t\t<m_CollectionName text="EffectEntries"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t</Element>
\t\t<Element>
\t\t\t<m_CollectionName text="Effects"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t</Element>
\t\t<Element>
\t\t\t<m_CollectionName text="UILenses"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{lenses}\t\t</Element>
\t\t<Element>
\t\t\t<m_CollectionName text="UILensEntries"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{entries}\t\t</Element>
\t</m_RootCollections>
</AssetObjects..ArtDefSet>
""".format(lenses=lenses, entries=entries)

# ---------------------------------------------------------------- mtl / ast

MTL = """{xml}<AssetObjects..MaterialInstance>
\t<m_CookParams>
\t\t<m_Values>
\t\t\t<Element class="AssetObjects..ObjectValue">
\t\t\t\t<m_ObjectName text="Loyalty_{Kind}_{s}"/>
\t\t\t\t<m_eObjectType>TEXTURE</m_eObjectType>
\t\t\t\t<m_ParamName text="UILensOverlayTexture"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..ObjectValue">
\t\t\t\t<m_ObjectName text=""/>
\t\t\t\t<m_eObjectType>TEXTURE</m_eObjectType>
\t\t\t\t<m_ParamName text="TransitionLensTexture"/>
\t\t\t</Element>
\t\t</m_Values>
\t</m_CookParams>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_ClassName text="UILensMaterial"/>
\t<m_DataFiles/>
\t<m_Name text="Loyalty_{Kind}_{s}_material"/>
\t<m_Description text=""/>
\t<m_Tags/>
</AssetObjects..MaterialInstance>
"""

AST_COMMON = """{xml}<AssetObjects..AssetInstance>
\t<m_BehaviorData>
\t\t<m_behaviorDataSets>
\t\t\t<m_animationBindings>
\t\t\t\t<m_Bindings/>
\t\t\t</m_animationBindings>
\t\t\t<m_timelineBindings>
\t\t\t\t<m_Bindings/>
\t\t\t</m_timelineBindings>
\t\t\t<m_timelines>
\t\t\t\t<m_Timelines/>
\t\t\t</m_timelines>
\t\t\t<m_attachmentPoints>
\t\t\t\t<m_Points/>
\t\t\t</m_attachmentPoints>
\t\t\t<m_stateSet/>
\t\t</m_behaviorDataSets>
\t\t<m_behaviorInstances/>
\t\t<m_dsgName text=""/>
\t\t<m_referenceGeometryNames/>
\t</m_BehaviorData>
\t<m_GeometrySet>
\t\t<m_ModelInstances>
\t\t\t<Element>
\t\t\t\t<m_Name text="{model}"/>
\t\t\t\t<m_GeoName text="{geo}"/>
\t\t\t\t<m_GroupStates>
\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Values>
\t\t\t\t\t\t\t<m_Values>
\t\t\t\t\t\t\t\t<Element class="AssetObjects..ObjectValue">
\t\t\t\t\t\t\t\t\t<m_ObjectName text="Loyalty_{Kind}_{s}_material"/>
\t\t\t\t\t\t\t\t\t<m_eObjectType>MATERIAL</m_eObjectType>
\t\t\t\t\t\t\t\t\t<m_ParamName text="LensMaterial"/>
\t\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t\t<Element class="AssetObjects..ObjectValue">
\t\t\t\t\t\t\t\t\t<m_ObjectName text=""/>
\t\t\t\t\t\t\t\t\t<m_eObjectType>MATERIAL</m_eObjectType>
\t\t\t\t\t\t\t\t\t<m_ParamName text="FOWMaterial"/>
\t\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t<m_GroupName text="{group}"/>
\t\t\t\t\t\t<m_MeshName text="{mesh}"/>
\t\t\t\t\t\t<m_StateName text="Default"/>
\t\t\t\t\t</Element>
\t\t\t\t</m_GroupStates>
\t\t\t</Element>
\t\t</m_ModelInstances>
\t</m_GeometrySet>
\t<m_SplineSet>
\t\t<m_Splines/>
\t</m_SplineSet>
\t<m_CookParams>
\t\t<m_Values>
\t\t\t<Element class="AssetObjects..Coord3DValue">
\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t<m_z>5.000000</m_z>
\t\t\t\t<m_ParamName text="Offset"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..RGBValue">
\t\t\t\t<m_r>255.000000</m_r>
\t\t\t\t<m_g>255.000000</m_g>
\t\t\t\t<m_b>255.000000</m_b>
\t\t\t\t<m_ParamName text="Color"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t<m_fValue>1.000000</m_fValue>
\t\t\t\t<m_ParamName text="Alpha"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t<m_ParamName text="UVOffset"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t<m_x>1.000000</m_x>
\t\t\t\t<m_y>1.000000</m_y>
\t\t\t\t<m_ParamName text="UVScale"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t<m_ParamName text="RotateToAlign"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t<m_ParamName text="IsBillboard"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..StringValue">
\t\t\t\t<m_Value text="{anim}"/>
\t\t\t\t<m_ParamName text="AnimType"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t<m_fValue>1.000000</m_fValue>
\t\t\t\t<m_ParamName text="AnimDuration"/>
\t\t\t</Element>
\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t<m_bValue>{autoplay}</m_bValue>
\t\t\t\t<m_ParamName text="AutoPlay"/>
\t\t\t</Element>
\t\t</m_Values>
\t</m_CookParams>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_ParticleEffects/>
\t<m_Geometries/>
\t<m_Animations/>
\t<m_Materials/>
\t<m_ClassName text="UILensAsset"/>
\t<m_DataFiles/>
\t<m_Name text="Loyalty_{Kind}_{s}_Box"/>
\t<m_Description text=""/>
\t<m_Tags/>
</AssetObjects..AssetInstance>
"""

# Overlay Box：官方六边形几何 + FADE_LOOP；Pressure Box：Pip 几何 + 无动画
AST_OVERLAY = dict(model="Hex", geo="HexModelGeo", group="09 - Default",
                   mesh="Official_Hex 034", anim="FADE_LOOP", autoplay="true")
# group 必须是 "09 - Default"（PipModelGeo 官方网格组名，工程 A 实测验证），
# 不能想当然写成 "PipModel"——组名对不上压力小图标不渲染
AST_PRESSURE = dict(model="PipModel", geo="PipModelGeo", group="09 - Default",
                    mesh="PipModel", anim="NONE", autoplay="false")

# ---------------------------------------------------------------- 辅助

def suffix(civ_type: str) -> str:
    if not civ_type.startswith("CIVILIZATION_"):
        raise SystemExit(f"错误：文明类型 {civ_type} 必须以 CIVILIZATION_ 开头")
    return civ_type[len("CIVILIZATION_"):]


def read_preserve(path: Path) -> tuple[str, str]:
    """读取文件并返回 (统一为 \\n 的文本, 原换行风格)。不改变原有换行风格。"""
    with open(path, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    return (raw.replace("\r\n", "\n"), "\r\n" if crlf else "\n")


def write_preserve(path: Path, text: str, newline: str) -> None:
    """按指定换行风格写出（新文件默认 CRLF，Windows 工程惯例）。"""
    if newline != "\r\n":
        newline = "\r\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", newline))


def write_if_changed(path: Path, content: str) -> str:
    if path.exists():
        old, _ = read_preserve(path)
        if old == content:
            return f"  未变   {path.name}"
    write_preserve(path, content, "\r\n")
    return f"  写入   {path}"


def gen_xlp(path: Path, cls: str, pkg: str, entry_ids: list[str], results: list[str]) -> None:
    """创建或追加 XLP 条目（幂等：已存在的 EntryID 跳过）。"""
    if path.exists():
        text, nl = read_preserve(path)
        new_entries = "".join(
            XLP_ENTRY.format(eid=e) for e in entry_ids
            if f'"{e}"' not in text)
        if not new_entries:
            results.append(f"  未变   {path.name}（条目已存在）")
            return
        if "<m_Entries/>" in text:
            # 空条目自闭合形式：先展开为常规形式再追加
            text = text.replace("<m_Entries/>", "<m_Entries>\n\t</m_Entries>")
        text = text.replace("\t</m_Entries>", new_entries + "\t</m_Entries>")
        write_preserve(path, text, nl)
        results.append(f"  追加   {path}（{new_entries.count('<m_EntryID')} 条）")
    else:
        entries = "".join(XLP_ENTRY.format(eid=e) for e in entry_ids)
        write_preserve(path, XLP_HEAD.format(xml=XML_DECL, cls=cls, pkg=pkg, entries=entries), "\r\n")
        results.append(f"  创建   {path}")


def patch_art_xml(art_xml: Path, results: list[str]) -> None:
    """幂等补齐 consumer 与 library 接线。"""
    text, nl = read_preserve(art_xml)
    orig = text

    def add_artdef(consumer: str, artdef: str) -> None:
        nonlocal text
        pat = re.compile(
            r'(<consumerName text="' + re.escape(consumer) + r'"/>\s*<relativeArtDefPaths>)(.*?)(</relativeArtDefPaths>)',
            re.DOTALL)
        m = pat.search(text)
        if not m:
            results.append(f"  警告   Art.xml 中找不到 consumer {consumer}，请手动补 {artdef}")
            return
        if f'"{artdef}"' in m.group(2):
            return
        text = text[:m.end(1)] + f'\n\t\t\t\t<Element text="{artdef}"/>' + text[m.end(1):]

    add_artdef("Overlay", "Overlay.artdef")
    add_artdef("RangeArrows", "Overlay.artdef")
    add_artdef("UILensAsset", "Overlay.artdef")
    add_artdef("StrategicView_Properties", "StrategicView.artdef")
    add_artdef("StrategicView_Sprite", "StrategicView.artdef")

    # UILensAsset 库挂包
    m = re.search(r'(<libraryName text="UILensAsset"/>\s*<relativePackagePaths>)(.*?)(</relativePackagePaths>)', text, re.DOTALL)
    if m and "UILensAssets" not in m.group(2):
        text = text[:m.end(1)] + '\n\t\t\t\t<Element text="UILensAssets"/>' + text[m.end(1):]

    if text != orig:
        write_preserve(art_xml, text, nl)
        results.append(f"  更新   {art_xml.name}（consumer/library 接线）")
    else:
        results.append(f"  未变   {art_xml.name}")


def patch_civ6proj(civ6proj: Path, content_files: list[str], results: list[str]) -> None:
    """幂等补 Content 条目（XLPs / ArtDefs 必须注册才会编译）。"""
    text, nl = read_preserve(civ6proj)
    missing = [f for f in content_files if f'<Content Include="{f}">' not in text]
    if not missing:
        results.append(f"  未变   {civ6proj.name}（Content 已齐）")
        return
    block = "".join(f'    <Content Include="{f}">\n      <SubType>Content</SubType>\n    </Content>\n' for f in missing)
    # 插到最后一个 </Content> 之后；没有任何 Content 时插到第一个 </ItemGroup> 前
    idx = text.rfind("</Content>")
    if idx == -1:
        idx = text.find("</ItemGroup>")
        insert_at = idx
    else:
        insert_at = text.find("</Content>", idx) + len("</Content>\n")
    text = text[:insert_at] + block + text[insert_at:]
    write_preserve(civ6proj, text, nl)
    results.append(f"  更新   {civ6proj.name}（新增 {len(missing)} 条 Content）")


def main() -> None:
    ap = argparse.ArgumentParser(description="文明6 忠诚度图标注册链生成")
    ap.add_argument("--project", required=True, help="工程根目录（含 .Art.xml / .civ6proj）")
    ap.add_argument("--civ-types", required=True,
                    help="文明类型，逗号分隔：CIVILIZATION_RAGUNNA_QYQXP,CIVILIZATION_X2")
    args = ap.parse_args()

    project = Path(args.project)
    civs = [c.strip() for c in args.civ_types.split(",") if c.strip()]
    art_xml = next(project.glob("*.Art.xml"))
    civ6proj = next(p for p in project.glob("*.civ6proj") if not p.name.endswith(".Art.xml"))
    xlp_dir = project / ("XLPs" if (project / "XLPs").is_dir() else "Xlps")
    results: list[str] = []

    # 1. XLP 条目包
    gen_xlp(xlp_dir / "UILensModels.xlp", "UILensAsset", "UILensAssets",
            [f"Loyalty_Overlay_{suffix(c)}_Box" for c in civs]
            + [f"Loyalty_Pressure_{suffix(c)}_Box" for c in civs], results)
    gen_xlp(xlp_dir / "StrategicView_UILenses.xlp", "StrategicView_Sprite",
            "strategicview/strategicview_uilenses",
            [f"StrategicView_Loyalty_Overlay_{suffix(c)}" for c in civs]
            + [f"StrategicView_Loyalty_Pressure_{suffix(c)}" for c in civs], results)

    # 2. ArtDef（本脚本只做整体生成；文件已存在且非本脚本生成时报错请手动合并）
    for name, gen in [("Overlay.artdef", overlay_artdef), ("StrategicView.artdef", strategicview_artdef)]:
        p = project / "ArtDefs" / name
        if p.exists():
            results.append(f"  跳过   {p}（已存在，如需合并文明请手动处理）")
        else:
            results.append(write_if_changed(p, gen(civs)))

    # 3. 材质与 Box 素材
    for c in civs:
        s = suffix(c)
        for kind in ("Overlay", "Pressure"):
            results.append(write_if_changed(
                project / "Materials" / f"Loyalty_{kind}_{s}_material.mtl",
                MTL.format(xml=XML_DECL, Kind=kind, s=s)))
            fields = AST_OVERLAY if kind == "Overlay" else AST_PRESSURE
            results.append(write_if_changed(
                project / "Assets" / f"Loyalty_{kind}_{s}_Box.ast",
                AST_COMMON.format(xml=XML_DECL, Kind=kind, s=s, **fields)))

    # 4. Art.xml + civ6proj 注册
    patch_art_xml(art_xml, results)
    patch_civ6proj(civ6proj, [
        f"{xlp_dir.name}\\UILensModels.xlp",
        f"{xlp_dir.name}\\StrategicView_UILenses.xlp",
        "ArtDefs\\Overlay.artdef",
        "ArtDefs\\StrategicView.artdef",
    ], results)

    print("\n".join(results))
    print("\n待办（素材审核通过后）：源 PNG 留在原处直接转换，勿复制进工程（.tex 源路径可悬空）")
    for c in civs:
        s = suffix(c)
        for kind in ("Overlay", "Pressure"):
            print(f"  - Loyalty_{kind}_{s}.png → DDS + .tex 输出 Textures/（art-pipeline，role=loyalty_3d）")
        print(f"  - StrategicView_Loyalty_Overlay_{s}.png → DDS + .tex 输出 Textures/（role=loyalty_sv）")
        print(f"  - StrategicView_Loyalty_Pressure_{s}.png → DDS + .tex 输出 Textures/（role=loyalty_sv）")


if __name__ == "__main__":
    main()
