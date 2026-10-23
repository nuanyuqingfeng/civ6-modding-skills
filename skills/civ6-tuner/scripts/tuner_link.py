#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FireTuner 线协议层：帧收发、握手、Lua 执行。

从 tuner_exec.py 原样抽出，行为不变，供冷连接 CLI 与常驻 daemon 共用。
协议来源：逆向成果借鉴 github.com/lmwilki/civ6-mcp（MIT License）。
    线格式：[4字节LE uint32 长度][4字节LE int32 tag][null 结尾 payload]
    握手：  tag=4 发 "APP:" -> 游戏身份；"LSQ:" -> Lua 状态列表
    执行：  tag=3 发 "CMD:{状态索引}:{Lua代码}"
    回包：  "O\\x00<上下文>: <值>" = print() 输出；"ERR:" 开头 = Lua 错误
    哨兵：  print("---END---") 标记输出收集完成
"""

from __future__ import annotations

import itertools
import os
import select
import socket
import struct
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

MAX_FRAME_BYTES = 16 * 1024 * 1024


class LuaError(Exception):
    """游戏返回 ERR: 时抛出。"""


class LinkClosed(Exception):
    """连接被对端关闭。"""


# ---------------------------------------------------------------------------
# 帧收发
# ---------------------------------------------------------------------------
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
# 状态解析与连接健康
# ---------------------------------------------------------------------------
def resolve_state(states: dict[str, int], key: str | None) -> int | None:
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


def suggest_states(states: dict[str, int], key: str) -> str:
    """列几个名字里含 key 片段的状态，帮用户找对上下文。"""
    needle = (key or "").lower()
    hits = [(n, i) for n, i in states.items() if needle and needle in n.lower()]
    if not hits:
        return ""
    txt = "，".join(f"{n}({i})" for n, i in sorted(hits, key=lambda kv: kv[1])[:8])
    return f" 名字相近的状态：{txt}"


def context_key(name: str | None, context: str = "gamecore") -> str:
    """--state 优先；否则 gamecore/ingame 映射到两个引擎沙箱态名。"""
    if name:
        return name
    return "GameCore_Tuner" if context == "gamecore" else "InGame"


def peer_closed(reader: "FrameReader") -> bool:
    """非阻塞检查对端是否已关闭（MSG_PEEK，不消费字节）。"""
    sock = reader.sock
    try:
        readable, _, _ = select.select([sock], [], [], 0)
    except OSError:
        return True
    if not readable:
        return False
    try:
        return sock.recv(1, socket.MSG_PEEK) == b""
    except BlockingIOError:
        return False
    except OSError:
        return True
