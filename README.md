# Civ6 Modding Skills

面向 AI 编码代理（Claude Code / DSH / opencode 等支持 `SKILL.md` 约定的 harness）的
**文明 6（Civilization VI）模组开发技能合集**：5 个互相引用的 skill，覆盖玩法逻辑、数据、
UI、2D 美术素材、原版美术引用链、音频管线、工坊发布与运行时验证。

作者：**千与千寻瀑** · 许可：**MIT**（见 [`LICENSE`](LICENSE)）

---

## 一、这套 skill 是什么

不是"教程合集"，而是**可执行的作业规范**：每个 skill 里都有决策树（"遇到 X 去读哪个文件"）、
踩坑记录（gotchas）、**零依赖校验器**（改完代码/数据当场自检），以及从真实工程沉淀出的实测数据
（图标尺寸表、原版换行口径、API 运行时核验结果等）。

**分工与署名**：本合集里**管线、工作流、方法论与实测结论**由作者（千与千寻瀑）整理；
随包分发的**教程、参考库、素材与模板是社区前人整理、分享的成果**（逐项出处见各文件与 [`skills/civ6-modding/reference/sources/README.md`](skills/civ6-modding/reference/sources/README.md)），
第三方**工具**（工坊上传器、Wwise 模板工程等）不随包分发，按上游许可自行获取。

| skill | 定位 | 关键内容 |
|---|---|---|
| **`civ6-modding`** | 玩法侧总入口 | Lua（UI + GamePlay）、ForgeUI XML 布局、`.civ6proj` / `.modinfo` 注册、数据库 XML/SQL、事件系统与 API 参考、总督/城邦/议程/平衡补丁分册、Steam 工坊发布；含离线数据库目录与 8 个校验器 |
| **`civ6-asset-forge`** | 2D 美术素材合成 + 注册链（六类） | 总督素材 / 忠诚度与宗教压力图标 / 单位晋升图标 / 2D 领袖纸片人 / UI 领袖立绘（Suk 适配）/ 历史时刻插画；每类附规格、模板、生成脚本与校验脚本 |
| **`civ6-art-reference`** | 原版美术引用链 + cook 层 | ArtDef / XLP 四层引用链查询与克隆（给新对象配原版模型）、cook 报错排查（pantry 找不到、引用被替换成 error asset）、双端不同步分级判定 |
| **`civ6-audio-pipeline`** | 音频全流程 | 素材整备（ncm 解密/指纹查重/音乐特征）→ 核验（PCM/48000Hz/声道/LUFS）→ 响度均衡（ffmpeg loudnorm）→ Wwise 2015 工程直改（WwiseCLI 命令行）→ 自动注册进 `.civ6proj` / `.modinfo` |
| **`civ6-tuner`** | 运行时验证 | 通过 FireTuner（TCP:4318）在**运行中的对局**里执行任意 Lua：接口行为/参数/PROPERTY/Modifier 的实测验证、复现脚本报错；附 19 个即用探针片段 |

**家族路由**（任务 → 去哪个 skill）见 [`skills/civ6-modding/reference/FAMILY_INDEX.md`](skills/civ6-modding/reference/FAMILY_INDEX.md)。
**每个 skill 的入口**是它自己的 `SKILL.md`（harness 加载的就是这个文件）。

---

## 二、安装

skill 目录是**纯文件**，没有构建步骤。把 `skills/` 下的 5 个目录放进你的 harness 的 skill 根目录即可：

```bash
git clone https://github.com/nuanyuqingfeng/civ6-modding-skills.git
# 例：DSH / 部分 harness 读取 ~/.agents/skills/<name>/SKILL.md
mkdir -p ~/.agents/skills
cp -r civ6-modding-skills/skills/* ~/.agents/skills/
```

> 5 个 skill **互为同级目录**：文档里的跨 skill 引用（如 `civ6-modding/art/gen_tex.py`、
> `civ6-asset-forge/reference/loyalty-icon.md`）都按"**同一 skills 根下的兄弟目录**"解析。
> 只装其中一部分也能用，但跨 skill 引用会落空——建议整套装。

---

## 三、环境要求

| 依赖 | 版本 | 谁需要 |
|---|---|---|
| **Python** | 3.9+（作者环境 3.14） | 除 2 个 `.mjs` 外的全部脚本；纯标准库脚本占多数 |
| **Node.js** | **≥ 22**（用内置 `node:sqlite`） | `civ6-modding/scripts/rgn_validate_runner.mjs`（SQL 引用完整性校验） |
| Windows | 10/11 | 路径自举用注册表 / Steam `libraryfolders.vdf` 探测；非 Windows 可手写 `local_paths.json` 后使用大部分只读工具 |
| Sid Meier's Civilization VI + SDK | 最新版 | 官方素材查询（P3/P4）、ModBuddy 构建、AssetEditor cook、工坊上传 |
| **texconv** | 最新 | PNG→DDS（`art/convert_art.ps1`、`art/make_atlas.py` 等） |
| Wwise | **2015.1.x**（Civ6 内置版本口径） | `civ6-audio-pipeline` 的 bank 生成 |
| ffmpeg | 任意近期版 | 音频转码 / 响度均衡（`audio_normalize.py`） |

### Python 第三方库（按脚本，其余脚本零依赖）

| 库 | 用在 |
|---|---|
| **Pillow** | `civ6-modding/art/`（图标/图集/DDS 读写，8 个脚本）、`civ6-asset-forge/scripts/`（11 个脚本） |
| **numpy** | 同上（5 + 7 个脚本）、`civ6-audio-pipeline/scripts/`（2 个） |
| **scipy** | `civ6-modding/art/normalize_icon.py`、`art/survey_icon_atlas.py`、`civ6-asset-forge/scripts/edge_gradient.py`、`recolor_template.py` |
| **psd_tools** | `civ6-asset-forge/scripts/apply_moment_template.py`（读 PSD 模板） |
| **pycryptodome** | `civ6-audio-pipeline/scripts/ncm_decrypt.py`（网易云 ncm 解密） |

```bash
pip install pillow numpy scipy psd_tools pycryptodome
```

每个 skill 的 `TOOLS.md` 有**逐脚本**的用途/用法/依赖清单（由 `civ6-modding/tools/skill_manifest.py` 生成）。

---

## 四、首次配置（**换机器必做**）

脚本**不写死路径**：每个 skill 各有一份 `local_paths.json`（个人环境文件，**不入库**），
查找顺序为 `local_paths.json` → 注册表 / Steam VDF 自动探测 → 内置默认值 → 明确报错。

```bash
python skills/civ6-modding/tools/_paths.py       # 打印 P1–P6 与外部工具的实际解析结果
```

缺失项会显示 `[缺失]`；按提示把实际路径写进 `skills/civ6-modding/local_paths.json` 即可，例如：

```json
{
  "modbuddy": "D:/documents/Firaxis ModBuddy/Civilization VI",
  "mods": "D:/documents/My Games/Sid Meier's Civilization VI/Mods",
  "game": "F:/Steam/steamapps/common/Sid Meier's Civilization VI",
  "sdk_assets": "F:/Steam/steamapps/common/Sid Meier's Civilization VI SDK Assets",
  "sdk": "F:/Steam/steamapps/common/Sid Meier's Civilization VI SDK"
}
```

`civ6-audio-pipeline` 有自己的一份（键名 `wwcli` / `template_full` / `p1` / `p2`），
也支持 `CIV6_<KEY>` 环境变量（如 `CIV6_WWCLI`）。

---

## 五、离线参考库（**全部随包分发**）

`skills/civ6-modding/database/` 是"写代码前先查库"的离线数据源，**全部随仓库分发**：

| 文件 | 体积 | 说明 |
|---|---|---|
| `api.sqlite` | 2.5 MB | 4857 条 Lua API + **人工实测核验列**（2026-09-08 FireTuner 全量），不可再生 |
| `api-verification-2026-09-08/` | 6.2 MB | 上表核验列的**原始凭证**：FireTuner 实跑输出、全量 CSV、人工复核清单与报告 |
| `DebugGameplay.sqlite` | 58.2 MiB | 官方 gameplay 库快照（427 表）—— **`rgn_validate` 的基础库**、SQL 查询主库 |
| `DebugLocalization.sqlite` | 62.1 MiB | 官方本地化文本（8 语言）+ 手工配色/图标名标注表，含不可再生的人工成果 |
| `DebugConfiguration.sqlite` | 1.1 MiB | 官方 FrontEnd 配置快照（`Maps` 等） |
| `source_index.sqlite` | 29.1 MiB | 官方行级来源索引 + 人工 `dlc_dependency` 标注 |

逐库的用途、可再生性与重建口径见 [`skills/civ6-modding/database/README.md`](skills/civ6-modding/database/README.md)。

---

## 六、随包内置的素材与工具（clone 即可用）

| 内容 | 位置 | 说明 |
|---|---|---|
| **texconv.exe** | `civ6-modding/art/bin/` | Microsoft DirectXTex（MIT）release 版 —— PNG→DDS 开箱可用；`_texconv.py` 优先取它，可用 `TEXCONV` 覆盖 |
| **历史时刻形状模板** | `civ6-asset-forge/templates/moment_illustration/` | 18 张官方形状 PSD（`apply_moment_template.py` 默认目录） |
| **原版图标标记全表** | `civ6-modding/reference/sources/civ6-icon-tags.sql` | 5056 个 `[ICON_*]`；另有百科颜色/图标常量、StretchMode 原版统计 |
| **社区参考件** | `civ6-modding/reference/sources/` | Civ VI Modding Companion 2.0（ChimpanG / WildW）、原版议程表 —— 出处与许可见该目录 README |

**仍属可选（缺失不影响 Civ6 侧功能）**：

- 生图依赖：`civ6-modding/art/make-icon.ps1` 需要自备 stable-diffusion.cpp（`sd-cli.exe` + FLUX 权重）与
  ImageMagick；路径用 `-SdDir` / `-Magick` 或 `SD_CPP` / `MAGICK` 指定。
- `WwiseCLI.exe` 与完整 Wwise 模板工程 —— `civ6-audio-pipeline/scripts/ensure_template.py`
  会指向**上游开源工程 URL**并请你确认后自行获取。
- 工坊上传器 —— 上游 [`Jianbao233/Civ6WorkshopUploader`](https://github.com/Jianbao233/Civ6WorkshopUploader)；
  用 `civ6-modding/release/scripts/build.ps1` 构建非 Trimmed 版。

---

## 七、许可

- 本仓库的**代码、文档、管线与工作流**：**MIT**（见 [`LICENSE`](LICENSE)），作者 **千与千寻瀑**。
- **随包分发的素材 / 模板 / 参考件来自社区前人的整理与分享**（逐项出处见各文件与该目录 README）；
  第三方**工具**不随包分发，按上游许可自行获取。完整清单与链接见文末
  [**九、上游链接与致谢**](#九上游链接与致谢)。
- 本仓库**不含**游戏安装目录里的原始素材文件（`.dds`/`.blp`/`.bnk` 等）：skill 里只有
  **引用关系、坐标/尺寸/字段规格与实测数据**；实际素材请从你自己的游戏（pantry）获取。

---

## 八、已知限制

1. **以 Windows 为主**：路径自举、ModBuddy/AssetEditor/cooker、工坊上传均假定 Windows；
   只读查询类工具（SQLite / 文档）跨平台可用。
2. **参考库全部随包**（含 58 MiB 的 `DebugGameplay.sqlite` 与 62 MiB 的 `DebugLocalization.sqlite`）：
   clone 体积偏大是预期；若只想跑校验器，保留 `DebugGameplay.sqlite` 即可。
3. **游戏版本敏感**：图标尺寸、artdef/XLP 条目、DB 列等结论基于当前版本实测；
   升级 DLC/补丁后建议用各 skill 的校验器复验。
4. **晋升图标（类别③）生成管线已作废**：只保留尺寸/格式规格
   （`civ6-asset-forge/reference/promotion-icon-sizes.md`），不要再照旧流程做图。
5. **工坊发布流程**（`civ6-modding/release.md`）含作者本机工具链（上传器 exe、代理诊断），
   其中的脚本按 `local_paths.json` 解析路径；缺工具时会明确报错。
6. 历史遗留的"作者本机绝对路径"已尽量改为相对描述或路径键，但**文档叙述中仍可能出现示例路径**
   （属说明性内容，不影响运行）。

---

## 九、目录结构

```
civ6-modding-skills/
├── README.md              ← 你正在读的文件
├── LICENSE                ← MIT
└── skills/
    ├── civ6-modding/      SKILL.md · TOOLS.md · 30+ 分册 · database/ · scripts/ · art/ · tools/ · release/
    ├── civ6-asset-forge/  SKILL.md · TOOLS.md · reference/ · scripts/ · assets/ · templates/
    ├── civ6-art-reference/SKILL.md · TOOLS.md · reference/ · scripts/ · assets/art_index.json.gz
    ├── civ6-audio-pipeline/SKILL.md · TOOLS.md · references/ · scripts/ · assets/
    └── civ6-tuner/        SKILL.md · TOOLS.md · reference/ · scripts/ · snippets/
```

---

## 十、上游链接与致谢

### 10.1 转载 / 引用的上游项目

| 上游项目 | 作者 / 组织 | 许可 | 在本仓库中的形态 |
|---|---|---|---|
| [`dwughjsd/Civ6_Modding_Textbook`](https://github.com/dwughjsd/Civ6_Modding_Textbook) | dwughjsd（小优妮） | 见上游仓库 | **不随包**：`civ6-audio-pipeline/scripts/ensure_template.py` 先询问再从上游拉取 Wwise 模板工程；音频 GUI 步骤以该教程为权威依据 |
| [`Jianbao233/Civ6WorkshopUploader`](https://github.com/Jianbao233/Civ6WorkshopUploader) | Jianbao233 | MIT | **不随包**：`civ6-modding/release/scripts/ensure_uploader.ps1` 一键 clone + 构建（非 Trimmed） |
| [`microsoft/DirectXTex`](https://github.com/microsoft/DirectXTex) | Microsoft | MIT | **随包**：`civ6-modding/art/bin/texconv.exe`（v2026.5.8.1，PNG→DDS 转换） |
| [`FYMapleLeaves/ml-civ6-lua-tutorial`](https://github.com/FYMapleLeaves/ml-civ6-lua-tutorial) | 枫叶 | 见上游仓库 | 致谢引用（Lua 教程） |
| Civ VI Modding Companion 2.0.xlsx | ChimpanG / WildW | 社区共享 | **随包**：`skills/civ6-modding/reference/sources/` |
| 原版图标标记全表（5056 个 `[ICON_*]`） | 号码菌 | 社区共享 | **随包**：`skills/civ6-modding/reference/sources/civ6-icon-tags.sql` |
| 原版议程表 · 颜色/图标常量 · StretchMode 统计 | 社区整理 | 社区共享 | **随包**：`skills/civ6-modding/reference/sources/` |
| Civ6 Modding Assistant 1.6.3（图标尺寸反编译表） | — | 见上游 | 图标尺寸表来源，**不随包** |
| 《文明 6》本体与 SDK | Firaxis Games / 2K | 商业软件 | 数据与素材来源；本仓库**不含**游戏原始素材文件 |

### 10.2 致谢

- **教程与经验**：优妮（《小优妮的文明6模组笔记》）、枫叶（Lua 教程）、Hemmelfort、夏凉凉凉、AWAW、岛村卯月 / UzukiShimamura
- **社区资料**：ChimpanG / WildW（Civ VI Modding Companion）、号码菌（原版图标标记全表）
- **工具**：Jianbao233（Civ6WorkshopUploader）、Microsoft（DirectXTex / texconv）
- **游戏与数据**：Firaxis Games / 2K（《文明 6》本体、SDK 与 pantry 素材）

> 若你是上述社区资料的作者并希望调整署名或移除，请提 issue。
