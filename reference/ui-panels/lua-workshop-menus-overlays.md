# 菜单系统 + 覆盖层面板 — 暂停/保存/城邦/排名/结束

> **来源**：`Menus/InGameTopOptionsMenu.*`(787行) + `Menus/SaveGameMenu.*`(725行) + `PartialScreens/CityStates.*`(1787行) + `WorldRankings.*`(2588行) + `ReportsList.*` + `EndGame/EndGameMenu.*`
> **地位**：游戏内 Shell 菜单、存档菜单、城邦面板、世界排名面板、结束画面。

---

## InGameTopOptionsMenu — 游戏内暂停菜单

### AlphaAnim+SlideAnim 模态弹窗

```
AlphaAnim(AlphaIn) ← 全屏暗色遮罩 (AlphaBegin=0→1, Speed=9)
  SlideAnim(SlideIn) ← 菜单窗口滑入 (Start="0,-20"→End="0,0", Speed=9)
    Grid(PauseWindow) ← DropShadow2 样式
      Label(WindowTitle) ← ShellHeader
      Stack(MainStack) ← StackGrowth=Bottom
        GridButton(ReturnButton) ← PauseMenuButton 样式
        GridButton(QuickSaveButton)
        GridButton(SaveGameButton)
        GridButton(LoadGameButton)
        GridButton(OptionsButton)
        GridButton(RetireButton)
        GridButton(RestartButton)
        GridButton(MainMenuButton)
        GridButton(ExitGameButton)
        
      Grid(ModsInUse) ← 隐藏的 Mod 列表 (DecoFrame)
        Label(ModsInUseHeader)
        ScrollPanel(ModListings) → Stack(ModListingsStack)
          ← ModInstance(Lua 的 g_ModListingsManager)
    
    Container(GameDetails) ← 底部游戏信息
      Image(LeaderIcon) + Image(GameDifficulty) + Image(GameSpeed)
      Label(VersionLabel)

  ← 子 LuaContext:
  LoadGameMenu / SaveGameMenu / Options (全部 Hidden=1)
```

### 关闭动画
```lua
function Close()
    Controls.SlideIn:Reverse()
    Controls.AlphaIn:Reverse()
    Controls.PauseWindowClose:Play()  -- 额外淡出
end
```
还有一个独立的 `AlphaAnim(PauseWindowClose)` 用于关闭过渡。

### 按钮显示/隐藏逻辑
```lua
SetupButtons() ← 根据游戏状态控制按钮可见性:
  - 单人: 隐藏 RestartButton
  - 热座: 隐藏 QuickSaveButton
  - PBC: 显示 PBCDeleteButton/PBCQuitButton
  - 多人: 显示 ModsInUse
```

---

## SaveGameMenu — 存档菜单

### XML 结构
```
MainWindow(1024×768)
  LogoContainer + Logo(MainLogo.dds)
  BackButton(ShellButtonOrnateFlat)
  Label(WindowHeader) ← ShellHeader

  ← 左侧: 文件列表
  PullDown(SortByPullDown) + PullDown(DirectoryPullDown)
  GridButton(CloudCheck) ← 云端存档复选框
  ScrollPanel(ScrollPanel) → Stack(FileListEntryStack)
    ← FileEntry 实例 (含选择动画 AlphaAnim+SlideAnim)

  ← 右侧: 检查器
  Grid(InspectorArea)
    EditBox(FileName) ← CallOnChar="1", FocusStop=1, MaxLength=32
    Image(SavedMinimap) ← 存档缩略图
    Image(LeaderIcon/GameDifficulty/GameSpeed) ← 游戏详情图标
    ScrollPanel(GameInfoScrollPanel) → Stack(GameInfoStack) ← 存档详情
    
    GridButton(ActionButton) ← ButtonConfirm
    GridButton(Delete) ← ButtonRed (Hidden=1)

  ← 删除确认模态
  Box(DeleteConfirm) ← 全屏暗色遮罩
    AlphaAnim + SlideAnim
      Label(DeleteHeader) + Label(Message)
      GridButton(Yes) + GridButton(No)
```

### CallOnChar 实时文件名验证
```lua
Controls.FileName:RegisterStringChangedCallback(OnFileNameChange)
function OnFileNameChange(fileNameEntry)
    g_FilenameIsValid = ValidateFileName(fileName)
    SetDontUpdateFileName(true/false)  -- 防止循环更新
end
```

### 文件条目实例（FileEntry）
```xml
<Instance Name="FileEntry">
  <Container ID="InstanceRoot">
    <GridButton ID="Button"/>
    <AlphaAnim ID="SelectionAnimAlpha"> ← 选中动画
      <SlideAnim ID="SelectionAnimSlide">
        <Label ID="ButtonText"/>
      </SlideAnim>
    </AlphaAnim>
  </Container>
</Instance>
```

---

## CityStates — 城邦面板

### 双层视图
```
← 主视图: 城邦列表 + 使者管理
SlideAnim(SlideAnim) ← 从右侧滑入
  ListOfCityStates
    HeaderBG ← 城邦数量 + 使者进度仪表
      Meter(EnvoysMeter) ← 24×24 使者圆点 (Speed=1, Follow=1)
      Stack(EnvoysStack) ← 使者计数 + +/- 按钮
    
    ScrollPanel(CityStateScroll) → Stack(CityStateStack)
      ← CityStateRowInstance × N (每行含: 城邦图标, 名称, 使者数, 3级加成图标, 宗主国标签)
    
    BonusArea ← 类型加成详情

← 单城邦视图: 详情 + 选项卡
SingleCityState
  Image(CityStateTypeIcon) ← CivSymbols64
  Label(CityStateName)
  GridButton(PeaceWarButton) ← 宣战/和平
  GridButton(LevyMilitaryButton) ← 征召军队
  ReportArea → 4个选项卡:
    EnvoysSentArea / InfluenceArea / QuestsArea / RelationshipsArea
```

### CityStateRowInstance 关键子控件
```
BoxButton(ID="Button") ← 可点击的城邦图标区域
GridButton(ID="NameButton") ← 名称
Image(Envoy) ← 使者图标组:
  Button(EnvoyLessButton) / Button(EnvoyMoreButton) / Label(EnvoyCount)
BonusImage1/3/6 ← 3/6使者加成的图标
BonusImageSuzerainOff/On ← 宗主国加成图标
Label(SuzerainLabel) / Label(Suzerain) ← 宗主国显示
Button(LookAtButton) ← 查看镜头
```

### InstanceManager（12个）
```lua
m_CityStateRowIM    = InstanceManager:new("CityStateRowInstance", "CityStateBase", ...)
m_BonusItemIM       = InstanceManager:new("BonusItemOnInstance", "Top", ...)
m_InfluenceRowIM    = InstanceManager:new("InfluenceRowInstance", "Top", ...)
m_QuestsIM          = InstanceManager:new("QuestInstance", "Top", ...)
m_RelationshipsButtonIM = InstanceManager:new("RelationshipIcon", "Background", ...)
-- 还有 CityStateColumnIM, BonusCityHeaderIM, EnvoysBonusItemIM 等
```

### 使者令牌系统
```lua
-- +/- 按钮累积待发送令牌
OnMoreEnvoyTokens(playerID) → pendingTokens++ → RealizeEnvoyChangeButtons()
OnConfirmPlacement() → 发送所有累计令牌 → WorldBuilder.PlayerManager:SetInfluenceTokens()
```

---

## WorldRankings — 世界排名

### XML 结构
```
SlideAnim(SlideAnim) ← 从右侧滑入
  
  TabContainer ← 动态标签 (CreateTabs)
    总体 / 分数 / 科技 / 文化 / 军事 / 宗教 / 自定义
    
  ← 每个视图独立的 ScrollPanel + Stack
  OverallView / ScoreView / ScienceView / CultureView / DominationView / ReligionView / GenericView
```

### TextureBar 大量使用
```xml
<!-- 科技里程碑进度条 -->
<TextureBar ID="ObjBar_1" Direction="Right" Speed="0" Size="56,16"
            TextureOffset="0,16" Texture="Controls_MeterLinear"/>

<!-- 文化旅游进度（垂直填充） -->
<TextureBar ID="TouristsFill" Direction="Up" Speed="0" Size="52,52"
            TextureOffset="0,52" Texture="Tourism_Meter"/>
```

### InstanceManager（20+个）
每个视图有独立的 IM：`g_ScoreIM`, `g_ScienceIM`, `m_CultureIM`, `m_DominationIM`, `m_ReligionIM`, `g_GenericIM` + 对应的 Team 变体 + 错误/实例 IM。

### 动态切换逻辑
```lua
PopulateTabs() ← 扫描 GameInfo.Victories() → 创建标签
OnTabClicked() → ResetState() + ViewXxx()
ViewScience() → GatherScienceData() → PopulateScienceTeamInstance/PlayerInstance
```

---

## ReportsList — 报告列表按钮

最简洁面板：
```xml
Grid(Background) ← EventPopupFrame, 200×auto
  Stack(MainStack) ← Padding=3
    Label(EmpireTitle) ← "帝国"
    Stack(EmpireReportsStack) ← ReportButtonInstance × N
    Label(GlobalTitle) ← "全球"
    Stack(GlobalReportsStack) ← ReportButtonInstance × N
```

6个报告按钮 → 触发 `LuaEvents.X` 打开对应的全屏报告（Yields/Resources/CityStatus/Gossip等）。

---

## EndGameMenu — 游戏结束画面

### 电影支持
```xml
BoxButton(MovieFill) ← 全屏黑底 (ConsumeAllMouse=1)
Movie(Movie) ← LoopMovie=0, StretchMode=UniformToFill
```
Lua 控制：
```lua
OnReplayMovie() → play movie → OnMovieExitOrFinished() → 恢复音乐/显示挑战弹窗
Controls.MovieFill:SetHide(false/true)  ← 显示/隐藏黑底
```

### 胜利/失败类型样式表
```lua
Styles = {
    VICTORY_CONQUEST = { Ribbon="EndGame_Ribbon_Domination", Movie="...", ... },
    VICTORY_CULTURE  = { Background="EndGame_BG_Culture", ... },
    DEFEAT_TIME      = { Color="Civ6Blue", ... },
    -- 每个条目的 RibbonIcon / Ribbon / Background / Movie / SndStart/Stop / Color
}
```

### 排行榜（RankEntry Instance）
```xml
<Instance Name="RankEntry">
  <Container ID="Root">
    <Label ID="Number"/> ← 排名数字
    <Label ID="LeaderName"/> ← 领袖名
    <Label ID="LeaderScore"/> ← 分数
    <Label ID="LeaderQuote"/> ← 引用
  </Container>
</Instance>
```
