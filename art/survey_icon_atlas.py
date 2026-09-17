#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""survey_icon_atlas.py — 按 `art-pipeline.md` §4.7 流程，「量出」某图标类别的规范

## 解决什么问题

`normalize_icon.py` 的 `ICON_SPECS` 里只预填了 4 个类别（unit/building/project/improvement）；
其余类别**故意留空**，需要时按 §4.7 的六步流程**实测**出 `canvas` / `content` / `outline`，
而不是拍脑袋填数。§4.7 描述得很清楚，但此前**没有一个脚本能一键完成第 2~5 步**
（切格 → 量占幅 → 量描边 → 校准），只能手写一次性脚本 —— 本工具补上这一环。

## 与 slice_atlas.py 的分工

| 工具 | 用途 |
|---|---|
| `civ6-asset-forge/scripts/slice_atlas.py` | 把**晋升**图集切格导出 PNG（做 ground truth 对照用） |
| **本工具** | **任意**图集：切格 + 量占幅分布 + 量描边剖面 + 给出建议 spec（喂 `ICON_SPECS`） |

## 六步流程对应

1. 拿原版图集 → 用 `--atlas` 指定（pantry 的 `Buildings256.dds` 等）
2. 切格 → 按 `--grid RxC`（默认 8x8）行优先切
3. 量占幅 → 每格 `alpha>8` 的 bbox 最长边占比 → min/p10/中位/p90/max
4. 量描边 → 对 `alpha>128` 做距离变换，统计距边界第 d 圈的亮度与 **逐通道 RGB 均值**
5. 校准 → 给出建议 `outline.px`（亮度≈描边色的最大 d）
6. 固化 → 输出可直接粘进 `ICON_SPECS` 的片段（`status="verified"`）

## 用法

    # 体检一个图集（默认 8x8 网格）
    python survey_icon_atlas.py --atlas "<pantry>/Buildings256.dds" --role building_icon

    # 指定网格与最小非空格阈值
    python survey_icon_atlas.py --atlas Dist256.dds --grid 4x4 --min-px 20

    # 只量占幅（跳过描边，快）
    python survey_icon_atlas.py --atlas X.dds --no-outline

    # 输出可直接粘进 ICON_SPECS 的片段
    python survey_icon_atlas.py --atlas X.dds --role district_icon --emit-spec

退出码：0 成功 / 1 参数或读取错误。
依赖：Pillow + numpy + scipy（distance_transform_edt；缺 scipy 时描边步骤降级为粗略近似）。
"""
import argparse
import os
import re
import sys

import numpy as np
from PIL import Image

try:
    from scipy import ndimage as ndi
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ALPHA_FLOOR = 8      # 「有内容」阈值
ALPHA_SOLID = 128    # 「实体」阈值（量描边用）


def load_rgba(path):
    """PNG/DDS 都能读成 RGBA ndarray。"""
    im = Image.open(path)
    im.load()
    return np.asarray(im.convert("RGBA"))


def slice_cells(arr, rows, cols, size=None):
    """行优先切格 → [(index, row, col, cell_ndarray)]。size 缺省按画布/网格推断。"""
    H, W = arr.shape[:2]
    ch, cw = H // rows, W // cols
    if cw * cols != W or ch * rows != H:
        print("  WARN 画布 %dx%d 不是网格 %dx%d 的整数倍；按整除尺寸切，右侧/底部余量丢弃"
              % (W, H, cols, rows))
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append((r * cols + c, r, c, arr[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]))
    return cells, cw, ch


def measure_extent(cell):
    """→ (bbox, 覆盖率, 最长边占比) 或 None（空格）。"""
    a = cell[..., 3]
    mask = a > ALPHA_FLOOR
    if mask.sum() < 1:
        return None
    ys, xs = np.nonzero(mask)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    canvas = max(cell.shape[0], cell.shape[1])
    return (int(x0), int(y0), int(x1), int(y1)), mask.mean(), max(bw, bh) / float(canvas)


def measure_outline(cell, max_d=12):
    """量描边：距 alpha 边界第 d 圈的亮度与逐通道 RGB 均值。

    → list of dict(d=1..max_d, n=像素数, lum=亮度均值, rgb=[r,g,b])
    """
    a = cell[..., 3]
    solid = a > ALPHA_SOLID
    if solid.sum() < 1:
        return []
    if HAVE_SCIPY:
        # 到「外部」的距离：先把外部（非 solid）标记，再算距离
        dist_out = ndi.distance_transform_edt(solid)
    else:
        # 退化近似：用简单腐蚀层数代替
        dist_out = np.zeros(solid.shape, dtype=float)
        cur = solid.copy()
        for d in range(1, max_d + 1):
            nxt = cur.copy()
            nxt[1:, :] &= cur[:-1, :]
            nxt[:-1, :] &= cur[1:, :]
            nxt[:, 1:] &= cur[:, :-1]
            nxt[:, :-1] &= cur[:, 1:]
            dist_out[nxt & (dist_out == 0)] = d
            cur = nxt
    rgb = cell[..., :3].astype(float)
    lum = rgb.mean(axis=2)
    out = []
    for d in range(1, max_d + 1):
        if HAVE_SCIPY:
            ring = (dist_out >= d) & (dist_out < d + 1)
        else:
            ring = (np.floor(dist_out) == d)
        n = int(ring.sum())
        if n == 0:
            out.append(dict(d=d, n=0, lum=None, rgb=None))
            continue
        out.append(dict(d=d, n=n,
                        lum=float(lum[ring].mean()),
                        rgb=[round(float(x), 1) for x in rgb[ring].reshape(-1, 3).mean(axis=0)]))
    return out


def pct(vals, p):
    return float(np.percentile(vals, p)) if vals else float("nan")


def main():
    ap = argparse.ArgumentParser(description="按 art-pipeline §4.7 量出图标类别规范")
    ap.add_argument("--atlas", required=True, help="原版图集 PNG/DDS 路径")
    ap.add_argument("--grid", default="8x8", help="网格 ROWSxCOLS（默认 8x8）")
    ap.add_argument("--role", default="", help="类别名（用于生成 ICON_SPECS 片段）")
    ap.add_argument("--min-px", type=int, default=8, help="格内 alpha>8 像素数低于此视为空格")
    ap.add_argument("--max-outline-d", type=int, default=10, help="描边最大探测圈数")
    ap.add_argument("--no-outline", action="store_true", help="跳过描边测量（更快）")
    ap.add_argument("--emit-spec", action="store_true", help="输出可粘进 ICON_SPECS 的片段")
    a = ap.parse_args()

    if not os.path.isfile(a.atlas):
        print("图集不存在：%s" % a.atlas)
        return 1
    m = re.fullmatch(r"(\d+)\s*[xX]\s*(\d+)", a.grid.strip())
    if not m:
        print("--grid 需形如 8x8")
        return 1
    rows, cols = int(m.group(1)), int(m.group(2))

    arr = load_rgba(a.atlas)
    cells, cw, ch = slice_cells(arr, rows, cols)
    print("=" * 74)
    print("图集：%s" % a.atlas)
    print("画布：%dx%d   网格：%dx%d   单格：%dx%d   共 %d 格"
          % (arr.shape[1], arr.shape[0], rows, cols, cw, ch, len(cells)))
    print("=" * 74)

    extents, nonempty, empties = [], [], []
    for idx, r, c, cell in cells:
        if (cell[..., 3] > ALPHA_FLOOR).sum() < a.min_px:
            empties.append(idx)
            continue
        box, cov, longest = measure_extent(cell)
        extents.append(longest)
        nonempty.append((idx, r, c, box, cov, longest))

    if not nonempty:
        print("无有效格（检查 --grid / --min-px）")
        return 1

    print()
    print("① 占幅（内容最长边 ÷ 单格边长）—— 共 %d 个非空格，空 %d 格"
          % (len(nonempty), len(empties)))
    print("   min=%.1f%%  p10=%.1f%%  中位=%.1f%%  p75=%.1f%%  p90=%.1f%%  max=%.1f%%"
          % (pct(extents, 0) * 100, pct(extents, 10) * 100, pct(extents, 50) * 100,
             pct(extents, 75) * 100, pct(extents, 90) * 100, pct(extents, 100) * 100))
    if empties:
        print("   空格序号（前 20）：%s" % empties[:20])

    # 细高/细宽子族
    ratios = []
    for idx, r, c, box, cov, longest in nonempty:
        bw, bh = box[2] - box[0] + 1, box[3] - box[1] + 1
        ratios.append(min(bw, bh) / float(max(bw, bh)))
    slender = [x for x in ratios if x <= 0.65]
    print("   长短边比：min=%.2f 中位=%.2f ; 细高/细宽(<=0.65) 占比 %.0f%%"
          % (min(ratios), pct(ratios, 50), len(slender) / len(ratios) * 100))

    # 中位占幅 → 建议 content
    med = pct(extents, 50)
    canvas = cw
    suggest_content = int(round(med * canvas))
    print("   → 建议 content = %d（中位 %.1f%% × 单格 %d）" % (suggest_content, med * 100, canvas))
    print("     偏满档（p90）= %d" % int(round(pct(extents, 90) * canvas)))

    outline_px, outline_rgb = None, None
    if not a.no_outline:
        print()
        print("② 描边（距离 alpha 边界第 d 圈的亮度/逐通道 RGB 均值）")
        print("   %-4s %-8s %-9s %s" % ("d", "像素数", "亮度", "RGB 均值"))
        # 用前若干个非空格做统计（全量太慢）
        sample = nonempty[:min(12, len(nonempty))]
        cell_by_idx = {i: cl for i, _r, _c, cl in cells}
        per_d = {}
        for idx, r, c, box, cov, longest in sample:
            cell = cell_by_idx[idx]
            prof = measure_outline(cell, a.max_outline_d)
            for e in prof:
                if e["n"] == 0:
                    continue
                per_d.setdefault(e["d"], []).append((e["lum"], e["rgb"]))
        dark_ds = []
        for d in sorted(per_d):
            lums = [x[0] for x in per_d[d]]
            rgbs = np.array([x[1] for x in per_d[d]])
            lum = float(np.mean(lums))
            rgb = [round(float(x), 1) for x in rgbs.mean(axis=0)]
            print("   %-4d %-8d %-9.1f %s" % (d, len(lums), lum, rgb))
            # 描边圈 = 明显偏暗的连续圈
            if lum < 90:
                dark_ds.append(d)
        if dark_ds:
            # 取从 1 开始连续偏暗的最大 d 作为**起点估计**
            run = 0
            for d in dark_ds:
                if d == run + 1:
                    run = d
                else:
                    break
            outline_px = run if run else max(dark_ds)
            base = per_d.get(min(dark_ds, key=lambda x: abs(x - 2)), per_d[dark_ds[0]])
            outline_rgb = [int(round(x)) for x in np.array([x[1] for x in base]).mean(axis=0)]
            print()
            print("   → outline.px **起点估计** = %d ；outline.rgb = %s" % (outline_px, outline_rgb))
            print("     （§4.7 第 4 步：务必按**通道**取，别只看亮度——"
                  "项目图是藏青 (0,25,45) 不是黑）")
            print("     ⚠ 这**只是起点**，不是最终值。§4.7 第 5 步要求把该 px 喂给")
            print("       normalize_icon.py 的引擎、扫 ±2px，取「深度-亮度剖面最贴原版」的")
            print("       那个值 —— 实测 building_icon 的起点估计是 5、校准后定为 **6**。")
        else:
            print("   未发现明显偏暗的描边圈（该类别可能无描边）")

    if a.emit_spec:
        print()
        print("③ 可粘进 normalize_icon.py 的 ICON_SPECS 片段")
        print("   （content 可直接用；**outline.px 需按 §4.7 第 5 步校准后再定稿**）")
        print()
        role = a.role or "<role>"
        print('    "%s": {' % role)
        print('        "canvas": %d, "content": %d, "color": None,' % (canvas, suggest_content))
        if outline_px and outline_rgb:
            print('        "outline": {"px": %d, "rgb": %s},' % (outline_px, outline_rgb))
        print('        "status": "verified",')
        print('        "source": "%s 全 %d 格实测(%s)",'
              % (os.path.basename(a.atlas), len(nonempty), "2026-09-17"))
        print('        "note": "最长边 min=%.1f%% p50=%.1f%% p90=%.1f%%；细高/细宽占 %.0f%%",'
              % (pct(extents, 0) * 100, med * 100, pct(extents, 90) * 100,
                 len(slender) / len(ratios) * 100))
        print("    },")
        print()
        print("  固化后请在 art-pipeline.md 第四节回填，并标 status=\"verified\"。")

    print()
    print("完成。（scipy %s）" % ("可用" if HAVE_SCIPY else "缺失，描边为粗略近似"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
