"""ps_place_resource.py — 资源图标 PS 自动化引擎（首选流程）

用法：
  python ps_place_resource.py --input <图案.png> --kind bonus|luxury --outdir <目录> [--fow] [--psd <模板.psd>]

先用 build_resource_icon.place_pattern 按落位框完成构图（与无 PS 引擎同一套构图铁律），
再交本机 Photoshop 打开内置模板，把已构图图案贴入 Pattern 组、按类别选底盘，
原样导出 256×256 RGBA 单元格。Photoshop 只承担图层合成的原生光栅化。
退出码: 0 成功; 2 输入/参数错误; 4 Photoshop 自动化通道不可用——缺 pywin32 模块，
或 Photoshop 未安装、未注册 Automation 接口，两种情况分别给出修复指引，
由 AI 询问用户改走 build_resource_icon.py 无 PS 引擎还是补齐 PS 环境后重跑。

构图铁律与无 PS 引擎共用（build_resource_icon.place_pattern）：等比缩放后居中装入落位框，
重采样走预乘 alpha 的 LANCZOS，最后在输出空间沿主体（alpha ≥ 64）的全部边缘向外描等宽黑边；禁止非等比拉伸。
依赖: pywin32（win32com）、psd-tools、Pillow、numpy。
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_resource_icon as b  # noqa: E402

from psd_tools import PSDImage  # noqa: E402

JSX = Path(__file__).resolve().parent / "ps_place_resource.jsx"
DEFAULT_PSD = Path(__file__).resolve().parent.parent / "templates" / "resource_icon" / "Resource_Icon_Photoshop_CC.psd"
PARAMS = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))) / "civ6_resource_ps_params.txt"
PLATE_LAYER = {("bonus", False): "bonus", ("luxury", False): "luxury",
               ("bonus", True): "bonus FOW", ("luxury", True): "luxury FOW"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="源图案 PNG")
    ap.add_argument("--kind", required=True, choices=b.KINDS, help="资源类别：bonus / luxury")
    ap.add_argument("--outdir", required=True, help="成品输出目录")
    ap.add_argument("--psd", default=str(DEFAULT_PSD), help="资源图标模板 PSD（默认内置）")
    ap.add_argument("--box", help="落位框 WxH@X,Y（默认取该类底盘 alpha 包围盒）")
    ap.add_argument("--threshold", type=int, default=b.DEFAULT_THRESHOLD, help="源图内容包围盒的 alpha 阈值（默认 8）")
    ap.add_argument("--fow", action="store_true", help="改用迷雾（FOW）底盘")
    ap.add_argument("--no-stroke", action="store_true", help="不加图案黑边（素材自身已带黑边时用）")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    if not src.is_file():
        print("错误: 找不到素材 %s" % src)
        sys.exit(2)
    psd = Path(args.psd).resolve()
    if not psd.is_file():
        print("错误: 找不到 PSD %s" % psd)
        sys.exit(2)
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    layer_name = PLATE_LAYER[(args.kind, args.fow)]
    box = b.parse_box(args.box) if args.box else b.default_box(args.kind, args.fow)
    pattern, placed, k = b.place_pattern(
        np.asarray(Image.open(src).convert("RGBA"), dtype=np.uint8), box, args.threshold,
        stroke=not args.no_stroke)
    material = PARAMS.parent / ("civ6_resource_ps_import_%s_%s%s.png"
                                % (src.stem, args.kind, "_fow" if args.fow else ""))
    Image.fromarray(pattern).save(material)
    print("素材: %s → 落位框 %s 装入 %dx%d k=%.3f 置入 PS: %s"
          % (src.name, b.fmt_box(box), placed[0], placed[1], k, material.name))

    PARAMS.write_text(
        "psd=%s\nmaterial=%s\noutdir=%s\nplate=%s\ntag=%s\n"
        % (psd.as_posix(), material.as_posix(), outdir.as_posix(), layer_name,
           "%s%s" % (args.kind, "_Fow" if args.fow else "")),
        encoding="utf-8")

    jsx = JSX.read_text(encoding="utf-8")

    missing = [m for m in ("win32com", "pythoncom") if importlib.util.find_spec(m) is None]
    if missing:
        print("错误: 当前 Python 解释器缺少 pywin32 模块 %s，Photoshop 自动化通道不可用"
              % " / ".join(missing))
        print("修复: \"%s\" -m pip install pywin32" % sys.executable)
        print("需询问用户：装 pywin32 后重跑 PS 引擎，或改走 build_resource_icon.py 无 PS 引擎")
        sys.exit(4)

    import pythoncom
    from win32com.client import Dispatch
    pythoncom.CoInitialize()
    try:
        app = Dispatch("Photoshop.Application")
    except Exception as e:  # ProgID 未注册，或 Photoshop 未安装
        print("错误: Photoshop 自动化接口不可用（%s: %s）" % (e.__class__.__name__, e))
        print("判定: pywin32 已就位，缺口在 Photoshop 一侧——未安装，或未注册 "
              "Photoshop.Application ProgID")
        print("需询问用户：安装 Photoshop 后重跑 PS 引擎，或改走 build_resource_icon.py 无 PS 引擎")
        sys.exit(4)
    result = app.DoJavaScript(jsx)
    print("PS 返回: %s" % result)
    print("产物目录: %s" % outdir)


if __name__ == "__main__":
    main()
