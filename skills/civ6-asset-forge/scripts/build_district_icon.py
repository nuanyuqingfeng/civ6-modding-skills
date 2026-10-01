"""build_district_icon.py — 文明6 区域图标合成：官方 PSD 模板底图 + 白色图案素材

用法：
  python build_district_icon.py --input <图案.png> --outdir <目录> [--preview]
  python build_district_icon.py --input <png> --outdir out --districts "Theater,Holy Site"
  python build_district_icon.py --psd <自定义模板.psd> --input <png> --outdir out
  python build_district_icon.py --list

默认用内置模板 templates/district_icon/District_Icon_Photoshop_CC.psd。
模拟 Photoshop 智能对象置入（无需 PS）：删背景按素材自动分路（自带透明通道跳过 /
纯黑白亮度映射 / 通用背景距离）→ 主体 bbox 裁剪 → 单步高质量重采样
（缩小 OpenCV INTER_AREA / 放大 INTER_CUBIC）
→ alpha 质心对齐落位框中心（视觉重心，越界钳制）→ 素材原样细节合成；
图案颜色由模板官方三效果接管（渐变染色 + 内描边 + 外发光）。
退出码: 0 成功; 2 输入/参数错误; 3 素材无法认定（主体占比过低等）。
"""

import argparse
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

try:
    from psd_tools import PSDImage
except ImportError:
    print("缺少 psd_tools: pip install psd-tools")
    sys.exit(2)

CANVAS = 256
# District Alpha 图层在模板中的落位框 (left, top, right, bottom)
PATTERN_BOX = (48, 48, 209, 207)
BG_NEAR = 6.0              # 通用路径：与背景色距离低于此值 → 全透明
BG_FAR = 42.0              # 通用路径：距离高于此值 → 全不透明
DOMAIN_NEAR = 10.0         # 通用路径：主体域低阈值（背景噪声之上、主体暗部之下）
CLOSE_RADIUS = 4           # 通用路径：闭运算半径（修补轮廓缺口）
MIN_MAIN_RATIO = 0.10      # 主体占图案区最低占比，低于则判定素材无法认定

# 内置模板（默认定位：scripts/../templates/district_icon/；--psd 可覆盖）
DEFAULT_PSD = Path(__file__).resolve().parent.parent / "templates" / "district_icon" / "District_Icon_Photoshop_CC.psd"


def parse_stops(effect):
    """从 GradientOverlay / Stroke 效果里读出色标 [(位置0~1, r, g, b), ...]。"""
    grad = effect.value.get(b"Grad")
    if grad is None:
        return None
    stops = []
    for s in grad.get(b"Clrs", []):
        c = s[b"Clr "]
        stops.append((float(s[b"Lctn"]) / 4096.0,
                      float(c[b"Rd  "]), float(c[b"Grn "]), float(c[b"Bl  "])))
    return sorted(stops) or None


def gradient_color(stops, t):
    """按色标位置线性插值。t ∈ [0,1]。"""
    if t <= stops[0][0]:
        return stops[0][1:]
    if t >= stops[-1][0]:
        return stops[-1][1:]
    for (p0, *c0), (p1, *c1) in zip(stops, stops[1:]):
        if p0 <= t <= p1:
            f = (t - p0) / (p1 - p0) if p1 > p0 else 0.0
            return tuple(c0[i] + (c1[i] - c0[i]) * f for i in range(3))
    return stops[-1][1:]


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def load_regions(psd_path):
    """解析模板 PSD → {区域名: dict(background, border, grad, stroke, glow)}。"""
    psd = PSDImage.open(psd_path)
    groups = [g for g in psd if g.is_group() and g.name == "Choose District"]
    if not groups:
        print(f"错误: PSD 里找不到 'Choose District' 组")
        sys.exit(2)
    regions = {}
    for reg in groups[0]:
        if not reg.is_group():
            continue
        entry = {"grad": None, "stroke": None, "glow": None,
                 "bg_grad": None, "bg_inner": None}
        for sub in reg:
            if sub.name == "Icon Background" and sub.is_group():
                for leaf in sub.descendants():
                    if leaf.is_group() or leaf.topil() is None:
                        continue
                    if leaf.name == "Background":
                        entry["background"] = leaf
                        for e in leaf.effects:
                            n = e.__class__.__name__
                            if n == "GradientOverlay" and e.enabled:
                                entry["bg_grad"] = parse_stops(e)
                            elif n == "InnerGlow" and e.enabled:
                                c = e.color
                                entry["bg_inner"] = (float(e.value.get(b"blur", 0.0)),
                                                     float(e.opacity) / 100.0,
                                                     (float(c[b"Rd  "]), float(c[b"Grn "]), float(c[b"Bl  "])))
                    elif leaf.name in ("Border", "Vector Smart Object"):
                        entry["border"] = leaf
            elif sub.name == "Alpha" and sub.is_group():
                for e in sub.effects:
                    n = e.__class__.__name__
                    if n == "GradientOverlay" and e.enabled:
                        entry["grad"] = parse_stops(e)
                    elif n == "Stroke" and e.enabled:
                        entry["stroke"] = (float(e.size), parse_stops(e))
                    elif n == "OuterGlow" and e.enabled:
                        c = e.color
                        entry["glow"] = (float(e.size), float(e.opacity) / 100.0,
                                         (float(c[b"Rd  "]), float(c[b"Grn "]), float(c[b"Bl  "])))
        if "background" not in entry or "border" not in entry:
            print(f"错误: 区域 {reg.name!r} 缺少 Background/Border 图层")
            sys.exit(2)
        if entry["grad"] is None or entry["stroke"] is None or entry["glow"] is None \
                or entry["bg_grad"] is None:
            print(f"错误: 区域 {reg.name!r} 缺少效果（图案三效果或底图 GradientOverlay）")
            sys.exit(2)
        regions[reg.name] = entry
    if not regions:
        print("错误: 'Choose District' 下没有区域组")
        sys.exit(2)
    return regions


def paste_on_canvas(layer, size=CANVAS):
    """把图层像素按 bbox 贴到画布坐标系。psd_tools 的 bbox = (left, top, right, bottom)。"""
    img = layer.topil().convert("RGBA")
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.alpha_composite(img, (layer.bbox[0], layer.bbox[1]))
    return base


def vertical_gradient(stops, y0, y1, size=CANVAS):
    """全画布的垂直渐变色场：y 从 y0(位置0) 到 y1(位置100%)。返回 (size,size,3)。"""
    ys = np.clip((np.arange(size) - y0) / max(1, y1 - y0), 0.0, 1.0)
    lut = np.array([gradient_color(stops, t) for t in ys])  # (size,3)
    return lut[:, None, :].repeat(size, axis=1)


def detect_monochrome(rgba):
    """纯黑白素材判定：RGB 三通道几乎相等（灰度图）。"""
    a = np.asarray(rgba, dtype=np.float64)
    if (a[..., 3] < 250).mean() <= 0.01:
        spread = a[..., :3].max(axis=2) - a[..., :3].min(axis=2)
        return bool(spread.mean() < 3.0)
    return False


def lum_to_alpha(rgba):
    """纯黑白素材的删背景：亮度直接映射 alpha。
    黑背景（边缘中位数）→ 全透明，前景亮部（高分位）→ 全不透明，
    中间灰阶线性过渡 = 天然抗锯齿边缘；素材明暗细节原样保留。"""
    a = np.asarray(rgba, dtype=np.float64)
    rgb = a[..., :3]
    h, w = a.shape[:2]
    lum = rgb.mean(axis=2)
    edge = np.concatenate([lum[0], lum[-1], lum[:, 0], lum[:, -1]])
    bg = float(np.median(edge))
    fg = float(np.percentile(lum, 99))
    if fg - bg < 32:
        fg = bg + 255.0  # 素材本身过暗时按满幅处理
    alpha = np.clip((lum - bg) / (fg - bg) * 255.0, 0, 255)
    out = np.dstack([rgb, alpha])
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def remove_background(rgba, near=BG_NEAR, far=BG_FAR, close_r=CLOSE_RADIUS):
    """通用路径（彩色素材/非近黑背景）：背景色距离场软阈值 → 低阈值主体域
    （开运算去噪 → 闭运算补缺口 → 孔洞填充）圈住主体并拉满内部不透明。
    纯黑白素材走 lum_to_alpha，不走此函数。已有有效 alpha 的素材原样返回。"""
    a = np.asarray(rgba, dtype=np.float64)
    if (a[..., 3] < 250).mean() > 0.01:
        return rgba  # 素材自带透明通道
    rgb, h, w = a[..., :3], a.shape[0], a.shape[1]
    edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(edge, axis=0)
    dist = np.abs(rgb - bg).max(axis=2)
    alpha = np.clip((dist - near) / (far - near) * 255.0, 0, 255)
    domain = dist > DOMAIN_NEAR
    if domain.any():
        domain = ndimage.binary_opening(domain, structure=disk(2))
        domain = ndimage.binary_closing(domain, structure=disk(close_r))
        domain = ndimage.binary_fill_holes(domain)
        alpha[domain] = 255.0
    out = np.dstack([rgb.astype(np.uint8), alpha.astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


def enhance_low_quality(rgba, target_min=280):
    """低画质素材预处理（--enhance，用户授权后使用）：
    1. 小图先 Lanczos 放大到 target_min（落位框的约 1.75 倍，留处理余量）
    2. alpha 对比度拉伸（非零 alpha 的 1%~99% 分位线性拉伸，收紧软边）
    3. UnsharpMask 轻度锐化（RGB 与 alpha 分通道，半径随尺寸）
    在删背景之后、trim/缩放之前执行。"""
    w, h = rgba.size
    if max(w, h) < target_min:
        s = target_min / max(w, h)
        rgba = rgba.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    a = np.asarray(rgba).astype(np.float64)
    al = a[..., 3]
    nz = al[al > 0]
    if nz.size:
        lo, hi = np.percentile(nz, (1, 99))
        if hi > lo:
            a[..., 3] = np.clip((al - lo) / (hi - lo) * 255.0, 0, 255)
    img = Image.fromarray(a.astype(np.uint8), "RGBA")
    radius = max(2.0, min(img.size) / 512.0)
    rgb = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=radius, percent=80, threshold=2))
    alpha = img.getchannel("A").filter(ImageFilter.UnsharpMask(radius=radius, percent=80, threshold=2))
    rgb.putalpha(alpha)
    return rgb


def high_quality_resize(img, target_w, target_h):
    """单步重采样：缩小用 OpenCV INTER_AREA（大比例缩小的面积平均最优），
    放大用 INTER_CUBIC。禁止递归减半/多步缩放——每步低通累积会让 2K/4K 素材
    明显变模糊；Pillow 的 Lanczos 缩小时本身自动扩展滤波核防混叠，单步即安全。"""
    arr = np.asarray(img)
    interp = cv2.INTER_AREA if (target_w < arr.shape[1] or target_h < arr.shape[0]) else cv2.INTER_CUBIC
    resized = cv2.resize(arr, (target_w, target_h), interpolation=interp)
    return Image.fromarray(resized, "RGBA")


def fit_pattern(rgba, box=PATTERN_BOX):
    """模拟 Photoshop 智能对象置入：主体 bbox 裁剪（alpha>32）→ 单步高质量重采样
    等比进落位框 → **alpha 质心对齐**落位框中心（视觉重心）→ 越界钳制。
    缩放系数含质心可对齐约束：max(fcx, w-fcx)*scale ≤ 框半宽——质心不在 bbox
    中心（构图不对称）时自动缩小留出平移余地，保证质心能落在框中心。
    返回 (贴图, paste_x, paste_y)。"""
    a = np.asarray(rgba)
    mask = a[..., 3] > 32
    if not mask.any():
        raise ValueError("素材没有有效 alpha 内容")
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    t, bt = np.where(rows)[0][[0, -1]]
    l, r = np.where(cols)[0][[0, -1]]
    rgba = rgba.crop((int(l), int(t), int(r) + 1, int(bt) + 1))
    # 质心（trim 后坐标系）
    ca = np.asarray(rgba)[..., 3].astype(np.float64)
    ys, xs = np.nonzero(ca > 0)
    wgt = ca[ys, xs]
    fcx = float((xs * wgt).sum() / wgt.sum())
    fcy = float((ys * wgt).sum() / wgt.sum())

    bw, bh = box[2] - box[0], box[3] - box[1]
    w, h = rgba.size
    scale = min(bw / w, bh / h)
    # 质心对齐可行性：px = 框中心 - fcx*scale 须满足 box[0] ≤ px ≤ box[2]-nw
    #   ⇔ fcx*scale ≤ bw/2 且 (w-fcx)*scale ≤ bw/2（垂直同理）
    scale = min(scale,
                bw / (2 * max(fcx, w - fcx)),
                bh / (2 * max(fcy, h - fcy)))
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    fitted = high_quality_resize(rgba, nw, nh)
    px = box[0] + bw / 2 - fcx * scale
    py = box[1] + bh / 2 - fcy * scale
    px = min(max(px, box[0]), box[2] - nw)
    py = min(max(py, box[1]), box[3] - nh)
    return fitted, int(round(px)), int(round(py))


def compose(region, pattern_rgba, size=CANVAS):
    """底图(染色+内发光) + 边框 + 外发光 + 渐变图案 + 内描边 → 成品。
    图案素材提供 alpha 形状（模拟智能对象置入：原样细节 + 质心对齐），
    颜色由模板官方三效果接管：GradientOverlay 主题色渐变填充 + Stroke 内描边 + OuterGlow。"""
    # 1. Background：白色内容按其 GradientOverlay 染区域主题色渐变
    bg_layer = region["background"]
    bg_img = paste_on_canvas(bg_layer)
    bg_arr = np.asarray(bg_img).astype(np.float64)
    content = bg_arr[..., 3] > 0
    grad_field = vertical_gradient(region["bg_grad"], bg_layer.bbox[1], bg_layer.bbox[3], size)
    bg_arr[..., :3][content] = grad_field[content]
    # InnerGlow：边缘向内 blur px 的柔光（默认黑，压暗六边形内缘）
    if region["bg_inner"]:
        blur, op, gcolor = region["bg_inner"]
        if blur > 0 and op > 0:
            dist_in = ndimage.distance_transform_edt(content)
            strength = np.clip(1.0 - dist_in / blur, 0.0, 1.0) * op
            gc = np.array(gcolor)
            for c in range(3):
                ch = bg_arr[..., c]
                ch[content] = ch[content] * (1 - strength[content]) + gc[c] * strength[content]
                bg_arr[..., c] = ch
    out = bg_arr

    # 2. Border（区域主题色边框环，原样）
    border = paste_on_canvas(region["border"])
    out = np.asarray(Image.fromarray(out.astype(np.uint8), "RGBA"))
    out = out.astype(np.float64)
    b_arr = np.asarray(border).astype(np.float64)
    alpha_b = (b_arr[..., 3:4] / 255.0)
    out[..., :3] = out[..., :3] * (1 - alpha_b) + b_arr[..., :3] * alpha_b
    out[..., 3] = np.maximum(out[..., 3], b_arr[..., 3])

    # 3. 图案 alpha 全画布掩码（PS 效果渲染语义：50% alpha 为形状边界——
    #    若用 >0 判定，缩放软边的极淡像素全被当成形状边缘，描边与发光会
    #    在图案内部产生网状亮纹）
    fitted, px, py = fit_pattern(pattern_rgba)
    pw, ph = fitted.size
    pa = np.asarray(fitted, dtype=np.float64)
    full = np.zeros((size, size), dtype=bool)
    full[py:py + ph, px:px + pw] = pa[..., 3] >= 128

    # 4. OuterGlow：图案外扩环带 multiply 压暗（画在图案之下）
    gsize, gopacity, gcolor = region["glow"]
    glow_zone = ndimage.binary_dilation(full, structure=disk(round(gsize))) & ~full
    if glow_zone.any():
        multiplied = out[..., :3] * (np.array(gcolor) / 255.0)
        w = gopacity
        for c in range(3):
            ch = out[..., c]
            ch[glow_zone] = ch[glow_zone] * (1 - w) + multiplied[..., c][glow_zone] * w
            out[..., c] = ch
    img = Image.fromarray(out.astype(np.uint8), "RGBA")

    # 5. 图案主体：区域主题色渐变填充（顶部位置0 → 底部位置100%，对齐图案 bbox）
    x0, y0, x1, y1 = px, py, px + pw, py + ph
    grad = region["grad"]
    ys = np.linspace(0.0, 1.0, y1 - y0)[:, None]
    top = np.array(gradient_color(grad, 0.0))
    bot = np.array(gradient_color(grad, 1.0))
    grad_rgb = top[None, :] + (bot - top)[None, :] * ys
    patch = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.float64)
    patch[..., :3] = grad_rgb[:, None, :]
    patch[..., 3] = pa[..., 3]
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    overlay.alpha_composite(Image.fromarray(patch.astype(np.uint8), "RGBA"), (x0, y0))
    img.alpha_composite(overlay)
    arr = np.asarray(img).astype(np.float64)

    # 6. Stroke：沿图案边缘向内 size 像素的环带，描边渐变同方向
    ssize, sstops = region["stroke"]
    inner = ndimage.binary_erosion(full, structure=disk(round(ssize)))
    ring = full & ~inner
    if ring.any() and sstops:
        col_field = vertical_gradient(sstops, y0, y1, size)
        for c in range(3):
            ch = arr[..., c]
            ch[ring] = col_field[..., c][ring]
            arr[..., c] = ch
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def checker_preview(img, cell=8):
    """棋盘底预览。"""
    w, h = img.size
    bgp = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(bgp)
    for yy in range(0, h, cell):
        for xx in range(0, w, cell):
            if (xx // cell + yy // cell) % 2:
                d.rectangle([xx, yy, xx + cell - 1, yy + cell - 1], fill=(204, 204, 204))
    bgp.paste(img, (0, 0), img)
    return bgp


def prepare_pattern(raw, enhance=False):
    """素材前置分路（两个引擎共用）：自带透明通道跳过删背景 / 纯黑白亮度映射 /
    通用背景距离；enhance=True 追加低画质增强。返回 (rgba, 路径说明)。"""
    if (np.asarray(raw, dtype=np.float64)[..., 3] < 250).mean() > 0.01:
        nobg, path_name = raw, "自带透明通道(跳过删背景)"
    else:
        mono = detect_monochrome(raw)
        nobg = lum_to_alpha(raw) if mono else remove_background(raw)
        path_name = "纯黑白亮度映射" if mono else "通用背景距离"
    if enhance:
        nobg = enhance_low_quality(nobg)
        path_name += " + 低画质增强"
    return nobg, path_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psd", default=str(DEFAULT_PSD),
                    help=f"区域图标模板 PSD（默认内置: {DEFAULT_PSD.name}）")
    ap.add_argument("--input", help="白色图案素材 PNG")
    ap.add_argument("--outdir", help="成品输出目录")
    ap.add_argument("--districts", help="逗号分隔的区域组名，默认全部")
    ap.add_argument("--preview", action="store_true", help="同时输出棋盘底预览图")
    ap.add_argument("--enhance", action="store_true",
                    help="低画质素材预处理：小图放大 + alpha 对比度拉伸 + UnsharpMask 锐化")
    ap.add_argument("--list", action="store_true", help="只列出 PSD 里的区域组")
    args = ap.parse_args()

    psd_path = Path(args.psd)
    if not psd_path.is_file():
        print(f"错误: 找不到 PSD {psd_path}")
        sys.exit(2)
    regions = load_regions(psd_path)
    if args.list:
        for name in regions:
            print(name)
        sys.exit(0)

    if not args.input or not args.outdir:
        print("错误: 合成需要 --input 与 --outdir")
        sys.exit(2)
    src = Path(args.input)
    if not src.is_file():
        print(f"错误: 找不到素材 {src}")
        sys.exit(2)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    wanted = None
    if args.districts:
        wanted = [s.strip() for s in args.districts.split(",") if s.strip()]
        missing = [s for s in wanted if s not in regions]
        if missing:
            print(f"错误: PSD 里没有这些区域组: {missing}")
            sys.exit(2)

    raw = Image.open(src).convert("RGBA")
    # 模拟 Photoshop 智能对象置入：删背景(按素材类型) → [低画质增强] → trim + 单步重采样 + 质心对齐 → 合成
    nobg, path_name = prepare_pattern(raw, enhance=args.enhance)
    cleaned, _, _ = fit_pattern(nobg)
    fa = np.asarray(cleaned)[..., 3]
    main_ratio = float((fa > 128).mean())
    print(f"素材: {src.name} {raw.size[0]}x{raw.size[1]} "
          f"路径={path_name} → 落位框内不透明占比 {main_ratio*100:.1f}%")
    if main_ratio < MIN_MAIN_RATIO:
        print(f"错误: 主体占图案区仅 {main_ratio*100:.1f}% (<{MIN_MAIN_RATIO*100:.0f}%)，素材或阈值无法认定，已停止")
        sys.exit(3)

    names = wanted or list(regions)
    ok = True
    for name in names:
        out = compose(regions[name], cleaned)
        f = outdir / f"{name}_256.png"
        out.save(f)
        line = f"{name}: {f.name} 尺寸={out.size[0]}x{out.size[1]}"
        if args.preview:
            pv = outdir / f"{name}_256_preview.png"
            checker_preview(out).save(pv)
            line += f" 预览={pv.name}"
        print(line)
        a = np.asarray(out)[..., 3]
        ratio = (a > 128).mean()
        if not (0.45 <= ratio <= 0.85):
            print(f"  [FAIL] 不透明占比 {ratio*100:.1f}% 超出六边形正常区间 (45~85%)")
            ok = False
    if not ok:
        sys.exit(2)
    print(f"完成: {len(names)} 张 → {outdir}")
    sys.exit(0)


if __name__ == "__main__":
    main()
