---
name: civ6-art-reference
description: "Civ6 mod 引用原版美术素材全流程：ArtDef/XLP 四层引用链（DB Type → artdef 条目 → Xref → BLPEntryValue → 打包资产）查询与克隆生成，外加一层 cook 层机制（.Art.xml 依赖声明 → pantry 解析、产物归一化、警告即静默降级、XLP 条目可解析性与打包后果、源/产物差异分级判定）。适用场景：为新增资源/区域/建筑/改良/单位配置原版模型素材（按语义自动匹配相近原版对象并完整复制其美术引用）、查询某对象用哪些模型/贴图/战略视图、排查美术引用悬空、排查 ArtDef 双端不同步（编码层 CRLF/LF vs 语义层 _MissingArt）与 cook 报错（pantry 找不到、引用被替换成默认值）、单位渲染残缺（如只剩头）。内含建筑 hero-building 组合链（BuildingSets/BaseVariants/BuildingVariants）与替换型建筑上模型流程。内置全量引用链索引（Base+全DLC artdef + SDK 262 xlp）与五个工具：artdef_indexer（重建索引）/ art_lookup（查链路/列条目/列包/反查建筑模型链）/ art_copy（克隆原版条目为 mod 条目）/ art_copy_building（替换型建筑 3D 注册一键生成）/ artdef_sync_check（源 vs Mods 副本差异分级体检）。不处理 2D 图标链（除非悬空），不解包任何 .blp。领袖/文明美术另有 civ6-asset-forge 专项 skill。"
version: "1.3"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - artdef
  - xlp
  - blp
  - 美术引用
  - 建筑模型
  - 区域 hero 建筑
  - modding
models:
  recommended:
    - claude-sonnet-4
  compatible:
    - deepseek-v3
languages:
  - zh
  - en
---

## 目的与边界

为 mod 新对象（资源/区域/建筑/改良/单位/特征）配置**原版已打包的美术素材**：找到
相近功能的原版对象，完整复制其美术引用链。

边界：
- 2D UI 图标（IconTextureAtlases/Icons.xlp）默认不处理；仅当该图标引用的纹理在游戏内缺失时才补链

- **例外**：裸纹理名链（`Governors.PortraitImage` / `PortraitImageSelected`、
  `SecretSocieties.SmallIcon` 这类存纹理名、靠 UITexture XLP 按名查找的列）属于
  「悬空排查」高发区，见 `reference/chain-map.md` §七 —— 不走 artdef 也不走图集。
- 领袖立绘/文明图标走 civ6-asset-forge 专项 skill（reference/leader-2d.md / reference/loyalty-icon.md）。
- 素材源文件查询只读 SDK pantry；游戏合并集以 `Base/ArtDefs` + `DLC/**/ArtDefs` 为准。

## ⚠ 注意事项：mod 工程目录**本身就是 pantry**（曾致 AssetEditor 闪退）

AssetEditor / cooker 会把**整个工程目录树**递归当 pantry 扫描 —— **不只是 `Textures/`**。
任何位置的 `.tex` 都会被注册为贴图实体，同名副本会抢占注册。实测（2026-09-12）：同名 `.tex` 副本 + `m_SourceFilePath` 为 depot 库路径 `//civ6/main/...`
→ AE 版本状态更新抛 `NotSupportedException: 不支持给定路径的格式` → 日志 `CRASH` → **浏览素材时闪退**。
复盘：`workspace/specs/2026-09-12-duplicate-tex-ae-crash.md`。

**四条硬性规则**

1. **`.tex` 只允许存在于 `Textures/`**，每个资产只留一份；`workspace/`、`gen/`、`tmp/`、`*_reimport/`、任何备份/中间目录**严禁**出现 `.tex`；
2. `m_Name` 与 `m_RelativePath` **全工程唯一**（`Textures/` 内同样不允许重名）；
3. `m_SourceFilePath` 统一为 **ASCII 虚拟路径**（本工程约定 `D:\desktop\<stem>.png`）；**严禁** `//civ6/main/...` 等 depot/库路径，严禁中文/乱码路径；
4. pantry 内文件名保持 **ASCII**。

**改名 `.tex` 时必须同步三元组**（否则 cooker 按旧名找贴图 → 全部引用条目变成 error asset「红色感叹号」）：

| 字段 | 必须同步为 |
|---|---|
| `m_Name` | `<新stem>` |
| `m_RelativePath` | `<新stem>.dds` |
| `.dds` 文件名 | `<新stem>.dds` |

> 同类坑：`.ast` 自身名与几何同名时，批量改名会误伤 `m_GeoName`。

**验证顺序**（贴图改动后）：

1. 跑 `scripts/check_pantry.py`（检查 `.tex` 位置 / 重名 / depot 路径 / 非 ASCII / `.tex`↔`.dds` 配对）—— 必须 0 error；
2. **清 AE 依赖缓存**（`%APPDATA%\AssetCloud\mod-<Mod>-asset-deps.json`）；
3. 再启动 AssetEditor，确认日志无 `CRASH`。

> ⚠ **缓存必须清**：不清缓存会出现假象 —— 问题文件已移走却仍显示不闪退。
> 参考实现：`scripts/check_pantry.py` 与 `scripts/clear_ae_cache.py`。
> 附带铁律：**禁止修改/替换 SDK 安装目录下的任何 DLL**。

## 原版美术资产路径（强制约定）

- **文明6游戏美术资产路径（唯一素材查找位置）**：
  `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets`
  （官方源素材库：`pantry\Textures` 内有散装 .dds 源贴图，另有 ArtDefs / XLPs / Geometries 等；
  `Civ6\pantry`、`Civ6\DLC\*\pantry` 为各资料片补充源素材。）
- 涉及原版美术资产的任务**只允许在上面这个路径里查找**，不得去其他目录挖素材。
- **任何情况下不允许尝试解包**：`.blp` 等打包文件一律不做解包/逆向/自写解包器，
  需要源素材时只查 pantry 的散装文件或通过引用链按名引用。
- 游戏安装根目录（`...\Sid Meier's Civilization VI`）仅用于读取 XML/Lua/数据库等
  游戏数据定义，不作为美术素材来源。

## 第一步：读文档

开始任何具体配置前，先读：

1. `reference/chain-map.md` — 引用链机制、分对象类别链路、XLP 包速查、坑
2. `reference/workflow.md` — 八步配置流程与工具用法
3. `reference/cook-layer.md` — **cook 层**：`.Art.xml` 依赖声明 → pantry 解析、
   产物归一化、警告即静默降级、XLP 条目可解析性；排「ArtDef 不同步 / cook 报错 /
   单位渲染残缺」类问题前先读这个
4. `CHANGELOG.md` — 版本改动与**实证来源**

## 第二步：查（art_lookup.py）

```bash
cd ~/.agents/skills/civ6-art-reference/scripts
python art_lookup.py RESOURCE_OLIVES Resources      # 条目引用链
python art_lookup.py --list Clutter CLUTTER_        # 列全部 clutter 候选
python art_lookup.py --xlp environment/clutter      # 列 XLP 包条目
python art_lookup.py --building BUILDING_AMPHITHEATER       # 反查建筑的 3D 模型链（在哪些区域/组合、落在哪个包）
python art_lookup.py --district-buildings DISTRICT_THEATER  # 列区域的 hero 组合表（标签 -> 建筑 -> 资产）
```

索引：`assets/art_index.json.gz`（Base+全DLC artdef、SDK 全部 xlp）。游戏更新后重建：

```bash
python artdef_indexer.py --out ../assets/art_index.json.gz
```

## 第三步：生成（art_copy.py）

```bash
python art_copy.py Resources RESOURCE_OLIVES RESOURCE_OLIVES_RGN \
    --set-xref CLUTTER_OLIVES \
    --out "<mod>/ArtDefs/Resources.artdef"
```

克隆原版条目整棵子树 → 改名 → 换 XrefName → 追加进 mod artdef（自动建骨架/幂等跳重）。

**替换型建筑（取代原版建筑）走另一条链**：建筑模型由「所在区域」给出，且必须反查
`DistrictReplaces`；完整步骤见 `reference/workflow.md` §④′，机制见 `reference/chain-map.md` §三.3：

```bash
python art_copy_building.py BUILDING_AMPHITHEATER BUILDING_GOLDEN_POETRY_SOCIETY_RGN --buildings-out "<mod>/ArtDefs/Buildings.artdef" --landmarks-out "<mod>/ArtDefs/Landmarks.artdef" --district DISTRICT_MY_RGN
```

`--district` 里的 **mod 侧区域不在索引里，必须显式给出**。

**两条铁律**：① 只能**新增**新标签子条目，绝不改名覆盖原版子条目；
② 必须把**所有**取代该区域的 District 都挂上（原版特色区域 + 本 mod 特色区域）。

## 第四步：注册与校验

- 新 artdef 文件挂进 mod `.Art.xml` 对应 consumer（如 `Resources` consumer 挂
  `Resources.artdef`）；`.civ6proj` 不需要条目。已有文件追加条目无需改 `.Art.xml`。
- **依赖声明**：用到 DLC 素材（条目属于哪个包）时，该包必须在 `.Art.xml` 的
  `<requiredGameArtIDs>` 里（传递依赖自动展开）。漏声明 → cooker 的 pantry 搜不到源
  文件 → 满屏 `Cannot cook the ArtDef ... does not exist in the pantry!` /
  `Unable to find the XLP (...)`。详见 `reference/cook-layer.md` §一。
- 校验：条目名=DB Type；`XrefName` 目标能用 art_lookup 查到；XML 可解析；
  引用 DLC 素材时 mod 依赖已声明。
- **cook 后校验（改动 artdef/xlp 后必做）**：
  ① 构建日志的 `Art Pantry Path` 行覆盖 `.Art.xml` 声明的全部包（漏声明时对应路径不出现）；
  ② 数清 `references … that does not exist` + `has had its value replaced with its
  default value` 的**对子数**，每对都能解释（真没美术 / 忘补条目）；
  ③ **重新 cook 一次，拿产物与 Mods 副本逐字节比对** —— 判断本次改动有无运行时影响只认这个。
  详见 `cook-layer.md` §三、§六。
- **「源 ↔ Mods 副本不一致」要分级看**：
  `python scripts/artdef_sync_check.py <工程名>`（或 `--all`）。
  L1–L5 命中（差异在某一级归一化后消失）= 纯编码层（行尾 / 自闭合写法 / 缩进 / 空行 / 注释），**可忽略**；
  五级归一化后仍不同 = 语义层，需分辨 `cook 补结构`（无害但永久）与
  `引用被清空`（`_MissingArt` / `text=""`，**真实缺陷**）。详见 `cook-layer.md` §2.2–2.4。
- 替换型建筑附加校验：① **原有子条目零丢失**（读改写前后同区域内各子集合的子条目名集合，
  旧集合必须是新集合的子集）；② 所有取代该区域的 District 都已挂。
  `art_copy_building.py` 自带第 ① 项自检，输出 `原有内容丢失 = 0` 才算过。
- **克隆单位条目前**：先按 `chain-map.md` §5.2 做 bin 可解析性体检（原版自身存在
  引用了不存在 bin 的成员类型，克隆过去会渲染残缺，典型表现是「只剩一个头」）。

## 排错速查

| 现象 | 先看 |
|---|---|
| 每次 build 后 artdef 与 Mods 副本「不同步」 | **先分级**：`python scripts/artdef_sync_check.py <工程名>`。L1–L5 命中 = 纯编码层（行尾/写法/缩进/空行/注释），可忽略；L5 仍不同才需看 → `cook-layer.md` §2.2 |
| 想让「不同步」彻底消失 | 把源 artdef 统一成 cook 规范写法（**LF + `<x/>` 紧凑 + 无注释**）→ 源即产物。2026-09 跨工程复核 → `cook-layer.md` §2.3 |
| 产物里出现 `_MissingArt` 或 `text=""` | **真实缺陷**：引用解析不到被 cook 清空 → `cook-layer.md` §2.4 |
| `Cannot cook the ArtDef ... does not exist in the pantry!` | `.Art.xml` `<requiredGameArtIDs>` 漏声明 → `cook-layer.md` §一 |
| `references an ArtDef entry (X) that does not exist` | 该 X 真的不存在；**语义已被降级成默认值** → `cook-layer.md` §三 |
| 日志出现 `error asset:` 但构建仍 succeeded | MSBuild 日志分级误报，不是错 → `cook-layer.md` §三.3 |
| 单位只剩一个头 / 缺身体 | 成员类型 bin 悬空 → `chain-map.md` §5.2 / §5.3 |

## 与本工程的约定

- 双目录工作流：源文件为准；同步 Mods 测试副本前先询问（细则见工程 AGENTS.md）。
- 新建/修改 artdef 后不在 rgn_validate 范围（那是 SQL 工具），按上文静态校验 + 游戏内验证。
- 默认不在源文件添加调试内容。

---

## 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮
