#!/usr/bin/env python3
"""文明6 忠诚度/宗教图标合成：图标 + 黑色光晕模板 → PNG 组。

--kind loyalty（默认，{SUFFIX} = 文明内部名去掉 CIVILIZATION_ 前缀）：
  Loyalty_Overlay_{SUFFIX}.png              512×512  3D 材质贴图（光晕 + 图标）
  StrategicView_Loyalty_Overlay_{SUFFIX}.png 256×256  战略视图（512 版 LANCZOS 缩小）
  Loyalty_Pressure_{SUFFIX}.png             128×128  3D 压力贴图（白色小剪影）
  StrategicView_Loyalty_Pressure_{SUFFIX}.png 128×128 战略视图（与 128 版相同）

--kind religion（{SUFFIX} = 宗教类型去掉 RELIGION_ 前缀；战略视图无覆盖层，共 3 张）：
  Religion_Overlay_{SUFFIX}.png    512×512  3D 材质贴图（光晕 + 图标）
  Religion_Pressure_{SUFFIX}.png   128×128  3D 压力贴图（白色小剪影）
  ReligionPressureIcon_{SUFFIX}.png 128×128 战略视图压力 sprite（与 128 版相同）

尺寸判定（默认 core 模式）：以图标 alpha 质量（不透明像素的集中区域）而非最外圈
像素做基准——徽记外围的射线/飘带等稀疏装饰不参与定标，主体大小贴合官方光晕轮廓；
全图随核心框一起缩放，核心中心对齐画布中心。

摆放参数来自官方 Loyalty_Overlay_Template.psd / Loyalty_Pressure_Template.psd 图层实测：
  Overlay：核心区 fit 进 227×269 盒，居中 (256,256)，叠在光晕上层（保持原色）
  Pressure：核心区 fit 进 40×48 盒，居中 (64,64)，白色剪影（RGB→255 保留 alpha）
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_GLOW = SKILL_DIR / "templates" / "Loyalty_Overlay_Template.png"

OVERLAY_SIZE = (512, 512)
OVERLAY_BOX = (227, 269)   # 图标内容（裁掉透明边后）适配盒，来自 PSD 智能对象实测
PRESSURE_SIZE = (128, 128)
PRESSURE_BOX = (40, 48)

ICON_EXTS = [".png", ".dds"]


def load_rgba(path: Path) -> Image.Image:
    im = Image.open(path)
    return im.convert("RGBA")


def trim_content(im: Image.Image) -> Image.Image:
    """裁掉四周全透明边，返回内容区。"""
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise SystemExit(f"错误：图标 {im} 没有任何非透明像素")
    return im.crop(bbox)


def core_box(im: Image.Image, keep: float) -> tuple[int, int, int, int]:
    """按 alpha 质量百分位求"主体集中区"包围盒 (l, t, r, b)。

    对横/竖两个方向的 alpha 边际分布各裁掉 (1-keep)/2 的尾部质量，
    使该盒包含约 keep 比例的不透明质量——外围稀疏装饰（射线、飘带）不参与定标。
    """
    w, h = im.size
    alpha = list(im.getchannel("A").getdata())
    col = [0] * w
    row = [0] * h
    for i, a in enumerate(alpha):
        if a:
            col[i % w] += a
            row[i // w] += a
    total = sum(row)

    def bounds(dist: list[int]) -> tuple[int, int]:
        tail = total * (1.0 - keep) / 2.0
        lo, acc = 0, 0.0
        while lo < len(dist) and acc + dist[lo] <= tail:
            acc += dist[lo]
            lo += 1
        hi, acc = len(dist) - 1, 0.0
        while hi > lo and acc + dist[hi] <= tail:
            acc += dist[hi]
            hi -= 1
        return lo, hi + 1

    l, r = bounds(col)
    t, b = bounds(row)
    return (l, t, r, b)


def fit_transform(content: Image.Image, box: tuple[int, int], keep: float,
                  fit_mode: str) -> tuple[Image.Image, tuple[int, int]]:
    """按判定基准等比缩放，返回 (缩放后的全图, 核心中心在画布上的落点)。

    core 模式：核心集中区适配 box，全图同比例缩放；
    extent 模式：整体内容区适配 box（旧行为）。
    返回的落点用于把核心中心对齐到目标画布中心。
    """
    if fit_mode == "extent":
        scaled = fit_contain(content, box)
        return scaled, (scaled.size[0] / 2, scaled.size[1] / 2)
    l, t, r, b = core_box(content, keep)
    core_w, core_h = max(1, r - l), max(1, b - t)
    scale = min(box[0] / core_w, box[1] / core_h)
    nw, nh = max(1, round(content.size[0] * scale)), max(1, round(content.size[1] * scale))
    scaled = content.resize((nw, nh), Image.LANCZOS)
    core_cx, core_cy = (l + r) / 2 * scale, (t + b) / 2 * scale
    return scaled, (core_cx, core_cy)


def fit_contain(content: Image.Image, box: tuple[int, int]) -> Image.Image:
    """等比缩放内容使其完全装入 box（contain），使用 LANCZOS。"""
    w, h = content.size
    scale = min(box[0] / w, box[1] / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    return content.resize((nw, nh), Image.LANCZOS)


def whiten(im: Image.Image) -> Image.Image:
    """白色剪影：RGB 全部置 255，保留 alpha。"""
    a = im.getchannel("A")
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(a)
    return white


def find_project_icon(project: Path, kind: str = "loyalty") -> Path:
    """在工程 Textures 目录里找尺寸最大的文明/宗教图标。"""
    tex_dir = project / "Textures"
    if not tex_dir.is_dir():
        raise SystemExit(f"错误：工程下不存在 {tex_dir}")
    prefix = "ICON_CIVILIZATION_" if kind == "loyalty" else "ICON_RELIGION_"
    candidates = []
    for p in tex_dir.iterdir():
        if p.suffix.lower() in ICON_EXTS and p.name.startswith(prefix):
            # 排除 _22/_30 之类小尺寸以外的衍生命名干扰，统一按像素尺寸排序
            candidates.append(p)
    if not candidates:
        raise SystemExit(f"错误：{tex_dir} 下找不到 {prefix}* 图标")
    best = max(candidates, key=lambda p: Image.open(p).size)
    return best


def compose(kind: str, suffix: str, icon: Image.Image, glow_path: Path, out_dir: Path,
            whiten_overlay: bool, keep: float, fit_mode: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []

    # 1. 3D 覆盖贴图 512：光晕置底，图标核心区 fit 后叠在光晕上层（保持全亮）
    glow = load_rgba(glow_path)
    if glow.size != OVERLAY_SIZE:
        raise SystemExit(f"错误：光晕模板应为 {OVERLAY_SIZE}，实际 {glow.size}")
    content = trim_content(icon)
    if whiten_overlay:
        content = whiten(content)
    scaled, (ccx, ccy) = fit_transform(content, OVERLAY_BOX, keep, fit_mode)
    px = round(OVERLAY_SIZE[0] / 2 - ccx)
    py = round(OVERLAY_SIZE[1] / 2 - ccy)
    if scaled.size[0] > OVERLAY_SIZE[0] or scaled.size[1] > OVERLAY_SIZE[1]:
        print(f"警告：{suffix} 图标缩放后 {scaled.size} 超出 {OVERLAY_SIZE}，已夹回画布边缘", file=sys.stderr)
    px = min(max(px, 0), OVERLAY_SIZE[0] - scaled.size[0])
    py = min(max(py, 0), OVERLAY_SIZE[1] - scaled.size[1])
    overlay = glow.copy()
    overlay.alpha_composite(scaled, (px, py))

    # 3. 3D 压力贴图 128：白色小剪影，核心区 fit 居中，透明背景
    # 全画布 RGB 置白、只让 alpha 承载剪影（仿 PS 导出的白色溢出，
    # 避免引擎双线性过滤在图标边缘采到黑边）
    small, (ccx, ccy) = fit_transform(whiten(content), PRESSURE_BOX, keep, fit_mode)
    tmp = Image.new("RGBA", PRESSURE_SIZE, (0, 0, 0, 0))
    px = round(PRESSURE_SIZE[0] / 2 - ccx)
    py = round(PRESSURE_SIZE[1] / 2 - ccy)
    px = min(max(px, 0), PRESSURE_SIZE[0] - small.size[0])
    py = min(max(py, 0), PRESSURE_SIZE[1] - small.size[1])
    tmp.alpha_composite(small, (px, py))
    pressure = Image.new("RGBA", PRESSURE_SIZE, (255, 255, 255, 0))
    pressure.putalpha(tmp.getchannel("A"))

    if kind == "religion":
        p1 = out_dir / f"Religion_Overlay_{suffix}.png"
        overlay.save(p1)
        results.append(p1)
        p2 = out_dir / f"Religion_Pressure_{suffix}.png"
        pressure.save(p2)
        results.append(p2)
        p3 = out_dir / f"ReligionPressureIcon_{suffix}.png"
        pressure.save(p3)
        results.append(p3)
        return results

    p1 = out_dir / f"Loyalty_Overlay_{suffix}.png"
    overlay.save(p1)
    results.append(p1)

    # 2. 战略视图覆盖贴图 256：512 版 LANCZOS 缩小
    p2 = out_dir / f"StrategicView_Loyalty_Overlay_{suffix}.png"
    overlay.resize((256, 256), Image.LANCZOS).save(p2)
    results.append(p2)

    p3 = out_dir / f"Loyalty_Pressure_{suffix}.png"
    pressure.save(p3)
    results.append(p3)

    # 4. 战略视图压力贴图 128：与 3D 版相同
    p4 = out_dir / f"StrategicView_Loyalty_Pressure_{suffix}.png"
    pressure.save(p4)
    results.append(p4)

    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="文明6 忠诚度/宗教图标合成")
    ap.add_argument("--kind", choices=["loyalty", "religion"], default="loyalty",
                    help="loyalty=文明忠诚度 4 张（默认）；religion=宗教压力 3 张（无 SV 覆盖层）")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--icon", help="图标源文件路径（png/dds，建议 ≥256）")
    src.add_argument("--project", help="工程路径：自动从 <project>/Textures 找最大的 "
                                       "ICON_CIVILIZATION_*（loyalty）/ ICON_RELIGION_*（religion）")
    ap.add_argument("--suffix", required=True,
                    help="loyalty：文明内部名去掉 CIVILIZATION_ 前缀（如 RAGUNNA_QYQXP）；"
                         "religion：宗教类型去掉 RELIGION_ 前缀（如 CUSTOM_RGN）")
    ap.add_argument("--out-dir", default=None,
                    help="输出目录（默认 D:\\desktop\\loyalty_out / D:\\desktop\\religion_out）")
    ap.add_argument("--glow", default=str(DEFAULT_GLOW), help="光晕模板路径（默认 skill 内置）")
    ap.add_argument("--whiten-overlay", action="store_true",
                    help="覆盖贴图中的图标也做白色剪影（源图标为彩色时使用；官方样例默认保持原色）")
    ap.add_argument("--fit-mode", choices=["core", "extent"], default="core",
                    help="尺寸判定基准：core=alpha 质量集中区（默认，外围稀疏装饰不参与定标）；extent=最外圈像素（旧行为）")
    ap.add_argument("--keep", type=float, default=0.90,
                    help="core 模式下核心区包含的 alpha 质量比例（默认 0.90，调大→核心区更大→图标更小）")
    args = ap.parse_args()

    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_dir = Path(r"D:\desktop") / ("loyalty_out" if args.kind == "loyalty" else "religion_out")

    icon_path = Path(args.icon) if args.icon else find_project_icon(Path(args.project), args.kind)
    icon = load_rgba(icon_path)
    if max(icon.size) < 128:
        print(f"警告：图标仅 {icon.size[0]}px，建议 ≥256，小图放大会发糊", file=sys.stderr)

    results = compose(args.kind, args.suffix, icon, Path(args.glow), out_dir,
                      args.whiten_overlay, args.keep, args.fit_mode)
    print(f"图标源：{icon_path} {icon.size}")
    for p in results:
        print(f"  生成 {p}")


if __name__ == "__main__":
    main()
