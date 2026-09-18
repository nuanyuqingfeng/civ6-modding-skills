#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iconify_text.py — 给游戏文本自动插入 `[ICON_x]` 标记（文本图标化）

## 为什么需要它

Civ6 文本里写 `[ICON_Science]` 会在游戏内渲染成图标。手工加很繁琐，而**图标名写错
不会报错、只是不显示**（见 `art-pipeline.md` §3 的静默失败案例），所以"批量加"必须
配一个"名称校验"，否则等于批量制造静默失败。

本工具 = 桌面版「图标化文本小工具」的逻辑（关键词映射 + 幂等防重复 + 保编码）
+ CLI 化 + **对照权威图标表校验** + 审计模式（只报告不写盘）。

## 名称来源与校验（本工具的核心价值）

一个 `[ICON_X]` 要能渲染，X 必须能从**任一**注册源解析到：

1. **官方原版**：`reference/sources/civ6-icon-tags.sql`（4836 个 `[ICON_*]` 全表，
   社区整理，随 skill 分发）；
2. **本工程自定义**：项目 Icons XML（`Data/*.xml`、`Mod_Adaptation/**/*.xml`）里
   声明的 `IconDefinitions` / `IconTextureAtlases` 名，以及字体图集名。

`--check` 会把「文本里出现的所有 `[ICON_x]`」逐一对这两源校验，抓出**悬空图标名**
（解析不到 = 游戏里空白）。这是桌面版没有的能力。

## 用法

    # 1) 审计现有文本里的图标名（只读，不写盘）—— 推荐先跑
    python iconify_text.py <工程根> --audit

    # 2) 预演：看会给哪些文本加什么图标（不写盘）
    python iconify_text.py <工程根> --check

    # 3) 实际写入（默认就地改，建议先 git commit）
    python iconify_text.py <工程根> --write

    # 4) 单个文件
    python iconify_text.py --file Text/Localization_RGN.sql --check

    # 5) 自定义映射（JSON: {"关键词": "IconName"}，覆盖内置表）
    python iconify_text.py <工程根> --map my_map.json --check

退出码：0 = 无待改项 / 已写；1 = --check/--audit 发现问题；2 = 用法错误。

## 与 `civ6-modding` 其它工具的关系

- 校验"图标名是否存在"用它的 `--audit`；
- 校验"图标是否真的进了包"（图集/格子/XLP）用 `art/verify_icon_atlas.py`；
- 两者互补：本工具管**文本侧引用是否可解析**，verify_icon_atlas 管**美术侧是否落地**。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_TAGS_SQL = os.path.join(SKILL_DIR, "reference", "sources", "civ6-icon-tags.sql")

# ---------------------------------------------------------------- 内置关键词映射
# 来源：桌面版「图标化文本小工具」的 ICON_MAPPING，逐条经 civ6-icon-tags.sql 校验全数存在。
# 键 = 中文关键词（长词优先匹配），值 = 图标名（不带 ICON_ 前缀，写入时补）。
ICON_MAPPING: dict[str, str] = {
    # 资源产出
    "科技": "Science", "文化": "Culture", "信仰": "Faith", "金币": "Gold",
    "生产力": "Production", "粮食": "Food", "食物": "Food", "旅游业绩": "Tourism",
    "军团": "Corps", "舰队": "Corps", "军队": "Army", "无敌舰队": "Army",
    # 城市相关
    "住房": "Housing", "宜居度": "Amenities", "市民": "Citizen", "公民": "Citizen",
    "人口": "Citizen", "总督头衔": "Governor", "电力": "Power", "首都": "Capital",
    # 回合/政策/政体
    "每回合": "Turn", "政策": "Policy", "政体": "Government",
    # 启发/尤里卡
    "鼓舞": "CivicBoosted", "尤里卡": "TechBoosted",
    # 外交/贸易
    "使者": "Envoy", "影响力": "InfluencePerTurn", "贸易路线": "TradeRoute",
    "商路": "TradeRoute", "贸易站": "TradingPost",
    # 宗教/伟人/伟作
    "宗教": "Religion",
    "海军统帅": "GreatAdmiral", "大艺术家": "GreatArtist", "大工程师": "GreatEngineer",
    "大将军": "GreatGeneral", "大商人": "GreatMerchant", "大音乐家": "GreatMusician",
    "大预言家": "GreatProphet", "大科学家": "GreatScientist", "大作家": "GreatWriter",
    "遗物": "GreatWork_Relic",
    # 时代
    "黑暗时代": "GLORY_DARK_AGE", "黄金时代": "GLORY_GOLDEN_AGE",
    "普通时代": "GLORY_NORMAL_AGE", "英雄时代": "GLORY_SUPER_GOLDEN_AGE",
    # 战斗/单位
    "战斗力": "Strength", "攻击力": "Strength", "近战": "Strength", "远程": "Ranged",
    "轰炸": "Bombard", "移动力": "Movement", "射程": "Range", "劳动力": "Charges",
    "使用次数": "Charges", "晋升": "Promotion", "受伤": "Damaged", "生命值": "Damaged",
    "驻扎": "Fortified", "防御": "Fortified",
    # 内容类型
    "野蛮人": "Barbarian", "蛮族": "Barbarian",
    "历史古迹": "RESOURCE_ANTIQUITY_SITE", "海难遗址": "RESOURCE_SHIPWRECK",
}

TOKEN_RE = re.compile(r"\[ICON_([A-Za-z0-9_]+)\]")


def icon_token(name: str) -> str:
    return "[ICON_%s]" % name


def load_vanilla_icons() -> set[str]:
    """官方 [ICON_*] 全表（小写化存储，比较时统一 casefold）。"""
    out: set[str] = set()
    if not os.path.isfile(ICON_TAGS_SQL):
        return out
    try:
        con = sqlite3.connect(":memory:")
        con.executescript(open(ICON_TAGS_SQL, encoding="utf-8").read())
        for (s,) in con.execute("SELECT IconString FROM Icon_Collection"):
            m = TOKEN_RE.fullmatch((s or "").strip())
            if m:
                out.add(m.group(1).casefold())
        con.close()
    except Exception as e:
        print("WARN 读取官方图标表失败：%s" % e, file=sys.stderr)
    return out


def load_project_icons(root: str) -> tuple[set[str], set[str]]:
    """扫工程 Icons XML → (IconDefinitions 名, IconTextureAtlases 名)，均 casefold。

    用**按块解析**而非全文件正则：IconDefinitions 的 `<Row Name=...>` 与
    IconTextureAtlases 的同形，只有落在各自容器块内才归属正确
    （全文件正则会把图集名混进定义名）。
    """
    defs: set[str] = set()
    atlases: set[str] = set()
    cands: list[str] = []
    for pat in ("Data/*.xml", "Mod_Adaptation/**/*.xml", "*.xml"):
        cands += glob.glob(os.path.join(root, pat), recursive=True)
    for p in sorted(set(cands)):
        try:
            txt = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if "IconDefinitions" not in txt and "IconTextureAtlases" not in txt:
            continue
        for sec, sink in (("IconDefinitions", defs), ("IconTextureAtlases", atlases)):
            for bm in re.finditer(
                    r"<%s\b[^>]*>(.*?)</%s>" % (sec, sec), txt, re.S | re.I):
                for rm in re.finditer(r"<Row\b[^>]*?\bName=\"([^\"]+)\"", bm.group(1)):
                    sink.add(rm.group(1).casefold())
    return defs, atlases


# ---------------------------------------------------------------- 图标化核心

def iconify_text(text: str, mapping: dict[str, str]) -> str:
    """为关键词插入 ICON 标记（幂等：已有同名标记则跳过）。

    幂等判据：关键词左侧紧邻（允许中间夹空白）已是同一个 `[ICON_x]`
    （名称大小写不敏感）。长关键词优先，避免"科技点数"被"科技"先切。
    """
    if not text:
        return text
    items = sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
    result = text
    for keyword, icon_name in items:
        if not keyword:
            continue
        token = icon_token(icon_name)
        want = icon_name.casefold()
        start = 0
        while True:
            pos = result.find(keyword, start)
            if pos < 0:
                break
            j = pos
            while j > 0 and result[j - 1].isspace():
                j -= 1
            has = False
            if j > 0:
                m = re.search(r"\[ICON_([A-Za-z0-9_]+)\]$", result[max(0, j - 128):j])
                if m and m.group(1).casefold() == want:
                    has = True
            if has:
                start = pos + len(keyword)
                continue
            result = result[:pos] + token + result[pos:]
            start = pos + len(token) + len(keyword)
    return result


# ---------------------------------------------------------------- 文本解析
# 只处理 LocalizedText 的写入：SQL 的 (Language, Tag, Text) 三元组 + XML 的
# <Row Language= Tag= Text= /> 与元素式 <Row><Language/><Tag/><Text/></Row>。

_SQL_INSERT_RE = re.compile(
    r"INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+LocalizedText\s*\(([^)]*)\)\s*VALUES",
    re.I)


def _split_sql_literals(s: str) -> list[tuple[str, int, int]]:
    """从一段 SQL 里切出字符串字面量 → [(解码值, 起点, 终点)]，span 只覆盖引号内。"""
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] != "'":
            i += 1
            continue
        j, start, parts = i + 1, i + 1, []
        while j < n:
            if s[j] == "'":
                if j + 1 < n and s[j + 1] == "'":
                    parts.append(s[start:j]); parts.append("'")
                    j += 2; start = j; continue
                parts.append(s[start:j])
                out.append(("".join(parts), i + 1, j))
                i = j + 1
                break
            j += 1
        else:
            break
    return out


def _skip_ws_comments(s: str, i: int) -> int:
    """跳过空白与 SQL 注释（`-- 行注释` / `/* 块注释 */`）。

    必须支持注释：本项目实际文本文件在多行 VALUES 的各元组之间夹着
    `-- ===== 分节标题 =====` 行注释。
    """
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif s.startswith("--", i):
            j = s.find("\n", i)
            i = n if j < 0 else j + 1
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            break
    return i


def _read_paren_group(s: str, i: int) -> tuple[str, int] | None:
    """从 s[i]=='(' 起读一个配平括号组 → (组内容含括号, 组后位置)。"""
    n, depth, start = len(s), 1, i
    j = i + 1
    while j < n:
        c = s[j]
        if c == "'":                      # 跳过字符串字面量（内含括号不算配平）
            j += 1
            while j < n:
                if s[j] == "'":
                    if j + 1 < n and s[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return s[start:j + 1], j + 1
        j += 1
    return None


def parse_sql_entries(content: str) -> list[dict]:
    """解析 `INSERT ... INTO LocalizedText (Tag, Language, Text) VALUES (...),(...)...`。

    两个必须支持的实况（本项目真实文本文件就是这样，桌面版解析器在此漏掉绝大多数行）：

    1. **多行 VALUES**：一条 INSERT 后跟逗号分隔的多个元组；
    2. **元组之间夹 SQL 注释**（`-- ===== 分节 =====`）。

    三元组按**列名**定位（顺序任意，实际工程里既有 `(Language, Tag, Text)`
    也有 `(Tag, Language, Text)`）。
    """
    entries: list[dict] = []
    for m in _SQL_INSERT_RE.finditer(content):
        cols = [c.strip().strip('"[]`').lower() for c in m.group(1).split(",")]
        try:
            i_lang, i_tag, i_text = cols.index("language"), cols.index("tag"), cols.index("text")
        except ValueError:
            continue
        i = _skip_ws_comments(content, m.end())
        while i < len(content) and content[i] == "(":
            got = _read_paren_group(content, i)
            if not got:
                break
            group, after = got
            lits = _split_sql_literals(group)
            if max(i_lang, i_tag, i_text) < len(lits):
                lang, tag, txt = lits[i_lang], lits[i_tag], lits[i_text]
                entries.append({
                    "language": lang[0], "tag": tag[0], "text": txt[0],
                    "start": i + txt[1], "end": i + txt[2],
                    "enc": lambda v: v.replace("'", "''"),
                })
            # 下一个：跳过空白/注释，遇到逗号继续，否则该 INSERT 结束
            j = _skip_ws_comments(content, after)
            if j < len(content) and content[j] == ",":
                i = _skip_ws_comments(content, j + 1)
            else:
                break
    return entries


def _xml_unescape(v: str) -> str:
    return (v.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
             .replace("&apos;", "'").replace("&amp;", "&"))


def _xml_escape_attr(v: str, quote: str) -> str:
    v = v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return v.replace('"', "&quot;") if quote == '"' else v.replace("'", "&apos;")


def _xml_escape_text(v: str) -> str:
    return v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse_xml_entries(content: str) -> list[dict]:
    entries: list[dict] = []
    seen: set[tuple[int, int]] = set()
    # 属性式：<Row Language=".." Tag=".." Text=".." />（含自闭合）
    for m in re.finditer(r"<(?:Row|Replace)\b[^>]*?/?>", content, re.I | re.S):
        tag_src = m.group(0)
        attrs: dict[str, tuple[str, int, int, str]] = {}
        for am in re.finditer(r"([A-Za-z_:][\w:.-]*)\s*=\s*([\"'])(.*?)\2", tag_src, re.S):
            attrs[am.group(1).lower()] = (
                _xml_unescape(am.group(3)),
                m.start() + am.start(3), m.start() + am.end(3), am.group(2))
        if {"language", "tag", "text"} <= set(attrs):
            tv, s, e, q = attrs["text"]
            if (s, e) in seen:
                continue
            seen.add((s, e))
            entries.append({"language": attrs["language"][0], "tag": attrs["tag"][0],
                            "text": tv, "start": s, "end": e,
                            "enc": lambda v, _q=q: _xml_escape_attr(v, _q)})
    # 元素式：<Row><Language/><Tag/><Text/></Row>
    for m in re.finditer(r"<Row\b[^>]*>(.*?)</Row>", content, re.I | re.S):
        inner, base = m.group(1), m.start(0)
        off = m.group(0).find(inner)
        lm = re.search(r"<Language\b[^>]*>(.*?)</Language>", inner, re.I | re.S)
        tm = re.search(r"<Tag\b[^>]*>(.*?)</Tag>", inner, re.I | re.S)
        xm = re.search(r"<Text\b[^>]*>(.*?)</Text>", inner, re.I | re.S)
        if not (lm and tm and xm):
            continue
        s = base + off + xm.start(1)
        e = base + off + xm.end(1)
        if (s, e) in seen:
            continue
        seen.add((s, e))
        entries.append({"language": _xml_unescape(lm.group(1).strip()),
                        "tag": _xml_unescape(tm.group(1).strip()),
                        "text": _xml_unescape(xm.group(1)),
                        "start": s, "end": e, "enc": _xml_escape_text})
    return entries


def read_text_file(path: str):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig" if bom else "utf-8"), ("utf-8-sig" if bom else "utf-8")


def find_text_files(root: str) -> list[str]:
    out: list[str] = []
    for pat in ("Text/**/*.sql", "Text/**/*.xml"):
        out += glob.glob(os.path.join(root, pat), recursive=True)
    return sorted(set(out))


def apply_entries(content: str, entries: list[dict]) -> str:
    reps = sorted(((e["start"], e["end"], e["enc"](e["new"])) for e in entries),
                  key=lambda t: t[0], reverse=True)
    out = content
    for s, e, r in reps:
        if s < 0 or e < s or e > len(out):
            raise ValueError("非法替换区间 %d-%d" % (s, e))
        out = out[:s] + r + out[e:]
    return out


def collect_icons(content: str) -> list[str]:
    return TOKEN_RE.findall(content)


# ---------------------------------------------------------------- 主流程

def process_file(path: str, mapping: dict[str, str], known: set[str],
                 audit_only: bool):
    """→ (entries, changed_count, 未知图标名 list, 原内容, 编码)"""
    content, enc = read_text_file(path)
    if audit_only:
        # 精确审计：只看解析出来的 Text 值（避免把注释里的 [ICON_x] 当成真引用）；
        # 解析不出条目时退化为整文件扫描，保证不漏。
        try:
            parsed = (parse_sql_entries(content) if path.lower().endswith(".sql")
                      else parse_xml_entries(content))
        except Exception:
            parsed = []
        blob = "\n".join(e["text"] for e in parsed) if parsed else content
        return [], 0, sorted({n for n in collect_icons(blob) if n.casefold() not in known}), content, enc
    entries = parse_sql_entries(content) if path.lower().endswith(".sql") else parse_xml_entries(content)
    changed = 0
    unknown: list[str] = []
    for e in entries:
        new = iconify_text(e["text"], mapping)
        e["new"] = new
        if new != e["text"]:
            changed += 1
        unknown += [n for n in collect_icons(new) if n.casefold() not in known]
    return entries, changed, sorted(set(unknown)), content, enc


def main() -> int:
    ap = argparse.ArgumentParser(description="给游戏文本自动插入 [ICON_x]（带权威图标名校验）")
    ap.add_argument("root", nargs="?", help="工程根目录（含 Text/）")
    ap.add_argument("--file", action="append", default=[], help="只处理指定文件（可重复）")
    ap.add_argument("--audit", action="store_true", help="只审计现有 [ICON_x] 是否可解析（不写盘）")
    ap.add_argument("--check", action="store_true", help="预演，列出待改项（不写盘）")
    ap.add_argument("--write", action="store_true", help="实际写入")
    ap.add_argument("--map", dest="map_file", help="自定义映射 JSON（覆盖内置，值为图标名）")
    ap.add_argument("--show-all", action="store_true", help="列出全部待改条目（默认只列前 40）")
    args = ap.parse_args()

    if not (args.audit or args.check or args.write):
        ap.error("需要 --audit / --check / --write 之一")
    if not args.root and not args.file:
        ap.error("需要给工程根目录，或用 --file 指定文件")

    mapping = dict(ICON_MAPPING)
    if args.map_file:
        try:
            with open(args.map_file, encoding="utf-8") as f:
                mapping.update(json.load(f))
        except Exception as e:
            print("读取映射失败：%s" % e, file=sys.stderr)
            return 2

    vanilla = load_vanilla_icons()
    pdefs, patlases = load_project_icons(args.root) if args.root else (set(), set())
    known = vanilla | pdefs | patlases
    print("图标名来源：官方全表 %d 个 + 工程 IconDefinitions %d 个 + 图集 %d 个"
          % (len(vanilla), len(pdefs), len(patlases)))
    if not vanilla:
        print("  WARN 官方图标表缺失（%s）—— --audit 会大量误报" % ICON_TAGS_SQL)

    files = list(args.file) if args.file else find_text_files(args.root)
    if not files:
        print("未找到 Text/ 下的 .sql / .xml")
        return 0

    total_changed = total_entries = 0
    unknown_all: dict[str, list[str]] = {}
    previews: list[tuple[str, str, str, str]] = []

    for p in files:
        try:
            entries, changed, unknown, _content, _enc = process_file(
                p, mapping, known, args.audit)
        except UnicodeDecodeError as e:
            print("WARN 非 UTF-8 跳过 %s：%s" % (p, e))
            continue
        except Exception as e:
            print("WARN 解析失败 %s：%s" % (p, e))
            continue
        if unknown:
            unknown_all[os.path.relpath(p, args.root or ".")] = unknown
        if args.audit:
            continue
        total_entries += len(entries)
        total_changed += changed
        for e in entries:
            if e["new"] != e["text"]:
                previews.append((os.path.basename(p), e["tag"], e["text"], e["new"]))

    if args.audit:
        print("\n=== 图标名审计（解析不到 = 游戏内空白） ===")
        if not unknown_all:
            print("  全部 [ICON_x] 均可解析。")
            return 0
        bad = 0
        for f, names in sorted(unknown_all.items()):
            print("  %s" % f)
            for n in names:
                print("      [ICON_%s]  ← 解析不到" % n)
                bad += 1
        print("\nFAIL: %d 处悬空图标名" % bad)
        return 1

    print("\n条目 %d 条，其中需改 %d 条" % (total_entries, total_changed))
    if previews:
        lim = len(previews) if args.show_all else min(40, len(previews))
        print("\n待改预览（前 %d 条）：" % lim)
        for f, tag, old, new in previews[:lim]:
            print("  [%s] %s" % (f, tag))
            print("      - %s" % old[:110])
            print("      + %s" % new[:110])
        if len(previews) > lim:
            print("  ... 另 %d 条（--show-all 全列）" % (len(previews) - lim))

    if unknown_all:
        print("\n注意：以下文件的图标名解析不到（写入后游戏内会空白）：")
        for f, names in sorted(unknown_all.items()):
            print("  %s: %s" % (f, ", ".join("[ICON_%s]" % n for n in names)))

    if args.write:
        if not total_changed:
            print("\n无需写入。")
            return 0
        written = 0
        for p in files:
            try:
                entries, changed, _u, content, enc = process_file(p, mapping, known, False)
            except Exception:
                continue
            if not changed:
                continue
            new_content = apply_entries(content, [e for e in entries if e["new"] != e["text"]])
            # newline="" 防止 Windows 把已有 \r\n 变成 \r\r\n（原桌面版同款处理）
            with open(p, "w", encoding=enc, newline="") as f:
                f.write(new_content)
            written += 1
        print("\n已写入 %d 个文件（保持原编码与换行）。" % written)
        return 0

    if total_changed:
        print("\n[--check] %d 条待改。加 --write 执行（建议先 git commit）。" % total_changed)
        return 1
    print("\n无需改动。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
