# modifier-alliance — 同盟类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 覆盖 15 个同盟相关 EffectType。按字母序排列。
>
> **挂载规则**：通过数据库查实际绑定位置判断。`MODIFIER_PLAYER_*` 命名（有 TraitModifiers/PolicyModifiers 实例）= 可挂玩家；`MODIFIER_ALLIANCE_*`（仅在 Alliance 表 XML 中）= 只能同盟本身挂。

---

### EFFECT_ADJUST_ALLIANCE_PLAYER_STRENGTH_MODIFIER

调整同盟内单位的战斗力和宗教战斗力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_COMBATS_UNIT_STRENGTHS` | `COLLECTION_ALLIANCE_COMBATS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，战斗力加成。例：5（军事同盟 Lv1 基础值）、10（军事同盟对异教城邦宗教战斗力） |

> **绑定**：同盟限定（仅在 Alliance 表 XML 中，无 TraitModifiers 实例）

---

### EFFECT_ADJUST_ALLIANCE_POINTS_FOR_COMMON_ENEMY_MODIFIER

调整与同盟有共同敌人时每回合获得的同盟点数加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ALLIANCE_POINTS_FOR_COMMON_FOE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每回合额外同盟点数。例：2（领袖特质） |
> **绑定**：可挂玩家（TraitModifiers 有实例）

---

### EFFECT_ADJUST_ALLIANCE_POINTS_FOR_MODIFIER

调整所有同盟每回合获得的同盟点数（泛用加成）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ALLIANCE_POINTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，Amount=4 即 +1 同盟点数/回合，Amount=1 即 +0.25。例：1（Arsenal of Democracy / Democracy / Wisselbanken） |
> **绑定**：可挂玩家（PolicyModifiers + GovernmentModifiers 有实例）

---

### EFFECT_ADJUST_GOVERNOR_ALLIANCE_POINTS

总督能力：为目标城市所在文明的所有同盟增加每回合同盟点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_ALLIANCE_POINTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每回合额外同盟点数。例：2（总督 Ibrahim — Khass Oda Bashi 能力） |

> 仅在 **Gathering Storm (Expansion2)** 及以上版本中可用。需要总督系统的 DLC 支持。
> **绑定**：可挂玩家（GovernorPromotionModifiers 有实例）

---

### EFFECT_ADJUST_PLAYER_ALL_ALLIANCES_PROVIDE_SHARED_VIS

使玩家所有同盟均提供共享视野（无论同盟等级/类型）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ALLIANCES_SHARED_VIS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ShareVis` | **必写** | 布尔值，`1` 启用共享视野。例：1（领袖特质 TRAIT_ALLIANCE_SHARED_VIS） |
> **绑定**：可挂玩家（TraitModifiers 有实例）

---

### EFFECT_ADJUST_PLAYER_ALLIANCE_FAVOR_MULTIPLIER

调整玩家从同盟获得的外交支持（Diplomatic Favor）倍率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ALLIANCE_FAVOR_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，百分比倍率（100 = +100%）。例：100（Popular Front 政策卡，同盟外交支持翻倍） |

> 仅 Gathering Storm 可用。通过同盟获得的**外交支持**百分比加成（成为城邦宗主国也视为同盟）。实例：POLICY_POPULAR_FRONT（Byzantium & Gaul DLC），Amount=100 即外交支持翻倍。
> **绑定**：无 Modifier 实例，存疑

---

### EFFECT_ALLIANCE_CULTURE_SHARING

同盟间通过贸易路线共享文化产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_CULTURE_FROM_ALLY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，共享的文化产出百分比。例：10（文化同盟 Lv1，从盟友贸易路线获得 10% 文化） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_ENVOY_POINTS_FROM_ALLY_TRIBUTARIES

同盟从盟友的城邦附庸（Tributary）获得使者点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_ENVOY_POINTS_FROM_ALLY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每个盟友附庸城邦提供的使者点数。例：1（标准值） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_GRANT_SHARED_VIS

同盟提供共享视野（特定同盟等级效果）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_SHARE_VISIBILITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 纯开关效果，挂上即启用该同盟的共享视野 |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_PRESSURE_FROM_NO_ALLY_RELIGION

减少非盟友宗教对己方城市的宗教压力（强化己方宗教传播）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_RELIGIOUS_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，非盟友宗教压力的减免百分比。例：20（宗教同盟 Lv2，减少 20%） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_RESEARCH_AGREEMENT

同盟研究协定：双方研究同一科技时获得科研加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_RESEARCH_AGREEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，科研加成百分比。例：30（研究同盟 Lv2，+30%） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_SCIENCE_SHARING

同盟间通过贸易路线共享科技产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_SCIENCE_FROM_ALLY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，共享的科技产出百分比。例：10（研究同盟 Lv1，从盟友贸易路线获得 10% 科技） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_SHARE_SUZERAIN

同盟共享城邦宗主国加成（己方获得盟友宗主城邦的使者加成）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_SHARE_SUZERAIN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 纯开关效果，挂上即共享宗主国加成 |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_TOURISM_SHARING

同盟间共享旅游业绩。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_TOURISM_FROM_ALLY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，共享的旅游业绩百分比。例：20（文化同盟 Lv2，+20% 盟友旅游业绩） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

### EFFECT_ALLIANCE_YIELD_INCOME_FROM_ALLY_RELIGION

从追随盟友宗教的己方城市获得额外产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_YIELD_FROM_FOLLOWERS_OF_ALLY_RELIGIONS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每位信徒提供的产出量。例：1 |
| `YieldType` | **必写** | `YIELD_FAITH` / `YIELD_GOLD` / `YIELD_CULTURE` / `YIELD_SCIENCE` 等，引用 [Yields.YieldType]。例：YIELD_FAITH（宗教同盟 Lv1，每个信徒 +1 信仰） |
> **绑定**：同盟限定（仅在 Alliance 表 XML 中）

---

## 注意事项

1. **COLLECTION_ALLIANCE_COMBATS** — `EFFECT_ADJUST_ALLIANCE_PLAYER_STRENGTH_MODIFIER` 是目前列表中唯一使用此 CollectionType 的效果，其余均为 `COLLECTION_OWNER`。该集合作用于同盟内的战斗单位，通常由同盟本身（Alliance 表）直接触发。
2. ~~MODIFIER_ALLIANCE_PLAYER_ADJUST_ALLIANCE_POINTS~~ — 经确认数据库中不存在此变体。
3. **无参数效果** — `EFFECT_ALLIANCE_GRANT_SHARED_VIS` 和 `EFFECT_ALLIANCE_SHARE_SUZERAIN` 无需任何参数，挂上即生效。此类纯开关效果通常搭配 Requirement 控制触发条件（如特定同盟等级）。
4. **相似效果对比**：
   - `EFFECT_ALLIANCE_GRANT_SHARED_VIS` 与 `EFFECT_ADJUST_PLAYER_ALL_ALLIANCES_PROVIDE_SHARED_VIS`：前者为单同盟级共享视野（挂在具体 Alliance 上），后者为玩家级全同盟共享视野（挂在玩家/特质上）。
   - `EFFECT_ALLIANCE_CULTURE_SHARING` / `EFFECT_ALLIANCE_SCIENCE_SHARING` / `EFFECT_ALLIANCE_TOURISM_SHARING`：三者结构完全一致，仅产出一类不同，均通过贸易路线共享。
5. **EFFECT_ADJUST_PLAYER_ALLIANCE_FAVOR_MULTIPLIER** — 仅在 Gathering Storm 中可用（DLC 依赖）。Effects.csv 标记为 UNTESTED，唯一官方案例来自 Byzantium & Gaul 的 POLITICAL_FRONT 政策卡（AMOUNT=100）。
6. **EFFECT_ALLIANCE_YIELD_INCOME_FROM_ALLY_RELIGION** — 唯一一个有 `YieldType` 参数的同盟 EffectType，产出类型可灵活配置。
7. **EFFECT_ADJUST_ALLIANCE_POINTS_FOR_COMMON_ENEMY_MODIFIER vs EFFECT_ADJUST_ALLIANCE_POINTS_FOR_MODIFIER** — 前者只在有共同敌人时生效，后者为无条件泛用加成。注意 Amount 特殊缩放：`Amount=4` 才 +1 同盟点数/回合。
