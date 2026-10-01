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
> - 需要一步到位 `tex+dds`（输出到项目 `Textures/`，细节见「输出规则」）。

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
| 立绘素材处理（用户 PNG → 1024×1024 TEXTURE/OPACITY） | → `scripts/process_leader_png.py`；默认输出到 `D:\desktop`；指定 `--tex-dds` 时输出到项目 `Textures/` 并同步 `.tex`/DDS |
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

注册文件已存在且内容有变化时，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时打印待写入清单。

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

> **收尾提醒**：`Assets/*.ast` 在已有工程里承载着外交语音时间轴，重跑生成器时它的改写结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时打印待写入清单。
> 已有语音的工程写入之前先确认 `.ast` 的 `m_FXName` 与时长是否要保留。

### 2.5 立绘素材处理（可选）

**入口只有一条：`scripts/process_leader_png.py`。** 素材已备齐时直接执行命令，不做读图分析、不做裁剪框推演、不打开图片看内容。

```bash
# 源图取自工程 AGENTS.md「美术与音频资产」表的「来源」列
python "<skills>/civ6-asset-forge/scripts/process_leader_png.py" \
  --input "<源PNG>" \
  --leader-type "<LeaderType>" \
  --project "<工程根>" --tex-dds
```

- 带 `--tex-dds` 时，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径（`Textures/` 之下的资产属可再生资产，由脚本直接覆盖）；脚本会在退出码 2 时打印待写入清单。
- 脚本按**短边居中裁剪**再缩放到 `1024×1024`，生成 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`；带 `--tex-dds` 时同步写 `.tex` 并按 `.tex` 的 `ePixelformat` 转换 DDS（TEXTURE → `R8G8B8A8_UNORM`，OPACITY → `R8_UNORM`，均带完整 mip 链）。
- 需要别的裁剪框时才加 `--crop left,top,side`（原图坐标）。**是否加这个参数，由用户指定，不自行推演。**
- `--project` + `--leader-name` 可用于从工程 SQL/XML 查找 LeaderType。

**以下情形才停下询问用户**（`SKILL.md` §三）：

| 情形 | 问什么 |
|---|---|
| 源图路径在工程 `AGENTS.md` 里未写明，或与磁盘实存文件不符 | 请用户给出源图路径 |
| 主体贴边、多主体、构图特殊 | 请用户给出裁剪范围 |
| 脚本依赖缺失（无 Pillow）、texconv 定位不到 | 请用户给出解释器或 texconv 路径 |

> `process_leader_png.py` 的 DDS 子步骤通过子进程管道调用 texconv。若运行环境禁止该管道（报 `PermissionError: [WinError 5]`），**就地停下**，把错误原文与 `.png`/`.tex` 已生成的状态报给用户，由用户决定后续，不换写法重试。

---

**输出规则：**
- 默认仅生成 PNG，输出到 `D:\desktop`：
  - `{LeaderType}_TEXTURE.png`
  - `{LeaderType}_OPACITY.png`
- 若用户要求一步到位（`--tex-dds`）：
  - 输出到项目 `<project>\Textures\`
  - 同步生成/更新 `.tex`，并将 `SourceFilePath` 指向项目内 PNG
  - 尝试调用 texconv 生成 DDS（TEXTURE：`R8G8B8A8_UNORM`；OPACITY：`R8_UNORM`）
  - 已有 `.tex` 且内容有变化时，改写结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；`.dds` 由脚本直接覆盖

**生成规则：**
- TEXTURE：1024×1024，保留透明背景（裁剪规则见「层级 1」）。
- OPACITY：以 PS Ctrl+点击图层选区语义为准，非全透明像素（`alpha > 0`）→ 纯白，全透明 → 纯黑，输出不透明黑白 PNG。

### 3. 素材文件（未提供素材时跳过）

| 素材 | 来源 | 说明 |
|------|------|------|
| `.fgx` / `.wig`（主体 + Camera） | 从已建成工程复制 | **通用平面模型，跨工程逐字节一致**（MD5：主体 fgx `D13E5D864C121D9DA51500A7DFE0DD4` / wig `B9C116E082A7DD783A89E1684ED9C0B5`；Camera fgx `7F8319922265FD53841D7C15469E4E19` / wig `C1F6B44B222FA827B683A26F411CD53E`），复制后重命名即可 |
| 环境光 dds | 从已建成工程复制 | **通用环境光贴图，跨工程逐字节一致**（MD5 `100A9AF5…54F1A6`），复制后按 `{Name}_Environment.dds` 改名即可；`gen_leader_2d.py` 会自动复制改名 |
| 立绘 png（TEXTURE / OPACITY） | 用户提供 | 用 `process_leader_png.py` 生成 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`（1024×1024）；默认输出桌面，`--tex-dds` 时输出项目 `Textures/` 并同步 `.tex`/DDS |


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
python "<skills>/civ6-asset-forge/scripts/migrate_leader_matte.py" <工程根> --write    # 迁移后的 .mtl 落 <工程>/workspace/gen/
python "<skills>/civ6-asset-forge/scripts/migrate_leader_matte.py" <Civ6工程父目录> --all-siblings --write
```

`--write` 时，命令跑完后迁移结果落在 `<工程>/workspace/gen/Materials/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时打印待写入清单。

★ 把 `workspace/gen/` 的材质写入工程后，**必须在 AssetEditor 重新 cook** 才生效（材质类属 cook 期数据）。

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

#### (2) 平面 geo 不带头发参数

`LEAD_ABBR_Name.geo` / `_Camera.geo` 的 `m_CookParams` 必须是 **`<m_Values/>`（空）** ——
纸片人**没有头发**，不得带 3D 人物几何的头发参数（`HairThickness` / `HairColor` ×4 /
`HairAccentMix` / `HairGlossPower`）；对照原版平面
`Hojo_flatBackground_Placeholder.geo`（4 顶点 / 2 图元，与纸片同构），cook 参数**就是空的**。

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
> `GrainTexture` 是 `ObjectValue`（TEXTURE）槽，纸片人不需要，模板与工程均已移除。
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

### 4. 更新工程文件

- `*.civ6proj`：新增 `ArtDefs` / `LightRigs` / `EnvironmentLights` 三个文件夹 + 3 个 Content Include：
  - `XLPs\leader_{PACK}.xlp`
  - `XLPs\Leader_LightRigs.xlp`
  - `ArtDefs\Leaders.artdef`
- **Geometries/Materials/Textures/Assets/LightRigs/EnvironmentLights 不需注册**——构建时自动扫描编译进 `Platforms\Windows\BLPs\*.blp`
- `*.Art.xml`：新增/修改 `XLPs\`、`ArtDefs\` 后**必须重新生成**——运行
  `python <civ6-modding skill>\art\gen_modartxml.py <projectRoot> --check`
  （差异人工确认后加 `--write`；`.Art.xml` 尚不存在时直写新建，已有且内容有变化时改写结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本按项目实存文件重算
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
- [ ] OPACITY 只包含纯黑和纯白两种颜色
- [ ] 文件名使用 `{LeaderType}_TEXTURE.png` / `{LeaderType}_OPACITY.png`
- [ ] 一步到位时 `.tex` 的 `SourceFilePath` 指向项目内 PNG，且 DDS 已生成（或已明确提示未生成）

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
