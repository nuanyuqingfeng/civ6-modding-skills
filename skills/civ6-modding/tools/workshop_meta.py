# -*- coding: utf-8 -*-
"""工坊 workshop.json 生成器（多语言）。

把「8 语言标题 + 正文」的规格文件转成 Civ6WorkshopUploader 需要的 `workshop.json`，
避免每次手写 JSON / 漏掉某个语言变体。同时可导出人类可读的介绍存档 txt。

规格文件（JSON，UTF-8）：

    {
      "mode": "create",                     // create = 首次发布；update = 更新
      "changeNote": "首次发布 / Initial release",
      "visibility": "public",               // create 时可省，默认 public
      "tags": ["Mod", "Gameplay"],          // create 时可省
      "dependencies": [3172771643],         // 工坊作品 ID 全量列表（见 workshop-intro.md §四）
      "preamble": {"schinese": "…", "english": "…"},   // 甲栏：点赞横幅、QQ 群行（可省）
      "postamble": {"schinese": "…"},                  // 乙栏：前置行、标语、致谢、写在最后（可省）
      "blocks": [
        {"language": "english",  "title": "…", "body": "…"},   // 丙栏：[code] 主体
        {"language": "schinese", "title": "…", "body": "…"}
      ]
    }

三栏口径（全文见 `workshop-intro.md`）：`preamble`（甲栏，取自 `release/templates/`）、
`body`（丙栏，由 `workshop_intro.py` 从工程 `Text/` 提取）、`postamble`（乙栏，用户提供）；
描述按 甲 + 丙 + 乙 顺序拼接，空栏整段跳过。`blocks[].description` 仍受支持，给出整篇时
不再拼接，两种写法不得同时出现在同一个语言块。

两种模式的差别（照 release.md 的经验）：
  · create —— 写全 title / description / visibility / tags / dependencies + 7 个语言变体。
  · update —— **只写 description + changeNote + 各变体的 description**，不写 title / visibility /
    tags。省略的字段上传器不会触碰（标题、标签、可见性、变体标题都保持原样），
    这是"只改介绍不改身份"的安全写法。★ 但 `dependencies` 例外：上传器每次上传都会按
    给定列表对线上依赖做增删同步，线上有依赖而本次不写 = 依赖被清空。

校验项：语言齐全与不重复、create 必须有 title、description 非空、无占位符残留、
title ≤ 128 字节、description ≤ 8000 字节（两者均按 UTF-8 字节判定，见 workshop-intro.md §六）。

用法：
    python workshop_meta.py <spec.json> --out <workshop.json> [--record <存档txt>]

退出码：0 通过 / 1 规格有错
"""
from __future__ import annotations

import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VISIBILITIES = {"private", "friends_only", "unlisted", "public"}
# 描述上限：k_cchPublishedDocumentDescriptionMax = 8000，Steamworks 文档写明按 UTF-8 字节计
MAX_DESC_BYTES = 8000
# 标题上限：k_cchPublishedDocumentTitleMax = 128 + 1（含结尾 NUL），同样按字节计
MAX_TITLE_BYTES = 128

# 占位符残留：出现即判失败（乙栏未提供时应整节不写，不能留标记）
PLACEHOLDER_RE = re.compile(
    r"(TODO|FIXME|<待填>|<待补>|\{\{|\}\}|xxx|XXX|\.\.\.\.|…待|待用户)", re.I)


def compose(pre: str, body: str, post: str) -> str:
    """按 甲栏 → 丙栏 → 乙栏 拼接，空栏整段跳过。"""
    parts = [x.strip() for x in (pre or "", body or "", post or "") if x and x.strip()]
    return "\n\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="多语言 workshop.json 生成器")
    ap.add_argument("spec", help="规格 JSON 路径")
    ap.add_argument("--out", required=True, help="输出的 workshop.json 路径")
    ap.add_argument("--record", default=None, help="可选：导出人类可读的介绍存档 txt")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    mode = spec.get("mode", "create")
    blocks = spec.get("blocks") or []
    if mode not in ("create", "update"):
        raise SystemExit("mode 只能是 create / update")

    pre_map = spec.get("preamble") or {}
    post_map = spec.get("postamble") or {}
    for name, mp in (("preamble", pre_map), ("postamble", post_map)):
        if not isinstance(mp, dict):
            raise SystemExit("%s 必须是 {语言: 文本} 形式" % name)

    problems, seen = [], set()
    primary = None
    lengths = []
    for b in blocks:
        lang = b.get("language")
        if not lang:
            problems.append("有语言块缺 language")
            continue
        if lang in seen:
            problems.append("语言重复：%s" % lang)
        seen.add(lang)
        # 丙栏（body）与整篇（description）二选一：给 body 时按 甲 + 丙 + 乙 拼接
        if b.get("description"):
            desc = b["description"]
            if b.get("body"):
                problems.append("%s：description 与 body 同时给出，只应保留一种" % lang)
        else:
            desc = compose(pre_map.get(lang, ""), b.get("body", ""), post_map.get(lang, ""))
        if not desc:
            problems.append("%s：description 为空" % lang)
        hit = PLACEHOLDER_RE.search(desc)
        if hit:
            problems.append("%s：description 残留占位符 %r（乙栏未提供时应整节不写）" % (lang, hit.group(0)))
        nb = len(desc.encode("utf-8"))
        lengths.append((lang, nb, len(desc)))
        if nb > MAX_DESC_BYTES:
            problems.append("%s：description %d B 超上限 %d" % (lang, nb, MAX_DESC_BYTES))
        b["_desc"] = desc
        if lang == "english":
            primary = b["_desc"]
            primary_block = b
        if mode == "create" and not b.get("title"):
            problems.append("%s：create 模式必须给 title" % lang)
        if b.get("title"):
            nbt = len(b["title"].encode("utf-8"))
            if nbt > MAX_TITLE_BYTES:
                problems.append("%s：title %d B 超上限 %d（k_cchPublishedDocumentTitleMax）"
                                % (lang, nbt, MAX_TITLE_BYTES))

    if primary is None:
        problems.append("必须有 english 块（上传器强制主变体写 english）")
    vis = spec.get("visibility", "public")
    if vis not in VISIBILITIES:
        problems.append("visibility 非法：%s（可选 %s）" % (vis, "/".join(sorted(VISIBILITIES))))

    if problems:
        print("规格校验失败：")
        for p in problems:
            print("  - " + p)
        return 1

    cfg: dict = {"changeNote": spec.get("changeNote", "")}
    if mode == "create":
        cfg["title"] = primary_block["title"]
        cfg["description"] = primary
        cfg["visibility"] = vis
        cfg["tags"] = spec.get("tags", [])
        cfg["dependencies"] = spec.get("dependencies", [])
        cfg["localizations"] = [{"language": b["language"], "title": b["title"], "description": b["_desc"]}
                                for b in blocks if b["language"] != "english"]
    else:
        cfg = {"description": primary, "changeNote": cfg["changeNote"],
               "localizations": [{"language": b["language"], "description": b["_desc"]}
                                 for b in blocks if b["language"] != "english"]}

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写入 %s（mode=%s）" % (args.out, mode))
    if mode == "create":
        if cfg["dependencies"]:
            print("依赖：%s（上传器每次上传都对线上依赖做增删同步）" % cfg["dependencies"])
        else:
            print("依赖：未声明。若条目需要其他工坊作品，先用 workshop_intro.py deps 取 ID 再填；"
                  "若线上已有依赖，务必写出全量列表。")
        if not pre_map or not post_map:
            print("甲 / 乙栏：preamble / postamble 为空 → 描述只含丙栏（[code] 主体）")

    if args.record:
        lines = ["# %s —— 工坊介绍（多语言，线上同源）" % (primary_block.get("title") or "Mod"), ""]
        for b in blocks:
            lang = b["language"]
            pre = pre_map.get(lang, "")
            post = post_map.get(lang, "")
            lines += ["=" * 60, "★ %s" % lang,
                      "【工坊标题】%s" % b.get("title", "(沿用原值)"),
                      "【描述长度】%d B / %d 字符" % (len(b["_desc"].encode("utf-8")), len(b["_desc"]))]
            if pre:
                lines += ["【甲栏 · 预置模板】", pre]
            lines += ["【丙栏 · [code] 主体，取自工程 Text/】", b.get("body", b["_desc"])]
            if post:
                lines += ["【乙栏 · 用户提供】", post]
            lines.append("")
        open(args.record, "w", encoding="utf-8", newline="\r\n").write("\n".join(lines))
        print("已写入 %s" % args.record)

    print("%-10s %7s %7s  %s" % ("language", "bytes", "chars", "title"))
    for lang, nb, nc in lengths:
        title = next((b.get("title", "-") for b in blocks if b["language"] == lang), "-")
        print("%-10s %7d %7d  %s" % (lang, nb, nc, title))
    return 0


if __name__ == "__main__":
    sys.exit(main())
