# modifier-unit-spawn — 单位生成/复制/授予能力类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

### EFFECT_ADJUST_EXTRA_UNIT_COPY

建造指定 UnitType 的单位时，额外获得一份拷贝（买一赠一）。与 `_TAG` 版区别在于本 Effect 绑定具体单位类型。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_UNIT_COPY` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_UNITS_ADJUST_EXTRA_UNIT_COPY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 额外获得的数量，`1` |
| `UnitType` | **必写** | `Units.UnitType`，如 `UNIT_SCYTHIAN_HORSE_ARCHER` |

> **溯源**：斯基泰 — 草原之马（TRAIT_CIVILIZATION_EXTRA_LIGHT_CAVALRY），每训练一个萨卡骑射手，额外获得一匹。ModifierId `TRAIT_EXTRASAKAHORSEARCHER` 使用 `MODIFIER_PLAYER_UNITS_ADJUST_EXTRA_UNIT_COPY`（`COLLECTION_OWNER`）。注意：是训练结束时触发，故训练队列中的第一个单位本身在触发时已存在。

---

### EFFECT_ADJUST_EXTRA_UNIT_COPY_TAG

建造指定兵种标签的单位时，额外获得一份拷贝。与 `_COPY` 版区别在于按 `Tag`（`PromotionClassType` 的 `CLASS_*` 前缀值）匹配，可覆盖整个兵种线。注意 Tag 值取自 `UnitPromotionClasses.PromotionClassType` 但去掉 `PROMOTION_CLASS_` 前缀改为 `CLASS_*`。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_UNIT_COPY_TAG` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_UNITS_ADJUST_EXTRA_UNIT_COPY_TAG` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 额外获得的数量，`1` |
| `Tag` | **必写** | `UnitPromotionClasses.PromotionClassType` 去掉前缀，形如 `CLASS_NAVAL_MELEE`、`CLASS_LIGHT_CAVALRY`。**不是** `PROMOTION_CLASS_*` |

> **溯源**：
> - 威尼斯军械库（BUILDING_VENETIAN_ARSENAL）：3 个 Modifier，分别覆盖 `CLASS_NAVAL_MELEE`、`CLASS_NAVAL_RANGED`、`CLASS_NAVAL_CARRIER`，使用 `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_UNIT_COPY_TAG`（`COLLECTION_PLAYER_CITIES`）
> - 斯基泰 — 草原之马：`CLASS_LIGHT_CAVALRY`，每次训练轻骑兵单位额外获得一匹，使用 `MODIFIER_PLAYER_UNITS_ADJUST_EXTRA_UNIT_COPY_TAG`（`COLLECTION_OWNER`）

---

### EFFECT_GRANT_ABILITY

> **[首选方案]** 给单位批量加效果的标准路径。官方 155 个实例均使用此模式。相比 `EFFECT_ATTACH_MODIFIER` 直挂单位的方式，GRANT_ABILITY 有 UI 显示、Tag 过滤、引擎级生命周期管理等优势。**涉及单位效果时，优先用此方案而非 ATTACH_MODIFIER**。

给单位授予一种能力（`UnitAbility`）。`AbilityType` 和 `ModifierId` 二选一：选 `AbilityType` 引用 `UnitAbilities` 表中的现成能力（主流用法）；选 `ModifierId` 则直接将一个 ModifierId 作为单位能力附加（极少数官方用法，仅 1 例）。

> **Tag 过滤机制**：Ability 通过 TypeTags 绑定 CLASS Tag，**只有同 Tag 的单位才能被授予**。因此给特定兵种（如远程/攻城）发能力时，**无需写 SubjectRequirementSet** 按 PROMOTION_CLASS 筛选——绑好 `CLASS_RANGED`、`CLASS_SIEGE` 等 Tag 即可自动过滤。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_UNITS_GRANT_ABILITY` | `COLLECTION_ALL_UNITS` |
| `MODIFIER_PLAYER_UNITS_GRANT_ABILITY` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_GRANT_ABILITY` | `COLLECTION_OWNER` |
| `MODIFIER_SINGLE_CITY_GRANT_ABILITY_FOR_TRAINED_UNITS` | `COLLECTION_CITY_TRAINED_UNITS` |
| `MODIFIER_PLAYER_TRAINED_UNITS_GRANT_ABILITY` | `COLLECTION_PLAYER_TRAINED_UNITS` |
| `MODIFIER_EMERGENCY_UNITS_GRANT_ABILITY` | `COLLECTION_EMERGENCY_UNITS` |
| `MODIFIER_PLAYER_UNITS_GRANT_ABILITY_GRANCOLOMBIA_MAYA` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AbilityType` | **择一必写** | `UnitAbilities.UnitAbilityType`。引用已定义的完整能力 |
| `ModifierId` | **择一必写** | 直接写入一个 ModifierId 作为能力。唯一官方用法：`GREATPERSON_MOVEMENT_AOE_INFORMATION_SEA` → `ABILITY_GREAT_ADMIRAL_MOVEMENT`（信息时代大提督移动力光环），该例中 ModifierId 本身就是 `ABILITY_*` 前缀的能力标识 |

> **溯源**：
> - `MODIFIER_ALL_UNITS_GRANT_ABILITY`：自然奇观效果 — 珠穆朗玛峰授予邻近单位 `ABILITY_ALTITUDE_TRAINING`（高原训练），马特洪峰授予 `ABILITY_ALPINE_TRAINING`（高山训练），巨人堤授予 `ABILITY_SPEAR_OF_FIONN`，青春之泉授予 `ABILITY_WATER_OF_LIFE`，百慕大三角洲授予 `ABILITY_MYSTERIOUS_CURRENTS`
> - `MODIFIER_PLAYER_UNITS_GRANT_ABILITY`：最广泛（155 例）。建筑类 — 大灯塔（海上移动力+登船能力）、兵马俑（考古学家开放边界）；文明特性 — 挪威-维京（忽略登船消耗+海军近战中立领土回血）；大提督光环 — 阿尔特米西亚至费尔南多，覆盖古典到信息时代，分别授予移动力光环和战斗力光环
> - `MODIFIER_PLAYER_UNIT_GRANT_ABILITY`：伟人激活（10 例），如鲍勃里斯激活给指定单位授予经验值加成。极少数单位晋升树也使用（MOD 内容）
> - `MODIFIER_SINGLE_CITY_GRANT_ABILITY_FOR_TRAINED_UNITS`：军事建筑经验加成 — 兵营、马厩、军械库、军事学院（陆军）；灯塔、造船厂、码头（海军）；机库、机场（空军）。共 28 例。还有特色建筑：皇家海军船坞（英国-移动力加成）、宫廷学园（马其顿-经验）、斡耳朵（蒙古-移动力+经验）
> - `MODIFIER_PLAYER_TRAINED_UNITS_GRANT_ABILITY`：政策卡 — 警卫专精（近战+7力）、狙击专精（远程+1射程）、教官（军事单位+25%经验）。MOD 内容也有使用
> - `MODIFIER_EMERGENCY_UNITS_GRANT_ABILITY`：仅 1 例 — 间谍紧急事件（SPYING_EMERGENCY_MEMBER_GRANT_ABILITY_BUFF），给紧急事件参与者间谍单位附加 Buff
> - `MODIFIER_PLAYER_UNITS_GRANT_ABILITY_GRANCOLOMBIA_MAYA`：DLC 专属，2 例 — 哥伦比亚-爱国军（+1 移动力）、玛雅-穆塔尔城邦之女（首都附近城市获得能力）

---

### EFFECT_GRANT_UNIT_BY_CLASS

在城中生成指定晋升兵种的单位。与 `EFFECT_GRANT_UNIT_IN_CITY` 的关键区别：本 Effect 只指定 `UnitPromotionClassType`（兵种线），游戏自动挑选该兵种当前时代可用的最强 `UnitType`。无需指定具体单位。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_GRANT_UNIT_BY_CLASS` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_GRANT_UNIT_BY_CLASS_IN_NEAREST_CITY` | `COLLECTION_UNIT_NEAREST_OWNER_CITY` |
| `MODIFIER_EMERGENCY_PLAYERS_GRANT_UNIT` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitPromotionClassType` | **必写** | `UnitPromotionClasses.PromotionClassType`，如 `PROMOTION_CLASS_RECON`、`PROMOTION_CLASS_MELEE`、`PROMOTION_CLASS_SPY` |

> **溯源**：
> - 维多利亚 — 英国强权下的和平（TRAIT_LEADER_PAX_BRITANNICA）：2 个 Modifier 使用 `MODIFIER_PLAYER_CITIES_GRANT_UNIT_BY_CLASS`（`COLLECTION_PLAYER_CITIES`）。`TRAIT_FREE_MELEE_UNIT_NON_HOME_CONTINENT`：在非原始首都所在大陆建城时获赠一个近战单位（`PROMOTION_CLASS_MELEE`）；`TRAIT_FREE_MELEE_UNIT_FOREIGN_ROYAL_NAVY_DOCKYARD`：在外国城市建造皇家海军船坞后获赠一个近战单位。此 ModifierType 数据库中无运行时实例（XML-only）
> - 部落村庄奖励：`GOODY_MILITARY_GRANT_SCOUT` 使用 `MODIFIER_SINGLE_CITY_GRANT_UNIT_BY_CLASS_IN_NEAREST_CITY`，在最近城市生成侦察兵（`PROMOTION_CLASS_RECON`）
> - 间谍紧急事件：`SPYING_EMERGENCY_TARGET_GRANT_SPY_REWARD` 使用 `MODIFIER_EMERGENCY_PLAYERS_GRANT_UNIT`，为紧急事件靶标方奖励一个间谍（`PROMOTION_CLASS_SPY`）

---

### EFFECT_GRANT_UNIT_BY_DOMAIN

在城中生成指定域（陆/海/空）的单位。游戏自动选取该域当前可用的单位。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_GRANT_UNIT_BY_DOMAIN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitDomain` | **必写** | `Domains.DomainType`，如 `DOMAIN_LAND` / `DOMAIN_SEA` / `DOMAIN_AIR` |

> **溯源**：伟人大将军安东尼奥·何塞·苏克雷（COMMANDANTE_JOSE_DE_SUCRE），激活后在最近城市生成一个陆地单位（`DOMAIN_LAND`）。
>
> 仅 Gathering Storm (XP2) 可用。数据库中仅 1 例。

---

### EFFECT_GRANT_UNIT_IN_CITY

在城中生成指定 `UnitType` 的确定单位。与 `EFFECT_GRANT_UNIT_BY_CLASS` 的关键区别：本 Effect 直接指定具体 `UnitType`，不依赖兵种线自动选择。可搭配 `AllowUniqueOverride` 自动将普通单位替换为文明特色单位。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_PLAYER_CITIES_GRANT_UNIT_IN_CITY` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY` | `COLLECTION_OWNER` |
| `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_NEAREST_CITY` | `COLLECTION_UNIT_NEAREST_OWNER_CITY` |
| `MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_UNIT` | `COLLECTION_PLAYER_BUILT_CITIES` |
| `MODIFIER_EMERGENCY_CAPITALS_GRANT_UNIT` | `COLLECTION_EMERGENCY_CAPITAL_CITIES` |
| `MODIFIER_PLAYER_CITIES_GRANT_UNIT_IN_CITY_GRANCOLOMBIA_MAYA` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitType` | **必写** | `Units.UnitType`，如 `UNIT_BUILDER`、`UNIT_SPY`、`UNIT_TRADER` |
| `Amount` | **必写** | 生成数量，`1` |
| `AllowUniqueOverride` | 可写 | `Boolean`，是否允许被文明特色单位替换。不写默认 `false`。设为 `1`/`true` 则若玩家在该兵种线拥有特色单位会自动生成特色单位 |

> **溯源**（按 ModifierType）：
> - `MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL`（7 例）：维多利亚特质 `FLYING_SQUADRON_TRAIT` 赠送间谍；克里-林地克里族（`TRAIT_CIVILIZATION_CREE_TRADE_GAIN_TILES`）赠送商队；武则天-罗织经（`TRAIT_LEADER_WU_ZETIAN`）赠送间谍；MOD 内容 — 情报站改良设施赠送商队
> - `MODIFIER_PLAYER_CITIES_GRANT_UNIT_IN_CITY`（1 例）：西班牙-财宝舰队（`TRAIT_CIVILIZATION_TREASURE_FLEET`），跨大陆建城时赠送一个建造者
> - `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_CITY`（27 例）：奇迹/建筑类最集中 — 巨像送商队、金字塔送建造者、宙斯像送 3 个枪兵+3 个弓手+1 个投石车、巨石阵送大预言家、摩诃菩提寺送 2 个使徒、米纳克希神庙送 2 个古鲁、高德院送 4 个武僧、情报局送 1 个间谍、草药屋（挪威）送 1 个狂战士。大商人 — 马可波罗、郑和各送商队
> - `MODIFIER_SINGLE_CITY_GRANT_UNIT_IN_NEAREST_CITY`（4 例）：部落村庄奖励 — `GOODY_SURVIVORS_GRANT_BUILDER` 在最近城市赠送建造者；大商人 — 安东尼奥·纳里诺赠送商队
> - `MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_UNIT`（2 例）：总督建筑-祠堂（BUILDING_GOV_WIDE），移民新建城市时赠送建造者；毛利-库佩的远航（`TRAIT_LEADER_KUPES_VOYAGE`），初始赠送建造者
> - `MODIFIER_EMERGENCY_CAPITALS_GRANT_UNIT`：数据库无运行时实例。XML 定义用于预言者紧急事件（Soothsayer），仅 XP2。参数标注 UNTESTED
> - `MODIFIER_PLAYER_CITIES_GRANT_UNIT_IN_CITY_GRANCOLOMBIA_MAYA`（1 例）：玛雅-穆塔尔城邦之女（`TRAIT_LEADER_MUTAL`），在首都附近城市赠送建造者

---

### EFFECT_GRANT_UNIT_IN_EACH_DISTRICT

在每个区域中生成一个指定单位。数量 = 拥有者的区域数量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GRANT_UNITS_IN_DISTRICTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitType` | **必写** | `Units.UnitType`，如 `UNIT_MUSKETMAN` |
| `UniqueOverride` | 可写 | `Boolean`，是否允许被文明特色单位替换 |
| `IgnoreDefensible` | 可写 | `Boolean`，`1` 则跳过防御型区域（如军营/马厩）。仅 1 例官方用法使用此参数 |

> **溯源**：伟人大将军图帕克·阿马鲁（`GREAT_PERSON_INDIVIDUAL_TUPAC_AMARU`），激活后在每个区域生成一个火枪手（`UNIT_MUSKETMAN`），启用 `UniqueOverride` 且跳过防御型区域（`IgnoreDefensible=1`）。仅 1 例。

---

### EFFECT_GRANT_UNIT_OF_CLASS_AND_APPLY_ABILITY

生成指定兵种的高级单位，同时给这个新单位附加一个 ModifierId 作为能力。相当于"按兵种生成单位"+"授予能力"的合体版，避免拆成两个 Modifier。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_ADVANCED_UNIT_OF_CLASS_IN_NEAREST_OWNER_CITY_AND_APPLY_ABILITY` | `COLLECTION_UNIT_NEAREST_OWNER_CITY` |
| `MODIFIER_PLAYER_GRANT_UNIT_OF_ABILITY_WITH_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitPromotionClassType` | **必写** | `UnitPromotionClasses.PromotionClassType`，如 `PROMOTION_CLASS_HEAVY_CAVALRY`、`PROMOTION_CLASS_NAVAL_MELEE` |
| `ModifierId` | **必写** | 要附加到生成单位的 ModifierId。该 Modifier 作为"能力"直接挂在生成单位上 |

> **溯源**：
> - 部落村庄奖励 — 陨石坑：`GOODY_METEOR_FREE_UNIT` 使用 `MODIFIER_PLAYER_GRANT_ADVANCED_UNIT_OF_CLASS_IN_NEAREST_OWNER_CITY_AND_APPLY_ABILITY`，生成重骑兵（`PROMOTION_CLASS_HEAVY_CAVALRY`）并附加 `GOODY_METEOR_UNIT_REFUND_COST`（退还建造费用）
> - 伟人大提督航海家汉诺（`GREAT_PERSON_INDIVIDUAL_HANNO_THE_NAVIGATOR`）：激活后生成近战海军（`PROMOTION_CLASS_NAVAL_MELEE`）并附加 `HANNO_FREE_UNIT_MOVEMENT_BUFF`（额外移动力加成）
>
> 仅 Gathering Storm (XP2) 可用。两个 ModifierType 各 1 例。

---

### EFFECT_GRANT_UNIT_TYPE_UNLIMITED_PROMOTION_CHOICES

指定 `UnitType` 的晋升可以从所有可用晋升中自由选择，而非从当前晋升树的随机子集中抽取。效果等价于耶烈万城邦使徒的"允许选择任何可用的晋升"。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_GRANT_UNLIMITED_PROMOTION_CHOICES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitType` | **必写** | `Units.UnitType`，如 `UNIT_APOSTLE`、`UNIT_SPY` |

> **溯源**：
> - 耶烈万城邦（`MINOR_CIV_YEREVAN`）：授予使徒（`UNIT_APOSTLE`）无限制晋升选择权
> - 未来政策 — 摇滚主义（`POLICY_FUTURE_VICTORY_CULTURE`）：使摇滚乐队（Rock Band）可选择任何可用晋升
> - 未来政策 — 反制科学行为（`POLICY_FUTURE_COUNTER_SCIENCE`）：使间谍（Spy）可选择任何可用晋升

---

### EFFECT_GRANT_UNIT_WITH_EXPERIENCE

授予一个指定类型的单位，同时设定该单位的初始经验值。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_GRANT_UNIT_WITH_EXPERIENCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitType` | **必写** | `Units.UnitType`，如 `UNIT_QUADRIREME` |
| `Experience` | **必写** | `Integer`。`0` = 无初始经验，`-1` = 刚好够升一级的经验量 |
| `UniqueOverride` | 可写 | `Boolean`，是否允许被文明特色单位替换 |

> **溯源**：几乎全部为伟人大提督/大将军激活效果（11 例）。如地米斯托克利（`GREATPERSON_THEMISTOCLES_ACTIVE`）：赠送一艘四段帆船（`UNIT_QUADRIREME`），`Experience=0`，`UniqueOverride=1`。李舜臣：赠送装甲舰，`Experience=-1`（刚好够升一级）。其余使用者包括：古斯塔夫·阿道弗斯、弗朗茨·希佩尔、道格拉斯·麦克阿瑟、詹西女王、艾哈迈德·沙哈·马苏德、萨莫里·杜尔、丹达拉、切斯特·尼米兹（单位晋升选项版）、弗朗西斯·德雷克。

---

### EFFECT_GRANT_UNIT_YIELD_ADJACENT_FEATURES

伟人（大科学家）激活消耗时，根据与其所在单元格相邻的特定地貌获得一笔一次性产出。**Amount 参数类型为 `ScaleByGameSpeed`**，产出量随游戏速度缩放。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_GRANT_ADJACENT_FEATURE_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每格产出值。**类型 `ScaleByGameSpeed`**（在 `ModifierArguments.Type` 中设为 `"ScaleByGameSpeed"`）。官方典型值 `400` |
| `FeatureType` | **必写** | `Features.FeatureType`，如 `FEATURE_JUNGLE` |
| `YieldType` | **必写** | `Yields.YieldType`，如 `YIELD_SCIENCE` |

> **溯源**：佳纳克伊·安马尔（大科学家）：激活时根据相邻雨林（`FEATURE_JUNGLE`）格数，每格获得 400（游戏速度缩放后）的 `YIELD_SCIENCE`。ModifierId `GREATPERSON_ADJACENT_RAINFOREST_SCIENCE`。

---

### EFFECT_GRANT_UNIT_YIELD_ADJACENT_NATURAL_WONDERS

伟人（大科学家）激活消耗时，根据与其所在单元格相邻的自然奇观获得一笔一次性产出。**无需指定具体自然奇观类型**，相邻任何自然奇观即触发。**Amount 参数类型为 `ScaleByGameSpeed`**。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_GRANT_ADJACENT_NATURAL_WONDER_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每格产出值。**类型 `ScaleByGameSpeed`**。官方典型值 `500` |
| `YieldType` | **必写** | `Yields.YieldType`，如 `YIELD_SCIENCE` |

> **溯源**：查尔斯·达尔文（大科学家）：激活时根据相邻自然奇观格数，每格获得 500（游戏速度缩放后）的 `YIELD_SCIENCE`。ModifierId `GREATPERSON_ADJACENT_NATURALWONDER_SCIENCE`。

---

### EFFECT_GRANT_UNIT_YIELD_ADJACENT_TERRAINS

伟人（大科学家）激活消耗时，根据与其所在单元格相邻的特定地形获得一笔一次性产出。**Amount 参数类型为 `ScaleByGameSpeed`**。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_GRANT_ADJACENT_TERRAIN_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每格产出值。**类型 `ScaleByGameSpeed`**。官方典型值 `250` |
| `TerrainType` | **必写** | `Terrains.TerrainType`，如 `TERRAIN_GRASS_MOUNTAIN`、`TERRAIN_DESERT_MOUNTAIN` |
| `YieldType` | **必写** | `Yields.YieldType`，如 `YIELD_SCIENCE` |

> **溯源**：伽利略·伽利雷（大科学家）：5 个 Modifier 分别对应 5 种山地形（草原山 `TERRAIN_GRASS_MOUNTAIN`、平原山 `TERRAIN_PLAINS_MOUNTAIN`、沙漠山 `TERRAIN_DESERT_MOUNTAIN`、冻土山 `TERRAIN_TUNDRA_MOUNTAIN`、雪地山 `TERRAIN_SNOW_MOUNTAIN`），每格获得 250（游戏速度缩放后）的 `YIELD_SCIENCE`。ModifierId 分别为 `GREATPERSON_ADJACENT_GRASSMOUNTAIN_SCIENCE` 等。

---

### EFFECT_UNIT_TELEPORT

将满足条件的单位随机传送到地图另一处。**仅 1 例官方实例**。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_UNIT_TELEPORT` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `MinRange` | 可写 | `Integer`，最小传送距离 |
| `MaxRange` | 可写 | `Integer`，最大传送距离 |

> **溯源**：百慕大三角洲（`FEATURE_BERMUDA_TRIANGLE`）自然奇观。通过 `GameModifiers` 表挂载 `BERMUDA_TRIANGLE_TELEPORT`，当单位满足 `UNIT_ENTERS_BERMUDA_TRIANGLE` 条件时传送到地图远处（`Permanent=1, Repeatable=1`）。官方将传送功能绑定在百慕大三角洲自身的 game-level Modifier 上，不通过传统 Trait/Building 等上游挂载。

---

### EFFECT_UNIT_TRANSFER_CITY_AS_GIFT_AND_APPLY_MODIFIER

将该单位所在城市作为礼物转让给另一个文明，同时附加一个 Modifier。**角色为伟人大商人激活效果。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_UNIT_ABSORB_CITY_STATE_AS_GIFT_AND_APPLY_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ModifierId` | **必写** | 转让后要附加到目标城市的 ModifierId |

> **溯源**：斯坦福·莱佛士（伟人大商人）：激活后将该城邦城市作为礼物并入本国领土，同时附加 `GREATPERSON_CITY_STATE_ABSORB_EXPANSIONS_LOYALTY_ATTACHMENT` 为该城市提供忠诚度修正，防止城市因忠诚度压力叛变。仅 1 例。

---

## 注意事项

- **EFFECT_ADJUST_EXTRA_UNIT_COPY vs _TAG**：`_COPY` 用 `UnitType` 指定单一单位；`_COPY_TAG` 用 `Tag` 指定整个兵种线。Tag 值来自 `UnitPromotionClasses.PromotionClassType`，但前缀为 `CLASS_*` 而非 `PROMOTION_CLASS_*`（如 `CLASS_NAVAL_MELEE` 而非 `PROMOTION_CLASS_NAVAL_MELEE`）。

- **EFFECT_GRANT_UNIT_IN_CITY vs EFFECT_GRANT_UNIT_BY_CLASS**：`IN_CITY` 指定具体 `UnitType` 生成固定单位（可搭配 `AllowUniqueOverride` 自动替换特色单位）；`BY_CLASS` 指定 `UnitPromotionClassType`，游戏自动挑选该兵种当前时代的最强单位。按兵种生成不会过时，按单位生成则可能落后时代。

- **EFFECT_GRANT_ABILITY 的双参数选择**：`AbilityType` 和 `ModifierId` 二选一。主流用法是 `AbilityType`（引用 `UnitAbilities` 表）。直接用 `ModifierId` 仅 1 例官方用法（信息时代大提督移动力光环）。

- **EFFECT_GRANT_UNIT_OF_CLASS_AND_APPLY_ABILITY**：合体效果 — 同时"按兵种生成单位"并"附加一个 ModifierId 作为能力"，避免拆成两个独立的 Modifier。仅 XP2 可用。

- **EFFECT_GRANT_UNIT_WITH_EXPERIENCE 的 Experience=-1**：含义为"刚好够升 1 级的经验"，常用于伟人大提督/大将军激活效果。`0` 表示无初始经验。

- **EFFECT_GRANT_UNIT_IN_EACH_DISTRICT 的 IgnoreDefensible**：设为 `1` 可跳过防御型区域（军营、马厩等），避免在这些区域中生成的单位因区域防御特性产生意外效果。

- **产出相邻类三兄弟**：`_FEATURES` / `_NATURAL_WONDERS` / `_TERRAINS` 的 `Amount` 参数类型均为 `ScaleByGameSpeed`。在 `ModifierArguments` 表中需将 `Type` 设为 `"ScaleByGameSpeed"` 而非 `"ARGTYPE_IDENTITY"`，否则产出量不会随游戏速度缩放。

- **EFFECT_GRANT_UNIT_YIELD_ADJACENT_NATURAL_WONDERS 无需指定具体自然奇观**：只要相邻任何自然奇观即触发，效果覆盖全部自然奇观类型。

- **EFFECT_UNIT_TELEPORT**：数据库中仅 1 例（百慕大三角洲），通过 `GameModifiers` 表而非传统上游挂载。参数标注 UNTESTED，不推荐在普通 Mod 中使用。

- **交叉引用**：`modifier-unit-combat.md` 中另含 4 个 spawn 类 EffectType：`EFFECT_ADJUST_PLAYER_DISTRICT_CREATE_UNIT`、`EFFECT_ADJUST_PLAYER_DISTRICT_AND_BUILDINGS_CREATE_UNIT_WITH_ABILITY_BY_CLASS`、`EFFECT_DISTRICT_ADD_NAVAL_UNIT`、`EFFECT_ADD_RELIGIOUS_UNIT`。完整单位生成效果请同时参考该文件。
