#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_leader_png.py — Civ6 2D 领袖立绘 PNG -> TEXTURE/OPACITY 1024x1024 素材生成器

用法:
  # 只生成 PNG，默认输出到 D:\\desktop
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA

  # 指定输出目录
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA \\
      --output-dir D:\\some\\dir

  # 指定自定义正方形裁剪框（原图坐标 left,top,side）
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA \\
      --crop 100,50,800

  # 一步到位：.tex 与 .dds 写入项目 Textures，PNG 仍留在输出目录（默认 D:\\desktop）
  python process_leader_png.py --input <源PNG> --leader-type LEADER_CANTARELLA \\
      --project <Civ6工程根目录> --tex-dds

说明:
  - 源图建议为近似 1:1、透明背景的 PNG。
  - TEXTURE：居中裁剪为正方形后缩放到 1024x1024，保留颜色与透明背景。
  - OPACITY：取源图 alpha 通道并缩放到同一尺寸，保留边缘抗锯齿；
    背景段（alpha <= --alpha-floor）统一写成 --alpha-base 底值（默认 4），
    避免 8 位量化把低值尾部切成同心环带；--alpha-base 0 即纯透明背景。
  - PNG 一律写到 --output-dir（默认 D:\\desktop），从不写进工程。工程 Textures/ 是
    AssetEditor 的 pantry，只允许 .tex 与 .dds；PNG 留在工程外充当 .tex 的源图。
  - 不指定 --tex-dds 时只生成 PNG，不生成/修改 .tex 与 .dds。
"""
import argparse
import codecs
import locale
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _projwrite import write_project_file, finish  # noqa: E402

# 头部校验与修复复用 civ6-modding 的 DDS 单一真源。
for _cand in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "civ6-modding", "art"),
              os.path.join(os.path.expanduser("~"), ".agents", "skills", "civ6-modding", "art")):
    if os.path.isfile(os.path.join(_cand, "dds_io.py")):
        sys.path.insert(0, os.path.abspath(_cand))
        break
from dds_io import ensure_official_header  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"
TEX_TEMPLATE_TEXTURE = TEMPLATE_DIR / "LEADER_NAME_TEXTURE.tex"
TEX_TEMPLATE_OPACITY = TEMPLATE_DIR / "LEADER_NAME_OPACITY.tex"


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


def _write_tex(path, content, project):
    """按系统 ANSI 代码页编码 .tex 后交给工程写入守卫；装不下的字符用 XML 字符引用转义。"""
    enc = _ansi_codec_name()
    xml_enc = _xml_encoding_name(enc)
    content = content.replace(
        '<?xml version="1.0" encoding="UTF-8" ?>',
        '<?xml version="1.0" encoding="%s" ?>' % xml_enc,
    )
    write_project_file(path, content.encode(enc, errors="xmlcharrefreplace"), project)
    return enc


def render_tex(template_path, stem, source_png):
    """从模板渲染 .tex：替换变量、SourceFilePath，并保留模板的 classname/格式设置。"""
    with open(template_path, encoding="utf-8") as f:
        text = f.read()
    text = text.replace("{TEX}", stem).replace("{OPAC}", stem)
    # m_SourceFilePath 统一用反斜杠（AGENTS.md 约定 D:\\desktop\\<stem>.png）
    src = source_png.replace("/", "\\")
    text = re.sub(
        r'(<m_SourceFilePath text=")[^"]*(")',
        lambda m: m.group(1) + src + m.group(2),
        text,
    )
    return text


def find_texconv():
    """定位 texconv。

    复用 `civ6-modding/art/_texconv.py` 的单一真源，但**显式取 recursive=False**：
    本脚本面向用户交互使用，遵循 `reference/leader-2d.md` 的
    「仅简单查找，不自动安装、不扩大搜索」——只查 PATH 与 WinGet Links 固定位，
    不递归扫 Packages（那是无人值守管线才需要的兜底）。
    """
    import sys as _sys
    _here = os.path.dirname(os.path.abspath(__file__))
    for _c in (os.path.join(_here, "..", "..", "civ6-modding", "art"),
               os.path.join(os.path.expanduser("~"), ".agents", "skills",
                            "civ6-modding", "art")):
        if os.path.isfile(os.path.join(_c, "_texconv.py")):
            _sys.path.insert(0, os.path.abspath(_c))
            break
    try:
        from _texconv import find_texconv as _find
    except ImportError:
        # 退化：与 _texconv 的 non-recursive 行为一致
        p = shutil.which("texconv")
        if p:
            return p
        links = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                             "Microsoft", "WinGet", "Links", "texconv.exe")
        return links if os.path.isfile(links) else None
    return _find(recursive=False)


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
    """texconv 转出一份 DDS 到 out_dir（中间产物），返回路径。失败就地终止。"""
    # -m 0 = 完整 mip 链，与 .tex 的 bUseMips=true / bCompleteMipChain=true 对应。
    # 写单 mip 会让远处采样失真。
    cmd = [texconv, "-y", "-f", fmt, "-m", "0", "-o", out_dir, src]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit("错误: texconv 转换失败（%s）: %s"
                         % (os.path.basename(src),
                            err or proc.stdout.decode("utf-8", errors="replace").strip()))
    dds = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + ".dds")
    if not os.path.isfile(dds):
        raise SystemExit("错误: texconv 未产出 DDS: %s" % dds)
    return dds


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


def build_texture_opacity(img, size, alpha_threshold, alpha_floor=8, alpha_base=4, crop=None):
    """输入 RGBA 图，返回 (texture_img, opacity_img)，均为 size×size。

    OPACITY 取源图 alpha 缩放后的连续值，保留边缘抗锯齿。
    背景段（alpha <= alpha_floor）统一写成同一个底值 alpha_base：径向羽化的
    低值尾部一旦保留连续衰减，8 位量化就会把它切成同心环带（实测 1~3 三级
    挤进 55.7% 的像素），外交场景里表现为一圈一圈的台阶。压成单一底值后
    背景完全平坦，只剩人物边缘的过渡。alpha_base=0 供硬边素材使用。
    """
    img = crop_square(img, crop)
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    texture = img.resize((size, size), resample)

    alpha = texture.getchannel("A")
    if alpha_floor > 0:
        alpha = alpha.point(lambda a: alpha_base if a <= alpha_floor else a)
    opacity = alpha.convert("RGB")
    return texture, opacity


def main():
    ap = argparse.ArgumentParser(description="Civ6 2D 领袖立绘 PNG -> TEXTURE/OPACITY 生成器")
    ap.add_argument("--input", required=True, help="源 PNG 路径（近似 1:1，透明背景）")
    ap.add_argument("--leader-type", default=None,
                    help="项目内精确 LeaderType，例如 LEADER_CANTARELLA；也可用 --project+--leader-name 自动查找")
    ap.add_argument("--leader-name", default=None,
                    help="领袖名（英文），配合 --project 自动查找 LeaderType，例如 Cantarella")
    ap.add_argument("--output-dir", default=None,
                    help="PNG 输出目录，必须在工程外；不指定时默认 D:\\desktop")
    ap.add_argument("--project", default=None, help="Civ6 工程根目录（--tex-dds 时必填）")
    ap.add_argument("--texconv-path", default=None,
                    help="texconv 完整路径；不提供时仅做 PATH / 固定目录简单查找")
    ap.add_argument("--tex-dds", action="store_true",
                    help="一步到位：.tex 与 .dds 写入项目 Textures，PNG 留在 --output-dir")
    ap.add_argument("--size", type=int, default=1024, help="输出尺寸，默认 1024")
    ap.add_argument("--crop", default=None,
                    help="自定义正方形裁剪: left,top,side（原图坐标）；缺省按短边居中")
    ap.add_argument("--alpha-threshold", type=int, default=0,
                    help="OPACITY 主体判定阈值：alpha 大于该值算主体，默认 0（PS Ctrl+点击语义）")
    ap.add_argument("--alpha-floor", type=int, default=8,
                    help="OPACITY 背景阈值：alpha 小于等于该值的像素写成 --alpha-base，默认 8")
    ap.add_argument("--alpha-base", type=int, default=4,
                    help="OPACITY 背景底值：背景段统一写该值，默认 4；0 表示纯透明背景")
    args = ap.parse_args()

    if Image is None:
        raise SystemExit("错误: 当前环境缺少 Pillow（PIL），无法生成 TEXTURE/OPACITY。")

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

    project = os.path.abspath(args.project) if args.project else None
    if project and not os.path.isdir(project):
        raise SystemExit("错误: 工程目录不存在: %s" % project)
    if args.tex_dds and not project:
        raise SystemExit("错误: --tex-dds 需要同时提供 --project 工程根目录")
    tex_dir = os.path.join(project, "Textures") if project else None

    output_dir = os.path.abspath(args.output_dir or r"D:\desktop")
    os.makedirs(output_dir, exist_ok=True)
    # PNG 是 .tex 的源图，必须留在工程外：工程目录本身是 AssetEditor 的 pantry，
    # cooker 递归扫描整棵目录树，只认 .tex 与 .dds；PNG 一旦落进去会被当成贴图实体登记。
    if project and (os.path.normcase(output_dir) == os.path.normcase(tex_dir)
                    or os.path.normcase(output_dir).startswith(os.path.normcase(project) + os.sep)):
        raise SystemExit("错误: --output-dir 不能指向工程目录内（含 Textures/）：%s" % output_dir)

    # texconv 的中间产物落在系统临时目录（%TEMP%），头部修好后才写进工程。
    staging = tempfile.mkdtemp(prefix="civ6_leader_dds_")

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
    texture, opacity = build_texture_opacity(img, args.size, args.alpha_threshold, args.alpha_floor,
                                             args.alpha_base, crop_box)

    artifacts = [(texture_png, texture), (opacity_png, opacity)]
    for path, im in artifacts:
        im.save(path, "PNG")
    for path, _im in artifacts:
        print("  生成 %s" % path)

    # 校验尺寸
    t_check = Image.open(texture_png)
    o_check = Image.open(opacity_png)
    if t_check.size != (args.size, args.size) or o_check.size != (args.size, args.size):
        raise SystemExit("错误: 生成图片尺寸不是 %dx%d" % (args.size, args.size))

    if not args.tex_dds:
        print("\n完成。已生成 PNG；未指定 --tex-dds，因此不修改任何 .tex。")
        return

    # ---- 一步到位：DDS 转换（texconv）→ 头部校验修复 → 写进工程 ----
    # 中间产物落在系统临时目录，头部修好后才进 pantry：中断不会在 Textures/ 留半截文件。
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
        raise SystemExit("错误: 找不到 texconv（已查 TEXCONV / 随包内置 / PATH / WinGet Links）。"
                         "用 --texconv-path 指定完整路径。")
    for src, fmt in ((texture_png, "R8G8B8A8_UNORM"), (opacity_png, "R8_UNORM")):
        run_texconv(texconv, src, staging, fmt)

    # texconv 直出的头部带 DDSD_PITCH、保留区无 FTXT、单通道写成 DDPF_LUMINANCE，
    # 与官方 cook 产物不一致（外交场景纸片人不显示、散布零星色块）。按官方口径重写。
    print("\n[--tex-dds] 校验并修复 DDS 头部...")
    for src in (texture_png, opacity_png):
        dds = os.path.join(staging, os.path.splitext(os.path.basename(src))[0] + ".dds")
        changed, issues = ensure_official_header(dds)
        if changed:
            print("  修复 %s：%s" % (os.path.basename(dds), "；".join(issues)))
        else:
            print("  合规 %s" % os.path.basename(dds))

    # ---- 一步到位：.tex 与 .dds 进工程 ----
    print("\n[--tex-dds] 同步 .tex 与 .dds...")
    tex_texture = render_tex(TEX_TEMPLATE_TEXTURE, texture_stem, texture_png)
    tex_opacity = render_tex(TEX_TEMPLATE_OPACITY, opacity_stem, opacity_png)
    tex_texture_path = os.path.join(tex_dir, texture_stem + ".tex")
    tex_opacity_path = os.path.join(tex_dir, opacity_stem + ".tex")
    enc1 = _write_tex(tex_texture_path, tex_texture, project)
    enc2 = _write_tex(tex_opacity_path, tex_opacity, project)
    print("  生成 %s (编码 %s)" % (tex_texture_path, enc1))
    print("  生成 %s (编码 %s)" % (tex_opacity_path, enc2))

    for src in (texture_png, opacity_png):
        dds = os.path.join(staging, os.path.splitext(os.path.basename(src))[0] + ".dds")
        with open(dds, "rb") as fh:
            write_project_file(os.path.join(tex_dir, os.path.basename(dds)), fh.read(), project)
        print("  生成 %s" % os.path.join(tex_dir, os.path.basename(dds)))

    shutil.rmtree(staging)
    print("\n完成。PNG: %s；.tex/.dds: %s" % (output_dir, tex_dir))
    return finish()


if __name__ == "__main__":
    sys.exit(main())