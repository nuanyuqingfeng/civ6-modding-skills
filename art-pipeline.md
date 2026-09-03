# art-pipeline — 素材转换子节点（PNG → DDS → .tex）

处理**用户自备美术素材**的转换、`.tex` 生成与注册联动。生图（AI 作画）不在本节点范围内。
路由到本文件 = 本次任务涉及素材文件——先读第一节铁律再动手。

---

## 一、铁律：素材处理前必须询问

任何涉及素材文件的步骤开始前，必须先询问用户：

1. **来源**：用户自备（要路径/清单）／暂缺（本次跳过该图及其全部注册条目）
2. **命名方式**：沿用用户原文件名／中文名映射（`asset_map.json` 记录 `技术名 ↔ 源名`，输出仍为技术名）
3. **多图意图**（用户提供 **≥2 张图**时必问）：拼成一张 **atlas 网格图集**（走 `make_atlas.py`，
   问清 `IconsPerRow/IconsPerColumn` 或让 AI 按组员数推荐）／**各自独立出图**（走 `convert_art.ps1`）。
   用户说"序列图""拼图""图集""合成一张"时走 atlas 路线。

**未确认前不得复制、改名、生成任何图片文件。**
被动语义：「删除 = 持久意图」——用户删掉的图永不自动恢复，只提醒缺失。

## 二、工作流（AI 决策、脚本执行）

```
用户提供成品图路径
→ AI 读项目 XLPs / Icons.xml / ArtDefs 推导每张图的技术名 + 角色（role）
→ 写 art_manifest.json（schema 见 art/art_manifest.schema.json；单图尺寸不填，由 role 内置）
→ 单图：pwsh -File <skill>\art\convert_art.ps1 -Manifest <manifest 路径>
   （内部：texconv 转 DDS → 写 asset_map.json → gen_tex.py 逐 DDS 生成 .tex）
→ 多图图集：python <skill>\art\make_atlas.py -Manifest <manifest 路径>
   （内部：组员按 grid 拼版 → 逐尺寸出整版 PNG → texconv 转 DDS → gen_tex.py 生成 .tex
     → 产出 <atlas>_registration.xml 注册片段）
→ 注册：把注册片段合并进项目 Data/Icons_*.xml；Mod.Art.xml 用
   python <skill>\art\gen_modartxml.py <projectRoot> --check 核对（差异需人工确认后 --write）
→ 检查 XLP 条目与 Textures 实存文件对齐（缺图不写条目；整包全空则不生成该 XLP，
  Art.xml 也不引用它）
→ 注册：Art.xml 的 <Content> 与 项目 `.civ6proj` 条目同步更新
```

依赖：`texconv`（缺失时脚本自动 winget 安装）、Python 3 + Pillow（make_atlas 组版用）。

## 三、图标尺寸规格全表（19 类）

数据来源：Civ6 Modding Assistant 1.6.3 `civ6/iconsize_data.pyc` 反编译表；已用本项目
`Atlas_Rgn` 序列图成品实测对齐（Districts 3×2、Leaders 3×2、Resources 6×7 各尺寸画布
均 = (IconsPerRow×s, IconsPerColumn×s)，与表逐位一致）。项目可自定义增减（如 Resources
加 32、Product 用 45），此时在 manifest atlas 条目显式填 `sizes`。

| role | 类别 | 尺寸 |
|---|---|---|
| `civ_icon` | Civilizations | 22,30,32,36,44,45,48,50,64,80,128,200,256（13 种） |
| `leader_icon` | Leaders | 32,45,48,50,55,64,80,256（8 种） |
| `building_icon` | Buildings | 32,38,50,80,128,256 |
| `citystate_icon` | Citystates | 22,30,32,36,40,44,48,64,68,80,256 |
| `civic_icon` | Civics | 38,42,128,160 |
| `district_icon` | Districts | 22,32,38,50,80,128,256 |
| `feature_icon` | Features | 50,64,256 |
| `government_icon` | Governments | 32,50 |
| `greatwork_icon` | Greatworks | 45,64,256 |
| `policy_icon` | Policies | 32,38,50,256 |
| `project_icon` | Projects | 30,32,38,50,70,80,256 |
| `resource_icon` | Resources | 38,50,64,256 |
| `stat_icon` | Stats | 16,22,32,45,55 |
| `tech_icon` | Tech | 30,38,42,128,160 |
| `unit_action_icon` | Unit_Actions | 38,50,80,256 |
| `unit_portrait` | Unit_Portraits | 38,50,70,95,200,256 |
| `unit_icon` | Units | 22,32,38,50,80,256 |
| `victory_icon` | Victories | 64,80,130,220 |
| `wonder_icon` | Wonders | 32,38,50,64,128,256 |

非图标 role（原尺寸单 DDS，不进此表）：`portrait`/`fallback`（立绘 544×968）、
`background`（1920×960）、`diplomacy_layer1..4`（960×505）、`loyalty_3d`/`loyalty_sv`
（忠诚度贴图 512/128 与 256/128，尺寸由 `civ6-loyalty-icon` skill 固定）、`custom`（兜底）。

**Atlas 图集命名约定（make_atlas.py 默认值即按此设计）：**
- 图集名统一以 `ATLAS` 起始；项目专属前缀（如示例中的 `MYMOD`）不属于本 skill 职责，由项目自身规范定义，下面用 `{PREFIX}` 占位。
- DDS 文件名：`ATLAS_{PREFIX}_ICON_{类别}{尺寸}`，或自定义模板（如 `{PREFIX}_Icon_{类别}{尺寸}`）——用 `filenamePattern` 表达；
- IconTextureAtlases.Name：`ATLAS_{PREFIX}_ICON_{类别}`；多格图集 Filename 带 `.dds` 后缀，1×1 单图集不带（make_atlas 自动处理）；
- 字体图集（FontIcon / `Baseline` 场景）：使用 `ATLAS_{PREFIX}_FONT_ICON_{类别}`，必须带 `Baseline` 属性；不要与普通 UI 图集共用 `ATLAS_{PREFIX}_ICON_` 命名。
- FOW 变体：独立一条 atlasEntries（如 `ATLAS_{PREFIX}_ICON_{类别}_FOW`），只出 256 一版全网格；
- IconDefinitions：组员顺序 = Index（行优先），组员 tech 写 `ICON_*` 全名。
- **重采样说明**：make_atlas 小尺寸缩放用 Pillow LANCZOS（锐利度优于普通插值），
  与旧序列图合成工具（普通插值）的输出允许像素级差异——尺寸/网格/命名完全一致，
  仅像素级更锐；重生成覆盖旧 DDS 前须向用户说明此差异（一致性上报守则）。

### 3.9 单位立绘（unit_portrait）与伟人立绘（great person portrait）

> 官方来源：`Base/Assets/UI/Icons/Icons_UnitPortraits.xml`、`Icons_GreatPeople.xml`、
> `PortraitSupport.lua`、`GreatPeoplePopup.lua`。本子节解决"单位立绘怎么注册、伟人立绘为什么不一样"。

#### A. 普通单位立绘（Unit Portrait）

- 尺寸：`unit_portrait` = **38 / 50 / 70 / 95 / 200 / 256**（六档）。
- 命名：`ICON_UNIT_<UnitType>_PORTRAIT`（1×1 单图集 Index=0 即可）。
- 官方解析链（`PortraitSupport.lua`，按序回退）：
  1. `ICON_[ETHNICITY_]<UnitType>_PORTRAIT_<ERA>`（如 `ICON_ETHNICITY_ASIAN_UNIT_X_PORTRAIT_RENAISSANCE`）
  2. `ICON_[ETHNICITY_]<UnitType>_PORTRAIT`
  3. `ICON_<UnitType>_PORTRAIT_<ERA>[_F/_M]`
  4. `ICON_<UnitType>_PORTRAIT[_F/_M]`
- 族裔前缀：文明 `Ethnicity` 非 `ETHNICITY_EURO` 时，UI 会带 `ICON_ETHNICITY_<ETH>_` 前缀；
  若项目文明是 `ETHNICITY_EURO`（如 RGN），**不需要**注册族裔前缀条目。
- 伟人单位额外有性别后缀 `_F/_M`（`GetGreatPersonGenderSuffix`），可按需注册
  `ICON_UNIT_<Type>_PORTRAIT_F` 等女性/男性变体。

#### B. 伟人立绘（Great Person）—— 与普通单位立绘是两套系统

1. **伟人招募面板头像（Great People Popup）**：
   - 名称 = `ICON_GENERIC_GREAT_PERSON_INDIVIDUAL_<CLASS>`（由 `GreatPeoplePopup.lua` 从 class 名生成，
     把 `GREAT_PERSON_CLASS_X` 的 `_CLASS` 替换为 `_INDIVIDUAL`）。
   - 图集 = `ICON_ATLAS_GREAT_PERSON_INDIVIDUAL`，**IconSize 105 / 216**（3×3 网格），
     官方 9 个职业通用头像（ADMIRAL/ARTIST/ENGINEER/GENERAL/MERCHANT/MUSICIAN/PROPHET/SCIENTIST/WRITER）。
   - **官方没有为每个伟人个体做专属立绘**；自定义伟人 class 时，要显示头像需注册
     `ICON_GENERIC_GREAT_PERSON_INDIVIDUAL_<自定义CLASS>`（可指向官方 generic 图集对应职业 Index，
     或自定义 105/216 图集）。
   - 若复用官方 class（如 `GREAT_PERSON_CLASS_MUSICIAN`），面板头像自动用官方 generic，无需注册。

2. **伟人单位的地图/单位面板立绘**：仍走普通 Unit Portrait（A），即 `ICON_UNIT_<Type>_PORTRAIT`。

3. **`GreatPersonIndividualIconModifiers.OverrideUnitIcon`**：只覆盖地图上的单位图标/旗帜，
   **不是**立绘；不要与 portrait 混为一谈。

4. 兄弟项目参考：Jinhsi 的自定义伟人同时注册了
   `ICON_UNIT_<自定义伟人单位>_PORTRAIT`（单位立绘 38~256）和
   `ICON_GENERIC_GREAT_PERSON_INDIVIDUAL_<自定义CLASS>`（招募面板头像，复用官方 generic Index），
   两者缺一不可。

## 四、图标规范化（icon normalization）—— 每类 Icon 遵守对应规范

> **背景**：不同来源的图标源图（画布尺寸、边距、内容填充率、是否贴边各不相同）若直接
> 进 `convert_art.ps1`（`-w/-h` 硬拉伸）或 `make_atlas.py`（正方形整体 resize），会被无脑拉伸 /
> 直接等比缩放，导致最终图标**视觉权重不均、贴边或失衡**。本节定义"先规范化、再转 DDS"的
> 专属流程，**每类 Icon 遵守各自的规范**。

### 4.1 规范结构（每类 Icon 一份）

| 字段 | 含义 |
|---|---|
| `canvas` | 统一主画布边长（该类别的最大档/基准档，px） |
| `content` | 内容最长边目标（px），占画布比例 = content/canvas |
| `color` | 剪影填充灰度（R=G=B）；彩色图标为 `None` 保留原色 |
| `status` | `verified`（已调研验证） / `inferred`（由其他类别推断，兜底） / 未定 |
| `source` | 规范依据/来源 |

引擎：`art/normalize_icon.py`（内置上述 registry `ICON_SPECS`，可 CLI / 模块 / manifest 调用）。

### 4.2 Units 图标规范（本次调研 · 已验证 verified）

- 来源：`F:\Steam\...\Base\Assets\UI\Icons\Icons_Units.xml`（`ICON_ATLAS_UNITS`
  256/80/50/38/32/22 六档 + FOW 32）+ 项目 12 个新增单位源实测。
- 参数：`canvas=256`、`content=200`（**占幅 ≈78%**）、`color=255`（白色剪影）、
  几何居中 → 四周统一边距 **≈28px**。
- **占幅要点**（本次新增的核心信息）：
  - 内容最长边缩放到 200px（256 画布的 78%），保持宽高比、等比 contain 居中；
  - 不裁剪主体、不拉伸；源图贴边/边距不均会被吸收（统一到 ~28px）；
  - 保留白色 R=G=B=255 + Alpha 定形（供游戏按玩家/文明色着色）；
  - FOW 变体单独 32（见第九节 apply_fow.py）。

```bash
# 按内建规范规范化单张
python art/normalize_icon.py --role unit_icon <源.png> <输出.png>
python art/normalize_icon.py --role unit_icon --show        # 查看该类别规范参数
```

### 4.3 其他 Icon 类别：下次触发时的三选一（必问，禁止默认）

未验证类别（building/district/wonder 等，registry 中 `status=inferred` 或未登记）**下次触发时**
（即用户给该类别素材、要求转换/导入时）必须先问用户选哪种：

1. **调研新规范**（推荐）：按 Units 的调研方式定位该类别原版规范（找 `Icons_*.xml` +
   社区笔记 + 项目实测），验证后把参数固化进 `ICON_SPECS`（`status=verified`）。
2. **原图直接入库**：用户自行处理好的/特殊的图（如 Leader 可能由用户仔细处理后才导入），
   **跳过规范化**（manifest `normalize:false` 或不写），以用户构图为准原样缩放。
3. **据其他规范推断**（兜底）：从相近类别推断参数，但**必须标记 `status=inferred`** 并
   在交付说明里注明"推断值，未经该类别专项验证"，下次仍回到三选一确认。

> 铁律衔接：本流程不豁免第一节「素材询问铁律」——处理素材前仍需先问来源/命名/多图意图；
> 三选一是在此基础上额外的一次询问。

### 4.4 manifest 接入（可选字段，默认关闭）

`entries` 与 `atlasEntries.members` 均支持（`normalize:true` 才启用）：

```jsonc
{ "tech": "ICON_UNIT_X", "role": "unit_icon",
  "source": "x.png", "normalize": true,      // 打开规范化预处理
  "canvas": 256, "content": 200, "color": 255 }  // 可选覆盖；缺省走 role 规范
```

- `normalize` 缺省 **false**＝保留现有直接缩放行为（用户构图原样入库 / 未咨询前不动）；
- 打开时：先 `normalize_icon.py` 规范化 → 再走 convert_art / make_atlas 转 DDS。
- `make_atlas.py` / `convert_art.ps1` 未内置调用，由 AI 在 manifest 里**先跑 normalize 再喂给转换器**
  （或在转换脚本内 import 处理；本 skill 优先在 AI 流程里显式两步，便于审计与回退）。

> **嵌套项目路径坑**：`make_atlas.py` 自动探测 Textures 目录依赖 `.civ6proj` 父目录名；
> 当工程目录本身带嵌套（如 `示例工程/示例工程`）时会多嵌一层 `示例工程/Textures`。
> 遇到此类结构请在 manifest 显式写 `texturesDir`（指向真实 `Textures/`），避免 DDS 落错目录。

## 五、通用转换约定（内置在 convert_art.ps1 / make_atlas.py，AI 只选 role）

- 图标类 role：多尺寸 DDS（上一节全表）；非图标 role：原尺寸单 DDS。
- 图标源图建议 ≥256×256 正方形；输出各尺寸由 texconv 缩放（atlas 组员由 Pillow 缩放后拼版）。
- 所有 DDS 统一 `R8G8B8A8_UNORM` 且**一律单 mip**：texconv 必须显式 `-m 1`——缺省或 `-m 0` 都会生成完整 mip 链（如 1440 宽图 11 级、体积 +1/3），与 AssetEditor `.tex` 的 `bUseMips=false` 约定冲突。转换后核对 DDS 头 `mips=1` 与文件大小再交付。
- **技术名区分大小写**（schema pattern 已放开）：忠诚度贴图为混合大小写（`Loyalty_Overlay_*`、`StrategicView_Loyalty_*`），artdef/XLP 引用处必须逐字符一致。

### manifest 示例

```jsonc
{
  "projectRoot": "D:\\documents\\Firaxis ModBuddy\\Civilization VI\\MyMod",
  "entries": [
    { "tech": "ICON_LEADER_CTTH",          "role": "leader_icon", "source": "卡提希娅-领袖图标.png" },
    { "tech": "LEADER_CTTH_FOREGROUND",    "role": "portrait",    "source": "D:/美术/卡提希娅立绘.png" },
    { "tech": "ICON_CIVILIZATION_MYMOD",     "role": "civ_icon",    "source": "拉古纳文明图标.png" }
  ],
  "atlasEntries": [
    {
      "atlas": "ATLAS_MYMOD_ICON_LEADERS",
      "grid": { "cols": 3, "rows": 2 },
      "role": "leader_icon",
      "members": [
        { "tech": "ICON_LEADER_CANTARELLA_QYQXP", "source": "坎特蕾拉.png" },
        { "tech": "ICON_LEADER_CARTETHYIA_QYQXP", "source": "卡提希娅.png" }
      ]
    },
    {
      "atlas": "ATLAS_MYMOD_ICON_PRODUCT",
      "grid": { "cols": 3, "rows": 3 },
      "sizes": [32, 38, 45, 50, 64, 256],
      "filenamePattern": "MYMOD_Product_Icons{size}",
      "members": [
        { "tech": "ICON_GREATWORK_PRODUCT_AUREO_MYMOD_1", "source": "奥利薇.png" }
      ]
    }
  ]
}
```

## 六、.tex 编码（重要坑，生成 .tex 时才需要知道）

AssetEditor（WinForm/.NET）读取 `.tex` 用**系统 ANSI 代码页**（中文系统 = GBK），不是 UTF-8：
`m_SourceFilePath` 含中文路径时写 UTF-8 会被 GBK 误读成乱码并令 AssetEditor 崩溃。
`art\gen_tex.py` 已内置正确处理：用 `GetACP()` 取真实代码页写出（勿用
`locale.getpreferredencoding`——Python UTF-8 模式下它误报 utf-8）；代码页装不下字符时退用
XML 字符引用转义，文件仍是合法 XML。**不要手工把 `.tex` 另存为 UTF-8。**

## 七、缺图过滤语义

- manifest 中 source 文件不存在 → 该条跳过（打印 skip），对应 XLP 条目**不写**；
- atlas 条目：单个组员缺图 → 网格留空位并 WARN（其余组员 Index 不变）；
  全部组员缺图 → 整组跳过；
- 某 XLP（Icons.xlp 等）按实存 DDS 过滤后一条不剩 → 整个文件不生成，Art.xml 不引用；
- 用户删除的图不重建、不恢复（删除 = 持久意图），仅向用户提醒缺失清单。

## 八、完成标准（对照验证）

1. `Textures\` 下 DDS 数量 = Σ(各 entry 尺寸数) + Σ(各 atlas 条目尺寸数)，每个 DDS 有同名 `.tex`；
2. atlas 画布尺寸 = (IconsPerRow×s, IconsPerColumn×s)，注册片段的 Name/Filename/Index 与
   项目 Icons XML 现状风格一致；
3. XLP 引用的每个纹理都能在 `Textures\` 找到（无悬空引用）；
4. Art.xml / `.civ6proj` 条目与磁盘一致（Project 文件同步规范）；
5. 若本次新增/修改了 `XLPs\` 或 `ArtDefs\` 文件：`gen_modartxml.py <projectRoot> --check`
   必跑，差异人工确认后才 `--write`（新增 XLP/Artdef 不重生成 Art.xml = 最常见的漏项）；
6. 未动用户未确认的任何素材文件。

## 九、FOW 迷雾变体（apply_fow.py）

原版 `*_FOW` 图标（迷雾中显示的变体）是"羊皮纸素描"风格。原版为逐图标手绘、
无法逐像素复刻；`art\apply_fow.py` 用官方
`F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets\Civ6\pantry\Textures\`
配对图集（Resources256 vs Resources256_FOW，逐桶 RGB 实测）拟合的两段式变换复刻：

1. **金调 LUT**：亮度→颜色映射，B 通道全程压低（金棕而非灰白——首版管线 B 通道
   抬太高导致灰白感，已修正）；暗部 L<40 保持深线稿色 (76,60,14)，平坦中段陡升为
   羊皮纸金，亮部为亮卡其 (218,192,100)；
2. **暗部加权排线**：45° 排线不透明度随原亮度衰减 ((1-L/255)^gamma)，阴影处排线浓、
   高光干净，近似官方"阴影用排线填充"的素描感。

```bash
python <skill>\art\apply_fow.py --input <图标.png|dds> [--output <路径>] \
    [--no-hatch] [--hatch-strength 0.6] [--hatch-gamma 1.6] [--strength 1.0]
```

- 默认输出 `<输入名>_FOW.png`；支持图集（整图处理）与 DDS 源（自动转 RGBA）
- **alpha 完整保留**（含半透明边缘）；排线只画在主体不透明区（alpha>128）
- `--no-hatch` 纯调色；`--strength <1` 与原色混合
- 产出后走常规转换：entries 用 `role=fow`（原尺寸单 DDS，与普通版同尺寸同格）；
  atlas 参照第三节 FOW 变体约定（独立 atlasEntries、只出 256 全网格）
- Data 侧按原版惯例登记 `ICON_XXX_FOW` 条目（与普通版同 atlas 同 Index 或独立 FOW atlas）
- 最像原版的做法仍是美术手绘；本工具用于程序化快速产出，效果可先出图给用户审核
