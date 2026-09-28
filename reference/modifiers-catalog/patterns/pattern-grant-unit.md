# 送单位（建城/首都/区域/补员）— 模式 G

> **适用场景**：送单位 / 获得单位 / 建城送 / 首都送 / 首城送 / 区域建成送 / 保持单位数量补员 / GRANT_UNIT
> 参考实证：0039（迈克尔·首都送一次）、0046（拉比丽斯·建城送至多3）、0053（天师·补员至多3）、0043（隧者·建城送+区域建成送）
> 写码前必读本文件的**通用铁律**（三个坑都是 0039 实测翻车换来的）。

## 方式总览（先选型）

| 场景 | 方式 | ModifierType | 参考 Mod |
|------|------|--------------|---------|
| 首都/首城送（只一次） | ② | `MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL` | 0039 |
| 后续建城送（可限上限） | ① | `MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_UNIT` | 0043, 0046 |
| 区域/建筑建成送 | ③ | DistrictModifiers + `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY` | 0043 |
| 保持数量补员（上限） | ④ | ATTACH 中转 + `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY` | 0053 |
| 项目补员（主动型，数量<上限解锁） | ⑤ | `MODIFIER_PLAYER_ALLOW_PROJECT_CHINA`(OwnerReq 数量<上限) + ProjectCompletionModifiers + `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY` | 0039/0045/0046 |

---

## 方式① 建城送 — MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_UNIT

**触发**：玩家**建立新城**事件时，单位生成在该新城。**⚠️ 首都（开局城市）不触发**（开局首都没有"建立"事件）。

```sql
-- 挂载（文明/单位特质皆可，0043/0046 均挂 TRAIT_UNIT_）
INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_UNIT_SIQI_U00XX_1', 'MODIFIER_SIQI_00XX_GRANT_UNIT');

-- 每建一城送 1 个（无条件）——0043 隧者
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_00XX_GRANT_UNIT', 'MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_UNIT', NULL, 0, 0);
-- 参数：UnitType, Amount=1, AllowUniqueOverride=1

-- 至多 N 个：加条件"城市<N"（0046 拉比丽斯，N=3）
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_00XX_GRANT_UNIT', 'MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_UNIT',
 'REQSET_SIQI_00XX_HAS_NOT_CITIES_N', 0, 0);
-- 条件：REQUIREMENT_PLAYER_HAS_AT_LEAST_NUMBER_CITIES Inverse=1, Amount=N
```

**要点**：RunOnce=0 + Permanent=0；上限用"城市<N"取反；**不能用于首都/首城送**。

## 方式② 首都/首城送（只一次）— MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL

**触发**：条件满足时在**首都**生成。0039 迈克尔最终版：

```sql
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0039_GRANT_MICHAEL_IN_CAPITAL', 'MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL',
 'REQSET_SIQI_0039_ONLY_1_CITY', NULL, 0, 0);   -- ← RunOnce=0 + Permanent=0
-- 参数：UnitType, Amount=1, AllowUniqueOverride=1

-- 条件"城市≤1"（官方 REQUIRES_PLAYER_HAS_ONLY_ONE_CITY 同款）：
INSERT INTO Requirements (RequirementId, RequirementType, Inverse) VALUES
('REQ_SIQI_0039_ONLY_1_CITY', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUMBER_CITIES', 1); -- ≥2取反=≤1
INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_0039_ONLY_1_CITY', 'Amount', 2);
```

**⚠️ 绝不能用 RunOnce=1**：开局（0 城）条件"≤1"就满足 → trait 附加时立即触发 → **无城市 → 生成失败且 RunOnce 锁定** → 永久无效（0039 两次翻车的根因）。
RunOnce=0 + Permanent=0（条件驱动）：开局失败无妨，**建首城（0→1）重新评估 → 触发成功**；建第 2 城后条件翻转 false → 不再触发。"只一次"靠**条件翻转**，不靠 RunOnce。

## 方式③ 区域/建筑建成送 — DistrictModifiers + MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY

**触发**：modifier 附加到**城市**时生成（挂 DistrictModifiers → 每个区域实例独立触发）。0043 星炬学院建成送隧者：

```sql
INSERT INTO DistrictModifiers (DistrictType, ModifierId) VALUES
('DISTRICT_SIQI_D0043_1', 'MODIFIER_SIQI_0043_DISTRICT_GRANT_U0043');

INSERT INTO Modifiers(ModifierId, ModifierType, RunOnce, Permanent, SubjectStackLimit) VALUES
('MODIFIER_SIQI_0043_DISTRICT_GRANT_U0043', 'MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY', 1, 1, 1);
-- 参数：UnitType, Amount=1, AllowUniqueOverride=1
```

**要点**：城市级 modifier **被附加时城市已存在 → RunOnce=1 安全**（附加即触发一次）；SubjectStackLimit=1 限每城 1 个。

## 方式④ 持续补员（数量上限）— ATTACH 中转 + 城市级 GRANT

**触发**：外层条件驱动附加，内层附加到城市时生成。0053 天师（<3 自动补）：

```sql
-- 外层（玩家级，Permanent=0，条件=数量<N + 城市条件）
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0053_ATTACH_TIANSHI', 'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER',
 'REQSET_SIQI_0053_FEWER_THAN_3_TIANSHI', 'REQSET_SIQI_0053_CITY_HAS_TIANSHIFU', 0, 0);
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0053_ATTACH_TIANSHI', 'ModifierId', 'MODIFIER_SIQI_0053_TIANSHIFU_GRANT_TIANSHI');

-- 内层（城市级，附加时触发）
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId, SubjectRequirementSetId, RunOnce, Permanent, SubjectStackLimit) VALUES
('MODIFIER_SIQI_0053_TIANSHIFU_GRANT_TIANSHI', 'MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY', NULL, NULL, 1, 1, 1);
-- 参数：UnitType, Amount=1
-- 数量条件：REQUIREMENT_COLLECTION_COUNT_ATLEAST(Count=N) + COLLECTION_PLAYER_UNITS + 单位类型 REQSET
```

**⚠️ 数量条件若为"<1"且单位可被玩家主动删除 → 删除→重生→无限攻击漏洞**（0039 教训：删除单位→数量=0→重新附加→再生成→再攻击）。
循环补只适合**单位难以被主动清除**的场景（如 0053 天师有 Lua 不死保护）。

---

## 方式⑤ 项目补员（主动型）— ALLOW_PROJECT + ProjectCompletionModifiers + 城市级 GRANT

**触发**：项目平时隐藏（`UnlocksFromEffect=1`）；玩家单位数量**少于上限**时，ALLOW modifier 的条件满足 → 项目出现在生产列表；完成后（可重复建造）在**完成城市**赠予 1 个该单位。0039/0045/0046 已实装（"迈克尔归来"/"魔王的再临"/"迷宫主的再临"）。

**与方式④的本质区别**：④是自动补（无成本、无决策，且触发即执行，有删除漏洞）；⑤是**玩家主动**补——付锤子、可控节奏，删除→再造也要付生产，无免费循环。

```sql
-- 项目（Projects + Projects_XP2，MaxSimultaneousInstances=1 限同时1个）
INSERT INTO Projects_XP2 (ProjectType, UnlocksFromEffect, MaxSimultaneousInstances) VALUES
('PROJECT_SIQI_00XX_1', 1, 1);

-- 解锁：自定义 ALLOW_PROJECT 型（官方 MODIFIER_PLAYER_ALLOW_PROJECT_CHINA 是 DLC 定义，不得引用！
--        自建等效：Types(KIND_MODIFIER) + DynamicModifiers(EFFECT_ADD_PLAYER_PROJECT_AVAILABILITY, COLLECTION_OWNER)）
INSERT INTO Types (Type, Kind) VALUES ('MODIFIER_SIQI_00XX_ALLOW_PROJECT', 'KIND_MODIFIER');
INSERT INTO DynamicModifiers (ModifierType, EffectType, CollectionType) VALUES
('MODIFIER_SIQI_00XX_ALLOW_PROJECT', 'EFFECT_ADD_PLAYER_PROJECT_AVAILABILITY', 'COLLECTION_OWNER');

INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('<TRAIT_>', 'MODIFIER_SIQI_00XX_REPLENISH_ALLOW');   -- 与"原始赠送"同 trait
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_00XX_REPLENISH_ALLOW', 'MODIFIER_SIQI_00XX_ALLOW_PROJECT',
 'REQSET_SIQI_00XX_FEWER_THAN_N', 0, 0);
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_00XX_REPLENISH_ALLOW', 'ProjectType', 'PROJECT_SIQI_00XX_1');

-- 完成赠送：ProjectCompletionModifiers（绑定完成城市，vanilla PCM 城市级已验证）
INSERT INTO ProjectCompletionModifiers (ProjectType, ModifierId) VALUES
('PROJECT_SIQI_00XX_1', 'MODIFIER_SIQI_00XX_REPLENISH_GRANT');
INSERT INTO Modifiers(ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_00XX_REPLENISH_GRANT', 'MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY', 0, 0);
-- 参数：UnitType / Amount=1 / AllowUniqueOverride=1

-- 数量条件（COLLECTION_COUNT_ATLEAST 取反 + 单位类型 REQSET 过滤，0053 同款）：
-- 'REQ_SIQI_00XX_FEWER_THAN_N': REQUIREMENT_COLLECTION_COUNT_ATLEAST, Inverse=1
--   参数：CollectionType=COLLECTION_PLAYER_UNITS, Count=上限(N), RequirementSetId=单位类型REQSET
```

**要点**：
- **上限取"数量<上限"**（`≥上限取反`），不是"≤上限"——满员时项目不可见，避免补出第 N+1 个。
- **grant 必须 RunOnce=0 + Permanent=0**（项目可重复建造，每次完成都触发；方式③的 RunOnce=1 只适用于"每城一次"的附加型触发）。
- `UnlocksFromEffect=1` 必须设置（跟 0046 高度训练/连栗炮同款，保证项目默认隐藏）。
- 事件类 req 勿加 Triggered（数量条件是状态检查，非事件）。
- 已知软边界：双城同回合完成（数量 N-1 时各排一个）可能补到 N+1；如需硬上限可在 grant 上也挂数量 req（未验证，需实测）。

---

## 通用铁律（0039 实测换来的三个坑）

1. **RunOnce=1 = 附加时条件满足即执行一次并锁定**（trait 附加 = 游戏初始化）——**附加时目标不存在（无城市）→ 失败且锁定 → 永久无效**。判断标准：条件在开局是否满足 + 执行目标开局是否存在。
2. **数量类 req（REQUIREMENT_PLAYER_HAS_AT_LEAST_NUMBER_CITIES / COLLECTION_COUNT_ATLEAST）在数据变化时重新评估，满足即触发**——"≥1"长期满足 → **每次建城都触发**（每城送 1 个）；要"只触发一次"必须用**会翻转的条件**（如"≤1 城"）。
3. **选型速查**：首都/首城送 → 方式②；后续建城送（含上限）→ 方式①；区域建成送 → 方式③；维持数量补员 → 方式④。
