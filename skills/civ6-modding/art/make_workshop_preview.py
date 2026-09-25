#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""make_workshop_preview.py — 工坊预览图（Steam cover）生成器

## 解决什么问题

工坊预览图必须在 **≤ 1 MB** 的前提下尽量清晰，但实践中极易做糊。2026-09 本项目实测定位到
根因**不是尺寸、也不是源图质量，而是缩放方式选错**：

| 缩放方式（同一源图 → 同一目标尺寸） | 锐度（Laplacian 方差） |
|---|---|
| ImageMagick **默认滤镜 / Mitchell**（未写 `-filter` 时走这条） | 2,592.6 |
| `-filter Lanczos` | 4,842.4 |
| Lanczos 逐级减半 + unsharp | **13,047.4** ← 采定的标准 |

即「封面太模糊」几乎总是**单步降采样 + 默认滤镜偏软**造成的。本工具把采定的管线固化为可执行件：

1. **Lanczos 逐级减半**（如 3840→1920→960→512）——单步大幅降采样会混叠/发闷；
2. **unsharp 中度锐化**（`0x0.7+0.85+0.02` 等价参数）——锐化量经「锐度 vs 振铃」实测择优；
3. **剥掉无用 alpha**（母版若 alpha 恒 255 全不透明，alpha 通道纯属浪费编码）；
4. PNG 最高压缩 + strip 元数据。

## 为什么选用 Pillow

ImageMagick 的**默认滤镜是 Mitchell（偏软）**，而 PIL 必须显式给 `Image.LANCZOS` ——
用 PIL 可以从根上消灭「忘了写 `-filter` 就发糊」这类事故，且不再依赖本机 magick 路径。
PIL 链与历史上 IM 链是**质量等价**（同族滤波 + 同参数），**不是逐字节相同**
（判据见 `art-pipeline.md` §8.1「质量等价」）。

## 铁律：已经达标的成品不要再缩

Steam 预览图上限 1 MB，采定尺寸 **512×512**。若输入本身已是 512×512 的成品
（例如上一轮已上传的封面），**再跑一次缩放只会更糊** —— 本工具默认**拒绝二次缩放**：
输入尺寸 == 目标尺寸时直接**直通**（不改一个像素），加 `--force-resize` 才强制重采样。

## 用法

    # 母版 → 工坊预览图（默认 512，带质量自检）
    python make_workshop_preview.py <master.png> --out <ws>/image.png --qa

    # 源已是达标成品：直通 + 只做上限体检
    python make_workshop_preview.py <已有512.png> --out <ws>/image.png

    # 强制从"已达标"的图重采样（一般不该用）
    python make_workshop_preview.py <512.png> --out x.png --force-resize

    # 只体检不改文件
    python make_workshop_preview.py <master.png> --check

## 质量自检（--qa）

| 指标 | 含义 | 看什么 |
|---|---|---|
| `sharpness` | Laplacian 方差 | 越高越锐；采定管线在同源同尺寸下约 **1.3 万**（单步 640 软图仅约 2.6 千） |
| `ringing` | 锐化后相对**未锐化参考**的局部值域越界占比 % | 锐化振铃（白边/过冲）代理，**随锐化量单调**：无锐化 ≈2.7、采定档（85%）≈17、120% ≈22、200% ≈31 |

> ★ `ringing` 必须**相对未锐化参考**算才有意义 —— 「超出邻居值域」若拿锐化图自身的邻居来算，
> 度量会被源图纹理淹没（实测：采定的金标成品 3.4%，而锐化到 300% 的只有 4.6%，**无法区分**）。
> 故该指标**只在走了降采样+锐化的链路上报告**（此时参考就是锐化前的中间图）；
> 直通路径没有参考，只报 `sharpness`。

退出码：0 成功 / 1 失败 / 2 体检告警（超 1 MB、疑似放大、锐化过量等，不阻断）
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_SIZE = 512                 # 采定尺寸（2026-09 用户约定；Steam 上限 1 MB）
MAX_BYTES = 1 << 20                # 1 MB
UNSHARP_RADIUS = 0.7               # 等价 IM `-unsharp 0x0.7+0.85+0.02`
UNSHARP_PERCENT = 85
UNSHARP_THRESHOLD = 2
# 锐度参考（同源同尺寸单步 Lanczos 无锐化约为它的 1/2.7；见模块 docstring 对照表）
SHARP_REFERENCE = 13047.0
# 振铃门（相对未锐化参考的越界占比%）：采定档实测 ≈17，120% ≈22，200% ≈31 → 25 为"过头"线
RINGING_WARN_PCT = 25.0
RINGING_SEVERE_PCT = 31.0
RING_THRESHOLD = 6


def _sharpness(im):
    import numpy as np
    from numpy.lib.stride_tricks import sliding_window_view

    lum = np.asarray(im.convert("L"), dtype=np.float64)
    k = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)
    return float((sliding_window_view(lum, (3, 3)) * k).sum(axis=(-1, -2)).var())


def ringing_pct(im, ref_im):
    """锐化振铃代理：im 中心像素超出【未锐化参考】8 邻域值域的占比%。

    必须用 ref（未锐化中间图）取邻居值域，否则度量被源图纹理淹没、无法区分锐化量
    （见模块 docstring 的实测说明）。
    """
    import numpy as np

    a = np.asarray(im.convert("L"), dtype=np.float64)
    r = np.asarray(ref_im.convert("L"), dtype=np.float64)
    c = a[1:-1, 1:-1]
    n = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                n.append(r[1 + dy:r.shape[0] - 1 + dy, 1 + dx:r.shape[1] - 1 + dx])
    st = np.stack(n, axis=0)
    lo, hi = st.min(axis=0), st.max(axis=0)
    over = np.maximum(0.0, lo - c) + np.maximum(0.0, c - hi)
    return float((over > RING_THRESHOLD).mean() * 100.0)


def _flatten(im):
    """剥掉无用 alpha：全不透明 → RGB；有真实透明 → 压到黑底。"""
    if im.mode in ("RGBA", "LA"):
        alpha = im.getchannel("A")
        if alpha.getextrema() == (255, 255):
            return im.convert("RGB"), "alpha 恒 255 全不透明 → 已剥离"
        from PIL import Image as _I
        bg = _I.new("RGB", im.size, (0, 0, 0))
        bg.paste(im.convert("RGBA"), mask=alpha)
        return bg, "有真实透明 → 已压至黑底"
    return im.convert("RGB"), "无 alpha"


def resize_chain(im, target):
    """Lanczos 逐级减半 → 目标尺寸。返回 (图, 阶梯说明)。"""
    from PIL import Image

    steps, cur = [], im
    while cur.width > target * 2:
        nxt = cur.width // 2
        cur = cur.resize((nxt, nxt), Image.LANCZOS)
        steps.append(nxt)
    if cur.width != target:
        cur = cur.resize((target, target), Image.LANCZOS)
        steps.append(target)
    return cur, steps


def build(im, target=DEFAULT_SIZE, sharpen=True):
    """标准预览图管线：剥 alpha → Lanczos 阶梯 → unsharp。

    供其它脚本（如 `workshop_cover.py`）复用，避免各写一份"随手 resize"。
    返回 `(成品图, 未锐化参考图或 None, 阶梯 list)`；参考图用于振铃自检。
    """
    from PIL import ImageFilter

    im, _note = _flatten(im)
    im, steps = resize_chain(im, target)
    ref = None
    if sharpen:
        ref = im
        im = im.filter(ImageFilter.UnsharpMask(
            radius=UNSHARP_RADIUS, percent=UNSHARP_PERCENT, threshold=UNSHARP_THRESHOLD))
    return im, ref, steps


def main() -> int:
    ap = argparse.ArgumentParser(description="工坊预览图生成（Lanczos 阶梯 + unsharp）")
    ap.add_argument("master", help="母版 PNG（越大越好；已是成品则直通）")
    ap.add_argument("--out", default=None, help="输出 PNG（通常 <workspace>/image.png）")
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE, help="目标边长（默认 512）")
    ap.add_argument("--force-resize", action="store_true",
                    help="输入已达标时仍强制重采样（默认直通，避免二次缩放变糊）")
    ap.add_argument("--no-sharpen", action="store_true", help="跳过 unsharp（只降采样）")
    ap.add_argument("--qa", action="store_true", help="打印质量指标（锐度/振铃）")
    ap.add_argument("--check", action="store_true", help="只体检，不写文件")
    args = ap.parse_args()

    if not os.path.isfile(args.master):
        print("FAIL 找不到母版：%s" % args.master)
        return 1
    if not args.check and not args.out:
        print("FAIL 需要 --out（或改用 --check 只体检）")
        return 1

    try:
        from PIL import Image, ImageFilter
    except ImportError:
        print("FAIL 需要 Pillow：pip install pillow")
        return 1

    src = Image.open(args.master)
    print("母版    %s  %s %s  %d B" % (args.master, src.size, src.mode,
                                       os.path.getsize(args.master)))

    warn = []
    # 母版比目标还小 → 放大只会更糊，属用错素材
    if src.width < args.size:
        warn.append("母版 %dpx 小于目标 %dpx —— 放大不会增加细节，请改用更大的母版"
                    % (src.width, args.size))

    already = (src.width == args.size and src.height == args.size)
    if already and not args.force_resize:
        print("直通    输入已是 %d×%d 成品 → 不重采样（铁律：已达标不再二次缩放）" % (args.size, args.size))
        if args.check:
            pass
        elif os.path.abspath(args.master) != os.path.abspath(args.out):
            shutil.copyfile(args.master, args.out)
            print("已复制   %s" % args.out)
        else:
            print("源与目标同路径，未改动")
    elif already and args.force_resize:
        warn.append("输入已是 %d×%d 却要求强制重采样 —— 只会变糊，除非确知原始母版更大"
                    % (args.size, args.size))

    made = False
    ref_im = None          # 未锐化参考（仅降采样链路上有）
    check_target = args.master
    if already and not args.force_resize:
        # 直通：目标 == 输入，产物就是它本身
        check_target = args.out if (args.out and os.path.isfile(args.out)) else args.master
    elif args.check:
        # --check 且需要重采样：只体检【母版】，不把母版体积当产物体积来判 1 MB
        print("[--check] 未写盘（若要体检产物，请给 --out 让它先出图）。")
        check_target = None
    else:
        im, note = _flatten(src)
        print("通道    %s" % note)
        im, steps = resize_chain(im, args.size)
        if steps:
            print("阶梯    Lanczos 逐级减半 → %s" % " → ".join(str(s) for s in steps))
        if not args.no_sharpen:
            from PIL import ImageFilter
            ref_im = im                      # 锐化前留档，供振铃指标做参考
            im = im.filter(ImageFilter.UnsharpMask(
                radius=UNSHARP_RADIUS, percent=UNSHARP_PERCENT,
                threshold=UNSHARP_THRESHOLD))
            print("锐化    UnsharpMask radius=%.1f percent=%d threshold=%d"
                  % (UNSHARP_RADIUS, UNSHARP_PERCENT, UNSHARP_THRESHOLD))
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        im.save(args.out, "PNG", optimize=True, compress_level=9)
        made = True
        check_target = args.out
        print("已写出  %s  %d×%d  %d B" % (args.out, im.width, im.height,
                                           os.path.getsize(args.out)))

    # 1 MB 上限只对【真正的产物】判（直通时是目标文件，重采样时是新产物）
    if check_target and os.path.isfile(check_target):
        n = os.path.getsize(check_target)
        if n > MAX_BYTES:
            warn.append("产物 %d B 超过 Steam 预览图上限 1 MB（%d B）" % (n, MAX_BYTES))
        else:
            print("体积    %d B（Steam 上限 1 MB，占比 %.1f%%）" % (n, n * 100.0 / MAX_BYTES))

    if args.qa or args.check:
        try:
            if check_target:
                print("质量    锐度 %.1f（参考 %.0f）"
                      % (_sharpness(Image.open(check_target)), SHARP_REFERENCE))
            if ref_im is not None:
                r = ringing_pct(im, ref_im)
                print("振铃    %.1f%%（参考：无锐化 ≈2.7 / 采定 85%% ≈17 / 200%% ≈31）" % r)
                if r > RINGING_SEVERE_PCT:
                    warn.append("振铃 %.1f%% 超过 %.0f%% —— 锐化明显过量，建议降低锐化量"
                                % (r, RINGING_SEVERE_PCT))
                elif r > RINGING_WARN_PCT:
                    warn.append("振铃 %.1f%% 偏高（> %.0f%%）—— 检查锐化量是否有必要这么大"
                                % (r, RINGING_WARN_PCT))
            if made and not args.no_sharpen and check_target:
                sh = _sharpness(Image.open(check_target))
                if sh < SHARP_REFERENCE * 0.5:
                    warn.append("锐度偏低（%.0f < 参考的 50%%）—— 检查母版是否本就发虚、"
                                "或误用了单步/默认滤镜" % sh)
        except ImportError:
            print("WARN  --qa 需要 numpy：pip install numpy")

    for w in warn:
        print("WARN %s" % w)
    return 2 if warn else 0


if __name__ == "__main__":
    sys.exit(main())
