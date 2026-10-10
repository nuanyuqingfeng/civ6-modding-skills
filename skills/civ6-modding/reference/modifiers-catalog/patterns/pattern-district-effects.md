# 模式 E：区域效果（槽位/生产/替换）

> 适用：区域建筑生产力、政策槽位增减、槽位替换、区域挂载 Modifier。
> 参考 Mod：`Siqi_Leaders_0045`（Data/Siqi_Leaders_0045_Districts.sql + Modifiers.sql）。

---

## 链路 1：取代官方区域（DistrictReplaces）

取代 `DISTRICT_GOVERNMENT` 的自定义区域：

```sql
-- ① 注册 Type + 独立特质（区域必须有自己的 TRAIT_DISTRICT_xxx，不能复用文明特质）
INSERT INTO Types (Type, Kind) VALUES
('DISTRICT_SIQI_D0045_1', 'KIND_DISTRICT'),
('TRAIT_DISTRICT_SIQI_D0045_1', 'KIND_TRAIT');

-- ② 特质
INSERT INTO Traits (TraitType, Name, Description) VALUES
('TRAIT_DISTRICT_SIQI_D0045_1', 'LOC_..._NAME', 'LOC_..._DESCRIPTION');

-- ③ 取代关系
INSERT INTO DistrictReplaces (CivUniqueDistrictType, ReplacesDistrictType) VALUES
('DISTRICT_SIQI_D0045_1', 'DISTRICT_GOVERNMENT');

-- ④ 主表（关键列：CostProgressionModel/Param1、Maintenance、MaxPerPlayer、TraitType）
INSERT INTO Districts (DistrictType, Name, Description, Cost, AdvisorType, PlunderType,
    PlunderAmount, CostProgressionModel, CostProgressionParam1, MilitaryDomain,
    Maintenance, CityStrengthModifier, MaxPerPlayer, RequiresPlacement, NoAdjacentCity,
    Aqueduct, InternalOnly, CaptureRemovesBuildings, CaptureRemovesCityDefenses,
    CaptureRemovesDistrict, TraitType) VALUES (...);
```

> 陷阱：区域**必须独立 TraitType**（`TRAIT_DISTRICT_xxx`）并填 Districts.TraitType 列——不能共用文明特质。

## 链路 2：区域挂载 Modifier（DistrictModifiers）

```sql
-- ① 挂载
INSERT INTO DistrictModifiers (DistrictType, ModifierId) VALUES
('DISTRICT_SIQI_D0045_1', 'MODIFIER_SIQI_0045_ADJUST_GOVERNOR_POINTS_5');

-- ② Modifier（SubjectRequirementSetId 可空）
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_GOVERNOR_POINTS_5', 'MODIFIER_PLAYER_ADJUST_GOVERNOR_POINTS', NULL, 1, 1);

-- ③ 参数
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_GOVERNOR_POINTS_5', 'Delta', 5);
```

> 注意：DistrictModifiers 挂在**区域**上，效果作用对象是**区域所有者玩家**——ModifierType 用 `MODIFIER_PLAYER_*` 系列时对区域所有者生效。

## 链路 3：政策槽位增减（GovernmentSlots）

```sql
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_GOVERNMENT_SLOT_MILITARY',
 'MODIFIER_PLAYER_CULTURE_ADJUST_GOVERNMENT_SLOTS_MODIFIER', NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_GOVERNMENT_SLOT_MILITARY', 'GovernmentSlotType', 'SLOT_MILITARY');
```

## 链路 4：槽位替换（ReplaceGovernmentSlots）

经济槽 → 通配符槽：

```sql
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_REPLACE_GOVERNMENT_SLOT_ECONOMIC_WILDCARD',
 'MODIFIER_PLAYER_CULTURE_REPLACE_GOVERNMENT_SLOTS', NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_REPLACE_GOVERNMENT_SLOT_ECONOMIC_WILDCARD', 'AddedGovernmentSlotType', 'SLOT_WILDCARD'),
('MODIFIER_SIQI_0045_REPLACE_GOVERNMENT_SLOT_ECONOMIC_WILDCARD', 'ReplacedGovernmentSlotType', 'SLOT_ECONOMIC'),
('MODIFIER_SIQI_0045_REPLACE_GOVERNMENT_SLOT_ECONOMIC_WILDCARD', 'ReplacesAll', 1);
```

## 出口检查

- [ ] 区域有自己的 `TRAIT_DISTRICT_xxx` 并填入 Districts.TraitType
- [ ] 取代官方区域时 DistrictReplaces 两列齐全
- [ ] DistrictModifiers 挂载的 ModifierId 在 Modifiers 表有定义
- [ ] 槽位替换参数：Added/Replaced/ReplacesAll 三件套
