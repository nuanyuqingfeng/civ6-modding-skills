# HTML 设计与精确纹理导出

## 先分解页面

从目标页面列出每一块的职责，而不是先画完整截图再想办法切片：

| 内容 | 导出方式 | 游戏内实现 |
|---|---|---|
| 固定舞台、边框、纹样 | 不含动态文字的 PNG | Image / Grid |
| 立绘、头像、装饰 | 独立透明 PNG，明确裁切框 | Image，保留独立大小和位置 |
| 可伸缩按钮 | 四态竖排 PNG，保护边角 | GridButton + GridData |
| 不可拉伸的异形按钮 | 固定单帧尺寸的四态 PNG | Button |
| 标题、数值、说明、价格 | 不烘焙进 PNG | Label + LOC/Lua |
| 进度、选中、可用性 | 底框可导出，状态不烘焙 | Bar/Meter、独立选择框、SetDisabled |

可用用户已有原始素材，但先看尺寸、透明区域和实际内容。`图片-*` 等处理目录也可能是有效源；已裁切的 PNG 不必反复重制。保留素材来源与转换记录，不把用户原项目素材打包进公共技能。

为每张纹理确定资源名、宽高、帧数、单帧宽高、SliceCorner 和用途。资源名前缀使用项目命名空间，例如 `UI_MYMOD_BUTTON_GOLD`；不要复用示例的 DEMO 前缀到正式项目。

## HTML 要求

- 源文件可包含用于讨论的多页导航和状态选择器，但导出模式必须隐藏这些辅助 UI。
- 可导出的根节点为 `#texture`，左上角精确位于 `(0,0)`，固定整数像素宽高；html/body 无默认 margin、缩放和滚动条，背景透明。阴影/发光超出根边界会被裁掉，需在尺寸预算中预留透明边距。
- 默认一个 CSS 像素对应一个 PNG 像素，DPR=1。不用响应式断点、viewport 单位或浏览器缩放决定导出尺寸。预览容器可以缩放，但不要把 transform 留在导出根或祖先上。
- 当前导出器以 `file://` 打开本地 HTML；相对图片、CSS 和普通 script 可直接引用。不要依赖 `fetch()` 读取本地 JSON、需要 HTTP 的 ES 模块或开发服务器，把配置嵌入页面/普通脚本，或先生成自包含静态页面。
- 用本地素材、CSS/SVG 和固定的渐变/纹样构图；字体也优先本地。固定随机种子、冻结动画、移除当前时间等不稳定输入。
- 等待字体与图片解码，不用固定睡眠“猜加载完成”。`img.decode()` 会暴露缺失素材；CSS background-image 和 canvas/WebGL 的异步依赖由 `renderTexture` 自己等待。远程资源需下载并保存为项目依赖，避免离线重建缺图。
- 预览可以显示模拟标题/数值，以检查排版；导出四态按钮只导出皮肤。静态品牌字样确有艺术需求时可单独导出，游戏语义/本地化文本仍是 Label。

## 渲染契约

[示例 HTML](../assets/starter/index.html) 实现以下接口：

```javascript
window.textureSpecs = {
  UI_MYMOD_PANEL: [640, 400],
  UI_MYMOD_BUTTON: [256, 192], // 4 × 48
  UI_MYMOD_SELECTED: [264, 356]
};
window.renderTexture = async function (name) {
  // 切换为纯纹理模式，设置 #texture 的精确宽高并生成该纹理 DOM。
  await document.fonts.ready;
  await Promise.all([...document.images].map(image => image.decode()));
  // 如有 CSS 背景、canvas 或额外加载任务，必须在这里等待它们。
};
```

`textureSpecs` 是非空对象，名称满足 `UI_[A-Za-z0-9_]+`，忽略大小写后唯一；宽高为 1～8192 的整数，与当前 ModTools 独立纹理通道一致。四态图总高必须是单帧高的四倍。当前非压缩 RGBA 通道没有“必须是 2 的幂”约束；以后改用块压缩格式时再核对相应限制。

导出脚本需要 **Node.js 22+（原生 WebSocket/fetch）** 和本机 Edge/Chromium。优先使用可用的本地运行时，无需 npm 包。命令中的路径替换为本机真实路径；Node 不在 PATH 时使用其绝对路径。

```powershell
node "$skillDir/scripts/render-textures.cjs" --html "$designDir/index.html" --out "$designDir/textures" --browser "$browserExe"
# 确认目标确为上次导出目录后，重新生成：
node "$skillDir/scripts/render-textures.cjs" --html "$designDir/index.html" --out "$designDir/textures" --browser "$browserExe" --replace
python "$skillDir/scripts/verify-textures.py" --manifest "$designDir/textures/texture_manifest.json" --png-dir "$designDir/textures"
```

输出为 `<name>.png` 和 `texture_manifest.json`。脚本只负责纹理导出，不会编译 XML、写 CIV、抓取外部网站或运行 Mod。它启动独立隐藏的无头浏览器和临时 profile，使用 CDP 设置透明底与 DPR，等待页面接口，检查精确边界，最后关闭自己的进程。不会连接/关闭用户正在使用的浏览器。

默认拒绝覆盖已有产物；`--replace` 只允许覆盖本次清单列出的文件及清单，不会删除旧的无关图片。图片先在本次私有临时目录中渲染，全部渲染成功后才更新目标 PNG，清单最后写入。缺图、脚本异常或尺寸错误不会替换上次导出的部分图片；若发生最终写盘错误，仍须以非零退出状态处理，不把旧清单当作本次成功证据。

## 导出后的视觉验收

查看实际生成 PNG，而不是只看 HTML。透明图用棋盘、黑底和白底各检查边缘；四态图逐帧看状态差异，尤其 Down 的位移、Disabled 的对比度和边角是否串帧。可用 Pillow 制作接触表用于检查，设计本身仍在 HTML/CSS 修改。

整页截图需用 `getBoundingClientRect()` 测量目标区域，不能猜导航栏占了多少像素。示例页可直接在浏览器打开，用状态选项检查按钮、卡片选择、长文本与禁用逻辑。复杂原型应按真实点击路径检查，不能仅切换 CSS 类就声称交互已通过。

HTML 字体、字距、模糊和滚动条与游戏控件不完全相同。因此最终文字区保留余量，并用游戏截图校正字号、WrapWidth、按钮高度和滚动范围。不要承诺网页截图与引擎文字逐像素一致。
