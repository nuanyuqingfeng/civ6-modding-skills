# art-pipeline — 素材转换子节点（PNG → DDS → .tex）

处理**用户自备美术素材**的转换、`.tex` 生成与注册联动。生图（AI 作画）不在本节点范围内。
路由到本文件 = 本次任务涉及素材文件——先读第一节铁律再动手。

---

## 一、铁律：素材处理前必须询问

任何涉及素材文件的步骤开始前，必须先询问用户：

1. **来源**：用户自备（要路径/清单）／暂缺（本次跳过该图及其全部注册条目）
2. **命名方式**：沿用用户原文件名／中文名映射（`asset_map.json` 记录 `技术名 ↔ 源名`，输出仍为技术名）
3. **多图意图**（用户提供 **≥2 张图**时必问）：拼成一张 **atlas 网格图集**（走 `make_atlas.py`，
   问清 `IconsPerRow/IconsPerColumn` 或让 AI 按组员数推荐）／**各自独立出图**（走 `convert_art.ps1`）。
   用户说"序列图""拼图""图集""合成一张"时走 atlas 路线。

4. **色相铁律（2026-09 实战教训）**：规范化只做**几何**（裁 alpha 外接框 / 等比缩放 / 居中），
   **不得**叠加 levels / gamma / 亮度 / 对比度 / 饱和度 / 色相 / 重着色——那属于改美术。
   彩色类别（建筑 / 区域 / 项目 / 资源 / 伟人 / 领袖…）必须 `color=None`；
   只有 `color=<n>` 是**显式**的「涂成灰度剪影」（`unit_icon` 的白色剪影就用它），
   它会把 R=G=B 整个覆盖掉，**用前必须确认该类别本来就是剪影**。
   需要「提亮暗图」时先问用户，不要自作主张——本项目建筑图标曾因加了一步 levels+gamma
   被判「色相变了」而全部返工。

**未确认前不得复制、改名、生成任何图片文件。**

被动语义：「删除 = 持久意图」——用户删掉的图永不自动恢复，只提醒缺失。

## 二、工作流（AI 决策、脚本执行）

```
用户提供成品图路径
→ AI 读项目 XLPs / Icons.xml / ArtDefs 推导每张图的技术名 + 角色（role）
→ 写 art_manifest.json（schema 见 art/art_manifest.schema.json；单图尺寸不填，由 role 内置）
→ 单图：pwsh -File <skill>\art\convert_art.ps1 -Manifest <manifest 路径>
   （内部：texconv 转 DDS → 写 asset_map.json → gen_tex.py 逐 DDS 生成 .tex）
→ 多图图集：python <skill>\art\make_atlas.py -Manifest <manifest 路径>
   （内部：组员按 grid 拼版 → 逐尺寸出整版 PNG → texconv 转 DDS → gen_tex.py 生成 .tex
     → 产出 <atlas>_registration.xml 注册片段）
→ 注册：**用 `art\merge_icon_registration.py` 幂等并入**（不要手工合并：漏行/重名高发）
     python <skill>\art\merge_icon_registration.py <projectRoot> --fragment <atlas>_registration.xml
            [--icons Data/Icons_RGN.xml] [--xlp XLPs/Icons.xlp] [--dry-run]
     它同时完成两件事：并入 IconTextureAtlases / IconDefinitions 行 + 给 XLP 补 UITexture 条目，
     并保留目标文件的 BOM / CRLF / 格式（只做行插入）；--dry-run 可先看将要插什么。
→ 注意 **新贴图必须登记进某个 `<m_ClassName text="UITexture"/>` 的 XLP**（本工程是 XLPs\Icons.xlp）。
     漏登记 = .dds 存在但不会被打进 UI/Icons 包，游戏里图标是空白。merge 工具会代劳。
     别混：几何/材质/模型类 XLP（`tilebases.xlp`=TileBase、本工程 `RGN_Clutter_*.xlp`=Landmark、
     `Leader_LightRigs.xlp`=LeaderLighting、`UILensModels.xlp`=UILensAsset 等）条目名**不是贴图**，
     登记进去也不会被打进 UI 包。
     但 ⚠ **`UI_LeaderScenes.xlp` 不是这类反例**——它 `m_ClassName=UITexture`（官方 3 个共 174 条），
     外交分层贴图就登记在它里面（见下方「三.1」）。
→ Mod.Art.xml：python <skill>\art\gen_modartxml.py <projectRoot> --check
     （差异需人工确认后才 --write；注意 --check 报的差异可能是**本次改动之前就存在的**，
      先看差异里有没有提到你这次新增的 XLP/artdef，没有就别顺手 --write）
→ 校验：python <skill>\art\verify_icon_atlas.py <projectRoot> [--vanilla "<官方 Icons 目录>"]
     （第八节「完成标准」的可执行版，交付前必跑，见第十节）
→ **类别校验**：python <skill>\art\verify_tex_class.py --project <projectRoot>
     （查 `.tex` 的 `m_ClassName` 与消费它的 XLP 类是否匹配 —— 见下方「二.1」。
       类别写错时 cooker 只报一句 class 不匹配，且 XLP cook 仍显示 success、
       条目被静默换成 error asset；本脚本是唯一能提前拦住的机械防线）
→ 边缘质量门：python <skill>\art\verify_icon_atlas.py <projectRoot> --edge-qa
     （专查"中间档被锐化/压对比 → 实机锯齿"；结构检查查不出这类损伤，见第 8.1 节。
       报 DAMAGED 时用 art\regen_atlas_tiers.py 从 256 母版重出，不必改 .tex/网格）
→ 注册：Art.xml 的 <Content> 与 项目 `.civ6proj` 条目同步更新

```

依赖：`texconv`（**已随包内置 `art/bin/texconv.exe`**，探测链见 `art/bin/README.md` / `_texconv.py`：
`TEXCONV` → 内置 → `PATH` → WinGet Links →（仅 `recursive=True`）WinGet Packages）、
Python 3 + **Pillow**（`make_atlas.py` 组版）、**numpy + scipy**（`normalize_icon.py` / `apply_fow.py` / `verify_icon_atlas.py` / `regen_atlas_tiers.py` / `survey_icon_atlas.py`）。

> ⚠ **"自动 winget 安装"只对 `convert_art.ps1` 入口成立**（它会跑一次 `winget install Microsoft.DirectXTex.Texconv`）；
> `make_atlas.py` / `_texconv.py` **只探测、不安装**，找不到就报错要求手动装或设 `TEXCONV`。

### 二.1 ⚠ `.tex` 类别（`m_ClassName`）是硬约束，且**不能靠名字猜**

`gen_tex.py` 判 `m_ClassName` 用的是「`FALLBACK_` 前缀 → `Leader_Fallback`，其余 → `UserInterface`」。

| 贴图名 | 真实用途 | 应有 `m_ClassName` | 注册在 |
|---|---|---|---|
| `FALLBACK_NEUTRAL_CARTETHYIA_QYQXP` | 3D 领袖回退（官方模板） | `Leader_Fallback` | `LeaderFallbacks.xlp` |
| `SUK_UI_PORTRAIT_CARTETHYIA_QYQXP` | **选人界面 2D 立绘**（第三方适配） | **`UserInterface`** | `UILeaders.xlp`（`UITexture`） |

#### 命名空间铁律：第三方界面素材**不得借用官方模板前缀**

**`FALLBACK_` / `LEADER_` / `ICON_` 等前缀是官方语义**（`FALLBACK_*`＝3D 回退，
固定对应 `Leader_Fallback` 类）。第三方界面适配的素材**一律进自己的独立命名空间**：

```
<适配对象短名>_UI_<KIND>_<KEY>          例：SUK_UI_PORTRAIT_<KEY> / SUK_UI_BACKGROUND_<KEY>
```

> **这条铁律是有代价换来的。** 历史上一度把 Suk 选人界面的 2D 立绘命名为
> `FALLBACK_NEUTRAL_<KEY>_Suk`（借用了官方 3D 回退前缀），于是：
> 同前缀、不同类别，`gen_tex.py` 被迫维护一张 `_UI_PORTRAIT_SUFFIXES` 例外表，
> 且 skill 文档、两个校验器都要反复解释"这两类为何同前缀"——后人极易把 UI 立绘
> 误当 3D 回退。2026-09-18 起素材迁入 `SUK_UI_*` 独立命名空间，该歧义从根上消失，
> 例外表退化为 legacy 兼容（见下）。
>
> **为什么当时"看起来非这么做不可"**：`Players.Portrait` / `PortraitBackground` 是
> **自由字符串列**，界面代码读值后交给 Image 控件显示——贴图名本身**没有任何**格式要求。
> 所谓"必须沿用某后缀"只是跨工程沿用的**惯例**，不是技术约束。

**新纳入第三方界面适配时**：选一个不与官方前缀重叠的短名（如 `SUK`），
按 `<短名>_UI_<KIND>_<KEY>` 命名，然后：
`civ6-asset-forge/scripts/gen_suk_portrait.py`（生成）/ `verify_suk_portrait.py`（校验）。

> **legacy 兼容**：`gen_tex.py` 的 `_UI_PORTRAIT_SUFFIXES = ("_Suk",)` 仍保留，
> 用于尚未迁移的旧工程；某工程报 `*_Suk` 贴图时，跑
> `migrate_suk_namespace.py <工程根> --write` 一次性迁移（会同时改文件名、`.tex` 内部
> 三字段、XLP 与 SQL 引用）。**全部工程迁移完成后，该常量与 `is_fallback()` 里的
> 那次判断可一并删除。** 迁移后**必须重新 cook**（新名字＝新 BLP 条目）。

> ⚠ **多情绪槽命名（`FALLBACK_<STATE>_LEADER_<KEY>`）**：这是另一套并存写法
> （`civ6-mod-developer` 的手工路线在用）。`is_fallback()` 用 `FALLBACK_` 前缀判据，
> 对 `NEUTRAL/HAPPY/UNHAPPY/ENRAGED` 四槽**全部命中**，无需特例。

类别写错的后果是**静默**的：cooker 报
`has class 'X', but is bound to parameter 'Y' which does not accept this class`，
错误沿「材质 → 资产 → XLP 条目」传播，而 **XLP cook 仍显示 success**，条目被替换成 error asset
（界面空白，不报错）。

- `gen_tex.py` 已内置 `_UI_PORTRAIT_SUFFIXES` 显式排除 `_Suk` 这类 UI 后缀；
  **新增同类后缀请往该常量里加**，不要再写前缀特例。
- 交付前自查（PowerShell）：`Select-String -Path Textures\*.tex -Pattern m_ClassName` 逐个核对，
  或跑 `python "<skills>/civ6-asset-forge/scripts/verify_suk_portrait.py" --project <工程根>`
  （`--project` 为必填；在意的就是这一条）。bash 下等价写法是 `grep m_ClassName Textures/*.tex`。
- 详见 `civ6-asset-forge/reference/ui-leader-portrait.md` §4.4。

## 三、图标尺寸规格全表（19 类）

数据来源：Civ6 Modding Assistant 1.6.3 `civ6/iconsize_data.pyc` 反编译表；已用本项目
`Atlas_Rgn` 序列图成品实测对齐（Districts 3×2、Leaders 3×2、Resources 6×7 各尺寸画布
均 = (IconsPerRow×s, IconsPerColumn×s)，与表逐位一致）。项目可自定义增减（如 Resources
加 32、Product 用 45），此时在 manifest atlas 条目显式填 `sizes`。

| role | 类别 | 尺寸 |
|---|---|---|
| `civ_icon` | Civilizations | 22,30,32,36,44,45,48,50,64,80,128,200,256（13 种） |
| `leader_icon` | Leaders | 32,45,48,50,55,64,80,256（8 种） |
| `building_icon` | Buildings | 32,38,50,80,128,256 |
| `citystate_icon` | Citystates | 22,30,32,36,40,44,48,64,68,80,256 |
| `civic_icon` | Civics | 38,42,128,160 |
| `district_icon` | Districts | 22,32,38,50,80,128,256 |
| `feature_icon` | Features | 50,64,256 |
| `government_icon` | Governments | 32,50 |
| `greatwork_icon` | Greatworks | 45,64,256 |
| `improvement_icon` | Improvements | 38,50,80,256 |
| `policy_icon` | Policies | 32,38,50,256 |
| `project_icon` | Projects | 30,32,38,50,70,80,256 |
| `resource_icon` | Resources | 38,50,64,256 |
| `stat_icon` | Stats | 16,22,32,45,55 |
| `tech_icon` | Tech | 30,38,42,128,160 |
| `unit_action_icon` | Unit_Actions | 38,50,80,256 |
| `unit_portrait` | Unit_Portraits | 38,50,70,95,200,256 |
| `unit_icon` | Units | 22,32,38,50,80,256 |
| `victory_icon` | Victories | 64,80,130,220 |
| `wonder_icon` | Wonders | 32,38,50,64,128,256 |

非图标 role（**原尺寸单 DDS**——`convert_art.ps1` 对它们**不加 `-w/-h`**，
即**脚本不强制尺寸**，尺寸由素材来源/所属类别决定）：

| role | 典型尺寸（原版实测） | 对应贴图 / 注册目标 |
|---|---|---|
| `portrait` | 高 **1024**（宽随内容，原版实测 389~803） | UI 选人立绘 `LEADER_*_NEUTRAL` → `UILeaders.xlp`（`UITexture`）<br>3D 纸片人贴图 `LEADER_*_TEXTURE`/`_OPACITY` = **1024²** → `Leaders.artdef` |
| `fallback` | 高 **1024/1080**（宽随内容；原版 554~816） | `FALLBACK_NEUTRAL_*` → `LeaderFallbacks.xlp`（`LeaderFallback`） |
| `background` | **1920×960** | `LEADER_*_BACKGROUND` → `Shell_Loading.xlp`（`UITexture`），领袖**加载界面**背景 |
| `diplomacy_layer1..4` | 层 1–3 = **960×505**；层 4 = **1920×1010** | `<LEADER>_1..4` → `UI_LeaderScenes.xlp`（`UITexture`），外交**场景分层** |
| `loyalty_3d` / `loyalty_sv` | 512 / 128 与 256 / 128 | 由 `civ6-asset-forge` 的 `reference/loyalty-icon.md` 固定；UILens XLP + artdef |
| `custom` | 不限 | 兜底，注册目标由调用方负责 |
| `fow` | 同其普通版 | FOW 迷雾变体，源图由 `apply_fow.py` 生成 |

> ⚠ **尺寸不是脚本强制的**：`convert_art.ps1` 的 `Get-Sizes()` 对上述 role 返回空表
> → 走「原尺寸单 DDS」分支（**不带 `-w/-h`**）。所以**给错尺寸不会报错**，
> 只会让游戏里显示异常。**填 manifest 前请查上表并核对参考文档**，不要凭记忆。

### 三.1 领袖「背景」的三条独立链（极易混淆，务必先读）

术语里「领袖背景」指**三个互不相同**的东西。它们的**尺寸、XLP、加载条件**都不同，
混淆会导致"图做了但游戏里不显示"。**引擎的真实逻辑**（`Base/Assets/UI/LeaderScene.lua:61-79`）：

```lua
local diplomacyInfo = GameInfo.DiplomacyInfo[leaderName];
if diplomacyInfo and diplomacyInfo.BackgroundImage then
    -- 链 C：直接用这一张图，**完全跳过** SceneLayers 分层
    CreateBackgroundLayer(diplomacyInfo.BackgroundImage, ...);
else
    local numLayers = GameInfo.Leaders[leaderName].SceneLayers;
    leaderName = string.gsub(leaderName, "LEADER_", "");   -- ← 去掉 LEADER_ 前缀
    if (numLayers == 0) then leaderName = "CLEOPATRA"; numLayers = 4; end   -- 兜底
    for i = 1, numLayers, 1 do
        CreateBackgroundLayer(leaderName .. "_" .. i, ...);  -- ← 拼 <NAME>_<i>
    end
end
```

| | 链 A `background`（**role 名**） | 链 B `diplomacy_layer1..4`（**role 名**） | 链 C `DiplomacyInfo`（**数据表，不是 role**） |
|---|---|---|---|
| 用途 | 领袖**加载/选人界面**背景 | 外交**分层场景**（视差） | 外交背景**整图替换** |
| 贴图名 | `LEADER_<X>_BACKGROUND` | `<X>_1` … `<X>_4`（**无** `LEADER_` 前缀） | 任意名（项目自定） |
| 尺寸（原版实测） | **1920×960** | 层 1–3 **960×505**；层 4 **1920×1010** | 随源图（示例工程 用 1920×1080） |
| XLP | `Shell_Loading.xlp` | `UI_LeaderScenes.xlp` | 任一 `UITexture` 包 |
| 加载条件 | 无条件（按名自动找） | 仅当**没有** `DiplomacyInfo` 行时 | **有即优先**，压过链 B |
| 层数由谁定 | —（单图） | `Leaders.SceneLayers`（原版只有 0 或 4） | —（单图） |

**三条要点（都是实测/源码级结论）**：

1. **链 C 压过链 B**：只要 `DiplomacyInfo` 里有该领袖一行，引擎**只**用那一张图，
   `SceneLayers` 与 `UI_LeaderScenes.xlp` 的分层贴图**根本不会被读**。
2. **链 B 的条目名不带 `LEADER_`**：引擎 `gsub("LEADER_","")` 之后才拼 `_i`，
   所以查找的是 `CARTETHYIA_QYXP_2` 而**不是** `LEADER_CARTETHYIA_QYXP_2`。
   原版 pantry 三个 `UI_LeaderScenes.xlp` 共 174 条**全部无 `LEADER_` 前缀**；
   第三方教程参考工程同样是 `JASPER_KITTY_1..4`。
   → 写成 `LEADER_<X>_2` 是**死条目**：不会被查到，白注册。
3. **层 4 用别名**：官方惯例是层 4 复用 `BARBAROSSA_4`
   （`<m_EntryID text="<X>_4"/><m_ObjectName text="BARBAROSSA_4"/>`），前 3 层才是自绘。

> **示例工程 现状（2026-09-17 实查，仅上报未改）**：该工程**三条链都用了**——
> `Leaders.SceneLayers=4` + `UI_LeaderScenes.xlp` 注册了 18 条
> `LEADER_<X>_<2|3|4>`（带前缀，属上述死条目）+ `DiplomacyInfo` 6 行单图。
> 因链 C 优先，**实际生效的是 DiplomacyInfo 单图**，那 18 条分层条目不影响运行
> （既不生效也不报错）。若要清理，把 EntryID 的 `LEADER_` 前缀去掉即可让链 B 也有意义；
> 但**只要 DiplomacyInfo 还在，链 B 就永远不会被读**——二者留一即可。

**原版实测依据**（全 pantry 6 个 `Textures` 目录、12686 个 `.tex` 扫描）：
`LEADER_*_BACKGROUND` **42/42 全为 1920×960**；
`<LEADER>_1/_2/_3` 主体为 **960×505**（另有 DLC 的 934×505、944×505 等变体）；
`<LEADER>_4` 为 **1920×1010**；`LEADER_*_NEUTRAL` 高度为 1024 或 1080、**最宽 803**。
与第三方教程《Civ6 Modding Textbook》第 08 章实测一致
（其参考工程：`LEADER_JASPER_KITTY_BACKGROUND` 1920×960、`JASPER_KITTY_1..3` 960×505）。

> ❗ **2026-09-17 勘误（AI 自引入并已回退）**：本节一度被改成
> `background = 1920×1080`、`diplomacy_layer = "由 DiplomacyInfo 决定"`，**那是错的**，
> 成因是把链 C 串味成链 A/B。三者互不相同：
> `background`(链 A) ≠ `diplomacy_layer1..4`(链 B) ≠ `DiplomacyInfo`(链 C)。
>
> ❓ **仍存疑**：本表历史上的 `544×968` 在 pantry（12686 个 `.tex`）与教程参考工程中
> **均无先例**，尚不能确认它对应哪个对象；已从表中移除，未再断言。
> 若后续遇到该尺寸的原始出处，请补记于此。


**Atlas 图集命名约定（make_atlas.py 默认值即按此设计）：**
- 图集名统一以 `ATLAS` 起始；项目专属前缀（如示例中的 `MYMOD`）不属于本 skill 职责，由项目自身规范定义，下面用 `{PREFIX}` 占位。
- DDS 文件名：`ATLAS_{PREFIX}_ICON_{类别}{尺寸}`，或自定义模板（如 `{PREFIX}_Icon_{类别}{尺寸}`）——用 `filenamePattern` 表达；
- IconTextureAtlases.Name：`ATLAS_{PREFIX}_ICON_{类别}`；多格图集 Filename 带 `.dds` 后缀，1×1 单图集不带（make_atlas 自动处理）；
- 字体图集（FontIcon / `Baseline` 场景）：使用 `ATLAS_{PREFIX}_FONT_ICON_{类别}`，必须带 `Baseline` 属性；不要与普通 UI 图集共用 `ATLAS_{PREFIX}_ICON_` 命名。
- **FontIcon（文本内嵌图标）：注册不带 `ICON_` 前缀，引用必须带 `ICON_` 前缀。** 两件事必须分开记：
  - **注册**：`IconDefinitions` 的 `Name` **不加 `ICON_`**。官方 `Base\Assets\UI\Icons\FontIcons.xml` 的 280 条定义**全部**如此（`Housing`/`Culture`/`Food`/`Envoy`/`Science`/`Gold`…，一条带前缀的都没有）。本项目同理：`RESOURCE_VISCUM_RGN`、`DISTRICT_GONDOLA_RGN`、`AUTHORITY_POINT_RGN`、`INSPIRATION_POINT_CCN`、`SECRETSOCIETY_GOLDEN_ANTHEM_RGN`。
  - **引用**：文本里写 **`[ICON_<注册名>]`** —— 官方文本写 `[ICON_HOUSING]`/`[ICON_Culture]` 去命中定义 `Housing`/`Culture`。即 **`ICON_` 是文本图标解析器的固定前缀，与注册名无关**。
  - 解析**大小写不敏感**：`[ICON_CULTURE]` 与 `[ICON_Culture]` 等价（官方文本两种写法都有）。
  - 这些条目必须放在 `IconDefinitions` 的 Font Icons 模块内，与其他 font 条目放在一起。
  - ⚠ **反例（2026-09 本项目真实踩过）**：`GreatWorkObjectTypes.IconString` 写成 `[GREATWORK_TREASURE_QYQXP]`（**漏了 `ICON_`**）→ 该珍物图标不显示；正确写法是 `[ICON_GREATWORK_TREASURE_QYQXP]`。
  - ⚠ **别把"注册带前缀"当成能让文本引用的办法（本项目 2026-09 已修的真实案例）**：原先 `Data/Icons_RGN.xml` 里对 `ICON_RELIGION_ORDER_OF_THE_DEEP_RGN` 做了"同名再挂字体图集"，注释称"文本内 `[ICON_...]` 解析走 FontIcons 通道"。这是错的，且一次踩两个坑：
    1. 文本 `[ICON_RELIGION_ORDER_OF_THE_DEEP_RGN]` 只会去找**名为 `RELIGION_ORDER_OF_THE_DEEP_RGN`** 的定义，带前缀的那条**永远命中不了**；
    2. **同名重复注册**（一次普通图集、一次 22px 字体图集）会让 `ICON_RELIGION_ORDER_OF_THE_DEEP_RGN` 在 `IconDefinitions` 里只指向 22px 字体图集 —— 非文本取图（50/100/270）随之失效。
    **正确写法**：普通图集保留 `ICON_RELIGION_ORDER_OF_THE_DEEP_RGN`（供 UI 按名取图），另在字体图集上加一条**不带前缀**的 `RELIGION_ORDER_OF_THE_DEEP_RGN`（供 `[ICON_RELIGION_ORDER_OF_THE_DEEP_RGN]` 文本解析）。二者**名字不同**，各司其职。
- FOW 变体：独立一条 atlasEntries（如 `ATLAS_{PREFIX}_ICON_{类别}_FOW`），只出 256 一版全网格；
- IconDefinitions（普通/显示图标）：组员顺序 = Index（行优先），组员 tech 写 `ICON_*` 全名；FontIcon 文本条目例外，按上一条不加 `ICON_` 前缀。
- **重采样说明**：make_atlas 小尺寸缩放用 Pillow LANCZOS（锐利度优于普通插值），
  与旧序列图合成工具（普通插值）的输出允许像素级差异——尺寸/网格/命名完全一致，
  仅像素级更锐；重生成覆盖旧 DDS 前须向用户说明此差异（一致性上报守则）。

### 三.2 单位立绘（unit_portrait）与伟人立绘（great person portrait）

> 官方来源：`Base/Assets/UI/Icons/Icons_UnitPortraits.xml`、`Icons_GreatPeople.xml`、
> `PortraitSupport.lua`、`GreatPeoplePopup.lua`。本子节解决"单位立绘怎么注册、伟人立绘为什么不一样"。

#### A. 普通单位立绘（Unit Portrait）

- 尺寸：`unit_portrait` = **38 / 50 / 70 / 95 / 200 / 256**（六档）。
- 命名：`ICON_UNIT_<UnitType>_PORTRAIT`（1×1 单图集 Index=0 即可）。
- 官方解析链（`PortraitSupport.lua`，按序回退）：
  1. `ICON_[ETHNICITY_]<UnitType>_PORTRAIT_<ERA>`（如 `ICON_ETHNICITY_ASIAN_UNIT_X_PORTRAIT_RENAISSANCE`）
  2. `ICON_[ETHNICITY_]<UnitType>_PORTRAIT`
  3. `ICON_<UnitType>_PORTRAIT_<ERA>[_F/_M]`
  4. `ICON_<UnitType>_PORTRAIT[_F/_M]`
- 族裔前缀：文明 `Ethnicity` 非 `ETHNICITY_EURO` 时，UI 会带 `ICON_ETHNICITY_<ETH>_` 前缀；
  若项目文明是 `ETHNICITY_EURO`（如 RGN），**不需要**注册族裔前缀条目。
- 伟人单位额外有性别后缀 `_F/_M`（`GetGreatPersonGenderSuffix`），可按需注册
  `ICON_UNIT_<Type>_PORTRAIT_F` 等女性/男性变体。

#### B. 伟人立绘（Great Person）—— 与普通单位立绘是两套系统

1. **伟人招募面板头像（Great People Popup）**：
   - 名称 = `ICON_GENERIC_GREAT_PERSON_INDIVIDUAL_<CLASS>`（由 `GreatPeoplePopup.lua` 从 class 名生成，
     把 `GREAT_PERSON_CLASS_X` 的 `_CLASS` 替换为 `_INDIVIDUAL`）。
   - 图集 = `ICON_ATLAS_GREAT_PERSON_INDIVIDUAL`，**IconSize 105 / 216**（3×3 网格），
     官方 9 个职业通用头像（ADMIRAL/ARTIST/ENGINEER/GENERAL/MERCHANT/MUSICIAN/PROPHET/SCIENTIST/WRITER）。
   - **官方没有为每个伟人个体做专属立绘**；自定义伟人 class 时，要显示头像需注册
     `ICON_GENERIC_GREAT_PERSON_INDIVIDUAL_<自定义CLASS>`（可指向官方 generic 图集对应职业 Index，
     或自定义 105/216 图集）。
   - 若复用官方 class（如 `GREAT_PERSON_CLASS_MUSICIAN`），面板头像自动用官方 generic，无需注册。

2. **伟人单位的地图/单位面板立绘**：仍走普通 Unit Portrait（A），即 `ICON_UNIT_<Type>_PORTRAIT`。

3. **`GreatPersonIndividualIconModifiers.OverrideUnitIcon`**：只覆盖地图上的单位图标/旗帜，
   **不是**立绘；不要与 portrait 混为一谈。

4. 兄弟项目参考：Jinhsi 的自定义伟人同时注册了
   `ICON_UNIT_<自定义伟人单位>_PORTRAIT`（单位立绘 38~256）和
   `ICON_GENERIC_GREAT_PERSON_INDIVIDUAL_<自定义CLASS>`（招募面板头像，复用官方 generic Index），
   两者缺一不可。

## 四、图标规范化（icon normalization）—— 每类 Icon 遵守对应规范

> **背景**：不同来源的图标源图（画布尺寸、边距、内容填充率、是否贴边各不相同）若直接
> 进 `convert_art.ps1`（`-w/-h` 硬拉伸）或 `make_atlas.py`（正方形整体 resize），会被无脑拉伸 /
> 直接等比缩放，导致最终图标**视觉权重不均、贴边或失衡**。本节定义"先规范化、再转 DDS"的
> 专属流程，**每类 Icon 遵守各自的规范**。

### 4.1 规范结构（每类 Icon 一份）

| 字段 | 含义 |
|---|---|
| `canvas` | 统一主画布边长（该类别的最大档/基准档，px） |
| `content` | 内容最长边目标（px），占画布比例 = content/canvas |
| `color` | 剪影填充灰度（R=G=B）；彩色图标为 `None` 保留原色 |
| `status` | `verified`（已调研验证） / `inferred`（由其他类别推断，兜底） / 未定 |
| `source` | 规范依据/来源 |

引擎：`art/normalize_icon.py`（内置上述 registry `ICON_SPECS`，可 CLI / 模块 / manifest 调用）。

### 4.2 Units 图标规范（本次调研 · 已验证 verified）

- 来源：`F:\Steam\...\Base\Assets\UI\Icons\Icons_Units.xml`（`ICON_ATLAS_UNITS`
  256/80/50/38/32/22 六档 + FOW 32）+ 项目 12 个新增单位源实测。
- 参数：`canvas=256`、`content=224`（**占幅 ≈87.5%**）、`color=255`（白色剪影）、
  几何居中 → 四周统一边距 **≈16px**。
- **占幅要点**（本次新增的核心信息）：
  - 内容最长边缩放到 224px（256 画布的 87.5%），保持宽高比、等比 contain 居中；
  - 不裁剪主体、不拉伸；源图贴边/边距不均会被吸收（统一到 ~16px）；
  - **仅狭长图标**（长短边比 ≥1.3，如细高/细宽的单位剪影）允许长边直接平齐画布边缘
    （full-bleed，`--slender-flush` 显式开启）；非狭长图标不适用该规则；
  - 保留白色 R=G=B=255 + Alpha 定形（供游戏按玩家/文明色着色）；
  - FOW 变体单独 32（见第九节 apply_fow.py）。

```bash
# 按内建规范规范化单张
python art/normalize_icon.py --role unit_icon <源.png> <输出.png>
python art/normalize_icon.py --role unit_icon --show        # 查看该类别规范参数
```

### 4.3 其他 Icon 类别：下次触发时的三选一（必问，禁止默认）

未验证类别（building/district/wonder 等，registry 中 `status=inferred` 或未登记）**下次触发时**
（即用户给该类别素材、要求转换/导入时）必须先问用户选哪种：

1. **调研新规范**（推荐）：按 Units 的调研方式定位该类别原版规范（找 `Icons_*.xml` +
   社区笔记 + 项目实测），验证后把参数固化进 `ICON_SPECS`（`status=verified`）。
2. **原图直接入库**：用户自行处理好的/特殊的图（如 Leader 可能由用户仔细处理后才导入），
   **跳过规范化**（manifest `normalize:false` 或不写），以用户构图为准原样缩放。
3. **据其他规范推断**（兜底）：从相近类别推断参数，但**必须标记 `status=inferred`** 并
   在交付说明里注明"推断值，未经该类别专项验证"，下次仍回到三选一确认。

> 铁律衔接：本流程不豁免第一节「素材询问铁律」——处理素材前仍需先问来源/命名/多图意图；
> 三选一是在此基础上额外的一次询问。

### 4.4 manifest 接入（可选字段，默认关闭）

`entries` 与 `atlasEntries.members` 均支持（`normalize:true` 才启用）：

```jsonc
{ "tech": "ICON_UNIT_X", "role": "unit_icon",
  "source": "x.png", "normalize": true,      // 打开规范化预处理
  "canvas": 256, "content": 224, "color": 255 }  // 可选覆盖；缺省走 role 规范
```

- `normalize` 缺省 **false**＝保留现有直接缩放行为（用户构图原样入库 / 未咨询前不动）；
- 打开时：先 `normalize_icon.py` 规范化 → 再走 convert_art / make_atlas 转 DDS。
- `make_atlas.py` / `convert_art.ps1` 未内置调用，由 AI 在 manifest 里**先跑 normalize 再喂给转换器**
  （或在转换脚本内 import 处理；本 skill 优先在 AI 流程里显式两步，便于审计与回退）。

> **嵌套项目路径坑**：`make_atlas.py` 自动探测 Textures 目录依赖 `.civ6proj` 父目录名；
> 当工程目录本身带嵌套（如 `示例工程/示例工程`）时会多嵌一层 `示例工程/Textures`。
> 遇到此类结构请在 manifest 显式写 `texturesDir`（指向真实 `Textures/`），避免 DDS 落错目录。

### 4.5 `building_icon` 规范（2026-09 实测 · verified）

来源：`SDK Assets\Civ6\pantry\Textures\Buildings{32,38,50,80,128,256}.dds` 全 50 格逐格实测，
对照 `Base\Assets\UI\Icons\Icons_Buildings.xml`（`ICON_ATLAS_BUILDINGS`）。

| 字段 | 值 | 依据 |
|---|---|---|
| `canvas` | 256 | 最大档 |
| `content` | 210（细高/细宽 ≤0.65 时 215） | 总占幅 86.7%（细高 88.7%），落在原版 p75~p90 |
| `color` | **None（保留原色）** | 彩色 diorama 渲染，改色即返工 |
| `outline` | `{px: 6, rgb: [0,0,0]}` | 原版 alpha 边界内 d1~4 纯黑、d5 过渡 |

- 原版主体最长边占画布 **61%~96%，中位 82.6%**，几何居中。
- **描边宽度靠距离变换校准**：用本引擎扫 px=4..8，取「深度-亮度剖面最贴原版」的值——
  `px=6` → d1~7 `[0,0,0,0,51,113,143]`；原版 `[0,0,0,0.5,35,110,127]`（MONUMENT）/
  `[0,0,0,0.8,47,126,144]`（LIBRARY）。`px=5` 细 1px、`px=7` 偏粗。
- 细高档参考：原版 CATHEDRAL 88%、GURDWARA 90%、BROADCAST_CENTER 86%、FILM_STUDIO 90%。
- 建筑**有** FOW 变体（原版 `ICON_ATLAS_BUILDINGS_FOW`，只 256 单档），用 `apply_fow.py` 出。

### 4.6 `project_icon` 规范（2026-09 实测 · verified）

来源：`SDK Assets\Civ6\pantry\Textures\Projects{30,32,38,50,70,80,256}.dds` 全 18 格实测，
对照 `Icons_Projects.xml`（`ICON_ATLAS_PROJECTS`，尺寸档 **30/32/38/50/70/80/256**）。

- 原版项目图是**固定模板**：六边形边框 + 描边 **`rgb=(0,25,45)` = `#00192D`**（18 格全一致，±0.3）
  + 内部白色浮雕；主体 bbox ≈ **208x235**、最长边 **92.6%**。
- **任意美术都无法靠几何规范化变进这个模板**。成品图（美术已按模板做好）应 `normalize:false`
  **直接入库**；本规范只用于**校验**：量 `outline_rgb` 是否 ≈(0,25,45)、bbox 是否 ≈208x235。
- 源图不是成品时：`outline={px:6, rgb:[0,25,45]}` 只能补描边，补不出六边形边框 → 找美术。
- 原版**没有** `_FOW` 变体，**不要**出 FOW。

### 4.7 新类别怎么「调研出」规范（可复用流程，替代拍脑袋推断）

第四节 4.3「三选一」里选「调研新规范」时照这个流程走，每步都有确定性判据：

1. **拿原版图集**：`SDK Assets\Civ6\pantry\Textures\`（Buildings*/Projects*/Districts*…）；
   DLC/资料片在 `SDK Assets\Civ6\DLC\<资料片>\pantry\Textures\`。同名 `.tex` 可读官方尺寸档，
   网格与 Icon 名从 `Base\Assets\UI\Icons\Icons_<类别>.xml` 取。
2. **切格**：图集是 `IconsPerRow x IconsPerColumn` 网格（多为 8x8），按 Index 行优先切单图。
3. **量占幅**：统计每格 `alpha>8` 的 bbox，得到最长边占比的 min/p10/median/p90/max；
   中位做 `content`，p75~p90 做「偏满档」；再看有没有「细高/细宽」子族需要单独放宽。
4. **量描边**：对 `alpha>128` 做 `distance_transform_edt`，统计**距边界第 d 圈的亮度与颜色**。
   描边宽度 = 亮度≈0（或等于描边色）的最大 d；`outline.rgb` 取那几圈的**逐通道均值**——
   务必按通道取，别只看亮度：项目图是藏青 (0,25,45) 不是黑，只看亮度会误判成「纯黑」。
5. **校准**：把 `outline.px` 喂给本引擎，扫 ±2px，取「深度-亮度剖面最贴原版」的值。
6. **固化**：写进 `normalize_icon.py` 的 `ICON_SPECS`，`status="verified"`，`source` 写明
   量自哪个图集/多少格/日期，再回填本文件。

### 4.8 素材暂存目录被删/不在本机时怎么办

- 用户删掉暂存目录（如 `D:\desktop\XXX_RGN`）是**持久意图**，不要去找回或重建。
- 已入库的素材应能在**工程内自洽重建**：成品源图放 `workspace/src/<类别>/`（含 `raw/`），
  manifest 指向工程内路径而不是桌面路径 —— 否则桌面一清空，`make_atlas.py` 下次必炸。
- 源图只剩桌面路径时：先把 manifest 改成工程内副本再转换。

> ⚠ **中间档源图陷阱（2026-09 真实踩坑，会造成"修好了又变回锯齿"）**
>
> 很多素材目录里**每个尺寸档都存了一份独立 PNG**（`ATLAS_X32.png`、`ATLAS_X45.png`…
> 与 `ATLAS_X256.png` 并列）。这些**小档 PNG 往往本身就是被锐化/压对比过的成品**
> —— 也就是第 8.1 节那个"锯齿损伤"的原始来源。
>
> **后果**：若 manifest 的 `members` 指向小档 PNG，或将来有人"照目录里的文件名"重跑
> `make_atlas.py`，就会把损伤**原样再产出一遍**，而 `--edge-qa` 又会报 DAMAGED，
> 看起来像"修了没用"。
>
> **规矩**：图集重建**一律以最大档（256）为唯一母版**逐格降采样；
> **永远不要**把 `ATLAS_X{32,45,50,80…}.png` 这类小档当成"源素材"使用。
> 判断方法：若某档的 `mid`（边界中间调占比）显著低于母版重出值，它就是受损产物，不是素材。
> 本项目 `D:\desktop\Material\Image-Rinascita\Atlas_Rgn\{Leaders,Distrits,Resources,Monopoly}_Atlas\`
> 下的小档 PNG **全部属于此类**（2026-09 实测；256 母版无此问题）。

### 4.9 `improvement_icon` 规范（2026-09 实测 · verified）

来源：`SDK Assets/Civ6/pantry/Textures/UnitActions{38,50,80,256}.dds` 的 23 个
`ICON_IMPROVEMENT_*` 格逐格实测，对照 `Base/Assets/UI/Icons/Icons_UnitActions.xml`。
**原版改良设施图标不在独立图集**，就挂在 `ICON_ATLAS_UNIT_ACTIONS`，尺寸档 **38/50/80/256**。

| 字段 | 值 | 依据 |
|---|---|---|
| `canvas` | 256 | 最大档 |
| `content` | 224（87.5%） | 实测主体最长边占画布 85.5%~100%（中位 92.6%）；取区间内保守值，与 `unit_icon` 口径一致（源图本身偏满可显式传 `--content 235`） |
| `color` | **None（保留原色）** | 原版是浅蓝灰插画（亮度 113~177 / 饱和度 5~25 / 近白像素仅 0~7%），改色即返工 |
| 描边 | 无 | 原版改良图标无附加描边 |
| FOW | **不出** | 原版改良设施没有 `_FOW` 图集 |

- 实测占幅明细（23 格，最长边 / 画布）：BARBARIAN_CAMP 90.6%、FARM 86.3%、MINE 90.6%、
  QUARRY 87.5%、FISHING_BOATS 100%、PASTURE 99.6%、PLANTATION 87.1%、CAMP 87.9%、
  LUMBER_MILL 86.7%、OIL_WELL 93.8%、OFFSHORE_OIL_RIG 85.5%、FORT 96.1%、AIRSTRIP 97.7%、
  BEACH_RESORT 92.6%、MISSILE_SILO 97.7%、CHATEAU 95.3%、COLOSSAL_HEAD 85.5%、GREAT_WALL 97.3%、
  KURGAN 93.8%、MISSION 86.3%、SPHINX 96.9%、STEPWELL 88.3%、ZIGGURAT 100%。
- 取图位置提醒：科技树解锁项按 **38px** 取图（`TechAndCivicSupport.lua` →
  `IconManager:FindIconAtlas(iconName, 38)`），建造按钮用 50px —— **四档缺一不可**。
- 首用案例：示例工程 神秘气泡 `ICON_IMPROVEMENT_BUBBLES_RGN`（源图白色剪影 128x128，
  按 `content=224` 规范化后入 `ATLAS_RGN_ICON_IMPROVEMENTS{38,50,80,256}`，
  管线留档 `workspace/src/improvement_icons/`）。

```bash
python art/normalize_icon.py --role improvement_icon <源.png> <输出.png>
python art/normalize_icon.py --role improvement_icon --show
```


## 五、通用转换约定（内置在 convert_art.ps1 / make_atlas.py，AI 只选 role）

- 图标类 role：多尺寸 DDS（上一节全表）；非图标 role：原尺寸单 DDS。
- 图标源图建议 ≥256×256 正方形；输出各尺寸由 texconv 缩放（atlas 组员由 Pillow 缩放后拼版）。
- 所有 DDS 统一 `R8G8B8A8_UNORM` 且**一律单 mip**：texconv 必须显式 `-m 1`——缺省或 `-m 0` 都会生成完整 mip 链（如 1440 宽图 11 级、体积 +1/3），与 AssetEditor `.tex` 的 `bUseMips=false` 约定冲突。转换后核对 DDS 头 `mips=1` 与文件大小再交付。
- **技术名区分大小写**（schema pattern 已放开）：忠诚度贴图为混合大小写（`Loyalty_Overlay_*`、`StrategicView_Loyalty_*`），artdef/XLP 引用处必须逐字符一致。

### 关于 NVIDIA Texture Tools（NVTT）—— 用不上，且**不随包**

本机若装了 **NVTT（NVIDIA Texture Tools Exporter / `nvtt_export.exe`）**，注意它**不是本管线的依赖**：

- **格式用不上**：NVTT 的强项是 BC1–BC7 / BC6H / ASTC 等 GPU 压缩格式，而 Civ6 工程 DDS
  **一律未压缩 `R8G8B8A8_UNORM`**（本节上一条 + 实测：本项目 238 个 DDS 全部为 RGBA8）；
  多 mip 也只出现在领袖立绘/压力图这类 `bUseMips=true` 的资产上，由 `.tex` 声明，**不需要外部压缩器**。
- **PNG→DDS 已有内置件**：走 `art/bin/texconv.exe`（Microsoft DirectXTex，**MIT，随包分发**）。
- **许可不同（关键）**：NVTT 是 NVIDIA **专有 SDK 许可**（`LICENSE.TXT`），
  **不满足 `art/bin/` 的「许可允许再分发」准入条件**，因此**不进随包目录**；
  只在 `tools/_paths.py` 登记**可选**路径键 `nvtt_dir`（缺失即返回 None，任何流程不得依赖它）。
- **唯一残余用途是诊断**：`nvddsinfo` 看 DDS 头、`nvimgdiff` 比两图。
  但同类需求优先用**零依赖**的 `art/dds_io.py --selftest`（纯标准库 + Pillow，只读 128 字节头）。

> 一句话：**不要为了转 DDS 去装 NVTT**，也不要把它放进随包目录。

### manifest 示例

```jsonc
{
  "projectRoot": "D:\\documents\\Firaxis ModBuddy\\Civilization VI\\MyMod",
  "entries": [
    { "tech": "ICON_LEADER_CTTH",          "role": "leader_icon", "source": "卡提希娅-领袖图标.png" },
    { "tech": "LEADER_CTTH_FOREGROUND",    "role": "portrait",    "source": "D:/美术/卡提希娅立绘.png" },
    { "tech": "ICON_CIVILIZATION_MYMOD",     "role": "civ_icon",    "source": "拉古纳文明图标.png" }
  ],
  "atlasEntries": [
    {
      "atlas": "ATLAS_MYMOD_ICON_LEADERS",
      "grid": { "cols": 3, "rows": 2 },
      "role": "leader_icon",
      "members": [
        { "tech": "ICON_LEADER_CANTARELLA_QYQXP", "source": "坎特蕾拉.png" },
        { "tech": "ICON_LEADER_CARTETHYIA_QYQXP", "source": "卡提希娅.png" }
      ]
    },
    {
      "atlas": "ATLAS_MYMOD_ICON_PRODUCT",
      "grid": { "cols": 3, "rows": 3 },
      "sizes": [32, 38, 45, 50, 64, 256],
      "filenamePattern": "MYMOD_Product_Icons{size}",
      "members": [
        { "tech": "ICON_GREATWORK_PRODUCT_AUREO_MYMOD_1", "source": "奥利薇.png" }
      ]
    }
  ]
}
```

## 六、.tex 编码（重要坑，生成 .tex 时才需要知道）

AssetEditor（WinForm/.NET）读取 `.tex` 用**系统 ANSI 代码页**（中文系统 = GBK），不是 UTF-8：
`m_SourceFilePath` 含中文路径时写 UTF-8 会被 GBK 误读成乱码并令 AssetEditor 崩溃。
`art\gen_tex.py` 已内置正确处理：用 `GetACP()` 取真实代码页写出（勿用
`locale.getpreferredencoding`——Python UTF-8 模式下它误报 utf-8）；代码页装不下字符时退用
XML 字符引用转义，文件仍是合法 XML。**不要手工把 `.tex` 另存为 UTF-8。**

## 七、缺图过滤语义

- manifest 中 source 文件不存在 → 该条跳过（打印 skip），对应 XLP 条目**不写**；
- atlas 条目：单个组员缺图 → 网格留空位并 WARN（其余组员 Index 不变）；
  全部组员缺图 → 整组跳过；
- 某 XLP（Icons.xlp 等）按实存 DDS 过滤后一条不剩 → 整个文件不生成，Art.xml 不引用；
- 用户删除的图不重建、不恢复（删除 = 持久意图），仅向用户提醒缺失清单。

## 八、完成标准（对照验证）

1. `Textures\` 下 DDS 数量 = Σ(各 entry 尺寸数) + Σ(各 atlas 条目尺寸数)，每个 DDS 有同名 `.tex`；
2. atlas 画布尺寸 = (IconsPerRow×s, IconsPerColumn×s)，注册片段的 Name/Filename/Index 与
   项目 Icons XML 现状风格一致；
3. XLP 引用的每个纹理都能在 `Textures\` 找到（无悬空引用）；
4. Art.xml / `.civ6proj` 条目与磁盘一致（Project 文件同步规范）；
5. 若本次新增/修改了 `XLPs\` 或 `ArtDefs\` 文件：`gen_modartxml.py <projectRoot> --check`
   必跑，差异人工确认后才 `--write`（新增 XLP/Artdef 不重生成 Art.xml = 最常见的漏项）；
6. 未动用户未确认的任何素材文件；
7. **各尺寸档的边缘抗锯齿质量合格**：`verify_icon_atlas.py <projectRoot> --edge-qa` 必须通过
   （见第 8.1 节）。这是唯一能抓出「结构全对、实机却是锯齿」的门。

### 8.1 边缘质量门（`--edge-qa`）—— 中间档锯齿 / 硬边的唯一防线

**症状**：游戏内图标（尤其 frontend 小尺寸档）肉眼可见线条锯齿、硬边、毛刺。

**成因**：图集的**中间档**（32/45/50/80/128…）本应从最高分辨率母版逐格等比降采样。
若这些小档不是从母版缩出来（链式缩放 / 有损来源反复转存），或缩完之后又被
**锐化 / 对比拉伸（levels）**，抗锯齿的过渡像素会被推向 alpha 两端，边缘退化成「二值硬边」。
**母版（256）本身往往是好的，所以肉眼看母版永远看不出问题。**

**为什么必须单独设门**：这类损伤**结构完全合法** —— 引用闭合、画布尺寸对、`.tex` 对齐、
格子非空、mips=1，第 1–6 项**全部 PASS**。本项目 2026-09 实测 **4 个图集共 22 个中间档**
中招（`ATLAS_RGN_ICON_LEADERS` 7 个、`ATLAS_RGN_ICON_DISTRICTS` 6 个、
`ATLAS_RGN_ICON_PRODUCT` 5 个、`ATLAS_RGN_ICON_RESOURCES` 4 个），结构校验一路绿灯，
而实机图标全是锯齿。

**判据**（对每个含 256 母版的图集，把「母版逐格 LANCZOS 重出」当**应有值**）：

| 指标 | 含义 | 受损特征 |
|------|------|---------|
| `mid` | 边界像素落在中间调 (20..235) 的比例% | 骤降（抗锯齿过渡被掏空） |
| `hard` | 相邻 alpha 跳变 >200 的比例% | 升高（边缘变硬） |
| `ratio` | 半透明像素数 ÷ 边界周长（形状无关） | 骤降（每单位边缘长度的过渡像素变少） |

判受损：`mid < 参考 - 8`（百分点）或 `ratio < 参考 × 0.7`。阈值可用
`--edge-tolerance` / `--edge-ratio` 调整。

**实测对照**（本项目 Leaders 45px，修复前 → 后）：

| | 边界中间调占比 | 二值端占比 | 过渡像素÷周长 | 内部 Laplacian |
|---|---|---|---|---|
| 受损档 | 20.4% | 74.7% | 0.59 | 23026 |
| 修复后 | 43.6% | 49.7% | 1.79 | 7408 |
| 原版参考 | 45.1% | 51.3% | 0.65 | 6947 |

注意**关键反直觉点**：受损档的内部高频（Laplacian）**高于**健康档 3 倍 ——
因为锐化在压边缘的同时也放大了内部噪点。「清晰度变好」不等于「边缘更宽」，而是
「不再有假的硬跳变」。

**修复**：用 `regen_atlas_tiers.py` 从母版逐格 LANCZOS 重出（下一节），
**不需要改 `.tex` / 网格 / 注册链**（尺寸完全不变）。

> **「重出结果是否等于既有档」的预期要摆正**（2026-09 实测）：
> 把「母版逐格 LANCZOS」对上工程既有**健康**档，**不是**逐字节相同 ——
> 实测 5 个图集 28 档中只有 `RGN_Icon_Projects`（6 档）逐字节一致，
> 其余（Units / Buildings / GreatWorks / UnitPortraits）边缘 alpha 有 0~56/255 的差异
> （不同滤波器族或不同工具的舍入），但**边界中间调占比差 ≤0.68pp**、不透明区 RGB 差 ≤0.6
> ⇒ **质量等价**。
> 对照：**受损**档修复前后差 **20+pp**、alpha 差达 **227/255**。两者差 3~4 个数量级。
> 所以自证判据用「**中间调差异 ≤2pp**」而不是「逐字节相同」；
> 逐字节只在"同一工具同一参数"时才有意义，跨工具/跨滤波器族不成立。

```bash
# 体检（不写盘，退出码 2 = 发现受损档）
python art/regen_atlas_tiers.py <projectRoot> --report
# 一次修好全部受损档
python art/regen_atlas_tiers.py <projectRoot> --report --write-damaged
# 复核
python art/verify_icon_atlas.py <projectRoot> --edge-qa
```

**无 256 母版的图集不在体检范围**（如通知 40/100、按钮 38/44/52、总督 1×1 各档）：
它们没有可当"应有值"的高分辨率源，本门跳过；如需覆盖，先补一份 256 母版。
（**单档贴图**也可用 `regen_atlas_tiers.py --file` 手工重出，见第 8.2 节。）

### 8.2 `.tex` 格式对齐官方（`align_tex_format.py`）

`.tex` 是 AssetEditor 的贴图元数据。由不同批次/工具生成的工程里常出现**格式类**
偏差（不影响当前构建，但会造成编码乱码风险、与官方结构不一致、语义相悖）：

| 字段 | 官方约定（全 SDK 12709 个 `.tex` 实测） | 本工程 2026-09 实测偏差 |
|------|--------------------------------------|----------------------|
| XML 声明 + 字节编码 | **100% UTF-8** | 77 个声明为 GBK |
| `m_Groups` | 多数为自闭合 `<m_Groups/>` | 210 个缺失 |
| 行尾 | **100% LF** | 已一致 |
| `bCompleteMipChain` | **按 `m_ClassName` 逐类决定** | 7 个与同类别官方相反 |
| `useMips` / `m_NumMipMaps` | `numMipMaps = DDS mips - 1`（官方不变量） | 226/226 合规 |

**只改格式、绝不改值**。工具坚决不碰：
`m_Width`/`m_Height`/`ePixelformat`/`m_ClassName`/`m_SourceFilePath`/`m_Name`/`m_RelativePath`/`m_Tags`、
以及 `m_CookParams` 内的**参数值**。

⚠ **`m_SourceFilePath` 必须保持本工程的 `D:/desktop/<stem>.png` 虚拟路径**，
严禁改成官方 pantry 的 `//civ6/main/ArtDev/...` depot 路径（AGENTS.md 硬性约定：
depot 路径在 pantry 里会让 AssetEditor 崩溃/找不到源）。本工具不碰该字段。

**`bCompleteMipChain` 为什么按类别而不是一刀切**：官方统计显示它**不是全局常量** ——
`Generic_*`/`StrategicView_*`/`Leader_*` 等 3D 与 sprite 类几乎 100% 为 `true`，
而 `TerrainElementHeightmap`/`ColorKey` 等 100% 为 `false`；
`UserInterface` 则是 `true` 69% / `false` 31%（**未达阈值，故意不动**）。
工具内置 `COMPLETE_POLICY` 表，只对「官方同类别一致率 ≥80%」的类生效。

⚠ **编码转换的安全前提**：`gen_tex.py` 的 docstring 警告
「.tex 若写 UTF-8，AssetEditor 按 GBK 解读会乱码崩溃」——
该风险**仅在内容含非 ASCII 字节时成立**（如中文 `m_SourceFilePath`）。
本项目 226 个 `.tex` **全为纯 ASCII**（pantry 文件名与虚拟路径均 ASCII，见 AGENTS.md），
ASCII 在 GBK/UTF-8 下**字节完全相同**，故改声明+改写出编码**零风险**。
工具会先校验：若发现非 ASCII 内容，应停止并人工确认。
（注意：新建 `.tex` 时若源路径含中文，仍须按 `gen_tex.py` 的 ANSI 代码页规则写出。）

```bash
# 体检（退出码 2 = 有待改项）
python art/align_tex_format.py <projectRoot> --check [--list]
# 实际改写
python art/align_tex_format.py <projectRoot> --write
# 只处理部分项
python art/align_tex_format.py <projectRoot> --write --only encoding,groups,complete
```

改写后必跑不变量复核（宽高 / `numMipMaps = mips-1` / `useMips` 与 mips 一致 /
`m_Name` 与文件名一致 / 源路径仍为 `D:/desktop/`），并 `check_pantry.py` 确认 pantry 卫生。

## 九、FOW 迷雾变体（apply_fow.py）

原版 `*_FOW` 图标（迷雾中显示的变体）是"羊皮纸素描"风格。原版为逐图标手绘、
无法逐像素复刻；`art\apply_fow.py` 用官方
`F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets\Civ6\pantry\Textures\`
配对图集（Resources256 vs Resources256_FOW，逐桶 RGB 实测）拟合的两段式变换复刻：

1. **金调 LUT**：亮度→颜色映射，B 通道全程压低（金棕而非灰白——首版管线 B 通道
   抬太高导致灰白感，已修正）；暗部 L<40 保持深线稿色 (76,60,14)，平坦中段陡升为
   羊皮纸金，亮部为亮卡其 (218,192,100)；
2. **暗部加权排线**：45° 排线不透明度随原亮度衰减 ((1-L/255)^gamma)，阴影处排线浓、
   高光干净，近似官方"阴影用排线填充"的素描感。

```bash
python <skill>\art\apply_fow.py --input <图标.png|dds> [--output <路径>] \
    [--hatch-strength 0.62] [--ink-strength 0.55] [--strength 1.0] \
    [--no-hatch] [--no-ink] [--no-vignette]
```

- 默认输出 `<输入名>_FOW.png`；支持图集（整图处理）与 DDS 源（自动转 RGBA）
- **alpha 完整保留**（含半透明边缘）；排线只画在主体不透明区（alpha>128）
- `--no-hatch` 纯调色；`--strength <1` 与原色混合
- 产出后走常规转换：entries 用 `role=fow`（原尺寸单 DDS，与普通版同尺寸同格）；
  atlas 参照第三节 FOW 变体约定（独立 atlasEntries、只出 256 全网格）
- Data 侧按原版惯例登记 `ICON_XXX_FOW` 条目（与普通版同 atlas 同 Index 或独立 FOW atlas）
- 最像原版的做法仍是美术手绘；本工具用于程序化快速产出，效果可先出图给用户审核


---

## 九·补、工坊预览图（`make_workshop_preview.py`）

工坊预览图（Steam cover，即上传工作区的 `image.png`）是**唯一有「≤ 1 MB 硬上限」**的素材，
很容易为了压体积而做糊。2026-09 本项目实测把根因定位清楚了：**不是尺寸、也不是源图质量，
而是缩放方式**——

| 同一源图 → 同一目标尺寸的缩放方式 | 锐度（Laplacian 方差） |
|---|---|
| ImageMagick **默认滤镜 / Mitchell**（`magick -resize` 不写 `-filter` 时走这条） | 2,592.6 |
| `-filter Lanczos` 单步 | 4,842.4 |
| **Lanczos 逐级减半 + unsharp**（采定） | **13,047.4** |

即"封面太模糊"几乎总是**单步降采样 + 默认滤镜偏软**造成的，与母版好坏无关。

**采定管线**（`art/make_workshop_preview.py`，由 `tools/workshop_cover.py` 复用）：

1. 剥掉无用 alpha（母版 alpha 恒 255 时纯属浪费编码）；
2. **Lanczos 逐级减半**（3840→1920→960→512）——避免单步大幅降采样的混叠/发闷；
3. **unsharp 中度锐化**（`radius=0.7 percent=85 threshold=2`，等价 IM `0x0.7+0.85+0.02`）——
   锐化量经「锐度 vs 振铃」实测择优；
4. PNG 最高压缩 + strip。

```bash
python <skill>\art\make_workshop_preview.py <母版.png> --out <ws>\image.png --qa
python <skill>\art\make_workshop_preview.py <已有512.png> --out <ws>\image.png   # 直通，不重采样
```

**两条铁律**：

- ★ **已达标（512×512）的成品不要再缩**。工具对「输入 == 目标」默认**直通**（一像素不改），
  要强制重采样得显式 `--force-resize`。本项目台账记的验收口径就是「直接作为 `image.png` 上传、
  **不再二次缩放**」——上一轮那个 512 成品再缩一次只会更糊。
- ★ **不要用 `magick -resize` 裸缩**。默认 Mitchell 偏软；这也是为什么执行端用 Pillow
  （必须显式写 `Image.LANCZOS`，从根上消灭"忘写 `-filter` 就发糊"）。

**质量指标**（`--qa`）：`sharpness`（Laplacian 方差，采定档 ≈1.3 万）与 `ringing`
（锐化振铃，**相对未锐化参考**算，随锐化量单调：无锐化 ≈2.7 / 采定 ≈17 / 200% ≈31）。
振铃指标必须拿未锐化中间图当参考——用锐化图自身的邻居算会被源图纹理淹没而失效（实测过）。

## 十、art 目录工具索引（2026-09 汇总）

| 工具 | 干什么 | 何时用 |
|---|---|---|
| `normalize_icon.py` | 图标规范化（裁 bbox / 等比 / 居中 / 可选描边 / 可选剪影涂色）；`ICON_SPECS` 存各类别规范 | 转 DDS 前统一构图；`--role <类别> --show` 查规范 |
| `make_atlas.py` | 多图拼网格序列图集 → 逐尺寸 PNG → texconv DDS → `.tex` → **注册片段** | 多图合并成一张序列图时 |
| `convert_art.ps1` | 单图 → 多尺寸 DDS + `.tex` | 单图独立出图时 |
| `merge_icon_registration.py` | **幂等**把注册片段并入项目 Icons XML + 补 XLP 条目；保 BOM/CRLF | `make_atlas.py` 出完片段之后（别手工合并） |
| `verify_icon_atlas.py` | 落地自查：引用闭合 / 画布与网格一致 / mips=1 / **格子非空** / `.tex` 对齐 / XLP 无悬空 / 与官方重名；**`--edge-qa` 另查中间档边缘抗锯齿质量**（第 8.1 节） | **交付前必跑**（第八节的可执行版）；改了图集贴图再加 `--edge-qa` |
| `regen_atlas_tiers.py` | **图集中间档母版重出**：从最大档逐格 LANCZOS 重出各小档，修「被锐化/压对比 → 实机锯齿」；`--report` 体检、`--report --write-damaged` 一键全修；`--file` 可重出单档贴图（如字体图集） | `--edge-qa` 报 DAMAGED 时；或接手他人图集想确认中间档是否干净 |
| `align_tex_format.py` | **`.tex` 格式对齐官方**：统一 UTF-8 / 补 `m_Groups` / 按类别修正 `bCompleteMipChain`；**只动格式不动值**，且不碰 `m_SourceFilePath` | 接手他人工程的 `.tex`、或发布前统一格式；见第 8.2 节 |
| `apply_fow.py` | 生成迷雾「羊皮纸」FOW 变体 | 该类别原版有 `_FOW` 时（建筑/区域/资源有，项目没有） |
| `gen_tex.py` | 按 DDS 头生成 `.tex`（GBK/ANSI 编码，别存 UTF-8） | 一般不直接调，make_atlas/convert_art 会调 |
| `gen_modartxml.py` | 生成/核对 `Mod.Art.xml` | 新增或改了 XLP/Artdef 时 `--check` |
| `make_workshop_preview.py` | **工坊预览图生成**（Lanczos 逐级减半 + unsharp，默认 512×512）；**已达标成品直通不二次缩放**；`--qa` 出锐度/振铃指标 | 出/换工坊封面 `image.png`（第九·补节） |
| `iconify_text.py` | **文本图标化**：按中文关键词给游戏文本插 `[ICON_x]`（幂等防重复、保编码换行），并用**官方图标全表 + 工程 Icons XML** 校验图标名；`--audit` 只查悬空图标名 | 批量给文本加图标、或**排查「图标不显示」**（见第十·补节） |

`verify_icon_atlas.py` 的实战产出（本项目 2026-09 首跑）：一次抓出 2 个此前无人发现的既有问题——
`RGN_Product_Font.dds` 被引用但文件不存在（7 条 IconDefinitions 悬空）、
`ATLAS_RGN_ICON_DISTRICTS256_FOW.dds` 被引用但没登记进任何 UITexture XLP（不会被打包）。
这类问题肉眼几乎看不出来，只有进游戏才会发现是空白图标。

`--edge-qa` + `regen_atlas_tiers.py` 的实战产出（2026-09）：领袖图标实机锯齿溯源到中间档 alpha
被压对比（45px 边界中间调仅 20.4%，原版 45.3%），修复后 43.6%；顺带全工程体检又抓出
`DISTRICTS`(6) / `PRODUCT`(5) / `RESOURCES`(4) 共 15 个同类受损档 —— 全部由结构校验 PASS、
只有边缘门能发现。

## 十·补、文本图标化与「图标不显示」排查（`iconify_text.py`）

前面各节的校验器管的都是**美术侧**（图集落地、格子非空、XLP 登记、`.tex` 对齐）。但图标
不显示还有**另一半原因在文本侧**：`[ICON_x]` 里的 `x` 解析不到。两个方向必须都查：

| 症状 | 病因层 | 用哪个工具 |
|---|---|---|
| 图标空白，但图集/贴图都正常 | **文本侧**：`[ICON_x]` 的 `x` 解析不到 | `iconify_text.py --audit` |
| 图标空白，文本写法也对 | **美术侧**：图集没落地 / 格子空 / 没进 XLP | `verify_icon_atlas.py` |

`iconify_text.py --audit` 把文本里出现的每个 `[ICON_x]` 拿去**两个来源**核对，解析不到就是悬空：

1. **官方原版**：`reference/sources/civ6-icon-tags.sql` 的 4836 个 `[ICON_*]` 全表；
2. **本工程自定义**：工程 `Data/*.xml`、`Mod_Adaptation/**/*.xml` 里 `IconDefinitions` /
   `IconTextureAtlases` 声明的名字（如 `RESOURCE_AUREO_RGN`）。

> 实测（本项目 2026-09）：全局审计 `Text/` 下全部 `.sql`，**0 处悬空**；同一跑法能识别
> 377 个工程自定义图标名 + 36 个图集名。

**批量加图标**用 `--check` 预演 → `--write` 写入。两个必须知道的实现要点：

- **幂等**：关键词左侧若已是同名 `[ICON_x]`（允许夹空白、大小写不敏感）则跳过，重复跑不叠加；
- **长词优先**：`旅游业绩` 先于 `旅游`、`大预言家` 先于 `预言家`，避免切错。

写入时**保持原编码（含 BOM 判定）与换行**（`newline=""`，防 Windows 把 `\r\n` 变成 `\r\r\n`），
且只改写 `Text` 字段的引号内 span —— 列顺序任意（工程里既有 `(Language, Tag, Text)` 也有
`(Tag, Language, Text)`）、多行 `VALUES` 与元组间 `-- 注释` 均已支持。

> ⚠ **图标名写错不报错、只是不显示**（本节 §3 起反复强调的静默失败）。所以「批量加图标」
> 必须配 `--audit`，否则等于批量制造静默失败。
