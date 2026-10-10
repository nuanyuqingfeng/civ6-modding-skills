# 文明6 Mod开发 - Type名称对照表

> 📖 这是详细参考文档。快速查阅请查看 [SKILL.md](../SKILL.md)

---

## 概述

本文档提供文明6中各类游戏元素的Type到中文/英文名称的对照，便于编写Mod时查找正确的Type值。

## 数据来源

所有数据从 `DebugGameplay.sqlite` 和 `DebugLocalization.sqlite` 提取：
- **Gameplay数据库**: 包含所有Type定义
- **Localization数据库**: 包含多语言名称（含简体中文）

## 对照表索引

查类型直接用 DebugGameplay.sqlite + DebugLocalization.sqlite：

```sql
-- 查所有单位 Type
SELECT UnitType FROM Units;

-- 查单位中英文名
SELECT t.UnitType, l.Text AS Name_CN
FROM Units t JOIN LocalizedText l ON t.Name = l.Tag
WHERE l.Language = 'zh_Hans_CN' AND t.UnitType LIKE '%WARRIOR%';
```

## 快速查找索引

DebugLocalization.sqlite 的 `LocalizedText` 表中 `Language='zh_Hans_CN'` 即为中文名：

## 常用Type示例

### 单位 (Units)
| Type | 中文名 | 英文名 |
|------|--------|--------|
| UNIT_WARRIOR | 战士 | Warrior |
| UNIT_ARCHER | 弓箭手 | Archer |
| UNIT_SETTLER | 开拓者 | Settler |
| UNIT_BUILDER | 建造者 | Builder |
| UNIT_TRADER | 商人 | Trader |

### 文明 (Civilizations)
| Type | 中文名 | 英文名 |
|------|--------|--------|
| CIVILIZATION_CHINA | 中国 | China |
| CIVILIZATION_AMERICA | 美国 | America |
| CIVILIZATION_ROME | 罗马 | Rome |
| CIVILIZATION_GERMANY | 德国 | Germany |
| CIVILIZATION_JAPAN | 日本 | Japan |

### 建筑 (Buildings)
| Type | 中文名 | 英文名 |
|------|--------|--------|
| BUILDING_MONUMENT | 纪念碑 | Monument |
| BUILDING_GRANARY | 粮仓 | Granary |
| BUILDING_LIBRARY | 图书馆 | Library |
| BUILDING_CAMPUS | 学院 | Campus |
| BUILDING_COMMERCIAL_HUB | 商业中心 | Commercial Hub |

### 区域 (Districts)
| Type | 中文名 | 英文名 |
|------|--------|--------|
| DISTRICT_CITY_CENTER | 市中心 | City Center |
| DISTRICT_CAMPUS | 学院 | Campus |
| DISTRICT_HOLY_SITE | 圣地 | Holy Site |
| DISTRICT_COMMERCIAL_HUB | 商业中心 | Commercial Hub |
| DISTRICT_INDUSTRIAL_ZONE | 工业区 | Industrial Zone |

### 产出类型 (Yields)
在Modifier参数中使用：
| Type | 中文名 |
|------|--------|
| YIELD_FOOD | 食物 |
| YIELD_PRODUCTION | 生产力 |
| YIELD_GOLD | 金币 |
| YIELD_SCIENCE | 科技值 |
| YIELD_CULTURE | 文化值 |
| YIELD_FAITH | 信仰值 |

## 在Mod中使用

### 示例1: 指定特定文明的Modifier
```sql
-- 创建仅对中国生效的Modifier
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQUIRES_CHINA', 'REQUIREMENTSET_TEST_ALL');

INSERT INTO Requirements (RequirementId, RequirementType)
VALUES ('REQUIRES_CIV_CHINA', 'REQUIREMENT_PLAYER_HAS_CIVILIZATION');

INSERT INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQUIRES_CIV_CHINA', 'CivilizationType', 'CIVILIZATION_CHINA');

INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQUIRES_CHINA', 'REQUIRES_CIV_CHINA');
```

### 示例2: 使用单位类型作为参数
```sql
-- 添加对特定单位的加成
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_MODIFIER', 'UnitType', 'ARGTYPE_IDENTITY', 'UNIT_WARRIOR');
```

### 示例3: 指定产出类型
```sql
-- 添加科技值产出
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('SCIENCE_BONUS', 'YieldType', 'ARGTYPE_IDENTITY', 'YIELD_SCIENCE');

INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('SCIENCE_BONUS', 'Amount', 'ARGTYPE_INTEGER', '5');
```

## 查询方法

### 从 SQLite 直接查询（首选）
```sql
-- 查询所有单位名
SELECT UnitType FROM Units;

-- 查询中文化名
SELECT UnitType, l.Text FROM Units t JOIN LocalizedText l ON t.Name = l.Tag
WHERE l.Language = 'zh_Hans_CN';

-- 查找特定 Type 是否存在
SELECT Type FROM Types WHERE Type = 'UNIT_WARRIOR';
```

## Trait → LocalizedText 关联链

### 完整关联路径

```
Traits.TraitType
    └── Traits.Name → LocalizedText.Tag = LOC_[TraitType]_NAME
    └── Traits.Description → LocalizedText.Tag = LOC_[TraitType]_DESCRIPTION
    └── TraitModifiers.ModifierId
            └── Modifiers.ModifierType
                    └── ModifierArguments.SimpleModifierDescription
                            └── LocalizedText.Tag
```

### 查询示例

```sql
-- 查找 Trait 关联的所有 Modifier
SELECT t.TraitType, tm.ModifierId, m.ModifierType
FROM Traits t
JOIN TraitModifiers tm ON t.TraitType = tm.TraitType
JOIN Modifiers m ON tm.ModifierId = m.ModifierId
WHERE t.TraitType = 'TRAIT_AGENDA_ALLY_OF_ENKIDU';
```

---

*文档版本: v1.1*  
*数据来源: DebugGameplay.sqlite + DebugLocalization.sqlite*
