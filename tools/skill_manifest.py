# -*- coding: utf-8 -*-
"""名录生成器：扫描一个 skill 的脚本，从各自 docstring 抽出「用途 + 用法」，
生成/刷新该 skill 的 `TOOLS.md`（可复用工具名录 + 路径收纳）。

为什么要有它：名录最大的敌人是**过时** —— 手工维护的清单迟早与磁盘脱节，
而脱节的名录会让"先查再改"变成"查了也不敢信"。所以名录由脚本从真实磁盘生成，
只有需要人判断的部分留在受保护的人工区块里。

幂等与保护：
  · `<!-- MANUAL:BEGIN -->` … `<!-- MANUAL:END -->` 之间的内容**原样保留**（首次生成时写入模板）。
  · 其余部分每次重跑都按磁盘重建。
  · 表格里登记的脚本必须真实存在；已删除的脚本会从表格消失（并在 stdout 提示 diff）。

用法：
    python skill_manifest.py <skill 目录名或绝对路径> [...]      # 指定 skill
    python skill_manifest.py --all-civ6                          # 批量刷新全部 civ6-* skill
    python skill_manifest.py civ6-modding --check                # 只比对，不写盘（CI / 提交前）

退出码：0 已写/一致 / 1 --check 发现名录与磁盘不一致
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILLS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCAN_DIRS = ["scripts", "tools", "art", "release/scripts"]
CODE_EXT = {".py", ".mjs", ".js", ".ps1", ".sh"}
MANUAL_BEGIN = "<!-- MANUAL:BEGIN -->"
MANUAL_END = "<!-- MANUAL:END -->"

MANUAL_TEMPLATE = """{b}
## 人工备注（重跑生成器时原样保留）

<!-- 在这里写：工具之间的顺序、踩过的坑、必须人工确认的边界。
     不要在这里重复上表的机械信息 —— 那部分由 skill_manifest.py 重生成。 -->

- （待补）

{e}"""


PATHS_SECTION = """## 路径收纳（本机绝对路径，勿写死进脚本）

Py 工具统一走路径解析器；**换机器只改 `civ6-modding/local_paths.json` 一处**。

```bash
python "<skills>/civ6-modding/tools/_paths.py"        # 打印 P1-P6 + 外部工具的实际解析结果
```

| 键 | 含义 |
|---|---|
| `modbuddy` | ModBuddy 源工程根（P1） |
| `mods` | 游戏 Mods 加载目录（P2） |
| `game` | 游戏本体：UI / Lua / XML 官方原文（P3） |
| `sdk_assets` | SDK Assets：artdef / 解包素材（P4） |
| `sdk` | SDK 工具：ModBuddy / MSBuild（P5） |
| `workshop_ref` | 创意工坊参考件，AppID 289070（P6） |
| `uploader` | 工坊上传器 exe（非 Trimmed 构建） |
| `sd_cpp` | 本地生图（stable-diffusion.cpp + FLUX 权重） |
| `imagemagick` | ImageMagick（图标阈值 / 裁边） |
| `luac` | Lua 5.1 语法检查 |
| `ws_root` | 上传临时工作区根（`%TEMP%\\civ6-ws`） |
| `steam_logs` | Steam 日志目录（反查工坊条目 ID） |

> 完整路径表与各键本机取值见 `civ6-modding/tools/README.md` 第 2 节；
> 生图**渠道可用性**（哪个模型还能用、失败模式）见
> `C:\\Users\\Administrator\\.config\\opencode\\imagegen-channels.md`，不在本文件维护。
"""


def _py_docstring(path: str) -> str:
    try:
        # utf-8-sig：PS1/部分脚本带 BOM，用 utf-8 读会让首行变成 "\ufeff# ..."，
        # 于是"注释块从第一行开始"的判断整体失效（实测 convert_art.ps1 因此被判为无 docstring）
        return ast.get_docstring(ast.parse(open(path, encoding="utf-8-sig").read())) or ""
    except Exception:
        return ""


def _comment_block(path: str) -> str:
    """非 Python：取文件**头部**注释块（支持 `//`、`#`、`/* … */`）。

    只扫头部 —— 早期版本允许"out 为空就继续扫"，结果把代码中间的第一条 `//` 注释
    当成 header（实测把 `// story` 认成了 `（语料执行器已移除）` 的用途）。
    """
    text = open(path, encoding="utf-8-sig", errors="replace").read()
    text = re.sub(r"^#![^\n]*\n", "", text)              # 先剥 shebang
    m = re.match(r"\s*/\*(.*?)\*/", text, re.S)          # JS/MJS 块注释（含 JSDoc）
    if not m:
        m = re.match(r"\s*<#(.*?)#>", text, re.S)        # PowerShell 块注释
    if m:
        return "\n".join(re.sub(r"^\s*\*+\s?", "", l) for l in m.group(1).splitlines())
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if out:
                break
            continue
        if s.startswith("//") or s.startswith("#"):
            out.append(re.sub(r"^(//+|#+)\s?", "", s))
        else:
            break
    return "\n".join(out)


def docstring_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return _py_docstring(path) if ext == ".py" else _comment_block(path)


_SEP = re.compile(r"^[\s─═=\-*_·—]+$")
_RUN = re.compile(r"^(python|node|pwsh|powershell|bash|sh)\s")
_USAGE_ONLY = re.compile(r"^(用法|使用方法|Usage)[^:：]*[:：]?\s*$", re.I)
_SECTION = re.compile(r"^[^:：]{1,12}[:：]$")          # 短节标题，如「行为:」「产出:」


def purpose_of(doc: str, name: str) -> str:
    for line in doc.splitlines():
        s = line.strip()
        if not s or _SEP.match(s) or _USAGE_ONLY.match(s) or _SECTION.match(s) or _RUN.match(s):
            continue
        s = re.sub(r"^%s\s*[-—:：]\s*" % re.escape(name), "", s)
        if s:
            return s
    return "（无 docstring，待补）"


def usage_of(doc: str, name: str = "") -> str:
    lines = doc.splitlines()

    def prefer(cands: list[str]) -> str | None:
        """优先取含脚本自身文件名的命令行，其次取第一条。"""
        if not cands:
            return None
        if name:
            hit = [c for c in cands if name in c]
            if hit:
                return "<br>".join(hit[:2])
        return cands[0]

    # ① 单行内联：`用法: python x.py ...`
    for l in lines:
        m = re.match(r"^\s*(用法|使用方法|Usage)\s*[:：]\s*(\S.*)$", l, re.I)
        if m:
            got = prefer([m.group(2).strip()])
            if got:
                return got

    # ② 节标题 + 后续若干行
    for i, l in enumerate(lines):
        s = l.strip()
        if _USAGE_ONLY.match(s) and s.endswith((":", "：")):
            got = []
            for l2 in lines[i + 1:i + 6]:
                s2 = l2.strip()
                if not s2:
                    if got:
                        break
                    continue
                if re.match(r"^\s*(退出码|输出|产出|依赖|注意|前置|Mode|Output|Args|行为)", s2):
                    break
                got.append(s2)
            hit = prefer(got)
            if hit:
                return hit

    # ③ 兜底 a：doc 里任何一行以 python/node/pwsh 开头
    cands = [l.strip() for l in lines if _RUN.match(l.strip())]
    hit = prefer(cands)
    if hit:
        return hit
    # ③ 兜底 b：任何一行里出现脚本自身文件名（常见写法 `<name> <参数> …`）
    if name:
        cands = [l.strip() for l in lines if name in l and len(l.strip()) > 8]
        hit = prefer(cands)
        if hit:
            return hit
    return "（见脚本 docstring）"


def load_overrides(skill_dir: str) -> dict:
    """可选 `<skill>/TOOLS.overrides.json`：{'rel/path.py': {'purpose': '…', 'usage': '…'}}

    给"docstring 抽不出人话"的少数脚本留的出口 —— 覆盖值参与生成，因此重跑不会丢。
    """
    p = os.path.join(skill_dir, "TOOLS.overrides.json")
    if not os.path.isfile(p):
        return {}
    try:
        import json
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print("WARN 读取 %s 失败：%s" % (p, e), file=sys.stderr)
        return {}


def collect(skill_dir: str) -> list[tuple[str, str, str, str]]:
    """返回 [(相对路径, 用途, 用法, 字节数)]，按路径排序。"""
    overrides = load_overrides(skill_dir)
    rows = []
    for sub in SCAN_DIRS:
        d = os.path.join(skill_dir, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if not os.path.isfile(p) or os.path.splitext(name)[1].lower() not in CODE_EXT:
                continue
            rel = os.path.relpath(p, skill_dir).replace(os.sep, "/")
            doc = docstring_of(p)
            stem = os.path.splitext(name)[0]
            ov = overrides.get(rel) or {}
            usage = ov.get("usage") or usage_of(doc, stem)
            if usage == "（见脚本 docstring）":
                try:
                    body = open(p, encoding="utf-8-sig", errors="replace").read()
                except OSError:
                    body = ""
                if "__main__" not in body and "argparse" not in body:
                    usage = "（库：被其它脚本 import，无独立 CLI）"
            rows.append((rel,
                         ov.get("purpose") or purpose_of(doc, stem),
                         usage,
                         os.path.getsize(p)))
    rows.sort(key=lambda r: r[0])
    return rows


def render(skill: str, skill_dir: str, rows: list[tuple]) -> str:
    body = [
        "# %s/TOOLS.md —— 可复用工具名录（先查这里，再动手）" % skill,
        "",
        "> **硬性约定**：要写脚本做某件事之前，**先查本名录**；有能用的就**改它**，不要重建。",
        "> 新增脚本 → 同一次改动里跑 `python civ6-modding/tools/skill_manifest.py %s` 刷新本文件。" % skill,
        "> 本目录的工具全部零第三方依赖（Python 标准库 / Node 内置），带退出码，可直接接 CI。",
        "> 跨 skill 先看 `civ6-modding/TOOLS.md`（通用工具）与 `civ6-modding/reference/FAMILY_INDEX.md`（家族路由）。",
        "",
        "## 工具名录（由 `skill_manifest.py` 扫描磁盘生成，勿手改表格）",
        "",
        "| 工具 | 干什么 | 用法 |",
        "|---|---|---|",
    ]
    if not rows:
        body.append("| （本 skill 暂无脚本） | | |")
    for rel, purpose, usage, size in rows:
        body.append("| `%s` | %s | `%s` |" % (rel, purpose.replace("|", "\\|"),
                                              usage.replace("|", "\\|")))
    body += [
        "",
        "共 %d 个脚本。" % len(rows),
        "",
        PATHS_SECTION,
        MANUAL_TEMPLATE.format(b=MANUAL_BEGIN, e=MANUAL_END),
        "",
    ]
    return "\n".join(body)


def extract_manual(old: str) -> str | None:
    m = re.search(re.escape(MANUAL_BEGIN) + r"(.*?)" + re.escape(MANUAL_END), old, re.S)
    return m.group(0) if m else None


def process(target: str, check_only: bool) -> int:
    skill_dir = target if os.path.isdir(target) else os.path.join(SKILLS_ROOT, target)
    if not os.path.isdir(skill_dir):
        print("SKIP 找不到 skill 目录：%s" % target)
        return 0
    skill = os.path.basename(skill_dir.rstrip(os.sep))
    rows = collect(skill_dir)
    new = render(skill, skill_dir, rows)

    out_path = os.path.join(skill_dir, "TOOLS.md")
    old = open(out_path, encoding="utf-8").read() if os.path.isfile(out_path) else ""
    manual = extract_manual(old)
    if manual:
        new = re.sub(re.escape(MANUAL_BEGIN) + r".*?" + re.escape(MANUAL_END), manual, new, flags=re.S)

    if check_only:
        if old != new:
            print("DRIFT %-24s 名录与磁盘不一致（跑一次生成器即可）" % skill)
            return 1
        print("OK    %-24s 一致（%d 个脚本）" % (skill, len(rows)))
        return 0

    action = "更新" if old and old != new else ("新建" if not old else "无需改动")
    if old != new:
        open(out_path, "w", encoding="utf-8", newline="\n").write(new)
    print("%-6s %-24s %2d 个脚本  ->  %s" % (action, skill, len(rows), out_path))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="skill 工具名录生成/刷新")
    ap.add_argument("skills", nargs="*", help="skill 目录名或绝对路径")
    ap.add_argument("--all-civ6", action="store_true", help="刷新全部 civ6-* skill")
    ap.add_argument("--check", action="store_true", help="只比对不写盘（名录漂移检测）")
    args = ap.parse_args()

    targets = list(args.skills)
    if args.all_civ6:
        targets += sorted(d for d in os.listdir(SKILLS_ROOT)
                          if d.startswith("civ6-") and os.path.isdir(os.path.join(SKILLS_ROOT, d)))
    if not targets:
        ap.error("至少给一个 skill，或用 --all-civ6")

    rc = 0
    for t in targets:
        rc |= process(t, args.check)
    return rc


if __name__ == "__main__":
    sys.exit(main())
