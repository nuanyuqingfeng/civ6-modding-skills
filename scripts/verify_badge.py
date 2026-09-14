#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_badge.py - 总督 24px 徽章几何/配色验证

用法:
  python verify_badge.py 生成.png                  # 只做几何自洽校验
  python verify_badge.py 生成.png 官方格.png        # 与官方对照，输出 IoU 与配色误差

判定标准（来自 reference/governor-art/specs.md 实测）：
  * 轮廓：y=3..20 共 18 行；最宽 18px(x3..x20)；左右居中；上下对称。
  * 与官方对照：轮廓 IoU >= 0.95；逐行跨度应零差异；逐行均色误差尽量小。
退出码: 0 = 通过, 1 = 不通过。
"""
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("需要 Pillow 与 numpy: pip install pillow numpy")

# 原版 24px 徽章逐行跨度（alpha>140 实测）
OFFICIAL_SPANS = {
    3: (8, 15), 4: (7, 16), 5: (6, 17), 6: (5, 18), 7: (4, 19),
    8: (3, 20), 9: (3, 20), 10: (3, 20), 11: (3, 20), 12: (3, 20),
    13: (3, 20), 14: (3, 20), 15: (3, 20),
    16: (4, 19), 17: (5, 18), 18: (6, 17), 19: (7, 16), 20: (8, 15),
}


def spans(img, thr=140):
    a = np.asarray(img.convert("RGBA"))
    out = {}
    for y in range(a.shape[0]):
        xs = np.where(a[y, :, 3] > thr)[0]
        out[y] = (int(xs[0]), int(xs[-1])) if len(xs) else None
    return out


def iou(a, b, thr=128):
    A = np.asarray(a.convert("RGBA"))[..., 3] > thr
    B = np.asarray(b.convert("RGBA"))[..., 3] > thr
    return (A & B).sum() / max(1, (A | B).sum())


def row_means(img):
    a = np.asarray(img.convert("RGBA")).astype(float)
    al = a[..., 3] / 255.0
    out = {}
    for y in range(a.shape[0]):
        m = al[y] > 0.9
        out[y] = a[y][m][:, :3].mean(0) if m.sum() else None
    return out


def geometry_check(img):
    print("== 几何自洽 ==")
    sp = spans(img)
    ok = True
    n = sum(1 for v in sp.values() if v)
    print("  有效行数 = %d (期望 18)" % n)
    if n != 18:
        ok = False
    for y, exp in OFFICIAL_SPANS.items():
        got = sp.get(y)
        if got != exp:
            print("  y=%2d 跨度 %s != 期望 %s  <-- 不符" % (y, got, exp))
            ok = False
    if ok:
        print("  y=3..20 逐行跨度全部与原版一致 (1:1)")
    return ok


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gen = Image.open(sys.argv[1]).convert("RGBA")
    ok = geometry_check(gen)

    if len(sys.argv) >= 3:
        off = Image.open(sys.argv[2]).convert("RGBA")
        # 允许直接传整张 8x1 图集：用 --cell N 选格（默认第 1 格，即 Generic 位）
        cell = 1
        if "--cell" in sys.argv:
            cell = int(sys.argv[sys.argv.index("--cell") + 1])
        if off.width > gen.width and off.width % gen.width == 0:
            n = off.width // gen.width
            if not (0 <= cell < n):
                sys.exit("--cell 超出范围 0..%d" % (n - 1))
            print("提示: 官方图 %dx%d 判为 %d 格图集，取第 %d 格对照"
                  % (off.width, off.height, n, cell))
            off = off.crop((cell * gen.width, 0, (cell + 1) * gen.width, gen.height))
        print("\n== 与官方对照 ==")
        v = iou(gen, off)
        print("  轮廓 IoU = %.4f  (判定阈值 0.95)" % v)
        if v < 0.95:
            ok = False
        sp_o, sp_m = spans(off), spans(gen)
        diff = [y for y in sorted(set(sp_o) | set(sp_m)) if sp_o.get(y) != sp_m.get(y)]
        print("  跨度不一致行 = %s" % (diff if diff else "无(1:1)"))
        mo, mm = row_means(off), row_means(gen)
        errs = []
        for y in sorted(OFFICIAL_SPANS):
            if mo.get(y) is not None and mm.get(y) is not None:
                errs.append(float(np.abs(mo[y] - mm[y]).mean()))
        if errs:
            print("  逐行均色平均误差 = %.2f (0=完全一致)" % float(np.mean(errs)))
        for name, im in (("官方", off), ("生成", gen)):
            a = np.asarray(im).astype(float)
            al = a[..., 3]
            px = a[al > 200][:, :3]
            if len(px) == 0:
                continue
            l = 0.299 * px[:, 0] + 0.587 * px[:, 1] + 0.114 * px[:, 2]
            print("  %s med=%s 高光P90=%s 暗部P10=%s" % (
                name, tuple(np.median(px, 0).round(0).astype(int)),
                tuple(np.median(px[l >= np.percentile(l, 90)], 0).round(0).astype(int)),
                tuple(np.median(px[l <= np.percentile(l, 10)], 0).round(0).astype(int))))

    print("\n结果: %s" % ("通过 PASS" if ok else "不通过 FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
