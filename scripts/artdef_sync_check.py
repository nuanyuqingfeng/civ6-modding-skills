#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""artdef_sync_check.py —— ArtDef 源文件 vs Mods 副本「差异性质」判定器

解决的问题
----------
ModBuddy 的 cook 会重写 artdef（行尾 LF 化、自闭合收紧、抹缩进/空行、剥注释、
补 RootCollections 结构），并把解析不到的引用清成默认值（`_MissingArt` / 空）。
结果是**源文件与游戏加载的副本必然不同**，于是「双端不一致」这个信号既吵又没信息量。

本工具把一维的「相同/不同」升级为**分级判定**，把「纯编码噪声」与「真实缺陷」分开：

    L0 字节相同            → 完全一致
    L1 统一行尾后相同       → 纯 CRLF/LF 差异              ← 可忽略
    L2 再收紧自闭合后相同   → <x /> vs <x/>                ← 可忽略
    L3 再抹缩进后相同       → 缩进差异                     ← 可忽略
    L4 再删空行后相同       → 空行差异                     ← 可忽略
    L5 再剥注释后相同       → XML 注释被 cook 剥离          ← 可忽略
    以上都不相同           → 语义层差异，需人工判断：
                              · cook 补结构（无害但永久）
                              · 引用被清空（★ 真实缺陷信号）

用法
----
    # 单个工程（工程名，自动在 src-root 下找 <名>/ArtDefs 或 <名>/<名>/ArtDefs）
    python artdef_sync_check.py 示例工程

    # 直接给 ArtDefs 目录
    python artdef_sync_check.py "D:/.../示例工程/示例工程/ArtDefs" --name 示例工程

    # 扫描 src-root 下全部工程
    python artdef_sync_check.py --all

    # 覆盖根目录（默认从本机已知位置推断，可用参数或环境变量覆盖）
    python artdef_sync_check.py --all --src-root "D:/.../Firaxis ModBuddy/Civilization VI" \
                                      --mods-root "D:/.../My Games/Sid Meier's Civilization VI/Mods"

退出码：0 = 只有编码层差异（或完全一致）；1 = 存在语义层差异或文件增删（需人工看）。

不改任何文件，只读+报告。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

# ---------------------------------------------------------------- 归一化分级

def _eol(d: bytes) -> bytes:
    return d.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

def _tight(d: bytes) -> bytes:
    """把自闭合标签里的多余空白去掉：`<x />` / `<x a="b" />` → `<x/>` / `<x a="b"/>`。

    注意：不能用 `<([A-Za-z_][^\\s>/]*)\\s+/>` 这种"标签名后紧跟空白"的正则 ——
    它跨越不了属性里的空格，只能处理无属性空元素，会把大量带属性的自闭合判成
    "内容不同"（假阳性）。
    """
    return re.sub(rb"\s+/>", b"/>", d)

def _strip_lines(d: bytes) -> bytes:
    return b"\n".join(l.strip() for l in d.split(b"\n"))

def _drop_blank(d: bytes) -> bytes:
    return b"\n".join(l for l in d.split(b"\n") if l.strip())

def _strip_comments(d: bytes) -> bytes:
    return re.sub(rb"<!--.*?-->", b"", d, flags=re.S)

# 每个级别的「累积变换」
LEVELS = [
    ("L0", "字节相同",              []),
    ("L1", "仅行尾差异",            [_eol]),
    ("L2", "行尾+自闭合写法",        [_eol, _tight]),
    ("L3", "行尾+写法+缩进",         [_eol, _tight, _strip_lines]),
    ("L4", "行尾+写法+缩进+空行",     [_eol, _tight, _strip_lines, _drop_blank]),
    ("L5", "行尾+写法+缩进+空行+注释", [_eol, _tight, _strip_comments, _strip_lines, _drop_blank]),
]

def normalize(data: bytes, idx: int) -> bytes:
    for fn in LEVELS[idx][2]:
        data = fn(data)
    return data

# ---------------------------------------------------------------- 语义层定性

RE_EMPTY_TEXT = re.compile(r'text=""\s*/>')
RE_STRUCT_ADD = re.compile(r'^<(m_RootCollections|/m_RootCollections|Element|/Element)>$')
RE_COLLNAME = re.compile(r'^<m_CollectionName ')

def _count_empty(lines) -> int:
    return sum(1 for l in lines if 'text=""' in l)

def classify_semantic(src: bytes, dst: bytes) -> dict:
    """把「L5 仍不同」的差异定性。只做启发式分类，结论仍需人工确认。"""
    a_all = [l for l in normalize(src, 5).decode("utf-8", "replace").split("\n") if l.strip()]
    b_all = [l for l in normalize(dst, 5).decode("utf-8", "replace").split("\n") if l.strip()]
    sa, sb = set(a_all), set(b_all)
    only_src = [l for l in a_all if l not in sb]     # 产物里被改写/丢弃
    only_dst = [l for l in b_all if l not in sa]     # cook 新增

    # 计数差：产物把值清成 text="" 时，那行往往在源里别处也存在，
    # 集合差集看不见 → 必须用「空值行数的增量」判定。
    empty_delta = _count_empty(b_all) - _count_empty(a_all)

    wiped = [l for l in only_dst if RE_EMPTY_TEXT.search(l)]
    missing_art = [l for l in only_dst if "_MissingArt" in l]
    struct = [l for l in only_dst if RE_STRUCT_ADD.match(l.strip()) or RE_COLLNAME.match(l.strip())]
    other_dst = [l for l in only_dst if l not in wiped + missing_art + struct]
    src_lost = [l for l in only_src if not RE_EMPTY_TEXT.search(l)]

    if missing_art:
        kind = "引用被清空→_MissingArt（artdef 条目找不到）"
    elif empty_delta > 0 or (wiped and src_lost):
        kind = f"引用被清空→空值（{len(src_lost)} 处源值在产物中变空）"
    elif struct and not src_lost:
        kind = "cook 补结构（无害但永久）"
    elif struct:
        kind = "补结构 + 引用被清空（混合）"
    else:
        kind = "其它（需人工看）"
    return {
        "kind": kind,
        "empty_delta": empty_delta,
        "only_src": only_src, "only_dst": only_dst,
        "wiped": wiped, "missing_art": missing_art, "struct": struct,
        "other_dst": other_dst, "src_lost": src_lost,
    }

# ---------------------------------------------------------------- 路径解析

DEFAULT_SRC_ROOT = r"D:\documents\Firaxis ModBuddy\Civilization VI"

# 本机路径不统一（有的机器 Documents 在 C:，有的在 D:），所以用「候选列表 + 首个存在者」。
_SRC_CANDIDATES = [
    DEFAULT_SRC_ROOT,
    os.path.join(os.path.expanduser("~"), "Documents", "Firaxis ModBuddy", "Civilization VI"),
    r"D:\documents\Firaxis ModBuddy\Civilization VI",
]
_MODS_CANDIDATES = [
    r"D:\documents\My Games\Sid Meier's Civilization VI\Mods",
    os.path.join(os.path.expanduser("~"), "Documents", "My Games",
                 "Sid Meier's Civilization VI", "Mods"),
    os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "My Games",
                 "Sid Meier's Civilization VI", "Mods"),
]

def _first_existing(paths, env_key):
    v = os.environ.get(env_key)
    if v:
        return v
    for p in paths:
        if os.path.isdir(p):
            return p
    return paths[0]

def resolve_src_artdefs(name: str, src_root: str) -> str | None:
    for cand in (os.path.join(src_root, name, "ArtDefs"),
                 os.path.join(src_root, name, name, "ArtDefs")):
        if os.path.isdir(cand):
            return cand
    hits = glob.glob(os.path.join(src_root, name, "**", "ArtDefs"), recursive=True)
    return hits[0] if hits else None

def list_projects(src_root: str) -> list[str]:
    if not os.path.isdir(src_root):
        return []
    out = []
    for d in sorted(os.listdir(src_root)):
        if os.path.isdir(os.path.join(src_root, d)) and resolve_src_artdefs(d, src_root):
            out.append(d)
    return out

# ---------------------------------------------------------------- 主流程

def check_one(name, src_dir, mods_dir, detail, emit, only=None) -> dict:
    res = {"name": name, "src": src_dir, "mods": mods_dir,
           "files": [], "verdict": "unknown"}
    if not os.path.isdir(mods_dir):
        res["verdict"] = "mods 目录不存在"
        emit(f"  ⚠ Mods/ArtDefs 不存在：{mods_dir}")
        return res

    sn = {os.path.basename(p) for p in glob.glob(os.path.join(src_dir, "*.artdef"))}
    mn = {os.path.basename(p) for p in glob.glob(os.path.join(mods_dir, "*.artdef"))}
    if only:
        sn &= only
        mn &= only
    only_s, only_m = sorted(sn - mn), sorted(mn - sn)
    common = sorted(sn & mn)

    if only_s:
        emit(f"  ⚠ 仅源有（未同步到 Mods）：{only_s}")
        res["only_src"] = only_s
    if only_m:
        emit(f"  ⚠ 仅 Mods 有（疑似未回写源）：{only_m}")
        res["only_mods"] = only_m

    for n in common:
        sb = open(os.path.join(src_dir, n), "rb").read()
        db = open(os.path.join(mods_dir, n), "rb").read()
        lvl = None
        for i in range(len(LEVELS)):
            if normalize(sb, i) == normalize(db, i):
                lvl = i
                break
        if lvl is None:
            sem = classify_semantic(sb, db)
            rec = {"file": n, "level": None, "verdict": sem["kind"],
                   "only_src": len(sem["only_src"]), "only_dst": len(sem["only_dst"])}
            emit(f"  ✗ {n:<28} 语义层差异：{sem['kind']}")
            emit(f"      仅在源中 {len(sem['only_src'])} 行 / 仅在产物中 {len(sem['only_dst'])} 行")
            if detail:
                for l in sem["src_lost"][:detail]:
                    emit(f"        源丢失值 : {l.strip()[:120]}")
                for l in (sem["missing_art"] + sem["wiped"] + sem["struct"])[:detail]:
                    emit(f"        产物新增 : {l.strip()[:120]}")
        else:
            tag, label, _ = LEVELS[lvl]
            rec = {"file": n, "level": lvl, "verdict": label, "encoding_only": lvl <= 5}
            mark = "✓" if lvl == 0 else "·"
            emit(f"  {mark} {n:<28} {tag} {label}")
        res["files"].append(rec)

    enc = sum(1 for f in res["files"] if f.get("level") is not None)
    l0 = sum(1 for f in res["files"] if f.get("level") == 0)
    sem = sum(1 for f in res["files"] if f.get("level") is None)
    if not res["files"]:
        res["verdict"] = "无可比对文件"
    elif sem == 0 and not only_s and not only_m:
        if enc and l0 == enc:
            res["verdict"] = "完全一致（源即产物）"
        else:
            res["verdict"] = "仅编码层差异（可忽略）"
    elif sem == 0:
        res["verdict"] = "编码层差异 + 文件增删（需看增删）"
    else:
        res["verdict"] = f"★{sem} 个文件存在语义层差异（需人工判断）"
    return res

def main(argv=None) -> int:
    # Windows 控制台默认 GBK，打不出 ✓/★ 等符号 → 强制 UTF-8（失败也不致命）
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(
        description="ArtDef 源文件 vs Mods 副本「差异性质」判定器（只读）",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?",
                    help="工程名，或直接给 ArtDefs 目录")
    ap.add_argument("--all", action="store_true", help="扫描 src-root 下全部工程")
    ap.add_argument("--name", help="target 是目录时，指定其工程名（用于定位 Mods 侧）")
    ap.add_argument("--src-root",
                    default=_first_existing(_SRC_CANDIDATES, "CIV6_PROJ_ROOT"),
                    help="ModBuddy 工程根目录（默认自动探测，可用 CIV6_PROJ_ROOT 覆盖）")
    ap.add_argument("--mods-root",
                    default=_first_existing(_MODS_CANDIDATES, "CIV6_MODS_ROOT"),
                    help="游戏 Mods 目录（默认自动探测，可用 CIV6_MODS_ROOT 覆盖）")
    ap.add_argument("--only", help="只比对该文件（支持逗号分隔）")
    ap.add_argument("--detail", type=int, default=0,
                    help="语义层差异时，打印每侧最多 N 条样本行（默认 0）")
    ap.add_argument("--json", dest="json_out", help="把结果写入 JSON 文件")
    ap.add_argument("--report", help="把可读报告写入文件（默认同时打到 stdout）")
    args = ap.parse_args(argv)

    lines: list[str] = []
    def emit(s=""):
        lines.append(s)
        print(s)

    emit("=" * 100)
    emit("ArtDef 源 vs Mods 副本 —— 差异性质判定")
    emit(f"  src-root  : {args.src_root}")
    emit(f"  mods-root : {args.mods_root}")
    emit("=" * 100)

    if args.all:
        names = list_projects(args.src_root)
        if not names:
            emit(f"未在 {args.src_root} 下找到任何含 ArtDefs 的工程")
            return 1
    elif args.target:
        if os.path.isdir(args.target) and glob.glob(os.path.join(args.target, "*.artdef")):
            name = args.name or os.path.basename(os.path.dirname(args.target)) or "mod"
            names = [(name, args.target)]
        else:
            names = [args.target]
    else:
        ap.print_help()
        return 2

    results = []
    rc = 0
    only = {s.strip() for s in args.only.split(",")} if args.only else None
    for item in names:
        if isinstance(item, tuple):
            name, src_dir = item
        else:
            name = item
            src_dir = resolve_src_artdefs(name, args.src_root)
        emit("")
        emit(f"### {name}")
        if not src_dir:
            emit(f"  ✗ 找不到源 ArtDefs：{args.src_root}\\{name}")
            results.append({"name": name, "verdict": "源目录不存在"})
            rc = 1
            continue
        mods_dir = os.path.join(args.mods_root, name, "ArtDefs")
        r = check_one(name, src_dir, mods_dir, args.detail, emit, only)
        results.append(r)
        emit(f"  → {r['verdict']}")
        if r["verdict"].startswith("★") or "不存在" in r["verdict"]:
            rc = 1

    emit("")
    emit("=" * 100)
    emit("汇总")
    emit("=" * 100)
    for r in results:
        emit(f"  {r['name']:<30} {r.get('verdict','')}")
    emit("")
    emit("判读：L1–L5 全是编码层差异（行尾/自闭合写法/缩进/空行/注释），可以忽略；")
    emit("      若想彻底消除，把源 artdef 统一成 cook 规范写法（LF + `<x/>` 紧凑 + 无注释）。")
    emit("      语义层差异不是噪声：`_MissingArt` / 空值 = 引用找不到，是真实缺陷信号。")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"\n报告已写入 {args.report}")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"JSON 已写入 {args.json_out}")
    return rc

if __name__ == "__main__":
    sys.exit(main())
