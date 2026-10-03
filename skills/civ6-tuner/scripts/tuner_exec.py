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
import itertools
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

# 每条命令带独立递增标记：前一条超时后迟到的结束帧不会被下一条命令错认成自己的，
# 因此一次超时不会污染后续命令的输出。
_CMD_NONCE = itertools.count(1)
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
class LinkClosed(Exception):
    """连接被对端关闭。"""


MAX_FRAME_BYTES = 16 * 1024 * 1024


class FrameReader:
    """持久接收缓冲。

    帧边界跨多次 recv 时残字节留在缓冲里：读超时抛 TimeoutError 且缓冲原样保留，
    不存在"读残了再丢掉"的路径，因此任何一次超时都不会让后续帧错位。
    """

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buf = bytearray()
        # 上一条命令超时后遗留的结束标记：下一条命令先等它到达并整段丢弃，
        # 否则迟到的输出行会被下一条命令当成自己的输出。
        self.pending_token: str | None = None

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def _extract(self) -> tuple[int, str] | None:
        """凑够一整帧就弹出；不足一帧返回 None（残字节留在缓冲）。"""
        if len(self.buf) < 8:
            return None
        length, tag = struct.unpack(HEADER_FMT, bytes(self.buf[:8]))
        if length < 0 or length > MAX_FRAME_BYTES:
            raise LinkClosed(f"帧长度异常（{length}），连字节流已错位")
        if len(self.buf) < 8 + length:
            return None
        payload = bytes(self.buf[8:8 + length])
        del self.buf[:8 + length]
        return tag, payload.rstrip(b"\x00").decode("utf-8", errors="replace")

    def read(self, timeout: float) -> tuple[int, str]:
        """读一整帧；超时抛 TimeoutError，对端关闭抛 LinkClosed。"""
        deadline = time.monotonic() + timeout
        while True:
            frame = self._extract()
            if frame is not None:
                return frame
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("等待帧超时")
            self.sock.settimeout(remaining)
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                raise TimeoutError("等待帧超时") from None
            except OSError as e:
                raise LinkClosed(str(e)) from None
            if not chunk:
                raise LinkClosed("对端关闭连接")
            self.buf += chunk

    def drain(self) -> list[tuple[int, str]]:
        """取走缓冲里已完整到达的全部帧，不阻塞等待新数据。"""
        out = []
        while True:
            frame = self._extract()
            if frame is None:
                return out
            out.append(frame)


def send_msg(sock: socket.socket, tag: int, payload: str) -> None:
    data = payload.encode("utf-8") + b"\x00"
    sock.sendall(struct.pack(HEADER_FMT, len(data), tag) + data)


# ---------------------------------------------------------------------------
# 握手与状态发现
# ---------------------------------------------------------------------------
def parse_states(raw: str) -> dict[str, int]:
    """解析 LSQ 回包：条目交替为 [索引数字, 状态名]。"""
    entries = [s.strip() for s in raw.split("\x00") if s.strip()]
    if len(entries) <= 1 and "\n" in raw:
        entries = [s.strip() for s in raw.split("\n") if s.strip()]
    states: dict[str, int] = {}
    i = 0
    while i + 1 < len(entries):
        try:
            states[entries[i + 1]] = int(entries[i])
            i += 2
        except ValueError:
            i += 1
    return states


def _query(reader: "FrameReader", timeout: float) -> str | None:
    """在 timeout 内等一条握手回包；超时返回 None。"""
    try:
        return reader.read(timeout)[1]
    except TimeoutError:
        return None


def handshake(reader: "FrameReader", timeout: float = 8.0) -> tuple[str, dict[str, int]]:
    """握手并解析 Lua 状态表。返回 (游戏身份, {状态名: 索引})。

    两条 query 各持独立截止时间，避免单次未达就静默退化成空表。
    """
    reader.drain()

    send_msg(reader.sock, TAG_HANDSHAKE, "APP:")
    identity = _query(reader, timeout) or "<无响应>"

    send_msg(reader.sock, TAG_HANDSHAKE, "LSQ:")
    raw = _query(reader, timeout) or ""
    return identity, parse_states(raw)


def connect(host: str, port: int) -> FrameReader:
    """建立连接并返回带持久缓冲的读取器。"""
    sock = socket.create_connection((host, port), timeout=5.0)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return FrameReader(sock)


# ---------------------------------------------------------------------------
# Lua 执行
# ---------------------------------------------------------------------------
def _frame_text(payload: str) -> str | None:
    """print 帧取净文本；非 print 帧返回 None。"""
    if not payload.startswith("O"):
        return None
    sep = payload.find(": ", 2)
    text = payload[sep + 2:] if sep >= 0 else payload.lstrip("O\x00").strip()
    return text.strip()


def _resync_after_timeout(reader: "FrameReader", timeout: float) -> None:
    """上一条命令超时后，先等它的结束标记到达并把这段输出整段丢弃。

    标记唯一，因此只有那个特定标记才算对齐；在它之前到达的一切（该命令迟到的
    输出行、其他命令的标记）一律丢弃。始终等不到就抛 LinkClosed，由调用方重连，
    避免把上一条命令的输出错记到本条命令名下。
    """
    stale = reader.pending_token
    if stale is None:
        return
    reader.pending_token = None
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LinkClosed("上一条超时命令的结束标记始终未到，字节流无法确认对齐")
        try:
            _tag, payload = reader.read(remaining)
        except TimeoutError:
            raise LinkClosed(
                "上一条超时命令的结束标记始终未到，字节流无法确认对齐") from None
        if _frame_text(payload) == stale:
            return


def execute(reader: "FrameReader", state_index: int, code: str,
            timeout: float = 10.0) -> list[str]:
    """在指定状态 VM 中执行 Lua，收集 print 输出直到哨兵或超时。

    结束帧由本函数负责补齐，且每条命令带独立标记（游戏不会自动追加结束标记：
    实测未带哨兵的代码只回 print 帧与一条空 ack）。标记唯一 ⇒ 即使前一条命令超时
    后其结束帧迟到，也不会被本次当成自己的终止帧。
    残帧由 FrameReader 跨次保留，只有真的到达 deadline 才判超时。
    """
    token = f"{SENTINEL}{next(_CMD_NONCE)}"
    _resync_after_timeout(reader, timeout)
    code += ('\n' if "\n" in code else ' ') + f'print("{token}")'
    reader.drain()
    send_msg(reader.sock, TAG_COMMAND, f"CMD:{state_index}:{code}")

    lines: list[str] = []
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            reader.pending_token = token
            raise TimeoutError(f"{timeout:.0f}s 内未收到哨兵，已收集 {len(lines)} 行")
        try:
            _tag, payload = reader.read(remaining)
        except TimeoutError:
            reader.pending_token = token
            raise TimeoutError(
                f"{timeout:.0f}s 内未收到哨兵，已收集 {len(lines)} 行") from None
        if payload.startswith("ERR:"):
            raise LuaError(payload)
        text = _frame_text(payload)
        if text is not None:
            if text == token:
                break
            # 迟到的结束帧（本命令之外的一切 ---END--- 变体）丢弃，不计入本次输出
            if text.startswith(SENTINEL):
                continue
            lines.append(text)
        # 其他 tag（如空 ack）忽略

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
    except LinkClosed as e:
        print(f"[FAIL] 握手期间连接断开 —— {e}")
        print("检查项：游戏是否正在切换对局？等它稳定后重试。")
        sock.close()
        return 1
    try:
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


def _run_in_context(reader: "FrameReader", states: dict[str, int], key: str,
                    code: str, timeout: float) -> tuple[int, list[str]]:
    """在指定状态 VM 执行，返回 (退出码, 输出行)。"""
    idx = _resolve_state(states, key)
    if idx is None:
        return 1, [f"[FAIL] 未找到状态 {key}。若在主菜单请先读档进对局。"
                   + _suggest_states(states, key)]
    try:
        return 0, execute(reader, idx, code, timeout=timeout)
    except LuaError as e:
        return 2, [f"[LUA ERROR] {e}"]
    except TimeoutError as e:
        return 3, [f"[TIMEOUT] {e}"]
    except LinkClosed as e:
        return 4, [f"[CLOSED] {e}"]


def _load_code(args: argparse.Namespace) -> str | None:
    """取代码原文；哨兵补齐统一由 execute() 负责，此处不重复追加。"""
    if args.file:
        return Path(args.file).read_text(encoding="utf-8-sig")
    if args.code is not None:
        return args.code
    print("[FAIL] 需要 --code 或 --file", file=sys.stderr)
    return None


def cmd_exec(args: argparse.Namespace) -> int:
    """执行 Lua 并打印收集到的输出。--both 时两端各跑一次并加标签。"""
    code = _load_code(args)
    if code is None:
        return 1
    if getattr(args, "tag", None):
        code = ('print("TUNER|op=' + args.tag + '|begin|turn=" .. Game.GetCurrentGameTurn())\n') + code

    try:
        sock = connect(args.host, args.port)
    except OSError as e:
        print(f"[FAIL] 无法连接 {args.host}:{args.port} —— {e}", file=sys.stderr)
        return 1
    try:
        identity, states = handshake(sock)
    except LinkClosed as e:
        print(f"[CLOSED] 握手中连接被对端关闭 —— {e}", file=sys.stderr)
        sock.close()
        return 4
    try:
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
    """尾随/检索日志。支持 --grep/--prefix 过滤与 --since-mark 从最近一次标记起截取。"""
    import re
    log_path = LOG_DIR / args.log_file
    if not log_path.exists():
        print(f"[MISS] 日志不存在：{log_path}")
        print("游戏本次启动后才会创建；确认路径或先用 --log-file 指定其他文件。")
        return 1
    with open(log_path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if getattr(args, "prefix", None):
        args.grep = re.escape(args.prefix)

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
    p_exec.add_argument("--tag", help="执行前向 Lua.log 打一行 TUNER|op=<tag>|begin（测试留痕）")
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
    p_logs.add_argument("--prefix", help="字面前缀过滤（--grep 的正则转义版，如 TUNER|RCC_AMENITY）")
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
