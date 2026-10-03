#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gamectl.py —— 文明6 对局生命周期控制（全部原语 2026-10-02/03 实机验证）。

子命令：
    wait [--timeout N] [--want ingame|inmenu|any]   轮询 4318 直至满足
    save <档名>                                      表参数存档 + 磁盘核对
    load <档名>                                      对局内 LeaveGame+LoadGame，主菜单直接 LoadGame
                                                     → 确认链推进 → 等待重建（主菜单也可用）
    restart                                          Network.RestartGame → 同上确认链
    exit-menu                                        Events.ExitToMainMenu → 等主菜单
    kill / launch                                    按 PID 逐个 taskkill / Popen 直启可执行文件
    host-game [--leader X] [--civ X]                 主菜单无头建局（可选指定领袖/文明）→ 确认链
    end-turn [--force] [--timeout N]                 结束回合并轮询推进；--force 推过被阻塞的回合

退出码：0 成功；1 失败/超时。
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import winreg
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game_input as GI  # noqa: E402
import tuner_exec as T   # noqa: E402

GAME_BINARIES = Path("Base") / "Binaries" / "Win64Steam" / "CivilizationVI.exe"
GAME_SUBDIR = Path("steamapps") / "common" / "Sid Meier's Civilization VI"
SAVES_TAIL = Path("My Games") / "Sid Meier's Civilization VI" / "Saves" / "Single"
STEAM_ROOTS = (r"F:\Steam", r"C:\Program Files (x86)\Steam", r"D:\Steam")


def steam_library_roots() -> list[str]:
    """从 libraryfolders.vdf 收集全部 Steam 库根；清单缺失即跳过。"""
    roots: list[str] = []
    for steam in STEAM_ROOTS:
        vdf = Path(steam) / "steamapps" / "libraryfolders.vdf"
        if not vdf.is_file():
            continue
        txt = vdf.read_text(encoding="utf-8", errors="replace")
        roots += [m.replace("\\\\", "\\") for m in re.findall(r'"path"\s+"([^"]+)"', txt)]
    return roots


def resolve_exe() -> Path:
    """定位 CivilizationVI.exe：Steam 库清单优先，随后已知安装根与显式覆盖。"""
    env = os.environ.get("RGN_CIV6_EXE")
    cands = [Path(env)] if env else []
    for root in list(steam_library_roots()) + list(STEAM_ROOTS):
        cands.append(Path(root) / GAME_SUBDIR / GAME_BINARIES)
    for cand in cands:
        if cand.is_file():
            return cand
    raise Fail("找不到 CivilizationVI.exe，请用 launch --exe 显式指定安装路径")


def _documents_dir() -> Path | None:
    """注册表记录的「文档」实际位置；读不到返回 None。"""
    try:
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            return Path(winreg.QueryValueEx(key, "Personal")[0])
    except OSError:
        return None


def _home_dir() -> Path | None:
    """用户主目录；环境变量缺失时返回 None（不抛异常）。"""
    for var in ("USERPROFILE", "HOME"):
        val = os.environ.get(var)
        if val:
            return Path(val)
    try:
        return Path.home()
    except (RuntimeError, OSError):
        return None


def resolve_saves_dir() -> Path:
    """定位单人存档目录：注册表「文档」优先，随后本机已知位置。

    候选逐个求值，缺失的候选返回 None 即跳过；环境变量不全时模块照常导入。
    """
    base = _documents_dir()
    home = _home_dir()
    cands = [base, Path(r"D:\documents"), home / "Documents" if home else None]
    for cand in cands:
        if cand and (cand / SAVES_TAIL).is_dir():
            return cand / SAVES_TAIL
    return (base or (home / "Documents" if home else Path(r"D:\documents"))) / SAVES_TAIL


SAVES_DIR = resolve_saves_dir()


class Fail(Exception):
    pass


_HOST, _PORT = T.DEFAULT_HOST, T.DEFAULT_PORT


# ---------------------------------------------------------------------------
# 连接与执行
# ---------------------------------------------------------------------------
class Session:
    """一次连接 + 握手；exec() 复用同一连接。"""

    def __init__(self, host=None, port=None):
        self.host, self.port = host or _HOST, port or _PORT
        self.sock = None
        self.states: dict[str, int] = {}
        self.identity = ""

    def connect(self):
        try:
            self.sock = T.connect(self.host, self.port)
            self.identity, self.states = T.handshake(self.sock)
            return True
        except (OSError, T.LinkClosed):
            self.sock = None
            return False

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def has(self, name: str) -> bool:
        return name in self.states

    def in_game(self) -> bool:
        return "GameCore_Tuner" in self.states and "InGame" in self.states

    def exec(self, state: str, code: str, timeout: float = 20.0):
        """在指定状态执行 Lua，返回输出行列表；LuaError/TimeoutError 上抛。"""
        if not self.sock and not self.connect():
            raise Fail("无法连接 4318")
        key = state
        if state == "gamecore":
            key = "GameCore_Tuner"
        elif state == "ingame":
            key = "InGame"
        if key not in self.states:
            raise Fail(f"状态 {key} 不存在（当前：{sorted(self.states)[:8]}…）")
        return T.execute(self.sock, self.states[key], code, timeout=timeout)

    def try_exec(self, state: str, code: str, timeout: float = 20.0):
        try:
            return 0, self.exec(state, code, timeout)
        except T.LuaError as e:
            return 2, [f"LUA ERROR: {e}"]
        except TimeoutError as e:
            return 3, [f"TIMEOUT: {e}"]
        except T.LinkClosed as e:
            return 4, [f"CLOSED: {e}"]


def esc_to_game():
    hwnd = GI.find_main_window()
    if not hwnd:
        raise Fail("未找到游戏窗口")
    if not GI.send_key(hwnd, GI.VK_ESCAPE):
        raise Fail("ESC 投递失败：目标窗口可能已关闭")


def deliver(s: Session, state: str, code: str, timeout: float) -> list[str]:
    """投递生命周期命令：回包丢失不算失败，返回收到的输出行。

    LoadGame / RestartGame / ExitToMainMenu 会在执行中途拆掉 Lua VM 与连接，
    因此 LinkClosed 与 TimeoutError 只提示，不中断后续的确认链；
    调用方凭返回的输出行判断引擎是否明确拒绝（形如 XXX=false）。
    """
    try:
        lines = s.exec(state, code, timeout=timeout)
    except T.LinkClosed as e:
        print(f"[..] 命令执行中连接被对端关闭（{e}），继续等对局重建")
        return []
    except TimeoutError:
        print("[..] 命令未回哨兵（VM 正在拆解），继续等对局重建")
        return []
    for line in lines:
        print(line)
    return lines


def require_ingame(what: str) -> None:
    """确认当前在对局内，否则立即报明确原因。

    主菜单只有 Main State / MainMenu，InGame 与 GameCore_Tuner 都不存在，
    任何依赖这两个态的命令都无从投递。挡在这里，命令立刻给出可操作的提示，
    不会白等一轮轮询再报成含糊的"等待超时"。
    """
    s = Session()
    if not s.connect():
        raise Fail("无法连接 4318：请先 gamectl.py launch，再 gamectl.py wait")
    try:
        if not s.in_game():
            raise Fail(f"当前不在对局内（{len(s.states)} 个状态）："
                       f"{what}需要先进对局，用 gamectl.py load <档名>")
    finally:
        s.close()


def wait_until(fn, timeout: float, interval: float, what: str) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return
        time.sleep(interval)
    raise Fail(f"等待超时（{timeout:.0f}s）：{what}")


def poll_session(want: str, timeout: float) -> Session:
    """反复重连，直到会话满足 want（ingame/inmenu/any）。

    inmenu 以 MainMenu 态出现为判据：冷启动期会先出现只含 "Main State" 的两三条状态，
    那不是可用的主菜单，投递建局命令会落进半初始化的上下文。
    """
    start = time.monotonic()
    deadline = start + timeout
    last = "尚未开始"
    last_report = 0.0
    while time.monotonic() < deadline:
        s = Session()
        if s.connect():
            if want == "any":
                return s
            if want == "ingame" and s.in_game():
                return s
            # 主菜单就绪以 MainMenu 出现为准：冷启动期先出现只有 "Main State" 的两三条状态，
            # 此时投递建局命令会落进半初始化的上下文。
            if want == "inmenu" and (not s.in_game()) and "MainMenu" in s.states:
                return s
            last = f"已连上但状态不满足 {want}（{len(s.states)} 个状态）"
            s.close()
        else:
            last = "4318 未监听（启动中或切换期）"
            if not GI._find_game_pids() and time.monotonic() - start > 10.0:
                raise Fail("游戏进程不存在：请先 launch 或手工启动游戏")
        if time.monotonic() - last_report > 15.0:
            last_report = time.monotonic()
            print(f"[..] 等待 {want} {time.monotonic() - start:.0f}s：{last}")
        time.sleep(3.0)
    raise Fail(f"等待 {want} 超时（{timeout:.0f}s）：{last}")


def try_direct_loadscreen_close() -> bool:
    """溯源路线：读档/建局后的"点击进入"界面，官方 ESC 处理体是
    LoadScreen 态的 OnActivateButtonClicked()（LoadScreen.lua:42，核心命令
    Events.LoadScreenClose()）。该态在 LSQ 可达时直接调用，绕过按键注入。
    返回是否成功。"""
    s = Session()
    if not s.connect():
        return False
    try:
        for name in s.states:
            if "loadscreen" in name.lower():
                rc, out = s.try_exec(
                    name,
                    'if OnActivateButtonClicked ~= nil then '
                    'OnActivateButtonClicked(); print("LS_CLOSED") '
                    'else print("LS_NOFN") end',
                    timeout=8.0)
                return rc == 0 and any("LS_CLOSED" in l for l in out)
        return False
    finally:
        s.close()


def _advance_past_loadscreen(last_flag: list) -> None:
    """确认链的单步推进：溯源路线优先，失败退回按键兜底。"""
    if try_direct_loadscreen_close():
        last_flag[0] = "direct"
        return
    esc_to_game()
    last_flag[0] = "esc"


def _dismiss_options_menu(s: Session, rounds: int = 3) -> None:
    """确认链收尾：按键推进的 ESC 过冲会把游戏内菜单（InGameTopOptionsMenu）留在屏上，
    遮挡后续画面观察并吞掉下一次投键。按状态表判定，重复投递 ESC 直到菜单关闭；
    连不上或退出对局即停，交回上层处理。"""
    for _ in range(rounds):
        if "InGameTopOptionsMenu" not in s.states:
            return
        try:
            esc_to_game()
        except Fail:
            return
        time.sleep(1.5)
        if not s.connect() or not s.in_game():
            return


def enter_confirm_chain(timeout: float = 180.0):
    """重载/建局后的确认链：等重载开始 → 溯源路线优先/ESC 兜底 → 等 GameCore_Tuner。

    推进条件取两条：状态表清空（Lua VM 已拆）或出现 LoadScreen 态（"点击进入"界面就绪）。
    只看清空会在重载过快时错过窗口，导致确认链空转到超时。
    轮询期间按 20 秒节拍报告进展；游戏进程消失时立即中止，不再等满超时。
    """
    start = time.monotonic()
    deadline = start + timeout
    reset_seen = False
    last_advance = 0.0
    last_flag = ["-"]
    last_report = 0.0
    while time.monotonic() < deadline:
        s = Session()
        if s.connect():
            if s.in_game():
                # 刚推进过的话补一发，关掉可能被按键打开的暂停菜单（溯源路线无此副作用）
                if last_flag[0] == "esc" and time.monotonic() - last_advance < 4.0:
                    try:
                        esc_to_game()
                    except Fail:
                        pass
                _dismiss_options_menu(s)
                return s
            if not s.states or any("loadscreen" in n.lower() for n in s.states):
                reset_seen = True
            if reset_seen and time.monotonic() - last_advance > 6.0:
                try:
                    _advance_past_loadscreen(last_flag)
                    last_advance = time.monotonic()
                except Fail:
                    pass
            s.close()
        else:
            # 4318 关闭本身就是重载期的常态：读档界面停在"点击进入"时端口是关的，
            # 此时只能靠按键推进。端口不可达期间同样按节拍投递 ESC，否则确认链会
            # 在游戏静候输入的状态下空转到超时。
            reset_seen = True
            if not GI._find_game_pids():
                raise Fail("游戏进程已退出：确认链中止")
            if time.monotonic() - last_advance > 6.0:
                try:
                    esc_to_game()
                    last_flag[0] = "esc"
                    last_advance = time.monotonic()
                except Fail:
                    pass
        if time.monotonic() - last_report > 20.0:
            last_report = time.monotonic()
            print(f"[..] 确认链 {time.monotonic() - start:.0f}s（最近推进：{last_flag[0]}）")
        time.sleep(3.0)
    raise Fail("确认链超时：对局未进入")


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------
def require_ingame(cmd: str) -> Session:
    """要求当前在对局内；否则立即报明确原因，不进入轮询。

    主菜单没有 InGame 态，store / restart / exit-menu 都无从投递：
    此时若直接 poll_session("ingame", 60)，会在主菜单白等一整轮，
    最终报成含糊的"等待 ingame 超时"，掩盖真实原因。
    """
    s = Session()
    if not s.connect():
        raise Fail("无法连接 4318：请先 gamectl.py launch 并 wait")
    if not s.in_game():
        s.close()
        raise Fail(f"当前不在对局内（{len(s.states)} 个状态）：{cmd} 需要先 "
                   f"gamectl.py load <档名> 进入对局")
    return s


def cmd_wait(a):
    s = poll_session(a.want, a.timeout)
    print(f"[OK] {a.want} 就绪：{len(s.states)} 个状态，GameCore_Tuner={s.has('GameCore_Tuner')}")
    s.close()
    return 0


def cmd_save(a):
    """存档：要求当前在对局内。

    主菜单没有 InGame 态，存档命令无从投递：此时立即报明确原因，
    不进入 60 秒轮询（否则会在主菜单白等一轮，报成含糊的"等待超时"）。
    """
    require_ingame("存档")
    s = poll_session("ingame", 60)
    try:
        code = ('local gf={Name="%s",Location=SaveLocations.LOCAL_STORAGE,'
                'Type=SaveTypes.SINGLE_PLAYER,FileType=SaveFileTypes.GAME_STATE};'
                'local rc=Network.SaveGame(gf); print("SAVE_RC="..tostring(rc))') % a.name
        lines = s.exec("ingame", code, timeout=60.0)
        print("\n".join(lines))
        if "true" not in "".join(lines):
            raise Fail("SaveGame 未返回 true")
        target = SAVES_DIR / f"{a.name}.Civ6Save"
        wait_until(lambda: target.exists(), 20, 1.0, f"{target} 出现")
        print(f"[OK] 存档落盘：{target}")
    finally:
        s.close()
    return 0


def cmd_load(a):
    """读档：对局中先 LeaveGame，主菜单直接 LoadGame。

    Network.LoadGame 在主菜单同样可用，因此读档入口不要求当前已在对局中，
    冷启动后也能一条命令进入对局。
    """
    s = Session()
    if not s.connect():
        raise Fail("无法连接 4318")
    try:
        if s.in_game():
            state, leave = "ingame", "Network.LeaveGame();"
        elif "MainMenu" in s.states:
            state, leave = "MainMenu", ""
        else:
            state, leave = "Main State", ""
        code = (leave +
                'local gf={Name="%s",Location=SaveLocations.LOCAL_STORAGE,'
                'Type=SaveTypes.SINGLE_PLAYER,FileType=SaveFileTypes.GAME_STATE};'
                'local rc=Network.LoadGame(gf, ServerType.SERVER_TYPE_NONE);'
                'print("LOAD_RC="..tostring(rc))') % a.name
        out = deliver(s, state, code, 60.0)
        if any("LOAD_RC=false" in ln for ln in out):
            raise Fail(f"LoadGame 被拒（存档名不存在或存档已损坏）：{a.name}")
    finally:
        s.close()
    s2 = enter_confirm_chain(a.timeout)
    print(f"[OK] 读档完成：{len(s2.states)} 个状态，GameCore_Tuner 就绪")
    s2.close()
    return 0


def cmd_restart(a):
    require_ingame("重开")
    s = poll_session("ingame", 60)
    try:
        out = deliver(s, "ingame", 'local rc=Network.RestartGame(); print("RESTART_RC="..tostring(rc))', 60.0)
        if any("RESTART_RC=false" in ln for ln in out):
            raise Fail("RestartGame 被拒")
    finally:
        s.close()
    s2 = enter_confirm_chain(a.timeout)
    print(f"[OK] 重开完成：GameCore_Tuner 就绪")
    s2.close()
    return 0


def cmd_exitmenu(a):
    require_ingame("退主菜单")
    s = poll_session("ingame", 60)
    try:
        deliver(s, "ingame", "Events.ExitToMainMenu(); print('EXIT_SENT')", 30.0)
    finally:
        s.close()
    poll_session("inmenu", a.timeout)
    print("[OK] 已回主菜单")
    return 0


def cmd_endturn(a):
    """结束回合并轮询回合推进。

    默认投递 UI 的 END_TURN 操作；--force 改发 REASON="UserForced"（Shift+Enter 等价，
    可推过被阻塞的回合）。推进与否以 gamecore 的 GetCurrentGameTurn 为准，
    轮询期间连接短暂不可达（AI 回合处理）按常态跳过。
    """
    s = require_ingame("结束回合")
    turn_code = "print(Game.GetCurrentGameTurn())"
    try:
        rc, out = s.try_exec("gamecore", turn_code, timeout=10.0)
        if rc:
            raise Fail(f"读取当前回合失败：{out}")
        before = int(out[-1])
        if a.force:
            code = ("UI.RequestAction(ActionTypes.ACTION_ENDTURN, {REASON='UserForced'}); "
                    "print('END_FORCED')")
        else:
            code = ("UI.RequestPlayerOperation(Game.GetLocalPlayer(), PlayerOperations.END_TURN, {}); "
                    "print('END_SENT')")
        s.exec("ingame", code, timeout=15.0)
        deadline = time.monotonic() + a.timeout
        while time.monotonic() < deadline:
            time.sleep(a.interval)
            r2 = Session()
            if r2.connect() and r2.in_game():
                rc2, out2 = r2.try_exec("gamecore", turn_code, timeout=10.0)
                r2.close()
                if rc2 == 0 and out2:
                    try:
                        now = int(out2[-1])
                    except ValueError:
                        continue
                    if now != before:
                        print(f"[OK] 回合推进：{before} -> {now}")
                        return 0
        raise Fail(f"回合未推进（仍为 {before}）：可能存在阻塞项（试 --force）或 AI 回合处理中")
    finally:
        s.close()
    return 0


def cmd_kill(a):
    """结束游戏进程：按实际 PID 终止，覆盖 DX12 可执行文件与启动器子进程。"""
    pids = sorted(GI._find_game_pids())
    if not pids:
        print("[OK] 游戏进程不存在")
        return 0
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    wait_until(lambda: not GI._find_game_pids(), 30, 1.0, "游戏进程退出")
    print(f"[OK] 已结束游戏进程：{pids}")
    return 0


def cmd_close(a):
    """收尾流程：可选存档 → taskkill → 确认进程消失。"""
    if a.save:
        cmd_save(argparse.Namespace(name=a.save))
    cmd_kill(argparse.Namespace())
    print("[OK] 游戏已退出（收尾完成）")
    return 0


def cmd_launch(a):
    """直接拉起游戏进程。

    不经 PowerShell，路径里的空格与撇号原样传入，不存在引号被剥离后
    参数被拆成位置参数的问题。已在运行时直接拒绝：单实例游戏会静默退出，
    旧写法会把"本来就在跑的那个进程"当成启动成功。
    """
    exe = Path(a.exe) if a.exe else resolve_exe()
    if not exe.is_file():
        raise Fail(f"找不到可执行文件：{exe}")
    before = GI._find_game_pids()
    if before:
        raise Fail(f"游戏已在运行（pid={sorted(before)}），无需重复拉起")
    proc = subprocess.Popen(
        [str(exe)], cwd=str(exe.parent), close_fds=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    wait_until(lambda: bool(GI._find_game_pids()), 20, 1.0, "游戏进程出现")
    print(f"[OK] 已启动 {exe}（pid={proc.pid}），随后用 wait 等待 4318")
    return 0


def cmd_host_game(a):
    want_menu = poll_session("inmenu", 120)
    menu_key = "MainMenu"
    want_menu.close()
    s = Session()
    if not s.connect():
        raise Fail("连接失败")
    try:
        lid = a.leader or ""
        cid = a.civ or ""
        set_leader = ""
        if lid:
            set_leader = 'pcall(function() PlayerConfigurations[0]:SetLeaderTypeName("%s") end);' % lid
        if cid:
            set_leader += 'pcall(function() PlayerConfigurations[0]:SetCivilizationTypeName("%s") end);' % cid
        steps = [
            ('GameConfiguration.SetToDefaults()', "defaults"),
            ('GameConfiguration.SetValue("RULESET", nil)', "ruleset_nil"),
            ('BuildHeadlessGameSetup()', "headless"),
            ('RebuildPlayerParameters(true)', "rebuild"),
            ('GameSetup_RefreshParameters()', "refresh"),
            ('ReleasePlayerParameters()', "release"),
            ('HideGameSetup()', "hide"),
        ]
        for code, name in steps:
            rc, out = s.try_exec(menu_key, code, timeout=90.0)
            if rc:
                raise Fail(f"{name} 失败：{out}")
            print(f"[..] {name}: ok")
        if set_leader:
            rc, out = s.try_exec(menu_key, set_leader +
                                 'print("LEADER="..tostring(PlayerConfigurations[0]:GetLeaderTypeName()))', timeout=60.0)
            if rc:
                raise Fail(f"领袖设定失败：{out}")
            print(f"[..] leader: {out}")
        rc, out = s.try_exec(menu_key, 'Network.HostGame(ServerType.SERVER_TYPE_NONE); print("HOST_SENT")', timeout=60.0)
        if rc:
            raise Fail(f"HostGame 失败：{out}")
        print(f"[..] host: {out}")
    finally:
        s.close()
    s2 = enter_confirm_chain(a.timeout)
    print(f"[OK] 对局已进入（{len(s2.states)} 个状态）")
    s2.close()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="文明6 对局生命周期控制")
    ap.add_argument("--host", default=T.DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=T.DEFAULT_PORT)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("wait"); p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--want", choices=["ingame", "inmenu", "any"], default="ingame")
    p.set_defaults(fn=cmd_wait)

    p = sub.add_parser("save"); p.add_argument("name"); p.set_defaults(fn=cmd_save)
    p = sub.add_parser("load"); p.add_argument("name")
    p.add_argument("--timeout", type=float, default=240.0); p.set_defaults(fn=cmd_load)
    p = sub.add_parser("restart"); p.add_argument("--timeout", type=float, default=240.0)
    p.set_defaults(fn=cmd_restart)
    p = sub.add_parser("exit-menu"); p.add_argument("--timeout", type=float, default=90.0)
    p.set_defaults(fn=cmd_exitmenu)
    p = sub.add_parser("end-turn")
    p.add_argument("--force", action="store_true", help="改发 REASON=UserForced，推过被阻塞的回合")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--interval", type=float, default=5.0)
    p.set_defaults(fn=cmd_endturn)
    sub.add_parser("kill").set_defaults(fn=cmd_kill)
    p = sub.add_parser("close")
    p.add_argument("--save", default="", help="退出前先存的档名（留空跳过存档）")
    p.set_defaults(fn=cmd_close)
    p = sub.add_parser("launch")
    p.add_argument("--exe", default=None, help="可执行文件路径；缺省时自动解析安装位置")
    p.set_defaults(fn=cmd_launch)
    p = sub.add_parser("host-game")
    p.add_argument("--leader", default="")
    p.add_argument("--civ", default="")
    p.add_argument("--timeout", type=float, default=300.0)
    p.set_defaults(fn=cmd_host_game)

    args = ap.parse_args()
    if args.cmd is None:
        ap.print_help()
        return 1
    global _HOST, _PORT
    _HOST, _PORT = args.host, args.port
    try:
        return args.fn(args)
    except Fail as e:
        print(f"[FAIL] {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
