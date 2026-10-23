← 返回 `SKILL.md` 路由

> 本文件内 `scripts/…`、`templates/…`、`assets/…`、`reference/…` 的根目录 = `civ6-asset-forge/`。

## 〇、前置判定门：有没有「领袖外交语音」（先过这关，再读 §一）

**外交回退立绘（`FALLBACK_NEUTRAL_*`，`Leader_Fallback` 类）是每位领袖必须制作的步骤**，
不随本文件判定门取舍，注册链见 `reference/leader-diplo-fallback.md`。

**本文件的整套 3D 纸片人注册链是可选扩展，唯一触发条件 = 该领袖有外交语音。** 未通过下列判定时，
**纸片人链不执行**（不生成 Geometries / Materials / `Assets/*.ast` /
`Leaders.artdef` / leader XLP），但 fallback 与 2D 立绘（`IMG_LOADING_FOREGROUND_*`）仍必须制作。

1. 工程 `Platforms/` 下**没有音频** → 直接跳过。
2. 素材里**没有明确的外交语音** → 不触发。
3. 查 **Speech bank** 事件名，命中 `FIRST_MEET` / `DECLARE_WAR_FROM_HUMAN` /
   `DECLARE_WAR_FROM_AI` / `KUDO_EXIT` / `WARNING_EXIT` / `DEFEAT_FROM_AI` 任一 → 才算有。

> ⚠ **`QUOTE` 不算。** `QuoteAudio` / `LeaderQuotes` 有值也不触发（quote 只进加载界面/百科）。
> ⚠ **看 `Speech.bnk`，不是 `Voice.bnk`** —— 实测 `Voice.bnk` 常只装游戏内 SFX。
> 详见 `SKILL.md` 铁律四。

---
## 一、素材的认定与询问条件

**源素材未写明、或磁盘上找不到时，才按下面的模板询问**（
`SKILL.md` §三）。工程 `AGENTS.md` 已写明源图且文件存在时，直接进入第三节执行，不提问。

询问模板：

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
> - 需要一步到位 `tex+dds`（`.tex`/`.dds` 输出到项目 `Textures/`，PNG 仍留在工程外，细节见「输出规则」）。

**未提供素材时的默认行为**（用户未明确要求时不得主动生成素材）：
1. 生成全部注册文件（XLPs / artdef / geo / mtl / tex / ast）
2. `.tex` 的 `SourceFilePath` 指向占位路径，需用户在 ModBuddy 导入素材后更新
3. 通用素材（fgx/wig 平面模型）需另行复制，脚本不做
4. **灯光链随注册文件一并生成**（`.lrg` / `.env` / 环境光 dds / `Leader_LightRigs.xlp` 四件）—— 见 §3.6

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
| 立绘素材处理（用户 PNG → 1024×1024 TEXTURE/OPACITY） | → `scripts/process_leader_png.py`；PNG 一律写到工程外的 `--output-dir`（默认 `D:\desktop`）；指定 `--tex-dds` 时把 `.tex`/DDS 写进项目 `Textures/`，PNG 不随行 |
| 忠诚度图标（文明 Loyalty Overlay/Pressure + 战略视图 sprite） | → **引用链路**：本 skill `reference/loyalty-icon.md`（4 张 PNG 合成 + XLP/ArtDef/mtl/ast 注册链） |
| 其他素材导入（png → dds，图标/背景等） | → **引用链路**：`civ6-modding` skill 的 `art-pipeline.md`（素材询问铁律 + art_manifest.json + convert_art.ps1 自动转换，含 .tex 生成与 XLP 实存过滤） |

## 三、标准工作流（生成注册文件）

### 1. 收集信息

从项目 SQL/XML 获取领袖列表（`LeaderType`）—— **下级文件名的唯一来源**：

| 领袖 | LeaderType（原样） | LeaderSuffix（去掉 `LEADER_`） | FX 缩写 |
|------|------------------|------------------------------|---------|
| 卡提希娅 | `LEADER_CARTETHYIA_QYQXP` | `CARTETHYIA_QYQXP` | `CTTH` |
| 某领袖 | `LEADER_FHB_A_SHUAI` | `FHB_A_SHUAI` | `FHB` |

- **FX 缩写**：领袖名字缩写（用于 ast 音频前缀 `{ABBR}_{FX}_*_A`），无现成表时询问用户
- **文明缩写 ABBR**：仅用于 `{OBJ}` 前缀与 ast 音频前缀，如 `RGN`
- **包名 PACK**：默认取工程目录名小写，XLP 包路径为 `/leaders/leader_{PACK}`

> 🔴 **模板与脚本里不得出现任何作者专用后缀。**
> 生成器一律从 `LeaderType` 派生 `LeaderSuffix` 并**原样保留**它自带的后缀 ——
> 那个后缀是 **SQL 的结果**，不是**模板的规则**。

### 2. 运行生成脚本

注册文件里的 `.sql`、`.xml`、`.civ6proj` 属代码文件与工程文件，脚本一律不写：生成器把待写内容写进 `<解决方案根>/workspace/gen/reports/` 的数据清单，由人逐行写入工程。`.dds`、`.tex`、`.ast`、`.mtl`、`.xlp`、`.artdef`、`*.Art.xml` 属美术产物，脚本直接写盘。

```bash
python "<skills>/civ6-asset-forge/scripts/gen_leader_2d.py" \
  --project "<工程路径>" \
  --pack <包名> \
  --abbr <文明缩写> \
  --leader-types "LEADER_CARTETHYIA_QYQXP,LEADER_FLEURDELYS_QYQXP"   # ★ 推荐：命名由此完全派生

# 需要给 ast 填 FX 缩写时，叠加 --leaders（按 Name:FX 匹配）
python "<skills>/civ6-asset-forge/scripts/gen_leader_2d.py" \
  --project "<工程路径>" --abbr RGN \
  --leader-types "LEADER_CARTETHYIA_QYQXP" --leaders "Cartethyia:CTTH"
```

新建的注册文件由脚本直写工程；生成文件清单（Leader 与几何名按命名规范自动推导）：

| 目录 | 文件（每领袖） | 说明 |
|------|--------------|------|
| `XLPs/` | `leader_{PACK}.xlp`（聚合） | Leader 条目包 |
| `XLPs/` | `Leader_LightRigs.xlp`（聚合） | 灯光条目包，包名 `leaders/light_rigs`，**只允许 WINDOWS** |
| `ArtDefs/` | `Leaders.artdef`（聚合） | 领袖集合定义（Leader/LightRig/ColorKey/Background 槽位）；Lightrig 槽 = `{LEADER}_LightRig` |
| `Geometries/` | `LEAD_{ABBR}_{Name}_{LeaderSuffix}.geo` + `_Camera.geo` | 平面几何 + 摄像机 |
| `Materials/` | `LEAD_{ABBR}_{Name}_{LeaderSuffix}_Material.mtl` | 材质（引用 TEXTURE/OPACITY）；**类必须 `Leader_Matte`**，见 §3.5 |
| `Textures/` | `{LeaderType}_TEXTURE.tex` + `{LeaderType}_OPACITY.tex` | 贴图定义（**cook 参数须为最高品质**，见 §3.6） |
| `Assets/` | `LEAD_{ABBR}_{Name}_{LeaderSuffix}.ast` | 行为资产（6 外交槽位 + NEUTRAL） |
| `LightRigs/` | `{Name}_LightRig.lrg` | 灯光绑定（`m_ClassName=LeaderEnvironment`），见 §3.6 |
| `EnvironmentLights/` | `{Name}_Environment.env` + `{Name}_Environment.dds` | 环境光定义与贴图（Hojo 通用资产），见 §3.6 |

> **收尾提醒**：`Assets/*.ast` 属美术产物，重跑生成器时由脚本直接覆盖；它在已有工程里承载着外交语音时间轴，覆盖前先确认 `m_FXName` 与时长是否需要保留。
> 已有语音的工程写入之前先确认 `.ast` 的 `m_FXName` 与时长是否要保留。

### 2.5 立绘素材处理（可选）

**入口只有一条：`scripts/process_leader_png.py`。** 素材已备齐时直接执行命令，不做读图分析、不做裁剪框推演、不打开图片看内容。

```bash
# 源图取自工程 AGENTS.md「美术与音频资产」表的「来源」列
python "<skills>/civ6-asset-forge/scripts/process_leader_png.py" \
  --input "<源PNG>" \
  --leader-type "<LeaderType>" \
  --project "<工程根>" --tex-dds      # PNG 留在 --output-dir，只有 .tex/.dds 进 Textures/
```

- PNG 由脚本直接写到工程外的 `--output-dir`；带 `--tex-dds` 时 `.tex` 与 `.dds` 由脚本直接写进项目 `Textures/`（美术产物）。
- 脚本按**短边居中裁剪**再缩放到 `1024×1024`，在 `--output-dir` 里生成 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`；带 `--tex-dds` 时在项目 `Textures/` 里写 `.tex`，并按 `.tex` 的 `ePixelformat` 转换 DDS（TEXTURE → `R8G8B8A8_UNORM`，OPACITY → `R8_UNORM`，均带完整 mip 链）。
- 需要别的裁剪框时才加 `--crop left,top,side`（原图坐标）。**是否加这个参数，由用户指定，不自行推演。**
- `--project` + `--leader-name` 可用于从工程 SQL/XML 查找 LeaderType。

**以下情形才停下询问用户**（`SKILL.md` §三）：

| 情形 | 问什么 |
|---|---|
| 源图路径在工程 `AGENTS.md` 里未写明，或与磁盘实存文件不符 | 请用户给出源图路径 |
| 主体贴边、多主体、构图特殊 | 请用户给出裁剪范围 |
| 脚本依赖缺失（无 Pillow）、texconv 定位不到 | 请用户给出解释器或 texconv 路径 |

> `process_leader_png.py` 的 DDS 子步骤通过子进程管道调用 texconv。若运行环境禁止该管道（报 `PermissionError: [WinError 5]`），**就地停下**，把错误原文报给用户，由用户决定后续，不换写法重试。texconv 找不到、转换非零退出、未产出 DDS，三种情形一律就地 `SystemExit`，不继续写 `.tex`。

---

**输出规则：**
- PNG 只写工程外，默认 `D:\desktop`：
  - `{LeaderType}_TEXTURE.png`
  - `{LeaderType}_OPACITY.png`
- 若用户要求一步到位（`--tex-dds`）：
  - 写进项目 `<project>\Textures\` 的只有 `.tex` 与 `.dds`
  - 同步生成/更新 `.tex`，`m_SourceFilePath` 指向工程外那张 PNG，`.tex` 的 `m_DataFiles` 引用同目录 `.dds`
  - 调用 texconv 生成 DDS（TEXTURE：`R8G8B8A8_UNORM`；OPACITY：`R8_UNORM`），中间产物落在系统临时目录
  - **DDS 头部按官方口径校验并修复**（`dds_io.ensure_official_header`）：texconv 直出会带 `DDSD_PITCH`、`dwPitchOrLinearSize` 非 0、保留区无 `FTXT`、单通道写成 `DDPF_LUMINANCE`，四处差异会让纸片在外交场景不显示（§3.6(5)）。修复在临时目录完成，合格后才写进工程
  - `.tex` 与 `.dds` 均由脚本直接覆盖（美术产物）
- **PNG 禁止落进工程任何目录**：`Textures/` 是 AssetEditor 的 pantry，cooker 递归扫描整棵工程目录树，落进去的 PNG 会被当成贴图实体登记，与 `.dds`/`.tex` 抢注册。`--output-dir` 指向工程目录内时脚本直接报错退出。

**生成规则：**
- TEXTURE：1024×1024，保留透明背景（裁剪规则见「层级 1」）。
- OPACITY：取源图 alpha 的连续灰度；背景段（`alpha <= --alpha-floor`，默认 8）统一写成 `--alpha-base`（默认 4），避免低值尾部被量化成同心环带（§3.6(6)）。源图的 alpha 是铺满画布的宽羽化光晕时（三条判定见 §3.6(7)），默认参数不够用，需按该条做分段拉伸。

### 3. 素材文件（未提供素材时跳过）

| 素材 | 来源 | 说明 |
|------|------|------|
| `.fgx` / `.wig`（主体 + Camera） | 从已建成工程复制 | **通用平面模型，跨工程逐字节一致**（MD5：主体 fgx `D13E5D864C121D9DA51500A7DFE0DD4` / wig `B9C116E082A7DD783A89E1684ED9C0B5`；Camera fgx `7F8319922265FD53841D7C15469E4E19` / wig `C1F6B44B222FA827B683A26F411CD53E`），复制后重命名即可 |
| 环境光 dds | 从已建成工程复制 | **通用环境光贴图，跨工程逐字节一致**（MD5 `100A9AF5…54F1A6`），复制后按 `{Name}_Environment.dds` 改名即可；`gen_leader_2d.py` 会自动复制改名 |
| 立绘 png（TEXTURE / OPACITY） | 用户提供 | 用 `process_leader_png.py` 在工程外生成 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`（1024×1024，默认桌面）；`--tex-dds` 时另把 `.tex`/DDS 写进项目 `Textures/`，PNG 仍留在工程外 |


### 3.5 材质类铁律：平面纸片用 `Leader_Matte`，不用 `Leader`

> 🔴 **2D 领袖纸片是「一张平面四边形」，材质类必须是 `Leader_Matte`。**
> `Leader`（原版 **3D 人物服装/皮肤**的 PBR 着色器类）会让纸片发灰发糊，
> 且通常附带 `TranslucencyColor=RGB(150,20,7)` 与 `ForceTransparency=true`，不得使用。

**实测症状（`Leader` 类 vs `Leader_Matte`，同一立绘对比）：**

```
人物区域   3D = 0.898 x 2D + 20.5   (sRGB)   ← 暗部 +18~19、亮部 -2~3（抬黑位 + 压对比）
背景区域   3D = 1.0002 x 2D + 0.16           ← 逐像素不变（63.9~66% 像素 |Δ|<2）
```

即：**像蒙了一层灰纱**（等效「不透明度 0.90、雾色 ~202」的叠层），另叠加等效高斯
`σ≈0.8px` 的低通模糊（频谱**低频比 1.02 / 高频比 0.42** —— 是低通卷积，**不是** mip 掉级）。
关键判据：**差异只发生在领袖本体，背景逐像素不变** → 不是全屏后处理（`.ast`），是材质本身。

**原版统计（`pantry/Materials/*.mtl`，363 个领袖类材质）：**

| 检查 | 原版事实 |
|---|---|
| `ForceTransparency=true` | **仅 2/363**，且两者**都绑定了 `Translucency` 贴图** |
| 平面四边形用什么类 | `Leader_Matte`（19 个）—— **全部是平面背景板** |
| 结构参照 | `Hojo_flatBackground_Placeholder.geo` 同为 **4 顶点 / 2 图元**平面，geo 类 `Leader`，**材质类 `Leader_Matte`** |
| `Leader_Matte` 参数集 | **只填 `BaseColor` (+`Opacity`)** |
| 对齐样本 | `pantry/Materials/LEAD_JAPA_Hojo_Background_Material.mtl` |

**机理**：拿 PBR 人物服装着色器去画一张平面贴图，其 `albedo × L + ambient` 响应
天然产生「增益<1 + 加性抬黑」，同时因缺少法线/粗糙度信息而低通软化 —— 与实测完全吻合。

**因此模板 `templates/LEAD_ABBR_Name_Material.mtl` 写死：**

```xml
	<m_ClassName text="Leader_Matte"/>
	<m_Version><major>3</major><minor>0</minor><build>176</build><revision>703</revision></m_Version>
	<!-- 参数槽只有 Opacity + BaseColor -->
	<m_Tags><Element text="Leader_Matte"/><Element text="Leader"/><Element text="Matte"/></m_Tags>
```

**存量工程体检 / 迁移**（幂等，默认只预演）：

```bash
python "<skills>/civ6-asset-forge/scripts/migrate_leader_matte.py" <工程根>            # 预演
python "<skills>/civ6-asset-forge/scripts/migrate_leader_matte.py" <工程根> --check    # 有待迁移项则 exit 2
python "<skills>/civ6-asset-forge/scripts/migrate_leader_matte.py" <工程根> --write    # 迁移后的 .mtl 直接写盘（美术产物）
python "<skills>/civ6-asset-forge/scripts/migrate_leader_matte.py" <Civ6工程父目录> --all-siblings --write
```

`--write` 时，`.mtl` 由脚本直接写盘（美术产物）。

★ 材质改动后**必须在 AssetEditor 重新 cook** 才生效（材质类属 cook 期数据）。

### 3.6 铁律：灯光链随工程自带；贴图必须最高品质（2026-09-28 实机实测）

#### (1) 灯光链必须随工程自带 —— 缺了会渲染成零星色块

**症状**：外交场景里纸片人不显示，只留下零星几块杂色方块。

**成因**：`Leaders.artdef` 的 Lightrig 槽写成 `ART_DEFAULT_LIGHT`，该条目在官方
`Leader_LightRigs.xlp` 里映射到 `Gorgo_LightRig`，包名同为 `leaders/light_rigs`。
工程内若没有本地同名包，`.dep` 里 `LeaderLighting` 库的 `PackageDependencies` 为空，
领袖场景取不到灯光，材质与几何照旧加载但整体渲染失败。

**三件套 + 两处接线：**

| 产出 | 命名与内容 | 规格来源 |
|---|---|---|
| `LightRigs/{Name}_LightRig.lrg` | `m_Name` 与 artdef 的 EntryName 同源 | `templates/LEAD_ABBR_Name_LightRig.lrg`；`m_ClassName=LeaderEnvironment`，`m_EnvironmentLights` 只有一条指向 `{Name}_Environment` |
| `EnvironmentLights/{Name}_Environment.env` | 三盏方向灯 | `templates/LEAD_ABBR_Name_Environment.env`；强度 `1.55 / 1.5 / 0.446472` |
| `EnvironmentLights/{Name}_Environment.dds` | Hojo 通用资产 | `templates/Leader_Environment.dds`；128×128 未压缩 RGBA8、单 mip、393,344 字节，MD5 `100A9AF5C487BDF8D1BD84AFF854F1A6`，跨工程逐字节一致 |
| `XLPs/Leader_LightRigs.xlp` | 包名固定 `leaders/light_rigs` | `m_ClassName=LeaderLighting`，`m_AllowedPlatforms` 只写 `WINDOWS`，每个领袖一条 `{LEADER}_LightRig → {Name}_LightRig` |
| `Leaders.artdef` 的 Lightrig 槽 | `<m_EntryName text="{LEADER}_LightRig"/>` | `m_XLPPath` 写 `Leader_LightRigs.xlp`，`m_BLPPackage` 写 `leaders/light_rigs` |
| `.Art.xml` | `LeaderLighting` 库的 `relativePackagePaths` 写 `leaders/light_rigs` | 不写则声明不出本地包 |
| `.civ6proj` | `<Content Include="XLPs/Leader_LightRigs.xlp">` | `.lrg` / `.env` / `.dds` 由构建自动扫描，不需要登记 |

> `.env` 三盏灯的强度按模板值照抄，不自行调参。
>
> 存量工程迁移：补齐上述四类文件，artdef 的 Lightrig 槽改成各自的 `*_LightRig`，
> `.Art.xml` 补 `leaders/light_rigs`，`.civ6proj` 补一条 Content。**改完必须重新 cook。**

#### (2) 平面 geo 的头发参数

`LEAD_ABBR_Name.geo` 的 `m_CookParams` 写全 7 个头发参数：`HairThickness` `0.005`、
`HairColor` 与 `HairColor_Secondary` `RGB(104,74,56)`、`HairColor_Accent` 与
`HairColor_AccentSecondary` `RGB(255,255,255)`、`HairAccentMix` `0`、`HairGlossPower` `1`；
`_Camera.geo` 的 `m_CookParams` 保持 **`<m_Values/>`（空）**。

依据：本机 5 个可用纸片工程（`Ragunna_Pack` / `Black_Shores_Pack` / `Hethereau_Mint` /
`Jinzhou_Changli` / `Jinzhou_Jinhsi`）与 §6.1 教程模板 `LEAD_FELI_JasperKitty.geo`
都带这 7 个参数。原版 `Hojo_flatBackground_Placeholder.geo` 的 `m_Groups` 指向
`Hojo_flatBackground_Placeholder_Material`，是背景板资产，其空参数不适用于领袖纸片。

#### (3) 后处理参数：要么统一为已验证值，要么保持全 0

`.ast` 的 `m_CookParams` 由纸片人**自己**的资产实例（`AssetInstance`）声明，
**不随 matte 材质类的参数槽缩减而失效**。后处理参数必须统一，禁止部分领袖开、部分领袖关。

**统一口径 = 除旋转外全部为 `0`**（≡「后处理关闭」）：

```
EnvironmentRotationX  0.000000
EnvironmentRotationY -7.199999
EnvironmentRotationZ 10.000000
AOPower               0.000000
AOScale               0.000000
AORadius              0.000000
BloomStrength         0.000000
BloomThreshold        0.000000
ExtraExposureRange    0.000000
GrainStrength         0.000000
VelocityScale         0.000000
```

> ⚠ **不要把 AO / Bloom / `ExtraExposureRange` 调成非 0。** 历史会话里正是照抄原版
> `LEAD_EGYP_Cleopatra.ast` 的那套值（`AOPower=3 / AOScale=0.85 / AORadius=5 /
> BloomStrength=0.05 / ExtraExposureRange=1.6`）让纸片**"太亮了反而失真"**，
> 随后被全量回退到 0 —— 那套值是**3D 人物**的配置，不是纸片的。
>
> `GrainTexture` 是 `ObjectValue`（TEXTURE）槽，`m_ObjectName` 留空，条目**必须保留**
> （位于 `ExtraExposureRange` 与 `GrainStrength` 之间）。
> **改后处理参数必须重新 cook 并实机确认**（属渲染表现改动）。

#### (4) TEXTURE / OPACITY 的 cook 参数必须是最高品质

**色度降采样是"纸片发糊 + 高饱和区色差"的元凶**（蓝色区色差实测 8.75 @N=3）。
两个 `.tex` 的 `m_CookParams` 必须写成：

| 文件 | 参数 |
|---|---|
| `{LeaderType}_TEXTURE.tex` | `Skip Compression=true` + `Quality Loss - Luma/Chroma=0` + `Resolution Loss - Luma/Chroma=0` |
| `{LeaderType}_OPACITY.tex` | `Quality Loss=0` + `Skip Compression=true` |

历史默认值 `QL-Chroma=4 / RL-Chroma=3` 属 **YCbCr 4:2:0 式压缩**：亮度全分辨率、**色度降到 1/8**，
表现为彩色轮廓发虚、蓝色装饰"洇边"。两个 `.tex` 模板已写死最高品质。

> 代价：DDS 体积上升（未压缩 RGBA 1024²）。纸片人只有 2 张图/领袖，可接受。

#### (5) DDS 头部必须取自可用的领袖产物

**症状**：外交场景纸片人不显示，整块区域均匀散布零星彩色碎块。材质类、灯光链、
两个 `.tex` 的 cook 参数、几何体与可用工程逐项相同，症状照旧。

**判据**：把 `Textures/{LeaderType}_TEXTURE.dds` 与 `_OPACITY.dds` 的字节头，
与任一已正常工作的领袖同格式 DDS 逐字节比对。贴图尺寸与 mip 级数相同时头长相同。

**实测差异**（`texconv` 直出与官方 cook 链产物对照，偏移从 0 起算）：

| 偏移 | 字段 | `texconv` 直出 | 官方产物 |
|---|---|---|---|
| 8 | `dwFlags` 首字节 | `0x0f`（含 `DDSD_PITCH=0x8`） | `0x07` |
| 21 | `dwPitchOrLinearSize` 次字节 | 非 0（TEXTURE `0x10`、OPACITY `0x04`） | `0x00` |
| 32–35 | 保留区前 4 字节 | `00 00 00 00` | `FTXT`（`46 54 58 54`） |
| 80–82 | `DDS_PIXELFORMAT.dwFlags` | OPACITY `0x00020000`（`DDPF_LUMINANCE`） | OPACITY `0x00000040`（`DDPF_RGB`）；TEXTURE 两侧同为 `0x41` |

`texconv` 没有任何参数能产出单通道 `DDPF_RGB` 头：`-f R8_UNORM`、叠加 `-dx9`、
叠加 `-dx10`、`-nologo -m 0` 四种组合实测都写成 `DDPF_LUMINANCE`。

**解决**：像素载荷用 `texconv` 生成的，头部按官方口径重写。

`civ6-modding/art/dds_io.py` 承担这一步，`process_leader_png.py` 在 `--tex-dds` 流程里自动调用：

| 接口 | 作用 |
|---|---|
| `dds_header_bytes(width, height, mips, bit_count)` | 按官方口径构造 128 字节头；`bit_count` 取 32（RGBA8）或 8（单通道） |
| `header_issues(path)` | 校验四处偏移与像素载荷长度，返回问题清单 |
| `ensure_official_header(path)` | 校验后不合规就地重写头部，像素载荷原样保留 |

命令行等价入口：

```bash
python "<skills>/civ6-modding/art/dds_io.py" --check <DDS ...>   # 不合规即非零退出
python "<skills>/civ6-modding/art/dds_io.py" --fix   <DDS ...>   # 校验并重写头部
```

`process_leader_png.py` 的中间产物落在系统临时目录，头部修复完成后才写进工程 `Textures/`；
修复失败或载荷长度不符时就地 `SystemExit`，工程侧不留半截文件。

**改完必须重新 cook**：`.tex` 引用的是 DDS 文件，像素与头部都属 cook 期输入。

#### (6) OPACITY 低 alpha 尾部必须压成单一底值

**症状**：外交场景纸片人物外围出现一圈一圈的同心环带。

**机理**：径向羽化的 OPACITY 在低值尾部保留连续衰减，8 位量化把 1~3 这类极窄区间切成大面积台阶。
实测 Hongkai_Elysia：alpha 1~3 三级共 55.71%（584,176 px）压在占全图 55.7% 的背景上，
8 条射线的恒值平台合计 22 段，外交场景表现为粉色同心光环。

**对照**（同引擎、同材质类，Ragunna_Pack 的 Roccia）：背景段统一写底值 4，占 63.22%（662,720 px），
8 射线恒值平台 12 段且绝大部分是同一值 4 的长平台，肉眼无环带。

**做法**：`process_leader_png.py` 把 `--alpha-floor`（默认 8）以下的像素统一写成 `--alpha-base`（默认 4），
背景完全平坦，只保留人物边缘的过渡；`--alpha-base 0` 供硬边素材使用。

**改后实测**（Hongkai_Elysia）：底值 4 占 63.40%（665,630 px）、灰阶 241 级、单段宽环 228.75、
径向尾部 6.7 / 4.2 / 4.0 / 4.0 / 4.0；外交场景环带消失。

**判据**：alpha 直方图的最低级占比，加射线扫描的恒值平台段数。最低级把绝大部分背景吞进两三级、
平台段数达二十余段，即为需要抬底的信号。

> 抬底的前提是 `(4)` 的 cook 参数：OPACITY 若不是 `Quality Loss=0` + `Skip Compression=true`，
> 压缩会重新量化渐变，抵消抬底效果。

#### (7) 宽羽化光晕的 OPACITY 需要分段拉伸

**症状**：`(6)` 的抬底已经做了（背景段是单一底值 4），外交场景里仍能看到一圈一圈的环带，人物外围还有一层弥散的灰雾。

**成因**：源图的 alpha 是一条跨度极大的径向羽化——从 0 爬到 255 铺满了画布的大部分面积，低值尾段横跨二十多个灰阶。抬底只切掉最底部那一小段，`9~63` 仍以连续灰阶铺在离人物很远的背景上，8 位量化后每一级都是一条宽环。

**判定**（把源图 alpha 缩放到 1024 后统计，三条同时成立才命中）：

| 量 | 测法 | 命中阈值 | Hongkai_Elysia 实测 |
|---|---|---|---|
| 低值段离主体的距离 | `alpha>=64` 做 16px 形态学膨胀，统计 `9~16` 区间落在其中的比例 | < 5% | 2.84% |
| 低值段面积 | `9~16` 区间像素占全图比例 | > 3% | 4.96% |
| 渐变铺开程度 | `8~247` 区间占比；横向游程 ≥4px 的灰阶级数 | > 20% 且级数 > 级数总量的 90% | 27.87%，255/256 |

三条全部命中即「渐变铺满画布」。任一条不命中说明渐变本来就贴着人物边缘，属正常的边缘抗锯齿，按 `(6)` 的默认流程处理。

判定由 `scripts/check_opacity_halo.py` 完成，接受源立绘 PNG 或已是单通道 alpha 的 OPACITY DDS：

```bash
python "<skills>/civ6-asset-forge/scripts/check_opacity_halo.py" <源立绘.png | OPACITY.dds ...>
```

命中任一张即退出码 1（提示按本条做分段拉伸），全部未命中退出码 0。实测兄弟工程 Ragunna_Pack 的五个领袖成品与 Hongkai_Elysia 处理后的贴图全部未命中，源立绘 `真我·人之律者立绘.png` 命中。

**做法**：对 alpha 做分段线性拉伸，端点取该图直方图的拐点（`low` 取低值尾段结束处，`high` 取主体实心区起点）：

- `alpha <= low` → `alpha_base`（默认 4）
- `alpha >= high` → 255
- 其间按 `(alpha - low) / (high - low)` 线性映射到 `alpha_base..255`

Hongkai_Elysia 实测 `low=96 / high=160 / base=4`：底值 4 占 63.45%、255 占 32.91%、中间调 3.64%、灰阶级数 65、轮廓跳变 2471、过渡带均宽 15.45px；兄弟工程 Ragunna_Pack 的 Roccia 成品为底值 63.20%、255 31.63%、中间调 5.17%、级数 252。两者形态一致。

**落笔前的复核**：过渡带均宽 = 中间调像素数 ÷ 轮廓跳变数，实测 15.45px，与源图边缘的羽化宽度同量级。被压到 2~3px 说明 `low` / `high` 取窄了，人物边缘会硬切。

**代价**：真正的半透明区域（薄纱、玻璃、发光特效、发丝末端）会被一并写成 4 或 255。素材里存在这类区域时这条处置会吃掉它们，因此只在三条判定全部命中时使用。

**重出载荷时头部原样保留**：`(5)` 的头部修复只针对 `texconv` 直出。工程里已合规的 DDS 换载荷时直接写入原 128 字节头 + 新载荷，实测头部 md5 `d3d8413442dc16e969b3eae7bdca25ff` 前后一致。

**改后必须重新 cook**，并在 Mods 副本上核对 BLP 逐字节变化：Hongkai_Elysia 实测 BLP md5 `58a71431b5e85027ae9bcd818a8cb3eb` → `9db2f19be559dfe8b7b3efe3c78e6432`。

### 4. 更新工程文件

- `*.civ6proj`：新增 `ArtDefs` / `LightRigs` / `EnvironmentLights` 三个文件夹 + 3 个 Content Include：
  - `XLPs\leader_{PACK}.xlp`
  - `XLPs\Leader_LightRigs.xlp`
  - `ArtDefs\Leaders.artdef`
- **Geometries/Materials/Textures/Assets/LightRigs/EnvironmentLights 不需注册**——构建时自动扫描编译进 `Platforms\Windows\BLPs\*.blp`
- `*.Art.xml`：新增/修改 `XLPs\`、`ArtDefs\` 后**必须重新生成**——运行
  `python <civ6-modding skill>\art\gen_modartxml.py <projectRoot> --check`
  （差异人工确认后加 `--write`；`*.Art.xml` 属美术产物，脚本直接写盘；脚本按项目实存文件重算
  artConsumers/gameLibraries/requiredGameArtIDs，替代手工补 Leader/LeaderLighting 引用）
  ⚠ `LeaderLighting` 库的 `relativePackagePaths` 必须是 `leaders/light_rigs`；生成器不代写这一处，缺了则本地灯光包声明不出来。
- **备份**：见 `SKILL.md`「不静默备份」节（四类共用，原条已上移）。

### 5. 验证清单

- [ ] 所有生成 XML 可解析（无残留 `{占位符}`）
- [ ] `leader_{PACK}.xlp` 条目数 = 领袖数；`Leaders.artdef` 块数 = 领袖数
- [ ] geo 的 fgx/wig 引用名与磁盘文件名一致（主体 + `_Camera`）
- [ ] mtl 引用 `{LeaderType}_TEXTURE` / `_OPACITY`；**artdef 的 Lightrig 槽为 `{LeaderType}_LightRig`**（见 §3.6）
- [ ] 灯光三件套齐备：`LightRigs/{Name}_LightRig.lrg`、`EnvironmentLights/{Name}_Environment.env` + `.dds`、`XLPs/Leader_LightRigs.xlp`（见 §3.6）
- [ ] `.Art.xml` 的 `LeaderLighting` 库 `relativePackagePaths` = `leaders/light_rigs`；`.civ6proj` 有 `XLPs/Leader_LightRigs.xlp` 的 Content 条目
- [ ] 两个 `.tex` 的 cook 块为最高品质（`Skip Compression=true`，四个 Loss 全 0；OPACITY 的 `Quality Loss=0`）
- [ ] **mtl 的 `m_ClassName` 为 `Leader_Matte`**，参数槽只有 `Opacity`+`BaseColor`，无 `TranslucencyColor`/`ForceTransparency`（见 §3.5）
- [ ] ast 的 GeometrySet 引用 Camera geo + 主体 geo + Material，FXName 为 `{ABBR}_{FX}_{动作}_A`
- [ ] 素材文件（若提供）复制后哈希与源一致
- [ ] 若已处理立绘：TEXTURE / OPACITY PNG 均为 `1024×1024`
- [ ] OPACITY 主体区连续灰度、背景段为单一底值（默认 4），低值尾部没有残留的连续衰减层
- [ ] 源图 alpha 命中 §3.6(7) 的三条判定时，OPACITY 已按该条做分段拉伸；未命中时保持默认流程（中间调占比、过渡带均宽两项复测留档）
- [ ] 文件名使用 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`
- [ ] 一步到位时 `.tex` 的 `SourceFilePath` 指向工程外的 PNG，DDS 已生成（或已明确提示未生成）
- [ ] 两个 `.dds` 的 128 字节头通过 `dds_io.header_issues`（无 `DDSD_PITCH`、`dwPitchOrLinearSize=0`、保留区 `FTXT`、单通道 `DDPF_RGB`）
- [ ] 工程 `Textures/` 内只有 `.tex` 与 `.dds`，没有 PNG

## 四、命名规范（生成脚本自动推导，手动修改时遵循）

| 对象 | 格式 | 示例（以 `LEADER_CARTETHYIA_QYQXP` 为例） |
|------|------|------|
| XLP EntryID | **= SQL 里的 `{LeaderType}` 原样** | `LEADER_CARTETHYIA_QYQXP` |
| XLP ObjectName / geo | `LEAD_{ABBR}_{Name}_{LeaderSuffix}` | `LEAD_RGN_Cartethyia_QYQXP` |
| Camera geo | `LEAD_{ABBR}_{Name}_{LeaderSuffix}_Camera` | `LEAD_RGN_Cartethyia_QYQXP_Camera` |
| Material | `LEAD_{ABBR}_{Name}_{LeaderSuffix}_Material` | `LEAD_RGN_Cartethyia_QYQXP_Material` |
| LightRig | `{Name}_LightRig`（artdef 的 EntryName 为 `{LEADER}_LightRig`） | `LEADER_CARTETHYIA_QYQXP_LightRig` |
| Environment | `{Name}_Environment`（`.env` 与 `.dds` 同名） | `Cartethyia_QYQXP_Environment` |
| Texture | `{LeaderType}_TEXTURE` / `{LeaderType}_OPACITY` | `LEADER_CARTETHYIA_QYQXP_TEXTURE` |
| AST | `LEAD_{ABBR}_{Name}_{LeaderSuffix}` | `LEAD_RGN_Cartethyia_QYQXP` |
| XLP 包名 | `/leaders/leader_{PACK}` | `/leaders/leader_ragunna_qyqxp` |

> 🔴 **命名铁律：一切从 SQL 里该领袖的 `LeaderType` 变量派生，禁止使用任何固定/惯例缩写常量。**
>
> - `{LeaderSuffix}` = `{LeaderType}` 去掉 `LEADER_` 前缀后的**完整剩余部分**（含它自带的任何后缀）。
>   例如 `LEADER_CARTETHYIA_QYQXP` → `CARTETHYIA_QYQXP`；**不要**再凭空追加 `QYQXP`。
> - **`QYQXP` 不是通用作者缩写，也不得写进模板。** 它在示例工程里出现，**只是因为那些工程的
>   SQL `LeaderType` 本身就叫 `LEADER_<NAME>_QYQXP`** —— 它是**结果**，不是**规则**。
>   SQL 里没有 `QYQXP` 的领袖（如 `LEADER_FHB_A_SHUAI`）生成的命名一律**不带** `QYQXP`。
> - 推导顺序：**先读 SQL 的 `LeaderType` → 再套前后缀**。禁止反过来（先定缩写再拼名字）。

**AST 音频 FXName**：`{ABBR}_{FX}_{动作}_A`，动作枚举：`FIRST_MEET` / `DECLARE_WAR_FROM_HUMAN` / `DECLARE_WAR_FROM_AI` / `KUDO_EXIT` / `WARNING_EXIT` / `DEFEAT_FROM_AI`。

## 五、关键架构事实

1. **平面模型是通用资产**：.fgx/.wig 直接复制改名即可，无需建模（哈希见第三节素材表）。
   环境光 dds 同样是通用资产（哈希见 §3.6 表），由 `gen_leader_2d.py` 逐领袖复制改名。
2. **聚合模板结构**：`leader_{PACK}.xlp` 用 `<!-- LEADER_BLOCK_START/END -->` 标记领袖块，脚本按领袖数复制；artdef 同理（容器内每个领袖块含 Leader/LightRig/ColorKey/Background 4 个 BLPEntry + 2 个 StringValue；其中 LightRig 槽为 `{LEADER}_LightRig`）。
3. **`{PACK}` 占位**：`leader_{PACK}` 与 `/leaders/leader_{PACK}` 保持 `leader_` 前缀不变；仅 `{PACK}` 部分替换。
4. **Camera geo 的骨骼名/模型名**是引用官方 `LEAD_ARAB_Saladin_Camera` / `LEAD_JAPA_Hojo_Camera`（.ma 源路径来自 Hojo），**不要改动**——这是官方共享摄像机资产。

## 六、参考工程（素材复制来源）

| 工程 | 路径 |
|------|------|
| 示例工程（本工程） | `D:\documents\Firaxis ModBuddy\Civilization VI\示例工程\示例工程` |
| 工程 A | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 A\工程 A` |
| 工程 C | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 C\工程 C` |
| 工程 B | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 B\工程 B` |

### 6.1 第三方交叉验证源（《Civ6 Modding Textbook》）

第三方中文教程 **《Civ6 Modding Textbook》**（小优妮）附带 10 个渐进参考工程
（`snapshot02..10` + `final`），可作本 skill 论断的**独立交叉验证源**：

```
<上游教程仓库本地副本>\
├─ Textbook\            12 章正文（225 KB）+ 221 张配图
├─ Project\             10 个可构建参考工程（Feline_JasperKitty）
└─ Assets\              图标/立绘 PSD 模板/纸片人模板/语音/WWise 工程
```

**已验证的吻合点（2026-09-17 实测，非引用其结论）**：

| 本 skill 的论断 | 教程工程的证据 | 结果 |
|---|---|---|
| `.fgx` / `.wig` 平面模型**跨工程逐字节一致**（通用资产） | `Assets/领袖纸片模板/Geometries/LEAD_FELI_JasperKitty.fgx` MD5 `D13E5D86…E0DD4`、`.wig` `B9C116E0…9C0B5`、Camera `.fgx` `7F831992…4E4E19`、Camera `.wig` `C1F6B44B…CD53E` | **4/4 与本文档记录相同** |
| `{Name}_Environment.dds` 是通用环境光（Hojo，MD5 `100A9AF5…54F1A6`） | `Assets/领袖纸片模板/EnvironmentLights/JasperKitty_Environment.dds` 同 MD5 | **1/1 相同** |
| `background` role = **1920×960** | `LEADER_JASPER_KITTY_BACKGROUND.tex` = 1920×960 | 一致 |
| `diplomacy_layer1..3` = **960×505** | `JASPER_KITTY_1..3.tex` = 960×505 | 一致 |
| 层 4 用**别名条目**指向官方资产 | `UI_LeaderScenes.xlp`：`<m_EntryID text="JASPER_KITTY_4"/>` + `<m_ObjectName text="BARBAROSSA_4"/>` | 一致 |
| UI 立绘应为 **`UserInterface`**、`Leader_Fallback` 是 3D 回退 | 其 34 个 `.tex`：`LEADER_JASPER_KITTY_NEUTRAL` = `UserInterface`、`FALLBACK_NEUTRAL_JASPER_KITTY` = `Leader_Fallback` | 一致 |

**用法**：需要独立复核某个尺寸/类别/链路的论断时，可对照该工程；
**但不要把它的素材整包搬进项目**（体积 960 MB、版权不明），只作**证据比对**。

> ⚠ 该教程亦有**未证实内容**：其素材包 `模组参数生成器.xlsx` 里的
> `CustomParameter`/`$VAR$` 模板变量机制，经全量核查在本机 ModBuddy 中**无实现**
> （详见 `civ6-modding/project-setup.md` 对应小节）。**教程内容需逐条核实后采信。**

## 七、交付要求

- 交付说明中包含：生成的文件清单、素材复制清单（哈希验证结果）、"待用户提供素材"清单、civ6proj 改动说明
- 素材相关（立绘 png/dds 导入）一律标注"待用户处理"，除非用户明确要求代处理
- 若已用 `process_leader_png.py` 处理立绘，交付说明中列出生成的 TEXTURE/OPACITY PNG、`.tex` 更新结果、DDS 生成结果
