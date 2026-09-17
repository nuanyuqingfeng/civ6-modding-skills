#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""_texconv.py — texconv（外部 DDS 转换器）定位的单一真源

## 为什么需要它

`texconv` 是 Microsoft DirectXTex 的 CLI，本 skill 家族用它做 PNG→DDS。
此前有 **3 份各自实现**的定位逻辑（`convert_art.ps1` 是 PowerShell，另有
`make_atlas.py` 与 `civ6-asset-forge/scripts/process_leader_png.py` 两份 Python），
探测深度还不一致 —— 改一处容易漏另两处。

本模块把 **Python 侧**的两份合并为一份，并把"搜索深度"做成**显式参数**：

| 调用方 | 策略 | 理由 |
|---|---|---|
| `art/make_atlas.py`（管线内部） | `recursive=True` | 无人值守批处理，宁可多找一层也要跑通 |
| `asset-forge/scripts/process_leader_png.py`（面向用户） | `recursive=False` | 遵循 `reference/leader-2d.md`「仅简单查找，**不自动安装、不扩大搜索**」 |

> `convert_art.ps1` 是 PowerShell，**无法复用本模块**；它的 `Find-Texconv`
> 保持等价实现（同样顺序：PATH → WinGet Links → WinGet Packages 递归）。
> 改探测顺序时**三处都要看**（本文件 + `convert_art.ps1`）。

## 探测顺序（与 convert_art.ps1 一致）

1. 环境变量 `TEXCONV`（显式覆盖，最高优先级）
2. **本 skill 随包内置**：`art/bin/texconv.exe`（Microsoft DirectXTex 官方 release 版，MIT；
   随仓库分发 → clone 后开箱可用）
3. `PATH` 上的 `texconv`
4. `%LOCALAPPDATA%\Microsoft\WinGet\Links\texconv.exe`（winget 安装后的固定链接位；
   winget 装完当前会话 PATH 不刷新，故需补探测）
5. （仅 `recursive=True`）`%LOCALAPPDATA%\Microsoft\WinGet\Packages` 下递归找

**不自动安装**：找不到就返回 `None`，由调用方决定报错还是跳过（本 skill 不代跑 winget）。

## 用法

    from _texconv import find_texconv, describe_missing

    tc = find_texconv(recursive=True)      # 管线内部
    tc = find_texconv(recursive=False)     # 面向用户、守"不扩大搜索"策略
    if not tc:
        raise SystemExit(describe_missing())

    python _texconv.py                     # 自检：打印实际解析结果
"""
import os
import sys
from pathlib import Path
from shutil import which

__all__ = ["find_texconv", "describe_missing", "WINGET_LINKS", "WINGET_PACKAGES", "BUNDLED"]

BUNDLED = Path(__file__).resolve().parent / "bin" / "texconv.exe"   # 随包内置（DirectXTex, MIT）
WINGET_LINKS = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/texconv.exe"
WINGET_PACKAGES = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages"


def find_texconv(recursive=True):
    """定位 texconv。找到返回完整路径（或 `"texconv"` 若在 PATH），否则 `None`。

    顺序：`TEXCONV` 环境变量 → 随包内置 `art/bin/texconv.exe` → PATH → WinGet Links
          →（recursive）WinGet Packages 递归。

    Args:
        recursive: True 时额外递归扫 `WinGet/Packages`（管线内部用）；
                   False 只查内置副本 / PATH / WinGet Links 固定位（面向用户用）。
    """
    env = os.environ.get("TEXCONV")
    if env and Path(env).is_file():
        return env
    try:
        if BUNDLED.is_file():
            return str(BUNDLED)
    except OSError:
        pass
    found = which("texconv")
    if found:
        return found
    try:
        if WINGET_LINKS.is_file():
            return str(WINGET_LINKS)
    except OSError:
        pass
    if recursive:
        try:
            if WINGET_PACKAGES.is_dir():
                for p in WINGET_PACKAGES.rglob("texconv.exe"):
                    return str(p)
        except OSError:
            pass
    return None


def describe_missing(recursive=True):
    """找不到时的统一提示文案（含手动安装命令）。"""
    scope = ("TEXCONV → 内置 art/bin/texconv.exe → PATH → WinGet Links → WinGet Packages(递归)"
             if recursive else "TEXCONV → 内置 art/bin/texconv.exe → PATH → WinGet Links")
    return (
        "找不到 texconv（已查：%s）。\n"
        "本 skill 不自动安装。请任选一种：\n"
        "  1) winget install Microsoft.DirectXTex.Texconv  然后**开新终端**重跑\n"
        "  2) 手动下载后在 PATH 上暴露 texconv.exe\n"
        "  3) 若你的环境禁止执行外部 exe，改用纯 Python 的 "
        "civ6-modding/art/dds_io.py 直接写 DDS（仅支持未压缩 RGBA8 单 mip）"
        % scope
    )


def _selftest():
    print("LOCALAPPDATA      :", os.environ.get("LOCALAPPDATA", "(unset)"))
    print("WINGET_LINKS      :", WINGET_LINKS, "->", WINGET_LINKS.is_file())
    try:
        print("WINGET_PACKAGES   :", WINGET_PACKAGES, "->", WINGET_PACKAGES.is_dir())
    except OSError:
        print("WINGET_PACKAGES   : (不可访问)")
    print("which('texconv')  :", which("texconv"))
    for rec in (True, False):
        p = find_texconv(recursive=rec)
        print("find_texconv(recursive=%-5s) -> %s" % (rec, p))
    if not find_texconv(recursive=True):
        print()
        print(describe_missing())
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
