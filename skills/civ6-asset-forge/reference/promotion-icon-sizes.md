← 返回 `SKILL.md` 路由

# 单位晋升图标 · 尺寸与规格（类别③）

> 本类别**只有尺寸 / 格式规格**：本 skill 不提供晋升图标脚本、模板与提示词。
> 需要做图 → 走 `civ6-modding` 的 `art-pipeline.md` 通用图标管线。
>
> 数据来源：`Promotions32.dds`（SDK Assets pantry 散装 DDS → texconv 转 PNG）**1:1 像素测量**，
> 外加 `Icons_Promotions.xml` / `UnitPromotionPopup.lua` 的注册事实。

## 一、图集、按钮与交付档位

| 文件 | 尺寸 | 用途 |
|------|------|------|
| `Promotions32.dds` | **32×32 px/格**，8×8 图集（**40 有效格** = 40 枚晋升） | 晋升图标主图集，注册名 `ICON_ATLAS_PROMOTIONS` |
| `PromotionsSmall.dds` | — | **近乎空置的占位图集，不要用它** |
| `Promotion_Button.dds` | **106×106**，**5 个状态**九宫格 | 晋升面板按钮底框 |
| `Promotion_ButtonCompleted.dds` | 同族 | 已完成态按钮底框 |

- **交付档位（原管线口径）**：**1024×1024 透明 PNG**（交付源图）+ **32×32**（游戏内图集位，与 `Promotions32.dds` 一格同尺寸）。
- 原版链：`Base\Assets\UI\Icons\Icons_Promotions.xml`；
  运行时 `UnitPromotionPopup.lua` → `IconManager:FindIconAtlas("ICON_"..UnitPromotionType, 32)`。
- 40 个有效格轮廓**完全一致**（已抽 0 / 3 / 24 等格 1:1 验证）。

## 二、盾形轮廓（32px 单格，1:1 像素实测）

- 画布 **32×32**；逐行宽度（y: 宽）：
  `y0-3: 0 / y4-18: 24 / y19: 22 / y20: 21 / y21: 19 / y22: 17 / y23: 15 / y24: 13 / y25: 11 / y26: 8 / y27: 6 / y28: 4 / y29: 2-3 / y30+: 0`
- 即：顶部平边（宽 24）+ 两侧短直边（y4→y18）+ 两条长斜边向内收至 y30 底尖。
- ⚠ **4px 块量化**会把盾形底尖读成圆弧——测轮廓**必须 1:1 像素**。
- ⚠ 单位晋升是**五边形盾形**；总督 24px 徽章是**八边形**（上下切角），两套尺寸/配色/图集
  完全独立，**禁止互相套用**（对照表见 `reference/governor-art/specs.md` §2.3）。

## 三、画布占幅比例（原版 Promotions32.dds 1:1 实测）

```
盾徽宽 = 画布宽 × 75%        左右留白各 12.5%
顶部留白 = 画布高 × 12.5%     底部留白 ≈ 6%（盾高 ≈ 81~84%）
不拉伸、不变形
```

- 自检口径：盾宽/画布宽 = **0.75（±0.02）**；左右留白相等；顶部留白 ≈ **2 倍**底部留白。

## 四、图形（glyph）参数

- 核心色 **RGB≈(18,8,4)**（近黑暖褐）；**无渐变、无描边**。
- 最大边 ≈ 底徽章宽度的 **50%~60%**；水平居中；垂直中心 ≈ 徽章高度的 **44%**。
- 底部柔和投影：纯黑、模糊 ≈ 画布 **0.8%**、下移 ≈ **2%**、不透明度 ≈ **50%**。

## 五、四类金属配色与 40 格分类

四类晋升 = 四种金属底徽章，每类 10 枚。

| 类别 | 边框环实测 | 内部渐变（上→下，采样自原版） |
|------|-----------|------------------------------|
| platinum 白金 | (248,248,248) 高光环 | (224,216,224) → (184,168,184) → (120,112,112) |
| gold 黄金 | (136,128,64) | (232,232,128) → (208,208,112) → (120,104,64) |
| silver 白银 | (112,104,96) | (120,112,112) → (112,104,104) → (88,80,88) |
| bronze 青铜 | (120,96,64) | (192,168,120) → (120,104,64) → (80,66,40) |

图集 40 格 → 四类对照（`idx: 首个晋升名`）：

- **platinum**: 0 EXPERT_MARKSMAN / 4 ELITE_GUARD / 8 HOLD_THE_LINE / 16 CREEPING_ATTACK / 20 ESCORT_MOBILITY / 24 SUPER_CARRIER / 26 CAMOUFLAGE / 32 BREAKTHROUGH / 33 DROP_TANKS / 35 SUPERFORTRESS
- **gold**: 1 ADVANCED_RANGEFINDING / 5 AMBUSH / 9 URBAN_WARFARE / 12 EMPLACEMENT / 17 SPYGLASS / 21 REDEPLOY / 25 ZWEIHANDER / 28 SUPPRESSION / 34 LONG_RANGE / 36 ADVANCED_ENGINES
- **silver**: 2 COMMANDO / 6 SHRAPNEL / 10 ROUT / 13 SQUARE / 18 SENTRY / 22 GUERRILLA / 27 AMPHIBIOUS / 29 DOUBLE_ENVELOPMENT / 31 DEPREDATION / 37 FOLDING_WINGS
- **bronze**: 3 VOLLEY / 7 GRAPE_SHOT / 11 BATTLECRY / 14 TORTOISE / 15 RANGER / 19 HANGAR_DECK / 23 HELMSMAN / 30 COURSERS / 38 FLIGHT_DECK / 39 LOOT（含宗教 / 间谍系共 22 项）

类别语义：白金 = 精密/远程/舰队，黄金 = 突击/工程，白银 = 机动/步兵战术，青铜 = 近战/骑兵/通用。

## 六、注册目标与 `.dds` / `.tex` 约束

- **mod 侧注册**：自建 `IconTextureAtlases`（**`IconSize="32"`**）+ `UpdateIcons` 加
  `ICON_<UnitPromotionType>` 行。走 2D `IconTextureAtlases` 路径（引擎按 `Filename` **直接找 `.dds`**），
  **不走** `.dds`/`.tex` 的 BLP 链。
> ⚠️ **本类别（单位晋升图标）生成管线已作废**，本节仅保留尺寸/格式事实。
> **注册口径以 `civ6-art-reference/reference/chain-map.md` §七 为准**：
> - **图集贴图一律需要 XLP 条目**（`Filename` 带不带 `.dds` 都要以 stem 登记进对应 XLP）；
> - 简化点是**图片本身走 `ImportFiles`（写法与 bink 视频同款）而非丢进 `Textures/`**；
> - 仅**领袖外交相关图片**（立绘 / 外交背景 / 纸片人 TEXTURE·OPACITY）才必须走 XLP + artdef 链。
- 面板底框引用原版 `Promotion_Button` 即可，**无需复刻**。
- **本类别不产出 `.tex`**，因此没有类别专属的 `m_ClassName` / `m_Tags` / mips 取值可写。
  若工程 pantry 规范要求补 `.tex`，按 `SKILL.md` §6.2 第 5 条**通用**规则核对：
  带 alpha 的贴图用 `PF_R8G8B8A8_UNORM` + `bUseMips=false`（texconv 必须带 `-m 1`）；
  `gen_tex.py` 默认写的 `m_ClassName=UserInterface` **必须人工复核**，不要照默认值直接交。
- 原版素材来源（唯一允许）：`F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets\Civ6\pantry\Textures\`
  （散装 DDS，用 `civ6-modding` 的 texconv —— 随包内置 `civ6-modding/art/bin/texconv.exe`，
定位真源 `art/_texconv.py` —— `-ft png -m 1` 纯格式转换；**禁止解包**）。
- 范围边界：**不处理总督晋升**（XP1/XP2 `GovernorPromotions24` 体系，属类别①）与 3D 单位模型；不修改游戏文件。

## 七、如需重做

按 `civ6-modding/art-pipeline.md` 的**通用图标管线**处理（`art/normalize_icon.py` + `art/convert_art.ps1`，
role 按产出层级选）；本 skill **不再提供晋升专用脚本、模板与提示词**。
