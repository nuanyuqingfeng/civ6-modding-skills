import sys
import struct
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wwise_shortid as ws

# 两个 bank 的内容比对：事件编号集合、媒体编号与尺寸、对象计数、锚点链。
# 用于「先不改号重生成一次，确认与在售 bank 内容一致」这道门。
#
# 用法:
#   python bank_compare.py <新 bank> <在售 bank> [--media size]
#   默认 --media id：媒体按「编号 → 尺寸」整表比对（未改号的重生成）
#   --media size：媒体只比尺寸多重集（解码重建后媒体编号会被重新分配）
# 退出码 = 内容差异项数（0 表示内容一致）

ANCHORS = (88602518, 854467727, 424381547)
TYPE_NAMES = {2: "Sound", 3: "Action", 4: "Event", 7: "ActorMixer"}


def load(path):
    with open(path, "rb") as fh:
        data = fh.read()
    _, didx, hirc, _ = ws.parse_bank(data)
    groups = {}
    for typ, body in hirc:
        groups.setdefault(typ, set()).add(struct.unpack("<I", body[:4])[0])
    mixers = []
    for typ, body in hirc:
        if typ == 7:
            mixers.append((struct.unpack("<I", body[:4])[0], struct.unpack("<I", body[11:15])[0]))
    return groups, {m[0]: m[2] for m in didx}, mixers, len(data)


def anchor_chain(mixers):
    parent = dict(mixers)
    leaf = [oid for oid, pid in mixers if pid == ANCHORS[2]]
    chain = []
    cur = leaf[0] if leaf else 0
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = parent.get(cur, 0)
    return chain


def main():
    argv = sys.argv[1:]
    if len(argv) < 2:
        raise SystemExit("用法: bank_compare.py <新 bank> <在售 bank> [--media size]")
    new_path, old_path = argv[0], argv[1]
    by_size = "--media" in argv and argv[argv.index("--media") + 1] == "size"

    ga, ma, xa, sa = load(new_path)
    gb, mb, xb, sb = load(old_path)
    fails = 0

    print("字节  新=%d 在售=%d" % (sa, sb))
    for typ in sorted(set(ga) | set(gb)):
        na, nb = len(ga.get(typ, [])), len(gb.get(typ, []))
        mark = "" if na == nb else "  <-- 数量不同"
        if na != nb:
            fails += 1
        print("  %-10s 新=%3d 在售=%3d%s" % (TYPE_NAMES.get(typ, str(typ)), na, nb, mark))

    only_new = ga.get(4, set()) - gb.get(4, set())
    only_old = gb.get(4, set()) - ga.get(4, set())
    for tag, diff in (("仅新 bank 有", only_new), ("仅在售有", only_old)):
        if diff:
            fails += 1
            print("  事件%s %d 个: %s" % (tag, len(diff), sorted(diff)[:6]))
    if not only_new and not only_old:
        print("  事件编号：完全一致（%d 个）" % len(ga.get(4, set())))

    if by_size:
        same = sorted(ma.values()) == sorted(mb.values())
        print("  媒体尺寸多重集：%s（新 %d / 在售 %d）" % ("一致" if same else "不同", len(ma), len(mb)))
        if not same:
            fails += 1
    else:
        if ma == mb:
            print("  媒体编号与尺寸：完全一致（%d 个）" % len(ma))
        else:
            fails += 1
            print("  媒体差异：仅新 %d / 仅在售 %d / 同编号不同尺寸 %d"
                  % (len(set(ma) - set(mb)), len(set(mb) - set(ma)),
                     len([k for k in set(ma) & set(mb) if ma[k] != mb[k]])))

    print("  锚点链 新=%s" % anchor_chain(xa))
    print("  锚点链 在售=%s" % anchor_chain(xb))

    print("[COMPARE] 差异项 %d" % fails)
    return fails


if __name__ == "__main__":
    sys.exit(main())
