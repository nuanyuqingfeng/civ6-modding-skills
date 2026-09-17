#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_icon_set.py - 由"一张头像"生成总督全套图标（色调高度一致）

产出（全部 RGBA PNG，命名照抄原版契约）：
  <stem>_PROMOTION24.png         24px  就职/晋升徽章  -> ICON_GOVERNOR_<TYPE>_PROMOTION
  <stem>_32.png / <stem>_64.png  32/64 头像小图标     -> ICON_GOVERNOR_<TYPE>
  <stem>_Normal_206x208.png                           -> GovernorNormal_<Key>
  <stem>_Selected_326x339.png                         -> GovernorSelected_<Key>

用法:
  python build_icon_set.py --avatar 头像.png --outdir out --key CTTH_RGN
  python build_icon_set.py --avatar 头像.png --outdir out --glyph 图形.png --checker

设计原则（全部来自 reference/governor-art/specs.md 的 1:1 实测）：
  * 结构锁死：八边形轮廓、上亮下暗渐变曲线、1px 高光边、图形占格 45~55%，均为原版常量。
  * 色调驱动：色相/饱和度取自头像（加权圆平均主色），亮度曲线沿用原版。
    => 同一头像出的整组图标彼此色调一致，且与原版并置不突兀。
  * 只出 1 张徽章：原版引擎仅 BaseAbility 读 _PROMOTION，其余阶位回落
    ICON_GOVERNOR_GENERIC_PROMOTION（GovernorPanel.lua:181）。
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
except ImportError:
    sys.exit("需要 Pillow 与 numpy: pip install pillow numpy")

# --------------------------------------------------------------- 原版实测常量
# 原版 24px 徽章逐行跨度（alpha>140 实测，XP1/XP2 八格一致）：y=3..20 共 18 行
OCT = [(8, 15), (7, 16), (6, 17), (5, 18), (4, 19),
       (3, 20), (3, 20), (3, 20), (3, 20), (3, 20),
       (3, 20), (3, 20), (3, 20),
       (4, 19), (5, 18), (6, 17), (7, 16), (8, 15)]
OCT_Y0 = 3
# 实测"镜面斜面"梯度（24px 徽章逐行均值，alpha>0.9，官方八格一致）：
#   顶/底边最亮(238,234,206) -> 内侧倾斜下落 -> 中部最暗(105,101,73)，上下对称。
#   这是金属徽章的倒角高光，不是简单线性渐变。
RIM_RGB = (238, 234, 206)       # 顶/底倒角高光
BODY_RGB = (197, 193, 165)      # 次亮环
UPPER_RGB = (143, 139, 111)     # 上部倾斜面
MED_RGB = (134, 130, 102)       # 中位
DARK_RGB = (105, 101, 73)       # 中部最暗带（y13/y15）
LOWER_RGB = (158, 154, 126)     # 下部回亮
GLYPH_RGB = (73, 69, 41)        # 内部图形

# 以画布 y 归一化（0..1，对应 24px 的 0..23）的关键点，取自实测行均值
GRADIENT_STOPS = [
    (3/23.0,  (238, 234, 206)),
    (4/23.0,  (238, 234, 206)),
    (5/23.0,  (197, 193, 165)),
    (7/23.0,  (143, 139, 111)),
    (8/23.0,  (134, 130, 102)),
    (9/23.0,  (141, 137, 109)),
    (11/23.0, (129, 125, 97)),
    (12/23.0, (112, 108, 80)),
    (13/23.0, (105, 101, 73)),
    (15/23.0, (111, 107, 79)),
    (16/23.0, (130, 126, 98)),
    (18/23.0, (158, 154, 126)),
    (19/23.0, (188, 184, 156)),
    (20/23.0, (212, 208, 181)),
]
CANON_HUE = 51.0               # 原版暖橄榄色相
# 头像色相占比。实测结论：官方八格徽章**互为同色**（暖橄榄金，与立绘无相关性），
# 故"徽章跟随头像"是本管线的**主动增强**而非复刻。默认 0.35 是在
# "能看出与头像同源"与"不偏离原版金属感"之间的折中；--strict-canon 可取 0.0。
HUE_FOLLOW = 0.35
BADGE_SIZE = 24


def rgb2hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / d)) % 360
    elif mx == g:
        h = 60 * ((b - r) / d) + 120
    else:
        h = 60 * ((r - g) / d) + 240
    s = 0.0 if mx == 0 else d / mx
    return h, s, mx


def hsv2rgb(h, s, v):
    h = h % 360
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int(round((r + m) * 255)), int(round((g + m) * 255)), int(round((b + m) * 255)))


def avatar_palette(avatar):
    """返回 (hue_deg, sat, val, top3)。只用不透明、非极暗/极亮像素。"""
    im = avatar.convert("RGBA")
    im.thumbnail((512, 512), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    al = a[..., 3] / 255.0
    rgb = a[..., :3]
    v = rgb.max(2) / 255.0
    mn = rgb.min(2) / 255.0
    s = np.where(v > 0, (v - mn) / np.maximum(v, 1e-6), 0.0)
    sel = (al > 0.5) & (v > 0.10) & (v < 0.97)
    if sel.sum() < 32:
        sel = al > 0.5
    if sel.sum() == 0:
        return CANON_HUE, 0.35, 0.55, []
    px = rgb[sel]
    ss = s[sel]
    vv = v[sel]
    # 统一抽样，保证 hue/sat/val/weight 一一对应
    idx = np.arange(len(px))
    if len(idx) > 4000:
        idx = idx[:: max(1, len(idx) // 4000)]
    px_s, ss_s, vv_s = px[idx], ss[idx], vv[idx]

    hh = np.array([rgb2hsv(*p)[0] for p in px_s])
    ww = ss_s * np.maximum(vv_s, 0.15)
    if len(hh) == 0 or ww.sum() <= 0:
        hue = CANON_HUE
    else:
        ang = np.deg2rad(hh)
        cy = float((ww * np.cos(ang)).sum())
        sy = float((ww * np.sin(ang)).sum())
        hue = math.degrees(math.atan2(sy, cy)) % 360
    sat = float(np.average(ss_s, weights=ww + 1e-6)) if ww.sum() > 0 else float(ss.mean())
    val = float(np.average(vv_s, weights=ww + 1e-6)) if ww.sum() > 0 else float(vv.mean())

    q = (px // 32).astype(int)
    key = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    uk, cnt = np.unique(key, return_counts=True)
    top = []
    for kk in uk[np.argsort(-cnt)[:3]]:
        m = key == kk
        top.append([int(x) for x in np.median(px[m], 0).round(0)])
    return hue, max(0.12, min(sat, 0.95)), max(0.18, min(val, 0.95)), top


# 原版梯度自身的平均饱和度在 tone_params 内按实测 stops 现算（见下）


def tone_params(hue, sat):
    """头像色相/饱和度 -> 徽章各层颜色。亮度(V)完全沿用实测值，只动 H/S。"""
    # 饱和度倍率：直接吃头像饱和度，不再做"相对原版归一化"。
    # （实测：官方八格徽章互为同色，sat 与立绘无相关性，
    #   故任何归一化都只是拿一个错基准去除；直接映射才不会六个总督挤到同一个钳位值。）
    # 0.42 是原版典型立绘饱和度，对应倍率恰好 1.0。
    s_rel = max(0.70, min(1.45, 0.35 + sat * 1.55))
    ah = math.radians(hue)
    ch = math.radians(CANON_HUE)
    hb = math.degrees(math.atan2(
        math.sin(ah) * HUE_FOLLOW + math.sin(ch) * (1 - HUE_FOLLOW),
        math.cos(ah) * HUE_FOLLOW + math.cos(ch) * (1 - HUE_FOLLOW))) % 360

    def keep_lum(rgb, sat_mul):
        _, s0, v0 = rgb2hsv(*rgb)
        return hsv2rgb(hb, min(0.92, s0 * sat_mul), v0)

    stops = [(t, keep_lum(c, s_rel)) for (t, c) in GRADIENT_STOPS]
    return dict(hue=hb, sat_scale=s_rel, stops=stops,
                rim=keep_lum(RIM_RGB, s_rel),
                body=keep_lum(BODY_RGB, s_rel),
                mid=keep_lum(MED_RGB, s_rel),
                shade=keep_lum(DARK_RGB, s_rel),
                glyph=keep_lum(GLYPH_RGB, s_rel))


def octagon_mask(size=BADGE_SIZE, ss=6):
    """按原版八边形常量生成 mask（0..255 L）。"""
    m = Image.new("L", (size * ss, size * ss), 0)
    d = ImageDraw.Draw(m)
    # 逐行直接铺像素，严格等于原版行跨度表（多边形光栅化会半像素偏移，弃用）。
    # OCT[i] = y=OCT_Y0+i 行被填满的 x 区间 [x0, x1]（闭区间）。
    for i, (x0, x1) in enumerate(OCT):
        y = OCT_Y0 + i
        d.rectangle([x0 * ss, y * ss, (x1 + 1) * ss - 1, (y + 1) * ss - 1], fill=255)
    return m.resize((size, size), Image.LANCZOS)


def _ring(mask_img):
    """mask 内缩 1px 的差分环 = 描边环。"""
    m = np.asarray(mask_img).astype(float) / 255.0
    inner = np.asarray(mask_img.filter(ImageFilter.MinFilter(3))).astype(float) / 255.0
    return m, np.clip(m - inner, 0, 1)


def render_badge_24(tp, glyph_img=None, size=BADGE_SIZE):
    """八边形徽章：1px 高光边 + 上亮下暗渐变 + 中心微压暗 + 可选剪影图形。"""
    mask = octagon_mask(size, 6)
    m, ring = _ring(mask)
    H = size
    stops = [(t, np.array(c, float)) for (t, c) in tp["stops"]]
    col = np.zeros((H, 3))
    for i in range(H):
        t = i / max(1, H - 1)
        if t <= stops[0][0]:
            col[i] = stops[0][1]
            continue
        if t >= stops[-1][0]:
            col[i] = stops[-1][1]
            continue
        for j in range(len(stops) - 1):
            t0, c0 = stops[j]
            t1, c1 = stops[j + 1]
            if t0 <= t <= t1:
                u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                col[i] = c0 + (c1 - c0) * u
                break
    img = np.zeros((H, H, 4), float)
    img[..., :3] = col[:, None, :]
    img[..., 3] = m * 255.0
    img[..., :3] = img[..., :3] * (1 - ring[..., None]) \
        + np.array(tp["rim"], float) * ring[..., None]
    # 梯度本身已含中部暗带，无需再压暗；保留极轻的整体回光避免死板
    yy = np.linspace(0, 1, H)[:, None]
    img[..., :3] *= (1.0 + 0.015 * np.exp(-((yy - 0.5) / 0.5) ** 2))
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")

    if glyph_img is not None:
        g = glyph_img.convert("RGBA")
        ga = np.asarray(g)[..., 3]
        ys, xs = np.where(ga > 90)
        if len(xs):
            g = g.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
            width = max(1, int(round(18 * 0.52)))
            gh = max(1, int(round(g.height * width / max(1, g.width))))
            g = g.resize((width, gh), Image.LANCZOS)
            gly = np.asarray(g).astype(float)
            gly[..., :3] = np.array(tp["glyph"], float)
            glyph = Image.fromarray(np.clip(gly, 0, 255).astype(np.uint8), "RGBA")
            left = (size - width) // 2
            top = int(round((size - gh) / 2)) - 1
            out.alpha_composite(glyph, (left, top))
    return out


def render_small(avatar, size, tp):
    """八边形裁切头像小图标（ICON_GOVERNOR_<TYPE> 的 32/64px）。"""
    av = avatar.convert("RGBA")
    w, h = av.size
    side = min(w, h)
    av = av.crop(((w - side) // 2, (h - side) // 2,
                  (w - side) // 2 + side, (h - side) // 2 + side))
    av = av.resize((size, size), Image.LANCZOS)
    m, ring = _ring(octagon_mask(size, 6))
    a = np.asarray(av.copy()).astype(float)
    a[..., 3] *= m
    a[..., :3] *= (1.0 - 0.12 * m[..., None])
    a[..., :3] = a[..., :3] * (1 - ring[..., None] * 0.85) \
        + np.array(tp["glyph"], float) * ring[..., None] * 0.85
    a[..., 3] = np.maximum(a[..., 3], ring * 255.0)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def render_portrait(avatar, size, tp, selected=False, feather=1.2):
    """立绘：等比 contain 到目标画布；选中态提亮 + 暖色轮廓光。"""
    W, H = size
    av = avatar.convert("RGBA")
    sc = min(W / av.width, H / av.height)
    nw, nh = max(1, int(round(av.width * sc))), max(1, int(round(av.height * sc)))
    av = av.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(av, ((W - nw) // 2, (H - nh) // 2))
    a = np.asarray(canvas).astype(float)
    if selected:
        a[..., :3] = np.clip(a[..., :3] * 1.06 + 6.0, 0, 255)
        al = Image.fromarray(a[..., 3].astype(np.uint8))
        grown = al.filter(ImageFilter.MaxFilter(5))
        glow = np.clip(np.asarray(grown).astype(float) - np.asarray(al).astype(float),
                       0, 255) / 255.0
        a[..., :3] = np.clip(a[..., :3] + glow[..., None] * np.array(tp["body"], float) * 0.30,
                             0, 255)
    if feather > 0:
        al = Image.fromarray(a[..., 3].astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather))
        a[..., 3] = np.asarray(al).astype(float)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def checker(bg, sq=16):
    W, H = bg.size
    c = Image.new("RGB", (W, H), (52, 52, 58))
    d = ImageDraw.Draw(c)
    for y in range(0, H, sq):
        for x in range(0, W, sq):
            if ((x // sq) + (y // sq)) % 2 == 0:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(74, 74, 82))
    c = c.convert("RGBA")
    c.alpha_composite(bg.convert("RGBA"))
    return c


def main():
    ap = argparse.ArgumentParser(description="头像 -> 总督全套图标（色调一致）")
    ap.add_argument("--avatar", required=True, help="源头像 PNG（建议透明底、>=256px）")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--key", default="GOV_RGN", help="命名后缀，如 CTTH_RGN")
    ap.add_argument("--glyph", default=None, help="可选：徽章内剪影图形 PNG（取 alpha）")
    ap.add_argument("--checker", action="store_true", help="额外输出棋盘底预览")
    ap.add_argument("--json", default=None, help="取色/产出报告写入 JSON")
    ap.add_argument("--strict-canon", action="store_true",
                    help="严格复刻原版：徽章不跟随头像色相（HUE_FOLLOW=0），只保留原版暖橄榄金")
    args = ap.parse_args()

    avatar = Image.open(args.avatar).convert("RGBA")
    if args.strict_canon:
        globals()["HUE_FOLLOW"] = 0.0
    hue, sat, val, top = avatar_palette(avatar)
    tp = tone_params(hue, sat)
    glyph = Image.open(args.glyph).convert("RGBA") if args.glyph else None

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    stem = args.key
    made = {}

    badge = render_badge_24(tp, glyph)
    made["promotion24"] = out / ("%s_PROMOTION24.png" % stem)
    badge.save(made["promotion24"])

    small = {}
    for sz in (32, 64):
        im = render_small(avatar, sz, tp)
        small[sz] = im
        made["icon%d" % sz] = out / ("%s_%d.png" % (stem, sz))
        im.save(made["icon%d" % sz])

    pn = render_portrait(avatar, (206, 208), tp, selected=False)
    made["normal"] = out / ("%s_Normal_206x208.png" % stem)
    pn.save(made["normal"])
    ps = render_portrait(avatar, (326, 339), tp, selected=True)
    made["selected"] = out / ("%s_Selected_326x339.png" % stem)
    ps.save(made["selected"])

    if args.checker:
        tiles = [("promotion24", badge), ("icon64", small[64]), ("normal", pn), ("selected", ps)]
        gap = 12
        W = sum(t[1].width for t in tiles) + gap * (len(tiles) + 1)
        H = max(t[1].height for t in tiles) + 2 * gap + 18
        sheet = Image.new("RGBA", (W, H), (28, 28, 34, 255))
        d = ImageDraw.Draw(sheet)
        x = gap
        for name, im in tiles:
            sheet.alpha_composite(checker(im).convert("RGBA"), (x, gap + 14))
            d.text((x, 2), name, fill=(230, 230, 230, 255))
            x += im.width + gap
        made["preview"] = out / ("%s_preview.png" % stem)
        sheet.save(made["preview"])

    report = dict(avatar=os.path.abspath(args.avatar), key=stem,
                  avatar_hue_deg=round(hue, 1), badge_hue_deg=round(tp["hue"], 1),
                  avatar_sat=round(sat, 3), sat_scale=round(tp["sat_scale"], 3),
                  palette_top3=top,
                  colors={k: list(tp[k]) for k in ("rim", "body", "mid", "shade", "glyph")},
                  outputs={k: str(v) for k, v in made.items()})
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                   encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
