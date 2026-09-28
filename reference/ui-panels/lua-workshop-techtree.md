# TechTree + CivicsTree — 科技/市政树全屏面板

> **来源**：`Screens/TechTree.xml`(260行) + `.lua`(2083行) + `Screens/CivicsTree.xml`(363行) + `.lua`(2442行) + `TechTreeNode.xml`(30行) + `Choosers/ResearchChooser.*` + `CivicsChooser.*`
> **地位**：全屏树形科技/市政面板——FlipAnim+Meter+ScrollPanel同步滚动+搜索。

---

## 面板结构

```
Container(Anchor="C,C", Size="full,768")
  PullDown(FilterPulldown) ← 分类筛选下拉
  EditBox(SearchEditBox) ← CallOnChar="1" 实时搜索
  GridButton(ToggleKeyButton) ← 图例切换
  
  ← 4个同步滚动面板
  ScrollPanel(ArtScroller) ← 背景艺术层（视差 1.2×）
  ScrollPanel(LineScroller) ← 连接线层
  ScrollPanel(NodeScroller) ← 节点层（主层）
  ScrollPanel(EraArtScroller) ← 时代背景层
  
  ← 搜索结果面板
  Container(SearchResultsPanelContainer) ← Hidden=1
    ScrollPanel(SearchResultsPanel) → Stack(SearchResultsStack)
```

## 核心实例

### NodeInstance（科技树节点，TechTreeNode.xml）
```xml
<Instance Name="NodeInstance">
  <Container ID="Top" Size="370,1">
    <GridButton ID="NodeButton" Size="370,84"
                Texture="TechTree_GearButton" StateOffsetIncrement="0,84"
                SliceCorner="77,45" SliceTextureSize="133,84">
      <FlipAnim ID="GearAnim" Size="34,38" Speed="20" FrameCount="3" Columns="3" Hidden="1"/>
      <Meter ID="BoostMeter" Size="68,68" Texture="TechTree_Meter_Boost" Follow="1"/>
      <Meter ID="ProgressMeter" Size="68,68" Texture="TechTree_Meter_Fill"/>
      <Label ID="NodeName" Style="TreeNodeText"/>
      <Label ID="Turns" Style="TreeTurnText"/>
      <Stack ID="UnlockStack" StackGrowth="Right"/> ← 解锁图标
      <Image ID="Icon" Size="42,42" Texture="Tech42"/>
      <Image ID="Bolt"/> ← 已加速标记
    </GridButton>
  </Container>
</Instance>
```
CivicsTree 有两个变体：`NodeInstance`(420×84) 和 `LargeNodeInstance`(420×140)

### Shared Instances（两个树共用）
| 实例 | 用途 |
|------|------|
| `EraLabelInstance` | 时代标签（旋转90°） |
| `EraDotInstance` | 时间轴上的时代标记点 |
| `PlayerMarkerInstance` | 玩家进度标记（含 TurnLabel/TurnNumber/Portrait） |
| `LineImageInstance` | 连接线（StretchMode=Tile） |
| `SearchResultInstance` | 搜索结果条目 |
| `UnlockInstance` | 解锁图标（38×38） |

## InstanceManager（TechTree: 8个, CivicsTree: 13个）

```lua
-- TechTree
m_kNodeIM          = InstanceManager:new("NodeInstance", "Top", Controls.NodeScroller)
m_kLineIM          = InstanceManager:new("LineImageInstance", "LineImage", Controls.LineScroller)
m_kEraLabelIM      = InstanceManager:new("EraLabelInstance", "Top", Controls.ArtScroller)
m_kSearchResultIM  = InstanceManager:new("SearchResultInstance", "Root", Controls.SearchResultsStack)
m_kMarkerIM        = InstanceManager:new("PlayerMarkerInstance", "Top", Controls.TimelineScrollbar)

-- CivicsTree 额外
m_kDiplomaticPolicyIM = InstanceManager:new("DiplomaticPolicyInstance", ...)
m_kEconomicPolicyIM   = InstanceManager:new("EconomicPolicyInstance", ...)
m_kMilitaryPolicyIM   = InstanceManager:new("MilitaryPolicyInstance", ...)
m_kWildcardPolicyIM   = InstanceManager:new("WildcardPolicyInstance", ...)
```

## 搜索系统

```lua
-- 创建搜索上下文
Search.CreateContext("Technologies", ...)
Search.AddData(entry)   -- 添加每个可搜索条目
Search.Optimize()

-- 实时搜索回调
Controls.SearchEditBox:RegisterStringChangedCallback(OnSearchCharCallback)
function OnSearchCharCallback()
    Search.Search("Technologies", str, 100)  -- 限制100个结果
    -- 填充 SearchResultsStack
end
```

## 4层同步滚动（视差效果）

```lua
function OnScroll(control, percent)
    -- NodeScroller 驱动，其余跟随
    Controls.ArtScroller:SetScrollValue(percent * PARALLAX_SPEED)
    Controls.LineScroller:SetScrollValue(percent)
    Controls.EraArtScroller:SetScrollValue(percent)
end
```

## ResearchChooser / CivicsChooser — 弹窗选择器

```
SlideAnim(Style="ChooserAnim")
  Grid(MainPanel) ← 主面板 (296×95)
    FlipAnim(MainGearAnim) ← 齿轮动画 (Speed=10, Stopped=1)
    Meter(BoostMeter) + Meter(ProgressMeter) ← 56×56 环形进度
    Stack(UnlockStack) ← 解锁图标行
    
  ScrollPanel(ChooseResearchList) ← 可选列表
    Stack(ResearchStack) ← 列表项实例
```

### ResearchListInstance
```xml
<Instance Name="ResearchListInstance">
  <Container ID="TopContainer" Size="276,90">
    <GridButton ID="Top" Size="276,80"
                Texture="ResearchPanel_ChooserButton" StateOffsetIncrement="0,80">
      <Meter ID="BoostMeter" Size="44,44" Follow="1"/>
      <Meter ID="ProgressMeter" Size="44,44" Follow="1"/>
      <Image ID="Icon" Size="30,30"/>
      <Label ID="TechName" Style="FontNormal14"/>
      <Label ID="TurnsLeft"/>
      <Stack ID="UnlockStack" StackGrowth="Right" StackPadding="-1"/>
    </GridButton>
  </Container>
</Instance>
```
