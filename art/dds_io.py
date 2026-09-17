#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""dds_io.py — Civ6 单 mip RGBA8 DDS 的最小读写（零外部依赖，纯标准库 + Pillow）

## 为什么需要它

Civ6 工程里的 UI 贴图（立绘 / 背景 / 图标非图集档）一律是
**未压缩 RGBA8、单 mip** 的 DDS，且 AssetEditor 产出的头部带一个 `FTXT` 签名。
`convert_art.ps1` 走 **texconv**（外部 exe）产出这类 DDS；但存在两种 texconv 不可用的场景：

  1. 沙箱/受限环境禁止执行外部 exe（实测：`texconv.exe` 被拒）；
  2. 需要**逐字节可复现**的产出（例如与既有工程 DDS 做哈希比对）。

此时用本模块直接构造 128 字节头 + 原始像素即可，产出与 texconv 口径**逐字节同构**。

## 头部布局（微软 DDS 规范，全部小端 uint32）

| 偏移 | 字段 | 本项目取值 |
|---|---|---|
| 0 | 魔数 | `DDS ` |
| 4 | dwSize | 124 |
| 8 | dwFlags | 0x21007 |
| 12 | dwHeight | h |
| 16 | dwWidth | w |
| 20 | dwPitchOrLinearSize | 0 |
| 24 | dwDepth | 1 |
| 28 | dwMipMapCount | 1（单 mip） |
| 32 | dwReserved1[11] | 首 4 字节 = `FTXT`，其余 0 |
| 76 | pf.dwSize | 32 |
| 80 | pf.dwFlags | 0x41（RGB \| ALPHAPIXELS） |
| 84 | pf.dwFourCC | 0 |
| 88 | pf.dwRGBBitCount | 32 |
| 92/96/100/104 | R/G/B/A 掩码 | 0xFF / 0xFF00 / 0xFF0000 / 0xFF000000 |
| 108 | dwCaps | 0x401008 |
| 112..124 | caps2/3/4 + reserved2 | 0 |

## 用法

    from dds_io import read_dds, write_dds, dds_header_bytes

    img  = read_dds("Textures/X.dds")        # -> PIL.Image (RGBA)
    write_dds("Textures/Y.dds", img)         # 单 mip RGBA8 写出
    hdr  = dds_header_bytes(w, h)            # 只要头

    python dds_io.py --selftest <某个既有.dds> [更多.dds ...]
        # 读→写往返，逐字节（MD5）比对，验证本模块与既有产出同构
"""
import argparse
import hashlib
import os
import struct
import sys

from PIL import Image

HEADER_SIZE = 128
MAGIC = b"DDS "

# 与 Civ6 工程既有 DDS 逐字节同构的常量（提取自 art/regen_atlas_tiers.py）
_FLAGS = 0x21007
_FTXT = bytes.fromhex("46545854")      # 'FTXT'
_PF_SIZE = 32
_PF_FLAGS = 0x41                       # DDPF_RGB | DDPF_ALPHAPIXELS
_PF_BITCOUNT = 32
_PF_MASKS = (0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
_CAPS = 0x401008


def dds_header_bytes(width, height):
    """构造 RGBA8 单 mip 的 128 字节 DDS 头。"""
    hdr = bytearray()
    hdr += MAGIC
    hdr += struct.pack("<7I", 124, _FLAGS, height, width, 0, 1, 1)
    hdr += _FTXT + bytes(40)                       # 签名 + dwReserved1 余位
    hdr += struct.pack("<2I", _PF_SIZE, _PF_FLAGS)
    hdr += b"\x00" * 4                             # dwFourCC
    hdr += struct.pack("<5I", _PF_BITCOUNT, *_PF_MASKS)
    hdr += struct.pack("<5I", _CAPS, 0, 0, 0, 0)
    assert len(hdr) == HEADER_SIZE, len(hdr)
    return bytes(hdr)


def read_dds(path):
    """读单 mip RGBA8 DDS → PIL.Image(RGBA)。非本格式抛 ValueError。"""
    with open(path, "rb") as f:
        head = f.read(HEADER_SIZE)
        if len(head) < HEADER_SIZE or head[:4] != MAGIC:
            raise ValueError("%s: 不是 DDS 或头部截断" % path)
        h, w = struct.unpack("<II", head[12:20])
        mips = struct.unpack("<I", head[28:32])[0]
        pf_flags = struct.unpack("<I", head[80:84])[0]
        fourcc = head[84:88]
        bits = struct.unpack("<I", head[88:92])[0]
        if fourcc != b"\x00\x00\x00\x00" or not (pf_flags & 0x40) or bits != 32:
            raise ValueError(
                "%s: 仅支持未压缩 RGBA8（fourCC=%r pfFlags=0x%X bits=%d）"
                % (path, fourcc, pf_flags, bits))
        raw = f.read(w * h * 4)
    if len(raw) != w * h * 4:
        raise ValueError("%s: 像素数据 %d != %d（w=%d h=%d mips=%d）"
                         % (path, len(raw), w * h * 4, w, h, mips))
    return Image.frombytes("RGBA", (w, h), raw)


def read_dds_info(path):
    """只读头 → dict(width,height,mips,pf_flags,bits,fourcc,has_ftxt)。"""
    with open(path, "rb") as f:
        head = f.read(HEADER_SIZE)
    if len(head) < HEADER_SIZE or head[:4] != MAGIC:
        raise ValueError("%s: 不是 DDS" % path)
    h, w = struct.unpack("<II", head[12:20])
    return dict(width=w, height=h,
                mips=struct.unpack("<I", head[28:32])[0],
                pf_flags=struct.unpack("<I", head[80:84])[0],
                fourcc=head[84:88],
                bits=struct.unpack("<I", head[88:92])[0],
                has_ftxt=head[32:36] == _FTXT)


def write_dds(path, img):
    """把 PIL.Image(RGBA) 写成单 mip RGBA8 DDS。返回 (w, h)。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(dds_header_bytes(w, h))
        f.write(img.tobytes())
    return w, h


def md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def selftest(paths):
    """读→写往返自检：能逐字节还原既有 DDS，才证明本模块口径与工程一致。"""
    import tempfile
    ok = True
    print("=== dds_io 往返自检（读→写，逐字节比对）===")
    for p in paths:
        if not os.path.exists(p):
            print("  MISSING %s" % p)
            ok = False
            continue
        try:
            img = read_dds(p)
        except ValueError as e:
            print("  SKIP    %s" % e)
            continue
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, os.path.basename(p))
            write_dds(out, img)
            same = md5(p) == md5(out)
        ok &= same
        print("  %-14s %-56s %s" % ("BYTE-EXACT" if same else "*** MISMATCH ***",
                                    os.path.basename(p), img.size))
    print()
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Civ6 单 mip RGBA8 DDS 读写 + 往返自检")
    ap.add_argument("--selftest", nargs="+", metavar="DDS",
                    help="对这些既有 DDS 做读→写往返，逐字节比对")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.selftest)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
