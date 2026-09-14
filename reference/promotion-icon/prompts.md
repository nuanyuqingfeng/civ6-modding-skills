# 提示词与命令手册（civ6-promotion-icon）

## 一、合成提示词（白色图标 + 盾形模板 → 成品）

适用：任何支持多图输入的生图模型（gemini-3-pro-image / gemini-2.5-flash-image / GPT-Image / Seedream 豆包）。
Image1 = 盾形模板（TEMPLATE_{metal}_1024.png），Image2 = 白色图标剪影。

### 中文版

```
参考图1是游戏晋升徽章模板（五边形盾形金属徽章），参考图2是白色图标剪影。
请把参考图2的白色图形合成为参考图1盾徽上的图标，严格遵循以下规则：
1. 将白色图形整体重新着色为深炭褐黑色（#120804），保持轮廓与细节完全不变，不要加渐变、不要加描边、不要发光；
2. 图形缩放到盾徽宽度的55%左右，水平居中，垂直中心放在盾徽高度约44%处（略偏上）；
3. 在图形下方添加柔和投影：纯黑色、模糊半径约为画布的0.8%、向下偏移约2%、不透明度约50%；
4. 盾徽模板本身保持一个像素都不改动：金属渐变、深色描边、顶部高光带全部原样保留；
5. 背景保持透明，除盾徽和图形外不得出现任何其他元素、文字或水印；
6. 风格：扁平2D游戏UI图标，与《文明6》原版单位晋升图标一致。
输出：与参考图1同尺寸的透明背景PNG。
```

### English Version

```
Image 1 is a game promotion badge template (pentagon heater-shield metal medallion). Image 2 is a white icon silhouette.
Composite Image 2 onto Image 1 following these exact rules:
1. Recolor the white silhouette to very dark charcoal-brown (#120804). Keep its outline and every detail unchanged. No gradient, no stroke, no glow on the glyph.
2. Scale the glyph to about 55% of the shield width, centered horizontally, vertical center at about 44% of the shield height (slightly above center).
3. Add a soft drop shadow under the glyph: pure black, blur radius about 0.8% of canvas, offset about 2% downward, opacity about 50%.
4. Keep the shield template pixel-identical: metal gradient, dark rim, and top highlight band must remain untouched.
5. Transparent background. No extra elements, no text, no watermark.
6. Style: flat 2D game UI icon, matching Civilization VI vanilla unit promotion icons.
Output: transparent PNG at the same resolution as Image 1.
```

### 负向提示

```
3D render, extrusion, bevel, gradient glyph, glowing outline, text, watermark,
extra icons, circular badge, changed badge colors, opaque background, blurry edges
```

## 二、视觉评审提示（gemini-3-flash-preview）

```
左：成品晋升图标（AI合成）  右：文明6原版晋升图标（放大参照）。
评价：1) 盾形轮廓是否标准（顶平边/短直边/底部收尖）；2) 图形与底徽章对比度是否达到原版水准；
3) 图形大小与位置（约55%宽、垂直44%）是否合适；4) 有无抠图残缺或杂物；5) 10分制打分与修改建议。
```

## 三、模板再造（FLUX img2img，锚定 ground truth）

**必须 img2img**，不要 text2img 直出几何（四步蒸馏模型画不准盾形）。

准备 init：ground truth（`assets/TEMPLATE_{metal}_gt1024.png`）贴到纯黑 RGB 画布。

```powershell
& %USERPROFILE%\sd-cpp\sd-cli.exe `
  --diffusion-model "%USERPROFILE%\sd-cpp\models\flux2-klein4b\flux-2-klein-4b-Q4_0.gguf" `
  --vae "%USERPROFILE%\sd-cpp\models\flux2-klein4b\vae_small_decoder.safetensors" `
  --llm "%USERPROFILE%\sd-cpp\models\flux2-klein4b\qwen3-4b-Q4_K_M.gguf" `
  -p "<下方提示词>" -i "<init图>" --strength 0.45 --cfg-scale 1.0 --steps 4 -H 1024 -W 1024 `
  --diffusion-fa --offload-to-cpu --seed 777 -o "<raw输出>"
```

提示词骨架（`<金属描述>` 按表替换）：

```
flat 2D game UI icon of a single empty pentagon heater shield badge, flat top edge,
short straight vertical upper sides, two long angled lower sides converging to a sharp bottom point,
front view, matte flat shading, thin dark rim outline, completely empty center,
no symbol, no letter, centered, isolated on pure black background, <金属描述>
```

| 类别 | `<金属描述>` |
|------|------|
| platinum | `bright silvery white platinum metal, bright glossy highlight band along the top inner edge, gentle vertical gradient to medium warm gray at bottom` |
| gold | `muted pale yellow gold metal, buttery lemon-gold highlight band along the top inner edge, gentle vertical gradient to olive bronze at bottom` |
| silver | `medium dark steel gray metal, pale silver highlight band along the top inner edge, gentle vertical gradient to near-charcoal gray at bottom` |
| bronze | `warm copper bronze metal, light tan copper highlight band along the top inner edge, gentle vertical gradient to medium dark brown at bottom, never pure black` |

抠图（保深描边的关键——四角泛洪，禁止整幅 `-transparent black`）：

```powershell
& "C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe" <raw> -alpha set -fuzz 7% -fill none `
  -floodfill +0+0 "#000000" -floodfill +1023+0 "#000000" -floodfill +0+1023 "#000000" -floodfill +1023+1023 "#000000" <输出>
```

校验：`python scripts/verify.py <输出> assets/TEMPLATE_{metal}_gt1024.png` → 轮廓 IoU≥0.94、配色贴近 `reference/promotion-icon/specs.md`。
统一系列观感：**四张用同一种子（777）**。多试种子时 42/2024 亦可。

## 四、白色剪影生成（可选）

```powershell
& %USERPROFILE%\sd-cpp\make-icon.ps1 -Subject "a laurel wreath with a captain helmet" -Out "D:\path\icon.png" -Seed 42
```

（脚本内置最优提示词，Subject 不要写风格词；线稿化时换种子。）
