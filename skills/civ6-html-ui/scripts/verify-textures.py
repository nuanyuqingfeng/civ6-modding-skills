#!/usr/bin/env python3
"""Read-only PNG and optional ModTools export-chain verification (requires Pillow)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from texture_manifest import load_manifest, source_entries

try:
    from PIL import Image, ImageChops
except ImportError:
    raise SystemExit("Pillow is required: install it in this Python environment (python -m pip install Pillow)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def open_rgba(file: Path, size):
    with Image.open(file) as image:
        require(image.size == tuple(size), f"Wrong dimensions: {file}: {image.size}, expected {size}")
        image.load()
        return image.convert("RGBA")


def max_difference(a, b):
    extrema = ImageChops.difference(a, b).getextrema()
    return extrema[1] if isinstance(extrema[0], int) else max(high for _, high in extrema)


def compare_visible(source, exported, tolerance, label):
    delta = max_difference(source.getchannel("A"), exported.getchannel("A"))
    for value in (0, 255):
        background = Image.new("RGBA", source.size, (value, value, value, 255))
        a = Image.alpha_composite(background, source)
        b = Image.alpha_composite(background, exported)
        delta = max(delta, max_difference(a, b))
    require(delta <= tolerance, f"Visible pixels/alpha differ: {label}, maximum {delta} > {tolerance}")
    return delta


def text_attribute(root, query):
    node = root.find(query)
    return node.get("text", "") if node is not None else ""


def project_packages(project: Path):
    packages = []
    for file in sorted((project / "XLPs").glob("*")):
        if file.suffix.casefold() != ".xlp":
            continue
        root = ET.parse(file).getroot()
        if text_attribute(root, "m_ClassName") != "UITexture":
            continue
        package = text_attribute(root, "m_PackageName")
        entries = [(text_attribute(node, "m_EntryID"), text_attribute(node, "m_ObjectName"))
                   for node in root.findall("m_Entries/Element")]
        packages.append((file, package, entries))
    registered = set()
    for file in project.glob("*"):
        if not file.name.casefold().endswith(".art.xml"):
            continue
        root = ET.parse(file).getroot()
        for node in root.iter("Element"):
            if text_attribute(node, "libraryName") == "UITexture":
                registered.update(child.get("text", "") for child in node.findall("relativePackagePaths/Element"))
    return packages, registered


def verify(manifest: Path, png_dir: Path, project: Path | None, tolerance: int):
    specs = load_manifest(manifest)
    source_entries(manifest, png_dir)
    packages, registered = project_packages(project) if project else ([], set())
    report = []
    for name, size in specs.items():
        source = open_rgba(png_dir / f"{name}.png", size)
        item = {"name": name, "size": size, "alpha_range": source.getchannel("A").getextrema()}
        if project:
            tex_path = project / "Textures" / f"{name}.tex"
            root = ET.parse(tex_path).getroot()
            require(text_attribute(root, "m_Name") == name, f"TEX m_Name mismatch: {tex_path}")
            require((int(root.findtext("m_Width", "0")), int(root.findtext("m_Height", "0"))) == tuple(size),
                    f"TEX dimensions mismatch: {tex_path}")
            dds_names = [text_attribute(node, "m_RelativePath") for node in root.findall("m_DataFiles/Element")
                         if text_attribute(node, "m_ID") == "DDS"]
            require(dds_names == [f"{name}.dds"], f"TEX DDS reference mismatch: {tex_path}: {dds_names}")
            matches = [(file, package) for file, package, entries in packages if (name, name) in entries]
            require(bool(matches), f"Missing UITexture XLP EntryID/ObjectName: {name}")
            require(any(package in registered for _, package in matches), f"Missing Art.xml UITexture package: {name}")
            export_png = open_rgba(project / "IMG" / f"{name}.png", size)
            dds = open_rgba(project / "Textures" / f"{name}.dds", size)
            item["png_max_visible_delta"] = compare_visible(source, export_png, tolerance, f"{name}.png")
            item["dds_max_visible_delta"] = compare_visible(source, dds, tolerance, f"{name}.dds")
            item["xlp"] = [file.name for file, _ in matches]
        report.append(item)
    return {"ok": True, "scope": "png-and-export-chain" if project else "source-png", "tolerance": tolerance, "textures": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--png-dir", required=True, type=Path)
    parser.add_argument("--project", type=Path, help="Exported ModBuddy project directory, not the .civ6proj file")
    parser.add_argument("--tolerance", type=int, default=0, help="Maximum per-channel alpha/visible-pixel difference (default: exact)")
    args = parser.parse_args()
    require(0 <= args.tolerance <= 255, "Tolerance must be in 0..255")
    print(json.dumps(verify(args.manifest, args.png_dir, args.project, args.tolerance), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, OSError, ET.ParseError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        sys.exit(1)
