#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""civ6-tuner：通过 FireTuner 调试接口在运行中的文明6对局内执行 Lua。

协议来源：逆向成果借鉴 github.com/lmwilki/civ6-mcp（MIT License）。
    线格式：[4字节LE uint32 长度][4字节LE int32 tag][null 结尾 payload]
    握手：  tag=4 发 "APP:" -> 游戏身份；"LSQ:" -> Lua 状态列表
    执行：  tag=3 发 "CMD:{状态索引}:{Lua代码}"
    回包：  "O\\x00<上下文>: <值>" = print() 输出；"ERR:" 开头 = Lua 错误
    哨兵：  print("---END---") 标记输出收集完成

前置条件：
    1. 游戏内 Options 勾选 Tuner（或 AppOptions.txt EnableTuner 1）
    2. 必须关闭 FireTuner GUI（游戏只允许一个 tuner 连接）
    3. 必须处于进行中的对局（主菜单没有 GameCore_Tuner/InGame 状态）

状态选择（exec）：
    --context gamecore|ingame  两个引擎沙箱态（mod 全局函数在这两态里为 nil）
    --state <名字|索引>        直接指定状态，用来投递到 **mod 自有的 UI 上下文**
                              （LSQ 列表里带 Context 名的条目，如 AllUnitsFoundCity）——
                              那里 mod 的全局函数是可调的，`Controls` 也是 mod 的控件表

退出码：0 成功；1 连接失败；2 Lua 执行错误；3 超时无响应
"""

from __future__ import annotations

import argparse
import os
import socket
import struct
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# 协议常量
# ---------------------------------------------------------------------------
HEADER_FMT = "<Ii"          # [长度][tag]，均为小端 4 字节
TAG_HANDSHAKE = 4
TAG_COMMAND = 3
SENTINEL = "---END---"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4318

# 日志目录（持久保留上次游玩记录，直到下次启动覆盖）
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / \
    "Firaxis Games" / "Sid Meier's Civilization VI" / "Logs"


class LuaError(Exception):
    """游戏返回 ERR: 时抛出。"""


# ---------------------------------------------------------------------------
# 帧收发
# ---------------------------------------------------------------------------
def send_msg(sock: socket.socket, tag: int, payload: str) -> None:
    data = payload.encode("utf-8") + b"\x00"
    sock.sendall(struct.pack(HEADER_FMT, len(data), tag) + data)


def recv_msg(sock: socket.socket) -> tuple[int, str] | None:
    """读一帧。超时/断开返回 None。"""
    try:
        header = _recv_exact(sock, struct.calcsize(HEADER_FMT))
        if header is None:
            return None
        length, tag = struct.unpack(HEADER_FMT, header)
        data = _recv_exact(sock, length)
        if data is None:
            return None
        return tag, data.rstrip(b"\x00").decode("utf-8", errors="replace")
    except OSError:
        return None


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def drain(sock: socket.socket, timeout: float = 0.3) -> list[tuple[int, str]]:
    """清空当前可读的杂散消息（游戏可能主动推送）。"""
    out = []
    sock.settimeout(timeout)
    while True:
        msg = recv_msg(sock)
        if msg is None:
            break
        out.append(msg)
    return out


# ---------------------------------------------------------------------------
# 握手与状态发现
# ---------------------------------------------------------------------------
def handshake(sock: socket.socket) -> tuple[str, dict[str, int]]:
    """握手并解析 Lua 状态表。返回 (游戏身份, {状态名: 索引})。"""
    drain(sock, 0.3)

    send_msg(sock, TAG_HANDSHAKE, "APP:")
    sock.settimeout(5.0)
    app_msg = recv_msg(sock)
    identity = app_msg[1] if app_msg else "<无响应>"

    send_msg(sock, TAG_HANDSHAKE, "LSQ:")
    lsq_msg = recv_msg(sock)
    states: dict[str, int] = {}
    if lsq_msg:
        raw = lsq_msg[1]
        entries = [s.strip() for s in raw.split("\x00") if s.strip()]
        if len(entries) <= 1 and "\n" in raw:
            entries = [s.strip() for s in raw.split("\n") if s.strip()]
        # 条目交替为 [索引数字, 状态名]
        i = 0
        while i + 1 < len(entries):
            try:
                states[entries[i + 1]] = int(entries[i])
                i += 2
            except ValueError:
                i += 1
    return identity, states


def connect(host: str, port: int) -> socket.socket:
    sock = socket.create_connection((host, port), timeout=5.0)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sock


# ---------------------------------------------------------------------------
# Lua 执行
# ---------------------------------------------------------------------------
def execute(sock: socket.socket, state_index: int, code: str,
            timeout: float = 10.0) -> list[str]:
    """在指定状态 VM 中执行 Lua，收集 print 输出直到哨兵或超时。"""
    drain(sock, 0.1)
    send_msg(sock, TAG_COMMAND, f"CMD:{state_index}:{code}")

    lines: list[str] = []
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"{timeout:.0f}s 内未收到哨兵，已收集 {len(lines)} 行")
        sock.settimeout(min(remaining, 2.0))
        msg = recv_msg(sock)
        if msg is None:
            continue  # 读超时未到总期限，继续等
        tag, payload = msg
        if payload.startswith("ERR:"):
            raise LuaError(payload)
        if payload.startswith("O"):
            sep = payload.find(": ", 2)
            text = payload[sep + 2:] if sep >= 0 else payload.lstrip("O\x00").strip()
            if text.strip() == SENTINEL:
                break
            lines.append(text)
        # 其他 tag（如空 ack）忽略

    drain(sock, 0.2)
    return lines


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> int:
    """探测连接与对局状态。"""
    try:
        sock = connect(args.host, args.port)
    except OSError as e:
        print(f"[FAIL] 无法连接 {args.host}:{args.port} —— {e}")
        print("检查项：游戏是否已启动？EnableTuner 是否开启？FireTuner GUI 是否已关闭？")
        return 1
    try:
        identity, states = handshake(sock)
        print(f"[OK] 已连接：{identity}")
        gc = states.get("GameCore_Tuner")
        ig = states.get("InGame")
        for name, idx in sorted(states.items(), key=lambda kv: kv[1]):
            print(f"  [{idx}] {name}")
        if gc is not None and ig is not None:
            print(f"[OK] 对局进行中（gamecore={gc}, ingame={ig}），可以执行测试。")
            return 0
        print("[WAIT] 已连上但缺少 GameCore_Tuner/InGame —— 当前在主菜单，请读档进入对局。")
        return 1
    finally:
        sock.close()


def _resolve_state(states: dict[str, int], key: str | None) -> int | None:
    """把状态名或索引解析成索引；未命中返回 None。

    支持 mod 自有 UI 上下文（如 AllUnitsFoundCity）：铁律 1 的
    "gamecore/ingame 里 mod 全局为 nil" 只适用于那两个沙箱态 ——
    mod 自己的上下文（LSQ 列表里带 Context 名的条目）里 mod 全局**是在的**，
    直接按名或索引投递即可。
    """
    if key is None:
        return None
    if key in states:
        return states[key]
    if key.isdigit():
        idx = int(key)
        if idx in states.values():
            return idx
    return None


def _suggest_states(states: dict[str, int], key: str) -> str:
    """列几个名字里含 key 片段的状态，帮用户找对上下文。"""
    needle = (key or "").lower()
    hits = [(n, i) for n, i in states.items() if needle and needle in n.lower()]
    if not hits:
        return ""
    txt = "，".join(f"{n}({i})" for n, i in sorted(hits, key=lambda kv: kv[1])[:8])
    return f" 名字相近的状态：{txt}"


def _run_in_context(sock: socket.socket, states: dict[str, int], key: str,
                    code: str, timeout: float) -> tuple[int, list[str]]:
    """在指定状态 VM 执行，返回 (退出码, 输出行)。"""
    idx = _resolve_state(states, key)
    if idx is None:
        return 1, [f"[FAIL] 未找到状态 {key}。若在主菜单请先读档进对局。"
                   + _suggest_states(states, key)]
    try:
        return 0, execute(sock, idx, code, timeout=timeout)
    except LuaError as e:
        return 2, [f"[LUA ERROR] {e}"]
    except TimeoutError as e:
        return 3, [f"[TIMEOUT] {e}"]


def _load_code(args: argparse.Namespace) -> str | None:
    if args.file:
        code = Path(args.file).read_text(encoding="utf-8-sig")
    elif args.code is not None:
        code = args.code
    else:
        print("[FAIL] 需要 --code 或 --file", file=sys.stderr)
        return None
    if SENTINEL not in code:
        code += ('\n' if "\n" in code else ' ') + f'print("{SENTINEL}")'
    return code


def cmd_exec(args: argparse.Namespace) -> int:
    """执行 Lua 并打印收集到的输出。--both 时两端各跑一次并加标签。"""
    code = _load_code(args)
    if code is None:
        return 1

    try:
        sock = connect(args.host, args.port)
    except OSError as e:
        print(f"[FAIL] 无法连接 {args.host}:{args.port} —— {e}", file=sys.stderr)
        return 1
    try:
        identity, states = handshake(sock)
        if not args.both:
            if args.state:
                key = args.state
            else:
                key = "GameCore_Tuner" if args.context == "gamecore" else "InGame"
            rc, lines = _run_in_context(sock, states, key, code, args.timeout)
            for ln in lines:
                (sys.stderr if rc else sys.stdout).write(ln + "\n")
            return rc

        # --both：两端各跑一次（GP 先、UI 后），输出带标签便于直接 diff
        rc_all = 0
        for label, key in (("GP", "GameCore_Tuner"), ("UI", "InGame")):
            print(f"########## {label} ({key}) ##########")
            rc, lines = _run_in_context(sock, states, key, code, args.timeout)
            for ln in lines:
                print(ln)
            if rc:
                rc_all = rc
            print()
        return rc_all
    finally:
        sock.close()


def cmd_ports(args: argparse.Namespace) -> int:
    """双端端口矩阵：跑 snippets/port_matrix.lua，输出两端结果 + 差异表。"""
    snip = Path(__file__).resolve().parent.parent / "snippets" / "port_matrix.lua"
    if not snip.exists():
        print(f"[FAIL] 缺少片段：{snip}", file=sys.stderr)
        return 1
    args.file = str(snip)
    args.code = None
    args.both = True
    args.timeout = args.timeout or 20.0
    return cmd_exec(args)


def cmd_logs(args: argparse.Namespace) -> int:
    """尾随/检索日志。支持 --grep 过滤与 --since-mark 从最近一次标记起截取。"""
    log_path = LOG_DIR / args.log_file
    if not log_path.exists():
        print(f"[MISS] 日志不存在：{log_path}")
        print("游戏本次启动后才会创建；确认路径或先用 --log-file 指定其他文件。")
        return 1
    with open(log_path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    start = 0
    if args.since_mark:
        marks = [i for i, l in enumerate(lines) if args.since_mark in l]
        if marks:
            start = marks[-1]
            print(f"[INFO] 从最后一次「{args.since_mark}」起（第 {start + 1} 行，共 {len(lines)} 行）")
        else:
            print(f"[INFO] 未找到标记「{args.since_mark}」，输出全部匹配行")

    seg = lines[start:]
    if args.grep:
        import re
        try:
            rx = re.compile(args.grep)
        except re.error as e:
            print(f"[FAIL] --grep 正则非法：{e}", file=sys.stderr)
            return 1
        seg = [l for l in seg if rx.search(l)]
        sys.stdout.write("".join(seg[-(args.lines or len(seg)):]))
        return 0

    sys.stdout.write("".join(seg[-args.lines:]))
    return 0


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        prog="tuner_exec.py",
        description="文明6 FireTuner 调试接口测试工具（详见 SKILL.md）",
    )
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)

    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("check", help="探测连接与对局状态").set_defaults(func=cmd_check)

    p_exec = sub.add_parser("exec", help="执行 Lua（默认 gamecore 只读上下文）")
    p_exec.add_argument("--context", choices=["gamecore", "ingame"],
                        default="gamecore",
                        help="gamecore=GP层只读(Player/GameInfo/Game)；"
                             "ingame=UI层读写(UI.*/CityManager/UnitManager)")
    p_exec.add_argument("--code", help="单行/多行 Lua 代码字符串")
    p_exec.add_argument("--file", help="Lua 文件路径（UTF-8）")
    p_exec.add_argument("--state", dest="state", default=None,
                        help="直接指定状态名或索引（覆盖 --context）。用来投递到 "
                             "mod 自有的 UI 上下文，如 --state AllUnitsFoundCity；"
                             "这类态里 mod 的全局函数是可调的")
    p_exec.add_argument("--both", action="store_true",
                        help="两端各跑一次（GP 先、UI 后），输出带标签便于直接对比")
    p_exec.add_argument("--timeout", type=float, default=10.0,
                        help="哨兵收集超时秒数，默认 10")
    p_exec.set_defaults(func=cmd_exec)

    p_ports = sub.add_parser("ports",
                             help="双端端口矩阵：跑 snippets/port_matrix.lua 并按两端口输出")
    p_ports.add_argument("--timeout", type=float, default=20.0)
    p_ports.set_defaults(func=cmd_ports)

    p_logs = sub.add_parser("logs", help="尾随/检索游戏日志")
    p_logs.add_argument("--log-file", default="Lua.log",
                        help="日志文件名，如 Database.log / Lua.log，默认 Lua.log")
    p_logs.add_argument("-n", "--lines", type=int, default=50,
                        help="显示最后 N 行，默认 50")
    p_logs.add_argument("--grep", help="只输出匹配该正则的行（常用：QJ / Runtime Error）")
    p_logs.add_argument("--since-mark", dest="since_mark",
                        help="从最后一次出现该字符串的位置开始截取（避开旧会话噪声）")
    p_logs.set_defaults(func=cmd_logs)

    argv = sys.argv[1:]
    # 简写：`--check` 单独出现等价于 `check`
    if "--check" in argv:
        argv = [a for a in argv if a != "--check"] or ["check"]
    args = ap.parse_args(argv)
    if args.cmd is None:
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
