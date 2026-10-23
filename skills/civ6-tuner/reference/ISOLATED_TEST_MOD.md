# 隔离测试 Mod（按需使用）

## 使用判据

只有需要验证 **mod 加载与注册语义** 时才使用隔离测试 Mod：

- `modinfo` 动作（`<File>`、`LoadOrder`、`Priority`、`<Criteria>`）
- `ImportFiles` 注册与 `include` 展开
- `AddUserInterfaces` 注册的独立 UI 上下文
- `UpdateArt`、`.dep`、`ModArtLoader` 链路
- 需要把测试文件与真实工程完全隔离，避免测试文件进入工程目录或 Mods 副本

以下场景直接在当前对局执行，不使用测试 Mod：

- `gamecore` / `ingame` 的 API 行为、参数语义、PROPERTY 读写
- Modifier / RequirementSet 是否入库及挂载链
- 事件通道可达性
- 破坏性操作（删单位、改地形、灭亡玩家等）

理由：`gamecore` 与 `ingame` 是独立的沙箱 Lua 态，不属于任何 mod 的 `_ENV`（见 SKILL.md 铁律 1）。

## 路径

- 用 `python "<skills>/civ6-modding/tools/_paths.py"` 的 `mods` 键取得游戏 Mods 根。
- 测试 Mod 固定目录名：`!!!!!_TEST_MOD_EMPTY`。
- 文档与脚本只使用解析结果拼接路径，不写死本机绝对路径。

## 最小可用形态

目录内至少需要一个 `.modinfo`：

- 新生成唯一 GUID，禁止复用任何真实工程、示例模板或创意工坊条目的 GUID。
- `<Authors>` 写 `千与千寻瀑`。
- 没有测试文件时，不写 `<File>` 与 Actions；需要承载测试文件时，再按本次测试增加最小条目。
- 不复制真实工程的 `Data/`、`Text/`、`Scripts/`、`UI/` 内容。
- 不参与 git，不做交付物，不跑工程门禁。

## 生命周期

1. 按 SKILL.md 前置条件启动游戏并进入对局。
2. 目录为空或缺少 `.modinfo` 时，先创建最小形态。
3. 在游戏 Mods 列表启用测试 Mod；需要重新解析 `modinfo` 时按 SKILL.md「改动生效路径速查」执行 `kill` + `launch` + `load`。
4. 普通探针仍用：

   ```bash
   python "<skill>/scripts/tuner_exec.py" exec --context gamecore --file <lua>
   python "<skill>/scripts/tuner_exec.py" exec --context ingame --file <lua>
   ```

5. 只有测试该 Mod 自己的 UI 上下文时才用：

   ```bash
   python "<skill>/scripts/tuner_exec.py" exec --state <上下文名> --file <lua>
   ```

6. 用 `logs --prefix` 提取本次打点。
7. 收尾：

   ```bash
   python "<skill>/scripts/tuner_exec.py" daemon stop
   ```

   - 删除一次性 Lua 与截图。
   - 测试 Mod 保持禁用或删除，避免影响正常游玩。

## 边界

- 测试 Mod 内的改动永不回写真实工程。验证通过后，按目标工程的写回规则重新实施。
- 测试 Mod 不替代目标工程的 Mods 副本；双目录工作流仍以目标工程为准。
- 破坏性操作边界以 SKILL.md「破坏性操作边界」节为准。
- 不把测试 Mod 的目录写进项目规则或项目 AGENTS.md。

## 已知限制

- 空目录不能被游戏识别为 Mod；缺少 `.modinfo` 时，`--state` 测试无从谈起。
- 项目 `workspace/` 中的一次性脚本不属于本 skill；存在路径或格式化缺陷时不得作为执行入口。
- 测试 Mod 的 UI 上下文名称由该 Mod 自己的 `AddUserInterfaces` 注册决定，不能凭空猜测。

## 验证清单

- `tuner_exec.py check` 退出码为 0。
- 游戏 Mods 列表能看到测试 Mod。
- `exec --state <上下文名>` 返回预期输出。
- `logs --prefix` 能提取到本次打点。
- 收尾后临时文件已删除，测试 Mod 已禁用或删除。
