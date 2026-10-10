# DiplomacyActionView + DiplomacyRibbon + LeaderScene — 外交系统

> **来源**：`DiplomacyActionView.xml`(507行) + `.lua`(3103行) + `DiplomacyRibbon.xml`(72行) + `.lua`(976行) + `LeaderScene.xml`(24行) + `.lua`(167行)
> **地位**：外交界面的完整三件套——领袖交互面板、HUD领袖丝带、3D领袖场景。

---

## DiplomacyActionView — 领袖交互面板

### XML 核心控件

```
Button(ScreenClickRegion) ← 全屏右键拦截
Container(OverviewContainer) ← 总览模式
  AlphaAnim(AlphaIn) + SlideAnim(SlideIn) ← 面板淡入+滑入
    Container(DiplomacyRibbonContainer) ← 左侧垂直丝带
      DiplomacyRibbonVert ← LeaderIcon55 × N
    Container(PlayerContainer) ← 右侧玩家信息
      PlayerPanel + IntelPanel
      
Container(ConversationContainer) ← 对话模式 (Hidden=1)
  AlphaAnim(LeaderResponse_Alpha) + SlideAnim(LeaderResponse_Slide)
    Grid(LeaderResponseGrid) ← 外交气泡
      CivilizationIcon22 + LeaderResponseName
      LeaderResponseText + LeaderReasonText

Container(BlackFade) ← 场景切换黑场过渡
```

### TextureBar — 关系条（IntelRelationshipPanel）

```xml
<TextureBar ID="RelationshipBar" Size="286,3" Anchor="C,C"
            Texture="Diplomacy_RelationshipBar"
            Direction="Right" Percent="0" Speed="10"/>
```
Lua动态设置：
```lua
intelSubPanel.RelationshipBar:SetPercent(relationshipPercent)
intelSubPanel.RelationshipIcon:SetOffsetX(relationshipPercent * barWidth)
```

### 情报面板系统（IntelPanel）

4个选项卡：Overview → Gossip → Access Level → Relationship
每个选项卡 = 独立的 IM 实例。

**InstanceManager（27个）**：`ms_PlayerPanelIM`, `ms_DiplomacyRibbonIM`, `ms_IconOnlyIM`, `ms_IconAndTextIM`, `ms_LeftRightListIM`, `ms_TopDownListIM`, `ms_IntelPanelIM`（含13个Intel子IM）, `ms_ConversationSelectionIM`, `ms_uniqueIconIM`, `ms_uniqueTextIM`

### 对话模式流程

```
1. Events.DiplomacyStatement → OnDiplomacyStatement
2. 确定视图模式 (CONVERSATION_MODE / CINEMA_MODE)
3. 查找语句处理器 (DEFAULT / MAKE_DEAL / MAKE_DEMAND)
4. ApplyStatement() → 填充 LeaderResponseText + ConversationSelectionStack
5. 用户点击对话选项 → OnSelectConversationDiplomacyStatement
6. DiplomacyManager.AddStatement() / AddResponse()
```

---

## DiplomacyRibbon — HUD 领袖丝带

```
AlphaAnim(ChatIndicatorWaitTimer)
Container(RibbonContainer) ← 右侧水平丝带
  ScrollPanel(LeaderScroll) → Stack(LeaderStack) ← StackGrowth="Left"
  Button(NextButtonContainer) / Button(PreviousButtonContainer) ← 滚动箭头
```

### LeaderInstance 结构
```xml
<Instance Name="LeaderInstance">
  <Container ID="LeaderContainer" Size="63,auto">
    <Grid ID="StatBacking" Style="Subheader">
      <SlideAnim ID="ActiveSlide" EndOffset="0,16"> ← 当前回合动画
        <AlphaAnim ID="ActiveLeaderAndStats"> ← 淡入
          <MakeInstance Name="LeaderIcon45"/>
          <Stack ID="StatStack" StackGrowth="Bottom">
            <Label ID="Score"/> <Label ID="Military"/> <Label ID="Science"/>
            <Label ID="Culture"/> <Label ID="Gold"/> <Label ID="Faith"/>
          </Stack>
        </AlphaAnim>
      </SlideAnim>
    </Grid>
  </Container>
</Instance>
```

### InstanceManager
```lua
m_kLeaderIM = InstanceManager:new("LeaderInstance", "LeaderContainer", Controls.LeaderStack)
```

### 回合激活动画
```lua
-- 当前活跃玩家：播放 ActiveSlide
uiLeader.ActiveSlide:SetToBeginning()
uiLeader.ActiveSlide:Play()
-- 非活跃回合：隐藏统计
```

### 数据更新
`UpdateStatValues(playerID, uiLeader)` → 从玩家对象读取 Score/Military/Science/Culture/Gold/Faith → 更新每个LeaderInstance的Label。

### 事件（18个游戏事件驱动刷新）
`DiplomacyDeclareWar/MakePeace/Meet`, `PlayerDefeat`, `LocalPlayerTurnBegin/End`, `RemotePlayerTurnBegin/End`

---

## LeaderScene — 3D 领袖场景 + 视差背景

### XML
```
Container(LeaderScene) ← Hidden=1, 传给引擎作为领袖背景
  Container(Backgrounds) ← 视差图层实例
  Image(BottomLetterbox) / Image(TopLetterbox) ← 黑边
  Image×4 ← 渐变叠加层
```

### 视差系统
```lua
Instance(Background_Anim) ← SlideAnim, Function="OutQuint", Power=4, Speed=.5
  Image(Background_Image) ← Sampler=Linear, StretchMode=Fill
```
`GenerateLayers(selectedPlayerID)` → 从 `Leader.SceneLayers` 读取并按层数创建视差图层。`Parallax(distance)` → N-1层从`-distance`滑动到0。

### 核心事件
```lua
-- LeaderScene监听
LuaEvents.DiploScene_SceneOpened.Add(OnSceneOpened) → 创建视差图层
LuaEvents.DiploScene_SceneClosed.Add(UninitializeView) → 销毁
-- 引擎调用
UI.SetLeaderSceneControl(Controls.LeaderScene)  ← 将Container传给引擎
Events.ShowLeaderScreen(leaderName, isLocalPlayer) ← 触发3D领袖加载
```
