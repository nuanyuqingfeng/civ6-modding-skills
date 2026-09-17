#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""regen_atlas_tiers.py — 图集中间档「母版重出」工具（修复被压对比/锐化的档位）

## 解决什么问题

图标图集的多个尺寸档（如 32/45/50/80/128）本应从**最高分辨率母版**逐格等比降采样得到。
但实践中常见两种污染，导致小档边缘出现**锯齿/硬边**：

  1. 小档不是从高分辨率母版缩出来的，而是从**已经缩小过的中间图**再缩（链式缩放），
     或有损来源反复转存；
  2. 缩完之后又对图像做了**锐化 / 对比拉伸（levels）**。这会把抗锯齿的过渡像素
     推向 alpha 两端，边缘退化成"二值硬边"，肉眼即锯齿。

这类损伤**在 256 档看不出来**（母版本身是好的），只有中间档中招；
用本工具从母版重出即可修复，且**不需要改 .tex / 网格 / 注册链**。

## 判据（measure 模式）

对每一档算三个边缘质量指标（口径与 `verify_icon_atlas.py --edge-qa` 一致）：

  mid   = 边界像素中落在中间调 (20..235) 的比例%   —— 越高 = 抗锯齿过渡越完整
  hard  = 相邻 alpha 跳变 > 200 的比例%             —— 越高 = 边缘越硬
  ratio = 半透明像素数 / 边界周长                   —— 归一化斜坡宽度（形状无关）

「应有值」= 从母版逐格 LANCZOS 重出的结果。现存文件若 `mid` 明显偏低
或 `ratio` 明显偏小，即判为受损档。

## 用法

    # ① 体检：报告哪些档受损（不写盘）
    python regen_atlas_tiers.py <projectRoot> --report

    # ② 预演：显示将如何重出（不写盘）
    python regen_atlas_tiers.py <projectRoot> --atlas ATLAS_X --master 256 --sizes 32,50,80

    # ③ 写盘
    python regen_atlas_tiers.py <projectRoot> --atlas ATLAS_X --master 256 --sizes 32,50,80 --write

    # ④ 只处理体检发现的问题档
    python regen_atlas_tiers.py <projectRoot> --report --write-damaged

    # ⑤ 指定单文件（图集名与文件名不一致时）
    python regen_atlas_tiers.py <projectRoot> --file RGN_X32.dds --master-file RGN_X256.dds \
        --grid 3x3 --size 32 --write

不传 --atlas/--file 且带 --report 时，自动扫描 <root>/Data/*.xml 与
<root>/Mod_Adaptation/**/*.xml 的 IconTextureAtlases，得到全部图集与网格。

网格：优先取 XML 的 IconsPerRow/IconsPerColumn；缺失时按 `--grid` 或从母版画布/档位推断。

退出码：0 = 无受损 / 已成功；1 = 参数或结构错误；2 = 体检发现受损档（仅 --report 时）。
"""
import argparse
import glob
import os
import re
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RESAMPLE = Image.Resampling.LANCZOS   # 工程既有约定：逐格 LANCZOS（见 art-pipeline.md）

# 受损判定阈值（与 verify_icon_atlas.py --edge-qa 保持一致）
MID_TOLERANCE = 8.0     # 中间调占比低于参考值 8 个百分点 → 受损
RATIO_FACTOR = 0.7      # 归一化斜坡宽度低于参考值 70% → 受损


# ---------------------------------------------------------------- DDS I/O

def dds_header_bytes(w, h):
    """R8G8B8A8 单 mip 的 DDS 头（与 Civ6 工程既有 DDS 逐字节同构）。"""
    hdr = bytearray()
    hdr += b'DDS '
    hdr += struct.pack('<7I', 124, 0x21007, h, w, 0, 1, 1)
    hdr += bytes.fromhex('46545854') + bytes(40)          # 'FTXT' 签名 + 备份位
    hdr += struct.pack('<2I', 32, 0x41)                   # pfSize, RGB|ALPHAPIXELS
    hdr += b'\x00' * 4                                    # fourCC
    hdr += struct.pack('<5I', 32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000)
    hdr += struct.pack('<5I', 0x401008, 0, 0, 0, 0)
    return bytes(hdr)


def read_dds(path):
    """→ (RGBA ndarray, width, height, mips)；失败抛 ValueError。"""
    with open(path, 'rb') as f:
        head = f.read(128)
        if head[:4] != b'DDS ':
            raise ValueError(f'不是 DDS: {path}')
        h, w = struct.unpack('<II', head[12:20])
        mips = struct.unpack('<I', head[28:32])[0]
        raw = f.read(w * h * 4)
    if len(raw) != w * h * 4:
        raise ValueError(f'{path}: 数据长度 {len(raw)} != {w*h*4}')
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 4), w, h, mips


def write_dds(path, arr):
    h, w = arr.shape[:2]
    with open(path, 'wb') as f:
        f.write(dds_header_bytes(w, h))
        f.write(np.ascontiguousarray(arr, dtype=np.uint8).tobytes())
    return w, h


# ---------------------------------------------------------------- 质量指标

def cell_metrics(im):
    """单格 (mid%, hard%, ratio) 或 None（空格）。"""
    a = im[:, :, 3].astype(int)
    if (a > 8).sum() < 16:
        return None
    m = a > 8
    b = np.zeros_like(m)
    b[:-1, :] |= m[:-1, :] != m[1:, :]
    b[:, :-1] |= m[:, :-1] != m[:, 1:]
    b[1:, :] |= m[1:, :] != m[:-1, :]
    b[:, 1:] |= m[:, 1:] != m[:, :-1]
    bd = a[b]
    mid = ((bd > 20) & (bd < 235)).mean() * 100
    hs = tot = 0
    for dy, dx in ((0, 1), (1, 0)):
        p = a[:a.shape[0] - dy, :a.shape[1] - dx]
        q = a[dy:, dx:]
        d = np.abs(p - q)
        sel = d[(p > 0) | (q > 0)]
        hs += int((sel > 200).sum())
        tot += int(sel.size)
    return mid, hs / max(tot, 1) * 100, int(((a > 0) & (a < 255)).sum()) / max(int(b.sum()), 1)


def atlas_metrics(arr, size, cols, rows):
    out = []
    for i in range(cols * rows):
        r, c = divmod(i, cols)
        if (r + 1) * size > arr.shape[0] or (c + 1) * size > arr.shape[1]:
            break
        q = cell_metrics(arr[r * size:(r + 1) * size, c * size:(c + 1) * size])
        if q:
            out.append(q)
    if not out:
        return None
    a = np.array(out)
    return a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean()


def regen_from_master(master, size, cols, rows, master_size):
    """母版逐格 LANCZOS → 目标尺寸图集。"""
    canv = np.zeros((rows * size, cols * size, 4), dtype=np.uint8)
    for i in range(cols * rows):
        r, c = divmod(i, cols)
        cell = Image.fromarray(
            master[r * master_size:(r + 1) * master_size,
                   c * master_size:(c + 1) * master_size])
        canv[r * size:(r + 1) * size, c * size:(c + 1) * size] = np.asarray(
            cell.resize((size, size), RESAMPLE))
    return canv


# ---------------------------------------------------------------- 图集规格发现

def parse_atlas_specs(root):
    """→ {atlas: {size: (filename, cols, rows)}}（含 Data/ 与 Mod_Adaptation/）。"""
    specs = {}
    pats = [str(root / 'Data' / '*.xml'),
            str(root / 'Mod_Adaptation' / '**' / '*.xml')]
    for pat in pats:
        for f in sorted(glob.glob(pat, recursive=True)):
            try:
                txt = Path(f).read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            for m in re.finditer(r'<Row\s+Name="([^"]+)"\s*([^/>]*)/>', txt):
                name, attrs = m.group(1), m.group(2)
                if 'IconSize' not in attrs:
                    continue
                size = int(re.search(r'IconSize="(\d+)"', attrs).group(1))
                fm = re.search(r'Filename="([^"]+)"', attrs)
                if not fm:
                    continue
                fn = fm.group(1)
                fn = os.path.basename(fn if fn.lower().endswith('.dds') else fn + '.dds')
                cr = re.search(r'IconsPerRow="(\d+)"', attrs)
                cc = re.search(r'IconsPerColumn="(\d+)"', attrs)
                specs.setdefault(name, {})[size] = (
                    fn, int(cr.group(1)) if cr else 1, int(cc.group(1)) if cc else 1)
    return specs


def survey(tex, specs):
    """体检：→ (报告行 list, 受损 list)。"""
    rows, damaged = [], []
    for atlas, sized in sorted(specs.items()):
        local = {s: v for s, v in sized.items() if (tex / v[0]).is_file()}
        if len(local) < 2:
            continue
        msize = 256 if 256 in local else max(local)
        mfn, mcols, mrows = local[msize]
        try:
            marr, mw, mh, mmips = read_dds(tex / mfn)
        except ValueError:
            continue
        if (mw, mh) != (mcols * msize, mrows * msize):
            rows.append((atlas, msize, mfn, None, None, 'GRID?', None))
            continue
        for s in sorted(local):
            fn, cols, rows_n = local[s]
            try:
                arr, w, h, mips = read_dds(tex / fn)
            except ValueError:
                continue
            if (w, h) != (cols * s, rows_n * s):
                continue          # 网格不符 → 交给 verify_icon_atlas 报
            q = atlas_metrics(arr, s, cols, rows_n)
            if q is None:
                continue
            ref = None
            verdict = ''
            if s != msize:
                ref_arr = regen_from_master(marr, s, cols, rows_n, msize)
                ref = atlas_metrics(ref_arr, s, cols, rows_n)
                if ref:
                    if q[0] < ref[0] - MID_TOLERANCE or q[2] < ref[2] * RATIO_FACTOR:
                        verdict = 'DAMAGED'
                        damaged.append(dict(atlas=atlas, size=s, file=fn, cols=cols,
                                            rows=rows_n, master=msize,
                                            master_file=mfn))
                    else:
                        verdict = 'ok'
            rows.append((atlas, s, fn, q, ref, verdict, msize if s != msize else None))
    return rows, damaged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('projectRoot')
    ap.add_argument('--report', action='store_true', help='体检全部图集，报告受损档')
    ap.add_argument('--write-damaged', action='store_true',
                    help='配合 --report：把体检出的受损档全部重出')
    ap.add_argument('--atlas', default='', help='图集名（IconTextureAtlases.Name）')
    ap.add_argument('--master', type=int, default=256, help='母版档位（默认 256）')
    ap.add_argument('--sizes', default='', help='要重出的档位，逗号分隔，如 32,50,80')
    ap.add_argument('--grid', default='', help='网格 cols x rows，如 3x3（XML 缺失时用）')
    ap.add_argument('--file', default='', help='单文件模式：目标 dds 文件名')
    ap.add_argument('--master-file', default='', help='单文件模式：母版 dds 文件名')
    ap.add_argument('--size', type=int, default=0, help='单文件模式：目标档位')
    ap.add_argument('--master-size', type=int, default=0, help='单文件模式：母版档位')
    ap.add_argument('--write', action='store_true', help='实际写盘（否则只预演）')
    args = ap.parse_args()

    root = Path(args.projectRoot)
    tex = root / 'Textures'
    if not tex.is_dir():
        raise SystemExit(f'找不到 Textures 目录: {tex}')
    specs = parse_atlas_specs(root)

    # ---- 体检模式
    if args.report:
        rows, damaged = survey(tex, specs)
        print('=' * 104)
        print(f'{"图集":<34} {"档":>4} {"中间调%":>8} {"硬跳%":>7} {"比值":>7} |'
              f'{"母版重出参考":>22} | {"判定":>9}')
        print('=' * 104)
        for atlas, s, fn, q, ref, verdict, ms in rows:
            if q is None:
                print(f'{atlas:<34} {s:>4} (网格与 XML 不符，跳过)')
                continue
            refs = f'{ref[0]:7.1f}% {ref[2]:6.2f}' if ref else ''
            print(f'{atlas:<34} {s:>4} {q[0]:8.1f} {q[1]:7.1f} {q[2]:7.2f} |'
                  f'{refs:>22} | {verdict:>9}')
        print()
        if damaged:
            print(f'发现受损档 {len(damaged)} 个：')
            for d in damaged:
                print(f'  {d["atlas"]:<34} {d["size"]:>4}px  {d["file"]}')
            if not args.write_damaged:
                print('\n加 --write-damaged 可一次重出全部。')
                return 2
            print('\n--write-damaged：开始重出')
        else:
            print('未发现受损档（无 256 母版的图集不在体检范围）。')
            return 0

    # ---- 作业清单
    jobs = []      # (src_dds, dst_dds, size, cols, rows, master_size)
    if args.report and args.write_damaged:
        _, damaged = survey(tex, specs)
        for d in damaged:
            jobs.append((tex / d['master_file'], tex / d['file'], d['size'],
                         d['cols'], d['rows'], d['master']))
    elif args.file:
        if not (args.master_file and args.size):
            raise SystemExit('--file 模式需要同时给 --master-file 与 --size')
        if args.grid:
            m = re.match(r'(\d+)\s*[x×]\s*(\d+)', args.grid)
            if not m:
                raise SystemExit(f'--grid 格式应为 colsxrows，收到 {args.grid!r}')
            cs, rs = int(m.group(1)), int(m.group(2))
        else:
            _marr, mw, mh, _mm = read_dds(tex / args.master_file)
            ms = args.master_size or 256
            cs, rs = mw // ms, mh // ms
        jobs.append((tex / args.master_file, tex / args.file, args.size, cs, rs,
                     args.master_size or 256))
    elif args.atlas:
        if args.atlas not in specs:
            raise SystemExit(f'图集 {args.atlas!r} 不在 Icons XML 中')
        sized = specs[args.atlas]
        cols, rows = sized[args.master][1], sized[args.master][2]
        if args.grid:
            m = re.match(r'(\d+)\s*[x×]\s*(\d+)', args.grid)
            if not m:
                raise SystemExit(f'--grid 格式应为 colsxrows，收到 {args.grid!r}')
            cols, rows = int(m.group(1)), int(m.group(2))
        mfn = sized[args.master][0]
        want = ([int(x) for x in args.sizes.split(',') if x.strip()]
                if args.sizes else [s for s in sorted(sized) if s != args.master])
        for s in want:
            if s == args.master:
                continue
            if s not in sized:
                print(f'  WARN 图集无 {s} 档，跳过')
                continue
            jobs.append((tex / mfn, tex / sized[s][0], s, cols, rows, args.master))
    else:
        ap.error('需要 --report / --atlas / --file 之一')

    if not jobs:
        print('没有要处理的目标。')
        return 1

    # ---- 执行
    print('=' * 104)
    print(f'{"目标文件":<40} {"档":>4} {"矩阵":>7} | {"现状 中/硬/比":>22} | '
          f'{"重出后 中/硬/比":>22}')
    print('=' * 104)
    n_ok = 0
    do_write = args.write or (args.report and args.write_damaged)
    for src, dst, size, cols, rows_n, msize in jobs:
        if not src.is_file():
            print(f'  !! 母版缺失 {src.name}，跳过')
            continue
        marr, mw, mh, mmips = read_dds(src)
        exp = (cols * msize, rows_n * msize)
        if (mw, mh) != exp:
            print(f'  !! {src.name} 画布 {mw}x{mh} != 预期 {exp[0]}x{exp[1]}，跳过')
            continue
        if mmips != 1:
            print(f'  !! {src.name} mips={mmips}（应 1），跳过')
            continue
        new = regen_from_master(marr, size, cols, rows_n, msize)
        q_old = None
        if dst.is_file():
            try:
                old, ow, oh, _ = read_dds(dst)
                if (ow, oh) != (cols * size, rows_n * size):
                    print(f'  !! {dst.name} 尺寸 {ow}x{oh} 与预期不符，拒绝覆盖')
                    continue
                q_old = atlas_metrics(old, size, cols, rows_n)
            except ValueError:
                pass
        q_new = atlas_metrics(new, size, cols, rows_n)

        def fmt(q):
            return f'{q[0]:6.1f}% {q[1]:5.1f}% {q[2]:5.2f}' if q else '   —'
        print(f'{dst.name:<40} {size:>4} {cols}x{rows_n:<4} | {fmt(q_old):>22} | '
              f'{fmt(q_new):>22}')
        if do_write:
            w, h = write_dds(dst, new)
            back, bw, bh, bm = read_dds(dst)
            assert (bw, bh) == (w, h) and bm == 1 and np.array_equal(back, new)
            n_ok += 1

    print()
    if do_write:
        print(f'完成：写出 {n_ok} 个 DDS（.tex 未触碰；尺寸/网格/mips 均未变）。')
        print('提示：仍需 ModBuddy 构建 + 进游戏验证；建议随后跑 '
              'verify_icon_atlas.py --edge-qa 复核。')
    else:
        print('[预演] 未写盘。加 --write（或 --report --write-damaged）实际执行。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
