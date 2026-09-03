#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_icon.py — Civ6 图标规范化预处理（art-pipeline「图标规范化」专属章节的引擎）

背景：不同来源的图标源图（画布尺寸、边距、填充率、是否贴边各不相同）若直接进
convert_art.ps1 / make_atlas.py，会被硬拉伸/直接 resize，导致最终图标视觉权重不均、
贴边或失衡。本脚本在转 DDS 前把源图统一成一致构图。

设计（与 art-pipeline.md「图标规范化」章节一致）：
  * 每个 Icon 类别的 **已验证规范（verifed spec）** 固化在 ICON_SPECS；
  * CSV/JSON 化数据放入 spec 表；本次 Units 为经项目调研（Icons_Units.xml）验证的规范；
  * 未验证类别由调用方按 art-pipeline「三选一」决定（调研 / 原图入库 / 推断）——
    脚本只负责执行业已确定的规范参数（canvas/content/color/...），不替用户拍板。

用法（CLI）：
  python normalize_icon.py <in.png> [out.png] [--canvas 256] [--content 200] [--color 255]
  python normalize_icon.py <in.png> --role unit_icon        # 用 registry 内置规范
  python normalize_icon.py <in.png> --role unit_icon --show # 打印该类别规范参数

也可作模块被 make_atlas.py / convert_art.ps1 调用：
  from normalize_icon import normalize_icon, spec_for_role, ICON_SPECS
"""
import argparse
import sys
import json

from PIL import Image
import numpy as np

# ---------------------------------------------------------------------------
# 一、Icon 类别规范化规范 registry（已验证 / 推断）
# ---------------------------------------------------------------------------
# 字段含义：
#   canvas  : 统一主画布边长（= 该类别的最大档/基准档）
#   content : 内容最长边目标（px）；相对画布占比见 content_pct
#   color   : 剪影填充色（灰度=R=G=B；彩色图标传 None 保留原色）
#   status  : "verified"=已调研验证 | "inferred"=由其他类别推断（兜底） | None=未定
#   source  : 依据/来源说明
ICON_SPECS = {
    # ---- 已验证规范（本次调研：F:\Steam\...\Base\Assets\UI\Icons\Icons_Units.xml + 社区笔记）----
    "unit_icon": {
        "canvas": 256, "content": 200, "color": 255,
        "status": "verified",
        "source": "Icons_Units.xml (ICON_ATLAS_UNITS 256/80/50/38/32/22, FOW32); 项目实测 12 源验证",
        "note": "白色剪影+Alpha；内容最长边缩至 78%（≈28px 边距），几何居中；FOW 单独 32。",
    },
}

# 其余图标类别（leader/building/district/wonder/...）**故意未预填**：
# 下次触发时按 art-pipeline 第四节「三选一」由用户决定（调研新规范 / 原图直接入库 / 推断兜底），
# 脚本不替用户拍板；确定后再把参数加入 ICON_SPECS 并标 status。

DEFAULT_CANVAS = 256
DEFAULT_CONTENT = 200


def spec_for_role(role):
    """返回某类别规范 dict；未登记返回 None。"""
    return ICON_SPECS.get(role)


# ---------------------------------------------------------------------------
# 二、核心：规范化一张图
# ---------------------------------------------------------------------------
def normalize_icon(img, canvas=None, content=None, color=None, center=True):
    """
    返回规范化后的 RGBA 图（不落盘）。
      img     : PIL.Image（任意模式）
      canvas  : 画布边长（默认 256）
      content : 内容最长边目标 px（默认 200=78%）
      color   : 剪影填充灰度 0-255；None 保留原色（用于彩色图标）
      center  : 是否按 alpha bbox 几何居中
    """
    if canvas is None:
        canvas = DEFAULT_CANVAS
    if content is None:
        content = DEFAULT_CONTENT
    rgba = img.convert("RGBA")
    aa = np.array(rgba.getchannel("A"))
    ys, xs = np.where(aa > 0)
    if len(xs) == 0:
        raise ValueError("source has empty alpha; cannot normalize")
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()+1), int(ys.min()), int(ys.max()+1)
    bw, bh = x1-x0, y1-y0
    crop = rgba.crop((x0, y0, x1, y1))
    scale = content / max(bw, bh)
    nw, nh = max(1, round(bw*scale)), max(1, round(bh*scale))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)

    fill = color if color is not None else 255
    out = Image.new("RGBA", (canvas, canvas), (fill, fill, fill, 0))
    px, py = (canvas-nw)//2, (canvas-nh)//2
    out.paste(crop, (px, py), crop)
    if color is not None:
        c = np.array(out)
        c[..., 0] = color
        c[..., 1] = color
        c[..., 2] = color
        out = Image.fromarray(c, "RGBA")
    return out


# ---------------------------------------------------------------------------
# 三、CLI
# ---------------------------------------------------------------------------
def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", help="源 PNG（--show 时可不填）")
    ap.add_argument("output", nargs="?", help="输出 PNG（缺省 <输入>_normalized.png）")
    ap.add_argument("--canvas", type=int, default=None)
    ap.add_argument("--content", type=int, default=None)
    ap.add_argument("--color", type=int, default=None)
    ap.add_argument("--role", help="按 registry 内置规范执行")
    ap.add_argument("--show", action="store_true", help="打印某类别规范参数后退出")
    args = ap.parse_args()

    canvas, content, color = args.canvas, args.content, args.color
    role_note = None
    if args.role:
        spec = spec_for_role(args.role)
        if spec is None:
            sys.exit(f"role '{args.role}' 未登记规范；请按 art-pipeline 三选一后显式传 --canvas/--content")
        if args.show:
            print(f"{args.role}: {json.dumps(spec, ensure_ascii=False, indent=2)}")
            return
        canvas = canvas or spec.get("canvas") or DEFAULT_CANVAS
        content = content or spec.get("content") or DEFAULT_CONTENT
        # color 默认取 spec（未显式覆盖时）
        if color is None:
            color = spec.get("color")
        role_note = spec.get("status")

    if args.show:
        print(f"default canvas={canvas or DEFAULT_CANVAS} content={content or DEFAULT_CONTENT} "
              f"color={color}")
        return

    if not args.input:
        sys.exit("缺少 input；请给源图路径")
    inp, outp = args.input, args.output or (args.input.rsplit(".", 1)[0] + "_normalized.png")
    im = Image.open(inp)
    res = normalize_icon(im, canvas=canvas, content=content, color=color)
    res.save(outp, "PNG")
    bbox = res.getchannel("A").getbbox()
    margin = min(bbox[0], bbox[1], canvas-bbox[2], canvas-bbox[3])
    print(f"ok: {outp}  {res.size}  alpha_bbox={tuple(bbox)}  minMargin={margin}px"
          + (f"  [spec:{role_note}]" if role_note else ""))


if __name__ == "__main__":
    _main()
