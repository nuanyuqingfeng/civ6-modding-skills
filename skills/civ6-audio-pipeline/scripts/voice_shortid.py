import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wwise_shortid as ws

# 领袖语音对象的 ShortID 打包命名：
#   31 位 = 槽位 4 位（第 30..27 位）+ 角色 2 位（第 26..25 位）+ 主体哈希 25 位（第 24..0 位）
#   主体键 = "<工程全名>/<资产名>"，FNV-1(32) 取低 25 位
#   事件 ShortID 由 Wwise 按事件名哈希决定，本工具不碰；三个锚点编号不碰
#
# 用法:
#   分配   python voice_shortid.py assign <工程目录> --project <工程全名> [--dry]
#   校验   python voice_shortid.py check <工程目录> --project <工程全名>
#   验产物 python voice_shortid.py verify-bank <bank.bnk> <工程目录> --project <工程全名>
#   查号   python voice_shortid.py id --project <工程全名> --asset <资产名> --role sound|action|container

USAGE = "用法: voice_shortid.py {assign|check|verify-bank|id} ... --project <工程全名>"

ANCHORS = (88602518, 854467727, 424381547)

SLOT_CODES = {
    "first_meet": 1,
    "declare_war_from_human": 2,
    "declare_war_from_ai": 3,
    "kudo_exit": 4,
    "warning_exit": 5,
    "defeat_from_ai": 6,
    "quote": 7,
    "misc_pep_talk": 8,
}
ROLE_CODES = {"sound": 0, "action": 1, "container": 2, "bus": 3}
ROLE_NAMES = {v: k for k, v in ROLE_CODES.items()}

SUBJECT_BITS = 25
SUBJECT_MASK = (1 << SUBJECT_BITS) - 1
FNV_PRIME = 16777619
FNV_OFFSET = 2166136261
M32 = 0xFFFFFFFF


def fnv1(text):
    h = FNV_OFFSET
    for b in text.lower().encode("utf-8"):
        h = (h * FNV_PRIME) & M32
        h ^= b
    return h & M32


def slot_code(asset_name):
    low = asset_name.lower()
    best_code = 0
    best_len = 0
    for name, code in SLOT_CODES.items():
        if name in low and len(name) > best_len:
            best_code = code
            best_len = len(name)
    return best_code


def decode(value):
    return (value >> 27) & 0xF, (value >> 25) & 0x3, value & SUBJECT_MASK


def compute(project, asset_name, role):
    slot = slot_code(asset_name)
    attempt = 1
    while True:
        suffix = "" if attempt == 1 else "/" + str(attempt)
        subject = fnv1(project + "/" + asset_name + suffix) & SUBJECT_MASK
        value = (slot << 27) | (ROLE_CODES[role] << 25) | subject
        if value not in ANCHORS:
            return value
        attempt += 1


ELEMENT_RE = re.compile(r"<(Sound|ActorMixer|Action|Event|Bus)\b([^>]*)>")
ATTR_NAME_RE = re.compile(r'Name="([^"]*)"')
ATTR_SHORTID_RE = re.compile(r'\bShortID="(\d+)"')
ATTR_ID_RE = re.compile(r'\bID="\{[0-9A-Fa-f-]+\}"')
OBJECTREF_RE = re.compile(r'<ObjectRef Name="([^"]+)"')
ANCHOR_NAME_RE = re.compile(r"^id\d+$")


def objects(text):
    current_event = ""
    for m in ELEMENT_RE.finditer(text):
        tag = m.group(1)
        head = m.group(2)
        name_m = ATTR_NAME_RE.search(head)
        if not name_m:
            continue
        if tag == "Event":
            current_event = name_m.group(1)
        shortid_m = ATTR_SHORTID_RE.search(head)
        target = None
        if tag == "Action":
            end = text.find("</Action>", m.end())
            block = text[m.end():end if end > 0 else len(text)]
            ref = OBJECTREF_RE.search(block)
            target = ref.group(1) if ref else None
        yield dict(tag=tag, name=name_m.group(1), event=current_event,
                   shortid=int(shortid_m.group(1)) if shortid_m else None,
                   begin=m.start(), head_end=m.end(), target=target)


def managed(obj):
    if obj["tag"] == "Action":
        return ("action", obj["event"] + "/" + obj["name"])
    if obj["tag"] == "Sound":
        return ("sound", obj["name"])
    if obj["tag"] == "ActorMixer":
        if ANCHOR_NAME_RE.match(obj["name"]):
            return None
        if obj["shortid"] in ANCHORS:
            return None
        return ("container", obj["name"])
    return None


def wwu_files(proj):
    out = []
    for sub in ("Events", "Actor-Mixer Hierarchy"):
        root = os.path.join(proj, sub)
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            out.extend(os.path.join(dirpath, fn) for fn in files if fn.endswith(".wwu"))
    return sorted(out)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))


def attribute_patch(text, obj, value):
    head = text[obj["begin"]:obj["head_end"]]
    if obj["shortid"] is None:
        patched = ATTR_ID_RE.sub(lambda m: m.group(0) + ' ShortID="%d"' % value, head, count=1)
    else:
        patched = ATTR_SHORTID_RE.sub('ShortID="%d"' % value, head, count=1)
    return text[:obj["begin"]] + patched + text[obj["head_end"]:]


def plan(proj, project):
    rows = []
    seen = {}
    for path in wwu_files(proj):
        for obj in objects(read(path)):
            kind = managed(obj)
            if kind is None:
                continue
            role, asset = kind
            seen[asset] = seen.get(asset, 0) + 1
            if seen[asset] > 1:
                asset = asset + "/" + str(seen[asset])
            rows.append(dict(path=path, obj=obj, role=role, asset=asset,
                             value=compute(project, asset, role)))
    return rows


def assign(proj, project, dry):
    rows = plan(proj, project)
    by_file = {}
    for row in rows:
        by_file.setdefault(row["path"], []).append(row)
    for path, items in sorted(by_file.items()):
        text = read(path)
        items.sort(key=lambda r: r["obj"]["begin"])
        for row in reversed(items):
            text = attribute_patch(text, row["obj"], row["value"])
        if not dry:
            write(path, text)
        print("  %-56s %3d" % (os.path.basename(path), len(items)))
    print("[ASSIGN] %s 共 %d 个对象%s" % (project, len(rows), "（预演，未写盘）" if dry else ""))
    return 0


def check(proj, project):
    rows = plan(proj, project)
    bad = []
    owners = {}
    for row in rows:
        current = row["obj"]["shortid"]
        if current != row["value"]:
            bad.append("%s %s 现为 %s 应为 %s" % (os.path.basename(row["path"]), row["obj"]["name"],
                                                 current, row["value"]))
        if current in owners:
            bad.append("%s 编号 %s 与 %s 重复" % (row["obj"]["name"], current, owners[current]))
        owners[current] = row["obj"]["name"]
    for item in bad:
        print("  [FAIL] " + item)
    print("[CHECK] %s 对象 %d 个，异常 %d 个" % (project, len(rows), len(bad)))
    return len(bad)


TYPE_ROLE = {2: "sound", 3: "action", 7: "container"}


def verify_bank(bank, proj, project):
    expected = {}
    for row in plan(proj, project):
        expected.setdefault(row["role"], set()).add(row["value"])
    with open(bank, "rb") as fh:
        data = fh.read()
    _, didx, hirc, _ = ws.parse_bank(data)
    bad = []
    counts = {}
    for typ, body in hirc:
        role = TYPE_ROLE.get(typ)
        if role is None:
            continue
        counts[role] = counts.get(role, 0) + 1
        oid = struct.unpack("<I", body[:4])[0]
        if oid in ANCHORS:
            continue
        if oid not in expected.get(role, set()):
            bad.append("type %d %d 不在 %s 的应得编号里" % (typ, oid, role))
    for item in bad:
        print("  [FAIL] " + item)
    print("[BANK] %s Sound=%d Action=%d ActorMixer=%d 媒体=%d 不合规=%d"
          % (os.path.basename(bank), counts.get("sound", 0), counts.get("action", 0),
             counts.get("container", 0), len(didx), len(bad)))
    return len(bad)


def main():
    argv = sys.argv[1:]
    if len(argv) < 3:
        raise SystemExit(USAGE)
    cmd = argv[0]
    if cmd == "id":
        project = argv[argv.index("--project") + 1]
        asset = argv[argv.index("--asset") + 1]
        role = argv[argv.index("--role") + 1]
        value = compute(project, asset, role)
        slot, role_code, subject = decode(value)
        print("%s  %d  槽位=%d 角色=%s 主体=%d" % (asset, value, slot, ROLE_NAMES[role_code], subject))
        return 0
    proj = argv[2] if cmd == "verify-bank" else argv[1]
    project = argv[argv.index("--project") + 1]
    if cmd == "assign":
        return assign(proj, project, "--dry" in argv)
    if cmd == "check":
        return check(proj, project)
    if cmd == "verify-bank":
        return verify_bank(argv[1], proj, project)
    raise SystemExit(USAGE)


if __name__ == "__main__":
    sys.exit(main())
