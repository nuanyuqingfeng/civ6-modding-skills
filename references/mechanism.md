# Civ6 音频机制速查（本机实证版）

> 结论来源：官方本体文件 + 工坊 127 mod 全量扫描 + 多个本地 mod 先例（含 .civ6proj 与 .modinfo 双路线）+ 实战交付。写码前先读「铁律」。

## 1. 官方音频体系

- 位置：`Base/Platforms/Windows/audio/`（小写 audio）
- `Banks.ini` 决定加载时机：`[Global]`(常驻) `[Menu]`(主菜单) `[InGame]`(对局) `[2D]` `[3D]` `[FMV]`
- 每个 bank 三件套：`.bnk` + 同名 `.xml`(Wwise SoundBanksInfo) + `.txt`(人读事件表)
- 流式媒体：数字 ID 命名 `.wem`，平铺在 bank 旁
- 语言夹（`Chinese(PRC)/` 等）= 本地化语音 per-language bank
- `Init.bnk` 是 Wwise 工程初始化（总线/游戏同步），**mod 不携带**

## 2. 版本指纹

| 指纹 | 值 | 说明 |
|---|---|---|
| SoundBanksInfo `SoundbankVersion` | **113** | 官方与 mod 一致（Wwise 2015.1.x） |
| BKHD 布局版本 | 官方=20；Wwise 2015.1.9 产物=**24** | 引擎兼容两者；本地先例 mod 用 24 实测可用 |
| 评估版许可 | 每 bank ≤ **200** 媒体项 | 大批量拆 bank |

## 3. Mod 注册三件套（缺一不可）

1. **Soundbanks ini**（`Platforms/Windows/Audio/xxx_Banks.ini`，无 BOM/CRLF/ASCII）：与官方 Banks.ini 同构 6 节，列 bank 文件名。
2. **`.modinfo`**：`<InGameActions>` 内 `<UpdateAudio id="X"><File>Platforms/Windows/Audio/xxx.ini</File></UpdateAudio>`；变体可同时列 .bnk/.xml；`<Files>` 打包清单补条目。
3. **`.civ6proj`**（ModBuddy 源工程）：`InGameActionData` CDATA 内单行 `<UpdateAudio id="X"><File>Platforms/Windows/Audio/xxx.ini</File></UpdateAudio>`（正斜杠）+ MSBuild 条目
   `    <Content Include="Platforms\Windows\Audio\x.wem">` + `      <SubType>Content</SubType>`（反斜杠）。
   实证先例：本地某领袖 mod 源工程 .civ6proj（CDATA 单行 UpdateAudio + Content 条目）。
   > 背景：给**既有 mod 首次加音频**时，P1 源工程与 P2 运行目录往往都没有音频注册——两边都要写（`register_to_mod.py` 默认双写），并非"防止重建丢失"。

## 4. Wwise 工程直改（免 GUI）要点

- Work unit 三类 root：Actor-Mixer 目录=`<AudioObjects>`；Events=`<Events>`；SoundBanks=`<SoundBanks>`；`SchemaVersion="70"`（Wwise 2015）。
- Sound 对象最小结构：PropertyList(可含 IsStreamingEnabled) + ReferenceList(Conversion→Default Conversion Settings `{6D1B890C-…}`；OutputBus→Master Audio Bus `{1514A4D8-…}`) + ChildrenList(AudioFileSource: `<Language>SFX</Language>` + `<AudioFile>名.wav</AudioFile>`，wav 平铺 `Originals/SFX/`) + ActiveSourceList(Platform="Linked")。
- 事件：`<Event>`>ChildrenList>`<Action Type="Play|Stop" Scope="One">`>ElementList>Element>ObjectRef(**WorkUnitID 必填**)。
- bank 挂接：`<SoundBank>`>ObjectInclusionList>`<ObjectRef … Filter="7" Origin="Manual"/>`。
- ShortID 可预填任意唯一值（模板作者手调 id 先例）；媒体 ID 由转换器按路径哈希自动分配，缺省即可。
- 生成：`WwiseCLI.exe <proj>.wproj -GenerateSoundBanks -Platform Windows -Bank <名>`；流式 wem 由 CopyStreamedFiles 后置步自动归位。

## 5. 触发端三通道

| 通道 | 写法 | 备注 |
|---|---|---|
| Lua(UI 上下文) | `UI.PlaySound('Play_X')` / 停止=`UI.PlaySound('Stop_X')` | **无 UI.StopSound**；api.sqlite 中 PlaySound/LoadSoundBankGroup/SetSoundSwitchValue/EnqueueNotificationSound 等全部 availability='UI' |
| 数据库列填事件名 | `UnitCommands.Sound` `UnitOperations.Sound` `Buildings.QuoteAudio` `TechnologyQuotes/CivicQuotes/LeaderQuotes/Features.QuoteAudio` `GreatWorks.Audio` `TurnSegments.Sound` `RandomEvent_Presentation.Sound` `LoadingInfo.PlayDawnOfManAudio` | GreatWorks.Audio 引擎自动加 `Play_` 前缀；其余为原样事件名 |
| artdef | Audio 集合(3D 位置音)；领袖语音=时间线 Sound 事件+动画 Duration | 教程 11 章尾部流程 |

## 6. 音乐/语音专项（教程 11 章核心）

- BGM 预处理：-28 LUFS(远古)/-25(后世)、48kHz 立体声 WAV、开 Stream、交互音乐时间线加 **ExitCustom** 自定义时间戳（缺它播完不再放任何音乐）。
- 语音预处理：-21 LUFS、单声道；语言本地化=语言夹同名 bank。
- 引擎只向 Wwise 发远古/中古/工业/原子四个时代信号，增设时代点无效；游戏同步在官方 `Init.bnk`，**绝不自制 Init**。

### 6.1 BGM 内部三组结构

文明音乐（BGM）按原版教程分为三组：

| 分组 | 用途 | Wwise 容器 | 事件 |
|---|---|---|---|
| 轮播背景音乐 | 正常游玩时随机/按权重轮播 | `CivilizationMusic_<Civ>` | `Play_Music_<Civ>` |
| 外交背景音乐 | 进入领袖外交界面时播放 | `LeaderMusic_<Civ>` | `Play_Leader_Music_<Civ>` |
| 主题音乐 | 每次载入游戏先播放当前时代主题曲 | `ThemeMusic_<Civ>` | `Start_Music_<Civ>` |

- 主题音乐建议按 4 个时代准备：远古 / 中古 / 工业 / 原子。
- 外交背景音乐采用官方标准做法：**一个文明对应一首外交背景音乐**，由 `LeaderMusic_<Civ>` 容器与 `Play_Leader_Music_<Civ>` 事件承载。
- 引擎只发送四个时代信号，文艺复兴没有独立信号，与中古同属 `MEDIEVAL_ERA`。

### 6.2 轮播机制与权重机制（区分）

- **轮播机制（composition）**：决定哪些音乐对象进入各时代 `CivilizationMusic_<Civ>` 播放列表。
  - Ancient：远古主题曲 + 全部本时代轮播音乐。
  - Medieval：中古主题曲 + 远古主题曲 + 远古轮播音乐热度前 50%。
  - Industrial：工业主题曲 + 中古主题曲 + 中古轮播音乐热度前 50%。
  - Atomic：原子主题曲 + 工业主题曲 + 工业轮播音乐热度前 50%。
  - 只跨一次时代：远古音乐不进入 Industrial/Atomic；中古音乐不进入 Atomic。
  - 热度前 50% 不足时，从该时代剩余轮播音乐随机补足。
- **权重机制（weights）**：决定同一时代播放列表内部曲目概率。
  - Ancient：全部 50。
  - Medieval：中古主题曲 50，其余曲目平分剩下 50。
  - Industrial：工业主题曲 60，中古主题曲及其带入曲目平分剩下 40。
  - Atomic：原子主题曲 60，工业主题曲及其带入曲目平分剩下 40。
- 两者独立：先按轮播机制确定列表成员，再按权重机制分配概率。

## 7. 先例索引

| 先例 | 学什么 |
|---|---|
| 工坊 2919148848 Raiden | SFX Lua 触发 + 音乐 Play/Stop 对 + 语音语言夹 |
| 工坊 2599959500 Liyue | 独立 UI 音效 bank |
| 工坊 2962169627 JadeChamber | 奇观台词走 Buildings.QuoteAudio（语言夹 bank 闭环） |
| 本地某领袖+伟人 mod | .civ6proj 注册 + GreatWorks.Audio + 伟人音 Lua 触发 |
| 本地某多领袖 mod 包 | .modinfo 注册 + MediaStop 统一媒体协调器（Play_→Stop_ 转换停止） |

## 8. 已知坑位（注册链路）

- **UpdateAudio 语义污染（已修+防呆）**：早期 `register_to_mod.py` 的 Files 条目锚点误匹配 UpdateAudio 块内自带 `<File>...ini</File>` 行，把 wem/bnk 条目塞进 `<UpdateAudio>` 内部。XML 良构校验通过、但游戏读 bank 时发现指向非 ini → bank 不加载 → 按钮静音（其他游戏声音正常）。**特征**：`<UpdateAudio>` 内出现 `<File>*.wem</File>`。**防线**：脚本已锚定 `</Files>` 插入 + 写后语义校验（UpdateAudio 只指向 .ini）+ 独立 `--verify` 命令（每次交付前跑，期望 PASS）。
- **媒体 ID 重建漂移**：重建 work unit 后流式媒体 ID 会重新分配，旧 wem 成孤儿。注册后必须清理运行目录中不被当前 bank xml 引用的 `\d+.wem`，并同步清理 modinfo Files 条目。
- **事件名=前缀+基名+组合码**：组合式 bank 的 `--event-base` 必须与触发端拼接前缀一致（如 `Play_`+`<基名前缀>`+`<组合码>`），漏基名会导致事件对不上、静默无声。

## 9. ShortID 规律与纯 Python 打包（历史经验）

**本质：Civ6 音频全部对象都挂在 WWise 的 32 位 ShortID 全局表上。“直接导入冲突/覆盖” = ShortID 撞车。**

### 9.1 Event 的 ShortID 由名字决定

- Event ShortID = **FNV-1(32)** 对“小写 UTF-8 事件名”的哈希。
- 例：某成品事件名 `XX_SS_FIRST_MEET_A -> 2650607710`（演示值），与对应成品 mod 完全一致（本机 8/8 抽样验证）。
- 游戏触发时按事件名重新哈希，所以**领袖/音频事件必须用唯一前缀**：前缀不同 → 名字不同 → ID 不同 → 共存。
- 反之，两个领袖若同名，后加载者的 Event ID 会覆盖先加载者。

### 9.2 其余 ID 是随机数，不同内容必须全域唯一

- Media / Sound / Action / Container / Bank 的 ShortID 是工程随机分配，不是由名字决定。
- 两份**不同内容**若落入相同数值 ID → 引擎全局表互相覆盖（“一个人物语音顶掉另一个人物”的根源）。
- 完全相同的内容共用同一 ID 是安全的（可去重）。
- 因此新增音频时，这些 ID 应从 `id_registry.json` 中**避让分配**并写入注册表。

### 9.3 锚点固定，禁止改号

- 语音容器链：`id88602518 -> id854467727 -> id424381547`；
- 配乐的 DummySwitches 等 `id\d+` 游戏同步对象；
- `Init.bnk` 承载时代等游戏同步，**绝不自制/替换**。
- `IdAllocator` 默认把三个语音锚点加入已用集合，新分配永不发放这些号。

### 9.4 纯 Python bank 字节模板重建 —— ⚠️ 仅研究，编码已废弃

- `wwise_shortid.py` 可从模板 Speech.bnk 提取 Sound/Action/Event/Anchor/Leaf 的 HIRC 字节模板，按 `BKHD + DIDX + DATA + HIRC` 重建 bank（SoundbankVersion=113）——**结构重建能力有效**，可用于 ShortID/布局研究。
- **编码已废弃（实机验证记录）**：用 ffmpeg 标准 `adpcm_ms` 内嵌进 WWise 语音模板后，游戏按 **WWise 私有 ADPCM 变体**解码（ffmpeg 无法解码，报 `block_predictor` 错），导致**噪音+闪退**；且 ADPCM 压缩率约 25%，也达不到成品音乐 7.8%（Vorbis 流式）。
- **正确做法（正式交付）**：把素材做成 **Stream（流式）→ WWise Vorbis wem**（约 8-10% 体积），建事件后由 WwiseCLI 生成 bank。语音（Speech bank）与普通音频/BGM 均如此——`audio_pack.py` 的纯 Python 产品**不得用于交付**。
- 内置模板 `assets/template_slim/template_speech.bnk` 是**纯结构模板**（瘦身模板 + 静音占位生成，无成品音频），仅用于研究。
