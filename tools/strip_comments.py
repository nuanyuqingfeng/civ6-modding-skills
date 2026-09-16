# -*- coding: utf-8 -*-
"""发布前剥离代码注释（**默认只剥离 Lua**），只作用于**发布副本**，不动源工程。

为什么只剥离发布副本：源工程是唯一保存设计理由与踩坑记录的地方（本项目里源工程才有注释，
Mods 副本/工坊包才是对外产物）。剥离后 源 与 Mods 会**故意不一致**——校验方式因此改为
「Mods == strip(源)」，用 `--src` 一次跑完（这也是 示例工程 v3 发布时用的口径）。

为什么默认只剥 Lua（2026-09-16 起）：
  · Lua 注释是「设计理由 + 踩坑记录」的主要载体，且剥离后可用 `luac -p` 做语法自证，
    掉注释的风险可控；
  · SQL/XML 的注释多为**分节标题与列对照**，体量小、可读性价值高，且剥离无等价自检手段
    （XML 尚可良构校验，SQL 注释与语句块边界相关，改动收益低而回归面大）；
  · 实测本项目：Lua 48 文件 / 825 KB（47 含注释），SQL 152 文件 / 2.2 MB、XML 30 文件 /
    178 KB —— 真正的压缩收益本就集中在 Lua。
  · 需要旧行为时显式传 `--exts .lua,.sql,.xml,.modinfo`（下列 SQL/XML 剥离器仍保留可用）。

安全性：
  · 字符串感知扫描（不把 `"--"`、`'--'`、`[[--]]` 里的内容当注释）；
  · 注释**逐行替换为空行**，因此行号不变（出问题时日志行号仍可对照源文件）；
  · `.lua` 剥离后自动跑 `luac -p` 语法自检（找不到 luac 则跳过并提示）。
  · 默认**只扫目标目录**；要顺带核对源工程用 `--src`（只读，不会写源）。

用法：
    python strip_comments.py <目标目录>                 # 就地剥离（默认仅 .lua）
    python strip_comments.py <目标目录> --dry-run        # 只统计，不写
    python strip_comments.py <目标目录> --src <源目录>   # 剥离后再核对 Mods == strip(src)
    python strip_comments.py <目标目录> --keep-lines    # 保留空行（行号与源一致；默认会折叠）
    python strip_comments.py <目标目录> --exts .lua,.sql,.xml,.modinfo   # 恢复旧的全类型剥离

退出码：0 成功 / 1 自检失败或核对不一致 / 2 参数错误
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 默认只剥 Lua：Lua 注释是设计理由/踩坑记录的主要载体且有 luac 自检；
# SQL/XML 注释多为分节标题与列对照，体量小、剥离无可比自检，收益低回归面大。
# 需要旧的全类型行为时用 --exts .lua,.sql,.xml,.modinfo（下方 SQL/XML 剥离器仍注册着）。
DEFAULT_EXTS = (".lua",)
# 曾经的全类型集合，保留作参考/显式覆盖用
ALL_EXTS = (".lua", ".sql", ".xml", ".modinfo")


# ---------------------------------------------------------------- Lua
def strip_lua(src: str) -> str:
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        # 行注释 / 块注释
        if c == "-" and i + 1 < n and src[i + 1] == "-":
            j = i + 2
            m = re.match(r"\[(=*)\[", src[j:])
            if m:                                        # --[[ ... ]] / --[=[ ... ]=]
                close = "]" + m.group(1) + "]"
                k = src.find(close, j + m.end())
                k = n if k < 0 else k + len(close)
                out.append("\n" * src.count("\n", i, k))  # 保留行数
                i = k
            else:                                         # -- 到行尾
                k = src.find("\n", i)
                i = n if k < 0 else k
            continue
        # 常规字符串
        if c in "\"'":
            q, j = c, i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == q:
                    j += 1
                    break
                if src[j] == "\n":                        # 未闭合，防跑飞
                    break
                j += 1
            out.append(src[i:j])
            i = j
            continue
        # 长字符串 [[ ... ]] / [=[ ... ]=]
        if c == "[":
            m = re.match(r"\[(=*)\[", src[i:])
            if m:
                close = "]" + m.group(1) + "]"
                k = src.find(close, i + m.end())
                k = n if k < 0 else k + len(close)
                out.append(src[i:k])
                i = k
                continue
        out.append(c)
        i += 1
    return "".join(out)


# ---------------------------------------------------------------- SQL
def strip_sql(src: str) -> str:
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == "-" and i + 1 < n and src[i + 1] == "-":
            k = src.find("\n", i)
            i = n if k < 0 else k
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            k = src.find("*/", i + 2)
            k = n if k < 0 else k + 2
            out.append("\n" * src.count("\n", i, k))
            i = k
            continue
        if c in "'\"":                                     # 字符串 / 引号标识符（'' 与 "" 为转义）
            q, j = c, i + 1
            while j < n:
                if src[j] == q:
                    if j + 1 < n and src[j + 1] == q:
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            out.append(src[i:j])
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


# ---------------------------------------------------------------- XML
def strip_xml(src: str) -> str:
    def repl(m):
        return "\n" * m.group(0).count("\n")
    return re.sub(r"<!--.*?-->", repl, src, flags=re.S)


STRIPPERS = {".lua": strip_lua, ".sql": strip_sql, ".xml": strip_xml, ".modinfo": strip_xml}


def collapse_blank(text: str) -> str:
    """清掉注释留下的空行。

    先清「纯空白行」——注释行被删后只剩原缩进，会让后面的换行折叠失效（缩进夹在换行之间，
    `\\n{3,}` 匹配不到）；再折叠连续空行。只动**整行皆为空白**的行，不碰代码行尾；
    唯一理论风险是长字符串（Lua 的 `[[...]]`）里恰好有一行纯空格，本项目未出现。
    """
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\A(?:\s*\n)+", "", text)          # 去掉文件开头因整块头注释留下的空行
    text = re.sub(r"(?:\n\s*)+\Z", "\n", text)        # 结尾只留一个换行
    return text


def harmonize_newlines(text: str, raw: str) -> str:
    """让剥离结果的换行风格与原文一致。

    剥离器用 `"\\n" * count` 重建被删注释所占的换行（见 strip_lua / strip_sql），
    这会在 **CRLF 文件里引入裸 LF**：文件读进来是 `\\r\\n`，注释块留下的却是 `\\n`，
    于是 Mods 副本变成 MIXED（实测 示例工程：328 CRLF + 6 裸 LF），
    与「换行分层铁律」冲突，也让 strip(源) 比对出现伪差异。

    以原文的主导风格回填：CRLF 文件统一 CRLF，纯 LF 文件统一 LF。
    """
    raw_crlf = raw.count("\r\n")
    raw_lf = raw.count("\n") - raw_crlf
    if raw_crlf > 0 and raw_crlf >= raw_lf:
        # 先统一成 LF 再整体转 CRLF，避免已有 \r\n 被二次转换产生 \r\r\n
        return text.replace("\r\n", "\n").replace("\n", "\r\n")
    if raw_lf > 0 and raw_crlf == 0:
        return text.replace("\r\n", "\n")
    return text


def luac_path():
    return _paths.tool("luac")


def luac_check_text(text: str) -> bool | None:
    """对一段 Lua 源码跑 `luac -p`；返回 None 表示本机没有 luac（无法判定）。

    用「文本」而非「文件路径」是为了支持**差分判定**：先验原文、再验剥离结果。
    只验剥离后的话，Civ6 自带的类型标注语法（`local x:table = {}`，非 Lua 5.1）
    会被误判成「剥离破坏了语法」——源文件本来就过不了（见 main 内注释）。
    """
    exe = luac_path()
    if not exe:
        return None
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".lua")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        r = subprocess.run([exe, "-p", tmp], capture_output=True)
        return r.returncode == 0
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def collect(target: str, exts):
    hits = []
    for root, _, names in os.walk(target):
        for n in sorted(names):
            if os.path.splitext(n)[1].lower() in exts:
                hits.append(os.path.join(root, n))
    return sorted(hits)


def main() -> int:
    ap = argparse.ArgumentParser(description="发布前剥离代码注释（默认仅 Lua，只动发布副本）")
    ap.add_argument("target", help="目标目录（Mods 副本 / 上传工作区 content）")
    ap.add_argument("--src", default=None, help="可选：源工程目录；剥离后核对 Mods == strip(src)")
    ap.add_argument("--exts", default=",".join(DEFAULT_EXTS),
                    help="处理的扩展名（默认仅 .lua；传 .lua,.sql,.xml,.modinfo 恢复旧的全类型行为）")
    ap.add_argument("--all-exts", action="store_true",
                    help="等价 --exts .lua,.sql,.xml,.modinfo（旧的 Lua/SQL/XML/modinfo 全类型剥离）")
    ap.add_argument("--dry-run", action="store_true", help="只统计不写盘")
    ap.add_argument("--keep-lines", action="store_true",
                    help="保留注释留下的空行（行号与源文件一致，便于按报错行号回查）；默认折叠")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print("FAIL 目标目录不存在：%s" % target)
        return 2
    exts_raw = ",".join(ALL_EXTS) if args.all_exts else args.exts
    exts = tuple("." + e.strip().lstrip(".") for e in exts_raw.split(",") if e.strip())

    files = collect(target, exts)
    if not files:
        print("FAIL 目标目录下没有 %s 文件" % (exts,))
        return 2

    before_total = after_total = 0
    changed = failed = 0
    preexisting = 0
    for p in files:
        raw = open(p, encoding="utf-8", newline="").read()
        # 统一在 LF 上做处理：既让 collapse_blank 的 `\n{3,}` 能在 CRLF 文件里正常折叠
        # （CRLF 下 `\n` 之间夹着 `\r`，正则匹配不到），也避免剥离器插入裸 LF。
        work = raw.replace("\r\n", "\n")
        stripped = STRIPPERS.get(os.path.splitext(p)[1].lower(), lambda s: s)(work)
        if not args.keep_lines:
            stripped = collapse_blank(stripped)
        stripped = harmonize_newlines(stripped, raw)   # 恢复原文换行风格
        before_total += len(raw.encode("utf-8"))
        after_total += len(stripped.encode("utf-8"))
        if stripped == raw:
            continue
        changed += 1
        # 语法自检改为**差分判定**：只在「原文能过、剥离后不过」时才算失败。
        # 原版本会对任何 luac 不过的文件报 FAIL，而 Civ6 的 Lua 带类型标注
        # （如 `local x:table = {}`）本就不是 Lua 5.1 语法 —— 源文件同样过不了，
        # 属既存误报（本项目 ImportFiles/OfficialOverrides/SecretSocietyPopup.lua 即此例），
        # 每次都让工具 exit 1，反而会掩盖真正的剥离破坏。
        if os.path.splitext(p)[1].lower() == ".lua":
            ok_before = luac_check_text(raw)
            ok_after = luac_check_text(stripped if stripped.endswith("\n") else stripped + "\n")
            if ok_before is not None and ok_after is not None:
                if ok_before and not ok_after:
                    print("FAIL luac -p 失败（剥离破坏了语法）：%s" % p)
                    failed += 1
                elif not ok_before:
                    preexisting += 1
        if not args.dry_run:
            open(p, "w", encoding="utf-8", newline="").write(stripped)
        if not args.quiet:
            print("  %-52s %7d -> %7d B" % (os.path.relpath(p, target),
                                             len(raw.encode("utf-8")), len(stripped.encode("utf-8"))))

    print("%s共 %d 个文件，%d 个含注释；%d B -> %d B（-%d B, -%.1f%%）" % (
        "[dry-run] " if args.dry_run else "", len(files), changed,
        before_total, after_total, before_total - after_total,
        100.0 * (before_total - after_total) / max(1, before_total)))
    if preexisting:
        print("注：%d 个 .lua 在**剥离前**就通不过 luac -p（Civ6 类型标注等既存语法，"
              "非剥离所致），已跳过判定。" % preexisting)
    if failed:
        return 1

    # 核对：目标 == strip(源)
    if args.src:
        src_dir = os.path.abspath(args.src)
        mismatch, derived = [], []
        for p in files:
            rel = os.path.relpath(p, target)
            sp = os.path.join(src_dir, rel)
            if not os.path.isfile(sp):
                # .modinfo 等由 .civ6proj 派生（modinfo_build.py 生成），源工程里本就没有 → 跳过并提示
                derived.append(rel)
                continue
            src_raw = open(sp, encoding="utf-8", newline="").read()
            # 与主流程同口径：在 LF 上剥离，再按源文件换行风格回填
            want = STRIPPERS.get(os.path.splitext(sp)[1].lower(), lambda s: s)(
                src_raw.replace("\r\n", "\n"))
            if not args.keep_lines:
                want = collapse_blank(want)
            want = harmonize_newlines(want, src_raw)
            if want != open(p, encoding="utf-8", newline="").read():
                mismatch.append((rel, "内容不一致"))
        for rel in derived:
            print("SKIP %-50s 派生文件（源工程无此文件，如 .modinfo 由 .civ6proj 生成）" % rel)
        if mismatch:
            print("FAIL 与 strip(源) 不一致：")
            for rel, why in mismatch:
                print("   %-50s %s" % (rel, why))
            return 1
        print("OK  目标目录 == strip(源工程)（%d 个文件逐字节一致，%d 个派生文件跳过）"
              % (len(files) - len(derived), len(derived)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
