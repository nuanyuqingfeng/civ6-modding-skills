#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_suk_portrait.py — Sukritact's Civ Selection Screen 适配素材与接线生成器

## 解决什么问题

**Sukritact's Civ Selection Screen**（工坊 GUID `60092bdd-ce39-4319-aef6-baea505c7c45`）
用自绘的 `UI/AdvancedSetup.{lua,xml}` 整屏替换原版领袖选择界面，并改为**纯 2D 选人**：
它在选人时读 `Players` 表的 `Portrait` / `PortraitBackground` 两列，交给
`LeaderImage` / `LeaderBG` 两个控件显示（比例运行时由 `DummyImage` 实测，故尺寸可自由）。

原版 mod 的 `Portrait` 通常是空串、`PortraitBackground` 是 328×935 竖版，
在 Suk 的宽屏 2D 界面下尺寸/构图都不合用，因此需要一套**专供 Suk 的 2D 素材**，
并在 `Criteria = Suk_Portrait` 下改写 `Players`（未启用 Suk 时行为完全不变）。

本脚本按兄弟工程（工程 A / 工程 D / 工程 B/C）已实证的约定产出：
`SUK_UI_*` 命名空间贴图 + `UPDATE Players` + XLP 条目 + `.civ6proj` 接线，**幂等**。

## 素材工艺（实测自兄弟工程既有产物，可确定性复现）

- **立绘**：源 1316² 立绘 → 等比缩到高 1024（LANCZOS）→ 按 alpha 内容定宽（内容 + 左右各 N px）
  → 内容水平居中粘贴（**不裁切**）。与原版 `LEADER_*_NEUTRAL` 约定一致
  （实测原版 44 张：高固定 1024/1080、下边距恒 0、宽随内容 389~803）。
- **背景**：源 1920×1080 外交背景 → 中心横裁 1440×1080（**纯裁切、零缩放**；
  与兄弟工程产物逐像素相同，meanAbsErr = 0.00）。

## 素材来源（铁律：必须先问用户）

- `--from-existing`（默认）：直接复用工程既有
  `FALLBACK_NEUTRAL_{L}_QYQXP.dds`（立绘）与 `IMG_LEADER_{L}_QYQXP_DIPLOMACY_BACKGROUND.dds`（背景）。
- `--portrait-dir` / `--bg-dir`：改用用户提供的 PNG（文件名需含 LeaderType 或领袖名片段）。
  **用户给素材时必须显式指定**，不要默默用既有素材。

## 用法

    # ① 预演（不写盘）
    python gen_suk_portrait.py --project <工程根> --check

    # ② 落盘（素材 + SQL + XLP + civ6proj 接线）
    python gen_suk_portrait.py --project <工程根> --write

    # ③ 只处理指定领袖
    python gen_suk_portrait.py --project <工程根> --leaders LEADER_X_QYQXP,LEADER_Y_QYQXP --write

    # ④ 用用户素材（目录内 PNG，文件名含领袖名片段即可）
    python gen_suk_portrait.py --project <工程根> --portrait-dir D:/art --bg-dir D:/art --write

退出码：0 成功 / 1 参数或结构错误。
"""
import argparse
import os
import re
import struct
import sys

# 复用 civ6-modding 的 DDS 读写（单一真源，避免重复实现头构造）。
# 解析顺序：本 skill 同级 → ~/.agents/skills → 环境变量 CIV6_SKILLS_ROOT 指定。
_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDS = [
    os.path.join(_HERE, "..", "..", "civ6-modding", "art"),
    os.path.join(os.path.expanduser("~"), ".agents", "skills", "civ6-modding", "art"),
]
if os.environ.get("CIV6_SKILLS_ROOT"):
    _CANDS.insert(0, os.path.join(os.environ["CIV6_SKILLS_ROOT"], "civ6-modding", "art"))
for _cand in _CANDS:
    _cand = os.path.abspath(_cand)
    if os.path.isfile(os.path.join(_cand, "dds_io.py")):
        sys.path.insert(0, _cand)
        break
try:
    from dds_io import read_dds, write_dds          # noqa: E402
    from PIL import Image                            # noqa: E402
except ImportError as e:                             # pragma: no cover
    print("需要 Pillow，且需能找到 civ6-modding/art/dds_io.py")
    print("  已尝试：%s" % ", ".join(os.path.abspath(c) for c in _CANDS))
    print("  可用环境变量 CIV6_SKILLS_ROOT 指向 skills 根目录。")
    print("  原始错误：%s" % e)
    raise SystemExit(1)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PORTRAIT_H = 1024          # 立绘目标高（与原版 LEADER_*_NEUTRAL 一致）
MARGIN = 8                 # 内容左右各留透明边距（px）
MAX_W = 1024
ALPHA_THR = 8
BG_W, BG_H = 1440, 1080    # 兄弟工程实证的 Suk 背景尺寸（4:3）
BG_CROP_X = 240            # 1920→1440 的中心裁切起点
SUK_SUFFIX = "_Suk"        # legacy 命名后缀：**仅用于识别未迁移的旧素材**，不再用于生成
UI_NS = "SUK_UI"           # 独立命名空间前缀。见下表——
# ★ 为什么不再复用 `FALLBACK_NEUTRAL_*_Suk`：
#   `FALLBACK_*` 是**官方 Leader_Fallback 模板的固定命名**（3D 回退，类 `Leader_Fallback`），
#   而 Suk 适配是 **UI 贴图（类 `UserInterface`）**。同前缀不同类别会让
#   `gen_tex.py` 的 is_fallback() 必须额外维护一张例外表，且到处都要解释"为何同前缀"，
#   后人极易把 UI 立绘误当 3D 回退。迁到独立命名空间后该歧义从根上消失。
#   通用规则：第三方界面适配素材走 `<适配对象短名>_UI_<KIND>_<KEY>`，不复用官方模板前缀。
SUK_DIR = os.path.join("Mod_Adaptation", "Suk")
SUK_SQL = "Suk_Portrait_RGN.sql"
CRITERION = "Suk_Portrait"

TEX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" ?>
<AssetObjects..TextureInstance>
\t<m_ExportSettings>
\t\t<ePixelformat>PF_R8G8B8A8_UNORM</ePixelformat>
\t\t<eFilterType>FT_BOX</eFilterType>
\t\t<bUseMips>false</bUseMips>
\t\t<iNumManualMips>0</iNumManualMips>
\t\t<bCompleteMipChain>true</bCompleteMipChain>
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
\t<m_Height>{h}</m_Height>
\t<m_Width>{w}</m_Width>
\t<m_Depth>1</m_Depth>
\t<m_NumMipMaps>0</m_NumMipMaps>
\t<m_SourceFilePath text="D:\\desktop\\{name}.png"/>
\t<m_SourceObjectName text=""/>
\t<m_ImportedTime>0</m_ImportedTime>
\t<m_ExportedTime>{exported}</m_ExportedTime>
\t<m_ClassName text="UserInterface"/>
\t<m_DataFiles>
\t\t<Element>
\t\t\t<m_ID text="DDS"/>
\t\t\t<m_RelativePath text="{name}.dds"/>
\t\t</Element>
\t</m_DataFiles>
\t<m_Name text="{name}"/>
\t<m_Description text=""/>
\t<m_Tags>
\t\t<Element text="UserInterface"/>
\t</m_Tags>
</AssetObjects..TextureInstance>
"""


# ---------------------------------------------------------------- 工程发现

def find_project_files(root):
    """→ dict(proj, sln, textures_dir, xlp_candidates, sql_candidates)"""
    proj = None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("workspace", ".git", "Cooked", "Build")]
        for fn in filenames:
            if fn.endswith(".civ6proj"):
                proj = os.path.join(dirpath, fn)
                break
        if proj:
            break
    if not proj:
        raise SystemExit("在 %s 下找不到 .civ6proj" % root)
    proj_dir = os.path.dirname(proj)
    textures = os.path.join(proj_dir, "Textures")
    xlps = []
    for d in ("XLPs", "Xlps", "xlps"):
        p = os.path.join(proj_dir, d)
        if os.path.isdir(p):
            xlps = [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.lower().endswith(".xlp")]
            break
    sqls = []
    data = os.path.join(proj_dir, "Data")
    if os.path.isdir(data):
        sqls = [os.path.join(data, f) for f in sorted(os.listdir(data)) if f.lower().endswith(".sql")]
    return dict(proj=proj, proj_dir=proj_dir, textures=textures, xlps=xlps, sqls=sqls)


def detect_leaders(files):
    """从 Data/*.sql 的 `INSERT ... INTO Leaders` 语句里找真正定义的 LEADER_*。

    只认 Leaders 表（`('LEADER_X', 'KIND_LEADER')`），不认通用扫描——否则会把
    `'LEADER_DEFAULT'`（Leaders 行的第 3 列「继承模板」，见 Data/Leaders_RGN.sql:39-44）
    之类的**引用值**误当成领袖。
    被注释掉的可选领袖行同样会被命中（本函数不区分注释），这是有意的：
    可选领袖也应当备齐素材。
    """
    found = []
    pat = re.compile(r"\(\s*'(LEADER_[A-Za-z0-9_]+)'\s*,\s*'KIND_LEADER'\s*\)")
    for p in files["sqls"]:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in pat.finditer(t):
            lt = m.group(1)
            if lt not in found:
                found.append(lt)
    return found


def pick_ui_xlp(files):
    """挑一个 m_ClassName=UITexture 的 XLP（优先已含 Suk 条目者，其次 UILeaders）。"""
    cands = []
    for p in files["xlps"]:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if 'm_ClassName text="UITexture"' not in t:
            continue
        score = 0
        if "suk" in t.lower():
            score += 2
        if "uileaders" in os.path.basename(p).lower():
            score += 1
        cands.append((score, p, t))
    if not cands:
        return None, None
    cands.sort(key=lambda x: -x[0])
    return cands[0][1], cands[0][2]


# ---------------------------------------------------------------- 素材处理

def alpha_bbox(img, thr=ALPHA_THR):
    m = img.getchannel("A").point(lambda v: 255 if v > thr else 0)
    return m.getbbox()


def make_portrait(src):
    """源立绘 → 高 1024、内容自适应宽度、内容居中的画布（不裁切）。"""
    inter = src.resize((1024, PORTRAIT_H), Image.LANCZOS)
    bb = alpha_bbox(inter)
    if bb is None:
        raise ValueError("立绘完全透明，无法定内容宽")
    x0, _y0, x1, _y1 = bb
    content_w = x1 - x0
    canvas_w = max(1, min(MAX_W, content_w + MARGIN * 2))
    out = Image.new("RGBA", (canvas_w, PORTRAIT_H), (0, 0, 0, 0))
    paste_x = (canvas_w - content_w) // 2
    out.paste(inter.crop((x0, 0, x1, PORTRAIT_H)), (paste_x, 0))
    return out, dict(content_w=content_w, canvas_w=canvas_w,
                     left=paste_x, right=canvas_w - paste_x - content_w, clipped=0)


def make_background(src):
    """源外交背景 1920×1080 → 中心横裁 1440×1080（纯裁切）。"""
    if src.size != (1920, 1080):
        raise ValueError("外交背景应为 1920×1080，实为 %dx%d" % src.size)
    return src.crop((BG_CROP_X, 0, BG_CROP_X + BG_W, BG_H)), dict(crop_x=BG_CROP_X)


def load_any(path):
    """PNG/JPG 或 DDS 都能读成 RGBA。"""
    if path.lower().endswith(".dds"):
        return read_dds(path)
    img = Image.open(path)
    img.load()
    return img.convert("RGBA")


def resolve_sources(files, leaders, args):
    """→ {leader: dict(portrait=<path>, bg=<path>, source='existing'|'user')}"""
    out = {}
    for lt in leaders:
        key = lt[len("LEADER_"):] if lt.startswith("LEADER_") else lt
        # 既有素材（工程默认来源）
        por_ex = os.path.join(files["textures"], "FALLBACK_NEUTRAL_%s.dds" % key)
        bg_ex = os.path.join(files["textures"], "IMG_LEADER_%s_DIPLOMACY_BACKGROUND.dds" % key)
        # 用户素材（目录内文件名含领袖名片段）
        por_us = bg_us = None
        if args.portrait_dir:
            por_us = _match_in_dir(args.portrait_dir, key)
        if args.bg_dir:
            bg_us = _match_in_dir(args.bg_dir, key)
        por = por_us or (por_ex if os.path.isfile(por_ex) else None)
        bg = bg_us or (bg_ex if os.path.isfile(bg_ex) else None)
        out[lt] = dict(portrait=por, bg=bg, key=key,
                       source="user" if (por_us or bg_us) else "existing")
    return out


def _match_in_dir(d, key):
    """在目录里找文件名含 key（大小写不敏感）的 png/jpg/dds。"""
    if not os.path.isdir(d):
        return None
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".dds")):
            continue
        if key.lower() in fn.lower():
            return os.path.join(d, fn)
    return None


# ---------------------------------------------------------------- 生成

def tex_text(name, w, h):
    body = TEX_TEMPLATE.format(h=h, w=w, name=name,
                               exported=400000000 + len(name) * 7919)
    return body.replace("\r\n", "\n")


def gen_assets(files, srcs, check):
    """生成素材。缺少源素材的领袖**跳过**（返回 ok=False），不中断其余领袖。"""
    rows = []
    for lt, s in srcs.items():
        if not (s["portrait"] and s["bg"]):
            miss = []
            if not s["portrait"]:
                miss.append("立绘")
            if not s["bg"]:
                miss.append("背景")
            rows.append((lt, None, None, "SKIP(缺%s)" % "+".join(miss), False))
            continue
        por, pst = make_portrait(load_any(s["portrait"]))
        bg, bst = make_background(load_any(s["bg"]))
        pname = "%s_PORTRAIT_%s" % (UI_NS, s["key"])
        bname = "%s_BACKGROUND_%s" % (UI_NS, s["key"])
        if not check:
            write_dds(os.path.join(files["textures"], pname + ".dds"), por)
            write_dds(os.path.join(files["textures"], bname + ".dds"), bg)
            for nm, im in ((pname, por), (bname, bg)):
                with open(os.path.join(files["textures"], nm + ".tex"),
                          "w", encoding="utf-8", newline="\n") as f:
                    f.write(tex_text(nm, im.size[0], im.size[1]))
        rows.append((lt, pname, bname, "%dx%d" % por.size, True))
        s["_ok"] = True
        s["_pname"], s["_bname"] = pname, bname
    return rows


def gen_sql(files, srcs, check):
    """只给**素材齐备**的领袖写 UPDATE（缺素材的跳过，避免指向不存在的贴图）。"""
    ok = [(lt, s) for lt, s in srcs.items() if s.get("_ok")]
    lines = [
        "-- Sukritact's Civ Selection Screen 适配（由 gen_suk_portrait.py 生成）",
        "-- 触发：Suk 选人界面启用时（Criteria %s）；未启用则不加载，原版界面行为不变" % CRITERION,
        "-- 说明：Suk 是纯 2D 选人界面，读 Players.Portrait / PortraitBackground 显示立绘与背景。",
        "--       此处把二者指向专为 Suk 准备的 %s_* 素材；未定义的领袖 UPDATE 影响 0 行，无副作用。" % UI_NS,
        "",
    ]
    for lt, s in ok:
        lines += [
            "UPDATE Players",
            "SET",
            "    Portrait = '%s'," % s["_pname"],
            "    PortraitBackground = '%s'" % s["_bname"],
            "WHERE LeaderType = '%s';" % lt,
            "",
        ]
    text = "\n".join(lines).rstrip() + "\n"
    path = os.path.join(files["proj_dir"], SUK_DIR, SUK_SQL)
    if not check and ok:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(text)
    return path, len(ok)


def gen_xlp(files, srcs, check):
    """向选定的 UITexture XLP 幂等追加 SUK_UI_* 条目（只含素材齐备者）。"""
    path, text = pick_ui_xlp(files)
    if not path:
        return None, 0
    names = []
    for s in srcs.values():
        if not s.get("_ok"):
            continue
        names.append(s["_pname"])
        names.append(s["_bname"])
    add = [n for n in names if ('<m_EntryID text="%s"' % n) not in text]
    if not add or check:
        return path, len(add)
    blocks = "\n".join(
        '\t\t<Element>\n\t\t\t<m_EntryID text="%s"/>\n\t\t\t<m_ObjectName text="%s"/>\n\t\t</Element>'
        % (n, n) for n in add)
    marker = "\t</m_Entries>"
    if text.count(marker) != 1:
        raise SystemExit("XLP %s 的 </m_Entries> 锚点不唯一，请手工合并" % path)
    text = text.replace(marker, blocks + "\n" + marker)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path, len(add)


def gen_proj(files, check):
    """幂等插入 Folder / Content / FrontEndAction 三处，保留 BOM 与 CRLF。"""
    path = files["proj"]
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[len(b"\xef\xbb\xbf"):] if bom else raw
    t = body.decode("utf-8")
    nl = "\r\n"
    ind, ind2 = "    ", "      "
    changed = []

    f_anchor = ind + '<Folder Include="Mod_Adaptation\\Rover" />'
    if 'Include="Mod_Adaptation\\Suk"' in t:
        changed.append("folder:skip")
    else:
        # 锚点优先 Rover，其次任意 Mod_Adaptation 子目录
        cand = [l for l in t.split(nl) if re.match(r'\s*<Folder Include="Mod_Adaptation\\[^"]+" />', l)]
        anchor = cand[-1] if cand else None
        if not anchor:
            changed.append("folder:MANUAL")
        else:
            t = t.replace(anchor, anchor + nl + ind + '<Folder Include="Mod_Adaptation\\Suk" />', 1)
            changed.append("folder:ok")

    c_rel = "%s\\%s" % (SUK_DIR.replace("/", "\\"), SUK_SQL)
    if c_rel in t:
        changed.append("content:skip")
    else:
        # 插在最后一个 Mod_Adaptation Content 块之后
        blocks = list(re.finditer(
            r'( +<Content Include="Mod_Adaptation\\\\[^"]+">' + re.escape(nl) +
            r' +<SubType>Content</SubType>' + re.escape(nl) + r' +</Content>' + re.escape(nl) + r')', t))
        if not blocks:
            changed.append("content:MANUAL")
        else:
            b = blocks[-1]
            ins = (ind + '<Content Include="%s">' % c_rel + nl +
                   ind2 + "<SubType>Content</SubType>" + nl + ind + "</Content>" + nl)
            t = t[:b.end()] + ins + t[b.end():]
            changed.append("content:ok")

    if 'id="RGN_Suk_Portrait"' in t or "RGN_Suk_Portrait" in t:
        changed.append("frontend:skip")
    else:
        fe = '<UpdateDatabase id="RGN_Rover_Config">'
        new = ('<UpdateDatabase id="RGN_Suk_Portrait">'
               '<Properties><LoadOrder>999999</LoadOrder></Properties>'
               '<Criteria>%s</Criteria>'
               '<File>%s/%s</File>'
               '</UpdateDatabase>' % (CRITERION, SUK_DIR.replace("\\", "/"), SUK_SQL))
        if fe not in t:
            # 退而求其次：插在 </FrontEndActions> 前
            if "</FrontEndActions>" not in t:
                changed.append("frontend:MANUAL")
                new = None
            else:
                t = t.replace("</FrontEndActions>", new + "</FrontEndActions>", 1)
                changed.append("frontend:ok(append)")
        else:
            t = t.replace(fe, new + fe, 1)
            changed.append("frontend:ok")
    if check:
        return changed
    payload = (b"\xef\xbb\xbf" if bom else b"") + t.encode("utf-8")
    open(path, "wb").write(payload)
    return changed


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Sukritact's Civ Selection Screen 适配素材与接线生成器")
    ap.add_argument("--project", required=True, help="工程根目录（含 .civ6proj）")
    ap.add_argument("--leaders", help="逗号分隔的 LeaderType；缺省自动从 Data/*.sql 探测")
    ap.add_argument("--portrait-dir", help="用户提供的立绘 PNG 目录（文件名含领袖名片段）")
    ap.add_argument("--bg-dir", help="用户提供的背景 PNG 目录")
    ap.add_argument("--check", action="store_true", help="预演，不写盘")
    ap.add_argument("--write", action="store_true", help="实际写盘")
    a = ap.parse_args()
    check = not a.write
    if not (a.check or a.write):
        ap.print_help()
        return 1

    root = os.path.abspath(a.project)
    if not os.path.isdir(root):
        raise SystemExit("工程目录不存在：%s" % root)
    files = find_project_files(root)

    if a.leaders:
        leaders = [x.strip() for x in a.leaders.split(",") if x.strip()]
    else:
        leaders = detect_leaders(files)
    if not leaders:
        raise SystemExit("未探测到 LEADER_*；请用 --leaders 指定")

    srcs = resolve_sources(files, leaders, a)
    print("MODE:", "CHECK (no write)" if check else "WRITE")
    print("project :", files["proj"])
    print("textures:", files["textures"])
    print("leaders :", len(leaders))
    print()
    print("%-30s %-38s %-38s %-12s %s" % ("leader", "portrait src", "bg src", "canvas", "note"))
    print("-" * 140)
    for lt, r in ((lt, srcs[lt]) for lt in leaders):
        print("%-30s %-38s %-38s %-12s %s" % (
            lt,
            os.path.basename(r["portrait"]) if r["portrait"] else "(none)",
            os.path.basename(r["bg"]) if r["bg"] else "(none)",
            "-", r["source"]))
    rows = gen_assets(files, srcs, check)
    print()
    print("%-30s %-46s %-46s %s" % ("leader", "portrait out", "background out", "size"))
    for lt, p, b, note, _ok in rows:
        print("%-30s %-46s %-46s %s" % (lt, p or "-", b or "-", note))
    missing = [r[0] for r in rows if not r[4]]
    if missing:
        print()
        print("!! 跳过 %d 位（缺源素材），其余照常处理：%s" % (len(missing), ", ".join(missing)))
        print("   立绘需 FALLBACK_NEUTRAL_<KEY>.dds，背景需 IMG_LEADER_<KEY>_DIPLOMACY_BACKGROUND.dds；")
        print("   或用 --portrait-dir / --bg-dir 指定用户素材。")

    ok_count = sum(1 for r in rows if r[4])
    if ok_count == 0:
        print()
        print("没有任何领袖素材齐备，未生成 SQL/XLP/接线。")
        return 1

    sql_path, n_sql = gen_sql(files, srcs, check)
    xlp_path, n_add = gen_xlp(files, srcs, check)
    changes = gen_proj(files, check)

    print()
    print("SQL      :", sql_path, "(%d UPDATE)" % n_sql)
    print("XLP      :", xlp_path, "(%d new entries)" % n_add)
    print("civ6proj :", ", ".join(changes))
    if any(c.endswith("MANUAL") for c in changes):
        print()
        print("!! civ6proj 有锚点找不到，需手工合并（见上 MANUAL 项）")
        return 1
    print()
    print("DONE (no write)" if check else "DONE (written)")
    print()
    print("后续：check_pantry.py → clear_ae_cache.py → AssetEditor → ModBuddy 构建 → 进游戏双态验证")
    return 0


if __name__ == "__main__":
    sys.exit(main())
