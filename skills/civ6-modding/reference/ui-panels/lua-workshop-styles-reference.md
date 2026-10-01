# Civ6_Styles + ColorAtlas — 样式/颜色/字体参考

> **来源**：`Civ6_Styles.xml`(2452行) + `Civ6_ColorAtlas.xml`(220行) + `Icons/FontIcons.xml`(316行)
> **地位**：所有控件的视觉基准——定义 100+ 种复合控件皮肤、60+ 种颜色/ColorSet、7 种字体族。

---

## 字体系统

### 字体族

| 族名 | 大小 | 说明 |
|------|------|------|
| `FontNormal` | 10/12/14/16/18/20/22 | 系统无衬线 |
| `FontNormalMedium` | 12/14/16/17 | 中粗 |
| `FontNormalBold` | 14/16 | 粗体 |
| `FontFlair` | 11/14/16/18/20/22/24/26/28/30/40 | 衬线装饰字 |
| `FontBoldFlair` | 18/21 | 粗体衬线 |
| `FontItalicFlair` | 22 | 斜体衬线 |

### FontStyle（字体效果）

| 值 | 效果 | Color1 作用 | 使用频率 |
|----|------|------------|----------|
| `shadow` | 右下投影 | 阴影颜色 | 标题、按钮文字 |
| `glow` | 向外辉光 | 辉光颜色（Color2可选第二层） | 按钮文字、UI文字 |
| `stroke` | 边缘描边 | 描边颜色 | 正文文本 |

---

## Color 系统

### 命名颜色速查（常用60+颜色）

| 颜色名 | RGBA | 用途 |
|--------|------|------|
| `Gold` | 206,194,85,255 | 金币文字 |
| `Science` | 68,179,234,255 | 科技文字 |
| `Culture` | 175,89,245,255 | 文化文字 |
| `Food` | 130,178,44,255 | 食物文字 |
| `Production` | 211,143,61,255 | 生产力文字 |
| `Faith` | 182,193,227,255 | 信仰文字 |
| `Military` | 188,22,22,255 | 军事文字 |
| `Tourism` | 181,116,102,255 | 旅游文字 |
| `Beige` | 255,255,200,255 | 浅色 |
| `Gray` / `GrayMedium` | 164,164,164 / 96,100,102 | 灰色 |
| `Red` / `Green` / `Blue` | 191,55,60 / 0,200,0 / 0,0,255 | 基础色 |
| `COLOR_FLOAT_CULTURE` | 254,42,237,255 | 文化浮动文字 |
| `COLOR_FLOAT_FOOD` | 85,155,6,255 | 食物浮动文字 |
| `COLOR_FLOAT_GOLD` | 229,213,66,255 | 金币浮动文字 |
| `COLOR_FLOAT_SCIENCE` | 95,145,255,255 | 科技浮动文字 |
| `COLOR_FLOAT_PRODUCTION` | 145,51,0,255 | 生产力浮动文字 |

### ColorSet（前景+效果色双色）

| ColorSet | Color0 | Color1 | 用途 |
|----------|--------|--------|------|
| `BodyTextCool` | 194,194,204 | 0,0,0,50 | 标准正文（冷灰） |
| `BodyTextBlue` | 6,53,92,255 | 135,185,201,150 | 深蓝正文 |
| `ConfirmButton` | 206,229,238,255 | 83,198,247,100 | 确认按钮文字 |
| `DenyButton` | 206,205,206,255 | 168,34,34,100 | 取消按钮文字 |
| `ShellHeader` | 158,171,179,255 | 10,137,173,200 | Shell 标题 |
| `ShellOptionText` | 22,157,152,255 | 0,0,0,50 | Shell 选项文字 |
| `TopBarLabelCS` | 179,175,179,255 | 0,0,0,155 | 顶栏标签 |
| `TopBarValueCS` | 170,169,168,255 | 0,0,0,155 | 顶栏数值 |
| `StatGoodCS` | 80,255,90,240 | 0,0,0,200 | 正面统计 |
| `StatBadCS` | 255,40,50,240 | 0,0,0,200 | 负面统计 |
| `ResFoodLabelCS` | 171,224,47,255 | 0,0,0,100 | 食物产出 |
| `ResProductionLabelCS` | 130,83,43,255 | 0,0,0,200 | 生产力产出 |
| `ResGoldLabelCS` | 229,213,66,255 | 0,0,0,100 | 金币产出 |
| `ResScienceLabelCS` | 10,137,173,255 | 0,0,0,100 | 科技产出 |
| `ResCultureLabelCS` | 190,89,189,255 | 0,0,0,100 | 文化产出 |
| `ResFaithLabelCS` | 100,128,160,255 | 0,0,0,100 | 信仰产出 |
| `ParchmentBrown` | 74,67,60,255 | 74,67,60,100 | 羊皮纸棕色 |
| `OperationChance_Green` | 40,162,78,255 | 0,0,0,100 | 间谍成功率(高) |
| `OperationChance_Red` | 200,62,52,255 | 0,0,0,100 | 间谍成功率(低) |

---

## 复合控件皮肤速查

### 按钮类

| Style 名 | 纹理 | 纹理尺寸 | 场景 |
|----------|------|----------|------|
| `ButtonConfirm` | Controls_Confirm | 80×41 | 确认按钮（蓝） |
| `MainButton` | Controls_Button | 80×41 | 主菜单大按钮 |
| `ButtonRed` | Controls_RedButton | 80×41 | 取消/危险按钮 |
| `ButtonControl` | Controls_ButtonControl | 24×24 缩放 | 通用控件按钮 |
| `TabButton` | Controls_Tab | 自适应 | 标签页按钮 |
| `ProductionButton` | ProductionPanel_ChooserButton | 102×48 | 生产面板 |
| `ButtonExpand` | Controls_ButtonExpand | 57×41 | 展开/折叠 |
| `ButtonLightWeight` | Controls_ButtonLightweight | 32×32 | 轻量按钮 |
| `RoundedButton` | Controls_ButtonControl | 24×24 缩放 | 圆角通用 |
| `ShellButton` | Shell_ButtonControl | 22×22 | Shell 风格 |
| `ShellButtonOrnate` | Shell_ButtonOrnate | 133×36 | 华丽装饰 |
| `PauseMenuButton` | Shell_ButtonOrnateFlat | 133×36 | 暂停菜单 |
| `ShellTab` | Shell_Tab | 50×32 | Shell 标签 |
| `CloseButtonLarge` | Controls_CloseLarge | 44×44 | X 关闭按钮 |

### 滚动条类

| Style 名 | 组合 |
|----------|------|
| `ScrollPanelWithRightBar` | ScrollPanel + ScrollVerticalBar(右侧) + 上下按钮 |
| `ScrollPanelWithLeftBar` | ScrollPanel + ScrollVerticalBar(左侧) + 上下按钮 |
| `ScrollPanelHighContrast` | ScrollPanel + 高对比度滚动条 |
| `WorldRankingsScrollPanel` | 排名面板专用 |
| `ScrollVerticalBar` | ScrollVerticalBacking(11×14) + ScrollThumb(5×12) |
| `ScrollVerticalBarAlt` | 变体 (46,54,60) |
| `ScrollThumb` | Controls_ScrollHandle, 5×12 |

### 滑块类

| Style 名 | 方向 | 轨道尺寸 | 场景 |
|----------|------|----------|------|
| `SliderControl` | 水平 | 220×13 | 设置页通用 |
| `Slider_Vert` | 垂直 | 18×18 | 滚动条（旧） |
| `Slider_Horiz` | 水平 | 12×8 | 水平滚动 |
| `Slider_Blue` | 垂直 | 10×14 | 蓝色主题 |
| `Slider_Light` | 垂直 | 11×14 | 亮色 |

### PullDown 类

| Style 名 | 尺寸 | 场景 |
|----------|------|------|
| `PullDownBlue` | 194×24 | 通用下拉 |
| `GenericPullDown` | 自适应 | 通用自适应 |
| `PlayerSelectPullDown` | 325×50 | 选领袖(带头像) |
| `ChatPullDown` | 自适应 | 聊天面板 |
| `SmallPullDown` | 194×26 | 小型下拉 |

### CheckBox 类

| Style 名 | 框尺寸 | 场景 |
|----------|--------|------|
| `MainCheckBox` | 17×17 | 通用复选框 |
| `CheckBoxControl` | 自适应(九宫格) | 8态复选框 |
| `CheckButton` | 41×26 | 大号开关按钮 |
| `CheckBoxExpand` | 41×26/22×22 | 展开/折叠箭头 |
| `CheckBoxModsControl` | 22×22 | Mod 管理界面 |
| `CheckBoxPopupControl` | 22×22 | 弹窗内复选框 |

### 容器/框架类

| Style 名 | 说明 |
|----------|------|
| `WindowFrameHUD` | 轻量窗口 (34×34) |
| `WindowFrameTitle` | 带标题的窗口 (118×118) |
| `DropShadow` / `DropShadow2/3/4` | 4级投影 (200→25) |
| `BlackContainer` | 黑色面板背景 (46×43) |
| `BlackContainerRect` | 黑色矩形面板 (37×43) |
| `SubContainer` | 子容器 (70×70) |
| `SubContainerSmall` | 子容器小 (16×16) |
| `SubContainerSmall2` | 子容器暗色小 (16×16) |
| `DecoGrid` / `DecoFrame` | 装饰网格/框架 |

---

## 文本标记

| 标记 | 用法 |
|------|------|
| `[ICON_Name]` | 内嵌图标（如 `[ICON_ScienceLarge]`） |
| `[COLOR:ColorSetName]` | 颜色套用（如 `[COLOR:ResFoodLabelCS]`） |
| `[COLOR:R,G,B,A]` | 字面色值 |
| `[ENDCOLOR]` | 关闭颜色 |
| `[NEWLINE]` | 换行 |
