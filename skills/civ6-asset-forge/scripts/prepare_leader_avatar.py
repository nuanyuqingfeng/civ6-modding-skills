#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_leader_avatar.py - 领袖圆形头像（ICON_LEADER_*）素材整备：判定 + 定标合成 + 底图换色

流程（规则真源 reference/leader-avatar.md）：
  1) 素材判定：透明抠图 → Icon 制作支路；圆形成品且占比合规 → 合规直通（零改动）；
     满幅不透明矩形（复杂背景）→ exit 2 停下询问。
  2) 锚点（由 AI 视觉定位提供，本脚本不采集）：双眼分别定位、唇中心、下巴最低点、
     头冠（脸部中心竖直方向上的头部圆弧顶点，视觉定位）、肩线。
  3) 定标：底边 = 下巴与肩线中点（落圆底）；顶隙 g = (肩线−下巴)/4（头冠点到圆缘上沿）；
     缩放 s = 盘径 ÷ (底边 − 头冠 + g)；脸中心（双眼中点与唇中点的中点）x → 画布中心。
  4) 圆缘贴合：艺术层 alpha 与底图 alpha 求交；出圈保留 = 上半区连通域
     （深度上限 盘R×1.18 与 画布圆−4px 软边界取小，AA 收尾）。
  5) 底图换色：色相 → 角色主色相（饱和像素 HSV 圆平均）、饱和度钳制 0.05~0.28、明度逐像素保留。

产出（<outdir>/）：
  <stem>_头像_<尺寸>.png   各画布规范成品
  <stem>_preview_<尺寸>.png 棋盘底预览
  <stem>_底图_换色.png      按主色调换色后的底图
  <stem>_锚点标注.png       双眼/唇/脸中心/下巴/头冠/肩线/底边证据图
  <stem>_metrics.json      量测与落位复测数据

用法:
  python prepare_leader_avatar.py --material 立绘.png --anchors 锚点.json --outdir out
  python prepare_leader_avatar.py --material a.png --anchors a.json --outdir out --canvas 256 --canvas 300
  python prepare_leader_avatar.py --material 圆头像.png --anchors 锚点.json --outdir out --passthrough

锚点 JSON 契约（画布 = 素材原生像素坐标）:
  {"L": [x,y], "R": [x,y], "lip": [x,y], "chin": y, "crown": [x,y], "shoulder": y}
  L/R = 左/右眼中心；lip = 唇中心；chin = 下巴最低点 y；crown = 头冠点（脸部中心竖直线上的
  头部圆弧顶点，视觉定位）；shoulder = 肩线 y。缺失键按 exit 2 报错。

退出码: 0 成功；2 规格/参数不满足（文件缺失、满幅无 alpha、锚点缺失、画布非 RGBA）。
"""
import argparse
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageChops, ImageDraw
from psd_tools import PSDImage  # noqa: F401  （与家族其它脚本一致保留依赖位）

DEFAULT_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "TEMPLATE_leader_avatar_base.png")

REQUIRED_KEYS = ("L", "R", "lip", "chin", "crown", "shoulder")


def die(msg, code=2):
    print("[FAIL] " + msg, file=sys.stderr)
    raise SystemExit(code)


def rgb_to_hsv(arr):
    rgb = arr[:, :, :3].astype(np.float64) / 255.0
    mx = rgb.max(axis=2); mn = rgb.min(axis=2); d = mx - mn
    v = mx
    s = np.where(mx > 0, d / np.maximum(mx, 1e-9), 0)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    h = np.zeros_like(mx)
    idx = (mx == r) & (d > 0); h[idx] = ((g - b)[idx] / d[idx]) % 6
    idx = (mx == g) & (d > 0); h[idx] = (b - r)[idx] / d[idx] + 2
    idx = (mx == b) & (d > 0); h[idx] = (r - g)[idx] / d[idx] + 4
    return h / 6.0, s, v


def hsv_to_rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=2)


def label_components(mask):
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    cur = 0
    for sy in range(h):
        for sx in np.nonzero(mask[sy] & (labels[sy] == 0))[0]:
            if labels[sy, sx]:
                continue
            cur += 1
            q = [(sy, sx)]
            labels[sy, sx] = cur
            while q:
                y, x = q.pop()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not labels[ny, nx]:
                            labels[ny, nx] = cur
                            q.append((ny, nx))
    return labels, cur


def circular_hue(arr, alpha):
    h, s, v = rgb_to_hsv(arr)
    w = np.where(s > 0.15, s * (alpha / 255.0), 0)
    if w.sum() < 100:
        return 350.0
    ang = np.arctan2((np.sin(h * 2 * np.pi) * w).sum(), (np.cos(h * 2 * np.pi) * w).sum())
    return float(np.degrees(ang) % 360)


def checker(size, cell=12):
    c = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(c)
    for yy in range(0, size, cell):
        for xx in range(0, size, cell):
            g = 255 if (xx // cell + yy // cell) % 2 == 0 else 204
            d.rectangle((xx, yy, xx + cell - 1, yy + cell - 1), fill=(g, g, g, 255))
    return c


def preview(img, path):
    bg = checker(img.size[0]).copy()
    bg.alpha_composite(img)
    bg.convert("RGB").save(path)


def save_png(img, path):
    for attempt in range(4):
        try:
            if os.path.exists(path):
                os.remove(path)
            img.save(path)
            return
        except OSError:
            if attempt == 3:
                raise
            time.sleep(0.6)


def fit_disc(base_im):
    """底图圆盘径向中位拟合：返回 (R, cx, cy)（底图本画布坐标）"""
    barr = np.asarray(base_im).astype(np.float64)
    ba = barr[:, :, 3]
    bm = ba >= 128
    ys, xs = np.nonzero(bm)
    H, W = ba.shape
    cy, cx = (H - 1) / 2.0, (W - 1) / 2.0
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    ang = (np.degrees(np.arctan2(yy - cy, xx - cx)) % 360).astype(int)
    rmax = np.zeros(360)
    for ag in range(360):
        sel = ang == ag
        if bm[sel].any():
            rmax[ag] = dist[sel][bm[sel]].max()
    R = float(np.median(rmax[rmax > 0]))
    sel_in = dist[ys, xs] <= R + 2
    return R, float(xs[sel_in].mean()), float(ys[sel_in].mean())


def main():
    ap = argparse.ArgumentParser(description="领袖圆形头像素材整备（占比定标）")
    ap.add_argument("--material", required=True, help="素材 PNG（透明抠图或圆形成品）")
    ap.add_argument("--anchors", required=True, help="锚点 JSON（L/R/lip/chin/crown/shoulder）")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--base", default=DEFAULT_BASE, help="底图 PNG（默认 assets/TEMPLATE_leader_avatar_base.png）")
    ap.add_argument("--canvas", type=int, action="append", default=None,
                    help="输出画布尺寸，可多次（默认 256 与 300）")
    ap.add_argument("--passthrough", action="store_true",
                    help="合规直通：只复制与出 256 导出，不做任何像素改动")
    args = ap.parse_args()

    for p in (args.material, args.anchors, args.base):
        if not os.path.exists(p):
            die(f"文件不存在: {p}")
    with open(args.anchors, encoding="utf-8") as f:
        anc = json.load(f)
    missing = [k for k in REQUIRED_KEYS if k not in anc]
    if missing:
        die(f"锚点 JSON 缺键: {missing}")

    mat = Image.open(args.material).convert("RGBA")
    W, H = mat.size
    arr = np.asarray(mat)
    a = arr[:, :, 3]
    opaque_frac = (a == 255).mean()
    transparent_frac = (a == 0).mean()
    if transparent_frac < 0.02 and opaque_frac > 0.9:
        die("素材为满幅不透明图（无有效 alpha 抠图）——复杂背景需先由用户抠图后重跑；纯色/渐变背景可先询问是否授权抠底")

    eye_mid = ((anc["L"][0] + anc["R"][0]) / 2, (anc["L"][1] + anc["R"][1]) / 2)
    face_c = ((eye_mid[0] + anc["lip"][0]) / 2, (eye_mid[1] + anc["lip"][1]) / 2)
    chin, crown, shoulder = float(anc["chin"]), (float(anc["crown"][0]), float(anc["crown"][1])), float(anc["shoulder"])

    base_im = Image.open(args.base).convert("RGBA")
    R_base, dcx, dcy = fit_disc(base_im)
    barr = np.asarray(base_im).astype(np.float64)
    hue = circular_hue(arr, a)
    bh, bs, bv = rgb_to_hsv(barr)
    brec = barr.copy()
    brec[:, :, :3] = hsv_to_rgb(np.full_like(bh, hue / 360.0), np.clip(bs, 0.05, 0.28), bv) * 255.0
    base_rec = Image.fromarray(brec.astype(np.uint8))

    bound = chin + (shoulder - chin) / 2.0
    gap = (shoulder - chin) / 4.0
    os.makedirs(args.outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.material))[0]
    metrics = {"material": args.material, "anchors": anc, "face_c": [round(face_c[0], 1), round(face_c[1], 1)],
               "hue": round(hue, 1), "base_R": round(R_base, 2), "bound": round(bound, 1), "gap": round(gap, 1),
               "judgment": "满幅图" if opaque_frac > 0.9 else ("透明抠图" if transparent_frac > 0.3 else "部分透明"),
               "canv": {}}

    save_png(base_rec.convert("RGBA"), os.path.join(args.outdir, f"{stem}_底图_换色.png"))

    canvases = args.canvas if args.canvas else [256, 300]
    for C in canvases:
        k = C / 256.0
        D = R_base * 2 * k
        disc_top = C / 2 - D / 2
        tw, th = int(round(base_im.size[0] * k)), int(round(base_im.size[1] * k))
        base_k = base_rec.resize((tw, th), Image.LANCZOS) if abs(k - 1) > 1e-6 else base_rec
        px = int(round(C / 2 - dcx * k))
        py = int(round(C / 2 - dcy * k))
        base = Image.new("RGBA", (C, C), (0, 0, 0, 0))
        base.alpha_composite(base_k, (px, py))
        base_alpha = np.asarray(base)[:, :, 3]

        if args.passthrough:
            canvas = mat.resize((C, C), Image.LANCZOS) if mat.size != (C, C) else mat.copy()
            metrics["canv"][C] = {"mode": "passthrough"}
        else:
            s = D / max(1.0, (bound - crown[1] + gap))
            A_big = mat.resize((max(1, int(round(W * s))), max(1, int(round(H * s)))), Image.LANCZOS)
            dx = int(round(C / 2 - face_c[0] * s))
            dy = int(round(disc_top + gap * s - crown[1] * s))
            art = Image.new("RGBA", (C, C), (0, 0, 0, 0))
            art.alpha_composite(A_big, (dx, dy))
            art_alpha = np.asarray(art)[:, :, 3]

            cy0 = C / 2.0
            margin = int(round(0.05 * C))
            r_cap = R_base * k * 1.18
            ss = int(r_cap * 2 * 4)
            cap_m = Image.new("L", (ss, ss), 0)
            ImageDraw.Draw(cap_m).ellipse((0, 0, ss - 1, ss - 1), fill=255)
            cap_l = np.asarray(cap_m.resize((C, C), Image.LANCZOS)).astype(np.int32)
            ss2 = C * 4
            rim_m = Image.new("L", (ss2, ss2), 0)
            rr2 = (C / 2 - 2) * 4
            c2 = ss2 / 2
            ImageDraw.Draw(rim_m).ellipse((c2 - rr2, c2 - rr2, c2 + rr2 - 1, c2 + rr2 - 1), fill=255)
            rim_l = np.asarray(rim_m.resize((C, C), Image.LANCZOS)).astype(np.int32)
            cap_l = np.minimum(cap_l, rim_l)
            outside = (art_alpha >= 1) & (base_alpha < 8)
            labels, n = label_components(outside)
            keep_l = np.zeros((C, C), dtype=np.int32)
            kept_px = clipped_px = 0
            for i in range(1, n + 1):
                comp = labels == i
                ys_c = np.nonzero(comp)[0]
                if ys_c.max() <= cy0 + margin:
                    keep_l = np.maximum(keep_l, comp * 255)
                    kept_px += int(comp.sum())
                else:
                    clipped_px += int(comp.sum())
            keep_l = np.minimum(keep_l, cap_l)
            allowed = np.maximum(base_alpha.astype(np.int32), keep_l)
            allowed_l = Image.fromarray(allowed.astype(np.uint8))
            art2 = art.copy()
            art2.putalpha(ImageChops.darker(art.getchannel("A"), allowed_l))
            canvas = Image.new("RGBA", (C, C), (0, 0, 0, 0))
            canvas.alpha_composite(base)
            canvas.alpha_composite(art2)
            crown_f = crown[1] * s + dy
            bound_f = bound * s + dy
            metrics["canv"][C] = {"s": round(s, 4), "off": [dx, dy],
                                  "crown_f": round(crown_f, 1), "top_gap": round(crown_f - (C / 2 - D / 2), 1),
                                  "bound_f": round(bound_f, 1), "kept": kept_px, "clipped": clipped_px}

        ca = np.asarray(canvas)[:, :, 3]
        ys4 = np.nonzero(ca >= 1)[0]
        edge_hard = sum(int((np.asarray(canvas)[rr, :, 3] >= 200).sum()) for rr in (0, C - 1)) + \
                    sum(int((np.asarray(canvas)[:, cc, 3] >= 200).sum()) for cc in (0, C - 1))
        metrics["canv"][C]["yrange"] = [int(ys4.min()), int(ys4.max())]
        metrics["canv"][C]["edge_hard"] = edge_hard
        save_png(canvas, os.path.join(args.outdir, f"{stem}_头像_{C}.png"))
        preview(canvas, os.path.join(args.outdir, f"{stem}_preview_{C}.png"))

    # 锚点标注（素材原生坐标）
    annot = mat.copy()
    d = ImageDraw.Draw(annot)
    for (cx, cy), col, r in [(anc["L"], (0, 220, 255, 255), max(8, W // 80)),
                             (anc["R"], (0, 220, 255, 255), max(8, W // 80)),
                             (anc["lip"], (0, 255, 120, 255), max(8, W // 80))]:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=max(2, W // 300))
    d.line((face_c[0] - W // 40, face_c[1], face_c[0] + W // 40, face_c[1]), fill=(255, 0, 255, 255), width=max(3, W // 250))
    d.line((face_c[0], face_c[1] - W // 40, face_c[0], face_c[1] + W // 40), fill=(255, 0, 255, 255), width=max(3, W // 250))
    d.ellipse((crown[0] - W // 55, crown[1] - W // 55, crown[0] + W // 55, crown[1] + W // 55), outline=(255, 200, 0, 255), width=max(2, W // 400))
    d.ellipse((face_c[0] - W // 60, chin - W // 60, face_c[0] + W // 60, chin + W // 60), outline=(0, 120, 255, 255), width=max(2, W // 400))
    d.line((W // 10, shoulder, W - W // 10, shoulder), fill=(255, 120, 0, 255), width=max(3, W // 320))
    d.line((W // 10, int(bound), W - W // 10, int(bound)), fill=(120, 0, 255, 255), width=max(2, W // 400))
    annot_path = os.path.join(args.outdir, f"{stem}_锚点标注.png")
    if os.path.exists(annot_path):
        os.remove(annot_path)
    annot.resize((1024, int(1024 * H / W)), Image.LANCZOS).save(annot_path)

    with open(os.path.join(args.outdir, f"{stem}_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=1)
    print(f"[OK] {stem}: hue={hue:.1f} 判定={metrics['judgment']} 底边={bound:.1f} 顶隙g={gap:.1f}")
    for C in canvases:
        print(f"  {C}: {metrics['canv'][C]}")
    print("[OK] 产出: " + ", ".join(sorted(os.listdir(args.outdir))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
