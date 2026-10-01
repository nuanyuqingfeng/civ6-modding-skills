#!/usr/bin/env python3
"""Read-only authoring checks; does not emulate ForgeUI or prove in-game rendering."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from texture_manifest import load_manifest


def pair(value):
    try:
        parts = [int(x.strip()) for x in value.split(',')]
        return tuple(parts) if len(parts) == 2 else None
    except (AttributeError, ValueError):
        return None


def check(xml: Path, specs: dict, fonts: set[str] | None = None):
    root = ET.parse(xml).getroot()
    parents = {child: parent for parent in root.iter() for child in parent}
    errors, warnings = [], []
    for node in root.iter():
        label = f'{xml.name}:{node.get("ID", node.tag)}'
        style = node.get('Style', '')
        if fonts is not None and re.match(r'^Font(?:Normal|Flair|Bold|Italic)', style) and style not in fonts:
            errors.append(f'{label}: unknown font style {style}')
        texture = node.get('Texture', '')
        if node.tag == 'GridData' and texture in specs:
            warnings.append(f'{label}: nine-slice requires native min/max-size verification')
        if node.tag != 'Button' or texture not in specs:
            continue
        size = pair(node.get('Size'))
        increment = pair(node.get('StateOffsetIncrement', '0,0'))
        offset = pair(node.get('TextureOffset', '0,0'))
        try:
            states = int(node.get('States', '1'))
        except ValueError:
            states = 0
        if size is None or increment is None or offset is None or states < 1:
            errors.append(f'{label}: explicit numeric Size/states/frame geometry required')
            continue
        width, height = size
        tw, th = specs[texture]
        if width <= 0 or height <= 0 or width != tw or offset != (0, 0):
            errors.append(f'{label}: fixed atlas requires positive dimensions, frame-width equality and zero initial offset')
        if states > 1 and increment != (0, height):
            errors.append(f'{label}: expected vertical state increment 0,{height}')
        if height * states != th:
            errors.append(f'{label}: atlas height {th} does not equal {states} frames of {height}')
        parent = parents.get(node)
        bounds = pair(parent.get('Size')) if parent is not None else None
        position = pair(node.get('Offset', '0,0'))
        # Deliberately limited to direct numeric L,T containers; Stack/Scroll/animations differ.
        if parent is not None and parent.tag == 'Container' and bounds and position and node.get('Anchor','L,T') == 'L,T':
            x, y = position
            if min(x,y) < 0 or x+width > bounds[0] or y+height > bounds[1]:
                errors.append(f'{label}: button hit area exceeds its direct container')
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--xml', type=Path, action='append', required=True)
    parser.add_argument('--font-styles', type=Path, action='append')
    args = parser.parse_args(argv)
    try:
        specs = load_manifest(args.manifest)
        fonts = None
        if args.font_styles:
            fonts = {node.tag for file in args.font_styles for node in ET.parse(file).getroot().iter()}
        errors, warnings = [], []
        for file in args.xml:
            e, w = check(file, specs, fonts)
            errors.extend(e); warnings.extend(w)
        print(json.dumps({'ok': not errors, 'errors': errors, 'warnings': warnings}, ensure_ascii=False, indent=2))
        return int(bool(errors))
    except (OSError, ValueError, ET.ParseError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
