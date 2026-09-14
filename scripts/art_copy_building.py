# -*- coding: utf-8 -*-
"""替换型建筑的 3D 模型注册生成器（civ6-art-reference skill）

给「新建筑 Type」挂上「被它替换的原版建筑」的模型：照原版 Ethiopia 结社建筑的做法，
在 Landmarks.artdef 里**增量**补三组子条目（绝不改名覆盖原版子条目）：

  BuildingSets      新标签组合                  -> 引用新建筑 Type
  BuildingVariants  Tag_HeroBuilding = 新建筑   -> 沿用原建筑的 hero_buildings 本体模型
  BaseVariants      同标签                      -> 沿用原建筑各时代 tilebases 区域底座

目标区域 = 自动反查到的游戏侧区域 + --district 指定的区域
（mod 侧区域不在索引里，必须用 --district 显式补，否则那条链没有模型）

要点（踩坑记录见 reference/chain-map.md 三.3）:
  · 建筑的模型不在 Buildings.artdef，而在「所在区域」的 Landmarks.artdef 条目里
  · 同名 artdef 条目是「按子集合、按子条目名增量合并」，不是整体覆盖
    -> 只能新增新标签子条目；改名覆盖会让原建筑在非该玩法下失去模型
  · 建筑所在区域可能被特色区域取代（DistrictReplaces）-> 两条链都要挂
"""
import argparse, copy, os, re, sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_copy

NL = chr(10)
TAB = chr(9)
TOK_RE = re.compile('<Element[^>]*?>|</Element>')
PREFIX = 'GA_'


def nm_of(e):
    n = e.find('m_Name')
    return n.get('text') if n is not None else None


def coll_name(c):
    n = c.find('m_CollectionName')
    return n.get('text') if n is not None else None


def cls_els(e, want):
    return [x for x in e.iter('Element') if (x.get('class') or '').endswith(want)]


def pval(it, pname):
    for v in it.findall('m_Fields/m_Values/Element'):
        pn = v.find('m_ParamName')
        if pn is not None and pn.get('text') == pname:
            t = v.find('m_ElementName')
            return t.get('text') if t is not None else None
    return None


def set_refs(it):
    out = []
    for v in cls_els(it, 'ArtDefReferenceValue'):
        pn, en = v.find('m_ParamName'), v.find('m_ElementName')
        if pn is not None and en is not None and (pn.get('text') or '').startswith('Set'):
            out.append(en.get('text'))
    return out


def match_element(text, open_pos):
    depth = 0
    for m in TOK_RE.finditer(text, open_pos):
        t = m.group(0)
        if t == '</Element>':
            depth -= 1
            if depth == 0:
                return m.start()
        elif t.endswith('/>'):
            continue
        else:
            depth += 1
    return -1


def find_top_entry_span(text, name):
    """定位 3-tab 缩进的顶层条目区间（artdef 根集合的直接子条目统一 3 tab）"""
    mk = re.search('<m_Name text="' + re.escape(name) + '"', text)
    if not mk:
        return None
    mstart = mk.start()
    marker = NL + TAB * 3 + '<Element>'
    pos = 0
    while True:
        i = text.find(marker, pos)
        if i < 0:
            return None
        op = i + 1
        cl = match_element(text, op)
        if cl > 0 and op < mstart < cl:
            return (op, cl)
        pos = i + 1


def load_children(entry, coll):
    for sub in entry.findall('m_ChildCollections/Element'):
        if coll_name(sub) == coll:
            return sub.findall('Element')
    return []


def find_coll_span(text, from_pos, coll):
    mk = re.search(NL + '[' + TAB + ' ]*<m_CollectionName text="' + re.escape(coll) + '"', text[from_pos:])
    if not mk:
        return None
    mstart = from_pos + mk.start()
    op = text.rfind('<Element>', from_pos, mstart)
    if op < 0:
        return None
    cl = match_element(text, op)
    return (op, cl) if cl > 0 else None


def transmute(el, new_name, old_tok, new_tok, old_b, new_b):
    e = copy.deepcopy(el)
    e.find('m_Name').set('text', new_name)
    for v in e.iter('Element'):
        pn, en = v.find('m_ParamName'), v.find('m_ElementName')
        if pn is None or en is None:
            continue
        k = pn.get('text') or ''
        if k == 'Set_HeroBuildings':
            en.set('text', (en.get('text') or '').replace(old_tok, new_tok))
        elif k == 'Tag_HeroBuilding':
            en.set('text', new_b)
        elif k.startswith('Set') and en.get('text') == old_b:
            en.set('text', new_b)
    return e


def serialize_elems(elems, indent):
    pad = TAB * indent
    out = []
    for el in elems:
        x = copy.deepcopy(el)
        if hasattr(ET, 'indent'):
            ET.indent(x, space=TAB)
        txt = ET.tostring(x, encoding='unicode').replace(chr(34) + ' />', chr(34) + '/>')
        out.append(NL.join(pad + l if l.strip() else l for l in txt.splitlines()))
    return NL.join(out)


def make_coll(name, elems):
    e = ET.Element('Element')
    ET.SubElement(e, 'm_CollectionName').set('text', name)
    ET.SubElement(e, 'm_ReplaceMergedCollectionElements').text = 'false'
    for x in elems:
        e.append(copy.deepcopy(x))
    return e


def game_targets(idx, src_building):
    """反查游戏侧所有 BuildingSets 引用了该建筑的区域"""
    hits = []
    for a in idx['artdefs']:
        if 'error' in a or (a.get('template') or '') != 'Landmarks':
            continue
        for r in a.get('childReferences', []):
            if r.get('coll') != 'BuildingSets' or not (r.get('param') or '').startswith('Set'):
                continue
            if r.get('element') == src_building and r.get('parent'):
                hits.append((a, r['parent']))
    return hits


def collect_child_names(entry):
    out = {}
    for sub in entry.findall('m_ChildCollections/Element'):
        out[coll_name(sub)] = [nm_of(x) for x in sub.findall('Element')]
    return out

def derive(entry, src_building):
    """从某区域的条目里推导：原标签 token + 与该建筑相关的三组子条目"""
    sets_all = load_children(entry, 'BuildingSets')
    old_tok = None
    for c in sets_all:
        refs = set_refs(c)
        if src_building in refs:
            parts = [x.strip() for x in (nm_of(c) or '').split(',')]
            if len(parts) == len(refs):
                old_tok = parts[refs.index(src_building)]
                break
    if not old_tok:
        return None, [], [], []
    base_vars = [c for c in load_children(entry, 'BaseVariants')
                 if old_tok in (pval(c, 'Set_HeroBuildings') or '')]
    bldg_vars = [c for c in load_children(entry, 'BuildingVariants')
                 if pval(c, 'Tag_HeroBuilding') == src_building]
    bldg_sets = [c for c in sets_all if src_building in set_refs(c)]
    return old_tok, base_vars, bldg_vars, bldg_sets


def uniq(name):
    return PREFIX + re.sub('[^A-Za-z0-9]+', '_', name).strip('_')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src_building')
    ap.add_argument('new_building')
    ap.add_argument('--landmarks-out')
    ap.add_argument('--buildings-out')
    ap.add_argument('--district', action='append', default=[],
                    help='额外目标区域（mod 侧区域不在索引里，必须显式给出）')
    ap.add_argument('--tag', help='新标签 token（默认由新建筑名推导）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    if not args.landmarks_out and not args.buildings_out:
        sys.exit('至少给一个 --landmarks-out / --buildings-out')

    new_tok = args.tag or re.sub('_RGN$', '', re.sub('^BUILDING_', '', args.new_building))
    idx = art_copy.load_index()

    auto = game_targets(idx, args.src_building)
    auto_names = []
    shown = []
    print('[反查] 游戏侧 BuildingSets 引用了 ' + args.src_building + ' 的区域：')
    for a, p in auto:
        if p not in auto_names:
            auto_names.append(p)
        if (a['rel'], p) in shown:
            continue
        shown.append((a['rel'], p))
        print('   · ' + p + '  @ ' + a['rel'])
    if not auto:
        print('   （无）—— 若是奇观，模型走 Landmarks.artdef 独立条目 + WonderMovie.artdef')

    if args.buildings_out:
        src = art_copy.find_source(idx, 'Buildings', args.src_building)
        if src is None:
            sys.exit('索引里找不到 Buildings 条目: ' + args.src_building)
        bel, bcoll = art_copy.extract_entry(idx, src, args.src_building)
        art_copy.rename_entry(bel, args.src_building, args.new_building)
        art_copy.insert_into_file(args.buildings_out, bel, 'Buildings', bcoll, dry_run=args.dry_run)
        print('[Buildings.artdef] ' + args.src_building + ' -> ' + args.new_building)

    if not args.landmarks_out:
        return

    targets = list(args.district)
    for n in auto_names:
        if n not in targets:
            targets.append(n)
    print('[Landmarks.artdef] 目标区域: ' + str(targets))

    text = ''
    if os.path.exists(args.landmarks_out):
        text = open(args.landmarks_out, encoding='utf-8-sig').read()
    before = {}
    for t in targets:
        span = find_top_entry_span(text, t) if text else None
        if span:
            ent = ET.fromstring('<W>' + text[span[0]:span[1] + 10] + '</W>')[0]
            before[t] = collect_child_names(ent)

    for t in targets:
        span = find_top_entry_span(text, t) if text else None
        if span:
            src_entry = ET.fromstring('<W>' + text[span[0]:span[1] + 10] + '</W>')[0]
            origin = '（目标文件已有条目）'
        else:
            g = None
            for a, p in auto:
                if p == t:
                    g = (a, p)
                    break
            if g is None:
                print('   ! ' + t + '：目标文件与游戏侧都没有该区域条目，跳过')
                continue
            src_entry, _ = art_copy.extract_entry(idx, g[0], t)
            origin = '（形状取自 ' + g[0]['rel'] + '）'

        old_tok, base_vars, bldg_vars, bldg_sets = derive(src_entry, args.src_building)
        if not old_tok or not bldg_sets or not bldg_vars:
            already = False
            for c in load_children(src_entry, 'BuildingSets'):
                if args.new_building in set_refs(c):
                    already = True
                    break
            if already:
                print('   · ' + t + '：已是目标状态（BuildingSets 已含 ' + args.new_building + '），跳过')
            else:
                print('   ! ' + t + '：推导不出该建筑相关的三组子条目，跳过')
            continue

        nbv = [transmute(c, uniq(nm_of(c)), old_tok, new_tok, args.src_building, args.new_building)
               for c in base_vars]
        nbd = [transmute(c, PREFIX + new_tok.title().replace('_', ''), old_tok, new_tok,
                         args.src_building, args.new_building) for c in bldg_vars]
        nbs = [transmute(c, (nm_of(c) or '').replace(old_tok, new_tok), old_tok, new_tok,
                         args.src_building, args.new_building) for c in bldg_sets]
        for e in nbs:
            assert args.new_building in set_refs(e) and args.src_building not in set_refs(e)
        for e in nbd:
            assert pval(e, 'Tag_HeroBuilding') == args.new_building
        print('   · ' + t + ' ' + origin + ' 标签 ' + old_tok + '->' + new_tok
              + '  [BaseVariants %d / BuildingVariants %d / BuildingSets %d]'
              % (len(nbv), len(nbd), len(nbs)))

        if span:
            op, cl = span
            scope = text[op:cl]
            existing = before.get(t, {})
            for coll, elems in (('BuildingSets', nbs), ('BuildingVariants', nbd), ('BaseVariants', nbv)):
                have = set(existing.get(coll, []))
                kept = [e for e in elems if nm_of(e) not in have]
                if len(kept) != len(elems):
                    print('       ' + coll + '：跳过已存在的 ' + str(len(elems) - len(kept)) + ' 条（幂等）')
                if not kept:
                    continue
                csp = find_coll_span(scope, 0, coll)
                if csp is None:
                    print('       ! 缺子集合 ' + coll + '，跳过')
                    continue
                cop, ccl = csp
                line_start = scope.rfind(NL, 0, cop) + 1
                ind = cop - line_start
                scope = scope[:ccl].rstrip() + NL + serialize_elems(kept, ind + 1) + NL + scope[ccl:]
            text = text[:op] + scope + text[cl:]
        else:
            entry = ET.Element('Element')
            f = src_entry.find('m_Fields')
            if f is not None:
                entry.append(copy.deepcopy(f))
            cc = ET.SubElement(entry, 'm_ChildCollections')
            cc.append(make_coll('BaseVariants', nbv))
            cc.append(make_coll('BuildingVariants', nbd))
            cc.append(make_coll('BuildingSets', nbs))
            ET.SubElement(entry, 'm_Name').set('text', t)
            ET.SubElement(entry, 'm_AppendMergedParameterCollections').text = 'false'
            body = serialize_elems([entry], 3)
            marker = TAB * 3 + '<m_ReplaceMergedCollectionElements>false</m_ReplaceMergedCollectionElements>'
            i = text.find(marker)
            if i < 0:
                sys.exit('目标文件结构异常：找不到根集合标记')
            root_open = text.rfind('<Element>', 0, i)
            root_close = match_element(text, root_open)
            text = text[:root_close].rstrip() + NL + body + NL + text[root_close:]

    if args.dry_run:
        print('[dry-run] 未写文件')
        return
    open(args.landmarks_out, 'w', encoding='utf-8', newline=NL).write(text)

    after = open(args.landmarks_out, encoding='utf-8-sig').read()
    bad = 0
    for t, colls in before.items():
        span = find_top_entry_span(after, t)
        if not span:
            print('   [FAIL] ' + t + ' 条目丢失')
            bad += 1
            continue
        ent = ET.fromstring('<W>' + after[span[0]:span[1] + 10] + '</W>')[0]
        now = collect_child_names(ent)
        for coll, names in colls.items():
            lost = [n for n in names if n not in (now.get(coll) or [])]
            if lost:
                print('   [FAIL] ' + t + '/' + coll + ' 丢失子条目: ' + str(lost))
                bad += 1
    ET.parse(args.landmarks_out)
    print('[自检] XML 可解析；原有内容丢失 = ' + str(bad) + '（0 = 纯增量）')


if __name__ == '__main__':
    main()
