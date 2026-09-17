#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""align_tex_format.py — 把工程 `.tex` 的**格式类字段**对齐官方 pantry 约定

## 背景

`Textures/*.tex` 是 AssetEditor 的贴图元数据。工程里的 `.tex` 由不同批次、不同工具
生成，格式上出现三类与官方不一致的偏差（**都不影响当前构建**，但会造成：

  - 编码不一致 → 某些工具/编辑器读写时乱码风险；
  - `m_Groups` 缺失 → 与官方结构不一致，重新导入时可能被 AssetEditor 补写；
  - `bCompleteMipChain` 与官方同类贴图相反 → 语义上声明"不生成完整 mip 链"，
    与官方同类别（Generic_BaseColor / StrategicView_Sprite）的 true 相悖。

## 对齐范围（**只动格式，不动值**）

| 字段 | 官方约定 | 处理 |
|------|---------|------|
| XML 声明 `encoding` + 文件字节编码 | 100% `UTF-8` | 统一为 UTF-8（无 BOM） |
| `m_Groups` | 官方多数为自闭合 `<m_Groups/>` | 缺失则补 `<m_Groups/>` |
| 行尾 | 100% LF | 已是 LF，保持 |
| `bCompleteMipChain` | 按 `m_ClassName` 逐类决定（≥80% 一致才动） | 见下 |
| `useMips` / `m_NumMipMaps` | 由 DDS 实际 mips 决定（官方不变量 `numMipMaps = mips-1`） | **校验**，不改值 |

**绝不动**的字段（值语义，抄官方会破坏工程约定）：
`m_Width` / `m_Height` / `ePixelformat` / `m_ClassName` / `m_SourceFilePath`
（AGENTS.md：必须是 `D:/desktop/<stem>.png` 虚拟路径，严禁改成 `//civ6/...` depot 路径）
/ `m_Name` / `m_RelativePath` / `m_Tags` / `m_CookParams` 内的**参数值**。

## 用法

    python align_tex_format.py <projectRoot> --check     # 体检，只报告
    python align_tex_format.py <projectRoot> --write     # 实际改写
    python align_tex_format.py <projectRoot> --write --only encoding,groups,complete
    python align_tex_format.py <projectRoot> --check --list

退出码：0 = 无需改动 / 已改完；2 = --check 发现待改项；1 = 错误。
"""
import argparse
import glob
import os
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# bCompleteMipChain 的官方按类政策（来自全 SDK 12709 个 .tex 的统计，此处只列
# 一致率 ≥80% 的类；不在表内的类别一律不动该字段）
COMPLETE_POLICY = {
    'Generic_BaseColor': 'true',
    'Generic_Normal': 'true',
    'Generic_Gloss': 'true',
    'Generic_AO': 'true',
    'Generic_Metalness': 'true',
    'Generic_Emissive': 'true',
    'Generic_OPAC': 'true',
    'Generic_TintMask': 'true',
    'Generic_LightMap': 'true',
    'Generic_Roughness': 'true',
    'StrategicView_Sprite': 'true',
    'StrategicView_CultureBorder': 'true',
    'StrategicView_Riverbank': 'true',
    'Leader_BaseColor': 'true',
    'Leader_Normal': 'true',
    'Leader_AO': 'true',
    'Leader_Gloss': 'true',
    'Leader_OPAC': 'true',
    'Leader_Fallback': 'true',
    'Leader_Metalness': 'true',
    'Leader_Anisotropy': 'true',
    'Leader_Translucency': 'true',
    'Leader_BlurWidth': 'true',
    'Leader_Tangent': 'true',
    'Leader_Fuzz': 'true',
    'VFXParticle_BaseColor': 'true',
    'VFXParticle_Mask': 'true',
    'Decal_BaseColor': 'true',
    'Decal_Heightmap': 'true',
    'Decal_FOWColor': 'true',
    'Decal_Spec': 'true',
    'Overlay': 'true',
    'FOWSprite': 'true',
    'Terrain_BaseColor': 'true',
    'Terrain_FOWColor': 'true',
    'Terrain_Spec': 'true',
    'Terrain_Heightmap': 'true',
    'TerrainElementBlendmap': 'true',
    'WaterDensityMap': 'true',
    # 官方一致为 false 的类
    'TerrainElementHeightmap': 'false',
    'TerrainElementIDMap': 'false',
    'Terrain_EditHeightmap': 'false',
    'ColorKey': 'false',
    # UserInterface 官方 true 69% / false 31% → 未达 80%，**故意不列**（不动）
}


def read_tex(p):
    """→ (原始字节, 文本, 实际编码名)。按官方约定优先按 UTF-8 解，失败退 GBK。"""
    raw = Path(p).read_bytes()
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            return raw, raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw, raw.decode('latin-1', errors='replace'), 'latin-1'


def get(txt, pat, dflt=None):
    m = re.search(pat, txt)
    return m.group(1) if (m and m.groups()) else dflt


def dds_mips(p):
    if not os.path.isfile(p):
        return None
    with open(p, 'rb') as f:
        d = f.read(128)
    return struct.unpack('<I', d[28:32])[0] if d[:4] == b'DDS ' else None


def plan_one(tex_path, kinds):
    """→ (改动列表 [(kind, old, new)], 新文本 or None, 备注列表)。"""
    raw, txt, enc = read_tex(tex_path)
    changes, notes = [], []
    new = txt

    # 1) 声明编码 + 字节编码统一 UTF-8
    if 'encoding' in kinds:
        decl = get(txt, r'encoding="([^"]*)"')
        if decl != 'UTF-8':
            new = re.sub(r'(<\?xml[^>]*encoding=")[^"]*(")',
                         r'\1UTF-8\2', new, count=1)
            changes.append(('encoding-decl', decl, 'UTF-8'))
        if enc != 'utf-8':
            changes.append(('encoding-bytes', enc, 'utf-8'))

    # 2) m_Groups 补齐
    if 'groups' in kinds:
        if not re.search(r'<m_Groups', new):
            # 锚点优先级：</m_Tags> 闭合 → <m_Tags/> 自闭合 → </m_DataFiles>
            # （领袖/Generic 类用自闭合 <m_Tags/>，不能只认闭合标签）
            m = re.search(r'(</m_Tags>\s*)', new) or re.search(r'(<m_Tags\s*/>\s*)', new)
            if m:
                new = new[:m.end(1)] + '\t<m_Groups/>\n' + new[m.end(1):]
                changes.append(('groups', '缺失', '补 <m_Groups/>'))
            else:
                m2 = re.search(r'(</m_DataFiles>\s*)', new)
                if m2:
                    new = new[:m2.end(1)] + '\t<m_Groups/>\n' + new[m2.end(1):]
                    changes.append(('groups', '缺失', '补 <m_Groups/> (锚 </m_DataFiles>)'))
                else:
                    notes.append('无 m_Tags/DataFiles 锚点，未补 m_Groups')

    # 3) bCompleteMipChain 按官方类别政策
    if 'complete' in kinds:
        cls = get(txt, r'<m_ClassName text="([^"]*)"')
        want = COMPLETE_POLICY.get(cls)
        cur = get(txt, r'<bCompleteMipChain>([^<]*)<')
        if want and cur and cur != want:
            new = re.sub(r'(<bCompleteMipChain>)[^<]*(</bCompleteMipChain>)',
                         r'\g<1>' + want + r'\g<2>', new, count=1)
            changes.append(('complete', f'{cur} (cls={cls})', want))
        elif want is None:
            notes.append(f'类别 {cls} 未达官方一致率阈值，complete 不动')

    # 4) 不变量校验（只报告，不改）
    dp = tex_path[:-4] + '.dds'
    m = dds_mips(dp)
    nm = get(txt, r'<m_NumMipMaps>(\d+)</m_NumMipMaps>')
    um = get(txt, r'<bUseMips>(\w+)</bUseMips>')
    if m is not None and nm is not None:
        try:
            if int(nm) != m - 1:
                notes.append(f'!! numMipMaps={nm} != DDS mips-1={m-1}')
            if (m > 1) != (um == 'true'):
                notes.append(f'!! useMips={um} 与 DDS mips={m} 不匹配')
        except ValueError:
            notes.append(f'!! numMipMaps 非法: {nm}')

    return changes, (new if changes else None), notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('projectRoot')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--only', default='encoding,groups,complete',
                    help='要处理的项，逗号分隔（encoding/groups/complete）')
    ap.add_argument('--list', action='store_true', help='逐文件列出改动')
    args = ap.parse_args()
    if not (args.check or args.write):
        ap.error('需要 --check 或 --write')

    kinds = {k.strip() for k in args.only.split(',') if k.strip()}
    tex_dir = Path(args.projectRoot) / 'Textures'
    if not tex_dir.is_dir():
        raise SystemExit(f'找不到 {tex_dir}')

    files = sorted(glob.glob(str(tex_dir / '*.tex')))
    tally = Counter()
    todo = []
    notes_all = []
    for f in files:
        ch, new, notes = plan_one(f, kinds)
        for n in notes:
            notes_all.append((os.path.basename(f), n))
        if ch:
            todo.append((os.path.basename(f), ch, new))
            for k, _o, _n in ch:
                tally[k] += 1
        else:
            tally['无需改动'] += 1

    print(f'扫描 {len(files)} 个 .tex   处理项: {sorted(kinds)}')
    print()
    print('改动统计：')
    for k, v in tally.most_common():
        print(f'   {k:<18} ×{v}')

    if args.list and todo:
        print()
        print('逐文件：')
        for name, ch, _new in todo:
            print(f'   {name}')
            for k, o, n in ch:
                print(f'      {k}: {o} -> {n}')

    if notes_all:
        print()
        print(f'校验提示（{len(notes_all)} 条）：')
        for name, n in notes_all[:30]:
            print(f'   {name:<46} {n}')
        if len(notes_all) > 30:
            print(f'   ... 另 {len(notes_all)-30} 条')

    if args.write and todo:
        for name, _ch, new in todo:
            p = tex_dir / name
            # 官方约定：UTF-8 无 BOM + LF
            Path(p).write_bytes(new.replace('\r\n', '\n').encode('utf-8'))
        print()
        print(f'已改写 {len(todo)} 个 .tex（UTF-8 无 BOM + LF）')

    print()
    if todo and not args.write:
        print(f'[--check] {len(todo)} 个文件待改。加 --write 执行。')
        return 2
    if todo:
        print(f'完成：{len(todo)} 个文件已对齐官方格式。')
    else:
        print('全部已符合官方格式，无需改动。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
