---
name: civ6-audio-pipeline
description: "Civ6 音频全流程管线：素材整备（ncm 解密 / 音频指纹查重 / 音乐特征分析）→ 素材核验（PCM WAV/48000Hz/声道/时长/LUFS）→ 按类别响度均衡（语音-21、BGM 远古-28/后世-25、普通音频 sfx 默认-27 LUFS，ffmpeg loudnorm 双遍）→ Wwise 2015 工程直改（素材导入/事件注册/bank 挂接/批量改名，WwiseCLI 官方命令行生成，免 GUI）→ 自动定位 .civ6proj / .modinfo 完成注册（Platforms/Windows/Audio + Banks.ini + UpdateAudio + Files/Content 条目）。三类路由：普通音频(sfx)全自动；领袖语音(voice)与文明 BGM(bgm)共用教程模板工程，容器类 GUI 步骤半自动。正式音频交付统一走 Wwise Vorbis 流式（纯 Python ADPCM 已被实证废弃，仅保留 ShortID/ID 注册表机制作研究）。触发词：音频导入、声音库、bank、响度均衡、wwise、语音、BGM、普通音频、Soundbanks、ncm 解密、网易云、素材查重、素材整备、音乐特征、ShortID、Vorbis、流式音频、id_registry"
version: "1.3"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - audio
  - wwise
  - soundbank
  - modding
---

> 🧰 **工具先查名录（硬性）**：要写脚本做某件事之前，先看本 skill 的 [`TOOLS.md`](TOOLS.md)
> —— 本 skill 全部脚本的用途 / 用法 / 路径清单，外加本机**路径收纳**表。
> **有能用的就改它，不要重建。** 新增或改名脚本后，跑一次
> `python "<skills>/civ6-modding/tools/skill_manifest.py" civ6-audio-pipeline` 刷新名录（`--check` 可做漂移检测）。

# Civ6 音频管线（civ6-audio-pipeline）

从素材到游戏内发声的全自动/半自动管线。（证据清单见 `references/mechanism.md` §7），机制细节见 `references/mechanism.md`，工作史与关键决策记录见 `references/history.md`，动手前先扫一遍"铁律"。

## 0. 环境与路径（默认值，可被 skill 目录 `local_paths.json` 覆盖）

| 项 | 路径 | 说明 |
|---|---|---|
| WwiseCLI | `E:\SoftWares\Wwise_v2015.1.9\Authoring\x64\Release\bin\WwiseCLI.exe` | 官方命令行生成器，与 GUI Shift+F7 同引擎 |
| 模板工程(内置) | `<skill>\assets\template_slim\FelineJasperKitty` | 结构化瘦身版 0.6MB（空 Originals 壳）；脚本默认 |
| 模板工程(完整) | `<上游教程仓库本地副本>\WWiseProject\FelineJasperKitty` | 含 301MB 媒体；GUI 里做 voice/bgm 容器工作时复制这份 |
| 教程 | `<skill>\assets\tutorial11\11音频.md`（已内化） | 领袖/BGM 的 GUI 步骤权威依据 |
| P1 源工程 | `D:\documents\Firaxis ModBuddy\Civilization VI` | `.civ6proj` 注册对象 |
| P2 运行目录 | `D:\documents\My Games\Sid Meier's Civilization VI\Mods` | `.modinfo` 注册对象 |
| ffmpeg/ffprobe | PATH 内 | 核验与响度均衡依赖 |

> `local_paths.json` 是本机私有配置（键：`wwcli` / `template_full` / `p1` / `p2`），分享 skill 前请删除；也可用 `CIV6_WWCLI`、`CIV6_TEMPLATE_FULL`、`CIV6_P1`、`CIV6_P2` 环境变量临时覆盖。

> **编码自适应（无需 `PYTHONUTF8=1`）**：`audio_check.py` / `audio_normalize.py` / `new_bank_project.py` / `wwise_wire.py` 已内置 UTF-8 子进程解码，并在输出重定向（管道/采集）时自动切 UTF-8 标准输出；

**铁律（违反即返工）：**
1. **直改工程文件前 Wwise 必须关闭**——GUI 内存态一旦保存会覆盖直改结果。
2. 只做**增量插入**与按 GUID 的 Name 更新；模板内 `id88602518` 等手调对象一个字节不碰。
3. bank 必须 Wwise 2015.1 编译（SoundbankVersion=113 / BKHD 布局 ver 24，与本地先例 mod 一致；官方原版 ver 20，引擎兼容两者）。禁止用新版 Wwise 迁移工程。
4. 评估版许可**每 bank ≤200 媒体项**，大批量拆 bank。
5. 事件引用全走 GUID；改名=只改 Name（引擎按 GUID 解析）。
6. ini 写盘：无 BOM、CRLF、ASCII；modinfo/civ6proj：保持原编码与换行。
7. **注册校对**：所有物理文件（含 ini）必须出现在 `.modinfo` 的 `<Files>` 节 / `.civ6proj` 的 `<Content>` 清单；ini 除此之外还必须单独出现在 `<UpdateAudio>` 加载动作。交付前 `register_to_mod.py --verify` 必须 PASS（自动核对 UpdateAudio→ini、磁盘↔清单一致）。

## 1. 三类路由（用户提供分类后先走此表）

| 类别 | Wwise 载体 | 全自动范围 | 必须人工(GUI)的步骤 |
|---|---|---|---|
| **sfx 普通音频**（UI音/单位音/环境音/台词单发） | 克隆模板→**新建独立 bank**（ActorMixer+Event+Bank 三个 work unit 直改） | 全流程：核验→均衡→导入→事件→生成→注册 | 无（触发端 Lua/DB 由后续接线需求决定） |
| **voice 领袖语音** | 教程模板的 Speech 工作单元（语言夹本地化） | 核验→均衡(-21LUFS/单声道)→导入→事件改名与注册→生成→注册 | 教程 11 章：动画时间线 Sound 事件填写 + 动画 Duration 调整（素材编辑器 Timeline Editor） |
| **bgm 文明音乐** | 教程模板的 Interactive Music（时代容器/权重） | 核验→均衡(-28/-25LUFS/立体声/流式)→媒体替换→事件→生成→注册 | 教程 11 章：交互音乐布局里 ExitCustom 自定义时间戳、时代选曲权重、主题音乐时代配置 |

> BGM/voice 的"人工步骤"在 GUI 里做完并保存后，回到本管线继续（事件/bank/注册仍由脚本完成）。

**分类决策规则**：用户先声明哪些是 voice / bgm / quote（台词类：伟人行动音、著作朗读、奇观语录）；**未声明的素材若时长 ≥60s → 疑似 BGM，必须询问用户后再归类**；否则一律按 sfx 处理（audio_check 会对 ≥60s 未分类文件打印 [需询问] 提示）。

## 1.5 BGM 内部三组结构与主动询问流程

文明音乐（BGM）按教程分为三组：

1. **轮播背景音乐**：正常游玩时随机/按权重轮播的背景音乐。
2. **外交背景音乐**：进入领袖外交界面时播放；按官方做法，**一个文明对应一首外交背景音乐**（`LeaderMusic_<Civ>` / `Play_Leader_Music_<Civ>`）。
3. **主题音乐**：每次载入游戏时先播放当前时代的主题曲；建议按 4 个时代准备（远古/中古/工业/原子）。

### BGM 素材分类引导（skill 触发时必须执行）

BGM 制作触发时必须主动引导分类：

1. 先扫描用户提供的素材目录/文件。
2. 按文件名/子目录预分类：
   - 文件名含 `Theme` / `主题` → 主题音乐；
   - 文件名含 `Diplo` / `外交` / `Leader` → 外交背景音乐；
   - 其余 → 默认归为轮播背景音乐。
3. 主动向用户确认：
   - “请确认哪些是主题音乐？”
   - “请确认哪些是外交背景音乐？”
   - “其余将默认为轮播背景音乐。”
4. 主动询问时代粒度：
   - “主题音乐是否按 4 个时代准备？”
5. 将分类结果记录为 assignment/manifest，后续脚本按此处理。

### 轮播机制 ≠ 权重机制（必读区分）

- **轮播机制**：决定“哪些音乐对象进入哪个时代的 `CivilizationMusic` 播放列表”。权威解释（教程原文 + 用户定案）——每个时代容器 = **本时代主题曲 1 首 + 本时代全部轮播音乐 + 上一时代主题曲 + 上一时代轮播音乐的一半**：
  - Ancient：远古主题曲 + 全部远古轮播音乐（首个时代，无上一时代可延续）。
  - Medieval：中古主题曲 + 全部中古轮播音乐 + 远古主题曲 + 一半远古轮播音乐。
  - Industrial：工业主题曲 + 全部工业轮播音乐 + 中古主题曲 + 一半中古轮播音乐。
  - Atomic：原子主题曲 + 全部原子轮播音乐 + 工业主题曲 + 一半工业轮播音乐。
  - Atomic 是最后一个时代容器，其轮播音乐不再向后续延续。
  - 教程原文的“一半（取你更喜欢的一半即可）”指**上一时代轮播音乐的一半**；热度排序只是可选的筛选细节，不是固化规则。
- **权重机制**：决定“同一时代播放列表内部各曲目的相对权重”：
  - Ancient：主题曲与轮播音乐等权。
  - Medieval：中古主题曲 50，其余曲目（含延续曲）各 10。
  - Industrial / Atomic：本时代主题曲 60，其余曲目（含延续曲）各 10。
- ⚠️ **共享禁忌**：同一 `MusicSegment` 严禁在多个容器下以相同 GUID 声明——Wwise 只承认第一个父级，其余容器引用该段的播放项会被**静默丢弃**（实机复核）。跨容器复用必须生成全独立 GUID 副本（segment/track/AudioFileSource/clip/cue 全新）。

## 2. 预命名规范（用户整理素材时约定，脚本按此路由）

- 文件名 = 事件名主体（去扩展名），**只用 ASCII 字母数字下划线**。
- sfx：`<前缀>_SFX_<用途>_<序号>.wav` 或任意稳定名；事件自动生成 `Play_<名>` / `Stop_<名>` 成对。
- voice：按教程惯例 `<前缀>_<场景>`（如 `FELI_JK_FIRST_MEET_A`）；同名事件改名由 `wwise_wire.py --rename-event` 批量完成。
- bgm（文明音乐）按三组命名：
  - 轮播背景音乐：`<CIV>_<时代>_Ambient<序号>.wav`（如 `Feline_Ancient_Ambient1`）；
  - 外交背景音乐：`<CIV>_Diplo.wav`（一个文明一首，如 `RAGUNNA_Diplo.wav`）；
  - 主题音乐：`<CIV>_<时代>_Theme.wav`（如 `Feline_Medieval_Theme.wav`）。
  - 事件沿用模板 `Play_Music_<CIV>` / `Play_Leader_Music_<CIV>` 等既有命名。
- **素材池阶段豁免**：查重/分区/响度整备阶段保留原始曲名（用户需辨认曲目）并输出 assignment 清单；进入 ③ 导入 Wwise 前才改上述规范名。
- 单文件 ≥30s 默认流式（Stream），短音效默认内存驻留；可用 `--streaming/--nostream` 覆盖。

## 2.5 响度策略（校准基准 + 组内相对均衡）

- **绝对响度**：（`references/calibration.json`）：voice **-21** / quote **-23.5** / BGM 远古 **-28** / BGM 后世 **-25** / **sfx 普通音频默认 -27** LUFS（乐队多轨叠加实测确认，接近远古 BGM -28 且多轨并播整体更平衡）。已知替代风格：BS 系热母带（BGM ≈ -12，已入游戏验证），沿用该家族风格时用 `--i` 覆盖。
- **BGM 时代响度分配（2026-09 用户定案）**：`-28`/`-25` 按**素材所属时代**分，不按播放时代分——远古时代素材**全部 -28**（远古主题曲即贯穿全局的主题曲，后续时代容器复用时保持 -28，**无需另做 -25 副本**）；中世纪及之后时代的素材**全部 -25**（含各自主题曲）。轮播曲跨时代复用只体现在 Wwise 容器权重配置，不改变文件响度。
- **⚠ 同一播放容器内严禁混排两档基准**：上一条是**文件层**的规则；而轮播机制（§1.5）会把**本时代素材 + 上一时代素材**塞进同一个时代容器，-28 与 -25 一旦同容器就是**逐曲跳 3 dB 台阶**（听感：忽大忽小）。定案：**同一容器（同一时代列表）内所有曲目必须落在同一基准上**——沿用 -28/-25 时代分配时，跨时代复用进同一容器的素材也要归到该容器的基准。验收靠 `audio_check.py` 的 `[POOL]` 段，它会直接点出"疑似双基准混排 + 两簇中心与间隔"（实机教训：某 BGM 包 97 首被判出 低簇 n=24 中心 -28.00 / 高簇 n=73 中心 -25.00 / 间隔 2.80 dB）。
- **短时响度锚（`--mode shortterm`）**：轮播池（BGM 轮播组）**不要用纯积分 LUFS 对齐**。积分响度相等 ≠ 听感相等——实测同一批交付 BGM 积分极差仅 **3.10 dB** 时，中位短时响度 S_p50 极差高达 **7.60 dB**，`corr(LRA, S_p50−I) = -0.555`（动态越大的曲子，典型听感越低于它自己的积分值）。`--mode shortterm` 以 S_p50 为目标、用**恒定增益**（`volume=` 滤波器）对齐，结构上不可能产生泵浦，并自带真峰夹紧（不越 `--tp`）。
- **绝对响度与原始音量无关**：loudnorm 归一化 = 响度测量 + 增益补偿，最终 LUFS 与原始峰值/响度无关。原始差异只影响：① 原始过静提增益后可能触发限幅/底噪放大；② 已削波素材降增益也救不回失真。处理后音色与相对动态不变。
- **相对响度**（`--mode relative`）：同批次同用途素材以**批内中位数为锚**，`target_i = 锚点 + retain×(原值−锚点)`，retain 默认 **0.10**（90% 矫正、保留 10% 偏差）——从高往低压但不强行平均，保留排序与动态。（15 轨批实测：散布 3.2dB → 残余 0.3dB）
- **声道中间件（实测修复 3dB 偏差）**：`audio_normalize.py` 对“源声道数 ≠ 目标声道数”的素材（如 voice 收立体声录屏、bgm 收单声道源）会先自动生成目标声道 PCM 中间件，再对中间件做 loudnorm 测量与均衡，保证测量对象 = 最终输出对象。（旧流程成品整体低 3dB，脚本内已闭环，无需人工预降混。）
- 若单轨**内部**乐器失衡（如混音里笛子偏响），per-track 响度无法修，需回源分轨重混。
- **淘汰件与母带一律备份隔离，禁止直接删除**：查重淘汰件移入专用隔离目录，原始母带移入归档目录，由用户验收后自行清理。

### 2.5a 三道安全闸（`audio_normalize.py` 已内建；违反即返工）

1. **幂等闸 `--idem`（默认 0.3 dB）**：已落在目标 ±0.3 dB 内的文件**直接跳过**，不做任何处理（`[SKIP]`）。
   *为什么*：对已达标素材再跑一遍，增益是 0，**唯一产物是风险**。实测某 BGM 批次 97 个源文件里 **91 个本已精确落在 -28.00/-25.00**（`Ancient_Ambient01` 源 = -28.00、`Atomic_Ambient01` 源 = -25.00、`Medieval_Ambient01` 源 = -24.99），这一遍均衡纯属空转；而其中 6 个文件正因为被"多跑了一遍"而在实机里出现忽大忽小。
2. **线性闸（预检 + 后验，默认开启）**：`linear=true` 在 ffmpeg 里是**"允许"不是"保证"**。
   `af_loudnorm.c` 的 `init()` 原文：
   ```c
   offset    = s->target_i - s->measured_i;
   offset_tp = s->measured_tp + offset;
   if ((offset_tp <= s->target_tp) && (s->measured_lra <= s->target_lra)) {
       s->frame_type = LINEAR_MODE;      // 否则落到 FIRST/INNER/FINAL_FRAME = 时变增益
   }
   ```
   不满足即**静默**改走时变增益——不报错、不告警，听感就是泵浦（呼吸感）。
   - **预检**：脚本复刻上式，不通过就**拒写该文件**（原文件零改动）、逐条给出原因，进程退出码 **2**。
   - **后验**：`print_format=json` 后 `uninit()` 会输出 `normalization_type = linear|dynamic`，这是权威判据；报 `dynamic` 一律判失败并丢弃产物。
   - **`--lra` 是双重身份**：既是"目标动态范围"，也是"是否允许线性"的开关。源 LRA 超它就会被降级——**放宽 `--lra`（如 20）即可放行并保留原动态**；`--allow-dynamic` 才是在知情前提下接受泵浦。
3. **短时闸**：轮播池走 `--mode shortterm`（恒定增益路径），结构上无泵浦可能。

**验收口径**：`audio_check.py` 现已输出 LRA / S_p50 / 同池离散度（`[POOL]` 段）与"泵浦风险文件"计数。**只查积分 LUFS 是查不出泵浦的**——泵浦文件的积分响度完全达标（实测：一个被时变增益处理过的文件，积分精确 -25.00 LUFS、看不出任何异常，而轨内增益在 3 秒窗上摆动达 5.95 dB）。


## 2.8 ShortID 注册表 + 纯 Python bank（⚠️ 实验性，正式交付走 Vorbis）

**正式音频交付一律走 Wwise Vorbis 流式**（`new_bank_project.py` + `wwise_wire.py` → WwiseCLI 生成）。纯 Python ADPCM 打包已被实机验证废弃（ffmpeg 标准 MS ADPCM 内嵌后游戏按 WWise 私有格式解码 → 噪音+闪退），`audio_pack.py` 的 `speechbank`/`plainbank` **仅作结构与 ShortID 研究，不得用于正式交付**。

本 skill 保留两项机制：

```bash
S=<skill目录>/scripts
# ✅ 有效：ShortID 注册表（防冲突基础）
python $S/audio_pack.py scan

# ⚠️ 实验：只做结构/bank 研究，勿用于交付（运行时会打印警告）
python $S/audio_pack.py speechbank <wav目录> --out <Audio目录> [--bank 名]
python $S/audio_pack.py plainbank <wav目录> --bank <名>_Bank --out <Audio目录> [--prefix Play_]
```

- ✅ **ShortID 规律（有效）**：Event ShortID = FNV-1(32)(小写事件名)，区分不同对象/音频靠唯一事件名前缀；媒体/声音/动作/容器 ID 从 `state/id_registry.json` 避让分配，杜绝不同内容 ID 撞车。`scan` 命令产出注册表，供 `new_bank_project.py` / `wwise_wire.py` 建 Wwise 工程时参考防冲突。
- ⚠️ **编码（废弃）**：不可用于交付（原因见本节首段）。
- 模板 `assets/template_slim/template_speech.bnk` 现在仅作实验参考；正式交付用完整模板工程（`ensure_template.py` 拉取）。
- 产物：实验产物 `.bnk/.xml/.txt` + `_Banks.ini` 仅用于研究，**不要**拿去 `register_to_mod.py` 注册交付。

## 2.9 第 0 步（可选）：素材整备（源池 → 规范素材池）

素材来源为网易云 ncm 加密、多目录混杂、存在重复或需要按时代分区时，先做整备再进五步标准流程：

```bash
# ⓪a ncm 解密（默认输出 <源目录>/converted；ffprobe 复核通过且显式 --delete-source 才删源）
python $S/ncm_decrypt.py <ncm文件或目录...> [--out DIR] [--delete-source] [--selftest]
# ⓪b 指纹查重（24对数频带×64时间片指纹 + 响度包络相关 + 时长比；默认只报告，--quarantine 才移动）
python $S/audio_dedupe.py <文件或目录...> [--auto 0.975 --env 0.985 --dur 0.99] \
    [--prefer 子串] [--quarantine DIR] [--cache DIR] [--jobs 4] [--report PATH]
# ⓪c 音乐特征分析（BPM/响度/动态/亮度/打击密度 + 唤醒度评分，四分位=四时代归属建议，CSV 落盘）
python $S/music_features.py <文件或目录...> [--out features.csv] [--cache DIR] [--jobs 4]
```

- **判同阈值**：fp≥0.975 且 env≥0.985 且时长比≥0.99 → 同一母带（本地 129 文件/32 对判同实证）。同曲不同混音、昼/夜变体、分轨（Layer/backing）落在疑似区，**保留并报告，不自动删**。
- **人声/伴奏守卫**：名称一边含 伴奏/instrumental 而另一边不含 → 即使高相似也只进疑似清单。
- **质量排序**：无损>有损 → 采样率 → 位深 → 时长，全平取 `--prefer` 子串匹配方（如网易云官方曲名）。
- **分区建议仅供参考**：唤醒度=0.40×BPM+0.30×RMS+0.15×打击密度+0.15×亮度（z 分数加权），与曲名语感冲突时以人工微调为准，不影响格式合规。
- 批量调用用 `--filelist` 传路径清单，禁止 shell 字符串拼接（中文/空格路径会因命令替换不做引号移除而断裂）。

## 3. 标准流程（五步，逐步对应脚本）

```bash
S=<skill目录>/scripts
# ① 核验（格式/采样率/声道/时长/LUFS 体检表；--fix 自动转 48k/单双声道；--json 程序化验收）
python $S/audio_check.py <素材路径...> --category sfx|voice|bgm [--era ancient|later] [--fix] \
    [--filelist F] [--jobs N] [--json PATH]
# ② 响度均衡（absolute=校准基准；relative=组内 90% 矫正保留 10% 偏差；就地写+备份；--out 模式统一 .wav 后缀）
python $S/audio_normalize.py <素材路径...> --category voice|quote|bgm|sfx [--era later] \
    [--mode absolute|relative] [--retain 0.10] [--i -23] [--out DIR] [--filelist F] [--jobs N]
# ②a 仅保留有效部分：ShortID 注册表刷新（speechbank/plainbank 为实验，正式交付勿用）
python $S/audio_pack.py scan
# ③ 正式打包统一走 Wwise Vorbis：建 Wwise 工程并导入（sfx 全自动；voice/bgm 用 --template 指向用户已复制好的教程模板副本）
python $S/new_bank_project.py --proj <新工程目录> --bank <名>_Bank --media <素材目录> [--template <模板工程>] [--generate]
# ④ 接线/改名/生成（用户 GUI 导入保存后的增量接线也走这里）
python $S/wwise_wire.py <工程目录> --scan
python $S/wwise_wire.py <工程目录> --wire <bank名> --events-wu <Events工作单元名> [--only 子串] [--dry-run]
python $S/wwise_wire.py <工程目录> --rename-event 旧名 新名
python $S/wwise_wire.py <工程目录> --generate <bank名>
# ⑤ 注册到 mod（自动定位 P1 源工程 .civ6proj / P2 运行目录 .modinfo，双向同步）
python $S/register_to_mod.py --bank-dir <工程>\GeneratedSoundBanks\Windows --bank <名>_Bank \
    --find <mod名> [--section ingame|global|menu] [--dry-run]
# ⑤b 注册后语义校验（每次注册/交付前必跑, 期望 PASS）
python $S/register_to_mod.py --verify --audio-id <id> --mod <mod目录>

```

## 4. 脚本清单

| 脚本 | 职责 | 依据 |
|---|---|---|
| `ncm_decrypt.py` | 网易云 ncm 解密→裸流（AES+RC4 变体密钥流，klen=128 布局变体兼容）；ffprobe 复核通过且显式 `--delete-source` 才删源；`--selftest` 往返自检 | anonymous5l/ncmdump 参考实现（taurusxin 复刻版）+ 本地 54/54 实证 |
| `audio_dedupe.py` | 跨目录音频指纹查重：判同/疑似/人声伴奏守卫，质量排序，淘汰件备份隔离（默认只报告） | 本地双库查重实证（129 文件 / 32 对判同，已知歌曲对校准阈值） |
| `music_features.py` | BPM/响度/动态/亮度/打击密度特征 + 唤醒度评分与四时代分位建议（CSV） | 本地 97 首 BGM 时代分区实证 |
| `audio_check.py` | RIFF/PCM/48k/声道/LUFS 体检 + `--fix` 容器纠正；**LRA / S_p50 / 同池离散度 `[POOL]`（含"双基准混排"判定）**；`--lra-cap/--pool-spread`；`--filelist/--jobs/--json`；UTF-8 子进程解码/输出自适应 | 教程 11 章最佳实践 + 中文 Windows 实测修复 + 2026-09 泵浦/听感离散度事故（§2.5a） |
| `audio_normalize.py` | loudnorm 双遍响度均衡；**幂等闸 `--idem`、线性闸（预检拒写 + `normalization_type` 后验，拒写时退出码 2）、短时锚 `--mode shortterm`**；`--out` 统一 .wav 后缀；`--filelist/--jobs`；声道中间件自动对齐测量/输出 | 教程：语音-21、远古 BGM-28、后世-25 + 立体声语音实测修复 + `af_loudnorm.c init()` 线性判定 + 2026-09 重复归一事故（§2.5a） |
| `new_bank_project.py` | 克隆模板→独立 bank 工程（导入+work unit 注入+可选生成） | 教程模板工程 + 本地实证 XML 模式 |
| `wwise_wire.py` | scan/wire/rename/generate | 本地 mod 实战交付验证 |
| `register_to_mod.py` | `.civ6proj`（CDATA UpdateAudio + Content 条目）与 `.modinfo`（UpdateAudio + Files）双注册 + Banks.ini；`--verify` 语义校验（UpdateAudio 只指向 ini） | 本地双案例（.civ6proj 与 .modinfo 各一）实证 |
| `build_combination_bank.py` | 组合式 bank：N 分轨 + 全组合 Play/Stop 多动作事件（引擎并轨，UI 零改动） | Wwise 多动作事件 schema |
| `music_wire.py` | fade 淡出检测 / ExitCustom 自动落点 / 时代权重（教程规则） | 模板 MusicCue CueType=2 + Weight=Real64 实测 |
| `leader_timeline.py` | 领袖 .ast 时间线：6 槽位 FXName + Duration=语音时长+pad（三案例路由） | civ6-asset-forge → reference/leader-2d.md 模板 ast 实测 schema |
| `unregister_audio.py` | 移除音频注册（modinfo UpdateAudio/Files、civ6proj CDATA/Content，可选清源目录） | 与 register 互逆 |
| `ensure_template.py` | 模板缺失时询问用户并从教程仓库拉取，写 local_paths.json 自适应 | 致谢章节同源 |
| `wwise_shortid.py` | WWise ShortID 核心库：FNV-1 事件哈希 / .bnk 解析 / 字节模板重建 / ID 注册表 / WAV→WEM 编码 | 内化自早期独立打包库（8/8 事件 ID 与成品一致实证）；ShortID 机制有效，编码部分不用于交付 |
| `audio_pack.py` | ShortID 注册表刷新（scan，有效）+ 实验性纯 Python bank（speechbank/plainbank，⚠️ ADPCM 已实证废弃，勿交付） | 内化自早期独立打包 CLI；正式交付走 Wwise Vorbis |

## 5. 注册产物基线（缺一不可）

```
<mod>\Platforms\Windows\Audio\
  ├─ <名>_Banks.ini        # [InGame] 下列 bank；主菜单要响移 [Global]
  ├─ <名>_Bank.bnk/.xml/.txt
  └─ <ID>.wem …            # bank xml 内引用的流式媒体，逐个拷入
```
`.modinfo`：`<InGameActions>` 开标签后插入 `<UpdateAudio id="…"><File>Platforms/Windows/Audio/….ini</File></UpdateAudio>` + `<Files>` 补条目。
`.civ6proj`：`InGameActionData` CDATA 内 `</InGameActions>` 前插单行 UpdateAudio（正斜杠）+ `<Content Include="Platforms\Windows\Audio\…"><SubType>Content</SubType></Content>` 条目。

## 6. 触发端速查（注册完成后接线用）

- **Lua（仅 UI 上下文）**：`UI.PlaySound('Play_X')`；**无 StopSound API，停止=播放 `Stop_X` 事件**（媒体协调器 MediaStop 模式：播放前 MediaStop→Play_→Stop_ 转换播放）。
- **数据库列直接填事件名**：`UnitCommands.Sound` / `UnitOperations.Sound` / `Buildings.QuoteAudio` / `TechnologyQuotes|CivicQuotes|LeaderQuotes|Features.QuoteAudio` / `GreatWorks.Audio`（引擎自动加 Play_ 前缀）/ `TurnSegments.Sound` / `RandomEvent_Presentation.Sound` / `LoadingInfo.PlayDawnOfManAudio`。
- **artdef**：Audio 集合（3D 位置音）+ 教程时间线 Sound 事件（领袖语音）。
- 测试：civ6-tuner（FireTuner TCP:4318）执行 `UI.PlaySound('Play_X')`。

## 7. 已知边界

- 交互音乐容器内部的素材不自动接线（由容器/switch 管理），`--scan` 会列出但需人工确认。
- 语言本地化语音按 `语言/<同名bank>` 约定铺文件；语言列表见教程模板的 Speech 工作单元。
- `.civ6proj` 的 Cooked 产物由 ModBuddy 构建生成，本管线只改源工程与运行目录，不模拟 ModBuddy 构建。
- **纯 Python ADPCM 打包已废弃**（原因与影响面见 §2.8）。
- 纯 Python 路径不做多语言 per-language bank。

---

## 致谢

本管线的模板工程、音频导入流程与预处理标准来自 **优妮《小优妮的文明6模组笔记》**（Civ6_Modding_Textbook）第 11 章「音频」与配套 WWiseProject 模板的无私分享：
`https://github.com/dwughjsd/Civ6_Modding_Textbook`。GUI 半自动步骤均以该教程为权威依据，感谢原作者对社区的支持。

## 模板自适应（分享后在新机器上运行）

全新机器首次使用前先确认：
- `ffmpeg` / `ffprobe` 已加入 PATH（素材核验/响度均衡/时长探测依赖；缺失时脚本会报找不到，请先安装）。
- Wwise 2015.1.9 已安装，且 `local_paths.json` 的 `wwcli` 指向 `WwiseCLI.exe`（脚本缺失时给出明确提示）。
- `git` 可用于 `ensure_template.py` 自动拉取完整模板；没有 git/网络时手动下载教程仓库并配置 `template_full`。
- 可选 Python 依赖：`numpy`（`audio_dedupe.py` / `music_features.py`）、`pycryptodome`（`ncm_decrypt.py`），用到对应步骤时再 `pip install`。


2. 需要**完整模板**（voice/bgm 的 GUI 容器工作）而机器上没有时：**先询问用户**，确认后执行
   `python scripts/ensure_template.py --to <目标目录>`——从上述仓库 `git clone --depth 1` 拉取并复制 `WWiseProject/FelineJasperKitty`（含媒体）。
3. 拉取后脚本会把新路径写入 skill 目录 `local_paths.json`（键 `template_full`），`ensure_template.py` 检测与 `audio_pack.py scan` 会自适应；调用完整模板时用 `new_bank_project.py --template <完整模板路径>` 或直接读取该键。
4. **实验性纯 Python bank**（`audio_pack.py speechbank/plainbank`）默认使用 `assets/template_slim/template_speech.bnk`（20KB，纯结构、无成品音频）；
5. **`state/id_registry.json` 是本机状态，不随 skill 分发**：接收方首次跑 `audio_pack.py scan`（或在 Wwise 打包前维护注册表）后开始累积自己的已用 ID 表。


---

## 作者与致谢

- 作者：千与千寻瀑
- 致谢：优妮、岛村卯月、UzukiShimamura
