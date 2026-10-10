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

注意： 本脚本只做几何变换（裁 alpha bbox / 等比缩放 / 居中），**逐通道不改 RGB**。
  `color` 参数一旦赋值就是**把 R=G=B 整个覆盖掉**（`unit_icon` 的 color=255 就是
  故意做白色剪影）；**彩色类别（建筑/区域/项目/资源/伟人/领袖…）必须 color=None**。
  **严禁再加任何 levels / gamma / 亮度 / 对比度 / 饱和度 / 色相调整**。
  需要"提亮暗图"等超出裁剪/通道透明度/描边的处理时，**停下询问用户**。

用法（CLI）：
  python normalize_icon.py <in.png> [out.png] [--canvas 256] [--content 224] [--color 255]
  python normalize_icon.py <in.png> --role unit_icon        # 用 registry 内置规范
  python normalize_icon.py <in.png> --role unit_icon --show # 打印该类别规范参数
  python normalize_icon.py <in.png> --role unit_icon --slender-flush
        # 仅狭长图标（长短边比≥1.3）生效：长边平齐画布边缘（full-bleed）
  python normalize_icon.py <in.png> --role building_icon --outline-px 5 --outline-color 0,0,0
        # 在主体外侧补一圈纯色描边（模拟原版 3D 图标的描边）；描边画在主体之外，
        # 需满足 content + 2*outline_px <= canvas，否则会被裁掉

也可作模块被 make_atlas.py / convert_art.ps1 调用：
  from normalize_icon import normalize_icon, spec_for_role, ICON_SPECS
"""
import argparse
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PIL import Image
import numpy as np

# ---------------------------------------------------------------------------
# 一、Icon 类别规范化规范 registry（已验证 / 推断）
# ---------------------------------------------------------------------------
# 字段含义：
#   canvas  : 统一主画布边长（= 该类别的最大档/基准档）
#   content : 内容（主体）最长边目标（px）；**不含描边**，描边额外向外生长
#   color   : 剪影填充色（灰度=R=G=B；彩色图标传 None 保留原色）
#   outline : 可选 {"px": int, "rgb": [r,g,b]}；主体外侧纯色描边（原版 3D 图标同款）
#   status  : "verified"=已调研验证 | "inferred"=由其他类别推断（兜底） | None=未定
#   source  : 依据/来源说明
ICON_SPECS = {
    # ---- 已验证规范（本次调研：F:\Steam\...\Base\Assets\UI\Icons\Icons_Units.xml + 社区笔记）----
    "unit_icon": {
        "canvas": 256, "content": 224, "color": 255,
        "status": "verified",
        "source": "Icons_Units.xml (ICON_ATLAS_UNITS 256/80/50/38/32/22, FOW32); 项目实测 12 源验证; 2025-09 占幅调优复核",
        "note": "白色剪影+Alpha；内容最长边缩至 87.5%（≈16px 边距），几何居中；FOW 单独 32。"
                "狭长图标（长短边比≥1.3）可加 --slender-flush 让长边平齐画布边缘。",
    },

    # ---- 2026-09 实测调研（原版 SDK pantry 图集 8x8 切格逐格量，方法见 art-pipeline 第四节）----
    # 建筑：原版 Buildings256.dds 50 格实测。彩色，**不改色**；原版自带纯黑描边 ~5px@256。
    "building_icon": {
        "canvas": 256, "content": 210, "color": None,
        "outline": {"px": 6, "rgb": [0, 0, 0]},
        "status": "verified",
        "source": "SDK Assets/Civ6/pantry/Textures/Buildings{32,38,50,80,128,256}.dds 全 50 格实测(2026-09); "
                  "原版尺寸档 32/38/50/80/128/256; 对照原版 Icons_Buildings.xml(ICON_ATLAS_BUILDINGS)",
        "note": "彩色 3D 微缩（diorama）图标，**保留原色**（color=None）——严禁调色。"
                "原版主体最长边占画布 61%~96%（中位 82.6%），几何居中。"
                "本规范 content=210 + outline 6px => 总占幅 86.7%，落在原版 p75~p90（取偏满档，"
                "保证细高主体在 32px 仍可辨）；**细高/细宽（长短边比 <=0.65）可把 content 提到 215**"
                "（总 88.7%，对齐原版 CATHEDRAL 88 / GURDWARA 90）。"
                "描边实测：原版 alpha 边界内第 1~4 圈 rgb=(0,0,0)、第 5 圈过渡、第 6~9 圈回正常亮度；"
                "以本引擎扫 px=4..8，**px=6** 的描边深度剖面与原版最贴（d1~4=0, d5≈51, d6≈113 vs 原版 35~47 / 110~126），"
                "px=5 偏细 1px、px=7 偏粗。",
    },
    # 项目：原版 Projects256.dds 18 格实测。**固定模板**，不要重新构图。
    "project_icon": {
        "canvas": 256, "content": 223, "color": None,
        "outline": {"px": 6, "rgb": [0, 25, 45]},
        "status": "verified",
        "source": "SDK Assets/Civ6/pantry/Textures/Projects{30,32,38,50,70,80,256}.dds 全 18 格实测(2026-09); "
                  "对照原版 Icons_Projects.xml(ICON_ATLAS_PROJECTS)",
        "note": "注意： 原版项目图是**固定模板**：六边形边框 + 描边 rgb=(0,25,45)#00192D（实测 18 格全一致）"
                "任意美术无法靠几何规范化变进模板。**成品图应 normalize:false 直接入库**，"
                "本规范只用于**校验**（主体 bbox≈208x235、最长边 92.6%、描边剖面 (0,25,45)）。"
                "原版无 _FOW 变体，不要出 FOW。",
    },
    # 改良设施：原版与单位操作共用 ICON_ATLAS_UNIT_ACTIONS（尺寸档 38/50/80/256，无 _FOW 变体）。
    # 2026-09 实测 UnitActions256.dds 全部 23 个 ICON_IMPROVEMENT_* 格。
    "improvement_icon": {
        "canvas": 256, "content": 224, "color": None,
        "status": "verified",
        "source": "SDK Assets/Civ6/pantry/Textures/UnitActions256.dds 的 23 个 ICON_IMPROVEMENT_* 格实测(2026-09); "
                  "对照原版 Base/Assets/UI/Icons/Icons_UnitActions.xml(ICON_ATLAS_UNIT_ACTIONS)",
        "note": "原版改良图标主体最长边占画布 85.5%~100%（中位 92.6%），几何居中；本规范 content=224（87.5%）"
                "取实测区间内的保守值，与 unit_icon 口径一致（源图本身偏满时可显式传 --content 235）。"
                "原版是浅蓝灰插画（亮度 113~177 / 饱和度 5~25），color=None 保留原色，**严禁调色**；"
                "原版改良设施**没有** _FOW 变体，不要出 FOW。",
    },
}

# 其余图标类别（leader/building/district/wonder/...）**故意未预填**：
# 下次触发时按 art-pipeline 第四节「三选一」由用户决定（调研新规范 / 原图直接入库 / 推断兜底），
# 脚本不替用户拍板；确定后再把参数加入 ICON_SPECS 并标 status。

DEFAULT_CANVAS = 256
DEFAULT_CONTENT = 224

# 狭长图标判定：长短边比 ≥ 此值才允许 --slender-flush 长边平齐画布边缘
SLENDER_RATIO = 1.3


def spec_for_role(role):
    """返回某类别规范 dict；未登记返回 None。"""
    return ICON_SPECS.get(role)


OUTLINE_SS = 4              # 描边超采样倍率（抗锯齿）
OUTLINE_ALPHA_THRESH = 96   # 主体判定阈值
OUTLINE_BLUR_SIGMA = 0.8    # 描边外缘高斯平滑


def stroke_outline(img, px, rgb=(0, 0, 0), ss=OUTLINE_SS):
    """在 RGBA 图**外侧**补一圈纯色描边（模拟原版 3D 图标的描边）。

    做法（2026-09 建筑图标实测口径，成品描边剖面可与原版逐深度对齐）：
      alpha>96 取主体 mask -> 4x 超采样 -> 二值膨胀 px 像素 -> fill_holes 补内部空洞
      -> 描边层下采样回 1x（外缘自然抗锯齿）-> **把原图原样 alpha_composite 在描边之上**。

    关键：主体在 1x 直接合成，**不参与任何重采样**，RGB/Alpha 逐像素原样保留；
    只有描边层走 4x 超采样。也就是"只新增描边像素，绝不碰主体"。

    px  : 描边宽度（px，按最终尺寸计）
    rgb : 描边颜色。原版实测：建筑=(0,0,0)纯黑、项目=(0,25,45)#00192D
    """
    if not px or px <= 0:
        return img
    from scipy import ndimage
    src = img.convert("RGBA")
    w, h = src.size
    W, H = w*ss, h*ss
    alpha = np.array(src.getchannel("A").resize((W, H), Image.Resampling.LANCZOS))
    mask = alpha > OUTLINE_ALPHA_THRESH
    dil = ndimage.binary_fill_holes(ndimage.binary_dilation(mask, iterations=int(px)*ss))
    layer = np.zeros((H, W, 4), np.uint8)
    layer[..., 0], layer[..., 1], layer[..., 2] = int(rgb[0]), int(rgb[1]), int(rgb[2])
    layer[..., 3] = (dil * 255).astype(np.uint8)
    layer = np.array(Image.fromarray(layer, "RGBA").resize((w, h), Image.Resampling.LANCZOS))
    canvas = Image.fromarray(layer, "RGBA")
    canvas.alpha_composite(src)          # 主体 1:1 原样贴回，零重采样
    return canvas


# ---------------------------------------------------------------------------
# 二、核心：规范化一张图
# ---------------------------------------------------------------------------
def normalize_icon(img, canvas=None, content=None, color=None, center=True, slender_flush=False,
                   outline_px=0, outline_rgb=(0, 0, 0)):
    """
    返回规范化后的 RGBA 图（不落盘）。**几何操作，不改任何颜色**
    （例外只有两处显式选项：color 会把主体涂成灰度剪影、outline_rgb 只画描边像素）。

      img     : PIL.Image（任意模式）
      canvas  : 画布边长（默认 256）
      content : 内容（主体）最长边目标 px；**不含描边**，描边额外向外长出
      color   : 剪影填充灰度 0-255；None 保留原色（彩色图标**必须** None）
      center  : 是否按 alpha bbox 几何居中
      slender_flush : 仅当源图为狭长构图（长短边比≥SLENDER_RATIO）时生效——
                      长边缩放至画布边长、直接平齐边缘；非狭长图标忽略此开关。
      outline_px    : >0 时在主体外侧补该宽度（按最终尺寸计）的纯色描边
      outline_rgb   : 描边颜色
    """
    if canvas is None:
        canvas = DEFAULT_CANVAS
    if content is None:
        content = DEFAULT_CONTENT
    if outline_px and content + 2*outline_px > canvas:
        print("WARN: content(%s) + 2*outline_px(%s) = %s > canvas(%s), 描边会被裁掉" % (content, outline_px,
              content + 2*outline_px, canvas), file=sys.stderr)
    rgba = img.convert("RGBA")
    aa = np.array(rgba.getchannel("A"))
    ys, xs = np.where(aa > 0)
    if len(xs) == 0:
        raise ValueError("source has empty alpha; cannot normalize")
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()+1), int(ys.min()), int(ys.max()+1)
    bw, bh = x1-x0, y1-y0
    crop = rgba.crop((x0, y0, x1, y1))
    slender = slender_flush and (max(bw, bh) / min(bw, bh)) >= SLENDER_RATIO
    scale = (canvas if slender else content) / max(bw, bh)
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
    if outline_px:
        out = stroke_outline(out, outline_px, outline_rgb)
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
    ap.add_argument("--slender-flush", action="store_true",
                    help="狭长图标（长短边比≥%.1f）长边平齐画布边缘；非狭长图标忽略" % SLENDER_RATIO)
    ap.add_argument("--outline-px", type=int, default=None,
                    help="主体外侧纯色描边宽度(px)，0=不加（原版建筑=5）")
    ap.add_argument("--outline-color", default=None,
                    help="描边颜色 R,G,B（原版建筑=0,0,0；原版项目=0,25,45）")
    ap.add_argument("--show", action="store_true", help="打印某类别规范参数后退出")
    args = ap.parse_args()

    canvas, content, color = args.canvas, args.content, args.color
    outline_px, outline_rgb = args.outline_px, None
    if args.outline_color:
        parts = [int(x) for x in str(args.outline_color).replace(" ", "").split(",")]
        if len(parts) != 3:
            sys.exit("--outline-color 需要 R,G,B 三个数字")
        outline_rgb = tuple(parts)
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
        # outline 默认取 spec（未显式覆盖时）
        _o = spec.get("outline") or {}
        if outline_px is None:
            outline_px = _o.get("px", 0)
        if outline_rgb is None:
            outline_rgb = tuple(_o.get("rgb", (0, 0, 0)))
        role_note = spec.get("status")

    if args.show:
        print(f"default canvas={canvas or DEFAULT_CANVAS} content={content or DEFAULT_CONTENT} "
              f"color={color}")
        return

    if not args.input:
        sys.exit("缺少 input；请给源图路径")
    inp, outp = args.input, args.output or (args.input.rsplit(".", 1)[0] + "_normalized.png")
    im = Image.open(inp)
    res = normalize_icon(im, canvas=canvas, content=content, color=color,
                         slender_flush=args.slender_flush,
                         outline_px=(outline_px or 0),
                         outline_rgb=(outline_rgb or (0, 0, 0)))
    res.save(outp, "PNG")
    bbox = res.getchannel("A").getbbox()
    margin = min(bbox[0], bbox[1], canvas-bbox[2], canvas-bbox[3])
    print(f"ok: {outp}  {res.size}  alpha_bbox={tuple(bbox)}  minMargin={margin}px"
          + (f"  [spec:{role_note}]" if role_note else "")
          + (f"  [outline {outline_px}px {outline_rgb}]" if outline_px else "")
          + ("  [slender-flush]" if args.slender_flush else ""))


if __name__ == "__main__":
    _main()
