# UnitPanel — 单位操作面板 + UnitFlagManager — 3D 世界旗帜

> **来源**：`Panels/UnitPanel.xml`(453行) + `.lua`(4290行) + `UnitFlagManager.xml`(137行) + `.lua`(2110行)
> **地位**：选中单位后右下角弹出的操作面板，和 3D 世界中的单位旗帜系统。

---

## UnitPanel XML 结构

```
AlphaAnim(UnitPanelAlpha) + SlideAnim(UnitPanelSlide)
  Container(UnitPanelBaseContainer)
    GridButton(MainPanelBacking) ← 木纹背景
      
      ← 战斗预览横幅
      Container(CombatPreviewBanners) ← 胜/负/平横幅
        Image(BannerVictory/Defeat/Stalemate)
        Label(CombatAssessmentText)
      
      ← 操作按钮（MOD注入点★）
      Stack(ActionsStack) ← 主操作区
        Stack(StandardActionsStack) ← StackGrowth=Right（MOD在此注入按钮）
        Stack(SecondaryActionsStack) ← 辅助操作（隐藏，展开后显示）
      
      ← 单位图标/血条
      Meter(UnitHealthMeter) ← 103×103 圆形血条
      Image(UnitIcon) ← 95×95 单位肖像
      
      ← 统计堆栈
      Stack(SubjectStatStack) ← 战斗/移动属性
      Stack(TargetStatStack) ← 目标属性
      
      ← 晋升/命名面板
      Grid(PromotionPanel) ← 晋升选择 (300×287)
      Grid(VeteranNamePanel) ← 老兵命名 (300×200)
      
      ← 间谍/贸易面板
      Container(TradeUnitContainer) ← 贸易路线详情
      Container(EspionageUnitContainer) ← 间谍任务详情
      
      ← 教程覆盖层 ×10
```

## StandardActionsStack — MOD 按钮注入点

```xml
<Stack ID="StandardActionsStack" StackGrowth="Right" Padding="2" ConsumeMouse="1" />
```

MOD 通过 `GetUnitActionsTable()` 的返回结果向 `StandardActionsStack` 注入按钮。

### MOD 钩子（可覆盖函数）

| 钩子 | 位置 | 用途 |
|------|------|------|
| `LateCheckActionBeforeAdd(actionsTable, actionHash, isDisabled, tooltip, icon)` | L364 | 修改命令的文本/禁用/图标 |
| `LateCheckOperationBeforeAdd(results, actionsTable, actionHash, ...)` | L371 | 修改操作的文本/禁用/图标 |
| `BuildActionModHook(instance, action)` | L824 | 修改构建操作实例 |
| `IsActionLimited(actionType, unit)` | L4179 | 按单位类型限制操作（默认返回false） |
| `LateInitialize()` | L4215 | 启动时注册额外事件/回调 |

### GetUnitActionsTable 逻辑

1. 迭代 `GameInfo.UnitCommands()` — 仅 `VisibleInUI` 的命令
2. 按 `CategoryInUI` 分类到子表：ATTACK, BUILD, MOVE, INPLACE, SECONDARY 等
3. 迭代 `GameInfo.UnitOperations()` — 仅当单位有剩余移动力
4. 构建操作被分组为 `StartIconGroup()`/`EndIconGroup()` 图标组

### 实例

| 实例名 | 用途 |
|--------|------|
| `UnitActionInstance` | 操作按钮 (44×53) |
| `BuildActionInstance` | 建造操作按钮 |
| `StatInstance` | 属性显示行 |
| `ModifierInstance` | 战斗修改器行 |
| `EarnedPromotionInstance` | 已获得晋升图标 |
| `PromotionSelectionInstance` | 可选晋升卡片 |
| `TradeResourceyInstance` | 贸易资源条目 |

### InstanceManager（12个）

`m_standardActionsIM`, `m_secondaryActionsIM`, `m_buildActionsIM`, `m_earnedPromotionIM`, `m_PromotionListInstanceMgr`, `m_subjectModifierIM`, `m_targetModifierIM`, `m_interceptorModifierIM`, `m_antiAirModifierIM`, `m_subjectStatStackIM`, `m_targetStatStackIM`

---

## UnitFlagManager — 3D 世界单位旗帜

```
ZoomAnchor(Anchor) ← 3D→2D 世界空间映射
  AlphaAnim(FlagRoot) ← 64×64 旗帜根
    Image(FlagBase) ← 主要旗帜纹理 (64×64)
    AlphaAnim×2 ← 鼠标悬停/离开高亮
    Button(NormalButton) ← 普通点击区 (52×52)
    Button(HealthBarButton) ← 受伤点击区 (42×42)
    Image(UnitIcon) ← 32×32 单位徽章
    TextureBar(HealthBar) ← 11×32 垂直血条
    Image(Promotion_Flag) ← 晋升旗标
    Container(CorpsMarker/ArmyMarker) ← 军团/军队标记
```

### 旗帜类型 → 纹理映射

| FormationClass | FlagStyle | 纹理 |
|---------------|-----------|------|
| LAND_COMBAT, AIR | MILITARY | UnitFlagBase_Combo |
| NAVAL | NAVAL | UnitFlagNaval_Combo |
| SUPPORT | SUPPORT | UnitFlagSupport_Combo |
| CIVILIAN (贸易) | TRADE | UnitFlagTrade_Combo |
| CIVILIAN (宗教) | RELIGION | UnitFlagReligion_Combo |
| CIVILIAN (其他) | CIVILIAN | UnitFlagCivilian_Combo |

### InstanceManager（7个）

```lua
m_MilitaryInstanceManager   = InstanceManager:new("UnitFlag", "Anchor", Controls.MilitaryFlags)
m_CivilianInstanceManager   = InstanceManager:new("UnitFlag", "Anchor", Controls.CivilianFlags)
m_SupportInstanceManager    = InstanceManager:new("UnitFlag", "Anchor", Controls.SupportFlags)
m_TradeInstanceManager      = InstanceManager:new("UnitFlag", "Anchor", Controls.TradeFlags)
m_NavalInstanceManager      = InstanceManager:new("UnitFlag", "Anchor", Controls.NavalFlags)
m_AttentionMarkerIM         = InstanceManager:new("AttentionMarkerInstance", "Root")
m_HeroGlowIM                = InstanceManager:new("HeroGlowInstance", "Root")
```

### UnitFlag 对象

```lua
UnitFlag:new(playerID, unitID, flagType, flagStyle)  -- 构造函数
  :Initialize(...)     -- 设置每个实例
  :SetColor()          -- 玩家颜色
  :UpdateHealth()      -- 绿/黄/红血条
  :UpdateFlagType()    -- 纹理切换（普通/驻守/登船等）
  :SetPosition(x,y,z)  -- 3D 世界坐标 + 碰撞偏移
  :UpdateVisibility()  -- 迷雾/可见性
  :SetInteractivity()  -- 鼠标回调
  :destroy()           -- 释放实例
```

### 图块中的多单位排列 (UpdateIconStack)

最多 3 个单位共享一个图块，排列偏移为 `[-32,0]`, `[32,0]`, `[0,-45]`。编队通过 `Formation2`/`Formation3` 纹理连接。
