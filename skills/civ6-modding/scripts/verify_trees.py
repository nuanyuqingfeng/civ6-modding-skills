# -*- coding: utf-8 -*-
"""Verify two directory trees are byte-identical (recursive SHA256 comparison).

Usage: python verify_trees.py <dirA> <dirB>
Exits 0 when identical, 1 otherwise; 2 on usage error.
"""
import hashlib
import os
import sys


def snapshot(root):
    out = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            with open(full, "rb") as f:
                h = hashlib.sha256()
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            out[rel] = (h.hexdigest(), os.path.getsize(full))
    return out


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if len(sys.argv) < 3 or not os.path.isdir(sys.argv[1]) or not os.path.isdir(sys.argv[2]):
        print("用法：python verify_trees.py <dirA> <dirB>（两个目录都必须存在）", file=sys.stderr)
        return 2
    a, b = sys.argv[1], sys.argv[2]
    sa, sb = snapshot(a), snapshot(b)
    only_a = sorted(set(sa) - set(sb))
    only_b = sorted(set(sb) - set(sa))
    diff = sorted(k for k in set(sa) & set(sb) if sa[k][0] != sb[k][0])
    print("A=%s files=%d" % (a, len(sa)))
    print("B=%s files=%d" % (b, len(sb)))
    for label, items in (("only in A", only_a), ("only in B", only_b), ("content differs", diff)):
        print("%s: %d" % (label, len(items)))
        for k in items[:200]:
            print("   - " + k)
    if not only_a and not only_b and not diff:
        print("RESULT: IDENTICAL")
        return 0
    print("RESULT: DIFFERENT")
    return 1


if __name__ == "__main__":
    sys.exit(main())
