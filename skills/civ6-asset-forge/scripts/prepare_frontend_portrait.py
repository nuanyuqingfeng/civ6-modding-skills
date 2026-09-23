#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""prepare_frontend_portrait.py — 原版 FrontEnd 前景/背景的**整理与接线**

配套 `reference/frontend-portrait.md`（类别⑦）。

## 〇、总规则（`SKILL.md` §1.0）

本工具**只做既有工具能胜任的简单操作**：**裁剪**（含等比缩放、居中）、
**通道透明度**（读 alpha、阈值）、**描边**，以及复制/改名/格式转换。
**不做**任何"把图改好"的处理（重绘、修补、重着色、调色、生成式补图、迭代调参）。

- 素材不满足要求 → **停下询问用户**（不自行尝试）。
- **两段式执行**：先出**计划**（默认，不写盘）→ 用户确认 → 再 `--write --confirmed`。
- 不覆盖工程已有贴图。

## 一、像素构成分类

分析 alpha 通道，把素材分成三类（判据在 `示例工程` 6 位领袖 × 3 类素材上实测可复现）：

| 类别 | 判据 | 处理 |
|---|---|---|
| **① 人物抠图** | 透明像素 ≥ `--subject-min-transp`（默认 40%） | 定内容框 → 缩到高 1024 → **底部对齐** → 按内容定宽居中 → `LEADER_<KEY>_NEUTRAL` |
| **② 满幅图** | 透明 ≤ `--bleed-max-transp`（默认 5%） | **空白前景（显式空串）+ 铺满背景** → `LEADER_<KEY>_BACKGROUND` |
| **③ 中间地带** | 其余 | **停下问用户**（exit 3），用 `--force-subject` / `--force-bleed` 表明裁决 |

实测参考（`示例工程`）：人物抠图透明率 60~74%、满幅图 ~0%。

## 二、分支②「空白前景」的正确写法（极易写错）

`PlayerSetupLogic.lua:807-829` 是 `if info.Portrait then ... else ... end`：

| SQL 取值 | Lua 值 | 行为 |
|---|---|---|
| 贴图名 | 非空串 | 直接用 |
| `''`（空串） | `""` —— **Lua 里 truthy** | `SetTexture("")` → **真空白，且短路回退** ✔ 本分支要的就是这个 |
| `NULL` | `nil`（falsy） | 走回退 → `<LeaderType>_NEUTRAL`（mod 通常没有 → 空白**且不报错**） |

→ **分支②必须写显式空串 `''`，不能写 NULL**。

## 三、背景获取顺序（分支① 需要背景时，严格降级）

1. **工程约定文件**：`PORTRAIT_<KEY>_BACKGROUND` → `IMG_LEADER_<KEY>_DIPLOMACY_BACKGROUND`
   → `IMG_LOADING_BACKGROUND_<KEY>` → `LEADER_<KEY>_BACKGROUND`
2. **`--bg-dir`**：目录内文件名含领袖名片段（模糊匹配）
3. **色系回退**：用 `pick_vanilla_background` 的调色板，以**人物抠图的加权圆平均色相**为参考挑官方背景；
   **仅当 Δh ≤ 60°** 才自动采用（否则判"不相似"，停下问用户）
4. 都失败 → 报缺失，**不静默编造**

## 四、命名（以官方为准；不动工程既有文件）

| 产物 | 命名 | 说明 |
|---|---|---|
| 前景 | `LEADER_<KEY>_NEUTRAL` | 官方约定（选人 placard 与加载界面**共用**） |
| 加载界面背景 | `LEADER_<KEY>_BACKGROUND` | 官方约定；**高 ≥960**（960 是基准、非上限） |
| placard 竖版背景 | `LEADER_<KEY>_PLACARD_BACKGROUND` | 官方无此物（官方直接拿 1920×960 去凑），故取官方前缀 + 语义后缀 |

> 本工程既有的 `PORTRAIT_*` / `IMG_LOADING_*` **不做重构**（仅被当作"①工程约定文件"读取）。

## 用法

    # ① 分类 + 预演（不写盘）—— 先看它被判成哪类、会产出什么
    python prepare_frontend_portrait.py --project <工程根> --leader LEADER_X_QYQXP \
        --image <素材.png>

    # ② 落盘
    python prepare_frontend_portrait.py --project <工程根> --leader LEADER_X_QYQXP \
        --image <素材.png> --write

    # ③ 中间地带由用户裁决后强制指定
    ... --force-subject --write      # 或 --force-bleed

    # ④ 批量（目录内文件名需含领袖名片段）
    python prepare_frontend_portrait.py --project <工程根> --image-dir <目录> --write

退出码：0 成功 / 1 错误 / **2 告警** / **3 需用户裁决**（分类中间地带 或 背景不相似）。
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_SKILLS = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_SKILLS, "civ6-modding", "art"))

try:
    from dds_io import read_dds, write_dds            # noqa: E402
    from PIL import Image                              # noqa: E402
except ImportError as e:                               # pragma: no cover
    print("需要 Pillow，且需能找到 civ6-modding/art/dds_io.py：%s" % e)
    raise SystemExit(1)

# 同目录兄弟脚本复用（不重复实现：bbox/定宽工艺、调色板/挑选、XLP 别名）
from gen_suk_portrait import (                         # noqa: E402
    alpha_bbox, make_portrait, load_any, _match_in_dir, tex_text,
    PORTRAIT_H, ALPHA_THR,
)
from pick_vanilla_background import (                  # noqa: E402
    image_stats, rank, load_palette, insert_alias, xlp_path,
    luminance, hue_distance, DEFAULT_PACKS,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# placard 竖版背景控件尺寸（reference/frontend-portrait.md §1.3 推导）
PLACARD_BG = (328, 935)
# 加载界面背景**基准**高（官方基线 1920×960；960 是基准不是上限）
LOADING_BASE_H = 960
LOADING_TARGET = (1920, 1080)     # 本项目实测良好的档位（16:9 零裁切）

EXIT_OK, EXIT_ERR, EXIT_WARN, EXIT_ASK = 0, 1, 2, 3


class NeedsDecision(Exception):
    """需要用户裁决才能继续（§1.0 总规则：不自行尝试复杂处理）。"""


# ---------------------------------------------------------------- 分类

def classify(img, subject_min_transp=40.0, bleed_max_transp=5.0):
    """→ (kind, stats)。kind ∈ {'subject','bleed','middle'}。

    判据（alpha 通道）：
      - 透明像素（alpha<=5）占比 ≥ subject_min_transp → 'subject'（人物抠图）
      - 透明占比 ≤ bleed_max_transp 且不透明（alpha>=250）占比 ≥ 90 → 'bleed'（满幅图）
      - 其余 → 'middle'（需用户裁决）
    """
    w, h = img.size
    a = img.getchannel("A")
    hist = a.histogram()
    total = float(w * h)
    transp = sum(hist[:6]) / total * 100.0
    opaque = sum(hist[250:]) / total * 100.0
    bb = a.getbbox()
    touches = 0
    if bb:
        touches = sum([bb[0] <= 1, bb[1] <= 1, bb[2] >= w - 1, bb[3] >= h - 1])
    st = dict(size=(w, h), transp=round(transp, 1), opaque=round(opaque, 1),
              bbox=bb, touches=touches)
    if transp >= subject_min_transp:
        return "subject", st
    if transp <= bleed_max_transp and opaque >= 90.0:
        return "bleed", st
    return "middle", st


# ---------------------------------------------------------------- 背景获取

PROJ_BG_PATTERNS = (
    "PORTRAIT_%s_BACKGROUND",           # 本工程既有竖版（328×935）
    "IMG_LEADER_%s_DIPLOMACY_BACKGROUND",
    "IMG_LOADING_BACKGROUND_%s",
    "LEADER_%s_BACKGROUND",
)


def find_project_bg(textures_dir, key):
    """① 工程约定文件（返回 (贴图名, 路径) 或 (None,None)）。"""
    for pat in PROJ_BG_PATTERNS:
        nm = pat % key
        for ext in (".dds", ".tex"):
            fp = os.path.join(textures_dir, nm + ext)
            if os.path.isfile(fp):
                return nm, fp
    return None, None


def official_bg_for_hue(ref_img, packs=DEFAULT_PACKS, max_dh=60.0):
    """③ 色系回退：→ (候选 dict 或 None, 是否相似)。

    以 ref_img 的加权圆平均色相为参考，挑官方背景；Δh > max_dh 判为不相似。
    """
    try:
        palette = load_palette()
    except Exception as e:
        print("WARN 调色板不可用：%s" % e, file=sys.stderr)
        return None, False
    ref = image_stats_of(ref_img)
    rows = rank(palette, ref, tuple(packs), 1)
    if not rows:
        return None, False
    top = rows[0]
    return top, bool(top["d_hue"] is not None and top["d_hue"] <= max_dh)


def image_stats_of(img):
    """直接对内存图像算 image_stats（避免落盘）。"""
    tmp = img.convert("RGBA")
    # 复用 pick_vanilla_background.image_stats 的算法，但走内存
    import math
    import cmath
    import colorsys
    im = tmp.convert("RGB")
    im.thumbnail((96, 96), Image.LANCZOS)
    px = list(im.getdata())
    n = len(px)
    acc = 0j
    wsum = 0.0
    for (r, g, b) in px:
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        wgt = ss * vv
        if wgt < 0.02:
            continue
        acc += wgt * cmath.exp(1j * math.radians(hh * 360.0))
        wsum += wgt
    hue = (math.degrees(cmath.phase(acc)) % 360.0) if wsum > 0 else 0.0
    return {"hue": round(hue, 1),
            "mean": [sum(p[0] for p in px) // n,
                     sum(p[1] for p in px) // n,
                     sum(p[2] for p in px) // n]}


# ---------------------------------------------------------------- 处理

def make_loading_bg(img):
    """加载界面背景：**只做等比缩放 + 居中裁剪**（§1.0 总规则允许的操作）。

    目标 1920×1080；源图高必须 ≥960（基准）。
    **若源图不够宽**（缩放后宽 < 1920），纯裁剪/缩放无法铺满 —— 不补边、不合成，
    直接抛 `NeedsDecision` 交用户（补边属"把图改好"，超出本 skill 范围）。
    """
    w, h = img.size
    tw, th = LOADING_TARGET
    if h < LOADING_BASE_H:
        raise NeedsDecision(
            "源图高 %d < 基准 %d：加载界面背景高度不足会有两侧裁剪风险。"
            "请提供高度 ≥%d 的素材（或明确授权如何处理）。"
            % (h, LOADING_BASE_H, LOADING_BASE_H))
    scale = th / float(h)
    nw = max(1, int(round(w * scale)))
    if nw < tw:
        raise NeedsDecision(
            "源图 %dx%d 按高缩放到 %d 后宽仅 %d < 目标宽 %d：纯裁剪/缩放无法铺满，"
            "补边属「把图改好」超出本 skill 范围。请提供更宽的素材，或指定处理方式。"
            % (w, h, th, nw, tw))
    x0 = (nw - tw) // 2
    return inter_crop(img, scale, x0, th, tw), dict(mode="crop", src="%dx%d" % (w, h), crop_x=x0)


def inter_crop(img, scale, x0, th, tw):
    nw = max(1, int(round(img.size[0] * scale)))
    inter = img.resize((nw, th), Image.LANCZOS)
    return inter.crop((x0, 0, x0 + tw, th))


def make_placard_bg(src_img):
    """placard 竖版背景：**只做等比缩放 + 居中裁剪**得到 328×935（§1.0 总规则允许）。"""
    tw, th = PLACARD_BG
    w, h = src_img.size
    scale = max(tw / float(w), th / float(h))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    inter = src_img.resize((nw, nh), Image.LANCZOS)
    x0 = (nw - tw) // 2
    return inter.crop((x0, 0, x0 + tw, th)), dict(scale=round(scale, 3))


def emit(files, name, img, check, report=None):
    """写 dds + tex（.tex 为 LF）。**已存在的贴图不覆盖** → 交用户裁决。"""
    dds = os.path.join(files["textures"], name + ".dds")
    if os.path.isfile(dds):
        raise NeedsDecision(
            "目标贴图 %s 已存在 —— 本 skill 不覆盖已有素材（除非用户明确授权）。"
            "请改名、移走旧图，或明确指示覆盖。" % os.path.basename(dds))
    if not check:
        write_dds(os.path.join(files["textures"], name + ".dds"), img)
        with open(os.path.join(files["textures"], name + ".tex"),
                  "w", encoding="utf-8", newline="\n") as f:
            f.write(tex_text(name, img.size[0], img.size[1]))


# ---------------------------------------------------------------- 主流程

def find_project_root_civ6proj(root):
    hits = glob.glob(os.path.join(root, "*.civ6proj"))
    return hits[0] if hits else None


def plan_one(root, lt, image_path, check, forced, bg_dir, packs, args, report, wiring):
    key = lt[len("LEADER_"):] if lt.startswith("LEADER_") else lt
    textures_dir = os.path.join(root, "Textures")
    img = load_any(image_path)
    kind, st = classify(img, args.subject_min_transp, args.bleed_max_transp)
    if forced:
        kind = forced
    report.append("  %s ← %s" % (lt, os.path.basename(image_path)))
    report.append("     尺寸 %dx%d · 透明 %s%% · 不透明 %s%% · 触边 %d → **%s**"
                  % (st["size"][0], st["size"][1], st["transp"], st["opaque"],
                     st["touches"],
                     {"subject": "人物抠图", "bleed": "满幅图",
                      "middle": "中间地带(需裁决)"}[kind]))

    if kind == "middle":
        report.append("     ⛔ 像素构成落在中间地带（透明 %s%%），**需用户裁决**："
                      % st["transp"])
        report.append("        是人物抠图（有透明背景、主体孤立）？→ 加 --force-subject")
        report.append("        是满幅画面（无透明、铺满画布）？→ 加 --force-bleed")
        return EXIT_ASK

    fg_name = "LEADER_%s_NEUTRAL" % key
    # placard 与 loading 的背景**来源不同、尺寸不同**，必须分开取：
    #   placard 要竖版 328×935；loading 要 ≥960 高（同一张竖版会因 935<960 被裁）
    placard_bg, loading_bg = acquire_bgs(root, textures_dir, key, img, bg_dir,
                                         packs, args, report, check)

    if kind == "subject":
        # ① 人物抠图：定内容框 → 高 1024 → 底部对齐 → 内容定宽居中
        out, meta = make_portrait(img)
        report.append("     前景 → %s（%dx%d，内容宽 %d，裁切 %d）"
                      % (fg_name, out.size[0], out.size[1], meta["content_w"],
                         meta["clipped"]))
        emit({"textures": textures_dir}, fg_name, out, check)
        portrait = fg_name
        loading_fg = fg_name
    else:
        # ② 满幅图：空白前景（显式空串！）
        report.append("     前景 → '' （**显式空串**：Lua 空串 truthy → 真空白且短路回退；"
                      "写 NULL 会回退到不存在的 _NEUTRAL）")
        portrait = "''"
        loading_fg = "''"

    if placard_bg is None:
        report.append("     ⛔ placard 背景未定 → **需用户裁决**（--pick / --bg-dir）")
        return EXIT_ASK
    if loading_bg is None and loading_fg != "''":
        report.append("     ⚠ 加载界面背景缺失 → 该领袖加载界面会回退到 "
                      "LEADER_%s_BACKGROUND（不存在则空白+DataError）" % key)

    wiring[lt] = dict(portrait=portrait, placard_bg=placard_bg,
                      loading_fg=loading_fg,
                      loading_bg=loading_bg or ("LEADER_%s_BACKGROUND" % key))
    report.append("     接线：Players.Portrait = %s" % portrait)
    report.append("           Players.PortraitBackground = %s" % placard_bg)
    report.append("           LoadingInfo.ForegroundImage = %s" % loading_fg)
    report.append("           LoadingInfo.BackgroundImage = %s" % wiring[lt]["loading_bg"])
    return EXIT_OK


def _xlp_index(root):
    """→ (所有 EntryID 集合, 别名 dict[EntryID→ObjectName])。"""
    ids, alias = set(), {}
    for xp in glob.glob(os.path.join(root, "XLPs", "*.xlp")):
        try:
            t = open(xp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in re.finditer(
                r'<m_EntryID text="([^"]*)"\s*/>\s*<m_ObjectName text="([^"]*)"\s*/>', t):
            ids.add(m.group(1))
            if m.group(1) != m.group(2):
                alias[m.group(1)] = m.group(2)
    return ids, alias


def _ensure_alias(root, xlp_name, entry_id, object_name, check, report):
    """在工程 XLP 里**幂等**登记别名 EntryID → ObjectName（官方命名 + 引用官方贴图）。

    → True 表示 entry_id 可解析（已存在或已写入/将写入）。
    """
    xp = xlp_path(root, xlp_name)
    if not xp:
        report.append("     ⚠ 工程 XLPs/ 下找不到 %s → 别名 %s 未登记（需手工补）"
                      % (xlp_name, entry_id))
        return False
    try:
        st = insert_alias(xp, entry_id, object_name, write=not check)
    except SystemExit as e:
        report.append("     ⚠ 登记别名失败：%s" % e)
        return False
    report.append("     XLP %s：%s → %s（%s）"
                  % (os.path.basename(xp), entry_id, object_name,
                     "已存在" if st == "exists" else ("将写入" if check else "已写入")))
    return True


# placard 竖版背景（本工程既有形态，328×935）
PLACARD_BG_PATTERNS = ("PORTRAIT_%s_BACKGROUND",)
# 加载界面背景（宽幅，高 ≥960）
LOADING_BG_PATTERNS = ("IMG_LOADING_BACKGROUND_%s",
                       "LEADER_%s_BACKGROUND",
                       "IMG_LEADER_%s_DIPLOMACY_BACKGROUND")


def _find_by_patterns(textures_dir, key, patterns):
    for pat in patterns:
        nm = pat % key
        for ext in (".dds", ".tex"):
            fp = os.path.join(textures_dir, nm + ext)
            if os.path.isfile(fp):
                return nm, fp
    return None, None


def acquire_bgs(root, textures_dir, key, ref_img, bg_dir, packs, args, report, check):
    """取两种背景 → (placard_bg, loading_bg)。两个目标**各自独立**取源。

    两者尺寸要求不同，**不能共用一个源**：
      placard : 竖版 328×935
      loading : 宽幅，高 ≥960

    降级顺序：
      loading : ① 工程 IMG_LOADING_* / LEADER_*_BACKGROUND → ② --bg-dir（**高 ≥960 才可用**）
                → ③ --pick → ④ 色系回退 → ⑤ 缺失
      placard : ① 工程 PORTRAIT_* 竖版 → ② --bg-dir（能裁出 328×935 即用）
                → ③ 由 loading 工程源 cover → ④ 停下询问
    """
    p_nm, _ = _find_by_patterns(textures_dir, key, PLACARD_BG_PATTERNS)
    l_nm, l_fp = _find_by_patterns(textures_dir, key, LOADING_BG_PATTERNS)

    # --bg-dir 里可能同时匹配到多张（竖版/宽幅），逐个按尺寸归位
    bg_candidates = []
    if bg_dir:
        for fn in sorted(os.listdir(bg_dir)) if os.path.isdir(bg_dir) else []:
            if fn.lower().endswith((".png", ".jpg", ".jpeg", ".dds")) and key.lower() in fn.lower():
                bg_candidates.append(os.path.join(bg_dir, fn))
    bg_for_placard = None
    bg_for_loading = None
    for c in bg_candidates:
        try:
            im = load_any(c)
        except Exception:
            continue
        w, h = im.size
        if bg_for_loading is None and h >= LOADING_BASE_H:
            bg_for_loading = (c, im)
        if bg_for_placard is None and h >= PLACARD_BG[1] and w >= PLACARD_BG[0]:
            bg_for_placard = (c, im)

    if l_nm:
        report.append("     加载界面背景 ← ① 工程既有：%s" % l_nm)
    elif bg_for_loading:
        c, im = bg_for_loading
        out, meta = make_loading_bg(im)
        l_nm = "LEADER_%s_BACKGROUND" % key
        emit({"textures": textures_dir}, l_nm, out, check)
        report.append("     加载界面背景 ← ② --bg-dir：%s → %s（%dx%d，%s）"
                      % (os.path.basename(c), l_nm, out.size[0], out.size[1], meta["mode"]))
    elif args.pick:
        l_nm = "LEADER_%s_BACKGROUND" % key
        report.append("     加载界面背景 ← 手动 --pick：%s（写官方命名别名）" % args.pick)
        _ensure_alias(root, "Shell_Loading.xlp", l_nm, args.pick, check, report)
    elif not args.no_color_fallback:
        top, similar = official_bg_for_hue(ref_img, packs, args.max_dh)
        if top and similar:
            l_nm = "LEADER_%s_BACKGROUND" % key
            report.append("     加载界面背景 ← ③ 色系回退：官方 %s（hue %.1f，Δh %.1f°，"
                          "score %.4f）→ 写官方命名别名 %s"
                          % (top["name"], top["hue"], top["d_hue"], top["score"], l_nm))
            _ensure_alias(root, "Shell_Loading.xlp", l_nm, top["name"], check, report)
        elif top:
            report.append("     ⛔ 加载界面背景色系回退失败：最佳 %s 的 Δh=%.1f° > %.0f°"
                          "（判为**不相似**）→ **需用户裁决**（--pick 指定）"
                          % (top["name"], top["d_hue"], args.max_dh))
            return p_nm, None
    if p_nm:
        report.append("     placard 背景 ← ① 工程既有竖版：%s" % p_nm)
    elif bg_for_placard:
        c, im = bg_for_placard
        pb, pm = make_placard_bg(im)
        p_nm = "LEADER_%s_PLACARD_BACKGROUND" % key
        emit({"textures": textures_dir}, p_nm, pb, check)
        report.append("     placard 背景 ← ② --bg-dir：%s → %s（%dx%d，cover %s×）"
                      % (os.path.basename(c), p_nm, pb.size[0], pb.size[1], pm["scale"]))
    else:
        # 既无竖版素材、也无可用宽幅源 → **停下询问用户**。
        # 不自行决定"拿横版去凑 placard"（StretchMode=None + 328×935 只会显示左上角一块），
        # 也不自行补边/重绘 —— 那属"把图改好"，超出本 skill 范围（§1.0）。
        raise NeedsDecision(
            "placard 竖版背景缺失：工程无 PORTRAIT_<KEY>_BACKGROUND，也没有可裁成 "
            "328×935 的宽幅源。请提供一张 328×935（或更大等比）的竖版背景 "
            "（用 --bg-dir <目录>），或明确指示用什么替代。")
    return p_nm, l_nm


def main():
    ap = argparse.ArgumentParser(
        description="原版 FrontEnd 前景/背景一站式自动处理（分类 → 处理 → 找背景 → 接线）")
    ap.add_argument("--project", required=True)
    ap.add_argument("--leader", help="单个 LeaderType（如 LEADER_CARTETHYIA_QYQXP）")
    ap.add_argument("--image", help="单个素材（PNG/JPG/DDS）")
    ap.add_argument("--image-dir", help="批量素材目录（文件名需含领袖名片段）")
    ap.add_argument("--leaders", help="逗号分隔的 LeaderType 列表（配合 --image-dir）")
    ap.add_argument("--bg-dir", help="背景素材目录（文件名含领袖名片段）")
    ap.add_argument("--pick", help="手动指定官方背景名（跳过色系回退）")
    ap.add_argument("--force-subject", action="store_true", help="强制按人物抠图处理")
    ap.add_argument("--force-bleed", action="store_true", help="强制按满幅图处理")
    ap.add_argument("--no-color-fallback", action="store_true", help="禁用色系回退")
    ap.add_argument("--max-dh", type=float, default=60.0, help="色系回退最大色相距离（默认 60°）")
    ap.add_argument("--allow-pack", default=",".join(DEFAULT_PACKS),
                    help="色系回退允许的官方 pack（默认 Base,Expansion1,Expansion2）")
    ap.add_argument("--subject-min-transp", type=float, default=40.0,
                    help="判为人物抠图的透明占比下限（默认 40%%）")
    ap.add_argument("--bleed-max-transp", type=float, default=5.0,
                    help="判为满幅图的透明占比上限（默认 5%%）")
    ap.add_argument("--write", action="store_true", help="实际写盘（**必须同时给 --confirmed**）")
    ap.add_argument("--confirmed", action="store_true",
                    help="用户已确认计划（§1.0 总规则：判断类操作一律先问后做）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    a = ap.parse_args()

    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        raise SystemExit("工程目录不存在：%s" % root)
    if bool(a.force_subject) and bool(a.force_bleed):
        raise SystemExit("--force-subject 与 --force-bleed 互斥")

    forced = "subject" if a.force_subject else ("bleed" if a.force_bleed else None)
    packs = tuple(x.strip() for x in a.allow_pack.split(",") if x.strip())

    # 组装任务列表
    tasks = []
    if a.leader and a.image:
        tasks.append((a.leader, a.image))
    elif a.image_dir:
        names = [x.strip() for x in (a.leaders or "").split(",") if x.strip()]
        if not names:
            # 从工程 SQL 探测
            from gen_suk_portrait import find_project_files, detect_leaders
            files = find_project_files(root)
            names = sorted(detect_leaders(files))
        for lt in names:
            key = lt[len("LEADER_"):] if lt.startswith("LEADER_") else lt
            m = _match_in_dir(a.image_dir, key)
            if m:
                tasks.append((lt, m))
            else:
                print("SKIP %s：%s 下找不到名字含 %s 的素材" % (lt, a.image_dir, key),
                      file=sys.stderr)
    else:
        raise SystemExit("需要 --leader+--image 或 --image-dir")

    if a.write and not a.confirmed:
        print("拒绝执行：--write 必须与 --confirmed 同时使用。\n"
              "  先跑一次不带 --write 的计划态，把计划交用户确认后再执行。", file=sys.stderr)
        return EXIT_ASK
    check = not a.write
    print("MODE: %s" % ("PLAN (no write)" if check else "WRITE (confirmed)"))
    print("project: %s" % root)
    report = []
    wiring = {}
    worst = EXIT_OK
    for lt, img in tasks:
        if not re.match(r"^LEADER_[A-Z0-9_]+$", lt):
            print("SKIP 非法 LeaderType：%s" % lt, file=sys.stderr)
            continue
        try:
            rc = plan_one(root, lt, img, check, forced, a.bg_dir, packs, a, report, wiring)
        except NeedsDecision as e:
            report.append("     ⛔ **需用户裁决**：%s" % e)
            rc = EXIT_ASK
        worst = max(worst, rc)

    print("\n".join(report))
    if wiring:
        print("\n=== 接线 SQL（FrontEnd 段：Players 属 Config 库）===")
        for lt, w in wiring.items():
            print("UPDATE Players SET Portrait = %s, PortraitBackground = '%s'"
                  % ("''" if w["portrait"] == "''" else "'%s'" % w["portrait"],
                     w["placard_bg"]))
            print("  WHERE LeaderType = '%s';" % lt)
        print("\n=== 接线 SQL（InGame 段：LoadingInfo 属 Gameplay 库）===")
        for lt, w in wiring.items():
            fg = "''" if w["loading_fg"] == "''" else "'%s'" % w["loading_fg"]
            print("INSERT OR REPLACE INTO LoadingInfo "
                  "(LeaderType, ForegroundImage, BackgroundImage, PlayDawnOfManAudio)")
            print("  VALUES ('%s', %s, '%s', 1);" % (lt, fg, w["loading_bg"]))
        print("\n⚠ 以上 SQL **不会自动写入工程**——接线落点由你/调用方决定"
              "（本工程既有做法：FrontEnd 写 Config_RGN.sql，Ingame 写 Leaders_RGN.sql）。")
    print("\n结论：%s" % {EXIT_OK: "全部可处理", EXIT_WARN: "有告警",
                           EXIT_ASK: "**有需用户裁决项**（见上）",
                           EXIT_ERR: "有错误"}[worst])
    if check:
        if worst == EXIT_ASK:
            print("（**未写盘**。请先把以上计划交用户确认并解决 ⛔ 项。）")
        else:
            print("（**未写盘**。把以上计划交用户确认后，再加 --write --confirmed 执行。）")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
