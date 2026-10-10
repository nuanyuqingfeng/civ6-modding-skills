---
name: civ6-html-ui
description: 用 HTML/CSS 设计文明6 Mod 界面并导出背景、透明装饰和按钮状态纹理，转换为原生 ForgeUI XML/Lua。不绑定任何工程工具链，独立使用。适用于 HTML 原型转化、Civ6 UI 美化、精灵表与九宫格制作；不用于普通网站开发，也不把 HTML 当作游戏运行时。原生布局规范、ForgeUI 模板与 UI↔GP 通信口径以 civ6-modding（xml-templates.md / gotchas.md §43 / context-matrix.md）为准。
---

# HTML → Civilization VI UI

交付目标是可维护的原生游戏界面：HTML/CSS 设计源、PNG 纹理、XML 控件、Lua 交互和资源注册共同组成结果。HTML 原型不是可直接加载进 Civ6 的页面，也不存在本 skill 提供的通用 DOM→XML 自动转换器。

## 入口与分享

> ⚠ **工程文件写入铁律**：脚本可以新建工程文件，绝不允许改写工程文件。本 skill 的 `render-textures.cjs` 只写 `--out` 指定的纹理目录，不写工程文件。真源见 `civ6-modding/SKILL.md` 的「工程文件写入铁律」。

本目录即为可独立复制的技能包，使用普通 Markdown、Node.js 和 Python，不依赖任何特定工程工具或 agent 平台。首次接收 ZIP 可先看 [分享包说明](README.md)。首次配置、分享或批量导入时读 [通用入口与依赖](references/portable-use.md)。渲染与校验直接运行包内脚本（`scripts/render-textures.cjs` / `verify-textures.py` / `check-native-ui.py`）。

## 开始时

- 确认 HTML/美术源、已有 XML/Lua 与目标 ModBuddy 工程；保留业务逻辑。
- 家族内先按 `civ6-modding` 的 L0 检索阶梯查正文；原生控件属性、Anchor/Offset 语法与官方样式对照 `civ6-modding` 的 `xml-templates.md` / `ui-controls.md` / `gotchas.md`（§43 Offset 方向）。
- 简短说明使用的依据与待验证项。具体控件/API 查本地官方 UI 调用点；不要从 CSS 名称猜 ForgeUI 属性。
- 列出各页面的入口、所属领袖/文明、Context、弹窗关系和主要状态。HTML 展示页的切换导航可以仅供预览；游戏里原本独立的页面继续独立，不因共享设计稿而合并。

## 按工作阶段读取

1. **设计或导出纹理**：读 [HTML 与导出契约](references/html-textures.md)。复制 [最小 HTML 示例](assets/starter/index.html) 到任务目录，按目标主题改写。运行 [render-textures.cjs](scripts/render-textures.cjs) 输出精确像素 PNG 与清单。
2. **原生布局与交互**：读 [XML/Lua 转换](references/native-ui.md)。[NativePanel.xml](assets/starter/NativePanel.xml) 和配套 Lua 是布局、选择态与弹窗生命周期示例，不含 Mod 专属玩法或通用顶栏注入器。
3. **接入工程、构建和验收**：读 [SDK 工程接入](references/standalone-integration.md)。用 [verify-textures.py](scripts/verify-textures.py) 检查源 PNG；导出链检查只用于符合其目录契约的工程。

不要一次加载全部参考；涉及哪个阶段才读哪个文件。

## 必须保留的设计边界

- 将背景、纹样、分隔线、按钮皮肤烘焙为纹理；数值、价格、状态、说明、可本地化标题与按钮文字保留原生 Label/LOC。进度填充和交互热区保留原生控件。
- 固定按钮优先使用同尺寸四态 PNG + Button；可变尺寸九宫格另行核实，不能把网页缩放当作原生保证。纹理尺寸、单帧高度、切片参数、XML Size 来自同一份尺寸设计。默认 DPR=1；网页缩放预览不能改变输出像素。
- 垂直四态按钮从上往下为 **Normal → Hover → Down → Disabled**。`StateOffsetIncrement="0,帧高"`；`SliceTextureSize` 是单帧大小，不是整张图。
- 标题、页签和奖励名称通常使用纯文字；字体图标用于效果/数值描述，独立 Image 图标另行处理，见[文本角色与尺寸警告](references/native-ui.md#标题文字与字体图标)。
- 字体 Style 从目标语言的 Civ6_FontStyles 文件核实，不按数字拼接：例如 FontFlair32 并不存在。运行原生参考中的尺寸/字体检查脚本。
- 选择框独立于文字内容；隐藏选择框不能连带隐藏卡片标题。禁用态要同时禁用交互，而不只是换成灰色图片。
- 重做 UI 不意味着重做玩法。保留事件协议和数据来源，UI 读数据、发请求，由既有 Gameplay 层验证并执行状态变更；UI↔GP 通道口径以 `civ6-modding/reference/context-matrix.md` 为准。
- 宽屏设计先确定最大宽高和四周留白；整页截图保留周围视口，按 [原生布局参考](references/native-ui.md) 校准尺寸，避免把长条面板默认拉满屏幕。
- 固定装饰可复用；页面入口、权限门控、滚动、弹窗层级和状态刷新要在原生实现中分别成立。

## 最小闭环

先跑通一个背景、一个四态按钮、一张透明选择框和一个原生面板，再批量扩展。无需为每一步重复索取批准；遵守用户已经给出的设计方向和修改范围。

1. 设计 HTML 的正常、禁用、选中、长文本和空内容状态；确认各独立页面的截图。
2. 导出 PNG，检查 alpha、尺寸和四态方向；保留源 HTML、依赖素材与尺寸清单。
3. 用 XML 重建层级；Lua 接入现有状态与操作。检查动态实例、键盘关闭、重复打开与初始化。
4. 通过目标工程的资源流程登记纹理、文本和 UI，检查 PNG→DDS/TEX→XLP→Art.xml 与 UI 入口；`.civ6proj` 清单登记与 cook 产物核对走 `civ6-modding` 的 `art-pipeline.md` / `check_proj_content.py` / `verify_mod_package.py`。
5. 范围内可执行时运行官方 Cooker，再进游戏验证字体、缩放、点击/滚动和弹窗遮挡；无法运行的阶段明确保留为待验收。

交付分别说明 **HTML、原生实现、工程接入、Cooker、游戏内** 的完成情况，附源文件与验证证据。单纯截图、Lua mock 或 Cooker 成功均不足以宣称游戏内验收完成。用户仅要求设计或排除 modinfo/部署时，不自行扩展到安装目录。

## 经验适用范围

提炼自 19.47 UI 重做：独立页面、透明装饰、四态皮肤、奖励弹窗和资源链已完成本地导出/静态及模拟验证，用户实机截图已暴露标题回退与按钮越界；本技能据此修正示例，修正后的引擎显示仍需游戏验收。示例使用原创几何 CSS，不依赖原项目素材、用户盘符或版本编号；不要把该案例的尺寸、角色数量、色系和业务数值当成通用要求。

2026-09-25：20.0 用户确认上一轮原生布局没有偏移；具体组合策略与适用边界见 [原生布局参考](references/native-ui.md)。随后限宽与纹理修改仍需新一轮游戏验收，不能沿用旧反馈作新设计的结论。
