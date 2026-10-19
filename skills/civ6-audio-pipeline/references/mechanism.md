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
   > 背景：给**既有 mod 首次加音频**时，P1 源工程与 P2 运行目录往往都没有音频注册——两边都要写（`register_to_mod.py` 默认双写）；该做法与"防止重建丢失"无关。
   > ⚠ 已有条目的 `.modinfo` / `.civ6proj`（以及 `Platforms/Windows/Audio/xxx_Banks.ini`）属改写：命令跑完后结果落在 `<解决方案根>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时打印待写入清单。首次注册时新建的 `.bnk` / `.wem` 属可再生二进制资产，由脚本直写。

## 4. Wwise 工程直改（免 GUI）要点

- Work unit 三类 root：Actor-Mixer 目录=`<AudioObjects>`；Events=`<Events>`；SoundBanks=`<SoundBanks>`；`SchemaVersion="70"`（Wwise 2015）。
- Sound 对象最小结构：PropertyList(可含 IsStreamingEnabled) + ReferenceList(Conversion→Default Conversion Settings `{6D1B890C-…}`；OutputBus→Master Audio Bus `{1514A4D8-…}`) + ChildrenList(AudioFileSource: `<Language>SFX</Language>` + `<AudioFile>名.wav</AudioFile>`，wav 平铺 `Originals/SFX/`) + ActiveSourceList(Platform="Linked")。
- 事件：`<Event>`>ChildrenList>`<Action Type="Play|Stop" Scope="One">`>ElementList>Element>ObjectRef(**WorkUnitID 必填**)。
- bank 挂接：`<SoundBank>`>ObjectInclusionList>`<ObjectRef … Filter="7" Origin="Manual"/>`。
- ShortID 可预填任意唯一值（模板作者手调 id 先例）；媒体 ID 由转换器按路径哈希自动分配，缺省即可。
- 生成：`WwiseCLI.exe <proj>.wproj -GenerateSoundBanks -Platform Windows -Bank <名>`；流式 wem 由 CopyStreamedFiles 后置步自动归位。

### 4.1 交互音乐（IMH）对象（媒体替换式重建要点）

- 段落块必备子块：`MusicSegment`(PropertyList: EndPosition) > `MusicTrack`(IsStreamingEnabled=True) > `AudioFileSource`
  (`<Language>SFX</Language>` + `<AudioFile>名.wav</AudioFile>` + `<ConvertedFileIDList><File ID="…"/></ConvertedFileIDList>`)
  + `MusicTransition`(Root) + `MusicTrackSequence` > `MusicClip`(EndTrimOffset/FadeIn/FadeOut) + `CueList`(Entry Cue / Exit Cue / **ExitCustom**)。
  **以模板段为原型克隆**最稳：从零手写极易漏子块。
- `<AudioSourceRef>` 引用**同段 `AudioFileSource` 的 GUID**（不是 ShortID）。
- `ConvertedFileIDList/<File ID>` 决定生成产物 `<ID>.wem` 的文件名（写死即固定该 ID；缺省则由转换器分配）。ID 从注册表避让。
- 播放列表容器：`GridFrequencyPreset=52` + 根播放项 `LoopCount=0`/`PlayMode`（Civ 轮播=3、Leader=1）+ 叶子项
  `PlaylistItemType=1` + `Weight`（Real64，`<Value>` 不带 Platform 属性）+ `SegmentRef`。
- 开关容器：`ArgumentList` 引 `Game_Location`(`{33A22C91-…}`)，`EntryList` 四个时代路径
  `Ancient_Era / Medieval_Era / Industrial_era / Modern_Era`，各指到对应时代的播放列表/段落；跨容器复用段落必须**全独立 GUID 副本**。

## 5. 触发端三通道

| 通道 | 写法 | 备注 |
|---|---|---|
| Lua(UI 上下文) | `UI.PlaySound('Play_X')` / 停止=`UI.PlaySound('Stop_X')` | **无 UI.StopSound**；api.sqlite 中 PlaySound/LoadSoundBankGroup/SetSoundSwitchValue/EnqueueNotificationSound 等全部 availability='UI' |
| 数据库列填事件名 | `UnitCommands.Sound` `UnitOperations.Sound` `Buildings.QuoteAudio` `TechnologyQuotes/CivicQuotes/LeaderQuotes/Features.QuoteAudio` `GreatWorks.Audio` `TurnSegments.Sound` `RandomEvent_Presentation.Sound` | GreatWorks.Audio 引擎自动加 `Play_` 前缀；其余为原样事件名 |
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
- **外交背景音乐响度**：目标 **-25 LUFS**（与后世 BGM 同档），靠**素材自身响度**达成，`LeaderMusic_<Civ>` 容器**不写 `Volume` 属性**。教程模板在容器上带 -8 dB 偏移，照抄会让外交界面比正常游玩明显偏轻（本地双先例实测外交曲 -25.0 LUFS 且容器无 Volume 属性）；`audio_normalize.py --category diplo` 与 `audio_check.py --category diplo` 即按此档。
- 引擎只发送四个时代信号，文艺复兴没有独立信号，与中古同属 `MEDIEVAL_ERA`。
- **引擎侧接线**：Wwise 侧交付后，新文明还须在 `CivilizationAudioTags` 与 `ArtDefs/Civilizations.artdef` 各写一处（有自制 BGM 写 `MusicOverride=1` + 空 `Audio`；无自制 BGM 不写该表 + `Audio/Entry/XrefName` 填借用的原版文明名），并同步 `*.Art.xml`——判定与写法见 `civ6-modding` skill 的 `reference/civ-metadata.md` §六。

### 6.1a 领袖语音的停止路径（实证）

- **全局停止是一条 ActorMixer 寻址的动作**：官方 `Speech.bnk` 内的 `Stop_Leader_Speech`（事件 ShortID **1239530600**）只含一条 `CAkActionStop`（`ulActionType 258 = Stop_E`），目标 `idExt` = **854467727**。游戏在结束领袖语音时播放这一个事件，引擎按该 ShortID 在 Actor-Mixer 树上找目标。
- **语音 Sound 必须挂在该 ActorMixer 之下**，停止才会命中：正确层级为
  `id88602518 > id854467727 > id424381547 > <Speech容器> > <Sound>`。
  把语音 Sound 放进一个自建的扁平 SFX Folder（输出总线 Master Audio Bus）时，它不在 854467727 子树内，全局停止落空——**表现为语音一句叠一句、永远停不下来**。
- **语音 bank 自身不含 Stop_ 事件**：权威先例 `Ragunna_Pack_Speech.bnk` 的 42 条事件全部是 Play，停止完全由上述全局动作承担。所以「照抄先例却删掉自己的 Stop_ 事件」不会修好停止——路由没动，症状照旧。
- `id88602518` / `id854467727` 自带 `MaxSoundPerInstance=1` + `UseMaxSoundPerInstance=True`，新一句自动切掉上一句；二者是模板手调对象，**一个字节不碰**，只在其下增量挂入新的 Speech 容器（与模板自带的 `JasperKittySpeech` 同级）。
- 该层级可用编译产物直接验收：`python scripts/audio_check.py --bank-hierarchy <bank.bnk> --voice-chain`。

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

  > ⚠ **数值口径以 `SKILL.md` §1.5「用户定案」为准**（那里写「其余曲目（含延续曲）各 10」）；本节为教程原文口径（「平分」）。延续曲目数量可变时两者会给出不同的实际概率分布。
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

## 8. 已知坑位（注册流程）

- **UpdateAudio 语义污染（已修+防呆）**：早期 `register_to_mod.py` 的 Files 条目锚点误匹配 UpdateAudio 块内自带 `<File>...ini</File>` 行，把 wem/bnk 条目塞进 `<UpdateAudio>` 内部。XML 良构校验通过、但游戏读 bank 时发现指向非 ini → bank 不加载 → 按钮静音（其他游戏声音正常）。**特征**：`<UpdateAudio>` 内出现 `<File>*.wem</File>`。**防线**：脚本已锚定 `</Files>` 插入 + 写后语义校验（UpdateAudio 只指向 .ini）+ 独立 `--verify` 命令（每次交付前跑，期望 PASS）。
- **媒体 ID 重建漂移**：重建 work unit 后流式媒体 ID 会重新分配，旧 wem 成孤儿。注册后必须清理运行目录中不被当前 bank xml 引用的 `\d+.wem`，并同步清理 modinfo Files 条目。
- **事件名=前缀+基名+组合码**：组合式 bank 的 `--event-base` 必须与触发端拼接前缀一致（如 `Play_`+`<基名前缀>`+`<组合码>`），漏基名会导致事件对不上、静默无声。
- **媒体 ID 重建后 `--prune` 的两遍顺序**：① 不带 `--prune` 拷媒体（`.bnk`/`.wem` 直写、侧车入位 `workspace/gen`）→ ② AI 落位侧车 → ③ 再带 `--prune` 清孤儿。`--prune` 以**磁盘上 bank xml 的引用**为孤儿判据，侧车未落位时会误判。

## 9. ShortID 规律与纯 Python 打包（历史经验）

**本质：Civ6 音频全部对象都挂在 WWise 的 32 位 ShortID 全局表上。“直接导入冲突/覆盖” = ShortID 撞车。**

### 9.1 Event 的 ShortID 由名字决定

- Event ShortID = **FNV-1(32)** 对“小写 UTF-8 事件名”的哈希。
- 例：某成品事件名 `XX_SS_FIRST_MEET_A -> 2650607710`（演示值），与对应成品 mod 完全一致（本机 8/8 抽样验证）。
- 游戏触发时按事件名重新哈希，**名字全局唯一即共存**。唯一标记要放在"引擎不会改写的那一段"：
  引擎按类别前缀拼接名字（文明音乐事件 `<动作>_Music_<CIV 内部名去 CIVILIZATION_>`、领袖派生名 `LEADER_<X>_<后缀>`），
  所以文明/领袖的内部名要自带作者码——**前缀剥离法**：剥离引擎前缀后剩下的主体仍全局唯一（唯一码是这种"自带"的做法，
  不是某个固定字面量）。自定名（语音事件等）没有引擎前缀，整名唯一即可（先例 `<CIV>_<领袖>_<场景>_<字母>`）。见 SKILL.md §2。
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
- 瘦身模板 `assets/template_slim/template_speech.bnk` 是**纯结构模板**（瘦身模板 + 静音占位生成，无成品音频），仅用于研究；
  该目录属第三方派生内容，**不随公开仓库分发**（本地保留，缺失时跑 `scripts/ensure_template.py`）。
