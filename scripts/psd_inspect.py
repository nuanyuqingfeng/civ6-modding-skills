#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PSD 结构检视 + 图层导出（类别⑥ 历史时刻模板反推用）。

用途：拿到一叠 PSD 模板（如「历史图片模板」1..18.psd）时，
  1) 打印每个 PSD 的画布尺寸、顶层元素名与完整图层/组树（含 kind / visible / bbox）；
  2) 可选把指定 PSD 的每个图层渲染成独立 PNG（附 composite 与棋盘底对照），供人眼/视觉模型复核。

这是「从 PSD 反推官方形状」流程的观察端：先看清图层语义（哪个是形状遮罩、哪个是描边），
再决定用 `apply_moment_template.py --template N` 套版。

用法:
  python psd_inspect.py <psd或目录> [--out <目录>] [--export-layers] [--pick 1,4,18] [--all]
  python psd_inspect.py --help

依赖: psd_tools（必需）、Pillow + numpy（仅 --export-layers 需要）。

说明：本脚本由作者工程里的一次性分析脚本泛化而来（原文硬编码模板目录与输出目录）。
"""
from __future__ import annotations

import argparse
import os
import sys


def _die(msg: str, code: int = 2):
    print("[FAIL] " + msg, file=sys.stderr)
    raise SystemExit(code)


def walk(layer, depth=0, acc=None):
    """递归收集 (depth, name, kind, visible, bbox)。"""
    if acc is None:
        acc = []
    try:
        nm = layer.name
    except Exception:
        nm = "?"
    try:
        vis = layer.visible
    except Exception:
        vis = None
    try:
        kind = layer.kind
    except Exception:
        kind = "?"
    try:
        box = layer.bbox
    except Exception:
        box = None
    acc.append((depth, nm, kind, vis, box))
    try:
        is_group = layer.is_group()
    except Exception:
        is_group = False
    if is_group:
        for c in layer:
            walk(c, depth + 1, acc)
    return acc


def sort_key(p):
    stem = p.stem
    return (0, int(stem)) if stem.isdigit() else (1, stem)


def collect(target: str, pick: str, take_all: bool):
    t = os.path.abspath(target)
    if os.path.isdir(t):
        files = sorted([os.path.join(t, f) for f in os.listdir(t) if f.lower().endswith(".psd")], key=lambda x: sort_key(__import__("pathlib").Path(x)))
    elif os.path.isfile(t):
        files = [t]
    else:
        _die("路径不存在：%s" % target)
    if not files:
        _die("未找到任何 .psd：%s" % target)
    if not take_all and pick:
        want = {s.strip() for s in pick.split(",") if s.strip()}
        sel = [f for f in files if os.path.splitext(os.path.basename(f))[0] in want]
        files = sel or files
    return t, files


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="PSD 结构检视 + 图层导出")
    ap.add_argument("target", help="PSD 文件或包含 PSD 的目录")
    ap.add_argument("--out", default=None, help="图层导出目录（--export-layers 时必填，默认 <target>/_psd_layers）")
    ap.add_argument("--export-layers", action="store_true", help="把图层渲染成 PNG（需 Pillow + numpy）")
    ap.add_argument("--pick", default="1,4,18", help="仅详细打印这些编号的 PSD（逗号分隔；默认 1,4,18）")
    ap.add_argument("--all", action="store_true", help="详细打印全部 PSD（覆盖 --pick）")
    a = ap.parse_args()

    try:
        from psd_tools import PSDImage
    except ImportError:
        _die("缺少 psd_tools。安装：pip install psd_tools")

    target, files = collect(a.target, a.pick, a.all)
    print("目标：%s" % target)
    print("PSD 数：%d" % len(files))

    summary = {}
    for f in files:
        psd = PSDImage.open(f)
        layers = []
        for L in psd:
            walk(L, 0, layers)
        summary[f] = (psd.size, layers)

    # 概览：每个 PSD 的尺寸与顶层元素名
    print()
    print("=" * 74)
    print("=== 各 PSD 顶层元素 ===")
    for f in files:
        size, layers = summary[f]
        top = [nm for (d, nm, k, v, b) in layers if d == 0]
        print("  %-14s %-12s %s" % (os.path.basename(f), "%dx%d" % size,
                                    " | ".join(t[:26] for t in top)))

    # 详表
    detail = files if a.all else [f for f in files if os.path.splitext(os.path.basename(f))[0] in
                                  {s.strip() for s in a.pick.split(",") if s.strip()}] or files
    for f in detail:
        size, layers = summary[f]
        print()
        print("=" * 74)
        print("%s  canvas=%s  图层/组=%d" % (os.path.basename(f), size, len(layers)))
        for depth, nm, kind, vis, box in layers:
            print("   %s%-40s kind=%-10s vis=%-5s box=%s" % ("  " * depth, str(nm)[:40], kind, vis, box))

    if not a.export_layers:
        print()
        print("（未请求 --export-layers：只做了结构检视）")
        return 0

    try:
        import numpy as np
        from PIL import Image
    except ImportError as e:
        _die("--export-layers 需要 Pillow + numpy（%s）。安装：pip install pillow numpy" % e)

    out = a.out or os.path.join(target if os.path.isdir(target) else os.path.dirname(target), "_psd_layers")
    os.makedirs(out, exist_ok=True)

    def checker(size, sq=8):
        w, h = size
        arr = np.zeros((h, w, 4), dtype=np.uint8)
        yy, xx = np.mgrid[0:h, 0:w]
        m = ((yy // sq) + (xx // sq)) % 2
        arr[..., :3] = np.where(m[..., None] == 0, 190, 230)
        arr[..., 3] = 255
        return Image.fromarray(arr, "RGBA")

    def on_checker(im):
        bg = checker(im.size)
        bg.alpha_composite(im.convert("RGBA"))
        return bg

    for f in detail:
        psd = PSDImage.open(f)
        stem = os.path.splitext(os.path.basename(f))[0]
        comp = psd.composite()
        if comp is not None:
            comp = comp.convert("RGBA")
            on_checker(comp).save(os.path.join(out, "%s_00_composite.png" % stem))
            print("%s composite %s" % (stem, comp.size))
        for i, L in enumerate(psd, 1):
            im = L.composite()
            if im is None:
                print("   [%d] %-38s (no raster)" % (i, L.name))
                continue
            im = im.convert("RGBA")
            alpha = np.asarray(im)[..., 3]
            nz = (alpha > 8).mean() * 100
            safe = "".join(c if (c.isalnum() or c in "-_") else "_" for c in str(L.name))[:28]
            fn = "%s_%02d_%s_vis%d.png" % (stem, i, safe, 1 if L.visible else 0)
            on_checker(im).save(os.path.join(out, fn))
            print("   [%d] %-38s kind=%-11s vis=%-5s alpha>8=%.1f%%  -> %s"
                  % (i, str(L.name)[:38], L.kind, L.visible, nz, fn))
    print()
    print("outdir:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
