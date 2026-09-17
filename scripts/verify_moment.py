#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""verify_moment.py — 历史时刻插画与接线的只读校验器

配套 `reference/moment-illustration.md`。**只读，不写盘**。退出码 0 = 全过。

检查项：
  1. 每张 `Moment_*` 贴图 `.dds` ↔ `.tex` 成对，`.tex` 宽高 == 456×332 == DDS 实际；
  2. `m_ClassName == UserInterface`、`m_Tags` 单条 `UserInterface`；
  3. **alpha 覆盖率落在 83~99%**（低于 83% = 漏套官方形状模板 —— 本节最有价值的检查）；
  4. 贴图已被 `UITexture` 类 XLP 登记（默认 UI/PrideMoments）；
  5. `MomentIllustrations` 每行 Texture 在磁盘存在、(MomentIllustrationType, MomentDataType) 配对合法；
  6. `.tex`/`.xlp` 为 LF，`.sql` 为 CRLF。

用法：
    python verify_moment.py --project <工程根>
    python verify_moment.py --project <工程根> --coverage-min 83 --coverage-max 99
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

MOMENT_W, MOMENT_H = 456, 332

# 原版 MomentIllustrations 实际使用的配对（实测 238 行聚合）
VALID_PAIRS = {
    ("MOMENT_ILLUSTRATION_UNIQUE_UNIT", "MOMENT_DATA_UNIT"),
    ("MOMENT_ILLUSTRATION_NATURAL_WONDER", "MOMENT_DATA_FEATURE"),
    ("MOMENT_ILLUSTRATION_RELIGION", "MOMENT_DATA_RELIGION"),
    ("MOMENT_ILLUSTRATION_UNIQUE_IMPROVEMENT", "MOMENT_DATA_IMPROVEMENT"),
    ("MOMENT_ILLUSTRATION_UNIQUE_DISTRICT", "MOMENT_DATA_DISTRICT"),
    ("MOMENT_ILLUSTRATION_UNIQUE_BUILDING", "MOMENT_DATA_BUILDING"),
    ("MOMENT_ILLUSTRATION_GOVERNMENT", "MOMENT_DATA_GOVERNMENT"),
    ("MOMENT_ILLUSTRATION_GOVERNOR", "MOMENT_DATA_GOVERNOR"),
    ("MOMENT_ILLUSTRATION_AIR_UNIT_ERA", "MOMENT_DATA_PLAYER_ERA"),
    ("MOMENT_ILLUSTRATION_SEA_UNIT_ERA", "MOMENT_DATA_PLAYER_ERA"),
    ("MOMENT_ILLUSTRATION_CIVIC_ERA", "MOMENT_DATA_PLAYER_ERA"),
    ("MOMENT_ILLUSTRATION_TECHNOLOGY_ERA", "MOMENT_DATA_PLAYER_ERA"),
    ("MOMENT_ILLUSTRATION_GAME_ERA", "MOMENT_DATA_PLAYER_ERA"),
}


def read_dds_wh(path):
    with open(path, "rb") as f:
        h = f.read(20)
    if len(h) < 20 or h[:4] != b"DDS ":
        return None
    ht, wd = struct.unpack("<II", h[12:20])
    return wd, ht


def dds_alpha_coverage(path):
    """读单 mip RGBA8 DDS 的 alpha，返回 (覆盖率%, 宽, 高)。"""
    with open(path, "rb") as f:
        head = f.read(128)
        if len(head) < 128 or head[:4] != b"DDS ":
            return None
        ht, wd = struct.unpack("<II", head[12:20])
        pf_flags = struct.unpack("<I", head[80:84])[0]
        bits = struct.unpack("<I", head[88:92])[0]
        fourcc = head[84:88]
        raw = f.read(wd * ht * 4)
    if fourcc != b"\x00\x00\x00\x00" or not (pf_flags & 0x40) or bits != 32:
        return None
    n = 0
    for i in range(3, len(raw), 4):
        if raw[i] > 8:
            n += 1
    return n / float(wd * ht) * 100.0, wd, ht


def eol(path):
    raw = open(path, "rb").read()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    return crlf, lf, raw.startswith(b"\xef\xbb\xbf")


def main():
    ap = argparse.ArgumentParser(description="历史时刻插画只读校验")
    ap.add_argument("--project", required=True)
    ap.add_argument("--prefix", default="MOMENT", help="贴名前缀（大小写不敏感），默认 MOMENT")
    ap.add_argument("--coverage-min", type=float, default=75.0,
                    help="alpha 覆盖率下界（默认 75：原版 min=83.0，留 8pp 余量避免误报边缘软边差异）")
    ap.add_argument("--coverage-max", type=float, default=99.5,
                    help="alpha 覆盖率上界（默认 99.5：原版 max=98.5）")
    a = ap.parse_args()

    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        print("工程目录不存在：%s" % root)
        return 1
    texdir = os.path.join(root, "Textures")
    fails, warns, infos = [], [], []

    # ---- 收集 ----
    tex_files, xlp_files, sql_files, proj_files = [], [], [], []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ("workspace", ".git", "Cooked", "Build", "obj", "bin")]
        for f in fn:
            p = os.path.join(dp, f)
            low = f.lower()
            if low.endswith(".tex"):
                tex_files.append(p)
            elif low.endswith(".xlp"):
                xlp_files.append(p)
            elif low.endswith(".sql"):
                sql_files.append(p)
            elif low.endswith(".civ6proj"):
                proj_files.append(p)
    if not proj_files:
        print("未找到 .civ6proj")
        return 1

    # 只认「文件名以 MOMENT 开头」的贴图（避免误抓 Moment_PromoteGovernor 之外的其它）
    pref = a.prefix.upper()
    targets = [p for p in tex_files if os.path.basename(p).upper().startswith(pref)]
    if not targets:
        infos.append("未发现 %s* 贴图 —— 本工程尚未做历史时刻插画" % pref)

    # ---- 1/2/3/4 ----
    ui_entries = set()
    for p in xlp_files:
        t = open(p, encoding="utf-8", errors="replace").read()
        if 'm_ClassName text="UITexture"' in t:
            ui_entries |= set(re.findall(r'<m_EntryID text="([^"]*)"', t))

    names = set()
    for p in targets:
        stem = os.path.splitext(os.path.basename(p))[0]
        names.add(stem)
        t = open(p, encoding="utf-8", errors="replace").read()
        dds = os.path.join(os.path.dirname(p), stem + ".dds")
        if not os.path.isfile(dds):
            fails.append("%s: 缺同名 .dds" % os.path.basename(p))
        else:
            wh = read_dds_wh(dds)
            mw = re.search(r"<m_Width>(\d+)", t)
            mh = re.search(r"<m_Height>(\d+)", t)
            if wh is None:
                fails.append("%s: .dds 非法" % stem)
            else:
                if wh != (MOMENT_W, MOMENT_H):
                    fails.append("%s: DDS 尺寸 %dx%d != %dx%d" % (stem, wh[0], wh[1], MOMENT_W, MOMENT_H))
                if mw and mh and (int(mw.group(1)), int(mh.group(1))) != wh:
                    fails.append("%s: .tex 声明 %sx%s != DDS 实际 %dx%d"
                                 % (stem, mw.group(1), mh.group(1), wh[0], wh[1]))
                cov = dds_alpha_coverage(dds)
                if cov is None:
                    warns.append("%s: 非未压缩 RGBA8，跳过覆盖率检查" % stem)
                else:
                    c, w, h = cov
                    if c < a.coverage_min:
                        fails.append("%s: alpha 覆盖率 %.1f%% < %.1f%% —— 疑似未套官方形状模板"
                                     "（原版 240 张最低 83.0%%；漏套实测仅 14~15%%）"
                                     % (stem, c, a.coverage_min))
                    elif c < 83.0:
                        warns.append("%s: alpha 覆盖率 %.1f%% 略低于原版下界 83.0%%"
                                     "（仍在容差内；若是刻意保留更多透明可忽略）" % (stem, c))
                    elif c > a.coverage_max:
                        warns.append("%s: alpha 覆盖率 %.1f%% > %.1f%% —— 软边可能被削掉"
                                     % (stem, c, a.coverage_max))
        cm = re.search(r'<m_ClassName text="([^"]*)"', t)
        cls = cm.group(1) if cm else "(missing)"
        if cls != "UserInterface":
            fails.append("%s: m_ClassName=%s（应为 UserInterface）" % (os.path.basename(p), cls))
        tg = re.search(r"<m_Tags>(.*?)</m_Tags>", t, re.S)
        tags = re.findall(r'<Element text="([^"]*)"', tg.group(1)) if tg else []
        if tags != ["UserInterface"]:
            fails.append("%s: m_Tags=%s（应为单条 UserInterface）" % (os.path.basename(p), tags))
        if stem not in ui_entries:
            fails.append("%s: 未被任何 UITexture XLP 登记 → 不会进 BLP，时刻图不显示" % stem)

    # ---- 5. MomentIllustrations ----
    rows = []
    for p in sql_files:
        t = open(p, encoding="utf-8", errors="replace").read()
        if "MomentIllustrations" not in t:
            continue
        for m in re.finditer(
                r"\(\s*'(MOMENT_ILLUSTRATION_[A-Z_]+)'\s*,\s*'(MOMENT_DATA_[A-Z_]+)'\s*,"
                r"\s*'([A-Za-z0-9_]+)'\s*,\s*'([^']+)'", t):
            rows.append((os.path.basename(p), m.group(1), m.group(2), m.group(3), m.group(4)))
    for src, mit, mdt, gdt, tex in rows:
        if (mit, mdt) not in VALID_PAIRS:
            fails.append("%s: 配对 (%s, %s) 不在原版实测合法组合内" % (src, mit, mdt))
        base = os.path.splitext(os.path.basename(tex))[0]
        if not os.path.isfile(os.path.join(texdir, base + ".dds")):
            fails.append("%s: Texture='%s' 在 Textures/ 无对应 .dds" % (src, tex))
        if base not in ui_entries:
            fails.append("%s: Texture='%s' 未被 UITexture XLP 登记" % (src, base))
        if not tex.lower().endswith(".dds"):
            warns.append("%s: Texture='%s' 未带 .dds 后缀（原版惯例是带后缀）" % (src, tex))

    # ---- 6. 行尾 ----
    for p in targets:
        crlf, lf, bom = eol(p)
        if crlf:
            fails.append("%s: .tex 应为 LF，实含 %d 个 CRLF" % (os.path.basename(p), crlf))
    for p in sql_files:
        t = open(p, encoding="utf-8", errors="replace").read()
        if "MomentIllustrations" not in t:
            continue
        crlf, lf, bom = eol(p)
        if lf:
            fails.append("%s: 含 MomentIllustrations 的 .sql 应为 CRLF，实含 %d 个裸 LF"
                         % (os.path.basename(p), lf))

    # ---- 输出 ----
    print("=" * 72)
    print("历史时刻插画校验：%s" % root)
    print("=" * 72)
    print("  目标 .tex（%s*）: %d" % (pref, len(targets)))
    print("  MomentIllustrations 行: %d" % len(rows))
    print("  UITexture 条目: %d" % len(ui_entries))
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
