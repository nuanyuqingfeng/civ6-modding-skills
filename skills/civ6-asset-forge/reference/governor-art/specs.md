# 总督（Governor）素材实测规格

数据来源：`Sid Meier's Civilization VI SDK Assets` 散装 DDS（pantry，禁止解包）→
**`civ6-modding` 的 texconv**（随包内置 `civ6-modding/art/bin/texconv.exe`，定位真源
`civ6-modding/art/_texconv.py`）`-ft png` 纯格式转换 → 1:1 像素测量。
全量清单见 `reference/governor-art/inventory.md`，配色表见 `reference/governor-art/palette.json`。

---

## 一、素材清单：一个总督 = 6 组素材

引擎侧查表结果（`Expansion1/2_Governors.xml` + `GovernorPanel.lua` + `GovernorDetailsPanel.xml`）：

| # | 素材 | 尺寸 | 图集布局 | 命名（mod 须照抄） | 引擎引用点 |
|---|------|------|----------|--------------------|-----------|
| 1 | 头像小图标 | 32px | 8×1 | `ICON_GOVERNOR_<TYPE>` | 城市横幅 / 任命面板 / 列表 |
| 2 | 头像小图标 @2x | 64px | 8×1 | 同上（同 Atlas 名，IconSize=64） | 高 DPI |
| 3 | 就职/晋升徽章 | 24px | 8×1 | `ICON_GOVERNOR_<TYPE>_PROMOTION` | `GovernorPanel.lua` BaseAbilityIcon |
| 4 | 立绘（常态） | 206×208 | 单图 | `GovernorNormal_<Key>` | `GovernorPanel/DetailsPanel` `SetTexture(governor.PortraitImage)` |
| 5 | 立绘（选中态） | 326×339 | 单图 | `GovernorSelected_<Key>` | `SetTexture(governor.PortraitImageSelected)` |
| 6 | 城市横幅滴 | 32px / 22px | 8×2 | `ICON_GOVERNOR_<TYPE>_FILL` / `_SLOT` | 城市横幅总督计量条 |

> `Governors.Image` 列（32px 小图标）在 SQL 里是**表列名 `Image`**，不是 `Icon`；
> `PortraitImage` / `PortraitImageSelected` 是**资产名**（不带扩展名、不带目录）。

### 关键结论（已逐条验证）

1. **晋升阶位没有独立图标。** `GovernorPanel.lua:181`
   `local iconName = "ICON_" .. governorDefinition.GovernorType .. "_PROMOTION"`
   `if not promotion.BaseAbility or not promotionInstance.PromotionIcon:SetIcon(iconName) then`
   `    promotionInstance.PromotionIcon:SetIcon("ICON_GOVERNOR_GENERIC_PROMOTION") end`
   → **只有 BaseAbility 用 `ICON_<GovernorType>_PROMOTION`，其余 5 个阶位一律回落通用图标**；
   `GovernorDetailsPanel.xml` 的 PromotionButton 更是纯文字（Name + Description），无图标位。
2. 官方 8 位总督的 24px 图集里，**8 格共用同一套暖橄榄-古铜徽章**，只有亮度分档差异
   （`metal_median` 实测跨度 135→220 灰阶）。**总督色身份不在徽章里**，而是由
   `GovernorNormal/Selected` 立绘 + 32/64px 头像逐格承载。
   → 因此"色调高度一致"的正确做法是：**整组 6 件素材取自同一头像调色板**，不是给每个图标单独配色。
3. 官方 `GovernorNormal` / `GovernorSelected` 是**硬边**元素：透明→不透明过渡仅 1~2px 抗锯齿
   （实测边缘 1px 处 alpha 均值 0.45~0.56），**没有软渐变**。
   立绘内容 bbox 各总督不同（128×203 ~ 206×203），说明是手工摆位，无统一裁剪算法。
4. `GovernorNormal.psd` 等的源 PSD 在 `.tex` 的 `m_SourceFilePath` 里有路径记录
   （`//civ6/main/ArtDev/UI/Icons/Governors/`），但**SDK 与游戏目录均无 PSD**，只能以 DDS 为唯一真值。

---

## 二、24px 就职/晋升徽章（核心模板，1:1 实测）

### 2.1 轮廓：上下切角正八边形（**不是圆、不是盾形**）

24×24 画布，有效内容 y=3..20（18 行）。逐行 x 跨度（alpha>140，cell1 实测，八个格一致）：

```
y= 0,1,2 : 空
y= 3     : x 8..15   w= 8
y= 4     : x 7..16   w=10
y= 5     : x 6..17   w=12
y= 6     : x 5..18   w=14
y= 7     : x 4..19   w=16
y= 8..15 : x 3..20   w=18   (8 行直边，最宽)
y=16     : x 4..19   w=16
y=17     : x 5..18   w=14
y=18     : x 6..17   w=12
y=19     : x 7..16   w=10
y=20     : x 8..15   w= 8
y=21..23 : 空
```

→ 顶/底各 5 级 45° 切角（每行缩 1px），中间 8 行满宽 18px，水平居中（左右各留 3px）。
对应 32px 头像图标用同一形状族：中段满宽 24px、顶底各 4 行平边（见 `Promotions32` 同款五边形对照说明，
总督体系统一用**八边形**）。

### 2.2 配色：**镜面斜面（mirrored bevel）**，不是线性渐变

实测逐行均值（alpha>0.9，官方八格一致）显示：顶部与底部**都亮**，中部**最暗** ——
这是金属徽章的倒角高光，上下近似对称：

| 画布 y | RGB | 层 |
|--------|-----|-----|
| 3 | (230, 226, 199) | 顶边抗锯齿 |
| 4 | **(238, 234, 206)** | 顶部倒角高光（最亮） |
| 5 | (197, 193, 165) | 次亮环 |
| 7 | (143, 139, 111) | 上部倾斜面 |
| 8–10 | (134, 130, 102)~(141, 137, 109) | 中位 |
| 11–12 | (129, 125, 97)→(112, 108, 80) | 收窄 |
| **13** | **(105, 101, 73)** | **中部最暗带** |
| 15 | (111, 107, 79) | 回亮 |
| 16–18 | (130, 126, 98)→(158, 154, 126) | 下部斜面 |
| 19 | (188, 184, 156) | 次亮环 |
| 20 | (212, 208, 181) | 底部倒角高光 |

- 色相 ≈ 51°（暖黄绿），饱和度中低。
- **内部图形（glyph）**：(73, 69, 41) 深橄榄褐，纯剪影、无描边、无渐变，
  最大边 ≈ 徽章宽度 45%~55%，居中略偏上。
- ⚠ **八格互为同色**：这是全体系唯一一套徽章配色，**与总督立绘颜色无相关性**。
  总督的颜色身份由立绘 + 32/64px 图标承载（见第三节）。
- 平滑曲线（供合成器使用）见 `reference/governor-art/palette.json` 的 `tone_lock_defaults` 与
  `scripts/build_icon_set.py` 的 `GRADIENT_STOPS`。

### 2.3 与单位晋升的区别（勿混用）

| | 单位晋升 | 总督就职/晋升 |
|---|---|---|
| 源图集 | `Promotions32.dds` 32px 8×8 | `XP1/XP2_GovernorPromotions24.dds` 24px 8×1 |
| 轮廓 | 五边形盾形（顶平边 24、底尖） | **八边形**（顶底 5 级切角） |
| 四大金属类 | 白金/黄金/白银/青铜 | **单一暖橄榄金**（无四类） |
| 图形色 | (18,8,4) 近黑暖褐 | (73,69,41) 深橄榄 |

→ 单位晋升（原类别③，**生成管线已作废**）的尺寸规格见 `reference/promotion-icon-sizes.md`，**不要**套用到总督。

---

## 三、32 / 64px 头像图标（8×1 图集）

- 布局：`XP1_Governors32.dds` = 224×32（8 格 ×32），`XP1_Governors64.dds` = 448×64（8 格 ×64）。
  注册：`IconsPerRow="8" IconsPerColumn="1"`，`Index` 从左到右 0..7。
- 单格不透明占比实测 **62%**（八格高度一致）→ 内容为圆形/八边形裁切的头像 + 深色描边环。
- 单格均色（cell0..6 = Defender/Cardinal/Builder/Ambassador/ResourceManager/Merchant/Educator）：
  `(83,72,63) (102,67,47) (99,63,52) (80,73,65) (76,58,45) (92,56,44) (95,84,68)`
  → **每格色相差异明显**，证实颜色身份在此层承载（红褐 / 暗灰 / 橄榄等）。
- 城市横幅 `Fill32/Slot32` = 256×64（IconsPerRow=8, IconsPerColumn=2，共 16 格），
  另 22px 变体 `Baseline="6"`；同族色相偏中性暖灰。

---

## 四、立绘（GovernorNormal / GovernorSelected）

| 项 | 常态 | 选中态 |
|----|------|--------|
| 画布 | 206×208 | 326×339 |
| 不透明占比 | 40%~67% | 42%~69% |
| 边缘过渡 | 1~2px AA | 1~2px AA |
| 内容 bbox | 128×203 ~ 206×203（各不同） | 同族 |
| 像素格式 | `PF_R8G8B8A8_UNORM`（预乘无、不压缩、无 mip，`bUseMips=false`） | 同 |

- 选中态平均亮度高于常态（同人同色调），差异在**轮廓装饰与打光**，不在色相。
- 两个状态必须同源同裁剪，仅做亮度/装饰分级。

---

## 五、纹理导出约定（写 `.tex` 用）

引擎实测（`GovernorNormal_Cardinal.tex`）：

```xml
<ePixelformat>PF_R8G8B8A8_UNORM</ePixelformat>
<eFilterType>FT_LANCZOS6</eFilterType>
<bUseMips>false</bUseMips>
<iColorKeyX>64</iColorKeyX> <iColorKeyY>64</iColorKeyY> <iColorKeyZ>64</iColorKeyZ>
<eExportMode>TEXTURE_2D</eExportMode>
<TexturePadding>2</TexturePadding>
```

- 带 alpha 的立绘/图标：`PF_R8G8B8A8_UNORM`，**`bUseMips=false`**
  → texconv 必须加 `-m 1`（否则默认生成完整 mip 链，与 .tex 声明冲突）。
- 纯遮罩（OPACITY）用单通道 `PF_R8_UNORM`。
- 项目既有 `.tex` 模板：`D:\...\示例工程\Textures\*.tex`（照抄字段顺序）。
