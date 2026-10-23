#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""dds_io.py — Civ6 DDS 的读写与头部校验（零外部依赖，纯标准库 + Pillow）

## 为什么需要它

Civ6 工程里的 UI 贴图（立绘 / 背景 / 图标非图集档）是**未压缩** DDS，
AssetEditor 产出的头部带一个 `FTXT` 签名。`convert_art.ps1` 走 **texconv**（外部 exe）产出这类 DDS，
但 texconv 的头部与官方 cook 产物不一致：多写 `DDSD_PITCH`、`dwPitchOrLinearSize` 非 0、
保留区没有 `FTXT`、单通道写成 `DDPF_LUMINANCE`。这四处差异会让领袖纸片在外交场景
不显示、只留零星色块（`civ6-asset-forge/reference/leader-2d.md` §3.6(5)）。

本模块承担两件事：

  1. 按官方口径**构造**头部（`dds_header_bytes`），可直接写盘，不必依赖 texconv；
  2. 按官方口径**校验并修复**既有 DDS 的头部（`header_issues` / `ensure_official_header`），
     像素载荷原样保留。

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
| 28 | dwMipMapCount | `mips`（完整 mip 链级数） |
| 32 | dwReserved1[11] | 首 4 字节 = `FTXT`，其余 0 |
| 76 | pf.dwSize | 32 |
| 80 | pf.dwFlags | 32 位：0x41（RGB \| ALPHAPIXELS）；8 位：0x40（RGB） |
| 84 | pf.dwFourCC | 0 |
| 88 | pf.dwRGBBitCount | 32（RGBA8）或 8（单通道 OPACITY） |
| 92/96/100/104 | R/G/B/A 掩码 | 32 位：0xFF / 0xFF00 / 0xFF0000 / 0xFF000000；8 位：0xFF / 0 / 0 / 0 |
| 108 | dwCaps | 0x401008 |
| 112..124 | caps2/3/4 + reserved2 | 0 |

## 用法

    from dds_io import read_dds, write_dds, dds_header_bytes, ensure_official_header

    img  = read_dds("Textures/X.dds")        # -> PIL.Image (RGBA)
    write_dds("Textures/Y.dds", img)         # 单 mip RGBA8 写出
    hdr  = dds_header_bytes(w, h)            # 只要头
    changed, issues = ensure_official_header("Textures/Y.dds")
        # 校验 128 字节头，不合规就地按官方口径重写（像素载荷不动）

    python dds_io.py --selftest <某个既有.dds> [更多.dds ...]
        # 读→写往返，逐字节（MD5）比对，验证本模块与既有产出同构
    python dds_io.py --check <DDS ...>       # 按官方口径校验头部，不合规即非零退出
    python dds_io.py --fix   <DDS ...>       # 校验并重写头部（像素载荷不动）
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
_PF_FLAGS_NO_ALPHA = 0x40              # DDPF_RGB（单通道 OPACITY 用这个）
_PF_BITCOUNT = 32
_PF_MASKS = (0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
_PF_MASKS_8 = (0x000000FF, 0, 0, 0)
_CAPS = 0x401008                       # DDSCAPS_TEXTURE | DDSCAPS_COMPLEX | DDSCAPS_MIPMAP


def mip_chain_length(width, height):
    """完整 mip 链的级数：从 w×h 逐级减半到 1×1。"""
    n = 1
    while width > 1 or height > 1:
        width = max(1, width // 2)
        height = max(1, height // 2)
        n += 1
    return n


def dds_header_bytes(width, height, mips=1, bit_count=32):
    """构造 128 字节 DDS 头。

    mips 取完整 mip 链的级数（单 mip 写 1）；bit_count 取 32（RGBA8）或 8（单通道）。
    官方 cook 产物的四处特征：dwFlags 不含 DDSD_PITCH、dwPitchOrLinearSize 为 0、
    保留区前 4 字节为 FTXT、单通道用 DDPF_RGB 而非 DDPF_LUMINANCE。
    """
    if bit_count == 32:
        pf_flags, masks = _PF_FLAGS, _PF_MASKS
    elif bit_count == 8:
        pf_flags, masks = _PF_FLAGS_NO_ALPHA, _PF_MASKS_8
    else:
        raise ValueError("仅支持 32 位 RGBA8 与 8 位单通道，收到 %r" % bit_count)
    hdr = bytearray()
    hdr += MAGIC
    hdr += struct.pack("<7I", 124, _FLAGS, height, width, 0, 1, mips)
    hdr += _FTXT + bytes(40)                       # 签名 + dwReserved1 余位
    hdr += struct.pack("<2I", _PF_SIZE, pf_flags)
    hdr += b"\x00" * 4                             # dwFourCC
    hdr += struct.pack("<5I", bit_count, *masks)
    hdr += struct.pack("<5I", _CAPS, 0, 0, 0, 0)
    assert len(hdr) == HEADER_SIZE, len(hdr)
    return bytes(hdr)


def read_dds(path):
    """读未压缩 RGBA8 DDS 的首级 → PIL.Image(RGBA)。非本格式抛 ValueError。

    多 mip 文件只取首级；mip 链的完整性由 `header_issues` 校验。
    """
    with open(path, "rb") as f:
        head = f.read(HEADER_SIZE)
        if len(head) < HEADER_SIZE or head[:4] != MAGIC:
            raise ValueError("%s: 不是 DDS 或头部截断" % path)
        h, w = struct.unpack("<II", head[12:20])
        pf_flags = struct.unpack("<I", head[80:84])[0]
        fourcc = head[84:88]
        bits = struct.unpack("<I", head[88:92])[0]
        if fourcc != b"\x00\x00\x00\x00" or not (pf_flags & 0x40) or bits != 32:
            raise ValueError(
                "%s: 仅支持未压缩 RGBA8（fourCC=%r pfFlags=0x%X bits=%d）"
                % (path, fourcc, pf_flags, bits))
        raw = f.read(w * h * 4)
    if len(raw) != w * h * 4:
        raise ValueError("%s: 首级像素数据 %d != %d（w=%d h=%d）"
                         % (path, len(raw), w * h * 4, w, h))
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


def payload_bytes(width, height, mips, bit_count):
    """完整 mip 链的像素载荷字节数。"""
    total = 0
    w, h = width, height
    for _ in range(mips):
        total += max(1, w) * max(1, h) * (bit_count // 8)
        w //= 2
        h //= 2
    return total


def header_issues(path):
    """按官方 cook 产物口径校验 128 字节头，返回问题清单（空 = 合规）。

    官方口径取自可用的领袖成品 DDS（`reference/leader-2d.md` §3.6(5)）：
      · dwFlags 不含 DDSD_PITCH(0x8)
      · dwPitchOrLinearSize 为 0
      · 保留区前 4 字节为 FTXT
      · 单通道用 DDPF_RGB(0x40)，不用 DDPF_LUMINANCE(0x20000)
      · 像素载荷长度等于完整 mip 链的期望值

    dwCaps 不参与校验：官方产物里单 mip 的 0x1000 与 0x401008 两种写法都存在。
    """
    with open(path, "rb") as f:
        head = f.read(HEADER_SIZE)
        payload = len(f.read())
    if len(head) < HEADER_SIZE or head[:4] != MAGIC:
        raise ValueError("%s: 不是 DDS 或头部截断" % path)
    h, w = struct.unpack("<II", head[12:20])
    mips = struct.unpack("<I", head[28:32])[0]
    flags = struct.unpack("<I", head[8:12])[0]
    pitch = struct.unpack("<I", head[20:24])[0]
    pf_flags = struct.unpack("<I", head[80:84])[0]
    bits = struct.unpack("<I", head[88:92])[0]
    issues = []
    if flags & 0x8:
        issues.append("dwFlags=0x%X 含 DDSD_PITCH" % flags)
    if flags != _FLAGS:
        issues.append("dwFlags=0x%X 应为 0x%X" % (flags, _FLAGS))
    if pitch != 0:
        issues.append("dwPitchOrLinearSize=0x%X 应为 0" % pitch)
    if head[32:36] != _FTXT:
        issues.append("保留区前 4 字节=%r 应为 %r" % (head[32:36], _FTXT))
    if bits == 32:
        if pf_flags != _PF_FLAGS:
            issues.append("pf.dwFlags=0x%X 应为 0x%X（32 位 RGBA8）" % (pf_flags, _PF_FLAGS))
    elif bits == 8:
        if pf_flags != _PF_FLAGS_NO_ALPHA:
            issues.append("pf.dwFlags=0x%X 应为 0x%X（8 位单通道）" % (pf_flags, _PF_FLAGS_NO_ALPHA))
    else:
        issues.append("pf.dwRGBBitCount=%d 应为 32 或 8" % bits)
    want = payload_bytes(w, h, mips, bits)
    if payload != want:
        issues.append("像素载荷 %d 字节，完整 mip 链（%d 级）应为 %d" % (payload, mips, want))
    return issues


def ensure_official_header(path):
    """校验 DDS 头，不合规就按官方口径重写（像素载荷原样保留）。

    返回 (changed, issues)：changed 表示是否动过盘，issues 为修复前的问题清单。
    载荷长度不符时无法靠换头救回，直接抛 ValueError。
    """
    issues = header_issues(path)
    if not issues:
        return False, issues
    with open(path, "rb") as f:
        head = f.read(HEADER_SIZE)
        payload = f.read()
    h, w = struct.unpack("<II", head[12:20])
    mips = struct.unpack("<I", head[28:32])[0]
    bits = struct.unpack("<I", head[88:92])[0]
    want = payload_bytes(w, h, mips, bits)
    if len(payload) != want:
        raise ValueError("%s: 像素载荷 %d != %d，换头无法修复"
                         % (path, len(payload), want))
    with open(path, "wb") as f:
        f.write(dds_header_bytes(w, h, mips=mips, bit_count=bits))
        f.write(payload)
    return True, issues


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
    """读→写往返自检：能逐字节还原既有单 mip DDS，才证明本模块口径与工程一致。"""
    import tempfile
    ok = True
    print("=== dds_io 往返自检（读→写，逐字节比对）===")
    for p in paths:
        if not os.path.exists(p):
            print("  MISSING %s" % p)
            ok = False
            continue
        if read_dds_info(p)["mips"] != 1:
            print("  SKIP    %s: 多 mip 文件（write_dds 只写单 mip）" % p)
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


def check_paths(paths, fix):
    """按官方口径校验（可选修复）一批 DDS 的头部。"""
    bad = 0
    for p in paths:
        issues = header_issues(p)
        if not issues:
            print("  OK      %s" % p)
            continue
        bad += 1
        if fix:
            changed, _ = ensure_official_header(p)
            print("  FIXED   %s（%s）" % (p, "；".join(issues) if changed else "无需改动"))
        else:
            print("  FAIL    %s" % p)
            for item in issues:
                print("            %s" % item)
    print()
    print("DDS 头部校验：%d 个文件，%d 个%s" % (len(paths), bad, "已修复" if fix else "不合规"))
    return 0 if (fix or not bad) else 1


def main():
    ap = argparse.ArgumentParser(description="Civ6 DDS 读写、往返自检与头部校验")
    ap.add_argument("--selftest", nargs="+", metavar="DDS",
                    help="对这些既有 DDS 做读→写往返，逐字节比对")
    ap.add_argument("--check", nargs="+", metavar="DDS",
                    help="按官方 cook 口径校验 128 字节头，不合规即非零退出")
    ap.add_argument("--fix", nargs="+", metavar="DDS",
                    help="校验并按官方口径重写头部（像素载荷不动）")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.selftest)
    if a.check:
        return check_paths(a.check, fix=False)
    if a.fix:
        return check_paths(a.fix, fix=True)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
