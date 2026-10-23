# civ6-text-authoring/TOOLS.md —— 可复用工具名录（先查这里，再动手）

> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。
> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py civ6-text-authoring` 刷新本文件。
> 本目录的工具**以纯标准库为主**（Python 标准库 / Node 内置），带退出码，可直接接 CI；用到第三方库的脚本逐条列在下方「第三方依赖」节。
> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。

## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）

| 工具 | 干什么 | 用法 |
|---|---|---|
| `scripts/build_zh_corpus.py` | build_zh_corpus.py — 把有效 zh 文本整理成结构化语料库 | `python scripts/build_zh_corpus.py [--class {main,mode}] [--dir <reference 目录>]` |
| `scripts/export_zh_text.py` | export_zh_text.py — 从本机游戏安装提取「风云变幻为准」的简体中文有效文本 | `python scripts/export_zh_text.py [--class {main,mode}] [--game <游戏根>] [--out <输出目录>]` |

共 2 个脚本。

## 第三方依赖

（本 skill 未登记第三方依赖扫描结果；请检查 `skill_manifest.py` 的 `THIRD_PARTY`。）

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
| `ws_root` | 上传临时工作区根；`content/` 用 junction 指向 Mods 副本（见 `release/scripts/make_workspace.ps1`） |
| `steam_logs` | Steam 日志目录（反查工坊条目 ID） |

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节。
> 全新机器上先跑一次上面那条命令：缺失的键会打印 `[缺失]`，按提示写 `local_paths.json` 即可。

<!-- MANUAL:BEGIN -->
## 一、本 skill 自带脚本（`scripts/`）

| 脚本 | 用途 | 用法 | 退出码 |
|---|---|---|---|
| `scripts/export_zh_text.py` | 从本机游戏安装按**引擎加载顺序**（`EXP2>EXP1>base` + DLC）重导简体中文**有效文本**（含 `<Delete>` 处理）；`--class main`（常规）/ `--class mode`（模式，仅 §1.1 模式模块用） | `python scripts/export_zh_text.py [--class {main,mode}] [--game <游戏根>] [--out <目录>]` → `reference/zh_effective.json`（或 `zh_mode_effective.json`）+ `*_diff_report.txt` + `*_tombstones.txt` | 0 成功 / 2 缺游戏或依赖 |
| `scripts/build_zh_corpus.py` | 把有效文本整理成**结构化语料库**（常规：六大分类 + 相邻/图标标记；模式：按 token 分类 + `TranslationMissing` 标记） | `python scripts/build_zh_corpus.py [--class {main,mode}] [--dir <reference 目录>]` → `reference/zh_corpus.sqlite`（或 `zh_mode_corpus.sqlite`）+ `reference/catalog/*.tsv` | 0 成功 / 2 缺输入 |

**依赖**：`export_zh_text.py` 复用同级 `civ6-modding/database/scripts/build_localization.py` 的分段实现（脚本自动定位家族目录）。运行顺序：先 `export_zh_text.py`，再 `build_zh_corpus.py`。

## 二、引用的家族执行层（单源在 `civ6-modding`，本 skill 不复制）

| 工具 | 用途 | 命令 |
|---|---|---|
| `civ6-modding/art/iconify_text.py` | 关键词→`[ICON_x]` 映射；校验图标名可解析 | `python <civ6-modding>\art\iconify_text.py <工程根> --audit` |
| `civ6-modding/scripts/check_text_refs.py` | `[ICON_x]` 正向 + `{LOC_x}` 反向 + Config 孤儿 tag | `python <civ6-modding>\scripts\check_text_refs.py <工程根>` |
| `civ6-modding/scripts/check_adjacency_text.py` | 相邻加成 Description 文本是否含 `[ICON_x]` + `{1_num}` | `python <civ6-modding>\scripts\check_adjacency_text.py <工程根>` |
| `civ6-modding/database/scripts/build_localization.py` | 合成/维护 `DebugLocalization.sqlite`（多语言参考库；本 skill 只出 zh，且以风云变幻为准） | `python … --report` |

> 为什么不搬：`iconify_text.py` 被家族 4 个 skill 的 ~15 个脚本 import，`_projwrite.py` 有 6 份受
> `check_script_write_targets.py` 一致性校验的副本。搬移会撕裂家族完整性；改以**路径引用**保持单源。

## 三、语料资源（`reference/`）

| 资源 | 内容 |
|---|---|
| `reference/zh_corpus.sqlite` | 主库：27,998 tag（表 `LocalizedText` + 6 视图：`zh_leader_trait`/`zh_item`/`zh_opening_ode`/`zh_diplomacy`/`zh_adjacency`/`zh_icon`） |
| `reference/catalog/*.tsv` | 分类清单（`leader_trait` / `item` / `opening_ode` / `diplomacy` / `other`），`Tag<TAB>Text` 可直接 grep |
| `reference/zh_effective.json` | 中间产物（常规类提取结果全量，供 `build_zh_corpus.py` 输入） |
| `reference/zh_mode_corpus.sqlite` | **模式语料**：1,282 tag（视图 `zh_mode`，含 `TranslationMissing` 列；⚠仅 197 可用）—— 仅 §1.1 模式模块使用 |
| `reference/catalog/mode.tsv` | 模式清单（`Tag<TAB>Text`，可 grep） |
| `reference/zh_diff_report.txt` | 与旧库 `DebugLocalization.sqlite` 的差异（验收依据） |
| `reference/zh_tombstones.txt` | 风云变幻环境下已删除的 tag（11 条） |
| `reference/civ6-icon-tags.sql` | 权威图标名表（5,056 个 `[ICON_*]`） |
| `reference/civ6-civilopedia-constants.sql` | 百科常量 |

## 四、本机路径收纳

| 用途 | 路径 |
|---|---|
| 本 skill 根 | `C:\Users\Administrator\.agents\skills\civ6-text-authoring` |
| P3 游戏本体 | `F:\Steam\steamapps\common\Sid Meier's Civilization VI` |
| 家族兄弟 skill | `C:\Users\Administrator\.agents\skills\civ6-modding`（执行层）/ `…\civ6-asset-forge`（美术）等 |
<!-- MANUAL:END -->
