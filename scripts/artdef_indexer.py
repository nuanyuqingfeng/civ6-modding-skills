# -*- coding: utf-8 -*-
"""文明6 ArtDef/XLP 引用链索引器（civ6-art-reference skill 版）

扫描游戏安装目录与 SDK Assets，解析全部 artdef / xlp 文件并建立引用链索引：
  - artdef: 模板名、根集合、条目列表；引用（BLP/ArtDefReference）作用域到所属条目
  - xlp: ClassName、PackageName、全部条目

用法:
  python artdef_indexer.py [--game <Civ6安装根目录>] [--sdk <SDK Assets根目录>]
                           [--out <输出.json[.gz]>]

默认根目录（本机）:
  game = F:\\Steam\\steamapps\\common\\Sid Meier's Civilization VI
  sdk  = F:\\Steam\\steamapps\\common\\Sid Meier's Civilization VI SDK Assets

扫描范围:
  <game>/Base/ArtDefs, <game>/DLC/**/ArtDefs, <sdk>/Civ6/pantry, <sdk>/Civ6/DLC/*/pantry

输出字段: source(base/dlc/sdk/sdkdlc), rel(相对路径), template, rootCollections,
entries[{collection,name}], references[{kind,entry,...}]
"""
import json, os, sys, re, gzip, argparse
import xml.etree.ElementTree as ET

DEFAULT_GAME = r"F:\Steam\steamapps\common\Sid Meier's Civilization VI"
DEFAULT_SDK  = r"F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets"

# 别人机器上的覆盖入口：默认值不存在时按 环境变量 → local_paths.json 探测（不改默认值语义）
_LOCAL_PATHS_FILES = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_paths.json'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 '..', 'civ6-modding', 'local_paths.json'),
]


def _from_local_paths(*keys):
    for lp in _LOCAL_PATHS_FILES:
        try:
            with open(lp, encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        for k in keys:
            v = data.get(k)
            if v:
                return v
    return None


def resolve_root(cli_value, env_keys, lp_keys, default):
    """CLI 显式值 > 默认值（本机存在时直接用）> 环境变量 > local_paths.json > 默认值。

    默认值存在时直接采用 —— 保证作者机上的行为与改造前完全一致，
    覆盖入口只在「默认路径缺失」这一分支生效。
    """
    if cli_value:
        return cli_value
    if os.path.isdir(default):
        return default
    for e in env_keys:
        v = os.environ.get(e)
        if v:
            return v
    v = _from_local_paths(*lp_keys)
    if v:
        return v
    return default


def load_xml(path):
    with open(path, 'rb') as f:
        raw = f.read().decode('utf-8', errors='replace')
    # 兼容个别原版文件：单/双冒号未声明前缀（AssetObjects: / AssetObjects::）、尾部 NUL 截断字节
    raw = re.sub(r'AssetObjects::?', 'AssetObjects..', raw)
    raw = raw.replace('\x00', '')
    return ET.fromstring(raw)

def tag_local(t):
    return t.rsplit('}', 1)[-1]

def parse_artdef(path):
    try:
        root = load_xml(path)
    except ET.ParseError as e:
        return {"error": f"parse error: {e}", "references": [], "entries": []}
    tpl_el = root.find('m_TemplateName')
    template = tpl_el.get('text') if tpl_el is not None else None
    rc = root.find('m_RootCollections')
    if rc is None:
        return {"error": "no RootCollections", "references": [], "entries": []}

    entries, refs, child_refs = [], [], []

    def vals_of(sub):
        """取一个值元素的直系字段（含 m_ParamName，用于区分 Set / Tag_HeroBuilding / Set_HeroBuildings / XrefName）"""
        out = {}
        for v in list(sub):
            st = tag_local(v.tag)
            if st in ('m_Value', 'm_nValue', 'm_fValue', 'm_bValue', 'm_EntryName',
                      'm_XLPClass', 'm_XLPPath', 'm_BLPPackage', 'm_LibraryName',
                      'm_ElementName', 'm_RootCollectionName', 'm_ArtDefPath',
                      'm_ParamName'):
                out[st] = v.get('text') if v.get('text') is not None else v.text
        return out

    def ref_record(vals, scope, kind_hint=None):
        cls = (kind_hint or '')
        if 'BLPEntryValue' in cls:
            return {"kind": "blp", "param": vals.get('m_ParamName'), "entryXLP": vals.get('m_EntryName'),
                    "xlpclass": vals.get('m_XLPClass'), "xlppath": vals.get('m_XLPPath'),
                    "package": vals.get('m_BLPPackage'), "library": vals.get('m_LibraryName')}
        return {"kind": "artdef", "param": vals.get('m_ParamName'), "element": vals.get('m_ElementName'),
                "rootcoll": vals.get('m_RootCollectionName'), "path": vals.get('m_ArtDefPath')}

    def collect_refs(el, entry, sink):
        for sub in el.iter():
            cls = sub.get('class')
            if not cls:
                continue
            if cls == 'AssetObjects..BLPEntryValue':
                rec = ref_record(vals_of(sub), entry, cls)
            elif cls == 'AssetObjects..ArtDefReferenceValue':
                rec = ref_record(vals_of(sub), entry, cls)
            else:
                continue
            rec["entry"] = entry
            sink.append(rec)

    def collect_children(el, parent):
        """条目自身的子集合结构 + 字段值；子树内每个子条目的引用另收进 child_refs"""
        colls, fields = {}, {}
        cc = el.find('m_ChildCollections')
        if cc is not None:
            for c in list(cc):
                if tag_local(c.tag) != 'Element':
                    continue
                n = c.find('m_CollectionName')
                if n is None or n.get('text') is None:
                    continue
                coll_name = n.get('text')
                names = []
                for it in list(c):
                    if tag_local(it.tag) != 'Element':
                        continue
                    inm = it.find('m_Name')
                    child_name = inm.get('text') if inm is not None else None
                    names.append(child_name)
                    if child_name:
                        for rec in _collect_child_refs(it, child_name):
                            rec["coll"] = coll_name
                            rec["parent"] = parent
                            child_refs.append(rec)
                colls[coll_name] = names
        fv = el.find('m_Fields/m_Values')
        if fv is not None:
            for v in list(fv):
                if tag_local(v.tag) != 'Element':
                    continue
                pn = v.find('m_ParamName')
                if pn is None or pn.get('text') is None:
                    continue
                for vt_name in ('m_bValue', 'm_Value', 'm_nValue', 'm_fValue', 'm_ElementName'):
                    vt = v.find(vt_name)
                    if vt is not None:
                        fields[pn.get('text')] = vt.get('text') if vt.get('text') is not None else vt.text
                        break
        return colls, fields

    def _collect_child_refs(it, child_name):
        out = []
        for sub in it.iter():
            cls = sub.get('class')
            if not cls:
                continue
            if cls == 'AssetObjects..BLPEntryValue':
                rec = ref_record(vals_of(sub), child_name, cls)
            elif cls == 'AssetObjects..ArtDefReferenceValue':
                rec = ref_record(vals_of(sub), child_name, cls)
            else:
                continue
            rec["entry"] = child_name
            out.append(rec)
        return out

    top_colls = []
    for el in list(rc):
        if tag_local(el.tag) != 'Element':
            continue
        cname = el.find('m_CollectionName')
        cname = cname.get('text') if cname is not None else None
        top_colls.append(cname)
        for child in list(el):
            if tag_local(child.tag) != 'Element':
                continue
            nm = child.find('m_Name')
            name = nm.get('text') if nm is not None else None
            colls, fields = collect_children(child, name)
            item = {"collection": cname, "name": name}
            if colls:
                item["childCollections"] = colls
            if fields:
                item["fields"] = fields
            entries.append(item)
            if name:
                collect_refs(child, name, refs)

    return {"template": template, "rootCollections": top_colls,
            "entryCount": len(entries), "entries": entries,
            "references": refs, "childReferences": child_refs}

def parse_xlp(path):
    try:
        root = load_xml(path)
    except ET.ParseError as e:
        return {"error": f"parse error: {e}", "entries": []}
    cls = root.find('m_ClassName')
    pkg = root.find('m_PackageName')
    entries = []
    me = root.find('m_Entries')
    if me is not None:
        for el in list(me):
            eid = el.find('m_EntryID')
            oname = el.find('m_ObjectName')
            entries.append({"id": eid.get('text') if eid is not None else None,
                            "object": oname.get('text') if oname is not None else None})
    return {"className": cls.get('text') if cls is not None else None,
            "packageName": pkg.get('text') if pkg is not None else None,
            "entryCount": len(entries), "entries": entries}

def main():
    # Windows 控制台默认 GBK，中文提示会乱码 → 强制 UTF-8（失败也不致命）
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=None,
                    help='Civ6 安装根目录（默认按 CIV6_GAME → local_paths.json 的 game → 作者示例路径探测）')
    ap.add_argument('--sdk',  default=None,
                    help='SDK Assets 根目录（默认按 CIV6_SDK_ASSETS → local_paths.json 的 sdk_assets → 作者示例路径探测）')
    ap.add_argument('--out',  default=None, help='输出 json 或 json.gz（默认与脚本同目录 art_index.json.gz）')
    ap.add_argument('--allow-missing-roots', action='store_true',
                    help='游戏根与 SDK 根都不可用时仍继续（会写出几乎空的索引，仅供自检）')
    args = ap.parse_args()

    game = resolve_root(args.game, ('CIV6_GAME', 'CIV6_GAME_ROOT'), ('game',), DEFAULT_GAME)
    sdk = resolve_root(args.sdk, ('CIV6_SDK_ASSETS', 'CIV6_SDK'), ('sdk_assets', 'sdk'), DEFAULT_SDK)

    roots = [
        ("base",   os.path.join(game, "Base", "ArtDefs")),
        ("dlc",    os.path.join(game, "DLC")),
        ("sdk",    os.path.join(sdk,  "Civ6", "pantry")),
        ("sdkdlc", os.path.join(sdk,  "Civ6", "DLC")),
    ]
    missing = [(label, root) for label, root in roots if not os.path.isdir(root)]
    miss_labels = {label for label, _ in missing}
    game_ok = not {"base", "dlc"} <= miss_labels
    sdk_ok = not {"sdk", "sdkdlc"} <= miss_labels
    if not game_ok and not sdk_ok and not args.allow_missing_roots:
        sys.stderr.write(
            "[FAIL] 游戏根与 SDK 根都不可用，无法建立索引"
            "（否则只会写出一份几乎空的索引却显示成功）。\n"
            "  本次 game = %s（Base/ArtDefs、DLC 均不存在）\n"
            "  本次 sdk  = %s（Civ6/pantry、Civ6/DLC 均不存在）\n"
            "  这两个默认值是作者机器路径，别人机器上通常不存在。请指向你自己的目录：\n"
            "    --game <Civ6 安装根>    形如 <Steam>/steamapps/common/Sid Meier's Civilization VI\n"
            "    --sdk  <SDK Assets 根>  形如 <Steam>/steamapps/common/Sid Meier's Civilization VI SDK Assets\n"
            "  也可用环境变量 CIV6_GAME / CIV6_SDK_ASSETS，或在 local_paths.json 写 "
            "{\"game\": \"...\", \"sdk_assets\": \"...\"}\n"
            "  （本脚本读取 <skill>/local_paths.json 与同级 civ6-modding/local_paths.json）\n"
            "  确知本机没有游戏、只想生成空索引时，加 --allow-missing-roots。\n"
            % (game, sdk))
        sys.exit(2)

    index = {"roots": {"game": game, "sdk": sdk}, "artdefs": [], "xlps": []}
    for label, root in roots:
        if not os.path.isdir(root):
            print(f"WARN root missing: {root}", file=sys.stderr)
            continue
        base_len = len(game if label in ("base", "dlc") else sdk)
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.lower().endswith(('.artdef', '.xlp')):
                    continue
                p = os.path.join(dirpath, fn)
                data = parse_artdef(p) if fn.lower().endswith('.artdef') else parse_xlp(p)
                data["source"] = label
                data["rel"] = p.replace('\\', '/')[base_len+1:]
                index["artdefs" if fn.lower().endswith('.artdef') else "xlps"].append(data)

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'art_index.json.gz')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    raw = json.dumps(index, ensure_ascii=False).encode('utf-8')
    if out.endswith('.gz'):
        with open(out, 'wb') as f:
            f.write(gzip.compress(raw, 9))
    else:
        with open(out, 'wb') as f:
            f.write(raw)

    errs = [a for a in index['artdefs'] if 'error' in a] + [x for x in index['xlps'] if 'error' in x]
    print(f"artdefs: {len(index['artdefs'])}, xlps: {len(index['xlps'])}, parse errors: {len(errs)}")
    for a in errs:
        print("  ERR", a['rel'], a['error'])
    if missing:
        print("已跳过 %d 个缺失根（其内容不在索引中）：%s"
              % (len(missing), "; ".join("%s=%s" % (l, r) for l, r in missing)))
    if args.allow_missing_roots and not game_ok and not sdk_ok:
        print("WARN --allow-missing-roots：游戏根与 SDK 根都不可用，本索引几乎为空，不可用于实际引用查询。")
    print(f"written: {out} ({os.path.getsize(out)/1e6:.2f} MB)")

if __name__ == '__main__':
    main()
