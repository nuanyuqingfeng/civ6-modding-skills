# -*- coding: utf-8 -*-
"""Lua 跨上下文体检 —— 找出「在另一个 Lua 上下文里根本调用不到」的写法。

规则真源：reference/context-matrix.md

上下文口径（2026-09-26 FireTuner 实测，见真源第五节）：
  · 每个 UI 上下文、每个 GamePlay 脚本都是独立的 Lua 状态，全局互不可见
  · 端内跨上下文只有 LuaEvents；跨端只有 EXECUTE_SCRIPT（UI→GP）、
    ReportingEvents.SendLuaEvent（GP→UI 推送）、PROPERTY 读取（双向）
  · include 的每个包含者各持一份副本，运行期改写不传播

「某个 .lua 属于哪一端」的判定（决定 C4 是否误报的关键）：
  · 角色 ① UI 上下文脚本 → UI 端
  · 角色 ③ GamePlay 脚本 → GP 端
  · 角色 ② include 共享库 → **本身没有端**，端由包含者决定，沿 include 反向边逐层向上求并集
  · 官方脚本替代件（<官方名>_<后缀>.lua，工程内没有被谁 include）→ 端 = 官方同名文件的端；
    在游戏本体的 Base\\Assets\\UI 下能查到同名文件即为 UI 端
  · 求不出端的文件 → C4 不判定（宁可漏报，不制造假阳性）

检查项：
  C1  UI 角色文件出现 GameEvents                        → 整条 nil，改到 GP 侧注册
  C2  UI 角色文件出现 SetProperty(                      → UI 侧无此端口，走 EXECUTE_SCRIPT
  C3  UI 角色文件调用 ReportingEvents.SendLuaEvent      → 端内广播应用 LuaEvents
  C4  一个 LuaEvents 事件的两端集合不相交                → 跨端不达
  C5  被调用的全局函数有定义，但定义点不在本文件的 include 闭包内 → 调用不到
  C6  出现 ExposedMembers                               → 报告使用点，需会话授权

豁免：写注释 -- context-check: allow <编号> <原因> 在对应那一行；
      整数常量的 SetProperty（SetProperty(key, 1)）属于引擎输入输出，不计入 C5。
      脚本在末尾列出全部豁免行，不静默跳过。

用法：
    python check_lua_context.py <工程根目录>

退出码：0 = 未发现问题；1 = 发现可疑项；2 = 参数/文件错误。
"""
import argparse
import os
import re
import sys

import _lua_roles as R

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MATRIX = "reference/context-matrix.md"

END_UI = "UI"
END_GP = "GP"

SKIP_DIRS = {".git", "workspace", "__pycache__", "_prev_mods", "node_modules", "Cooked"}

KEYWORDS = {
    "if", "while", "for", "return", "and", "or", "not", "else", "elseif", "end",
    "then", "do", "function", "local", "in", "repeat", "until", "break", "nil",
    "true", "false", "type", "tostring", "tonumber", "print", "pairs", "ipairs",
    "assert", "error", "pcall", "setmetatable", "rawget", "rawset", "string",
    "table", "math", "os", "io", "select", "unpack", "next",
}

RE_DEF_FUNC = re.compile(r"(?:^|\s)function\s+([A-Za-z_]\w*)\s*\(")
RE_DEF_ASSIGN = re.compile(r"(?:^|[^\w.:])([A-Za-z_]\w*)\s*=\s*function\s*\(")
RE_CALL = re.compile(r"(?<![\w.:])([A-Za-z_]\w*)\s*\(")
RE_EVT_ADD = re.compile(r"LuaEvents\.([A-Za-z_]\w*)\s*\.\s*Add\s*\(")
RE_EVT_REMOVE = re.compile(r"LuaEvents\.([A-Za-z_]\w*)\s*\.\s*Remove\s*\(")
RE_EVT_FIRE = re.compile(r"LuaEvents\.([A-Za-z_]\w*)\s*\(")
RE_INCLUDE = re.compile(r'include\s*\(\s*"([^"]+)"')
RE_SENDLUA = re.compile(r"ReportingEvents\s*\.\s*SendLuaEvent")
RE_SETPROP = re.compile(r"[.:]\s*SetProperty\s*\(")
RE_GAMEEVENTS = re.compile(r"\bGameEvents\b")
RE_EXPOSED = re.compile(r"\bExposedMembers\b")
RE_ALLOW = re.compile(r"context-check:\s*allow\s+(C\d)")
RE_INT_ARG = re.compile(r"SetProperty\s*\([^,]+,\s*-?\d+\s*\)")
RE_LOCAL = re.compile(r"\blocal\s+([A-Za-z_]\w*)")
RE_FUNC_PARAMS = re.compile(r"function\s*[\w.:]*\s*\(([^)]*)\)")
RE_FOR_VARS = re.compile(r"\bfor\s+([^=]+?)\s*(?:=|\bin\b)")

OFFICIAL_UI_ROOT = os.path.join("Base", "Assets", "UI")


def strip_comment(line):
    """去掉行尾注释，保留字符串字面量内部的 -- 。"""
    out = []
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == "\\":
                if i + 1 < len(line):
                    out.append(line[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        else:
            if ch in ("'", '"'):
                quote = ch
                out.append(ch)
            elif ch == "-" and i + 1 < len(line) and line[i + 1] == "-":
                break
            else:
                out.append(ch)
        i += 1
    return "".join(out)


def local_names(text):
    """本文件里声明为 local 或形参的名字 —— 这些不是跨文件全局，C5 必须排除。"""
    names = set()
    for line in text.splitlines():
        code = strip_comment(line)
        for m in RE_LOCAL.finditer(code):
            names.add(m.group(1))
        for m in RE_FUNC_PARAMS.finditer(code):
            for part in m.group(1).split(","):
                part = part.strip().rstrip(":")
                if re.fullmatch(r"[A-Za-z_]\w*", part):
                    names.add(part)
        for m in RE_FOR_VARS.finditer(code):
            for part in m.group(1).split(","):
                part = part.strip()
                if re.fullmatch(r"[A-Za-z_]\w*", part):
                    names.add(part)
    return names


def index_by_stem(rels):
    idx = {}
    for rel in rels:
        if rel.lower().endswith(".lua"):
            idx.setdefault(os.path.basename(rel)[:-4], []).append(rel)
    return idx


def resolve_include(spec, stem_idx):
    """把 include 参数解析成工程内相对路径列表（支持通配写法 include("前缀_", true)）。"""
    if spec.endswith("_"):
        return sorted(r for s, rs in stem_idx.items() if s.startswith(spec) for r in rs)
    for key in (spec, os.path.basename(spec)):
        if key in stem_idx:
            return list(stem_idx[key])
    return []


def closure(rel, include_edges, seen=None):
    """本文件的 include 闭包：自己 + 全部可达的 include 目标。"""
    if seen is None:
        seen = set()
    if rel in seen:
        return seen
    seen.add(rel)
    for nxt in include_edges.get(rel, ()):
        closure(nxt, include_edges, seen)
    return seen


def find_official_ui(stem):
    """在游戏本体 Base\\Assets\\UI 下按文件名找官方同名 .lua（找得到 = 它是 UI 端上下文）。"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "tools"))
        import _paths
        game = _paths.get("game")
    except Exception:
        return False
    if not game:
        return False
    root = os.path.join(game, OFFICIAL_UI_ROOT)
    if not os.path.isdir(root):
        return False
    target = stem + ".lua"
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in ("binaries", "maps", "scenarios")]
        if target in filenames:
            return True
    return False


def official_override_end(rel):
    """官方脚本替代件（<官方名>_<后缀>.lua）的端：官方同名文件在 Base\\Assets\\UI 里就判 UI。"""
    base = os.path.basename(rel)[:-4]
    for stem in sorted(R.OFFICIAL_STEMS, key=len, reverse=True):
        if base.startswith(stem + "_"):
            return END_UI if find_official_ui(stem) else None
    return None


def compute_ends(roles, include_edges, sources):
    """端集合：角色 ①→UI、③→GP；角色 ② 由包含者向上求并集；官方替代件查游戏本体。"""
    ends = {}
    for rel in sources:
        role = roles.get(rel, R.ROLE_UNKNOWN)
        if role == R.ROLE_UI_CONTEXT:
            ends[rel] = {END_UI}
        elif role == R.ROLE_GAMEPLAY:
            ends[rel] = {END_GP}

    includers = {}
    for src, targets in include_edges.items():
        for tgt in targets:
            includers.setdefault(tgt, set()).add(src)

    changed = True
    while changed:
        changed = False
        for rel in sources:
            if rel in ends:
                continue
            acc = set()
            for inc in includers.get(rel, ()):
                acc |= ends.get(inc, set())
            if acc:
                ends[rel] = acc
                changed = True

    for rel in sources:
        if rel not in ends:
            oe = official_override_end(rel)
            if oe:
                ends[rel] = {oe}
    return ends


def main():
    ap = argparse.ArgumentParser(description="Lua 跨上下文体检")
    ap.add_argument("root", help="工程根目录（含 .civ6proj）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: 目录不存在: %s" % root)
        return 2
    loaded = R.load_project(root)
    if loaded is None:
        print("ERROR: 目录下没有 .civ6proj: %s" % root)
        return 2
    pj, actions, content, content_set, luas = loaded

    all_lua = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.lower().endswith(".lua"):
                all_lua.append(R.norm(os.path.relpath(os.path.join(dirpath, fn), root)))
    all_lua = sorted(set(all_lua))
    stem_idx = index_by_stem(all_lua)

    roles, sources = {}, {}
    for rel in all_lua:
        role, _bad, _why = R.classify(rel, content_set, actions, root)
        roles[rel] = role
        text = R.read_lua(root, rel)
        if text is not None:
            sources[rel] = text

    include_edges = {}
    for rel, text in sources.items():
        edges = []
        for spec in RE_INCLUDE.findall(text):
            edges.extend(resolve_include(spec, stem_idx))
        include_edges[rel] = sorted(set(e for e in edges if e != rel))

    ends = compute_ends(roles, include_edges, sources)

    defs = {}
    for rel, text in sources.items():
        for rx in (RE_DEF_FUNC, RE_DEF_ASSIGN):
            for m in rx.finditer(text):
                defs.setdefault(m.group(1), set()).add(rel)

    findings, allows = [], []
    evt_reg, evt_fire = {}, {}

    for rel, text in sorted(sources.items()):
        role = roles[rel]
        lines = text.splitlines()
        code_lines = [strip_comment(l) for l in lines]
        clo = closure(rel, include_edges)
        locals_here = local_names(text)

        if role == R.ROLE_UI_CONTEXT:
            for i, line in enumerate(code_lines):
                if RE_GAMEEVENTS.search(line):
                    findings.append((rel, i + 1, "C1",
                                     "UI 上下文里出现 GameEvents（整条为 nil，其后语句全部不执行）"))
                if RE_SETPROP.search(line):
                    findings.append((rel, i + 1, "C2",
                                     "UI 上下文里调用 SetProperty（UI 侧无此端口）"))
                if RE_SENDLUA.search(line):
                    findings.append((rel, i + 1, "C3",
                                     "UI 上下文里调用 ReportingEvents.SendLuaEvent（端内广播应用 LuaEvents）"))

        for i, line in enumerate(code_lines):
            if RE_EXPOSED.search(line):
                findings.append((rel, i + 1, "C6",
                                 "使用 ExposedMembers（暴露函数，按 context-matrix 第三条第 9 行的口径处理）"))
            for evt in RE_EVT_ADD.findall(line) + RE_EVT_REMOVE.findall(line):
                evt_reg.setdefault(evt, set()).add(rel)
            for m in RE_EVT_FIRE.finditer(line):
                if line[m.end():].startswith("."):
                    continue
                evt_fire.setdefault(m.group(1), set()).add(rel)

        for i, line in enumerate(code_lines):
            if RE_INT_ARG.search(line):
                continue
            for m in RE_CALL.finditer(line):
                name = m.group(1)
                if name in KEYWORDS or name in locals_here:
                    continue
                if RE_DEF_FUNC.match(line[max(0, m.start() - 24):]):
                    continue
                owners = defs.get(name)
                if not owners or (owners & clo):
                    continue
                findings.append((rel, i + 1, "C5",
                                 "调用 %s()，其定义在 %s，不在本文件的 include 闭包内 → 该上下文里为 nil"
                                 % (name, ", ".join(sorted(owners)[:3]))))

        for i, line in enumerate(lines):
            m = RE_ALLOW.search(line)
            if m:
                allows.append((rel, i + 1, m.group(1), line.strip()))

    for evt, fire_files in sorted(evt_fire.items()):
        reg_files = evt_reg.get(evt, set())
        if not reg_files:
            continue
        fire_ends = set()
        reg_ends = set()
        unknown = False
        for rel in fire_files:
            e = ends.get(rel)
            if e is None:
                unknown = True
            fire_ends |= e or set()
        for rel in reg_files:
            e = ends.get(rel)
            if e is None:
                unknown = True
            reg_ends |= e or set()
        if unknown or not fire_ends or not reg_ends or (fire_ends & reg_ends):
            continue
        for rel in sorted(fire_files):
            text = sources[rel]
            for i, line in enumerate(text.splitlines()):
                code = strip_comment(line)
                for m in RE_EVT_FIRE.finditer(code):
                    if code[m.end():].startswith(".") or m.group(1) != evt:
                        continue
                    findings.append((rel, i + 1, "C4",
                                     "在本端（%s）触发 LuaEvents.%s，注册只在另一端（%s）→ 跨端不达"
                                     % ("/".join(sorted(ends.get(rel, {"?"}))),
                                        evt, "/".join(sorted(reg_ends)))))

    allowed_keys = {(r, l, c) for r, l, c, _ in allows}
    kept = [f for f in findings if (f[0], f[1], f[2]) not in allowed_keys]

    print("=" * 78)
    print("%s   扫描 .lua %d 个（UI 上下文 %d / include 库 %d / GamePlay %d）"
          % (pj, len(sources),
             sum(1 for r in roles.values() if r == R.ROLE_UI_CONTEXT),
             sum(1 for r in roles.values() if r == R.ROLE_INCLUDE_LIB),
             sum(1 for r in roles.values() if r == R.ROLE_GAMEPLAY)))
    print("=" * 78)

    for rel, ln, code, msg in sorted(kept):
        print("  %s:%d: %s [%s] → 见 %s" % (rel, ln, code, msg, MATRIX))
    if not kept:
        print("  ✓ 未发现跨上下文问题")

    if allows:
        print()
        print("  豁免（人工确认，非静默跳过）:")
        for rel, ln, code, raw in allows:
            print("    %s:%d  %s" % (rel, ln, raw))

    print()
    print("问题数: %d / 豁免数: %d" % (len(kept), len(allows)))
    return 1 if kept else 0


if __name__ == "__main__":
    sys.exit(main())
