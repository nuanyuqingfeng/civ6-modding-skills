# 文明6 HTML 转原生 UI · 独立分享包

本包不依赖 ModTools 或其版本。支持 SKILL.md 的 AI 工具可加载整个文件夹；其他 AI 可先读取 [SKILL.md](SKILL.md)，按任务打开对应参考。保留完整目录结构即可。

能力包括 HTML/CSS 设计、精确 PNG 导出、透明装饰/四态按钮、原生 XML/Lua 布局指导及静态检查。HTML 到原生 UI 需要按控件语义实现；本包不提供通用 DOM→XML 编译器，也不自动生成完整游戏 Mod。

## 快速使用

解压并进入 civ6-html-ui 文件夹。准备 Node.js 22+、本机 Edge/Chrome/Chromium，以及 Python 3.10+；像素校验另需 Pillow（可用 python -m pip install Pillow 安装）。无需 npm install、Qt、ModTools、Codex 插件或账号。

先复制 assets/starter 到自己的设计目录再修改。以下命令直接验证随包示例，输出到当前文件夹 output：

~~~powershell
node scripts/render-textures.cjs --html assets/starter/index.html --out output --browser "浏览器可执行文件的完整路径"
python scripts/verify-textures.py --manifest output/texture_manifest.json --png-dir output
python scripts/check-native-ui.py --manifest output/texture_manifest.json --xml assets/starter/NativePanel.xml
~~~

--browser 指定浏览器程序，不是网页 URL；路径有空格须加引号。输出已存在时，确认要更新后给导出命令加 --replace。不要移动或清理正式素材源。

要检查字体，在第三条命令加 --font-styles "目标游戏的 Civ6_FontStyles_zh_Hans_CN.xml 路径"；不传字体表时不进行字体可用性验证。三条命令成功返回 0，错误返回非零。图片输出是背景 640×400、按钮 256×192（四帧各 256×48）、选择框 256×160。

## 后续接入

- 独立使用：[SDK 工程接入](references/standalone-integration.md)，通过已有 ModBuddy/Asset Editor 流程完成纹理、LOC、XML/Lua 注册，再编译和游戏验收。
- 选择 ModTools：[CIV 导入与验证](references/integration-validation.md)，命令以所用版本实际帮助为准。
- 排版和交互：[原生布局参考](references/native-ui.md)；渲染契约见 [HTML 纹理参考](references/html-textures.md)。

--project 的完整导出链检查采用包内说明的 IMG/Textures/XLPs/*.Art.xml 目录约定；不是任意 SDK 工程的通用验证器。普通独立使用先执行不带 --project 的 PNG 检查。

## 来源与分享

维护来源：ModTools 仓库 skills/civ6-html-ui。版权署名沿用项目：Copyright (c) 2026 Siqi，采用 [MIT 许可证](LICENSE)，分享和改编时保留版权与许可全文。具体项目验证经验及其适用范围保留在技能参考中。

示例是原创几何 CSS 和演示 XML/Lua；包内没有游戏素材、字体、SDK、浏览器或运行时。文明 VI、ForgeUI、ModBuddy 及官方调用点属于 Firaxis / 2K 的产品和资料，本包不改变其权利或许可。

实机呈现、字体、缩放、点击层级和玩法需在目标环境验收。Windows 独立脚本已验证；其他系统和游戏运行环境分别验证。PACKAGE.json 记录包内文件 SHA-256，便于核对分享文件完整性。
