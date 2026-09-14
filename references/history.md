# 工作史与决策记录（去项目化）

> 本文档只记录“规律、结论与教训”，不保留具体项目、人物、成品音频与本地路径。
> 作为本管线的演化依据，供后续维护者判断“为什么这样做”。

## 阶段一：搞清楚“冲突/覆盖”的本质

- 游戏音频引擎为 WWise，全部音频对象使用 32 位 ShortID。
- **事件（Event）ShortID = FNV-1(32) 对小写事件名哈希**：
  - 名字唯一 → 哈希唯一 → 事件不冲突；
  - 因此区分不同语音/音频 = 分配唯一事件名前缀，而不是用其它技法。
- **媒体/声音/动作/容器等其它 ID 为工程随机数值**：
  - 不同内容必须全域唯一，否则相同 ID 互相覆盖；
  - 完全相同的内容可共用同一 ID（无害去重）。
- **锚点容器与游戏同步对象禁止改号**：
  - 语音链路锚点、音乐 DummySwitches 等 `id\d+` 对象必须原样保留；
  - `Init.bnk` 承载游戏同步，mod 不自制/替换。

## 阶段二：工具化尝试

- 建立了 ID 注册表：扫描既有成品/模板工程，收集已用 ShortID，新分配时避让。
- 实现了两条打包路径：
  1. **纯 Python bank 重建**：解析模板 bnk 的 HIRC 字节布局，按 `BKHD + DIDX + DATA + HIRC` 重建；
  2. **Wwise 工程自动化**：复制模板工程、前缀改名、非锚点 ShortID 重排、一键生成。
- 纯 Python 路径最初用 ffmpeg 标准 MS ADPCM 内嵌，结构自检通过、事件哈希验证通过。

## 阶段三：游戏实机修正（关键转折）

- 在“普通音频”接入中，先只放文件、未注册加载动作 → 游戏内触发事件但无声。
- 定位到注册链路必须完整：
  - `Banks.ini` 写加载分类；
  - `.modinfo` 的 `<UpdateAudio>` 指向 ini；
  - 所有物理文件（bnk/txt/xml/ini/wem）必须进 `<Files>` 打包清单；
  - `.civ6proj`（ModBuddy 源工程）同步 `<UpdateAudio>` + `<Content>` 条目。
- 补充注册后仍发现实际播放异常，最终实机定位到**编码方案错误**：
  - WWise 的 “MS ADPCM” 是私有变体，ffmpeg 标准 `adpcm_ms` 并不兼容；
  - 直接用 ffmpeg 标准 ADPCM 内嵌进模板 bank，游戏按 WWise 私有格式解码 → **噪音 + 闪退**；
  - 且 ADPCM 压缩率约 25%，远不如成品音乐流式 Vorbis（约 8-10%）。
- 结论：**纯 Python ADPCM bank 不作为正式交付方案**。

## 阶段四：BGM 三组结构认知

- 明确文明音乐不是单一“bgm”类，而是三组：
  - 轮播背景音乐；
  - 外交背景音乐；
  - 主题音乐。
- 主题音乐建议按 4 个时代准备。
- 外交背景音乐采用官方标准做法：**一个文明对应一首外交背景音乐**，由 `LeaderMusic_<Civ>` 容器与 `Play_Leader_Music_<Civ>` 事件承载。
- `PauseModCivMusic` / `ResumeModCivMusic` 只用于临时遮挡场景，不能用于正常 BGM 时代切换或外交音乐切换，容易导致音乐停摆。

## 最终决策

- **正式音频交付统一走 Wwise Vorbis 流式**：
  - 在 Wwise 工程中把素材设为 Stream → 生成 Vorbis wem + bank；
  - 语音、普通音频、BGM 均按此路线。
- **保留且有效的部分**：
  - ShortID 规律（Event FNV-1、非 Event ID 避让、锚点保护）；
  - ID 注册表 `scan` 机制（防冲突基础）；
  - Wwise 工程自动化（复制/改名/重排/一键生成）；
  - 注册与校验流程（`register_to_mod.py --verify`）。
- **降级为实验/研究的部分**：
  - `audio_pack.py speechbank/plainbank` 纯 Python 生成，仅用于结构/ShortID 研究；
  - 它们不产出可交付的正式 bank。

## 留给后续维护者的检查单

1. 新音频接入先过素材核验与响度均衡，再进打包。
2. 打包前运行 `audio_pack.py scan` 刷新 ShortID 注册表。
3. 正式 bank 必须由 Wwise 生成 Vorbis（不要用纯 Python ADPCM 产物交付）。
4. 注册必须写齐 Banks.ini + UpdateAudio + Files/Content，并跑 `--verify`。
5. 命名坚持唯一前缀 + 槽位/用途；绝不改锚点对象。