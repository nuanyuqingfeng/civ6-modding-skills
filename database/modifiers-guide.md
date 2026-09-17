# Civilization VI Mod Database Guide

Quick reference for Civilization VI modding. This skill provides structured data, SQL templates, and a query tool for creating mods.

## When to Read What

| Need | Read This |
|------|-----------|
| **Find a ModifierType** | `SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'` (DebugGameplay.sqlite) |
| **Check ModifierType args** | `SELECT Name, Value FROM ModifierArguments WHERE ModifierId='X'` (DebugGameplay.sqlite) |
| **Find a RequirementType** | `SELECT * FROM Requirements WHERE RequirementType LIKE '%Key%'` (DebugGameplay.sqlite) |
| **Find a game type (Unit/Building/Civ)** | `SELECT UnitType FROM Units WHERE UnitType LIKE '%Key%'` (DebugGameplay.sqlite)；中文名用 DebugLocalization.sqlite |
| **Create a new Modifier** | This file (Quick SQL Template) + `database/scripts/sql_query_templates.sql` |
| **Lookup Type -> Name** | `reference/TYPE_NAME_MAPPING.md` |
| **Modifier parameter formats** | `reference/MODIFIER_ARGUMENTS.md` |
| **Advanced patterns (bulk SQL, attachments, timing flags)** | `reference/WORKSHOP_PATTERNS.md` |

## Query Tool

🔴 **SQLite 优先** — 一切结构化查询直接用 DebugGameplay.sqlite：

```sql
-- Search ModifierTypes
SELECT * FROM Modifiers WHERE ModifierType LIKE '%YIELD%';

-- Show argument template for a specific ModifierType
SELECT Name, Value FROM ModifierArguments WHERE ModifierId='MODIFIER_XXX';

-- Search Requirements
SELECT * FROM Requirements WHERE RequirementType LIKE '%CITY_HAS_BUILDING%';

-- Search DynamicModifiers (Collection + Effect mapping; official table has exactly 3 columns)
SELECT ModifierType, CollectionType, EffectType FROM DynamicModifiers WHERE EffectType LIKE '%ATTACH_MODIFIER%';

-- DLC/Mode dependency annotation (metadata DB: database/source_index.sqlite, NOT a game column)
SELECT * FROM dlc_dependency WHERE ModifierType LIKE '%KEYWORD%';

-- Search type names in Chinese or English
SELECT Type FROM Units JOIN LocalizedText ON Units.Name = LocalizedText.Tag
WHERE LocalizedText.Language = 'zh_Hans_CN' AND LocalizedText.Text = '纪念碑';
```

## Core Concepts

```
Trait → TraitModifiers → Modifier → ModifierType → Effect
                    ↓
            RequirementSet → Requirements
```

### Quick SQL Template: Create Modifier

```sql
-- 1. Create Modifier
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MONUMENT_SCIENCE_10', 'MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE');

-- 2. Add arguments
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MONUMENT_SCIENCE_10', 'BuildingType', 'BUILDING_MONUMENT'),
    ('MONUMENT_SCIENCE_10', 'YieldType', 'YIELD_SCIENCE'),
    ('MONUMENT_SCIENCE_10', 'Amount', '10');

-- 3. Bind to target (choose one)
INSERT INTO BuildingModifiers (BuildingType, ModifierId)
VALUES ('BUILDING_MONUMENT', 'MONUMENT_SCIENCE_10');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_CIVILIZATION_PEARL_DANUBE', 'MONUMENT_SCIENCE_10');
```

### Defensive INSERT Patterns

- **`INSERT OR REPLACE INTO`** — Override existing data intentionally.
- **`INSERT OR IGNORE INTO`** — Add new rows without failing if they already exist.

```sql
INSERT OR REPLACE INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('TRAIT_BOOST_HOLY_SITE_PRODUCTION', 'Amount', '42');

INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_CITY_HAS_CAMPUS', 'REQUIREMENT_CITY_HAS_DISTRICT');
```

## Modifier Binding Tables

Common `*_Modifiers` tables:

| Table | Target Field | Example Target |
|-------|--------------|----------------|
| `BeliefModifiers` | BeliefType | `BELIEF_GODDESS_OF_FIRE` |
| `BuildingModifiers` | BuildingType | `BUILDING_MONUMENT` |
| `CivicModifiers` | CivicType | `CIVIC_CODE_OF_LAWS` |
| `DistrictModifiers` | DistrictType | `DISTRICT_CAMPUS` |
| `GovernmentModifiers` | GovernmentType | `GOVERNMENT_MONARCHY` |
| `ImprovementModifiers` | ImprovementType | `IMPROVEMENT_FARM` |
| `PolicyModifiers` | PolicyType | `POLICY_SURPLUS_LOGISTICS` |
| `TechnologyModifiers` | TechnologyType | `TECH_BRONZE_WORKING` |
| `TraitModifiers` | TraitType | `TRAIT_CIVILIZATION_PEARL_DANUBE` |
| `UnitAbilityModifiers` | UnitAbilityType | `ABILITY_HEAVY_CHARIOT` |
| `UnitPromotionModifiers` | UnitPromotionType | `PROMOTION_FUROR` |
| `GovernorPromotionModifiers` | GovernorPromotionType | `GOVERNOR_PROMOTION_EDUCATOR_RESEARCHER` |
| `ProjectCompletionModifiers` | ProjectType | `PROJECT_LAUNCH_EARTH_SATELLITE` |
| `GameModifiers` | — | Global rules |

See `database/scripts/sql_query_templates.sql` for INSERT examples for all tables.

## RequirementSet System

When you need to **restrict when a Modifier applies**, use RequirementSets.

### Basic Structure

```
Modifiers.SubjectRequirementSetId → RequirementSet → Requirements
```

| Field | Checks | Example |
|-------|--------|---------|
| `OwnerRequirementSetId` | Who owns the modifier | Player is Hungary |
| `SubjectRequirementSetId` | What the modifier affects | Plot is capital |

### Common RequirementTypes

| Category | Types |
|----------|-------|
| **Plot** | `REQUIREMENT_PLOT_IS_OWNER_CAPITAL_CONTINENT`, `REQUIREMENT_PLOT_NEAR_CAPITAL`, `REQUIREMENT_PLOT_IS_HILLS`, `REQUIREMENT_PLOT_FEATURE_TYPE_MATCHES`, `REQUIREMENT_PLOT_TERRAIN_TYPE_MATCHES` |
| **City** | `REQUIREMENT_CITY_IS_ORIGINAL_CAPITAL`, `REQUIREMENT_CITY_HAS_BUILDING`, `REQUIREMENT_CITY_HAS_DISTRICT` |
| **Player** | `REQUIREMENT_PLAYER_HAS_CIVILIZATION_OR_LEADER_TRAIT`, `REQUIREMENT_PLAYER_HAS_TECHNOLOGY`, `REQUIREMENT_PLAYER_HAS_CIVIC`, `REQUIREMENT_PLAYER_IS_AT_WAR` |
| **Unit** | `REQUIREMENT_UNIT_TYPE_MATCHES`, `REQUIREMENT_UNIT_TAG_MATCHES` |
| **Logic** | `REQUIREMENT_COLLECTION_ALL_MET`, `REQUIREMENT_COLLECTION_ANY_MET`, `REQUIREMENT_REQUIREMENTSET_IS_MET` (for nesting) |

**RequirementType 实测共 327 个**（口径：`SELECT COUNT(DISTINCT RequirementType) FROM Requirements`；`Requirements` 1051 行 / `RequirementSets` 982 行）：`SELECT * FROM Requirements WHERE RequirementType LIKE '%Keyword%'` (DebugGameplay.sqlite) 或 `database/scripts/requirement_reference.sql`（常用类型分类整理）。

### Subject vs Owner Requirements

| Field | What it filters | Typical use |
|-------|-----------------|-------------|
| `SubjectRequirementSetId` | The **target** receiving the bonus | City has campus, plot is hills, unit is melee |
| `OwnerRequirementSetId` | The **source** granting the bonus | Player has a tech/civic, player is a specific civ |

A modifier can use **both at once**. Example: Gaul mine culture only after unlocking Humanism:

```sql
-- Owner gate: player must have CIVIC_HUMANISM
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_HAS_HUMANISM', 'REQUIREMENT_PLAYER_HAS_CIVIC');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_HAS_HUMANISM', 'CivicType', 'CIVIC_HUMANISM');
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_HAS_HUMANISM', 'REQUIREMENTSET_TEST_ALL');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_HAS_HUMANISM', 'REQ_HAS_HUMANISM');

-- Apply to the existing modifier
UPDATE Modifiers SET OwnerRequirementSetId = 'REQSET_HAS_HUMANISM'
WHERE ModifierId = 'GAUL_MINE_CULTURE';
```

## Applying Effects to All Major Civilizations

Bind the modifier to `TRAIT_LEADER_MAJOR_CIV` instead of creating a trait for every civilization.

```sql
-- Example: All major civs get +30 Production in cities with a Campus
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_CITY_HAS_CAMPUS', 'REQUIREMENT_CITY_HAS_DISTRICT');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_CITY_HAS_CAMPUS', 'DistrictType', 'DISTRICT_CAMPUS');
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_CITY_HAS_CAMPUS', 'REQUIREMENTSET_TEST_ALL');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_CITY_HAS_CAMPUS', 'REQ_CITY_HAS_CAMPUS');

INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_MAJOR_CIV_CAMPUS_PRODUCTION', 'MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE', 'REQSET_CITY_HAS_CAMPUS');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_MAJOR_CIV_CAMPUS_PRODUCTION', 'YieldType', 'YIELD_PRODUCTION'),
    ('MODIFIER_MAJOR_CIV_CAMPUS_PRODUCTION', 'Amount', '30');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_MAJOR_CIV_CAMPUS_PRODUCTION');
```

## Nested Modifiers (ATTACH_MODIFIER)

When a modifier needs to apply a **separate** sub-modifier with its own requirements, use an attachment modifier.

**Why you need this:** Many `MODIFIER_PLAYER_UNIT_*` and `MODIFIER_PLAYER_CITY_*` types operate on a **single** unit or city. If you want that effect to apply to **all** units/cities, wrap it in an **attachment modifier** that distributes the sub-modifier to every target in the collection.

Common attachment types:
- `MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER`
- `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER`
- `MODIFIER_ALL_CITIES_ATTACH_MODIFIER`

See `reference/WORKSHOP_PATTERNS.md` for a complete multi-sub-modifier example (Warriors +5 movement before turn 10).

## Global Game Modifiers

For rules that apply to the entire game regardless of player/civ, insert into `GameModifiers`:

```sql
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_FLOODPLAINS_FOOD', 'MODIFIER_GAME_ADJUST_PLOT_YIELD', 'REQSET_IS_FLOODPLAINS');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_FLOODPLAINS_FOOD', 'YieldType', 'YIELD_FOOD'), ('MODIFIER_FLOODPLAINS_FOOD', 'Amount', '1');
INSERT INTO GameModifiers (ModifierId)
VALUES ('MODIFIER_FLOODPLAINS_FOOD');
```

## Quick Reference Tables

### Common ModifierTypes

| Effect | ModifierType |
|--------|--------------|
| Building +X yield | `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE` |
| Building +X% yield | `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_MODIFIER` |
| City +X yield | `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE` |
| Capital city +X yield | `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_YIELD_CHANGE` |
| Unit +X combat | `MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` |
| District +X production | `MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION` |
| Building +X production | `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION` |
| Plot +X yield | `MODIFIER_PLAYER_ADJUST_PLOT_YIELD` / `MODIFIER_GAME_ADJUST_PLOT_YIELD` |
| Attach sub-modifier to units | `MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER` |
| Attach sub-modifier to cities | `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER` |
| Trade route +X yield | `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL` |

### YieldTypes

`YIELD_SCIENCE`, `YIELD_CULTURE`, `YIELD_GOLD`, `YIELD_FAITH`, `YIELD_PRODUCTION`, `YIELD_FOOD`

### RequirementSet Logic

| Type | Meaning |
|------|---------|
| `REQUIREMENTSET_TEST_ALL` | AND - All conditions must be true |
| `REQUIREMENTSET_TEST_ANY` | OR - Any condition can be true |

## Data Files Index

### Type Name Lookups
🔴 **SQLite 优先** — 查类型值直接用 DebugGameplay.sqlite：

```sql
SELECT UnitType FROM Units WHERE UnitType LIKE '%WARRIOR%';
SELECT CivilizationType FROM Civilizations;
SELECT BuildingType FROM Buildings;
SELECT DistrictType FROM Districts;
```

中英类型名对照用 DebugLocalization.sqlite：`SELECT Type, Text FROM LocalizedText WHERE Language='zh_Hans_CN' AND Tag IN (SELECT Name FROM Units)`。

### Core Data
所有结构化数据（ModifierTypes, Effects, Requirements, Collections）通过 DebugGameplay.sqlite 直接查询。

### SQLite Databases
| File | Contents |
|------|----------|
| **`database/DebugGameplay.sqlite`** | Modifiers, Requirements, Traits — 直接 SQL 查询 |
| **`database/DebugLocalization.sqlite`** | 中英文名称查询 |

## References

- **Type Names & Relationship Chain**: `reference/TYPE_NAME_MAPPING.md` - Type → Name lookup + Trait→Modifier→LocalizedText 关联链 SQL
- **Workshop Patterns**: `reference/WORKSHOP_PATTERNS.md` - Bulk SQL, attachments, property states, timing flags
- **Modifier Args**: `reference/MODIFIER_ARGUMENTS.md` - Parameter data types
- **Requirement SQL**: `database/scripts/requirement_reference.sql` - RequirementType 分类整理（实测 `Requirements` 表去重 **327** 个类型 / 1051 行）
- **Query Templates**: `database/scripts/sql_query_templates.sql` - SQL patterns
