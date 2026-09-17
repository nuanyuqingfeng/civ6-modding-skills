# civ6-art-reference/TOOLS.md —— 可复用工具名录（先查这里，再动手）

> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。
> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py civ6-art-reference` 刷新本文件。
> 本目录的工具**以纯标准库为主**（Python 标准库 / Node 内置），带退出码，可直接接 CI；用到第三方库的脚本逐条列在下方「第三方依赖」节。
> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。

## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）

| 工具 | 干什么 | 用法 |
|---|---|---|
| `scripts/art_copy.py` | ArtDef 条目克隆生成器（civ6-art-reference skill） | `python art_copy.py <模板名> <原版条目> <新条目名> [选项]` |
| `scripts/art_copy_building.py` | 替换型建筑的 3D 模型注册生成器（civ6-art-reference skill） | `python art_copy_building.py <src_building> <new_building> [--district <区域>] [--tag <token>] [--landmarks-out <path>] [--buildings-out <path>] [--dry-run]` |
| `scripts/art_lookup.py` | ArtDef 引用链查询工具（civ6-art-reference skill） | `python art_lookup.py <关键词> [模板名]           # 查包含关键词的条目及其完整引用链<br>python art_lookup.py --list <模板名> --prefix <前缀>   # 列出某模板全部条目（--prefix 按前缀过滤）` |
| `scripts/artdef_indexer.py` | 文明6 ArtDef/XLP 引用链索引器（civ6-art-reference skill 版） | `python artdef_indexer.py [--game <Civ6安装根目录>] [--sdk <SDK Assets根目录>]` |
| `scripts/artdef_sync_check.py` | artdef_sync_check.py —— ArtDef 源文件 vs Mods 副本「差异性质」判定器 | `python artdef_sync_check.py 示例工程<br>python artdef_sync_check.py "D:/.../示例工程/示例工程/ArtDefs" --name 示例工程` |

共 5 个脚本。

## 第三方依赖

本 skill 的脚本**全部零第三方依赖**（只用 Python 标准库 / Node 内置）。

## 路径收纳（本机绝对路径，勿写死进脚本）

每个 skill **各自**有一份 `local_paths.json`（个人环境文件，不入库）：

| skill | 路径解析器 | 环境变量前缀 |
|---|---|---|
| `civ6-modding` | `tools/_paths.py`（P1–P6 + 外部工具） | 见该文件 `DEFAULTS` / `TOOL_DEFAULTS` |
| `civ6-audio-pipeline` | `scripts/paths.py`（`wwcli` / `template_full` / `p1` / `p2`） | `CIV6_<KEY>`（如 `CIV6_WWCLI`） |
| 其余 skill | 无独立解析器：脚本用 CLI 参数 / 相对定位，或调用 `civ6-modding` 的解析器 | — |

```bash
python "<skills>/civ6-modding/tools/_paths.py"        # 打印 P1-P6 + 外部工具的实际解析结果
```

| 键（civ6-modding） | 含义 |
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

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节。
> 全新机器上先跑一次上面那条命令：缺失的键会打印 `[缺失]`，按提示写 `local_paths.json` 即可。

<!-- MANUAL:BEGIN -->
## 人工备注（重跑生成器时原样保留）

<!-- 在这里写：工具之间的顺序、踩过的坑、必须人工确认的边界。
     不要在这里重复上表的机械信息 —— 那部分由 skill_manifest.py 重生成。 -->

### 四步流程（与 SKILL.md 章节一一对应）

```
第一步 读文档   → artdef / xlp 的四层引用链语义（SKILL.md「第一步」）
第二步 查       → scripts/art_lookup.py（引用链索引，先查再生成）
第三步 生成     → scripts/art_copy.py（单对象） / art_copy_building.py（替换型建筑）
第四步 注册校验 → scripts/artdef_sync_check.py + SKILL.md「第四步」的验证顺序
```

### 边界

- **mod 工程目录本身就是 pantry** —— 任何位置出现 `.tex` 都会被 AssetEditor 当实体注册，
  曾致闪退；相关铁律见 SKILL.md 开头警示 + `civ6-modding` 的「Pantry 卫生与 .tex 铁律」。
- 索引过期时先跑 `scripts/artdef_indexer.py` 重建，再 `art_lookup.py` —— 拿旧索引查新素材会得到假阴性。
- 只做引用链，不做素材合成（合成去 `civ6-asset-forge`）。

<!-- MANUAL:END -->
