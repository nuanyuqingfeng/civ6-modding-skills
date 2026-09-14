# -*- coding: utf-8 -*-
"""ArtDef 条目克隆生成器（civ6-art-reference skill）

把原版 artdef 条目完整克隆为 mod 侧新条目（改名 + 可选替换 XrefName），
追加写入 mod 的 artdef 文件（不存在则自动创建骨架）。这是"完整复制其美术素材引用"
的落地工具——克隆出的条目引用原版已打包资产（BLP 按名引用），无需携带任何模型文件。

用法:
  python art_copy.py <模板名> <原版条目> <新条目名> [选项]

示例:
  # 克隆原版橄榄资源条目为新资源，XrefName 换成原版 clutter
  python art_copy.py Resources RESOURCE_OLIVES RESOURCE_OLIVES_RGN \
      --set-xref CLUTTER_OLIVES --out "D:/mod/ArtDefs/Resources.artdef"

选项:
  --set-xref NAME   把条目内全部 XrefName 字符串值替换为 NAME（一般指向原版
                    CLUTTER_*，也可以是 Landmark 条目名）
  --out PATH        目标 mod artdef 文件（缺省仅打印到 stdout）
  --dry-run         只打印生成结果，不写文件
  --index PATH      指定索引文件（默认 ../assets/art_index.json.gz）

注意:
  - 克隆保留原条目的全部子集合（Clutter/Landmark/Audio/ClutterVariants 与
    Feature/Terrain 变体），--set-xref 会统一替换所有 XrefName（含变体）；
    需要精细区分变体时克隆后手改。
  - 音频参数（XrefStop/Xref3DName）若含原条目名会被同步替换为新条目名。
"""
import json, os, sys, gzip, argparse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INDEX = os.path.join(HERE, '..', 'assets', 'art_index.json.gz')

def load_index(path=None):
    path = path or DEFAULT_INDEX
    if not os.path.exists(path):
        alt = path[:-3] if path.endswith('.gz') else path + '.gz'
        if os.path.exists(alt):
            path = alt
        else:
            sys.exit(f"索引不存在: {path}（先运行 artdef_indexer.py 生成）")
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rb') as f:
        return json.loads(f.read().decode('utf-8'))

def load_xml(path):
    raw = open(path, 'rb').read().decode('utf-8', errors='replace').replace('\x00', '')
    import re
    raw = re.sub(r'AssetObjects::?', 'AssetObjects..', raw)
    return ET.fromstring(raw)

def tag_local(t):
    return t.rsplit('}', 1)[-1]

SOURCE_RANK = {'base': 0, 'dlc': 1, 'sdk': 2, 'sdkdlc': 3}

def find_source(idx, template, entry):
    """定位含该条目的原版 artdef（base 优先，其次 dlc 的 Expansion1/2）"""
    cands = []
    for a in idx['artdefs']:
        if 'error' in a:
            continue
        if (a.get('template') or '') != template:
            continue
        if any(e.get('name') == entry for e in a.get('entries', [])):
            rel = a['rel']
            dlc_rank = 0
            if 'Expansion2' in rel:
                dlc_rank = 3
            elif 'Expansion1' in rel:
                dlc_rank = 1
            elif a['source'] == 'dlc':
                dlc_rank = 2
            cands.append((SOURCE_RANK.get(a['source'], 9), dlc_rank, a))
    if not cands:
        return None
    cands.sort(key=lambda c: (c[0], c[1]))
    return cands[0][2]

def extract_entry(idx, artdef, entry):
    """从源文件提取条目 Element（深拷贝）"""
    path = os.path.join(idx['roots']['game'] if artdef['source'] in ('base', 'dlc') else idx['roots']['sdk'],
                        artdef['rel'].replace('/', os.sep))
    root = load_xml(path)
    rc = root.find('m_RootCollections')
    for coll in list(rc):
        if tag_local(coll.tag) != 'Element':
            continue
        for child in list(coll):
            if tag_local(child.tag) != 'Element':
                continue
            nm = child.find('m_Name')
            if nm is not None and nm.get('text') == entry:
                return child, coll.find('m_CollectionName').get('text') if coll.find('m_CollectionName') is not None else 'Element'
    sys.exit(f"源文件中未找到条目: {entry}")

def rename_entry(el, old, new):
    """改名: 条目 m_Name + 指向自身的引用（m_ElementName == 旧名）+ 音频等字符串参数中的旧名"""
    nm = el.find('m_Name')
    if nm is not None:
        nm.set('text', new)
    for sub in el.iter():
        cls = sub.get('class') or ''
        if 'ArtDefReferenceValue' in cls:
            # 指向旧条目本身的引用（Xref3D 等自引用约定）随条目改名
            en = sub.find('m_ElementName')
            if en is not None and en.get('text') == old:
                en.set('text', new)
            continue
        if 'StringValue' not in cls:
            continue
        v = sub.find('m_Value')
        pn = sub.find('m_ParamName')
        if v is None or pn is None:
            continue
        # 只改音频引用类参数，避免误伤 XrefName（由 --set-xref 控制）
        if pn.get('text').startswith('Xref') and pn.get('text') != 'XrefName':
            if old in (v.get('text') or ''):
                v.set('text', (v.get('text') or '').replace(old, new))

def set_xrefs(el, value):
    for sub in el.iter():
        cls = sub.get('class') or ''
        if 'StringValue' not in cls:
            continue
        pn = sub.find('m_ParamName')
        v = sub.find('m_Value')
        if pn is not None and pn.get('text') == 'XrefName' and v is not None:
            v.set('text', value)

def serialize(el):
    # 深拷贝后规范化缩进（源文件遗留的空白会被 ET 保留，直接序列化会深浅不一）
    import copy
    el = copy.deepcopy(el)
    if hasattr(ET, 'indent'):
        ET.indent(el, space='\t')
    text = ET.tostring(el, encoding='unicode')
    # 条目位于根集合 Element 之下（3 个 tab 层级）
    out = []
    for line in text.splitlines():
        out.append('\t\t\t' + line if line.strip() else line)
    return '\n'.join(out)

def file_skeleton(template, collection):
    return f'''<?xml version="1.0" encoding="UTF-8" ?>
<AssetObjects..ArtDefSet>
\t<m_Version>
\t\t<major>1</major>
\t\t<minor>0</minor>
\t\t<build>0</build>
\t\t<revision>0</revision>
\t</m_Version>
\t<m_TemplateName text="{template}"/>
\t<m_RootCollections>
\t\t<Element>
\t\t\t<m_CollectionName text="{collection}"/>
\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>
\t\t</Element>
\t</m_RootCollections>
</AssetObjects..ArtDefSet>
'''

def find_rootcoll_close(raw, from_pos):
    """从 marker 之后扫描，找到第一个根集合闭合 </Element>。
    三种标签形态需区分：
      <Element>            结构开标签  → 深度 +1
      <Element class=...>  值开标签    → 深度 +1
      <Element ... />      值自闭合    → 不计数
      </Element>           闭标签      → 深度 -1
    """
    import re
    tok = re.compile(r'<Element[^>]*?>|</Element>')
    depth = 0
    for m in tok.finditer(raw, from_pos):
        t = m.group(0)
        if t == '</Element>':
            depth -= 1
            if depth < 0:
                return m.start()
        elif t.endswith('/>'):
            continue
        else:
            depth += 1
    return -1

def insert_into_file(path, entry_el, template, collection, dry_run=False):
    """追加条目到 mod artdef（文件存在则合并，否则建骨架）"""
    marker = '\t\t\t<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>'
    snippet = serialize(entry_el)
    if os.path.exists(path):
        raw = open(path, 'rb').read().decode('utf-8')
        root = load_xml(path)
        tpl = root.find('m_TemplateName')
        if tpl is None or tpl.get('text') != template:
            sys.exit(f"目标文件模板不匹配: {path} ({tpl.get('text') if tpl is not None else '?'} != {template})")
        # ET 序列化会在 /> 前带空格，重复检测须兼容两种写法
        import re as _re
        if _re.search(r'<m_Name text="%s"\s*/>' % _re.escape(entry_el.find('m_Name').get('text')), raw):
            print(f"WARN: 条目已存在于目标文件，跳过: {entry_el.find('m_Name').get('text')}")
            return
        # 插到第一个根集合的闭合 </Element> 之前
        i = raw.find(marker)
        if i < 0:
            sys.exit(f"目标文件结构异常（找不到根集合标记）: {path}")
        close = find_rootcoll_close(raw, i)
        if close < 0:
            sys.exit(f"目标文件结构异常（找不到根集合闭合）: {path}")
        new = raw[:close].rstrip() + '\n' + snippet + '\n\t\t' + raw[close:]
    else:
        new = file_skeleton(template, collection)
        i = new.find(marker)
        close = new.find('</Element>', i)
        new = new[:close].rstrip() + '\n' + snippet + '\n\t\t' + new[close:]
    if not dry_run:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new)
    print(f"written: {path} (+{entry_el.find('m_Name').get('text')})" if not dry_run else f"[dry-run] {path} (+{entry_el.find('m_Name').get('text')})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('template')
    ap.add_argument('src_entry')
    ap.add_argument('new_entry')
    ap.add_argument('--set-xref', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--index', default=None)
    args = ap.parse_args()

    idx = load_index(args.index)
    src = find_source(idx, args.template, args.src_entry)
    if src is None:
        sys.exit(f"原版索引中未找到 {args.template} 模板条目: {args.src_entry}")
    print(f"源: {src['rel']} ({src['source']})")
    el, coll = extract_entry(idx, src, args.src_entry)
    rename_entry(el, args.src_entry, args.new_entry)
    if args.set_xref:
        set_xrefs(el, args.set_xref)
    # 报告克隆后剩余的引用
    blps = {(r.find('m_EntryName').get('text'), r.find('m_BLPPackage').get('text'))
            for r in el.iter() if (r.get('class') or '') == 'AssetObjects..BLPEntryValue'}
    if blps:
        print("保留的 BLP 直连引用:")
        for e, p in sorted(blps):
            print(f"   {e} @ {p}")
    sv = [(s.find('m_ParamName').get('text'), s.find('m_Value').get('text'))
          for s in el.iter() if (s.get('class') or '') == 'AssetObjects..StringValue'
          and s.find('m_ParamName') is not None and s.find('m_Value') is not None
          and s.find('m_ParamName').get('text') == 'XrefName']
    if sv:
        print("XrefName:", ', '.join(sorted({v for _, v in sv})))
    if args.out:
        insert_into_file(args.out, el, args.template, coll, args.dry_run)
    else:
        print('--- 条目 XML ---')
        print(serialize(el))

if __name__ == '__main__':
    main()
