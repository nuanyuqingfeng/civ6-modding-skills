← 返回 `SKILL.md` 路由

> **来源**：原 `civ6-promotion-icon` skill 的 `SKILL.md`（112 行 / 6317 字节 / LF），已并入 `civ6-asset-forge`。
> 本文件正文为原文件**逐字搬运**（未改写、未精简任何实测规格），仅做结构性处理：
> 1. 去掉 YAML frontmatter —— 原文逐字保留于下方，触发词/边界已并入 `SKILL.md` 的 description；
> 2. 文末「作者与致谢」块上移至 `SKILL.md`（四类共用一份）；
> 3. 跨 skill 引用与移动后的 `reference/` 路径已同步（见 `CHANGELOG.md`「引用修正」）；
> 4. 原 `reference/specs.md` / `reference/prompts.md` 移至 `reference/promotion-icon/`，引用已同步。
> 本文件内 `scripts/…`、`templates/…`、`assets/…`、`reference/…` 的根目录 = `civ6-asset-forge/`。

原 frontmatter（逐字保留）：

```yaml
name: civ6-promotion-icon
description: "文明6 单位晋升图标全套制作：四类金属底徽章（白金/黄金/白银/青铜，五边形盾形）+ 白色剪影合成原版风格晋升图标。内置原版实测规格（盾形轮廓/配色/图形参数）、像素级 ground-truth 模板、生图模板再造管线（FLUX img2img + 抠图 + IoU 校验）、确定性合成器与视觉验证。触发词：晋升图标、promotion icon、单位晋升、白色图标合成、盾形徽章。"
version: "1.0"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - promotion-icon
  - imagegen
  - ui-icons
  - modding
languages:
  - zh
  - en
```

---

<!-- ↓↓↓ 以下为原 SKILL.md 正文逐字内容（未改写） ↓↓↓ -->

## 目的

为 mod 新单位生成与原版同风格的**单位晋升图标**：四类金属底徽章 × 单位白色剪影图形 → 成品 PNG（1024 交付 + 32px 游戏内尺寸）。

## 强制约定（先读）

- **美术素材只允许在** `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` 内查找
  （晋升图标源：`Civ6\pantry\Textures\Promotions32.dds` 等，全部是散装文件）。
- **任何情况下不允许解包**（.blp 等打包文件不碰、不写解包器）。需要原版图就找 pantry 散装 DDS，
  用 `F:\CivNexus6\texconv.exe -ft png` 做纯格式转换即可。
- 游戏安装目录只读 XML/Lua 数据定义，不作素材来源。
- 视觉评审：gemini-3-flash-preview（密钥在 `~/.local/share/opencode/auth.json` 的 google 键，
  需走代理 `http://127.0.0.1:7897`，脚本见 `scripts/vcheck_multi.py`）。
- 生图通道优先级：多图编辑模型（gemini-3-pro-image 等）→ 实测 429 配额死则**直接回退本地 FLUX**
  （`%USERPROFILE%\sd-cpp\sd-cli.exe`，参数见 `reference/promotion-icon/prompts.md`）。

## 原版实测规格（写提示词/做校验的唯一依据）

来源：`Promotions32.dds`（8×8 图集，32px/格，40 有效格）+ `Icons_Promotions.xml`。

1. **轮廓 = 五边形盾形**：顶部水平直边（宽 24/31），两侧短直边（约 y4→y18 等宽），
   两条长斜边向内收至 y31 底尖。行宽数据见 `reference/promotion-icon/specs.md`。
2. **四类金属底色**（每类原版各 10 枚）：

| 类别 | 顶部高光 | 内部渐变(上→下) | 边框环 |
|------|------|------|------|
| 白金 platinum | (248,248,248) | (224,216,224)→(120,112,112) | 亮银白 |
| 黄金 gold | (232,232,128) | (208,208,112)→(120,104,64) | (136,128,64) |
| 白银 silver | — | (120,112,112)→(88,80,88) | (112,104,96) |
| 青铜 bronze | (192,168,120) | (120,104,64)→(80,66,40) | (120,96,64) |

3. **图形（glyph）**：深炭褐黑 RGB≈(18,8,4)，无渐变无描边，最大边 ≈ 底徽章宽度 50%~60%，
   水平居中、垂直中心约在徽章高度 44% 处，底部带柔和投影（黑，模糊≈画布0.8%，下移≈2%，不透明度≈50%）。
4. 层次：透明 → 1px 抗锯齿黑 → 深色描边环 → 顶部亮色高光带 → 金属渐变（上亮下暗）→ 图形+投影。

## 工作流

### ① 素材准备（用户提供或生成）
白色图标：纯白 `#FFFFFF` 剪影、透明背景、正方形 256~1024px、图形占画布 60%~75%。
（生成白色剪影可用 `%USERPROFILE%\sd-cpp\make-icon.ps1 -Subject "..." -Out ...`）

### ② 选模板
本 skill `assets/` 内置四类盾形模板（`TEMPLATE_{metal}_1024.png`，生图模型产出，
轮廓 IoU≥0.95 vs 像素级 ground truth `gt` 系列）。类别语义对照：
白金=精密/远程/舰队，黄金=突击/工程，白银=机动/步兵战术，青铜=近战/骑兵/通用（详见 `reference/promotion-icon/specs.md` 的 40 枚对照表）。

### ③ 合成成品
- **有多图生图模型可用时**：白图标 + 模板两张图 + `reference/promotion-icon/prompts.md` 第二节提示词（中英双语）。
- **本地管线（默认可靠路径）**：
  ```bash
  python scripts/compose.py <模板1024.png> <白图标.png> <输出.png> [scale=0.55] [cy=0.44]
  ```
  自动完成：白→#120804 重着色、按徽章宽 55% 缩放、居中(44%高)、柔和投影、输出 1024 + 32px。

### ③b 带内容旧模板的重着色（用户提供成品图/旧模板时）
不要用剪影覆盖重画，走保浮雕重着色：
```bash
python scripts/recolor_template.py <旧模板.png> <outdir>
```
管线：白底分割（剔投影）→ 浮雕系数 rel=L/Lblur → 四种实测配色行渐变 base(v)×rel^K
（K 白金1.8/黄金1.35/白银1.5/青铜1.15）→ 中性白高光提亮 → UnsharpMask 恢复棱线
→ 输出 白底/透明底/1024/game32（game32 按 24:27 占位、顶部 y=4/32 与原版图集一致）。
高光必须中性白（RGB 等量），加暖色会使白金/白银"发粉发脏"。

### ④ 验证（缺一不可）
```bash
python scripts/verify.py <成品.png> <对应gt1024.png>   # 轮廓 IoU、配色采样、图形对比度
```
再走视觉评审（vcheck_multi.py）：与原版图对照，检查轮廓/描边/高光/渐变/图形对比度。
不达标：调整 scale（0.5~0.6）或换模板种子重生成，**不要手工修图**。

### ⑤ 模板再造（需要新配色/新形状变体时）
ground-truth init（黑底 RGB）+ FLUX img2img（`--strength 0.45 --steps 4 --cfg-scale 1.0 --seed 777`，
提示词模板见 `reference/promotion-icon/prompts.md` 第三节）→ 四角泛洪抠图（`-fuzz 7% -floodfill`，禁止整幅 `-transparent black`，
否则吃掉深描边）→ `verify.py` 轮廓 IoU≥0.94 且配色贴近 `reference/promotion-icon/specs.md` 才算过。
**不要用 text2img 直出几何形状**（四步蒸馏模型画不准盾形），必须 img2img 锚定 ground truth。

### ⑥ 进游戏注册（要点）
- 成品 32px 换入图集位或自建图集：mod 内 `IconTextureAtlases`（IconSize 32）+ `Icons_Promotions.xml`
  加 `ICON_<UnitPromotionType>` 行；UI 面板底框引用原版 `Promotion_Button` 即可，无需复刻。
- 参考原版链：`Base\Assets\UI\Icons\Icons_Promotions.xml` + `UnitPromotionPopup.lua`（FindIconAtlas 32px）。

## 边界

- 不处理总督晋升（XP1/XP2_GovernorPromotions24 体系）与 3D 单位模型。
- 不修改游戏文件；生成产物一律交付到用户指定目录。
- 原 32px 图集中圆形读取是**量化误差**，以本 skill 的盾形规格为准（已 1:1 像素轮廓验证）。
