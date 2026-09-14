#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edge_gradient.py - 立绘"边缘透明渐变"处理器

解决的问题：给两张大立绘图自动做出干净、柔和、可平铺合成的透明边缘。
现有 leader-2d 管线 (process_leader_png.py) 把 alpha 二值化
(mask = 255 if a > threshold else 0)，边缘是硬切，放大后会看到锯齿与白边。
本脚本保留真实软 alpha，并额外做三件事：

  1) 去杂边 (defringe)：原图抠底常留一圈"半透明背景色"光晕。用
     反预乘 + 邻域背景估计把它压掉，避免黑边/白边。
  2) 羽化并收紧 (feather + erode)：给出可控的 alpha 渐变带宽度，
     并把 alpha 曲线末端压到 0，保证四边完全透明、人物内芯不透明。
  3) 边缘保色 (unmultiply)：Civ6 用 PF_R8G8B8A8_UNORM 直通 alpha，
     不做预乘，故半透明像素的 RGB 必须是"未预乘"的原色，否则会发灰。

产出：
  <stem>_soft.png          通用软边透明 PNG（原始尺寸）
  <stem>_1024_TEXTURE.png  1024x1024 方形裁切，真实 alpha 保留（Civ6 TEXTURE）
  <stem>_1024_OPACITY.png  1024x1024 灰度遮罩，**保留渐变**（Civ6 OPACITY，PF_R8）
  <stem>_Normal_206x208.png / _Selected_326x339.png  可选总督立绘尺寸
  <stem>_preview.png       棋盘底预览（验收用）

用法:
  python edge_gradient.py --input 立绘.png --outdir out --key CTTH_RGN
  python edge_gradient.py --input a.png --input b.png --outdir out --key CTTH_RGN
  python edge_gradient.py --input a.png --outdir out --feather 2.5 --spill 0.5
  python edge_gradient.py --input a.png --outdir out --governor-sizes
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
    from scipy import ndimage
except ImportError:
    sys.exit("需要 Pillow 与 numpy: pip install pillow numpy")


def _f32(a):
    return a.astype(np.float32)


def extend_rgb_nearest(rgb, alpha, core_thr=0.92):
    """*必需步骤* 把不透明内芯的 RGB 按最近邻蔓延，填满整幅透明区。

    为什么必需：原图全透明区域的 RGB 是无意义数据（常为近黑）。
    若直接对 alpha 做羽化，这些垃圾 RGB 会被“半透明化”，
    在人物外围形成一圈**黑边/白边光晕**。
    实测该 bug 曾污染画面 1.7% 面积，新增半透明像素里 96% 是近黑 RGB(5,5,5)。
    正确顺序永远是：先铺满前景色，再动 alpha。
    """
    a = np.clip(np.asarray(alpha, dtype=np.float32), 0, 255) / 255.0
    core = a >= core_thr
    if core.sum() < 16:
        nz = a[a > 0.05]
        core = a >= (float(np.percentile(nz, 60)) if nz.size else 1.0)
    if core.sum() < 4:
        return rgb
    idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    return rgb[idx[0], idx[1]]
def _box_blur(x, radius):
    """积分图实现的方形均值模糊（numpy，支持 float，O(1)/像素）。"""
    r = max(1, int(round(radius)))
    x = _f32(x)
    H, W = x.shape
    c = np.cumsum(np.cumsum(x, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    ys = np.arange(H); xs = np.arange(W)
    y0 = np.clip(ys - r, 0, H); y1 = np.clip(ys + r + 1, 0, H)
    x0 = np.clip(xs - r, 0, W); x1 = np.clip(xs + r + 1, 0, W)
    S = c[np.ix_(y1, x1)] - c[np.ix_(y0, x1)] - c[np.ix_(y1, x0)] + c[np.ix_(y0, x0)]
    cnt = ((y1 - y0)[:, None] * (x1 - x0)[None, :]).astype(np.float32)
    return S / np.maximum(cnt, 1.0)


def estimate_background_color(rgb, alpha):
    """估计与人物混色的背景色 B。

    取 alpha 极低(0.03..0.28)的最外圈——那里 B 占比最高、前景污染最少。
    若该带不存在(说明原图已是干净直通 alpha)，返回 None，跳过去杂边。
    """
    a = alpha / 255.0
    m = (a > 0.03) & (a < 0.28)
    if m.sum() < 24:
        return None
    px = _f32(rgb[m])
    lum = px.mean(axis=1)
    keep = lum <= np.percentile(lum, 85)     # 去掉最亮的离群(前景泄漏)
    return np.median(px[keep] if keep.sum() >= 12 else px, axis=0)


def unspill(rgb, alpha, bg, strength=1.0):
    """按直通合成公式 C = F*al + B*(1-al) 反解 F，去掉边缘残留背景色。

    这是去杂边的**正确**解法：已知 B 与 al，则 F = (C - B*(1-al)) / al。
    低 alpha 处反解噪声大，用邻域不透明色填充，避免出现彩色噪点。
    """
    if bg is None or strength <= 0:
        return rgb
    a = np.clip(_f32(alpha), 0, 255) / 255.0
    C = _f32(rgb)
    F = np.zeros_like(C)
    ok = a > 1e-4
    F[ok] = (C[ok] - bg[None, :] * (1.0 - a[ok])[:, None]) / a[ok][:, None]
    F = np.clip(F, 0, 255)
    # 低 alpha 区域不可靠：用不透明内芯做邻域填充
    core = (np.clip(_f32(alpha), 0, 255) >= 250).astype(np.float32)
    if core.sum() >= 16:
        num = np.zeros_like(C); den = np.zeros(C.shape[:2], np.float32)
        for c in range(3):
            num[..., c] = _box_blur(np.where(core > 0, F[..., c], 0.0), 3)
        den = _box_blur(core, 3)
        fill = num / np.maximum(den[..., None], 1e-6)
        weak = (a < 0.35) & (den > 1e-3)
        F[weak] = fill[weak]
    w = np.clip(strength, 0, 1) * np.clip(1.0 - a, 0, 1)
    return np.clip(C * (1 - w[..., None]) + F * w[..., None], 0, 255)


def alpha_curve(alpha, feather=1.5, floor=0.0, gamma=1.0, lift=0.0):
    """羽化并重塑 alpha：高斯羽化 + gamma + 末端压零，得到平滑渐变带。"""
    a = _f32(alpha)
    if feather > 0:
        a = _f32(np.asarray(Image.fromarray(a.astype(np.uint8))
                            .filter(ImageFilter.GaussianBlur(feather))).astype(np.float32))
    if gamma != 1.0:
        a = 255.0 * np.power(np.clip(a / 255.0, 0, 1), gamma)
    if lift > 0:
        # 轻微抬升中间调，让渐变更"柔"（Civ6 立绘观感偏软）
        a = 255.0 * (np.clip(a / 255.0, 0, 1) ** (1.0 / max(1e-6, 1.0 + lift)))
    a = np.clip((a - floor * 255.0) / max(1e-6, 1.0 - floor), 0, 255)
    return a


def soften_edge_band(rgb, alpha, band_px=1.0, tint=None):
    """在 alpha 边界带内做一圈极轻的提亮/压暗，避免锯齿感（可选）。"""
    if band_px <= 0:
        return rgb
    a = _f32(alpha)
    blur = _f32(np.asarray(Image.fromarray(a.astype(np.uint8))
                           .filter(ImageFilter.GaussianBlur(band_px))).astype(np.float32))
    edge = np.clip((blur - a), 0, 255) / 255.0     # 只取外侧过渡
    col = np.array(tint if tint else (0, 0, 0), dtype=np.float32)
    return np.clip(rgb * (1 - edge[..., None] * 0.25) + col * edge[..., None] * 0.25, 0, 255)


def contain_square(img, size):
    """等比 contain 到 size×size 居中，其余透明（不裁掉人物）。"""
    W = H = size
    sc = min(W / img.width, H / img.height)
    nw, nh = max(1, int(round(img.width * sc))), max(1, int(round(img.height * sc)))
    r = img.resize((nw, nh), Image.LANCZOS)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c.alpha_composite(r, ((W - nw) // 2, (H - nh) // 2))
    return c


def contain_box(img, box):
    """等比 contain 到 box=(W,H) 居中。"""
    W, H = box
    sc = min(W / img.width, H / img.height)
    nw, nh = max(1, int(round(img.width * sc))), max(1, int(round(img.height * sc)))
    r = img.resize((nw, nh), Image.LANCZOS)
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c.alpha_composite(r, ((W - nw) // 2, (H - nh) // 2))
    return c


def checker(bg, sq=24):
    W, H = bg.size
    c = Image.new("RGB", (W, H), (50, 50, 56))
    d = ImageDraw.Draw(c)
    for y in range(0, H, sq):
        for x in range(0, W, sq):
            if ((x // sq) + (y // sq)) % 2 == 0:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(72, 72, 80))
    c = c.convert("RGBA")
    c.alpha_composite(bg.convert("RGBA"))
    return c


def process(img, feather=0.0, spill=0.0, gamma=1.0, lift=0.0, band_px=0.0):
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3]
    if (alpha < 255).sum() == 0:
        # 全不透明输入：没有 alpha 可用，视为需要"从背景里抠"的失败情形
        sys.stderr.write("警告: 输入 PNG 无透明通道(alpha 全 255)，"
                         "边缘渐变无从谈起；请提供透明底素材。\n")
    # ★顺序不可颠倒：先把前景色铺满透明区，再改 alpha / 去脏边
    if feather > 0 or spill > 0:
        rgb = extend_rgb_nearest(rgb, alpha)
    bg = None
    if spill > 0:
        bg = estimate_background_color(rgb, alpha)
        rgb = unspill(rgb, alpha, bg, spill)
    if feather > 0:
        alpha = alpha_curve(alpha, feather, floor=0.0, gamma=gamma, lift=lift)
    if band_px > 0:
        rgb = soften_edge_band(rgb, alpha, band_px)
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 255)]).astype(np.uint8)
    return Image.fromarray(out, "RGBA"), bg


def main():
    ap = argparse.ArgumentParser(description="立绘边缘透明渐变处理器")
    ap.add_argument("--input", required=True, action="append",
                    help="输入立绘 PNG（可重复传多次，例如两张立绘）")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--key", default="PORTRAIT", help="输出命名前缀")
    ap.add_argument("--feather", type=float, default=0.0,
                    help="羽化半径 px。默认 0=不羽化(素材已抗锯齿就别开，会糊边)")
    ap.add_argument("--spill", type=float, default=0.0,
                    help="去杂边强度 0~1。默认 0=不改你的边缘色；确有残留底色再开 0.3~0.6")
    ap.add_argument("--gamma", type=float, default=1.0, help="alpha gamma（>1 更瘦，<1 更胖）")
    ap.add_argument("--lift", type=float, default=0.0, help="中间调抬升 0~1，让渐变更柔")
    ap.add_argument("--edge-tint", type=float, default=0.0, help="边缘带柔化强度 px（0=关）")
    ap.add_argument("--size", type=int, default=1024, help="TEXTURE/OPACITY 边长（默认 1024）")
    ap.add_argument("--governor-sizes", action="store_true",
                    help="额外输出总督立绘尺寸 206x208 与 326x339")
    ap.add_argument("--checker", action="store_true", help="额外输出棋盘底预览")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    reports = []

    for i, src in enumerate(args.input, start=1):
        srcp = Path(src)
        stem = args.key if len(args.input) == 1 else "%s_%d" % (args.key, i)
        img = Image.open(srcp).convert("RGBA")
        soft, bg = process(img, args.feather, args.spill, args.gamma,
                           args.lift, args.edge_tint)

        made = {}
        p = outdir / ("%s_soft.png" % stem); soft.save(p); made["soft"] = p

        sq = contain_square(soft, args.size)
        p = outdir / ("%s_%d_TEXTURE.png" % (stem, args.size)); sq.save(p); made["texture"] = p
        # OPACITY: 单通道灰度，保留渐变（这是与 leader-2d 二值化的关键差别）
        op = sq.getchannel("A").convert("L")
        p = outdir / ("%s_%d_OPACITY.png" % (stem, args.size)); op.save(p); made["opacity"] = p

        if args.governor_sizes:
            for tag, box in (("Normal_206x208", (206, 208)), ("Selected_326x339", (326, 339))):
                im = contain_box(soft, box)
                p = outdir / ("%s_%s.png" % (stem, tag)); im.save(p)
                made[tag] = p

        if args.checker:
            sc = soften_preview = checker(sq)
            p = outdir / ("%s_preview.png" % stem); sc.save(p); made["preview"] = p

        al = np.asarray(soft)[..., 3]
        ramp = ((al > 8) & (al < 247)).sum()
        reports.append(dict(input=str(srcp), key=stem,
                            size=soft.size, bg_estimate=(None if bg is None else [int(x) for x in bg]),
                            soft_px=int(ramp), soft_px_pct=round(100.0 * ramp / al.size, 2),
                            fully_opaque_pct=round(100.0 * (al >= 255).mean(), 2),
                            fully_clear_pct=round(100.0 * (al == 0).mean(), 2),
                            outputs={k: str(v) for k, v in made.items()}))

    import json
    print(json.dumps(reports, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
