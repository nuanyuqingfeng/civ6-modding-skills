# -*- coding: utf-8 -*-
"""ArtDef 引用链查询工具（civ6-art-reference skill）

用法:
  python art_lookup.py <关键词> [模板名]           # 查包含关键词的条目及其完整引用链
  python art_lookup.py --list <模板名> [前缀]      # 列出某模板全部条目（可按前缀过滤）
  python art_lookup.py --xlp <包名或文件名>        # 列出某 XLP 包的条目

索引自动从脚本同目录 ../assets/art_index.json(.gz) 读取；--index 可指定其他索引。
"""
import json, os, sys, gzip, argparse

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

def roots_of(idx):
    game = idx.get('roots', {}).get('game', '')
    sdk = idx.get('roots', {}).get('sdk', '')
    return game, sdk

def abs_path(idx, a):
    game, sdk = roots_of(idx)
    base = game if a.get('source') in ('base', 'dlc') else sdk
    return os.path.join(base, a['rel'].replace('/', os.sep))

def entry_strings(idx, artdef, name):
    """从源文件提取条目内的 StringValue（XrefName 等字符串引用参数）"""
    import re
    path = abs_path(idx, artdef)
    if not os.path.exists(path):
        return {}
    raw = open(path, 'rb').read().decode('utf-8', errors='replace')
    raw = raw.replace('\x00', '')
    # 定位条目 m_Name，再向前回溯至条目 Element 起点（向前取足够大的窗口覆盖整个条目）
    m = re.search(r'<m_Name text="%s"/>' % re.escape(name), raw)
    if not m:
        return {}
    # 条目边界：m_Name 之后是 </Element> 收尾，之前是整个子树；取前一个同级 <Element> 开头
    start = raw.rfind('<Element>', 0, m.start())
    # 向后截取到条目结束（m_Name 后一般紧跟 m_AppendMergedParameterCollections + </Element>）
    end = raw.find('</Element>', m.end())
    seg = raw[start:end] if start >= 0 and end > start else raw[max(0, m.start()-8000):m.end()+200]
    out = {}
    for sm in re.finditer(r'<m_Value text="([^"]*)"[^>]*/>\s*<m_ParamName text="([^"]+)"/>', seg):
        val, param = sm.group(1), sm.group(2)
        if val and (param.startswith('Xref') or param in ('SelectionRule', 'AudioEvent', 'Mode')):
            out.setdefault(param, []).append(val)
    return out

def query(idx, kw, tpl, show_strings):
    found = False
    for a in idx['artdefs']:
        if 'error' in a:
            continue
        if tpl and (a.get('template') or '').lower() != tpl.lower():
            continue
        hits = [e for e in a.get('entries', []) if e.get('name') and kw.lower() in e['name'].lower()]
        if not hits:
            continue
        found = True
        names = {e['name'] for e in hits}
        refs = [r for r in a.get('references', []) if r.get('entry') in names]
        blps = [r for r in refs if r['kind'] == 'blp']
        adrs = [r for r in refs if r['kind'] == 'artdef']
        print(f"\n=== {a['rel']}  (template={a.get('template')}, source={a['source']}) ===")
        for e in hits[:6]:
            print(f"  entry: {e['name']} (collection={e['collection']})")
        if len(hits) > 6:
            print(f"  ... 共 {len(hits)} 个匹配条目")
        if blps:
            print(f"  BLP 引用（模型/贴图终端引用）:")
            seen = set()
            for r in blps:
                key = (r['entryXLP'], r['package'])
                if key in seen:
                    continue
                seen.add(key)
                print(f"    [{r['entry']}] -> {r['entryXLP']}  @ {r['package']}  (xlp={r['xlppath']}, class={r['xlpclass']})")
                if len(seen) >= 20:
                    print(f"    ...（去重后 {len(seen)}+ 种，共 {len(blps)} 条）")
                    break
        if adrs:
            print(f"  ArtDef 间引用:")
            seen = set()
            for r in adrs:
                key = (r['entry'], r['path'], r['rootcoll'], r['element'])
                if key in seen:
                    continue
                seen.add(key)
                target = f"{r['path'] or '(本文件)'}::{r['rootcoll'] or ''}/{r['element'] or '(同名条目)'}"
                print(f"    [{r['entry']}] -> {target}")
                if len(seen) >= 20:
                    print(f"    ...（共 {len(adrs)} 条）")
                    break
        if show_strings:
            for e in hits[:6]:
                sv = entry_strings(idx, a, e['name'])
                if sv:
                    print(f"  字符串引用参数 [{e['name']}]:")
                    for p, vals in sv.items():
                        print(f"    {p} = {', '.join(vals[:8])}")
    return found

def list_template(idx, tpl, prefix):
    for a in idx['artdefs']:
        if 'error' in a:
            continue
        if (a.get('template') or '').lower() != tpl.lower():
            continue
        names = sorted({e['name'] for e in a.get('entries', []) if e.get('name') and (not prefix or e['name'].startswith(prefix))})
        if not names:
            continue
        print(f"\n=== {a['rel']} ({len(names)} 条目) ===")
        for i in range(0, len(names), 5):
            print('  ' + ', '.join(names[i:i+5]))

def list_xlp(idx, kw):
    for x in idx['xlps']:
        if 'error' in x:
            continue
        if kw.lower() in (x.get('rel') or '').lower() or kw.lower() in (x.get('packageName') or '').lower():
            print(f"\n=== {x['rel']} (className={x.get('className')}, package={x.get('packageName')}, {x.get('entryCount')} 条目) ===")
            names = [e['id'] for e in x.get('entries', []) if e.get('id')]
            for i in range(0, len(names), 5):
                print('  ' + ', '.join(names[i:i+5]))

def _crefs(a, coll=None, name=None, parent=None, param_prefix=None, kind=None, element=None):
    """从索引的 childReferences 里过滤子条目级引用"""
    out = []
    for r in a.get('childReferences', []):
        if coll and r.get('coll') != coll:
            continue
        if name and r.get('entry') != name:
            continue
        if parent and r.get('parent') != parent:
            continue
        if kind and r.get('kind') != kind:
            continue
        if param_prefix and not (r.get('param') or '').startswith(param_prefix):
            continue
        if element and r.get('element') != element:
            continue
        out.append(r)
    return out


def _blps(a, coll, name, parent=None):
    rs = _crefs(a, coll=coll, name=name, parent=parent, kind='blp')
    ids = []
    pkgs = []
    for r in rs:
        if r.get('entryXLP') and r['entryXLP'] not in ids:
            ids.append(r['entryXLP'])
        if r.get('package') and r['package'] not in pkgs:
            pkgs.append(r['package'])
    return ids, pkgs


def _params(a, coll, name, prefix, parent=None):
    """取某子条目下以 prefix 开头的引用参数值（如 Set* / Tag_HeroBuilding / Set_HeroBuildings / Tag_Era）"""
    vals = []
    for r in _crefs(a, coll=coll, name=name, parent=parent, param_prefix=prefix, kind='artdef'):
        if r.get('element') and r['element'] not in vals:
            vals.append(r['element'])
    return vals


def district_buildings(idx, dname):
    """列出某区域的 hero building 组合表：标签 -> 区内建筑 -> 底座/本体资产"""
    found = False
    for a in idx['artdefs']:
        if 'error' in a or (a.get('template') or '') != 'Landmarks':
            continue
        for e in a['entries']:
            if e.get('name') != dname:
                continue
            cc = e.get('childCollections') or {}
            if not cc:
                continue
            found = True
            print()
            print(f"=== {e['name']} @ {a['rel']}  (collection={e['collection']}) ===")
            if 'BuildingSets' in cc:
                print("  BuildingSets 组合表（标签 -> 区内 hero 建筑；模型不在这里）:")
                for lbl in cc['BuildingSets']:
                    refs = _params(a, 'BuildingSets', lbl, 'Set', e['name'])
                    print(f"    [{lbl}] -> {refs}")
            if 'BuildingVariants' in cc:
                print("  BuildingVariants（建筑本体模型）:")
                for n in cc['BuildingVariants']:
                    hero = _params(a, 'BuildingVariants', n, 'Tag_HeroBuilding', e['name'])
                    era = _params(a, 'BuildingVariants', n, 'Tag_Era', e['name'])
                    ids, pkgs = _blps(a, 'BuildingVariants', n, e['name'])
                    print(f"    [{n}] hero={hero} era={era} asset={ids} @ {pkgs}")
            if 'BaseVariants' in cc:
                print("  BaseVariants（区域底座模型）:")
                bylabel = {}
                for n in cc['BaseVariants']:
                    labs = _params(a, 'BaseVariants', n, 'Set_HeroBuildings', e['name'])
                    ids, pkgs = _blps(a, 'BaseVariants', n, e['name'])
                    for l in labs:
                        bylabel.setdefault(l, []).append((n, ids, pkgs))
                for l, items in bylabel.items():
                    for n, ids, pkgs in items:
                        print(f"    [{l}] {n} -> {ids} @ {pkgs}")
    if not found:
        print(f"（未找到区域条目 {dname}；请用 Landmarks 模板的条目名，如 DISTRICT_THEATER）")


def building_chain(idx, btype):
    """反查某建筑（Buildings.artdef 条目名）的 3D 模型链路"""
    print(f"########## {btype} ##########")
    for a in idx['artdefs']:
        if 'error' in a or (a.get('template') or '') != 'Buildings':
            continue
        for e in a['entries']:
            if e.get('name') != btype:
                continue
            print()
            print(f"[建筑条目] {btype} @ {a['rel']} (collection={e['collection']})")
            f = e.get('fields') or {}
            if f:
                print("  字段: " + ', '.join(f"{k}={v!r}" for k, v in f.items()))
                if f.get('AffectsDistrictBuildingSet') == 'true':
                    print("  -> AffectsDistrictBuildingSet=true：参与所在区域的 hero building 组合，模型由区域给出")
            sv = []
            for r in a.get('references', []):
                if r.get('entry') == btype and r.get('param') == 'XrefName' and r.get('element'):
                    if r['element'] not in sv:
                        sv.append(r['element'])
            if sv:
                print(f"  StrategicView（战略视图精灵）: {sv}")
    hits = []
    for a in idx['artdefs']:
        if 'error' in a or (a.get('template') or '') != 'Landmarks':
            continue
        for r in _crefs(a, coll='BuildingSets', param_prefix='Set', kind='artdef', element=btype):
            hits.append((a, r.get('parent'), r.get('entry')))
    if not hits:
        print()
        print("[模型链路] 未在任何 Landmarks 区域的 BuildingSets 中被引用 -> 不会有 3D 模型")
        print("           （若为奇观，模型走 Landmarks.artdef 独立条目 + WonderMovie.artdef）")
        return
    seen = []
    print()
    print("[模型链路] 由「所在区域」的 Landmarks 条目提供：")
    for a, parent, lbl in hits:
        k = (a['rel'], parent, lbl)
        if k in seen:
            continue
        seen.append(k)
        print(f"  · 区域 {parent} @ {a['rel']}  ->  BuildingSets 标签 [{lbl}]")
    printed = []
    for a, parent, lbl in hits:
        k = (a['rel'], parent)
        if k in printed:
            continue
        printed.append(k)
        e = None
        for x in a['entries']:
            if x.get('name') == parent:
                e = x
                break
        if e is None:
            continue
        cc = e.get('childCollections') or {}
        labels = []
        for l in cc.get('BuildingSets', []):
            if btype in _params(a, 'BuildingSets', l, 'Set', parent):
                labels.append(l)
        print()
        print(f"  --- {parent} @ {a['rel']} ---")
        print(f"      相关组合标签: {labels}")
        for n in cc.get('BuildingVariants', []):
            if btype in _params(a, 'BuildingVariants', n, 'Tag_HeroBuilding', e['name']):
                ids, pkgs = _blps(a, 'BuildingVariants', n, e['name'])
                print(f"      建筑本体[{n}] -> {ids} @ {pkgs}")
        for l in labels:
            for n in cc.get('BaseVariants', []):
                if l in _params(a, 'BaseVariants', n, 'Set_HeroBuildings', e['name']):
                    ids, pkgs = _blps(a, 'BaseVariants', n, e['name'])
                    print(f"      区域底座[{n}] 标签[{l}] -> {ids} @ {pkgs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('keyword', nargs='?', help='条目名关键词')
    ap.add_argument('template', nargs='?', help='模板名过滤（如 Resources/Clutter/Districts）')
    ap.add_argument('--list', metavar='TEMPLATE', help='列出模板全部条目')
    ap.add_argument('--prefix', default='', help='配合 --list 的前缀过滤')
    ap.add_argument('--xlp', metavar='PKG', help='列出 XLP 包条目')
    ap.add_argument('--building', metavar='BUILDING_X', help='反查某建筑的 3D 模型链路（所在区域 BuildingSets/BaseVariants/BuildingVariants）')
    ap.add_argument('--district-buildings', metavar='DISTRICT_X', help='列出某区域的 hero building 组合表（标签->建筑->资产）')
    ap.add_argument('--index', default=None)
    ap.add_argument('--no-strings', action='store_true', help='不回读源文件提取字符串引用参数')
    args = ap.parse_args()

    idx = load_index(args.index)
    if args.building:
        building_chain(idx, args.building)
    elif args.district_buildings:
        district_buildings(idx, args.district_buildings)
    elif args.xlp:
        list_xlp(idx, args.xlp)
    elif args.list:
        list_template(idx, args.list, args.prefix)
    elif args.keyword:
        if not query(idx, args.keyword, args.template, not args.no_strings):
            print(f"（索引中无匹配: {args.keyword}）")
    else:
        ap.print_help()

if __name__ == '__main__':
    main()
