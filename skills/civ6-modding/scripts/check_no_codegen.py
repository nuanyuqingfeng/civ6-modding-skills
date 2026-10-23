# -*- coding: utf-8 -*-
"""代码文件生成闸：跑任何生成器前后各校验一次，任何新增或被改动的代码文件都判违规。

铁律真源：焚诀「禁止用程序化的方式编写或修改任何代码文件（最严厉铁律）」。

代码文件指 .sql / .lua / .xml / .ini / .gitignore / .gitattributes。脚本与工具只允许把结果
写成 workspace/gen/reports/ 下的数据清单，由人逐行写入工程。本工具的作用是把这条铁律变成
可执行的闸门：生成器跑之前留一份哈希基线，跑完再比一次，任何代码文件新增或内容变化即失败。

用法:
    python check_no_codegen.py snapshot <根目录> [--baseline <json>]
    python check_no_codegen.py --check <根目录> [--baseline <json>]

基线缺省落在 <根目录>/workspace/gen/reports/codegen_baseline.json。

判定口径:
  新增     基线里没有、现在存在的代码文件            -> 违规
  改动     基线里存在、哈希不同                      -> 违规
  删除     基线里存在、现在不存在                    -> 只报告（删除是持久意图，不判违规）

退出码: 0 无违规；1 有违规；2 参数或文件错误。
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _projwrite import workspace_gen  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CODE_EXTS = (".sql", ".lua", ".xml", ".ini", ".gitignore", ".gitattributes")
PROJECT_EXTS = (".civ6sln", ".civ6proj", ".modinfo")

SKIP_DIRS = {"workspace", ".git", "__pycache__", "Mods", "Build", "Cooked",
             "bin", "obj", "node_modules"}


def baseline_path(root, given):
    if given:
        return os.path.abspath(given)
    return os.path.join(workspace_gen(root), "reports", "codegen_baseline.json")


def is_code_file(name):
    lower = name.lower()
    return any(lower.endswith(ext) for ext in CODE_EXTS + PROJECT_EXTS)


def scan(root):
    """遍历根目录，返回 {相对路径(posix): sha256}，只收代码文件与三个工程文件。"""
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if not is_code_file(name):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            with open(path, "rb") as handle:
                found[rel] = hashlib.sha256(handle.read()).hexdigest()
    return found


def cmd_snapshot(args):
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("FAIL 目录不存在：%s" % root)
        return 2
    table = scan(root)
    out = baseline_path(root, args.baseline)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"root": root, "files": table}, handle, ensure_ascii=False,
                  indent=2, sort_keys=True)
        handle.write("\n")
    print("基线 %s（%d 个代码文件）" % (out, len(table)))
    return 0


def cmd_check(args):
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("FAIL 目录不存在：%s" % root)
        return 2
    path = baseline_path(root, args.baseline)
    if not os.path.isfile(path):
        print("FAIL 基线不存在：%s（先跑 snapshot）" % path)
        return 2
    with open(path, encoding="utf-8") as handle:
        base = json.load(handle)
    before = base.get("files") or {}
    now = scan(root)

    added = sorted(set(now) - set(before))
    changed = sorted(rel for rel in set(now) & set(before) if now[rel] != before[rel])
    removed = sorted(set(before) - set(now))

    for rel in added:
        print("违规    新增代码文件  %s" % rel)
    for rel in changed:
        print("违规    代码文件被改动  %s" % rel)
    for rel in removed:
        print("报告    代码文件已删除  %s" % rel)

    print("")
    print("基线 %s" % path)
    print("共扫描 %d 个文件：新增 %d / 改动 %d / 删除 %d"
          % (len(now), len(added), len(changed), len(removed)))
    if added or changed:
        print("FAIL 生成器产出了代码文件，按焚诀·最严厉铁律判整个任务不合格。")
        return 1
    print("[OK] 无代码文件由生成器产出")
    return 0


def main():
    ap = argparse.ArgumentParser(description="代码文件生成闸")
    ap.add_argument("command", nargs="?", default=None,
                    help="snapshot 留基线；check 比对（也可用 --check）")
    ap.add_argument("root", nargs="?", default=None, help="工程根或解决方案根")
    ap.add_argument("--check", action="store_true", help="比对基线")
    ap.add_argument("--baseline", default=None, help="基线文件路径")
    args = ap.parse_args()

    if args.check or args.command == "check":
        args.root = args.root or args.command
        return cmd_check(args)
    if args.command == "snapshot":
        return cmd_snapshot(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
