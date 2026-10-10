"""build_resource_icon.py — 资源图标底盘合成引擎（无 Photoshop 路径）

把源图案裁到内容包围盒，等比装入落位框，再以 source-over 叠到对应类别底盘上，
输出 256×256 RGBA 单元格。加成（BONUS）用黄盘，奢侈（LUXURY）用紫盘。

用法：
  python build_resource_icon.py --input <源图.png> --kind bonus|luxury [--out <png>]
  python build_resource_icon.py --input <源图.png> --kind luxury --box 186x190@35,33
  python build_resource_icon.py --input <源图.png> --kind luxury --fow
  python build_resource_icon.py --input <源图.png> --kind bonus --pattern-only
  python build_resource_icon.py --plates

构图铁律：等比缩放（k = min(框宽/源宽, 框高/源高)）后居中装入落位框，禁止非等比拉伸；
重采样走预乘 alpha 的 LANCZOS，RGB 与 alpha 同步，避免源图透明区的 RGB 渗出；
最后在输出空间沿图案全部边缘（外轮廓与内部空隙）向外描一圈等宽黑边（规格见 reference/resource-icon.md 第三节）。
依赖：numpy、Pillow。
"""

import argparse
import os
import re

import numpy as np
from PIL import Image, ImageFilter

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")
CELL = 256
KINDS = ("bonus", "luxury")
DEFAULT_THRESHOLD = 8
STROKE_WIDTH = 5
STROKE_SIGMA = 0.6
STROKE_THRESHOLD = 64
STROKE_RGB = (0, 0, 0)

PLATE_FILES = {
    ("bonus", False): "TEMPLATE_resource_plate_bonus.png",
    ("luxury", False): "TEMPLATE_resource_plate_luxury.png",
    ("bonus", True): "TEMPLATE_resource_plate_bonus_fow.png",
    ("luxury", True): "TEMPLATE_resource_plate_luxury_fow.png",
}


def plate_path(kind, fow=False):
    return os.path.join(ASSETS, PLATE_FILES[(kind, fow)])


def load_plate(kind, fow=False):
    p = plate_path(kind, fow)
    if not os.path.isfile(p):
        raise SystemExit("缺少底盘资产：%s" % p)
    a = np.asarray(Image.open(p).convert("RGBA"), dtype=np.uint8)
    if a.shape != (CELL, CELL, 4):
        raise SystemExit("底盘必须是 %dx%d：%s 实为 %dx%d" % (CELL, CELL, p, a.shape[1], a.shape[0]))
    return a


def alpha_bbox(alpha, thr=DEFAULT_THRESHOLD, what=""):
    ys, xs = np.nonzero(np.asarray(alpha) >= thr)
    if ys.size == 0:
        raise SystemExit("找不到内容（alpha >= %d）%s" % (thr, what))
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def parse_box(text):
    m = re.fullmatch(r"(\d+)x(\d+)@(-?\d+),(-?\d+)", text.strip())
    if not m:
        raise SystemExit("--box 格式应为 WxH@X,Y（如 186x190@35,33），收到 %s" % text)
    w, h, x, y = (int(v) for v in m.groups())
    return x, y, x + w, y + h


def fmt_box(b):
    return "%dx%d@%d,%d" % (b[2] - b[0], b[3] - b[1], b[0], b[1])


def default_box(kind, fow=False):
    return alpha_bbox(load_plate(kind, fow)[:, :, 3])


def premul_resize(arr, size):
    f = arr.astype(np.float64) / 255.0
    al = f[:, :, 3:4]
    pm = np.concatenate([f[:, :, :3] * al, al], axis=2)
    im = Image.fromarray((pm * 255.0 + 0.5).astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
    o = np.asarray(im, dtype=np.float64) / 255.0
    oa = o[:, :, 3]
    rgb = np.zeros_like(o[:, :, :3])
    nz = oa > 1e-6
    rgb[nz] = o[nz, :3] / oa[nz][:, None]
    out = np.concatenate([rgb, oa[:, :, None]], axis=2) * 255.0 + 0.5
    return np.clip(out, 0, 255).astype(np.uint8)


def over(top, bot):
    t = top.astype(np.float64) / 255.0
    b = bot.astype(np.float64) / 255.0
    ta, ba = t[:, :, 3:4], b[:, :, 3:4]
    oa = ta + ba * (1.0 - ta)
    num = t[:, :, :3] * ta + b[:, :, :3] * ba * (1.0 - ta)
    rgb = np.where(oa > 1e-6, num / np.maximum(oa, 1e-6), 0.0)
    return np.clip(np.concatenate([rgb, oa], axis=2) * 255.0 + 0.5, 0, 255).astype(np.uint8)


def icon_layer(cell, plate, safe=250.0):
    # 反解「图标 over 底盘」中的图标层；底盘 alpha >= safe 处不可观测，一律计 0
    pf = plate.astype(np.float64) / 255.0
    cf = cell.astype(np.float64) / 255.0
    pa, ca = pf[:, :, 3], cf[:, :, 3]
    ppm = pf[:, :, :3] * pa[:, :, None]
    cpm = cf[:, :, :3] * ca[:, :, None]
    ia = np.zeros_like(ca)
    ok = pa < safe / 255.0
    den = np.maximum(1.0 - pa, 1e-9)
    ia[ok] = np.clip((ca[ok] - pa[ok]) / den[ok], 0.0, 1.0)
    num = cpm - ppm * (1.0 - ia)[:, :, None]
    rgb = np.zeros_like(cpm)
    nz = ia > 1e-6
    rgb[nz] = num[nz] / ia[nz][:, None]
    out = np.zeros((CELL, CELL, 4), np.uint8)
    out[:, :, :3] = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)
    out[:, :, 3] = np.clip(ia * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return out


def dilate_disk(mask, r):
    # 半径 r 的圆盘膨胀，按欧氏距离取邻域；逐层 4 邻域迭代会让对角方向明显偏细。
    if r <= 0:
        return mask
    h, w = mask.shape
    pad = np.zeros((h + 2 * r, w + 2 * r), bool)
    pad[r:r + h, r:r + w] = mask
    out = np.zeros((h, w), bool)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r:
                out |= pad[r + dy:r + dy + h, r + dx:r + dx + w]
    return out


def edge_stroke(layer, width=STROKE_WIDTH, sigma=STROKE_SIGMA, rgb=STROKE_RGB,
                thr=STROKE_THRESHOLD):
    # 在**输出空间**沿图案全部边缘向外描 width 像素黑边：主体掩码取 alpha >= thr
    # （浅阴影与软边不参与成环），圆盘膨胀后减去掩码得到等宽环带，环带只落在主体之外，
    # 环带 alpha 做 sigma 高斯羽化后 source-over 叠回图案。
    # 外轮廓、枝节边缘、内部空隙一并成环；主体自身像素不被覆盖。
    # 描边在缩放落位之后进行，各格宽度一致，不随源图尺寸与 k 变化。
    m = layer[:, :, 3] >= thr
    ring = dilate_disk(m, width) & ~m
    ov = np.zeros_like(layer)
    ov[ring, 0], ov[ring, 1], ov[ring, 2] = rgb
    ov[ring, 3] = 255
    if sigma > 0:
        blurred = Image.fromarray(ov[:, :, 3], "L").filter(ImageFilter.GaussianBlur(sigma))
        ov[:, :, 3] = np.asarray(blurred, dtype=np.uint8)
    return over(ov, layer)


def place_pattern(src, box, thr=DEFAULT_THRESHOLD, stroke=True):
    sb = alpha_bbox(src[:, :, 3], thr, "（源图）")
    crop = src[sb[1]:sb[3], sb[0]:sb[2]]
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    dw, dh = box[2] - box[0], box[3] - box[1]
    # 描边在落位之后向外铺开，故图案先按「落位框内缩描边宽度」等比装入，
    # 图案与黑边的总占位仍等于落位框，各格一致。
    pad = STROKE_WIDTH if stroke else 0
    k = min(max(dw - 2 * pad, 1) / float(sw), max(dh - 2 * pad, 1) / float(sh))
    # 取整可能把图案撑过内缩后的框 1px，连同黑边就溢出落位框，故对上限同时取小
    nw = max(1, min(int(round(sw * k)), dw - 2 * pad))
    nh = max(1, min(int(round(sh * k)), dh - 2 * pad))
    rs = premul_resize(crop, (nw, nh))
    layer = np.zeros((CELL, CELL, 4), np.uint8)
    px = box[0] + (dw - nw) // 2
    py = box[1] + (dh - nh) // 2
    layer[py:py + nh, px:px + nw] = rs
    if stroke:
        layer = edge_stroke(layer)
    return layer, (nw, nh), k


def compose(src_path, kind, box=None, fow=False, pattern_only=False,
            thr=DEFAULT_THRESHOLD, stroke=True):
    if kind not in KINDS:
        raise SystemExit("--kind 只能取 %s" % " / ".join(KINDS))
    src = np.asarray(Image.open(src_path).convert("RGBA"), dtype=np.uint8)
    use_box = box if box is not None else default_box(kind, fow)
    layer, placed, k = place_pattern(src, use_box, thr, stroke=stroke)
    if pattern_only:
        return layer, placed, k, use_box
    return over(layer, load_plate(kind, fow)), placed, k, use_box


def plate_report():
    for kind in KINDS:
        for fow in (False, True):
            p = load_plate(kind, fow)
            a = p[:, :, 3]
            v, c = np.unique(a, return_counts=True)
            top = sorted(zip(c.tolist(), v.tolist()), reverse=True)[:4]
            bx = alpha_bbox(a)
            print("  %-6s %-4s %s" % (kind, "FOW" if fow else "", os.path.basename(plate_path(kind, fow))))
            print("         非零%6d  包围盒 %-14s  alpha 前4(数量,值) %s"
                  % (int((a > 0).sum()), fmt_box(bx), top))
            for val in (153, 202, 255):
                if (a == val).any():
                    sel = a == val
                    uv = np.unique(np.ascontiguousarray(p[:, :, :3][sel]).reshape(-1, 3), axis=0)
                    print("         alpha=%3d n=%6d  唯一 RGB %d 种  %s"
                          % (val, int(sel.sum()), len(uv),
                             tuple(int(x) for x in uv[0]) if len(uv) == 1 else "多色"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="源图案 PNG")
    ap.add_argument("--kind", choices=KINDS, help="资源类别：bonus=加成（黄盘）/ luxury=奢侈（紫盘）")
    ap.add_argument("--out", help="输出 PNG（默认 <输入名>_<kind>.png）")
    ap.add_argument("--box", help="落位框 WxH@X,Y（默认取底盘 alpha 包围盒）")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help="源图内容包围盒的 alpha 阈值（默认 8）")
    ap.add_argument("--no-stroke", action="store_true", help="不加图案黑边（素材自身已带黑边时用）")
    ap.add_argument("--fow", action="store_true", help="改用迷雾（FOW）底盘，产出 *_Fow 图集用单元格")
    ap.add_argument("--pattern-only", action="store_true", help="只输出落位后的图案层（透明底，供 PS 路径预构图）")
    ap.add_argument("--plates", action="store_true", help="打印内置底盘规格后退出")
    args = ap.parse_args()

    if args.plates:
        plate_report()
        return 0
    if not args.input:
        raise SystemExit("缺少 --input；可先用 --plates 查看内置底盘")
    if not args.kind:
        raise SystemExit("缺少 --kind（bonus / luxury）")
    if not os.path.isfile(args.input):
        raise SystemExit("找不到源图：%s" % args.input)

    box = parse_box(args.box) if args.box else None
    img, placed, k, use_box = compose(args.input, args.kind, box=box, fow=args.fow,
                                      pattern_only=args.pattern_only, thr=args.threshold,
                                      stroke=not args.no_stroke)
    out = args.out or ("%s_%s%s.png" % (os.path.splitext(args.input)[0], args.kind,
                                        "_pattern" if args.pattern_only else ""))
    Image.fromarray(img).save(out, "PNG")
    print("ok: %s  落位框 %s  装入 %dx%d  k=%.3f  %s"
          % (out, fmt_box(use_box), placed[0], placed[1], k,
             "图案层" if args.pattern_only else ("%s 底盘" % ("FOW " if args.fow else "") + args.kind)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
