# civ6-tuner/TOOLS.md —— 可复用工具名录（先查这里，再动手）

> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。
> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py civ6-tuner` 刷新本文件。
> 本目录的工具**以纯标准库为主**（Python 标准库 / Node 内置），带退出码，可直接接 CI；用到第三方库的脚本逐条列在下方「第三方依赖」节。
> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。

## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）

| 工具 | 干什么 | 用法 |
|---|---|---|
| `scripts/game_input.py` | 向文明6游戏窗口投递按键，不抢焦点、不影响其它窗口。 | `python game_input.py esc            # 向游戏窗口投递一次 ESC<br>python game_input.py key 0x1B       # 同上，任意虚拟键码` |
| `scripts/gamectl.py` | gamectl.py —— 文明6 对局生命周期控制（全部原语 2026-10-02/03 实机验证）。 | `gamectl.py —— 文明6 对局生命周期控制（全部原语 2026-10-02/03 实机验证）。` |
| `scripts/tuner_exec.py` | civ6-tuner：通过 FireTuner 调试接口在运行中的文明6对局内执行 Lua。 | `python tuner_exec.py {check\|exec\|ports\|logs} [...]（exec 子命令执行 Lua；需游戏内开启 Tuner 且关闭 FireTuner GUI）` |
| `scripts/tuner_link.py` | FireTuner 线协议层：帧收发、握手、Lua 执行。 | `（库：被其它脚本 import，无独立 CLI）` |
| `scripts/tuner_node.js` | FireTuner 线协议客户端（Python 不可用时的等价入口）。 | `node tuner_node.js check<br>node tuner_node.js exec --context gamecore\|ingame [--state 名字\|索引] --code <Lua>` |
| `scripts/tunerd.py` | civ6-tuner 会话守护进程：持有唯一 FireTuner 连接，向本地 CLI 提供 JSONL 请求。 | `（见脚本 docstring）` |

共 6 个脚本。

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
| `ws_root` | 上传临时工作区根；`content/` 用 junction 指向 Mods 副本（见 `release/scripts/make_workspace.ps1`） |
| `steam_logs` | Steam 日志目录（反查工坊条目 ID） |

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节。
> 全新机器上先跑一次上面那条命令：缺失的键会打印 `[缺失]`，按提示写 `local_paths.json` 即可。

<!-- MANUAL:BEGIN -->
## 人工备注（重跑生成器时原样保留）

<!-- 在这里写：工具之间的顺序、踩过的坑、必须人工确认的边界。
     不要在这里重复上表的机械信息 —— 那部分由 skill_manifest.py 重生成。 -->

### 前置条件（三条缺一不可）

1. 游戏内 Options 勾选 Tuner（或 `AppOptions.txt` 里 `EnableTuner 1`）；
2. **必须关闭 FireTuner GUI** —— 游戏只允许一个 tuner 连接；
3. 必须处于**进行中的对局**（主菜单没有 `GameCore_Tuner` / `InGame` 状态）。

端口 4318；先 `check` 探连接与对局状态，再 `exec`。

### 用它回答哪类问题

静态校验（`rgn_validate` / `api.sqlite`）回答"文档说这条 API 是什么"，
本 skill 回答"**运行时它到底是什么行为**" —— 凡是接口行为、参数语义、PROPERTY 读写时机、
跨端可见性这类问题，别靠推断，直接实测；实测出的通道口径统一记进 `civ6-modding/reference/context-matrix.md`（端内用 `LuaEvents` 首选或暴露函数；跨端四通道，暴露函数仅按钮回调禁用）。

### 边界

- SKILL.md 的**七条铁律**全部是实测结论，动手前必读（尤其"两端总线可见性不同"
  与"`GetProperty` 未设置返回 0 个值，nil 不返回"）。
- 判端口合法性**必须在调用方所在的那一端**实测，另一端的结果不算数。
- 片段库在 `<skill>/snippets/`，新写的一次性 Lua 也往里放，别散落。

### 组合动作层

`tuner_exec.py act <动作名> --参数 值` 执行预设的多步测试操作。动作片段在
`snippets/actions/<动作名>.lua`，Python 侧按 `ACTIONS` 参数表生成 CONFIG 块替换片段里的
标记区间，再按动作声明投递到对应上下文（`MainMenu` / `gamecore` / `ingame`）。

常用动作：

- `game-mode`、`leader`（MainMenu，建局前）
- `end-turn`、`select-unit`、`research-set`、`civic-set`、`city-build`（ingame）
- `build`、`gold-inject`、`faith-inject`、`tech-complete`、`civic-complete`、
  `unit-spawn`、`terrain-change`、`fog-reveal`、`snapshot`（gamecore）

研究目标、市政推进目标与城市生产队列都走**玩家操作/城市操作**通道，只有 ingame 侧能发：
`research-set` 与 `civic-set` 用 `UI.RequestPlayerOperation`（`PlayerOperations.RESEARCH` /
`PROGRESS_CIVIC` + `PARAM_INSERT_MODE=VALUE_EXCLUSIVE`）。城市生产队列的入队在 tuner 沙箱内
不可达：`CityManager.RequestOperation` 在 ingame 侧是 function、`CanStartOperation` 返回 true，
调用后 gamecore 回读 `BuildQueue:CurrentlyBuilding` 保持旧项；gamecore 侧该函数为 nil。
`city-build` 保留作通道探测，建建筑用 `build`、出兵用 `unit-spawn`。

调试技巧：

- 列出全部动作与所需上下文：`python tuner_exec.py act list`
- 查看某动作的参数表与步骤：`snippets/actions/<动作名>.lua` 的文件头注释
- 提取本次动作打点：`python tuner_exec.py logs --prefix "VERIFY_" -n 0`
- 冷路径对照：`python tuner_exec.py --no-daemon act <动作名> ...`（输出与守护进程路径一致）

动作片段的固定结构：文件头注释（参数、前置断言、执行步骤、成功判据、失败码、已知限制）、
`-- ===== CONFIG =====` 标记区间、`ASSERTION_*` / `EXECUTE` / `VERIFY_*` / `FINAL=OK|FAIL` 打点。
新增动作时两步走：在 `ACTIONS` 里登记参数表与上下文，再按同一结构写片段。

<!-- MANUAL:END -->
