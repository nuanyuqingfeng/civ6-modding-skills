#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_leader_png.py — Civ6 2D 领袖立绘 PNG -> TEXTURE/OPACITY 1024x1024 素材生成器

用法:
  # 只生成 PNG，默认输出到 D:\\desktop
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA_QYQXP

  # 指定输出目录
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA_QYQXP \\
      --output-dir D:\\some\\dir

  # 指定自定义正方形裁剪框（原图坐标 left,top,side）
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA_QYQXP \\
      --crop 100,50,800

  # 一步到位：输出到项目 Textures，同步 .tex，并尝试生成 DDS
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA_QYQXP \\
      --project <Civ6工程根目录> --tex-dds

说明:
  - 源图建议为近似 1:1、透明背景的 PNG。
  - TEXTURE：居中裁剪为正方形后缩放到 1024x1024，保留颜色与透明背景。
  - OPACITY：以 Photoshop Ctrl+左键点击图层缩略图的选区语义为准，
    非全透明像素（alpha > 0）填充纯白 RGB(255,255,255)，
    全透明像素填充纯黑 RGB(0,0,0)，输出不透明黑白 PNG。
  - 不指定 --tex-dds 时只生成 PNG，不生成/修改 .tex。
"""
import argparse
import codecs
import locale
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"
TEX_TEMPLATE_TEXTURE = TEMPLATE_DIR / "LEADER_NAME_QYQXP_TEXTURE.tex"
TEX_TEMPLATE_OPACITY = TEMPLATE_DIR / "LEADER_NAME_QYQXP_OPACITY.tex"


def _ansi_codec_name():
    """系统 ANSI 代码页（.tex 读出/写入编码，AssetEditor 使用 Encoding.Default）。"""
    if os.name == "nt":
        try:
            import ctypes
            acp = ctypes.windll.kernel32.GetACP()
        except Exception:
            acp = 0
        if acp:
            try:
                return codecs.lookup("cp%d" % acp).name
            except LookupError:
                if acp == 65001:
                    return "utf-8"
    try:
        return (locale.getpreferredencoding(False) or "utf-8").lower()
    except Exception:
        return "utf-8"


def _xml_encoding_name(codec_name):
    common = {
        "utf-8": "UTF-8",
        "gbk": "GBK",
        "gb2312": "GBK",
        "cp936": "GBK",
        "shift_jis": "Shift_JIS",
        "cp932": "Shift_JIS",
        "cp950": "Big5",
        "big5": "Big5",
        "cp949": "windows-949",
    }
    name = common.get(codec_name)
    if name:
        return name
    if codec_name.startswith("cp125"):
        return "windows-" + codec_name[2:]
    return codec_name.upper()


def _write_tex(path, content):
    """按系统 ANSI 代码页写出 .tex；装不下的字符用 XML 字符引用转义。"""
    enc = _ansi_codec_name()
    xml_enc = _xml_encoding_name(enc)
    content = content.replace(
        '<?xml version="1.0" encoding="UTF-8" ?>',
        '<?xml version="1.0" encoding="%s" ?>' % xml_enc,
    )
    with open(path, "w", encoding=enc, errors="xmlcharrefreplace", newline="\n") as f:
        f.write(content)
    return enc


def render_tex(template_path, stem, source_png):
    """从模板渲染 .tex：替换变量、SourceFilePath，并保留模板的 classname/格式设置。"""
    with open(template_path, encoding="utf-8") as f:
        text = f.read()
    text = text.replace("{TEX}", stem).replace("{OPAC}", stem)
    src = source_png.replace("\\", "/")
    text = re.sub(
        r'(<m_SourceFilePath text=")[^"]*(")',
        lambda m: m.group(1) + src + m.group(2),
        text,
    )
    return text


def find_texconv():
    """只做简单固定查找：PATH 或 WinGet Links 固定路径，不递归扩大搜索。"""
    p = shutil.which("texconv")
    if p:
        return p
    local = os.environ.get("LOCALAPPDATA", "")
    links = os.path.join(local, "Microsoft", "WinGet", "Links", "texconv.exe")
    if os.path.isfile(links):
        return links
    return None


def find_leader_type(project, leader_name):
    """在项目 SQL/XML 里按名字查找 LeaderType（用于不手动传 --leader-type 时）。"""
    key = leader_name.strip().upper()
    for root, _, files in os.walk(project):
        for f in files:
            if not f.endswith((".sql", ".xml")):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8-sig", errors="ignore") as fh:
                    text = fh.read()
            except Exception:
                continue
            for m in re.finditer(r"\b(LEADER_[A-Z0-9_]+)\b", text):
                lt = m.group(1).upper()
                if key in lt:
                    return lt
    return None


def run_texconv(texconv, src, out_dir, fmt):
    # -m 1 单 mip；texconv 缺省/0 = 完整 mip 链，与 .tex bUseMips=false 约定冲突
    cmd = [texconv, "-y", "-f", fmt, "-m", "1", "-o", out_dir, src]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print("  警告: texconv 转换失败: %s" % (proc.stderr.strip() or proc.stdout.strip()))
        return False
    dds = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + ".dds")
    if os.path.isfile(dds):
        print("  生成 %s" % dds)
        return True
    print("  警告: 未找到 texconv 输出 DDS: %s" % dds)
    return False


def crop_square(img, crop=None):
    """默认按短边居中裁剪；也可传入 (left, top, side) 自定义正方形裁剪。"""
    w, h = img.size
    if crop:
        left, top, side = crop
        if side <= 0 or left < 0 or top < 0 or left + side > w or top + side > h:
            raise SystemExit(
                "错误: --crop 超出原图范围 (left=%d, top=%d, side=%d, 原图=%dx%d)"
                % (left, top, side, w, h)
            )
        return img.crop((left, top, left + side, top + side))
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def build_texture_opacity(img, size, alpha_threshold, crop=None):
    """输入 RGBA 图，返回 (texture_img, opacity_img)，均为 size×size。"""
    img = crop_square(img, crop)
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    texture = img.resize((size, size), resample)

    alpha = texture.getchannel("A")
    mask = alpha.point(lambda a: 255 if a > alpha_threshold else 0)
    opacity = mask.convert("RGB")
    return texture, opacity


def main():
    ap = argparse.ArgumentParser(description="Civ6 2D 领袖立绘 PNG -> TEXTURE/OPACITY 生成器")
    ap.add_argument("--input", required=True, help="源 PNG 路径（近似 1:1，透明背景）")
    ap.add_argument("--leader-type", default=None,
                    help="项目内精确 LeaderType，例如 LEADER_CANTARELLA_QYQXP；也可用 --project+--leader-name 自动查找")
    ap.add_argument("--leader-name", default=None,
                    help="领袖名（英文），配合 --project 自动查找 LeaderType，例如 Cantarella")
    ap.add_argument("--output-dir", default=None,
                    help="输出目录；不指定时默认 D:\\desktop；--tex-dds 时默认 <project>\\Textures")
    ap.add_argument("--project", default=None, help="Civ6 工程根目录（--tex-dds 时必填）")
    ap.add_argument("--texconv-path", default=None,
                    help="texconv 完整路径；不提供时仅做 PATH / 固定目录简单查找")
    ap.add_argument("--tex-dds", action="store_true",
                    help="一步到位：输出到项目 Textures，同步 .tex，并尝试生成 DDS")
    ap.add_argument("--size", type=int, default=1024, help="输出尺寸，默认 1024")
    ap.add_argument("--crop", default=None,
                    help="自定义正方形裁剪: left,top,side（原图坐标）；缺省按短边居中")
    ap.add_argument("--alpha-threshold", type=int, default=0,
                    help="OPACITY 主体判定阈值：alpha 大于该值算主体，默认 0（PS Ctrl+点击语义）")
    args = ap.parse_args()

    if Image is None:
        print("错误: 当前环境缺少 Pillow（PIL）。")
        print("退化选项：")
        print("  1) 请提供本机可用的 Python/Pillow 环境或图片工具路径；")
        print("  2) 允许调用其他有图片处理能力的模型/工具来读图并自行裁剪；")
        print("  3) 本次跳过自动处理，由你稍后自行添加素材。")
        sys.exit(2)

    if not os.path.isfile(args.input):
        raise SystemExit("错误: 输入 PNG 不存在: %s" % args.input)

    leader_type = None
    if args.leader_type:
        leader_type = args.leader_type.strip().upper()
    elif args.project and args.leader_name:
        project = os.path.abspath(args.project)
        if not os.path.isdir(project):
            raise SystemExit("错误: 工程目录不存在: %s" % project)
        leader_type = find_leader_type(project, args.leader_name)
        if not leader_type:
            raise SystemExit("错误: 在项目内未找到与 '%s' 匹配的 LeaderType，请手动传入 --leader-type" % args.leader_name)
        print("从项目查得 LeaderType: %s" % leader_type)
    else:
        raise SystemExit("错误: 请提供 --leader-type，或同时提供 --project 和 --leader-name 自动查找")

    if not leader_type.startswith("LEADER_"):
        print("警告: LeaderType 通常以 LEADER_ 开头，当前值: %s" % leader_type)

    if args.tex_dds:
        if not args.project:
            raise SystemExit("错误: --tex-dds 需要同时提供 --project 工程根目录")
        project = os.path.abspath(args.project)
        if not os.path.isdir(project):
            raise SystemExit("错误: 工程目录不存在: %s" % project)
        output_dir = os.path.join(project, "Textures")
    else:
        output_dir = args.output_dir or r"D:\desktop"

    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    crop_box = None
    if args.crop:
        parts = [int(x.strip()) for x in args.crop.split(",")]
        if len(parts) != 3:
            raise SystemExit("错误: --crop 格式应为 left,top,side，例如 100,50,800")
        crop_box = tuple(parts)

    texture_stem = "%s_TEXTURE" % leader_type
    opacity_stem = "%s_OPACITY" % leader_type
    texture_png = os.path.join(output_dir, texture_stem + ".png")
    opacity_png = os.path.join(output_dir, opacity_stem + ".png")

    print("LeaderType: %s" % leader_type)
    print("输出目录: %s" % output_dir)

    img = Image.open(args.input).convert("RGBA")
    texture, opacity = build_texture_opacity(img, args.size, args.alpha_threshold, crop_box)

    texture.save(texture_png, "PNG")
    opacity.save(opacity_png, "PNG")
    print("  生成 %s" % texture_png)
    print("  生成 %s" % opacity_png)

    # 校验尺寸
    t_check = Image.open(texture_png)
    o_check = Image.open(opacity_png)
    if t_check.size != (args.size, args.size) or o_check.size != (args.size, args.size):
        raise SystemExit("错误: 生成图片尺寸不是 %dx%d" % (args.size, args.size))

    if not args.tex_dds:
        print("\n完成。已生成 PNG；未指定 --tex-dds，因此不修改任何 .tex。")
        return

    # ---- 一步到位：.tex 同步 ----
    print("\n[--tex-dds] 同步 .tex...")
    tex_texture = render_tex(TEX_TEMPLATE_TEXTURE, texture_stem, texture_png)
    tex_opacity = render_tex(TEX_TEMPLATE_OPACITY, opacity_stem, opacity_png)
    tex_texture_path = os.path.join(output_dir, texture_stem + ".tex")
    tex_opacity_path = os.path.join(output_dir, opacity_stem + ".tex")
    enc1 = _write_tex(tex_texture_path, tex_texture)
    enc2 = _write_tex(tex_opacity_path, tex_opacity)
    print("  生成 %s (编码 %s)" % (tex_texture_path, enc1))
    print("  生成 %s (编码 %s)" % (tex_opacity_path, enc2))

    # ---- 一步到位：DDS 转换（texconv） ----
    print("\n[--tex-dds] 转换 DDS...")
    texconv = None
    if args.texconv_path:
        if os.path.isfile(args.texconv_path):
            texconv = args.texconv_path
        else:
            print("警告: 指定的 texconv 路径不存在: %s" % args.texconv_path)
    if not texconv:
        texconv = find_texconv()
    if not texconv:
        print("警告: 未找到 texconv（仅做 PATH / 固定目录简单查找，不自动安装、不扩大搜索）。")
        print("退化选项：")
        print("  1) 请提供 texconv 所在目录或完整路径（使用 --texconv-path）；")
        print("  2) 允许调用其他有图片处理能力的模型/工具；")
        print("  3) 本次只生成 PNG 和 .tex，DDS 稍后由 art-pipeline 补充。")
    else:
        run_texconv(texconv, texture_png, output_dir, "R8G8B8A8_UNORM")
        run_texconv(texconv, opacity_png, output_dir, "R8_UNORM")

    print("\n完成。一步到位输出目录: %s" % output_dir)


if __name__ == "__main__":
    main()