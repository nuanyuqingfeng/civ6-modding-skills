# modifier-policy-government -- 政策卡/政体/槽位类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

### EFFECT_ADJUST_GOVERNMENT_SLOTS

调整全体玩家的政策槽位数量（可增减任意数量，不像 `EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE` 只能 +1）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GOVERNMENT_ADJUST_SLOTS` | `COLLECTION_MAJOR_PLAYERS`（对全体主要玩家生效） |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `GovernmentSlotType` | **必填** | `SLOT_ECONOMIC` / `SLOT_MILITARY` / `SLOT_DIPLOMATIC` / `SLOT_WILDCARD`，来源 `GovernmentSlots.GovernmentSlotType` |
| `Amount` | **必填** | 增减数量。`1` = +1 槽位，`-1` = -1 槽位 |

> **溯源**：世界议会决议"世界意识形态"（`WC_RES_WORLD_IDEOLOGY`）——通过 `ResolutionEffects` 挂载两个 Modifier：`GOVT_ADD_WILDCARD_SLOT`（Amount=1, SLOT_WILDCARD）和 `GOVT_LOSE_WILDCARD_SLOT`（Amount=-1, SLOT_WILDCARD）。该决议仅 2 个实例，均增减通配符槽。

---

### EFFECT_ADJUST_PLAYER_BAN_POLICY

禁止指定玩家使用某张政策卡，将其从可选政策列表中移除。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_BANNED_POLICY` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `PolicyType` | **必填** | `POLICY_xxx`，来自 `Policies.PolicyType`。每个 Modifier 只能禁一张政策，禁止多张需挂多个 Modifier |

> **溯源**：DB 中共 24 个实例，全部来自 SIQI 模组（无原版使用案例）。通过 `TraitModifiers` 挂在文明特性上，配合 `SubjectRequirementSetId` 实现条件禁用（如"未拥有某建筑时禁止某政策"）。设置 `SubjectRequirementSetId` 可实现条件解禁——满足条件后才能使用该政策，不满足即禁止。引擎层面支持，但原版 `Effects.csv` 标记为 `UNTESTED`。

---

### EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE

为当前玩家新增一个指定类型的政策槽位（固定 +1，无 `Amount` 参数；若要增减任意数量用 `EFFECT_ADJUST_GOVERNMENT_SLOTS`）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CULTURE_ADJUST_GOVERNMENT_SLOTS_MODIFIER` | `COLLECTION_OWNER`（只对拥有者） |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `GovernmentSlotType` | **必填** | `SLOT_ECONOMIC`（经济）/ `SLOT_MILITARY`（军事）/ `SLOT_DIPLOMATIC`（外交）/ `SLOT_WILDCARD`（通配符），来源 `GovernmentSlots.GovernmentSlotType` |

> **溯源**（官方原版实例）：
> - **建筑**（通过 `BuildingModifiers`）：
>   - 阿尔罕布拉宫（`BUILDING_ALHAMBRA`）→ "+1 军事政策槽位"
>   - 布达拉宫（`BUILDING_POTALA_PALACE`）→ "+1外交政策槽位"
>   - 紫禁城（`BUILDING_FORBIDDEN_CITY`）→ "+1 通配符政策槽位"
>   - 大本钟（`BUILDING_BIG_BEN`）→ "+1 经济政策槽位"
> - **文明/领袖特性**（通过 `TraitModifiers`）：
>   - 希腊-柏拉图理想国（`TRAIT_CIVILIZATION_PLATOS_REPUBLIC`）→ "每种政体可获得一个额外的通配符槽位"——`TRAIT_WILDCARD_GOVERNMENT_SLOT`（SLOT_WILDCARD）
>   - 神圣罗马皇帝（`TRAIT_LEADER_HOLY_ROMAN_EMPEROR`）→ "额外的军事政策槽位"——`TRAIT_MILITARY_GOVERNMENT_SLOT`（SLOT_MILITARY）
>   - 忽必烈-腰牌（`TRAIT_LEADER_KUBLAI`）→ "任意政体中额外增加一个经济政策槽位"——`TRAIT_ECONOMIC_GOVERNMENT_SLOT`（SLOT_ECONOMIC）
> - **伟人一次性效果**（`GreatPersonIndividualActionModifiers`）：
>   - `GREATPERSON_ECONOMIC_POLICY_SLOT`（RunOnce=1, Permanent=1）——某伟人一次性永久增加经济槽

注：ModifierType 命名虽含 `CULTURE` 但实际效果与文化值无关，仅为 Firaxis 内部命名。

---

### EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR

每回合根据指定类型的政策槽位数量提供外交支持。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `Amount` | **必填** | 整数，每回合获得的额外外交支持数量 |
| `GovernmentSlotType` | **必填** | `SLOT_ECONOMIC` / `SLOT_MILITARY` / `SLOT_DIPLOMATIC` / `SLOT_WILDCARD`，来源 `GovernmentSlots.GovernmentSlotType` |

> **溯源**（仅 1 个原版实例）：
> - 美国文明特性"开国元勋"（`TRAIT_CIVILIZATION_FOUNDING_FATHERS`）→ 通过 `TraitModifiers` 挂载 `TRAIT_WILD_CARD_FAVOR`（Amount=1, GovernmentSlotType=SLOT_WILDCARD）：每个通配符槽位每回合额外 +1 外交支持。

注意：此 EffectType 的 ModifierType 名为 `MODIFIER_PLAYER_ADJUST_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR`，与 `EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE`（ModifierType = `MODIFIER_PLAYER_CULTURE_ADJUST_GOVERNMENT_SLOTS_MODIFIER`）**不是同一 ModifierType**。旧版文档误认为二者共享同一 ModifierType。

---

### EFFECT_ADJUST_PLAYER_OTHER_GOVERNMENT_INTOLERANCE

调整 AI 领袖对其他文明所采用的不同政体的容忍度，影响因"不同政体"而产生的外交好感度惩罚。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GOVERNMENT_ADJUST_OTHER_GOVERNMENT_INTOLERANCE` | `COLLECTION_OWNER` |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `IntoleranceMultiplier` | **必填** | 每级政体差异的好感度惩罚倍率（整数）。官方值 `2` = 惩罚翻倍 |
| `SameEraIntoleranceFlatBonus` | 可选 | 同一时代的固定好感修正（负值 = 减少不满）。官方值 `-6` |

> **溯源**（2 个实例，参数值完全相同）：
> - 议程"偏好相同政体"（`TRAIT_AGENDA_PREFER_SAME_GOVERNMENT`）→ 通过 `TraitModifiers` 挂载 `AGENDA_ADJUST_GOVERNMENT_INTOLERANCE`
> - 林肯议程（`TRAIT_AGENDA_LINCOLN`）→ 通过 `TraitModifiers` 挂载 `AGENDA_ADJUST_GOVERNMENT_INTOLERANCE_LINCOLN`
>
> 两组参数值均为 `IntoleranceMultiplier=2`, `SameEraIntoleranceFlatBonus=-6`，意味着对政体差异的容忍度降低（好感惩罚翻倍），但如果是同一时代的政体，则给予 6 点好感减免。

---

### EFFECT_ADJUST_POLICY_AMENITY

根据政策或政体条件，调整城市的宜居度（正值为增加宜居度，负值为减少）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_POLICY_AMENITY` | `COLLECTION_PLAYER_CITIES`（对玩家所有城市生效，通常配合 `SubjectRequirementSetId` 筛选） |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `Amount` | **必填** | 宜居度增减值（整数）。常见范围 `-2` ~ `+2` |

> **溯源**（原版政策卡实例，通过 `PolicyModifiers`）：
> | 政策 | LOC 描述 | ModifierId | Amount | 条件 |
> |---|---|---|---|---|
> | 自由主义（`POLICY_LIBERALISM`） | 至少两个独立区域的城市 +1 宜居度 | `LIBERALISM_SPECIALTYAMENITY` | `1` | `CITY_HAS_2_SPECIALTY_DISTRICTS_REQUIREMENTS` |
> | 新政（`POLICY_NEW_DEAL`） | 3 个特色区城市 +2 宜居度 | `NEWDEAL_SPECIALTYAMENITY` | `2` | `CITY_HAS_3_SPECIALTY_DISTRICTS_REQUIREMENTS` |
> | 侍从（`POLICY_RETAINERS`） | 拥有驻军单位的城市 +1 宜居度 | `RETAINERS_AMENITYBONUS` | `1` | `CITY_HAS_GARRISON_UNIT_REQUIERMENT` |
> | 体育传媒（`POLICY_SPORTS_MEDIA`） | 体育场 +1 宜居度 | `SPORTSMEDIA_STADIUMENTERTAINMENT` | `1` | `CITY_HAS_STADIUM_REQUIREMENTS` |
> | 民间威望（`POLICY_CIVIL_PRESTIGE`） | 含 2 项升级总督的城市 +1 宜居度 | `CIVILPRESTIGE_GOVAMENITY` | `1` | `CITY_HAS_2_TITLE_GOVERNOR_REQUIREMENTS` |
> | 敛财大亨（`POLICY_ROBBER_BARONS`） | 所有城市 -2 宜居度 | `ROBBERBARONS_AMENITIES_LOST` | `-2` | 无（全城生效） |
> | 音乐审查制度（`POLICY_MUSIC_CENSORSHIP`） | 10+ 人口城市 -1 宜居度 | `MUSIC_CENSORSHIP_AMENITY_LOSS` | `-1` | `MUSIC_CENSORSHIP_10_POPULATION_REQUIREMENT` |
> | 自动化劳动力（`POLICY_AUTOMATED_WORKFORCE`） | 城市每回合 -1 宜居度 | `AUTOMATED_WORKFORCE_AMENITY_LOSS` | `-1` | 无（全城生效） |
>
> **政体实例**（通过 `GovernmentModifiers`）：
> - 古典共和（`GOVERNMENT_CLASSICAL_REPUBLIC`）→ +1 宜居度（含至少 1 个特色区时），与政策"自由主义"共享同一 Modifier
> - 数字化民主（`GOVERNMENT_DIGITAL_DEMOCRACY`）→ +2 宜居度（无条件全城生效）

---

### EFFECT_ADJUST_POLICY_HOUSING

根据政策或政体条件，调整城市的住房。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_POLICY_HOUSING` | `COLLECTION_PLAYER_CITIES`（对玩家所有城市生效，通常配合 `SubjectRequirementSetId` 筛选） |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `Amount` | **必填** | 住房增减值（整数）。常见范围 `1` ~ `4` |

> **溯源**（原版政策卡实例，通过 `PolicyModifiers`）：
> | 政策 | LOC 描述 | ModifierId | Amount | 条件 |
> |---|---|---|---|---|
> | 楼房（`POLICY_INSULAE`） | 2+ 区域城市 +1 住房 | `INSULAE_SPECIALTYHOUSING` | `1` | `CITY_HAS_2_SPECIALTY_DISTRICTS_REQUIREMENTS` |
> | 古老城区（`POLICY_MEDINA_QUARTER`） | 3+ 独立区域城市 +2 住房 | `MEDINAQUARTER_SPECIALTYHOUSING` | `2` | `CITY_HAS_3_SPECIALTY_DISTRICTS_REQUIREMENTS` |
> | 新政（`POLICY_NEW_DEAL`） | 3 特色区城市 +4 住房 | `NEWDEAL_SPECIALTYHOUSING` | `4` | `CITY_HAS_3_SPECIALTY_DISTRICTS_REQUIREMENTS` |
> | 古典共和政策（`POLICY_GOV_CLASSICAL_REPUBLIC`） | 1+ 特色区城市 +1 住房 | `CLASSICAL_REPUBLIC_HOUSING` | `1` | `CITY_HAS_1_SPECIALTY_DISTRICT` |
> | 君主制政策（`POLICY_GOV_MONARCHY`） | 远古墙/中世纪墙/文艺复兴墙各 +1 住房 | `MONARCHY_WALLS_HOUSING` / `MONARCHY_CASTLE_HOUSING` / `MONARCHY_STARFORT_HOUSING` | 各 `1` | `CITY_HAS_ANCIENT_WALLS` 等 |
> | 民间威望（`POLICY_CIVIL_PRESTIGE`） | 含 2 项升级总督的城市 +2 住房 | `CIVILPRESTIGE_GOVHOUSING` | `2` | `CITY_HAS_2_TITLE_GOVERNOR_REQUIREMENTS` |
> | 集体主义（`POLICY_COLLECTIVISM`） | 所有城市 +2 住房 | `COLLECTIVISM_ADD_HOUSING` | `2` | 无（全城生效） |
>
> **政体实例**（通过 `GovernmentModifiers`）：
> - 古典共和（`GOVERNMENT_CLASSICAL_REPUBLIC`）→ +1 住房（含 1+ 特色区）；同时也有 `POLICY_GOV_CLASSICAL_REPUBLIC` 伪政策卡（`PolicyModifiers`），在 UI 中显示为政体的"固有加成"
> - 君主制（`GOVERNMENT_MONARCHY`）→ 按城墙等级提供住房，同 `POLICY_GOV_MONARCHY` 伪政策卡
>
> **建筑实例**（通过 `BuildingModifiers`）：
> - 谒见厅（`BUILDING_GOV_TALL`）→ 有总督的城市 +4 住房（`GOV_TALL_HOUSING_BUFF`，配合 `CITY_HAS_GOVERNOR_REQUIREMENTS`）

---

### EFFECT_REPLACE_PLAYER_GOVERNMENT_SLOT_TYPE

将玩家政体的某个类型的政策槽位替换为另一种类型（如把军事槽换成通配符槽）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CULTURE_REPLACE_GOVERNMENT_SLOTS` | `COLLECTION_OWNER` |

| 参数 | 必填 | 值/引用 |
|---|---|---|
| `ReplacedGovernmentSlotType` | **必填** | 被替换的槽位类型。`SLOT_ECONOMIC` / `SLOT_MILITARY` / `SLOT_DIPLOMATIC`，来源 `GovernmentSlots.GovernmentSlotType` |
| `AddedGovernmentSlotType` | **必填** | 替换成的新槽位类型（官方用法始终为 `SLOT_WILDCARD`） |
| `ReplacesAll` | 可选 | 布尔值。`true` 或 `1` = 替换该类型全部槽位；不写则为默认替换 1 个 |

> **溯源**（官方原版实例，均通过 `TraitModifiers`）：
> - 波兰文明特性"贵族民主制"（`TRAIT_CIVILIZATION_GOLDEN_LIBERTY`）→ `TRAIT_REPLACE_MILITARY_SLOT_WITH_WILDCARD`：Replaced=SLOT_MILITARY, Added=SLOT_WILDCARD（仅替换 1 个军事槽）
> - 美国文明特性"开国元勋"（`TRAIT_CIVILIZATION_FOUNDING_FATHERS`）→ `TRAIT_ALL_DIPLO_POLICY_ARE_WILDCARDS`：Replaced=SLOT_DIPLOMATIC, Added=SLOT_WILDCARD, ReplacesAll=1（**所有**外交槽替换为通配符）
>
> 该效果只有 `ReplacesAll` 参数影响替换数量，无独立 `Amount` 参数。

---

## 注意事项

1. **两个"增加槽位"效果的区别**：
   - `EFFECT_ADJUST_GOVERNMENT_SLOTS`：可增减任意数量（`Amount` 参数，±N），`COLLECTION_MAJOR_PLAYERS`（全体玩家）
   - `EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE`：固定 +1 槽位（无 `Amount`），`COLLECTION_OWNER`（仅拥有者）

2. **`EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE` 与 `EFFECT_REPLACE_PLAYER_GOVERNMENT_SLOT_TYPE` 的区别**：前者新增一个槽位（拓展槽位总数），后者替换现有槽位的类型（总数不变）。

3. **ModifierType 命名警告**：
   - `MODIFIER_PLAYER_CULTURE_ADJUST_GOVERNMENT_SLOTS_MODIFIER` 命名含 `CULTURE` 但效果与文化值无关
   - `MODIFIER_PLAYER_CULTURE_REPLACE_GOVERNMENT_SLOTS` 同理，命名含 `CULTURE` 但与文化值无关

4. **`EFFECT_ADJUST_PLAYER_BAN_POLICY`**：引擎支持但原版无使用实例（DB 中 24 个实例全来自 SIQI 模组）。`Effects.csv` 标记为 UNTESTED。配合 `SubjectRequirementSetId` 可实现条件禁用（如必须拥有某建筑才能使用某政策）。

5. **`EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR`** 的 ModifierType 为 `MODIFIER_PLAYER_ADJUST_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR`，与 `EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE` 的 ModifierType `MODIFIER_PLAYER_CULTURE_ADJUST_GOVERNMENT_SLOTS_MODIFIER` **完全不同**，勿混淆。

6. **`POLICY_GOV_*` 伪政策卡**：政体固有加成（如古典共和 +1 住房/+1 宜居度）同时存在于 `PolicyModifiers`（挂 `POLICY_GOV_CLASSICAL_REPUBLIC`）和 `GovernmentModifiers`（挂 `GOVERNMENT_CLASSICAL_REPUBLIC`）。`POLICY_GOV_*` 用作 UI 显示的"政策卡"载体，选择政体时自动获得对应伪政策，改政体时自动移除。

7. **槽位枚举值**：
   - `SLOT_ECONOMIC` = 经济槽位
   - `SLOT_MILITARY` = 军事槽位
   - `SLOT_DIPLOMATIC` = 外交槽位
   - `SLOT_WILDCARD` = 通配符槽位（`AllowsAnyPolicy=1`，可放任意类型政策卡）
   - `SLOT_GREAT_PERSON` = 伟人槽位（DLC 引入，极少使用）
