import argparse
import struct
import sys

from PIL import Image, ImageFilter

CORE_ALPHA = 64
LOW_LO = 9
LOW_HI = 16
DILATE_RADIUS = 16
MID_LO = 8
MID_HI = 247
WIDE_RUN = 4


def load_alpha(path, size):
    if path.lower().endswith(".dds"):
        with open(path, "rb") as f:
            head = f.read(128)
            h, w = struct.unpack("<II", head[12:20])
            raw = f.read(w * h)
        return Image.frombytes("L", (w, h), raw)
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    box = ((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side)
    return img.crop(box).resize((size, size), Image.LANCZOS).getchannel("A")


def wide_levels(alpha):
    w, h = alpha.size
    px = alpha.load()
    maxrun = {}
    for y in range(h):
        x = 0
        while x < w:
            v = px[x, y]
            n = 1
            while x + n < w and px[x + n, y] == v:
                n += 1
            if n > maxrun.get(v, 0):
                maxrun[v] = n
            x += n
    return sum(1 for v, n in maxrun.items() if n >= WIDE_RUN)


def measure(alpha):
    w, h = alpha.size
    total = w * h
    hist = alpha.histogram()

    core = alpha.point(lambda v: 255 if v >= CORE_ALPHA else 0)
    near = core.filter(ImageFilter.MaxFilter(2 * DILATE_RADIUS + 1))
    band = alpha.point(lambda v: 255 if LOW_LO <= v <= LOW_HI else 0)
    band_n = band.histogram()[255]
    zero = Image.new("L", alpha.size, 0)
    inside = Image.composite(band, zero, near).histogram()[255]

    low_share = 100.0 * band_n / total
    near_share = 100.0 * inside / band_n if band_n else 0.0
    mid_share = 100.0 * sum(hist[MID_LO:MID_HI + 1]) / total
    levels = sum(1 for v in range(256) if hist[v])
    wide = wide_levels(alpha)

    hits = {
        "低值段远离主体": near_share < 5.0,
        "低值段面积": low_share > 3.0,
        "渐变铺满画布": mid_share > 20.0 and wide > levels * 0.9,
    }
    return dict(near_share=near_share, low_share=low_share, mid_share=mid_share,
                levels=levels, wide=wide, hits=hits)


def report(path, m):
    print("%s" % path)
    print("  低值段 %d~%d 落在主体 %dpx 内的比例  %6.2f%%   判定线 <5%%    %s"
          % (LOW_LO, LOW_HI, DILATE_RADIUS, m["near_share"], "命中" if m["hits"]["低值段远离主体"] else "未命中"))
    print("  低值段 %d~%d 占全图比例              %6.2f%%   判定线 >3%%    %s"
          % (LOW_LO, LOW_HI, m["low_share"], "命中" if m["hits"]["低值段面积"] else "未命中"))
    print("  中间调 %d~%d 占全图比例              %6.2f%%   判定线 >20%%   %s"
          % (MID_LO, MID_HI, m["mid_share"], "命中" if m["hits"]["渐变铺满画布"] else "未命中"))
    print("  灰阶级数 %d，横向游程 >=%dpx 的级数 %d（判定线 >%.1f）"
          % (m["levels"], WIDE_RUN, m["wide"], m["levels"] * 0.9))


def main():
    ap = argparse.ArgumentParser(description="判定 OPACITY 源图是否为铺满画布的宽羽化光晕（leader-2d.md §3.6(7)）")
    ap.add_argument("images", nargs="+", help="源立绘 PNG，或已是 alpha 单通道的 OPACITY DDS")
    ap.add_argument("--size", type=int, default=1024, help="PNG 裁剪缩放的目标边长，默认 1024")
    args = ap.parse_args()

    hit_any = False
    for path in args.images:
        m = measure(load_alpha(path, args.size))
        report(path, m)
        hit = all(m["hits"].values())
        hit_any = hit_any or hit
        print("  结论：%s" % ("命中，按 §3.6(7) 做分段拉伸" if hit else "未命中，按 §3.6(6) 默认流程处理"))
        print()

    return 1 if hit_any else 0


if __name__ == "__main__":
    sys.exit(main())
