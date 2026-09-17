# 原版总督素材清单（散装 DDS 实测）

来源目录（**只读，禁止解包**）：
- `...\SDK Assets\Civ6\DLC\Shared\pantry\Textures`  ← 142 个总督相关文件（立绘 + UI 组件 + 徽章）
- `...\SDK Assets\Civ6\DLC\Expansion2\pantry\Textures`  ← 18 个（`XP1_*` / `XP2_*` 图集）

转换：`civ6-modding` 的 texconv（随包内置 `civ6-modding/art/bin/texconv.exe`，定位真源 `art/_texconv.py`）
`texconv -ft png -m 1 -o <outdir> <file.dds>`

> 注意：文件名带空格的（如 `Governors_PromotionOff_Group 143.dds`）在 shell 里要加引号。

---

## 一、图标图集（8×1 与 8×2）

| 文件 | 尺寸 | 布局 | 注册 |
|------|------|------|------|
| `XP1_Governors32.dds` | 224×32 | 8×1 @32 | `ICON_ATLAS_EXPANSION_1_GOVERNORS` IconSize=32 |
| `XP1_Governors64.dds` | 448×64 | 8×1 @64 | 同名 IconSize=64 |
| `XP2_Governors32.dds` | 32×32 | 1×1 @32 | `ICON_ATLAS_EXPANSION_2_GOVERNORS`（只有 Ibrahim） |
| `XP2_Governors64.dds` | 64×64 | 1×1 @64 | 同上 |
| `XP1_GovernorPromotions24.dds` | 192×24 | 8×1 @24 | `ICON_ATLAS_EXPANSION_1_GOVERNOR_PROMOTIONS` |
| `XP2_GovernorPromotions24.dds` | 24×24 | 1×1 @24 | `ICON_ATLAS_EXPANSION_2_GOVERNOR_PROMOTIONS` |
| `XP1_GovernorsCityBannerFill32.dds` | 256×64 | **8×2** @32 | `ICON_ATLAS_EXPANSION_1_GOVERNORS_FILL` |
| `XP1_GovernorsCityBannerSlot32.dds` | 256×64 | **8×2** @32 | `ICON_ATLAS_EXPANSION_1_GOVERNORS_SLOT` |
| `XP1_GovernorsCityBannerFill22.dds` | 176×44 | 8×2 @22 `Baseline="6"` | 同名 IconSize=22 |
| `XP1_GovernorsCityBannerSlot22.dds` | 176×44 | 8×2 @22 `Baseline="6"` | 同名 |
| `XP1_Governors_Unknown32/64.dds` | 32/64 | 1×1 | 未任命占位 |
| `XP2_GovernorsCityBannerFill22/32.dds` | 同族 | — | Ibrahim 用 |

### 32px 图集 Index 顺序（`Expansion1_Icons_Governors.xml`）

| Index | GovernorType | 32px 中位色（实测） |
|-------|--------------|---------------------|
| 0 | `GOVERNOR_THE_DEFENDER` | (70, 59, 52) 暗灰褐 |
| 1 | `GOVERNOR_THE_CARDINAL` | (69, 55, 38) 暖褐 |
| 2 | `GOVERNOR_THE_BUILDER` | (78, 51, 39) 红褐 |
| 3 | `GOVERNOR_THE_AMBASSADOR` | (60, 55, 41) 橄榄 |
| 4 | `GOVERNOR_THE_RESOURCE_MANAGER` | (57, 51, 36) 暗橄榄 |
| 5 | `GOVERNOR_THE_MERCHANT` | (74, 52, 36) 红褐 |
| 6 | `GOVERNOR_THE_EDUCATOR` | (78, 64, 46) 灰褐 |
| 7 | （空） | — |

### 24px 徽章图集 Index 顺序（`Expansion1_Icons_GovernorPromotions.xml`）

| Index | IconDefinition |
|-------|----------------|
| 0 | `ICON_GOVERNOR_GENERIC_PROMOTION` ← **所有非 BaseAbility 阶位的回落目标** |
| 1 | `ICON_GOVERNOR_THE_AMBASSADOR_PROMOTION` |
| 2 | `ICON_GOVERNOR_THE_BUILDER_PROMOTION` |
| 3 | `ICON_GOVERNOR_THE_CARDINAL_PROMOTION` |
| 4 | `ICON_GOVERNOR_THE_DEFENDER_PROMOTION` |
| 5 | `ICON_GOVERNOR_THE_EDUCATOR_PROMOTION` |
| 6 | `ICON_GOVERNOR_THE_MERCHANT_PROMOTION` |
| 7 | `ICON_GOVERNOR_THE_RESOURCE_MANAGER_PROMOTION` |

### 城市横幅 8×2 图集（行主序，Index = row×8 + col）

- 行 0（idx 0–6）：7 位总督的 FILL / SLOT
- idx 7：中性灰，未任命
- 行 1 idx 8：`ICON_GOVERNOR_OTHER_AMBASSADORS_FILL/_SLOT`（中性灰，其他使节）
- idx 9–15：全透明（未使用）
- SLOT 色明显暗于 FILL（如 idx0：FILL (136,113,99) vs SLOT (46,32,26)）——SLOT 是"槽位底"，FILL 是"指派后填充"

---

## 二、立绘与 UI 组件

| 文件 | 尺寸 | 用途 |
|------|------|------|
| `GovernorNormal_<Key>.dds` | 206×208 | 立绘常态（`PortraitImage`） |
| `GovernorSelected_<Key>.dds` | 326×339 | 立绘选中态（`PortraitImageSelected`） |
| `Governors_PortraitFrame.dds` | 188×201 | 立绘外框（常态面板） |
| `Governors_ProfileFrame.dds` | 336×366 | 立绘外框（详情页九宫格，`SliceCorner="16,320"`） |
| `Governors_NamePlaque.dds` | 58×58 | 名牌底（九宫格 `SliceCorner="20,25"`） |
| `Governors_BaseAbilityBox.dds` | 57×57 | BaseAbility 底框（九宫格 `SliceCorner="28,28"`） |
| `Governors_PromotionBox.dds` | 150×150 | 晋升树底板（`SliceCorner="70,70"`） |
| `Governors_PromotionBoxGrey.dds` | 78×78 | 同上灰态 |
| `Governors_Promotion_Button.dds` | 174×847 | 晋升按钮，**7 个状态**，`StateOffsetIncrement="0,121"` |
| `Governors_PromotionOff/On_Group 142/143.dds` | 202×130 / 202×133 | 晋升格开/关组 |
| `Governors_Neutralized.dds` | 170×170 | 中立化遮罩（纯黑剪影层） |
| `Governors_PromotionScreen_DecoLeft/Right.dds` | 184×42 | 晋升页装饰（纯白，靠 Color 调色） |
| `Governors_Column_*.dds`、`Governors_BackgroundTile_*.dds` | — | 面板列/背景（九宫格或平铺） |
| `GOVERNOR_<NAME>.dds` | 178×242 或 188×272 | 旧版/占位头像集（**`Governors.Image` 列的历史值**） |
| `Moment_PromoteGovernor_<Name>.dds` | — | 晋升时刻图（Pride Moments） |

### `<Key>` 命名对照（立绘）

引擎取 `Governors.PortraitImage` 的**资产名**再减前缀：

- `GovernorNormal_<Key>` ← `PortraitImage` 去掉 `GovernorNormal` 前缀后的部分
- `GovernorSelected_<Key>` ← `PortraitImageSelected` 去掉 `GovernorSelected` 前缀

例：官方 `PortraitImage="GovernorNormal_Defender"`、`PortraitImageSelected="GovernorSelected_Defender"`。
mod 里惯用 `<Key>` = 总督缩写（如 `CTTH_RGN`）。

### `.tex` 源 PSD 路径（仅供追溯，**PSD 不存在**）

`m_SourceFilePath` 记录如 `//civ6/main/ArtDev/UI/Icons/Governors/GovernorNormal.psd`，
`m_SourceObjectName` 是 PSD 内图层名（如 `Cardinal`）。
SDK 与游戏安装目录**均无 PSD**，不要去找；以 DDS 为唯一真值。

---

## 三、引擎侧引用链速查

```
Governors.Image            -> ICON_GOVERNOR_<TYPE>            (32px, 列表/横幅)
Governors.PortraitImage    -> GovernorNormal_<Key>            (206x208)
Governors.PortraitImageSelected -> GovernorSelected_<Key>     (326x339)
GovernorPanel.lua:181      -> "ICON_"..GovernorType.."_PROMOTION"  (BaseAbility 专用)
                           -> 回落 "ICON_GOVERNOR_GENERIC_PROMOTION"
Expansion1_Icons_Governors.xml -> ICON_GOVERNOR_<TYPE>_FILL / _SLOT (城市横幅)
```

数据库列名（官方 `Expansion1_Governors.xml` `<Governors>` 行）：
`GovernorType, Image, Name, Title, ShortTitle, Description, IdentityPressure,
TransitionStrength, PortraitImage, PortraitImageSelected`
（`Image` **不是** `Icon`；`Expansion2` 额外有 `TraitType`、`Governors_XP2.AssignToMajor`）
