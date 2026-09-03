#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""apply_fow.py — 给图标/图集 PNG 套上原版风格的迷雾（FOW）蒙版。v4 模型。

v4 在 v3 半透明薄膜架构上，按图像分析报告实现四项改进：
  1. 薄膜三段 Sigmoid 平滑过渡（cut1=65, cut2=160），只微调常数项不改透出率 k，
     保留原图 30-45% 固有色透出（拒绝全局暖化）；
  2. DoG 边缘检测墨线层，在薄膜之后最后叠加——轮廓不被薄膜冲淡，始终保持深墨色；
  3. 排线密度梯度调制：缝隙/褶皱（高梯度）间距加密到 4px，平坦区稀疏到 9px，
     排线不透明度随亮度带衰减（中间调最强、亮/暗两端减弱），消除硬截断断层；
  4. 画框内侧径向暗角（中心 1.0 → 边缘 0.82，余弦平滑），只作用于不透明区。

用法：
  python apply_fow.py --input <图标.png|dds> [--output <路径>]
                      [--hatch-strength 0.55] [--no-hatch] [--no-ink] [--no-vignette]

默认输出 <输入名>_FOW.png（DDS 源自动转 RGBA 处理，输出一律 PNG）。
产出 PNG 后走 civ6-modding art-pipeline 转 DDS/.tex（role=fow）。
依赖：numpy、Pillow。
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

INK = np.array([74.0, 53.0, 22.0])
STROKE = np.array([56.0, 36.0, 12.0])
# 逐通道 (透出率 k, 薄膜贡献 m)：k 锁定，m 按 v4 豆包报告修正——
# R 提升最大 / B 压低抑制橄榄绿，亮段整体抬升减轻高光压暗
FILM_MID = (np.array([0.30, 0.42, 0.43]), np.array([124.0, 78.0, 19.0]))
FILM_BRI = (np.array([0.48, 0.41, 0.30]), np.array([160.0, 132.0, 84.0]))
# 背景专属变换（官方配对样本背景区单独拟合，v9）：
# 比主体薄膜更亮、B 保留更多（紫底→玫瑰金而非黄棕），匹配官方"底色明亮金黄/玫瑰土金"
BG_FILM = (np.array([0.385, 0.340, 0.276]), np.array([94.6, 82.2, 49.2]))


def _smooth(x, lo, hi):
    """sigmoid 平滑阶跃：lo 前 0，hi 后 1。"""
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def _gauss(arr, radius):
    """单通道 float 数组高斯模糊（经 PIL）。"""
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), float)


def _dog_edges(gray: np.ndarray, sigma_small=1.2, sigma_big=2.2) -> np.ndarray:
    """DoG 边缘强度：暗线位置为正，0-1 归一。"""
    dog = _gauss(gray, sigma_small) - _gauss(gray, sigma_big)
    e = np.clip(-dog, 0, None)
    peak = np.percentile(e, 97)
    return np.clip(e / peak, 0, 1) if peak > 0 else e * 0


def _morph(mask_u8: np.ndarray, radius: int, grow: bool) -> np.ndarray:
    im = Image.fromarray(mask_u8, "L")
    f = ImageFilter.MaxFilter(radius * 2 + 1) if grow else ImageFilter.MinFilter(radius * 2 + 1)
    return np.asarray(im.filter(f), float)


def fow_transform(im: Image.Image, hatch_strength: float = 0.62,
                  ink_strength: float = 0.55, ink_outer_boost: float = 0.15,
                  vignette: bool = True,
                  hatch_lo: int = 60, hatch_peak: int = 120, hatch_hi: int = 178,
                  subject_dist: int = 90, strength: float = 1.0) -> Image.Image:
    a = np.asarray(im.convert("RGBA"), float)
    rgb, alpha = a[..., :3], a[..., 3]
    L = rgb @ np.array([0.299, 0.587, 0.114])
    k_mid, m_mid = FILM_MID
    k_bri, m_bri = FILM_BRI

    # 1. 三段薄膜（Sigmoid 过渡，cut1=65 / cut2=152；线稿上界 75 防止底色被墨色权重拖暗）
    w_ink = 1 - _smooth(L, 45, 75)
    w_bri = _smooth(L, 132, 172)
    w_mid = np.clip(1 - w_ink - w_bri, 0, 1)
    out = (INK * w_ink[..., None]
           + (rgb * k_mid + m_mid) * w_mid[..., None]
           + (rgb * k_bri + m_bri) * w_bri[..., None])
    if strength < 1.0:
        # 保留更多原色：薄膜结果与原色插值（仅作用于薄膜输出，alpha 不动）
        out = rgb * (1 - strength) + out * strength
    # 4. 径向暗角：中心 1.0 → 画框内缘 0.88，余弦平滑，只作用于不透明区
    h, w = L.shape
    yy, xx = np.mgrid[0:h, 0:w]
    if vignette:
        r = np.maximum(np.abs(xx - (w - 1) / 2) / (w / 2),
                       np.abs(yy - (h - 1) / 2) / (h / 2))
        vign = 1 - 0.12 * _smooth(r, 0.82, 1.0)
        out *= vign[..., None]

    # -- 背景主色与主体掩码（墨线环与排线共用，双条件：颜色距离 OR 梯度幅值）--
    q = (rgb // 24).astype(int).reshape(-1, 3)
    code = (q[:, 0] * 65536 + q[:, 1] * 256 + q[:, 2]).reshape(h, w)
    vals, counts = np.unique(code[alpha > 200], return_counts=True)
    bg = vals[counts.argmax()]
    bg_rgb = np.array([(bg >> 16) & 255, (bg >> 8) & 255, bg & 255], float) + 12
    gx, gy = np.gradient(_gauss(L, 1.5))
    gmag = np.clip(np.hypot(gx, gy) / 24, 0, 1)
    gmag = _gauss(gmag, 3.0)
    subject = ((np.abs(rgb - bg_rgb[None, None, :]).sum(axis=2) > subject_dist)
               | (gmag > 0.35)) & (alpha > 128)
    subject_f = _gauss(subject * 255.0, 1.0) / 255

    # 1.5 背景专属变换（v9 分离处理）：与背景主色接近的平坦区走背景薄膜——
    # 比主体薄膜更亮、B 保留更多，复刻官方"底色明亮金黄/玫瑰土金"（暗框 L<50 不参与）
    kbg, mbg = BG_FILM
    bg_flat = ((np.abs(rgb - bg_rgb[None, None, :]).sum(axis=2) <= subject_dist)
               & (alpha > 128) & (L >= 50))
    bg_w = _gauss(bg_flat * 255.0, 1.5) / 255
    out = out * (1 - bg_w[..., None]) + (rgb * kbg + mbg) * bg_w[..., None]

    # 2. DoG 墨线层（薄膜之后最后叠加）：外轮廓/内部褶皱双强度
    gray_s = _gauss(L, 1.0)
    if ink_strength > 0:
        e = _dog_edges(gray_s)
        # 外轮廓环：主体掩码的形态学梯度（膨胀-腐蚀），该圈上的墨线加强
        sb = (subject * 255).astype(np.uint8)
        ring = np.abs(_morph(sb, 2, True) - _morph(sb, 2, False))
        ring = _gauss(ring, 1.0) / 255
        strength_map = ink_strength + ink_outer_boost * np.clip(ring * 2, 0, 1)
        ink_a = e * strength_map * _smooth(alpha, 100, 200)
        out = out * (1 - ink_a[..., None]) + INK * ink_a[..., None]

    # 3. 排线：密度梯度调制 + 亮度带不透明度衰减 + 高光抑制
    if hatch_strength > 0:
        # 局部间距：平坦 9px → 高梯度 4px（相位场连续变化，线随密度弯曲）
        spacing = 9 - 5 * gmag
        phase = (yy - xx) / spacing
        pattern = (phase - np.floor(phase)) < (2.0 / spacing)
        # 亮度带（hi=178 上沿提前截止）+ 高光截断：L>175 起排线快速衰减到 0
        band = np.clip(1 - np.abs(L - hatch_peak) / (hatch_hi - hatch_lo), 0, 1)
        band = band * band * (3 - 2 * band)
        highlight = np.clip(1 - (L - 175) / 80, 0, 1)
        ta = pattern * band * subject_f * highlight * hatch_strength
        out = out * (1 - ta[..., None]) + STROKE * ta[..., None]

    res = np.dstack([np.clip(out, 0, 255), alpha]).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def main() -> None:
    ap = argparse.ArgumentParser(description="给图标加原版风格 FOW 迷雾蒙版（v4 半透明薄膜+密度排线，PNG 输出）")
    ap.add_argument("--input", required=True, help="原图标 png/dds（支持图集，整图处理）")
    ap.add_argument("--output", help="输出路径（默认 <输入名>_FOW.png）")
    ap.add_argument("--hatch-strength", type=float, default=0.62, help="排线强度 0-1（默认 0.62）")
    ap.add_argument("--ink-strength", type=float, default=0.55, help="DoG 墨线层基础强度 0-1（默认 0.55，外轮廓自动 +0.15）")
    ap.add_argument("--no-hatch", action="store_true", help="不叠加排线")
    ap.add_argument("--no-ink", action="store_true", help="不叠加墨线层")
    ap.add_argument("--no-vignette", action="store_true", help="不加径向暗角")
    ap.add_argument("--strength", type=float, default=1.0,
                    help="薄膜强度 0-1（默认 1.0；<1 与原图色插值，保留更多原色）")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"错误：找不到 {src}")
    im = Image.open(src).convert("RGBA")

    out = fow_transform(im, hatch_strength=0 if args.no_hatch else args.hatch_strength,
                        ink_strength=0 if args.no_ink else args.ink_strength,
                        vignette=not args.no_vignette, strength=args.strength)

    dst = Path(args.output) if args.output else src.with_name(src.stem + "_FOW.png")
    out.save(dst)
    print(f"输入 {src} {im.size}")
    print(f"生成 {dst}")


if __name__ == "__main__":
    main()
