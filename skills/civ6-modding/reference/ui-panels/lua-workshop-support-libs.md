# Support 共享库 — 核心工具函数

> **来源**：`SupportFunctions.lua`(671行) + `Civ6Common.lua`(792行) + `ToolTipHelper.lua`(1358行) + `PopupManager.lua`(131行)
> **地位**：所有 UI Lua 文件共享的基础设施。

---

## SupportFunctions.lua — 通用工具

### 文本截断

```lua
TruncateString(control, resultSize, longStr, trailingText)          → bool
TruncateStringWithTooltip(control, resultSize, longStr)             → bool
TruncateStringWithTooltipClean(control, resultSize, longStr)        → bool
TruncateSelfWithTooltip(control)                                     → bool
TruncateStringByLength(textString, textLen)                          → string
```

### 表格操作

```lua
FormatTableAsString(tStringTable, strSeparator)      → string  -- LOC key 数组 + 空格连接
FormatTableAsNewLineString(tStringTable, bDoubleLines) → string
RemoveTableEntry(T, key, theValue)                    → bool
ShuffleTable(tbl)                                     → table
DeepCopy(orig)                                        → table
DeepCompare(table1, table2)                           → bool
orderedPairs(t)                                       → iterator  -- 按 key 排序迭代
```

### 位运算（Lua 5.1 无原生位运算）

```lua
numberToBitsTable(value)    → table   -- 数字→位表
bitsTableToNumber(kTable)   → number  -- 位表→数字
bitNot(value)               → number
lshift(value, shift)        → number
rshift(value, shift)        → number
```

### 数学

```lua
Clamp(value, min, max)          → number
SoftRound(x)                    → integer
Round(num, idp)                 → number   -- 指定小数位
RandRange(min, max)             → integer  -- 同步随机（使用 Game.GetRandNum）
RandWeight(rollTable)           → table    -- 加权随机滚动
Triangular(iN)                  → number   -- 三角数 n*(n+1)/2
PolarToCartesian(r, phi)        → x, y
PolarToRatioCartesian(r, phi, ratio) → x, y
RBGtoHSV(red, green, blue)      → h, s, v
```

### 字符串

```lua
Split(str, delim, maxNb)        → table
GetIPType(ip)                   → 4 / 6 / 0
```

---

## Civ6Common.lua — 游戏通用查询

### 产出格式化

```lua
GetYieldTextIcon(yieldType)                  → "[ICON_Food]"
GetYieldTextColor(yieldType)                 → "[COLOR:ResFoodLabelCS]"
GetYieldString(yieldType, amount)            → "[ICON_Food][COLOR:ResFoodLabelCS]+2[ENDCOLOR]"
toPlusMinusString(value)                     → "+2" / "-1" / "0"
toPlusMinusNoneString(value)                 → "+2" / "-1" / " "
```

### 单位相关

```lua
GetUnitStats(hashOrType)                     → {Bombard, Combat, Moves, BaseMoves, RangedCombat, Range}
GetUnitIcon(pUnit, iconSize)                 → {textureSheet, textureOffsetX, textureOffsetY}
MoveUnitToPlot(kUnit, plotX, plotY)          -- 含宣战确认弹窗
```

### UI 工具

```lua
AutoSizeGridButton(gridButton, minX, minY, padding, sizeOption) → labelX, labelY
GetTopBarHeight()                                              → 29
GetColorPercentString(multiplier)                               → 彩色百分比字符串
FormatTimeRemaining(timeRemaining, bIsConcrete)                 → 本地化时间字符串
```

### 文明/领袖信息

```lua
GetLeaderUniqueTraits(leaderType, useFullDescriptions)     → unique_abilities, uu, ub
GetCivilizationUniqueTraits(civType, useFullDescriptions)  → unique_abilities, uu, ub
DifferentiateCiv(playerID, tooltipControl, icon, ...)      -- 文明颜色 + 工具提示
```

### 查询

```lua
IsTutorialRunning()          → bool
IsDiplomacyPending()         → bool
IsDiplomacyOpen()            → bool
IsPlayerCityless(playerID)   → bool
GetGreatWorksForCity(pCity)  → table
IsExpansion1Active() / IsExpansion2Active()   → bool  -- 已加载
IsExpansion1Enabled() / IsExpansion2Enabled() → bool  -- 已启用
```

### 持久化

```lua
WriteCustomData(key, value)   -- 写入存档（UI.GetGameParameters）
ReadCustomData(key)           → ... -- 读取存档
```

### 常量

```lua
ProductionType = {BUILDING="BUILDING", DISTRICT="DISTRICT", PROJECT="PROJECT", UNIT="UNIT"}
```

---

## ToolTipHelper.lua — 工具提示生成

### 主调度器

```lua
ToolTipHelper.GetToolTip(typeName, playerId, bBaseValues) → string
```

通过 `g_ToolTipGenerators` 表按类型分发：

| KIND 常量 | 生成函数 |
|-----------|---------|
| `KIND_BUILDING` | `GetBuildingToolTip` |
| `KIND_CIVIC` | `GetCivicToolTip` |
| `KIND_UNIT` | `GetUnitToolTip` |
| `KIND_DISTRICT` | `GetDistrictToolTip` |
| `KIND_PROJECT` | `GetProjectToolTip` |
| `KIND_IMPROVEMENT` | `GetImprovementToolTip` |
| `KIND_ROUTE` | `GetRouteToolTip` |
| `KIND_POLICY` | `GetPolicyToolTip` |
| `KIND_GOVERNMENT` | `GetGovernmentToolTip` |
| `KIND_RESOURCE` | `GetResourceToolTip` |
| `KIND_TECH` | `GetTechnologyToolTip` |
| `KIND_DIPLOMATIC_ACTION` | `GetDiplomaticActionToolTip` |

### 扩展机制

```lua
include("ToolTipLoader_", true)  -- 通配符加载所有 ToolTipLoader_*.lua
```

Mod 可添加 `ToolTipLoader_MyMod.lua` 注入自定义 KIND 到 `g_ToolTipGenerators`。

### 辅助函数

```lua
ToolTipHelper.GetAdjacencyBonuses(t, field, key)  -- 相邻加成文本
AddBuildingExtraCostTooltip(buildingHash)          -- XP 扩展覆盖的桩函数
AddBuildingYieldTooltip(buildingHash, city, tooltipLines)
AddUnitStrategicResourceTooltip(unitRef, formationType, pBuildQueue)
```

---

## PopupManager.lua — 排他性弹窗锁

防止多个弹窗同时出现，锁定游戏进程直到玩家处理。

```lua
-- 1. 创建
local lock = ExclusivePopupManager:new("MyPopupName")

-- 2. 加锁（暂停游戏进程）
lock:Lock(context, priority, params)           → bool

-- 3. 解锁（恢复游戏进程）
lock:Unlock()

-- 4. 查询状态
lock:IsLocked()                                 → bool

-- 5. 序列化（存档/读档）
local saved = lock:ToTable()
lock:FromTable(saved, freshContext)
```

**加锁时做的事情**：
1. `UI.ReferenceCurrentEvent()` → 获取引擎事件 ID 阻止进程
2. `Input.PushActiveContext(InputContext.Reveal)` → 推输入上下文
3. `UIManager:QueuePopup(context, priority, params)` → 入队弹窗
