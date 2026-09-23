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
| `Buildings` | Building definitions | 46 columns — includes `PrereqDistrict`, `Housing` |
| `Buildings_XP2` | GS expansion columns | `RequiredPower`, `PreventsFloods` |
| `Districts` | District definitions | 40 columns — includes `CostProgressionModel` |
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

