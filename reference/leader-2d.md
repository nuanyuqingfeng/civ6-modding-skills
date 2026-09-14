← 返回 `SKILL.md` 路由

> **来源**：原 `civ6-leader-2d` skill 的 `SKILL.md`（234 行 / 13146 字节 / LF），已并入 `civ6-asset-forge`。
> 本文件正文为原文件**逐字搬运**（未改写、未精简任何实测规格），仅做结构性处理：
> 1. 去掉 YAML frontmatter —— 原文逐字保留于下方，触发词/边界已并入 `SKILL.md` 的 description；
> 2. 文末「作者与致谢」块上移至 `SKILL.md`（四类共用一份）；
> 3. 跨 skill 引用与移动后的 `reference/` 路径已同步（见 `CHANGELOG.md`「引用修正」）；
> 4. 原第四节「备份：不静默备份…」一条上移至 `SKILL.md`（四类共用，原文逐字保留于该节）；
>    脚本绝对路径 `…\skills\civ6-leader-2d\scripts\` 已更新为 `…\skills\civ6-asset-forge\scripts\`，
>    跨 skill 引用（忠诚度图标）已改为本 skill 内 `reference/loyalty-icon.md`。
> 本文件内 `scripts/…`、`templates/…`、`assets/…`、`reference/…` 的根目录 = `civ6-asset-forge/`。

原 frontmatter（逐字保留）：

```yaml
name: civ6-leader-2d
description: "Civ6 2D 领袖（立绘纸片人）建模注册：为 mod 领袖生成完整美术注册链（XLP 包 / Leaders.artdef / 平面几何 / 材质 / 灯光 / 环境光 / 贴图 / 行为资产 ast），支持任意数量的领袖与多语言占位；也支持用户提供近似 1:1 透明背景 PNG，自动生成 1024×1024 TEXTURE/OPACITY 素材。素材处理前必须先询问用户是否提供素材，默认不处理素材、仅生成注册文件。"
version: "1.0"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - leader
  - 2d
  - artdef
  - xlp
  - modding
models:
  recommended:
    - claude-sonnet-4
  compatible:
    - gpt-4o
    - deepseek-v3
languages:
  - zh
  - en
```

---

<!-- ↓↓↓ 以下为原 SKILL.md 正文逐字内容（未改写） ↓↓↓ -->

## 一、铁律：素材处理前必须询问

**开始任何 2D 领袖任务前，必须先询问用户是否提供了素材**（png/dds/fgx/wig 等）。询问模板：

> 本次任务是否已提供立绘素材？
>
> **素材要求：**
> - 格式：PNG，建议**透明背景**，尺寸**近似 1:1**
> - 处理后会生成两张 `1024×1024` 贴图：
>   - **底色图（TEXTURE）**：立绘本身，保留颜色和透明背景，用于显示人物外观。
>   - **透明度遮罩（OPACITY）**：黑白剪影图——人物主体是纯白、背景是纯黑，告诉游戏哪里显示、哪里透明。
>
> 请选择：
> - **已有素材可直接处理**：提供 PNG 路径，我会自动生成 TEXTURE / OPACITY。
> - **暂无素材**：本次只生成注册文件，素材由你稍后自行添加。
>
> 若选择直接处理，请同时说明：
> - 只要 PNG（默认输出到 `D:\desktop`），还是
> - 需要一步到位 `tex+dds`（输出到项目 `Textures/`，细节见「输出规则」）。

**未提供素材时的默认行为**（用户未明确要求时不得主动生成素材）：
1. 生成全部注册文件（XLPs / artdef / geo / mtl / lrg / env / tex / ast）
2. `.tex` 的 `SourceFilePath` 指向占位路径，需用户在 ModBuddy 导入素材后更新
3. 通用素材（fgx/wig 平面模型、环境光 dds）需另行复制，脚本不做

**已提供立绘素材时的处理入口：**
- 从项目 SQL/XML 中找到该领袖的精确 `LeaderType`（如 `LEADER_CANTARELLA_QYQXP`）
- 调用 `scripts/process_leader_png.py` 生成：
  - `{LeaderType}_TEXTURE.png`
  - `{LeaderType}_OPACITY.png`

## 二、任务路由

| 任务 | 处理 |
|------|------|
| 为新领袖生成全套注册文件 | → 第三节：运行 `gen_leader_2d.py` |
| 已有注册文件，只补/改某个文件 | → 直接用对应模板手动改，命名见第四节 |
| 添加 config（领袖互斥/同名） | → 不归本 skill 管，参考项目 Data 下 Config SQL（DuplicateLeaders 表） |
| 立绘素材处理（用户 PNG → 1024×1024 TEXTURE/OPACITY） | → `scripts/process_leader_png.py`；默认输出到 `D:\desktop`；指定 `--tex-dds` 时输出到项目 `Textures/` 并同步 `.tex`/DDS |
| 忠诚度图标（文明 Loyalty Overlay/Pressure + 战略视图 sprite） | → **引用链路**：本 skill `reference/loyalty-icon.md`（4 张 PNG 合成 + XLP/ArtDef/mtl/ast 注册链） |
| 其他素材导入（png → dds，图标/背景等） | → **引用链路**：`civ6-modding` skill 的 `art-pipeline.md`（素材询问铁律 + art_manifest.json + convert_art.ps1 自动转换，含 .tex 生成与 XLP 实存过滤） |

## 三、标准工作流（生成注册文件）

### 1. 收集信息

从项目 SQL/XML 获取领袖列表（`LeaderType`），例如：

| 领袖 | LeaderType | FX 缩写 |
|------|-----------|---------|
| 卡提希娅 | `LEADER_CARTETHYIA_QYQXP` | `CTTH` |
| 芙露德莉斯 | `LEADER_FLEURDELYS_QYQXP` | `FDL` |

- **FX 缩写**：领袖名字缩写（用于 ast 音频前缀 `{ABBR}_{FX}_*_A`），无现成表时询问用户
- **文明缩写 ABBR**：如 示例工程 → `RGN`
- **包名 PACK**：默认取工程目录名小写（如 `myciv_qyqxp`），XLP 包路径为 `/leaders/leader_{PACK}`

### 2. 运行生成脚本

```bash
python %USERPROFILE%\.agents\skills\civ6-asset-forge\scripts\gen_leader_2d.py \
  --project "<工程路径>" \
  --pack <包名> \
  --abbr <文明缩写> \
  --leaders "LeaderName:FX缩写,LeaderName2:FX2,..."
```

生成文件清单（Leader 与几何名按命名规范自动推导）：

| 目录 | 文件（每领袖） | 说明 |
|------|--------------|------|
| `XLPs/` | `leader_{PACK}.xlp`（聚合） | Leader 条目包 |
| `XLPs/` | `Leader_LightRigs.xlp`（聚合） | LightRig 条目包 |
| `ArtDefs/` | `Leaders.artdef`（聚合） | 领袖集合定义（Leader/LightRig/ColorKey/Background 槽位） |
| `Geometries/` | `LEAD_{ABBR}_{Name}_QYQXP.geo` + `_Camera.geo` | 平面几何 + 摄像机 |
| `Materials/` | `LEAD_{ABBR}_{Name}_QYQXP_Material.mtl` | 材质（引用 TEXTURE/OPACITY） |
| `LightRigs/` | `{Name}_QYQXP_LightRig.lrg` | 灯光（引用 env） |
| `EnvironmentLights/` | `{Name}_QYQXP_Environment.env` | 环境光（引用 dds） |
| `Textures/` | `LEADER_{NAME}_QYQXP_TEXTURE.tex` + `_OPACITY.tex` | 贴图定义 |
| `Assets/` | `LEAD_{ABBR}_{Name}_QYQXP.ast` | 行为资产（6 外交槽位 + NEUTRAL） |

### 2.5 立绘素材处理（可选）

### 层级 1：自行处理（优先）

具备图片处理能力（vision-tools、可调用的图片编辑/生图模型）时，自行读图处理：

- **先读图并分析内容**：确认主体位置、透明背景、边缘是否贴边、头顶/脚下留白、整体构图是否适合裁成正方形。
- **思考怎么裁剪合适**：默认仍**迁就短边**——按 `min(宽, 高)` 居中裁剪为正方形，再缩放到 `1024×1024`；但如果主体明显偏左/偏右/偏上，可基于分析适当平移裁剪框，避免裁掉主体边缘。
- **难以决定时先询问用户**：如果主体贴边、多主体、构图特殊，或你无法判断怎样裁剪最合适，先询问用户期望的裁切范围/保留重点，再继续处理。
- 生成 `{LeaderType}_TEXTURE.png` 与 `{LeaderType}_OPACITY.png`（输出与命名见「输出规则」）。

### 层级 2：检查本机工具

若无法自行处理，再检查本机固定工具（**仅简单查找，不自动安装、不扩大搜索**）：

- Python + Pillow：运行 `process_leader_png.py`。
- texconv：仅检查 PATH 或固定目录；找不到时不自动安装。
- 若脚本因依赖缺失失败，进入层级 3。

```bash
python %USERPROFILE%\.agents\skills\civ6-asset-forge\scripts\process_leader_png.py \
  --input "<源PNG路径>" \
  --leader-type "LEADER_CANTARELLA_QYQXP"
```

> 也可用 `--project <工程路径> --leader-name <英文名>` 自动从项目 SQL/XML 查找 LeaderType。
> 若 texconv 不在默认位置，可让用户提供路径并用 `--texconv-path <完整路径>` 指定。
> 若读图后决定使用自定义裁剪框，可加 `--crop left,top,side`（原图坐标），例如 `--crop 100,50,800`。

### 层级 3：调用子代理 / 询问用户

- 向用户确认 Python（Pillow）/ texconv 的实际安装路径。
- 或询问是否允许调用其他有图片处理能力的模型。
- 用户提供工具路径（如带 Pillow 的 Python 解释器、texconv 路径）后重试；

---

**输出规则：**
- 默认仅生成 PNG，输出到 `D:\desktop`：
  - `{LeaderType}_TEXTURE.png`
  - `{LeaderType}_OPACITY.png`
- 若用户要求一步到位（`--tex-dds`）：
  - 输出到项目 `<project>\Textures\`
  - 同步生成/更新 `.tex`，并将 `SourceFilePath` 指向项目内 PNG
  - 尝试调用 texconv 生成 DDS（TEXTURE：`R8G8B8A8_UNORM`；OPACITY：`R8_UNORM`）

**生成规则：**
- TEXTURE：1024×1024，保留透明背景（裁剪规则见「层级 1」）。
- OPACITY：以 PS Ctrl+点击图层选区语义为准，非全透明像素（`alpha > 0`）→ 纯白，全透明 → 纯黑，输出不透明黑白 PNG。

### 3. 素材文件（未提供素材时跳过）

| 素材 | 来源 | 说明 |
|------|------|------|
| `.fgx` / `.wig`（主体 + Camera） | 从已建成工程复制 | **通用平面模型，跨工程逐字节一致**（MD5：主体 fgx `D13E5D864C121D9DA51500A07DFE0DD4` / wig `B9C116E082A7DD783A89E1684ED9C0B5`；Camera fgx `7F8319922265FD53841D7C15469E4E19` / wig `C1F6B44B222FA827B683A26F411CD53E`），复制后重命名即可 |
| `{Name}_QYQXP_Environment.dds` | 从已建成工程复制 | **通用环境光**（Hojo，MD5 `100A9AF5C487BDF8D1BD84AFF854F1A6`），每领袖各留一份 |
| 立绘 png（TEXTURE / OPACITY） | 用户提供 | 用 `process_leader_png.py` 生成 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`（1024×1024）；默认输出桌面，`--tex-dds` 时输出项目 `Textures/` 并同步 `.tex`/DDS |

### 4. 更新工程文件

- `*.civ6proj`：新增 `ArtDefs` 文件夹 + 3 个 Content Include：
  - `XLPs\leader_{PACK}.xlp`
  - `XLPs\Leader_LightRigs.xlp`
  - `ArtDefs\Leaders.artdef`
- **Geometries/Materials/LightRigs/EnvironmentLights/Textures/Assets 不需注册**——构建时自动扫描编译进 `Platforms\Windows\BLPs\*.blp`
- `*.Art.xml`：新增/修改 `XLPs\`、`ArtDefs\` 后**必须重新生成**——运行
  `python <civ6-modding skill>\art\gen_modartxml.py <projectRoot> --check`
  （差异人工确认后加 `--write` 写回；脚本按项目实存文件重算
  artConsumers/gameLibraries/requiredGameArtIDs，替代手工补 Leader/LeaderLighting 引用）
- **备份**：见 `SKILL.md`「不静默备份」节（四类共用，原条已上移）。

### 5. 验证清单

- [ ] 所有生成 XML 可解析（无残留 `{占位符}`）
- [ ] `leader_{PACK}.xlp` 条目数 = 领袖数；`Leaders.artdef` 块数 = 领袖数
- [ ] geo 的 fgx/wig 引用名与磁盘文件名一致（主体 + `_Camera`）
- [ ] mtl 引用 `{NAME}_QYQXP_TEXTURE` / `_OPACITY`；lrg 引用 env；env 引用 dds
- [ ] ast 的 GeometrySet 引用 Camera geo + 主体 geo + Material，FXName 为 `{ABBR}_{FX}_{动作}_A`
- [ ] 素材文件（若提供）复制后哈希与源一致
- [ ] 若已处理立绘：TEXTURE / OPACITY PNG 均为 `1024×1024`
- [ ] OPACITY 只包含纯黑和纯白两种颜色
- [ ] 文件名使用 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`
- [ ] 一步到位时 `.tex` 的 `SourceFilePath` 指向项目内 PNG，且 DDS 已生成（或已明确提示未生成）

## 四、命名规范（生成脚本自动推导，手动修改时遵循）

| 对象 | 格式 | 示例 |
|------|------|------|
| XLP EntryID | `LEADER_{NAME}_QYQXP` | `LEADER_CARTETHYIA_QYQXP` |
| XLP ObjectName / geo | `LEAD_{ABBR}_{Name}_QYQXP` | `LEAD_RGN_Cartethyia_QYQXP` |
| Camera geo | `LEAD_{ABBR}_{Name}_QYQXP_Camera` | `LEAD_RGN_Cartethyia_QYQXP_Camera` |
| Material | `LEAD_{ABBR}_{Name}_QYQXP_Material` | `LEAD_RGN_Cartethyia_QYQXP_Material` |
| LightRig | `{Name}_QYQXP_LightRig` | `Cartethyia_QYQXP_LightRig` |
| Environment | `{Name}_QYQXP_Environment` | `Cartethyia_QYQXP_Environment` |
| Texture | `{LeaderType}_TEXTURE` / `{LeaderType}_OPACITY` | `LEADER_CARTETHYIA_QYQXP_TEXTURE` |
| AST | `LEAD_{ABBR}_{Name}_QYQXP` | `LEAD_RGN_Cartethyia_QYQXP` |
| XLP 包名 | `/leaders/leader_{PACK}` | `/leaders/leader_myciv_qyqxp` |

**AST 音频 FXName**：`{ABBR}_{FX}_{动作}_A`，动作枚举：`FIRST_MEET` / `DECLARE_WAR_FROM_HUMAN` / `DECLARE_WAR_FROM_AI` / `KUDO_EXIT` / `WARNING_EXIT` / `DEFEAT_FROM_AI`。

## 五、关键架构事实

1. **平面模型与环境光均为通用资产**：.fgx/.wig 与环境光 dds 直接复制改名即可，无需建模（哈希见第三节素材表）。
2. **聚合模板结构**：`leader_{PACK}.xlp` 用 `<!-- LEADER_BLOCK_START/END -->` 标记领袖块，脚本按领袖数复制；artdef 同理（容器内每个领袖块含 Leader/LightRig/ColorKey/Background 4 个 BLPEntry + 2 个 StringValue）。
3. **`{PACK}` 占位**：`leader_{PACK}` 与 `/leaders/leader_{PACK}` 保持 `leader_` 前缀不变；仅 `{PACK}` 部分替换。
4. **Camera geo 的骨骼名/模型名**是引用官方 `LEAD_ARAB_Saladin_Camera` / `LEAD_JAPA_Hojo_Camera`（.ma 源路径来自 Hojo），**不要改动**——这是官方共享摄像机资产。

## 六、参考工程（素材复制来源）

| 工程 | 路径 |
|------|------|
| 示例工程（本工程） | `D:\documents\Firaxis ModBuddy\Civilization VI\示例工程\示例工程` |
| 工程 A | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 A\工程 A` |
| 工程 C | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 C\工程 C` |
| 工程 B | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 B\工程 B` |

## 七、交付要求

- 交付说明中包含：生成的文件清单、素材复制清单（哈希验证结果）、"待用户提供素材"清单、civ6proj 改动说明
- 素材相关（立绘 png/dds 导入）一律标注"待用户处理"，除非用户明确要求代处理
- 若已用 `process_leader_png.py` 处理立绘，交付说明中列出生成的 TEXTURE/OPACITY PNG、`.tex` 更新结果、DDS 生成结果
