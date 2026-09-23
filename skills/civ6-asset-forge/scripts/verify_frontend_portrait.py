#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""verify_frontend_portrait.py — **原版环境** 领袖前景/背景接线的只读校验器

配套 `reference/frontend-portrait.md`。只读，不写盘。退出码 0 = 全过，2 = 有告警。

覆盖**环境 A（FrontEnd 选人）** 与 **环境 B（加载界面）**——
这两者不属 Suk 那条链（Suk 用 `verify_suk_portrait.py`）。

## 检查项（对应 `reference/frontend-portrait.md` §五）

1. `Players.Portrait` / `PortraitBackground`（Config 库，`Data/Config_*.sql`）
   与 `LoadingInfo.ForegroundImage` / `BackgroundImage`（Gameplay 库，`Data/Leaders_*.sql`）
   里出现的贴图名，必须满足**其一**：
     a) 磁盘上有同名 `.dds`（或 `.tex`）；
     b) 是某 XLP 里的别名 `EntryID`（`m_ObjectName` 才是真贴图名）且该 `ObjectName` 可解析；
     c) 是官方 pantry 里已存在的贴图（本机 SDK Assets 可查）；
   否则报「悬空」。
2. **留空 = 高风险**：两列为空/NULL 时，引擎会回退到
   `LEADER_<LeaderType>_NEUTRAL` / `LEADER_<LeaderType>_BACKGROUND`；
   若这两个名字**既不在工程、也不在官方**，报「空白风险」（这是最常见的静默失败——
   前端**不报错**，只是控件空白）。
3. `LoadingInfo` 写在 **InGameActions**（Gameplay 库）、`Players` 写在 **FrontEndActions**
   （Config 库）——写错段会 `no such table`。
4. `.tex`：`m_ClassName == UserInterface`、`m_Width/m_Height` == 实际 DDS 宽高。
5. 尺寸告警（口径已于 2026-09-19 按实机观察修订）：
   - 环境 A 背景 ≠ 328×935（也非其整数倍）→ WARN「`LeaderBG` 是 StretchMode=None，会被截断」；
   - 环境 B 背景**低于 960 高** → WARN（两侧裁剪风险）；**≥960 一律合规**（官方 960 是**基准**不是上限，
     本项目 1920×1080 实机效果良好）。
6. 行尾：`.tex` / `.xlp` = LF；`.sql` = CRLF。

用法：
    python verify_frontend_portrait.py --project <工程根>
    python verify_frontend_portrait.py --project <工程根> --json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import struct
import sys

SKIP_DIRS = {"workspace", ".git", "Cooked", "Build", "bin", "obj"}

# 环境 A 背景控件尺寸（reference/frontend-portrait.md §1.3）
PLACARD_BG = (328, 935)
# 环境 B 官方背景尺寸（实测 41/41）
LOADING_BG = (1920, 960)


def read_dds_wh(path):
    try:
        with open(path, "rb") as f:
            h = f.read(20)
    except OSError:
        return None
    if len(h) < 20 or h[:4] != b"DDS ":
        return None
    ht, wd = struct.unpack("<II", h[12:20])
    return wd, ht


def tex_meta(path):
    """→ (w, h, class_name)（读不到给 None）。"""
    try:
        t = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    w = re.search(r"<m_Width>(\d+)</m_Width>", t)
    h = re.search(r"<m_Height>(\d+)</m_Height>", t)
    c = re.search(r'<m_ClassName text="([^"]*)"', t)
    return (int(w.group(1)) if w else None,
            int(h.group(1)) if h else None,
            c.group(1) if c else None)


def eol_of(path):
    try:
        raw = open(path, "rb").read()
    except OSError:
        return None
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    return crlf, lf, raw.startswith(b"\xef\xbb\xbf")


def collect(root):
    tex, xlp, sql, proj = [], [], [], []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
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


def parse_xlp_alias(xlp_files):
    """→ (entry_ids:set, aliases:dict[entry→object])。"""
    ids, alias = set(), {}
    for p in xlp_files:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in re.finditer(
                r'<m_EntryID text="([^"]*)"\s*/>\s*<m_ObjectName text="([^"]*)"\s*/>', t):
            eid, obj = m.group(1), m.group(2)
            ids.add(eid)
            if eid != obj:
                alias[eid] = obj
    return ids, alias


def official_names(sdk_assets):
    """官方 pantry 的贴图名集合（含别名 ObjectName）。找不到 SDK 时返回空集。"""
    names = set()
    if not sdk_assets:
        return names
    base = os.path.join(sdk_assets, "Civ6")
    for d in (os.path.join(base, "pantry"), os.path.join(base, "DLC")):
        for dp, dn, fn in os.walk(d):
            for f in fn:
                if f.endswith((".dds", ".tex")):
                    names.add(os.path.splitext(f)[0])
    return names


# --- SQL 解析（窄口径：只抓我们需要的那几条列） -------------------------------

RE_PLAYERS = re.compile(
    r"INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+Players\s*\(([^)]*)\)\s*VALUES(.*?);",
    re.I | re.S)
RE_LOADING = re.compile(
    r"INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+LoadingInfo\s*\(([^)]*)\)\s*VALUES(.*?);",
    re.I | re.S)
RE_ROW = re.compile(r"\((.*?)\)", re.S)
RE_LIT = re.compile(r"'((?:[^']|'')*)'|(NULL)|([-\d.]+)")


def split_cols(cols: str):
    return [c.strip().strip('"').strip() for c in cols.split(",") if c.strip()]


def parse_values(body: str):
    """→ list[dict[col→value]]（按列名对齐；只处理字面量）。"""
    rows = []
    for rm in RE_ROW.finditer(body):
        vals = []
        for vm in RE_LIT.finditer(rm.group(1)):
            if vm.group(1) is not None:
                vals.append(vm.group(1).replace("''", "'"))
            elif vm.group(2) is not None:
                vals.append(None)
            else:
                vals.append(vm.group(3))
        rows.append(vals)
    return rows


def extract_refs(sql_files):
    """→ (players_refs, loading_refs)：[(文件, LeaderType, {列: 值}), ...]。"""
    p_refs, l_refs = [], []
    for p in sql_files:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        # 去行注释，避免注释里的示例误导
        t = re.sub(r"--[^\n]*", "", t)
        for m in RE_PLAYERS.finditer(t):
            cols = split_cols(m.group(1))
            for vals in parse_values(m.group(2)):
                if len(vals) < len(cols):
                    continue
                row = dict(zip(cols, vals))
                lt = row.get("LeaderType")
                if isinstance(lt, str) and lt.startswith("LEADER_"):
                    p_refs.append((p, lt, {
                        "Portrait": row.get("Portrait"),
                        "PortraitBackground": row.get("PortraitBackground")}))
        for m in RE_LOADING.finditer(t):
            cols = split_cols(m.group(1))
            for vals in parse_values(m.group(2)):
                if len(vals) < len(cols):
                    continue
                row = dict(zip(cols, vals))
                lt = row.get("LeaderType")
                if isinstance(lt, str) and lt.startswith("LEADER_"):
                    l_refs.append((p, lt, {
                        "ForegroundImage": row.get("ForegroundImage"),
                        "BackgroundImage": row.get("BackgroundImage")}))
    return p_refs, l_refs


def action_sections(proj_files):
    """→ (frontend_files, ingame_files)：civ6proj 里两段各自引用的 SQL 相对路径 → 绝对。"""
    fe, ig = set(), set()
    for p in proj_files:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue

        def grab(tag):
            i = t.find("<%s><![CDATA[" % tag)
            if i < 0:
                return ""
            s = i + len("<%s><![CDATA[" % tag)
            e = t.find("]]></%s>" % tag, s)
            return t[s:e] if e > 0 else ""

        root = os.path.dirname(p)
        for tag, bucket in (("FrontEndActionData", fe), ("InGameActionData", ig)):
            body = grab(tag)
            for m in re.finditer(r"<File>([^<]+)</File>", body):
                f = m.group(1).strip().replace("/", os.sep)
                bucket.add(os.path.normpath(os.path.join(root, f)).lower())
    return fe, ig


def main():
    ap = argparse.ArgumentParser(description="原版环境（FrontEnd + 加载界面）立绘/背景接线校验")
    ap.add_argument("--project", required=True)
    ap.add_argument("--sdk-assets", default=None, help="SDK Assets 路径（默认从 civ6-modding/local_paths.json 解析）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        raise SystemExit("工程目录不存在：%s" % root)

    sdk = a.sdk_assets
    if not sdk:
        try:
            skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, os.path.join(os.path.dirname(skill_dir), "civ6-modding", "tools"))
            import _paths  # type: ignore
            sdk = _paths.get("sdk_assets")
        except Exception:
            sdk = None

    tex, xlp, sql, proj = collect(root)
    ids, alias = parse_xlp_alias(xlp)
    official = official_names(sdk)
    p_refs, l_refs = extract_refs(sql)
    fe_files, ig_files = action_sections(proj)

    disk = {os.path.splitext(os.path.basename(t))[0] for t in tex}
    disk |= {os.path.splitext(os.path.basename(d))[0]
             for d in glob.glob(os.path.join(root, "Textures", "*.dds"))}

    errors, warns, infos = [], [], []
    checked = []

    def resolvable(name):
        """→ ('disk'|'alias'|'official'|None, 说明)。"""
        if not name:
            return None, "空"
        if name in disk:
            return "disk", "工程磁盘"
        if name in ids:
            tgt = alias.get(name, name)
            if tgt in disk or tgt in official:
                return "alias", "XLP 别名 → %s" % tgt
            return None, "XLP 条目 %s 的 ObjectName=%s 既不在工程也不在官方" % (name, tgt)
        if name in official:
            return "official", "官方 pantry"
        return None, "未找到"

    def check(env, where, lt, col, val, fallback_suffix):
        """★ 三态语义（区别极关键，此前误判过）：

        | SQL 取值 | Lua 里的值 | 引擎行为 |
        |---|---|---|
        | 名 字 | 非空字符串 | 直接用该贴图 |
        | `''`（空串） | `""` —— **Lua 里是 truthy** | `SetTexture("")` → **真正的空白前景，且短路回退** |
        | `NULL` | `nil`（falsy） | 走回退 → `<LeaderType>_NEUTRAL` / `_BACKGROUND` |

        依据 `PlayerSetupLogic.lua:807-829` 的 `if info.Portrait then ... else ... end`。
        所以「空白前景 + 铺满背景」是**合法设计**（本项目做法），不是缺陷；
        而 `NULL` + 无回退贴图才是真的会空白且**报不了错**。
        """
        # --- 情形 1：空串 → 有意留空（短路回退），合法 ---
        if isinstance(val, str) and val.strip() == "":
            checked.append({"env": env, "leader": lt, "col": col, "value": "''",
                            "how": "blank", "why": "显式空串 = 有意空白（短路回退）"})
            infos.append("%s %s.%s = '' → **有意空白**（Lua 空串 truthy，短路回退；"
                         "「空白前景+铺满背景」即此做法）[%s]"
                         % (env, lt, col, os.path.basename(where)))
            return
        # --- 情形 2：NULL / 未写该列 → 触发回退 ---
        if val is None:
            fb = lt + fallback_suffix
            how, why = resolvable(fb)
            if how is None:
                errors.append("%s %s 的 %s 为 NULL（触发回退），且回退名 %s 不可解析（%s）→ "
                              "控件**空白**且前端不报错 [%s]"
                              % (env, lt, col, fb, why, os.path.basename(where)))
            else:
                infos.append("%s %s.%s 为 NULL → 回退到 %s（%s）"
                             % (env, lt, col, fb, why))
            return
        # --- 情形 3：正常贴图名 ---
        how, why = resolvable(val)
        checked.append({"env": env, "leader": lt, "col": col, "value": val,
                        "how": how, "why": why})
        if how is None:
            errors.append("%s %s.%s = %s 悬空：%s（%s）"
                          % (env, lt, col, val, why, os.path.basename(where)))

    for f, lt, cols in p_refs:
        check("A", f, lt, "Portrait", cols["Portrait"], "_NEUTRAL")
        check("A", f, lt, "PortraitBackground", cols["PortraitBackground"], "_BACKGROUND")
        if os.path.normpath(f).lower() not in fe_files and fe_files:
            errors.append("A %s 未被任何 civ6proj 的 FrontEndActions 引用"
                          "（Players 属 Config 库，放 InGameActions 会 no such table）" % os.path.basename(f))
    for f, lt, cols in l_refs:
        check("B", f, lt, "ForegroundImage", cols["ForegroundImage"], "_NEUTRAL")
        check("B", f, lt, "BackgroundImage", cols["BackgroundImage"], "_BACKGROUND")
        if os.path.normpath(f).lower() not in ig_files and ig_files:
            errors.append("B %s 未被任何 civ6proj 的 InGameActions 引用"
                          "（LoadingInfo 属 Gameplay 库）" % os.path.basename(f))

    # --- .tex 类别 / 尺寸 / 行尾（**只查本类相关贴图**，不做全工程体检）---
    # 本类相关 = SQL 引用到的 + 各领袖的回退名（_NEUTRAL / _BACKGROUND）
    relevant = set()
    for _, lt, cols in p_refs:
        for c in ("Portrait", "PortraitBackground"):
            v = cols[c]
            if isinstance(v, str) and v.strip():
                relevant.add(v)
        relevant |= {lt + "_NEUTRAL", lt + "_BACKGROUND"}
    for _, lt, cols in l_refs:
        for c in ("ForegroundImage", "BackgroundImage"):
            v = cols[c]
            if isinstance(v, str) and v.strip():
                relevant.add(v)
        relevant |= {lt + "_NEUTRAL", lt + "_BACKGROUND"}

    by_name = {}
    for t in tex:
        nm = os.path.splitext(os.path.basename(t))[0]
        w, h, cls = tex_meta(t)
        dds = os.path.join(os.path.dirname(t), nm + ".dds")
        dw, dh = read_dds_wh(dds) if os.path.isfile(dds) else (None, None)
        by_name[nm] = (w, h, cls, dw, dh)
        if nm not in relevant:
            continue
        if cls != "UserInterface":
            errors.append(".tex 类别非 UserInterface：%s（%s）" % (os.path.basename(t), cls))
        if dw and (w, h) != (dw, dh):
            errors.append(".tex 声明 %sx%s != DDS 实际 %sx%s：%s"
                          % (w, h, dw, dh, os.path.basename(t)))
        e = eol_of(t)
        if e and e[0] > 0:
            errors.append(".tex 含 CRLF（应为 LF，见 gotchas §68）：%s" % os.path.basename(t))

    # .xlp 只查登记了本类条目的那些
    for p in xlp:
        try:
            txt = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not (relevant & set(re.findall(r'<m_EntryID text="([^"]*)"', txt))):
            continue
        e = eol_of(p)
        if e and e[0] > 0:
            errors.append(".xlp 含 CRLF（应为 LF）：%s" % os.path.basename(p))

    # --- 尺寸告警 ---
    for f, lt, cols in p_refs:
        bg = cols["PortraitBackground"]
        if isinstance(bg, str) and bg in by_name:
            w, h, _, _, _ = by_name[bg]
            if not (w and h):
                continue
            if (w, h) == PLACARD_BG or (w % PLACARD_BG[0] == 0 and h % PLACARD_BG[1] == 0):
                continue                       # 精确 或 整数倍放大：无裁切
            if abs(w - PLACARD_BG[0]) <= 2 and abs(h - PLACARD_BG[1]) <= 2:
                infos.append("A %s 的背景 %s 是 %sx%s（控件 %sx%s，差 %+d/%+d px，"
                             "StretchMode=None 下可忽略）"
                             % (lt, bg, w, h, PLACARD_BG[0], PLACARD_BG[1],
                                w - PLACARD_BG[0], h - PLACARD_BG[1]))
            else:
                warns.append("A %s 的背景 %s 是 %sx%s；控件 LeaderBG 为 %sx%s 且 "
                             "StretchMode=None → 会被截断或留边（自建建议 %sx%s 或其整数倍）"
                             % (lt, bg, w, h, PLACARD_BG[0], PLACARD_BG[1],
                                PLACARD_BG[0], PLACARD_BG[1]))
    for f, lt, cols in l_refs:
        bg = cols["BackgroundImage"]
        if isinstance(bg, str) and bg in by_name:
            w, h, _, _, _ = by_name[bg]
            if not (w and h):
                continue
            # ★ 以官方 960 为**基准**（不是硬规格）：允许超过（本项目 1920×1080 实机效果良好），
            #   但**低于 960 有两侧裁剪风险** —— 依据实机观察 + LoadScreen.xml:9 的
            #   `BackgroundImage` 是 StretchMode="Auto" 且**无 Size 属性**（Auto 疑似 cover 语义），
            #   高度不足时按高放大 → 宽溢出 → 两侧被 `Clip="1"`（LoadScreen.xml:10）裁掉。
            if h < LOADING_BG[1]:
                warns.append("B %s 的背景 %s 高度 %d < 基准 %d → 加载界面**两侧可能被裁剪**"
                             "（Auto 疑为 cover：按高放大后宽溢出，被 Clip 裁掉）。"
                             "建议高度 ≥ %d；官方基线为 %dx%d"
                             % (lt, bg, h, LOADING_BG[1], LOADING_BG[1],
                                LOADING_BG[0], LOADING_BG[1]))
            elif (w, h) == LOADING_BG:
                pass                       # 官方基线，静默通过
            else:
                infos.append("B %s 的背景 %s 是 %sx%s（高 %d ≥ 基准 %d，合规；官方基线 %dx%d）"
                             % (lt, bg, w, h, h, LOADING_BG[1], LOADING_BG[0], LOADING_BG[1]))

    if a.json:
        print(json.dumps({"checked": checked, "errors": errors, "warnings": warns,
                          "info": infos, "official_indexed": len(official),
                          "xlp_entries": len(ids), "xlp_aliases": len(alias)},
                         ensure_ascii=False, indent=1))
    else:
        print("工程：%s" % root)
        print("官方 pantry 索引：%s 个贴图名（SDK：%s）" % (len(official), sdk or "未解析到"))
        print("XLP 条目 %d 个，其中别名 %d 个" % (len(ids), len(alias)))
        print("解析到 Players 行 %d 条、LoadingInfo 行 %d 条" % (len(p_refs), len(l_refs)))
        for c in checked:
            print("  [%s] %-32s %-20s %-40s %s" %
                  (c["env"], c["leader"], c["col"], c["value"], c["why"]))
        for i in infos:
            print("INFO  " + i)
        for w in warns:
            print("WARN  " + w)
        for e in errors:
            print("ERROR " + e)
        print("\n结论：%d error / %d warn / %d info" % (len(errors), len(warns), len(infos)))
    return 1 if errors else (2 if warns else 0)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    raise SystemExit(main())
