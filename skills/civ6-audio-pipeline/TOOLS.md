# civ6-audio-pipeline/TOOLS.md —— 可复用工具名录（先查这里，再动手）

> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。
> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py civ6-audio-pipeline` 刷新本文件。
> 本目录的工具**以纯标准库为主**（Python 标准库 / Node 内置），带退出码，可直接接 CI；用到第三方库的脚本逐条列在下方「第三方依赖」节。
> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。

## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）

| 工具 | 干什么 | 用法 |
|---|---|---|
| `scripts/audio_check.py` | audio_check.py -- Civ6 音频素材核验 | `python audio_check.py <文件或目录...> [--category voice\|bgm\|sfx] [--era ancient\|later] [--fix]` |
| `scripts/audio_dedupe.py` | audio_dedupe.py -- 跨目录音频指纹查重: 同曲判定 -> 组内质量排序 -> 淘汰件备份隔离(默认只报告) | `python audio_dedupe.py <文件或目录...> [--auto 0.975 --env 0.985 --dur 0.99]` |
| `scripts/audio_normalize.py` | audio_normalize.py -- Civ6 audio loudness normalization (ffmpeg loudnorm 2-pass, linear) | `python audio_normalize.py <文件或目录...> [--category voice\|quote\|bgm\|sfx] [--era ancient\|later] [--mode absolute\|relative\|shortterm] [--i <目标LUFS>] [--out DIR] [--filelist F]` |
| `scripts/audio_pack.py` | audio_pack.py - ShortID 注册表 + 纯 Python bank 结构实验（历史独立打包器内化） | `python audio_pack.py scan<br>[实验] python audio_pack.py speechbank <wav目录> --out <Audio目录> [--bank 名] [--template 模板bnk]` |
| `scripts/build_combination_bank.py` | build_combination_bank.py -- 组合式 bank 构建器（乐队/分层音频专用） | `python build_combination_bank.py --proj <工程目录> --bank <Bank名>       --stems a.wav b.wav c.wav d.wav --codes C,D,H,L [--prefix Play_] [--dry]` |
| `scripts/ensure_template.py` | ensure_template.py -- 模板自适应保障 | `python ensure_template.py [--to <目录>] [--repo https://github.com/dwughjsd/Civ6_Modding_Textbook]` |
| `scripts/leader_timeline.py` | leader_timeline.py -- 领袖 2D 行为资产(.ast)的语音时间线自动配置 | `python leader_timeline.py patch <ast路径\|目录> --media <语音wav目录\|文件...> [--pad 0.5] [--map 槽位关键字=事件名 ...] [--dry]（另一子命令：check <ast路径\|目录>）` |
| `scripts/music_features.py` | music_features.py -- BGM 音乐特征分析: BPM/响度/动态/亮度/打击密度 + 唤醒度评分 | `python music_features.py <文件或目录...> [--out features.csv] [--jobs 4] [--cache DIR]` |
| `scripts/music_wire.py` | music_wire.py -- 交互音乐工程接线 (BGM 半自动流程的自动化部分) | `python music_wire.py {fade\|exitcustom\|weights} [...]（fade <wav>；exitcustom <工程目录>；weights <工程目录> --civ-prefix X）` |
| `scripts/ncm_decrypt.py` | ncm_decrypt.py -- 网易云 .ncm 解密为裸流 (flac/mp3/wav/ogg) | `python ncm_decrypt.py <ncm文件或目录...> [--out DIR] [--delete-source] [--selftest]` |
| `scripts/new_bank_project.py` | new_bank_project.py -- 克隆模板工程 -> 独立 bank 工程 (素材导入 + work unit 注入 + 可选生成) | `python new_bank_project.py --proj <新工程目录> --bank <Bank名> --media <素材目录\|文件...>` |
| `scripts/paths.py` | Skill 路径配置中心（本机私有，不随 skill 分发）。 | `读取 skill 根目录 local_paths.json；也支持同名 CIV6_* 环境变量覆盖，<br>local_paths.json 示例：` |
| `scripts/register_to_mod.py` | register_to_mod.py -- bank 产物注册到 mod (P1 源工程 .civ6proj / P2 运行目录 .modinfo 双注册) | `python register_to_mod.py --bank-dir <工程>\GeneratedSoundBanks\Windows --bank <Bank名>       (--find <mod名> \| --mod <mod目录>) [--section ingame\|global\|menu] [--civ6proj <路径>] [--dry-run]` |
| `scripts/unregister_audio.py` | unregister_audio.py -- 从 mod 注册点移除音频注册 (与 register_to_mod.py 互逆) | `python unregister_audio.py --audio-id <id> [--find <mod名> \| --mod <目录> \| --civ6proj <路径>]` |
| `scripts/wwise_shortid.py` | wwise_shortid.py - WWise ShortID 核心规律 + 纯 Python bank 打包核心库。 | `（库：被其它脚本 import，无独立 CLI）` |
| `scripts/wwise_wire.py` | wwise_wire.py -- Wwise 工程直改工具 (Wwise 2015.x, Yuni 谱系工程实测) | `扫描   python wwise_wire.py <工程目录> --scan<br>接线   python wwise_wire.py <工程目录> --wire <BANK名> [--events-wu <名称>]` |

共 16 个脚本。

## 第三方依赖（非标准库）

本 skill 的脚本**多数是纯标准库**；下列脚本需要先 `pip install` 对应第三方库：

- `scripts/audio_dedupe.py` → numpy
- `scripts/music_features.py` → numpy
- `scripts/ncm_decrypt.py` → pycryptodome

> 口径：对脚本 `import` 的实测扫描；纯标准库脚本不列。新增/改动依赖时同一次改动里更新 `skill_manifest.py` 的 `THIRD_PARTY`。

## 路径收纳（本机绝对路径，勿写死进脚本）

每个 skill **各自**有一份 `local_paths.json`（个人环境文件，不入库）：

| skill | 路径解析器 | 环境变量前缀 |
|---|---|---|
| `civ6-modding` | `tools/_paths.py`（P1–P6 + 外部工具） | 见该文件 `DEFAULTS` / `TOOL_DEFAULTS` |
| `civ6-audio-pipeline` | `scripts/paths.py`（`wwcli` / `template_full` / `p1` / `p2`） | `CIV6_<KEY>`（如 `CIV6_WWCLI`） |
| 其余 skill | 无独立解析器：脚本用 CLI 参数 / 相对定位，或调用 `civ6-modding` 的解析器 | — |

```bash
python "<skills>/civ6-modding/tools/_paths.py"        # 打印 P1-P6 + 外部工具的实际解析结果
```

| 键（civ6-modding） | 含义 |
|---|---|
| `modbuddy` | ModBuddy 源工程根（P1） |
| `mods` | 游戏 Mods 加载目录（P2） |
| `game` | 游戏本体：UI / Lua / XML 官方原文（P3） |
| `sdk_assets` | SDK Assets：artdef / 解包素材（P4） |
| `sdk` | SDK 工具：ModBuddy / MSBuild（P5） |
| `workshop_ref` | 创意工坊参考件，AppID 289070（P6） |
| `uploader` | 工坊上传器 exe（非 Trimmed 构建） |
| `sd_cpp` | 本地生图（stable-diffusion.cpp + FLUX 权重） |
| `imagemagick` | ImageMagick（图标阈值 / 裁边） |
| `luac` | Lua 5.1 语法检查 |
| `ws_root` | 上传临时工作区根（`%TEMP%\civ6-ws`） |
| `steam_logs` | Steam 日志目录（反查工坊条目 ID） |

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节。
> 全新机器上先跑一次上面那条命令：缺失的键会打印 `[缺失]`，按提示写 `local_paths.json` 即可。

<!-- MANUAL:BEGIN -->
## 人工备注（重跑生成器时原样保留）

<!-- 在这里写：工具之间的顺序、踩过的坑、必须人工确认的边界。
     不要在这里重复上表的机械信息 —— 那部分由 skill_manifest.py 重生成。 -->

### 五步标准流程（SKILL.md §3，逐步对应脚本）

```
① 核验      scripts/audio_check.py
② 响度均衡  scripts/audio_normalize.py（基准见 references/calibration.json；三道安全闸已内建）
③ 正式打包  Wwise Vorbis（scripts/new_bank_project.py / build_combination_bank.py）
④ 接线改名  scripts/music_wire.py / wwise_wire.py（用户 GUI 导入保存后的增量接线也走这里）
⑤ 注册      scripts/register_to_mod.py
```

### 边界

- **正式交付统一走 Wwise Vorbis 流式**；纯 Python bank（`wwise_shortid.py`）是**实验性**的，
  只用于结构研究，运行时打印警告，勿用于交付（SKILL.md §2.8 有明确标注）。
- 响度是"整轨积分响度相等 ≠ 听感相等"：轮播池必须用 `shortterm` 模式对齐 S_p50（§2.5 实测差可达 7.6 dB）。
- 素材分类不清时先走 §1 三类路由表 + §1.5 的主动询问流程，不要自行假设 sfx/voice/bgm。

<!-- MANUAL:END -->
