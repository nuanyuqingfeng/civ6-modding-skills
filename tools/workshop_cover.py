# -*- coding: utf-8 -*-
"""工坊封面合成：生图模型出的底图/徽记 + **确定性 CJK 排版**。

为什么不是"让生图模型直接写标题"：扩散模型渲染中文得到的是形近伪字
（实测 "人类玩家所有单位" → "义凵薊丨劦……"），拉丁长句也会掉字母。
所以封面固定走两步：模型只出**无文字的底图与徽记**，文字由本脚本用真实字体排版 ——
排版可控，且天然不会出现"末尾两个字孤零零掉到第二行"这类丑排版。

项目硬性约定：**封面任何情况下不署名**（作者只写在 .modinfo 的 Authors 与代码里）。
本脚本因此不提供作者行参数。

用法（先出底图，再合成）：
    python local_flux.py --prompt-file bg.txt --out bg_7.png --seeds 42,7,123
    python local_flux.py --prompt-file emblem.txt --out emblem.png   # 或由 sd_cpp 下的 make-icon.ps1 / art/normalize_icon.py 出白色剪影
    python workshop_cover.py --bg bg_7.png --emblem emblem.png \
        --line1 "人类玩家所有单位" --line2 "可以建立城市" \
        --subtitle "CIVILIZATION VI MOD" \
        --master "D:\\desktop\\X_Surface.png" --preview out/image.png

排版自检：行数不匹配 / 末行过短（孤儿行）/ 行宽超安全边距 → 打印 WARN，不阻断。
退出码：0 成功 / 1 失败
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

INK = (5, 11, 20)
GOLD_TOP = (247, 230, 178)
GOLD_BOTTOM = (196, 152, 66)
DEFAULT_CJK_FONT = r"C:\Windows\Fonts\msyhbd.ttc"
DEFAULT_LATIN_FONT = r"C:\Windows\Fonts\seguisb.ttf"


def _lerp(a, b, t):
    return a + (b - a) * t


def _scrim(size: int):
    """中部压暗带：给文字一块干净底（竖直 alpha 剖面线性插值）。"""
    from PIL import Image
    s = size / 1024.0
    stops = [(0, 0), (int(300 * s), 0), (int(430 * s), 168), (int(900 * s), 178),
             (int(985 * s), 60), (size, 0)]
    m = Image.new("L", (size, size), 0)
    px = m.load()
    for y in range(size):
        a = stops[0][1]
        for i in range(len(stops) - 1):
            y0, a0 = stops[i]
            y1, a1 = stops[i + 1]
            if y0 <= y <= y1:
                a = _lerp(a0, a1, 0.0 if y1 == y0 else (y - y0) / float(y1 - y0))
                break
        else:
            a = stops[-1][1]
        v = int(max(0, min(255, a)))
        for x in range(size):
            px[x, y] = v
    return m


def _tracked_width(font, text, tracking):
    return sum(font.getlength(c) for c in text) + tracking * (len(text) - 1)


def _draw_tracked(draw, text, font, tracking, top, fill, canvas_w):
    x = (canvas_w - _tracked_width(font, text, tracking)) / 2.0
    for c in text:
        draw.text((x, top), c, font=font, fill=fill)
        x += font.getlength(c) + tracking


def main() -> int:
    ap = argparse.ArgumentParser(description="工坊封面合成（确定性 CJK 排版）")
    ap.add_argument("--bg", required=True, help="底图 PNG（生图模型产出，不含文字）")
    ap.add_argument("--emblem", default=None, help="可选：徽记/剪影 PNG（透明底）")
    ap.add_argument("--line1", required=True, help="标题第一行")
    ap.add_argument("--line2", default=None, help="标题第二行（可选）")
    ap.add_argument("--subtitle", default=None, help="副标题（拉丁字母，如 CIVILIZATION VI MOD）")
    ap.add_argument("--master", required=True, help="母版输出 PNG")
    ap.add_argument("--preview", default=None, help="预览图输出 PNG（Steam 上限 1 MB）")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--preview-size", type=int, default=640)
    ap.add_argument("--title-size", type=int, default=92)
    ap.add_argument("--cjk-font", default=DEFAULT_CJK_FONT)
    ap.add_argument("--latin-font", default=DEFAULT_LATIN_FONT)
    args = ap.parse_args()

    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("FAIL 需要 Pillow：pip install pillow")
        return 1

    S = args.size
    s = S / 1024.0

    # 排版自检（不阻断）
    warn = []
    if args.line2 and len(args.line2) < len(args.line1) * 0.5:
        warn.append("第二行（%d 字）明显短于第一行（%d 字），检查是否出现孤儿行"
                    % (len(args.line2), len(args.line1)))
    if args.line2 is None and len(args.line1) > 10:
        warn.append("单行标题 %d 字，建议拆成两行以保持可读性" % len(args.line1))
    for w in warn:
        print("WARN %s" % w)

    bg = Image.open(args.bg).convert("RGB").resize((S, S), Image.LANCZOS)
    bg = Image.blend(bg, Image.new("RGB", (S, S), INK), 0.18)
    bg = Image.composite(Image.new("RGB", (S, S), (4, 9, 17)), bg, _scrim(S))

    # 徽记：深色剪影压在顶部光晕上
    if args.emblem:
        em = Image.open(args.emblem).convert("RGBA")
        eh = int(176 * s)
        ew = max(1, int(em.width * eh / em.height))
        em = em.resize((ew, eh), Image.LANCZOS)
        tint = Image.new("RGBA", em.size, INK + (255,))
        tint.putalpha(em.getchannel("A").point(lambda v: int(v * 0.96)))
        ex, ey = (S - ew) // 2, int(118 * s)
        bg.paste(tint, (ex, ey), tint)
        base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        bd = ImageDraw.Draw(base)
        lw = ew + int(96 * s)
        lx, ly = (S - lw) // 2, ey + eh + int(14 * s)
        for i in range(lw):
            t = i / (lw - 1.0)
            fade = min(1.0, min(t, 1.0 - t) * 6.0)
            bd.point((lx + i, ly), fill=(212, 172, 96, int(200 * fade)))
            bd.point((lx + i, ly + 1), fill=(150, 116, 58, int(120 * fade)))
        bg = Image.alpha_composite(bg.convert("RGBA"), base.filter(ImageFilter.GaussianBlur(0.6))).convert("RGB")

    # 标题
    font_title = ImageFont.truetype(args.cjk_font, int(args.title_size * s))
    tracking = int(12 * s)
    lines = [t for t in (args.line1, args.line2) if t]
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    y0, line_gap = int(478 * s), int(136 * s)
    widths = []
    for i, txt in enumerate(lines):
        widths.append(_tracked_width(font_title, txt, tracking))
        _draw_tracked(md, txt, font_title, tracking, y0 + i * line_gap, 255, S)
    max_w = max(widths)
    if max_w > S * 0.86:
        print("WARN 标题最宽 %.0fpx 超过安全边距（%.0fpx），建议减小 --title-size" % (max_w, S * 0.86))

    bg = Image.composite(Image.new("RGB", (S, S), (0, 0, 0)), bg,
                         mask.filter(ImageFilter.GaussianBlur(int(16 * s))).point(lambda v: int(v * 0.75)))

    grad = Image.new("RGB", (S, S))
    gp = grad.load()
    g_top, g_bot = int(440 * s), int(700 * s)
    for y in range(S):
        t = 0.0 if y <= g_top else (1.0 if y >= g_bot else (y - g_top) / float(g_bot - g_top))
        c = (int(_lerp(GOLD_TOP[0], GOLD_BOTTOM[0], t)),
             int(_lerp(GOLD_TOP[1], GOLD_BOTTOM[1], t)),
             int(_lerp(GOLD_TOP[2], GOLD_BOTTOM[2], t)))
        for x in range(S):
            gp[x, y] = c
    bg = Image.composite(grad, bg, mask)

    # 分隔线 + 副标题
    d = ImageDraw.Draw(bg)
    div_w = int(168 * s)
    dy = int(748 * s)
    d.rectangle([(S - div_w) // 2, dy, (S + div_w) // 2, dy + max(1, int(2 * s))], fill=(176, 138, 72))
    d.rectangle([(S - div_w) // 2, dy + int(5 * s), (S + div_w) // 2, dy + int(6 * s)], fill=(120, 92, 48))
    if args.subtitle:
        f_sub = ImageFont.truetype(args.latin_font, int(31 * s))
        _draw_tracked(d, args.subtitle, f_sub, int(13 * s), int(792 * s), (154, 168, 188), S)

    os.makedirs(os.path.dirname(os.path.abspath(args.master)), exist_ok=True)
    bg.save(args.master, "PNG")
    print("MASTER  %s  %d B" % (args.master, os.path.getsize(args.master)))

    if args.preview:
        os.makedirs(os.path.dirname(os.path.abspath(args.preview)), exist_ok=True)
        bg.resize((args.preview_size, args.preview_size), Image.LANCZOS).save(args.preview, "PNG", optimize=True)
        n = os.path.getsize(args.preview)
        print("PREVIEW %s  %d B%s" % (args.preview, n, "  <== 超过 Steam 1 MB 上限！" if n > 1 << 20 else ""))
    print("提醒    封面不署名（项目约定）；作者只写在 .modinfo 的 Authors 与代码里")
    return 0


if __name__ == "__main__":
    sys.exit(main())
