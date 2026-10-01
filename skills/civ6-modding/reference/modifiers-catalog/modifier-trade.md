# modifier-trade -- 商路类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

## 概述

商路类 EffectType 共 **57** 个，涵盖商路产出、容量、外交、宗教压力、旅游业绩等所有商路相关机制。

| 子类 | 数量 | 说明 |
|------|------|------|
| 商路产出调整（城市级） | ~11 | PER_DESTINATION / PER_LOCAL 系列，城市级按资源/设施计算 |
| 商路产出调整（玩家级） | ~19 | TRADE_ROUTE_YIELD 系列，玩家全局或按条件 |
| 商路容量 | 6 | 增加商路数量上限（含特殊触发条件变体） |
| 外交与商路 | 3 | 一厢情愿贸易 / 贸易关系好感 / 同盟点数 |
| 城邦商路加成 | 3 | 城邦类型商路加成 / 城邦区域产出 / 使者复制 |
| 同盟/宗主商路 | 4 | 同盟间 + 宗主间商路产出（起源/目的地双向） |
| 特殊机制 | 11 | 宗教压力 / 旅游业绩 / 掠夺免疫 / 禁运 / 忠诚度等 |

---

## A. 商路产出调整（城市级）

以**城市为作用域**的产出调整，建筑/区域附着时使用。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_FOR_DOMESTIC

调整单城国内商路固定产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_TRADE_ROUTE_YIELD_FOR_DOMESTIC` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_YIELD_FOR_DOMESTIC_WARLORDS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType`，如 `YIELD_GOLD` / `YIELD_PRODUCTION` |

> **溯源**：纳迪尔沙（波斯之剑）— 国内商路 +3 金币、+2 信仰（`COLLECTION_PLAYER_CITIES`）。基础版 `COLLECTION_OWNER` 用于建筑附着（如自定义区域建筑）。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL

调整单城国际商路固定产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |
| `MODIFIER_ALL_CITIES_ADJUST_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL` | `COLLECTION_ALL_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：宗教社区（信条）— 神社/寺庙等建筑各 +2 金币（`COLLECTION_OWNER`，建筑附着）。帕依提提（自然奇观）— 国际商路 +4 金币（`COLLECTION_ALL_CITIES`，全局城市）。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_DESTINATION_LUXURY_RESOURCE_FOR_INTERNATIONAL

国际商路**目的地**每有一种奢侈资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_YIELD_PER_DESTINATION_LUXURY_FOR_INTERNATIONAL` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_ADJUST_TRADE_ROUTE_YIELD_PER_DESTINATION_LUXURY_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种奢侈资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：市场经济（政策）— 国际商路目的地每种奢侈资源 +1 金币。阿姆斯特丹/安条克（城邦）— 每种奢侈资源 +1 金币。贝伦塔（奇观）— 每种奢侈资源 +2 金币（`COLLECTION_OWNER`）。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_DESTINATION_STRATEGIC_RESOURCE_FOR_DOMESTIC

国内商路**目的地**每有一种战略资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_YIELD_PER_DESTINATION_STRATEGIC_FOR_DOMESTIC` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种战略资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：大商人（马可波罗/梅莉塔·本茨）— 国内商路目的地每种战略资源 +2 金币。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_DESTINATION_STRATEGIC_RESOURCE_FOR_INTERNATIONAL

国际商路**目的地**每有一种战略资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_YIELD_PER_DESTINATION_STRATEGIC_FOR_INTERNATIONAL` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种战略资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：大商人（马可波罗/梅莉塔·本茨）— 国际商路目的地每种战略资源 +2 金币。市场经济（政策）— 每种战略资源 +1 金币。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_BONUS_RESOURCE_FOR_DOMESTIC

国内商路**起源城市**每有一种加成资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_BONUS_RESOURCE_FOR_DOMESTIC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种加成资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：大津巴布韦（奇观）— 国内商路起源每种加成资源 +2 金币（`COLLECTION_OWNER`，单城）。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_BONUS_RESOURCE_FOR_INTERNATIONAL

国际商路**起源城市**每有一种加成资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_BONUS_RESOURCE_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_TRADE_ROUTE_YIELD_PER_LOCAL_BONUS_RESOURCE_FOR_INTERNATIONAL` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 支持小数（如 `0.5`），每种加成资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：大津巴布韦（奇观）— 国际商路起源每种加成资源 +2 金币（`COLLECTION_OWNER`）。埃塞俄比亚（阿克苏姆的遗产）— 每种加成资源 +0.5 信仰（`COLLECTION_PLAYER_CITIES`）。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_LUXURY_RESOURCE_FOR_INTERNATIONAL

国际商路**起源城市**每有一种奢侈资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_TRADE_ROUTE_YIELD_PER_LOCAL_LUXURY_RESOURCE_FOR_INTERNATIONAL` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SIQI0032_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_LUXURY_RESOURCE_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 支持小数（如 `0.5`），每种奢侈资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：埃塞俄比亚（阿克苏姆的遗产）— 每种奢侈资源 +0.5 信仰（`COLLECTION_PLAYER_CITIES`）。注意 `SIQI0032` 变体为社区自定义但已在 DB 中注册为独立 ModifierType。

---

### EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_STRATEGIC_RESOURCE_FOR_INTERNATIONAL

国际商路**起源城市**每有一种战略资源，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_TRADE_ROUTE_YIELD_PER_LOCAL_STRATEGIC_RESOURCE_FOR_INTERNATIONAL` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SIQI0032_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_STRATEGIC_RESOURCE_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 支持小数（如 `0.5`），每种战略资源增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：埃塞俄比亚（阿克苏姆的遗产）— 每种战略资源 +0.5 信仰（`COLLECTION_PLAYER_CITIES`）。

---

### EFFECT_ADJUST_CITY_YIELD_FROM_FOREIGN_TRADE_ROUTES_PASSING_THROUGH

外国商路经过本城时，为本城提供产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_YIELD_FROM_FOREIGN_TRADE_ROUTES_PASSING_THROUGH` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_ADJUST_YIELD_FROM_FOREIGN_TRADE_ROUTES_PASSING_THROUGH` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每条路过的外国商路提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：在线社区（政策）— 经过的外国商路 +3 金币（`COLLECTION_OWNER`，单城作用域）。注意在线社区的官方 LOC 为"在线社区"，实际使用 `FOREIGN_EXCHANGE` ModifierId。

---

### EFFECT_ADJUST_CITY_YIELD_PER_MAJOR_TRADE_PARTNER

每有一个主要文明贸易伙伴，城市产出增加（仅 GS 扩展）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_PER_MAJOR_TRADE_PARTNER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每个主要贸易伙伴提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：新加坡（城邦）— 每个主要贸易伙伴 +2 生产力（`COLLECTION_PLAYER_CITIES`）。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_DOMESTIC

国内商路目的地城市每有一处专业化区域，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_DOMESTIC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 支持小数（如 `0.5`），每专业区域增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：德川家康（幕藩）— 国内商路目的地每个专业化区域 +1 文化/+1 金币/+1 科技。大商人（马可波罗）— 国内商路每个专业区域 +0.5 金币。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_INTERNATIONAL

国际商路目的地城市每有一处专业化区域，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数或小数，每专业区域增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：经济黄金时代纪念（GS 模式）— 国际商路每个专业化区域 +3 金币。

---

## B. 商路产出调整（玩家级）

以**玩家为作用域**的全局产出调整，政策/领袖特质/伟人用。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD

调整所有商路的固定产出（最基础通用的商路产出效果）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：商队旅馆（政策）— 所有商路 +2 金币。三角贸易（政策）— 所有商路 +4 金币、+1 信仰。电子商务（政策）— 所有商路 +5 金币、+2 生产力。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_FOR_DOMESTIC

调整所有国内商路的产出（玩家全局）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_FOR_DOMESTIC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `Intercontinental` | 选写 | `Boolean`，`1` = 仅跨大陆国内商路有效 |

> **溯源**：孤立主义（政策）— 国内商路 +2 粮食、+2 生产力（`Intercontinental=0`）。集体化（政策）— 国内商路 +4 粮食、+2 生产力。波斯行省总督（文明特质）— 国内商路 +1 文化、+2 金币。葡萄牙（印度之家）— 跨大陆国内商路 +6 金币/+6 信仰/+6 生产力（`Intercontinental=1`）。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL

调整所有国际商路的产出（玩家全局）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `Intercontinental` | 选写 | `Boolean`，`1` = 仅跨大陆国际商路有效 |

> **溯源**：贸易联盟（政策）— 国际商路 +1 文化、+1 科技。市场经济（政策）— 国际商路 +2 文化、+2 科技。电子商务（政策）— 国际商路 +2 金币、+2 生产力。葡萄牙（印度之家）— 国际商路 +3 金币/+3 信仰/+3 生产力；跨大陆时 +6（`Intercontinental=1`）。

---

### EFFECT_ADJUST_PLAYER_INTERNATIONAL_TRADE_ROUTE_YIELD_MODIFIER

**百分比**调整国际商路产出（支持多产出逗号分隔）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_INTERNATIONAL_TRADE_ROUTE_YIELD_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_ADJUST_INTERNATIONAL_TRADE_ROUTE_YIELD_MODIFIER_WARLORDS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 逗号分隔的百分比列表（如 `"50, 50, 50, 50, 50, 50"`），负值 = 减少 |
| `YieldType` | **必写** | 逗号分隔的 `Yields.YieldType` 列表，与 `Amount` 一一对应 |

> **溯源**：葡萄牙（印度之家）— 国际商路全产出 +50%（6 种产出各 +50%）。德川家康（幕藩）— 国际商路全产出 -25%（`_WARLORDS` 变体，6 种各 -25%）。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_MODIFIER

百分比调整商路产出（可分别指定起源/目的地侧）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数（百分比），正值为增加，负值为减少 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `Origin` | 选写 | `Boolean`，`1` = 影响起源城市侧 |
| `Destination` | 选写 | `Boolean`，`1` = 影响目的地城市侧 |

> **溯源**：私掠许可证（政策）— 目的地侧 6 种产出各 -50% + 起源侧 6 种产出各 -50%（逐产出分别建 Modifier，共 12 个）。采办中心（自定义建筑）— 类似私掠许可证的正值版（各 +50%）。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_IN_TARGET_CITY

商路目标城市每有指定改良设施，产出增加。可分别指定起源/目的地侧。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_IN_TARGET` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_AT_LOCATION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每改良设施增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `ImprovementType` | **必写** | `Improvements.ImprovementType` |
| `Origin` | 选写 | `Boolean`，`1` = 影响起源侧 |
| `Destination` | 选写 | `Boolean`，`1` = 影响目的地方侧 |

> **溯源**：威尔米娜（"同盟与贸易"领袖）— 营地 +1 粮食（Origin）、+1 金币（Destination）；牧场 +1 粮食（Origin）、+1 金币（Destination）。葡萄牙商站文明— 商站 +4 金币（Origin）、+1 生产力（Origin），使用 `AT_LOCATION` 变体。

> **区别：** `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_IN_TARGET` 同时支持 `Origin` + `Destination` 参数。`MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_AT_LOCATION` 仅支持 `Origin`。

---

### EFFECT_ADJUST_PLAYER_INTERNATIONAL_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_IN_ORIGIN_CITY

国际商路起源城市每有指定改良设施，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_IMPROVEMENT_AT_LOCATION_BABYLON` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每改良设施增加的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `ImprovementType` | **必写** | `Improvements.ImprovementType` |

> **溯源**：撒马尔罕（城邦）— 国际商路起源每有贸易圆顶 +1 金币。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_PATH_TILE

商路每经过一格，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_PATH_TILE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 支持小数（如 `0.2`）或整数，每格产出增加 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：罕萨（城邦）— 商路每格 +0.2 金币。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_POST_IN_FOREIGN_CITY

每条商路的外国城市中每有一个己方贸易站，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_POST_IN_FOREIGN_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每个外国城市贸易站提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：雅加达（城邦）— 每个外国城市贸易站 +1 金币。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_POST_IN_OWN_CITY

每条商路的己方城市中每有一个己方贸易站，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_POST_IN_OWN_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每个己方城市贸易站提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：克莉奥帕特拉（地中海新娘）— 每个己方城市贸易站 +1 金币。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_TERRAIN_FOR_DOMESTIC

国内商路起源/目的地城市有指定地形时，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_TERRAIN_DOMESTIC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种指定地形/格提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `TerrainType` | **必写** | `Terrains.TerrainType`，如 `TERRAIN_DESERT_MOUNTAIN` |
| `Origin` | 选写 | `Boolean`，`1` = 影响起源城市 |

> **溯源**：帕查库蒂（印加路网）— 国内商路起源有沙漠山脉/草原山脉/平原山脉/雪地山脉/冻土山脉时，每种 +1 粮食（Origin=1，每种地形分别建一个 Modifier）。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_TERRAIN_FOR_INTERNATIONAL

国际商路起源/目的地城市有指定地形时，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_TERRAIN_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种指定地形/格提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `TerrainType` | **必写** | `Terrains.TerrainType` |
| `Origin` | 选写 | `Boolean`，`1` = 影响起源城市 |

> **溯源**：曼萨穆萨（萨赫勒商人）— 国际商路起源有沙漠时 +1 金币（Origin=1）。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_YIELD_PER_FOLLOWER

商路目的地城市的信仰追随者每有一人，产出增加。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_FOLLOWER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每个追随者提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：欣盖提（城邦）— 目的地每位追随者 +1 信仰。

---

### EFFECT_ADJUST_PLAYER_PROGRESS_DIFF_TRADE_BONUS

根据科技/市政领先程度提供商路加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PROGRESS_DIFF_TRADE_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `TechCivicsPerYield` | **必写** | 整数，每领先 N 个科技/市政提供 1 点商路产出 |

> **溯源**：巴比伦（大使馆）— 每领先 3 个科技/市政，商路提供额外产出（参数名非 `Amount`，使用 `TechCivicsPerYield`）。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_CHANGE

调整特定商路集合的产出（同盟和紧急事件专用）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_TRADE_ROUTES_ADJUST_YIELDS` | `COLLECTION_EMERGENCY_TRADE_ROUTES` |
| `MODIFIER_ALLIANCE_TRADE_ROUTE_ADJUST_YIELD` | `COLLECTION_ALLIANCE_TRADEROUTES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `AffectOrigin` | 选写 | `Boolean`，`1` = 影响起源侧 |
| `AffectDestination` | 选写 | `Boolean`，`1` = 影响目的地方侧 |

> **溯源**：经济同盟（1 级）— 同盟间商路目的地 +2 金币、起源 +4 金币。文化同盟（1 级）— 目的地方 +1 文化、起源 +1 文化。宗教同盟（1 级）— 目的地方 +2 信仰、起源 +2 信仰。科技同盟（1 级）— 目的地方 +1 科技、起源 +1 科技。背叛紧急事件 — 会员间商路起源 +2 生产力、目的地方 +2 生产力（同时设置 `AffectOrigin=1, AffectDestination=1`）。

> **注意：** 此 Effect 作用于商路集合（`COLLECTION_ALLIANCE_TRADEROUTES` / `COLLECTION_EMERGENCY_TRADE_ROUTES`），非玩家或城市级，需配合同盟/紧急事件的 SubjectRequirementSet。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_FROM_OTHERS

调整**其他文明通往己方**的商路为己方提供的产出（外部商路→己方获得）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_YIELD_FROM_OTHERS` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_TRADE_ROUTE_YIELD_FROM_OTHERS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `Domestic` | 选写 | `Boolean`，`0` = 仅国际商路（默认），`1` = 含国内 |

> **溯源**：克莉奥帕特拉（地中海新娘）— 入向商路 +2 金币（`COLLECTION_PLAYER_CITIES`）。威廉明娜（橙色电台）— 入向商路 +2 文化。郑和（大商人）— 单城入向商路 +2 金币（`COLLECTION_OWNER`）。桑科雷大学（奇观）— 入向商路 +2 科技（Domestic=0）。世界议会贸易条约决议 — 入向商路 +4 金币。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_TO_OTHERS

调整**己方通往其他文明**的商路为对方提供的产出（己方商路→对方获得）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_YIELD_TO_OTHERS` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_TRADE_ROUTE_YIELD_TO_OTHERS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |
| `Domestic` | 选写 | `Boolean`，`true`/`false`，`true` = 含国内商路 |

> **溯源**：克莉奥帕特拉（地中海新娘）— 出向商路对方 +2 粮食（`COLLECTION_PLAYER_CITIES`）。各城邦类型（贸易/文化/工业/军事/宗教/科技）— 对应产出给对方 +1~+2（`COLLECTION_PLAYER_CITIES`）。桑科雷大学（奇观）— 出向商路对方 +1 金币/+1 科技；国内出向商路对方 +1 信仰/+1 科技（Domestic=1）。郑和（大商人）— 单城出向商路对方 +2 金币（`COLLECTION_OWNER`）。剩余物流（政策）— 出向国内商路对方 +2 粮食（Domestic=true）。

---

## C. 城邦商路加成

---

### EFFECT_ADJUST_CITY_STATE_TRADE_ROUTE_FLAT_YIELD

调整通往城邦的商路所额外提供的固定产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTES_CITY_STATE_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，固定产出数值 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：伊本·法德兰（大商人）— 通往城邦商路 +2 信仰。统治（政策）— 通往城邦商路 +2 金币。

---

### EFFECT_ADJUST_CITY_STATE_TRADE_ROUTE_DISTRICT_YIELD

通往城邦的商路，目的地城市每有一种区域类型，产出增加（库马西机制）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_STATE_TRADE_ROUTE_DISTRICT_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每区域提供的产出 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：库马西（城邦）— 通往城邦的商路，每个区域 +2 文化、+1 金币。伊丽莎白一世（德瑞克的遗产）— 通往城邦商路 +3 金币。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_BY_CITY_STATE_BONUS_TYPE_MODIFIER

百分比修改城邦类型提供的商路加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_MAJOR_PLAYER_TRADE_ROUTE_BY_CITY_STATE_BONUS_TYPE_MODIFIER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数（百分比），如 `100` = 加倍 |

> **溯源**：世界议会主权决议 — 城邦类型商路加成 +100%（`COLLECTION_MAJOR_PLAYERS`，作用于所有主要文明）。

---

## D. 同盟/宗主商路产出

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_DESTINATION_YIELD_FOR_ALLY_ROUTE

通往盟友的商路，为**目的地城市**增加产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_DESTINATION_YIELD_FOR_ALLY_ROUTE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：民主主义政体 — 盟友商路目的地 +4 粮食、+4 生产力。贸易银行（政策）— +2 粮食、+2 生产力。民主兵工厂（政策）— +2 粮食、+2 生产力。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_DESTINATION_YIELD_FOR_SUZERAIN_ROUTE

通往宗主的商路，为**目的地城市**增加产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_DESTINATION_YIELD_FOR_SUZERAIN_ROUTE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：民主主义政体 — 宗主商路目的地 +4 粮食、+4 生产力。贸易银行（政策）— +2 粮食、+2 生产力。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_ORIGIN_YIELD_FOR_ALLY_ROUTE

来自盟友的商路，为**起源城市**增加产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_ORIGIN_YIELD_FOR_ALLY_ROUTE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：民主主义政体 — 来自盟友的商路起源 +4 粮食、+4 生产力。民主兵工厂（政策）— +2 粮食、+2 生产力。贸易银行（政策）— 起源 +2 粮食、+2 生产力。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_ORIGIN_YIELD_FOR_SUZERAIN_ROUTE

来自宗主的商路，为**起源城市**增加产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_ORIGIN_YIELD_FOR_SUZERAIN_ROUTE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出增量 |
| `YieldType` | **必写** | `Yields.YieldType` |

> **溯源**：民主主义政体 — 来自宗主的商路起源 +4 粮食、+4 生产力。贸易银行（政策）— 起源 +2 粮食、+2 生产力。

---

## E. 商路容量

---

### EFFECT_ADJUST_TRADE_ROUTE_CAPACITY

调整商路容量上限（最通用的商路容量效果）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_CAPACITY` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_TRADE_ROUTE_CAPACITY` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_PLAYER_CITIES_ADJUST_TRADE_ROUTE_CAPACITY` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_ALLIANCE_PLAYER_TRADE_ROUTE_CAPACITY` | `COLLECTION_ALLIANCE_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，增加的商路容量 |

> **溯源**：
> - `COLLECTION_OWNER`（最常用）：巨像/大津巴布韦 +1；市场/灯塔 +1；对外贸易市政 +1；大商人（马可波罗/张骞/梅莉塔）激活后 +1；伊丽莎白一世 +2
> - `COLLECTION_PLAYER_DISTRICTS`：每个商业中心 +1（见 `TRAIT_POTTERY_TRADE_ROUTE` 示例）
> - `COLLECTION_PLAYER_CITIES`：迦太基建国者 — 政府区建筑每城 +1
> - `COLLECTION_ALLIANCE_PLAYERS`：同盟成员 +1

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_CAPACITY_ON_MEETING

首次遭遇其他文明时获得商路容量。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_CAPACITY_ON_MEETING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，商路容量增加数 |
| `Intercontinental` | 选写 | `Boolean`，`1` = 仅跨大陆有效 |

> **溯源**：若昂三世（关闸）— 首次遭遇文明 +1 商路容量（`Amount=1`）。

---

### EFFECT_GRANT_FOUND_FOREIGN_CITY_TRADE_ROUTE_CAPACITY

首次在外大陆建立城市时获得商路容量。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_CAPACITY_FOUND_FOREIGN_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，增加的商路容量 |

> **溯源**：维多利亚（英国强权下的和平）— 在外大陆建城 +1 商路。

---

### EFFECT_GRANT_GOLDEN_AGE_TRADE_ROUTE_CAPACITY

黄金时代获得商路容量。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_CAPACITY_GOLDEN_AGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，增加的商路容量 |

> **溯源**：曼萨穆萨（萨赫勒商人）— 黄金时代 +1 商路容量。

---

### EFFECT_ADJUST_TRADE_ROUTE_WATER_RANGE

调整水上商路范围。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_WATER_RANGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，水上商路额外格数 |

> **溯源**：葡萄牙（印度之家）— 水上商路范围 +15 格。

---

## F. 外交与商路

---

### EFFECT_DIPLOMACY_ONE_SIDED_TRADES

对"只发不收"交易（一厢情愿贸易）的文明产生外交好感惩罚。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DIPLOMACY_ONE_SIDED_TRADES` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数，好感变化增量（通常为 `0`） |
| `MaxValue` | **必写** | 整数，最大好感惩罚值 |
| `ReductionTurns` | **必写** | 整数，惩罚衰减所需回合数 |
| `ReductionValue` | **必写** | 整数，每回合衰减量 |
| `TradeValuePerModifierPoint` | **必写** | 整数，每点惩罚对应的贸易价值阈值 |

> **溯源**：标准外交（`TRAIT_LEADER_MAJOR_CIV`）— 所有主要文明默认行为：`MaxValue=20, ReductionTurns=2, ReductionValue=1, TradeValuePerModifierPoint=10`。此参数体系完全不同于其他商路效果。

---

### EFFECT_DIPLOMACY_TRADE_RELATIONS

根据贸易关系调整外交好感。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DIPLOMACY_TRADE_RELATIONS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `LOC_` 文本键，外交陈述语句 |
| `SimpleModifierDescription` | **必写** | `LOC_` 文本键，简单描述 |
| `TradeBonus` | **必写** | 整数，基础贸易好感加成 |
| `BonusPerRoute` | 选写 | `Boolean`，`1` = 每条商路额外加好感 |
| `NoTradePenalty` | 选写 | 整数，无商路时的好感惩罚值（如 `12`） |
| `OnlyInboundTrade` | 选写 | `Boolean`，`1` = 仅计入来向商路 |

> **溯源**：标准外交（所有文明默认）— `TradeBonus=3`（基础 +3 好感）。威尔米娜（亿万富翁议程）— `BonusPerRoute=1, NoTradePenalty=12, OnlyInboundTrade=1`，每条来向商路额外好感。伊丽莎白一世（贸易协定议程）— 同上参数。

---

### EFFECT_ADJUST_ALLIANCE_POINTS_FOR_TRADE_MODIFIER

调整每商路提供的同盟点数倍率。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ALLIANCE_POINTS_FOR_TRADE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每商路同盟点数倍率（`1` = 标准倍率） |

> **溯源**：克莉奥帕特拉（地中海新娘）— 每商路同盟点数 ×1（标准倍率）。

---

## G. 特殊机制

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_RELIGIOUS_PRESSURE

调整商路带来的宗教压力。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_RELIGIOUS_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宗教压力百分比增量（如 `100` = 加倍） |
| `Destination` | 选写 | `Boolean`，`1` = 影响目的地宗教压力 |
| `Origin` | 选写 | `Boolean`，`1` = 影响起源城市宗教压力 |

> **溯源**：西班牙（艾斯科里亚尔）— 商路起源+目的地宗教压力各 +100%（`Origin=1, Destination=1`）。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_TOURISM_MODIFIER

百分比调整商路带来的旅游业绩。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_TOURISM_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数（百分比），如 `25` = +25%，`-25` = -25% |

> **溯源**：大商人（莎拉·布里德洛夫/梅莉塔·本茨）— 商路旅游业绩 +25%。在线社区（政策）— +50%。德川家康（幕藩）— 国际商路旅游业绩 -25%。

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_TRADE_ROUTE_COMPLETED

每完成一条商路，获得时代分数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_TRADE_ROUTE_COMPLETED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每条完成的商路给予的时代分数 |

> **溯源**：经济黄金时代纪念（GS 模式）— 每完成商路 +1 时代分数。

---

### EFFECT_ADJUST_PLAYER_IDENTITY_PER_TURN_FOR_DOMESTIC_TRADE_ROUTE_ORIGIN

每有一条国内商路从己方城市出发，每回合获得忠诚度。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_IDENTITY_PER_TURN_FOR_DOMESTIC_TRADE_ROUTE_ORIGIN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每条国内出发商路提供的忠诚度/回合 |

> **溯源**：威廉明娜（橙色电台）— 每条国内出发商路 +2 忠诚度/回合。

---

### EFFECT_ADJUST_UNIT_TRADE_ROUTE_PLUNDER_IMMUNITY

使指定域的单位获得商路掠夺免疫。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TRADE_ROUTE_PLUNDER_IMMUNITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DomainType` | **必写** | `DOMAIN_LAND` 或 `DOMAIN_SEA` |

> **溯源**：经济黄金时代 — 陆地单位免疫掠夺（`DOMAIN_LAND`）+ 海上单位免疫掠夺（`DOMAIN_SEA`）。曼德卡鲁骑兵（马里 UU）— 附近陆地商路免疫掠夺。拜占庭桨帆船 — 附近海上商路免疫掠夺。

---

### EFFECT_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_TRADE_ROUTE_TO

向有商路连接的城邦派遣使者时，额外获得等同于已派遣数量的使者。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_TRADE_ROUTE_TO` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，复制的使者数量（= 已派遣数量 × Amount，通常为 `1`） |

> **溯源**：西奥多·罗斯福（罗斯福推论）— 向有商路的城邦派遣使者时，复制已派遣使者数量（`Amount=1`）。

---

### EFFECT_ADJUST_PLAYER_TRADE_GAIN_TILES_EN_ROUTE

商路经过地块时获得视野。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_TRADE_GAIN_TILES_EN_ROUTE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `GainTileRadius` | **必写** | 整数，商路沿途获得视野的半径格数 |

> **溯源**：克里（林地克里人）— 商路路径打开 3 格视野（`GainTileRadius=3`）。注意参数名非 `Amount`。

---

### EFFECT_TRADE_ROUTE_DISABLE

禁用指定类型的商路。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_TRADE_ROUTES_DISABLE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Domestic` | **必写** | `Boolean`，`1` = 禁用国内商路 |
| `InternationalMajors` | **必写** | `Boolean`，`1` = 禁止通往主要文明的国际商路 |
| `InternationalMinors` | **必写** | `Boolean`，`1` = 禁止通往城邦的国际商路 |

> **溯源**：世界议会贸易条约决议（效果 2）— 禁用国际主要文明商路（`Domestic=0, InternationalMajors=1, InternationalMinors=0`）。

---

## H. 无活跃实例的效果（需验证）

以下 EffectType 在 DynamicModifiers 中注册，但数据库中**无活跃 Modifier 实例**，且无 `GameEffectArguments` 定义。参数仅能通过命名和关联模式推断。

| EffectType | 注册 ModifierType | CollectionType | 风险 |
|---|---|---|---|
| `EFFECT_ADJUST_PLAYER_ANYONE_TRADE_TO_FAVOR` | `MODIFIER_PLAYER_ADJUST_ANYONE_TRADE_TO_FAVOR` | `COLLECTION_OWNER` | 中 — 推断参数 `Amount`（外交支持），名称含 "ANYONE" 暗示与所有文明交易相关 |
| `EFFECT_ADJUST_PLAYER_SEND_TRADE_ROUTE_FAVOR_BY_BONUS_TYPE` | `MODIFIER_PLAYER_ADJUST_SEND_TRADE_ROUTE_FAVOR_BY_BONUS` | `COLLECTION_OWNER` | 中 — 推断参数 `Amount` + `BonusType`，`BonusType` 枚举待确认 |
| `EFFECT_ADJUST_PLAYER_TOKEN_ON_TRADE_ROUTE_STARTED` | `MODIFIER_PLAYER_ADJUST_TOKEN_ON_TRADE_ROUTE_STARTED` | `COLLECTION_OWNER` | 高 — 无参数记录，推断为商路开始时获得使者 |
| `EFFECT_TRADE_ROUTE_CANCEL` | `MODIFIER_EMERGENCY_TRADE_ROUTES_CANCEL` | `COLLECTION_EMERGENCY_TRADE_ROUTES` | 高 — 两个 ModifierType 均无活跃实例，无参数记录 |
| `EFFECT_TRADE_ROUTE_CANCEL` | `MODIFIER_PLAYER_TRADE_ROUTES_CANCEL` | `COLLECTION_OWNER` | 高 — 同上 |

---

## PER_xxx 系列效果矩阵

"起源地每有一种 X 资源" vs "目的地每有一种 Y 资源"，国内 vs 国际商路，三种资源类型（加成/奢侈/战略）的交叉矩阵。

| 维度 | 国内 (Domestic) | 国际 (International) |
|------|:--:|:--:|
| 目的地奢侈资源数 | **缺失** | `PER_DESTINATION_LUXURY_RESOURCE_FOR_INTERNATIONAL` |
| 目的地战略资源数 | `PER_DESTINATION_STRATEGIC_RESOURCE_FOR_DOMESTIC` | `PER_DESTINATION_STRATEGIC_RESOURCE_FOR_INTERNATIONAL` |
| 目的地加成资源数 | **缺失**（游戏本身有此判定逻辑吗？） | **缺失** |
| 起源地加成资源数 | `PER_LOCAL_BONUS_RESOURCE_FOR_DOMESTIC` | `PER_LOCAL_BONUS_RESOURCE_FOR_INTERNATIONAL` |
| 起源地奢侈资源数 | **缺失** | `PER_LOCAL_LUXURY_RESOURCE_FOR_INTERNATIONAL` |
| 起源地战略资源数 | **缺失** | `PER_LOCAL_STRATEGIC_RESOURCE_FOR_INTERNATIONAL` |

**8 种可能组合中 5 种缺失。** 缺失的格子可通过 `EFFECT_ADJUST_TRADE_ROUTE_YIELD_FOR_DOMESTIC` 或 `EFFECT_ADJUST_TRADE_ROUTE_YIELD_FOR_INTERNATIONAL` 配合条件需求间接实现。

近年新增的 `PER_SPECIALTY_DISTRICT_FOR_DOMESTIC` 和 `PER_SPECIALTY_DISTRICT_FOR_INTERNATIONAL` 属于专业化区域维度，非资源维度，完整矩阵（国内/国际）均有覆盖。

---

## 注意事项

### 作用域选择

| CollectionType | 适用场景 | 示例 |
|---|---|---|
| `COLLECTION_OWNER` | 单城（建筑/区域附着）或单玩家全局 | 灯塔 +1 商路、民主政体同盟商路产出 |
| `COLLECTION_PLAYER_CITIES` | 全文明城市 | 纳迪尔沙国内商路产出、埃塞俄比亚资源加成 |
| `COLLECTION_ALL_CITIES` | 全局所有城市（自然奇观/世界奇观） | 帕依提提 +4 金币 |
| `COLLECTION_PLAYER_DISTRICTS` | 按区域类型累加 | 每商业中心 +1 商路 |
| `COLLECTION_MAJOR_PLAYERS` | 所有主要文明（外交/世界议会） | 贸易关系好感、一厢情愿惩罚 |
| `COLLECTION_ALLIANCE_PLAYERS` | 同盟成员 | 同盟 +1 商路 |
| `COLLECTION_ALLIANCE_TRADEROUTES` | 同盟间的商路集合 | 同盟 1 级商路产出 |
| `COLLECTION_EMERGENCY_TRADE_ROUTES` | 紧急事件相关商路集合 | 背叛紧急事件商路 buff |

### 关键区别

1. **`EFFECT_ADJUST_CITY_TRADE_ROUTE_YIELD_FOR_DOMESTIC` vs `EFFECT_ADJUST_TRADE_ROUTE_YIELD_FOR_DOMESTIC`**
   - 前者（CITY 前缀）：城市级，建筑/区域附着用。两种 ModifierType 变体（`SINGLE_CITY` / `PLAYER_CITIES_WARLORDS`）
   - 后者（无 CITY 前缀）：玩家全局。一种 ModifierType，支持 `Intercontinental` 参数

2. **`FROM_OTHERS` vs `TO_OTHERS`**
   - `FROM_OTHERS` = 其他文明通往己方的商路为**己方**提供产出（入向）
   - `TO_OTHERS` = 己方通往其他文明的商路为**对方**提供产出（出向）
   - 两者均有 `SINGLE_CITY`（`COLLECTION_OWNER`）和 `PLAYER_CITIES`（`COLLECTION_PLAYER_CITIES`）变体

3. **`PER_IMPROVEMENT_IN_TARGET` vs `PER_IMPROVEMENT_AT_LOCATION`**
   - `IN_TARGET`：同时支持 `Origin` + `Destination` 参数，可分别指定影响哪一侧
   - `AT_LOCATION`：仅支持 `Origin` 参数

4. **`EFFECT_ADJUST_TRADE_ROUTE_YIELD_CHANGE` = 商路集合级**
   - 作用于 `COLLECTION_ALLIANCE_TRADEROUTES` / `COLLECTION_EMERGENCY_TRADE_ROUTES`
   - 参数为 `AffectOrigin` / `AffectDestination`（非 `Origin` / `Destination`）

### 特殊参数

- `EFFECT_ADJUST_PLAYER_INTERNATIONAL_TRADE_ROUTE_YIELD_MODIFIER` 的 `Amount` / `YieldType` 使用**逗号分隔多值列表**（6 种产出各 50% 配 6 个 YieldType）
- `EFFECT_ADJUST_PLAYER_PROGRESS_DIFF_TRADE_BONUS` 使用 `TechCivicsPerYield` 参数（非 `Amount`）
- `EFFECT_ADJUST_PLAYER_TRADE_GAIN_TILES_EN_ROUTE` 使用 `GainTileRadius` 参数（非 `Amount`）
- `EFFECT_DIPLOMACY_ONE_SIDED_TRADES` / `EFFECT_DIPLOMACY_TRADE_RELATIONS` 参数体系完全独立，使用 `StatementKey` / `TradeBonus` 等自定义参数名
- `EFFECT_ADJUST_UNIT_TRADE_ROUTE_PLUNDER_IMMUNITY` 使用 `DomainType` 参数（`DOMAIN_LAND` / `DOMAIN_SEA`）

### 商路容量特殊变体

`EFFECT_GRANT_FOUND_FOREIGN_CITY_TRADE_ROUTE_CAPACITY` 和 `EFFECT_GRANT_GOLDEN_AGE_TRADE_ROUTE_CAPACITY` 均有独立的 EffectType（非 `EFFECT_ADJUST_TRADE_ROUTE_CAPACITY` 的子集），各有专用触发条件。

### SIQI 前缀的 ModifierType

DB 中存在多个 `MODIFIER_SIQIxxx` 变体（如 `MODIFIER_SIQI0032_CITY_TRADE_ROUTE_YIELD_PER_LOCAL_LUXURY_RESOURCE_FOR_INTERNATIONAL`），这些为社区自定义 Mod 注册的独立 ModifierType，与官方变体（`MODIFIER_PLAYER_CITIES_TRADE_ROUTE_YIELD_PER_LOCAL_xxx`）功能等价但 CollectionType 不同（`COLLECTION_OWNER` vs `COLLECTION_PLAYER_CITIES`）。使用官方命名时无需关注这些变体。
