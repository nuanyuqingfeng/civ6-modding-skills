# 转换为 ForgeUI XML/Lua

## 控件与布局映射

| HTML/CSS 设计 | ForgeUI 对应 | 需要人工决定的内容 |
|---|---|---|
| div 分组 | Container | Size、Anchor、Offset；Container 本身不画底色 |
| 纯色块/遮罩 | Box | Color、ConsumeMouse，不假设 Container.Color 能画矩形 |
| 位图背景/头像 | Image | Texture、Size、裁切/伸缩策略 |
| 九宫格背景 | Grid | SliceCorner、SliceTextureSize |
| flex row/column | Stack | StackGrowth Right/Bottom、StackPadding；没有完整 CSS flex 算法 |
| 固定 2×2 卡片 | 两行 Stack，外层纵向 Stack | 比未经验证的自动换行更易保持尺寸 |
| 可滚动正文/列表 | ScrollPanel + Label/Stack | 视口、WrapWidth、滚动条空间、重新计算尺寸 |
| 文本 | Label | 实际存在的 FontNormal/FontFlair 样式及 LOC |
| 状态按钮 | GridButton + GridData / Button | 状态帧、热区、禁用行为 |
| 进度 | Bar、TextureBar 或 Meter | 依官方同类实例选择，用 SetPercent 更新 |

核对目标游戏的 Civ6_Styles.xml 和同类官方屏幕；若工作区有 ModTools，可同时查 skills/04-lua/lua-xml-controls.md。独立包不要求存在该仓库路径。属性名、字体样式、API 的证据来自原生调用点，而不是浏览器 DOM。不要假定 CSS 的 z-index、box-shadow、flex-wrap、border-radius 都能直接变成 XML 属性。

### 像素与锚点

明确面板固定画布与最小可用游戏视口。1024×640 只是一个可选案例，不是统一标准。大面板需要在目标分辨率/UI 缩放下验证；不要猜测不存在的 `SetScale` 方法来解决越界。

`Anchor="L,T"` 时正 Offset 向右/下；`R,B` 时正 Offset 向左/上；`C,C` 与 `L,T` 同向（正 X 向右、正 Y 向下；`C` 无镜像）。不能把 CSS `top` 的符号不加转换地贴到居中或底部锚点。初次迁移优先明确的左上锚点，底部按钮再使用相应锚点。

### 居中、限宽与页面比例

宽屏界面可以使用居中的受限宽度，不能把“宽”自动解释成铺满整个窗口。先分别确定最大宽度、最大高度和四周最小留白，再按稿件数量、说明长度及操作顺序分配内部空间。多个页面共用外框时，各页仍可有自己的正文最大宽度，例如较少的里程碑卡片无需拉宽填满画布。具体像素值是项目设计参数，不是文明6通用尺寸。

继续使用明确的 `Anchor="L,T"` 时，可从同一组游戏视口尺寸计算：

```lua
local screenW, screenH = UIManager:GetScreenSizeVal();
if not screenW or not screenH or screenW <= 0 or screenH <= 0 then return false; end
local width = math.min(maxWidth, screenW - marginX * 2);
local height = math.min(maxHeight, screenH - marginY * 2);
if width <= 0 or height <= 0 then return false; end
Controls.Frame:SetSizeX(width);
Controls.Frame:SetSizeY(height);
Controls.Frame:SetOffsetVal(math.floor((screenW-width)/2), math.floor((screenH-height)/2));
```

`maxWidth/maxHeight/marginX/marginY` 由调用者传入或定义。正文和滚动视口都从最终 `width/height` 推导；不要用框体的受限宽度配合子页面的全屏宽度。无效尺寸返回后，调用方也必须推迟后续排版；窗口恢复时走官方尺寸变化事件，不必逐帧轮询。

HTML 预览须截取**完整视口**，显示面板与周围空间的比例；仅截面板或缩放到浏览器宽度会掩盖“几乎全屏”的问题。源纹理、原生控件和 HTML 中的切片、按钮单帧、间距共用同一组设计尺寸；同时检查短文、长文、空数据和大量条目。动态卡片按 Label 实际高度安排下一行，避免用一套很高的固定空框容纳所有内容。

2026-09-25，20.0 项目用户实机反馈确认上一轮横向布局“没有出现偏移”。该轮组合使用了左上坐标计算居中、受限高度、等尺寸四态固定按钮，以及可变卡片显式零偏移/内边距。这个反馈支持在该项目中保留整套策略，不能证明某个单独参数就是旧偏移根因，也不代表全部分辨率/UI缩放已验证。本轮随后提出的限宽留白和新纹理应另行验收。

### 四态与九宫格

固定尺寸按钮优先导出与控件**单帧同尺寸**的四态纹理，直接使用 Button：

```xml
<Button ID="ConfirmButton" Size="216,48" Anchor="L,T" Offset="400,320"
        Texture="UI_MYMOD_BUTTON_GOLD_216" StateOffsetIncrement="0,48" States="4">
  <Label ID="ConfirmLabel" Anchor="C,C" Style="FontNormal16"
         String="LOC_MYMOD_CONFIRM" />
</Button>
```

此源 PNG 为 **216×192**，单帧 216×48。180×40 与 216×40 的按钮分别导出 180×160、216×160；不能仅改 XML Size 就假设源皮肤被正确缩放。装饰文字保持独立 Label。选择框另放 Image，不能把标题、正文放进会被 SetHide 的选择框子树。

需要可变宽度时才选 GridButton/GridData，依据官方同类皮肤核对 **SliceCorner、SliceSize、SliceTextureSize、MinSize 和 InnerPadding/Offset**，并做原生最小/最大宽度验收。HTML 的 background-size 不证明游戏九宫格可用。不要把 256px 源宽与 180px 目标宽、缺省 SliceSize 的旧示例作为已验证模板。

19.47 的实机截图观察到任务按钮跨卡片延伸；相关旧 XML 使用了上述未验证九宫格模式。本次改为等尺寸 Button 可消除该参数依赖，最终显示仍以修正后的游戏截图为准；不把尚未证实的引擎内部原因写成定论。

官方 `Controls_Close.dds` 配合 `StateOffsetIncrement="0,34"` 可核对帧序：顶部 Normal，其下 Hover、Down、Disabled。正 Y 向下选帧，不翻转 PNG/DDS。九宫格的 SliceTextureSize 也只取一帧尺寸。

### 字体不是连续的字号序列

查 **Base/Assets/UI/Fonts/Civ6_FontStyles_zh_Hans_CN.xml**（以及目标语言版本）；只查 Civ6_Styles.xml 不够。真实定义包含 FontFlair28、FontFlair30、FontFlair40，但没有 FontFlair32。19.47 使用不存在的 FontFlair32 后实机标题回退为很小的文字，不能靠 Offset 修正。

优先选择存在的样式，再将 HTML 对齐到相同字号。自定义字体样式需要单独验证加载，不通过拼接字号生成未知 Style。中文字体字面框与浏览器字体不同，允许通过实机对照做少量光学对齐。

### 动态实例与滚动

XML `Instance` 是模板，模板内 ID 通过 `instance.ControlName` 访问，不是 `Controls.ControlName`。重建列表后重新赋值、注册回调，避免使用已回收的实例引用。模板根 ID、InstanceManager 根控件名称保持一致。

长说明使用明确的视口和 WrapWidth，为滚动条留宽。动态填入内容后对相关 Stack `CalculateSize()`，对 ScrollPanel `CalculateInternalSize()`；按实际调用点补齐 anchoring。不要为避免溢出无限缩小字号，也不要直接拉长面板覆盖确认按钮。

### 滚轮、排序与卡片状态验收

滑动条可拖动不代表滚轮热区正确。分别检查 ScrollPanel 的视口、`MouseWheelAreaSize`、`DisableMouseWheelScroll`，以及覆盖其上的容器/按钮是否吞掉滚轮。官方 `Base/Assets/UI/NotificationPanel.xml` 使用显式 MouseWheelAreaSize；需要拦截点击的卡片应区分 `ConsumeMouseButton` 与 `ConsumeMouseWheel`，不要把所有祖先统一改为吞掉鼠标。动态重排后重算滚动范围。属性应以本机官方 XML 为依据，HTML 滚动或 XML 解析通过不能证明 ForgeUI 实际响应；游戏内分别在卡片、卡片间隙和详情区测试滚轮。

排序验收必须包含时代与战斗力顺序相反的条目，以及相同主键、无战斗力和平民条目；检查列表首尾/完整顺序，不只检查按钮文字。两个排序字段偶然得到同序时并非必然错误。若设计为再次点击反向排序，要显示方向，并验证首次选择字段和重复点击两个路径。

等尺寸新闻/物品卡不能只给禁用状态增加原因行。先测量同一列表全部可见卡片的文本高度，再使用统一高度和网格步长；可用卡保留同一状态栏空间。长原因可截断并用浮动文本补全，不能覆盖奖励正文；切换筛选、城市和可用状态后重新计算。

## Lua 连接与生命周期

示例所需 LOC 声明见 [texts.json](../assets/starter/texts.json)。独立使用时将 tag / text 转成目标语言的 LocalizedText，经工程 UpdateText 注册；group 仅为编辑分组，JSON 本身不由游戏加载。使用 ModTools 时合并进 .CIV 的 workspace["文本"]["custom_entries"]；已有工程按 tag 更新/去重，保留无关条目。正式使用时统一重命名 DEMO 资源、LOC 和事件前缀。

[NativePanel.lua](../assets/starter/NativePanel.lua) 展示纯 UI 的打开、选择、确认和关闭；配套 [XML](../assets/starter/NativePanel.xml) 与 HTML 共用资源尺寸。示例仅发送 `LuaEvents.DemoPanel_Confirmed()`，并没有创建 Gameplay 奖励。接入真实工程时改成已存在且经核实的协议，不把示例的本地选择状态当作真实游戏状态。

- 保留原有 Controls ID、实例字段、事件名及领袖/文明门控；需要变更协议时同步调用者。
- UI 从项目既有数据层读取，修改玩法通过现有 `UI.RequestPlayerOperation` 路径交给 GP 执行。核对当前项目参数签名；不凭示例猜 `OnStart` 名称。GP 仍须重新检查资格/费用，UI 禁用按钮不是业务验证。
- 枚举可见状态及优先级：不可用原因、就绪、进行中、冷却、已完成/待领取、选中、请求中等，按实际玩法选择。全局状态与个体状态并存时确认优先级，不能仅看个体计时为 0 就显示就绪。
- 注册事件在初始化中执行一次，避免重复打开叠加回调或顶栏按钮。需退出清理的订阅在 shutdown 移除；reload 与新存档分别验证。
- 共享 helper 走 import 角色，不作为第二个 UI/Gameplay 入口执行。文件名中含版本点号时，在 `include("MyMod_19.47_Support.lua")` 明确保留 `.lua` 后缀，避免解析歧义。

### 弹窗层级与关闭

需要覆盖另一个面板的奖励/确认框使用原生 Popup 队列；单靠 XML 顺序、SetHide 或 HTML z-index 无法保证覆盖。按官方类似屏幕选用优先级和参数。已有实用模式：

```lua
UIManager:QueuePopup(ContextPtr, PopupPriority.Current)
-- 确认、关闭按钮和 Esc 均汇入同一关闭函数
UIManager:DequeuePopup(ContextPtr)
```

不要一律使用最高优先级，也不要不经检查给子弹窗设置 RenderAtCurrentParent，后者可能把它留在父层级之下。打开前校验本地玩家/权限，刷新数据；无可选项时禁用确认，选中数量由现有规则决定。Esc/取消不要意外提交奖励或费用。

采用 AnimSidePanelSupport 时使用 `CreateScreenAnimation(...)` 返回对象的 Show/Hide；它与 SlideAnim 控件本身不同。退出动画要等 OnEndOut 再隐藏 Context，立即 `SetHide(true)` 会截断动画。选用动画时核对官方 helper 的当前签名和清理逻辑。

顶栏入口不属于 HTML 的导航。独立 Context 可以各自注入入口，沿用已验证的 LaunchBar 支持代码；不要修改原版 XML 或照搬不完整的跨 Context InstanceManager。项目需要新入口时读对应官方/项目实现并测试初始化顺序。

## 标题文字与字体图标

页面/页签标题、奖励名称、卡片标题和分组名通常保持纯文字；产出、费用与效果描述按语义使用 `[ICON_XXX]` 并带文字标签。例如标题用 `住房`，正文用 `本城 +2[ICON_Housing]住房`。不能因为标题含产出关键词就套用描述装饰器。

标题旁独立的实体或类别 Image 图标可按设计保留；它不是嵌入标题 LOC 的字体图标。原版特定样式或用户要求可有例外，不把这个偏好做成对所有标题的无条件过滤。文本同时承担标题和描述角色时拆分 LOC。验收还要检查 Lua 动态填充的奖励名，单看 `_TITLE` 后缀不够。

## 尺寸控制与警告定位

每个轴选择一种尺寸来源。XML 用 `parent` / `parent-N` 时让引擎管理该轴；若 Lua 会调用 `SetSizeX/SetSizeY/SetSizeVal` 或布局函数重写该轴，则 XML 用数值初值。两者混用会触发 `SetSize called on parent-sized control`，没有明显偏移也不等于声明正确。检查动态实例中的子背景，不只检查顶层容器。

列表筛选中的“没有对应条目”可能是正常结果，使用无副作用的成员查询，不借用每次打印 WARN 的执行校验器。真正要应用奖励时仍验证修正器/目标存在。不要为降噪关闭整个日志系统。

通用 Lua 解释器提供的标准库或测试桩函数不能代替目标游戏环境证据。固定参数调用直接传参；按类型动态选取官方 helper 时先确认函数存在。一行包含多个调用的 nil-function 报错应拆开定位，不能据此断言具体哪项 API 在所有版本都不可用。模拟测试覆盖缺失 helper/库函数的路径，修复后的实机状态单独记录。

## 迁移验收

先运行 [check-native-ui.py](../scripts/check-native-ui.py) 的尺寸/字体检查：

```powershell
python check-native-ui.py --manifest textures/texture_manifest.json --xml NativePanel.xml --font-styles "游戏/Base/Assets/UI/Fonts/Civ6_FontStyles_zh_Hans_CN.xml"
```

可重复传入 --xml 和 --font-styles；脚本只读，检查已注册纹理的固定 Button 帧尺寸、四态范围、直接父容器内的左上热区和字体存在性。九宫格只报告需要原生验收，不声称能静态模拟游戏布局。

逐项比对 HTML 与 XML 的面板尺寸、边距、卡片间距、热区、滚动视口、层级与各状态，不以背景看起来相似代替交互验收。检查长中文、较大数值、无数据、重复点击、不同本地领袖、重复开关、Esc 和父子弹窗；保留业务原有数值，除非用户明确要求调整。
