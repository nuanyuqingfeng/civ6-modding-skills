# 使用方式与跨 agent 分享

## 独立使用优先

进入 civ6-html-ui 文件夹，先按 [分享包说明](../README.md) 运行三条独立脚本命令；需要进入游戏时读 [SDK 工程接入](standalone-integration.md)。这些步骤不要求任何工程工具链或固定版本。

## 入口与维护来源

本目录是家族内的正式来源。无需个人安装目录、Codex API、插件或会话历史。支持 SKILL.md 的 agent 可直接加载；其他 agent 打开 SKILL.md 后按链接读取相关参考并执行普通命令即可。

只分享本能力时，复制或打包整个 `civ6-html-ui` 文件夹，保留 SKILL.md、references、scripts、assets 的相对结构。`agents/openai.yaml` 是可选显示元数据，其他平台可忽略；执行逻辑不读取它。不要只分享 SKILL.md 而遗漏脚本/示例，也不要带上生成纹理、浏览器 profile、缓存或原项目美术。

## 依赖与边界

| 操作 | 依赖 | 说明 |
|---|---|---|
| 读技能、编辑 HTML/XML/Lua | 文本编辑能力 | — |
| 运行 HTML 纹理导出 | Node.js 22+、本机 Chromium/Chrome/Edge | 直接运行 scripts/render-textures.cjs |
| 原生按钮尺寸/字体静态检查 | Python 3.10+，目标字体 XML 可选 | check-native-ui.py 只读 |
| PNG/导出链像素校验 | Python 3.10+、Pillow | 直接运行 scripts/verify-textures.py |
| 纹理登记进 `.civ6proj` 工程 | `civ6-modding` 的 art-pipeline / check_proj_content / verify_mod_package | 按 SDK 工程流程 |
| 原生 Cooker/游戏验收 | 对应平台 SDK/游戏环境 | 独立步骤 |

浏览器工具采用 Node 标准 API、参数数组和本地文件 URL，校验脚本采用 pathlib；没有用户盘符和平台私有运行时路径。Windows 隐藏子进程窗口；不会自动加 `--no-sandbox` 绕过 Chromium 限制。已实测 Windows；其他操作系统需提供可执行的 Chromium/Node 并运行示例验收，不能据此宣称 Civ6 SDK 全流程跨系统可用。

## 脚本入口

先复制 `assets/starter/` 到 Mod 的设计目录并改名资源/LOC/事件前缀。以下导出命令也可直接跑原始示例；路径相对技能文件夹：

```bash
node scripts/render-textures.cjs --html assets/starter/index.html --out /path/to/output --browser "/path/to/chromium"
python scripts/verify-textures.py --manifest /path/to/output/texture_manifest.json --png-dir /path/to/output
```

`render` 优先使用 `--node` / `--browser` 指定值，其次 `CIV6_UI_NODE` / `CIV6_UI_BROWSER`，最后查 Node/PATH 浏览器及系统常见安装路径。显式路径无效时直接报错，不静默切换。未安装依赖时按提示配置，不默认下载/安装浏览器。路径有空格时整体加引号。

清单是 `{ "UI_MYMOD_PANEL": [640, 400] }`。PNG 默认为清单同目录的 `<name>.png`，可用 `--png-dir` 指定独立目录。`render`/`verify` 成功均输出 JSON，错误返回非零状态；render 失败时不能使用旧清单当作本次成功的凭据。输出已存在时，确认要更新后给导出命令加 `--replace`。

导出的 PNG → DDS/TEX → XLP → Art.xml 登记按 [SDK 工程接入](standalone-integration.md) 与 `civ6-modding` 的 `art-pipeline.md` 执行；本包不生成 modinfo、不部署，也不将 HTML 自动翻译为原生 XML。

原生布局检查脚本（字体表路径按目标游戏语言设置）：

```bash
python scripts/check-native-ui.py --manifest /path/to/output/texture_manifest.json --xml /path/to/NativePanel.xml --font-styles "/path/to/game/Base/Assets/UI/Fonts/Civ6_FontStyles_zh_Hans_CN.xml"
```
