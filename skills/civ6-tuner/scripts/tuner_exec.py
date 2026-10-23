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
# 组合动作层
# ---------------------------------------------------------------------------
ACTION_DIR = Path(__file__).resolve().parent.parent / "snippets" / "actions"
CONFIG_BEGIN = "-- ===== CONFIG ====="
CONFIG_END = "-- ==================="

# 动作名 -> 描述。参数表格式：键名 -> (默认值, 说明)。
# 默认值的类型决定命令行取值形态：bool 为开关，int 为整数，list 为逗号分隔，str 为文本。
ACTIONS: dict[str, dict] = {
    "game-mode": {
        "state": "MainMenu",
        "desc": "启用/关闭游戏模式（秘密结社、英雄、蛮族氏族等）",
        "params": {
            "MODES": ([], "启用的模式键名，逗号分隔，如 MODE_SECRET_SOCIETIES"),
            "ENABLE_ONLY": (False, "仅启用 MODES 列出的模式，其余全部关闭"),
        },
    },
    "leader": {
        "state": "MainMenu",
        "desc": "指定玩家槽位的领袖与文明（建局前）",
        "params": {
            "PLAYER_ID": (0, "玩家槽位编号"),
            "LEADER": ("", "领袖类型名，如 LEADER_CARTETHYIA_QYQXP"),
            "CIV": ("", "文明类型名，留空表示不改"),
            "PREPARE": (True, "先跑标准建局准备链（默认开启）"),
        },
    },
    "end-turn": {
        "context": "ingame",
        "desc": "结束回合并轮询回合推进",
        "post": "wait_turn",
        "params": {
            "FORCE": (False, "改发 REASON=UserForced，推过被阻塞的回合"),
            "BLOCKCHECK": (True, "先读回合阻塞项清单"),
            "TIMEOUT": (120, "等待回合推进的秒数"),
        },
    },
    "select-unit": {
        "context": "ingame",
        "desc": "按条件筛选并选中一个单位",
        "params": {
            "TYPE": ("", "单位类型名，如 UNIT_WARRIOR"),
            "X": (-1, "筛选该地块上的单位，-1 表示不按坐标筛选"),
            "Y": (-1, "配合 X 使用"),
            "RADIUS": (-1, "以本地玩家首都为中心的半径，-1 表示不按半径筛选"),
            "HP_THRESHOLD": (-1, "血量百分比上限（只选不高于该值的单位），-1 表示不筛选"),
            "PROMOTION": ("", "要求已获得该晋升类型名"),
        },
    },
    "build": {
        "context": "gamecore",
        "desc": "在指定城市建成一座建筑",
        "params": {
            "CITY": ("capital", "capital 或城市 ID"),
            "BUILDING": ("", "建筑类型名，如 BUILDING_MONUMENT"),
            "FORCE_PRECOST": (False, "缺科技/市政前置时补齐"),
        },
    },
    "gold-inject": {
        "context": "gamecore",
        "desc": "设定或增减金币",
        "params": {
            "AMOUNT": (0, "目标余额；--delta 时为增量"),
            "DELTA": (False, "以增量为语义"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "faith-inject": {
        "context": "gamecore",
        "desc": "设定或增减信仰值",
        "params": {
            "AMOUNT": (0, "目标余额；--delta 时为增量"),
            "DELTA": (False, "以增量为语义"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "tech-complete": {
        "context": "gamecore",
        "desc": "完成一项科技",
        "params": {
            "TECH": ("", "科技类型名，如 TECH_BRONZE_WORKING"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "civic-complete": {
        "context": "gamecore",
        "desc": "完成一项市政",
        "params": {
            "CIVIC": ("", "市政类型名，如 CIVIC_CODE_OF_LAWS"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "unit-spawn": {
        "context": "gamecore",
        "desc": "在地块刷单位（先校验地形）",
        "params": {
            "TYPE": ("", "单位类型名，如 UNIT_WARRIOR"),
            "X": (0, "地块横坐标"),
            "Y": (0, "地块纵坐标"),
            "COUNT": (1, "生成数量"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "terrain-change": {
        "context": "gamecore",
        "desc": "改地块地形与地貌",
        "params": {
            "X": (0, "地块横坐标"),
            "Y": (0, "地块纵坐标"),
            "TERRAIN": ("", "地形类型名，如 TERRAIN_GRASS，留空表示不改"),
            "FEATURE": ("", "地貌类型名，如 FEATURE_FLOODPLAINS，留空表示不改"),
        },
    },
    "fog-reveal": {
        "context": "gamecore",
        "desc": "揭示指定地块周围视野",
        "params": {
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
            "X": (0, "中心地块横坐标"),
            "Y": (0, "中心地块纵坐标"),
            "RADIUS": (3, "揭示半径（方形范围，六边形距离未实现）"),
        },
    },
    "snapshot": {
        "context": "gamecore",
        "desc": "全量状态快照（金/信仰/科技/市政/城市/单位）",
        "params": {
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "research-set": {
        "context": "ingame",
        "desc": "设定当前研究的科技",
        "params": {
            "TECH": ("", "科技类型名，如 TECH_POTTERY"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
        },
    },
    "civic-set": {
        "context": "ingame",
        "desc": "把某项市政设为当前推进目标",
        "params": {
            "CIVIC": ("", "市政类型名，如 CIVIC_FOREIGN_TRADE"),
            "PID": (-1, "玩家编号，-1 表示本地玩家"),
            "RETRY": (20, "回读轮询次数"),
        },
    },
    "city-build": {
        "context": "ingame",
        "desc": "把建筑、单位或区域加入城市生产队列",
        "post": "verify_queue",
        "params": {
            "CITY": ("capital", "capital 或城市 ID"),
            "BUILDING": ("", "建筑类型名，空表示不排建筑"),
            "UNIT": ("", "单位类型名，空表示不排单位"),
            "DISTRICT": ("", "区域类型名，空表示不排区域（须同时给 X/Y）"),
            "X": (-1, "区域放置地块横坐标，--district 时必填"),
            "Y": (-1, "区域放置地块纵坐标，--district 时必填"),
            "APPEND": (False, "追加到队尾；默认替换当前位置"),
            "RETRY": (20, "回读轮询次数"),
        },
    },
}


def _lua_value(value) -> str:
    """把 Python 取值渲染成 Lua 字面量。"""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "{" + ", ".join(_lua_value(v) for v in value) + "}"
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _coerce(key: str, default, raw: str):
    """按默认值类型解析命令行文本。"""
    if isinstance(default, bool):
        low = raw.strip().lower()
        if low in ("1", "true", "yes", "on"):
            return True
        if low in ("0", "false", "no", "off"):
            return False
        raise ValueError(f"参数 {key} 只接受 true/false，收到 {raw}")
    if isinstance(default, int):
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"参数 {key} 需要整数，收到 {raw}") from None
    if isinstance(default, list):
        return [s.strip() for s in raw.split(",") if s.strip()]
    return raw


def parse_action_args(name: str, argv: list[str]) -> dict:
    """解析动作参数：--key value / --key=value / bool 开关单独出现。"""
    spec = ACTIONS[name]["params"]
    values = {k: v[0] for k, v in spec.items()}
    i = 0
    while i < len(argv):
        cur = argv[i]
        if not cur.startswith("--"):
            raise ValueError(f"无法识别的参数 {cur}；参数一律以 -- 开头")
        key, _, inline = cur[2:].partition("=")
        key = key.replace("-", "_").upper()
        if key not in spec:
            raise ValueError(f"动作 {name} 没有参数 {key}；可用参数：{', '.join(spec)}")
        default = spec[key][0]
        if isinstance(default, bool) and inline == "":
            values[key] = True
            i += 1
            continue
        if inline == "":
            if i + 1 >= len(argv):
                raise ValueError(f"参数 {key} 缺少取值")
            inline = argv[i + 1]
            i += 2
        else:
            i += 1
        values[key] = _coerce(key, default, inline)
    return values


def config_block(spec: dict, values: dict) -> str:
    """生成 Lua 的 CONFIG 块（含起止标记行）。"""
    lines = [CONFIG_BEGIN, "local CONFIG = {"]
    for key, (_default, help_text) in spec.items():
        lines.append(f"    {key} = {_lua_value(values[key])},  -- {help_text}")
    lines.append("}")
    lines.append(CONFIG_END)
    return "\n".join(lines)


def replace_config_block(code: str, block: str) -> str:
    """用生成的 CONFIG 块替换片段里的标记区间。"""
    lines = code.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == CONFIG_BEGIN), None)
    if start is None:
        raise ValueError(f"Lua 片段缺少 {CONFIG_BEGIN} 标记行")
    end = next((i for i, ln in enumerate(lines)
                if i > start and ln.strip() == CONFIG_END), None)
    if end is None:
        raise ValueError(f"Lua 片段缺少 {CONFIG_END} 标记行")
    return "\n".join(lines[:start] + block.splitlines() + lines[end + 1:])


def _cold_run(args: argparse.Namespace, key: str, code: str,
              timeout: float) -> tuple[int, list[str]]:
    """冷连接执行一次，返回 (退出码, 输出行)，由调用方决定怎么打印。"""
    try:
        sock = connect(args.host, args.port)
    except OSError as e:
        return 1, [f"[FAIL] 无法连接 {args.host}:{args.port} —— {e}"]
    try:
        _identity, states = handshake(sock)
        return _run_in_context(sock, states, key, code, timeout)
    except LinkClosed as e:
        return 4, [f"[CLOSED] 握手中连接被对端关闭 —— {e}"]
    finally:
        sock.close()


def run_code(args: argparse.Namespace, code: str, timeout: float,
             context: str | None = None,
             state: str | None = None) -> tuple[int, list[str]]:
    """按守护进程优先、冷连接兜底的顺序执行一段 Lua，返回 (退出码, 输出行)。"""
    if not getattr(args, "no_daemon", False):
        ns = argparse.Namespace(**vars(args))
        ns.context, ns.state, ns.both, ns.timeout = context, state, False, timeout
        resp = _daemon_exec(ns, code)
        if resp is not None:
            return int(resp.get("rc") or 0), resp.get("lines") or []
        print("[WARN] 守护进程不可用，回退直连 FireTuner", file=sys.stderr)
    else:
        _stop_daemon(_control_port(args))
    key = state or ("GameCore_Tuner" if context == "gamecore" else "InGame")
    return _cold_run(args, key, code, timeout)


def _tag_int(lines: list[str], prefix: str) -> int | None:
    """从输出行里取形如 PREFIX=N 的整数。"""
    for ln in lines:
        if ln.startswith(prefix):
            try:
                return int(float(ln[len(prefix):]))
            except ValueError:
                return None
    return None


def _wait_turn_advance(args: argparse.Namespace, before: int, timeout: float) -> int:
    """轮询回合数直到推进；超时按退出码 3 返回。"""
    deadline = time.monotonic() + timeout
    code = 'print("TURN=" .. Game.GetCurrentGameTurn())'
    while time.monotonic() < deadline:
        time.sleep(3.0)
        rc, lines = run_code(args, code, 10.0, context="gamecore")
        if rc != 0:
            continue
        now = _tag_int(lines, "TURN=")
        if now is None:
            continue
        if now != before:
            print(f"[OK] 回合推进：{before} -> {now}")
            return 0
    print(f"[FAILURE] 回合未推进（仍为 {before}）：可能存在阻塞项（试 --force）或 AI 回合处理中")
    return 3


def _split_timeout(argv: list[str], default: float) -> tuple[list[str], float]:
    """把动作参数里的 --timeout 提出来：写在小节段超时。

    argparse 的 REMAINDER 会把动作名之后的一切（含 --timeout）都吞进 action_args，
    因此 `act end-turn --timeout 60` 这种自然写法必须在这里接住。
    """
    rest: list[str] = []
    timeout = default
    i = 0
    while i < len(argv):
        cur = argv[i]
        if cur == "--timeout":
            if i + 1 >= len(argv):
                raise ValueError("--timeout 缺少取值")
            timeout = float(argv[i + 1])
            i += 2
            continue
        if cur.startswith("--timeout="):
            timeout = float(cur.split("=", 1)[1])
            i += 1
            continue
        rest.append(cur)
        i += 1
    return rest, timeout


def _run_action(args: argparse.Namespace, name: str, values: dict,
                timeout: float) -> tuple[int, list[str]]:
    """按动作名读片段、注入 CONFIG 并投递，返回 (退出码, 输出行)。"""
    meta = ACTIONS[name]
    path = ACTION_DIR / f"{name}.lua"
    code = path.read_text(encoding="utf-8")
    code = replace_config_block(code, config_block(meta["params"], values))
    return run_code(args, code, timeout,
                    context=meta.get("context", "gamecore"),
                    state=meta.get("state"))


def _verify_queue(args: argparse.Namespace, expect: str, values: dict,
                  timeout: float) -> int:
    """city-build 的后置回读：在 gamecore 侧读城市当前生产项并与期望比对。

    CurrentlyBuilding 只在 gamecore 侧存在（ingame 侧为 nil），因此这一读必须
    单独投递；排队是异步结算，轮询到上限再判失败。
    """
    city_arg = values.get("CITY", "capital")
    code = (
        'local pid=Game.GetLocalPlayer();'
        'local city=nil;'
        'if "' + city_arg + '"=="capital" then '
        'city=Players[pid]:GetCities():GetCapitalCity() '
        'else '
        'for _,c in Players[pid]:GetCities():Members() do '
        'if c:GetID()==' + (city_arg if city_arg != "capital" else "0") + ' then city=c break end '
        'end end;'
        'if city==nil then print("NO_CITY") return end;'
        'print("VERIFY_QUEUE=" .. city:GetBuildQueue():CurrentlyBuilding())')
    for attempt in range(values.get("RETRY", 20)):
        rc, lines = run_code(args, code, timeout, context="gamecore")
        if rc != 0:
            print("[FAIL] 生产队列回读失败", file=sys.stderr)
            for ln in lines:
                print(ln, file=sys.stderr)
            return rc
        actual = None
        for ln in lines:
            if ln.startswith("VERIFY_QUEUE="):
                actual = ln[len("VERIFY_QUEUE="):]
        if actual is None:
            print("[FAIL] 回读输出缺少 VERIFY_QUEUE", file=sys.stderr)
            for ln in lines:
                print(ln, file=sys.stderr)
            return 1
        if actual == expect:
            print(f"VERIFY_QUEUE={actual}")
            print("FINAL=OK")
            return 0
        time.sleep(0.2)
    print(f"VERIFY_QUEUE={actual}")
    print(f"FINAL=FAIL|queue_mismatch|expect={expect}|actual={actual}")
    return 2


def cmd_act(args: argparse.Namespace) -> int:
    """执行组合动作：读片段、注入 CONFIG、投递并做后置编排。"""
    if args.action in ("list", "--list"):
        for name, meta in ACTIONS.items():
            where = meta.get("state") or meta.get("context", "gamecore")
            print(f"{name:<16} [{where}] {meta['desc']}")
        return 0
    meta = ACTIONS.get(args.action)
    if meta is None:
        print(f"[FAIL] 未定义的动作 {args.action}；可用：{', '.join(ACTIONS)}", file=sys.stderr)
        return 1
    try:
        action_args, args.timeout = _split_timeout(args.action_args, args.timeout)
        values = parse_action_args(args.action, action_args)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    print(f"[..] act {args.action}：{' '.join(args.action_args) or '<无参数>'}")
    rc, lines = _run_action(args, args.action, values, args.timeout)
    for ln in lines:
        print(ln)

    if rc != 0:
        return rc

    if any(ln.startswith("FINAL=FAIL") for ln in lines):
        return 2

    if meta.get("post") == "verify_queue":
        expect = None
        for ln in lines:
            if ln.startswith("EXPECT_QUEUE="):
                expect = ln[len("EXPECT_QUEUE="):]
        if expect is None:
            print("[FAIL] 输出缺少 EXPECT_QUEUE，无法判定生产队列", file=sys.stderr)
            return 1
        return _verify_queue(args, expect, values, args.timeout)

    if meta.get("post") == "wait_turn":
        before = _tag_int(lines, "TURN_BEFORE=")
        if before is None:
            print("[FAIL] 输出缺少 TURN_BEFORE，无法判定回合推进", file=sys.stderr)
            return 1
        return _wait_turn_advance(args, before, values.get("TIMEOUT", args.timeout))
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

    p_act = sub.add_parser("act", help="执行组合动作（多步编排，见 act list）")
    p_act.add_argument("--timeout", type=float, default=20.0,
                       help="段落收集超时秒数，默认 20（写在动作名之后同样可用）")
    p_act.add_argument("action", help="动作名；用 list 列出全部动作")
    p_act.add_argument("action_args", nargs=argparse.REMAINDER,
                       help="动作参数，形如 --amount 10000")
    p_act.set_defaults(func=cmd_act)

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
