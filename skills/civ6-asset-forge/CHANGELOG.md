# CHANGELOG — civ6-asset-forge

## 2026-09-17/18 · 类别③「单位晋升图标」生成管线作废（仅保留尺寸说明）

**来源**：用户裁决 —— 类别③（promotion icon）的整条**生成管线**是**失败尝试的遗留**，不再需要；
**只保留一份"尺寸说明"**。本次只改本 skill，其它 4 个 skill 未动。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/promotion-icon-sizes.md` | **唯一保留**的类别③文档：只写尺寸/格式事实（`Promotions32.dds` 32px 图集 / `Promotion_Button*` 106×106×5 / 占幅 75%·12.5%·6% / glyph 参数 / 四类金属配色 / 40 格分类 / 注册目标 / `.tex` 约束），**不含**管线步骤、提示词与脚本用法 |

### 删除（逐文件已 grep 证明"引用它的地方只有类别③"）

| 文件 | 依据 |
|---|---|
| `scripts/compose.py` | `SKILL.md` / `TOOLS.md` / `TOOLS.overrides.json` / `reference/promotion-icon.md` / `prompts-metal-recolor.md` —— 全部类别③；**实测未被 `build_icon_set.py` import**（`TOOLS.md` 原注"也被 build_icon_set 调用"系误，一并随重跑消失） |
| `scripts/recolor_template.py` | 同上 5 处，全部类别③ |
| `scripts/slice_atlas.py` | `SKILL.md` / `TOOLS.md` / 自身 docstring，全部类别③ |
| `scripts/verify.py` | `SKILL.md` / `TOOLS.md` / `reference/promotion-icon.md` / `reference/promotion-icon/prompts.md` |
| `scripts/vcheck_multi.py` | `SKILL.md` / `TOOLS.md` / `TOOLS.overrides.json` / `reference/promotion-icon.md` |
| `scripts/__pycache__/vcheck_multi.cpython-314.pyc` | 已删模块的编译产物（`.gitignore` 已忽略，可再生） |
| `assets/TEMPLATE_{platinum,gold,silver,bronze}_{gt32,gt512,gt1024,1024}.png`（16 个） | 类别③ 生图模板与像素级 ground truth |
| `assets/white_glyph_samples/`（5 个：BATTLECRY / HOLD_THE_LINE / MARKSMAN / RANGER / VOLLEY） | 类别③ 白剪影样例（文件名全部属 `Promotions32` 的晋升） |
| `assets/vanilla_promotion_sheet.png` | 类别③ 原版盾形整表（840×150，五边形盾形金属底） |
| `reference/promotion-icon.md` | 类别③ 分册（原 `civ6-promotion-icon` 的 `SKILL.md`） |
| `reference/promotion-icon/specs.md`、`prompts.md`、`prompts-metal-recolor.md` | 类别③ 实测规格 / 提示词手册（`prompts-metal-recolor.md` 系 2026-09-17 当天新增，同属作废管线） |

删除后 `reference/promotion-icon/` 已空，目录一并移除。

### 保留（经证据核验**不属**类别③，未删）

| 文件 | 依据 |
|---|---|
| `scripts/verify_badge.py` | **类别① 总督**：八边形 24px 徽章验证器（`OFFICIAL_SPANS` y=3..20 共 18 行、最宽 18px），被 `SKILL.md` ① 行与 `reference/governor-art.md` 引用 |
| `assets/TEMPLATE_badge24_canonical.png` | **类别①**：24×24，逐行跨度与 `verify_badge.py` 的 `OFFICIAL_SPANS` **1:1 零差异**（八边形暖橄榄金） |
| `assets/TEMPLATE_badge24_canonical_x16.png` | **类别①**：上者的放大对照图（512×512，最近邻 **512/24 ≈ 21.3×** 铺满画布，内容 bbox 426×426）——**文件名里的 `x16` 与实测倍率无关**，勿按字面理解 |
| `assets/REF_official_promotions24_x6.png` | **类别①**：1152×144 = **8×1 @24px × 6 倍放大**。逐格按 6×6 块中心取样还原成 24px 后，**第 1~7 格与 `verify_badge.py` 的 `OFFICIAL_SPANS` 逐行完全一致**（第 0 格是 21 行的 generic 变体）；与 `governor-art/specs.md` §2.3「`XP1/XP2_GovernorPromotions24.dds` 24px **8×1**」、`governor-art.md` §一 第 3 行完全吻合 → 是官方**总督**晋升徽章图集（`GovernorPromotions24` 属类别①） |

> 上表 4 个文件均**无任何文本引用**（属素材级引用），归类依据是**内容 + 尺寸实测**，非文本引用。

### 改动

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 「六类」→「五类」（description / §一 标题 / §二 路由判定 / §三 标题 / §六 标题与 §6.1 标题 / §七 标题 / §八 目录树 / §九 标题）；**删除类别③ 行**（§一 分类表、§三 素材询问表、§6.1 声明层落点、§七 校验表）；§二 路由表 ③ 行改指 `reference/promotion-icon-sizes.md` 并注明"仅尺寸规格，管线已废"；§八 脚本表删 5 行（18 → 13）；§一 表下与 §6.1 表下补作废说明 |
| `TOOLS.overrides.json` | 删 `scripts/compose.py` / `scripts/recolor_template.py` / `scripts/vcheck_multi.py` 三条覆盖 |
| `reference/governor-art.md` | 「边界」节 ③ 指向改为 `reference/promotion-icon-sizes.md`（**CRLF 保持**） |
| `reference/governor-art/specs.md` | §2.3 结论行同样改指 `reference/promotion-icon-sizes.md`（**CRLF 保持**） |

### 待办（落在其它 skill / 生成器侧，本次未动）

- `civ6-modding/tools/skill_manifest.py` 的 `THIRD_PARTY["civ6-asset-forge"]` 仍列
  `compose.py` / `recolor_template.py` / `slice_atlas.py` / `verify.py` 四条 —— 该节由表**逐条原样输出**（不校验文件是否存在），
  **不清理则重跑生成器会把已删脚本写回 `TOOLS.md` 的「第三方依赖」节**。
- `civ6-modding/art/survey_icon_atlas.py`（"与 `slice_atlas.py` 的分工"节）与
  `civ6-modding/reference/FAMILY_INDEX.md`（第 55 / 61 行）仍指向已删的 `promotion-icon.md` / `slice_atlas.py`。
- 本 skill `TOOLS.md` 的工具表与依赖节按文件内"**勿手改表格**"约定**未手改**，待重跑 `skill_manifest.py` 刷新。

---

## 2026-09-17 · 新增类别⑥「历史时刻插画」（MomentIllustrations）

**来源**：用户提供官方历史时刻模板（`历史图片模板（新）/1..18.psd`）+ 用户既定 PS 工作流
（Ctrl+点击模板层载入选区 → 切目标图层 → Ctrl+J 复制 → 单独导出）+ 对原版 240 张时刻图的实测反推。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/moment-illustration.md` | 类别⑥ 完整分册：规格 / 18 张官方形状模板 / 手工与脚本流程 / 接线 / 验证 |
| `scripts/apply_moment_template.py` | 套官方形状模板（`--list`/`--template N`/`--auto`/`--dds`），并报告覆盖率对照原版区间 |
| `scripts/verify_moment.py` | 只读校验器：**alpha 覆盖率下界**、456×332、类别、XLP 登记、`MomentIllustrations` 配对 |

### 改动

| 文件 | 说明 |
|---|---|
| `SKILL.md` | description/触发词加历史时刻系列；「五类」→「六类」；路由 / 素材询问 / 声明层 / 校验表 / 目录结构均补类别⑥ |

### 关键实测结论（写进 reference）

- **画布 456×332、`m_ClassName=UserInterface`**：原版 240 张 `Moment_*.dds` 全部如此。
- **alpha 覆盖率 83.0%~98.5%**：原版 240 张实测区间（min 83.0 / 中位 88.0 / max 98.5），**无一张 <50%**。
  官方每张时刻图都用同一族**卡片形状蒙版**裁出，故覆盖率有下界。
- **18 张模板 = 官方形状族**：原版 240 张对 18 模板做二值 IoU，**全部 ≥0.80**（0.90–0.95 占 22.9%、
  0.80–0.90 占 75.8%），且 18 形状两两互不重复 → 证实其为官方完整形状族。
  其中 `4.psd` 的数字层为空（作者中间稿），脚本自动跳过。
- **漏套模板的实际后果**：某工程 `MOMENT_UNIT_GONDOLA_RGN` / `MOMENT_UNIT_PATRICIUS_RGN`
  覆盖率仅 **14.5% / 15.3%**（最佳模板 IoU 仅 0.30）→ 即未套任何模板，卡片形状不对。
- **`Texture` 列带 `.dds` 后缀**（与 `Players.Portrait` 不带后缀的惯例相反，易写错）。

### 已验证

- `apply_moment_template.py` 端到端：把一张 94.1% 的「实心矩形（未套模板）」输入套模板后，
  覆盖率落入 **83.8%~89.5%**（官方区间内）；`--dds` 产出单 mip RGBA8。
- `verify_moment.py` 在 示例工程 上跑出 **2 个真缺陷**（上述 14.5%/15.3%）；
  一度误报 `MOMENT_DISTRICT_GONDOLA_RGN`（82.4%，仅低于原版下界 0.6pp 且软边正常 41.6%），
  已把默认下界从 83.0 调为 **75.0**（留 8pp 容差）并降级为 warn。

---

## 2026-09-17 · 新增类别⑤「UI 领袖立绘 / 选人界面背景」（Suk 适配）

**来源**：在 `示例工程` 上首次落地并实测通过的 Sukritact's Civ Selection Screen 适配流程，
用户确认「实测效果很好」后要求固化为备选管线。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/ui-leader-portrait.md` | 类别⑤ 完整分册：触发判定 / 素材询问模板 / 实测规格 / **类别陷阱** / 接线 / 验证顺序 |
| `scripts/gen_suk_portrait.py` | 素材 + `UPDATE Players` + XLP + `civ6proj` 接线一体生成器（幂等，`--check`/`--write`） |
| `scripts/verify_suk_portrait.py` | 只读校验器（类别陷阱 / 尺寸对齐 / XLP 登记 / 悬空引用 / 行尾） |

### 改动

| 文件 | 说明 |
|---|---|
| `SKILL.md` | frontmatter description 与触发词加 Suk 系列；「四类」→「五类」；路由表 / 素材询问表 / 声明层落点 / 校验表 / 目录结构均补类别⑤ |
| `civ6-modding/art/dds_io.py` | **新增**：Civ6 单 mip RGBA8 DDS 读写（纯 Python，带 `--selftest` 往返自检）。原 `regen_atlas_tiers.py` 内的头构造逻辑抽为共享模块 |
| `civ6-modding/art/gen_tex.py` | **修正 P0 类别陷阱**：`is_fallback()` 原为纯前缀判断，会把 `FALLBACK_NEUTRAL_*_Suk` 误判成 `Leader_Fallback`（它是 `UITexture` XLP 里的 UI 立绘，应为 `UserInterface`），导致 cooker「类别与参数不匹配」→ 静默变 error asset。现由 `_UI_PORTRAIT_SUFFIXES` 显式排除 |

### 已验证

- 生成器对 `示例工程` 既有 12 组交付物 **逐字节复现**（6 立绘 + 6 背景，含 DDS 头）；
- 校验器在真实工程 PASS，且在注入 10 类缺陷的最小工程上**全部命中**（非空跑）；
- `gen_tex.py` 修正后：`_Suk` → `UserInterface`，真 3D 回退 `FALLBACK_NEUTRAL_X` → 仍为 `Leader_Fallback`。

---

## 2026-09-14 · v1.0 · 由 4 个 skill 合并而来（初始版本）

本 skill 由 4 个「美术素材合成类」skill 合并而成。四者**同一骨架换参数**：
给定 PNG → 确定性合成器（Python/Pillow）→ 原版风格素材 → 注册链（`.dds`/`.tex` + xlp/artdef/mtl/ast
+ `Art.xml` + `.civ6proj`）→ 校验器。合并后注册链逻辑只在 `SKILL.md` 维护一份，
各类别专属实测规格（尺寸/坐标/配色/像素参数/完整哈希）**逐字保留**在 `reference/*.md`。

### 一、来源仓库与最后的 commit

| 原 skill | 最后 commit | 提交时间 | 末次提交标题 | 并入落点 |
|----------|-------------|---------|-------------|---------|
| `civ6-loyalty-icon` | `8f97cf686b65cdbd7eb618f579caa2c8b826f2da` | 2026-09-14 19:11:44 +0800 | docs: 剩余去冗余项 | `reference/loyalty-icon.md` + `scripts/` + `templates/` |
| `civ6-promotion-icon` | `b5b5a170b407ff760ae91516ba7eb620c6ac3536` | 2026-09-14 19:10:35 +0800 | docs: 剩余去冗余项 | `reference/promotion-icon.md` + `reference/promotion-icon/` + `scripts/` + `assets/` |
| `civ6-governor-art` | `ceb03d9f489c326d5f12246c84a8156b3d2ea012` | 2026-09-14 19:10:36 +0800 | docs: 剩余去冗余项 | `reference/governor-art.md` + `reference/governor-art/` + `scripts/` + `assets/` |
| `civ6-leader-2d` | `08767d49703d19d55d9edf2d5c69182185913e60` | 2026-09-14 19:10:35 +0800 | docs: 剩余去冗余项 | `reference/leader-2d.md` + `scripts/` + `templates/` |

四个原仓库合并前工作区均干净（`git status --porcelain` 空）；合并完成后原目录已删除。

### 二、文件级合并结果（零丢失）

原 4 个 skill 共 **90 个 git 跟踪文件**（另有 8 个 `.gitignore` 排除的 `__pycache__/*.pyc`），
全部并入，逐文件 SHA256 核对通过：

| 原 skill | 跟踪文件数 | 并入 | 说明 |
|----------|-----------|------|------|
| `civ6-loyalty-icon` | 30 | 30 | `SKILL.md` → `reference/loyalty-icon.md`；3 脚本；1 光晕模板 + `loyalty_chain/`(12) + `religion_chain/`(11) |
| `civ6-promotion-icon` | 32 | 32 | `SKILL.md` → `reference/promotion-icon.md`；2 附属文档 → `reference/promotion-icon/`；5 脚本；22 素材 |
| `civ6-governor-art` | 12 | 12 | `SKILL.md` → `reference/governor-art.md`；3 附属文档 → `reference/governor-art/`；3 脚本；3 素材 |
| `civ6-leader-2d` | 16 | 16 | `SKILL.md` → `reference/leader-2d.md`；2 脚本；11 模板 |
| 4 × `.gitattributes` / `.gitignore` | 8 | 2 | 四份内容**逐字节相同**（SHA256 `7847EB84…` / `CA4140C9…`），各留一份 |

- **脚本未改名**：13 个脚本 basename 互不冲突（`verify.py` 与 `verify_badge.py` 是不同文件），
  因此无需加类别前缀，`SKILL.md` / `reference` 中的脚本名引用保持有效。
- **素材/模板未改名**：`assets/`（25）与 `templates/`（35）合并后无同名冲突。
- 未并入：`scripts/__pycache__/*.pyc`（loyalty 2 / governor 2 / leader-2d 2，共 6 个；promotion 无）
  —— `.gitignore` 排除的可再生运行缓存，原仓库亦未跟踪，脚本运行即自动重建。

### 三、引用修正（仅限"移动导致的失效引用"，逐条）

| 文件 | 原引用 | 改为 |
|------|--------|------|
| `reference/loyalty-icon.md` | `civ6-leader-2d` skill（2D 领袖相关） | 本 skill `reference/leader-2d.md` |
| `reference/leader-2d.md` | `civ6-loyalty-icon` skill（忠诚度图标链路） | 本 skill `reference/loyalty-icon.md` |
| `reference/leader-2d.md` | `C:\...\skills\civ6-leader-2d\scripts\gen_leader_2d.py`、`...\process_leader_png.py` | `C:\...\skills\civ6-asset-forge\scripts\...`（2 处） |
| `reference/leader-2d.md` | 第四节「备份：不静默备份…」 | 上移至 `SKILL.md` 第四节（四类共用，原文逐字保留），此处改为指向 |
| `reference/governor-art.md` | `reference/specs.md`、`reference/palette.json`、`reference/inventory.md` | `reference/governor-art/specs.md`、`…/palette.json`、`…/inventory.md` |
| `reference/governor-art.md` | `civ6-leader-2d` 管线 / `civ6-leader-2d/scripts/process_leader_png.py` | `reference/leader-2d.md` / `scripts/process_leader_png.py`（见 `reference/leader-2d.md`） |
| `reference/governor-art.md` | 单位晋升走 `civ6-promotion-icon` skill | 单位晋升走 `reference/promotion-icon.md` |
| `reference/promotion-icon.md` | `reference/prompts.md`、`reference/specs.md`、裸 `specs.md`（共 6 处） | `reference/promotion-icon/prompts.md`、`reference/promotion-icon/specs.md` |
| `reference/governor-art/specs.md` | `reference/inventory.md`、`reference/palette.json`、裸 `palette.json`、`civ6-promotion-icon` skill | `reference/governor-art/…`、`reference/promotion-icon.md`（3 处） |
| `reference/promotion-icon/prompts.md` | 裸 `specs.md` | `reference/promotion-icon/specs.md`（1 处） |
| `scripts/verify_badge.py`（注释） | `来自 reference/specs.md 实测` | `来自 reference/governor-art/specs.md 实测` |
| `scripts/build_icon_set.py`（注释） | `全部来自 reference/specs.md 的 1:1 实测` | `全部来自 reference/governor-art/specs.md 的 1:1 实测` |
| `scripts/gen_leader_2d.py`（注释） | `根据 civ6-leader-2d skill 的 templates/ 模板` | `根据 civ6-asset-forge skill 的 templates/ 模板` |

保留不动的引用：`civ6-modding`（art-pipeline / `gen_modartxml.py`）与 `civ6-art-reference` 均为独立 skill，仍然有效。

### 四、换行风格（逐文件按原值保留，未统一）

- **LF**：loyalty 的 `SKILL.md`、3 个脚本、`templates/loyalty_chain/**`（12 个，含 `.artdef`/`.ast`/`.mtl`/`.tex`/`.xlp`）；
  promotion 的全部文本文件（`SKILL.md`、2 附属文档、5 脚本）；governor 的 `reference/inventory.md`、`scripts/edge_gradient.py`、
  `scripts/verify_badge.py`；leader-2d 的全部文本文件（`SKILL.md`、2 脚本、11 模板）；本仓库新写的 `SKILL.md`、`CHANGELOG.md`。
- **CRLF**：governor 的 `SKILL.md`（→ `reference/governor-art.md`）、`reference/specs.md`（→ `reference/governor-art/specs.md`）、
  `reference/palette.json`（→ `reference/governor-art/palette.json`）、`scripts/build_icon_set.py`；
  loyalty 的 `templates/religion_chain/**`（11 个）。
- 说明：任务书假设"loyalty/promotion/leader-2d 全 LF、governor 全 CRLF"，**逐字节实测不符**——
  真实分布见上（loyalty 的 `religion_chain/` 是 CRLF，governor 有 3 份文本是 LF）。本仓库按**每个文件的实际值**保留。
- `.gitattributes` 沿用原约定 `* text=auto eol=lf`；索引内统一 LF，工作区保留各自原换行（与原仓库行为一致）。

### 五、结构变化（合并后新增/重组）

- 新增 `SKILL.md`（路由 + 四类共用链条/铁律/验证顺序，共用内容只写一份）与 `CHANGELOG.md`（本文件）。
- 原 4 份 `SKILL.md` → `reference/{loyalty-icon,promotion-icon,governor-art,leader-2d}.md`：
  正文逐字搬运，仅去掉 frontmatter（在文件头部以 yaml 块**逐字保留**）与文末「作者与致谢」（上移 `SKILL.md` 一份）。
- 原 `reference/specs.md` 同名冲突（promotion 与 governor 各一份）→ 按类别归入 `reference/<类别>/` 子目录。
