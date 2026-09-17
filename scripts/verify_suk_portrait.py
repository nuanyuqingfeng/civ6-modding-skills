#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""verify_suk_portrait.py — Suk 选人界面适配素材与接线的只读校验器

配套 `reference/ui-leader-portrait.md`。**只读，不写盘**。退出码 0 = 全过。

检查项（对应参考文档 §6.1）：
  1. 每张 `_Suk` 贴图 `.dds` ↔ `.tex` 成对，且 `.tex` 的 m_Width/m_Height == DDS 实际宽高；
  2. `m_ClassName == UserInterface`、`m_Tags` 仅含 `UserInterface`
     —— 这是本类最大的坑：`FALLBACK_NEUTRAL_*_Suk` 与 3D 回退同前缀，
     误判成 `Leader_Fallback` 会导致「类别与 XLP 参数不匹配」→ 静默变 error asset；
  3. 每张 `_Suk` 贴图都被某个 `UITexture` 类 XLP 登记（否则不进 BLP = 界面空白）；
  4. SQL 中 Portrait / PortraitBackground 指向的贴图在磁盘存在（无悬空）；
  5. 行尾：`.tex` / `.xlp` = LF；`.sql` = CRLF。

用法：
    python verify_suk_portrait.py --project <工程根>
    python verify_suk_portrait.py --project <工程根> --suffix _Suk
"""
import argparse
import os
import re
import struct
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BOM = b"\xef\xbb\xbf"


def read_dds_wh(path):
    """→ (width, height) 或 None（非 DDS）。"""
    with open(path, "rb") as f:
        h = f.read(20)
    if len(h) < 20 or h[:4] != b"DDS ":
        return None
    ht, wd = struct.unpack("<II", h[12:20])
    return wd, ht


def eol_of(path):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    return crlf, lf, raw.startswith(BOM)


def find_files(root):
    """收集工程内相关文件（跳过 workspace/Build/Cooked）。"""
    skip = {"workspace", ".git", "Cooked", "Build", "bin", "obj"}
    tex, xlp, sql, proj = [], [], [], []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip]
        for f in fn:
            p = os.path.join(dp, f)
            low = f.lower()
            if low.endswith(".tex"):
                tex.append(p)
            elif low.endswith(".xlp"):
                xlp.append(p)
            elif low.endswith(".sql"):
                sql.append(p)
            elif low.endswith(".civ6proj"):
                proj.append(p)
    return tex, xlp, sql, proj


def main():
    ap = argparse.ArgumentParser(description="Suk 适配素材与接线只读校验")
    ap.add_argument("--project", required=True)
    ap.add_argument("--suffix", default="_Suk", help="贴图后缀，默认 _Suk")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    a = ap.parse_args()

    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        print("工程目录不存在：%s" % root)
        return 1
    tex_files, xlp_files, sql_files, proj_files = find_files(root)
    if not proj_files:
        print("未找到 .civ6proj")
        return 1
    proj_dir = os.path.dirname(proj_files[0])

    fails, warns, infos = [], [], []

    # ---- 目标贴图集合：文件名含后缀的 .tex ----
    targets = [p for p in tex_files if os.path.splitext(os.path.basename(p))[0].endswith(a.suffix)]
    if not targets:
        infos.append("未发现 *%s.tex —— 本工程尚未做 Suk 适配（或后缀不同，用 --suffix 指定）"
                     % a.suffix)

    tex_names = set()
    for p in targets:
        stem = os.path.splitext(os.path.basename(p))[0]
        tex_names.add(stem)
        t = open(p, encoding="utf-8", errors="replace").read()

        # [1] .dds 成对
        dds = os.path.join(os.path.dirname(p), stem + ".dds")
        if not os.path.isfile(dds):
            fails.append("%s: 缺同名 .dds" % os.path.basename(p))
        else:
            m = re.search(r"<m_Width>(\d+)</m_Width>", t)
            n = re.search(r"<m_Height>(\d+)</m_Height>", t)
            wh = read_dds_wh(dds)
            if not (m and n):
                fails.append("%s: .tex 缺 m_Width/m_Height" % os.path.basename(p))
            elif wh is None:
                fails.append("%s: .dds 非合法 DDS" % stem)
            elif (int(m.group(1)), int(n.group(1))) != wh:
                fails.append("%s: .tex 声明 %sx%s != DDS 实际 %dx%d"
                             % (os.path.basename(p), m.group(1), n.group(1), wh[0], wh[1]))

        # [2] 类别 / 标签
        cm = re.search(r'<m_ClassName text="([^"]*)"', t)
        cls = cm.group(1) if cm else "(missing)"
        tags = re.findall(r'<m_Tags>(.*?)</m_Tags>', t, re.S)
        tagset = re.findall(r'<Element text="([^"]*)"', tags[0]) if tags else []
        if cls != "UserInterface":
            fails.append("%s: m_ClassName=%s（应为 UserInterface；"
                         "Leader_Fallback 会与本类 XLP 参数不匹配 → 静默 error asset）"
                         % (os.path.basename(p), cls))
        if tagset != ["UserInterface"]:
            fails.append("%s: m_Tags=%s（应为单条 UserInterface）"
                         % (os.path.basename(p), tagset))
        if cls == "UserInterface" and not re.search(r"<bUseMips>false</bUseMips>", t):
            warns.append("%s: bUseMips 非 false（本类贴图通常单 mip）" % os.path.basename(p))

    # ---- [3] UITexture XLP 登记 ----
    ui_entries = set()
    for p in xlp_files:
        t = open(p, encoding="utf-8", errors="replace").read()
        if 'm_ClassName text="UITexture"' not in t:
            continue
        ui_entries |= set(re.findall(r'<m_EntryID text="([^"]*)"', t))
    for n in sorted(tex_names):
        if n not in ui_entries:
            fails.append("%s: 未被任何 UITexture XLP 登记 → 不会进 BLP，界面空白" % n)

    # ---- [3b] 反向：XLP 里登记了但磁盘没有的 _Suk 条目 ----
    for e in sorted(x for x in ui_entries if x.endswith(a.suffix)):
        if e not in tex_names:
            fails.append("XLP 条目 %s 无对应 Textures/*.tex（悬空）" % e)

    # ---- [4] SQL 指向的贴图存在 ----
    refs = []
    for p in sql_files:
        t = open(p, encoding="utf-8", errors="replace").read()
        if a.suffix not in t:
            continue
        for m in re.finditer(r"Portrait = '([^']+)'", t):
            refs.append((p, "Portrait", m.group(1)))
        for m in re.finditer(r"PortraitBackground = '([^']+)'", t):
            refs.append((p, "PortraitBackground", m.group(1)))
    for src, col, name in refs:
        tp = os.path.join(proj_dir, "Textures", name + ".tex")
        if not os.path.isfile(tp):
            fails.append("%s: %s='%s' 在 Textures/ 无对应 .tex（悬空引用）"
                         % (os.path.basename(src), col, name))
        if name not in ui_entries:
            fails.append("%s: %s='%s' 未被 UITexture XLP 登记" % (os.path.basename(src), col, name))

    # ---- [4b] Criteria 是否挂上 ----
    pt = open(proj_files[0], encoding="utf-8", errors="replace").read()
    if refs:
        if "Suk_Portrait" not in pt:
            fails.append("civ6proj 缺 Criteria Suk_Portrait —— 不加判据会让 SQL 无条件加载，"
                         "改变未启用 Suk 时的界面行为")
        if not re.search(r'Suk_Portrait</Criteria>|Criteria>Suk_Portrait<', pt):
            warns.append("civ6proj 里未见到挂 Suk_Portrait 判据的 action，请人工确认")

    # ---- [5] 行尾 ----
    for p in targets:
        crlf, lf, bom = eol_of(p)
        if crlf:
            fails.append("%s: .tex 应为 LF，实含 %d 个 CRLF" % (os.path.basename(p), crlf))
        if bom:
            warns.append("%s: .tex 带 BOM（工程约定无 BOM）" % os.path.basename(p))
    for p in xlp_files:
        crlf, lf, bom = eol_of(p)
        if crlf:
            fails.append("%s: .xlp 应为 LF，实含 %d 个 CRLF" % (os.path.basename(p), crlf))
    for p in sql_files:
        t = open(p, encoding="utf-8", errors="replace").read()
        if a.suffix not in t:
            continue
        crlf, lf, bom = eol_of(p)
        if lf:
            fails.append("%s: 含 %s 的 .sql 应为 CRLF，实含 %d 个裸 LF"
                         % (os.path.basename(p), a.suffix, lf))

    # ---- 输出 ----
    print("=" * 72)
    print("Suk 适配校验：%s" % root)
    print("=" * 72)
    print("  目标 .tex（*%s）: %d" % (a.suffix, len(targets)))
    print("  UITexture XLP 条目 : %d" % len(ui_entries))
    print("  SQL 引用(含后缀)   : %d" % len(refs))
    print()
    for i in infos:
        print("  [info] %s" % i)
    for w in warns:
        print("  [warn] %s" % w)
    for f in fails:
        print("  [FAIL] %s" % f)
    if not (infos or warns or fails):
        print("  全部检查通过。")
    print()
    print("RESULT:", "PASS" if not fails else "FAIL (%d)" % len(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
