# -*- coding: utf-8 -*-
"""示例工程 pantry 体检 —— 开 AssetEditor / cook 前必跑。

pantry = 本工程目录。AssetEditor / cooker 会**递归扫描整棵目录树**，
任何位置的 .tex 都会被当作贴图实体注册；重复 .tex / 库路径会直接导致 AE 闪退
（NotSupportedException: 不支持给定路径的格式 → CRASH: Multiple Aggregated Exceptions）。

用法：
    python workspace/_tools/check_pantry.py [--root <pantry 路径>] [--quiet]

退出码：0 = 通过（可能有 warning）；1 = 有 error，禁止开 AE / cook。
"""
import argparse
import collections
import os
import re
import sys

CANON_TEX_DIR = 'Textures'
SRC_ABS_OK = re.compile(r'^[A-Za-z]:\\desktop\\(?:[A-Za-z0-9_.\-]+\\+)*(?P<stem>[A-Za-z0-9_.\-]+)\.png$')


def read_text(path):
    """按 .tex 可能的声明编码读入（UTF-8 / GBK），同时返回原始字节。"""
    raw = open(path, 'rb').read()
    for enc in ('utf-8', 'gbk'):
        try:
            return raw.decode(enc), raw
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace'), raw


def find_tex(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != '.git']
        for f in fn:
            if f.lower().endswith('.tex'):
                out.append(os.path.join(dp, f))
    return sorted(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.abspath(os.path.join(here, '..', '..'))
    ap = argparse.ArgumentParser(description='pantry 卫生体检（.tex 铁律）')
    ap.add_argument('--root', default=default_root, help='pantry 根（默认本工程目录）')
    ap.add_argument('--quiet', action='store_true', help='只打印汇总')
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    errors, warnings = [], []
    tex = find_tex(root)
    names = collections.defaultdict(list)
    rels = collections.defaultdict(list)

    for p in tex:
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        stem = os.path.splitext(os.path.basename(p))[0]
        text, raw = read_text(p)
        m_name = re.search(r'<m_Name text="([^"]*)"', text)
        m_rel = re.search(r'<m_RelativePath text="([^"]*)"', text)
        m_src = re.search(r'<m_SourceFilePath text="([^"]*)"', text)

        # 1) .tex 只允许在 Textures/
        if rel.split('/')[0] != CANON_TEX_DIR:
            errors.append('[tex-outside] %s —— .tex 必须在 %s/ 下' % (rel, CANON_TEX_DIR))
        # 4) depot / 库路径
        if '//civ6/' in text:
            errors.append('[depot-path] %s 含 //civ6/ 库路径' % rel)
        # 5) 非 ASCII 字节
        if any(b > 127 for b in raw):
            errors.append('[non-ascii-bytes] %s 含非 ASCII 字节' % rel)

        if not m_name:
            errors.append('[missing-name] %s 缺 m_Name' % rel)
        else:
            names[m_name.group(1)].append(rel)
        if not m_rel:
            errors.append('[missing-relpath] %s 缺 m_RelativePath' % rel)
        else:
            rels[m_rel.group(1)].append(rel)

        # 6) 源路径约定：D:\desktop\<stem>.png
        if not m_src:
            errors.append('[missing-src] %s 缺 m_SourceFilePath' % rel)
        else:
            v = m_src.group(1)
            mt = SRC_ABS_OK.match(v)
            if not mt or mt.group('stem') != stem:
                warnings.append('[src-convention] %s  m_SourceFilePath=%r（期望 D:\\desktop\\%s.png）'
                                % (rel, v, stem))

    # 2/3) 全工程重名
    for n, ps in sorted(names.items()):
        if len(ps) > 1:
            errors.append('[dup-name] m_Name=%r 出现 %d 次: %s' % (n, len(ps), ', '.join(ps)))
    for n, ps in sorted(rels.items()):
        if len(ps) > 1:
            errors.append('[dup-relpath] m_RelativePath=%r 出现 %d 次: %s' % (n, len(ps), ', '.join(ps)))

    # 7) 非 ASCII 文件名（排除 .git 与 workspace/ —— workspace 是素材区）
    nonascii = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != '.git']
        r = os.path.relpath(dp, root).replace(os.sep, '/')
        if r == 'workspace' or r.startswith('workspace/'):
            continue
        for f in fn:
            if any(ord(c) > 127 for c in f):
                nonascii.append((r + '/' + f) if r != '.' else f)
    for f in nonascii[:20]:
        warnings.append('[non-ascii-name] %s' % f)
    if len(nonascii) > 20:
        warnings.append('[non-ascii-name] ... 共 %d 个' % len(nonascii))

    # 8) .tex <-> .dds 配对（仅 Textures/）
    tdir = os.path.join(root, CANON_TEX_DIR)
    if os.path.isdir(tdir):
        tset = {os.path.splitext(f)[0] for f in os.listdir(tdir) if f.lower().endswith('.tex')}
        dset = {os.path.splitext(f)[0] for f in os.listdir(tdir) if f.lower().endswith('.dds')}
        for s in sorted(tset - dset):
            warnings.append('[no-dds] %s.tex 无同名 .dds' % s)
        for s in sorted(dset - tset):
            warnings.append('[no-tex] %s.dds 无同名 .tex' % s)

    print('pantry root : %s' % root)
    print('.tex 总数   : %d' % len(tex))
    print('error       : %d    warning : %d' % (len(errors), len(warnings)))
    if not args.quiet:
        for e in errors:
            print('  ERROR   ' + e)
        for w in warnings:
            print('  WARN    ' + w)
    if errors:
        print('\n结论：%d 个 error —— 禁止开 AssetEditor / cook。' % len(errors))
        return 1
    print('\n结论：通过（%d warning，不阻断）。' % len(warnings))
    return 0


if __name__ == '__main__':
    sys.exit(main())
