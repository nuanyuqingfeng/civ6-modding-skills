← 返回 `SKILL.md` 路由

> 本文件内 `scripts/…`、`templates/…`、`assets/…`、`reference/…` 的根目录 = `civ6-asset-forge/`。

## 目的

为 mod 新增总督生成**与原版同风格且彼此色调一致**的全套素材，并解决立绘的
**边缘透明渐变**问题。两条独立管线：

| 需求 | 入口 | 产出 |
|------|------|------|
| ① 给一张头像 → 生成风格接近的晋升/就职等图标（要求色调高度一致） | `scripts/build_icon_set.py` | 24px 徽章 + 32/64px 图标 + 两种立绘尺寸 |
| ② 给两张立绘 → 自动做好边缘透明渐变 | `scripts/edge_gradient.py` | 软边透明 PNG + 1024² TEXTURE + 1024² OPACITY（保留渐变） |

规格全部来自 **1:1 像素实测**。
详见 `reference/governor-art/specs.md`（完整规格）与 `reference/governor-art/palette.json`（实测配色）。
素材清单见 `reference/governor-art/inventory.md`。

---

## 强制约定（先读）

- **美术素材只允许在** `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` 内查找。
  总督素材在 `Civ6\DLC\Shared\pantry\Textures`（142 个文件）与 `Civ6\DLC\Expansion2\pantry\Textures`。
- **任何情况下不允许解包**（.blp 不碰）。需要原版图就用 pantry 散装 DDS，
  用 **`civ6-modding` 的 texconv**（随包内置 `civ6-modding/art/bin/texconv.exe`，定位真源 `art/_texconv.py`）
  跑 `texconv -ft png -m 1 -o <dir> <file.dds>` 做纯格式转换。
- 游戏安装目录只读 XML/Lua 定义，不作素材来源。
- 交付产物一律写到用户指定目录；**不修改游戏文件**。
- 视觉评审：视觉评审不可用（模型侧 429 / 配额耗尽）时不要反复重试，改用本地像素度量（`scripts/verify_badge.py`）
  + 输出棋盘底预览图给人眼验收。

---

## 一、核心认知：原版总督体系到底有哪些素材

**一个总督 = 6 组素材**。引擎侧查表来源：
`Expansion1/2_Governors.xml`、`GovernorPanel.lua`、`GovernorDetailsPanel.xml/.lua`。

| # | 素材 | 尺寸 | 图集 | 命名（mod 照抄） |
|---|------|------|------|------------------|
| 1 | 头像小图标 | 32 | 8×1 | `ICON_GOVERNOR_<TYPE>` |
| 2 | 头像小图标 @2x | 64 | 8×1 | 同上 Atlas，`IconSize="64"` |
| 3 | 就职/晋升徽章 | 24 | 8×1 | `ICON_GOVERNOR_<TYPE>_PROMOTION` |
| 4 | 立绘（常态） | 206×208 | 单图 | `GovernorNormal_<Key>` |
| 5 | 立绘（选中） | 326×339 | 单图 | `GovernorSelected_<Key>` |
| 6 | 城市横幅滴 | 32 / 22 | 8×2 | `ICON_GOVERNOR_<TYPE>_FILL` / `_SLOT` |

### 三条必须知道的事实

1. **晋升阶位没有独立图标。** `GovernorPanel.lua:181` 只对 BaseAbility 查
   `ICON_<GovernorType>_PROMOTION`，其余 5 个阶位一律回落
   `ICON_GOVERNOR_GENERIC_PROMOTION`；`GovernorDetailsPanel.xml` 的 promotion 按钮
   是纯文字（Name + Description），连图标位都没有。
   → **所以"给几个晋升图标"= 每个总督一张 `_PROMOTION` 徽章**，不可能是每阶一张（"每阶一张"须改 UI，见「边界」）。
2. **官方 8 格徽章互为同色。** 实测八格中位色跨度仅 135→220 灰阶，色相统一暖橄榄金
   （**与立绘颜色无相关性**）。总督的"颜色身份"由 **立绘 + 32/64px 图标**承载，不在徽章里。
   → 所以 `build_icon_set.py` 的"徽章跟随头像色相"是**主动增强**，不是复刻；
     要严格复刻原版请加 `--strict-canon`。
3. **官方立绘是硬边**（透明→不透明仅 1~2px 抗锯齿，实测边缘 alpha 均值 0.45~0.56），
   **没有软渐变**。`GovernorNormal/Selected` 各总督内容 bbox 都不同（128×203~206×203），
   说明是手工摆位、无统一裁剪算法。
   → `edge_gradient.py` 的柔性边缘是**为 mod 素材质量服务**，不是模仿原版。

---

## 二、管线①：头像 → 全套图标（`scripts/build_icon_set.py`）

```bash
python scripts/build_icon_set.py --avatar 头像.png --outdir out --key CTTH_RGN --checker
python scripts/build_icon_set.py --avatar 头像.png --outdir out --key CTTH_RGN --glyph 剪影.png
python scripts/build_icon_set.py --avatar 头像.png --outdir out --strict-canon   # 徽章不跟随头像色相
```

产出：`<key>_PROMOTION24.png` / `_32.png` / `_64.png` / `_Normal_206x208.png` /
`_Selected_326x339.png` / `_preview.png`（棋盘底验收图）。

**设计原则**

- **结构锁死**：八边形轮廓（逐行跨度表）、镜面斜面梯度曲线、1px 高光边、
  图形占格 45~55% —— 全部用原版实测常量，不随输入变化。
- **色调驱动**：色相/饱和度取自头像（HSV 圆平均主色，按饱和度×明度加权），
  亮度曲线沿用原版。默认色相混合比 `HUE_FOLLOW=0.35`（35% 头像 + 65% 原版暖金血统），
  
- 同一头像出的整组素材共用一套 `tone_params`，**彼此必然同色**；改头像即整组联动。

**徽章内部图形（glyph）**：默认空（原版 Generic 就是空徽章）。要放图形用 `--glyph`，
传任意 PNG（只取 alpha），会自动缩放到徽章宽 52% 并居中、重着色为 `tp["glyph"]`。

---

## 三、管线②：立绘边缘透明渐变（`scripts/edge_gradient.py`）

```bash
python scripts/edge_gradient.py --input 立绘A.png --outdir out --key CTTH_RGN --governor-sizes --checker
python scripts/edge_gradient.py --input 立绘A.png --input 立绘B.png --outdir out --key CTTH_RGN
python scripts/edge_gradient.py --input a.png --outdir out --feather 2.5 --spill 0.6 --lift 0.3
```

产出：`_soft.png`、`_1024_TEXTURE.png`、`_1024_OPACITY.png`（**保留渐变**，非二值化）、
可选 `_Normal_206x208.png` / `_Selected_326x339.png`、`_preview.png`。

**三步处理**

1. **去杂边（unspill）**：按直通合成公式 `C = F·α + B·(1−α)` 反解
   `F = (C − B·(1−α)) / α`，其中 B 用**最外圈**（α∈0.03~0.28）中位数估计。
   这才能去掉"抠图残留背景色"造成的黑边/白边。
   ⚠ **绝不能用 `RGB/α` 直接反预乘** —— PNG/Civ6 用的是直通 alpha，那样会把边缘冲成纯白。
2. **羽化并重塑（alpha_curve）**：高斯羽化 + gamma + 中间调抬升，得到平滑渐变带；
   末端压到 0 保证四边全透明。
3. **边缘保色**：半透明像素保持**未预乘原色**（Civ6 `PF_R8G8B8A8_UNORM` 直通，不预乘）。

### ⚠ 羽化前必须先"铺满前景色"（最容易犯的错）

**错误做法**：直接对 alpha 做高斯羽化 → 原本全透明区域的 RGB 是垃圾数据（近黑），
被羽化"半透明化"后在人物外围形成**黑边光晕**。
实测污染画面 **1.7% 面积**，新增的半透明像素里 **96% 是近黑 RGB(5,5,5)**。

**正确顺序（`process()` 已强制）**：

1. `extend_rgb_nearest()` —— 用 EDT 最近邻把不透明内芯的 RGB 蔓延填满整幅透明区
2. 再 `unspill()` 去脏边（可选）
3. 最后才 `alpha_curve()` 改 alpha

修复前后对比（同一张 1211×786 立绘，feather=1.5）：

| | 新增半透明像素 | 其 RGB 均值 | 近黑个数 |
|---|---|---|---|
| 错误 | 16154 | **(5,5,5)** | **15472 (96%)** |
| 正确 | 16154 | (140,121,111) | 474 |

### ⚠ 默认值就是"不要乱动作画"

素材若**已经是手绘好抗锯齿边的透明 PNG**，正确做法是**几乎什么都不做**：
`--feather 0 --spill 0`（默认值）只跑安全检查、原样输出。

- `--feather > 0` 会把柔边带从 ~1% 扩到 4~5%（**糊边**）。
- `--spill > 0` 会改动你原有边缘像素的颜色（实测平均偏移 **34/255**），可能把边缘洗淡。
  确认真有残留背景色才开 0.3~0.6。

### 量化坑：别用"边缘偏离前景色"当质量指标

该指标**会被黑边光晕骗**（黑边被 unspill 拉向中间色 → 指标反而"变好"）。
正确指标：**新增半透明像素里近黑/近白的比例应接近 0**。

**与 2D 领袖（`reference/leader-2d.md`）管线的关系**

`scripts/process_leader_png.py`（见 `reference/leader-2d.md`） 把 alpha **二值化**
（`mask = 255 if a > threshold else 0`），边缘是硬切，放大后有锯齿和白边。
本 skill 的 `edge_gradient.py` 是它的**增强替代**：
**OPACITY 保留真实渐变带**，不做阈值二值化。
→ 给 2D 领袖做贴图时优先用本脚本产出的 `_1024_TEXTURE.png` / `_1024_OPACITY.png`，
两者尺寸/命名与 leader-2d 完全兼容，可直接替换。

---

## 四、验证（缺一不可）

```bash
python scripts/verify_badge.py <生成的24px徽章.png> [官方对应格.png]
```

- 有官方对照时：输出轮廓 IoU（**应 ≥0.95，本管线实测 0.985**）、逐行跨度一致性、
  逐行均色误差、P90 高光/P10 暗部对比。轮廓跨度表应**零差异**。
- 无对照时：只校验几何自洽（18 行、y=3..20、最宽 18px、左右居中）。
- 肉眼验收：看 `_preview.png`（棋盘底），确认无脏边、渐变自然。

---

## 五、进游戏注册（要点）

> ⚠ **注册链的单一真源在 `civ6-modding/governor-authoring.md` ⑩「图标与立绘」**（另一入口是
> `civ6-modding/SKILL.md` 的 Task Routing「总督」行）。本节只补**美术侧**要点（`.tex` 类别 / XLP / 规格），
> SQL 与 XML 片段与那边**必须一致**；改注册写法时**两处一起改**（或直接以 `governor-authoring.md` 为准）。

**数据库**（照抄原版列名，注意 `Image` 不是 `Icon`）：

```sql
INSERT OR REPLACE INTO Governors
  (GovernorType, Name, IdentityPressure, Title, ShortTitle, Description,
   TransitionStrength, Image, PortraitImage, PortraitImageSelected)
VALUES
  ('GOVERNOR_CTTH_RGN','LOC_GOVERNOR_CTTH_RGN_NAME',8,'LOC_..._TITLE','LOC_..._SHORT_TITLE',
   'LOC_..._DESCRIPTION',150,'GOVERNOR_CTTH_RGN',
   'GovernorNormal_CTTH_RGN','GovernorSelected_CTTH_RGN');
```

> ⚠ **`Image` 列填的是不带 `ICON_` 前缀的纹理名**（官方 `Expansion1_Governors.xml` 实测形如
> `Image="GOVERNOR_CITY_DEFENDER"`，一个带 `ICON_` 的都没有）；引擎自己找 `ICON_<Image>`，
> 也就是下面 `IconDefinitions` 里那条 `ICON_GOVERNOR_CTTH_RGN`。写成 `'ICON_GOVERNOR_...'`
> 会去找 `ICON_ICON_GOVERNOR_...` → 图标静默不显示。（口径同 `civ6-modding/governor-authoring.md` §二②）

**图标注册**（图集 + 图标定义，两行凑齐 32/64 两个 IconSize 共用一个 Atlas 名）：

```xml
<IconTextureAtlases>
  <Row Name="ICON_ATLAS_RGN_GOVERNORS" IconSize="32" IconsPerRow="1" IconsPerColumn="1"
       Filename="RGN_Governor32.dds"/>
  <Row Name="ICON_ATLAS_RGN_GOVERNORS" IconSize="64" IconsPerRow="1" IconsPerColumn="1"
       Filename="RGN_Governor64.dds"/>
  <Row Name="ICON_ATLAS_RGN_GOV_PROMO" IconSize="24" IconsPerRow="1" IconsPerColumn="1"
       Filename="RGN_GovernorPromo24.dds"/>
</IconTextureAtlases>
<IconDefinitions>
  <Row Name="ICON_GOVERNOR_CTTH_RGN"            Atlas="ICON_ATLAS_RGN_GOVERNORS"  Index="0"/>
  <Row Name="ICON_GOVERNOR_CTTH_RGN_PROMOTION"  Atlas="ICON_ATLAS_RGN_GOV_PROMO"  Index="0"/>
</IconDefinitions>
```

**`.tex` 要点**：带 alpha 的贴图用 `PF_R8G8B8A8_UNORM` + **`bUseMips=false`**
→ texconv 必须带 `-m 1`（否则默认生成完整 mip 链，与 .tex 声明冲突）。
OPACITY 用单通道 `PF_R8_UNORM`。项目既有 `.tex` 模板可直接照抄字段顺序。

**XLP**：把贴图加进项目的 `XLPs/Icons.xlp`；
`.civ6proj` 的 Content **不必**登记（理由与实测证据见 `loyalty-icon.md` §六.5），
但 `.Art.xml` 的 consumer 声明必须同步。

---

## 边界

- 不做 3D 总督模型、不做城市横幅滴的 UI 布局改动（只出贴图）。
- 不修改 `GovernorPanel.lua` 的图标查找逻辑（即"每阶一张图"需要自行改 UI）。
- 官方 PSD 源文件在 `.tex` 的 `m_SourceFilePath` 里有路径记录，但 SDK 与游戏目录**均无 PSD**，
  只能以 DDS 为唯一真值；不要去找 PSD。
- 单位晋升图标（原类别③）的**生成管线已作废**，尺寸规格见 `reference/promotion-icon-sizes.md`（五边形盾形、四类金属），
  **不要**把总督的八边形徽章套到单位晋升上。
