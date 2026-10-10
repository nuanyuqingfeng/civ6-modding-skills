# 独立接入文明6 SDK 工程

适用：不使用 ModTools，已有或准备使用文明6 ModBuddy / Asset Editor 工程。先完成 HTML 设计、PNG 导出和原生 XML/Lua 实现；本包独立脚本不编译 SDK 资源，也不写入 .CIV。

## 输入与产物

保留源 HTML、引用素材、PNG 和 texture_manifest.json。清单记录纹理名与尺寸，供脚本校验；不是游戏自动读取的注册文件。

将 assets/starter/NativePanel.xml、NativePanel.lua、texts.json 复制到自己的设计目录并改写，统一替换 DEMO 资源、LOC 和事件前缀。示例的 LuaEvents 只演示 UI 环境通信，不跨 UI / GP 传递玩法修改。

## 在自己的工程中登记

1. 用既有 SDK 纹理流程处理 PNG，保留尺寸、方向及透明通道，生成相应 DDS/TEX。四态按钮单帧尺寸与 XML Size 一致；不要让转换器自动上下翻转。
2. 将 TEX 对象加入 UITexture 类 XLP。XML Texture 使用对应 EntryID；ObjectName 对应纹理对象，Art.xml 声明该资源包及实际依赖。按官方 SDK 和项目已有结构核对，不从网页 CSS 推导字段。
3. 将同名 XML/Lua 登记为项目内容，UI 入口动作 AddUserInterfaces 引用 XML，Context 与目标屏幕一致。Lua 配对文件需打包，但不作为另一个独立 UI 入口重复加载。helper 依项目导入约定供 include 使用。
4. 将 texts.json 的 tag / text 转为目标语言 LocalizedText，由 UpdateText 加载。group 是编辑分类；该 JSON 不能直接当游戏文本数据库文件。
5. 沿用项目的前台/游戏内作用域、加载顺序和依赖。不把原项目玩法替换成示例事件；UI 读数据并提交请求，GP 检查并执行。

SDK 的标准美术源目录供 pantry / Cooker 读取，不把所有 DDS/TEX/XLP 一律当普通 Content 复制。实际打包的是对应构建产物和运行时文件；按目标 SDK 工程与构建日志核对。

## 验证

在技能文件夹中执行：

~~~powershell
python scripts/verify-textures.py --manifest "设计目录/textures/texture_manifest.json" --png-dir "设计目录/textures"
python scripts/check-native-ui.py --manifest "设计目录/textures/texture_manifest.json" --xml "设计目录/MyPanel.xml" --font-styles "游戏字体表.xml"
~~~

如果工程恰好使用下述目录契约，第一条命令可加 --project "工程目录" 校验完整链：

~~~text
工程目录/
  IMG/<纹理名>.png
  Textures/<纹理名>.dds
  Textures/<纹理名>.tex
  XLPs/*.xlp
  *.Art.xml
~~~

该检查要求 TEX 的 m_Name、DDS 相对引用、XLP 的 EntryID/ObjectName 和文件名对应。采用别名、自定义目录或其他合法 SDK 组织时，使用源 PNG 检查及 SDK 自身的引用验证，不为迎合检查器修改有效工程。

通过 SDK 构建/Cooker 后核对日志、缺失条目和本次实际产物；最终进游戏检查不同分辨率/UI 缩放、字体、四态、滚动、关闭、重复打开及玩法事件。不要将浏览器截图或 XML 语法通过等同于游戏验收。

如用户只要求设计与纹理，交付源文件、清单和验证结果即可，保留 SDK/游戏步骤为未执行。SDK 和游戏按使用者已有安装提供，不随本分享包分发。
