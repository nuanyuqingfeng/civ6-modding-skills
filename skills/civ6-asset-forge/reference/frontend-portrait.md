← 返回 `SKILL.md` 路由

> **来源**：2026-09-19 对「原版环境下的领袖前景 / 背景」的专项补齐。
> 起因是一次真实误判——把 Suk 适配（**可选分支**）当成了 FrontEnd 立绘的全部，
> 而**原版环境**下 FrontEnd 的立绘与背景才是**必需**的。相关证据全部来自引擎源码
> （`Base/Assets/UI/**`）与官方数据库快照（`civ6-modding/database/DebugConfiguration.sqlite` /
> `DebugGameplay.sqlite`），**逐条实测，非推测**。

# 原版环境：领袖前景（立绘）与背景（三环境对照）

## 〇、先分清「三套环境」——本类最大的误判源

「领袖前景 / 背景」在 Civ6 里是**三套互不相同的通道**，各有自己的**数据表、回退规则、XLP、尺寸**。
混为一谈必然出「图做了但游戏里不显示」。

| | **环境 A：FrontEnd（选人 / 游戏设置）** | **环境 B：加载界面（LoadScreen）** | **环境 C：InGame 外交** |
|---|---|---|---|
| 数据表 | `Players`（**Config 库**） | `LoadingInfo`（**Gameplay 库**） | `DiplomacyInfo`（Gameplay）+ `Leaders.SceneLayers` |
| 前景列 | `Portrait` | `ForegroundImage` | 无贴图列（3D 模型；缺资源时用 `FallbackLeaderImage`） |
| 背景列 | `PortraitBackground` | `BackgroundImage` | `BackgroundImage`（整图，**压过**分层） |
| 引擎读法 | `PlayerSetupLogic.lua:553`（查询）→ `:807-829`（赋值） | `LoadScreen.lua:209-220`（背景）、`:240-249`（前景） | `LeaderScene.lua:61-79` |
| **前景回退** | 空 → `<LeaderType>_NEUTRAL` | 空 → `<LeaderType>_NEUTRAL` | —（3D 模型 / Fallback 图） |
| **背景回退** | 空 → `<LeaderType>_BACKGROUND` | 空 → `<LeaderType>_BACKGROUND` → 再失败**强制** `LEADER_T_ROOSEVELT_BACKGROUND` | `DiplomacyInfo` 无行 → `<X>_1..4`；`SceneLayers=0` → 强制 `CLEOPATRA` 4 层 |
| 注册 XLP | `UI_Leaders.xlp`（`UITexture`；官方 22 条，其中 20 条 `LEADER_*_NEUTRAL`） | `Shell_Loading.xlp`（`UITexture`；官方 24 条含 2 条别名） | `UI_LeaderScenes.xlp`（`UITexture`）/ `LeaderFallbackImages.xlp`（`LeaderFallback`） |
| 贴图尺寸 | 前景高 **1024/1080**（宽 389~803）；背景 **1920×960** | 同左（与 A 共用同一批贴图） | 背景随源图；层 1–3 `960×505`、层 4 `1920×1010` |
| 是否必需 | ★ **必需** | 可选（不填即回退） | ★ 必需 |

> **A 与 B 共用同一批贴图名**：`LEADER_<X>_NEUTRAL` / `LEADER_<X>_BACKGROUND`。
> 区别只在**读它的表**不同（Config vs Gameplay），以及**没填时的兜底行为**不同。
> 所以做一套素材可以同时喂 A 和 B；但**两边的数据行必须分别写**（不同库、不同 Action 段）。

**与环境 C 的关系**：环境 C 是**外交场景**（三条链见 `civ6-modding/art-pipeline.md` §三.1）。
本文件**不重复**该内容，只做交叉引用；A/B 与 C 的贴图名**互不通用**。

**与 Suk（本 skill 类别⑤）的关系**：Suk 是**第三方界面替换**，它改写的是**环境 A 的两列**
（`Players.Portrait` / `PortraitBackground`），且**只在 Suk 启用时生效**（`Criteria` 门控）。
即：

- **原版 FrontEnd（本文件）= 必需**；**Suk 适配 = 可选分支**。
- 未启用 Suk 时，走的就是本文件这一套；**两套必须都能跑**，不能只做 Suk。

---

## 一、环境 A：FrontEnd 选人 / 游戏设置的立绘与背景

### 1.1 数据：`Players` 两列（Config 库）

```sql
-- Config 库（FrontEndActions → UpdateDatabase）
SELECT ... Portrait, PortraitBackground ... FROM Players
WHERE Domain = ? AND LeaderType = ? LIMIT 1
```
（`PlayerSetupLogic.lua:553`）

两列都是**自由字符串**，指向 XLP 条目名，**没有任何格式要求**；空串/NULL 合法且会触发回退。

### 1.2 引擎行为（回退链，必须记住）

`PlayerSetupLogic.lua:800-830`（函数 `SetUniqueCivLeaderData`，仅当 `tooltipControls.HasLeaderPlacard`）：

```lua
if info.Portrait then leaderPortrait = info.Portrait
else                    leaderPortrait = info.LeaderType .. "_NEUTRAL" end
tooltipControls.DummyImage:SetTexture(leaderPortrait);
tooltipControls.LeaderImage:SetTexture(leaderPortrait);

if info.PortraitBackground then leaderBGImage = info.PortraitBackground
else                            leaderBGImage = info.LeaderType .. "_BACKGROUND" end
tooltipControls.LeaderBG:SetTexture(leaderBGImage);
```

**推论（本类最容易漏的一条）**：两列**留空不等于安全**。
留空后引擎去找 `LEADER_<你的LeaderType>_NEUTRAL` / `..._BACKGROUND`；
mod 领袖通常**没有**这两个名字的贴图 → 这两个控件**空白**，且前端**不报错**。
所以 mod 领袖的正确做法是**二选一**：

| 做法 | 竖版 328×935 背景 | 说明 |
|---|---|---|
| **① 自建（推荐）** | 填 `PORTRAIT_<KEY>_BACKGROUND` | 目标控件就是竖版，**建议直接出 328×935 竖版**（见 §1.4） |
| **② 复用官方（零素材）** | 别名指向 `LEADER_<原版>_BACKGROUND` | 官方贴图是 1920×960 横版，控件 `StretchMode="None"` 不拉伸 → **只显示左上角一块**，视觉上"糊一块"。见 §三 |

### 1.3 控件与尺寸推导（`328×935` 从哪来）

**`328×935` 是控件尺寸，不是官方贴图尺寸**——官方 `LEADER_*_BACKGROUND` 实测 42/42 全为 **1920×960**。

推导链（全部实测）：

| # | 出处 | 事实 |
|---|---|---|
| 1 | `AdvancedSetup.xml:148` | `<Container ID="BasicPlacardContainer" Size="340,670" .../>` |
| 2 | `AdvancedSetup.lua:19` | `local MAX_SIDEBAR_Y :number = 960;` |
| 3 | `AdvancedSetup.lua:1671-1675` | `Resize()` 里 `iSidebarSize = min(CreateGameWindow:GetSizeY(), 960)` 后 `BasicPlacardContainer:SetSizeY(iSidebarSize)` |
| 4 | `AdvancedSetup.xml:600` | 内层 `<Container Size="parent-12,parent-25" .../>` |
| 5 | 合计 | `340-12 = 328`；`960-25 = 935` → **328×935** |

同容器内的控件（`AdvancedSetup.xml:595-616`）：

```xml
<Instance Name="LeaderPlacard">
  <Container ID="Top" Size="340,parent" Anchor="C,C">
    ...
    <Container Size="parent-12,parent-25" Anchor="C,T" Offset="0,9">
      <Image ID="LeaderBG"    Size="parent,parent" StretchMode="None" />   <!-- 背景：328×935，不拉伸 -->
      <Image ID="DummyImage"  StretchMode="Auto" Hidden="1"/>              <!-- 量比例用 -->
      <Image ID="LeaderImage" StretchMode="UniformToFill" Size="parent,670" Anchor="C,B"/>  <!-- 前景：328×670 -->
      ...
```

- **背景 `LeaderBG`**：`StretchMode="None"` → 贴图**按原始像素贴左上角**，超出裁掉。竖版 328×935 或更高（如 656×1870）不会变形。
- **前景 `LeaderImage`**：`UniformToFill` + 高 670 → **等比填满，超出裁切**，任意尺寸都不会拉变形。
- **比例自适应**：`DummyImage:GetSizeX()/GetSizeY()`（`PlayerSetupLogic.lua:816-821`）按贴图长宽比决定偏移 → 宽扁图与瘦高图会自动换位置。

> 该 placard 出现在**单人选人 / 剧情设置 / 多人 StagingRoom**：`AdvancedSetup.lua:1188`、
> `ScenarioSetup.lua:555`、`StagingRoom.lua:1311`（后者 `HasLeaderPlacard=false` 时不显示人物板）。

### 1.4 素材规格（环境 A）

| 项 | 前景 `Portrait` | 背景 `PortraitBackground` |
|---|---|---|
| 目标控件 | 328×670（`UniformToFill`） | 328×935（`None`） |
| **建议尺寸** | 高 **1024**、宽随内容（与原版 `LEADER_*_NEUTRAL` 同约定） | **328×935** 竖版（控件原始尺寸，1:1 无裁切）；若要留余量可 656×1870 等比放大 |
| 内容贴底 | 是（原版实测下边距恒 0，人物触底） | — |
| `.tex` `m_ClassName` | `UserInterface` | `UserInterface` |
| `.tex` `m_Tags` | `UserInterface` | `UserInterface` |
| 注册 XLP | `XLPs/UILeaders.xlp`（`m_ClassName=UITexture`） | 同左 |
| 像素格式 | 未压缩 RGBA8、单 mip（`bUseMips=false`、`m_NumMipMaps=0`） | 同左 |

> **为什么前景建议照抄原版约定**：官方 `LEADER_*_NEUTRAL` 实测 22 张（SDK pantry）**高恒 1024**
> （个别 1080）、宽 389~803、下边距恒 0 —— 即"内容定宽 + 触底"的紧致画布。
> 工艺见 `ui-leader-portrait.md` §4.1（等比缩到高 1024 → 按 alpha 内容定宽 → 水平居中，**不裁切**），
> 同一套工艺可直接复用于环境 A 的前景。

### 1.5 接线（三处，缺一不可）

| # | 位置 | 做什么 |
|---|---|---|
| 1 | `Textures/` | 新增 `<前景名>.{dds,tex}` + `<背景名>.{dds,tex}` |
| 2 | `Data/Config_*.sql` | `INSERT OR REPLACE INTO Players (..., Portrait, PortraitBackground) VALUES (..., '<前景名>', '<背景名>')` |
| 3 | `*.civ6proj` | 该 SQL 必须挂在 **`FrontEndActions` → `UpdateDatabase`**；`Textures/` 不需写清单（引擎自动扫描）；XLP 需登记 |

**为什么必须 FrontEnd**：`Players` 表**只存在于 Config 库**（实测：`DebugConfiguration.sqlite` 有，
`DebugGameplay.sqlite` 没有）。写进 `InGameActions` 会 `no such table: Players`。
（另见 `civ6-modding/project-setup.md`「Config = FrontEnd 专属」。）

```xml
<FrontEndActions>
  <UpdateDatabase id="RGN_Data_Config">
    <File>Data/Config_RGN.sql</File>
  </UpdateDatabase>
</FrontEndActions>
```

**不要挂 `Criteria`**（与 Suk 不同）：这是原版环境的必备数据，必须**无条件加载**。

---

## 二、环境 B：加载界面的前景与背景

### 2.1 数据：`LoadingInfo`（**Gameplay 库**）

```sql
CREATE TABLE "LoadingInfo" (          -- Base/Assets/Gameplay/Data/Schema/01_GameplaySchema.sql:1927
  "LeaderType" TEXT NOT NULL,
  "ForegroundImage" TEXT,             -- 前景（通常 = LEADER_<X>_NEUTRAL）
  "BackgroundImage" TEXT,             -- 背景（通常 = LEADER_<X>_BACKGROUND）
  "EraText" TEXT,
  "LeaderText" TEXT,
  "PlayDawnOfManAudio" BOOLEAN NOT NULL DEFAULT 1,
  "DawnOfManLeaderId" TEXT,
  "DawnOfManEraId" TEXT,
  PRIMARY KEY(LeaderType),
  FOREIGN KEY (LeaderType) REFERENCES Types(Type) ...);
```

官方 41 行**全部**自指（`ForegroundImage = LEADER_<X>_NEUTRAL`、`BackgroundImage = LEADER_<X>_BACKGROUND`）。

### 2.2 引擎行为（`LoadScreen.lua`）

```lua
-- 背景（:207-220）
if loadingInfo and loadingInfo.BackgroundImage then backgroundTexture = loadingInfo.BackgroundImage
else backgroundTexture = leaderType .. "_BACKGROUND" end
Controls.BackgroundImage:SetTexture( backgroundTexture );
if (not Controls.BackgroundImage:HasTexture()) then
    UI.DataError("Failed to load background image texture: "..backgroundTexture);
    Controls.BackgroundImage:SetTexture("LEADER_T_ROOSEVELT_BACKGROUND");  -- 强制兜底
end

-- 前景（:239-249）
if loadingInfo and loadingInfo.ForegroundImage then portraitName = loadingInfo.ForegroundImage
else portraitName = leaderType .. "_NEUTRAL" end
Controls.Portrait:SetTexture( portraitName );
if (not Controls.Portrait:HasTexture()) then
    UI.DataError("We are lacking a texture for "..portraitName);
end
```

**要点**：

1. 与 A 的差别只在"**背景多一层强制兜底**"（罗斯福特那张）——但那是 `DataError`，**不该依赖**。
2. **加载界面的前景同样读 `_NEUTRAL`**：这就是"**不自定义加载界面时，前景与 FrontEnd 共享同一张图**"的机制。
   → 你只要做了 `LEADER_<X>_NEUTRAL` 并让它在 `UITexture` 包里可解析，**A 和 B 同时满足**。
3. 加载界面的**背景**与 A 的竖版背景**不是同一张**：B 用 `_BACKGROUND`（1920×960 横版，
   `Shell_Loading.xlp`），A 用 `PortraitBackground`（328×935 竖版，`UI_Leaders.xlp`）。
4. `EndGameMenu.lua:824-828, 919-923`（失败结算界面）也用 `LoadingInfo.ForegroundImage` → 同一张前景。

### 2.3 素材规格（环境 B）

| 项 | 前景 `ForegroundImage` | 背景 `BackgroundImage` |
|---|---|---|
| 推荐值 | `LEADER_<X>_NEUTRAL`（与 A 共用） | `LEADER_<X>_BACKGROUND` |
| 尺寸 | 高 1024/1080，宽随内容（同 A 的前景） | **官方基线 1920×960**；实作**以 960 为基准、允许超过**（本项目 1920×1080 实机效果良好）。**低于 960 会有两侧裁剪风险**——见 §2.4 |
| 注册 XLP | `XLPs/UILeaders.xlp`（`UITexture`） | `XLPs/Shell_Loading.xlp`（`UITexture`） |
| 加载 | 无条件 | 无条件 |

> 官方 `Shell_Loading.xlp` = 24 条（`UITexture`），其中 `LEADER_*_BACKGROUND` 20 条；
> 布局见 `LoadScreen.xml:9`（`BackgroundImage`，`StretchMode="Auto"`）、`:14-15`（`PortraitContainer`/`Portrait`）。
> 尺寸口径另见 `civ6-modding/art-pipeline.md` role 表 `background` 行。

### 2.4 背景尺寸规则：**以 960 为基准，允许超过**（实机修正）

**结论（实机观察，权威）**：加载界面背景**高度 ≥960 即合规，可以更高**；
**高度低于 960 会出现两侧裁剪**。

| 高度 | 判定 | 说明 |
|---|---|---|
| **≥960** | ✔ 合规 | 960 是**基准**不是上限。本项目 6 张 1920×1080 实机效果良好 |
| **<960** | ✘ 有风险 | 两侧被裁（见下机制） |

**机制（假说，标注为待实机复核）**：`LoadScreen.xml:9` 的 `BackgroundImage` 是
`StretchMode="Auto"` 且**没有 `Size` 属性**；社区统计（`civ6-modding/reference/sources/stretchmode-vanilla-stats.md:67-71`）
也把 `Auto` 列为"最不确定"。若 `Auto` 实为 **cover 语义**（保持比例填满）：

| 贴图 | 16:9 屏上按高放大 | 结果 |
|---|---|---|
| 1920×960（官方基线） | ×1.125 → 2160×1080 | 每侧裁 120px |
| **1920×1080**（本项目） | ×1.0 | **零裁切** ✔ |
| 1920×900（<960） | ×1.2 → 2304×1080 | 每侧裁 192px ✘ |

**引擎确证部分**（与假说无关的部分，可直接采信）：
- `LoadScreen.lua:344` `Controls.BackgroundImage:GetSizeVal()` —— `Auto` 下控件尺寸**跟随贴图原始尺寸**；
- `LoadScreen.xml:10` `<Group Size="parent,parent" Clip="1">` —— 溢出部分**确实会被裁掉**。

> ⚠ **机制部分（cover 假说）未经实机对照验证**；"≥960 合规 / <960 有裁剪风险"这一**结论**来自实机观察。
> 若要落成更硬的规格，需用 FireTuner 或对照测试（改 `LoadingInfo.BackgroundImage` 指向不同高度的图）确认。

**推荐档位**：若要零裁切，出 **1920×1080**（16:9 屏）；只求合规可用，**宽幅 × ≥960** 即可。

### 2.5 `LoadingInfo` 写在哪

- 该表属 **Gameplay** → `InGameActions` → `UpdateDatabase`（**不是** FrontEnd）。
  实测：`DebugGameplay.sqlite` 有 `LoadingInfo`（41 行）；`DebugConfiguration.sqlite` **没有**。
- 其余列：`LeaderText`（加载界面简介 LOC tag）、`PlayDawnOfManAudio`（0/1）、`EraText`。

> ⚠ 本 skill 旧文档（`SKILL.md` §2.1、`ui-leader-portrait.md` §二）把「加载界面」判为
> **"不关联（另一条链）"并到此为止**——判定本身没错（确实不是 Suk 那条链），
> 但**没有文档承接它**，于是成了职责真空。本文件即该链的落点。

---

## 三、"没有自有背景，借用原版某位领袖的背景"——机制与（缺失的）选取规则

### 3.1 机制：XLP **别名条目**（官方自己的做法，零素材复制）

XLP 条目的 `m_EntryID` 与 `m_ObjectName` **可以不同** —— 后者才是真正的贴图名。
这正是官方的别名机制（实测）：

| XLP | 别名条目 | 指向 |
|---|---|---|
| `Shell_Loading.xlp` | `LEADER_CATHERINE_DE_MEDICI_BACKGROUND` | `LEADER_CATHERINE_BACKGROUND` |
| `Shell_Loading.xlp` | `LEADER_PHILIP_II_BACKGROUND` | `LEADER_PHILLIP_II_BACKGROUND` |
| `UI_Leaders.xlp` | `LEADER_CATHERINE_DE_MEDICI_NEUTRAL` | `LEADER_CATHERINE_NEUTRAL` |
| `UI_LeaderScenes.xlp` | `<X>_4`（**23 条**） | `BARBAROSSA_4` |

即：**`Players.PortraitBackground` 可以直接填 `LEADER_<别的领袖>_BACKGROUND`，无需复制 DDS。**

```xml
<!-- 复用（不新增贴图）：EntryID 可解析，ObjectName 指官方 -->
<Element>
  <m_EntryID  text="LEADER_CARTETHYIA_QYQXP_BACKGROUND"/>
  <m_ObjectName text="LEADER_HOJO_BACKGROUND"/>
</Element>
```

> ⚠ **未实测项**：别名指向的贴图必须**已经在该 XLP 所属的 BLP 包里**（官方别名都指本包内条目）。
> 跨包引用（例如在 `UI_Leaders.xlp` 里指向只存在于 `Shell_Loading` 的贴图）**没有先例**，
> 是否解析成功**不确定** —— 要跨包复用，稳妥做法是**用同一组 `<m_EntryID>/<m_ObjectName>` 在你自己的 XLP 里登记**，
> 或直接复制 DDS。不确定时按"复制 DDS"办。

### 3.2 选取规则：**量化口径（新增，基于官方实测调色板）**

官方**没有任何一位领袖借用另一位不同领袖的背景**（DB 全表扫描：`Players` 三 Domain 各 54/65/77 行，
`LoadingInfo` 41 行，唯一的"跨"引用都是**同一领袖的变体**，如
`T_ROOSEVELT_ROUGHRIDER → LEADER_T_ROOSEVELT_BACKGROUND`）。
所以"按色调挑一张"是**本 skill 新增的约定**，不是原版事实——按下列口径执行：

**调色板数据**：`reference/vanilla-leader-backgrounds.json`（脚本
`scripts/pick_vanilla_background.py` 维护）。每张官方背景记录：

- `mean` / `median`（缩到 96px 后的平均 / 中位 RGB）
- `hue`（**饱和度×明度加权的圆平均色相**，规避暗部噪声；排除 `S·V < 0.02` 的近黑像素）
- `pack`（Base / Expansion1 / Expansion2 / CivRoyaleScenario，决定可用性——**缺 DLC 就没有那张图**）

**挑选口径（两步，先硬后软）**：

1. **硬条件**：候选所属 `pack` 必须是目标工程**已依赖**的（`示例工程` 依赖 Expansion2
   → 只能用 Base + Expansion1 + Expansion2，**不要**用 CivRoyaleScenario）。
2. **软条件（相似度）**：以主角色的 `hue` 为主键、`mean` 亮度为辅键打分：

   ```
   score = 色相距离(Δh, 环形 0..180) / 180 * 0.7  +  亮度距离(|ΔL|/255) * 0.3
   取 score 最小者；Δh 环形距离 > 60° 时直接判为"不相似"，改用自建或人工指定。
   ```

   - **色相优先**：人眼对色相差异远敏感于亮度，故权重 0.7。
   - **亮度辅之**：避免挑到"同为青色但一个近黑一个高亮"的搭配。
   - **暖色（hue 330~30）跨 0° 是同一族**：`331.7`(Cleopatra) 与 `29.3`(Default) 的环形距离约 57°，
     不要按线性差 `297` 计算。

**已知的官方背景色相参考**（节选，完整见 JSON）：

| 领袖背景 | hue | mean RGB | 观感 |
|---|---|---|---|
| `LEADER_CATHERINE_BACKGROUND` | 180.6 | (1, 37, 37) | 深青 |
| `LEADER_MONTEZUMA_BACKGROUND` | 173.3 | (1, 38, 34) | 深青绿 |
| `LEADER_HARDRADA_BACKGROUND` | 196.9 | (13, 36, 45) | 深蓝青 |
| `LEADER_HOJO_BACKGROUND` | 222.3 | (28, 37, 58) | 深靛蓝 |
| `LEADER_DIDO_BACKGROUND` | 221.5 | (28, 37, 59) | 深靛蓝 |
| `LEADER_PEDRO_BACKGROUND` | 248.6 | (37, 35, 49) | 蓝紫 |
| `LEADER_GORGO_BACKGROUND` | 0.1 | (51, 9, 8) | 暗红 |
| `LEADER_VICTORIA_BACKGROUND` | 338.7 | (52, 21, 32) | 酒红 |
| `LEADER_ELEANOR_ENGLAND_BACKGROUND` | 7.9 | (73, 19, 11) | 砖红 |
| `LEADER_DEFAULT_BACKGROUND` | 29.3 | (58, 41, 26) | 暖棕 |
| `LEADER_GANDHI_BACKGROUND` | 28.6 | (67, 35, 6) | 橙棕 |
| `LEADER_QIN_BACKGROUND` | 52.5 | (39, 35, 6) | 橄榄 |
| `LEADER_MATTHIAS_CORVINUS_BACKGROUND` | 93.3 | (28, 45, 15) | 深绿 |
| `LEADER_BARBAROSSA_BACKGROUND` | 0.0 | (42, 43, 40) | 中性灰 |

**工具**：

```bash
# ① 列出全部官方背景的色相/亮度（供人工挑选）
python <skill>/scripts/pick_vanilla_background.py --list

# ② 给一张主角立绘/参考图，按上述口径推荐 top-N 官方背景
python <skill>/scripts/pick_vanilla_background.py --reference <主角图.png> --top 5

# ③ 直接产接线：写出别名 XLP 条目 + 打印 Players/LoadingInfo 该填什么
python <skill>/scripts/pick_vanilla_background.py --project <工程根>     --leader LEADER_CARTETHYIA_QYQXP --reference <立绘.png> --write
```

> 🔴 **仍必须先问用户**（本 skill 通用铁律一）：借用官方背景属"素材决策"，
> 脚本只出**候选与理由**；**未确认前不写盘**（`--write` 需显式给出，且 `--check` 可先预演）。

---

## 三bis、自动处理流程（`scripts/prepare_frontend_portrait.py`）

前面三节是**规格**；本节是**拿到一张素材后怎么自动决定用哪套规格**。脚本把
"分类 → 处理 → 找背景 → 出接线" 串成一条链，避免每次手判。

### 3b.1 像素构成分类（核心）

分析 alpha 通道，把素材分成三类：

| 类别 | 判据 | 处理 |
|---|---|---|
| **① 人物抠图** | 透明像素（alpha≤5）占比 **≥40%** | 定内容框 → 缩到高 1024 → **底部对齐** → 按内容定宽居中 → `LEADER_<KEY>_NEUTRAL` |
| **② 满幅图** | 透明 **≤5%** 且不透明（alpha≥250）**≥90%** | **空白前景（显式空串）+ 铺满背景** |
| **③ 中间地带** | 其余 | **停下问用户**（exit 3），用 `--force-subject` / `--force-bleed` 裁决 |

**实测参考**（`示例工程` 6 位领袖 × 3 类素材）：

| 素材 | 透明% | 不透明% | 判定 |
|---|---|---|---|
| `FALLBACK_NEUTRAL_*_QYQXP`（3D 回退立绘） | 60~74 | 25~38 | ① 人物抠图 |
| `IMG_LOADING_FOREGROUND_*_QYQXP` | 60~74 | 25~38 | ① 人物抠图 |
| `IMG_LOADING_BACKGROUND_*_QYQXP` | 0.0 | 99.7~100 | ② 满幅图 |
| `PORTRAIT_*_BACKGROUND`（竖版） | 0.0 | 100 | ② 满幅图 |

→ 两类的透明率差距极大（0% vs 60%+），默认阈值（40% / 5%）把它们分得很干净，
**中间地带只会在真正模棱两可时命中**。

### 3b.2 分支②「空白前景」的**正确写法**（极易写错，★）

`PlayerSetupLogic.lua:807-829` 是 `if info.Portrait then ... else ... end`：

| SQL 取值 | Lua 里的值 | 引擎行为 |
|---|---|---|
| 贴图名 | 非空串 | 直接用该贴图 |
| **`''`（空串）** | `""` —— **Lua 里 truthy** | `SetTexture("")` → **真正的空白，且短路回退** ✔ 本分支要的就是这个 |
| **`NULL`** | `nil`（falsy） | 走回退 → `<LeaderType>_NEUTRAL`（mod 通常没有 → **空白且不报错**） |

> **结论**：分支② **必须写显式空串 `''`，不能写 `NULL`**。
> 本项目当前 `Config_RGN.sql` 写的正是 `''`，属**正确设计**（早期版本的校验器曾把它
> 误报成"空白风险"，已于 2026-09-19 修正为三态判定）。

### 3b.3 背景获取顺序（严格降级，不静默编造）

前景与背景**分别取**（placard 要竖版 328×935；加载界面要 ≥960 高，二者不能共用一张源）：

| 目标 | 降级顺序 |
|---|---|
| **加载界面背景** | ① 工程既有 `IMG_LOADING_BACKGROUND_<KEY>` / `LEADER_<KEY>_BACKGROUND` → ② `--bg-dir` → ③ **色系回退**（§三）→ ④ 报缺失 |
| **placard 竖版背景** | ① 工程既有 `PORTRAIT_<KEY>_BACKGROUND` → ② 由加载背景 cover 到 328×935 → ③ 官方别名（会警告"横版被裁"） |

**色系回退仅当 Δh ≤ 60° 才自动采用**；否则判"不相似" → **exit 3 交用户裁决**
（可用 `--pick <官方背景名>` 手动指定）。

### 3b.4 命名（**以官方为准**）

| 产物 | 命名 | 备注 |
|---|---|---|
| 前景 | `LEADER_<KEY>_NEUTRAL` | 官方约定；选人 placard 与加载界面**共用** |
| 加载界面背景 | `LEADER_<KEY>_BACKGROUND` | 官方约定；高 ≥960 |
| placard 竖版背景 | `LEADER_<KEY>_PLACARD_BACKGROUND` | 官方无此物（官方直接拿 1920×960 凑），取官方前缀 + 语义后缀 |

> **本项目既有的 `PORTRAIT_*` / `IMG_LOADING_*` 不做重构**——脚本只把它们
> 当作"① 工程既有"读入。新做的才走上面的官方命名。

### 3b.5 用法（**两段式**：先计划 → 确认 → 执行）

```bash
# ① 计划态（默认，**不写盘**）：分类 + 处置方案 + 背景来源，交用户确认
python <skill>/scripts/prepare_frontend_portrait.py --project <工程根> \
    --leader LEADER_X_QYQXP --image <素材.png>

# ② 用户确认后执行
python <skill>/scripts/prepare_frontend_portrait.py --project <工程根> \
    --leader LEADER_X_QYQXP --image <素材.png> --write --confirmed

# ③ 裁决项由用户拍板后强制指定
... --force-subject --write --confirmed      # 或 --force-bleed

# ④ 批量（目录内文件名需含领袖名片段）
python <skill>/scripts/prepare_frontend_portrait.py --project <工程根> --image-dir <目录> --write --confirmed
```

退出码：`0` 成功 / `1` 错误 / `2` 告警 / **`3` 需用户裁决**。

**`--write` 必须与 `--confirmed` 同时给**：只给 `--write` 会被直接拒绝（exit 3），
防止在用户没看过计划时落盘。

### 3b.6 会停下询问的情形（§1.0 总规则）

以下情形脚本**不自行决定**，一律 exit 3 并要求用户裁决：

| 情形 | 原因 |
|---|---|
| 像素构成落在**中间地带** | 分类不明确，需人判"人物抠图 or 满幅图" |
| 色系回退**最佳候选 Δh > 60°** | 判为不相似，需人指定 `--pick` |
| **placard 竖版背景缺失** | 不自行拿横版去凑（`StretchMode=None` 只显示左上角），也不自行补边 |
| **源图高 < 960** | 加载界面背景高度不足会有两侧裁剪风险 |
| **缩放后宽度不足**（无法铺满 1920） | 补边属"把图改好"，超出本 skill 范围 |
| **目标贴图已存在** | 不覆盖工程已有素材 |

**脚本会做什么 / 不会做什么**：

| 会 | 不会 |
|---|---|
| 产出 `.dds` + `.tex`（前景 / placard 背景 / 加载背景） | **不自动改工程 SQL**（打印接线 SQL 供你落位） |
| 幂等登记 XLP 别名（`Shell_Loading.xlp` / `UILeaders.xlp`） | **不覆盖**已存在的工程贴图 |
| 打印 FrontEnd 段 / InGame 段的接线 SQL | 不重构本项目既有的 `PORTRAIT_*` / `IMG_LOADING_*` 命名 |
| 只做**裁剪 / 通道透明度 / 描边**（§1.0 总规则） | 不做重绘、修补、重着色、调色、生成式补图、迭代调参 |

---

## 四、完整判定树（拿到"给我做领袖立绘/背景"时）

```
用户说「领袖立绘 / 领袖背景 / 选人界面」
│
├─ 提到 Suk / 选人界面替换 / PortraitBackground 且在意 Suk？
│    └─ 是 → 【可选分支】类别⑤ reference/ui-leader-portrait.md（Criteria 门控）
│
└─ 不涉及 Suk（或要求"原版也要正常"）
     │
     ├─ 【有素材】→ 跑 scripts/prepare_frontend_portrait.py（§三bis）
     │    ├─ 第 1 次（计划态，不写盘）→ 把计划交用户确认
     │    ├─ 透明 ≥40%  → ① 人物抠图：LEADER_<X>_NEUTRAL（高 1024、底对齐、内容定宽）
     │    │               背景走 §三bis.3 降级（工程 → --bg-dir → 色系回退 → 问用户）
     │    ├─ 透明 ≤5%   → ② 满幅图：前景 = '' （**显式空串**）+ 铺满背景
     │    ├─ 中间地带   → ⛔ exit 3，**停下问用户**（--force-subject / --force-bleed）
     │    └─ 第 2 次（用户确认后）→ 加 --write --confirmed 执行
     │
     └─ 【无素材 / 手工做】
          ├─ 要选人界面(A)的前景/背景？
          │    ├─ 前景 → LEADER_<X>_NEUTRAL 风格，高 1024，UILeaders.xlp
          │    └─ 背景 → ① 自建 328×935 竖版（推荐）或 ② 别名复用官方（§3）
          ├─ 要加载界面(B)的前景/背景？
          │    ├─ 前景 → 复用同一张 _NEUTRAL（B 自动跟随）
          │    └─ 背景 → LEADER_<X>_BACKGROUND，**高 ≥960**（基准，可超过），Shell_Loading.xlp
          └─ 要外交场景(C)？
               └─ 走 civ6-modding/art-pipeline.md §三.1（DiplomacyInfo / SceneLayers）
```

---

## 五、验证清单

```
0. （若有素材）**两段式**：先跑计划态交用户确认，确认后再 `--write --confirmed`
1. python <skill>/scripts/verify_frontend_portrait.py --project <工程根>   # A+B 两环境专用校验器
2. python <civ6-modding>/scripts/check_pantry.py                           # 0 error
3. python <civ6-modding>/art/verify_tex_class.py --project <工程根>          # .tex 类别
4. python <civ6-modding>/art/gen_modartxml.py <工程根> --check               # Art.xml 同步
5. ModBuddy Rebuild All → 同步 Mods → 进游戏
6. 实机三处验收（**缺一不可**）：
   - 选人界面：点开领袖 → placard 左侧出现立绘 + 竖版背景
   - 开局加载界面：背景是 1920×960 横版、前景是同一张立绘
   - 失败结算界面（可选）：`LoadingInfo.ForegroundImage` 生效
7. Suk 开 / Suk 关 **双态验证**（若同时做了类别⑤）
```

`verify_frontend_portrait.py` 检查项：

1. `Players.Portrait/PortraitBackground`（若有值）**在磁盘存在**同名 `.dds`/`.tex`，**或**是合法 XLP 别名；
2. **留空时**：对应 `LEADER_<LeaderType>_NEUTRAL` / `_BACKGROUND` **必须**能在某个 `UITexture` XLP 中找到，
   否则报「空白风险」（这是最常见的静默失败）；
3. `LoadingInfo.ForegroundImage/BackgroundImage` 同上；
4. `.tex` 的 `m_Width/m_Height` == 实际 DDS 宽高、`m_ClassName == UserInterface`；
5. 背景尺寸告警：环境 A 背景 ≠ 328×935（且非其等比）→ WARN「可能被 `StretchMode=None` 截断」；
   **环境 B 背景低于 960 高 → WARN（两侧裁剪风险）；≥960 一律合规**（960 是基准，官方基线 1920×960）；
6. 行尾：`.tex`/`.xlp` = LF、`.sql` = CRLF（`civ6-modding/gotchas.md` §68）。

---

## 六、实测依据汇总（为什么这些数字可信）

| 结论 | 证据 |
|---|---|
| `Players` 在 Config 库、`LoadingInfo` 在 Gameplay 库 | node:sqlite 实测表清单：Config 78 表含 Players 无 LoadingInfo；Gameplay 427 表反之 |
| A 的回退链 | `PlayerSetupLogic.lua:807-829` 源码 |
| B 的回退链 + 强制兜底 | `LoadScreen.lua:207-220, 239-249` 源码 |
| `328×935` = 控件尺寸 | `AdvancedSetup.xml:148,600` + `AdvancedSetup.lua:19,1671-1675` 推导 |
| 官方背景 `LEADER_*_BACKGROUND` 全 1920×960 | SDK pantry 41 张 DDS 逐个读宽高：41/41 |
| 官方 `LEADER_*_NEUTRAL` 高 1024/1080、宽 389~803 | pantry 22 张逐个读宽高 |
| 官方**无**跨领袖背景借用 | `Players`×3 Domain + `LoadingInfo` 全表扫描，跨引用仅同领袖变体 |
| XLP 别名机制真实存在 | `Shell_Loading.xlp` 2 条、`UI_Leaders.xlp` 2 条、`UI_LeaderScenes.xlp` 23 条 `EntryID≠ObjectName` |
| 加载界面背景 **≥960 合规、<960 两侧裁剪** | **实机观察**（本项目 1920×1080 效果良好）；机制假说见 §2.4，**未做实机对照** |
| 像素构成可分三类（透明 0% vs 60%+） | 本项目 6 位领袖 × `FALLBACK_NEUTRAL`/`IMG_LOADING_FOREGROUND`（透明 60~74%）与 `IMG_LOADING_BACKGROUND`/`PORTRAIT_*_BACKGROUND`（透明 0%）实测 |
| 空串 `''` 短路回退、`NULL` 才回退 | `PlayerSetupLogic.lua:807-829` 的 `if info.Portrait then ... else ... end`（Lua 空串 truthy） |
| `FALLBACK_NEUTRAL_*` 是**3D 回退**、与环境 A/B 无关 | `m_ClassName=Leader_Fallback`，注册在 `LeaderFallbackImages.xlp`，消费方 `UI.SetLeaderImageControl`（`DiplomacyActionView.lua:2108`） |
