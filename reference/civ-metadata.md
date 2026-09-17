← 返回 `SKILL.md` 路由

> **来源**：2026-09-17 对照第三方教程《Civ6 Modding Textbook》第 10 章补齐，schema 与取值域
> 全部取自本 skill 自带的 `database/DebugGameplay.sqlite` 实测（行数见表）。
> 适用场景：新文明/新领袖**收尾阶段**——百科资料卡、城市名、市民名、出生关联、
> BGM 开关、知名地名。这些表**不影响玩法能否运行**，但缺了会让文明"不完整"
> （百科空白、城市名是 `LOC_...`、没有出生倾向）。

# 文明周边数据（Civ Metadata）

## 一、总览：6 类表

| 类别 | 表 | 作用 | 缺了会怎样 |
|---|---|---|---|
| 百科资料卡 | `CivilizationInfo` | 文明百科页的 4 栏（位置/大小/人口/首都） | 百科页该区块空白 |
| 城市名 | `CityNames` | 建城时按序取名 | 城市叫 `LOC_CITY_NAME_...` |
| 市民名 | `CivilizationCitizenNames` | 城市人口姓名池 | 市民无名字 |
| 出生关联 | `StartBiasTerrains` / `StartBiasResources` / `StartBiasFeatures` | 出生点偏好 | 出生点随机，不贴合文明设定 |
| BGM 开关 | `CivilizationAudioTags` | 是否用 mod 自带 BGM 覆盖 artdef 音乐 | 无法让自定义 BGM 生效 |
| 知名地名 | `NamedMountains`/`NamedRivers`/`NamedDeserts`/`NamedLakes`/`NamedSeas`/`NamedVolcanoes` + 各自 `*Civilizations` | 附近地形用你的命名 | 用原版默认地名 |

> **注册环境**：`CivilizationInfo`/`CityNames`/`CivilizationCitizenNames`/`StartBias*` 属
> **InGame**（`UpdateDatabase`）；`Civilizations`/`CivilizationAudioTags` 同时也在 Config，
> 参见 `project-setup.md` 的「文件类型 → 注册位置对照表」。
> **知名地名 5 组（含 Continent）是风云变幻（XP2）内容**，写进 `Expansion2.xml` 或
> 用 `<Criteria>` 限定 `RULESET_EXPANSION_2`。

---

## 二、`CivilizationInfo` —— 百科资料卡

**列**：`CivilizationType` | `Header` | `Caption` | `SortIndex`（实测原版 **200 行** = 50 个文明 × 4 栏）

固定 **4 栏**，`Header` 是**固定 tag**（原版共用），`Caption` 才是你这个文明自己的文案：

```xml
<CivilizationInfo>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" Header="LOC_CIVINFO_LOCATION"   Caption="LOC_CIVINFO_RAGUNNA_QYQXP_LOCATION"   SortIndex="10"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" Header="LOC_CIVINFO_SIZE"       Caption="LOC_CIVINFO_RAGUNNA_QYQXP_SIZE"       SortIndex="20"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" Header="LOC_CIVINFO_POPULATION" Caption="LOC_CIVINFO_RAGUNNA_QYQXP_POPULATION" SortIndex="30"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" Header="LOC_CIVINFO_CAPITAL"    Caption="LOC_CIVINFO_RAGUNNA_QYQXP_CAPITAL"    SortIndex="40"/>
</CivilizationInfo>
```

- 4 个 `Header` 是**原版现成 tag**，**直接复用、不要翻译**：
  `LOC_CIVINFO_LOCATION` / `LOC_CIVINFO_SIZE` / `LOC_CIVINFO_POPULATION` / `LOC_CIVINFO_CAPITAL`
- `SortIndex` 用 10/20/30/40（原版一致）；顺序即百科页显示顺序
- `Caption` 需自己在 `Text/*.sql` 写 8 语言文案

---

## 三、`CityNames` —— 城市名池

**列**：`ID` | `CivilizationType` | `LeaderType` | `ContinentType` | `CityName` | `SortIndex`
（实测原版 **1677 行** / ID 1..1705）

```xml
<CityNames>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" CityName="LOC_CITY_NAME_RAGUNNA_QYQXP_1"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" CityName="LOC_CITY_NAME_RAGUNNA_QYQXP_2"/>
</CityNames>
```

**要点**（关于顺序，实测结论与直觉不同）：

- **顺序由 `ID`（插入序）决定，不是 `SortIndex`**：原版 **1677 行的 `SortIndex` 全为 0**；
  而 `ID` 1、2、3… 恰好对应 American 的 Washington → New York → Philadelphia。
  → **写 `Row` 时保持你想要的顺序即可**，别指望靠 `SortIndex` 排序。
- **不必填 `ID`**（自增）。`LeaderType` / `ContinentType` **原版全部为 NULL**
  （1677/1677）——是可选列，**留空即可**。
- 引擎从**未使用**的前 `RandomCityNameDepth` 个名字里随机挑，**越靠前概率越大**。
- **各领袖的首都名也要放进来**（`CivilizationLeaders.CapitalName` 用的 tag
  最好也在 `CityNames` 里出现一次）。
- 借用的名字（如共用 `LOC_CITY_NAME_PAWTIMORE`）在地图上**只出现一次**。
- 用 `INSERT OR IGNORE` 而非 `Row`，可避免重名冲突直接报错（教程推荐）。

> **数量建议**：实测 50 个主要文明（`CityNames` >5 条者）的**中位条数是 31.5**，
> 最多 41（越南/加拿大）。**建议 ≥30 条**。
> （注意：城邦与 Free Cities 等只有 1 条，不属于主要文明，别拿来当参考。）

---

## 四、`CivilizationCitizenNames` —— 市民名池

**列**：`CivilizationType` | `CitizenName` | `Female` | `Modern`（实测原版 **2002 行**）

```xml
<CivilizationCitizenNames>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" CitizenName="LOC_CITIZEN_RAGUNNA_QYQXP_MALE_1"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" CitizenName="LOC_CITIZEN_RAGUNNA_QYQXP_MODERN_MALE_1" Modern="true"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" CitizenName="LOC_CITIZEN_RAGUNNA_QYQXP_FEMALE_1"      Female="true"/>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" CitizenName="LOC_CITIZEN_RAGUNNA_QYQXP_MODERN_FEMALE_1" Modern="true" Female="true"/>
</CivilizationCitizenNames>
```

- `Female` / `Modern` 是**布尔列**（实测存 0/1，缺省即 0/false）
- **`Modern` = 仅游戏后期出现**（不是"现代名"的字面意思，是"后期才进池"）
- **数量建议**：实测原版**主要文明几乎全是 40 条**（France 42，其余 40），
  即四类各 10 个（前期男 / 前期女 / 后期男 / 后期女）——**写 40 条**
- 命名里**带上文明名**避免跨 mod 冲突

---

## 五、出生关联 `StartBias*`

**列**：`CivilizationType` | `<Terrain|Resource|Feature>Type` | `Tier`

```xml
<StartBiasTerrains>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" TerrainType="TERRAIN_PLAINS_HILLS" Tier="2"/>
</StartBiasTerrains>
<StartBiasResources>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" ResourceType="RESOURCE_AMBER" Tier="1"/>
</StartBiasResources>
```

- **`Tier` 取值 1–5，数字越小关联越紧密**（原版实测：Terrains 用到 1–5；Resources 用 2/5；Features 用 1/2/3/5）
- 可配合 `RandomCityNameDepth`（在 `Civilizations` 表）：

```xml
<Civilizations>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" ... RandomCityNameDepth="10" Ethnicity="ETHNICITY_EURO"/>
</Civilizations>
```

- **`RandomCityNameDepth` 原版只有两个值：`10`（50 个主要文明）与 `1`（约 55 个城邦/蛮族/自由城市）**。
  → **主要文明一律填 10**。
- **`Ethnicity` 取值域（原版实测，恰 5 个）**：
  `ETHNICITY_EURO` / `ETHNICITY_MEDIT` / `ETHNICITY_SOUTHAM` / `ETHNICITY_ASIAN` / `ETHNICITY_AFRICAN`
  （留空 = 默认）。它决定**单位头像的种族外观**。

---

## 六、`CivilizationAudioTags` —— BGM 覆盖开关

**列**：`CivilizationType` | `MusicOverride`（实测原版 **15 行**，`MusicOverride` 全为 `1`）

```xml
<CivilizationAudioTags>
  <Row CivilizationType="CIVILIZATION_RAGUNNA_QYQXP" MusicOverride="1"/>
</CivilizationAudioTags>
```

- `MusicOverride=1` → 使用 **mod 自带 BGM**，并让 `Civilizations.artdef` 里
  配置的官方 BGM 引用**失效**（即从"借用原版音乐"切到"自己的音乐"）
- **只有 15 个原版文明有这一行**（America / Byzantium / China / Egypt / England /
  Germany / Japan / Kongo / Korea / Mali / Norway / Persia / Portugal / Rome / Vietnam
  ——即"有自定义 BGM 的那批"），其余 90 个文明**不写**。
- → **只在有自定义 BGM 时写**；没有自定义音乐就**不要写**

---

## 七、知名地名（风云变幻）

**共 7 类地形**，各有「定义表 + 关联表」（实测行数）：

| Kind | 定义表 | 关联表 | 行数（定义/关联） |
|---|---|---|---|
| `KIND_NAMED_MOUNTAIN` | `NamedMountains` | `NamedMountainCivilizations` | 227 / 260 |
| `KIND_NAMED_RIVER` | `NamedRivers` | `NamedRiverCivilizations` | 288 / 324 |
| `KIND_NAMED_DESERT` | `NamedDeserts` | `NamedDesertCivilizations` | 55 / 55 |
| `KIND_NAMED_LAKE` | `NamedLakes` | `NamedLakeCivilizations` | 294 / 314 |
| `KIND_NAMED_SEA` | `NamedSeas` | `NamedSeaCivilizations` | 199 / 278 |
| `KIND_NAMED_VOLCANO` | `NamedVolcanoes` | `NamedVolcanoCivilizations` | 143 / 133 |
| `KIND_NAMED_OCEAN` | `NamedOceans` | `NamedOceanCivilizations` | 9 / **0** |

> 注意最后一行是 **`NamedOceans`（复数 Ocean）**，且原版**没有任何文明关联**它
> （`NamedOceanCivilizations` 0 行）—— 写 `NamedOcean` 会找不到表。

**三步式写法**（以山脉为例）：

```xml
<!-- ① 声明 Kind -->
<Types>
  <Row Type="NAMED_MOUNTAIN_KITTY_MOUNTAINS" Kind="KIND_NAMED_MOUNTAIN"/>
</Types>

<!-- ② 定义名字 -->
<NamedMountains>
  <InsertOrIgnore NamedMountainType="NAMED_MOUNTAIN_KITTY_MOUNTAINS"
                  Name="LOC_NAMED_MOUNTAIN_KITTY_MOUNTAINS_NAME"/>
</NamedMountains>

<!-- ③ 关联到文明 -->
<NamedMountainCivilizations>
  <InsertOrIgnore NamedMountainType="NAMED_MOUNTAIN_KITTY_MOUNTAINS"
                  CivilizationType="CIVILIZATION_RAGUNNA_QYQXP"/>
</NamedMountainCivilizations>
```

- **`KIND_NAMED_*` 必须先在 `Types` 声明**（漏了则整行静默丢弃 —— 用
  `check_types_kinds.py` 可查；合法枚举共 7 个，见上表首列）
- 关联用 **`InsertOrIgnore`**（重名不报错，符合"地名池"语义）
- **是 XP2 内容**：原版由 `DLC/Expansion2/Data/Expansion2_NamedPlaces.xml` 及
  各 DLC 的 `*_Expansion2.xml` 提供（`Babylon` 走 `_Expansion1`）
  → 写进 `Expansion2.xml` 或用 `RuleSetInUse` 判据限定。

---

## 八、最小检查清单

新增文明收尾时，逐项确认：

- [ ] `CivilizationInfo` 4 行（Header 复用原版 4 tag、SortIndex 10/20/30/40）
- [ ] `CityNames` ≥30 条（原版主要文明中位 31.5），含各领袖首都名；**顺序按 `Row` 书写序，`SortIndex` 原版全 0 不必填**
- [ ] `CivilizationCitizenNames` 40 条（四类各 10）
- [ ] `StartBias*` 按设定填（`Tier` 1–5，越小越紧）
- [ ] `Civilizations.Ethnicity` 填 5 选 1（影响单位头像）、`RandomCityNameDepth=10`
- [ ] `CivilizationAudioTags` **仅在有自定义 BGM 时**填 `MusicOverride=1`
- [ ] 知名地名（XP2）若要，定义表 + 关联表齐全，且 `KIND_NAMED_*` 已在 `Types` 声明
- [ ] **所有 `LOC_*` tag 在 8 语言 `Text/*.sql` 都有文案**（缺则显示原始 key）

> 校验：`python <skill>/scripts/rgn_validate_runner.mjs <Data 目录>` 查悬空引用；
> `python <skill>/scripts/check_types_kinds.py <工程>` 查 Kind 是否合法枚举。
