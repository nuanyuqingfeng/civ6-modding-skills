# -*- coding: utf-8 -*-
"""交付包体检：源工程 ↔ Mods 副本 ↔ 上传工作区 三处一致性 + .modinfo 结构与引用闭合。

覆盖三类只有"打包之后"才暴露的问题：
  ① 三处不同步 —— Mods 副本（游戏真正加载的）落后于源工程，或上传工作区落后于 Mods；
  ② 悬空引用 —— modinfo 里声明的文件实际不存在（ModBuddy 只拷 `<Content>` 条目，
     只写在 InGameActions 而未进 Content 的文件会漏部署，本项目踩过）；
  ③ 漏登记 —— Mods 目录里躺着 modinfo 未声明的实体文件（会把不该传的东西带上工坊）。

★ **剥离感知**（2026-09-16 起）：发布前会对发布副本跑 `strip_comments.py`（默认只剥 `.lua`），
  于是「Mods 的 .lua ≠ 源 的 .lua」是**预期**的。本工具对此自动放行：
  `.lua` 在三处哈希不一致时，会再算一次 `strip(源)` 比对，
  命中则记为 `OK(已剥离)` 而不计入问题。想强制逐字节一致时加 `--strict`。

★ **cook 产物感知**：`Platforms/Windows/BLPs/**`（AssetEditor/cooker 产出）与任意 `*.dep`
  在源工程里**本就不存在** —— 它们只活在 Mods 副本、且每次 `Rebuild All` 重新生成。
  这类文件也不计入问题（`--strict` 下仍会报），避免长期假红灯淹没真问题。

用法：
    python verify_mod_package.py --src <源工程目录> --mods <Mods/<ModName>>
                                 [--ws <上传工作区 content 目录>] [--files a/b.lua,c.lua]
                                 [--strict]

退出码：0 全部通过 / 1 有问题 / 2 参数或读取错误
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def find_modinfo(mods_dir: str) -> str:
    hits = [f for f in os.listdir(mods_dir) if f.lower().endswith(".modinfo")]
    if not hits:
        raise SystemExit("Mods 目录里没有 .modinfo：%s" % mods_dir)
    if len(hits) > 1:
        print("WARN 发现多个 modinfo，取第一个：%s" % hits)
    return os.path.join(mods_dir, hits[0])


# ── 剥离感知：发布副本的 .lua 已剥注释，不能按逐字节比 ──────────────
_STRIP_TOOLS = os.path.dirname(os.path.abspath(__file__))

# cook 产物：只存在于 Mods 副本，每次 Rebuild All 重新生成；源工程本就没有
#   `.dep` 由 ModBuddy 构建时从 `.civ6proj` 的 `(Mod Art Dependency File)` 占位符派生，
#   文件名随 mod 名变化（如 `<ModName>.dep`），故按后缀判定而不是写死某个名字。
COOK_ARTIFACT_PREFIXES = ("platforms/windows/blps/", "platforms/macos/blps/")
COOK_ARTIFACT_SUFFIXES = (".dep",)


def is_cook_artifact(rel: str) -> bool:
    r = rel.replace("\\", "/").lower()
    return r.startswith(COOK_ARTIFACT_PREFIXES) or r.endswith(COOK_ARTIFACT_SUFFIXES)


def _strip_lua_text(text: str) -> str:
    """复刻 strip_comments.py 的 Lua 剥离 + 折叠空行，用于「目标 == strip(源)」判定。"""
    sys.path.insert(0, _STRIP_TOOLS)
    import strip_comments as sc  # 局部导入：只有需要时才依赖
    work = text.replace("\r\n", "\n")
    out = sc.strip_lua(work)
    out = sc.collapse_blank(out)
    return sc.harmonize_newlines(out, text)


def stripped_lua_matches(src_path: str, other_path: str) -> bool:
    """other 是否等于 strip(源)？用于放行「发布副本已剥注释」这一预期差异。"""
    try:
        src_text = open(src_path, encoding="utf-8", newline="").read()
        other_text = open(other_path, encoding="utf-8", newline="").read()
        return _strip_lua_text(src_text) == other_text
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="交付包三处一致性 + modinfo 结构体检")
    ap.add_argument("--src", required=True, help="ModBuddy 源工程目录（含 .civ6proj）")
    ap.add_argument("--mods", required=True, help="游戏 Mods 副本目录（含 .modinfo）")
    ap.add_argument("--ws", default=None, help="可选：上传工作区 content 目录")
    ap.add_argument("--files", default=None, help="可选：逗号分隔的待比对文件（默认取 modinfo 的 <Files>）")
    ap.add_argument("--strict", action="store_true",
                    help="不做剥离感知：要求三处逐字节一致（发布副本已剥注释时会报不一致，属预期）")
    args = ap.parse_args()

    mods_dir = os.path.abspath(args.mods)
    if not os.path.isdir(mods_dir):
        raise SystemExit("Mods 副本目录不存在：%s" % mods_dir)
    modinfo = find_modinfo(mods_dir)
    raw = open(modinfo, encoding="utf-8").read()
    root = ET.fromstring(raw)

    declared = [f.text for f in root.findall("Files/File") if f.text]
    files = [x.strip() for x in args.files.split(",")] if args.files else declared

    print("modinfo      : %s" % modinfo)
    print("GUID         : %s" % root.get("id"))
    print("version      : %s" % root.get("version"))
    print("Authors      : %s" % (root.findtext("Properties/Authors") or "(未写)"))
    print("LoadOrders   : %s" % (re.findall(r"<LoadOrder>(\d+)</LoadOrder>", raw) or "无"))
    print()

    problems = 0
    stripped_ok = 0
    cook_skipped = 0
    print("%-44s %s" % ("文件", "src / mods / ws"))
    for rel in files:
        rows, ok = [], True
        paths = {}
        for base in (args.src, mods_dir, args.ws):
            if base is None:
                continue
            p = os.path.join(base, rel.replace("/", os.sep))
            paths[base] = p
            if os.path.isfile(p):
                rows.append(sha256(p)[:12])
            else:
                rows.append("缺失")
                ok = False
        if len(set(rows)) != 1:
            ok = False
            # cook 产物感知：源工程本就没有（AssetEditor/cooker 生成，只在 Mods 副本）
            if not args.strict and is_cook_artifact(rel):
                ok = True
                cook_skipped += 1
            # 剥离感知：仅 .lua，且其余副本都等于 strip(源) → 视为预期的「已剥离」
            elif not args.strict and rel.lower().endswith(".lua"):
                src_p = paths.get(args.src)
                others = [p for b, p in paths.items() if b != args.src and os.path.isfile(p)]
                if src_p and os.path.isfile(src_p) and others and \
                        all(stripped_lua_matches(src_p, o) for o in others):
                    ok = True
                    stripped_ok += 1
        problems += 0 if ok else 1
        print("%-44s %s  %s" % (rel, " / ".join(rows),
                                "OK" if ok else "<== 不一致"))

    dangling = [f for f in declared if not os.path.isfile(os.path.join(mods_dir, f.replace("/", os.sep)))]
    if dangling:
        problems += 1
        print("\n悬空引用（modinfo 声明但 Mods 副本没有）：%s" % dangling)

    unregistered = []
    for dirpath, _, names in os.walk(mods_dir):
        for n in names:
            rel = os.path.relpath(os.path.join(dirpath, n), mods_dir).replace(os.sep, "/")
            if not rel.lower().endswith(".modinfo") and rel not in declared:
                unregistered.append(rel)
    if unregistered:
        hard = [r for r in unregistered if not (not args.strict and is_cook_artifact(r))]
        soft = len(unregistered) - len(hard)
        if hard:
            problems += 1
            print("漏登记（在 Mods 副本里但 modinfo 未声明）：%s" % hard)
        if soft:
            print("（另有 %d 个 cook 产物未登记，属预期、不计入问题）" % soft)

    langs = sorted({e.tag for e in root.findall("LocalizedText/Text/*")})
    print("\n本地化语言   : %s（%d 条 Text）" % (", ".join(langs) if langs else "无", len(root.findall("LocalizedText/Text"))))
    if stripped_ok:
        print("剥离感知     : %d 个 .lua 命中「副本 == strip(源)」，按预期差异放行" % stripped_ok)
    if cook_skipped:
        print("cook 产物    : %d 个 BLPs/.dep 只存在于 Mods 副本（源工程本就没有），按预期放行" % cook_skipped)
    if stripped_ok or cook_skipped:
        print("               （以上两类加 --strict 可强制逐字节核对）")
    print("\n结论: %s" % ("全部一致且引用闭合" if problems == 0 else "发现 %d 类问题，见上" % problems))
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
