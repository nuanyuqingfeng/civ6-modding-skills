#!/usr/bin/env python3
"""文明6 新宗教（自定义宗教类型）压力/镜头图标注册链生成。

与 gen_loyalty_art.py 同一套引擎机制（UILensAsset + 同两个 XLP 包 + 同两个 ArtDef），
命名映射换成官方宗教约定。不处理 2D UI 图标（IconTextureAtlases，另走数据路径），
不覆盖官方 RELIGION_CUSTOM_1~12 预留位。

用法：
  python gen_religion_art.py --project "<工程路径>" --religion-types RELIGION_CUSTOM_RGN[,RELIGION_X2...]

命名约定（{R} = 宗教类型去掉 RELIGION_ 前缀，如 CUSTOM_RGN）：
  3D Box 资产        Religion_Overlay_{R}_Box / Religion_Pressure_{R}_Box   （UILensModels.xlp）
  战略视图 sprite     ReligionPressureIcon_{R}                               （StrategicView_UILenses.xlp）
  引擎查找键          artdef 元素名 = 完整宗教类型 RELIGION_{R}（须与数据库 Religions.Type 逐字符一致，
                    不一致游戏不报错但图标静默不显示）

生成/更新的文件：
  XLPs/UILensModels.xlp            UILensAsset 条目包（追加 2 条/宗教）
  XLPs/StrategicView_UILenses.xlp  StrategicView_Sprite 条目包（追加 1 条/宗教）
  ArtDefs/Overlay.artdef           Overlays 根集合：Religion_Pressure_{R} + ReligionLensIcons +
                                   ReligionLensArrows（同名元素幂等追加 LensModel 子项）
  ArtDefs/StrategicView.artdef     UILenses + UILensEntries（幂等追加）
  Materials/Religion_{Overlay,Pressure}_{R}_material.mtl
  Assets/Religion_{Overlay,Pressure}_{R}_Box.ast
  <工程>.Art.xml / <工程>.civ6proj 幂等补注册

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
# 官方结构（Base/ArtDefs/Overlay.artdef，根集合 Overlays）：
#   1. Religion_Pressure_{R}   —— 3D 压力 pip 覆盖（Model 子集合，HexModel + HexModelFOW 双引用）
#   2. ReligionLensIcons       —— LensModel 子集合：RELIGION_{R} -> Religion_Overlay_{R}_Box
#   3. ReligionLensArrows      —— LensModel 子集合：RELIGION_{R} -> Religion_Pressure_{R}_Box
# 官方共享箭头（ReligionPressureArrow/Convert/In/Out、ReligionArrowBackground）基础库已有，
# mod 侧同名合并追加，不重复声明（重复元素精简）。

def blp_ref(box: str, param: str = "BaseModel", indent: str = "\t" * 8) -> str:
    return f"""{indent}<Element class="AssetObjects..BLPEntryValue">
{indent}\t<m_EntryName text="{box}"/>
{indent}\t<m_XLPClass text="UILensAsset"/>
{indent}\t<m_XLPPath text="UILensModels.xlp"/>
{indent}\t<m_BLPPackage text="UILensAssets"/>
{indent}\t<m_LibraryName text="UILensAsset"/>
{indent}\t<m_ParamName text="{param}"/>
{indent}</Element>
"""


EMPTY_COLL = """\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="{name}"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t\t\t</Element>
"""

# 官方 Religion_Pressure_{R} 的 Model 子元素完整字段集（Base 实测逐字段复制）
PRESSURE_MODEL_CHILD = """\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Fields>
\t\t\t\t\t\t\t<m_Values>
{hex_model}{move_offset}\t\t\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t\t\t\t\t<m_ParamName text="RotateToAlign"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..RGBValue">
\t\t\t\t\t\t\t\t<m_r>0.000000</m_r>
\t\t\t\t\t\t\t\t<m_g>0.000000</m_g>
\t\t\t\t\t\t\t\t<m_b>0.000000</m_b>
\t\t\t\t\t\t\t\t<m_ParamName text="RGBColor"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..StringValue">
\t\t\t\t\t\t\t\t<m_Value text="NONE"/>
\t\t\t\t\t\t\t\t<m_ParamName text="AnimType"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t\t\t\t\t<m_ParamName text="NumTiles"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t\t\t\t\t<m_fValue>0.000000</m_fValue>
\t\t\t\t\t\t\t\t<m_ParamName text="AnimDuration"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t\t\t\t\t<m_ParamName text="AutoPlay"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..FloatValue">
\t\t\t\t\t\t\t\t<m_fValue>0.000000</m_fValue>
\t\t\t\t\t\t\t\t<m_ParamName text="Alpha"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t\t\t<m_x>0.000000</m_x>
\t\t\t\t\t\t\t\t<m_y>0.000000</m_y>
\t\t\t\t\t\t\t\t<m_ParamName text="UV Offset Start"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..Coord2DValue">
\t\t\t\t\t\t\t\t<m_x>1.000000</m_x>
\t\t\t\t\t\t\t\t<m_y>1.000000</m_y>
\t\t\t\t\t\t\t\t<m_ParamName text="UV_Scale"/>
\t\t\t\t\t\t\t</Element>
\t\t\t\t\t\t\t<Element class="AssetObjects..BoolValue">
\t\t\t\t\t\t\t\t<m_bValue>false</m_bValue>
\t\t\t\t\t\t\t\t<m_ParamName text="IsBillboard"/>
\t\t\t\t\t\t\t</Element>
{fow_model}\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Fields>
\t\t\t\t\t\t<m_ChildCollections/>
\t\t\t\t\t\t<m_Name text="{box}"/>
\t\t\t\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t\t\t\t</Element>
"""

def pressure_model_child(r: str) -> str:
    box = f"Religion_Pressure_{r}_Box"
    return PRESSURE_MODEL_CHILD.format(
        box=box,
        hex_model=blp_ref(box, "HexModel", "\t" * 7),
        move_offset="""\t\t\t\t\t\t\t<Element class="AssetObjects..ArtDefReferenceValue">
\t\t\t\t\t\t\t\t<m_ElementName text="Default"/>
\t\t\t\t\t\t\t\t<m_RootCollectionName text="Coord3D_WS"/>
\t\t\t\t\t\t\t\t<m_ArtDefPath text="Overlay.artdef"/>
\t\t\t\t\t\t\t\t<m_CollectionIsLocked>false</m_CollectionIsLocked>
\t\t\t\t\t\t\t\t<m_TemplateName text="Overlay"/>
\t\t\t\t\t\t\t\t<m_ParamName text="MoveOffset"/>
\t\t\t\t\t\t\t</Element>
""",
        fow_model=blp_ref(box, "HexModelFOW", "\t" * 7))


# LensModel 子元素（ReligionLensIcons/ReligionLensArrows 用）：单 BLPEntryValue BaseModel 引用
LENSMODEL_CHILD = """\t\t\t\t\t<Element>
\t\t\t\t\t\t<m_Fields>
\t\t\t\t\t\t\t<m_Values>
{ref}\t\t\t\t\t\t</m_Values>
\t\t\t\t\t\t</m_Fields>
\t\t\t\t\t\t<m_ChildCollections/>
\t\t\t\t\t\t<m_Name text="{child}"/>
\t\t\t\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t\t\t\t</Element>
"""

def lensmodel_child(box: str, child: str) -> str:
    return LENSMODEL_CHILD.format(ref=blp_ref(box, "BaseModel", "\t" * 7), child=child)


def religion_pressure_element(r: str) -> str:
    """根集合 Overlays 下的 Religion_Pressure_{R} 元素（官方 Religion_Pressure_Buddhism 精简复制）。"""
    return f"""\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values/>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections>
{EMPTY_COLL.format(name="Filled")}{EMPTY_COLL.format(name="Texture")}\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="Model"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{pressure_model_child(r)}\t\t\t\t</Element>
{EMPTY_COLL.format(name="SplineBorder")}{EMPTY_COLL.format(name="LensModel")}\t\t\t</m_ChildCollections>
\t\t\t<m_Name text="Religion_Pressure_{r}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""


def lens_container_element(name: str, child: str, box: str) -> str:
    """ReligionLensIcons / ReligionLensArrows 元素：只带本宗教的 LensModel 子项。
    基础库已有同名元素，游戏合并时子集合追加（m_ReplaceMergedCollectionElements=false）。"""
    return f"""\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values/>
\t\t\t</m_Fields>
\t\t\t<m_ChildCollections>
{EMPTY_COLL.format(name="Filled")}{EMPTY_COLL.format(name="Texture")}{EMPTY_COLL.format(name="Model")}{EMPTY_COLL.format(name="SplineBorder")}\t\t\t\t<Element>
\t\t\t\t\t<m_CollectionName text="LensModel"/>
\t\t\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{lensmodel_child(box, child)}\t\t\t\t</Element>
\t\t\t</m_ChildCollections>
\t\t\t<m_Name text="{name}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""


def overlay_artdef(religions: list[str]) -> str:
    elements = ""
    for r in religions:
        elements += religion_pressure_element(r)
        elements += lens_container_element("ReligionLensIcons", f"RELIGION_{r}",
                                           f"Religion_Overlay_{r}_Box")
        elements += lens_container_element("ReligionLensArrows", f"RELIGION_{r}",
                                           f"Religion_Pressure_{r}_Box")
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
# 官方结构（Base/ArtDefs/StrategicView.artdef）：
#   UILenses:     RELIGION_{R}（PositionSet=1_Center + PlacementRule=ReligiousPressure，
#                  Entries: Arrow -> 共享箭头条目 / Icon -> ReligionPressureIcon_{R}）
#   UILensEntries: ReligionPressureIcon_{R}（StrategicView_Sprite XLP 条目引用）
# 官方字段值逐字段复制（PlacementRule 与 PositionSet 的 ArtDefPath 均为 StrategicView.artdef）。

SV_LENS_RELIGION = """\t\t<Element>
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
\t\t\t\t\t\t<m_ElementName text="ReligiousPressure"/>
\t\t\t\t\t\t<m_RootCollectionName text="PlacementRules"/>
\t\t\t\t\t\t<m_ArtDefPath text="StrategicView.artdef"/>
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
\t\t\t\t\t\t\t\t\t<m_ElementName text="ReligionPressureIcon_{r}"/>
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
\t\t\t<m_Name text="RELIGION_{r}"/>
\t\t\t<m_AppendMergedParameterCollections>false</m_AppendMergedParameterCollections>
\t\t</Element>
"""

SV_LENS_ENTRY = """\t\t<Element>
\t\t\t<m_Fields>
\t\t\t\t<m_Values>
\t\t\t\t\t<Element class="AssetObjects..BLPEntryValue">
\t\t\t\t\t\t<m_EntryName text="{sprite}"/>
\t\t\t\t\t\t<m_XLPClass text="StrategicView_Sprite"/>
\t\t\t\t\t\t<m_XLPPath text="StrategicView_UILenses.xlp"/>
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
\t\t\t\t\t\t<m_XLPPath text="StrategicView_UILenses.xlp"/>
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

SV_ROOT_SKELETON = ["EffectEntries", "Effects", "UILenses", "UILensEntries"]

def strategicview_artdef(religions: list[str]) -> str:
    lenses = "".join(SV_LENS_RELIGION.format(r=r) for r in religions)
    entries = "".join(SV_LENS_ENTRY.format(sprite=f"ReligionPressureIcon_{r}",
                                           name=f"ReligionPressureIcon_{r}")
                      for r in religions)
    collections = ""
    for c in SV_ROOT_SKELETON:
        body = {"UILenses": lenses, "UILensEntries": entries}.get(c, "")
        collections += f"""\t\t<Element>
\t\t\t<m_CollectionName text="{c}"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
{body}\t\t</Element>
"""
    return XML_DECL + """<AssetObjects..ArtDefSet>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_TemplateName text="StrategicView"/>
\t<m_RootCollections>
{collections}\t</m_RootCollections>
</AssetObjects..ArtDefSet>
""".format(collections=collections)

# ---------------------------------------------------------------- mtl / ast（与 loyalty 同构，仅命名换 Religion）

MTL = """{xml}<AssetObjects..MaterialInstance>
\t<m_CookParams>
\t\t<m_Values>
\t\t\t<Element class="AssetObjects..ObjectValue">
\t\t\t\t<m_ObjectName text="Religion_{Kind}_{r}"/>
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
\t<m_Name text="Religion_{Kind}_{r}_material"/>
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
\t\t\t\t\t\t\t\t\t<m_ObjectName text="Religion_{Kind}_{r}_material"/>
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
\t<m_Name text="Religion_{Kind}_{r}_Box"/>
\t<m_Description text=""/>
\t<m_Tags/>
</AssetObjects..AssetInstance>
"""

# 与 loyalty 同一套官方几何：Overlay=HexModelGeo/FADE_LOOP，Pressure=PipModelGeo/NONE；
# group 必须是 "09 - Default"（PipModelGeo 官方网格组名，组名对不上压力小图标不渲染）
AST_OVERLAY = dict(model="Hex", geo="HexModelGeo", group="09 - Default",
                   mesh="Official_Hex 034", anim="FADE_LOOP", autoplay="true")
AST_PRESSURE = dict(model="PipModel", geo="PipModelGeo", group="09 - Default",
                    mesh="PipModel", anim="NONE", autoplay="false")

# ---------------------------------------------------------------- 辅助（与 gen_loyalty_art.py 同款）

def rsuffix(rel_type: str) -> str:
    if not rel_type.startswith("RELIGION_"):
        raise SystemExit(f"错误：宗教类型 {rel_type} 必须以 RELIGION_ 开头")
    r = rel_type[len("RELIGION_"):]
    if re.fullmatch(r"CUSTOM(_\d+)?", r, re.IGNORECASE):
        raise SystemExit(
            f"错误：{rel_type} 撞官方预留位（RELIGION_CUSTOM_1~12 已由基础库注册，"
            f"换图请直接覆盖对应贴图，不走本脚本；新宗教请用自定义类型名）")
    return r


def read_preserve(path: Path) -> tuple[str, str]:
    """读取文件并返回 (统一为 \\n 的文本, 原换行风格)。不改变原有换行风格。"""
    with open(path, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    return (raw.replace("\r\n", "\n"), "\r\n" if crlf else "\n")


def write_preserve(path: Path, text: str, newline: str) -> None:
    if newline != "\r\n":
        newline = "\r\n"
    path.parent.mkdir(parents=True, exist_ok=True)
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
            text = text.replace("<m_Entries/>", "<m_Entries>\n\t</m_Entries>")
        text = text.replace("\t</m_Entries>", new_entries + "\t</m_Entries>")
        write_preserve(path, text, nl)
        results.append(f"  追加   {path}（{new_entries.count('<m_EntryID')} 条）")
    else:
        entries = "".join(XLP_ENTRY.format(eid=e) for e in entry_ids)
        write_preserve(path, XLP_HEAD.format(xml=XML_DECL, cls=cls, pkg=pkg, entries=entries), "\r\n")
        results.append(f"  创建   {path}")


def append_into_collection(text: str, coll_name: str, blocks: list[str]) -> tuple[str, list[str]]:
    """把 blocks 插入到根集合 coll_name 的开头（元素顺序无关），返回 (新文本, 实际插入的块)。

    锚点 = 根集合开头的 <m_CollectionName text="{coll}"/> + 紧随的
    <m_ReplaceMergedCollectionElements .../> 行。找不到锚点时返回原文本。
    """
    pat = re.compile(
        r'(<m_CollectionName text="' + re.escape(coll_name) + r'"/>\s*'
        r'<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>\s*\n)')
    m = pat.search(text)
    if not m:
        return text, []
    inserted = [b for b in blocks if b not in text]
    if not inserted:
        return text, []
    pos = m.end(1)
    return text[:pos] + "".join(inserted) + text[pos:], inserted


def append_lensmodel_child(text: str, container: str, child_block: str) -> tuple[str, bool]:
    """向已存在的 container 元素（ReligionLensIcons/ReligionLensArrows）的 LensModel
    子集合末尾追加 child_block。container 元素的 m_Name 在其子集合之后，因此从 m_Name
    位置向前找最近的 LensModel 集合开锚、向后找该集合的关闭标签。"""
    name_pat = f'<m_Name text="{container}"/>'
    idx = text.find(name_pat)
    if idx == -1:
        return text, False
    anchor = text.rfind('<m_CollectionName text="LensModel"/>', 0, idx)
    if anchor == -1:
        return text, False
    # LensModel 集合自身的关闭标签是 4 缩进的 </Element>（子元素关闭是 5 缩进，不会误匹配）
    close = text.find("\n\t\t\t\t</Element>", anchor)
    if close == -1 or close > idx:
        return text, False
    return text[:close] + "\n" + child_block.rstrip("\n") + text[close:], True


def merge_overlay_artdef(p: Path, religions: list[str], results: list[str]) -> None:
    """Overlay.artdef：不存在则整体生成；存在则按官方同名元素合并语义幂等追加。"""
    text, nl = read_preserve(p)
    orig = text
    notes: list[str] = []

    # 1) 缺失的元素：Religion_Pressure_{R} 根元素；ReligionLensIcons/ReligionLensArrows
    #    容器（文件里没有才整体追加；已有则走第 2 步的子项插入）
    new_elements = []
    has_icons = '<m_Name text="ReligionLensIcons"/>' in text
    has_arrows = '<m_Name text="ReligionLensArrows"/>' in text
    pressure_blocks = [religion_pressure_element(r) for r in religions
                       if f'<m_Name text="Religion_Pressure_{r}"/>' not in text]
    for r in religions:
        if not has_icons:
            new_elements.append(lens_container_element("ReligionLensIcons", f"RELIGION_{r}",
                                                       f"Religion_Overlay_{r}_Box"))
            has_icons = True  # 同批多宗教时容器只补一次
        if not has_arrows:
            new_elements.append(lens_container_element("ReligionLensArrows", f"RELIGION_{r}",
                                                       f"Religion_Pressure_{r}_Box"))
            has_arrows = True
    blocks = pressure_blocks + new_elements
    if blocks:
        text, inserted = append_into_collection(text, "Overlays", blocks)
        if not inserted:
            notes.append("    警告   找不到 Overlays 根集合锚点，请手动合并 " + str(p))

    # 2) 已有容器时，把缺失的 RELIGION_{r} 子项插进 LensModel
    for r in religions:
        child_icons = lensmodel_child(f"Religion_Overlay_{r}_Box", f"RELIGION_{r}")
        child_arrows = lensmodel_child(f"Religion_Pressure_{r}_Box", f"RELIGION_{r}")
        if f'<m_Name text="RELIGION_{r}"/>' in text:
            continue  # 本文件已有该宗教子项（SV 侧同名元素共用此名，视为已处理）
        for container, child in (("ReligionLensIcons", child_icons),
                                 ("ReligionLensArrows", child_arrows)):
            if f'<m_Name text="{container}"/>' in text:
                text, ok = append_lensmodel_child(text, container, child)
                if not ok:
                    notes.append(f"    警告   {container} 缺少 LensModel 锚点，RELIGION_{r} 子项未插入，请手动合并")

    if text != orig:
        write_preserve(p, text, nl)
        results.append(f"  更新   {p}")
    else:
        results.append(f"  未变   {p.name}（宗教条目已存在）")
    results.extend(notes)


def merge_strategicview_artdef(p: Path, religions: list[str], results: list[str]) -> None:
    """StrategicView.artdef：不存在则整体生成；存在则向 UILenses/UILensEntries 幂等追加。"""
    text, nl = read_preserve(p)
    orig = text
    notes: list[str] = []
    lens_blocks, entry_blocks = [], []
    for r in religions:
        if f'<m_Name text="RELIGION_{r}"/>' not in text:
            lens_blocks.append(SV_LENS_RELIGION.format(r=r))
        if f'<m_Name text="ReligionPressureIcon_{r}"/>' not in text:
            entry_blocks.append(SV_LENS_ENTRY.format(sprite=f"ReligionPressureIcon_{r}",
                                                     name=f"ReligionPressureIcon_{r}"))
    if lens_blocks:
        text, inserted = append_into_collection(text, "UILenses", lens_blocks)
        if not inserted:
            notes.append("    警告   找不到 UILenses 根集合锚点，请手动合并 " + str(p))
    if entry_blocks:
        text, inserted = append_into_collection(text, "UILensEntries", entry_blocks)
        if not inserted:
            notes.append("    警告   找不到 UILensEntries 根集合锚点，请手动合并 " + str(p))
    if text != orig:
        write_preserve(p, text, nl)
        results.append(f"  更新   {p}")
    else:
        results.append(f"  未变   {p.name}（宗教条目已存在）")
    results.extend(notes)


def patch_art_xml(art_xml: Path, results: list[str]) -> None:
    """幂等补齐 consumer 与 library 接线（与忠诚度共用同一组 consumer/library）。"""
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

    m = re.search(r'(<libraryName text="UILensAsset"/>\s*<relativePackagePaths>)(.*?)(</relativePackagePaths>)', text, re.DOTALL)
    if m and "UILensAssets" not in m.group(2):
        text = text[:m.end(1)] + '\n\t\t\t\t<Element text="UILensAssets"/>' + text[m.end(1):]

    if text != orig:
        write_preserve(art_xml, text, nl)
        results.append(f"  更新   {art_xml.name}（consumer/library 接线）")
    else:
        results.append(f"  未变   {art_xml.name}")


def patch_civ6proj(civ6proj: Path, content_files: list[str], results: list[str]) -> None:
    text, nl = read_preserve(civ6proj)
    missing = [f for f in content_files if f'<Content Include="{f}">' not in text]
    if not missing:
        results.append(f"  未变   {civ6proj.name}（Content 已齐）")
        return
    block = "".join(f'    <Content Include="{f}">\n      <SubType>Content</SubType>\n    </Content>\n' for f in missing)
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
    ap = argparse.ArgumentParser(description="文明6 新宗教压力/镜头图标注册链生成")
    ap.add_argument("--project", required=True, help="工程根目录（含 .Art.xml / .civ6proj）")
    ap.add_argument("--religion-types", required=True,
                    help="宗教类型，逗号分隔：RELIGION_CUSTOM_RGN,RELIGION_X2（勿用 RELIGION_CUSTOM_*）")
    args = ap.parse_args()

    project = Path(args.project)
    religions = [rsuffix(t.strip()) for t in args.religion_types.split(",") if t.strip()]
    art_xml = next(project.glob("*.Art.xml"))
    civ6proj = next(p for p in project.glob("*.civ6proj") if not p.name.endswith(".Art.xml"))
    xlp_dir = project / ("XLPs" if (project / "XLPs").is_dir() else "Xlps")
    results: list[str] = []

    # 1. XLP 条目包
    gen_xlp(xlp_dir / "UILensModels.xlp", "UILensAsset", "UILensAssets",
            [f"Religion_Overlay_{r}_Box" for r in religions]
            + [f"Religion_Pressure_{r}_Box" for r in religions], results)
    gen_xlp(xlp_dir / "StrategicView_UILenses.xlp", "StrategicView_Sprite",
            "strategicview/strategicview_uilenses",
            [f"ReligionPressureIcon_{r}" for r in religions], results)

    # 2. ArtDef（存在则幂等合并追加，支持与忠诚度内容共存）
    artdefs = project / "ArtDefs"
    ov, sv = artdefs / "Overlay.artdef", artdefs / "StrategicView.artdef"
    if ov.exists():
        merge_overlay_artdef(ov, religions, results)
    else:
        results.append(write_if_changed(ov, overlay_artdef(religions)))
    if sv.exists():
        merge_strategicview_artdef(sv, religions, results)
    else:
        results.append(write_if_changed(sv, strategicview_artdef(religions)))

    # 3. 材质与 Box 素材
    for r in religions:
        for kind in ("Overlay", "Pressure"):
            results.append(write_if_changed(
                project / "Materials" / f"Religion_{kind}_{r}_material.mtl",
                MTL.format(xml=XML_DECL, Kind=kind, r=r)))
            fields = AST_OVERLAY if kind == "Overlay" else AST_PRESSURE
            results.append(write_if_changed(
                project / "Assets" / f"Religion_{kind}_{r}_Box.ast",
                AST_COMMON.format(xml=XML_DECL, Kind=kind, r=r, **fields)))

    # 4. Art.xml + civ6proj 注册（与忠诚度共用同一批 consumer/library/Content）
    patch_art_xml(art_xml, results)
    patch_civ6proj(civ6proj, [
        f"{xlp_dir.name}\\UILensModels.xlp",
        f"{xlp_dir.name}\\StrategicView_UILenses.xlp",
        "ArtDefs\\Overlay.artdef",
        "ArtDefs\\StrategicView.artdef",
    ], results)

    print("\n".join(results))
    print("\n待办（素材审核通过后）：源 PNG 留在原处直接转换，勿复制进工程（.tex 源路径可悬空）")
    for r in religions:
        print(f"  - Religion_Overlay_{r}.png → DDS + .tex 输出 Textures/（art-pipeline，role=loyalty_3d，512×512）")
        print(f"  - Religion_Pressure_{r}.png → DDS + .tex 输出 Textures/（role=loyalty_3d，128×128）")
        print(f"  - ReligionPressureIcon_{r}.png → DDS + .tex 输出 Textures/（role=loyalty_sv，128×128）")


if __name__ == "__main__":
    main()
