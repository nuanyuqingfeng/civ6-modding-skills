# civ6-asset-forge/TOOLS.md —— 可复用工具名录（先查这里，再动手）

> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。
> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py civ6-asset-forge` 刷新本文件。
> 本目录的工具全部零第三方依赖（Python 标准库 / Node 内置），带退出码，可直接接 CI。
> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。

## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）

| 工具 | 干什么 | 用法 |
|---|---|---|
| `scripts/build_icon_set.py` | build_icon_set.py - 由"一张头像"生成总督全套图标（色调高度一致） | `python build_icon_set.py --avatar 头像.png --outdir out --key CTTH_RGN<br>python build_icon_set.py --avatar 头像.png --outdir out --glyph 图形.png --checker` |
| `scripts/compose.py` | 确定性合成器：白色图标 + 盾形模板 → 原版风格晋升图标（库函数 compose()，也被 build_icon_set 调用） | `python compose.py <模板.png> <图标.png> <输出.png>` |
| `scripts/edge_gradient.py` | edge_gradient.py - 立绘"边缘透明渐变"处理器 | `python edge_gradient.py --input 立绘.png --outdir out --key CTTH_RGN<br>python edge_gradient.py --input a.png --input b.png --outdir out --key CTTH_RGN` |
| `scripts/gen_leader_2d.py` | gen_leader_2d.py — Civ6 2D 领袖（立绘纸片人）注册文件生成器 | `python gen_leader_2d.py --project <工程路径> [--pack 包名] [--abbr 缩写]       --leaders "Cartethyia:CTTH,Fleurdelys:FDL,Cantarella:CTRL,Ciaccona:CCN,Phoebe:PHB,Roccia:ROC"` |
| `scripts/gen_loyalty_art.py` | 文明6 忠诚度图标注册链生成：XLP / ArtDef / mtl / ast + Art.xml、civ6proj 补注册。 | `python gen_loyalty_art.py --project "<工程路径>" --civ-types CIVILIZATION_RAGUNNA_QYQXP[,CIVILIZATION_X2...]` |
| `scripts/gen_religion_art.py` | 文明6 新宗教（自定义宗教类型）压力/镜头图标注册链生成。 | `python gen_religion_art.py --project "<工程路径>" --religion-types RELIGION_CUSTOM_RGN[,RELIGION_X2...]` |
| `scripts/gen_suk_portrait.py` | gen_suk_portrait.py — Sukritact's Civ Selection Screen 适配素材与接线生成器 | `python gen_suk_portrait.py --project <工程根> --check<br>python gen_suk_portrait.py --project <工程根> --write` |
| `scripts/process_leader_png.py` | process_leader_png.py — Civ6 2D 领袖立绘 PNG -> TEXTURE/OPACITY 1024x1024 素材生成器 | `python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA_QYQXP` |
| `scripts/process_loyalty_icon.py` | 文明6 忠诚度/宗教图标合成：图标 + 黑色光晕模板 → PNG 组。 | `python process_loyalty_icon.py --kind {loyalty\|religion} (--icon <png> \| --project <工程>) --suffix <后缀> [--out-dir <目录>] [--fit-mode {core,extent}]` |
| `scripts/recolor_template.py` | 旧晋升模板 → 四类金属（platinum/gold/silver/bronze）重着色，保留浮雕细节 | `python recolor_template.py <源模板.png> <输出目录>` |
| `scripts/slice_atlas.py` | 把 Promotions32.png 图集切成 40 枚晋升图标(带类别与晋升名) | `python slice_atlas.py <Promotions32.png> <Icons_Promotions.xml> <outdir>` |
| `scripts/vcheck_multi.py` | 多图视觉复核（把若干 PNG 一起丢给 Gemini 视觉模型问一个问题） | `python vcheck_multi.py "<问题>" <图片1.png> [图片2.png ...]` |
| `scripts/verify.py` | 校验晋升图标/模板: 轮廓 IoU + 配色采样 + 图形检查 | `python verify.py <candidate.png> <gt1024.png> [--mode auto\|template\|final]` |
| `scripts/verify_badge.py` | verify_badge.py - 总督 24px 徽章几何/配色验证 | `python verify_badge.py 生成.png                  # 只做几何自洽校验<br>python verify_badge.py 生成.png 官方格.png        # 与官方对照，输出 IoU 与配色误差` |
| `scripts/verify_suk_portrait.py` | verify_suk_portrait.py — Suk 选人界面适配素材与接线的只读校验器 | `python verify_suk_portrait.py --project <工程根><br>python verify_suk_portrait.py --project <工程根> --suffix _Suk` |

共 15 个脚本。

## 路径收纳（本机绝对路径，勿写死进脚本）

Py 工具统一走路径解析器；**换机器只改 `civ6-modding/local_paths.json` 一处**。

```bash
python "<skills>/civ6-modding/tools/_paths.py"        # 打印 P1-P6 + 外部工具的实际解析结果
```

| 键 | 含义 |
|---|---|
| `modbuddy` | ModBuddy 源工程根（P1） |
| `mods` | 游戏 Mods 加载目录（P2） |
| `game` | 游戏本体：UI / Lua / XML 官方原文（P3） |
| `sdk_assets` | SDK Assets：artdef / 解包素材（P4） |
| `sdk` | SDK 工具：ModBuddy / MSBuild（P5） |
| `workshop_ref` | 创意工坊参考件，AppID 289070（P6） |
| `uploader` | 工坊上传器 exe（非 Trimmed 构建） |
| `sd_cpp` | 本地生图（stable-diffusion.cpp + FLUX 权重） |
| `imagemagick` | ImageMagick（图标阈值 / 裁边） |
| `luac` | Lua 5.1 语法检查 |
| `ws_root` | 上传临时工作区根（`%TEMP%\civ6-ws`） |
| `steam_logs` | Steam 日志目录（反查工坊条目 ID） |

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节；
> 生图**渠道可用性**（哪个模型还能用、失败模式）见
> `%USERPROFILE%\.config\opencode\imagegen-channels.md`，不在本文件维护。

<!-- MANUAL:BEGIN -->
## 人工备注（重跑生成器时原样保留）

<!-- 在这里写：工具之间的顺序、踩过的坑、必须人工确认的边界。
     不要在这里重复上表的机械信息 —— 那部分由 skill_manifest.py 重生成。 -->

### 四类素材的边界（先读 SKILL.md「一、本 skill 覆盖的四类素材」）

四类共用同一条注册链（`SKILL.md` §六），**但徽章形状不得混用**：
总督 = 八边形徽章，单位晋升 = 五边形盾形 —— 混用会一眼看出不是官方素材。

### 顺序

```
用户素材（先按 §三 铁律询问，禁止静默处理）
  → 归一化/合成（本 skill scripts）
  → PNG 组命名照官方契约
  → 注册（artdef / xlp / mtl / ast / Art.xml / .civ6proj 幂等补注册）
  → SKILL.md §七 的验证顺序
```

### 边界

- 用户素材**必须先问**（§三 铁律一）；不做静默备份（§四）。
- 原版素材只读 pantry，**禁止解包**（§五）；素材搬运边界见 §6.3（别污染工程 pantry）。
- 尺寸规格一律查 `civ6-modding/art-pipeline.md` 的图标尺寸表，不要凭记忆报数。

<!-- MANUAL:END -->
