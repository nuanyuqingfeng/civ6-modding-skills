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
  —— 上游源码：**`https://github.com/Jianbao233/Civ6WorkshopUploader`**（第三方 CLI，MIT，**不随本 skill 分发**；
  本机实测与上游同版：commit `e7dc27a`，无本地改动）。
  用本 skill 的自适应脚本一键获取（与音频模板的 `ensure_template.py` 同口径：**先询问、再联网、可回退**）：

  ```powershell
  powershell -File release/scripts/ensure_uploader.ps1              # 只检查；缺则 exit 2 并打印上游地址
  powershell -File release/scripts/ensure_uploader.ps1 -Confirmed   # 允许后 clone + 构建(非 Trimmed) + 组装 tool\
  ```
  脚本会把可执行文件放到 `<To>\tool\Civ6WorkshopUploader.exe` 并打印该写进哪：
  `civ6-modding/local_paths.json` 的 `uploader` 键（也可用环境变量/`-Tool` 参数覆盖）。
  手动等价流程：`git clone` 上游 → `powershell -File release/scripts/build.ps1`（内部即
  `dotnet publish -c Release -r win-x64`，**勿加** `-p:PublishTrimmed=true`）→ 把 `steam\steam_api64.dll`、
  `steam\steam_appid.txt` 与 `template\` 一并复制到 exe 同级。
- Clash Verge（可选，网络差时使用）已运行

> ⚠ **不要用来路不明的预编译 zip 替换本机 `tool\`**。上游仓库**没有 Releases、没有 tag、没有 CI**
> （`has_downloads: false`，`/releases` 返回 `[]`），所以任何 `Civ6WorkshopUploader-*-win-x64.zip`
> 都不是官方分发产物。2026-09 实测过一份网传 `1.0.0-win-x64.zip`：其代码提交与本地同源
> （`e7dc27a..17b3206` 之间仅两处 README 改动、**零代码差异**），但产物是 **Trimmed 构建**
> （exe 16 MB vs 本地非 Trimmed 68 MB；内嵌程序集 57 vs 200，缺 `System.Linq.Expressions` /
> `System.ComponentModel.TypeConverter` 等）——正是下文硬规则 ① 禁止的形态，有卡
> `PreparingContent` 的风险，且当年堆栈缺 `.cs` 行号（无 PDB）。**换过去零收益、纯担风险。**
> 判据：`Civ6WorkshopUploader.exe --version` 打印的 commit 只说明**源码**同版，**不能**证明构建方式；
> 要比就比 in-tree 体积与 `tool\` 里有没有 `.pdb`。

## Hard Rules

1. **必须使用非 Trimmed 构建**：
   ```powershell
   dotnet publish -c Release -r win-x64
   ```
   不要加 `-p:PublishTrimmed=true`，否则可能卡在 `PreparingContent`。
   判据（2026-09 实测）：非 Trimmed ≈ **68 MB** 且 `tool\` 有 `.pdb`；Trimmed ≈ **16 MB** 且无 PDB。

2. **命令面与退出码**：

   ```text
   Civ6WorkshopUploader.exe new      -w <dir>          从模板建 workspace 骨架
   Civ6WorkshopUploader.exe validate -w <dir>          上传前建议性检查
   Civ6WorkshopUploader.exe upload   -w <dir> [-i <id>] 创建新条目或更新已有条目
   Civ6WorkshopUploader.exe remove   -w <dir> [-i <id>] 删除工坊条目（不可逆）
   ```

   | 退出码 | 含义 | 处理 |
   |---|---|---|
   | `0` | 成功 | 继续 |
   | `1` | **硬错误**（缺 `workshop.json` / 参数错 / SteamAPI 初始化失败 / 条目不存在） | 必须先修 |
   | `2` | validate 的**提示级**问题 | **不阻断**，但**不代表可以忽略**（见 §4） |

   - ★ `remove` **不可逆**，且**只删线上条目、本地 workspace 不受影响**；执行前先确认条目 ID（台账 + `mod_id.txt` 双核对）。
   - ★ `new` 的模板路径是**相对路径** `new DirectoryInfo("template")` ——
     **必须让 cwd = exe 所在目录**，否则报 `Template not found at <cwd>\template` 直接 exit 1。
     等价写法：`Push-Location <tool 目录>; & .\Civ6WorkshopUploader.exe new -w $ws; Pop-Location`
     （`& $tool new -w $ws` 从任意 cwd 调用**同样会失败**，因为 exe 不会切自己的 cwd）。
   - `new` 只铺骨架（`workshop.json` / `README.md` / `content/`）——它出的 `workshop.json` 是模板占位，
     **多语言与正文仍应按 §3 用 `workshop_meta.py` 生成并覆盖**。

3. **workspace 固定结构**：
   ```text
   <workspace>/
   ├── workshop.json   # 元数据配置
   ├── image.png       # 工坊预览图——可选（存在才上传，对齐官方上传器）
   ├── content/        # mod 目录本身（.modinfo + 全部引用文件）
   └── mod_id.txt      # 工坊条目 ID，绝不能删除
   ```
   `image.png` 缺省即跳过预览图上传（**不报错、不阻断**），条目会保留原有预览图。
   要放图时用 `tools/workshop_cover.py --preview <ws>\image.png` 直接产出，别手工缩图。

4. **仅更新内容时，workshop.json 只写 changeNote**：
   ```json
   {
     "changeNote": "Update content (YYYY-MM-DD)"
   }
   ```
   不要写 `title` / `description` / `visibility` / `tags`。

5. **上传前必须先 validate**：
   ```text
   Civ6WorkshopUploader.exe validate -w <workspace>
   ```
   只有 exit 0 才允许 upload（exit 2 为提示级，确认后可继续）。

6. **上传后必须验证**：
   通过 Steam API 获取 `time_updated` / `hcontent_file`，确认内容 manifest 真的变化。

7. **大文件上传失败先等待再重试**：间隔 1–2 分钟；连续失败先检查网络/代理节点。

8. **workspace 必须建在 `%TEMP%\civ6-ws\<ModName>`**：
   - 工作区根固定为 `$env:TEMP\civ6-ws`（本机实例如 `%USERPROFILE%\AppData\Local\Temp\civ6-ws\<ModName>`）
   - **不要**用 `%TEMP%\Civ6WorkshopUploader` 做工作区根——那是上传工具本身的源码/构建目录
   - **禁止**把 workspace 建在 git 仓库内（如 ModBuddy 工程目录 `D:\documents\Firaxis ModBuddy\Civilization VI\...`）——数百 MB 的 mod 内容会污染 `git status`（untracked 大量 sql/xml/lua/artdef）
   - 旧位置 `D:\documents\Civ6WorkshopUploader` 需完整文件权限才能写入；DSH 沙箱为 "never" 审批策略时不可用，仅当策略为 "ask" 且已授权时才使用
   - TEMP 位置在 DSH 沙箱内无需提权即可读写。
   - ★ **`content/` 用 junction 指向 Mods 副本，不要物理复制**（见 Hard Rules ⑩）：
     一次 `Copy-Item` 在本项目要 751 MB / 约 7 秒，且复制完成后 Mods 若再改动，工作区就悄悄
     变成旧版（`verify_mod_package.py` 三处比对的经典假红灯来源）。junction 下工作区与 Mods
     恒等：零复制、零漂移、零清理成本。
   - ★ DSH 会话在 `workspace-write` 策略下 `$env:TEMP` 是**每会话独立目录**（形如
     `...\Temp\dsh-<id>`），上一会话的工作区在下一会话既看不到、也过不了 `cleanup.ps1`
     的根路径守卫。所以「复用旧 workspace」在 DSH 里通常不成立 —— junction 方案下重建成本
     只有 1 MB 的壳加一条链，**默认每次都重建**即可。

9. **上传成功并验证通过后，自动删除临时 workspace**：
   - 仅当 Steam API 确认 `hcontent_file` 已变化（真成功，非 `No content change detected` 假成功）后，删除 `%TEMP%\civ6-ws\<ModName>`
   - 用 `release\scripts\cleanup.ps1 -Workspace $ws` 执行（内置路径安全校验，只允许删 `$env:TEMP\civ6-ws\` 之下）
   - **绝不动** Mods 源目录（`D:\documents\My Games\Sid Meier's Civilization VI\Mods\<ModName>`，本体所在）和旧位置 `D:\documents\Civ6WorkshopUploader`
   - 上传失败或无变化（假成功）时**保留** workspace，便于排查

10. **`content/` 必须是「指向 Mods 副本的 junction」，不是物理复制**：

    ```powershell
    New-Item -ItemType Junction -Path "$ws\content" -Target "<Mods 路径>\<ModName>"
    ```

    - **为什么可以**：上传器对 `content/` 的要求是「一个装着 mod 的目录」，源码里没有任何
      一步会解析 reparse point 或拒绝链接（`UploadCommand.cs` 只做 `DirectoryInfo.Exists`
      → `SteamUGC.SetItemContent(路径)`；`ValidateCommand.cs` 用
      `GetFiles("*.modinfo", SearchOption.AllDirectories)`）。**已实测**：走 junction 建的工作区
      `validate` exit 0 且逐条检查通过，与真目录完全等价。
    - **为什么该做**：本项目 Mods 副本 420 文件 / 751 MB，其中 **98% 是 cooker 产物**
      （`.blp` 306 MB + `.bik` 221 MB + `.wem` 209 MB），源工程里根本没有这 51 个文件。
      junction 把每次发布的复制量从 751 MB 降到 0。
    - **★ 语义变化**：`strip_comments.py` 是**就地写盘**的不可逆操作（无 dry-run）。content 是
      junction 时，剥离**直接改的就是 Mods 副本本体**，不再是「改副本→（忘）回拷」。
      最终状态相同（发布口径本就是「Mods 副本 == strip(源工程)」），但「就地」这个性质别忘，
      尤其**别在剥离后、上传前又对 Mods 做修改**。
    - **清理安全**：实测 `Remove-Item -Recurse` 作用在**含 junction 的父目录**上时，PS 5.1 与
      PS 7.6 都只删链接本身、**绝不递归进目标**（目标目录原封不动）。`cleanup.ps1` 在此之上
      另加三重守卫（见该脚本头注释）。
    - **重建工作区**：`release/scripts/make_workspace.ps1` 已把这套流程（建链 → workshop.json →
      mod_id.txt → 剥离 → validate）固化成一个幂等脚本，**它是本节的执行端**：

      ```powershell
      powershell -File release/scripts/make_workspace.ps1 `
          -ModDir "D:\...\Mods\<ModName>" -ItemId <工坊ID> -Src "<ModBuddy 源工程>"
      ```

## Standard Workflow

### 1. 定位本地 mod 目录

```powershell
D:\documents\My Games\Sid Meier's Civilization VI\Mods\<ModName>
```

确认存在 `<ModName>.modinfo`。

### 2. 剥离注释（发布前必跑）

> **用 `make_workspace.ps1` 时本步已内置**（§3 ③ 会连剥离一起做）——那就**跳过本节**，
> 直接看 §3。本节是「脚本不可用」或「想单独剥离并核对」时的手工流程。
> 无论走哪条路，**顺序恒定：`modinfo_build.py --deploy`（或 Rebuild All）→ 剥离 → 上传**，
> 因为每次部署都会把注释带回来。

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
- ★ 本步是**就地写盘**的不可逆操作（`--dry-run` 只统计、不写），作用对象是 **Mods 副本本体**。
  工作区 `content/` 是 junction 时（Hard Rules ⑩），「工作区里的那份」与「Mods 副本」是
  **同一个目录**，所以本步与「剥离工作区」是同一件事，不存在「剥了工作区却没剥 Mods」的中间态

### 3. 创建 workspace

**首选：一条命令搞定**（`release/scripts/make_workspace.ps1`）——它依次做
「建 junction → workshop.json → mod_id.txt → 剥离注释 → validate」，且**幂等可重跑**：

```powershell
powershell -File "$env:USERPROFILE\.agents\skills\civ6-modding\release\scripts\make_workspace.ps1" `
    -ModDir "D:\documents\My Games\Sid Meier's Civilization VI\Mods\<ModName>" `
    -ItemId <工坊条目ID> `
    -Src    "D:\documents\Firaxis ModBuddy\Civilization VI\<工程>\<工程>"
```

- `-ItemId` 省略时**不会自作主张**：若工作区已有 `mod_id.txt` 就沿用，否则打 WARN 提醒你
  「这样 upload 会新建条目」——这是最贵的失误（见 §3.1），脚本刻意不猜。
- `-NoStrip` 跳过剥离、`-SkipValidate` 跳过 validate、`-Force` 才允许覆盖已存在的**普通
  目录**形式的 `content`（普通目录默认**拒绝**，防止把 mod 本体当旧副本删掉）。
- 剥离是**就地**改 Mods 副本（Hard Rules ⑩），脚本会显式打印这一点。

**手工等价流程**（脚本不可用时照此做）：

```powershell
$ws      = "$env:TEMP\civ6-ws\<ModName>"    # 固定用 TEMP 工作区根 civ6-ws（勿建在 git 仓库内）
$modDir  = "<Mods 路径>\<ModName>"

New-Item -ItemType Directory -Force -Path $ws | Out-Null
New-Item -ItemType Junction -Path "$ws\content" -Target $modDir    # ★ 不复制，只建链
# workshop.json 见下；mod_id.txt 见 §3.1
```

> **旧式（物理复制）工作区怎么升级**：**直接整个删掉重建**，别手工「删 content 再建链」——
> 手工删一旦敲错路径就是 751 MB 的 Mods 本体。用 `make_workspace.ps1` 时它会**明确拒绝**
> 覆盖普通目录形式的 `content`（除非加 `-Force`），正是为了逼你先确认 

> **不要再用 `new -w` 铺骨架**：它只为「从零建一个新 mod」服务，会铺出 `content/README.md`
> 等你随后必须删掉的东西；它唯一的非模板产物是 `template/workshop.json`（模板占位，§3 下方
> 本来就要覆盖）。更新已有条目更是用不上。`new` 仍需 `Push-Location <tool 目录>` 才能跑
> （相对路径找 `template\`）——这条坑只在真的要新建条目时才相关。

#### 3.1 `mod_id.txt`

- **首建**：**不要**手工创建，`upload` 成功后自动回写条目 ID。
- **更新**：必须已存在且内容为正确 ID（从台账抄；台账是唯一真源）。
  缺失时 `upload` 会**当成新条目另建一个**——这是最贵的失误，上传前务必 `Test-Path "$ws\mod_id.txt"`。

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

#### 3.2 预览图 `image.png`（可选）

workspace 根放 **`image.png`** 即会上传为工坊预览图；**没有就跳过**（不报错、不阻断，
线上保留原有预览图），这与官方上传器行为一致。

**执行端在 `art/`**（生成/缩放归美术管线，上传只负责放到位）：

```powershell
# 母版 → 达标预览图（Lanczos 逐级减半 + unsharp，默认 512）
python "$env:USERPROFILE\.agents\skills\civ6-modding\art\make_workshop_preview.py" `
    "<母版.png>" --out "$ws\image.png" --qa
```

- 完整排版封面（底图 + 徽记 + 中文标题）仍走 `tools/workshop_cover.py --preview`，
  它**内部已委托**同一个 `art/` 执行端，不必也不能自己再缩一次。
- 规格：PNG、**512×512**、**≤ 1 MB**（Steam 硬上限；超限上传可能失败）。
- ★ **已经达标的 512 成品不要再缩**：`make_workshop_preview.py` 对「输入==目标」默认**直通**
  （一个像素都不改），`--force-resize` 才强制重采样 —— 二次缩放只会更糊。
- ★ **别用 `magick -resize …` 裸缩**：ImageMagick 默认滤镜是 **Mitchell（偏软）**，
  这正是本项目 2026-09 封面发糊的根因（实测锐度仅约采定管线的 1/5，见
  `art/make_workshop_preview.py` 的对照表）。
- **本工程约定：封面/预览图一律不署名**（作者只写在 `.modinfo` 的 `Authors` 与代码里）。
- 换图后 `upload` 会重传预览图（日志出现 `k_EItemUpdateStatusUploadingPreviewFile`）；
  只想改文字元数据、不想动图时**别放** `image.png`。

### 4. validate

```powershell
& "$toolDir\Civ6WorkshopUploader.exe" validate -w $ws
```

- exit 0：继续
- exit 1：必须修复（**缺 `workshop.json`** / 参数错 / SteamAPI 初始化失败 / 条目不存在）
- exit 2：提示级问题，**不阻断**，确认后可继续（语义见「Hard Rules」②）

实测（2026-09，故意造错喂进去）：

| 制造的错 | 输出 | exit |
|---|---|---|
| workspace 缺 `workshop.json` | `There is no file named workshop.json in the workspace!` | **1** |
| modinfo 引用的文件不存在 | `File referenced in modinfo does not exist: X.lua` | **2** |
| `Properties/Name`、`Description` 为空 | `Mod Title (Properties/Name) is empty or missing.` | **2** |

> ⚠ **exit 2 不是"可以忽略"**：它把「引用了不存在的文件」和「标题为空」都只算**提示级**，
> 一律打印 `Upload may still proceed (validation is advisory).`。所以
> **`validate` 通过 ≠ 包是好的**——本项目交付前仍必须跑
> `tools/verify_mod_package.py`（引用闭合 + 三处一致性），它才是硬门。
> 该工具对三类**预期差异**自动放行、不产生假红灯：`.lua` 已剥离、`BLPs/**`+`.dep` 是
> cooker 产物、美术引用管线文件（按规范不进 proj 的 `<Content>`、也不进 `.modinfo` 的
> `<Files>`）。想按逐字节严格口径复核时加 `--strict`。

### 4.5 预览图（要换封面时）

**执行端在 `art/`**（缩放/锐化属美术管线；上传只负责把成品放到 `<ws>\image.png`）：

```powershell
# 已有达标 512 成品 → 直通（不重采样，见 §3.2 铁律）
python "$env:USERPROFILE\.agents\skills\civ6-modding\art\make_workshop_preview.py" `
    "<母版>.png" --out "$ws\image.png" --qa

# 或走完整封面排版（内部已委托同一 art/ 执行端）
python "$env:USERPROFILE\.agents\skills\civ6-modding\tools\workshop_cover.py" `
    --bg <底图.png> [--emblem <徽记.png>] --line1 "…" [--line2 "…"] `
    --subtitle "CIVILIZATION VI MOD" `
    --master "<桌面>\<Mod>_Surface.png" --preview "$ws\image.png"
```

- 期望 `PREVIEW … < 1 MB`；512×512。
- **不换封面就别放 `image.png`**（跳过上传、线上保留原图，不报错）。
- **别用 `magick -resize` 裸缩**——默认 Mitchell 滤镜偏软，是封面发糊的经典根因。

### 5. upload

```powershell
& "$toolDir\Civ6WorkshopUploader.exe" upload -w $ws
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

三条守卫（脚本头注释有全文）：① 路径必须严格在 `$env:TEMP\civ6-ws\` 之下；② 工作区**自身**
不能是 reparse point；③ **先逐个摘掉内部链接**（`Remove-Item <link>` 不带 `-Recurse` = 只删链），
再整体递归删除。`content/` 是 junction 时日志会打印
`已摘除链接: … -> <Mods 路径>`，看到这行属**正常**，Mods 副本不受影响。

### 9. 下架（`remove`，不可逆）

```powershell
Push-Location $toolDir
& ".\Civ6WorkshopUploader.exe" remove -w $ws -i <id>
Pop-Location
```

- **不可逆**：线上条目直接消失，订阅者丢失。执行前用台账 + `mod_id.txt` **双向核对 ID**。
- **只删线上条目**，本地 workspace 与 Mods 副本均不受影响（想彻底清干净再跑
  `cleanup.ps1`，且 `mod_id.txt` 也一并作废）。
- 下架后回写台账「操作历史」表，标注下架日期与原因。


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
| 卡 `PreparingContent` 超过 10 分钟 | Trimmed 构建回调问题 | 换非 Trimmed 构建（68 MB + 有 `.pdb`） |
| `Template not found at <cwd>\template!` | `new` 的 cwd 不在 exe 目录 | `Push-Location <tool 目录>` 后再调 |
| 更新后工坊多出一个条目 | workspace 缺 `mod_id.txt`，被当成新条目 | 从台账找回 ID 写回；多余条目用 `remove -i <新ID>` 删掉 |
| `k_EResultFail` / `No Connection` | Steam 内容服务器连接失败 | 检查网络/代理，间隔后重试 |
| `UploadingContent` 后失败 | 大文件传输超时 | 换节点或间隔后重试 |
| `0 of 0 bytes -- success` | 可能只是元数据更新或 chunk 已存在 | 必须验证 `hcontent_file` |
| Steam API result 9 | 条目可能私有/不可匿名查询 | 以作者身份用上传器确认，不要直接判定不存在 |
| `Upload finished ... : OK` 但 API 没变 | 假成功 | 检查日志是否有 `No content change detected` |
| validate/upload 报"未识别命令或参数"（workspace 路径含空格如 `Civilization VI`） | Start-Process -ArgumentList 会把路径按空格拆开 | 直接用 `& $tool validate -w $ws` / `& $tool upload -w $ws`（pwsh 原生引号处理） |
| `There is no 'content' directory inside the workspace!` | 直接把 Mods 目录当工作区传给了 `-w`（上传器只认 `<ws>\content`，不会自己去 Mods 里找） | 用 `make_workspace.ps1` 建工作区；`content` 应为指向 Mods 副本的 junction |
| 上传后线上仍是旧内容，但工作区看着是新的 | `content/` 是**物理复制**且复制后 Mods 又改过（版本漂移） | 改用 junction（Hard Rules ⑩）；已漂移的工作区直接删掉重建 |
| `cleanup.ps1` 报 `拒绝删除：… 不在临时工作区根 …` | 工作区建在了 `$env:TEMP\civ6-ws\` 之外（DSH 会话的 `$env:TEMP` 每会话独立，跨会话路径必然不匹配） | 别删它，重新用 `make_workspace.ps1` 在本会话 TEMP 下建一个 |

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
| `release/scripts/make_workspace.ps1` | **建上传工作区（首选入口）**：content 用 junction 指向 Mods 副本 → workshop.json → mod_id.txt → 剥离注释 → validate，幂等可重跑 |
| `release/scripts/validate.ps1` | 上传前 validate（`-Workspace <ws>`） |
| `release/scripts/upload.ps1` | 上传/更新（`-Workspace <ws> [-TimeoutSeconds 1800]`，日志默认写 `<tool目录>\logs`） |
| `release/scripts/verify.ps1` | 上传后 Steam API 验证（`-ItemId <id>`，比对 `time_updated` / `hcontent_file`） |
| `release/scripts/cleanup.ps1` | 真成功后删临时 workspace（`-Workspace <ws>`；三重守卫：仅在 `$env:TEMP\civ6-ws\` 之下 + 工作区自身非链接 + 先摘内部链接再递归删） |
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
