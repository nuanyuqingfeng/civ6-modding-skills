# Database XML Format

Game data is stored in an SQLite database. Mods modify it via XML files loaded through `UpdateDatabase` actions.

## Where to find base schemas

```
Base/Assets/Gameplay/Data/             -- 83+ XML data files
Base/Assets/Gameplay/Data/Schema/      -- SQL schema definitions
Base/Assets/Database/                  -- Modding framework schema
```

## XML Format

All database XML wraps tables in `<GameInfo>`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<GameInfo>
    <!-- Type registration (required for new types) -->
    <Types>
        <Row Type="UNIT_MY_WARRIOR" Kind="KIND_UNIT"/>
    </Types>

    <!-- Main data table -->
    <Units>
        <Row UnitType="UNIT_MY_WARRIOR"
             BaseMoves="2"
             Cost="100"
             Combat="35"
             BaseSightRange="2"
             ZoneOfControl="true"
             PrereqTech="TECH_IRON_WORKING"
             MandatoryObsoleteTech="TECH_GUNPOWDER"
             PromotionClass="PROMOTION_CLASS_MELEE"
             TraitType="TRAIT_CIVILIZATION_DEFAULT"/>
    </Units>

    <!-- Related tables -->
    <UnitUpgrades>
        <Row Unit="UNIT_MY_WARRIOR" UpgradeUnit="UNIT_SWORDSMAN"/>
    </UnitUpgrades>

    <UnitReplaces>
        <Row CivUniqueUnitType="UNIT_MY_WARRIOR" ReplacesUnitType="UNIT_WARRIOR"/>
    </UnitReplaces>
</GameInfo>
```

## Column Reference

> **Full column details (types, NotNull, Defaults): `PRAGMA table_info(TableName)` (DebugGameplay.sqlite)**
> **Detailed common-table schema with example values: `database/schema-annotated.md`**
> **Modifier/Effect/Requirement types: `SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'` (DebugGameplay.sqlite)**

## Key Database Tables

| Table | Purpose | Key Info |
|-------|---------|----------|
| `Types` | Type registration (required) | PK: `Type`, also `Kind` |
| `Units` | Unit definitions | 67 columns — see `PRAGMA table_info(Units)` |
| `UnitUpgrades` | Upgrade paths | `Unit` → `UpgradeUnit` |
| `UnitReplaces` | Unique unit replaces | `CivUniqueUnitType` → `ReplacesUnitType` |
| `Units_XP2` | GS expansion columns | `ResourceCost`, `CanFormMilitaryFormation` |
| `Buildings` | Building definitions | 46 columns — includes `PrereqDistrict`, `Housing`；`PrereqDistrict` 填被取代的原版区域（见 `gotchas.md` G15） |
| `Buildings_XP2` | GS expansion columns | `RequiredPower`, `PreventsFloods` |
| `Districts` | District definitions | 40 columns — includes `CostProgressionModel` |
| `Adjacency_YieldChanges` | 区域/改良相邻加成规则 | PK: `ID`，来源列 `AdjacentTerrain` / `AdjacentImprovement` / `AdjacentDistrict` 等 |
| `District_Adjacencies` | 区域 ↔ 相邻加成规则挂载 | `DistrictType` → `YieldChangeId` |
| `Improvements` | Tile improvements | 49 columns — includes `Buildable`, `Domain` |
| `Improvements_XP2` | GS expansion columns | `DisasterResistant`, `PreventsDrought` |
| `Technologies` | Tech tree entries | `Cost`, `EraType`, `UITreeRow` |
| `Civics` | Civics tree entries | `Cost`, `EraType`, `UITreeRow` |
| `Civilizations` | Civilization definitions | `Adjective`, `StartingCivilizationLevelType` |
| `Leaders` | Leader definitions | `InheritFrom`, `Sex` (default "Male") |
| `Traits` | Trait definitions | `InternalOnly` |
| `Policies` | Policy cards | `GovernmentSlotType`, `PrereqCivic` |
| `Governments` | Government types | `BonusType`, `InfluencePointsPerTurn` |
| `Modifiers` | Modifier definitions | `SubjectRequirementSetId`, `RunOnce` |
| `ModifierArguments` | Modifier params | PK: (`ModifierId`, `Name`) |
| `Requirements` | Requirement definitions | `RequirementType`, `Inverse` |
| `RequirementArguments` | Requirement params | PK: (`RequirementId`, `Name`) |
| `Resources` | Resource definitions | `ResourceClassType`, `Frequency` |
| `Features` | Map features | `Removable`, `AddsFreshWater`, `NaturalWonder` |
| `Terrains` | Terrain types | `MovementCost`, `Hills`, `Water` |
| `Yields` | Yield types | `IconString`, `DefaultValue` |
| `Eras` | Era definitions | `ChronologyIndex`, `GreatPersonBaseCost` |
| `GlobalParameters` | Global constants | `Name`, `Value` |
| `PlayerColors` | Color definitions | `PrimaryColor`, `SecondaryColor`, `TextColor`, `Alt1/2/3PrimaryColor`, `Alt1/2/3SecondaryColor`（参考库取 `Color_Tables.xml` + `ColorManager.sql` 并集） |
| `BaseGameText` | Localization | PK: `Tag`, also `Text` |
| `IconDefinitions` | Icon atlas mapping | PK: `Name`, also `Atlas`, `Index` |
| `PlayerItems` | 选人界面特色物品清单（**Config 库**） | 准入规则见下节 |

## `PlayerItems` 准入规则

入 `PlayerItems` 的对象必须在注册时带 `TraitType`，且该 `TraitType` 已通过 `LeaderTraits` 或 `CivilizationTraits` 关联到本行的 `LeaderType` / `CivilizationType`。主体限 `Districts` / `Units` / `Buildings` / `Improvements` 四张表。

`Projects` 表没有 `TraitType` 列，项目永远不进 `PlayerItems`。原版全表实测（`DebugConfiguration.sqlite → PlayerItems`，421 行）：`KIND_BUILDING` 56 / `KIND_DISTRICT` 66 / `KIND_IMPROVEMENT` 82 / `KIND_UNIT` 217 / `KIND_PROJECT` 0。

该违规不产生任何报错——Config 侧写错只是让选人界面多出一条不该出现的条目。机械拦截在 `scripts/rgn_validate_runner.mjs` 的「FrontEnd 清单资格」一节：它在 Config 库副本上清空 `PlayerItems`、重放项目 SQL，把 Gameplay 快照的 `TraitType` 与关联表复制进来做跨库查询，只判定项目新增的行。

## Adjacency_YieldChanges 与 District_Adjacencies

区域相邻加成由两张表组成：`Adjacency_YieldChanges` 定义一条「来源 + 产出」规则，`District_Adjacencies` 把它挂到具体区域上。固定加成优先用这两张表；需要科技/人文等动态条件时才改用 `EFFECT_*_ADJACENCY` 系列 Modifier（见 `reference/modifiers-catalog/modifier-improvement-plot.md`）。

`Adjacency_YieldChanges` 关键列：

| 列 | 说明 |
|---|---|
| `ID` | 主键，工程内建议带项目缩写 |
| `Description` | 必须指向 `LOC_` 文本键，游戏内相邻加成提示用；文本格式见下方文档 |
| `YieldType` | `YIELD_*` |
| `YieldChange` | 每个触发来源的产出量 |
| `TilesRequired` | 默认 `1`；`2` 表示每 2 个来源触发 1 次（半级加成） |
| `OtherDistrictAdjacent` | `1` = 其它区域相邻计数，`0` = 关闭 |
| `Self` | `1` = 区域自身作为来源（自相邻） |
| 来源列 | `AdjacentTerrain` / `AdjacentFeature` / `AdjacentImprovement` / `AdjacentDistrict` / `AdjacentResource` 等，每行只填一个 |

`District_Adjacencies` 只有两列：`DistrictType` 与 `YieldChangeId`。替换原版区域的特色区域不会自动继承原区域挂载，需要自行复制或逐条挂载。

相邻加成 `Description` 的文本必须包含 `{1_num}` 动态数字与 `[ICON_产出]` 图标，写法规范与完整模板见 `reference/modifiers-catalog/modifier-improvement-plot.md` 的「相邻加成本地化文本铁律」和 `xml-templates.md` 的「自定义区域相邻加成模板」。

## 取代对象的子表复刻

`BuildingReplaces` / `DistrictReplaces` / `UnitReplaces` 只登记取代映射：引擎按它把特色对象当作原版对象参与建造资格判定。被取代对象在各子表里的行不会被继承，特色对象在某张子表里零行时，该表承载的行为静默丢失、加载期零报错。

取料：

```bash
python scripts/replacement_subtables.py <工程根> --diff          # 未覆盖表清单，有未覆盖时退出码 1
python scripts/replacement_subtables.py <工程根> --diff --sql    # 连同可照抄的 INSERT
python scripts/replacement_subtables.py <工程根> --object DISTRICT_HOLY_SITE --sql
```

标准写法是把被取代对象的行原样搬过来，只换主体列：

```sql
INSERT INTO Building_YieldChanges (BuildingType, YieldType, YieldChange)
SELECT 'BUILDING_XXX_ELY', YieldType, YieldChange
FROM Building_YieldChanges WHERE BuildingType = 'BUILDING_TEMPLE';
```

主体列只有两类：表名以对象族开头且列名以 `Type` 结尾（`Building_YieldChanges.BuildingType`、`District_Adjacencies.DistrictType`、`Units_XP2.UnitType`），以及 `BuildingPrereqs.Building` 与 `Unit_BuildingPrereqs.Unit` 这两张用裸列的。其余列照抄。`ModifierArguments.Value`、`StartingBuildings.Building`、`MajorStartingUnits.District`、`MutuallyExclusiveDistricts.District` 是别人的表在引用该对象，复刻过去等于把起始配给与互斥关系搬错位置；`Prereq*` 列是反向引用（该行要求某个对象存在），同样只读不抄。

复刻是**写入阶段**的动作，不设常规校验项：手动删除子表行属持久意图，把这类删除当缺陷的校验器必然误报。完整口径与触发时机见 `gotchas.md` G15b。

## Removing Data

Use `<Delete>` tags in XML loaded before your data:

```xml
<?xml version="1.0" encoding="utf-8"?>
<GameData>
    <Units>
        <Delete UnitType="UNIT_WARRIOR"/>
    </Units>
    <Buildings>
        <Delete BuildingType="BUILDING_MONUMENT"/>
    </Buildings>
</GameData>
```

移除动作要早于主数据。两种写法都有效，按「想控制动作之间还是动作内部」选用。
> **默认不必为它拆动作**（动作划分判据见 `reference/action-splitting.md`）：只有 `criteria` 不一致、或库归属不同时，才**必须**拆。

**写法 A：独立动作 + `LoadOrder="-100"`**（控制动作之间的先后）：
```xml
<!-- 移除先跑 -->
<UpdateDatabase id="MyRemove" criteria="MyCriteria">
    <Properties><LoadOrder>-100</LoadOrder></Properties>
    <File>Data/MyRemoveData.xml</File>
</UpdateDatabase>
<!-- 主数据后跑（默认 LoadOrder=0） -->
<UpdateDatabase id="MyData" criteria="MyCriteria">
    <File>Data/MyGameplayData.xml</File>
</UpdateDatabase>
```

**写法 B：同一动作内用文件级 `Priority`**（控制动作内部各文件的先后，无需拆动作）—— **数值越大越先**（反直觉）：
```xml
<UpdateDatabase id="MyData" criteria="MyCriteria">
    <File Priority="2">Data/MyRemoveData.xml</File>   <!-- 数值大 → 先跑 -->
    <File>Data/MyGameplayData.xml</File>              <!-- 无 Priority → 后跑 -->
</UpdateDatabase>
```

## Adding Localized Text

```xml
<?xml version="1.0" encoding="utf-8"?>
<GameData>
    <BaseGameText>
        <Row Tag="LOC_MY_UNIT_NAME">
            <Text>My Warrior</Text>
        </Row>
        <Row Tag="LOC_MY_UNIT_DESC">
            <Text>A custom warrior unit for testing.</Text>
        </Row>
    </BaseGameText>
</GameData>
```

> **🔴 SQL 编码陷阱：单引号转义** — 若用 `.sql` 文件写 `INSERT OR REPLACE INTO LocalizedText`，文本内的单引号 `'` 必须写成两个连续单引号 `''`（SQL 标准转义，反斜杠 `\'` 无效）。例如：
> ```sql
> ('LOC_CITY_NAME_EXAMPLE', 'en_US', 'Penitent''s End'),  -- ✓ 正确
> ('LOC_CITY_NAME_EXAMPLE', 'en_US', 'Penitent\'s End'),  -- ✗ 错误
> ```

## Schema Files

Core SQL schema at `Base/Assets/Gameplay/Data/Schema/`:
- `01_GameplaySchema.sql` — Core tables
- `02_AddTriggers.sql` — Database triggers
- Additional schema in XML format for colors, diplomacy, leaders, etc.

When adding new columns to existing tables, use SQL in a `.sql` file loaded before data:
```sql
ALTER TABLE Units ADD COLUMN MyCustomColumn TEXT DEFAULT NULL;
```

## Player Colors

```xml
<GameInfo>
    <PlayerColors>
        <Row Type="PLAYERCOLOR_MYMOD_BLUE"
             Usage="Unique" PrimaryColor="COLOR_PLAYER_BLUE"
             SecondaryColor="COLOR_PLAYER_WHITE"
             Alt1SecondaryColor="COLOR_PLAYER_YELLOW"
             Alt2SecondaryColor="COLOR_PLAYER_RED"
             Alt3SecondaryColor="COLOR_PLAYER_PURPLE"/>
    </PlayerColors>
</GameInfo>
```

## Icons

```xml
<GameInfo>
    <IconDefinitions>
        <Row Name="ICON_UNIT_MY_WARRIOR" Atlas="ICON_ATLAS_UNITS" Index="1"/>
    </IconDefinitions>
</GameInfo>
```

## ModifierType / Requirement / Effect 深度参考

### 结构化数据查询（🔴 SQLite 优先）

**所有游戏数据查询直接用 DebugGameplay.sqlite**：

```sql
-- 按关键词搜索 ModifierType
SELECT * FROM Modifiers WHERE ModifierType LIKE '%ATTACH%';

-- 查看 ModifierType 的参数签名
SELECT Name, Value FROM ModifierArguments WHERE ModifierId='MODIFIER_XXX';

-- 按关键词搜索 Requirement
SELECT * FROM Requirements WHERE RequirementType LIKE '%CITY%';

-- 按关键词搜索 Effect
SELECT EffectType, CollectionType FROM DynamicModifiers WHERE EffectType LIKE '%ADJUST%';

-- 中英类型名查找
SELECT UnitType FROM Units WHERE UnitType LIKE '%WARRIOR%';
-- 中文名查询: DebugLocalization.sqlite LocalizedText 表
```

### SQL 模板 (`database/scripts/`)

- `sql_query_templates.sql` — 8 种常用 SQL 模式（建筑加成、单位强化、嵌套 Modifier 等），可直接复制修改
- `requirement_reference.sql` — RequirementType 分类整理（实测 `Requirements` 表去重 **327** 个类型 / 1051 行；本文件收录其中常用类型），含完整示例

> **CLI 备份**: `py database/scripts/query_civ6_db.py` 是 SQLite 的命令行封装，不便写 SQL 时可用。

### 高级参考

- `reference/MODIFIER_ARGUMENTS.md` — Modifier 参数分类详解（11 类：Yield/Unit/Building/District/...），含取值列表
- `reference/WORKSHOP_PATTERNS.md` — 高级 SQL 模式：批量生成、CTE、自定义 DynamicModifier、多层附件链
- `reference/TYPE_NAME_MAPPING.md` — Type→中英文名称查询 + Trait→LocalizedText 关联链 SQL
- `database/modifiers-guide.md` — Modifier 系统完整指南（原 civ6-mod-database 技能文件）

## PROPERTY 系统快速参考

### 写入 Modifier 对照

| ModifierType | 作用对象 | 典型绑定 |
|-------------|---------|---------|
| `MODIFIER_PLAYER_ADJUST_PROPERTY` | 玩家 | TraitModifiers / DistrictModifiers / BuildingModifiers |
| `MODIFIER_SINGLE_CITY_ADJUST_PROPERTY` | 单城市 | BuildingModifiers / DistrictModifiers / GovernorPromotionModifiers |
| `MODIFIER_UNIT_ADJUST_PROPERTY` | 单单位 | UnitAbilityModifiers |

### 引擎级读出渠道（仅两种）

| 机制 | 适用范围 | 用途 |
|------|---------|------|
| `REQUIREMENT_PLOT_PROPERTY_MATCHES` | **仅地块** | 条件开关，分级检测（PropertyMinimum=1/2/3...） |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` + Key | **仅单位战斗力** | 读 PROPERTY 值自动叠加战斗力 |

**不存在 `CITY_PROPERTY_MATCHES` 或 `UNIT_PROPERTY_MATCHES`。**
城市/玩家 PROPERTY 的能力开关或数值输入均需 Lua。

详细设计：SKILL.md Rule 0.9。

## DB.Query() — SQL in Lua

Only works in InGame (UI environment has `DB.ConfigurationQuery()` for FrontEnd):

```lua
local results = DB.Query("SELECT * FROM Units WHERE TraitType IS NULL AND CanTrain = 1");
if results and #results > 0 then
    for _, row in ipairs(results) do
        print(row.UnitType);
    end
end
```

## DLC 来源查询（source_index.sqlite）

> `database/source_index.sqlite` 记录官方 XML 行的 DLC 来源（2026-08 全量校准，457 表 / 5.8 万行，已与 DebugGameplay 清理态同步）。

### 表结构

| 表 | 说明 |
|----|------|
| `row_source(table_name, pk_json, pk_text, source, first_file, first_line, op)` | 行级来源：每行主键 + 来源 + 首个定义文件:行号 |
| `table_summary(table_name, distinct_pk, base_rows, exp1_rows, exp2_rows, dlc_rows)` | 每表来源分布统计 |
| `missing_tables` | 官方 XML 中存在但 Debug 库无此表名的表（UI/Config 相关，如 IconDefinitions） |
| `dlc_dependency(ModifierType, IsDlcDependency, Source, FirstFile, Note)` | 人工标注的 Mode/Scenario DLC 依赖（12 行，来自 `database/annotations/dynamic_modifiers_dlc.json`）。**不是 `DynamicModifiers` 的列**，只在此元数据库存在 |

> 补全/清理的过程日志（missing_rows、patch_log、cleanup_log）已按清理要求删除；操作摘要见 `database/CALIBRATION_LOG_2026-08.md`。

### 来源判定规则

1. **Base 优先**：同一主键在 Base 与 DLC 都出现 → `Base`（Base 定义为主）
2. **Expansion 次之**：Base 无 → `Expansion1` / `Expansion2`
3. **具体 DLC**：再没有才标文件夹名（`Babylon`、`GranColombia_Maya`、`Ethiopia` 等）

> **row_source 与 DB 一致性**：非领袖 DLC（情景 `*Scenario` / 模式 `BarbarianClansMode`、`TreeRandomizer`）来源的内容表行已从 DebugGameplay 删除，row_source 同步删除——`row_source` 中标注的行均可在 DB 查到（系统表保留的情景机制行除外，其词典定义仍有效）。

### 查询示例

```sql
-- 某 Modifier 来自哪个 DLC
SELECT source, first_file, first_line FROM row_source
WHERE table_name='Modifiers' AND pk_text LIKE '%MY_MODIFIER%';

-- 某表 Base vs DLC 分布
SELECT * FROM table_summary WHERE table_name='Types';

-- 某 DLC 定义了哪些 Types
SELECT pk_text, first_file FROM row_source
WHERE table_name='Types' AND source='Ethiopia';
```

### 注意

- `pk_text` 为规范化主键（列名大小写、BOOLEAN/INTEGER 类型已对齐 DB）
- **Update/Delete 操作不参与来源判定**（不定义行）；Replace 与 Row 等效
- 引擎自动主键表（`UniqueId`/`PrimaryKey`/`ID` 自增列，如 `BehaviorTreeNodes`）行级无法比对，仅在 `table_summary` 统计
- LocalizedText（文本）不收录，见 DebugLocalization.sqlite
- 领袖/文明包 DLC（Babylon、Ethiopia、Portugal、GranColombia_Maya 等）来源行全部保留，可在 row_source 中按文件夹名查询

### 2026-08 校准摘要

1. **补全**：DebugGameplay/DebugConfiguration 原为旧版导出，缺 8,770 行官方 XML 数据 → 用官方 XML 补全 +8,330 行（补全详情见 `CALIBRATION_LOG_2026-08.md`）
2. **清理**：删除 4,459 行非领袖 DLC（情景/模式）来源的内容表行 + Types 内容类 Kind 行——情景专属内容（如 `UNIT_EXPLORER`、`BUILDING_PLAGUE_HOSPITAL`）常规对局不存在，保留会污染查询导致误用报错
3. **保留**：系统词典表全量（Requirements/RequirementSets/Modifiers/ModifierArguments/DynamicModifiers/TypeTags 等，含情景新机制定义）；Types 系统类 Kind；全部领袖 DLC 与资料片内容

**查询一致性提示**：`Types` 表与内容表同步清理（查 `Units`/`Buildings` 命中的 Type 必在 `Types` 存在）；`Modifiers`/`Requirements` 表保留全量词典（查 `ModifierType`/`RequirementType` 能看到全部官方定义，含情景）。

