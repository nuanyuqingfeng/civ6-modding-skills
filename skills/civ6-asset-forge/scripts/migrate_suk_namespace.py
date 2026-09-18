#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""migrate_suk_namespace.py — 把「Suk 选人界面适配」素材从**官方前缀借用**迁到**独立命名空间**

## 为什么迁

Sukritact's Civ Selection Screen 的适配素材原先被命名为

    FALLBACK_NEUTRAL_<KEY>_Suk          ← 立绘（借用了 3D 回退的官方前缀）
    PORTRAIT_<KEY>_BACKGROUND_Suk       ← 背景
    IMG_CONFIG_FOREGROUND_<KEY>_Suk     ← 立绘（早期工程用的另一种写法）
    IMG_CONFIG_BACKGROUND_<KEY>_Suk     ← 背景

问题：`FALLBACK_*` 是**官方 Leader_Fallback 模板的固定命名**，而 Suk 适配是
**UI 贴图（`UserInterface` 类）**——同前缀不同类别，导致
`gen_tex.py` 的 `is_fallback()` 必须额外维护一张 `_UI_PORTRAIT_SUFFIXES` 例外表，
并且到处都要解释"这两类为什么同前缀"。后人极易把 UI 立绘当成 3D 回退。

迁移后进入**独立命名空间**，与官方模板不再共享前缀：

    SUK_UI_PORTRAIT_<KEY>       （原 FALLBACK_NEUTRAL_<KEY>_Suk / IMG_CONFIG_FOREGROUND_<KEY>_Suk）
    SUK_UI_BACKGROUND_<KEY>     （原 PORTRAIT_<KEY>_BACKGROUND_Suk / IMG_CONFIG_BACKGROUND_<KEY>_Suk）

通用规则：**第三方界面适配素材一律走 `<适配对象短名>_UI_<KIND>_<KEY>`，
不复用官方模板前缀**（`FALLBACK_` / `LEADER_` / `ICON_` 等保留给官方语义）。

## 为什么可以随便改（不是猜测）

`Players.Portrait` / `PortraitBackground` 是**自由字符串列**：Suk 界面
`SELECT Portrait, PortraitBackground FROM Players WHERE Domain=? AND LeaderType=?`
读到值后交给 Image 控件显示——贴图名只是"被引用的字符串"，
引擎与 Sukritact 的 mod **都不要求**它叫 `FALLBACK_*` 或带 `_Suk`。

## 用法

    python migrate_suk_namespace.py <工程根>                  # 预演（默认，不写盘）
    python migrate_suk_namespace.py <工程根> --check          # 只体检：有待迁移项则 exit 2
    python migrate_suk_namespace.py <工程根> --write          # 实际执行
    python migrate_suk_namespace.py <工程根> --namespace SUK_UI --write   # 换命名空间前缀

## 改动面（全部自动完成）

1. `.dds` / `.tex` **文件改名**；
2. `.tex` **内部字段**（`m_Name` / `m_RelativePath` / `m_SourceFilePath` 均含该名字）——
   按**字节**替换，不动 GBK/ANSI 编码与换行；
3. 引用该名字的文本文件（`.xlp` / `.sql` / `.lua` / `.artdef` / `.xml` / `.civ6proj`）——
   整词匹配（不会把 `..._CHINA_...` 误当成 `...` 的子串）。

★ 本工具**不**负责重新 cook 或同步 Mods 副本：改名后必须在 AssetEditor 重新 cook
（新名字 = 新 BLP 条目），再按 release.md 同步/上传。

退出码：0 无需迁移或已成功 / 1 错误 / 2 `--check` 发现待迁移项
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TEXT_EXTS = {".xlp", ".sql", ".lua", ".artdef", ".xml", ".civ6proj"}
SKIP_DIRS = {"workspace", ".git", "__pycache__", "Cooked", "Build"}

# 旧名 → 新名的**语义**映射（顺序有意义：先长后短由 build_map 里按长度排序保证）
LEGACY_RULES = [
    # (正则, 目标 KIND)
    (re.compile(r"^FALLBACK_NEUTRAL_(.+)_Suk$"), "PORTRAIT"),
    (re.compile(r"^IMG_CONFIG_FOREGROUND_(.+)_Suk$"), "PORTRAIT"),
    (re.compile(r"^PORTRAIT_(.+)_BACKGROUND_Suk$"), "BACKGROUND"),
    (re.compile(r"^IMG_CONFIG_BACKGROUND_(.+)_Suk$"), "BACKGROUND"),
]


def scan(root, namespace):
    """→ (rename_map, ref_files)；rename_map: 旧stem -> 新stem"""
    rename = {}
    ref_files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            stem, ext = os.path.splitext(f)
            if ext.lower() in (".dds", ".tex") and stem.endswith("_Suk"):
                for rx, kind in LEGACY_RULES:
                    m = rx.match(stem)
                    if m:
                        rename[stem] = "%s_%s_%s" % (namespace, kind, m.group(1))
                        break
            elif ext.lower() in TEXT_EXTS:
                ref_files.append(os.path.join(dp, f))
    return rename, ref_files


def _apply_bytes(data, pairs):
    """按字节整词替换；(old,new) 已按 old 长度降序排列。"""
    for old, new in pairs:
        pat = re.compile(re.escape(old.encode("ascii")) + rb"(?![A-Za-z0-9_])")
        data = pat.sub(new.encode("ascii").replace(b"\\", b"\\\\"), data)
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="Suk 适配素材 → 独立命名空间迁移")
    ap.add_argument("project", help="工程根（含 .civ6proj 的那层）")
    ap.add_argument("--namespace", default="SUK_UI", help="新命名空间前缀（默认 SUK_UI）")
    ap.add_argument("--check", action="store_true", help="只体检：有待迁移项则 exit 2")
    ap.add_argument("--write", action="store_true", help="实际写盘（默认仅预演）")
    args = ap.parse_args()

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print("FAIL 找不到工程根：%s" % root)
        return 1

    rename, ref_files = scan(root, args.namespace)
    if not rename:
        print("OK   无需迁移：%s（未发现 `*_Suk` 贴图）" % os.path.basename(root))
        return 0

    pairs = sorted(rename.items(), key=lambda kv: -len(kv[0]))
    print("工程：%s" % root)
    print("命名空间：%s_*" % args.namespace)
    print("\n贴图改名（%d 个 stem / %d 个文件）：" % (len(rename), len(rename) * 2))
    for old, new in sorted(rename.items()):
        print("   %-46s -> %s" % (old, new))

    # 文本引用
    hits = {}
    for p in ref_files:
        try:
            data = open(p, "rb").read()
        except OSError:
            continue
        n = 0
        for old, new in pairs:
            n += len(re.findall(re.escape(old.encode("ascii")) + rb"(?![A-Za-z0-9_])", data))
        if n:
            hits[p] = n
    print("\n文本引用（%d 个文件）：" % len(hits))
    for p, n in sorted(hits.items()):
        print("   %-64s %d 处" % (os.path.relpath(p, root).replace("\\", "/"), n))

    if args.check:
        print("\n[--check] 发现 %d 个待迁移 stem —— 跑 --write 执行。" % len(rename))
        return 2
    if not args.write:
        print("\n[预演] 未写盘。加 --write 实际执行。")
        return 0

    # ---- 写盘 ----
    errs = 0
    for old, new in pairs:
        for ext in (".dds", ".tex"):
            src = None
            for dp, dn, fn in os.walk(root):
                dn[:] = [d for d in dn if d not in SKIP_DIRS]
                if (old + ext) in fn:
                    src = os.path.join(dp, old + ext)
                    break
            if not src:
                continue
            dst = os.path.join(os.path.dirname(src), new + ext)
            if os.path.exists(dst) and os.path.abspath(dst) != os.path.abspath(src):
                print("FAIL 目标已存在，跳过：%s" % dst)
                errs += 1
                continue
            # 先改内容（.tex 内部字段），再改名
            if ext == ".tex":
                data = _apply_bytes(open(src, "rb").read(), pairs)
                open(src, "wb").write(data)
            os.replace(src, dst)

    for p, _n in hits.items():
        data = _apply_bytes(open(p, "rb").read(), pairs)
        open(p, "wb").write(data)

    print("\n完成：改名 %d 组贴图，重写 %d 个引用文件。" % (len(rename), len(hits)))
    print("★ 后续必须做：AssetEditor 重新 cook（新名字=新 BLP 条目）→ 同步 Mods 副本 → 按 release.md 上传。")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
