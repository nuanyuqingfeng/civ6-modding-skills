# DiplomacyDealView — 交易界面（Instance 模板黄金标准）

> **来源**：`DiplomacyDealView.xml`(468行) + `.lua`(3179行)
> **地位**：Instance 模板最丰富、最完整的官方范例。9个Instance定义覆盖了图标按钮到多层嵌套报价面板。

---

## XML 结构

```
Container(TradePanel) ← 全屏
  AlphaAnim(TradePanelFade) + SlideAnim(TradePanelSlide) ← 淡入+滑入
    Image ← 宽幅横幅背景 (Controls_BannerWide, StretchMode=Tile)
    
    ← 页眉对话气泡
    Grid(外交气泡) + MakeInstance(CivilizationIcon22)
      AlphaAnim(LeaderDialogFade) + SlideAnim(LeaderDialogSlide)
        Label(LeaderDialog) + Label(LeaderEffect)
    
    ← 操作按钮
    GridButton(AcceptDeal) ← ButtonConfirm, 200×41
    GridButton(RefuseDeal) ← ButtonLightWeight, 200×32
    GridButton(EqualizeDeal) ← ButtonLightWeight, 200×32
    GridButton(DemandDeal) ← ButtonRed, 200×41
    
    ← 报价列 MyOffer / TheirOffer (ScrollPanel + Stack)
    ← 库存列 MyInventory / TheirInventory (ScrollPanel + Stack + WrapWidth)
    
    ← 数值编辑弹窗
    Box(ValueEditPopupBackground) ← 半透明黑遮罩
      EditBox(ValueAmountEditBox) ← NumberInput=1, MaxLength=11
```

## 9个 Instance 模板

### 显示模板

| Instance | 根控件 | 用途 |
|----------|--------|------|
| `IconOnly` | GridButton `SelectButton` (56×56) | 纯图标项目 |
| `IconAndText` | GridButton `SelectButton` (210×56) | 图标+文本+删除按钮 |
| `CityIconAndDetails` | Container `CityDetailsContainer` | 带展开/折叠的城市项目 |
| `MinimizedSection` | Grid `MinimizedSectionContainer` | 折叠视图 |

### 布局模板

| Instance | 根控件 | 布局 |
|----------|--------|------|
| `LeftRightList` | Stack `List` | 水平排列（资源类：金币/奢侈/战略）+ 标题 |
| `TopDownList` | Stack `List` | 垂直排列（协议/城市/巨作/人质）+ 可折叠标题 |

### 面板模板

| Instance | 根控件 | 用途 |
|----------|--------|------|
| `MyOffers` | Stack `OfferStack` | 完整的"我的报价"面板（一次性/30回合/协议/城市/巨作/人质） |
| `TheirOffers` | Stack `OfferStack` | 对称的"对方报价"面板 |
| `AgreementOptionInstance` | GridButton `AgreementOptionButton` (280×56) | 协议选项 |

### IconAndText 结构（模板范例）
```xml
<Instance Name="IconAndText">
  <GridButton ID="SelectButton" Style="ButtonDraggableGrid" Size="210,56">
    <Stack Size="parent,0" StackGrowth="Right">
      <Container Size="44,parent">
        <Image ID="Icon" StretchMode="None" Size="44,44" Anchor="C,C"/>
        <Label ID="AmountText" Style="FontNormalBold12" Anchor="R,B" Offset="24,-9"/>
      </Container>
      <Container Size="parent-44,parent">
        <Stack StackGrowth="Bottom" Anchor="L,C">
          <Label ID="IconText" Size="parent,0" Style="FontNormalBold12"/>
          <ScrollTextField ID="ValueText" Size="125,0" Style="FontNormalBold12"/>
        </Stack>
      </Container>
    </Stack>
    <Image ID="UnacceptableIcon" Texture="Alert18" Size="18,18" Anchor="R,T" Hidden="1"/>
    <Button ID="RemoveButton" Texture="Controls_RemoveDeal" Size="22,22" Hidden="1"/>
  </GridButton>
</Instance>
```

## InstanceManager（7个）

```lua
ms_IconOnlyIM        = InstanceManager:new("IconOnly", "SelectButton", Controls.IconOnlyContainer)
ms_IconAndTextIM     = InstanceManager:new("IconAndText", "SelectButton", Controls.IconAndTextContainer)
ms_LeftRightListIM   = InstanceManager:new("LeftRightList", "List", ...)
ms_TopDownListIM     = InstanceManager:new("TopDownList", "List", ...)
ms_AgreementOptionIM = InstanceManager:new("AgreementOptionInstance", "AgreementOptionButton", ...)
ms_CityDetailsIM     = InstanceManager:new("CityIconAndDetails", "CityDetailsContainer", ...)
ms_MinimizedSectionIM = InstanceManager:new("MinimizedSection", "MinimizedSectionContainer")
```

## 关键模式

### 多层嵌套 Instance（MyOffers/TheirOffers）

每个报价面板 = 完整的嵌套 Instance：
```
OfferStack (StackGrowth=Bottom)
  ├─ DirectionsBracket ← 指示文本
  ├─ OneTimeDeals (StackGrowth=Right, WrapWidth=240)
  ├─ For30TurnsDeals (同上)
  ├─ Agreements (带展开/折叠 MinimizedStack)
  ├─ Cities (带展开/折叠 MinimizedStack)
  ├─ GreatWorks (带展开/折叠 MinimizedStack)
  └─ Captives (带展开/折叠 MinimizedStack)
```

### Instance 缓存容器

```xml
<Container ID="IconOnlyContainer" Hidden="1"/>
<Container ID="IconAndTextContainer" Hidden="1"/>
```
隐藏容器作为 IM 的父控——实例在隐藏容器中创建，`GetInstance(parent)` 时 ChangeParent 到可见位置。

### 展开/折叠组模式

每个可折叠分类存储两组 Instance：
- `XxxDealsStack` ← 展开的全尺寸列表
- `MinimizedXxxDealsStack` ← 折叠的 WrapWidth 紧凑视图
- `OnDealsHeaderCollapseButton` 在两者间切换

### 数值编辑弹窗

```xml
<EditBox ID="ValueAmountEditBox" NumberInput="1" EditMode="1" MaxLength="11" .../>
<Button ID="ValueAmountEditLeftButton" Style="ArrowButtonLeft"/>
<Button ID="ValueAmountEditRightButton" Style="ArrowButtonRight"/>
```
左右箭头增减数值，EditBox 手动输入，`NumberInput="1"` 限制纯数字。

### PopupDialog 集成
```lua
m_kPopupDialog = PopupDialog:new("DiplomacyDealView")
```
用于不可接受交易项目的确认弹窗。
