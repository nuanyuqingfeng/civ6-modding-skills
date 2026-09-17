# StretchMode 方法汇总

## 原版中实际出现过的 StretchMode

| StretchMode | 出现次数 |
| --- | ---: |
| `Auto` | 46 |
| `Fill` | 80 |
| `None` | 21 |
| `Tile` | 139 |
| `TileX` | 12 |
| `TileY` | 5 |
| `Uniform` | 7 |
| `UniformToFill` | 16 |
| `UniformToFillCentered` | 1 |

## 各模式效果推测

### `Tile`

- 双向平铺。
- 更像“把一张小纹理重复铺满整个控件”。
- 适合底纹、花边、重复背景。

### `TileX`

- 仅横向平铺。
- 纵向通常不会重复。
- 适合横条、横向装饰带、长条底板。

### `TileY`

- 仅纵向平铺。
- 横向通常不会重复。
- 适合竖条、纵向装饰纹。

### `Fill`

- 强制把纹理拉伸到控件大小。
- 不保证宽高比，可能发生变形。
- 适合需要“先铺满再说”的背景图、遮罩图。

### `Uniform`

- 保持原始宽高比。
- 会完整显示进控件内，但可能留空边。
- 类似常见 UI 里的 `contain`。

### `UniformToFill`

- 保持原始宽高比，但要求铺满控件。
- 可能会裁掉一部分边缘。
- 类似常见 UI 里的 `cover`。

### `UniformToFillCentered`

- 效果大概率接近 `UniformToFill`。
- 区别更像是“按中心点裁切”。
- 原版只出现 1 次，属于更特化的版本。

### `None`

- 不做拉伸。
- 纹理按原始尺寸显示。
- 可能出现超出裁切，也可能出现空白边。

### `Auto`

- 这个最不确定。
- 从命名看，更像交给引擎自动决定显示方式。
- 可以把它理解为“默认策略”或“自动适配策略”。

## 与 Sampler 的显式搭配

原版 XML 里，明确在**同一行**同时写出 `StretchMode` 与 `Sampler` 的，当前只统计到下面两种：

| StretchMode | Sampler | 出现次数 |
| --- | --- | ---: |
| `Fill` | `Linear` | 6 |
| `UniformToFill` | `Linear` | 5 |

## 可以确认的常见搭配

### `StretchMode="Fill" Sampler="Linear"`

- 原版中明确存在。
- 适合需要放大/缩小且希望边缘更平滑的图片。
- 常见于人物图、背景图、需要整体铺满的插图。

示例：

- `Base\Assets\UI\DiplomacyActionView.xml`
  - `FallbackLeaderImage`
  - `StretchMode="Fill" Sampler="Linear"`

### `StretchMode="UniformToFill" Sampler="Linear"`

- 原版中明确存在。
- 更适合“保比例铺满”，允许裁边，但不希望画面锯齿明显的图片。

## 实战理解建议

如果目标是：

- 重复花纹底板：优先试 `Tile` / `TileX` / `TileY`
- 强行铺满整个区域：优先试 `Fill`
- 保持比例且允许裁边：优先试 `UniformToFill`
- 保持比例且不裁边：优先试 `Uniform`
- 按原图大小显示：用 `None`

如果图片属于：

- 人物图、大插画、背景图：  
  通常可以优先试 `StretchMode="Fill" Sampler="Linear"` 或 `StretchMode="UniformToFill" Sampler="Linear"`

- 可重复纹理、装饰条、花边：  
  通常优先试 `Tile` / `TileX` / `TileY`

## 对当前项目的直接参考

你当前项目里这类写法就很典型：

```xml
<Image ID="PalaceBackground" Anchor="C,C" StretchMode="Tile" Size="parent,parent" Hidden="1"/>
```

这类写法的语义基本就是：

- 让背景纹理按平铺方式覆盖整个容器
- 尽量避免单张图片被强行拉伸变形

## 备注

- 上面的“效果推测”是基于原版命名语义、原版使用习惯，以及常见 UI 引擎同名规则做出的判断。
- 其中 `Tile` / `Fill` / `Uniform` / `UniformToFill` 的含义相对可靠。
- `Auto` 与 `UniformToFillCentered` 的具体底层实现，仍建议在游戏内做对照测试确认。
