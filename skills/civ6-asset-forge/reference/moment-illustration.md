← 返回 `SKILL.md` 路由

> **来源**：2026-09-17 由用户提供的官方历史时刻模板（**已随 skill 内置**：`templates/moment_illustration/1..18.psd`）
> + 用户既定 PS 工作流 + 对原版 240 张时刻图的实测反推，固化为此分册。
> 实测数据与脚本：`scripts/apply_moment_template.py`、`scripts/verify_moment.py`；模板用法见同目录 `README.md`。

# 历史时刻插画（Historical Moment Illustration）

## 一、这是什么 / 什么时候用

Civ6 的**历史时刻**（Historic Moment）在触发时会弹出一张**插画卡片**。
`MomentIllustrations` 表把「某类时刻 + 某个游戏对象」映射到一张贴图：

```xml
<MomentIllustrations>
  <Row MomentIllustrationType="MOMENT_ILLUSTRATION_UNIQUE_UNIT"
       MomentDataType="MOMENT_DATA_UNIT"
       GameDataType="UNIT_FELINE_KITTEN"
       Texture="Moment_UniqueUnit_Feline.dds"/>
</MomentIllustrations>
```

**典型用法**：为自己的**特色单位 / 特色区域 / 特色建筑 / 特色改良 / 自定义总督**
配专属插画（原版 13 类时刻类型里，这 5 类最常被 mod 覆盖）。

**本类不做**：
- 不做 `MomentIllustrationType` 的**新增**（那是 `MomentIllustrationTypes` 表级改动，属玩法侧；
  且原版 13 种已覆盖绝大多数场景）
- 不做 `Moments` 表（时刻**本体**的定义，那是游戏核心机制，不是插画）

## 二、规格（实测）

| 项 | 值 | 依据 |
|---|---|---|
| 画布 | **456×332** | 原版 240 张 `Moment_*.dds` **全部**为 456×332；项目既有 16 张亦同 |
| 像素格式 | 未压缩 RGBA8、**单 mip** | 与其它 UI 贴图同 |
| `m_ClassName` | **`UserInterface`** | 原版与项目实测一致 |
| `m_Tags` | 单条 `UserInterface` | 同上 |
| **alpha 覆盖率** | **83.0% ~ 98.5%** | 原版 240 张实测区间（min 83.0 / 中位 88.0 / max 98.5） |
| 注册目标 | `UI_PrideMoments.xlp`（`m_ClassName=UITexture`，`PackageName=UI/PrideMoments`） | 原版 pantry + 项目既有 XLP |

> ⚠ **覆盖率是最有用的机械判据**：官方每张时刻图都是**同一族卡片形状蒙版**裁出来的，
> 所以**原版 240 张不会低于 83%**。而 `verify_moment.py` 的**校验门槛默认 75%**
> （原版下界留 8pp 容差，避免把软边差异误报；见 `CHANGELOG.md`）——低于门槛即判 FAIL。
> 成品覆盖率远低于门槛时（实测漏套模板的案例仅 **14.5% / 15.3%**），
> 说明**没有套模板**——卡片在 UI 里会形状不对、该透明处不透明，像贴了块方形补丁。

## 三、官方形状模板（18 张 PSD，**已随 skill 内置**）

模板目录：**`templates/moment_illustration/1.psd … 18.psd`**（随仓库分发，见该目录 `README.md`）。
脚本默认就取这一份；换成自己的模板时用 `--template-dir`，或在 `local_paths.json` 写
`{"moment_template_dir": "<目录>"}`。

**结构**：每个 PSD 是 456×332，含
- `图层 1`：**全画布黑底**（不透明，opacity 110，用于压暗/预览）
- `图层 2`：空占位层（隐藏）
- **数字命名层**（`1` / `2` / … / `18`）：**官方形状蒙版** —— 白色不透明区 = 保留区，带软边

**实测结论（关键）**：这 18 个形状**两两不同**，且
**原版 240 张时刻图全部能匹配到其中之一**（二值 alpha IoU **0.81~0.996**，无一张 <0.80）。
→ 即这 18 张就是官方所用的完整形状族。

> 例外：`4.psd` 的数字层是**空的**（该文件是作者的中间工作稿，用智能对象占位），
> 脚本会自动跳过并在 `--list` 中标注。

## 四、制作流程

### 4.1 手工流程（用户既定，Photoshop）

1. PS 打开一个模板（如 `1.psd`）；
2. **选中数字图层**（如图层 `1`）；
3. `Ctrl + 左键点击`该图层 → 载入其像素为**选区**；
4. 切到**目标图片**图层；
5. `Ctrl + J` → 用选区**复制出新图层**；
6. 关闭多余图层，**单独导出这个新图层** = 历史时刻成品；
7. （可选，调色）`Ctrl+U` 勾选「着色」调色；或**新建黄色图层 + 正片叠底**以便调饱和度。

> 另一种等价理解：成品 alpha = **源图 alpha × 模板蒙版**，颜色保留源图。
> 软边（中间调）也会被保留 —— 这就是为什么官方成品的覆盖率是 83~98%，未达 100%。

### 4.2 脚本流程（本 skill 提供，等价第 1–6 步）

```bash
# 看模板清单（含覆盖率与宽高比）
python <skill>/scripts/apply_moment_template.py --list

# 单张：指定模板 1
python <skill>/scripts/apply_moment_template.py --input 原图.png --template 1 --out out

# 批量 + 自动挑模板（按源图 alpha 外接框长宽比）
python <skill>/scripts/apply_moment_template.py --input-dir 源目录 --out out --auto

# 直接出 DDS（单 mip RGBA8，与工程既有 DDS 同构）
python <skill>/scripts/apply_moment_template.py --input a.png --template 1 --out out --dds
```

脚本会**报告每张成品的覆盖率并对照 83~99% 区间**：
低于 83% 会标 `**偏低(漏套?)**`，高于 99% 会标 `偏高`（前者说明蒙版没生效，后者说明软边被削掉）。

## 五、接线（4 处）

| # | 位置 | 做什么 |
|---|---|---|
| 1 | `Textures/Moment_<名>.{dds,tex}` | 新增贴图；`.tex` 的 `m_ClassName=UserInterface`、`m_Tags` 单条 `UserInterface`、`m_Width/Height=456/332` |
| 2 | `XLPs/UI_PrideMoments.xlp` | 每条一张贴图：`<m_EntryID>` + `<m_ObjectName>`（同名） |
| 3 | `Data/*.sql` | `INSERT OR REPLACE INTO MomentIllustrations` 四列 |
| 4 | `*.civ6proj` | **无需注册**（实测可运行工程的 Content 里没有 `.xlp` 条目，见 `loyalty-icon.md` §六.5）；真正必需的是 `.Art.xml` 的 consumer 声明 |

### 5.1 `MomentIllustrationType` × `MomentDataType` 配对表（实测原版）

必须**成对**使用，错配则不触发：

| `MomentIllustrationType` | 配对 `MomentDataType` | 原版用量 |
|---|---|---|
| `MOMENT_ILLUSTRATION_UNIQUE_UNIT` | `MOMENT_DATA_UNIT` | 58 |
| `MOMENT_ILLUSTRATION_NATURAL_WONDER` | `MOMENT_DATA_FEATURE` | 34 |
| `MOMENT_ILLUSTRATION_RELIGION` | `MOMENT_DATA_RELIGION` | 25 |
| `MOMENT_ILLUSTRATION_UNIQUE_IMPROVEMENT` | `MOMENT_DATA_IMPROVEMENT` | 23 |
| `MOMENT_ILLUSTRATION_UNIQUE_DISTRICT` | `MOMENT_DATA_DISTRICT` | 17 |
| `MOMENT_ILLUSTRATION_UNIQUE_BUILDING` | `MOMENT_DATA_BUILDING` | 16 |
| `MOMENT_ILLUSTRATION_GOVERNMENT` | `MOMENT_DATA_GOVERNMENT` | 12 |
| `MOMENT_ILLUSTRATION_AIR_UNIT_ERA` / `CIVIC_ERA` / `GAME_ERA` / `SEA_UNIT_ERA` / `TECHNOLOGY_ERA` | `MOMENT_DATA_PLAYER_ERA` | 各 9 |
| `MOMENT_ILLUSTRATION_GOVERNOR` | `MOMENT_DATA_GOVERNOR` | 8 |

> 原版共 13 种 `MomentIllustrationType` / 23 种 `MomentDataType`（全表见
> `MomentIllustrationTypes` / `MomentDataTypes` 表）；
> 上表是**实际被 `MomentIllustrations` 使用**的组合。

### 5.2 `GameDataType` 写什么

写**被展示对象的 Type**：`UNIT_*` / `BUILDING_*` / `DISTRICT_*` / `IMPROVEMENT_*` / `GOVERNOR_*`。
它必须已存在于对应 base 表，否则该行**静默不生效**。

### 5.3 `Texture` 列写什么

**带 `.dds` 后缀**（原版实测如此，如 `Moment_UniqueUnit_Aztec.dds`），
而**不是** XLP 的 EntryID。这与 `Players.Portrait`（写不带后缀的贴图名）**不同**，容易写错。

## 六、验证

```bash
python <skill>/scripts/verify_moment.py --project <工程根>
```

检查（只读）：

1. 每张 `Moment_*` 贴图 `.dds` ↔ `.tex` 成对，`.tex` 宽高 == 456×332 == DDS 实际；
2. `m_ClassName == UserInterface`、`m_Tags` 单条 `UserInterface`；
3. **alpha 覆盖率 75~99%**（脚本默认下界 **75.0**、上界 99.5；低于下界判 FAIL = 漏套模板，
   75~83 之间只 warn —— **原版 240 张实测最低 83.0%**，是本节最有价值的检查）；
4. 贴图已被 `UITexture` XLP（`UI/PrideMoments`）登记；
5. `MomentIllustrations` 每行的 `Texture` 在磁盘存在、`GameDataType` 在对应表存在、
   `(MomentIllustrationType, MomentDataType)` 配对合法；
6. `.tex`/`.xlp` 为 LF，`.sql` 为 CRLF。

## 七、实测记录（为什么这些数字可信）

| 结论 | 证据 |
|---|---|
| 画布 456×332 | 原版 240 张 `Moment_*.dds` 全部为该尺寸；`Moment_*.tex` 240 张 `m_ClassName=UserInterface` |
| 覆盖率下界 83.0% | 原版 240 张实测 min=83.0 / p1=83.0 / p5=83.1 / 中位=88.0 / max=98.5；**无一张 <50%** |
| 18 张模板 = 官方形状族 | 原版 240 张对 18 模板做二值 IoU：**全部 ≥0.80**（0.90–0.95 占 22.9%、0.80–0.90 占 75.8%）；18 形状两两 IoU 均 ≤0.98（互不重复） |
| 漏套模板的实际后果 | 某工程 `MOMENT_UNIT_GONDOLA_RGN` / `MOMENT_UNIT_PATRICIUS_RGN` 覆盖率仅 **14.5% / 15.3%**，最佳模板 IoU 仅 0.30 —— 即未套任何模板 |
| `Texture` 列带 `.dds` | 原版 `MomentIllustrations` 12 行样例全部形如 `Moment_UniqueUnit_Aztec.dds` |
