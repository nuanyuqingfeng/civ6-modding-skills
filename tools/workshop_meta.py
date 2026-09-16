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
      "dependencies": [],                   // 可省
      "blocks": [
        {"language": "english",  "title": "...", "description": "..."},
        {"language": "schinese", "title": "...", "description": "..."}
      ]
    }

两种模式的差别（照 release.md 的经验）：
  · create —— 写全 title / description / visibility / tags / dependencies + 7 个语言变体。
  · update —— **只写 description + changeNote + 各变体的 description**，不写 title / visibility /
    tags。省略的字段上传器不会触碰（标题、标签、可见性、变体标题都保持原样），
    这是"只改介绍不改身份"的安全写法。

用法：
    python workshop_meta.py <spec.json> --out <workshop.json> [--record <存档txt>]

退出码：0 通过 / 1 规格有错
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VISIBILITIES = {"private", "friends_only", "unlisted", "public"}
MAX_DESC_BYTES = 8000


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

    problems, seen = [], set()
    primary = None
    for b in blocks:
        lang = b.get("language")
        if not lang:
            problems.append("有语言块缺 language")
            continue
        if lang in seen:
            problems.append("语言重复：%s" % lang)
        seen.add(lang)
        desc = b.get("description") or ""
        if not desc:
            problems.append("%s：description 为空" % lang)
        nb = len(desc.encode("utf-8"))
        if nb > MAX_DESC_BYTES:
            problems.append("%s：description %d B 超上限 %d" % (lang, nb, MAX_DESC_BYTES))
        if lang == "english":
            primary = b
        if mode == "create" and not b.get("title"):
            problems.append("%s：create 模式必须给 title" % lang)

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
        cfg["title"] = primary["title"]
        cfg["description"] = primary["description"]
        cfg["visibility"] = vis
        cfg["tags"] = spec.get("tags", [])
        cfg["dependencies"] = spec.get("dependencies", [])
        cfg["localizations"] = [{"language": b["language"], "title": b["title"], "description": b["description"]}
                                for b in blocks if b["language"] != "english"]
    else:
        cfg = {"description": primary["description"], "changeNote": cfg["changeNote"],
               "localizations": [{"language": b["language"], "description": b["description"]}
                                 for b in blocks if b["language"] != "english"]}

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写入 %s（mode=%s）" % (args.out, mode))

    if args.record:
        lines = ["# %s —— 工坊介绍（多语言，线上同源）" % (primary.get("title") or "Mod"), ""]
        for b in blocks:
            d = b["description"]
            lines += ["=" * 60, "★ %s" % b["language"],
                      "【工坊标题】%s" % b.get("title", "(沿用原值)"),
                      "【描述长度】%d" % len(d.encode("utf-8")),
                      "【工坊描述】", d, ""]
        open(args.record, "w", encoding="utf-8", newline="\r\n").write("\n".join(lines))
        print("已写入 %s" % args.record)

    print("%-10s %7s  %s" % ("language", "bytes", "title"))
    for b in blocks:
        print("%-10s %7d  %s" % (b["language"], len(b["description"].encode("utf-8")), b.get("title", "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
