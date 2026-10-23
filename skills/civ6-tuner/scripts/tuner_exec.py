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
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tuner_link import (  # noqa: E402  同目录脚本，必须先补 sys.path
    DEFAULT_HOST,
    DEFAULT_PORT,
    LOG_DIR,
    FrameReader,
    LinkClosed,
    LuaError,
    connect,
    execute,
    handshake,
    resolve_state,
    suggest_states,
)
from tunerd import (  # noqa: E402
    CREATE_NO_WINDOW,
    DAEMON_PORT,
    DETACHED_PROCESS,
    pid_alive,
    read_registry,
)


# ---------------------------------------------------------------------------
# 守护进程客户端
# ---------------------------------------------------------------------------
def _control_port(args: argparse.Namespace) -> int:
    return args.daemon_port or int(os.environ.get("CIV6_TUNER_DAEMON_PORT", DAEMON_PORT))


def _request(port: int, payload: dict, wait: float) -> dict:
    """向守护进程发一条 JSONL 请求并读回一条应答。"""
    reg = read_registry() or {}
    token = reg.get("token") if reg.get("port") == port else None
    body = {"v": 1, "token": token, **payload}
    with socket.create_connection(("127.0.0.1", port), timeout=3.0) as sock:
        sock.settimeout(wait)
        sock.sendall((json.dumps(body, ensure_ascii=False) + "\n").encode("utf-8"))
        buf = bytearray()
        while b"\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
    if not buf:
        raise OSError("守护进程未返回应答")
    return json.loads(bytes(buf).split(b"\n", 1)[0].decode("utf-8"))


def _ping(port: int) -> bool:
    try:
        return bool(_request(port, {"op": "ping"}, 2.0).get("ok"))
    except (OSError, ValueError):
        return False


def ensure_daemon(port: int) -> str | None:
    """返回 existing / spawned；起不来返回 None。

    只按需拉起，不做任何后台轮询——这是与"常驻服务"的关键区别。
    """
    if _ping(port):
        return "existing"
    script = Path(__file__).resolve().parent / "tunerd.py"
    try:
        subprocess.Popen(
            [sys.executable, str(script), "--port", str(port)],
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        print(f"[WARN] 无法拉起守护进程：{e}", file=sys.stderr)
        return None
    deadline = time.monotonic() + 6.0
    while time.monotonic() < deadline:
        reg = read_registry() or {}
        if reg.get("port") == port and pid_alive(reg.get("pid")) and _ping(port):
            return "spawned"
        time.sleep(0.1)
    return None


def daemon_call(args: argparse.Namespace, payload: dict,
                wait: float) -> tuple[dict | None, bool]:
    """发请求；返回 (应答, 是否本次拉起)。应答为 None 时调用方回退直连。"""
    port = _control_port(args)
    state = ensure_daemon(port)
    if state is None:
        return None, False
    try:
        return _request(port, payload, wait), state == "spawned"
    except (OSError, ValueError) as e:
        print(f"[WARN] 守护进程通信失败：{e}", file=sys.stderr)
        return None, state == "spawned"


def _stop_daemon(port: int) -> None:
    """尽力通知守护进程退出；失败不报错（它会在空闲熔断时自己走）。"""
    try:
        _request(port, {"op": "stop"}, 3.0)
    except (OSError, ValueError):
        pass


def yield_daemon(port: int | None = None) -> bool:
    """让守护进程主动断开游戏连接。

    FireTuner 只允许一个连接：gamectl 等需要直连的工具在连接前调用本函数，
    避免被守护进程占着名额而收到"连接被拒绝"。
    """
    port = port or int(os.environ.get("CIV6_TUNER_DAEMON_PORT", DAEMON_PORT))
    if not _ping(port):
        return False
    try:
        return bool(_request(port, {"op": "release"}, 5.0).get("ok"))
    except (OSError, ValueError):
        return False


def _print_game_status(resp: dict) -> int:
    """按 check 的既有格式打印守护进程返回的连接状态。"""
    if not resp.get("ok"):
        err = resp.get("error") or {}
        msg = err.get("message") or "未知错误"
        print(f"[FAIL] {msg}")
        if err.get("kind") == "connect":
            print("检查项：游戏是否已启动？EnableTuner 是否开启？FireTuner GUI 是否已关闭？")
        return int(resp.get("rc") or 1)
    meta = resp.get("meta") or {}
    if not meta.get("connected"):
        print("[FAIL] 未建立连接")
        return 1
    print(f"[OK] 已连接：{meta.get('identity')}")
    states = meta.get("states") or {}
    for name, idx in sorted(states.items(), key=lambda kv: kv[1]):
        print(f"  [{idx}] {name}")
    if meta.get("in_game"):
        print(f"[OK] 对局进行中（gamecore={states.get('GameCore_Tuner')}, "
              f"ingame={states.get('InGame')}），可以执行测试。")
        return 0
    print("[WAIT] 已连上但缺少 GameCore_Tuner/InGame —— 当前在主菜单，请读档进入对局。")
    return 1


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> int:
    """探测连接与对局状态。默认经守护进程；--no-daemon 时冷连接直连。"""
    if not getattr(args, "no_daemon", False):
        resp, spawned = daemon_call(args, {"op": "ensure"}, 40.0)
        if resp is not None:
            rc = _print_game_status(resp)
            # 只有"本次刚拉起却连不上游戏"才回收；主菜单是有效连接，留着给后续读档用
            kind = (resp.get("error") or {}).get("kind")
            if spawned and not resp.get("ok") and kind == "connect":
                _stop_daemon(_control_port(args))
            return rc
        print("[WARN] 守护进程不可用，回退直连 FireTuner", file=sys.stderr)
    else:
        # 显式回退：先把守护进程停掉，否则它占着 FireTuner 唯一连接
        _stop_daemon(_control_port(args))
    return _cold_check(args)


def _cold_check(args: argparse.Namespace) -> int:
    """冷连接版 check（原实现，作为回退路径保留）。"""
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


def _run_in_context(reader: "FrameReader", states: dict[str, int], key: str,
                    code: str, timeout: float) -> tuple[int, list[str]]:
    """在指定状态 VM 执行，返回 (退出码, 输出行)。"""
    idx = resolve_state(states, key)
    if idx is None:
        return 1, [f"[FAIL] 未找到状态 {key}。若在主菜单请先读档进对局。"
                   + suggest_states(states, key)]
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


def _daemon_exec(args: argparse.Namespace, code: str) -> dict | None:
    """把 exec/both 转成一条守护进程请求。"""
    payload = {
        "op": "both" if args.both else "exec",
        "code": code,
        "timeout": args.timeout,
    }
    if getattr(args, "state", None):
        payload["state"] = args.state
    else:
        payload["context"] = getattr(args, "context", "gamecore")
    resp, spawned = daemon_call(args, payload, args.timeout + 30.0)
    if resp is None:
        return None
    kind = (resp.get("error") or {}).get("kind")
    if int(resp.get("rc") or 0) != 0 and spawned and kind in ("connect", "closed"):
        _stop_daemon(_control_port(args))
    return resp


def _print_exec_result(resp: dict) -> int:
    rc = int(resp.get("rc") or 0)
    if resp.get("sections"):
        for sec in resp["sections"]:
            print(f"########## {sec['label']} ({sec['key']}) ##########")
            for ln in sec.get("lines") or []:
                print(ln)
            print()
        return rc
    if resp.get("ok"):
        for ln in resp.get("lines") or []:
            sys.stdout.write(ln + "\n")
        return rc
    if resp.get("lines"):
        for ln in resp["lines"]:
            sys.stderr.write(ln + "\n")
    err = resp.get("error") or {}
    msg = err.get("message") or "未知错误"
    tag = {"lua": "[LUA ERROR]", "timeout": "[TIMEOUT]",
           "closed": "[CLOSED]", "state_missing": "[FAIL]"}.get(err.get("kind"), "[FAIL]")
    print(f"{tag} {msg}", file=sys.stderr)
    return rc or 1


def cmd_exec(args: argparse.Namespace) -> int:
    """执行 Lua。默认经守护进程；--no-daemon 时冷连接直连。"""
    code = _load_code(args)
    if code is None:
        return 1
    if getattr(args, "tag", None):
        code = ('print("TUNER|op=' + args.tag + '|begin|turn=" .. Game.GetCurrentGameTurn())\n') + code
    if not getattr(args, "no_daemon", False):
        resp = _daemon_exec(args, code)
        if resp is not None:
            return _print_exec_result(resp)
        print("[WARN] 守护进程不可用，回退直连 FireTuner", file=sys.stderr)
    else:
        _stop_daemon(_control_port(args))
    return _cold_exec(args, code)


def _cold_exec(args: argparse.Namespace, code: str) -> int:
    """冷连接版 exec（原实现，作为回退路径保留）。"""
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


def cmd_daemon(args: argparse.Namespace) -> int:
    """查询或停止会话守护进程（不触发拉起）。"""
    port = _control_port(args)
    if not _ping(port):
        print("[OFF] 守护进程未运行")
        return 0
    try:
        resp = _request(port, {"op": "stop" if args.action == "stop" else "status"}, 5.0)
    except (OSError, ValueError) as e:
        print(f"[FAIL] 守护进程通信失败：{e}")
        return 1
    meta = resp.get("meta") or {}
    if args.action == "stop":
        print("[OK] 已通知守护进程退出")
        return 0
    if args.json:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0
    idle_limit = float(meta.get("idle_limit") or 0)
    print(f"[ON] pid={meta.get('pid')} port={meta.get('port')} "
          f"uptime={meta.get('uptime')}s idle={meta.get('idle_for')}s/{idle_limit:.0f}s")
    conn = (f"已连接 {meta.get('identity')}" if meta.get("connected") else "未连接")
    print(f"     游戏：{conn}（代际 {meta.get('generation')}，"
          f"对局 {'是' if meta.get('in_game') else '否'}）")
    if meta.get("last_error"):
        print(f"     最近错误：{meta['last_error']}")
    return 0


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
def _hoist_globals(argv: list[str]) -> list[str]:
    """把 --no-daemon / --daemon-port 提到子命令之前，两种写法都接受。"""
    head: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(argv):
        cur = argv[i]
        if cur == "--no-daemon":
            head.append(cur)
            i += 1
        elif cur == "--daemon-port" and i + 1 < len(argv):
            head.extend([cur, argv[i + 1]])
            i += 2
        elif cur.startswith("--daemon-port="):
            head.append(cur)
            i += 1
        else:
            rest.append(cur)
            i += 1
    return head + rest


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="tuner_exec.py",
        description="文明6 FireTuner 调试接口测试工具（详见 SKILL.md）",
    )
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-daemon", action="store_true",
                    help="不走会话守护进程，冷连接直连 FireTuner（回退路径）")
    ap.add_argument("--daemon-port", type=int, default=None,
                    help=f"守护进程控制端口，默认 {DAEMON_PORT}（也可用 CIV6_TUNER_DAEMON_PORT）")

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

    p_daemon = sub.add_parser("daemon", help="查询或停止会话守护进程（不会主动拉起）")
    p_daemon.add_argument("action", choices=["status", "stop"])
    p_daemon.add_argument("--json", action="store_true", help="status 输出原始 meta JSON")
    p_daemon.set_defaults(func=cmd_daemon)

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

    argv = _hoist_globals(sys.argv[1:])
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
