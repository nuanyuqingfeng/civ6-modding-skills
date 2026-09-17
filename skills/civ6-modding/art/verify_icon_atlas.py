#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_icon_atlas.py — 图标图集落地自查（art-pipeline 第八节「完成标准」的可执行版）

把「图标到底进没进游戏」这件事从肉眼检查变成可跑的自检。逐项对应 art-pipeline 第八节：

  1. IconDefinitions 的每个 (Atlas, IconSize) 都能解析到实存 DDS —— 无悬空引用；
  2. 图集画布尺寸 == (IconsPerRow*size, IconsPerColumn*size)，且 DDS 头 mips=1（必须单 mip）；
  3. 每个 IconDefinitions 对应的格子非空（alpha>8 像素数 >= --min-px）；
     这一步等价于模拟 IconManager:FindIconAtlas(name, size) 后取图，能抓出
     「注册写对了但图集里那格是空的/挪位了」这类唯一能在运行时才暴露的问题；
  4. .tex 的 m_Width/m_Height 与 DDS 实际宽高一致（不一致 → AssetEditor 会裁/拉伸）；
  5. XLP 里每一条 <m_EntryID> 在 Textures/ 下都有同名 .dds（漏登记 → 游戏里纹理不加载）；
  6. （可选）自定义 IconDefinitions 名与官方 Icons_*.xml 无重名。
  7. **--edge-qa**：边缘抗锯齿质量门 —— 各尺寸档的 alpha 过渡是否被「锐化/对比拉伸」破坏。
     这类损伤让图标在游戏内呈现硬边锯齿，但**结构完全合法**（引用闭合、尺寸对、格子非空），
     前 6 项**全部查不出来**，只有肉眼在实机才看得见。判据见下方「边缘质量门」。

用法：
  python verify_icon_atlas.py <projectRoot> [--icons a.xml b.xml] [--xlp a.xlp b.xlp]
                              [--vanilla "<官方 Base/Assets/UI/Icons 目录>"] [--min-px 20]
                              [--edge-qa] [--edge-tolerance 8.0] [--edge-ratio 0.7]
不传 --icons 时自动扫 <projectRoot>/Data/*.xml 与 Mod_Adaptation/**/*.xml 里含 <IconDefinitions> 的。
退出码 0 = 全通过；1 = 有失败项。

## 边缘质量门（--edge-qa）

对每个含 256 母版的图集，把「母版逐格 LANCZOS 重出」当作**应有值**，与现存档比三个指标：

  mid   = 边界像素中落在中间调 (20..235) 的比例%   —— 越高 = 抗锯齿过渡越完整
  hard  = 相邻 alpha 跳变 > 200 的比例%             —— 越高 = 边缘越硬
  ratio = 半透明像素数 / 边界周长                   —— 归一化斜坡宽度（形状无关）

判受损：`mid < 参考 - tolerance`（默认 8 个百分点）或 `ratio < 参考 * factor`（默认 0.7）。
修复用同目录的 `regen_atlas_tiers.py`（逐格 LANCZOS 从母版重出）。

为什么必须单独抽一个门：**损伤只出现在中间档**（母版是好的），且完全不影响上面的结构检查 ——
本项目 2026-09 实测 4 个图集共 22 个中间档中招（LEADERS 7 / DISTRICTS 6 / PRODUCT 5 /
RESOURCES 4），前 6 项全 PASS，而实机图标是锯齿状硬边。
"""
import argparse
import glob
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def dds_header(path):
    """返回 (width, height, mips, ok_rgba8888) —— 只读 128 字节头，不依赖 texdiag。"""
    with open(path, "rb") as f:
        h = f.read(128)
    if len(h) < 128 or h[:4] != b"DDS ":
        return None
    height, width = struct.unpack("<I", h[12:16])[0], struct.unpack("<I", h[16:20])[0]
    mips = struct.unpack("<I", h[28:32])[0]
    masks = struct.unpack("<4I", h[92:108])
    return width, height, mips, masks == (0xFF, 0xFF00, 0xFF0000, 0xFF000000)


def tex_wh(path):
    try:
        txt = Path(path).read_text(encoding="latin-1")
    except Exception:
        return None
    w = re.search(r"<m_Width>(\d+)</m_Width>", txt)
    h = re.search(r"<m_Height>(\d+)</m_Height>", txt)
    return (int(w.group(1)), int(h.group(1))) if w and h else None


_ALPHA_CACHE = {}


def _load_alpha(path):
    """整图 RGBA，按文件缓存（不缓存的话每格都重解一遍大图集，几十秒起步）。"""
    import numpy as np
    key = str(path)
    if key not in _ALPHA_CACHE:
        from PIL import Image
        _ALPHA_CACHE[key] = np.array(Image.open(path).convert("RGBA"))
    return _ALPHA_CACHE[key]


# ---------------------------------------------------------------- 边缘质量门

def _cell_edge(im):
    """单格 (mid%, hard%, ratio)；空格返回 None。"""
    import numpy as np
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


def _atlas_edge(arr, size, cols, rows):
    import numpy as np
    out = []
    for i in range(cols * rows):
        r, c = divmod(i, cols)
        if (r + 1) * size > arr.shape[0] or (c + 1) * size > arr.shape[1]:
            break
        q = _cell_edge(arr[r * size:(r + 1) * size, c * size:(c + 1) * size])
        if q:
            out.append(q)
    if not out:
        return None
    a = np.array(out)
    return a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean()


def _regen(arr, size, cols, rows, msize):
    """母版逐格 LANCZOS → 目标尺寸（工程既有约定）。"""
    import numpy as np
    from PIL import Image as _I
    canv = np.zeros((rows * size, cols * size, 4), dtype=np.uint8)
    for i in range(cols * rows):
        r, c = divmod(i, cols)
        cell = _I.fromarray(arr[r * msize:(r + 1) * msize, c * msize:(c + 1) * msize])
        canv[r * size:(r + 1) * size, c * size:(c + 1) * size] = np.asarray(
            cell.resize((size, size), _I.Resampling.LANCZOS))
    return canv


def edge_qa(tex, atlas, tolerance, ratio_factor):
    """→ (行 list, 受损 list)。只审有 256 母版的图集。"""
    import numpy as np
    rows, damaged = [], []
    by_atlas = {}
    for (name, size), (fn, cols, rows_n) in atlas.items():
        by_atlas.setdefault(name, {})[size] = (fn, cols, rows_n)
    for name, sized in sorted(by_atlas.items()):
        local = {s: v for s, v in sized.items() if (tex / v[0]).is_file()}
        if len(local) < 2:
            continue
        msize = 256 if 256 in local else max(local)
        mfn, mcols, mrows = local[msize]
        try:
            marr = _load_alpha(tex / mfn)
        except Exception:
            continue
        if marr.shape[:2] != (mrows * msize, mcols * msize):
            continue
        for s in sorted(local):
            fn, cols, rows_n = local[s]
            try:
                arr = _load_alpha(tex / fn)
            except Exception:
                continue
            if arr.shape[:2] != (rows_n * s, cols * s):
                continue
            q = _atlas_edge(arr, s, cols, rows_n)
            if q is None:
                continue
            ref = None
            if s != msize:
                ref = _atlas_edge(_regen(marr, s, cols, rows_n, msize), s, cols, rows_n)
            rows.append((name, s, fn, q, ref, msize if s != msize else None))
            if ref and (q[0] < ref[0] - tolerance or q[2] < ref[2] * ratio_factor):
                damaged.append((name, s, fn, q, ref))
    return rows, damaged


def cell_alpha_px(png_or_dds, size, index, cols):
    """读出图集第 index 格的 alpha>8 像素数（-1 = 越界）。"""
    try:
        a = _load_alpha(png_or_dds)
    except ImportError:
        return None
    except Exception:
        return -1
    r, c = divmod(index, cols)
    if c * size >= a.shape[1] or r * size >= a.shape[0]:
        return -1
    return int((a[r * size:(r + 1) * size, c * size:(c + 1) * size, 3] > 8).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projectRoot")
    ap.add_argument("--icons", nargs="*", default=None, help="Icons XML，缺省自动扫")
    ap.add_argument("--xlp", nargs="*", default=None, help="XLP，缺省扫 <root>/XLPs/*.xlp")
    ap.add_argument("--vanilla", default="", help="官方 Base/Assets/UI/Icons 目录（查重名）")
    ap.add_argument("--min-px", type=int, default=20, help="格子非空阈值（alpha>8 像素数）")
    ap.add_argument("--strict-xlp", action="store_true", help="额外反向检查：XLP 条目是否都有同名 .dds")
    ap.add_argument("--edge-qa", action="store_true",
                    help="边缘抗锯齿质量门：查中间档是否被锐化/对比拉伸破坏（见文件头说明）")
    ap.add_argument("--edge-tolerance", type=float, default=8.0,
                    help="--edge-qa：中间调占比允许低于参考值的百分点（默认 8）")
    ap.add_argument("--edge-ratio", type=float, default=0.7,
                    help="--edge-qa：归一化斜坡宽度允许低于参考值的比例（默认 0.7）")
    args = ap.parse_args()

    root = Path(args.projectRoot)
    tex = root / "Textures"

    icons = args.icons
    if not icons:
        cand = sorted(glob.glob(str(root / "Data" / "*.xml"))) + \
               sorted(glob.glob(str(root / "Mod_Adaptation" / "**" / "*.xml"), recursive=True))
        icons = [p for p in cand if "IconDefinitions" in Path(p).read_text(encoding="utf-8", errors="ignore")]
    xlps = args.xlp or sorted(glob.glob(str(root / "XLPs" / "*.xlp")))

    atlas, defs = {}, {}
    for x in icons:
        try:
            r = ET.parse(x).getroot()
        except Exception as e:
            print(f"  WARN 解析失败 {x}: {e}")
            continue
        t = r.find("IconTextureAtlases")
        for e in (t if t is not None else []):
            atlas[(e.get("Name"), int(e.get("IconSize")))] = (
                e.get("Filename"), int(e.get("IconsPerRow") or 1), int(e.get("IconsPerColumn") or 1))
        t = r.find("IconDefinitions")
        for e in (t if t is not None else []):
            defs[e.get("Name")] = (e.get("Atlas"), int(e.get("Index")))

    fails, warns, checked = [], [], 0
    vanilla_atlas = set()
    print(f"扫描: Icons XML {len(icons)} 个 | 图集行 {len(atlas)} | 图标定义 {len(defs)}")

    dds_cache = {}
    for name, (aname, idx) in sorted(defs.items()):
        if aname not in {a for a, _ in atlas}:
            # 图集行不在本工程 Icons XML 里 = 复用原版/DLC 注册的图集（合法用法），跳过格子检查
            vanilla_atlas.add(aname)
            continue
        for (a, s) in sorted(k for k in atlas if k[0] == aname):
            fn, cols, rows = atlas[(a, s)]
            if not fn.endswith(".dds"):
                fn += ".dds"
            p = tex / fn
            if not p.is_file():
                fails.append(f"{name} @{s}: 缺文件 {fn}")
                continue
            if fn not in dds_cache:
                dds_cache[fn] = dds_header(p)
            hdr = dds_cache[fn]
            if hdr is None:
                fails.append(f"{fn}: 不是合法 DDS")
                continue
            w, h, mips, rgba = hdr
            if (w, h) != (cols * s, rows * s):
                fails.append(f"{fn}: 画布 {w}x{h} != IconsPerRow*size x IconsPerColumn*size "
                             f"({cols}*{s} x {rows}*{s})")
            if mips != 1:
                fails.append(f"{fn}: mips={mips}（必须 1，.tex 是 bUseMips=false）")
            if not rgba:
                warns.append(f"{fn}: 像素格式不是 R8G8B8A8（掩码非 ff/ff00/ff0000/ff000000）")
            tp = tex / (fn[:-4] + ".tex")
            if not tp.is_file():
                fails.append(f"{fn}: 缺同名 .tex（AssetEditor 必需）")
            else:
                twh = tex_wh(tp)
                if twh and twh != (w, h):
                    fails.append(f"{tp.name}: .tex {twh[0]}x{twh[1]} != DDS {w}x{h}")
            n = cell_alpha_px(p, s, idx, cols)
            if n is None:
                warns.append(f"{fn}: 未装 Pillow，跳过空格检查")
            elif n < 0:
                fails.append(f"{name} @{s}: Index={idx} 超出 {cols}x{rows} 网格（挪位/越界）")
            elif n < args.min_px:
                fails.append(f"{name} @{s}: 格子几乎为空（alpha>8 只有 {n}px）-> 运行时图标会是空白")
            checked += 1

    print(f"\n图标解析检查: {checked} 个 (定义 x 尺寸档)")
    if vanilla_atlas:
        _v = sorted(vanilla_atlas)
        print(f"  复用原版/DLC 图集的条目已跳过（{len(_v)} 个图集）: "
              + ", ".join(_v[:6]) + (" ..." if len(_v) > 6 else ""))
    for m in warns:
        print(f"  WARN {m}")

    print(f"XLP 检查: {len(xlps)} 个文件（只认 m_ClassName=UITexture 的）")
    xlp_entries, xlp_n = set(), 0
    for x in xlps:
        try:
            r = ET.parse(x).getroot()
        except Exception:
            continue
        cls = r.find("m_ClassName")
        if (cls is None) or (cls.get("text") != "UITexture"):
            continue
        for e in (r.find("m_Entries") if r.find("m_Entries") is not None else []):
            eid = e.find("m_EntryID")
            if eid is not None and eid.get("text"):
                xlp_entries.add(eid.get("text"))
                xlp_n += 1
    # 正向检查：图集引用的每个贴图都必须在某个 UITexture XLP 里登记，否则不会被 cook 进包
    atlas_files = sorted({(fn[:-4] if fn.endswith(".dds") else fn)
                          for (fn, _c, _r) in atlas.values()})
    unreg = [f for f in atlas_files if f not in xlp_entries]
    print(f"  UITexture 条目共 {xlp_n} 条；图集引用贴图 {len(atlas_files)} 个，"
          f"未登记 {len(unreg)} 个")
    for f in unreg:
        fails.append(f"{f}.dds 被 IconTextureAtlases 引用，但没有任何 UITexture XLP 登记它 -> 不会被打进 UI/Icons 包")
    if getattr(args, "strict_xlp", False):
        n_dds = 0
        for e in sorted(xlp_entries):
            if (tex / (e + ".dds")).is_file():
                n_dds += 1
            else:
                fails.append(f"XLP 条目 {e} 在 Textures/ 下没有同名 .dds（--strict-xlp）")

    # ---- 边缘质量门
    if args.edge_qa:
        try:
            rows, damaged = edge_qa(tex, atlas, args.edge_tolerance, args.edge_ratio)
        except ImportError:
            print("\n边缘质量门: 未装 Pillow/numpy，跳过")
            rows, damaged = [], []
        print(f"\n边缘质量门 (--edge-qa): 审查 {len(rows)} 档"
              f"（mid=边界中间调占比% / ratio=过渡像素÷周长；参考值=母版逐格 LANCZOS 重出）")
        if rows:
            print(f"  {'图集':<32} {'档':>4} {'中间调%':>8} {'硬跳%':>7} {'比值':>7} |"
                  f" {'参考 中间调/比值':>17} | {'判定':>8}")
            for name, s, fn, q, ref, ms in rows:
                refs = f"{ref[0]:7.1f}% {ref[2]:6.2f}" if ref else ""
                bad = any(d[0] == name and d[1] == s for d in damaged)
                verdict = "DAMAGED" if bad else ("ok" if ref else "母版")
                print(f"  {name:<32} {s:>4} {q[0]:8.1f} {q[1]:7.1f} {q[2]:7.2f} |"
                      f" {refs:>17} | {verdict:>8}")
        for name, s, fn, q, ref in damaged:
            fails.append(
                f"{fn} @{s}: 边缘抗锯齿受损（中间调 {q[0]:.1f}% < 参考 {ref[0]:.1f}%，"
                f"过渡/周长 {q[2]:.2f} < 参考 {ref[2]:.2f}）"
                f" -> 用 regen_atlas_tiers.py 从母版重出")
        if not damaged and rows:
            print("  全部档位边缘质量正常。")



    if args.vanilla:
        van = set()
        for f in glob.glob(os.path.join(args.vanilla, "*.xml")):
            try:
                r = ET.parse(f).getroot()
            except Exception:
                continue
            for sec in ("IconDefinitions", "IconTextureAtlases"):
                el = r.find(sec)
                for e in (el if el is not None else []):
                    van.add(e.get("Name"))
        clash = sorted(n for n in defs if n in van)
        print(f"\n与官方重名检查: {'无' if not clash else clash}")
        if clash:
            fails.append(f"自定义 IconDefinitions 与官方重名: {clash}")

    print()
    if fails:
        print(f"FAIL: {len(fails)} 项")
        for m in fails:
            print(f"  x {m}")
        return 1
    print("PASS: 全部通过（引用闭合 / 画布与网格一致 / mips=1 / 格子非空 / .tex 对齐 / XLP 无悬空）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
