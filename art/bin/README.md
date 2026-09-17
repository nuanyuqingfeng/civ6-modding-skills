# art/bin/ —— 随包内置的外部可执行文件

## texconv.exe

| 项 | 值 |
|---|---|
| 来源 | [Microsoft DirectXTex](https://github.com/microsoft/DirectXTex) 的 `texconv` CLI（release 构建） |
| 版本 | **2026.5.8.1** |
| 许可 | **MIT**（Microsoft）——允许随本仓库再分发 |
| 用途 | PNG → DDS 转换（`art/convert_art.ps1`、`art/make_atlas.py`、`civ6-asset-forge/scripts/process_leader_png.py`） |

**为什么内置**：全新环境不该为了"把一张 PNG 转成 DDS"先去装 winget 包 —— 随包一份可让
clone 后立即跑通整条美术管线。

**探测顺序**（单一真源：`art/_texconv.py`；`convert_art.ps1` 的 `Find-Texconv` 保持等价实现）：

1. 环境变量 `TEXCONV`（显式覆盖）
2. **本目录的 `texconv.exe`**（内置副本）
3. `PATH` 上的 `texconv`
4. `%LOCALAPPDATA%\Microsoft\WinGet\Links\texconv.exe`
5. （仅 `recursive=True`）`%LOCALAPPDATA%\Microsoft\WinGet\Packages` 下递归

想用自己更新的版本：设 `TEXCONV=<你的 texconv.exe>`，或把 `art/bin/texconv.exe` 换成新版
（`winget install Microsoft.DirectXTex.Texconv` 后从 WinGet Links 复制过来即可）。

> 本目录只放**必需且许可允许再分发**的可执行文件；其余外部工具（ffmpeg / WwiseCLI /
> AssetEditor / ModBuddy）仍按 `civ6-modding/tools/_paths.py` 的路径键解析，不随包分发。
