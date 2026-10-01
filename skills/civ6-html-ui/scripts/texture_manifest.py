"""Portable texture manifest contract shared by standalone scripts and modgen.

No Qt, Pillow, browser, agent-specific runtime or repository imports required.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import struct


def load_manifest(manifest: Path) -> dict[str, list[int]]:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    specs = json.loads(Path(manifest).read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    if not isinstance(specs, dict) or not specs:
        raise ValueError("Manifest must be a nonempty object")
    names = set()
    for name, size in specs.items():
        if not re.fullmatch(r"UI_[A-Za-z0-9_]+", name):
            raise ValueError(f"Invalid name: {name}")
        if name.casefold() in names:
            raise ValueError(f"Case-insensitive duplicate: {name}")
        names.add(name.casefold())
        if not (isinstance(size, list) and len(size) == 2
                and all(type(v) is int and 1 <= v <= 8192 for v in size)):
            raise ValueError(f"Invalid dimensions for {name}: {size}")
    return specs


def source_entries(manifest: Path, png_dir: Path | None = None) -> list[dict[str, str]]:
    """Validate the entire batch before returning declarations; never write files."""
    manifest = Path(manifest).resolve()
    directory = Path(png_dir).resolve() if png_dir is not None else manifest.parent
    entries = []
    for name, size in load_manifest(manifest).items():
        source = (directory / f"{name}.png").resolve()
        if not source.is_relative_to(directory):
            raise ValueError(f"PNG escapes its source directory: {name}")
        with source.open("rb") as stream:
            header = stream.read(24)
        if (len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n"
                or header[8:12] != b"\x00\x00\x00\r" or header[12:16] != b"IHDR"):
            raise ValueError(f"Invalid PNG header: {source}")
        actual = struct.unpack(">II", header[16:24])
        if actual != tuple(size):
            raise ValueError(f"Wrong dimensions: {source}: {actual}, expected {size}")
        entries.append({"name": name, "path": str(source)})
    return entries
