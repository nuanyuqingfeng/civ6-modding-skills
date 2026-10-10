"""ps_place_district.py — 区域图标 PS 自动化引擎（效果最好的首选流程）

用法：
  python ps_place_district.py --input <图案.png> --outdir <目录> [--enhance] [--psd <自定义模板.psd>]

先用 build_district_icon.pattern_canvas 按落位框完成构图（与模拟引擎同一套 fit_pattern），
再交本机 Photoshop 编辑内置模板的 District Alpha 智能对象 → 原位置入 → 逐区域导出。
Photoshop 只承担渐变、描边、发光的原生光栅化，不再自行缩放或居中素材。
退出码: 0 成功; 2 输入/参数错误; 4 本机 Photoshop 不可用（由 AI 询问用户：
改走 build_district_icon.py 模拟管线（效果较差），或安装 Photoshop 后重跑）。

素材前置与模拟引擎共用（build_district_icon.prepare_pattern）：自带透明通道跳过删背景，
近黑背景灰度图走亮度映射，彩色无 alpha 走通用背景距离；--enhance 低画质增强同样适用。
依赖: pywin32（win32com）、psd-tools、Pillow、numpy、scipy、opencv-python。
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_district_icon as b  # noqa: E402

try:
    from psd_tools import PSDImage  # noqa: F401
except ImportError:
    print("缺少 psd_tools: pip install psd-tools")
    sys.exit(2)

JSX = Path(__file__).resolve().parent / "ps_place_district.jsx"
PARAMS = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))) / "civ6_district_ps_params.txt"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="白色图案素材 PNG")
    ap.add_argument("--outdir", required=True, help="成品输出目录")
    ap.add_argument("--psd", default=str(b.DEFAULT_PSD),
                    help=f"区域图标模板 PSD（默认内置: {b.DEFAULT_PSD.name}）")
    ap.add_argument("--enhance", action="store_true",
                    help="低画质素材预处理：小图放大 + alpha 对比度拉伸 + UnsharpMask 锐化")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    if not src.is_file():
        print(f"错误: 找不到素材 {src}")
        sys.exit(2)
    psd = Path(args.psd).resolve()
    if not psd.is_file():
        print(f"错误: 找不到 PSD {psd}")
        sys.exit(2)
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    raw = Image.open(src).convert("RGBA")
    nobg, path_name = b.prepare_pattern(raw, enhance=args.enhance)
    # 构图预调整：先用自建引擎的 fit_pattern（trim + 单步重采样 + 质心对齐）把图案落进
    # 模板落位框，铺满与智能对象内嵌工作稿等大的画布。PS 只承担效果光栅化，构图沿用自建流程。
    inner, transform = b.smart_object_placement(psd)
    canvas = b.pattern_canvas(nobg, inner, transform)
    material = PARAMS.parent / f"civ6_district_ps_import_{src.stem}.png"
    canvas.save(material)
    print(f"素材: {src.name} {raw.size[0]}x{raw.size[1]} 路径={path_name} "
          f"→ 构图预调整 {inner[0]}x{inner[1]} 置入 PS: {material.name}")

    PARAMS.write_text(
        f"psd={psd.as_posix()}\n"
        f"material={material.as_posix()}\n"
        f"outdir={outdir.as_posix()}\n",
        encoding="utf-8")

    jsx = JSX.read_text(encoding="utf-8")

    import pythoncom
    from win32com.client import Dispatch
    pythoncom.CoInitialize()
    try:
        app = Dispatch("Photoshop.Application")
    except Exception as e:  # COM 连接失败 = 本机无可用 Photoshop
        print(f"错误: 本机 Photoshop 不可用（{e.__class__.__name__}: {e}）")
        print("需询问用户：改走 build_district_icon.py 模拟管线（效果较差），或安装 Photoshop 后重跑")
        sys.exit(4)
    result = app.DoJavaScript(jsx)
    print(f"PS 返回: {result}")
    print(f"产物目录: {outdir}")


if __name__ == "__main__":
    main()
