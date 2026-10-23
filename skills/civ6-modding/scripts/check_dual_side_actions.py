import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET


SIDES = (("FrontEndActionData", "FrontEndActions"),
         ("InGameActionData", "InGameActions"))
PAIRED_ACTIONS = ("UpdateArt", "UpdateColors", "UpdateIcons")
ICON_REF_RE = re.compile(r"\bICON_[A-Z0-9_]+\b")


def localname(el):
    return el.tag.split("}")[-1]


def read_text(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()


def find_project(root):
    hits = sorted(glob.glob(os.path.join(root, "*.civ6proj")))
    if not hits:
        sys.exit("未找到 *.civ6proj: %s" % root)
    if len(hits) > 1:
        sys.exit("工程目录下存在多个 *.civ6proj，无法确定身份: %s"
                 % ", ".join(os.path.basename(h) for h in hits))
    return hits[0]


def line_of(raw, needle):
    idx = raw.find(needle)
    if idx < 0:
        return ""
    return ":%d" % (raw.count("\n", 0, idx) + 1)


def parse_actions(proj_path):
    raw = read_text(proj_path)
    tree = ET.fromstring(raw)
    out = {}
    for holder, action_root in SIDES:
        node = None
        for el in tree.iter():
            if localname(el) == holder:
                node = el
                break
        if node is None:
            sys.exit("%s 缺少 %s 节点" % (os.path.basename(proj_path), holder))
        body = (node.text or "").strip()
        if not body:
            sys.exit("%s 的 %s 为空" % (os.path.basename(proj_path), holder))
        root = ET.fromstring(body)
        if localname(root) != action_root:
            sys.exit("%s 的 %s 根元素应为 %s，实为 %s"
                     % (os.path.basename(proj_path), holder, action_root, localname(root)))
        actions = []
        for child in root:
            files = [(f.text or "").strip() for f in child if localname(f) == "File"]
            actions.append({"tag": localname(child), "id": child.get("id"), "files": files})
        out[holder] = actions
    return out, raw


def load_icon_xml(path):
    tree = ET.fromstring(read_text(path))
    atlases = []
    defs = set()
    for node in tree.iter():
        name = localname(node)
        if name == "IconTextureAtlases":
            for row in node:
                if localname(row) != "Row":
                    continue
                atlases.append((row.get("Name"), row.get("IconSize"), row.get("Filename")))
        elif name == "IconDefinitions":
            for row in node:
                if localname(row) != "Row":
                    continue
                defs.add(row.get("Name"))
    return atlases, defs


def main():
    ap = argparse.ArgumentParser(
        description="检查 .civ6proj 的 FrontEndActions 与 InGameActions 动作对称性，"
                    "以及两端图标注册闭合（图集档位、IconDefinitions、SQL 引用、磁盘贴图）")
    ap.add_argument("root", nargs="?", default=".", help="工程主体目录（含 *.civ6proj）")
    ap.add_argument("--quiet", action="store_true", help="只打印结论")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        sys.exit("目录不存在: %s" % root)
    proj = find_project(root)
    proj_name = os.path.basename(proj)
    actions, raw = parse_actions(proj)
    fe = actions["FrontEndActionData"]
    ig = actions["InGameActionData"]
    fe_tags = set(x["tag"] for x in fe)
    ig_tags = set(x["tag"] for x in ig)
    fails = []

    def loc(needle):
        return "%s%s" % (proj_name, line_of(raw, needle))

    for tag in PAIRED_ACTIONS:
        if tag in fe_tags and tag not in ig_tags:
            for x in fe:
                if x["tag"] == tag:
                    fails.append("%s 仅出现在 FrontEndActions（id=%s）— %s"
                                 % (tag, x["id"], loc('id="%s"' % x["id"])))
        elif tag in ig_tags and tag not in fe_tags:
            for x in ig:
                if x["tag"] == tag:
                    fails.append("%s 仅出现在 InGameActions（id=%s）— %s"
                                 % (tag, x["id"], loc('id="%s"' % x["id"])))

    def icon_files(side, side_name):
        out = []
        for x in side:
            if x["tag"] != "UpdateIcons":
                continue
            for f in x["files"]:
                p = os.path.join(root, f.replace("/", os.sep))
                if not os.path.isfile(p):
                    fails.append("%s 的 UpdateIcons 引用文件不存在: %s" % (side_name, f))
                    continue
                out.append(p)
        return out

    fe_files = icon_files(fe, "FrontEndActions")
    ig_files = icon_files(ig, "InGameActions")

    fe_atl, fe_defs = set(), set()
    for p in fe_files:
        atl, defs = load_icon_xml(p)
        fe_atl |= set((n, s) for n, s, _ in atl)
        fe_defs |= defs
    ig_atl, ig_defs = set(), set()
    for p in ig_files:
        atl, defs = load_icon_xml(p)
        ig_atl |= set((n, s) for n, s, _ in atl)
        ig_defs |= defs

    for name, size in sorted(fe_atl - ig_atl):
        fails.append("图集 %s 的 %s 档仅在 FrontEnd 注册，InGame 缺失" % (name, size))
    for name in sorted(x for x in fe_defs - ig_defs if x):
        fails.append("IconDefinitions %s 仅在 FrontEnd 定义，InGame 缺失" % name)

    project_icons = set(x for x in (fe_defs | ig_defs) if x)
    referenced = set()
    for p in sorted(glob.glob(os.path.join(root, "Data", "*.sql"))):
        referenced |= set(ICON_REF_RE.findall(read_text(p)))
    owned = referenced & project_icons
    for name in sorted(owned - ig_defs):
        fails.append("%s 被 Data/*.sql 引用且由本工程定义，InGame 无 IconDefinitions" % name)

    tex_dir = os.path.join(root, "Textures")
    seen = set()
    for p in fe_files + ig_files:
        if p in seen:
            continue
        seen.add(p)
        atl, _ = load_icon_xml(p)
        for name, size, fname in atl:
            if not fname:
                fails.append("%s: 图集 %s 的 %s 档缺少 Filename" % (os.path.basename(p), name, size))
                continue
            # Filename 口径见 art-pipeline.md「图标图集」：多格图集带 .dds 后缀，1×1 单图集不带
            dds_name = fname if fname.lower().endswith(".dds") else fname + ".dds"
            if not os.path.isfile(os.path.join(tex_dir, dds_name)):
                fails.append("%s: 图集 %s 的 %s 档指向 %s，Textures 下无该贴图"
                             % (os.path.basename(p), name, size, fname))

    if not a.quiet:
        print("=" * 72)
        print("双端动作与图标注册校验：%s" % root)
        print("=" * 72)
        print("  FrontEndActions 动作 %d 个 / InGameActions 动作 %d 个" % (len(fe), len(ig)))
        print("  成对动作: %s" % (", ".join(t for t in PAIRED_ACTIONS if t in fe_tags and t in ig_tags) or "无"))
        print("  FrontEnd 图集 %d 档 / IconDefinitions %d 条" % (len(fe_atl), len(fe_defs)))
        print("  InGame   图集 %d 档 / IconDefinitions %d 条" % (len(ig_atl), len(ig_defs)))
        print("  SQL 引用图标 %d 个，其中本工程定义 %d 个" % (len(referenced), len(owned)))
    if fails:
        print("")
        print("── 失败项（%d）──" % len(fails))
        for m in fails:
            print("  ✗ %s" % m)
    print("")
    if fails:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
