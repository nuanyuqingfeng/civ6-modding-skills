-- 文明6 Mod开发 - SQL查询模板

-- ============================================
-- SQL 创建模板（可直接复制修改）
-- ============================================

-- --------------------------------------------
-- 模板1：城市有指定区域时 +X 产出
-- 例如：有学院的城市 +30 生产力
-- --------------------------------------------
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_CITY_HAS_CAMPUS', 'REQUIREMENT_CITY_HAS_DISTRICT');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_CITY_HAS_CAMPUS', 'DistrictType', 'DISTRICT_CAMPUS');
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_CITY_HAS_CAMPUS', 'REQUIREMENTSET_TEST_ALL');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_CITY_HAS_CAMPUS', 'REQ_CITY_HAS_CAMPUS');

INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_CAMPUS_PRODUCTION_30', 'MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE', 'REQSET_CITY_HAS_CAMPUS');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_CAMPUS_PRODUCTION_30', 'YieldType', 'YIELD_PRODUCTION'),
    ('MODIFIER_CAMPUS_PRODUCTION_30', 'Amount', '30');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_CAMPUS_PRODUCTION_30');

-- --------------------------------------------
-- 模板2：指定兵种标签 +X 战斗力
-- 例如：所有近战单位 +2 战斗力
-- --------------------------------------------
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_UNIT_IS_MELEE', 'REQUIREMENT_UNIT_TAG_MATCHES');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_UNIT_IS_MELEE', 'Tag', 'CLASS_MELEE');
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_UNIT_IS_MELEE', 'REQUIREMENTSET_TEST_ALL');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_UNIT_IS_MELEE', 'REQ_UNIT_IS_MELEE');

INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_MELEE_COMBAT_2', 'MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH', 'REQSET_UNIT_IS_MELEE');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_MELEE_COMBAT_2', 'Amount', '2');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_MELEE_COMBAT_2');

-- --------------------------------------------
-- 模板3：指定区域建造加速
-- 例如：剧院区建造速度 +40%
-- --------------------------------------------
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_THEATER_PRODUCTION_40', 'MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_THEATER_PRODUCTION_40', 'DistrictType', 'DISTRICT_THEATER'),
    ('MODIFIER_THEATER_PRODUCTION_40', 'Amount', '40');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_THEATER_PRODUCTION_40');

-- --------------------------------------------
-- 模板4：指定建筑 +X 产出
-- 例如：纪念碑 +10 科技
-- --------------------------------------------
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_MONUMENT_SCIENCE_10', 'MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_MONUMENT_SCIENCE_10', 'BuildingType', 'BUILDING_MONUMENT'),
    ('MODIFIER_MONUMENT_SCIENCE_10', 'YieldType', 'YIELD_SCIENCE'),
    ('MODIFIER_MONUMENT_SCIENCE_10', 'Amount', '10');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_MONUMENT_SCIENCE_10');

-- --------------------------------------------
-- 模板5：嵌套 Modifier（给目标附加子Modifier）
-- 例如：所有城市获得一个子Modifier
-- --------------------------------------------
-- 子Modifier（实际效果）
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_SUB_CITY_GROWTH', 'MODIFIER_SINGLE_CITY_ADJUST_CITY_GROWTH', 'REQSET_CITY_IS_CAPITAL');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_SUB_CITY_GROWTH', 'Amount', '10');

-- 外壳Modifier（将子Modifier附加到所有城市）
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_ATTACH_CITY_GROWTH', 'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_ATTACH_CITY_GROWTH', 'ModifierId', 'MODIFIER_SUB_CITY_GROWTH');

INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_ATTACH_CITY_GROWTH');

-- --------------------------------------------
-- 模板6：全局地块产出修改（不绑定任何文明）
-- 例如：泛滥平原 +1 食物
-- --------------------------------------------
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_PLOT_FLOODPLAINS', 'REQUIREMENT_PLOT_FEATURE_TYPE_MATCHES');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_PLOT_FLOODPLAINS', 'FeatureType', 'FEATURE_FLOODPLAINS');
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_PLOT_FLOODPLAINS', 'REQUIREMENTSET_TEST_ANY');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_PLOT_FLOODPLAINS', 'REQ_PLOT_FLOODPLAINS');
-- 如有多种特征可继续添加

INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_FLOODPLAINS_FOOD', 'MODIFIER_GAME_ADJUST_PLOT_YIELD', 'REQSET_PLOT_FLOODPLAINS');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_FLOODPLAINS_FOOD', 'YieldType', 'YIELD_FOOD'),
    ('MODIFIER_FLOODPLAINS_FOOD', 'Amount', '1');

INSERT INTO GameModifiers (ModifierId)
VALUES ('MODIFIER_FLOODPLAINS_FOOD');

-- --------------------------------------------
-- 模板7：Owner条件限制（科技/市政解锁后生效）
-- 例如：玩家解锁人文主义后，矿山+1文化
-- --------------------------------------------
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_HAS_HUMANISM', 'REQUIREMENT_PLAYER_HAS_CIVIC');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_HAS_HUMANISM', 'CivicType', 'CIVIC_HUMANISM');
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_HAS_HUMANISM', 'REQUIREMENTSET_TEST_ALL');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_HAS_HUMANISM', 'REQ_HAS_HUMANISM');

UPDATE Modifiers SET OwnerRequirementSetId = 'REQSET_HAS_HUMANISM'
WHERE ModifierId = 'YOUR_MODIFIER_ID';

-- --------------------------------------------
-- 模板8：Attach Modifier（给所有指定单位附加带条件的子Modifier）
-- 例如：第10回合前，勇士+5移动力且无视地形和河流
-- --------------------------------------------
-- 条件1：第10回合前生效（Inverse=1 表示取反，即 turn < 10）
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType, Inverse)
VALUES ('REQ_TURN_AT_LEAST_10', 'REQUIREMENT_GAME_TURN_ATLEAST', 1);
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_TURN_AT_LEAST_10', 'MinGameTurn', '10');

-- 条件2：单位类型为勇士
INSERT OR IGNORE INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_UNIT_IS_WARRIOR', 'REQUIREMENT_UNIT_TYPE_MATCHES');
INSERT OR IGNORE INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_UNIT_IS_WARRIOR', 'UnitType', 'UNIT_WARRIOR');

-- 组合条件
INSERT OR IGNORE INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_WARRIOR_BEFORE_TURN_10', 'REQUIREMENTSET_TEST_ALL');
INSERT OR IGNORE INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES 
    ('REQSET_WARRIOR_BEFORE_TURN_10', 'REQ_TURN_AT_LEAST_10'),
    ('REQSET_WARRIOR_BEFORE_TURN_10', 'REQ_UNIT_IS_WARRIOR');

-- 子Modifier1：+5移动力（作用于单个单位）
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_WARRIOR_MOVEMENT_5', 'MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT', 'REQSET_WARRIOR_BEFORE_TURN_10');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_WARRIOR_MOVEMENT_5', 'Amount', '5');

-- 子Modifier2：无视地形和河流（作用于单个单位）
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_WARRIOR_IGNORE_TERRAIN', 'MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_TERRAIN_COST', 'REQSET_WARRIOR_BEFORE_TURN_10');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_WARRIOR_IGNORE_TERRAIN', 'Ignore', '1'),
    ('MODIFIER_WARRIOR_IGNORE_TERRAIN', 'Type', 'ALL');

-- Attach Modifier1：将移动力子Modifier附加到所有单位
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_ATTACH_WARRIOR_MOVEMENT', 'MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_ATTACH_WARRIOR_MOVEMENT', 'ModifierId', 'MODIFIER_WARRIOR_MOVEMENT_5');

-- Attach Modifier2：将无视地形子Modifier附加到所有单位
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_ATTACH_WARRIOR_TERRAIN', 'MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_ATTACH_WARRIOR_TERRAIN', 'ModifierId', 'MODIFIER_WARRIOR_IGNORE_TERRAIN');

-- 绑定到所有主要文明
INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES 
    ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_ATTACH_WARRIOR_MOVEMENT'),
    ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_ATTACH_WARRIOR_TERRAIN');

-- ============================================
-- 原有查询模板
-- ============================================

-- 1. 查询Trait的所有信息
SELECT t.TraitType, t.Name, lt.Text as Name_CN
FROM Traits t
LEFT JOIN LocalizedText lt ON t.Name = lt.Tag AND lt.Language = 'zh_Hans_CN'
WHERE t.TraitType = 'TRAIT_YOUR_TRAIT';

-- 2. 查询Trait关联的所有Modifier
SELECT t.TraitType, tm.ModifierId, m.ModifierType
FROM Traits t
JOIN TraitModifiers tm ON t.TraitType = tm.TraitType
JOIN Modifiers m ON tm.ModifierId = m.ModifierId
WHERE t.TraitType = 'TRAIT_YOUR_TRAIT';

-- 3. 查询Modifier的完整参数
SELECT m.ModifierId, m.ModifierType, ma.Name, ma.Value
FROM Modifiers m
LEFT JOIN ModifierArguments ma ON m.ModifierId = ma.ModifierId
WHERE m.ModifierId = 'YOUR_MODIFIER';

-- 4. 查询所有ModifierType
SELECT DISTINCT ModifierType FROM Modifiers ORDER BY ModifierType;

-- 5. 查询RequirementSet中的所有条件
SELECT rs.RequirementSetId, r.RequirementId, r.RequirementType, r.Inverse
FROM RequirementSets rs
JOIN RequirementSetRequirements rsr ON rs.RequirementSetId = rsr.RequirementSetId
JOIN Requirements r ON rsr.RequirementId = r.RequirementId
WHERE rs.RequirementSetId = 'YOUR_REQUIREMENT_SET';

-- 6. 查找Trait的描述文本
SELECT ma.ModifierId, ma.Value as DescriptionTag, lt.Text as Description_CN
FROM ModifierArguments ma
JOIN LocalizedText lt ON ma.Value = lt.Tag
WHERE ma.ModifierId = 'YOUR_MODIFIER'
AND ma.Name = 'SimpleModifierDescription'
AND lt.Language = 'zh_Hans_CN';

-- 7. 查询最常用的ModifierType
SELECT ModifierType, COUNT(*) as UsageCount
FROM Modifiers
GROUP BY ModifierType
ORDER BY UsageCount DESC
LIMIT 50;

-- 8. 查询带条件的Modifier
SELECT ModifierId, ModifierType, OwnerRequirementSetId, SubjectRequirementSetId
FROM Modifiers
WHERE OwnerRequirementSetId IS NOT NULL OR SubjectRequirementSetId IS NOT NULL;

-- ============================================
-- 查询 Modifier 绑定表（22种目标）
-- ============================================

-- 查询建筑绑定的Modifier
SELECT bm.BuildingType, bm.ModifierId, m.ModifierType
FROM BuildingModifiers bm
JOIN Modifiers m ON bm.ModifierId = m.ModifierId
WHERE bm.BuildingType = 'BUILDING_MONUMENT';

-- 查询政策卡绑定的Modifier
SELECT pm.PolicyType, pm.ModifierId, m.ModifierType
FROM PolicyModifiers pm
JOIN Modifiers m ON pm.ModifierId = m.ModifierId
WHERE pm.PolicyType = 'POLICY_YOUR_POLICY';

-- 查询科技绑定的Modifier
SELECT tm.TechnologyType, tm.ModifierId, m.ModifierType
FROM TechnologyModifiers tm
JOIN Modifiers m ON tm.ModifierId = m.ModifierId
WHERE tm.TechnologyType = 'TECH_YOUR_TECH';

-- 查询市政绑定的Modifier
SELECT cm.CivicType, cm.ModifierId, m.ModifierType
FROM CivicModifiers cm
JOIN Modifiers m ON cm.ModifierId = m.ModifierId
WHERE cm.CivicType = 'CIVIC_YOUR_CIVIC';

-- 查询信仰绑定的Modifier
SELECT bm.BeliefType, bm.ModifierId, m.ModifierType
FROM BeliefModifiers bm
JOIN Modifiers m ON bm.ModifierId = m.ModifierId
WHERE bm.BeliefType = 'BELIEF_YOUR_BELIEF';

-- 查询总督晋升绑定的Modifier
SELECT gpm.GovernorPromotionType, gpm.ModifierId, m.ModifierType
FROM GovernorPromotionModifiers gpm
JOIN Modifiers m ON gpm.ModifierId = m.ModifierId;

-- 查询单位晋升绑定的Modifier
SELECT upm.UnitPromotionType, upm.ModifierId, m.ModifierType
FROM UnitPromotionModifiers upm
JOIN Modifiers m ON upm.ModifierId = m.ModifierId;

-- 查询单位能力绑定的Modifier
SELECT uam.UnitAbilityType, uam.ModifierId, m.ModifierType
FROM UnitAbilityModifiers uam
JOIN Modifiers m ON uam.ModifierId = m.ModifierId;

-- 查询改良设施绑定的Modifier
SELECT im.ImprovementType, im.ModifierId, m.ModifierType
FROM ImprovementModifiers im
JOIN Modifiers m ON im.ModifierId = m.ModifierId;

-- 查询区域绑定的Modifier
SELECT dm.DistrictType, dm.ModifierId, m.ModifierType
FROM DistrictModifiers dm
JOIN Modifiers m ON dm.ModifierId = m.ModifierId;

-- 查询政体绑定的Modifier
SELECT gm.GovernmentType, gm.ModifierId, m.ModifierType
FROM GovernmentModifiers gm
JOIN Modifiers m ON gm.ModifierId = m.ModifierId;

-- 查询项目完成绑定的Modifier
SELECT pcm.ProjectType, pcm.ModifierId, m.ModifierType
FROM ProjectCompletionModifiers pcm
JOIN Modifiers m ON pcm.ModifierId = m.ModifierId;

-- ============================================
-- Requirement（条件系统）查询
-- ============================================

-- 查询RequirementSet中的所有条件（带参数）
SELECT 
    rs.RequirementSetId,
    rs.RequirementSetType,
    r.RequirementId,
    r.RequirementType,
    r.Inverse,
    ra.Name as ArgName,
    ra.Value as ArgValue
FROM RequirementSets rs
JOIN RequirementSetRequirements rsr ON rs.RequirementSetId = rsr.RequirementSetId
JOIN Requirements r ON rsr.RequirementId = r.RequirementId
LEFT JOIN RequirementArguments ra ON r.RequirementId = ra.RequirementId
WHERE rs.RequirementSetId = 'YOUR_REQSET';

-- 查询使用特定RequirementType的所有条件
SELECT RequirementId, RequirementType, Inverse
FROM Requirements
WHERE RequirementType = 'REQUIREMENT_CITY_HAS_BUILDING';

-- 查询带特定条件的Modifier
SELECT m.ModifierId, m.ModifierType, m.SubjectRequirementSetId
FROM Modifiers m
JOIN RequirementSets rs ON m.SubjectRequirementSetId = rs.RequirementSetId
JOIN RequirementSetRequirements rsr ON rs.RequirementSetId = rsr.RequirementSetId
JOIN Requirements r ON rsr.RequirementId = r.RequirementId
WHERE r.RequirementType = 'REQUIREMENT_PLOT_IS_CAPITAL';

-- 查询Modifier的完整条件链
SELECT 
    m.ModifierId,
    m.ModifierType,
    rs.RequirementSetId,
    rs.RequirementSetType,
    r.RequirementId,
    r.RequirementType,
    r.Inverse,
    ra.Name,
    ra.Value
FROM Modifiers m
LEFT JOIN RequirementSets rs ON m.SubjectRequirementSetId = rs.RequirementSetId
LEFT JOIN RequirementSetRequirements rsr ON rs.RequirementSetId = rsr.RequirementSetId
LEFT JOIN Requirements r ON rsr.RequirementId = r.RequirementId
LEFT JOIN RequirementArguments ra ON r.RequirementId = ra.RequirementId
WHERE m.ModifierId = 'YOUR_MODIFIER';
