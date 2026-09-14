# 原版实测规格（civ6-promotion-icon）

数据来源：`Promotions32.dds`（SDK Assets pantry 散装 DDS → texconv 转 PNG）1:1 像素测量。

## 一、盾形轮廓（32px 单格）

- 画布 32×32；轮廓行宽（y: 宽）：
  `y0-3: 0 / y4-18: 24 / y19: 22 / y20: 21 / y21: 19 / y22: 17 / y23: 15 / y24: 13 / y25: 11 / y26: 8 / y27: 6 / y28: 4 / y29: 2-3 / y30+: 0`
- 即：顶部平边（宽24），两侧短直边（y4→y18），两条斜边收到 y30 底尖。
- 图集 40 个有效格轮廓完全一致（已抽 0/3/24 等 1:1 验证）。

## 二、四类金属配色（四类晋升 = 四种底徽章，每类 10 枚）

| 类别 | 边框环实测 | 内部渐变（上→下，采样自原版） | 生图模板实测（顶/中/底） |
|------|------|------|------|
| platinum 白金 | (248,248,248) 高光环 | (224,216,224)→(184,168,184)→(120,112,112) | (232,231,236)/(170,172,184)/(120,119,131) |
| gold 黄金 | (136,128,64) | (232,232,128)→(208,208,112)→(120,104,64) | (230,227,152)/(194,189,124)/(106,99,48) |
| silver 白银 | (112,104,96) | (120,112,112)→(112,104,104)→(88,80,88) | (183,183,186)/(157,157,160)/(78,78,81) |
| bronze 青铜 | (120,96,64) | (192,168,120)→(120,104,64)→(80,66,40) | (215,170,120)/(180,142,98)/(89,60,39) |

轮廓 IoU（生图模板 vs 像素级 ground truth）：platinum 0.956 / gold 0.962 / silver 0.965 / bronze 0.967。

## 三、图形 glyph

- 核心色 RGB≈(18,8,4)（近黑暖褐）；无渐变、无描边。
- 最大边 ≈ 底徽章宽度 50%~60%；水平居中；垂直中心 ≈ 徽章高度 44%。
- 底部柔和投影：黑、模糊 ≈ 画布 0.8%、下移 ≈ 2%、不透明度 ≈ 50%。

## 四、图集 40 格 → 四类对照（idx: 首个晋升名）

- platinum: 0 EXPERT_MARKSMAN / 4 ELITE_GUARD / 8 HOLD_THE_LINE / 16 CREEPING_ATTACK / 20 ESCORT_MOBILITY / 24 SUPER_CARRIER / 26 CAMOUFLAGE / 32 BREAKTHROUGH / 33 DROP_TANKS / 35 SUPERFORTRESS
- gold: 1 ADVANCED_RANGEFINDING / 5 AMBUSH / 9 URBAN_WARFARE / 12 EMPLACEMENT / 17 SPYGLASS / 21 REDEPLOY / 25 ZWEIHANDER / 28 SUPPRESSION / 34 LONG_RANGE / 36 ADVANCED_ENGINES
- silver: 2 COMMANDO / 6 SHRAPNEL / 10 ROUT / 13 SQUARE / 18 SENTRY / 22 GUERRILLA / 27 AMPHIBIOUS / 29 DOUBLE_ENVELOPMENT / 31 DEPREDATION / 37 FOLDING_WINGS
- bronze: 3 VOLLEY / 7 GRAPE_SHOT / 11 BATTLECRY / 14 TORTOISE / 15 RANGER / 19 HANGAR_DECK / 23 HELMSMAN / 30 COURSERS / 38 FLIGHT_DECK / 39 LOOT(含宗教/间谍系共 22 项)

## 五、相关资产与注册链

- 图集注册：`Base\Assets\UI\Icons\Icons_Promotions.xml` → `ICON_ATLAS_PROMOTIONS`（32px, 8×8, Promotions32.dds）
- 面板底框：`Promotion_Button.dds`（106×106×5 状态九宫格）/ `Promotion_ButtonCompleted.dds`
- 运行时：`UnitPromotionPopup.lua` → `IconManager:FindIconAtlas("ICON_"..UnitPromotionType, 32)`
- 素材路径（唯一允许）：`F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets\Civ6\pantry\Textures\`
- mod 侧注册：自建 `IconTextureAtlases`（IconSize 32）+ `ICON_<UnitPromotionType>` 行（UpdateIcons）

## 六、已知坑

1. 4px 块量化会把盾形底尖读成圆弧——测轮廓必须 1:1 像素。
2. FLUX text2img 直出"圆形徽章"倾向极强，盾形必须 img2img 锚定 GT。
3. 泛洪抠图前若先 `-trim`，会破坏与 init 的对齐（IoU 掉到 0.7）——先抠图后裁。
4. img2img 打磨成品会把细线条图形变细变虚（glyph IoU 0.74~0.84），交付版用确定性合成。
5. `PromotionsSmall.dds` 近乎空置，是占位图集，不要用它。
