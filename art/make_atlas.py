#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_atlas.py — Civ6 多图网格图集（IconTextureAtlas）合成器。

把多张独立图标源图拼成网格 atlas（序列图合成），逐尺寸输出：
  组员 PNG（≥256×256 正方形）
  → 按 grid 网格拼版、按尺寸缩放，输出整版 PNG
  → texconv 转 DDS（R8G8B8A8_UNORM，单 mip，与 convert_art.ps1 图标口径一致）
  → 生成 .tex（复用 gen_tex.py）
  → 产出注册片段 <atlas>_registration.xml（IconTextureAtlases + IconDefinitions，
    待 AI 合并进 Data/Icons_*.xml，不直接改项目文件）

manifest 写法（art_manifest.json 顶层新增 atlasEntries，与 entries 并列）：
{
  "atlasEntries": [
    {
      "atlas": "ATLAS_MYMOD_ICON_LEADERS",  // IconTextureAtlases.Name
      "grid": {"cols": 3, "rows": 2},          // 网格；cols*rows >= 组员数
      "role": "leader_icon",                   // 可选：决定 sizes（与 entries 同一套 role 表）
      "sizes": [32, 45, 48, 50, 55, 64, 80, 256],  // 可选：显式覆盖 role
      "filenamePattern": "{atlas}{size}",      // 可选，默认 "{atlas}{size}"；可用 {atlas}/{size}
      "members": [                             // 顺序即 Index（行优先）
        {"tech": "ICON_LEADER_CANTARELLA_QYQXP", "source": "坎特蕾拉.png"},
        {"tech": "ICON_LEADER_CARTETHYIA_QYQXP",  "source": "卡提希娅.png"}
      ]
    }
  ]
}

用法：python make_atlas.py [-Manifest art_manifest.json] [-ProjectRoot <path>]
依赖：Pillow（组员缩放）、texconv（DDS，与 convert_art.ps1 同一探测逻辑）、gen_tex.py 同目录。
缺图跳过该组员并 WARN（网格留空位），整组员全缺时整组跳过。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PIL import Image

# --- role -> 尺寸表（与 convert_art.ps1 同源：civ6ma iconsize_data + 项目实测）---
SIZE_TABLES = {
    "civ_icon":          [22, 30, 32, 36, 44, 45, 48, 50, 64, 80, 128, 200, 256],
    "leader_icon":       [32, 45, 48, 50, 55, 64, 80, 256],
    "building_icon":     [32, 38, 50, 80, 128, 256],
    "citystate_icon":    [22, 30, 32, 36, 40, 44, 48, 64, 68, 80, 256],
    "civic_icon":        [38, 42, 128, 160],
    "district_icon":     [22, 32, 38, 50, 80, 128, 256],
    "feature_icon":      [50, 64, 256],
    "government_icon":   [32, 50],
    "greatwork_icon":    [45, 64, 256],
    "policy_icon":       [32, 38, 50, 256],
    "project_icon":      [30, 32, 38, 50, 70, 80, 256],
    "resource_icon":     [38, 50, 64, 256],
    "stat_icon":         [16, 22, 32, 45, 55],
    "tech_icon":         [30, 38, 42, 128, 160],
    "unit_action_icon":  [38, 50, 80, 256],
    "unit_portrait":     [38, 50, 70, 95, 200, 256],
    "unit_icon":         [22, 32, 38, 50, 80, 256],
    "victory_icon":      [64, 80, 130, 220],
    "wonder_icon":       [32, 38, 50, 64, 128, 256],
}


def resolve_sizes(entry):
    """role 与 sizes 二选一：sizes 显式优先，其次 role 表，都没有则报错。"""
    sizes = entry.get("sizes")
    if sizes:
        return list(sizes)
    role = entry.get("role")
    if role in SIZE_TABLES:
        return list(SIZE_TABLES[role])
    raise SystemExit(f"atlas 条目 {entry.get('atlas')!r} 缺 sizes 且 role 不在尺寸表: {role!r}")


def find_texconv():
    """与 convert_art.ps1 同一探测顺序：PATH → WinGet Links → WinGet Packages 递归。"""
    from shutil import which
    found = which("texconv")
    if found:
        return found
    links = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/texconv.exe"
    if links.is_file():
        return str(links)
    pkgs = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages"
    if pkgs.is_dir():
        for p in pkgs.rglob("texconv.exe"):
            return str(p)
    return None


def compose_grid(member_images, cols, rows, size):
    """把组员 RGBA 缩放到 size×size（非正方形源等比 contain 到格内）后行优先拼版。"""
    canvas = Image.new("RGBA", (cols * size, rows * size), (0, 0, 0, 0))
    for i, img in enumerate(member_images):
        if img is None:  # 缺图组员：网格留空位，后续组员按 Index 原位贴入
            continue
        row, col = divmod(i, cols)
        rgba = img.convert("RGBA")
        if rgba.width == size and rgba.height == size:
            cell = rgba
        elif rgba.width == rgba.height:
            cell = rgba.resize((size, size), Image.Resampling.LANCZOS)
        else:
            # 非正方形：等比 contain，居中贴格（四周透明）
            scale = min(size / rgba.width, size / rgba.height)
            w, h = max(1, round(rgba.width * scale)), max(1, round(rgba.height * scale))
            cell = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            thumb = rgba.resize((w, h), Image.Resampling.LANCZOS)
            cell.paste(thumb, ((size - w) // 2, (size - h) // 2))
        canvas.paste(cell, (col * size, row * size))
    return canvas


def gen_tex_base(dds_name):
    """与 gen_tex.py get_source_png 的 base 规则一致：ICON_..._<digits> 剥尺寸后缀。"""
    m = re.match(r"(ICON_\w+?)_(\d+)$", dds_name)
    return m.group(1) if m else dds_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-Manifest", default="art_manifest.json")
    ap.add_argument("-ProjectRoot", default="")
    ap.add_argument("--no-dds", action="store_true", help="只拼 PNG + 产出注册片段，不转 DDS/.tex")
    args = ap.parse_args()

    manifest = Path(args.Manifest)
    if not manifest.is_absolute():
        manifest = Path.cwd() / manifest
    if not manifest.is_file():
        raise SystemExit(f"manifest not found: {manifest}")
    cfg = json.loads(manifest.read_text(encoding="utf-8"))

    entries = cfg.get("atlasEntries") or []
    if not entries:
        raise SystemExit("manifest 没有 atlasEntries，无事可做")

    root = Path(args.ProjectRoot) if args.ProjectRoot else (
        Path(cfg["projectRoot"]) if cfg.get("projectRoot") else manifest.parent)
    textures_dir = Path(cfg["texturesDir"]) if cfg.get("texturesDir") else None
    if textures_dir is None:
        sln = sorted(root.glob("*.civ6sln"))
        if sln:
            mod_name = sln[0].stem
        else:
            proj = next(iter(root.rglob("*.civ6proj")), None)
            if proj is None:
                raise SystemExit(f"cannot detect ModName: no .civ6sln/.civ6proj under {root}")
            mod_name = proj.parent.name
        textures_dir = root / mod_name / "Textures"
    assets_dir = Path(cfg["assetsDir"]) if cfg.get("assetsDir") else root / ".assets"
    textures_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    texconv = find_texconv()
    if not texconv and not args.no_dds:
        raise SystemExit("texconv 未找到（先跑一次 convert_art.ps1 让其 winget 安装，或手动安装后重试）")

    # asset_map 合并读写（不覆盖 convert_art.ps1 的条目；ps1 侧也已改为合并）
    asset_map_path = manifest.parent / "asset_map.json"
    try:
        asset_map = json.loads(asset_map_path.read_text(encoding="utf-8"))
    except Exception:
        asset_map = {}

    script_dir = Path(__file__).resolve().parent
    gen_tex = script_dir / "gen_tex.py"

    total_ok, total_skip = 0, 0
    for entry in entries:
        atlas = entry["atlas"]
        grid = entry.get("grid") or {}
        cols, rows = int(grid.get("cols", 1)), int(grid.get("rows", 1))
        if cols < 1 or rows < 1:
            raise SystemExit(f"{atlas}: grid 非法 cols={cols} rows={rows}")
        pattern = entry.get("filenamePattern", "{atlas}{size}")
        sizes = resolve_sizes(entry)

        members = entry.get("members") or []
        slots = cols * rows
        if len(members) > slots:
            print(f"WARN: {atlas} 组员数 {len(members)} 超过网格 {cols}x{rows}={slots}，"
                  f"多余 {len(members) - slots} 个不进图（Index 也不生成）")
        if len(members) < slots:
            print(f"WARN: {atlas} 网格 {slots} 格只用 {len(members)} 格，其余留空")

        # 组员源图预载（缺图跳过并留空位）
        images, member_ok = [], 0
        for m in members[:slots]:
            src = Path(m["source"])
            if not src.is_absolute():
                src = assets_dir / src
            if not src.is_file():
                print(f"  skip (missing): {m['tech']} <- {src}")
                images.append(None)
                continue
            images.append(Image.open(src))
            member_ok += 1
        if member_ok == 0:
            print(f"  skip (no member): {atlas}")
            total_skip += 1
            continue

        atlas_rows, defs_rows = [], []
        for s in sizes:
            dds_name = pattern.format(atlas=atlas, size=s)
            png_name = dds_name + ".png"
            canvas = compose_grid(images, cols, rows, s)
            out_png = assets_dir / png_name
            canvas.save(out_png, format="PNG")

            # gen_tex 源映射：按其 base 规则登记（组员名→拼好的整版 PNG）
            asset_map[gen_tex_base(dds_name)] = dds_name

            # IconTextureAtlases 行：多格图集 Filename 带 .dds（与项目 Icons XML 现状一致）
            fname = dds_name + ".dds" if slots > 1 else dds_name
            row_attr = f' Name="{atlas}" IconSize="{s}"'
            if cols > 1:
                row_attr += f' IconsPerRow="{cols}"'
            if rows > 1:
                row_attr += f' IconsPerColumn="{rows}"'
            row_attr += f' Filename="{fname}"'
            atlas_rows.append(f"        <Row{row_attr}/>")

            if not args.no_dds:
                with tempfile.TemporaryDirectory() as staging:
                    subprocess.run(
                        [texconv, "-y", str(out_png), "-o", staging,
                         "-f", "R8G8B8A8_UNORM", "-m", "1",
                         "-w", str(canvas.width), "-h", str(canvas.height)],
                        check=True, capture_output=True)
                    produced = Path(staging) / (Path(out_png).stem + ".dds")
                    # 临时目录与项目可能跨盘，用 shutil.move（os.replace 跨盘会 WinError 17）
                    shutil.move(str(produced), str(textures_dir / (dds_name + ".dds")))
                print(f"  ok: {dds_name}.dds  ({cols * s}x{rows * s}, {cols}x{rows} 格)")

        # IconDefinitions 行：Index = 组员序号（行优先），仅登记实进图的组员
        for i, m in enumerate(members[:slots]):
            if images[i] is not None:
                defs_rows.append(
                    f'        <Row Name="{m["tech"]}" Atlas="{atlas}" Index="{i}"/>')

        frag = manifest.parent / f"{atlas}_registration.xml"
        frag.write_text(
            "<GameData>\n"
            "    <IconTextureAtlases>\n" + "\n".join(atlas_rows) + "\n    </IconTextureAtlases>\n\n"
            "    <IconDefinitions>\n" + "\n".join(defs_rows) + "\n    </IconDefinitions>\n"
            "</GameData>\n",
            encoding="utf-8")
        print(f"  注册片段: {frag.name}（AI 合并进项目 Icons XML，勿直接覆盖项目文件）")
        total_ok += 1

    asset_map_path.write_text(json.dumps(asset_map, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.no_dds:
        py = None
        for c in ("python", "python3", "py"):
            try:
                subprocess.run([c, "--version"], check=True, capture_output=True)
                py = c
                break
            except Exception:
                continue
        if py:
            subprocess.run([py, str(gen_tex), str(textures_dir), str(assets_dir),
                            str(asset_map_path)], check=False)
        else:
            print("WARN: python 未找到，跳过 .tex 生成（DDS 已完成）")

    dds = len(list(textures_dir.glob("*.dds")))
    tex = len(list(textures_dir.glob("*.tex")))
    print(f"\nDone. atlas 组 ok={total_ok} skip={total_skip} | Textures: DDS={dds} TEX={tex}")


if __name__ == "__main__":
    main()
