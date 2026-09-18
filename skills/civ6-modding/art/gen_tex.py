#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 {MOD_NAME}/Textures/ 下的每个 dds 文件生成同名 .tex 文件。

用法：python gen_tex.py [textures_dir] [assets_dir] [asset_map_json]
  不传参则使用脚本内默认路径。
零第三方依赖（纯标准库）：直接解析 DDS 头获取分辨率 / mip 层数 / 像素格式，
不需要 texdiag。
.assets 源文件使用「中文名-角色」友好名，通过 scripts/asset_map.json
（技术名 -> 友好名）解析；无映射时回退同名（兼容旧项目）。

编码（重要）：.tex 按【系统 ANSI 代码页】写出，而不是 UTF-8。m_SourceFilePath
里含 .assets 中文路径，AssetEditor（WinForm/.NET）读取 .tex 用 Encoding.Default
（= 系统 ANSI 代码页，中文系统即 GBK/cp936）。若写成 UTF-8，GBK 解读会乱码并
导致 AssetEditor 崩溃。系统 ANSI 代码页用 GetACP() 取（勿用
locale.getpreferredencoding——Python UTF-8 模式下它会返回 utf-8，与 AssetEditor
实际读取编码不一致）。ANSI 代码页装不下的字符（如西文系统遇中文路径）用 XML
字符引用转义，保证文件始终是合法 XML、不会因非法字节而崩溃。
"""

import codecs
import json
import locale
import os
import re
import struct
import sys
import pathlib

# 强制 UTF-8 输出：Windows 控制台默认按 GBK 写、AI 管道按 UTF-8 读，中文会乱码。
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Can be overridden by CLI args: python gen_tex.py [textures_dir] [assets_dir]
# Default: auto-detect project root (parent of scripts/ directory), find MOD_NAME from .civ6sln
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent

def _detect_civ_name(root):
    """Find MOD_NAME by looking for .civ6sln or .civ6proj"""
    for f in root.iterdir():
        if f.suffix == '.civ6sln':
            return f.stem
    for f in root.rglob('*.civ6proj'):
        return f.parent.name
    return None

_civ_name = _detect_civ_name(_PROJECT_ROOT)
TEXTURES_DIR = sys.argv[1] if len(sys.argv) > 1 else str(_PROJECT_ROOT / (_civ_name or "MOD_NAME") / "Textures")
ASSETS_DIR = sys.argv[2] if len(sys.argv) > 2 else str(_PROJECT_ROOT / ".assets")
ASSET_MAP_PATH = sys.argv[3] if len(sys.argv) > 3 else str(_PROJECT_ROOT / "scripts" / "asset_map.json")

# 技术名 basename -> .assets 友好名 basename（中文）；读不到映射时回退原名（兼容旧项目）
_ASSET_MAP = {}
try:
    with open(ASSET_MAP_PATH, encoding="utf-8") as f:
        _ASSET_MAP = json.load(f)
except Exception:
    _ASSET_MAP = {}


def _ansi_codec_name():
    """系统 ANSI 代码页对应的 Python 编解码名（.tex 的写出编码）。

    AssetEditor 是 WinForm/.NET，读取 .tex 用 Encoding.Default = 系统 ANSI 代码页
    （中文系统 cp936/GBK、日文系统 cp932、西文系统 cp1252……系统开启 UTF-8 时 65001）。
    用 GetACP() 取真实代码页，勿用 locale.getpreferredencoding——Python UTF-8 模式
    （PEP 686，3.15 起默认开启）下它返回 utf-8，会与 AssetEditor 实际读取编码不一致。"""
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
    # 非 Windows 或拿不到 ACP：回退 locale（多数情况下等价于 ANSI 代码页）
    try:
        enc = locale.getpreferredencoding(False)
    except Exception:
        enc = "utf-8"
    return (enc or "utf-8").lower()


def _xml_encoding_name(codec_name):
    """把 Python 编解码名映射为 XML 声明可用的名称（IANA 字符集名，ASCII 安全）。"""
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
        "euc_kr": "EUC-KR",
    }
    name = common.get(codec_name)
    if name:
        return name
    if codec_name.startswith("cp125"):
        return "windows-" + codec_name[2:]
    return codec_name.upper()


TEX_ENCODING = _ansi_codec_name()          # .tex 写出编码（系统 ANSI 代码页）
XML_ENCODING = _xml_encoding_name(TEX_ENCODING)  # XML 声明里的编码名，与写出编码一致

TEX_TEMPLATE = '''<?xml version="1.0" encoding="{xml_encoding}" ?>
<AssetObjects..TextureInstance>
\t<m_ExportSettings>
\t\t<ePixelformat>{pixelformat}</ePixelformat>
\t\t<eFilterType>FT_BOX</eFilterType>
\t\t<bUseMips>{busemips}</bUseMips>
\t\t<iNumManualMips>0</iNumManualMips>
\t\t<bCompleteMipChain>{completemipchain}</bCompleteMipChain>
\t\t<fValueClampMin>0.000000</fValueClampMin>
\t\t<fValueClampMax>1.000000</fValueClampMax>
\t\t<fSupportScale>1.000000</fSupportScale>
\t\t<fGammaIn>2.200000</fGammaIn>
\t\t<fGammaOut>2.200000</fGammaOut>
\t\t<iSlabWidth>0</iSlabWidth>
\t\t<iSlabHeight>0</iSlabHeight>
\t\t<iColorKeyX>64</iColorKeyX>
\t\t<iColorKeyY>64</iColorKeyY>
\t\t<iColorKeyZ>64</iColorKeyZ>
\t\t<eExportMode>TEXTURE_2D</eExportMode>
\t\t<bSampleFromTopLayer>false</bSampleFromTopLayer>
\t</m_ExportSettings>
\t<m_CookParams>
\t\t<m_Values/>
\t</m_CookParams>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_Height>{height}</m_Height>
\t<m_Width>{width}</m_Width>
\t<m_Depth>1</m_Depth>
\t<m_NumMipMaps>{nummipmaps}</m_NumMipMaps>
\t<m_SourceFilePath text="{sourcefilepath}"/>
\t<m_SourceObjectName text=""/>
\t<m_ImportedTime>0</m_ImportedTime>
\t<m_ExportedTime>2573668599</m_ExportedTime>
\t<m_ClassName text="{classname}"/>
\t<m_DataFiles>
\t\t<Element>
\t\t\t<m_ID text="DDS"/>
\t\t\t<m_RelativePath text="{ddsname}"/>
\t\t</Element>
\t</m_DataFiles>
\t<m_Name text="{name}"/>
\t<m_Description text=""/>
\t<m_Tags>
{tags}
\t</m_Tags>
</AssetObjects..TextureInstance>
'''


# ---- DDS 头解析（替代 texdiag，纯标准库） ----
# DDS_HEADER 布局（微软 DDS 规范，全部小端 uint32；文件偏移 = 头偏移 + 4 字节魔数）：
#   12    dwHeight
#   16    dwWidth
#   28    dwMipMapCount
#   76    ddspf（DDS_PIXELFORMAT，32 字节）：
#   80      dwFlags（DDPF_*）
#   84      dwFourCC（"DX10" 或压缩格式，如 "DXT5"）
#   88      dwRGBBitCount
#   92..   dwRBitMask / dwGBitMask / dwBBitMask / dwABitMask
#   128   （可选）DDS_HEADER_DXT10.dxgiFormat（头后 4 字节）
DDPF_ALPHAPIXELS = 0x1
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40

# DXGI 格式 ID -> PF_ 枚举名（覆盖本管线可能出现的常见格式）
DXGI_TO_NAME = {
    28: "R8G8B8A8_UNORM",
    87: "B8G8R8A8_UNORM",
    11: "R16G16B16A16_UNORM",
    71: "BC1_UNORM",
    74: "BC2_UNORM",
    77: "BC3_UNORM",
    98: "BC7_UNORM",
}

# 压缩 fourCC -> PF_ 枚举名
FOURCC_TO_NAME = {
    b"DXT1": "BC1_UNORM", b"DXT3": "BC2_UNORM", b"DXT5": "BC3_UNORM",
    b"BC1": "BC1_UNORM", b"BC2": "BC2_UNORM", b"BC3": "BC3_UNORM",
    b"BC4": "BC4_UNORM", b"BC5": "BC5_UNORM", b"BC6H": "BC6H_UF16",
    b"BC7": "BC7_UNORM",
}


def parse_dds_info(dds_path):
    """读取 DDS 文件头，返回 {width, height, mip_levels, format}。
    format 为 PF_ 枚举名（如 R8G8B8A8_UNORM），由 DDS 像素格式推导；
    无法识别时抛 ValueError（附明确提示），不会静默写出错误的 .tex。"""
    with open(dds_path, "rb") as f:
        head = f.read(132)  # 4 魔数 + 124 DDS_HEADER + 可选 DX10 扩展头首字段
    if len(head) < 132 or head[0:4] != b"DDS ":
        raise ValueError(f"{dds_path} 不是有效的 DDS 文件（缺 DDS 魔数）")
    width = struct.unpack_from("<I", head, 16)[0]
    height = struct.unpack_from("<I", head, 12)[0]
    mips = struct.unpack_from("<I", head, 28)[0]
    flags = struct.unpack_from("<I", head, 80)[0]
    fourcc = head[84:88]
    bitcount = struct.unpack_from("<I", head, 88)[0]
    masks = struct.unpack_from("<IIII", head, 92)
    return {
        "width": width,
        "height": height,
        "mip_levels": mips,
        "format": _dds_format_name(flags, fourcc, bitcount, masks, head),
    }


def _dds_format_name(flags, fourcc, bitcount, masks, head):
    """由 DDS 像素格式推导 PF_ 枚举名；无法识别时抛 ValueError。"""
    if flags & DDPF_FOURCC:
        if fourcc == b"DX10":  # DX10 扩展头：dxgiFormat 位于偏移 128
            dxgi = struct.unpack_from("<I", head, 128)[0]
            name = DXGI_TO_NAME.get(dxgi)
            if name is None:
                raise ValueError(f"不支持的 DDS 格式（DXGI 格式 ID {dxgi}）")
            return name
        name = FOURCC_TO_NAME.get(fourcc)
        if name is None:
            raise ValueError(f"不支持的 DDS 压缩格式 fourCC={fourcc!r}")
        return name
    if flags & DDPF_RGB:
        name = _legacy_rgb_name(bitcount, masks)
        if name is not None:
            return name
    raise ValueError(
        f"无法识别的 DDS 像素格式（flags=0x{flags:X}, bitcount={bitcount}, "
        f"masks={masks}）。支持 8 位/通道的 RGBA/BGRA 及常见 DX10/BC 格式。")


def _legacy_rgb_name(bitcount, masks):
    """按位掩码推断 8 位/通道的 R/G/B/A 通道顺序（如 R8G8B8A8_UNORM）。"""
    if bitcount != 32:
        return None
    by_shift = {}
    for i, ch in ((0, "R"), (1, "G"), (2, "B"), (3, "A")):
        mask = masks[i]
        if mask == 0:
            continue
        shift = (mask & -mask).bit_length() - 1
        if mask != (0xFF << shift):  # 每通道必须恰好 8 位
            return None
        by_shift[shift] = ch
    shifts = sorted(by_shift)
    if len(by_shift) not in (3, 4) or shifts != list(range(0, len(shifts) * 8, 8)):
        return None
    order = "".join(by_shift[s] for s in shifts)
    return "".join(f"{c}8" for c in order) + "_UNORM"


def is_icon_with_suffix(name):
    """判断是否为带尺寸后缀的图标，如 ICON_CIVILIZATION_DONGHAN_22"""
    m = re.match(r"(ICON_\w+?)_(\d+)$", name)
    return m.group(1) if m else None


def get_source_png(name_no_ext):
    """获取对应的源 png 文件路径（.assets 中文名，经 asset_map 技术名映射）。"""
    base = is_icon_with_suffix(name_no_ext) or name_no_ext
    friendly = _ASSET_MAP.get(base) or base
    return os.path.join(ASSETS_DIR, friendly + ".png")


# legacy：Suk 适配素材的**旧**命名后缀。2026-09-18 起该类素材已迁到**独立命名空间**
# `SUK_UI_PORTRAIT_*` / `SUK_UI_BACKGROUND_*`（迁移工具：
# civ6-asset-forge/scripts/migrate_suk_namespace.py）——不再与 `FALLBACK_` 共享前缀，
# 因此新命名**不需要**任何例外表。本常量仅为兼容尚未迁移的旧工程而保留；
# 全部工程迁移完成后，可连同 is_fallback() 里那次判断一并删除。
_UI_PORTRAIT_SUFFIXES = ("_Suk",)


def is_fallback(name):
    """判断是否为 Fallback 前景立绘（3D 领袖回退用的 Leader_Fallback 贴图）。

    **`FALLBACK_` 前缀即 Leader_Fallback** —— 这是官方模板的固定命名，按约定
    **不再被第三方界面素材借用**：第三方适配进各自的独立命名空间
    （Suk 选人界面适配＝`SUK_UI_*`），从而从根上避免"同前缀不同类别"的歧义。

    历史例外（legacy，仅为兼容未迁移的旧工程）：
    `FALLBACK_NEUTRAL_{X}_Suk` 是 Suk 选人界面的 **2D UI 立绘**（类别 `UserInterface`），
    与 3D 回退同前缀。旧工程必须排除它，否则 cooker 报
    `has class 'X', but is bound to parameter 'Y' which does not accept this class`，
    且 **XLP cook 仍显示 success**、条目被静默替换成 error asset。
    该类素材现名 `SUK_UI_PORTRAIT_{X}`。

    新增同类 UI 素材时**不要再借用 `FALLBACK_` 前缀**，改用独立命名空间；
    最终防线始终是 `verify_tex_class.py`（校验 `.tex` 类别 ↔ 所绑 XLP 类，**不依赖文件名**）。
    """
    if name.endswith(_UI_PORTRAIT_SUFFIXES):   # legacy 兼容；全部工程迁移后可删
        return False
    return name.startswith("FALLBACK_")


def make_tags(classname):
    """根据 classname 生成 m_Tags XML 片段"""
    if classname == "Leader_Fallback":
        lines = [
            '\t\t<Element text="Leader_Fallback"/>',
            '\t\t<Element text="Leader"/>',
            '\t\t<Element text="Fallback"/>',
        ]
    else:
        lines = [
            '\t\t<Element text="UserInterface"/>',
        ]
    return "\n".join(lines)


def gen_tex(dds_path):
    """为单个 dds 文件生成 .tex 文件"""
    dds_name = os.path.basename(dds_path)
    tex_name = os.path.splitext(dds_name)[0] + ".tex"
    name_no_ext = os.path.splitext(dds_name)[0]
    tex_path = os.path.join(os.path.dirname(dds_path), tex_name)

    png_path = get_source_png(name_no_ext)

    if not os.path.exists(png_path):
        print(f"  skip (no source png): {name_no_ext}")
        return False

    try:
        info = parse_dds_info(dds_path)   # 读的是 dds 本身，而不是源 png
    except ValueError as e:
        print(f"  skip ({e})")
        return False
    width = info["width"]
    height = info["height"]
    mip_levels = info["mip_levels"]
    fmt = info["format"]

    fallback = is_fallback(name_no_ext)
    classname = "Leader_Fallback" if fallback else "UserInterface"

    # m_NumMipMaps = dds 的 mipLevels - 1（mipLevels 从 DDS 头读取，与 dds 实际一致）
    # bCompleteMipChain always false because iNumManualMips is always 0
    if mip_levels > 1:
        busemips = "true"
        nummipmaps = str(mip_levels - 1)
    else:
        busemips = "false"
        nummipmaps = "0"
    completemipchain = "false"

    pixelformat = "PF_" + fmt
    tags_xml = make_tags(classname)

    content = TEX_TEMPLATE.format(
        xml_encoding=XML_ENCODING,
        pixelformat=pixelformat,
        busemips=busemips,
        completemipchain=completemipchain,
        height=height,
        width=width,
        nummipmaps=nummipmaps,
        sourcefilepath=png_path.replace("\\", "/"),
        classname=classname,
        ddsname=dds_name,
        name=name_no_ext,
        tags=tags_xml,
    )

    # 按系统 ANSI 代码页写出（与 AssetEditor 读取编码一致，见模块 docstring）。
    # 若该代码页装不下路径里的字符（如西文系统 cp1252 遇中文路径），用 XML
    # 字符引用（&#x...;）转义而非报错——任何 XML 解析器都能还原原文，
    # 也不会因非法字节导致 AssetEditor 乱码崩溃。
    errs = "strict"
    try:
        content.encode(TEX_ENCODING)
    except UnicodeEncodeError:
        errs = "xmlcharrefreplace"
        print(f"  warn: 系统默认编码 {TEX_ENCODING} 无法编码 {name_no_ext} 的源路径"
              f"（含中文），已用 XML 字符引用转义（XML 解析器可还原，AssetEditor 显示为实体）")
    except LookupError:
        errs = "xmlcharrefreplace"
        print(f"  warn: 未知编解码名 {TEX_ENCODING!r}，退用 XML 字符引用转义")

    with open(tex_path, "w", encoding=TEX_ENCODING, errors=errs, newline="\n") as f:
        f.write(content)
    return True


def main():
    # `-h` / `--help`：本脚本在**导入期**就读 sys.argv 定目录（见文件头部），
    # 此前 `--help` 会被当成贴图目录 → FileNotFoundError 指向 "<cwd>\--help"。
    # 这里在真正干活前拦下，给出用法而不是令人困惑的路径错误。
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        # 注意：TEXTURES_DIR 在导入期已把 "--help" 当成 argv[1] 吃掉了，
        # 所以这里不能直接打印它（会显示 textures_dir=--help）。
        _default = str(_PROJECT_ROOT / (_civ_name or "MOD_NAME") / "Textures")
        print("用法：python gen_tex.py [textures_dir] [assets_dir] [asset_map_json]")
        print("  为 textures_dir 下每个 .dds 生成同名 .tex（按 DDS 头推导格式/mip 等字段）")
        print("  三个参数都可省；通常由 make_atlas.py / convert_art.ps1 自动调用，不直接跑。")
        print(f"  省参数时的默认贴图目录：{_default}")
        return 0
    if not os.path.isdir(TEXTURES_DIR):
        print(f"ERROR: 贴图目录不存在：{TEXTURES_DIR}", file=sys.stderr)
        return 2
    dds_files = sorted(f for f in os.listdir(TEXTURES_DIR) if f.endswith(".dds"))
    print(f"Found {len(dds_files)} dds files")
    print(f"tex encoding = system ANSI ({TEX_ENCODING}), xml declaration = {XML_ENCODING}\n")

    ok, skip = 0, 0
    for dds in dds_files:
        dds_path = os.path.join(TEXTURES_DIR, dds)
        tex_name = os.path.splitext(dds)[0] + ".tex"
        print(f"  {tex_name}")
        if gen_tex(dds_path):
            ok += 1
        else:
            skip += 1

    print(f"\nDone: {ok} generated, {skip} skipped")


if __name__ == "__main__":
    main()
