# civ6-modding/TOOLS.md —— 可复用工具名录（先查这里，再动手）

> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。
> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py civ6-modding` 刷新本文件。
> 本目录的工具**以纯标准库为主**（Python 标准库 / Node 内置），带退出码，可直接接 CI；用到第三方库的脚本逐条列在下方「第三方依赖」节。
> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。

## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）

| 工具 | 干什么 | 用法 |
|---|---|---|
| `art/_texconv.py` | _texconv.py — texconv（外部 DDS 转换器）定位的单一真源 | `python _texconv.py                     # 自检：打印实际解析结果` |
| `art/align_tex_format.py` | align_tex_format.py — 把工程 `.tex` 的**格式类字段**对齐官方 pantry 约定 | `python align_tex_format.py <projectRoot> --check     # 体检，只报告<br>python align_tex_format.py <projectRoot> --write     # 实际改写` |
| `art/apply_fow.py` | apply_fow.py — 给图标/图集 PNG 套上原版风格的迷雾（FOW）蒙版。v4 模型。 | `python apply_fow.py --input <图标.png\|dds> [--output <路径>]` |
| `art/convert_art.ps1` | convert_art.ps1 — Civ6 素材通用转换器（读 art_manifest.json 执行） | `pwsh -File convert_art.ps1 [-Manifest <path>] [-ProjectRoot <path>]` |
| `art/dds_io.py` | dds_io.py — Civ6 单 mip RGBA8 DDS 的最小读写（零外部依赖，纯标准库 + Pillow） | `python dds_io.py --selftest <某个既有.dds> [更多.dds ...]` |
| `art/gen_modartxml.py` | gen_modartxml.py — Mod.Art.xml（AssetObjects..GameArtSpecification）生成器。 | `python gen_modartxml.py <projectRoot>            # 生成结果打印到 stdout<br>python gen_modartxml.py <projectRoot> --check    # 与项目现有 *.Art.xml 比对，只报告不写` |
| `art/gen_tex.py` | 为 {MOD_NAME}/Textures/ 下的每个 dds 文件生成同名 .tex 文件。 | `python gen_tex.py [textures_dir] [assets_dir] [asset_map_json]` |
| `art/iconify_text.py` | iconify_text.py — 给游戏文本自动插入 `[ICON_x]` 标记（文本图标化） | `python iconify_text.py <工程根> --audit<br>python iconify_text.py <工程根> --check` |
| `art/make-icon.ps1` | Civ6 白色扁平图标管线（v2 阈值版）： | `powershell -File make-icon.ps1 -Subject "a lighthouse" -Out "D:\out\icon.png" [-Seed 42]<br>powershell -File make-icon.ps1 -Subject "a sword" -Out out.png -SdDir "D:\sd-cpp"` |
| `art/make_atlas.py` | make_atlas.py — Civ6 多图网格图集（IconTextureAtlas）合成器。 | `python make_atlas.py [-Manifest art_manifest.json] [-ProjectRoot <path>]` |
| `art/make_workshop_preview.py` | make_workshop_preview.py — 工坊预览图（Steam cover）生成器 | `python make_workshop_preview.py <master.png> --out <ws>/image.png --qa<br>python make_workshop_preview.py <已有512.png> --out <ws>/image.png` |
| `art/merge_icon_registration.py` | merge_icon_registration.py — 把 make_atlas.py 产出的注册片段幂等并入项目 | `python merge_icon_registration.py <projectRoot> --fragment <...>_registration.xml` |
| `art/normalize_icon.py` | normalize_icon.py — Civ6 图标规范化预处理（art-pipeline「图标规范化」专属章节的引擎） | `python normalize_icon.py <in.png> [out.png] [--canvas 256] [--content 224] [--color 255]<br>python normalize_icon.py <in.png> --role unit_icon        # 用 registry 内置规范` |
| `art/regen_atlas_tiers.py` | regen_atlas_tiers.py — 图集中间档「母版重出」工具（修复被压对比/锐化的档位） | `python regen_atlas_tiers.py <projectRoot> --report<br>python regen_atlas_tiers.py <projectRoot> --atlas ATLAS_X --master 256 --sizes 32,50,80` |
| `art/survey_icon_atlas.py` | survey_icon_atlas.py — 按 `art-pipeline.md` §4.7 流程，「量出」某图标类别的规范 | `python survey_icon_atlas.py --atlas "<pantry>/Buildings256.dds" --role building_icon<br>python survey_icon_atlas.py --atlas Dist256.dds --grid 4x4 --min-px 20` |
| `art/verify_icon_atlas.py` | verify_icon_atlas.py — 图标图集落地自查（art-pipeline 第八节「完成标准」的可执行版） | `python verify_icon_atlas.py <projectRoot> [--icons a.xml b.xml] [--xlp a.xlp b.xlp]` |
| `art/verify_tex_class.py` | verify_tex_class.py — 校验「.tex 的 m_ClassName」与其「XLP 注册类」是否匹配 | `python verify_tex_class.py --project <工程根>              # 只查类别匹配<br>python verify_tex_class.py --project <工程根> --full        # 全量贴图体检（见下）` |
| `database/scripts/audit_schema_drift.py` | audit_schema_drift.py - guard the civ6-modding reference DB against | `python database/scripts/audit_schema_drift.py<br>python database/scripts/audit_schema_drift.py --game "F:/Steam/.../Sid Meier's Civilization VI"` |
| `database/scripts/build_localization.py` | build_localization.py — 从**本机游戏安装**按分层规则合成本地化文本库 | `python build_localization.py --report<br>python build_localization.py --build-main <主库.sqlite> --build-mode <模式库.sqlite>` |
| `database/scripts/export_side_tables.py` | export_side_tables.py — 把 `DebugLocalization.sqlite` 的**人工标注侧表**导出为随包 JSON。 | `python export_side_tables.py                 # 写入 annotations/ 下的规范位置<br>python export_side_tables.py --out <路径>    # 指定输出` |
| `database/scripts/query_api.py` | Civ6 API Query Tool — 主源 api.sqlite（含子项 sub_func_name 与运行时核验字段）， | `python query_api.py --search <关键词>              # 搜 表名/函数名/子项名/真名/id（子项一并命中）<br>python query_api.py --search <关键词> --sub-only   # 只看"本身是子项"的条目` |
| `database/scripts/query_civ6_db.py` | Civilization VI Mod Database Query Tool — SQLite CLI wrapper. | `（见脚本 docstring）` |
| `database/scripts/query_effect_args.py` | query_effect_args.py — 查「某个 EffectType / ModifierType 该填哪些参数、参数能填什么值」 | `python query_effect_args.py --effect EFFECT_ADJUST_PLOT_YIELD<br>python query_effect_args.py --modifier MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE` |
| `database/scripts/query_events.py` | Civ6 Event Query Tool — 直接查 events_enhanced.json，无需中间索引。 | `（见脚本 docstring）` |
| `database/scripts/search_impl.py` | search_impl.py — 反查「某个游戏对象/效果，原版是怎么实现的」 | `python search_impl.py --object 农场<br>python search_impl.py --object TRAIT_CIVILIZATION_KHMER_BARAYS` |
| `release/scripts/build.ps1` | 构建非 Trimmed 版 Civ6WorkshopUploader（勿用 PublishTrimmed，会卡 PreparingContent） | `powershell -File build.ps1（内部 dotnet publish -c Release -r win-x64）` |
| `release/scripts/clash_api.ps1` | Clash Verge 命名管道 API 调用壳（返回原始 HTTP 响应） | `powershell -File clash_api.ps1 -Method GET -Path "/proxies" -OutFile resp.txt` |
| `release/scripts/clash_proxy.py` | Clash Verge 代理节点测速与自动选优（上传工坊网络差时用） | `python clash_proxy.py [--url <工坊链接>] [--timeout 3000] [--max-workers 8]（测完自动选最优节点为 GLOBAL，无关闭开关）` |
| `release/scripts/cleanup.ps1` | 删除临时上传工作区（真上传成功并验证后才跑）。三重守卫：仅在 $env:TEMP\civ6-ws\ 之下 / 工作区自身非 reparse point / 先摘内部链接再递归删——content 是 junction 时 Mods 副本不受影响 | `powershell -File cleanup.ps1 -Workspace $env:TEMP\civ6-ws\<ModName>` |
| `release/scripts/ensure_uploader.ps1` | ensure_uploader.ps1 —— 工坊上传器的"自适应保障"（与音频模板 ensure_template.py 同口径） | `powershell -File ensure_uploader.ps1                 # 只检查，缺就提示（exit 2）<br>powershell -File ensure_uploader.ps1 -Confirmed      # 允许联网 clone + 构建` |
| `release/scripts/find_item_id.ps1` | 从本机 Steam 日志反查工坊条目 ID | `powershell -File find_item_id.ps1 -ModName <ModName>` |
| `release/scripts/make_workspace.ps1` | 建工坊上传工作区（首选入口）：content 用 junction 指向 Mods 副本（不物理复制 751 MB）→ workshop.json → mod_id.txt → validate，幂等可重跑 | `powershell -File make_workspace.ps1 -ModDir <Mods/<ModName>> [-ItemId <工坊ID>] [-WsRoot <根>] [-Force] [-SkipValidate]` |
| `release/scripts/upload.ps1` | 上传 / 更新工坊条目（日志默认写 <tool目录>\logs） | `powershell -File upload.ps1 -Workspace <工作区> [-TimeoutSeconds 1800]` |
| `release/scripts/validate.ps1` | 上传前 validate 工作区（exit 0 才允许 upload） | `powershell -File validate.ps1 -Workspace <工作区>` |
| `release/scripts/verify.ps1` | 上传后经 Steam API 验证（比对 time_updated / hcontent_file，识别假成功） | `powershell -File verify.ps1 -ItemId <工坊条目ID>` |
| `scripts/check_lua_registration.py` | `.lua` 注册体检 —— 用「按角色判定」的规则找出真正不会被加载的脚本。 | `python check_lua_registration.py <工程根目录> [--modinfo <构建产物.modinfo>]` |
| `scripts/check_pantry.py` | pantry 体检：`.tex` 位置 / 重名 / depot 库路径 / 非 ASCII / `.tex`↔`.dds` 配对 —— 开 AssetEditor / cook 前必跑。（注：其中 `m_SourceFilePath` 期望 `D:\desktop\<stem>.png` 这一条是**示例工程（作者 mod 工程）的约定**，不是 Civ6 通用规则；别的工程会命中 `[src-convention]` 告警，按你自己工程的约定判断即可。） | `python check_pantry.py --root <工程根> [--quiet]        # 注意：根目录只走 --root（不是位置参数），也没有贴图目录过滤选项` |
| `scripts/check_proj_content.py` | 核对 .civ6proj 的 <Content Include> 清单与实际磁盘内容是否闭合。 | `python check_proj_content.py <工程根目录><br>python check_proj_content.py --root <工程根目录>     # 等价写法` |
| `scripts/check_sql_antipatterns.py` | SQL 语义反模式静态扫描 —— 抓「语法完全合法、但语义恒假/恒错」的写法。 | `python check_sql_antipatterns.py <工程根目录> [--glob *.sql]` |
| `scripts/check_sql_exec.py` | 全工程 SQL 执行排查 —— 抓「整条语句报废」类错误（非法转义 / 字符错位）。 | `python check_sql_exec.py [--root <工程根目录>] [--base <基础库>]` |
| `scripts/check_types_kinds.py` | Types.Kind 合法性检查 —— 复现游戏加载期的 `Invalid Reference on Types.Kind`。 | `python check_types_kinds.py [--root <工程根目录>] [--db <基础库>] [--dirs Data,Mod_Adaptation]` |
| `scripts/clear_ae_cache.py` | 清除 AssetEditor 依赖缓存（可再生文件，按「备份规范」不备份、直接删）。 | `python clear_ae_cache.py [--mod <ModName>] [--dry-run]        # 动过贴图后必跑，否则 AssetEditor 结论是缓存假象` |
| `scripts/normalize_eol.py` | 归一化文本文件换行：mod 工程按「原版分层铁律」，skill 仓库一律 LF（`--repo-skill`）。 | `python normalize_eol.py <工程目录>                 # 只报告，不写盘（默认）<br>python normalize_eol.py <工程目录> --fix           # 就地归一化` |
| `scripts/rgn_validate_runner.mjs` | rgn_validate 离线执行器 v2 — 核心判定逻辑提取自 @dsh-external/dsh-rgn-tools 的 | `node rgn_validate_runner.mjs [目录=cwd] [文件模式=*.sql] [checkNaming=true] [--base <基础库>] [--static]` |
| `scripts/verify_trees.py` | Verify two directory trees are byte-identical (recursive SHA256 comparison). | `python verify_trees.py <dirA> <dirB>` |
| `tools/_paths.py` | 本机 Civ6 关键路径解析（P1–P6），全 civ6-modding/tools 共用。 | `python _paths.py                          # 自检：打印 P1-P6 关键路径 + 外部工具的实际解析结果（缺失项标 [缺失]）
python _paths.py --tool uploader            # 只打印某个外部工具的解析路径（供 shell 包装脚本调用）
python _paths.py --path mods                # 同上，取 P1-P6 路径键；未找到 exit 1、键名非法 exit 2` |
| `tools/civ_leader_data.py` | civ_leader_data.py — 新文明 / 新领袖的**数据与文本机械推导**（规格 JSON → SQL） | `python civ_leader_data.py <spec.json> --project <工程根>          # 预演（不写盘）<br>python civ_leader_data.py <spec.json> --project <工程根> --write` |
| `tools/cook_assets.py` | cook_assets.py — 无 GUI 重放 ModBuddy 的 ArtDef / XLP cook（Civ6.targets 的三组分区）。 | `python cook_assets.py <工程根>                    # 全量 cook 到 Mods 副本<br>python cook_assets.py <工程根> --check            # 只列 pantry 展开、调用清单与对账结果` |
| `tools/cook_dep.py` | cook_dep.py — 从 <ModName>.Art.xml 生成 <ModName>.dep（AssetObjects..GameDependencyData）。 | `python cook_dep.py <工程根><br>python cook_dep.py <工程根> --out "<Mods>/<ModName>"` |
| `tools/local_flux.py` | 本地 FLUX.2-klein-4B 文生图封装（免费、离线、约 8–30s/张）。 | `python local_flux.py --prompt "..." --out x.png [--seed 42] [--size 1024]<br>python local_flux.py --prompt-file p.txt --out x.png --seeds 42,7,123   # 多 seed 取样挑图` |
| `tools/modinfo_build.py` | 从 .civ6proj 派生 .modinfo（等价 ModBuddy 的构建动作），并可选部署到游戏 Mods 目录。 | `python modinfo_build.py <X.civ6proj>                 # 只生成到 <proj目录>/Build/X.modinfo<br>python modinfo_build.py <X.civ6proj> --deploy        # cook 美术产物 + 复制 Content + 写 modinfo` |
| `tools/new_project.py` | new_project.py — 从零生成 Civ6 ModBuddy 工程骨架（`.civ6proj` + 目录 + 版本控制骨架） | `python new_project.py "D:\documents\Firaxis ModBuddy\Civilization VI\MyMod" --name MyMod<br>python new_project.py <目录> --name MyMod --title-en "My Mod" --title-zh "我的模组"` |
| `tools/skill_manifest.py` | 名录生成器：扫描一个 skill 的脚本，从各自 docstring 抽出「用途 + 用法」， | `python skill_manifest.py <skill 目录名或绝对路径> [...]      # 指定 skill<br>python skill_manifest.py --all-civ6                          # 批量刷新全部 civ6-* skill` |
| `tools/verify_mod_package.py` | 交付包体检：源工程 ↔ Mods 副本 ↔ 上传工作区 三处一致性 + .modinfo 结构与引用闭合。两类预期差异自动放行：cook 产物（BLPs 与 .dep 源工程本就没有）、美术引用管线文件（见 ART_PIPELINE_EXTS，按规范不进 Content 与 Files）。ImportFiles/ 之下不豁免，须三处齐全。UpdateArt 与 .dep 另做独立硬检查，不参与软放行 | `python verify_mod_package.py --src <源工程目录> --mods <Mods/<ModName>> [--ws <上传工作区 content>] [--files a/b.lua,c.lua] [--strict]
--strict = 关掉全部放行，逐字节 + 零未登记（默认关闭）` |
| `tools/workshop_cover.py` | 工坊封面合成：生图模型出的底图/徽记 + **确定性 CJK 排版**。 | `python workshop_cover.py --bg bg_7.png --emblem emblem.png         --line1 "人类玩家所有单位" --line2 "可以建立城市"         --subtitle "CIVILIZATION VI MOD"         --master "D:\desktop\X_Surface.png" --preview out/image.png` |
| `tools/workshop_item_check.py` | 工坊条目线上状态核对（Steam Web API，无需登录）。 | `python workshop_item_check.py 3801714971 [3800974286 ...]<br>python workshop_item_check.py 3801714971 --expect-title "All Units Can Found Cities" --expect-public` |
| `tools/workshop_meta.py` | 工坊 workshop.json 生成器（多语言）。 | `python workshop_meta.py <spec.json> --out <workshop.json> [--record <存档txt>]` |

共 57 个脚本。

## 第三方依赖（非标准库）

本 skill 的脚本**多数是纯标准库**；下列脚本需要先 `pip install` 对应第三方库：

- `art/apply_fow.py` → numpy、Pillow
- `art/dds_io.py` → Pillow
- `art/make_atlas.py` → Pillow
- `art/make_workshop_preview.py` → Pillow、numpy（--qa 指标）
- `art/normalize_icon.py` → numpy、Pillow、scipy
- `art/regen_atlas_tiers.py` → numpy、Pillow
- `art/survey_icon_atlas.py` → numpy、Pillow、scipy
- `art/verify_icon_atlas.py` → numpy、Pillow
- `tools/workshop_cover.py` → Pillow

> 口径：对脚本 `import` 的实测扫描；纯标准库脚本不列。新增/改动依赖时同一次改动里更新 `skill_manifest.py` 的 `THIRD_PARTY`。

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
| `ws_root` | 上传临时工作区根；`content/` 用 junction 指向 Mods 副本（见 `release/scripts/make_workspace.ps1`） |
| `steam_logs` | Steam 日志目录（反查工坊条目 ID） |

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节。
> 全新机器上先跑一次上面那条命令：缺失的键会打印 `[缺失]`，按提示写 `local_paths.json` 即可。

<!-- MANUAL:BEGIN -->
## 人工备注（重跑生成器时原样保留）

<!-- 在这里写：工具之间的顺序、踩过的坑、必须人工确认的边界。
     不要在这里重复上表的机械信息 —— 那部分由 skill_manifest.py 重生成。 -->

### 新 mod 从工程到线上的推荐顺序

```
⓪ python tools/modinfo_build.py <X.civ6proj> --deploy   # cook 美术产物 → 生成 .modinfo → 部署到 Mods
                                                        #   --deploy 内部先调 tools/cook_assets.py
                                                        #   （ArtDef / XLP 三分区，69 次调用约 35 秒）；
                                                        #   没有 *.Art.xml 的工程加 --no-cook 跳过
                                                        # ★ 一切工作区动作都必须在本次 deploy 之后
① python tools/verify_mod_package.py --src <工程> --mods <Mods副本>
                                                        # 三处一致性 + 引用闭合
② python scripts/check_lua_registration.py <工程>       # 改过 .lua 时
   scripts/README.md「标准验证顺序」①–⑥                  # 改过 SQL 时（另有 ⓿ 运行时库）
③ release/scripts/make_workspace.ps1 -ModDir <Mods副本> -ItemId <ID>
                                                        # 建工作区（首选入口，幂等）：
                                                        #   content 用 junction 指向 Mods，不物理复制
                                                        #   → workshop.json → mod_id.txt → validate
                                                        # ★ 别再用 new -w 铺骨架；也别 Copy-Item 751 MB。
                                                        #   DSH 会话 TEMP 每会话独立 → 每次重建，别想复用
④ python tools/workshop_meta.py <spec.json> --out <ws>/workshop.json --record <桌面存档>
⑤ python tools/local_flux.py … → python tools/workshop_cover.py …
                                                        # 底图（模型，无文字）+ 封面（真实字体排版）
                                                        封面加 --preview <ws>/image.png 即成为工坊预览图
                                                        （已达标 512 成品直通、不二次缩放；不放 = 保留线上原图）
   或只需缩放：python art/make_workshop_preview.py <母版> --out <ws>/image.png --qa
                                                        # ★ 预览图缩放的执行端在 art/（单一真源）
                                                        #   别用 magick -resize 裸缩（默认 Mitchell 偏软 → 发糊）
⑥ release/scripts/validate.ps1 → upload.ps1 → verify.ps1
⑦ python tools/workshop_item_check.py <id>              # 线上复核
⑧ release/scripts/cleanup.ps1 -Workspace <ws>           # 真成功后才删工作区
                                                        # 三重守卫；content 是 junction 时日志会打印
                                                        # 「已摘除链接 → <Mods 路径>」，属正常
⑨ （下架）.\Civ6WorkshopUploader.exe remove -w <ws> -i <id>   # 不可逆，只删线上
```

> 上传工具的完整命令面（`new` / `validate` / `upload` / `remove`）、退出码
> （`0` 成功 / `1` 硬错误 / `2` validate 提示级不阻断）与 workspace 结构见
> [`release.md`](release.md)「Hard Rules」。**别用来路不明的预编译 zip 替换本机
> `tool\`**（上游无 Releases/tag/CI）——判据与实测见同节。

### 详细说明与踩坑

`tools/` 的**用法细节、顺序理由、每条教训的出处**写在 `tools/README.md`：
本文件的工具表是自动索引（防"找不到"），README 是使用说明（防"用错"），两者互补。

#### 美术引用管线文件不进 `.modinfo` 的 `<Files>` 是规范行为

美术引用链路上的文件不写进 `.civ6proj` 的 `<Content Include>`，也不进 `.modinfo` 顶层
`<Files>` —— 它们由 cook 链路承载（pantry → cooker → `BLPs` / `.dep`）。
豁免清单见 `verify_mod_package.py` 的 `ART_PIPELINE_EXTS`（按扩展名判定：`.artdef` /
`.xlp` / `.tex` / `.dds` / `.mtl` / `.geo` / `.ast` / `.lrg` / `.env` / `.fgx` / `.wig` /
`.anm` / `.s3d` / `.blb`）。

#### ★ 例外：`ImportFiles/` 之下不豁免（显式导入通道）

美术素材若走「不经 XLP 直接导入」，落点是 `ImportFiles/<子目录>/`。这类文件属**显式导入
通道**，与 cook 链路不同，与其它 ImportFiles 文件同等对待，须 `.civ6proj` 的 `<Content>` +
`<ImportFiles>` 加载动作 + `.modinfo` 顶层 `<Files>` 三处齐全。故 `verify_mod_package.py`
对 `ImportFiles/` 前缀一律不豁免，其下素材漏登记照报。

### 边界

- 本 skill 同时管着 `art/`（图标/贴图管线）与 `release/`（上传执行），两者都在上面的表里 —— 别去别处另造一份。
- 新增/改名脚本后跑 `python tools/skill_manifest.py civ6-modding`；抽不出人话的写进 `TOOLS.overrides.json`。
- 纯 C++/引擎层行为（如"FOUND_CITY 是否对非开拓者可用"）**不要靠猜**：先查 `database/api.sqlite` 的
  `verify_status/verify_scope/runtime_gp/runtime_ui`，再用游戏内 `civ6-tuner` 实测。

<!-- MANUAL:END -->
