# 文生图渠道现状（Civ6 美术辅助用）

> **来源**：作者本机实测记录（最后一次复测 **2026-08-06**）。渠道状态会变，改动只需更新本文件。
> 本文件只讲"用哪个渠道出图、哪些坑不能再踩"，**具体调用方式**见 `tools/local_flux.py` /
> `tools/workshop_cover.py` / `art/make-icon.ps1`（都已内化到本 skill）。

## 一、结论速览

| 渠道 | 状态 | 说明 |
|---|---|---|
| **本地扩散模型（推荐）** | ✅ 可用 · 免费 · 全自动 | stable-diffusion.cpp + FLUX.2-klein-4B，约 4 steps / 8 秒每张；Civ6 扁平图标、封面底图优先用它 |
| 云端免费生图（各类第三方聚合） | ❌ 不可用 | 端点 404 / 超时 / 免费层不含生图模型；免费额度不稳定，不要依赖 |
| 官方 API 生图（Gemini 等） | ⚠ 视额度 | 需要自己的 key 与额度（429 quota 是常态）；生图结果建议交视觉模型复核 |
| 人工渠道（豆包 / Seedream 等客户端） | 人工 | 需要用户手动操作；作为本地渠道失败后的备用渠道 |

**优先级**：本地扩散模型 → 人工渠道 → 付费 API。

## 二、⚠ 扩散模型的文字能力（实测，别再踩）

- **中文 / 日文完全不可用**：渲染出的是形近伪字（实测 `人类玩家所有单位` → `义凵薊丨劦…`）。
  需要中文文字的成品必须走「模型输出**无字**底图 → 用真实字体排版」两步——现成实现是
  `tools/workshop_cover.py`（内置孤儿行 / 超边距自检）。
- **拉丁长句也会掉字母**：`CIVILIZATION` → `CIVILLZATION`。短标签可用，长句仍需人工核对。
- **图标类容易出线稿**：模型偶尔输出空心轮廓；`art/make-icon.ps1` 内置阈值后处理可
  解决灰阶残留，若整体是线稿就换种子重试。
- 生成结果**必须人工/视觉复核**再进管线（换 seed 重试比调提示词更快，每张约 8 秒）。

## 三、本地图标管线（`art/make-icon.ps1`）

```powershell
powershell -File art/make-icon.ps1 -Subject "a lighthouse" -Out "D:\out\icon.png" [-Seed 42] [-SdDir <sd-cpp 目录>] [-Magick <magick.exe>]
```

- `-Subject`：主体描述（英文），**不要**写风格词——脚本已内置最优提示词模板
  （`solid white filled silhouette / no outline / no line art / flat game icon / pure white on pure black`）；
- 依赖 **不随包分发**（需自备）：stable-diffusion.cpp 的 `sd-cli.exe` + FLUX.2-klein-4B 权重（Apache-2.0）、
  ImageMagick 的 `magick.exe`；路径用 `-SdDir` / `-Magick` 或环境变量 `SD_CPP` / `MAGICK` 指定；
- 输出：透明背景白色实心图标（2 色），可直接进 `art/convert_art.ps1` 转 DDS。

> 通用文生图（照片/插画风格）请直接调 `sd-cli.exe`（参数模板见 `tools/local_flux.py`），
> 它比 `make-icon.ps1` 多了数量、尺寸与提示词模板管理。
