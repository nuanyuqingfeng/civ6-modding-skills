# -*- coding: utf-8 -*-
r"""核对 .civ6proj 的 CDATA 动作块是否按「一元素一行」排版规范书写。

规范真源：project-setup.md「动作块排版规范（硬性）」。

为什么需要它：
    长 CDATA 块（动作全挤在一行时，InGameActionData 单行可达两千字符）在文本编辑器里
    无法核对「在什么前提下加载了哪些文件」。展开成一层两空格后，起始符号与结束符号的
    对应关系、每个参数与文件名的归属都直接可见。手工展开最容易出的错是
    **拆行时吞掉闭标签** —— 把 `</UpdateText><UpdateText ...>` 从中间切开却只写开标签，
    块结构随即断裂，且要到 XML 解析时才报错。本脚本按行检查，在解析失败之前点出位置。

查什么：
    1. 一行一个元素：`</UpdateText><UpdateText ...>` 这类两元素挤一行即违规；
    2. 动作块内缩进每层 +2 空格，闭标签与对应开标签同缩进，
       块闭标签与块开标签同缩进；
    3. 行宽 ≤ --max-width（默认 120）；单个完整叶子元素（`<Tag>文本</Tag>`）豁免
       —— 自然语言无法拆分。

作用范围：
    InGameActionData / FrontEndActionData / ActionCriteriaData 按全部规则查；
    AssociationData / LocalizedTextData 只查「一行一个元素」，它们的自然排版
    （+4 层级）不在本规范内。

只读不写：工程文件的改写一律由 AI 用文件编辑工具完成
（SKILL.md「工程文件写入铁律」），故本脚本不提供 --fix。

用法：
    python check_proj_layout.py <工程根目录>
    python check_proj_layout.py <X.civ6proj>
    python check_proj_layout.py <工程根目录> --max-width 100

退出码：0 通过 / 1 有排版问题 / 2 参数或文件错误。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 块名 -> 内层根标签。前三项按全部规则查，后两项只查「一行一个元素」。
ACTION_BLOCKS = {
    "InGameActionData": "InGameActions",
    "FrontEndActionData": "FrontEndActions",
    "ActionCriteriaData": "ActionCriteria",
}
PASSIVE_BLOCKS = {
    "AssociationData": "Associations",
    "LocalizedTextData": "LocalizedText",
}

TAG = r"[A-Za-z_][\w.:-]*"
LEAF_RE = re.compile(r"<(%s)((?:\s[^<>]*?)?)>[^<>]*</\1>" % TAG)
SELF_RE = re.compile(r"<(%s)((?:\s[^<>]*?)?)\s*/>" % TAG)
ANY_TAG_RE = re.compile(r"</?%s(?:\s[^<>]*?)?/?>" % TAG)
START_RE = re.compile(r"<(%s)((?:\s[^<>]*?)?)>$" % TAG)
END_RE = re.compile(r"</(%s)>$" % TAG)
SELF_FULL_RE = re.compile(r"<(%s)((?:\s[^<>]*?)?)\s*/>$" % TAG)
LEAF_FULL_RE = re.compile(r"<(%s)((?:\s[^<>]*?)?)>[^<>]*</\1>$" % TAG)


def markers(line):
    """返回 (元素标记数, 无法解释的残留)。残留非空即该行含拼接标签或裸文本。"""
    s = line.strip()
    count = 0
    while True:
        m = LEAF_RE.search(s)
        if not m:
            break
        count += 1
        s = s[:m.start()] + s[m.end():]
    while True:
        m = SELF_RE.search(s)
        if not m:
            break
        count += 1
        s = s[:m.start()] + s[m.end():]
    count += len(ANY_TAG_RE.findall(s))
    s = ANY_TAG_RE.sub("", s).strip()
    return count, s


def find_cdata_blocks(lines):
    """定位全部 CDATA 块的开标签行，返回 [(行下标, 块名, 内层根标签)]。"""
    names = list(ACTION_BLOCKS.items()) + list(PASSIVE_BLOCKS.items())
    found = []
    for idx, raw in enumerate(lines):
        s = raw.strip()
        for tag, wrapper in names:
            if s.startswith("<%s><![CDATA[<%s>" % (tag, wrapper)):
                found.append((idx, tag, wrapper))
    return found


def check_block(lines, start_idx, tag, wrapper, problems):
    """检查单个块，返回块的行区间 (start_idx, end_idx)。"""
    close_text = "</%s>]]></%s>" % (wrapper, tag)
    open_raw = lines[start_idx]
    open_indent = len(open_raw) - len(open_raw.lstrip(" "))
    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip() == close_text:
            end_idx = i
            break
    if end_idx is None:
        if close_text in open_raw:
            problems.append((start_idx + 1,
                             "块内容未展开：整段 CDATA 挤在一行，应按一层两空格展开"))
            return start_idx, start_idx
        problems.append((start_idx + 1, "找不到块闭标签 %s" % close_text))
        return start_idx, start_idx

    close_indent = len(lines[end_idx]) - len(lines[end_idx].lstrip(" "))
    if tag in ACTION_BLOCKS and close_indent != open_indent:
        problems.append((end_idx + 1,
                         "块闭标签缩进 %d，应与块开标签同缩进 %d" % (close_indent, open_indent)))

    base = open_indent + 2
    stack = []
    for i in range(start_idx + 1, end_idx):
        raw = lines[i]
        s = raw.strip()
        lineno = i + 1
        if not s:
            problems.append((lineno, "块内出现空行"))
            continue
        if "\t" in raw:
            problems.append((lineno, "缩进含制表符，应为空格"))
        cnt, residue = markers(s)
        if cnt > 1 or residue:
            problems.append((lineno, "一行出现多个元素或残留文本：%s" % s[:70]))
            continue
        if tag not in ACTION_BLOCKS:
            continue
        cur_indent = len(raw) - len(raw.lstrip(" "))
        expected = stack[-1][1] + 2 if stack else base
        m = END_RE.match(s)
        if m:
            if not stack:
                problems.append((lineno, "多余的闭标签 </%s>" % m.group(1)))
                continue
            open_tag, open_indent_inner = stack[-1]
            if m.group(1) != open_tag:
                problems.append((lineno, "闭标签 </%s> 与开标签 <%s> 不配对"
                                 % (m.group(1), open_tag)))
            if cur_indent != open_indent_inner:
                problems.append((lineno, "闭标签 </%s> 缩进 %d，应与开标签同缩进 %d"
                                 % (m.group(1), cur_indent, open_indent_inner)))
            stack.pop()
            continue
        if cur_indent != expected:
            problems.append((lineno, "缩进 %d，应为 %d" % (cur_indent, expected)))
        if not SELF_FULL_RE.match(s) and not LEAF_FULL_RE.match(s):
            m2 = START_RE.match(s)
            if m2:
                stack.append((m2.group(1), cur_indent))
    if stack:
        problems.append((end_idx + 1, "块内未闭合的标签：%s"
                         % ", ".join(t for t, _ in stack)))
    return start_idx, end_idx


def main():
    ap = argparse.ArgumentParser(
        description="核对 .civ6proj 的 CDATA 动作块是否按「一元素一行」排版规范书写")
    ap.add_argument("target", help="工程根目录或 .civ6proj 路径")
    ap.add_argument("--max-width", type=int, default=120,
                    help="结构行的最大宽度（默认 120；单元素叶子文本行豁免）")
    args = ap.parse_args()

    target = os.path.abspath(args.target)
    if os.path.isdir(target):
        proj = None
        for name in sorted(os.listdir(target)):
            if name.endswith(".civ6proj"):
                proj = os.path.join(target, name)
        if not proj:
            print("ERROR: 目录内没有 .civ6proj: %s" % target)
            return 2
    elif os.path.isfile(target) and target.endswith(".civ6proj"):
        proj = target
    else:
        print("ERROR: 既不是目录也不是 .civ6proj: %s" % target)
        return 2

    with open(proj, "rb") as f:
        lines = f.read().decode("utf-8-sig").splitlines()

    print(".civ6proj: %s" % os.path.basename(proj))

    problems = []
    blocks = find_cdata_blocks(lines)
    if not blocks:
        print("ERROR: 未找到任何 CDATA 块")
        return 2

    print("CDATA 块: %d" % len(blocks))
    for idx, tag, wrapper in blocks:
        before = len(problems)
        start_idx, end_idx = check_block(lines, idx, tag, wrapper, problems)
        scope = "全部规则" if tag in ACTION_BLOCKS else "一行一个元素"
        flag = "OK  " if len(problems) == before else "FAIL"
        print("  %s %-20s 行 %4d-%-4d  [%s]" % (flag, tag, start_idx + 1, end_idx + 1, scope))

    wide = []
    for i, raw in enumerate(lines):
        if len(raw) <= args.max_width:
            continue
        if LEAF_FULL_RE.match(raw.strip()):
            wide.append((i + 1, len(raw), "豁免"))
            continue
        wide.append((i + 1, len(raw), "违规"))

    over = [w for w in wide if w[2] == "违规"]
    print("\n[行宽] 上限 %d；超宽 %d 行（其中单元素叶子文本豁免 %d 行）"
          % (args.max_width, len(wide), len(wide) - len(over)))
    for lineno, width, kind in over:
        print("    %s 行 %d，%d 字符" % (kind, lineno, width))

    if problems:
        print("\n[排版] %d 处问题：" % len(problems))
        for lineno, msg in sorted(problems):
            print("    行 %d  %s" % (lineno, msg))
    else:
        print("\n[排版] 无问题")

    ok = not problems and not over
    print("\nRESULT: %s" % ("通过" if ok else "存在排版问题"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
