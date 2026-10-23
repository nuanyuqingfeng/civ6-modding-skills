#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""civ6-tuner 会话守护进程：持有唯一 FireTuner 连接，向本地 CLI 提供 JSONL 请求。

设计要点（与 SKILL.md「会话与守护进程」一致）：
    * 不随机自启，只由 CLI 在首个命令时按需拉起（DETACHED_PROCESS）。
    * 空闲 180s / 兜底 8h 自行退出；有在途命令时不计时、不退出。
    * 对端断开只标记失效，**不做后台自动重连**（坏握手会把 tuner 打挂）。
    * 退出只关闭 socket 并删登记文件，不存档、不关游戏、不杀进程。

控制协议：本地回环 TCP，一行一条 JSON。
    请求 {"v":1,"token":"...","id":"c-1","op":"exec","state":"gamecore","code":"...","timeout":10}
    应答 {"v":1,"id":"c-1","ok":true,"rc":0,"lines":["..."],"meta":{...}}
         {"v":1,"id":"c-1","ok":false,"rc":1,"error":{"kind":"connect","message":"..."}}

登记文件：%LOCALAPPDATA%\\civ6-tuner\\daemon.json（端口 / PID / token / 启动时刻）
日志文件：%LOCALAPPDATA%\\civ6-tuner\\daemon.log
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import socket
import sys
import threading
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tuner_link import (  # noqa: E402  同目录脚本，必须先补 sys.path
    DEFAULT_HOST,
    DEFAULT_PORT,
    LinkClosed,
    LuaError,
    connect,
    context_key,
    execute,
    handshake,
    peer_closed,
    resolve_state,
    suggest_states,
)

# ---------------------------------------------------------------------------
# 路径与默认值
# ---------------------------------------------------------------------------
STATE_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "civ6-tuner"
REGISTRY_PATH = STATE_DIR / "daemon.json"
LOG_PATH = STATE_DIR / "daemon.log"

DAEMON_PORT = 4319
PROTOCOL_VERSION = 1
MAX_LOG_BYTES = 2 * 1024 * 1024

IDLE_SECONDS = float(os.environ.get("CIV6_TUNER_IDLE", "180"))
MAX_LIFE_SECONDS = float(os.environ.get("CIV6_TUNER_MAX_LIFE", "28800"))

# Windows 进程创建标志：脱离控制台 + 不弹窗口，终端关掉也不影响守护进程
DETACHED_PROCESS = 0x00000008
CREATE_NO_WINDOW = 0x08000000


class StateMissing(Exception):
    """目标状态名/索引不在当前 LSQ 列表里。"""

    def __init__(self, key: str, hint: str):
        super().__init__(key)
        self.key = key
        self.hint = hint


# ---------------------------------------------------------------------------
# 登记文件与日志
# ---------------------------------------------------------------------------
def read_registry() -> dict | None:
    """读登记文件；不存在或损坏返回 None。"""
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_registry(port: int, token: str, pid: int, game_port: int) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "v": PROTOCOL_VERSION,
        "port": port,
        "pid": pid,
        "token": token,
        "game_port": game_port,
        "started": time.time(),
    }, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, REGISTRY_PATH)


def clear_registry(token: str) -> None:
    """只删除属于本进程的登记，避免误删新实例刚写的文件。"""
    reg = read_registry()
    if reg and reg.get("token") == token:
        try:
            REGISTRY_PATH.unlink()
        except OSError:
            pass


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def log_line(text: str) -> None:
    """追加一行日志；超过上限就先截断，避免长期占用磁盘。"""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > MAX_LOG_BYTES:
            LOG_PATH.write_text("", encoding="utf-8")
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{stamp} {text}\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# 游戏连接
# ---------------------------------------------------------------------------
class GameLink:
    """一条常驻 FireTuner 连接，外加状态表与连接代际。"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader = None
        self.identity = ""
        self.states: dict[str, int] = {}
        self.generation = 0
        self.last_error: str | None = None

    @property
    def connected(self) -> bool:
        return self.reader is not None and not peer_closed(self.reader)

    def drop(self, reason: str) -> None:
        if self.reader is not None:
            self.reader.close()
        self.reader = None
        self.identity = ""
        self.states = {}
        self.last_error = reason

    def ensure(self) -> None:
        """确保连接可用。失败只尝试一次，不做重试（坏握手防护）。"""
        if self.reader is not None:
            if not peer_closed(self.reader):
                return
            self.drop("对端已关闭")
        self.reader = connect(self.host, self.port)
        try:
            self.identity, self.states = handshake(self.reader)
        except Exception as e:
            self.reader.close()
            self.reader = None
            self.states = {}
            self.identity = ""
            self.last_error = f"握手失败：{e}"
            raise
        self.generation += 1
        self.last_error = None

    def run(self, key: str, code: str, timeout: float) -> list[str]:
        idx = resolve_state(self.states, key)
        if idx is None:
            raise StateMissing(key, "若在主菜单请先读档进对局。" + suggest_states(self.states, key))
        return execute(self.reader, idx, code, timeout=timeout)


# ---------------------------------------------------------------------------
# 守护进程
# ---------------------------------------------------------------------------
class Daemon:
    def __init__(self, port: int, game_host: str, game_port: int,
                 idle: float = IDLE_SECONDS, max_life: float = MAX_LIFE_SECONDS):
        self.port = port
        self.idle = idle
        self.max_life = max_life
        self.link = GameLink(game_host, game_port)
        self.token = secrets.token_hex(16)
        self.started = time.monotonic()
        self.last_activity = time.monotonic()
        self.work_lock = threading.Lock()
        self.busy = False
        self.stop_event = threading.Event()
        self.stop_reason = ""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", port))
        self.server.listen(8)
        self.server.settimeout(0.5)

    # -- 生命周期 ----------------------------------------------------------
    def serve(self) -> None:
        write_registry(self.port, self.token, os.getpid(), self.link.port)
        log_line(f"daemon up pid={os.getpid()} port={self.port} "
                 f"game={self.link.host}:{self.link.port} idle={self.idle:.0f}s")
        threading.Thread(target=self._maintain, name="maintain", daemon=True).start()
        try:
            while not self.stop_event.is_set():
                try:
                    conn, addr = self.server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                threading.Thread(target=self._handle, args=(conn, addr),
                                 name="request", daemon=True).start()
        finally:
            self._shutdown()

    def request_stop(self, reason: str) -> None:
        if not self.stop_reason:
            self.stop_reason = reason
        self.stop_event.set()

    def _shutdown(self) -> None:
        # 等当前命令收尾（最多 10s）再断连接，避免把在途 exec 拦腰切断
        got_lock = self.work_lock.acquire(timeout=10.0)
        try:
            self.link.drop("守护进程退出")
        finally:
            if got_lock:
                self.work_lock.release()
        try:
            self.server.close()
        except OSError:
            pass
        clear_registry(self.token)
        log_line(f"daemon down pid={os.getpid()} reason={self.stop_reason or 'normal'}")

    def _maintain(self) -> None:
        """每秒检查空闲 / 兜底寿命 / 对端存活；这是唯一的自动退出路径。"""
        while not self.stop_event.wait(1.0):
            if self.busy:
                # 有在途命令时一切计时暂停：既不会误杀，也不会把忙时算进空闲
                self.last_activity = time.monotonic()
                continue
            now = time.monotonic()
            if self.link.reader is not None and peer_closed(self.link.reader):
                self.link.drop("对端已关闭")
                log_line("game link closed by peer; marked dead (no auto-reconnect)")
            if now - self.last_activity > self.idle:
                self.request_stop(f"idle {now - self.last_activity:.0f}s")
                return
            if now - self.started > self.max_life:
                self.request_stop(f"max-life {now - self.started:.0f}s")
                return

    # -- 请求处理 ----------------------------------------------------------
    def _handle(self, conn: socket.socket, _addr) -> None:
        conn.settimeout(300)
        try:
            raw = _read_line(conn)
            if not raw:
                return
            try:
                req = json.loads(raw)
            except ValueError as e:
                _send(conn, _fail(None, 1, "protocol", f"请求不是合法 JSON：{e}"))
                return
            resp = self._dispatch(req)
            _send(conn, resp)
        except OSError:
            pass
        except Exception:
            log_line("handler crashed: " + traceback.format_exc().splitlines()[-1])
            try:
                _send(conn, _fail(None, 1, "internal", "守护进程内部错误，详见 daemon.log"))
            except OSError:
                pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _dispatch(self, req: dict) -> dict:
        rid = req.get("id")
        if not hmac.compare_digest(str(req.get("token") or ""), self.token):
            return _fail(rid, 1, "auth", "token 不匹配，拒绝执行")

        op = req.get("op")
        self.last_activity = time.monotonic()

        if op == "ping":
            return _ok(rid, 0, meta=self._status())

        if op == "status":
            return _ok(rid, 0, meta=self._status())

        if op == "stop":
            self.request_stop("client stop")
            return _ok(rid, 0, lines=["[OK] 守护进程正在退出"])

        if op == "ensure":
            return self._with_work(lambda: self._op_ensure(rid))

        if op == "release":
            # FireTuner 只允许一个连接：其他工具（gamectl）要直连时先让路。
            self._with_work(lambda: self._op_release(rid))
            return _ok(rid, 0, meta=self._status())

        if op == "exec":
            return self._with_work(lambda: self._op_exec(rid, req))

        if op == "both":
            return self._with_work(lambda: self._op_both(rid, req))

        return _fail(rid, 1, "protocol", f"未知 op：{op}")

    def _with_work(self, fn) -> dict:
        with self.work_lock:
            self.busy = True
            try:
                return fn()
            finally:
                self.busy = False
                self.last_activity = time.monotonic()

    def _op_ensure(self, rid) -> dict:
        try:
            self.link.ensure()
        except OSError as e:
            self.link.last_error = str(e)
            return _fail(rid, 1, "connect", f"无法连接 {self.link.host}:{self.link.port} —— {e}")
        except LinkClosed as e:
            self.link.last_error = str(e)
            return _fail(rid, 4, "closed", f"握手期间连接断开 —— {e}")
        except TimeoutError as e:
            return _fail(rid, 3, "timeout", str(e))
        return _ok(rid, 0, meta=self._status())

    def _op_release(self, rid) -> None:
        """主动断开游戏连接，把唯一的 tuner 名额让给别的进程。"""
        self.link.drop("client release")

    def _op_exec(self, rid, req: dict) -> dict:
        key = context_key(req.get("state"), req.get("context") or "gamecore")
        code = req.get("code")
        if not isinstance(code, str):
            return _fail(rid, 1, "protocol", "缺少 code")
        timeout = float(req.get("timeout") or 10.0)
        try:
            self.link.ensure()
            lines = self.link.run(key, code, timeout)
        except StateMissing as e:
            return _fail(rid, 1, "state_missing", f"未找到状态 {e.key}。{e.hint}")
        except LuaError as e:
            return _fail(rid, 2, "lua", str(e))
        except TimeoutError as e:
            # 常驻连接一旦超时就废弃：残留命令可能仍在游戏里跑，
            # 继续等它的结束标记只会让下一条命令再烧一次超时。
            self.link.drop(f"命令超时：{e}")
            return _fail(rid, 3, "timeout", str(e))
        except LinkClosed as e:
            self.link.drop(str(e))
            return _fail(rid, 4, "closed", str(e))
        except OSError as e:
            self.link.drop(str(e))
            return _fail(rid, 1, "connect", f"无法连接 {self.link.host}:{self.link.port} —— {e}")
        return _ok(rid, 0, lines=lines, meta=self._status())

    def _op_both(self, rid, req: dict) -> dict:
        code = req.get("code")
        if not isinstance(code, str):
            return _fail(rid, 1, "protocol", "缺少 code")
        timeout = float(req.get("timeout") or 10.0)
        sections = []
        rc_all = 0
        try:
            self.link.ensure()
        except OSError as e:
            return _fail(rid, 1, "connect", f"无法连接 {self.link.host}:{self.link.port} —— {e}")
        except LinkClosed as e:
            return _fail(rid, 4, "closed", f"握手期间连接断开 —— {e}")
        for label, key in (("GP", "GameCore_Tuner"), ("UI", "InGame")):
            try:
                lines = self.link.run(key, code, timeout)
                rc = 0
            except StateMissing as e:
                lines, rc = [f"[FAIL] 未找到状态 {e.key}。{e.hint}"], 1
            except LuaError as e:
                lines, rc = [f"[LUA ERROR] {e}"], 2
            except TimeoutError as e:
                self.link.drop(f"命令超时：{e}")
                sections.append({"label": label, "key": key, "rc": 3,
                                 "lines": [f"[TIMEOUT] {e}"]})
                return _ok(rid, 3, sections=sections, meta=self._status())
            except LinkClosed as e:
                self.link.drop(str(e))
                return _fail(rid, 4, "closed", str(e))
            rc_all = rc_all or rc
            sections.append({"label": label, "key": key, "rc": rc, "lines": lines})
        return _ok(rid, rc_all, sections=sections, meta=self._status())

    # -- 自述 --------------------------------------------------------------
    def _status(self) -> dict:
        now = time.monotonic()
        return {
            "pid": os.getpid(),
            "port": self.port,
            "version": PROTOCOL_VERSION,
            "uptime": round(now - self.started, 1),
            "idle_for": round(now - self.last_activity, 1),
            "idle_limit": self.idle,
            "max_life": self.max_life,
            "busy": self.busy,
            "connected": self.link.connected,
            "identity": self.link.identity,
            "states": self.link.states,
            "generation": self.link.generation,
            "in_game": ("GameCore_Tuner" in self.link.states
                        and "InGame" in self.link.states),
            "game": {"host": self.link.host, "port": self.link.port},
            "last_error": self.link.last_error,
        }


# ---------------------------------------------------------------------------
# 线格式辅助
# ---------------------------------------------------------------------------
def _ok(rid, rc: int, lines: list[str] | None = None, sections=None, meta=None) -> dict:
    out = {"v": PROTOCOL_VERSION, "id": rid, "ok": rc == 0, "rc": rc}
    if lines is not None:
        out["lines"] = lines
    if sections is not None:
        out["sections"] = sections
    if meta is not None:
        out["meta"] = meta
    return out


def _fail(rid, rc: int, kind: str, message: str) -> dict:
    return {"v": PROTOCOL_VERSION, "id": rid, "ok": False, "rc": rc,
            "error": {"kind": kind, "message": message}}


def _read_line(conn: socket.socket, limit: int = 32 * 1024 * 1024) -> str:
    buf = bytearray()
    while b"\n" not in buf:
        chunk = conn.recv(65536)
        if not chunk:
            break
        buf += chunk
        if len(buf) > limit:
            raise OSError("请求过大")
    return bytes(buf).split(b"\n", 1)[0].decode("utf-8", errors="replace")


def _send(conn: socket.socket, payload: dict) -> None:
    conn.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(prog="tunerd.py", description="civ6-tuner 会话守护进程")
    ap.add_argument("--port", type=int, default=DAEMON_PORT, help="控制端口，默认 4319")
    ap.add_argument("--game-host", default=DEFAULT_HOST)
    ap.add_argument("--game-port", type=int, default=DEFAULT_PORT, help="FireTuner 端口，默认 4318")
    ap.add_argument("--idle", type=float, default=IDLE_SECONDS, help="空闲退出秒数，默认 180")
    ap.add_argument("--max-life", type=float, default=MAX_LIFE_SECONDS, help="兜底寿命秒数")
    args = ap.parse_args()

    try:
        daemon = Daemon(args.port, args.game_host, args.game_port,
                        idle=args.idle, max_life=args.max_life)
    except OSError as e:
        # 端口被占：已有实例在跑，直接退出让客户端去连它
        log_line(f"bind failed port={args.port}: {e}")
        return 2

    try:
        daemon.serve()
    except KeyboardInterrupt:
        daemon.request_stop("interrupt")
        daemon._shutdown()
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
