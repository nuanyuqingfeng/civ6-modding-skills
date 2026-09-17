# Civ6 创意工坊发布（Steam Workshop Upload / Update）

> ← 返回 `SKILL.md` 路由
>
> 定位：`civ6-modding` 的**发布分册** —— 把已经构建好的 mod 送上 Steam 创意工坊：workspace 准备 → 非 Trimmed 上传工具构建 → validate / upload → 上传后 Steam API 验证 → Clash Verge 代理节点选择与官方上传器异常诊断。

## When to Use

- 需要上传或更新 Civ6 创意工坊 mod
- 需要确认 mod 是否真的更新到 Steam（避免“0 of 0 bytes -- success”假成功）
- 遇到大文件 mod 上传超时、`PreparingContent` 卡死、`No Connection` 等异常
- 需要通过 Clash Verge 切换代理节点后再上传

## Prerequisites

- Steam 客户端已运行并登录，账号拥有 Civ6（AppID `289070`）
- 本地已有构建好的 mod 目录，包含 `.modinfo` 和其引用的全部文件
- 已构建非 Trimmed 版 `Civ6WorkshopUploader.exe`
  —— 上游源码：`https://github.com/Jianbao233/Civ6WorkshopUploader`（第三方 CLI，**不随本 skill 分发**）：
  ```powershell
  git clone https://github.com/Jianbao233/Civ6WorkshopUploader.git %TEMP%\Civ6WorkshopUploader
  powershell -File release/scripts/build.ps1        # 内部即 dotnet publish -c Release -r win-x64
  ```
  构建产物路径写进 `tools/_paths.py` 的 `uploader` 键（或环境/`local_paths.json` 覆盖）。
- Clash Verge（可选，网络差时使用）已运行

## Hard Rules

1. **必须使用非 Trimmed 构建**：
   ```powershell
   dotnet publish -c Release -r win-x64
   ```
   不要加 `-p:PublishTrimmed=true`，否则可能卡在 `PreparingContent`。

2. **workspace 固定结构**：
   ```text
   <workspace>/
   ├── workshop.json   # 元数据配置
   ├── content/        # mod 目录本身（.modinfo + 全部引用文件）
   └── mod_id.txt      # 工坊条目 ID，绝不能删除
   ```

3. **仅更新内容时，workshop.json 只写 changeNote**：
   ```json
   {
     "changeNote": "Update content (YYYY-MM-DD)"
   }
   ```
   不要写 `title` / `description` / `visibility` / `tags`。

4. **上传前必须先 validate**：
   ```text
   Civ6WorkshopUploader.exe validate -w <workspace>
   ```
   只有 exit 0 才允许 upload。

5. **上传后必须验证**：
   通过 Steam API 获取 `time_updated` / `hcontent_file`，确认内容 manifest 真的变化。

6. **大文件上传失败先等待再重试**：间隔 1–2 分钟；连续失败先检查网络/代理节点。

7. **workspace 必须建在 `%TEMP%\civ6-ws\<ModName>`**：
   - 工作区根固定为 `$env:TEMP\civ6-ws`（本机实例如 `%USERPROFILE%\AppData\Local\Temp\civ6-ws\<ModName>`）
   - **不要**用 `%TEMP%\Civ6WorkshopUploader` 做工作区根——那是上传工具本身的源码/构建目录
   - **禁止**把 workspace 建在 git 仓库内（如 ModBuddy 工程目录 `D:\documents\Firaxis ModBuddy\Civilization VI\...`）——数百 MB 的 mod 内容会污染 `git status`（untracked 大量 sql/xml/lua/artdef）
   - 旧位置 `D:\documents\Civ6WorkshopUploader` 需完整文件权限才能写入；DSH 沙箱为 "never" 审批策略时不可用，仅当策略为 "ask" 且已授权时才使用
   - TEMP 位置在 DSH 沙箱内无需提权即可读写。

8. **上传成功并验证通过后，自动删除临时 workspace**：
   - 仅当 Steam API 确认 `hcontent_file` 已变化（真成功，非 `No content change detected` 假成功）后，删除 `%TEMP%\civ6-ws\<ModName>`
   - 用 `release\scripts\cleanup.ps1 -Workspace $ws` 执行（内置路径安全校验，只允许删 `$env:TEMP\civ6-ws\` 之下）
   - **绝不动** Mods 源目录（`D:\documents\My Games\Sid Meier's Civilization VI\Mods\<ModName>`，本体所在）和旧位置 `D:\documents\Civ6WorkshopUploader`
   - 上传失败或无变化（假成功）时**保留** workspace，便于排查

## Standard Workflow

### 1. 定位本地 mod 目录

```powershell
D:\documents\My Games\Sid Meier's Civilization VI\Mods\<ModName>
```

确认存在 `<ModName>.modinfo`。

### 2. 剥离注释（发布前必跑）

对外产物不该带内部说明。**2026-09-16 起默认只剥 `.lua`**（SQL/XML 注释保留）：

```powershell
python "$env:USERPROFILE\.agents\skills\civ6-modding\tools\strip_comments.py" `
    "<Mods 路径>\<ModName>" --src "<ModBuddy 源工程>"
```

- 期望输出 `OK  目标目录 == strip(源工程)`、exit 0
- 需要旧的全类型剥离（Lua+SQL+XML+modinfo）时加 `--all-exts`
- `.lua` 剥离后自动跑 `luac -p` **差分**自检（仅「原文能过 → 剥离后不过」才算失败）；
  Civ6 的类型标注语法（`local x:table = {}`）源文件本就过不了，会被跳过并计数
- ★ 每次 `modinfo_build.py --deploy` 或 ModBuddy `Rebuild All` 都会把注释带回来，**故本步必跑**

### 3. 创建 workspace

```powershell
$ws = "$env:TEMP\civ6-ws\<ModName>"   # 固定用 TEMP 工作区根 civ6-ws（勿建在 git 仓库内）
# 复制 mod 目录（用剥离后的版本）
Copy-Item "<Mods 路径>\<ModName>" "$ws\content" -Recurse
# 写 workshop.json
# 写 mod_id.txt
```

`workshop.json` 最小内容：

```json
{
  "changeNote": "Update content (2026-08-17)"
}
```

**不想留任何更新说明**时写空对象 —— 省略的字段上传器不会触碰：

```json
{}
```

> 用了空对象后，上传器日志会显示 `Uploading '' to the steam workshop`（标题为空串），
> 这是正常的；标题/描述/标签/可见性/封面均保持原样。**上传后仍须用 Steam API 复核标题未被清空。**

### 4. validate

```powershell
& "D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe" validate -w $ws
```

- exit 0：继续
- exit 1：必须修复
- exit 2：提示级问题，确认后可继续

### 5. upload

```powershell
& "D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe" upload -w $ws
```

大文件建议给足超时（如 30 分钟），并把输出保存到日志。
注：**直调 exe 不写 `tool\logs\`**，只有 `release/scripts/upload.ps1` 包装才写日志文件。

### 6. verify

```powershell
& "$env:USERPROFILE\.agents\skills\civ6-modding\release\scripts\verify.ps1" -ItemId <id>
```

对比上传前后：

- `hcontent_file` 变了 → 内容真的更新
- `hcontent_file` 没变 → 假成功，需要排查

### 7. 更新台账

在 `workshop-ledger.md` 改四处：表 1 版本号、内容规模、历史版本、表 3 操作历史。

### 8. 清理（真成功必做）

```powershell
& "$env:USERPROFILE\.agents\skills\civ6-modding\release\scripts\cleanup.ps1" -Workspace $ws
```


## Finding Workshop Item ID

- 从 Steam 日志搜索：
  ```text
  F:\Steam\logs\workshop_log.txt
  ```
  关键词：
  ```text
  Create new workshop item ... : <id>
  Upload starting for workshop item <id>
  ```

- 或用 Steam API 按标题确认：
  ```text
  POST https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/
  ```

## Clash Verge Proxy (网络差时)

- Clash Verge API 走命名管道：
  ```text
  \.\pipe\verge-mihomo
  ```
- 辅助脚本：
  ```powershell
  release\scripts\clash_api.ps1     # 通过 named pipe 调 Clash API
  release\scripts\clash_proxy.py    # 测试节点延迟并自动选择最佳节点
  ```
- 测试 URL 建议用目标工坊页面：
  ```text
  https://steamcommunity.com/sharedfiles/filedetails/?id=<id>
  ```
- 优先选择延迟低且稳定的香港/日本 IEPL 节点。

## Troubleshooting Quick Reference

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 卡 `PreparingContent` 超过 10 分钟 | Trimmed 构建回调问题 | 换非 Trimmed 构建 |
| `k_EResultFail` / `No Connection` | Steam 内容服务器连接失败 | 检查网络/代理，间隔后重试 |
| `UploadingContent` 后失败 | 大文件传输超时 | 换节点或间隔后重试 |
| `0 of 0 bytes -- success` | 可能只是元数据更新或 chunk 已存在 | 必须验证 `hcontent_file` |
| Steam API result 9 | 条目可能私有/不可匿名查询 | 以作者身份用上传器确认，不要直接判定不存在 |
| `Upload finished ... : OK` 但 API 没变 | 假成功 | 检查日志是否有 `No content change detected` |
| validate/upload 报"未识别命令或参数"（workspace 路径含空格如 `Civilization VI`） | Start-Process -ArgumentList 会把路径按空格拆开 | 直接用 `& $tool validate -w $ws` / `& $tool upload -w $ws`（pwsh 原生引号处理） |

## Machine-Specific Defaults

- 上传工具：`D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe`
- 工作区根：`%TEMP%\civ6-ws`（= `$env:TEMP\civ6-ws`；旧位置 `D:\documents\Civ6WorkshopUploader` 仅在有完整文件权限时使用）
- Steam 日志：`F:\Steam\logs\workshop_log.txt`
- 已确认作品：
  - Changli：`<你的工坊条目 ID>`
  - Jinhsi：`3567447705`
  - Balance Patch：`3573460321`
  - Test Empty：`3679086609`

## `release/` 附带文件

| 路径 | 用途 |
|---|---|
| `release/scripts/build.ps1` | 构建非 Trimmed `Civ6WorkshopUploader.exe`（`dotnet publish -c Release -r win-x64`） |
| `release/scripts/validate.ps1` | 上传前 validate（`-Workspace <ws>`） |
| `release/scripts/upload.ps1` | 上传/更新（`-Workspace <ws> [-TimeoutSeconds 1800]`，日志默认写 `<tool目录>\logs`） |
| `release/scripts/verify.ps1` | 上传后 Steam API 验证（`-ItemId <id>`，比对 `time_updated` / `hcontent_file`） |
| `release/scripts/cleanup.ps1` | 真成功后删临时 workspace（`-Workspace <ws>`，仅允许删 `$env:TEMP\civ6-ws\` 之下） |
| `release/scripts/find_item_id.ps1` | 从 Steam 日志反查工坊条目 ID（`-ModName <名>`） |
| `release/scripts/clash_api.ps1` | Clash Verge 命名管道 API 调用壳（返回原始 HTTP 响应） |
| `release/scripts/clash_proxy.py` | 测各节点延迟并自动选择最佳节点（`--url <工坊链接>`） |
| `release/templates/workshop.update.json` | 仅更新内容时的 `workshop.json` 最小模板 |
| `release/docs/checklist.md` | 上传前 / 中 / 后逐项核对清单 |
| `release/docs/troubleshooting.md` | 六类异常的现象 / 原因 / 处理 |

## Related Skills

- `civ6-modding`（本文件所属家族，总入口见 `SKILL.md`）：Civ6 mod 本身的制作/数据库/Lua/UI 知识

---

## 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮
