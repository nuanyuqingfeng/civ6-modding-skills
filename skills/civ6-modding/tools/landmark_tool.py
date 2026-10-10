# -*- coding: utf-8 -*-
"""landmark_tool —— 静态地标（SDK TileBase AST 组合）全流程 CLI，与 .CIV 工程通道完全解耦。

移植与适配来源：ModTools 5.4（MIT，Copyright (c) 2026 Siqi）
- 算法层 `landmark_lib/landmarks.py` ← `ModTools_5_4/project/landmarks.py`（原样复制 + 模板参数化）；
- `verify_bundle` / `cook_bundle` ← `modgen/landmark.py`（移植）；
- `install_bundle` 为本 skill 新写（替代 ModTools 的 `import` CIV 通道，见下）。

与 ModTools 版的差异（设计决议 D6：.civ6proj 保持手工维护）：
1. 不提供 `import`（写入 .CIV）；落地走 `install`——把 bundle 文件放进 ModBuddy 工程
   标准目录（Assets/Geometries/Materials/Textures 为 pantry 源，ArtDefs/XLPs 为编译项），
   合并 Landmarks/Buildings artdef，回填实体条目的 Landmark Xref；
   ArtDefs/XLPs 不登记 .civ6proj（官方 Civ6.targets 直接扫描磁盘，见 civ6-landmarks
   references/landmarks.md）；check_proj_content.py 照跑，核对工程既有清单闭合。
2. `verify --project` 不检查 civ6proj 内的美术源登记残留（本家族规则：美术源与
   ArtDefs/XLPs 一律不进 Content/Folder/None）。
3. cook 直接调官方 Cooker（ASCII 暂存、不部署）；整机 cook 仍用 `cook_assets.py`。

用法：
    python landmark_tool.py catalog  --sdk-assets <SDK Assets> [--query 关键词]
    python landmark_tool.py compose  --recipe r.json --sdk-assets <SDK Assets> --out <bundle 目录> [--template t.artdef]
    python landmark_tool.py verify   --bundle <manifest.json> [--sdk-assets X] [--project <工程根>]
    python landmark_tool.py install  --bundle <manifest.json> --project <工程根> [--force] [--dry-run]
    python landmark_tool.py cook     --bundle <manifest.json> --sdk-assets X [--sdk <SDK 根>] --out <输出目录> [--project <工程根>]

退出码：0 成功；1 结果含错误；2 用法/环境错误，或本次有改写被 guard 入位 workspace/gen。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
_SCRIPTS_DIR = _TOOLS_DIR.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _projwrite import is_direct, write_project_file, finish  # noqa: E402
from landmark_lib import (  # noqa: E402
    SDKIndex,
    LocalResourceIndex,
    compose,
    load_bundle,
    validate_assets,
    validate_local_sources,
    merge_artdef,
    text_at,
    xml_text,
)

SOURCE_DIRS = ("Assets", "Geometries", "Materials", "Textures")


def default_sdk_assets() -> Path | None:
    """--sdk-assets > 环境变量 CIV6_SDK_ASSETS > 本机路径真源 _paths（P4）。"""
    env = os.environ.get("CIV6_SDK_ASSETS")
    if env and Path(env).is_dir():
        return Path(env)
    try:
        from _paths import get
        value = get("sdk_assets", must_exist=False)
        if value and Path(value).is_dir():
            return Path(value)
    except Exception:
        pass
    return None


def default_sdk_tools() -> Path | None:
    try:
        from _paths import get
        value = get("sdk", must_exist=False)
        if value and Path(value).is_dir():
            return Path(value)
    except Exception:
        pass
    return None


# ------------------------------------------------------------------ verify（移植自 modgen/landmark.py）

def verify_bundle(manifest: Path, sdk_assets: Path | None = None, project: Path | None = None) -> dict:
    data, files = load_bundle(manifest)
    assets = {Path(name).stem: ET.fromstring(content) for name, content in files.items() if name.endswith('.ast')}
    index = LocalResourceIndex(manifest.parent, files, SDKIndex(sdk_assets) if sdk_assets else None)
    errors = validate_assets(assets, index if sdk_assets else None)
    errors += validate_local_sources(manifest.parent, files, index) if data['version'] == 2 else []
    xlp = ET.fromstring(files['XLPs/tilebases.xlp'])
    entries = [(text_at(e, 'm_EntryID'), text_at(e, 'm_ObjectName')) for e in xlp.findall('./m_Entries/Element')]
    if set(entries) != {(name, name) for name in assets} or len(entries) != len(assets):
        errors.append('XLP must register every AST exactly once with matching EntryID/ObjectName')
    landmarks = ET.fromstring(files['ArtDefs/Landmarks.artdef'])
    for p in landmarks.findall('.//Element[@class="AssetObjects..BLPEntryValue"]'):
        if text_at(p, 'm_EntryName') not in assets:
            errors.append('Landmarks references unknown asset ' + text_at(p, 'm_EntryName'))
    for binding in data['bindings']:
        coll = 'Districts' if binding['kind'] == 'district' else 'Landmarks'
        collection = next((c for c in landmarks.findall('./m_RootCollections/Element') if text_at(c, 'm_CollectionName') == coll), None)
        if collection is None or binding['landmark'] not in {text_at(e, 'm_Name') for e in collection.findall('Element')}:
            errors.append(f"Missing landmark {binding['landmark']}")
    if project:
        for name, content in files.items():
            p = project / name
            if name == 'ArtDefs/Buildings.artdef' and p.exists():
                # Supplemental built-in entries coexist with this mod's buildings.
                exported = ET.parse(p).getroot()
                entries_by_name = {text_at(e, 'm_Name'): e for e in exported.findall('./m_RootCollections/Element/Element')}
                for e in ET.fromstring(content).findall('./m_RootCollections/Element/Element'):
                    building = text_at(e, 'm_Name')
                    actual = entries_by_name.get(building)
                    if actual is None:
                        errors.append('Missing supplemental building: ' + building)
                        continue
                    fields = {text_at(p, 'm_ParamName'): p for p in actual.findall('./m_Fields/m_Values/Element')}
                    for expected in e.findall('./m_Fields/m_Values/Element'):
                        name_p = text_at(expected, 'm_ParamName')
                        field = fields.get(name_p)
                        if field is None or field.get('class') != expected.get('class') or any(
                            field.findtext(value.tag) != value.text
                            for value in expected if value.tag != 'm_ParamName'
                        ):
                            errors.append(f'Invalid supplemental building field: {building}.{name_p}')
                continue
            if not p.exists() or (p.read_bytes() if isinstance(content, bytes) else p.read_text(encoding='utf-8-sig')) != content:
                errors.append(f'Generated project differs from bundle: {name}')
        for binding in data['bindings']:
            path = project / 'ArtDefs' / ('Districts.artdef' if binding['kind'] == 'district' else 'Improvements.artdef')
            if not path.exists():
                errors.append(f'Missing {path.name}'); continue
            root = ET.parse(path).getroot()
            entry = next((e for e in root.findall('./m_RootCollections/Element/Element') if text_at(e, 'm_Name') == binding['entity']), None)
            refs = [] if entry is None else [p for p in entry.findall('.//Element[@class="AssetObjects..ArtDefReferenceValue"]') if text_at(p, 'm_ParamName') == 'Xref' and text_at(p, 'm_ArtDefPath') == 'Landmarks.artdef']
            if len(refs) != 1 or text_at(refs[0], 'm_ElementName') != binding['landmark']:
                errors.append(f"Broken entity -> Landmark binding: {binding['entity']}")
        art_files = list(project.glob('*.Art.xml'))
        if len(art_files) != 1:
            errors.append('Expected exactly one Art.xml')
        else:
            root = ET.parse(art_files[0]).getroot()
            lib = next((e for e in root.findall('./gameLibraries/Element') if text_at(e, 'libraryName') == 'TileBase'), None)
            if lib is None or not any(e.get('text') == 'landmarks/tilebases' or e.text == 'landmarks/tilebases' for e in lib.iter()):
                errors.append('Art.xml TileBase library lacks landmarks/tilebases')
            actual_ids = {text_at(e, 'id') for e in root.findall('./requiredGameArtIDs/Element')}
            for identity in data.get('required_game_art_ids', []):
                if identity['id'] not in actual_ids:
                    errors.append('Art.xml missing SDK dependency: ' + identity['name'])
            consumer = next((e for e in root.findall('./artConsumers/Element') if text_at(e, 'consumerName') == 'Landmarks'), None)
            if consumer is None or not any(e.get('text') == 'Landmarks.artdef' for e in consumer.findall('./relativeArtDefPaths/Element')) or not any(e.get('text') == 'TileBase' for e in consumer.findall('./libraryDependencies/Element')):
                errors.append('Art.xml Landmarks consumer is incomplete')

    return {'ok': not errors, 'assets': len(assets), 'bindings': len(data['bindings']), 'errors': errors}


# ------------------------------------------------------------------ install（本 skill 新写：解耦 .CIV）

def _read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8-sig')


def _inside(path: Path, root: Path) -> bool:
    """path 是否位于 root 之内（用于判断 --out 是否落在工程里）。"""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _find_project(path: Path) -> Path | None:
    """从 path 向上找最近的工程根（含 *.civ6proj 的目录）；找不到返回 None。"""
    for candidate in (path, *path.parents):
        if candidate.is_dir() and next(candidate.glob('*.civ6proj'), None):
            return candidate
    return None


def _entity_artdef_path(project: Path, kind: str) -> Path:
    return project / 'ArtDefs' / ('Districts.artdef' if kind == 'district' else 'Improvements.artdef')


def install_bundle(manifest_path: Path, project: Path, *, force: bool = False, dry_run: bool = False) -> dict:
    """bundle → ModBuddy 工程。文件落位 + artdef 合并 + Xref 回填；ArtDefs/XLPs 不登记 .civ6proj。"""
    report = verify_bundle(manifest_path)
    if not report['ok']:
        raise ValueError('\n'.join(report['errors']))
    data, files = load_bundle(manifest_path)
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError(f'工程目录不存在：{project}')

    def guarded(dest, text):
        """既有文件有变化时由守卫入位 workspace/gen；返回值与 dest.write_text 相同。"""
        write_project_file(str(dest), text.encode('utf-8'), str(project))
        return len(text)

    written: list[str] = []
    merged: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    plan: list[tuple[Path, object, str]] = []  # (dest, content, mode)  mode: write|merge

    for name, content in files.items():
        top = name.split('/', 1)[0]
        if top in SOURCE_DIRS:
            plan.append((project / name, content, 'write'))
        elif name == 'ArtDefs/Landmarks.artdef':
            plan.append((project / name, content, 'merge-or-write'))
        elif name == 'ArtDefs/Buildings.artdef':
            plan.append((project / name, content, 'merge-or-write'))
        elif name == 'XLPs/tilebases.xlp':
            plan.append((project / name, content, 'write-guarded'))
        else:
            errors.append(f'bundle 内出现无法落地的文件：{name}')

    for dest, content, mode in plan:
        exists = dest.exists()
        if not exists:
            if not dry_run:
                write_project_file(str(dest), content, str(project))
            written.append(str(dest.relative_to(project)))
            continue
        current = dest.read_bytes() if isinstance(content, bytes) else _read_text(dest)
        if current == content:
            skipped = f'{dest.relative_to(project)}（与 bundle 一致）'
            written.append(skipped)
            continue
        if mode == 'merge-or-write' and not isinstance(content, bytes):
            if not dry_run:
                merged_text = merge_artdef(current, content if isinstance(content, str) else content.decode('utf-8'))
                guarded(dest, merged_text)
            merged.append(str(dest.relative_to(project)))
            continue
        if mode == 'write-guarded' and not force:
            errors.append(f'{dest.relative_to(project)} 已存在且与 bundle 不同（tilebases.xlp 必须与 AST 全集一致）；'
                          f'确认后加 --force 覆盖')
            continue
        if not dry_run:
            write_project_file(str(dest), content, str(project))
        written.append(f'{dest.relative_to(project)}（覆盖）' if mode == 'write-guarded' else str(dest.relative_to(project)))

    # 实体条目 → Landmark Xref 回填（Improvements/Districts.artdef 是 mod 自有内容，可改）
    binding_report = []
    for binding in data['bindings']:
        path = _entity_artdef_path(project, binding['kind'])
        info = {'entity': binding['entity'], 'kind': binding['kind'], 'landmark': binding['landmark'], 'artdef': None}
        if not path.exists():
            info['status'] = '缺少 ArtDef 文件（先按 civ6-art-reference 克隆实体条目）'
            binding_report.append(info); continue
        root = ET.parse(path).getroot()
        entry = next((e for e in root.findall('./m_RootCollections/Element/Element') if text_at(e, 'm_Name') == binding['entity']), None)
        if entry is None:
            info['status'] = '工程 ArtDef 中没有该实体条目（先克隆实体，再重跑 install）'
            binding_report.append(info); continue
        refs = [p for p in entry.findall('.//Element[@class="AssetObjects..ArtDefReferenceValue"]')
                if text_at(p, 'm_ParamName') == 'Xref' and text_at(p, 'm_ArtDefPath') == 'Landmarks.artdef']
        if len(refs) == 1:
            if not dry_run:
                refs[0].find('m_ElementName').set('text', binding['landmark'])
                guarded(path, xml_text(root))
            info['status'] = 'Xref 已指向 landmark' + ('（dry-run 未写入）' if dry_run else '')
        elif len(refs) == 0:
            info['status'] = ('条目缺少 Landmark Xref 参数——手工补一个 ArtDefReferenceValue：'
                              'm_ParamName=Xref、m_ArtDefPath=Landmarks.artdef、m_RootCollectionName=Landmarks、'
                              f'm_ElementName={binding["landmark"]}')
        else:
            info['status'] = f'条目有 {len(refs)} 个 Landmark Xref，结构异常，请人工检查'
        binding_report.append(info)

    # Art.xml 要点（只报告，不写工程文件）
    required_ids = data.get('required_game_art_ids', [])
    art_hint = None
    if required_ids:
        ids = '\n'.join(f'    <Element id="{i["id"]}" name="{i["name"]}" />' for i in required_ids)
        art_hint = (
            '<Mod.Art.xml> 需要以下三项（幂等核对，缺哪项补哪项；可对照 gen_modartxml.py 产物结构）：\n'
            '  ① gameLibraries 增加/确认：<Element><libraryName text="TileBase" /> ... landmarks/tilebases</Element>\n'
            '  ② requiredGameArtIDs 增加：\n' + ids + '\n'
            '  ③ artConsumers 增加 Landmarks 消费者：relativeArtDefPaths=Landmarks.artdef、libraryDependencies=TileBase'
        )
    followups = [
        'ArtDefs/XLPs 不登记 .civ6proj（Civ6.targets 直接扫描磁盘）；跑 scripts/check_proj_content.py 核对工程既有清单闭合',
        'Art.xml 三项核对/补齐（见 art_hint）',
        '整机 cook：python tools/cook_assets.py <工程根>；或本 bundle 隔离 cook：landmark_tool.py cook',
        '游戏内验收（外观 / 地块占用 / 与区域建筑差分的联动）',
    ]
    return {'ok': not errors, 'dry_run': dry_run, 'project': str(project),
            'written': written, 'merged': merged, 'bindings': binding_report,
            'art_hint': art_hint,
            'followups': followups, 'errors': errors + warnings}


# ------------------------------------------------------------------ cook（移植自 modgen/landmark.py）

def cook_bundle(manifest: Path, sdk_assets: Path, sdk: Path, output: Path, project: Path | None = None, *,
                project_root: Path | None) -> dict:
    """Stage to ASCII because the official Cooker corrupts non-ASCII pantry paths.

    No game deployment and no full mod build. Logs and staged files remain for
    diagnosis. Each run uses a new directory, so old BLPs cannot fake success.

    --out 落在工程内时每份产物都交给守卫：工程里尚不存在的照常直写，既有文件有变化
    则改写结果入位 workspace/gen。
    """
    report = verify_bundle(manifest, sdk_assets, project)
    if not report['ok']:
        raise ValueError('\n'.join(report['errors']))
    _, files = load_bundle(manifest)

    def routed(dest):
        """该产物是否落在工程内、且不属于可再生资产（需要交给守卫判定）。"""
        return (project_root is not None and _inside(dest.resolve(), project_root.resolve())
                and not is_direct(os.path.relpath(dest, project_root)))

    def emit(dest, data):
        """--out 与暂存目录在工程外时直写；落在工程内时交给守卫判定。"""
        if routed(dest):
            write_project_file(str(dest), data, str(project_root))
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as handle:
            handle.write(data)

    stage = Path(tempfile.mkdtemp(prefix='civ6-landmarks-'))
    if not str(stage).isascii():
        raise ValueError('Official Cooker needs an ASCII temporary directory; set TMP/TEMP to one')
    pantry = stage / 'pantry'; pantry.mkdir()
    for name, content in files.items():
        path = pantry / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content) if isinstance(content, bytes) else path.write_text(content, encoding='utf-8')
    if project:
        for path in (project / 'ArtDefs').glob('*.artdef'):
            if path.name != 'Landmarks.artdef':
                shutil.copy2(path, pantry / 'ArtDefs' / path.name)
        for path in project.glob('*.Art.xml'):
            shutil.copy2(path, pantry / path.name)
    cooker = sdk / 'AssetModTools/Cooker'
    executable = cooker / 'Civ6AssetCooker_FinalRelease.exe'
    if not executable.is_file():
        raise ValueError(f'Missing official Cooker: {executable}')
    pantries = [sdk_assets / 'Civ6/pantry', sdk_assets / 'Civ6/DLC/Shared/pantry',
                sdk_assets / 'Civ6/DLC/Expansion1/pantry', sdk_assets / 'Civ6/DLC/Expansion2/pantry']
    common = [str(executable), '--absolute_paths', '--no_mt', '--platform', 'Windows', '--pantry', str(pantry)]
    for path in pantries:
        if path.exists():
            common.extend(['--pantry', str(path)])
    common += ['--config', str(cooker / 'Civ6.cfg')]
    runs = []
    targets = [('XLP', 'XLPs/tilebases.xlp', '--stewpot', 'BLPs', 'BLPs/landmarks/tilebases.blp')]
    targets += [('ArtDef', 'ArtDefs/' + name + '.artdef', '--banquet_hall', 'ArtDefs', 'ArtDefs/' + name + '.artdef') for name in ('Landmarks', 'Districts', 'Improvements') if (pantry / ('ArtDefs/' + name + '.artdef')).exists()]
    for mode, relative, flag, directory, expected in targets:
        destination = stage / 'cooked' / directory; destination.mkdir(parents=True, exist_ok=True)
        cmd = common + ['--mode', mode, flag, str(destination), str(pantry / relative)]
        process = subprocess.run(cmd, cwd=cooker, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = process.stdout.decode('utf-8', errors='replace')
        log_path = stage / (Path(relative).stem + '-' + mode + '.log')
        emit(log_path, log.encode('utf-8'))
        artifact = stage / 'cooked' / expected
        failures = [line.strip() for line in log.splitlines() if re.search(r'\b(error|failed|failure)\b|could not find|could not load.*(?:asset|geometry|material)|does not exist|Unable to (?:load|open)', line, re.I)]
        warnings = [line.strip() for line in log.splitlines() if re.search(r'warn|empty OB|Geometry is required|Unable to find|Unable to auto-generate', line, re.I)]
        runs.append({'target': relative, 'exit_code': process.returncode, 'artifact': expected,
                     'bytes': artifact.stat().st_size if artifact.exists() else 0,
                     'errors': failures, 'warnings': warnings})
    output.mkdir(parents=True, exist_ok=True)
    for source in sorted((stage / 'cooked').rglob('*')):
        if source.is_file():
            emit(output / 'cooked' / source.relative_to(stage / 'cooked'), source.read_bytes())
    for log in stage.glob('*.log'):
        emit(output / log.name, log.read_bytes())
    result = {'ok': all(r['exit_code'] == 0 and r['bytes'] > 0 and not r['errors'] for r in runs),
              'stage': str(stage), 'runs': runs, 'visual_verified': False}
    emit(output / 'cook-report.json', (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return result


# ------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    # 写入作用域：--project，或 --out 自身所在的工程（向上找 *.civ6proj）。
    # --out 落在工程内时产物交给守卫判定；工程外与 %TEMP% 暂存目录直写。
    project: Path | None = None
    project_root: Path | None = None

    ap = argparse.ArgumentParser(description='静态地标组合/校验/落地/隔离 Cooker（与 .CIV 工程通道解耦）')
    sub = ap.add_subparsers(dest='op', required=True)

    p = sub.add_parser('catalog', help='只读检索 SDK TileBase AST')
    p.add_argument('--sdk-assets', default=None)
    p.add_argument('--query', default='')

    p = sub.add_parser('compose', help='从 JSON 配方生成托管 AST/XLP/Landmarks 资源包')
    p.add_argument('--recipe', required=True)
    p.add_argument('--sdk-assets', default=None)
    p.add_argument('--out', required=True)
    p.add_argument('--template', default=None, help='Landmarks.artdef 模板（默认 SDK pantry 官方文件，需含 DISTRICT_THEATER）')

    p = sub.add_parser('verify', help='校验包、可选 SDK 与已落地工程的引用链')
    p.add_argument('--bundle', required=True)
    p.add_argument('--sdk-assets', default=None)
    p.add_argument('--project', default=None)

    p = sub.add_parser('install', help='bundle 落地到 ModBuddy 工程（文件 + artdef 合并 + Xref 回填；.civ6proj 只出清单）')
    p.add_argument('--bundle', required=True)
    p.add_argument('--project', required=True)
    p.add_argument('--force', action='store_true', help='覆盖已存在且不同的 tilebases.xlp')
    p.add_argument('--dry-run', action='store_true')

    p = sub.add_parser('cook', help='ASCII 暂存目录运行官方 Cooker，不部署游戏')
    p.add_argument('--bundle', required=True)
    p.add_argument('--sdk-assets', default=None)
    p.add_argument('--sdk', default=None, help='SDK 工具根（默认 _paths P5）')
    p.add_argument('--out', required=True)
    p.add_argument('--project', default=None)

    args = ap.parse_args(argv)
    project = Path(args.project).resolve() if getattr(args, 'project', None) else None
    project_root = project if project is not None else (
        _find_project(Path(args.out).resolve()) if args.op == 'cook' else None)
    sdk_assets = Path(args.sdk_assets) if getattr(args, 'sdk_assets', None) else default_sdk_assets()
    if args.op in ('catalog', 'compose', 'cook') and (not sdk_assets or not sdk_assets.is_dir()):
        print('错误：找不到 SDK Assets（--sdk-assets / 环境变量 CIV6_SDK_ASSETS / _paths P4）', file=sys.stderr)
        return 2

    if args.op == 'catalog':
        result = SDKIndex(sdk_assets).catalog(args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.op == 'compose':
        template = Path(args.template) if args.template else None
        manifest = compose(Path(args.recipe), sdk_assets, Path(args.out), template)
        print(json.dumps({'manifest': str(manifest)}, ensure_ascii=False, indent=2))
        return 0
    if args.op == 'verify':
        result = verify_bundle(Path(args.bundle), sdk_assets,
                               Path(args.project) if args.project else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['ok'] else 1
    if args.op == 'install':
        result = install_bundle(Path(args.bundle), Path(args.project), force=args.force, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return (0 if result['ok'] else 1) if args.dry_run else (finish() or (0 if result['ok'] else 1))
    if args.op == 'cook':
        sdk = Path(args.sdk) if args.sdk else default_sdk_tools()
        if not sdk or not sdk.is_dir():
            print('错误：找不到 SDK 工具根（--sdk / _paths P5）', file=sys.stderr)
            return 2
        result = cook_bundle(Path(args.bundle), sdk_assets, sdk, Path(args.out), project,
                             project_root=project_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return finish() or (0 if result.get('ok') else 1)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
