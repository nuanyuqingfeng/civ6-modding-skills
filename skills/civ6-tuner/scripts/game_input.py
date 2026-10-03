#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向文明6游戏窗口投递按键，不抢焦点、不影响其它窗口。

用途：读档/重开后停在"点击进入"确认界面时，向游戏窗口单独投递 ESC
（PostMessage 到 CivilizationVI.exe 的顶层窗口，非全局 keybd_event——
全局键击会命中当前焦点窗口，误伤调用方终端）。

用法：
    python game_input.py esc            # 向游戏窗口投递一次 ESC
    python game_input.py key 0x1B       # 同上，任意虚拟键码
    python game_input.py esc --repeat 3 --gap 1.5   # 连发 N 次，间隔秒

退出码：0 已投递；1 未找到游戏窗口/进程。
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import sys
import time

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_ESCAPE = 0x1B
PROCESS_NAME_SUFFIX = "civilizationvi.exe"


def _find_game_pids() -> set[int]:
    """用进程快照找出所有 CivilizationVI.exe 的 PID（纯 ctypes）。"""
    TH32CS_SNAPPROCESS = 0x2
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                    ("th32ProcessID", wt.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                    ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                    ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wt.DWORD), ("szExeFile", wt.WCHAR * 260)]
    k32 = ctypes.windll.kernel32
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pids: set[int] = set()
    if snap == -1:
        return pids
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    ok = k32.Process32FirstW(snap, ctypes.byref(entry))
    while ok:
        name = entry.szExeFile.lower()
        if name == PROCESS_NAME_SUFFIX or name == "civilizationvi_dx12.exe":
            pids.add(entry.th32ProcessID)
        ok = k32.Process32NextW(snap, ctypes.byref(entry))
    k32.CloseHandle(snap)
    return pids


def find_game_windows() -> list[int]:
    """枚举顶层窗口，返回属于游戏进程的可见窗口句柄。"""
    pids = _find_game_pids()
    if not pids:
        return []
    user32 = ctypes.windll.user32
    hwnds: list[int] = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def on_window(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wt.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            hwnds.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(on_window), 0)
    return hwnds


def window_area(hwnd: int) -> int:
    """窗口面积，用来挑选游戏主窗口。"""
    user32 = ctypes.windll.user32
    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return max(0, rect.right - rect.left) * max(0, rect.bottom - rect.top)


def find_main_window() -> int | None:
    """面积最大的游戏窗口句柄；没有可见窗口时返回 None。"""
    hwnds = find_game_windows()
    if not hwnds:
        return None
    return max(hwnds, key=window_area)


def send_key(hwnd: int, vk: int) -> bool:
    """向指定窗口投递一次按键（按下+抬起），不改变焦点。返回是否投递成功。"""
    user32 = ctypes.windll.user32
    down = bool(user32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0))
    time.sleep(0.05)
    up = bool(user32.PostMessageW(hwnd, WM_KEYUP, vk, 0))
    return down and up


def main() -> int:
    ap = argparse.ArgumentParser(description="向文明6窗口投递按键（不抢焦点）")
    ap.add_argument("action", choices=["esc", "key"], help="esc=发送 ESC；key=发送指定虚拟键码")
    ap.add_argument("vk", nargs="?", default=None, help="key 模式的虚拟键码，如 0x1B / 13")
    ap.add_argument("--repeat", type=int, default=1, help="投递次数，默认 1")
    ap.add_argument("--gap", type=float, default=1.0, help="两次投递间隔秒，默认 1.0")
    args = ap.parse_args()

    vk = VK_ESCAPE if args.action == "esc" else int(args.vk, 0)
    target = find_main_window()
    if target is None:
        print("[FAIL] 未找到 CivilizationVI.exe 的可见窗口（游戏未启动或最小化到独占状态）")
        return 1
    for i in range(args.repeat):
        if not send_key(target, vk):
            print(f"[FAIL] 投递失败：hwnd=0x{target:X} 可能已关闭")
            return 1
        print(f"[OK] 已投递 {'ESC' if args.action == 'esc' else hex(vk)} -> hwnd=0x{target:X}"
              + (f" ({i + 1}/{args.repeat})" if args.repeat > 1 else ""))
        if i + 1 < args.repeat:
            time.sleep(args.gap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
