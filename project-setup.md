# Project Setup — `.civ6proj` & `.modinfo`

## Overview

Civ6 mods use **two formats** of "manifest" file. Both describe the same content (actions, files, metadata),
but consume it differently:

| File | Created by | Used by | Current Status |
|------|-----------|---------|----------------|
| `.civ6proj` | ModBuddy IDE (MSBuild XML) | ModBuddy build / packaging | **Wheelers in use** |
| `.modinfo` | Hand OR by Build → Export | Game runtime loader | **Distribution format** |

ModBuddy builds a `.modinfo` from the `.civ6proj` automatically when packaging a mod (Build menu).
You can hand-edit either, but most modern mods are edited in `.civ6proj` and the `.modinfo` is regenerated.

> **Workflow rule of thumb:** Maintain the `.civ6proj` in ModBuddy; let Build → export generate the `.modinfo`.
> If you hand-edit the `.modinfo`, do not regenerate afterwards (your edits will be overwritten).

---

## Shared Concepts (same vocabulary in both formats)

These pieces of vocabulary are identical between `.modinfo` and `.civ6proj` (only their nesting context differs).

### Action Types

| Action | Where | Purpose |
|--------|-------|---------|
| `UpdateDatabase` | InGame / FrontEnd | Load XML/SQL into database |
| `AddGameplayScripts` | InGame | Register GamePlay Lua scripts |
| `AddUserInterfaces` | InGame | Add new UI panel (XML ref only; Lua in ImportFiles) |
| `ReplaceUIScript` | InGame | Override an existing LuaContext by ID |
| `ImportFiles` | InGame | Import loose files without processing |
| `UpdateArt` | InGame / FrontEnd | `.dep` art dependencies |
| `UpdateColors` | InGame / FrontEnd | Player color definitions |
| `UpdateIcons` | InGame / FrontEnd | Icon definitions |
| `UpdateText` | InGame / FrontEnd | Localization XML |
| `UpdateAudio` | InGame | Audio bank config |
| `AddMap` | FrontEnd | Map files for game setup |
| `UpdateLogitechARX` | InGame | Logitech ARX support |

### Properties (`<Properties>` block inside an action)

| Property | Description |
|----------|-------------|
| `LoadOrder` | Database load order (negative = earlier) |
| `Priority` | File execution order (higher = later) |
| `LuaContext` | For ReplaceUIScript: the ID of the context to replace |
| `LuaReplace` | For ReplaceUIScript: the replacement Lua file path |
| `Context` | For AddUserInterfaces: the parent context (e.g. "InGame") |
| `RuleSet` | Associate with a specific ruleset |
| `Name` / `Description` | For maps: display name/description |
| `Group` | For maps: group name for map picker |

### Load Order Values

**vanilla 官方阶梯**（官方 modinfo 实测）：

```
-100: Schema changes, Remove Data
-75:  Unofficial schema changes
-50:  Premature updates
0:    Standard content updates (DEFAULT)
50:   Post updates
100:  Scenario updates
```

> ⚠ **官方阶梯只覆盖 `-100 … 100`，真实工程用的远不止这一段。**
> 11 个真实工程实测出现了 `-2 / -1 / 10 / 200 / 1000 / 10000 / 20000 / 30000 / 600000 / 610003 / 777777 / 888888 / 999999 / 1000000 / 9999999`。
> **`LoadOrder = -1` 出现在 8/11 个工程**，且 4 个独立总督工程都把它用于 `Governors` 数据 → 事实约定：*被其他内容引用的定义类数据要早加载*。
> 完整观测阶梯表、`600000` 段社区约定、以及「跨 mod 同 LoadOrder 次序无保证」的警告见 **`gotchas.md` §44**。
> 写**平衡补丁**时的专项规则（必须压过主工程最终覆盖层，否则数值被静默回滚）见 **`balance-patch.md` §三**。

**分层实践**（推荐骨架，来自真实工程）：

```
-1        内容/类型定义（被他人引用的先落地）
200       常规内容（Types / Icons / 主数据）
600000    ImportFiles（共享 Core 文件）
600005+   Modifiers（晚于 Types，因为要引用它们）
610002+   AddUserInterfaces（UI 必须晚于 ImportFiles）
999999+   最终覆盖层（立绘适配 / 兼容补丁 / 平衡补丁）
```

### 官方 .modinfo 实证模式（42 个官方 modinfo 统计）

> 来源：`Firaxis 官方 42 个 .modinfo`（Base Scenarios + 全部 DLC）全量解析统计，2026-08 校准。

**官方常用的 `criteria` 命名与组合模式：**

| 模式 | 官方示例 | 说明 |
|------|---------|------|
| 单一 DLC | `criteria="Expansion1"` / `"Expansion2"` | 仅当对应 DLC 加载时生效 |
| 复合 DLC | `criteria="Expansion1AndBeyond"` / `"Expansion2AndBeyond"` | DLC 级联条件（后者包含前者） |
| 扩展组合 | `criteria="Australia_Expansion1"` / `"Australia_Expansion2"` | 文明包 × DLC 组合，同一文件按扩展分别声明 |
| 游戏模式 | `criteria="Heroes_Mode"` / `"Monopolies_Mode"` / `"DramaticAges_Mode"` | MODE 内容独立 criteria，支持 `_Expansion1`/`_Expansion2` 后缀组合 |
| 情景 | `criteria="BlackDeathScenario"` / `"PiratesScenario"` | 情景内容 |

**`File` 元素的 `Priority` 属性（官方实际值分布）：**

| 值 | 用途（官方实测） | 出现次数 |
|----|----------------|---------|
| `Priority="1"` | 移除/前置数据（RemoveData 类 XML）、Text 前置 | UpdateText x246, UpdateDatabase x21 |
| `Priority="2"` | Schema 之后的主数据 | UpdateDatabase x31, UpdateText x19 |
| `Priority="3"` | 追加数据 | x2 |
| `Priority="0"` | 基础数据（最前） | x2 |
| 无 Priority | 常规数据（默认最后执行） | 大量 |

官方惯例（Expansion2.modinfo）：`Schema.sql Priority=2` → `RemoveData.xml Priority=1` → 常规数据无 Priority。**移除数据用低 Priority 数字（先跑），主数据无 Priority（后跑）。**

**`LoadOrder` 官方实际使用值：** `-100`（2 处，schema/remove）与 `100`（9 处，情景/追加）。官方大量 UpdateDatabase 不写 LoadOrder（默认 0）。

**`ReplaceUIScript` 的 `LuaContext` 官方值（Top 12）：**

```
WorldRankings, GovernmentScreen, TopPanel, PlotToolTip, ActionPanel, ARXManager,
UnitPanel, MinimapPanel, DiplomacyRibbon, InGameTopOptionsMenu, WorldTracker, WorldInput
```

官方 ReplaceUIScript 全部**同时提供** `LuaContext`（要替换的上下文 ID）与 `LuaReplace`（替换脚本路径，放在 `UI/Replacements/`），二者成对出现。

**`AddUserInterfaces` 官方 `Context` 值：** 全部为 `InGame`（官方仅用于 InGame 上下文）。

**官方 modinfo 顶层结构要点：**

- `<Mod id="GUID" version="1">`（官方全部 version="1"）
- `<ActionCriteria>` 定义所有 criteria，`<InGameActions>` 内 action 用 `criteria="X"` 属性绑定
- 带 criteria 的 action 占官方 action 总数的 100%（无裸 action）；`<Properties>` 是可选的（LoadOrder 等）


### Criteria — Selective Loading

```xml
<Criteria id="MyCriteria">
    <ConfigurationValueMatches>
        <Group>Game</Group>
        <ConfigurationId>GAMEMODE_MY_MODE</ConfigurationId>
        <Value>1</Value>
    </ConfigurationValueMatches>
    <ModInUse>A3F42CD4-...</ModInUse>
    <ModInUse inverse="1">073b6367-...</ModInUse>   <!-- .civ6proj only -->
    <RuleSetInUse>RULESET_EXPANSION_2</RuleSetInUse>
    <GameCoreInUse>Expansion2</GameCoreInUse>
    <LeaderPlayable>Players:Expansion2_Players::LEADER_MY_LEADER</LeaderPlayable>
</Criteria>
```

All actions support attaching criteria for conditional loading. `inverse="1"` inside `<ModInUse>`
negates the check (criterion passes when the listed mod is **NOT** in use). `inverse` is a `.civ6proj`
CDATA feature; in hand-written `.modinfo` you must pre-define a separate "X_Disabled" criteria.

---

## Format 1 — `.civ6proj` (ModBuddy project file)

MSBuild-style XML. Mod metadata + actions + criteria + file/folder tree for the IDE.

### Skeleton

```xml
<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="12.0" DefaultTargets="Default" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup>
    <Configuration Condition=" '$(Configuration)' == '' ">Default</Configuration>
    <Name>LOC_MYMOD_MOD_TITLE</Name>
    <Guid>{mod-guid-here}</Guid>                       <!-- .modinfo Mod id source -->
    <ProjectGuid>{project-guid-here}</ProjectGuid>     <!-- ModBuddy internal only -->
    <ModVersion>1</ModVersion>
    <Teaser>LOC_MYMOD_MOD_TEASER</Teaser>
    <Description>LOC_MYMOD_MOD_DESCRIPTION</Description>
    <Authors>千与千寻瀑</Authors>
    <SpecialThanks>Pen, Ophidy, 系七</SpecialThanks>
    <AffectsSavedGames>true</AffectsSavedGames>
    <SupportsSinglePlayer>true</SupportsSinglePlayer>
    <SupportsMultiplayer>true</SupportsMultiplayer>
    <SupportsHotSeat>true</SupportsHotSeat>
    <CompatibleVersions>1.2,2.0</CompatibleVersions>
    <AssemblyName>MyMod</AssemblyName>
    <RootNamespace>MyMod</RootNamespace>

    <AssociationData><![CDATA[ ... ]]></AssociationData>
    <LocalizedTextData><![CDATA[ ... ]]></LocalizedTextData>
    <ActionCriteriaData><![CDATA[ ... ]]></ActionCriteriaData>
    <FrontEndActionData><![CDATA[ ... ]]></FrontEndActionData>
    <InGameActionData><![CDATA[ ... ]]></InGameActionData>
  </PropertyGroup>
  <PropertyGroup Condition=" '$(Configuration)' == 'Default' ">
    <OutputPath>.</OutputPath>
  </PropertyGroup>
  <ItemGroup>
    <Folder Include="Data\" />
    <Folder Include="Scripts" />
  </ItemGroup>
  <ItemGroup>
    <Content Include="Data\MyData.sql"><SubType>Content</SubType></Content>
  </ItemGroup>
  <Import Project="$(MSBuildLocalExtensionPath)Civ6.targets" />
</Project>
```

### CDATA blocks — what each one carries

| Block | Required | Carries | Auto-loaded? |
|-------|---------|---------|--------------|
| `<AssociationData>` | Common | `<Dependency type="Dlc\|Mod" title=".." id=".." />`, `<Reference>` | Yes — drives dependency |
| `<LocalizedTextData>` | Common | Mod metadata text (title/teaser/desc/authors) in `<LocalizedText>` format | Yes — no `UpdateText` action needed for these |
| `<ActionCriteriaData>` | By need | `<Criteria>` definitions listed above | Yes — criteria usable by actions |
| `<FrontEndActionData>` | If FE actions exist | Any `Update*/Add*` action, content format = InGame | Yes |
| `<InGameActionData>` | If IG actions exist | Idem | Yes |

### Minimal `<AssociationData>` (Gathering Storm dependency)

```xml
<AssociationData><![CDATA[<Associations>
  <Dependency type="Dlc" title="Expansion: Gathering Storm"
              id="4873eb62-8ccc-4574-b784-dda455e74e68" />
  <Reference type="Dlc" title="Expansion: Gathering Storm"
              id="4873eb62-8ccc-4574-b784-dda455e74e68" />
</Associations>]]></AssociationData>
```

### Minimal `<LocalizedTextData>`

```xml
<LocalizedTextData><![CDATA[<LocalizedText>
    <Text id="LOC_MYMOD_MOD_TITLE">
        <en_US>My Mod Title</en_US>
        <zh_Hans_CN>我的模组标题</zh_Hans_CN>
        <zh_Hant_HK>我的模組標題</zh_Hant_HK>
    </Text>
    <Text id="LOC_MYMOD_MOD_TEASER"><en_US>Teaser</en_US><zh_Hans_CN>副标题</zh_Hans_CN></Text>
    <Text id="LOC_MYMOD_MOD_DESCRIPTION"><en_US>Description.</en_US><zh_Hans_CN>描述。</zh_Hans_CN></Text>
</LocalizedText>]]></LocalizedTextData>
```

### Minimal `<ActionCriteriaData>` (with examples)

```xml
<ActionCriteriaData><![CDATA[<ActionCriteria>
  <Criteria id="MyLeader_Playable_Expansion2">
    <LeaderPlayable>Players:Expansion2_Players::LEADER_MY_LEADER</LeaderPlayable>
    <RuleSetInUse>RULESET_EXPANSION_2</RuleSetInUse>
  </Criteria>
  <Criteria id="Expansion2"><GameCoreInUse>Expansion2</GameCoreInUse></Criteria>
  <Criteria id="HD"><ModInUse>521b8777-0977-4859-a5ee-3e411a732e5c</ModInUse></Criteria>
  <Criteria id="NoOtherMod">
    <ModInUse inverse="1">66685738-4d78-4c73-874a-055e5d24d86a</ModInUse>
  </Criteria>
  <Criteria id="Monopolies_Mode">
    <ConfigurationValueMatches>
      <ConfigurationId>GAMEMODE_MONOPOLIES</ConfigurationId><Group>Game</Group><Value>1</Value>
    </ConfigurationValueMatches>
  </Criteria>
</ActionCriteria>]]></ActionCriteriaData>
```

### Minimal `<InGameActionData>` — actions are **child `<Criteria>` elements** (not `criteria=` attribute)

```xml
<InGameActionData><![CDATA[<InGameActions>
  <UpdateDatabase id="MyData">
    <Properties><LoadOrder>200</LoadOrder></Properties>
    <Criteria>Expansion2</Criteria>
    <File>Data/Buildings_MyMod.sql</File>
    <File>Data/Civilization_MyMod.sql</File>
  </UpdateDatabase>
  <UpdateDatabase id="MyModifiers">
    <Properties><LoadOrder>999999</LoadOrder></Properties>
    <Criteria>Expansion2</Criteria>
    <File>Data/Modifiers_MyMod.sql</File>
  </UpdateDatabase>
  <UpdateText id="Text">
    <Properties><LoadOrder>30000</LoadOrder></Properties>
    <File>Text/Text_MyMod.xml</File>
  </UpdateText>
  <UpdateColors id="Colors"><File>Data/Colors_MyMod.sql</File></UpdateColors>
  <UpdateIcons id="Icons"><File>Data/Icons_MyMod.xml</File></UpdateIcons>
  <AddGameplayScripts id="Scripts">
    <Properties><LoadOrder>600001</LoadOrder></Properties>
    <File>Scripts/Lua_MyMod.lua</File>
  </AddGameplayScripts>
  <AddUserInterfaces id="MyUI">
    <Properties><Context>InGame</Context></Properties>
    <File>UI/MyPanel.xml</File>
  </AddUserInterfaces>
  <ImportFiles id="Import">
    <File>UI/MyPanel.lua</File>
    <File>ImportFiles/CityBannerManager_MyMod.lua</File>
  </ImportFiles>
  <UpdateArt id="Art"><File>(Mod Art Dependency File)</File></UpdateArt>
</InGameActions>]]></InGameActionData>
```

> **Multiple `<Criteria>` children on one action = logical AND.**
> Example: `<Criteria>Jinhsi_Disabled</Criteria><Criteria>Changli_Playable_Expansion2</Criteria>`
> means "load only when Jinhsi is NOT in use AND Changli IS playable."

### Minimal `<FrontEndActionData>`

```xml
<FrontEndActionData><![CDATA[<FrontEndActions>
  <UpdateDatabase id="Config"><File>Data/Config_MyMod.sql</File></UpdateDatabase>
  <UpdateIcons id="Icons_Config"><File>Data/Icons_MyMod.xml</File></UpdateIcons>
  <UpdateColors id="Colors_Config"><File>Data/Colors_MyMod.sql</File></UpdateColors>
  <UpdateText id="Text_Config"><File>Text/Text_Config_MyMod.sql</File></UpdateText>
  <UpdateArt id="Art"><File>(Mod Art Dependency File)</File></UpdateArt>
</FrontEndActions>]]></FrontEndActionData>
```

### `<ItemGroup>` — file & folder list

```xml
<ItemGroup>
  <!-- Folders appear in ModBuddy Solution Explorer. Required to use Context Include paths. -->
  <Folder Include="Data\" />
  <Folder Include="Scripts" />
  <Folder Include="UI\" />
</ItemGroup>
<ItemGroup>
  <Content Include="Data\Buildings_MyMod.sql"><SubType>Content</SubType></Content>
  <Content Include="Data\Modifiers_MyMod.sql"><SubType>Content</SubType></Content>
  <Content Include="Scripts\Lua_MyMod.lua"><SubType>Content</SubType></Content>
  <Content Include="UI\MyPanel.xml"><SubType>Content</SubType></Content>
  <Content Include="UI\MyPanel.lua"><SubType>Content</SubType></Content>
  <!-- For Art-XML files that aren't "content" proper -->
  <None Include="MyMod.Art.xml" />
</ItemGroup>
<Import Project="$(MSBuildLocalExtensionPath)Civ6.targets" />
```

> **Drive**: The `<Import Project="$(MSBuildLocalExtensionPath)Civ6.targets" />` line is mandatory — it pulls in
> the build rules that turn the CDATA action definitions + `<Content Include>` list into the final `.modinfo`.

> **哪些文件需要写进 `<Content Include>` 清单**：只有 **XML / SQL / Lua** 文件一定需要写入；ImportFiles 引用的图片/视频、`Platforms/` 下的音频 bank 等媒体资产受特殊规则约束（专门的导入流程或用户手动导入）；其余文件 ModBuddy 引擎默认自动打包，**无需**放进 Content 文件清单。详见下方 Important Rules 第 3 条与「文件清单同步」。

---

## Format 2 — `.modinfo` (production runtime manifest)

Hand-friendly XML with a single `<Mod id="GUID" version="V">` root.

### Complete example (WarMachineScenario style)

```xml
<?xml version="1.0" encoding="utf-8"?>
<Mod id="<GUID>" version="1">
    <Properties>
        <Name>LOC_MOD_TITLE</Name>
        <Teaser>LOC_MOD_TEASER</Teaser>
        <Description>LOC_MOD_DESCRIPTION</Description>
        <Authors>LOC_MOD_AUTHORS_FIRAXIS</Authors>
        <CompatibleVersions>2.0</CompatibleVersions>
        <EnabledByDefault>1</EnabledByDefault>
        <SupportsSinglePlayer>0</SupportsSinglePlayer>
    </Properties>

    <Dependencies>
        <Mod id="<dep-guid>" title="LOC_EXPANSION2_MOD_TITLE"/>
    </Dependencies>

    <ActionCriteria>
        <Criteria id="MyCriteria">
            <RuleSetInUse>RULESET_STANDARD</RuleSetInUse>
            <GameCoreInUse>Expansion2</GameCoreInUse>
        </Criteria>
    </ActionCriteria>

    <InGameActions>
        <UpdateDatabase id="MyData" criteria="MyCriteria">
            <Properties><LoadOrder>100</LoadOrder></Properties>
            <File Priority="1">Data/MyRemoveData.xml</File>
            <File>Data/MyGameplayData.xml</File>
        </UpdateDatabase>

        <AddGameplayScripts id="MyScripts" criteria="MyCriteria">
            <File>Scripts/MyGameplay.lua</File>
        </AddGameplayScripts>

        <AddUserInterfaces id="MyNewUI" criteria="MyCriteria">
            <Properties><Context>InGame</Context></Properties>
            <File>UI/Additions/MyPanel.xml</File>
        </AddUserInterfaces>

        <ReplaceUIScript id="MyReplace" criteria="MyCriteria">
            <Properties>
                <LuaContext>TopPanel</LuaContext>
                <LuaReplace>UI/Replacements/TopPanel_MyMod.lua</LuaReplace>
            </Properties>
        </ReplaceUIScript>

        <ImportFiles id="MyFiles" criteria="MyCriteria">
            <File>UI/Additions/MyPanel.lua</File>
            <File>UI/Replacements/TopPanel_MyMod.lua</File>
        </ImportFiles>

        <UpdateArt id="MyArt" criteria="MyCriteria"><File>MyMod.dep</File></UpdateArt>
        <UpdateColors id="MyColors" criteria="MyCriteria"><File>Data/MyPlayerColors.xml</File></UpdateColors>
        <UpdateIcons id="MyIcons" criteria="MyCriteria"><File>Data/MyAllIcons.xml</File></UpdateIcons>
        <UpdateText id="MyText" criteria="MyCriteria"><File Priority="1">Text/en_US/MyText.xml</File></UpdateText>
        <UpdateAudio id="MyAudio" criteria="MyCriteria"><File>Platforms/Windows/Audio/Banks.ini</File></UpdateAudio>
        <UpdateLogitechARX id="MyARX" criteria="MyCriteria"><File>Data/ARX/index.html</File></UpdateLogitechARX>
    </InGameActions>

    <FrontEndActions>
        <UpdateDatabase id="SettingsData"><File>Data/MyConfig.xml</File></UpdateDatabase>
        <UpdateText id="SettingsText"><File>Text/en_US/MyConfigText.xml</File></UpdateText>
        <AddMap id="MyMap">
            <Properties>
                <Name>LOC_MAPSIZE_MYMAP_NAME</Name>
                <Description>LOC_MAPSIZE_MYMAP_DESCRIPTION</Description>
                <Group>MyMod_Maps</Group>
            </Properties>
            <File>Maps/MyMap.Civ6Map</File>
        </AddMap>
    </FrontEndActions>

    <Files>
        <!-- ALL files used by the mod must be listed here -->
        <File>MyMod.dep</File>
        <File>Data/MyGameplayData.xml</File>
        <File>Scripts/MyGameplay.lua</File>
        <File>UI/Additions/MyPanel.lua</File>
        <File>UI/Additions/MyPanel.xml</File>
    </Files>
</Mod>
```

---

## `.civ6proj` vs `.modinfo` — side-by-side

| 维度 | `.modinfo` | `.civ6proj` |
|------|------------|-------------|
| Root | `<Mod id="GUID" version="V">` | MSBuild `<Project>` |
| Mod ID | `<Mod id=` attribute | `<Guid>` element **+** `<ProjectGuid>` (ModBuddy internal) |
| 显示/元数据 | `<Properties>` (Name/Teaser/Description/Authors/...) | `<PropertyGroup>` (same + SpecialThanks, AffectsSavedGames, Supports*, CompatibleVersions, AssemblyName, RootNamespace) |
| 依赖 | `<Dependencies><Mod id="..">` | `<AssociationData>` CDATA — `<Dependency type="Dlc\|Mod" id="..">` |
| 本地化 (mod metadata) | Must register via `UpdateText` action | `<LocalizedTextData>` CDATA auto-loaded |
| Action List | `<InGameActions>` / `<FrontEndActions>` direct child elements | `<InGameActionData>` / `<FrontEndActionData>` CDATA (internal XML format identical to the .modinfo equivalent) |
| Action → Criteria 绑定 | `criteria="X"` attribute (single string) | `<Criteria>X</Criteria>` child element; **multiple children = AND** |
| Action → 文件 | `<File>`/`<File Priority="1">` | Same inside CDATA |
| Criteria 定义 | `<ActionCriteria><Criteria id="X">` direct element | `<ActionCriteriaData>` CDATA (internal XML same) |
| Criteria 反选 | Must pre-define `X_Disabled` criteria listing the mod | `<ModInUse inverse="1">GUID</ModInUse>` directly |
| 文件清单 | `<Files><File>X</File>` | `<ItemGroup><Content Include="X"><SubType>Content</SubType></Content>` (IDE-only) |
| 文件夹切片 | none | `<ItemGroup><Folder Include="Path"/></ItemGroup>` (IDE-only) |
| Art | `<Dependencies>` + `.dep` references in Files; build via ModBuddy | Option: `<None Include="MyMod.Art.xml" />` for art rules；**新增/修改 XLP/Artdef 后重跑** `art\gen_modartxml.py <projectRoot> --check`（见 art-pipeline.md） |
| Build footer | none | `<Import Project="$(MSBuildLocalExtensionPath)Civ6.targets" />` (REQUIRED) |

---

## Important Rules (both formats unless noted)

1. **Mod ID must be a valid GUID** — generate a new one per mod. In `.civ6proj`, the `<Guid>` becomes
   `<Mod id>` in the exported `.modinfo`.
2. **`AddUserInterfaces` references only the `.xml`** — the matching `.lua` goes in `ImportFiles`.
3. **File list 按文件类别区分，不是"所有文件都列"**：
   - `.modinfo`: `<Files><File>` block；`.civ6proj`: `<Content Include="X">` entries。
   - **XML / SQL / Lua**：**一定需要写进清单** —— 新增/删除/改名时同步条目。
   - **ImportFiles 引用的图片/视频、`Platforms/` 下的音频 bank 等媒体资产**：受**特殊规则约束** —— 走专门的导入流程或由用户手动导入，不按普通清单条目默认同步。
   - **其他文件**：ModBuddy 引擎默认自动打包，**无需放进 proj 的 Content 文件清单**，也不要写进 `.modinfo` 的 `<Files>`。
4. **Higher `Priority` = loaded later** — removal XML usually gets `Priority="1"` to run first.
5. **`LoadOrder` of `-100`** is for schema modifications and data removal.
6. **`.civ6proj`: `<Guid>` and `<ProjectGuid>` are different.** `<Guid>` is the mod's public ID (referenced by
   other mods' `<ModInUse>`); `<ProjectGuid>` is purely a ModBuddy solution ID and isn't exported.
7. **`.civ6proj`: Multiple `<Criteria>` children on one action = logical AND.**
   Do not put `;` or `,` between them — each `<Criteria>...</Criteria>` element is one condition; if all
   must be true, just list them.

## Civilization / Leader Pack Registration Pattern

文明/领袖包涉及多类文件，每类的注册位置和方式不同。参考多个成熟 mod 项目归纳如下：

### 文件类型 → 注册位置对照表

| 文件类型 | 注册位置 | 动作类型 |
|---------|---------|---------|
| **配置** (Players/PlayerItems) | **FrontEnd 仅** | `UpdateDatabase` |
| **颜色** (Colors/PlayerColors) | **FrontEnd + InGame 两侧** | `UpdateColors` |
| **图标** (IconTextureAtlases) | **FrontEnd + InGame 两侧** | `UpdateIcons` |
| **配置文本** (仅 Config 用的 LOC) | **FrontEnd 仅** | `UpdateText` |
| **类型定义** (Buildings, Units, Civs, Districts, Leaders, Projects, Resources, Improvements, GreatPeople, GreatWorks, Beliefs, Governors 等) | **InGame 仅** | `UpdateDatabase` |
| **Modifiers 表** (Modifiers, ModifierArguments, TraitModifiers, BuildingModifiers 等) | **InGame 仅** | `UpdateDatabase` |
| **游戏文本** (LocalizedText) | **InGame 仅** | `UpdateText` |
| **Lua 脚本** | **InGame 仅** | `AddGameplayScripts` |
| **UI XML** | **InGame 仅** | `AddUserInterfaces` (Context=InGame) |
| **UI Lua** | **InGame 仅** | `ImportFiles` |
| **Core 共享 Lua** | **InGame 仅** | `ImportFiles` |

### 关键规则

1. **Config = FrontEnd 专属** — `Players`、`PlayerItems` 表仅存在于 FrontEnd 数据库，写入它们的 SQL 必须在 `<FrontEndActions>` 的 `<UpdateDatabase>` 中注册。放入 InGame 会导致 `no such table: Players`。

2. **Colors 和 Icons 双侧注册** — `Colors`、`PlayerColors`、`IconTextureAtlases` 表在 FrontEnd 和 InGame 数据库中都存在，因此颜色和图标文件必须在两侧分别注册（`UpdateColors` / `UpdateIcons`），漏掉一侧会导致对应上下文缺少颜色或图标。

3. **文本用 UpdateText，不是 UpdateDatabase** — 即使 LocalizedText 以 SQL (`INSERT INTO LocalizedText`) 书写，也改用 `<UpdateText>` 动作。SQL 和 XML 格式均可。`Text_Config_*.sql` 仅 FrontEnd 需要，其余游戏文本 InGame 即可。

4. **类型定义和 Modifiers 分开注册** — 类型定义（建筑、单位、文明等）和 Modifiers 表分别放在独立的 `UpdateDatabase` 动作中，便于控制加载顺序。

### 标准 FrontEnd 结构

```xml
<FrontEndActionData><![CDATA[<FrontEndActions>
  <UpdateDatabase id="Config"><File>Data/Config_MyMod.sql</File></UpdateDatabase>
  <UpdateColors id="Colors_Config"><File>Data/Colors_MyMod.sql</File></UpdateColors>
  <UpdateIcons id="Icons_Config"><File>Data/Icons_MyMod.xml</File></UpdateIcons>
  <UpdateText id="Text_Config"><File>Text/Text_Config_MyMod.sql</File></UpdateText>
  <UpdateArt id="Art" />
</FrontEndActions>]]></FrontEndActionData>
```

### 标准 InGame 结构

```xml
<InGameActionData><![CDATA[<InGameActions>
  <AddUserInterfaces id="UI">
    <Properties><Context>InGame</Context></Properties>
    <File>UI/MyPanel.xml</File>
  </AddUserInterfaces>
  <ImportFiles id="Import">
    <File>ImportFiles/Core.lua</File>
    <File>UI/MyPanel.lua</File>
  </ImportFiles>
  <UpdateDatabase id="Types">
    <Properties><LoadOrder>200</LoadOrder></Properties>
    <File>Data/Buildings_MyMod.sql</File>
    <File>Data/Civilization_MyMod.sql</File>
    <File>Data/Units_MyMod.sql</File>
    <!-- 其余类型文件，不含 Config/Colors/Icons -->
  </UpdateDatabase>
  <UpdateDatabase id="Modifiers">
    <Properties><LoadOrder>600005</LoadOrder></Properties>
    <File>Data/Modifiers_MyMod.sql</File>
  </UpdateDatabase>
  <UpdateText id="Text">
    <Properties><LoadOrder>200</LoadOrder></Properties>
    <File>Text/Text_MyMod.sql</File>
  </UpdateText>
  <AddGameplayScripts id="Scripts">
    <File>Scripts/Lua_MyMod.lua</File>
  </AddGameplayScripts>
  <UpdateIcons id="Icons"><File>Data/Icons_MyMod.xml</File></UpdateIcons>
  <UpdateColors id="Colors"><File>Data/Colors_MyMod.sql</File></UpdateColors>
  <UpdateArt id="Art" />
</InGameActions>]]></InGameActionData>
```

### `.modinfo` 等效写法

`.modinfo` 的注册方式与 `.civ6proj` CDATA 内部完全一致，仅有的区别：

| 差异点 | `.civ6proj` CDATA | `.modinfo` |
|--------|-------------------|------------|
| Criteria 绑定 | `<Criteria>X</Criteria>` 子元素（多个 = AND） | `criteria="X"` 属性（单字符串） |
| 反选 | `<ModInUse inverse="1">GUID</ModInUse>` | 需预定义 `X_Disabled` Criteria |

其余动作类型、属性、文件路径写法完全通用。

## Workflow Rules (file maintenance)

### 默认行为矩阵

| 变更类型 | `.civ6proj` | `.modinfo` |
|---------|-------------|-----------|
| **文件清单**（新增/删除/改名磁盘文件） | **默认更新** | **默认更新** |
| **加载动作**（`<UpdateDatabase>` / `<AddGameplayScripts>` / `<AddUserInterfaces>` / `<ImportFiles>` 等动作定义及其 `<File>` 子项） | **仅询问** | **默认完善** |

> **"默认更新"**：检测到磁盘文件变更后，直接补齐清单条目，无需先确认。
> **"仅询问"**：检测到需要新增/删除/修改某个加载动作时，提出方案并等用户确认，不擅自改动动作定义。
> **"默认完善"**：根据当前文件清单和上一步动作，直接补齐缺失的动作条目（例：新增 `Lua_Foo_X.lua` 到 ImportFiles 时，若发现 `.civ6proj` 中相应 `<AddGameplayScripts>` 或 `<ImportFiles>` 的对应条目已确认，可直接写入 `.modinfo` 的 `<InGameActions>`）。

### 文件清单同步（`<Content Include>` / `<Files>`）

**只有 XML / SQL / Lua 文件**在新增/删除/改名时**默认同步**两个清单；其余文件类型按下表分类处理：

| 文件类别 | 处理方式 |
|---------|---------|
| **XML / SQL / Lua** | 默认同步清单：`.civ6proj` 补 `<Content Include>`，`.modinfo` 补 `<Files><File>` |
| **ImportFiles 引用的图片/视频、`Platforms/` 下的音频 bank 等媒体资产** | 受特殊规则约束：走专门的导入流程或用户手动导入，不自动写清单 |
| **其他文件** | ModBuddy 引擎默认自动打包，**无需放进 proj 的 Content 文件清单**，也不要写进 `<Files>` |

XML / SQL / Lua 同步时的条目格式：

| `.civ6proj` | `.modinfo` |
|-------------|-----------|
| `<ItemGroup><Content Include="path"><SubType>Content</SubType></Content></ItemGroup>` | `<Files><File>path</File></Files>` |
| 新建目录还需 `<Folder Include="path\" />` | （无目录概念） |

> 💡 `.civ6proj` 是 ModBuddy 的项目台账 —— XML/SQL/Lua 缺失条目会导致文件不被打包；若残留指向不存在文件的条目，会编译报错。
> `.modinfo` 的 `<Files>` 块是运行时打包清单 —— XML/SQL/Lua 缺失条目会导致文件不包含在最终模组里。

#### ⚠ 两条轴：`<Content Include>` 管打包，Action 段管加载

| 轴 | 来源 | 作用 | 漏了的后果 |
|---|---|---|---|
| **打包** | `.civ6proj` 的 `<Content Include>` → 构建时展平成 `.modinfo` 顶层 `<Files>` | 文件**是否被复制进 Mods 目录**（编译期） | 部署包里没有该文件 |
| **加载** | `.civ6proj` 的 Action 段（`AddUserInterfaces` / `ImportFiles` / `AddGameplayScripts` / …） | 文件**在游戏里以什么身份被装载** | 视文件角色而定，见下 |

**`.lua` 怎么登记 —— 按角色分三类，不要一刀切**：

| 角色 | 判定 | 登记位置 |
|---|---|---|
| ① **UI 上下文脚本** | 有同名 `<Context>` `.xml` 被列进 `AddUserInterfaces` | **只需打包清单**；引擎会**自动加载同名 `.lua`** |
| ② **include 扩展件 / 官方脚本替代件** | 文件名 `<官方名>_<后缀>.lua`，靠官方 `include("<官方名>_", true)` 拉入；或替换官方文件 | **必须进 `ImportFiles`** |
| ③ **GamePlay 脚本** | 在 GP 侧运行 | **必须进 `AddGameplayScripts`** |

**证据（官方 + 工坊 170 个 modinfo 全量统计）**：
- `AddUserInterfaces` 内**只列 `.xml`** 的占 **128/130** —— 标准写法；
- 同名 `.lua` **只在顶层 `<Files>`、不在任何 Action** 的有 **203 例**（含 5 个整包零 Action 级 lua 却正常工作的成品 mod）→ 证明①的自动加载存在；
- Firaxis 官方 `UI/Additions/*.lua`、`UI/Replacements/*.lua`（Expansion2 共 138 个）**全部在 `ImportFiles`** → 证明②确实必需。

**自检**：把 Action 段引用的文件与 `<Content Include>` 做归一化（`\`→`/`）差集，再按上表判角色 —— ③类落在差集里 = 真漏；①类落在差集里 = 正常。
参考实现：示例工程 `workspace/_tools/check_proj_content.py`。

### 工程骨架：`.gitignore` 白名单 + `.gitattributes` 钉 LF

真实工程（多个独立收敛到同一策略）推荐的仓库骨架：

```gitignore
# 默认忽略一切，只放行可管理的源文件
*
!*/
!.gitignore
!*.civ6proj
!*.civ6sln
!*.xlp
!*.artdef
!*.sql
!*.xml
!*.lua

# 专用的 agent/素材工作区（中间产物、源素材，统一不入库）
workspace/

# 可再生的贴图（由脚本生成）
*.tex
*.dds

# 安全网：常见中间/临时产物显式忽略（防止被白名单放行）
*.bak_*
*.log
*.tmp
*.wem

# 例外：音频 bank 产物要入库
!Platforms/Windows/Audio/*.bnk
!Platforms/Windows/Audio/*.txt
!Platforms/Windows/Audio/*.ini
```

```gitattributes
# ★ ArtDef / XML / SQL / Lua：强制 LF
# 本机 core.autocrlf 常见为 true，checkout 会把仓库里的 LF 写成工作区 CRLF；
# 而 cooker 产物一律是 LF → 「源 ↔ Mods 副本」会出现永久伪不一致。
*.artdef  text eol=lf
*.xml     text eol=lf
*.sql     text eol=lf
*.lua     text eol=lf

# 美术二进制资产：禁止任何换行/编码转换
*.dds -text -diff -merge binary
*.tex -text -diff -merge binary
*.ast -text -diff -merge binary
*.mtl -text -diff -merge binary
*.geo -text -diff -merge binary
*.blp -text -diff -merge binary
```

> `.gitattributes` 的完整论证与实测支撑见 `civ6-art-reference/reference/cook-layer.md §2.3.1`。
> 加完后若出现大批"看似被改动"的文件，那是 autocrlf 历史遗留，用 `git add --renormalize .` 一次性归位，**不是内容改动**。

### 加载动作更新（动作定义 / Action definitions）

加载动作包括：`UpdateDatabase`、`UpdateText`、`UpdateIcons`、`UpdateColors`、`UpdateArt`、`UpdateAudio`、
`AddGameplayScripts`、`AddUserInterfaces`、`ReplaceUIScript`、`ImportFiles`、`AddMap`、`UpdateLogitechARX` 这些
节点，以及它们内部的 `<File>` 子项和 `<Properties>` / `<Criteria>` 子项。

| 场景 | `.civ6proj` 行为 | `.modinfo` 行为 |
|------|------------------|----------------|
| 新增 `X.sql` 需要加入 `UpdateDatabase` | 提出"在 `<InGameActionData>` 的 `X` 动作下追加 `<File>Data/X.sql</File>`"，等确认 | 默认直接在对应 `<UpdateDatabase id="X">` 内追加 `<File>Data/X.sql</File>` |
| 新增 `X.lua` 需要注册 `AddGameplayScripts` | 提议新增 `<AddGameplayScripts id="...">`，等确认 | 默认直接新增/补全对应的 `<AddGameplayScripts>` 块 |
| 删除某文件 → 需移除其 `<File>` 引用 | 默认同步清单（属上一节），但**是否从动作中剔除**要询问 | 默认从 `<InGameActions>` 中移除对应 `<File>` 条目 |
| 修改 LoadOrder / Context / LuaContext 等动作属性 | 仅询问，给出方案 | 默认完善 |

### 询问格式（`.civ6proj` 加载动作变更）

提出方案时遵循此模板，便于用户一句话决策：

```
检测到 <变更描述>。
建议在 .civ6proj 修改：
  <动作 id="X"> 下 <File>path</File> （新增/删除/修改）
确认后我会写入。
```

或简短一句话描述也行，关键是写明 **改哪个动作的哪个 `<File>` / `<Properties>` / `<Criteria>`**。