# -*- coding: utf-8 -*-
r"""workshop_intro.py — 工坊介绍「丙栏」（`[code]` 主体）提取与依赖清单生成

配合 `workshop-intro.md` 的三栏口径使用：丙栏（能力与条目描述）由本工具从工程
`Text/` 的本地化文本提取；甲栏（点赞横幅、QQ 群行）取自 `release/templates/`
的预置模板；乙栏（前置行、标语、致谢、写在最后）由用户逐字提供，本工具不生成。

子命令：

    python workshop_intro.py scan   <源工程根> [--lang schinese] [--kind ABILITY,DISTRICT]
    python workshop_intro.py build  <源工程根> --order <order.json> --langs <codes> --out <spec.json>
    python workshop_intro.py titles <源工程根> [--spec <spec.json> [--write]] [--json]
    python workshop_intro.py deps   <源工程根> [--json]

`scan` 把候选 tag 按条目类型分组打印（含文本首段），供 agent 编写 `order.json`；
`build` 按 `order.json` 的节序产出各语言 `[code]` 主体、规格 JSON 与缺失 tag 清单；
`titles` 取工程 `.civ6proj`（或同目录 / 同名的 `.modinfo`）里的 `..._MOD_TITLE` 各语言文本，
作者未明确指定标题时以它为准，可用 `--spec ... --write` 直接回填规格 JSON 的空 `title`；
`deps` 读 `.civ6proj` 的 `<AssociationData>`，区分官方 DLC 与工坊作品（后者反查数字工坊 ID）。

文本来源与工程布局：简中在 `Text/*.sql`（`Language = 'zh_Hans_CN'`），其余语言在
`Text/<locale>/Text_*.sql`（`zh_Hant_HK` / `en_US` / `ja_JP` / `ko_KR` / `de_DE` /
`es_ES` / `fr_FR`）。同一 tag 在多文件出现时后读到的覆盖先读到的。

退出码：0 成功 / 1 参数或读取错误 / 2 有缺失或未解析项（可继续，须人工补齐）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 工坊语言代码 ↔ 工程 Text 目录名。schinese 走工程根 Text/*.sql（Language = zh_Hans_CN）
LOCALE_OF = {
    "english": "en_US",
    "schinese": "zh_Hans_CN",
    "tchinese": "zh_Hant_HK",
    "japanese": "ja_JP",
    "koreana": "ko_KR",
    "german": "de_DE",
    "spanish": "es_ES",
    "french": "fr_FR",
}
LANG_OF_LOCALE = {v: k for k, v in LOCALE_OF.items()}
DEFAULT_LANGS = ["english", "schinese", "tchinese", "japanese", "koreana",
                 "german", "spanish", "french"]

# 文本行的解析：INSERT ... VALUES ('LOC_X', 'en_US', '文本'), —— 文本内的单引号写成 ''
ROW_RE = re.compile(
    r"\(\s*'(LOC_[A-Za-z0-9_]+)'\s*,\s*'([A-Za-z_]+)'\s*,\s*'(.*?)'\s*\)\s*[,;]",
    re.S,
)
TAG_RE = re.compile(r"\{([A-Za-z0-9_]+)\}")

# 清除游戏内标记：[ICON_x] [NEWLINE] [COLOR:xxx] [ENDCOLOR] 等
MARKER_RE = re.compile(r"\[(?:ICON_[A-Za-z0-9_]+|NEWLINE|COLOR:[^\]]*|ENDCOLOR|NUMBER|SPEAKER[^\]]*)\]")

# 标记连同它前后的半角空格一起吃掉：「获得 [ICON_X] 权能点」→「获得权能点」
SPACED_MARKER_RE = re.compile(r"[ \t]*" + MARKER_RE.pattern + r"[ \t]*")


def drop_marker(m: re.Match) -> str:
    """标记两侧都是 ASCII 字母数字时留一个空格，避免英文单词粘连。"""
    left = m.string[m.start() - 1] if m.start() else ""
    right = m.string[m.end()] if m.end() < len(m.string) else ""
    if left.isascii() and left.isalnum() and right.isascii() and right.isalnum():
        return " "
    return ""

# 中日韩字符与全角标点的区间，用于清理标记清除后残留的半角空格
CJK = "\u3000-\u303f\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef"

KIND_RULES = [
    ("总督晋升", r"_GOV_PROMO_"),
    ("特色总督", r"_GOVERNOR_"),
    ("文明 / 领袖能力", r"_TRAIT_"),
    ("特色项目", r"_PROJECT_"),
    ("特色改良设施", r"_IMPROVEMENT_"),
    ("特色区域", r"_DISTRICT_"),
    ("特色建筑", r"_BUILDING_"),
    ("特色伟人", r"_(?:GREAT_PERSON|GREATPERSON)_"),
    ("单位", r"_UNIT_"),
    ("能力", r"_ABILITY_"),
    ("领袖", r"_LEADER_"),
    ("文明", r"_CIVILIZATION_"),
]
KIND_ORDER = [k for k, _ in KIND_RULES]


def kind_of(tag: str) -> str:
    for name, pat in KIND_RULES:
        if re.search(pat, tag):
            return name
    return "其他"


def load_text(project: str) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    """返回 ({language: {tag: text}}, {language: 未解析的 LOC 行数})。

    语言以数据行自带的 Language 列为准（同一文件里可以按语言分块混排，如丹瑾的
    `Text/Text_Danjin.sql`），目录名只用于说明文本来源位置。
    """
    text_root = os.path.join(project, "Text")
    if not os.path.isdir(text_root):
        raise SystemExit("FAIL 找不到 Text 目录：%s" % text_root)

    table: dict[str, dict[str, str]] = {lang: {} for lang in DEFAULT_LANGS}
    unparsed: dict[str, int] = {lang: 0 for lang in DEFAULT_LANGS}

    for dirpath, _dirnames, filenames in os.walk(text_root):
        for name in sorted(filenames):
            if not name.lower().endswith(".sql"):
                continue
            raw = open(os.path.join(dirpath, name), encoding="utf-8", errors="replace").read()
            found = 0
            for m in ROW_RE.finditer(raw):
                tag, row_lang, value = m.group(1), m.group(2), m.group(3)
                lang = LANG_OF_LOCALE.get(row_lang)
                if lang is None:
                    continue
                table[lang][tag] = value.replace("''", "'")
                found += 1
            # 行首为 '('LOC_ 的才是数据行；差额即格式异常的待核对项
            rows = len(re.findall(r"\(\s*'LOC_[A-Za-z0-9_]+'\s*,", raw))
            if rows > found:
                lang = LANG_OF_LOCALE.get(rel_locale(dirpath, text_root)) or "schinese"
                unparsed[lang] += rows - found
    return table, unparsed


def rel_locale(dirpath: str, text_root: str) -> str:
    """文件所在目录名推断的工程语言目录（仅用于统计未解析行）。"""
    rel = os.path.relpath(dirpath, text_root)
    return "zh_Hans_CN" if rel == "." else rel.split(os.sep)[0]


def clean_text(value: str, table: dict[str, str], expand: bool, depth: int = 0) -> str:
    """展开 {LOC_X} 引用、清除标记、收敛空白与标点。"""
    if expand and depth < 5:
        for _ in range(5):
            refs = [t for t in TAG_RE.findall(value) if t in table]
            if not refs:
                break
            for ref in refs:
                value = value.replace("{%s}" % ref, clean_text(table[ref], table, expand, depth + 1))
    value = SPACED_MARKER_RE.sub(drop_marker, value)
    value = TAG_RE.sub("", value)
    value = re.sub(r"[ \t]{2,}", " ", value)
    value = re.sub(r"\s*\n+\s*", " ", value)
    # 标记清除与引用展开会留下紧贴中文的空格、以及重复句读
    value = re.sub("(?<=[" + CJK + r"])[ ]+(?=[0-9A-Za-z+%])", "", value)
    value = re.sub("(?<=[0-9A-Za-z+%])[ ]+(?=[" + CJK + r"])", "", value)
    value = re.sub(r"(?<!\.)\.\.(?!\.)", ".", value)
    for pair, one in (("。。", "。"), ("，，", "，"), ("；；", "；"), ("：：", "："),
                      ("、、", "、"), ("（）", "")):
        value = value.replace(pair, one)
    return value.strip()


def label_from(order_label: str, table: dict[str, str], problems: list[str], lang: str) -> str:
    """把 label 里的 {LOC_X} 换成该语言文本；缺文本时记问题并保留 tag 名。"""
    out = order_label
    for tag in TAG_RE.findall(order_label):
        if tag in table:
            out = out.replace("{%s}" % tag, clean_text(table[tag], table, True))
        else:
            problems.append("%s：label 引用的 %s 无文本" % (lang, tag))
    return out


def cmd_scan(args) -> int:
    table, unparsed = load_text(args.project)
    lang = args.lang
    if lang not in table:
        raise SystemExit("FAIL 未知语言代码：%s" % lang)
    texts = table[lang]
    kinds = args.kind.split(",") if args.kind else KIND_ORDER + ["其他"]

    print("工程：%s" % os.path.abspath(args.project))
    print("语言：%s（工程目录 %s）｜tag 总数 %d" % (lang, LOCALE_OF[lang], len(texts)))
    if unparsed[lang]:
        print("WARN 有 %d 处 LOC_ 未按标准 INSERT 行解析，需人工核对" % unparsed[lang])
    for kind in kinds:
        tags = [t for t in sorted(texts) if kind_of(t) == kind]
        if not tags:
            continue
        print("\n== %s（%d）==" % (kind, len(tags)))
        for tag in tags:
            body = re.sub(r"\s+", " ", texts[tag]).strip()
            print("  %-58s %s" % (tag, body[:70]))
    print("\n提示：把选中的 tag 写进 order.json 的 sections（text 取 *_DESCRIPTION，"
          "label 可写 {LOC_..._NAME} 或自拟文字）。")
    return 0


def cmd_build(args) -> int:
    langs = [x.strip() for x in args.langs.split(",") if x.strip()] or DEFAULT_LANGS
    table, unparsed = load_text(args.project)
    order = json.load(open(args.order, encoding="utf-8"))
    sections = order.get("sections") or []
    if not sections:
        raise SystemExit("FAIL order.json 的 sections 为空")

    problems: list[str] = []
    blocks = []
    for lang in langs:
        texts = table.get(lang)
        if texts is None:
            raise SystemExit("FAIL 未知语言代码：%s" % lang)
        lines: list[str] = ["[code]"]
        first_block = True
        for sec in sections:
            level = int(sec.get("level", 3))
            text_tag = sec.get("text")
            label = sec.get("label")
            if label is None:
                if not text_tag:
                    problems.append("%s：有 section 既无 label 也无 text" % lang)
                    continue
                label = "{%s}" % re.sub(r"_DESCRIPTION$", "_NAME", text_tag)
            title = label_from(label, texts, problems, lang)
            if text_tag:
                if text_tag not in texts:
                    problems.append("%s：缺文本 %s" % (lang, text_tag))
                    continue
                body = clean_text(texts[text_tag], texts, expand=not args.no_expand)
            else:
                body = ""
            if level <= 2:
                if not first_block:
                    lines.append("[hr][/hr]")
                first_block = False
                lines.append("[h%d]%s[/h%d]" % (level, title, level))
            else:
                lines.append("[h3]%s[/h3]" % title)
            if body:
                lines.append(body)
            lines.append("")
        lines.append("[/code]")
        blocks.append({"language": lang, "title": "", "body": "\n".join(lines).rstrip() + "\n"})

    spec = {
        "mode": "create",
        "changeNote": "首次发布 / Initial release",
        "visibility": "public",
        "tags": [],
        "dependencies": [],
        "preamble": {},
        "postamble": {},
        "blocks": blocks,
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写入规格 JSON：%s（mode=create，preamble / postamble 留空待填）" % args.out)

    for block in blocks:
        size = len(block["body"].encode("utf-8"))
        print("  %-9s 丙栏 %6d B  %5d 字符" % (block["language"], size, len(block["body"])))
    print("提示：title 与甲、乙两栏按 workshop-intro.md 的口径填入；"
          "dependencies 由 `deps` 子命令产出。")

    if problems:
        seen = []
        for p in problems:
            if p not in seen:
                seen.append(p)
        print("\n缺失 / 待补（%d）:" % len(seen))
        for p in seen[:80]:
            print("  - " + p)
        if len(seen) > 80:
            print("  …… 其余 %d 项从略" % (len(seen) - 80))
        return 2
    return 0


def read_mod_titles(project: str) -> tuple[dict[str, str], str]:
    """取工程里的各语言 Mod 标题：返回 ({language: title}, 来源路径)。

    来源优先 `.civ6proj` 的 `<LocalizedTextData>` CDATA（源工程唯一真源），
    其次同目录或 Mods 副本里的 `<ModName>.modinfo`。取 `<Text id="..._MOD_TITLE">`，
    找不到时退回 id 以 `_TITLE` 结尾的第一个条目。
    """
    candidates = []
    for name in sorted(os.listdir(project)):
        if name.endswith(".civ6proj"):
            candidates.append(os.path.join(project, name))
    for name in sorted(os.listdir(project)):
        if name.lower().endswith(".modinfo"):
            candidates.append(os.path.join(project, name))
    if not candidates:
        raise SystemExit("FAIL 工程根下既没有 .civ6proj 也没有 .modinfo：%s" % project)

    for path in candidates:
        raw = open(path, encoding="utf-8", errors="replace").read()
        blocks = re.findall(r"<LocalizedText[ >](.*?)</LocalizedText>", raw, re.S)
        if not blocks:
            m = re.search(r"<LocalizedTextData><!\[CDATA\[(.*?)\]\]></LocalizedTextData>", raw, re.S)
            blocks = [m.group(1)] if m else []
        for block in blocks:
            entries = re.findall(r'<Text\s+id="([^"]+)"\s*>(.*?)</Text>', block, re.S)
            if not entries:
                continue
            chosen = None
            for tag, body in entries:
                if tag.endswith("_MOD_TITLE"):
                    chosen = body
                    break
            if chosen is None:
                for tag, body in entries:
                    if tag.endswith("_TITLE"):
                        chosen = body
                        break
            if chosen is None:
                continue
            titles = {}
            for locale, text in re.findall(r"<([A-Za-z_]+)>([^<]*)</\1>", chosen):
                lang = LANG_OF_LOCALE.get(locale)
                if lang:
                    titles[lang] = text.strip()
            if titles:
                return titles, path
    raise SystemExit("FAIL 未找到 ..._MOD_TITLE 条目：%s" % ", ".join(candidates))


def cmd_titles(args) -> int:
    titles, source = read_mod_titles(args.project)
    print("标题来源：%s" % source)
    print("%-9s %6s  %s" % ("language", "bytes", "title"))
    over = []
    for lang in DEFAULT_LANGS:
        text = titles.get(lang)
        if text is None:
            print("%-9s %6s  （缺该语言标题）" % (lang, "-"))
            continue
        nb = len(text.encode("utf-8"))
        flag = "" if nb <= 128 else "  ★ 超 128 字节"
        if nb > 128:
            over.append(lang)
        print("%-9s %6d  %s%s" % (lang, nb, text, flag))
    print("提示：上传器标题上限 k_cchPublishedDocumentTitleMax = 128 + 1（含结尾的 NUL），"
          "按 UTF-8 字节判定。")

    if args.json:
        print(json.dumps(titles, ensure_ascii=False, indent=2))

    if args.spec:
        spec = json.load(open(args.spec, encoding="utf-8"))
        filled, kept = [], []
        for block in spec.get("blocks") or []:
            lang = block.get("language")
            if not lang:
                continue
            if block.get("title"):
                kept.append(lang)
                continue
            if lang in titles:
                block["title"] = titles[lang]
                filled.append(lang)
        if args.write:
            with open(args.spec, "w", encoding="utf-8", newline="\n") as f:
                json.dump(spec, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print("已回填 %d 个语言标题 → %s（%s）"
                  % (len(filled), args.spec, ", ".join(filled) or "无"))
        else:
            print("预演：将回填 %d 个语言标题（%s）；加 --write 才写入"
                  % (len(filled), ", ".join(filled) or "无"))
        if kept:
            print("保留作者已指定的标题（%d 个）：%s" % (len(kept), ", ".join(kept)))
        missing = [b.get("language") for b in spec.get("blocks") or []
                   if b.get("language") and not b.get("title")]
        if missing:
            print("★ 仍未填标题的语言：%s（modinfo 无对应标题，需作者给出）" % ", ".join(missing))
            return 2

    return 2 if over else 0


def parse_dependencies(project: str) -> list[dict]:
    """从 .civ6proj 的 <AssociationData> 里取依赖条目。"""
    cands = [os.path.join(project, n) for n in os.listdir(project) if n.endswith(".civ6proj")]
    if not cands:
        raise SystemExit("FAIL 工程根下没有 .civ6proj：%s" % project)
    raw = open(cands[0], encoding="utf-8", errors="replace").read()
    m = re.search(r"<AssociationData><!\[CDATA\[(.*?)\]\]></AssociationData>", raw, re.S)
    if not m:
        return []
    out = []
    for dep in re.finditer(
            r'<Dependency\s+type="([^"]+)"\s+title="([^"]*)"\s+id="([^"]+)"\s*/?>',
            m.group(1)):
        out.append({"type": dep.group(1), "title": dep.group(2), "guid": dep.group(3)})
    return out


def _self_guids(root: str, max_dirs: int = 4000) -> dict[str, list[str]]:
    """扫描一个 mod 根目录：{guid: [目录名, ...]}（只认 modinfo 自身的 <Mod id=）。"""
    table: dict[str, list[str]] = {}
    if not root or not os.path.isdir(root):
        return table
    n = 0
    for entry in sorted(os.listdir(root)):
        sub = os.path.join(root, entry)
        if not os.path.isdir(sub):
            continue
        n += 1
        if n > max_dirs:
            break
        for name in os.listdir(sub):
            if not name.lower().endswith(".modinfo"):
                continue
            try:
                head = open(os.path.join(sub, name), encoding="utf-8", errors="replace").read(2000)
            except OSError:
                continue
            m = re.search(r'<Mod\s+id="([0-9A-Fa-f\-]{36})"', head)
            if m:
                table.setdefault(m.group(1).lower(), []).append(entry)
    return table


def cmd_deps(args) -> int:
    deps = parse_dependencies(args.project)
    if not deps:
        print("未声明任何依赖（.civ6proj 的 <AssociationData> 为空）")
        return 0

    ws_root = _paths.get("workshop_ref", must_exist=False)
    mods_root = _paths.get("mods", must_exist=False)
    ws_table = _self_guids(ws_root) if ws_root else {}
    mods_table = _self_guids(mods_root) if mods_root else {}

    workshop_ids: list[str] = []
    dlcs: list[dict] = []
    unknown: list[dict] = []
    for dep in deps:
        guid = dep["guid"].lower()
        if dep["type"].lower() == "dlc":
            dlcs.append(dep)
            continue
        if guid in ws_table:
            for wid in ws_table[guid]:
                if wid.isdigit() and wid not in workshop_ids:
                    workshop_ids.append(wid)
            dep["resolve"] = "workshop"
        elif guid in mods_table:
            dep["resolve"] = "local-mods"
            unknown.append(dep)
        else:
            dep["resolve"] = "unresolved"
            unknown.append(dep)

    if args.json:
        print(json.dumps({"dependencies": workshop_ids, "dlc": dlcs, "unresolved": unknown},
                         ensure_ascii=False, indent=2))
    else:
        print("工坊 dependencies（写进 workshop.json，数值数组）：")
        print("  %s" % (workshop_ids or "无"))
        print("\n官方 DLC / 资料片（只能在 .civ6proj 与 .modinfo 声明，工坊不接受）：")
        if dlcs:
            for d in dlcs:
                print("  %s  %s" % (d["title"], d["guid"]))
            print("  提示：需要在介绍里提示玩家时，写进乙栏的前置行（由用户提供）。")
        else:
            print("  无")
        print("\n未能解析为工坊条目的依赖（须人工确认）：")
        if unknown:
            for d in unknown:
                print("  [%s] %s  %s" % (d.get("resolve"), d["title"], d["guid"]))
            print("  本地 Mods 目录内的依赖无法作为工坊依赖声明；若对方也有工坊条目，"
                  "把其数字 ID 补进 dependencies。")
        else:
            print("  无")

    return 0 if not unknown else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="工坊介绍丙栏提取与依赖清单生成")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="列出候选 tag（按条目类型分组）")
    p.add_argument("project", help="源工程根（含 .civ6proj 与 Text/）")
    p.add_argument("--lang", default="schinese", choices=DEFAULT_LANGS)
    p.add_argument("--kind", default="", help="只看某几类，逗号分隔，如 ABILITY,DISTRICT")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("build", help="按 order.json 产出各语言 [code] 主体与规格 JSON")
    p.add_argument("project")
    p.add_argument("--order", required=True, help="节序文件 JSON")
    p.add_argument("--langs", default=",".join(DEFAULT_LANGS))
    p.add_argument("--out", required=True, help="输出的规格 JSON 路径")
    p.add_argument("--no-expand", action="store_true", help="不展开 {LOC_X} 引用")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("titles", help="取工程内的各语言 Mod 标题，可回填规格 JSON")
    p.add_argument("project")
    p.add_argument("--spec", default=None, help="规格 JSON；空 title 用工程标题回填")
    p.add_argument("--write", action="store_true", help="真正写入规格 JSON（默认只预演）")
    p.add_argument("--json", action="store_true", help="另打印 JSON 形式")
    p.set_defaults(func=cmd_titles)

    p = sub.add_parser("deps", help="列出官方 DLC 与工坊作品依赖")
    p.add_argument("project")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_deps)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
