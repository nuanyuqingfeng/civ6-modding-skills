# CHANGELOG — civ6-asset-forge

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
