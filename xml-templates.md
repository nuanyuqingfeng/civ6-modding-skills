# XML Layout Templates

Copy-pasteable XML templates for common Civ6 UI patterns.

---

## Template 1: Fullscreen Overlay Panel

A modal panel that covers the entire screen with a semi-transparent background.

```xml
<?xml version="1.0" encoding="utf-8"?>
<Context Name="MyPanel">
    <!-- Main container: fullscreen, centered, starts hidden -->
    <Container ID="MainContainer" Size="parent,parent" Anchor="C,C" Hidden="1" ConsumeMouseButton="1">
        <!-- Semi-transparent background overlay -->
        <Image ID="Background" Size="parent,parent" Color="0,0,0,180" ConsumeMouseButton="1"/>

        <!-- Panel frame (centered, fixed size) -->
        <Container ID="PanelFrame" Size="900,700" Anchor="C,C" ConsumeMouseButton="1">
            <!-- Background texture -->
            <Grid ID="PanelBG" Size="parent,parent" Texture="Controls_GenericPanel"
                  SliceCorner="24,24" SliceTextureSize="48,48" Color="255,255,255,255"/>

            <!-- Title bar -->
            <Label ID="TitleLabel" Anchor="C,T" Offset="0,20"
                   String="LOC_MY_PANEL_TITLE" Font="Font_22" Align="Center"/>

            <!-- Close button (top-right) -->
            <GridButton ID="CloseButton" Anchor="R,T" Offset="-20,15" Size="32,32"
                        Texture="Controls_Close" SliceCorner="14,14" SliceTextureSize="28,28"/>

            <!-- Content area with scroll -->
            <ScrollPanel ID="ContentScroll" Anchor="C,C" Size="parent-40,parent-80"
                         Offset="0,20" ScrollBarAutoHide="1">
                <Stack ID="ItemStack" Anchor="T,L" StackGrowth="Vertical"
                       Padding="0,0,8,0" StackGrowthSpacing="4"/>
            </ScrollPanel>
        </Container>
    </Container>
</Context>
```

**Key points:**
- `Hidden="1"` — mod contexts start hidden, show via Lua
- `ConsumeMouseButton="1"` — prevents click-through on background
- `SliceCorner` + `SliceTextureSize` — 9-slice scaling for the panel background
- `parent-40` — subtracts 40px from parent width (20px padding each side)

---

## Template 2: Side Panel (Right Edge)

A panel that slides in from the right side of the screen.

```xml
<?xml version="1.0" encoding="utf-8"?>
<Context Name="MySidePanel">
    <Container ID="MainContainer" Size="400,parent" Anchor="R,C" Hidden="1"
               ConsumeMouseButton="1">
        <!-- Background -->
        <Grid ID="PanelBG" Size="parent,parent" Texture="Controls_GenericPanel"
              SliceCorner="24,24" SliceTextureSize="48,48"/>

        <!-- Header -->
        <Container ID="Header" Size="parent,60" Anchor="T,L">
            <Label ID="TitleLabel" Anchor="C,C" String="LOC_MY_SIDE_PANEL"
                   Font="Font_18"/>
            <GridButton ID="CloseButton" Anchor="R,C" Offset="-10,0" Size="28,28"
                        Texture="Controls_Close" SliceCorner="14,14" SliceTextureSize="28,28"/>
        </Container>

        <!-- Content -->
        <ScrollPanel ID="ContentScroll" Anchor="T,L" Offset="0,60"
                     Size="parent-16,parent-76" ScrollBarAutoHide="1">
            <Stack ID="ContentStack" Anchor="T,L" StackGrowth="Vertical"/>
        </ScrollPanel>
    </Container>
</Context>
```

---

## Template 3: List Panel with InstanceManager

A scrollable list of dynamically created items.

```xml
<?xml version="1.0" encoding="utf-8"?>
<Context Name="MyListPanel">
    <Container ID="MainContainer" Size="parent,parent" Anchor="C,C" Hidden="1"
               ConsumeMouseButton="1">
        <Image ID="Background" Size="parent,parent" Color="0,0,0,180" ConsumeMouseButton="1"/>

        <Container ID="PanelFrame" Size="800,600" Anchor="C,C">
            <Grid ID="PanelBG" Size="parent,parent" Texture="Controls_GenericPanel"
                  SliceCorner="24,24" SliceTextureSize="48,48"/>

            <Label ID="TitleLabel" Anchor="C,T" Offset="0,20"
                   String="LOC_MY_LIST_TITLE" Font="Font_22"/>
            <GridButton ID="CloseButton" Anchor="R,T" Offset="-20,15" Size="32,32"
                        Texture="Controls_Close" SliceCorner="14,14" SliceTextureSize="28,28"/>

            <!-- List area -->
            <ScrollPanel ID="ListScroll" Anchor="C,C" Size="parent-40,parent-80"
                         Offset="0,20" ScrollBarAutoHide="1">
                <Stack ID="ListStack" Anchor="T,L" StackGrowth="Vertical"
                       StackGrowthSpacing="4"/>
            </ScrollPanel>
        </Container>
    </Container>

    <!-- Instance template for list items -->
    <Instance Name="ListItem">
        <Container ID="Root" Size="parent,80" ConsumeMouseButton="1">
            <Grid ID="BG" Size="parent,parent" Texture="Controls_GenericPanel_Blank"
                  SliceCorner="8,8" SliceTextureSize="16,16" Color="40,40,40,200"
                  ConsumeMouseButton="1"/>
            <Image ID="Icon" Size="48,48" Anchor="L,C" Offset="16,0"/>
            <Label ID="NameLabel" Anchor="L,C" Offset="80,0" Font="Font_16"
                   TruncateWidth="400"/>
            <Label ID="ValueLabel" Anchor="R,C" Offset="-16,0" Font="Font_16"
                   Align="Right"/>
            <Button ID="ActionButton" Anchor="R,C" Offset="-120,0" Size="100,36"
                    Style="ButtonNormalText" String="LOC_ACTION"/>
        </Container>
    </Instance>
</Context>
```

**Matching Lua pattern:**
```lua
local m_listIM:table = InstanceManager:new("ListItem", "Root", Controls.ListStack);

function Refresh()
    m_listIM:ResetInstances();

    for i, itemData in ipairs(m_dataList) do
        local inst = m_listIM:GetInstance();
        inst.Icon:SetTexture(0, 0, itemData.IconAtlas);
        inst.NameLabel:SetText(itemData.Name);
        inst.ValueLabel:SetText(tostring(itemData.Value));
        inst.ActionButton:RegisterCallback(Mouse.eLClick, function()
            OnAction(itemData.ID);
        end);
    end

    Controls.ListStack:CalculateSize();
    Controls.ListStack:ReprocessAnchoring();
    Controls.ListScroll:CalculateInternalSize();
end
```

---

## Template 4: Tab Panel

A panel with multiple switchable tabs.

```xml
<?xml version="1.0" encoding="utf-8"?>
<Context Name="MyTabPanel">
    <Container ID="MainContainer" Size="parent,parent" Anchor="C,C" Hidden="1"
               ConsumeMouseButton="1">
        <Image ID="Background" Size="parent,parent" Color="0,0,0,180" ConsumeMouseButton="1"/>

        <Container ID="PanelFrame" Size="1000,700" Anchor="C,C">
            <Grid ID="PanelBG" Size="parent,parent" Texture="Controls_GenericPanel"
                  SliceCorner="24,24" SliceTextureSize="48,48"/>

            <GridButton ID="CloseButton" Anchor="R,T" Offset="-20,15" Size="32,32"
                        Texture="Controls_Close" SliceCorner="14,14" SliceTextureSize="28,28"/>

            <!-- Tab buttons -->
            <Stack ID="TabButtonStack" Anchor="T,L" Offset="20,10" Size="parent-40,40"
                   StackGrowth="Horizontal" StackGrowthSpacing="4">
                <Button ID="Tab1Button" Size="120,36" Style="ButtonNormalText"
                        String="LOC_TAB_1"/>
                <Button ID="Tab2Button" Size="120,36" Style="ButtonNormalText"
                        String="LOC_TAB_2"/>
                <Button ID="Tab3Button" Size="120,36" Style="ButtonNormalText"
                        String="LOC_TAB_3"/>
            </Stack>

            <!-- Tab content containers (only one visible at a time) -->
            <Container ID="Tab1Content" Size="parent-40,parent-70" Anchor="C,C" Offset="0,15">
                <!-- Tab 1 content here -->
            </Container>
            <Container ID="Tab2Content" Size="parent-40,parent-70" Anchor="C,C" Offset="0,15"
                       Hidden="1">
                <!-- Tab 2 content here -->
            </Container>
            <Container ID="Tab3Content" Size="parent-40,parent-70" Anchor="C,C" Offset="0,15"
                       Hidden="1">
                <!-- Tab 3 content here -->
            </Container>
        </Container>
    </Container>
</Context>
```

**Matching Lua pattern:**
```lua
local m_tabContents:table = {};
local m_currentTab:number = 1;

function SelectTab(tabIndex:number)
    -- Hide all tabs
    for i, container in ipairs(m_tabContents) do
        container:SetHide(true);
    end
    -- Show selected tab
    m_tabContents[tabIndex]:SetHide(false);
    m_currentTab = tabIndex;
end

function OnInit(isReload:boolean)
    m_tabContents = { Controls.Tab1Content, Controls.Tab2Content, Controls.Tab3Content };

    Controls.Tab1Button:RegisterCallback(Mouse.eLClick, function() SelectTab(1); end);
    Controls.Tab2Button:RegisterCallback(Mouse.eLClick, function() SelectTab(2); end);
    Controls.Tab3Button:RegisterCallback(Mouse.eLClick, function() SelectTab(3); end);

    SelectTab(1);
end
```

---

## Template 5: Tooltip-Rich Info Card

A compact card with icon, text, and rich tooltip.

```xml
<Instance Name="InfoCard">
    <Container ID="Root" Size="parent,60">
        <Grid ID="BG" Size="parent,parent" Texture="Controls_GenericPanel_Blank"
              SliceCorner="8,8" SliceTextureSize="16,16" Color="30,30,30,200"/>
        <Image ID="Icon" Size="40,40" Anchor="L,C" Offset="10,0"
               Texture="ICON_DEFAULT" ToolTip="LOC_ICON_TOOLTIP"/>
        <Label ID="Title" Anchor="L,C" Offset="60,-8" Font="Font_14"
               String="LOC_CARD_TITLE"/>
        <Label ID="Subtitle" Anchor="L,C" Offset="60,10" Font="Font_12"
               String="LOC_CARD_SUBTITLE" Color="180,180,180,255"/>
        <Label ID="Value" Anchor="R,C" Offset="-10,0" Font="Font_18"
               Align="Right"/>
    </Container>
</Instance>
```

---

## Template 6: Confirmation Popup

A centered popup with message and OK/Cancel buttons.

```xml
<Instance Name="ConfirmPopup">
    <Container ID="Root" Size="parent,parent" Anchor="C,C" ConsumeMouseButton="1">
        <Image ID="Overlay" Size="parent,parent" Color="0,0,0,150" ConsumeMouseButton="1"/>
        <Container ID="Dialog" Size="500,250" Anchor="C,C">
            <Grid ID="DialogBG" Size="parent,parent" Texture="Controls_GenericPanel"
                  SliceCorner="24,24" SliceTextureSize="48,48"/>
            <Label ID="Message" Anchor="C,C" Offset="0,-30" Size="parent-40,auto"
                   Font="Font_16" Align="Center" Wrap="1"/>
            <Stack ID="ButtonStack" Anchor="C,B" Offset="0,-30"
                   StackGrowth="Horizontal" StackGrowthSpacing="20">
                <Button ID="OKButton" Size="140,40" Style="ButtonNormalText"
                        String="LOC_OK"/>
                <Button ID="CancelButton" Size="140,40" Style="ButtonNormalText"
                        String="LOC_CANCEL"/>
            </Stack>
        </Container>
    </Container>
</Instance>
```

---

## Template 7: LaunchBar Button Instance

Standard button instance for the bottom LaunchBar.

```xml
<Instance Name="MyLaunchBarButton">
    <Button ID="Button" Anchor="L,C" Size="49,49"
            Texture="LaunchBar_Hook_GovernmentButton" Style="ButtonNormalText"
            StateOffsetIncrement="0,49" ToolTip="LOC_MY_BUTTON_TOOLTIP">
        <Image ID="Icon" Size="35,35" Anchor="C,C" Offset="0,0"
               Texture="ICON_MY_BUTTON"/>
        <Label ID="AlertIndicator" String="[ICON_New]" Anchor="R,T" AnchorSide="O,O"
               Offset="-18,-18" ToolTip="LOC_NEW" Hidden="1"/>
    </Button>
</Instance>

<!-- Pin (the small dot indicator on the right of the button) -->
<Instance Name="MyLaunchBarPin">
    <Image ID="Pin" Anchor="L,C" Offset="0,-2" Size="7,7"
           Texture="LaunchBar_TrackPip" Color="255,255,255,200"/>
</Instance>
```

**Usage in Lua:**
```lua
function AttachControls()
    local buttonStack = ContextPtr:LookUpControl("/InGame/LaunchBar/ButtonStack");
    if not buttonStack then return; end

    local instance = {};
    ContextPtr:BuildInstanceForControl("MyLaunchBarButton", instance, buttonStack);
    instance.Button:RegisterCallback(Mouse.eLClick, OnMyButtonClick);

    ContextPtr:BuildInstanceForControl("MyLaunchBarPin", {}, buttonStack);

    -- Resize LaunchBar
    buttonStack:CalculateSize();
    local backing = ContextPtr:LookUpControl("/InGame/LaunchBar/LaunchBacking");
    if backing then backing:SetSizeX(buttonStack:GetSizeX() + 116); end
    local backingTile = ContextPtr:LookUpControl("/InGame/LaunchBar/LaunchBackingTile");
    if backingTile then backingTile:SetSizeX(buttonStack:GetSizeX() - 20); end
    LuaEvents.LaunchBar_Resize(buttonStack:GetSizeX());
end
```

### Refresh / Toggle Without Rebuilding

按钮已附加后，刷新内容或切换显隐时**不要 `DestroyChild` 再重建**（会导致 LaunchBar 抖动）。用 `SetHide` 切换 + 内容刷新：

```lua
-- 首次附加（仅调用一次）
function AttachControls()
    -- ... BuildInstanceForControl + Resize 同上 ...
end

-- 后续刷新：切换显隐 + 更新内容
function RefreshButton()
    if instance.Button then
        instance.Button:SetHide(shouldHide)
    end
    UpdateTooltip()
    UpdateAlertIndicator()
end
```

| ❌ 错误 | ✅ 正确 |
|--------|--------|
| 遍历字节点 `DestroyChild` 后重新 `BuildInstanceForControl` | 一次构建，后续 `SetHide(false/true)` 切换 |
| 每次刷新都 `CalculateSize` + `LuaEvents.LaunchBar_Resize` | 仅在首次 `AttachControls` 执行一次 |

---

## Size Syntax Reference

| Syntax | Meaning |
|--------|---------|
| `parent` | Same as parent's dimension |
| `parent-16` | Parent minus 16px |
| `auto` | Fit to children content |
| `400` | Fixed 400px |
| `400,300` | Width 400px, Height 300px |

## Anchor Syntax Reference

Format: `Horizontal,Vertical`

| Horizontal | Vertical | Example |
|-----------|----------|---------|
| `L` (Left) | `T` (Top) | `L,T` = top-left |
| `C` (Center) | `C` (Center) | `C,C` = center |
| `R` (Right) | `B` (Bottom) | `R,B` = bottom-right |

### Offset 方向：正值恒指向容器内部（锚点镜像）

**Offset 的正负不做全局坐标系，而是按锚点反向翻转**——正值永远把控件往容器内部推，负值往外部推：

| 锚点 | X 正值方向 | Y 正值方向 |
|------|-----------|-----------|
| `L` | 向右（内部） | — |
| `R` | **向左（内部）** | — |
| `T` | — | 向下（内部） |
| `B` | — | **向上（内部）** |
| `C` | 向右（全局正向） | 向下（全局正向） |

- `R,B` + `Offset="17,8"` → 从右下角向左 17、向上 8（vanilla `WorldBuilderMenu.xml:14` WBAConfirmButton）
- `L,B` + `Offset="20,8"` → 从左下角向右 20、向上 8（vanilla `WorldBuilderMenu.xml:15` WBACancelButton）
- `C,B` + `Offset="0,15"` → 底部居中，向上 15（vanilla `BoostUnlockedPopup.xml` 协议按钮）
- `R,B` + `Offset="-80,33"` → 向左上镜像对称的反向：**向右 80 推出容器右缘，贴屏幕边缘**（错误）

⚠️ 曾出 bug：确认/取消按钮一个用 `L,B`、一个用 `R,B` 却都写正值，右上角的按钮就跑到屏幕外。**写 `R,B`/`B,T`/`L,B` 等角落锚点前，务必按上表反推符号。** 不确定时优先用 `C,*` 锚点 + 正值（无镜像歧义）。

## Common Texture Names

| Texture | Use |
|---------|-----|
| `Controls_GenericPanel` | Standard panel background (9-slice) |
| `Controls_GenericPanel_Blank` | Flat panel background (9-slice) |
| `Controls_Close` | Close button (X) |
| `LaunchBar_Hook_GovernmentButton` | LaunchBar button style |
| `LaunchBar_TrackPip` | LaunchBar pin dot |

---

## 官方样式参考（Civ6_Styles.xml 提炼）

> 本节为官方文件提炼的**补充参考**，不替代上文模板；官方样式表先于 mod 加载，其中定义的样式/纹理可直接 `Style="..."` / `Texture="..."` 引用。
>
> 权威自验来源：
> - `Base\Assets\UI\Civ6_Styles.xml`（主样式表，2452 行，2 空格缩进）
> - `Base\Assets\UI\Fonts\Civ6_FontStyles_EFIGS.xml`（字体样式定义）
> - 本机路径：`F:\steam\steamapps\common\Sid Meier's Civilization VI\Base\Assets\UI\`

### 官方字体样式速查（免自建字体）

| 族 | 样式名 | 说明 |
|---|---|---|
| 正文（MyriadPro-Semibold） | `FontNormal8~50`：8/9/10/11/12/13/14/15/16/17/18/20/22/24/26/28/30/40/50 | 字号随名字 |
| 正文粗体 | `FontNormalBold12` / `14` / `16` | |
| 正文常规字重（MyriadPro-Regular） | `FontNormalMedium12/13/14/16/17/18/20` | |
| 衬线（MinionPro） | `FontFlair10~50`：10/11/12/14/16/18/20/22/24/26/28/30/40/50 | 标题花体 |
| 衬线粗体 | `FontBoldFlair18/21/26/60` | |
| 衬线斜体 | `FontItalicFlair18/21/22/26/60` | |
| 等宽 | `FontMono14` | |

**常用组合样式**（官方已配好颜色/描边/大写，直接 `Style=` 引用）：

| 样式 | 构成 | 用途 |
|---|---|---|
| `WindowHeader` | FontFlair22 + SmallCaps26 + glow | 弹窗标题 |
| `ShellHeader` | FontFlair24 + SmallCaps28 + glow | 页头大标题 |
| `HeaderFont` | FontBoldFlair18 + stroke + 居中 | 区块标题 |
| `BodyFont` / `BodyFont16` | FontNormal20 / 16 + shadow | 深底正文 |
| `ButtonNormalText` | FontNormalBold14 + stroke | 按钮文字 |
| `ButtonText14/16/18/20` | FontNormal14/16/18/20 + glow | 浅底按钮文字 |
| `ConfirmButtonText16/18` | FontNormal16/18 + glow（ConfirmButton 色） | 确认按钮文字 |
| `RedButtonText14/18` | FontNormal14/18 + glow（DenyButton 色） | 红色按钮文字 |
| `PanelText` | FontNormal20 + stroke | 面板正文 |
| `TabFont` / `TabSelectedFont` | FontNormal14 glow / shadow | 选项卡文字 |
| `PanelHeaderText` | FontFlair14 + SmallCaps18 | 面板小节标题 |
| `EventPopupTitle` | FontFlair20 + SmallCaps26 + 居中 | 事件弹窗标题 |
| `HeaderTextParchment16` | FontFlair14 + SmallCaps18（羊皮纸色） | 浅底标题 |

### 9-slice 与按钮状态属性（官方完整用法）

| 属性 | 作用 | 官方示例 |
|---|---|---|
| `SliceCorner="x,y"` | 四角切角（不拉伸区） | `55,55`（WindowFrame） |
| `SliceTextureSize="w,h"` | 单帧贴图尺寸 | `118,118`（WindowFrame） |
| `SliceSize="x,y"` | 可拉伸区（边/中心） | `1,1`（TTGrid）；`2,3`（WCScrollBar） |
| `SliceStart="x,y"` | 贴图帧起点偏移（同图取高亮帧） | `0,41`（Grid9MainButtonHighlight） |
| `StateOffsetIncrement="0,h"` | 多状态贴图垂直步进（normal→over→down→disabled） | `0,24`（ButtonControl） |
| `States="n"` | 状态帧数 | `2`（ScrollUpButton） |
| `NoStateChange="1"` | 忽略 hover/按下状态 | `1`（CityPanelIgnoreYieldButton） |
| `MinSize="w,h"` | 最小尺寸 | `80,41`（Grid9MainButton） |
| `InnerPadding="x,y"` | 内容内边距 | `16,16`（WindowFrameHUD） |
| `InnerOffset="x,y"` | 内容相对偏移 | `7,7`（WindowFrameHUD） |
| `TextureOffset="x,y"` | 贴图取样偏移 | `43,39`（DropShadowRightEdge） |

> `StateOffsetIncrement` 垂直步进值 = 按钮单帧高度（如 24/26/41/44/49）；mod 用多状态贴图时按纹理实际帧高取值。

### 官方按钮"悬停高亮"标准结构

官方按钮通用模式：**文字样式 + GridData（9-slice 底图）+ AlphaAnim(ShowOnMouseOut) 包裹高亮 Grid（SliceStart 取高亮帧）**。mod 做官观按钮抄此结构：

```xml
<ButtonMainSmall Style="ButtonText14">
    <GridData Style="Grid9ButtonMainSmall" />
    <AlphaAnim ShowOnMouseOut="1" Anchor="L,T" Size="parent,parent"
               Pause="0" Cycle="Once" Speed="2" AlphaStart="1" AlphaEnd="0">
        <Grid Size="parent,parent" Offset="0,0" Padding="0,0" Style="Grid9ButtonMainSmallHL" />
    </AlphaAnim>
</ButtonMainSmall>
```

配套底图样式（普通帧 + 高亮帧）：

```xml
<Grid9ButtonMainSmall Texture="Controls_ButtonSmall"
                      SliceTextureSize="51,26"
                      SliceCorner="25,13"
                      StateOffsetIncrement="0,26" />
<Grid9ButtonMainSmallHL Texture="Controls_ButtonSmall"
                        SliceTextureSize="51,26"
                        SliceCorner="25,13"
                        SliceStart="0,26"
                        StateOffsetIncrement="0,0" />
```

同结构官方范例：`ShellButton`、`ShellButtonOrnate`、`ButtonConfirm`、`ButtonRed`、`TabButton`、`ButtonBig`（`Shell_ButtonControl` / `Controls_Confirm` / `Controls_RedButton` / `Controls_Tab` / `Controls_ButtonBig`）。

### ScrollPanel 官方完整配方 + AnchorSide

```xml
<ScrollPanel Vertical="1" AutoScrollBar="1" Size="parent,parent">
    <ScrollBar Style="ScrollVerticalBar" Anchor="R,C" AnchorSide="O,I" />
    <UpButton   Style="ScrollUpButton"   Anchor="R,T" AnchorSide="O,I" />
    <DownButton Style="ScrollDownButton" Anchor="R,B" AnchorSide="O,I" />
</ScrollPanel>
```

`AnchorSide="水平,垂直"`：控件相对父容器锚点边的位置，`O`=外侧（Outer），`I`=内侧（Inner）。官方用例：滚动条 `R,C` + `O,I`（右缘外侧居中）；`LogoContainer` `C,T` + `I,O`；`ScrollPanelHighContrast` 的 ScrollBar `I,I`；`GenericPullDown` GridData `C,B` + `I,O`。贴边控件（滚动条/渐变条/指示器）通常需要它，skill 原模板未提及。

官方滚动条/按钮样式：`ScrollVerticalBar`/`ScrollHorizontalBar`（`Controls_ScrollbarV/H`，11,14 / 12,8）、`ScrollVerticalBarAlt`、`Slider_Blue`（`Controls_ScrollbarBlue` 10,14）、`Slider_Vert`（`slider_vert` 18,18）、`ScrollUpButton`/`ScrollDownButton`（17,17，`States="2"`，`StateOffsetIncrement="0,17"`）。样式表还预置了现成 ScrollPanel 组合样式：`ScrollPanelWithLeftBar`、`ScrollPanelWithRightBar`、`ScrollPanelHighContrast`。

### 官方现成控件样式速查（Style= 直接引用）

**面板 / 容器**

| 样式 | 纹理 + 关键参数 | 用途 |
|---|---|---|
| `WindowFrame` | `Controls_Window`，SliceCorner=55,55，SliceTextureSize=118,118，MinSize=118,118 | 主弹窗 |
| `WindowFrameHUD` | `Controls_WindowLight`，SliceCorner=17,15，InnerPadding=16,16 | HUD 内弹窗 |
| `SubContainer2` | `Controls_SubContainer2`，SliceCorner=17,17，InnerPadding=16,14 | 通用子面板 |
| `SubContainer3/4/5` | `Controls_SubContainer3/4/5` | 小面板/图标框 |
| `SubContainerSmall` | `Controls_ItemContainer`，SliceCorner=8,8，16,16 | 列表条目框 |
| `BlackContainer` | `ActionPanel_Flyout`，SliceCorner=23,17 | 深色浮层 |
| `BlackContainerRect` | `Controls_ContainerBlack`，SliceCorner=3,11，InnerPadding=6,22 | 深色矩形面板 |
| `BGBlock` | Size=parent,parent，Anchor=C,C，Color=0,0,0,200，ConsumeMouse=1 | 全屏黑遮罩（一键样式） |
| `DropShadow2/3/4` | `Controls_DropShadow2/3/4` | 阴影层 |
| `ColumnHeader` | `Controls_ColumnHeader`，SliceCorner=14,14，28,28 | 列标题 |
| `HeaderBannerLeft/Right` | `Controls_HeaderBanner`，SliceCorner=120,40，240,59 | 页头横幅 |

**按钮**

| 样式 | 纹理 + 关键参数 | 用途 |
|---|---|---|
| `ButtonControl` | `Controls_ButtonControl`，SliceCorner=12,6，24,24，StateOffsetIncrement=0,24 | 标准按钮 |
| `ButtonControlBrown` / `ButtonControlTan` | `Controls_ButtonControl_Brown/Tan` | 棕色/米色按钮 |
| `ShellButton` | `Shell_ButtonControl`，SliceCorner=5,5，22,22 | Shell 按钮 |
| `ShellButtonOrnate` | `Shell_ButtonOrnate`，SliceCorner=23,4，133,36 | 花边按钮 |
| `MainButton` | `Controls_Button`，SliceCorner=41,20，80,41，MinSize=80,41 | 主按钮 |
| `ButtonConfirm` | `Controls_Confirm`，SliceCorner=34,20，80,41 | 确认按钮 |
| `ButtonRed` / `ButtonRedSmall` | `Controls_RedButton`，SliceCorner=35,20 | 红色按钮 |
| `TabButton` / `TabButtonSelected` | `Controls_Tab`，SliceCorner=21,16，StateOffsetIncrement=0,34 | 选项卡 |
| `ButtonLightweightSmall` | `Controls_ButtonLightweightSmall`，SliceCorner=13,9，27,19 | 轻量小按钮 |
| `RoundedButton` | `Controls_ButtonControl`，SliceCorner=10,10，24,24 | 圆角按钮 |
| `ArrowButtonLeft/Right` | `Controls_ArrowButtonLeft/Right`，19,23 | 箭头按钮 |

**关闭按钮（官方 4 档尺寸，非 9-slice，直接固定尺寸）**

| 样式 | 尺寸 | StateOffsetIncrement |
|---|---|---|
| `CloseButtonSmall` | 34,34 | 0,34 |
| `CloseButtonLarge` | 44,44 | 0,44 |
| `CloseButtonAlt` | 32,32 | 0,32 |
| `ClosePanelButtonSmall` | 26,26 | 0,26 |

**其他**

| 样式 | 纹理 + 参数 | 用途 |
|---|---|---|
| `TTGrid` + `TTText` | `Controls_Tooltip`，SliceCorner=16,10，33,32 | 标准 tooltip 外观 |
| `EnhancedToolTip` | `Controls_EnhancedToolTip`，SliceCorner=28,22，54,54 | 增强 tooltip |
| `EditTextArea` | `Controls_TextArea`，SliceCorner=11,15，22,22 | 文本域 |
| `EditTextButton` | `Controls_TextEntry`，SliceCorner=30,13，44,26，StateOffsetIncrement=0,26 | 文本输入框 |
| `CheckButton` | `Controls_CheckButton2`，41,26，CheckTextureOffset=0,104 | 开关按钮 |
| `MainCheckBox` | `Controls_Checkbox`，17,17，CheckTextureOffset=0,17 | 复选框 |
| `Divider2/3/4/6` | `Controls_Div2/3/4/6` | 分割线（54,8 / 35,8 / 10,10 / 143,2） |
| `DivHeader` | `Controls_DivHeader`，272,24，AutoSize=V | 章节头 |
| `Glow` | `Controls_Glow2`，SliceCorner=25,25，50,50 | 发光层 |

### 官方弹窗模板与 ID 约定

官方弹窗样式可配合现成 `PopupDialog.lua`（ID 约定：`PopupDialog` / `PopupTitle` / `PopupStack`），无需自写逻辑。官方 `PopupDialogBox` 的淡入+滑入结构：

```xml
<PopupDialogBox ID="PopupDialog" Size="parent,parent" ConsumeMouse="1" Color="0,0,0,150" Hidden="1">
    <AlphaAnim ID="PopupAlphaIn" Size="parent,parent" AlphaBegin="0" AlphaEnd="1" Speed="3" Function="Root" Cycle="Once">
        <SlideAnim ID="PopupSlideIn" Size="parent,parent" Start="0,-20" End="0,0" Speed="3" Function="Root" Cycle="Once">
            <Grid Size="auto,auto" Anchor="C,C" Style="DropShadow2" AutoSizePadding="25,25" ConsumeMouse="1">
                <Grid Size="500,auto" Anchor="C,C" Style="WindowFrameTitle" AutoSizePadding="0,10">
                    <Label ID="PopupTitle" Style="WindowHeader" Anchor="C,C" />
                    <Stack ID="PopupStack" Size="parent,100" Anchor="C,T" Offset="0,50" StackGrowth="Bottom" StackPadding="30" />
                </Grid>
            </Grid>
        </SlideAnim>
    </AlphaAnim>
</PopupDialogBox>
```

其他官方弹窗约定：`ModalScreen`（ID：`ModalScreenTitle` / `ModalScreenClose`，`CloseButtonLarge`）、`NotificationPopup`（ID：`PopupTitle` / `PopupCloseButton`，`CloseButtonSmall`）。

### 动画元素模板

| 控件 | 关键属性 | 说明 |
|---|---|---|
| `AlphaAnim` | `AlphaBegin` `AlphaEnd` `Speed` `Function="Root"` `Cycle="Once"/"Bounce"` `Delay` `ShowOnMouseOut/ShowOnMouseOver` | 淡入淡出 |
| `SlideAnim` | `Start="x,y"` `End="x,y"` `Speed` `Function="OutSine"` `Cycle` `Stopped="1"` | 平移滑入 |
| `FlipAnim` | `FrameCount` `Columns` `Speed` `Stopped="1"` | 序列帧动画 |
| `Meter` | `Percent` `Speed` `Follow="1"` | 进度环/条 |

官方范例：`RundownAnimBG`（右侧滑入面板，`Start="-514,27" End="-1,27"`）、`CurrentCivicProgBar`（`<Meter Anchor="C,C" Size="56,56" Percent=".4" Texture="CivicPanel_Meter" Speed="1.0" Follow="1"/>`）。

### Stack 官方用法补充

官方 Stack 间距属性为 `StackPadding`（数值，官方 85 文件使用）；生长方向取值：`Right`（水平向右，最常见）、`Down` / `Bottom`（垂直向下）、`Left`、`Top` / `Up`。PullDown 的 `StackData` 惯用 `StackGrowth="Bottom" Anchor="C,T"`。官方范例：`<Stack StackPadding="8" StackGrowth="Down" Anchor="L,C">`。
