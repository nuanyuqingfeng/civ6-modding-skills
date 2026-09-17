#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""apply_moment_template.py — 历史时刻插画：把源图套上官方形状模板

## 解决什么问题

Civ6 的「历史时刻」插画（`MOMENT_ILLUSTRATION_*`，见 `MomentIllustrations` 表）
在 UI 里以一张**固定形状的卡片**显示：456×332、四角透明、边缘有软过渡。
官方 240 张时刻图的 alpha 覆盖率全部落在 **83.0%~98.5%**（实测），
即它们都被同一族「卡片形状蒙版」裁过。

若直接把一张方形/不规则抠图当时刻图用，覆盖率会远低于该区间
（实测某工程两张漏套模板的图仅 **14.5% / 15.3%**），表现为：卡片边缘形状不对、
该透明的地方不透明、UI 里像贴了一块方形补丁。

## 官方形状从哪来

用户提供的历史时刻模板 PSD（`历史图片模板（新）/1..18.psd`）：
每个 PSD 的**数字命名图层**（`1` / `2` / … / `18`）就是一张官方形状蒙版
（alpha 即保留区，带软边）。实测这 18 个形状两两不同，且
**原版 240 张时刻图全部能匹配到其中之一**（二值 IoU 0.81~0.996，无 <0.80），
证明这 18 张就是官方形状族。

## 手工流程（本脚本要替代的 PS 操作）

用户既定流程：
  1. 打开模板 PSD；
  2. `Ctrl+左键点击` 模板数字图层 → 载入其像素为选区；
  3. 切到目标图片图层；
  4. `Ctrl+J` 复制为新图层；
  5. 单独导出该新图层 → 时刻图成品。

本脚本等价实现：`源图 alpha × 模板蒙版 = 成品 alpha`，颜色保留源图。

## 用法

    # 看有哪些模板及其覆盖率
    python apply_moment_template.py --list --template-dir "<模板目录>"

    # 单张：套 1 号模板
    python apply_moment_template.py --input 原图.png --template 1 --out 输出目录

    # 批量 + 自动挑最合适的模板（按源图 alpha 外接框长宽比匹配）
    python apply_moment_template.py --input-dir 源目录 --out 输出目录 --auto

    # 直接写 DDS（单 mip RGBA8，格式与工程既有 DDS 同构）
    python apply_moment_template.py --input a.png --template 1 --out out --dds

退出码：0 成功 / 1 参数或结构错误。
"""
import argparse
import glob
import os
import re
import sys

import numpy as np
from PIL import Image

try:
    from psd_tools import PSDImage
except ImportError:  # pragma: no cover
    print("需要 psd-tools：pip install psd-tools")
    raise SystemExit(1)

# 与 civ6-modding/art/dds_io.py 共用同一套 DDS 头（单一真源）
_HERE = os.path.dirname(os.path.abspath(__file__))
for _c in (os.path.join(_HERE, "..", "..", "civ6-modding", "art"),
           os.path.join(os.path.expanduser("~"), ".agents", "skills", "civ6-modding", "art")):
    if os.path.isfile(os.path.join(_c, "dds_io.py")):
        sys.path.insert(0, os.path.abspath(_c))
        break
try:
    from dds_io import write_dds
except ImportError:  # pragma: no cover
    write_dds = None

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MOMENT_W, MOMENT_H = 456, 332
MASK_THR = 128


# ---------------------------------------------------------------- 模板

def load_templates(tdir):
    """→ {模板号(int): (alpha_mask_float01, 原始alpha_uint8)}。"""
    if not os.path.isdir(tdir):
        raise SystemExit("模板目录不存在：%s" % tdir)
    out = {}
    for f in sorted(glob.glob(os.path.join(tdir, "*.psd")),
                    key=lambda x: int(re.sub(r"\D", "", os.path.basename(x)) or 0)):
        num = re.sub(r"\D", "", os.path.basename(f))
        if not num:
            continue
        psd = PSDImage.open(f)
        # 取「数字命名」的像素层 = 官方形状蒙版
        target = None
        for L in psd:
            nm = (L.name or "").strip()
            if L.kind == "pixel" and nm == num:
                target = L
                break
        if target is None:      # 退路：任一数字层
            for L in psd:
                nm = (L.name or "").strip()
                if L.kind == "pixel" and nm.isdigit():
                    target = L
                    break
        if target is None:
            print("  WARN 模板 %s 找不到数字蒙版层，跳过" % os.path.basename(f))
            continue
        a = np.asarray(target.composite().convert("RGBA"))[..., 3]
        m = np.zeros((psd.size[1], psd.size[0]), dtype=np.uint8)
        l, t, r, b = target.bbox
        h, w = a.shape
        dx0, dy0 = max(0, l), max(0, t)
        dx1, dy1 = min(m.shape[1], l + w), min(m.shape[0], t + h)
        if dx1 > dx0 and dy1 > dy0:
            sub = a[dy0 - t:dy0 - t + (dy1 - dy0), dx0 - l:dx0 - l + (dx1 - dx0)]
            m[dy0:dy1, dx0:dx1] = sub
        if (m > 8).sum() == 0:
            # 该 PSD 的数字层是空的（多为作者的中间工作稿，如 4.psd 用的是智能对象）
            print("  SKIP 模板 %s：数字层为空（非成品模板）" % os.path.basename(f))
            continue
        out[int(num)] = m
    return out


def template_signature(mask):
    """模板特征：覆盖率 + alpha 外接框长宽比（用于自动选模板）。"""
    nz = mask > 8
    cov = nz.mean()
    if not nz.any():
        return cov, 1.0
    ys, xs = np.nonzero(nz)
    bw = xs.max() - xs.min() + 1
    bh = ys.max() - ys.min() + 1
    return cov, bw / float(bh)


# ---------------------------------------------------------------- 合成

def apply_mask(src_img, mask):
    """源图 alpha × 模板蒙版 → 456×332 RGBA。颜色取源图。"""
    src = src_img.convert("RGBA")
    if src.size != (MOMENT_W, MOMENT_H):
        src = src.resize((MOMENT_W, MOMENT_H), Image.LANCZOS)
    a = np.asarray(src).astype(np.uint16)
    m = mask.astype(np.uint16)
    # 用「乘法」近似 PS 的选区裁切：保留两者都有的区域，并保留软边过渡
    a[..., 3] = (a[..., 3] * m // 255).astype(np.uint16)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def pick_template(src_img, templates):
    """按源图 alpha 外接框长宽比挑最接近的模板。"""
    a = np.asarray(src_img.convert("RGBA"))[..., 3]
    nz = a > 8
    if not nz.any():
        return 1
    ys, xs = np.nonzero(nz)
    bw = xs.max() - xs.min() + 1
    bh = ys.max() - ys.min() + 1
    r = bw / float(bh)
    best, bestd = None, 1e9
    for num, m in templates.items():
        cov, mr = template_signature(m)
        d = abs(mr - r)
        if d < bestd:
            best, bestd = num, d
    return best


def coverage(img):
    a = np.asarray(img.convert("RGBA"))[..., 3]
    return (a > 8).mean() * 100


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="历史时刻插画：套官方形状模板")
    ap.add_argument("--template-dir", default=r"D:\desktop\模板\历史图片模板（新）")
    ap.add_argument("--input", help="单个源图")
    ap.add_argument("--input-dir", help="源图目录（批量）")
    ap.add_argument("--template", type=int, help="模板编号 1..18")
    ap.add_argument("--auto", action="store_true", help="按长宽比自动挑模板")
    ap.add_argument("--out", required=False, default=".", help="输出目录")
    ap.add_argument("--dds", action="store_true", help="同时写单 mip RGBA8 DDS")
    ap.add_argument("--list", action="store_true", help="只列出模板信息")
    a = ap.parse_args()

    templates = load_templates(a.template_dir)
    if not templates:
        raise SystemExit("未加载到任何模板")
    print("加载模板 %d 个（%s）" % (len(templates), a.template_dir))

    if a.list:
        print()
        print("%-6s %-10s %-10s" % ("编号", "覆盖率%", "宽高比"))
        for num in sorted(templates):
            cov, r = template_signature(templates[num])
            print("%-6d %-10.1f %-10.3f" % (num, cov * 100, r))
        print()
        print("原版 240 张时刻图覆盖率区间：83.0% ~ 98.5%（成品应落在该区间）")
        return 0

    if not (a.input or a.input_dir):
        ap.print_help()
        return 1
    if not a.template and not a.auto:
        raise SystemExit("需指定 --template <编号> 或 --auto")

    os.makedirs(a.out, exist_ok=True)
    if a.input:
        files = [a.input]
    else:
        files = sorted(
            os.path.join(a.input_dir, f) for f in os.listdir(a.input_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".dds", ".tga")))

    print()
    print("%-44s %-7s %-9s %-9s %s" % ("source", "模板", "成品覆盖%", "区间判定", "输出"))
    print("-" * 108)
    n_ok = 0
    for p in files:
        try:
            if p.lower().endswith(".dds"):
                from dds_io import read_dds
                src = read_dds(p)
            else:
                src = Image.open(p)
                src.load()
        except Exception as e:
            print("  SKIP %s (%s)" % (os.path.basename(p), e))
            continue
        num = a.template if a.template else pick_template(src, templates)
        out_img = apply_mask(src, templates[num])
        cov = coverage(out_img)
        verdict = "OK" if 83.0 <= cov <= 99.0 else ("**偏低(漏套?)**" if cov < 83.0 else "偏高")
        stem = os.path.splitext(os.path.basename(p))[0]
        opng = os.path.join(a.out, stem + ".png")
        out_img.save(opng)
        line = "%-44s %-7d %-9.1f %-9s %s" % (stem, num, cov, verdict, os.path.basename(opng))
        if a.dds:
            if write_dds is None:
                raise SystemExit("--dds 需要 civ6-modding/art/dds_io.py")
            od = os.path.join(a.out, stem + ".dds")
            write_dds(od, out_img)
            line += "  +" + os.path.basename(od)
        print(line)
        n_ok += 1

    print()
    print("完成 %d 张 -> %s" % (n_ok, a.out))
    print()
    print("后续：")
    print("  1) 贴图登记进 m_ClassName=UITexture 的 UI_PrideMoments.xlp（PackageName=UI/PrideMoments）")
    print("  2) MomentIllustrations 表加行（MomentIllustrationType/MomentDataType/GameDataType/Texture）")
    print("  3) 跑 verify_moment.py 复核")
    return 0


if __name__ == "__main__":
    sys.exit(main())
