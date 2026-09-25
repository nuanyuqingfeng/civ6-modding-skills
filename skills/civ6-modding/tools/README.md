# tools/ —— 可复用工具名录（先查这里，再动手）

> 🧰 **本 skill 全部脚本（含 `scripts/`、`art/`、`release/scripts/`）的自动索引在
> [`../TOOLS.md`](../TOOLS.md)**（由 `skill_manifest.py` 扫磁盘生成）。
> 本文件是 `tools/` 的**使用说明**：用法细节、推荐顺序、每条教训的出处。
> 两者互补 —— 索引防"找不到"，本文件防"用错"。

> **硬性约定（写给 AI 与未来的自己）**
>
> 1. **动手前先查本名录**：需要"造个脚本做 X"时，先在本文件、[`../TOOLS.md`](../TOOLS.md)、
>    `../scripts/README.md`、`../art/`、`../release/`、其它 civ6-* skill 的 `TOOLS.md` 里找。
>    **能改就改，不要重建。**
> 2. **改完就地升级**：改了行为就更新本名录的"用法/退出码/边界"三列，别让名录与代码脱节。
> 3. **新工具必须登记**：新增脚本 → 同一次改动里跑
>    `python skill_manifest.py <skill>` 刷新名录；抽不出人话的写进 `<skill>/TOOLS.overrides.json`。
> 4. **路径不写死在正文里**：一律走 `_paths.py`（本机路径的单一真源），需要换机器只改
>    `../local_paths.json`。

---

## 0. 目录分工（别把工具放错地方）

| 目录 | 定位 | 典型内容 |
|---|---|---|
| `../scripts/` | **校验器 / 运维 / 语料**：改完就能跑、带退出码的检查 | `rgn_validate_runner.mjs`、`check_*.py`、`clear_ae_cache.py` |
| `tools/`（本目录） | **生产流程工具**：把一个 mod 从工程做成线上条目 | 构建、打包体检、工坊元数据、封面、本地生图 |
| `../art/` | **美术资产管线**：图标/贴图规范化、atlas、ArtDef 注册 | `gen_tex.py`、`normalize_icon.py`、`merge_icon_registration.py` |
| `../release/` | **上传执行与模板**：调上传器、validate、清理、代理诊断 | `upload.ps1`、`cleanup.ps1`、`docs/checklist.md` |

---

## 1. 工具名录

| 工具 | 干什么 | 用法 | 退出码 |
|---|---|---|---|
| `skill_manifest.py` | **名录生成器**：扫 skill 下脚本 → 从 docstring/argparse 抽「用途 + 用法」→ 生成/刷新 `<skill>/TOOLS.md`（人工备注块受保护、幂等、可 `--check` 做漂移检测） | `python skill_manifest.py <skill 名或路径> [...]` / `--all-civ6` / `--check` | 0 / 1 |
| `_paths.py` | **本机路径单一真源**（P1–P6 + 外部工具）。其它工具统一 `import _paths` 取路径；也可直接跑来自检本机环境 | `python _paths.py` | 0 |
| `new_project.py` | **从零建工程骨架**：生成 `.civ6proj`（5 个 CDATA 块 + ItemGroup）+ 目录 + `.gitignore`/`.gitattributes`，并自动派生 `.modinfo`。★ GUID 内置全网查重（禁止复制示例 GUID） | `python new_project.py <目录> --name <ModName> [--title-en … --title-zh …] [--deploy]` | 0 / 1 / 2 |
| `civ_leader_data.py` | **新文明/新领袖数据与文本推导**：规格 JSON → `Data/CivLeader_*.sql`（Civilizations/Leaders/Traits/CivilizationLeaders/城市名…）+ `Data/Config_*.sql`（Players/PlayerItems）+ `Text/Text_*.sql`（8 语言）。★ 列名全部取自 `database/*.sqlite` 实测；含 LOC tag 闭包与语言齐缺自检 | `python civ_leader_data.py <spec.json> --project <工程根> [--write|--check]`（示例规格 `../reference/civ-leader-spec.example.json`） | 0 / 1 / 2 |
| `modinfo_build.py` | 从 `.civ6proj` **派生 `.modinfo`**（等价 ModBuddy 构建）并可选部署到 Mods。★ **`--deploy` 先调 `cook_assets.py`**（cook 失败即中止，不做部分部署；无 `.Art.xml` 的工程用 `--no-cook` 跳过）。★ **自动把 `(Mod Art Dependency File)` 占位符替换为 `<ModName>.dep`**（ModBuddy 构建期行为，缺了它 UpdateArt 静默失效、美术全空），并把该 `.dep` 并入顶层 `<Files>`；顺带做 XML 良构 + 动作文件引用闭合自检 | `python modinfo_build.py <X.civ6proj> [--deploy] [--mods-root <目录>] [--no-cook]` | 0 / 1 |
| `cook_assets.py` | **无 GUI 重放 ModBuddy 的 ArtDef / XLP cook**（`Civ6.targets` 的三组分区逐文件 spawn，本工程 69 次调用约 35 秒）→ 直接写 Mods 副本的 `ArtDefs/`、`Platforms/<平台>/BLPs/` 与 `<ModName>.dep`。pantry 由 `.Art.xml` 的 `<requiredGameArtIDs>` 递归展开（`Shared` 是 `Expansion2` 的传递依赖，不是手写项）。★ 收尾把源工程 `ArtDefs/*.artdef` 覆盖进副本：cook 会把 pantry 解析不到的引用清成空值，副本侧要保留源里完好的引用链。★ 降级警告（`references … does not exist` / `HAS MISSING ENTRIES` / `will not be cooked`）**只报告不判失败**，判失败的是「产物缺失」与「退出码非零且日志无可解释模式」 | `python cook_assets.py <工程根> [--check] [--only ArtDef\|XLP] [--mods-root <目录>] [--out <目录>] [--quiet]` | 0 / 1 / 2 |
| `cook_dep.py` | **从 `<ModName>.Art.xml` 生成 `<ModName>.dep`**（`AssetObjects..GameDependencyData`）—— 走 cooker 的 `--mode Dependency`，**无需 ModBuddy GUI**。★ `.dep` 是 `<UpdateArt>` 的实际载荷，缺它则全部美术/图标静默不加载；落点默认 `<工程>/workspace/tmp/dep`（cooker 默认落 CWD，易漂移，本工具显式固定） | `python cook_dep.py <工程根> [--out <目录>] [--platform Windows] [--check]` | 0 / 1 / 2 |
| `verify_mod_package.py` | **交付包体检**：源工程 ↔ Mods 副本 ↔ 上传工作区 三处 SHA256 一致性；modinfo 悬空引用 / 漏登记文件 / 本地化语言清点。**cook 产物 · 美术管线 两感知**（`BLPs/**`+`.dep` 源工程本就没有、美术管线文件见 `ART_PIPELINE_EXTS` 不进 Content 与 Files → 均按预期放行；★ `ImportFiles/` 之下不豁免；`--strict` 关掉全部放行）。★ **`<UpdateArt>`/`.dep` 独立硬检查**（占位符残留、`.dep` 缺失、`.dep` 未进 `<Files>` 一律判失败 —— 这类是静默失效，不能按 cook 产物软放行） | `python verify_mod_package.py --src <工程> --mods <Mods副本> [--ws <content>] [--files a,b] [--strict]` | 0 / 1 |
| `workshop_meta.py` | **多语言 `workshop.json` 生成**（create / update 两种模式）+ 导出人类可读介绍存档 | `python workshop_meta.py <spec.json> --out <workshop.json> [--record <txt>]` | 0 / 1 |
| `workshop_item_check.py` | **线上条目核对**：标题 / 描述 / 归属账号 / 可见性 / 标签 / 内容清单 / 预览图；支持 `--expect-*` 断言；直连失败自动回落本机代理 | `python workshop_item_check.py <id> [...] [--expect-title <子串>] [--expect-public]` | 0 / 1 / 3 |
| `workshop_cover.py` | **工坊封面合成**：生图底图 + 徽记 + **确定性 CJK 排版**（含孤儿行/超边距自检）。**不提供署名参数** —— 项目约定封面永不署名 | `python workshop_cover.py --bg <png> [--emblem <png>] --line1 "…" [--line2 "…"] [--subtitle "…"] --master <png> [--preview <png>]` | 0 / 1 |
| `local_flux.py` | **本地 FLUX.2-klein-4B 文生图**（免费离线，8–30s/张）；支持多 seed 取样 | `python local_flux.py (--prompt "…" \| --prompt-file p.txt) --out <png> [--seed 42] [--seeds 42,7,123] [--size 1024]` | 0 / 1 |

**建议顺序**（新 mod 从工程到线上）：

```
new_project.py --name <ModName>      # ⓪ 从零建工程骨架（.civ6proj + 目录 + .gitignore/.gitattributes
                                     #    + 自动派生 .modinfo）。已有工程跳过本步
modinfo_build.py --deploy            # ① cook 美术产物（内部调 cook_assets.py）→ 生成 modinfo → 部署 Mods
verify_mod_package.py                # ② 三处一致性 / 引用闭合体检
（改过 .lua 时）python ../scripts/check_lua_registration.py <工程>
（改过 SQL 时）../scripts/README.md「标准验证顺序」①–⑥
workshop_meta.py                     # ③ 生成 workshop.json（+ 介绍存档）
local_flux.py → workshop_cover.py    # ④ 底图 + 封面（模型只出无字底图）
../release/scripts/validate.ps1 → upload.ps1 → verify.ps1
workshop_item_check.py <id>          # ⑤ 线上复核（标题/描述/账号/标签未被顺带改掉）
```

> **新文明 / 新领袖**的数据与 LOC 推导见 `../civilization-authoring.md`、`../leader-authoring.md`；
> 美术（图标/立绘）→ `civ6-asset-forge`，3D 模型引用 → `civ6-art-reference`，BGM/语音 → `civ6-audio-pipeline`。

---

## 2. 路径收纳（本机绝对路径单一真源）

全部由 `_paths.py` 解析：`local_paths.json`（个人覆盖）→ 注册表 → 默认值。**换机器只改一处。**

跑 `python _paths.py` 可实时自检。当前解析结果：

| 键 | 含义 | 本机值 |
|---|---|---|
| `modbuddy` | ModBuddy 源工程根 | `D:\documents\Firaxis ModBuddy\Civilization VI` |
| `mods` | 游戏 Mods 加载目录 | `D:\documents\My Games\Sid Meier's Civilization VI\Mods` |
| `game` | 游戏本体（UI/Lua/XML 官方原文） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI` |
| `sdk_assets` | SDK Assets（artdef / 解包素材） | `…\Sid Meier's Civilization VI SDK Assets` |
| `sdk` | SDK 工具（ModBuddy / MSBuild） | `…\Sid Meier's Civilization VI SDK` |
| `workshop_ref` | 创意工坊参考件（289070） | `F:\Steam\steamapps\workshop\content\289070` |
| `uploader` | 工坊上传器（**非 Trimmed 构建，勿改**） | `D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe` |
| `sd_cpp` | 本地生图（stable-diffusion.cpp + FLUX 权重） | `%USERPROFILE%\sd-cpp` |
| `imagemagick` | ImageMagick（图标阈值/裁边用） | `C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe` |
| `luac` | Lua 语法检查（`luac -p`，Civ6 是 5.1 方言） | `E:\SoftWares\Lua\5.1\luac.exe` |
| `ws_root` | 上传临时工作区根（`content/` 用 junction 指向 Mods，见 `release/scripts/make_workspace.ps1`） | `%TEMP%\civ6-ws` |
| `steam_logs` | Steam 日志（查 workshop item id） | `F:\Steam\logs` |

生图渠道现状（哪个能用、哪个挂了、扩散模型出不了中文等实测坑）**已内化**在本 skill：
见 `reference/imagegen-channels.md`（渠道清单 + 失败模式 + `art/make-icon.ps1` 用法）。

本机内置的 `art/bin/texconv.exe`（DirectXTex, MIT）优先于 PATH 上的同名工具；
需要换版本时设环境变量 `TEXCONV` 或替换该文件，详见 `art/bin/README.md`。

---

## 3. 这些工具是在什么坑里长出来的（别把结论丢掉）

- **`modinfo_build.py`**：ModBuddy 只拷贝 `<Content Include>` 条目 —— 只写在 `InGameActions`
  而漏进 `Content` 的文件**不会被部署**，表现为"Mods 副本缺文件、modinfo 悬空引用"。
  工具因此把 `Content` 当拷贝清单，并在生成后强制做引用存在性检查。
- **`verify_mod_package.py`**：要同时看三处（源 / Mods / 上传工作区）。只比源与 Mods 会漏掉
  "上传工作区落后于 Mods"（曾经真发生过）；`--ws` 就是为这一步准备的。
  另：工作区 `content/` 改用 junction 后（见 `release/scripts/make_workspace.ps1`），
  Mods 与 ws 两列在物理上就是同一份文件，该列的"漂移"假红灯从根上消失。
- **`workshop_meta.py`**：`update` 模式**故意不写 title / visibility / tags** —— 省略的字段
  上传器不触碰，这是"只改介绍、不碰身份"的安全写法（写全字段反而有被顺带改掉的风险）。
- **`workshop_cover.py`**：中文标题**必须**由真实字体排版。扩散模型渲染中文得到形近伪字
  （实测 `人类玩家所有单位` → `义凵薊丨劦…`），拉丁长句也会掉字母（`CIVILIZATION` → `CIVILLZATION`）。
  另外**封面一律不署名**（项目约定，作者只写在 `.modinfo` 的 `Authors` 与代码里）。
  **预览图（`--preview`）的缩放执行端已迁到 `art/make_workshop_preview.py`**（默认 512×512）——
  本脚本只做排版，写完委托那条采定管线；原先各写一份 `resize()` 正是封面发糊的来源。
- **工坊预览图为什么会糊（`art/make_workshop_preview.py`）**：根因不是尺寸、也不是源图，
  而是**缩放方式**——`magick -resize` 不写 `-filter` 时走 **Mitchell（偏软）**，实测锐度
  2,592.6；`-filter Lanczos` 4,842.4；**Lanczos 逐级减半 + unsharp 13,047.4**（采定）。
  两条铁律：① **已达标 512 成品不要再缩**（工具默认直通，`--force-resize` 才重采样）；
  ② 别裸用 `magick -resize`。执行端改用 Pillow 是因为它**必须显式写 `Image.LANCZOS`**，
  从根上消灭"忘写 `-filter` 就发糊"。细节见 `art-pipeline.md` 第九·补节。
- **`local_flux.py`**：Google 生图（`gemini-*-image`）配额耗尽时，本地 FLUX 是唯一免费自动渠道；
  但它**不能出中文文字**，也不要拿它做图标（图标剪影走 `art/normalize_icon.py`：把已有主体图
  裁边/等比/居中并涂成白色剪影（`--color 255`、unit 图标用 `--role unit_icon`），再由
  `art/convert_art.ps1` 出 DDS/.tex；要**由文字直接生成**剪影则用**随包内置**的
  `art/make-icon.ps1`（`-Subject/-Out/-Seed`；模型目录用 `-SdDir`，默认取 `_paths.py` 的 `sd_cpp` 键，
  本机没有 sd-cpp 时需自备），用法与踩坑见 `reference/imagegen-channels.md`）。
- **`verify_mod_package.py`**：对**发布副本**做体检时，有两类差异是预期的、不计入问题：
  ① `Platforms/*/BLPs/**` 与 `*.dep` 源工程本就没有（AssetEditor/cooker 产物，只在 Mods 副本）；
  ② **美术引用管线文件**（见 `ART_PIPELINE_EXTS`）—— 按项目规范既不写进 `.civ6proj` 的 `<Content>`，
  也不写进 `.modinfo` 的 `<Files>`，由 cook 链路承载。

  ★ **`ImportFiles/` 之下不适用上述豁免**：那是显式导入通道，其下素材与其它 ImportFiles
  文件同等对待，须三处齐全，漏登记照报。

  加 `--strict` 可关掉以上全部放行、恢复逐字节 + 零未登记的严格口径。
- **`workshop_item_check.py`**：Steam API **忽略 `language` 参数**、只回默认变体，非英语变体
  只能靠上传器日志的 `Language variant 'x' updated.` 交叉验证；`result=9` ≠ 条目不存在。
  直连 Steam API 可能被 reset，工具已内置代理回落（`127.0.0.1:7897`）。
