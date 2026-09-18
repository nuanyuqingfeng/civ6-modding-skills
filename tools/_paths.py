# -*- coding: utf-8 -*-
"""本机 Civ6 关键路径解析（P1–P6），全 civ6-modding/tools 共用。

解析顺序（与 SKILL.md「环境路径总表」一致）：
  1) `civ6-modding/local_paths.json`（个人环境文件，分享时不携带）
  2) 注册表 HKCU\\SOFTWARE\\Firaxis\\Civilization6_ModBuddy\\... → UserPath / AssetsPath / ToolsPath
  3) 硬编码默认值
  4) Steam libraryfolders.vdf 推断（游戏本体）

只读操作，不修改任何路径。
"""
from __future__ import annotations

import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PATHS = os.path.join(SKILL_DIR, "local_paths.json")

DEFAULTS = {
    "modbuddy": r"D:\documents\Firaxis ModBuddy\Civilization VI",
    "mods": r"D:\documents\My Games\Sid Meier's Civilization VI\Mods",
    "game": r"F:\Steam\steamapps\common\Sid Meier's Civilization VI",
    "sdk_assets": r"F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets",
    "sdk": r"F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK",
    "workshop_ref": r"F:\Steam\steamapps\workshop\content\289070",
}

# 外部可执行/工具路径（同样可被 local_paths.json 覆盖）—— 全 skill 的"路径收纳"单一真源
TOOL_DEFAULTS = {
    "uploader": r"D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe",
    "sd_cpp": os.path.expandvars(r"%USERPROFILE%\sd-cpp"),
    "imagemagick": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
    "luac": r"E:\SoftWares\Lua\5.1\luac.exe",
    "ws_root": os.path.join(os.environ.get("TEMP", r"C:\Windows\Temp"), "civ6-ws"),
    "steam_logs": r"F:\Steam\logs",
}


REG_KEY = (r"SOFTWARE\Firaxis\Civilization6_ModBuddy\2013\DialogPage"
           r"\Firaxis.VisualStudio.Projects.Civ6.OptionsPages.OptionsDialogPage")

_overrides: dict | None = None


def _load_overrides() -> dict:
    global _overrides
    if _overrides is None:
        _overrides = {}
        if os.path.isfile(LOCAL_PATHS):
            try:
                with open(LOCAL_PATHS, encoding="utf-8") as f:
                    _overrides = json.load(f)
            except Exception as e:  # 坏文件不阻断，回落到默认
                print("WARN 读取 %s 失败：%s" % (LOCAL_PATHS, e), file=sys.stderr)
    return _overrides


def _registry_paths() -> dict:
    """注册表三值：UserPath / AssetsPath / ToolsPath（ToolsPath 去尾部 ' SDK'）。"""
    out = {}
    try:
        import winreg  # type: ignore
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY) as k:
            for name, slot in (("UserPath", "mods"), ("AssetsPath", "sdk_assets"), ("ToolsPath", "sdk")):
                try:
                    v, _ = winreg.QueryValueEx(k, name)
                    if v:
                        out[slot] = v
                except OSError:
                    pass
    except Exception:
        return {}
    if "mods" in out:
        out["mods"] = os.path.join(out["mods"], "Mods")
    return out


def _steam_game_root() -> str | None:
    """从 Steam libraryfolders.vdf 找 appid 289070 的安装目录。"""
    libs = []
    for steam in (r"F:\Steam", r"C:\Program Files (x86)\Steam", r"D:\Steam"):
        vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
        if not os.path.isfile(vdf):
            continue
        try:
            txt = open(vdf, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        libs += re.findall(r'"path"\s+"([^"]+)"', txt)
    for lib in libs:
        cand = os.path.join(lib.replace("\\\\", "\\"), "steamapps", "common", "Sid Meier's Civilization VI")
        if os.path.isdir(cand):
            return cand
    return None


def get(key: str, must_exist: bool = True) -> str | None:
    """取路径。key ∈ modbuddy/mods/game/sdk_assets/sdk/workshop_ref。"""
    if key not in DEFAULTS:
        raise KeyError("未知路径键：%s（可选：%s）" % (key, ", ".join(DEFAULTS)))
    cand = _load_overrides().get(key)
    if not cand:
        cand = _registry_paths().get(key)
    if not cand and key == "game":
        cand = _steam_game_root()
    if not cand:
        cand = DEFAULTS[key]
    if key in ("sdk", "sdk_assets") and cand and not os.path.isdir(cand) and "game" not in cand:
        pass
    if must_exist and not os.path.exists(cand):
        return None
    return cand


def require(key: str) -> str:
    p = get(key)
    if not p:
        raise SystemExit(
            "找不到路径 %s。请把本机实际路径写入 %s（形如 {\"%s\": \"...\"}）。" % (key, LOCAL_PATHS, key))
    return p


def summary() -> str:
    rows = []
    for k in DEFAULTS:
        p = get(k)
        rows.append("  %-14s %s  %s" % (k, "[OK]  " if p else "[缺失]", p or DEFAULTS[k]))
    return "\n".join(rows)


def tool(key: str, must_exist: bool = True) -> str | None:
    """取外部工具路径。key ∈ uploader/sd_cpp/imagemagick/luac/ws_root/steam_logs。"""
    if key not in TOOL_DEFAULTS:
        raise KeyError("未知工具键：%s（可选：%s）" % (key, ", ".join(TOOL_DEFAULTS)))
    cand = _load_overrides().get(key) or TOOL_DEFAULTS[key]
    if must_exist and not os.path.exists(cand):
        return None
    return cand


def require_tool(key: str) -> str:
    p = tool(key)
    if not p:
        raise SystemExit("找不到工具 %s。请把实际路径写入 %s（形如 {\"%s\": \"...\"}）。"
                         % (key, LOCAL_PATHS, key))
    return p


def tools_summary() -> str:
    rows = []
    for k in TOOL_DEFAULTS:
        p = tool(k)
        rows.append("  %-14s %s  %s" % (k, "[OK]  " if p else "[缺失]", p or TOOL_DEFAULTS[k]))
    return "\n".join(rows)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # `--tool <键>` / `--path <键>`：把解析结果**单独打印**给 shell 包装脚本用
    # （PowerShell 侧无法 import Python 模块，此前只能各自写死路径 —— 实测
    #  ensure_uploader.ps1 因此把已装好的机器判成"缺工具"）。
    # 退出码：0 找到（打印路径）/ 1 未找到或键名非法。
    argv = sys.argv[1:]
    if argv and argv[0] in ("-t", "--tool", "-p", "--path"):
        want_tool = argv[0] in ("-t", "--tool")
        if len(argv) < 2:
            print("用法：python _paths.py (--tool|--path) <键名>", file=sys.stderr)
            raise SystemExit(2)
        key = argv[1]
        try:
            val = tool(key) if want_tool else get(key)
        except KeyError as e:
            print(str(e), file=sys.stderr)
            raise SystemExit(2)
        if val:
            print(val)
            raise SystemExit(0)
        print("MISSING %s" % key, file=sys.stderr)
        raise SystemExit(1)

    print("本机 Civ6 路径：")
    print(summary())
    print("\n外部工具路径：")
    print(tools_summary())
