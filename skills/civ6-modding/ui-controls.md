# ForgeUI 控件详细参考

基于 Civ6Docs.html 整理的完整 ForgeUI 控件参考文档。

---

## 控件类型总览

### Layout Controls (布局控件)

| 控件 | 说明 |
|------|------|
| **Container** | 最基础的控件，所有其他控件都继承自它。用于组合其他控件 |
| **Group** | 类似 Container，但支持裁剪(Clipping)，子控件超出区域会被隐藏 |
| **TabControl** | 允许通过点击标签在不同面板之间切换 |
| **ScrollPanel** | 允许子控件通过滚动条移动，并裁剪超出范围的子控件 |
| **Stack** | 按顺序排列子控件的容器，支持线性或2D网格布局 |
| **WorldAnchor** | 绑定到3D世界中位置的控件 |

### Context Controls (上下文控件)

| 控件 | 说明 |
|------|------|
| **Context** | 包含 XML 文件中定义的控件的容器 |
| **LuaContext** | 由 Lua 程序支持的 Context |

### Animation Controls (动画控件)

| 控件 | 说明 |
|------|------|
| **ScrollAnim** | 动画滚动纹理 |
| **FlipAnim** | 翻书动画控件 |
| **SlideAnim** | 允许子控件在屏幕上滑动的容器 |
| **AlphaAnim** | 允许动画化子控件透明度的容器 |
| **SpinAnim** | 旋转动画控件 |

### Visual Controls (视觉控件)

| 控件 | 说明 |
|------|------|
| **Line** | 在两点之间绘制线段 |
| **Box / ColorBox** | 用单一颜色填充的矩形控件 |
| **Bar** | 使用纯色的进度条 |
| **TextureBar** | 使用纹理的进度条 |
| **Meter** | 旋转圆形进度条 |
| **Image** | 包含任意纹理的控件 |
| **Grid** | 9切片图像，纹理映射到3x3网格 |
| **Label** | 包含任意文本的控件 |
| **Movie** | 可播放视频的控件(Bink编码) |
| **Render** | 绘制游戏生成纹理的控件 |
| **Graph** | 折线图，可显示任意数据 |

### Interactive Controls (交互控件)

| 控件 | 说明 |
|------|------|
| **Button** | 带纯色背景的简单按钮 |
| **BoxButton** | 带纯色背景的按钮 |
| **TextButton** | 带文本的按钮 |
| **GridButton** | 带9网格纹理背景的按钮 |
| **EditBox** | 允许用户直接编辑文本的文本框 |
| **ListBox** | 包含条目列表的控件 |
| **MultiSelectListBox** | 允许选择任意数量选项的控件 |
| **CheckBox** | 只有2种状态的按钮 |
| **RadioButton** | 只有2种状态的按钮，同一组中只能有一个激活 |
| **Slider** | 允许用户用滑块选择值的控件 |
| **PullDown** | 可包含多个选项的下拉框 |
| **SimplePullDown** | 简化版 PullDown |
| **Drag** | 可用鼠标拖动的控件 |

### Miscellaneous (其他)

| 控件 | 说明 |
|------|------|
| **Tween** | 补间动画 |
| **Include** | 将 XML 文件内容包含到当前上下文 |
| **MakeInstance** | 创建对象实例 |
| **ToolTipType** | 自定义工具提示类型 |
| **Tutorial** | 教程系统控件 |

---

## 详细控件说明

### Container

最基础的控件，所有其他控件都继承自它。

**用途：**
- 组合多个控件以便统一操作（显示/隐藏）
- 作为布局容器

**XML 示例：**
```xml
<Container ID="MyContainer" Size="parent,parent" Anchor="C,C" Hidden="1">
    <Label ID="Title" String="Hello" />
    <Button ID="OK" String="OK" />
</Container>
```

---

### Group

类似 Container，但支持裁剪。子控件超出 Group 区域的部分会被隐藏。

**用途：**
- 实现滑入/滑出动画效果
- 裁剪超出区域的内容

**XML 示例：**
```xml
<Group ID="ClipArea" Size="200,100">
    <!-- 子控件超出200x100区域的部分会被裁剪 -->
    <Button ID="SlidingContent" Offset="-200,0" Size="100,50" />
</Group>
```

---

### ScrollPanel

带有滚动条的容器，允许子控件在较小的视口中滚动显示。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `AutoScrollBar` | 当内部大小等于视口大小时自动隐藏滚动条 |
| `HideScrollBar` | 永不显示滚动条 |
| `Vertical` | 设置为 true 以垂直滚动（默认是水平） |
| `FullClip` | 在两个维度上都裁剪（默认只在滚动方向裁剪） |

**子控件：**
- `<UpButton>` - 向上滚动按钮
- `<DownButton>` - 向下滚动按钮
- `<ScrollBar>` - 滚动条滑块

**Lua 方法：**

```lua
ctrl:CalculateSize()                    -- 计算大小
ctrl:GetScrollValue() -> float          -- 获取滚动位置(0.0-1.0)
ctrl:SetScrollValue(float)              -- 设置滚动位置
ctrl:RegisterScrollCallback(func)       -- 注册滚动回调
```

**XML 示例：**
```xml
<ScrollPanel ID="ContentScroll" Size="parent-40,parent-80" Vertical="1" AutoScrollBar="1">
    <Stack ID="ItemStack" StackGrowth="Down" />
</ScrollPanel>
```

---

### Stack

按顺序排列子控件的容器，支持线性或2D网格布局。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `StackGrowth` | 堆叠方向：`"Down"` `"Up"` `"Left"` `"Right"` |
| `StackPadding` | 子元素之间的间距(像素) |
| `WrapWidth` | 超过此宽度后开始换行 |
| `WrapGrowth` | 换行后的堆叠方向 |

**Lua 方法：**

```lua
ctrl:CalculateSize()          -- 计算大小（子控件改变后必须调用）
ctrl:ReprocessAnchoring()     -- 重新处理锚定
```

**XML 示例：**
```xml
<Stack ID="ButtonStack" StackGrowth="Down" StackPadding="5" Anchor="C,T">
    <Button String="Button 1" Size="200,40" />
    <Button String="Button 2" Size="200,40" />
    <Button String="Button 3" Size="200,40" />
</Stack>
```

**2D 网格布局：**
```xml
<Stack StackGrowth="Right" WrapWidth="600" WrapGrowth="Down" StackPadding="10">
    <!-- 超过600px后自动换到下一行 -->
</Stack>
```

---

### Label

显示文本的控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `String` | 显示的文本内容 |
| `Font` | 字体名称 |
| `FontSize` | 字体大小 |
| `FontStyle` | 字体样式：`"Shadow"` `"Glow"` `"Stroke"` |
| `Align` | 对齐方式：`"left"` `"center"` `"right"` |
| `WrapWidth` | 自动换行宽度 |
| `TruncateWidth` | 截断宽度 |
| `Rotation` | 旋转角度(度) |
| `Color` | 文本颜色 |
| `EffectColor` | 效果颜色(阴影、发光等) |
| `GradientColor` | 底部渐变颜色 |

**`Align` 说明：**

- 合法属性名是 `Align`，**不是** `Alignment`（原版 Base+DLC 全量实测：`Align=` 581 处、`Alignment=` 0 处）。写成 `Alignment` 会**静默失效**——不报错也不警告，只是不生效。
- **`Align` 只在控件有显式 `Size` 时才有视觉意义。** Label 尺寸默认自适应（盒子宽 = 文本实际宽），盒内没有多余空间可对齐，`Align` 自然看不出差别。原版 541 个含 `Align` 的 Label 中，496 个没有 `Size`（无效），仅 45 个同时有 `Size`（生效）。
- 文字看起来居中/靠右，通常是 `Anchor` 的功劳——`C,*` 把盒子摆到容器中间、`R,*` 摆到右侧，与 `Align` 无关。

| 想达到的效果 | 正确做法 |
|------|------|
| 文字在本行**内**居中 / 靠右 | 给控件显式 `Size="宽,高"`（宽 > 文本宽），**再**设 `Align` |
| 整块文本摆到容器**中间** | 用 `Anchor="C,*"`，无需 `Align` |

> 排查“对齐不生效”时**先查有没有 `Size`**。示例工程 曾踩坑：17 处 `Alignment`→`Align` 后实机毫无变化，一度误判属性无效，实为这些 Label 全都没有 `Size`；补上 `Size` 后 `Align="Left"` 立即靠左，才证实属性有效。
>
> 其余支持 `Align` 的控件（原版用量）：`CheckBox` 12、`TextButton` 4、`EditBox` 3、`Stack` 2，同样遵循“需有 `Size` 才生效”的规律。

**Lua 方法：**

```lua
ctrl:SetText("raw text")
ctrl:LocalizeAndSetText("LOC_KEY")
ctrl:SetFontSize(14)
ctrl:SetTruncateWidth(200)
ctrl:SetColor(r, g, b, a)
ctrl:SetColorByName("ColorName")
```

**XML 示例：**
```xml
<Label ID="Title" String="LOC_TITLE" Font="Font_22" Align="Center" Color="255,255,255,255" />
```

---

### Image

显示纹理的控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `TextureOffset` | 纹理偏移(像素) |
| `StretchMode` | 拉伸模式：`None` `Uniform` `Fill` `Tile` `TileX` `TileY` `UniformToFill` `Auto` |
| `FlipX` | 水平翻转 |
| `FlipY` | 垂直翻转 |
| `Rotate` | 旋转角度(度) |
| `Scale` | 统一缩放倍数 |
| `Icon` | 从图标管理器获取图标 |
| `IconSize` | 图标大小 |
| `MaskTexture` | Alpha 遮罩纹理 |
| `ColorSpace` | 颜色空间：`"RGB"` 或 `"Linear"` |
| `Sampler` | 采样器：`"Point"` 或 `"Linear"` |

**StretchMode 说明：**
- `None` - 按原始大小显示，必要时裁剪
- `Uniform` - 保持宽高比填充控件
- `Fill` - 拉伸纹理以适应控件大小
- `UniformToFill` - 保持宽高比填充，可能裁剪
- `Tile` - 重复纹理填充区域
- `Auto` - 根据纹理原始大小调整控件

**Lua 方法：**

```lua
ctrl:SetTexture(offsetX, offsetY, textureSheet)  -- 从图标图集设置
ctrl:SetIcon("ICON_NOTIFICATION_NEXT_TURN")       -- 便捷设置图标
```

**XML 示例：**
```xml
<Image ID="Icon" Size="48,48" Texture="MyTexture.dds" StretchMode="Fill" />
```

---

### Grid

9切片图像控件，允许纹理在拉伸时保持边缘和角落不变形。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `SliceStart` | 纹理中切片开始的坐标 |
| `SliceCorner` | 从纹理开始处开始9切片的偏移 |
| `SliceSize` | 中心矩形的大小 |
| `SliceTextureSize` | 纹理的完整大小 |
| `Color` | 顶点颜色 |
| `NoStateChange` | 状态改变时不偏移纹理 |
| `StateOffsetIncrement` | 状态改变时的纹理偏移量 |

**XML 示例：**
```xml
<Grid ID="PanelBG" Size="parent,parent" Texture="Controls_GenericPanel"
      SliceCorner="24,24" SliceTextureSize="48,48" />
```

---

### Button

简单的按钮控件，使用纹理贴图。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `TextureOffset` | 纹理偏移 |
| `States` | 状态数量(2,4,5,7,8) |
| `StateOffsetIncrement` | 状态改变时的纹理偏移 |
| `NoStateChange` | 状态改变时不偏移纹理 |
| `String` | 按钮文本 |
| `Color` | RGB 色调 |
| `ToolTip` | 工具提示文本 |
| `TextAnchor` | 文本锚定 |
| `TextOffset` | 文本偏移 |
| `DisabledCallbacks` | 禁用时触发输入回调 |

**按钮状态顺序：**
1. Normal (正常)
2. MouseOver (鼠标悬停)
3. ButtonDown (按下)
4. Disabled (禁用)
5. Selected (选中)
6. Selected Over (选中悬停)
7. Selected Down (选中按下)

**Lua 方法：**

```lua
ctrl:RegisterCallback(Mouse.eLClick, func)    -- 注册左键点击回调
ctrl:RegisterCallback(Mouse.eRClick, func)    -- 注册右键点击回调
ctrl:RegisterCallback(Mouse.eMClick, func)    -- 注册中键点击回调
ctrl:RegisterCallback(Mouse.eMouseEnter, func) -- 注册鼠标进入回调
ctrl:RegisterCallback(Mouse.eMouseExit, func)  -- 注册鼠标离开回调
ctrl:ClearCallback(state)                      -- 清除回调
ctrl:SetSelected(bool)                         -- 设置选中状态
ctrl:SetVoid1(value)                           -- 设置回调值1
ctrl:SetVoid2(value)                           -- 设置回调值2
ctrl:SetVoids(v1, v2)                          -- 设置回调值1和2
```

**XML 示例：**
```xml
<Button ID="MyButton" Size="100,40" Texture="ButtonTexture.dds"
        String="Click Me" ToolTip="LOC_TOOLTIP" />
```

---

### GridButton

使用 Grid 作为背景的按钮，大小可自适应。

**XML 属性：**
- 继承 Button 的所有属性
- `Font` - 字体名称
- `FontSize` - 字体大小
- `FontStyle` - 字体样式
- `TextColor` - 文本颜色
- `SelectedTextColor` - 选中时文本颜色
- `TextAnchor` - 文本锚定
- `TextOffset` - 文本偏移

**Lua 方法：**
- 继承 Button 的所有方法
- `ctrl:SetText(text)` - 设置文本
- `ctrl:GetText()` - 获取文本
- `ctrl:LocalizeAndSetText(key)` - 本地化设置文本
- `ctrl:SetSizeToText(w, h)` - 根据文本调整大小
- `ctrl:GetTextControl()` - 获取文本子控件

**XML 示例：**
```xml
<GridButton ID="CloseButton" Anchor="R,T" Offset="-20,15" Size="32,32"
            Texture="Controls_Close" SliceCorner="14,14" SliceTextureSize="28,28" />
```

---

### TextButton

纯文本按钮控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `String` | 按钮文本 |
| `Style` | 正常状态样式 |
| `MouseOverStyle` | 鼠标悬停样式 |
| `ButtonDownStyle` | 按下状态样式 |
| `DisabledStyle` | 禁用状态样式 |
| `Font` | 字体名称 |
| `FontSize` | 字体大小 |
| `FontStyle` | 字体样式 |

**XML 示例：**
```xml
<TextButton ID="MyTextButton" String="LOC_BUTTON_TEXT"
            Style="ButtonNormalText" Size="140,40" />
```

---

### CheckBox

复选框控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `ButtonSize` | 按钮大小（必需） |
| `ButtonTexture` | 按钮纹理（必需） |
| `CheckTexture` | 选中标记纹理 |
| `CheckSize` | 选中标记大小 |
| `CheckOffset` | 选中标记偏移 |
| `CheckColor` | 选中标记颜色 |
| `UnCheckTexture` | 未选中时的纹理 |
| `UnCheckColor` | 未选中时的颜色 |
| `IsChecked` | 初始选中状态 |
| `BoxOnLeft` | 复选框在文本左侧 |
| `String` | 标签文本 |
| `UseSelectedTextures` | 选中时使用选中状态纹理 |

**Lua 方法：**

```lua
ctrl:SetCheck(bool)     -- 设置选中状态
ctrl:IsChecked() -> bool -- 获取选中状态
```

**XML 示例：**
```xml
<CheckBox ID="MyCheck" String="LOC_OPTION" ButtonSize="24,24"
          ButtonTexture="CheckBox.dds" CheckTexture="CheckMark.dds"
          IsChecked="true" BoxOnLeft="true" />
```

---

### RadioButton

单选按钮控件，同一组中只能有一个被选中。

**XML 属性：**
- 继承 CheckBox 的所有属性
- `RadioGroup` - 单选按钮组名称（必需）

**XML 示例：**
```xml
<Stack StackGrowth="Down">
    <RadioButton ID="Option1" RadioGroup="MyGroup" String="Option 1"
                 ButtonSize="24,24" ButtonTexture="Radio.dds" CheckTexture="RadioCheck.dds" />
    <RadioButton ID="Option2" RadioGroup="MyGroup" String="Option 2"
                 ButtonSize="24,24" ButtonTexture="Radio.dds" CheckTexture="RadioCheck.dds" />
</Stack>
```

---

### EditBox

文本输入框控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Font` | 字体名称 |
| `FontSize` | 字体大小 |
| `FontStyle` | 字体样式 |
| `MaxLength` | 最大字符数 |
| `NumberInput` | 仅允许数字输入 |
| `Obscure` | 隐藏输入内容(密码) |
| `EditMode` | 编辑模式(ESC取消，失焦提交) |
| `KeepFocus` | 输入后保持焦点 |
| `HighlightOnFocus` | 获得焦点时高亮所有文本 |
| `CursorColor` | 光标颜色 |
| `HighlightColor` | 文本高亮颜色 |

---

### Bar

纯色进度条控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `FGColor` | 前景颜色 |
| `BGColor` | 背景颜色 |
| `Direction` | 填充方向：`"Up"` `"Down"` `"Left"` `"Right"` |
| `Percent` | 初始百分比(0.0-1.0) |
| `Speed` | 动画速度(0=无动画) |

**Lua 方法：**

```lua
ctrl:SetPercent(float)            -- 设置百分比(0.0-1.0)
ctrl:SetShadowPercent(float)      -- 设置阴影百分比
ctrl:SetAnimationSpeed(float)     -- 设置动画速度
```

**XML 示例：**
```xml
<Bar ID="HealthBar" Size="200,20" Direction="Right" Percent="0.75"
     FGColor="0,255,0,255" BGColor="100,100,100,255" Speed="0.5" />
```

---

### TextureBar

纹理进度条控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `TextureOffset` | 纹理偏移 |
| `Direction` | 填充方向 |
| `Percent` | 初始百分比 |
| `Speed` | 动画速度 |
| `ShadowColor` | 阴影颜色 |
| `Color` | 颜色调 |

**Lua 方法：**
- 同 Bar

---

### Meter

旋转圆形进度条控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `Percent` | 初始百分比 |
| `CounterClockwise` | 逆时针旋转 |
| `Follow` | 纹理跟随旋转 |
| `HasShadow` | 显示阴影版本 |
| `ShadowAlpha` | 阴影透明度 |
| `Speed` | 动画速度 |
| `Color` | 颜色 |

**Lua 方法：**

```lua
ctrl:SetPercent(float)              -- 设置百分比
ctrl:SetShadowPercent(float)        -- 设置阴影百分比
ctrl:SetPercents(main, shadow)      -- 同时设置主百分比和阴影百分比
ctrl:SetCounterClockwise(bool)      -- 设置逆时针
ctrl:SetFollow(bool)                -- 设置跟随旋转
ctrl:SetShadowColor(uint)           -- 设置阴影颜色(ABGR)
ctrl:SetAnimationSpeed(float)       -- 设置动画速度
```

---

### AlphaAnim

透明度动画控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `AlphaBegin` | 起始透明度(0.0-1.0) |
| `AlphaEnd` | 结束透明度(0.0-1.0) |
| `Texture` | 可选纹理 |
| `Cycle` | 循环模式：`"Once"` `"Loop"` `"Bounce"` |
| `Speed` | 动画速度 |

**Lua 方法：**

```lua
ctrl:SetToBeginning()    -- 跳到开始
ctrl:SetToEnd()          -- 跳到结束
ctrl:Play()              -- 播放动画
ctrl:Reverse()           -- 反向播放
ctrl:RegisterEndCallback(func)  -- 注册结束回调
ctrl:ClearEndCallback()  -- 清除结束回调
ctrl:SetSpeed(float)     -- 设置速度
```

**XML 示例：**
```xml
<AlphaAnim ID="FadeIn" AlphaBegin="0" AlphaEnd="1" Cycle="Once" Speed="1.5">
    <Label String="Hello" />
</AlphaAnim>
```

---

### SlideAnim

滑动动画控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Begin` | 起始偏移 |
| `End` | 结束偏移 |
| `Cycle` | 循环模式 |
| `Speed` | 动画速度 |

**Lua 方法：**

```lua
ctrl:SetBeginVal(x, y)        -- 设置起始位置
ctrl:SetEndVal(x, y)          -- 设置结束位置
ctrl:SetRealiveEndVal(x, y)   -- 设置相对结束位置
```

---

### SpinAnim

旋转动画控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `Speed` | 旋转速度 |
| `Cycle` | 循环模式 |

---

### FlipAnim

翻书动画（Flipbook Animation）控件。按帧步进遍历纹理图集，实现逐帧动画效果。

纹理需将所有帧排列在一个图像中，`Columns` 控制换行位置。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 包含所有动画帧的纹理文件名（帧按列排列） |
| `FrameCount` | 总帧数 |
| `Columns` | 纹理中每行列数（用于换行），总行数 = ceil(FrameCount / Columns) |
| `Clip` | 是否裁剪超出区域（默认 false） |

**Lua 方法：**

```lua
ctrl:SetFrame(int)                -- 设置当前帧索引(0-based)
ctrl:SetTexture(string)           -- 设置纹理
```

**继承自 Control 的动画方法：**
```lua
ctrl:SetToBeginning()             -- 跳到第一帧
ctrl:SetToEnd()                   -- 跳到最后一帧
ctrl:Play()                       -- 播放动画
ctrl:Stop()                       -- 停止动画
ctrl:SetSpeed(float)              -- 设置播放速度
```

**XML 示例：**
```xml
<!-- 4x4 网格，16帧，循环播放 -->
<FlipAnim ID="LoadingAnim" Texture="LoadingSpinner.dds"
          FrameCount="16" Columns="4" Size="64,64"
          Speed="0.05" Cycle="Loop" />
```

**使用场景：**
- 加载旋转动画（spinner）
- 图标闪烁/高亮效果
- 任何需要逐帧切换纹理的动画

---

### ScrollAnim

滚动纹理动画控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Texture` | 纹理文件名 |
| `MaskTexture` | 遮罩纹理文件名 |

**Lua 方法：**

```lua
ctrl:SetTexture(string)           -- 设置纹理
ctrl:SetMask(string)              -- 设置遮罩
ctrl:SetTextureAndMask(t, m)      -- 同时设置纹理和遮罩
```

---

### PullDown

下拉选择框控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `AutoFlip` | 自动翻转到按钮上方 |
| `AutoSizePopUp` | 自动调整弹出大小 |
| `SpaceForScroll` | 为滚动条保留空间 |
| `ScrollThreshold` | 添加滚动条的阈值 |

**子控件：**
- `<ButtonData>` - 定义打开下拉框的按钮
- `<GridData>` - 定义下拉框背景网格
- `<ScrollPanelData>` - 包含子按钮的滚动面板
- `<StackData>` - 包含子按钮的堆栈
- `<InstanceData>` - 子按钮模板

**Lua 方法：**

```lua
ctrl:BuildEntry()                    -- 添加条目
ctrl:ClearEntries()                  -- 清除所有条目
ctrl:CalcuateInternals()             -- 计算内部大小
ctrl:ForceClose()                    -- 强制关闭
ctrl:GetButton() -> Button           -- 获取按钮
ctrl:GetGrid() -> Grid               -- 获取网格
ctrl:GetScrollPanel() -> ScrollPanel -- 获取滚动面板
ctrl:GetStack() -> Stack             -- 获取堆栈
ctrl:IsOpen() -> bool                -- 是否打开
ctrl:RegisterSelectionCallback(func) -- 注册选择回调
ctrl:SetDisabled(bool)               -- 设置禁用
```

---

### SimplePullDown

简化版下拉框控件。

**XML 属性：**
- 继承 PullDown 的所有属性
- `EntryInstance` - 条目实例的 ID

**Lua 方法：**

```lua
ctrl:SetEntries(table, selected)       -- 设置条目
ctrl:ClearEntries()                    -- 清除条目
ctrl:SetSelectedIndex(index, callback) -- 设置选中索引
ctrl:GetSelectedIndex() -> uint        -- 获取选中索引
ctrl:GetSelectedEntry() -> table       -- 获取选中条目
ctrl:SetEntrySelectedCallback(func)    -- 注册选择回调
```

---

### TabControl

标签页控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `TabContainer` | 包含标签页的控件ID |
| `TabButtons` | 包含标签按钮的控件ID |
| `SelectedTab` | 初始选中的标签页ID |

**标签按钮命名规则：**
按钮ID必须以 `"SelectTab_"` 开头，后跟标签页ID。

**Lua 方法：**

```lua
ctrl:SelectTab(control)              -- 选择标签页
ctrl:SelectTabByID(string)           -- 通过ID选择标签页
ctrl:GetSelectedTab() -> Control     -- 获取选中的标签页
ctrl:GetSelectedTabID() -> string    -- 获取选中的标签页ID
ctrl:SetTabSelectedCallback(func)    -- 注册选择回调
```

**XML 示例：**
```xml
<TabControl TabContainer="TabPages" TabButtons="TabButtons" SelectedTab="Tab1">
    <Stack ID="TabButtons" StackGrowth="Horizontal">
        <Button ID="SelectTab_Tab1" String="Tab 1" />
        <Button ID="SelectTab_Tab2" String="Tab 2" />
    </Stack>
    <Container ID="TabPages">
        <Container ID="Tab1">Content 1</Container>
        <Container ID="Tab2" Hidden="1">Content 2</Container>
    </Container>
</TabControl>
```

---

### Slider

滑块控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Style` | 背景网格样式 |
| `Gutter` | 滑块到达两端前停止的区域 |
| `Vertical` | 垂直滑动 |
| `Length` | 滑块长度 |
| `<Thumb>` | 滑块子控件 |

---

### DragPanel

可拖动面板控件。通过按住鼠标获得焦点后拖动到新位置，显示被裁剪在上下/左右/四周之外的内容。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Horizontal` | 允许水平拖动滚动（默认 true） |
| `Vertical` | 允许垂直拖动滚动（默认 true） |
| `ZoomMax` | 发送给控件/Lua 的最大缩放值 |
| `ZoomMin` | 发送给控件/Lua 的最小缩放值 |
| `ZoomStep` | 鼠标滚轮等效缩放的增量 |

**XML 示例：**
```xml
<DragPanel ID="MapDrag" Size="parent,parent" Horizontal="1" Vertical="1" />
```

---

### WorldAnchor

绑定到3D世界位置的控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `ZoomOffsetNear` | 近处缩放偏移 |
| `ZoomOffsetFar` | 远处缩放偏移 |

**Lua 方法：**

```lua
ctrl:SetWorldPositionVal(x, y, z)           -- 设置世界位置
ctrl:SetZoomOffsetNearVal(x, y, z)          -- 设置近处缩放偏移
ctrl:SetZoomOffsetFarVal(x, y, z)           -- 设置远处缩放偏移
```

---

### Line

绘制线段的控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Start` | 起点坐标 |
| `End` | 终点坐标 |
| `Width` | 线宽 |
| `Color` | 颜色(RGBA) |

**XML 示例：**
```xml
<Line Start="100,100" End="400,400" Width="10" Color="255,128,63,200" />
```

---

### Box / ColorBox

纯色矩形控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Color` | 颜色(RGBA) |

**Lua 方法：**

```lua
ctrl:SetColor(r, g, b, a)    -- 设置颜色
ctrl:SetColorByName(name)    -- 通过名称设置颜色
```

**XML 示例：**
```xml
<Box Size="100,50" Color="255,0,0,128" />
```

---

### Movie

视频播放控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `Movie` | Bink 视频文件名 |
| `MovieMask` | 视频遮罩 |
| `LoopMovie` | 循环播放 |
| `MaskTexture` | 遮罩纹理 |
| `StretchMode` | 拉伸模式 |
| `FlipX` | 水平翻转 |
| `FlipY` | 垂直翻转 |

**XML 示例：**
```xml
<Movie Movie="Intro.bik" Size="640,480" LoopMovie="1" />
```

---

### Graph

折线图控件。

**Lua 方法：**

```lua
ctrl:SetSeriesColor(index, r, g, b, a)  -- 设置系列颜色
ctrl:AddSeriesPoint(index, x, y)        -- 添加数据点
ctrl:ClearSeries(index)                  -- 清除系列数据
ctrl:SetAxisLabels(xLabel, yLabel)       -- 设置轴标签
```

---

### Include

将其他 XML 文件的内容包含到当前上下文。

**XML 示例：**
```xml
<Include File="PopupDialog" />
```

---

### Instance

定义一组可以通过 `<MakeInstance>` 标签或 `ContextPtr:BuildInstanceForControl()` 创建的控件模板。

**XML 定义：**
```xml
<Instance Name="MyInstance">
    <Bar ID="TopControl" Size="10,10" Hidden="1"/>
</Instance>
```

### MakeInstance

创建 Instance 实例。

**XML 使用：**
```xml
<Stack ID="MyStack">
    <MakeInstance Name="MyInstance" ID="MyInstance1" />
    <MakeInstance Name="MyInstance" ID="MyInstance2" />
</Stack>
```

**Lua 动态创建：**
```lua
local myInstance:table = {};
ContextPtr:BuildInstanceForControl("MyInstance", myInstance, Controls.MyStack);
-- myInstance.TopControl 现在可以访问
```

**Lua 访问：**
```lua
Controls.MyInstance1.TopControl:SetHide(false);
```

---

### ToolTipType

自定义工具提示类型。

**XML 示例：**
```xml
<ToolTipType Name="TypeRoundImage">
    <Image ID="ToolTipFrame" Size="64,64" Texture="Frame.dds">
        <Image ID="ToolTipImage" Size="64,64" Texture="Icon.dds" />
    </Image>
</ToolTipType>

<!-- 使用自定义工具提示 -->
<Button ToolTipType="TypeRoundImage" />
```

---

### Tutorial

教程系统控件。

**XML 属性：**

| 属性 | 说明 |
|------|------|
| `AlwaysShow` | 调试时始终显示 |
| `ID` | 教程控件ID |
| `TriggerBy` | 触发显示的ID列表(逗号分隔) |

**Lua 方法：**

```lua
UITutorialManager:ShowControlsByID("triggerID")
UITutorialManager:HideControlsByID("triggerID")
UITutorialManager:HideAll()
```

**XML 示例：**
```xml
<Container ID="TutorialArea">
    <Tutorial>
        <Button ID="TutorialButton" String="Click Me" />
    </Tutorial>
</Container>
```

---

## 通用 XML 属性

所有控件都支持以下属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `ID` | string | 控件名称，用于 Lua 中的 Controls 命名空间 |
| `Size` | `N,N` / `parent,N` / `auto,N` | 控件大小 |
| `Offset` | `x,y` | 相对于锚点的位置 |
| `Anchor` | `X,Y` | 锚定位置：`L/C/R` × `T/C/B` |
| `AnchorSide` | `I,O` | 锚定在父控件的内部或外部 |
| `Hidden` | `0`/`1` | 初始隐藏状态 |
| `Disabled` | `0`/`1` | 初始禁用状态 |
| `Color` | `R,G,B,A` | 颜色值(0-255) |
| `Alpha` | `0.0-1.0` | 透明度 |
| `ToolTip` | string | 工具提示文本 |
| `ToolTipType` | string | 工具提示类型 |
| `ConsumeMouseButton` | `0`/`1` | 消耗鼠标点击 |
| `ConsumeMouseOver` | `0`/`1` | 消耗鼠标移动 |
| `ConsumeMouseWheel` | `0`/`1` | 消耗鼠标滚轮 |
| `NeedsMouseOver` | `0`/`1` | 接收鼠标进入/退出事件 |
| `NoClip` | `0`/`1` | 禁用裁剪 |
| `GlobalUpdate` | `0`/`1` | 隐藏时也更新 |
| `ModalBlocksInput` | `0`/`1` | 模态时阻止输入 |
| `ShowOnMouseOver` | `0`/`1` | 鼠标悬停时显示 |
| `HideOnMouseOver` | `0`/`1` | 鼠标悬停时隐藏 |
| `ClampSize` | `0`/`1`/`"Vertical"`/`"Horizontal"` | 限制为父控件大小 |
| `InnerPadding` | `x,y` | 使用 parent 大小时的内边距 |
| `MinSize` | `w,h` | 自动大小时的最小大小 |
| `AutoSizePadding` | `x,y` | 自动大小时子控件周围的边框 |
| `d` | string | 调试属性 |

---

## 通用 Lua 方法

所有控件都支持以下方法：

### 显示/隐藏
```lua
ctrl:SetHide(bool)           -- 设置隐藏
ctrl:SetShow(bool)           -- 设置显示
ctrl:IsHidden() -> bool      -- 是否隐藏
ctrl:IsVisible() -> bool     -- 是否可见
ctrl:SetAllChildrenVisible(bool) -- 显示/隐藏所有子控件
```

### 大小
```lua
ctrl:SetSizeVal(w, h)        -- 设置大小
ctrl:GetSizeX() -> number    -- 获取宽度
ctrl:GetSizeY() -> number    -- 获取高度
ctrl:GetSizeVal() -> w, h    -- 获取大小
ctrl:DoAutoSize()            -- 根据子控件自动调整大小
```

### 位置
```lua
ctrl:SetOffsetVal(x, y)      -- 设置偏移
ctrl:GetOffsetX() -> number  -- 获取X偏移
ctrl:GetOffsetY() -> number  -- 获取Y偏移
ctrl:GetOffsetVal() -> x, y  -- 获取偏移
ctrl:GetScreenOffset() -> x, y -- 获取屏幕偏移
```

### 颜色/透明度
```lua
ctrl:SetColor(r, g, b, a)    -- 设置颜色
ctrl:SetColorByName(name)    -- 通过名称设置颜色
ctrl:SetAlpha(float)         -- 设置透明度
ctrl:GetAlpha() -> number    -- 获取透明度
```

### 禁用/启用
```lua
ctrl:SetDisabled(bool)       -- 设置禁用
ctrl:IsDisabled() -> bool    -- 是否禁用
ctrl:SetEnabled(bool)        -- 设置启用
ctrl:IsEnabled() -> bool     -- 是否启用
```

### 锚定
```lua
ctrl:SetAnchor(string)       -- 设置锚定
ctrl:ReprocessAnchoring()    -- 重新处理锚定
```

### 父子关系
```lua
ctrl:ChangeParent(newParent) -- 改变父控件
ctrl:GetParent() -> Control  -- 获取父控件
ctrl:GetParentByType(type) -> Control  -- 按类型获取父控件
ctrl:GetParentByID(id) -> Control      -- 按ID获取父控件
ctrl:Reparent()              -- 重新附加到父控件
ctrl:GetNumChildren() -> number        -- 获取子控件数量
ctrl:GetChildren() -> Control[]        -- 获取所有子控件
ctrl:DestroyAllChildren()    -- 销毁所有子控件
ctrl:SortChildren(func)      -- 排序子控件
ctrl:AddChildAtIndex(ctrl, index) -- 在指定索引添加子控件
```

### 工具提示
```lua
ctrl:SetToolTipString(text)           -- 设置工具提示
ctrl:LocalizeAndSetToolTip(key)       -- 本地化设置工具提示
ctrl:GetToolTipString() -> string     -- 获取工具提示
ctrl:SetToolTipCallback(func)         -- 设置工具提示回调
ctrl:ClearToolTipCallback()           -- 清除工具提示回调
ctrl:SetToolTipType(type)             -- 设置工具提示类型
ctrl:EnableToolTip(bool)              -- 启用/禁用工具提示
ctrl:IsToolTipEnabled() -> bool       -- 工具提示是否启用
```

### 鼠标事件
```lua
ctrl:RegisterMouseEnterCallback(func)  -- 注册鼠标进入回调
ctrl:RegisterMouseExitCallback(func)   -- 注册鼠标离开回调
ctrl:RegisterMouseOverCallback(func)   -- 注册鼠标移动回调
ctrl:ClearMouseEnterCallback()         -- 清除鼠标进入回调
ctrl:ClearMouseExitCallback()          -- 清除鼠标离开回调
ctrl:ClearMouseOverCallback()          -- 清除鼠标移动回调
ctrl:RegisterWhenShown(func)           -- 注册显示时回调
ctrl:RegisterWhenHidden(func)          -- 注册隐藏时回调
ctrl:HasMouseOver() -> bool            -- 鼠标是否在控件上
```

### 鼠标消耗
```lua
ctrl:SetConsumeMouseOver(bool)         -- 设置消耗鼠标移动
ctrl:SetConsumeMouseButton(bool)       -- 设置消耗鼠标点击
ctrl:SetConsumeMouseWheel(bool)        -- 设置消耗鼠标滚轮
ctrl:GetConsumeMouseOver() -> bool     -- 是否消耗鼠标移动
ctrl:GetConsumeMouseButton() -> bool   -- 是否消耗鼠标点击
ctrl:GetConsumeMouseWheel() -> bool    -- 是否消耗鼠标滚轮
```

### 其他
```lua
ctrl:SetID(string)                     -- 设置ID(不更新Controls表)
ctrl:GetID() -> string                 -- 获取ID
ctrl:SetModal(bool)                    -- 设置模态
ctrl:IsModal() -> bool                 -- 是否模态
ctrl:SetTag(int)                       -- 设置调试标签
ctrl:GetTag() -> int                   -- 获取调试标签
ctrl:BranchResetAnimation()            -- 递归重置动画
ctrl:CalculateVisibilityBox()          -- 更新可见框
ctrl:SetNoClip(bool)                   -- 设置禁用裁剪
```

---

## 调试属性 (d)

`d` 属性用于在不修改 Lua 的情况下显示调试覆盖层：

| 值 | 效果 |
|----|------|
| `"1"` - `"6"` | 纯色覆盖层 |
| `"*"` | 随机颜色(12种旋转) |
| `"id"` | 显示控件ID文本，悬停时显示完整路径工具提示 |
| `"+"` 后缀 | 级联到所有子控件(如 `"id+"`, `"6+"`) |

**XML 示例：**
```xml
<Image ID="MyIcon" d="1"/>           <!-- 单个控件的颜色覆盖 -->
<Container d="id+">                   <!-- 显示所有子控件的ID -->
    <Label ID="Title"/>
    <Button ID="OK"/>
</Container>
```

---

## Size 语法参考

| 语法 | 含义 |
|------|------|
| `parent` | 与父控件相同大小 |
| `parent-16` | 父控件大小减去16px |
| `auto` | 适应子控件内容 |
| `400` | 固定400px |
| `400,300` | 宽400px，高300px |

## Anchor 语法参考

格式：`水平,垂直`

| 水平 | 垂直 | 示例 |
|------|------|------|
| `L` (左) | `T` (上) | `L,T` = 左上 |
| `C` (中) | `C` (中) | `C,C` = 居中 |
| `R` (右) | `B` (下) | `R,B` = 右下 |

## 常用纹理名称

| 纹理 | 用途 |
|------|------|
| `Controls_GenericPanel` | 标准面板背景(9切片) |
| `Controls_GenericPanel_Blank` | 平坦面板背景(9切片) |
| `Controls_Close` | 关闭按钮(X) |
| `LaunchBar_Hook_GovernmentButton` | LaunchBar 按钮样式 |
| `LaunchBar_TrackPip` | LaunchBar 小圆点指示器 |
