# 官方 UI 面板对照分析（XML + Lua 双文件）

> 来源：ModTools 5.4（MIT，Copyright (c) 2026 Siqi）`skills/04-lua/` 的官方面板分析篇（2026-09-28 吸收）。
> 通信通道与上下文口径以 [`reference/context-matrix.md`](../context-matrix.md) 为准；
> 控件属性速查与 ForgeUI 模板见 `../../ui-controls.md` / `../../xml-templates.md`；Offset 方向见 `../../gotchas.md` §43。

## 核心架构

- [lua-workshop-ingame-structure.md](lua-workshop-ingame-structure.md) — InGame 控件树全景（渲染层级 + LuaContext 加载 + BulkHide + Mod 注入点）
- [lua-workshop-popupdialog.md](lua-workshop-popupdialog.md) — PopupDialog 标准弹窗框架（内容模板 + 生命周期 + 命令系统）
- [lua-workshop-instance-manager.md](lua-workshop-instance-manager.md) — InstanceManager 动态克隆系统（Instance 模板写法 + Lua 包装类模式）
- [lua-workshop-support-libs.md](lua-workshop-support-libs.md) — Support 共享库（SupportFunctions + Civ6Common + ToolTipHelper + PopupManager）

## HUD 面板

- [lua-workshop-actionpanel.md](lua-workshop-actionpanel.md) — 结束回合按钮 + 动画系统（AlphaAnim/SlideAnim/FlipAnim/Meter）
- [lua-workshop-citypanel.md](lua-workshop-citypanel.md) — 城市详情面板（产出/人口/建筑/生产 + MOD 按钮注入点）
- [lua-workshop-unitpanel.md](lua-workshop-unitpanel.md) — 单位操作面板 + UnitFlagManager 3D 旗帜
- [lua-workshop-production-panel.md](lua-workshop-production-panel.md) — 生产选择器 + LaunchBar + TopPanel
- [lua-workshop-worldtracker-minimap.md](lua-workshop-worldtracker-minimap.md) — 科技追踪器 + 小地图镜头 + 通知面板

## 外交系统

- [lua-workshop-diplomacy-dealview.md](lua-workshop-diplomacy-dealview.md) — 交易界面（Instance 模板黄金标准 + 展开折叠 + 数值编辑）
- [lua-workshop-diplomacy-actionview.md](lua-workshop-diplomacy-actionview.md) — 外交三件套（领袖面板 + 丝带 + 3D 场景）

## 全屏面板

- [lua-workshop-techtree.md](lua-workshop-techtree.md) — 科技/市政树（同步滚动 + 搜索 + 弹窗选择器）
- [lua-workshop-government-greatworks.md](lua-workshop-government-greatworks.md) — 政体政策卡 + 巨作管理（拖拽 + 嵌套 IM）
- [lua-workshop-report-religion-trade.md](lua-workshop-report-religion-trade.md) — 报告/宗教/贸易面板（TabSupport 标签 + 可折叠组）

## 弹窗 + 菜单 + 样式

- [lua-workshop-popups-system.md](lua-workshop-popups-system.md) — 7 种系统弹窗全览（电影化 + 居中面板 + 队列）
- [lua-workshop-menus-overlays.md](lua-workshop-menus-overlays.md) — 暂停菜单 + 存档 + 城邦 + 世界排名 + 结束画面
- [lua-workshop-styles-reference.md](lua-workshop-styles-reference.md) — Styles + ColorAtlas 样式颜色字体速查
