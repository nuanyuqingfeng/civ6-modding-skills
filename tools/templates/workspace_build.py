# -*- coding: utf-8 -*-
"""build.py —— 本工程的构建与校验入口（由 new_project.py 生成，与本工程同名）。

## 与其他工程的区别

本脚本**不往工程里复制任何 skill 脚本**，而是直接调 civ6-modding skill 里的那一份。
把 check_*.py 拷进 workspace/_tools 再各自演化的做法实测会让校验口径与 skill 分叉
（Ragunna_Pack 的 5 个同名脚本与 skill 版本已全部不同），skill 更新也传不进来。

## 落盘边界（硬性）

工作区里只允许出现两类东西：

  1. **mod 成品**：工程根下 Data/ 与 Text/ 里的 SQL / XML，加上 .civ6proj、.gitignore、
     .gitattributes、AGENTS.md；
  2. **workspace/ 下的全部内容** —— 脚本、日志、派生产物、设计文档、资料、中间产物。

工程根不落任何构建产物。日常迭代走 stage + verify，产物全部落在 workspace/gen/。

## 用法

    python workspace/_tools/build.py check      # 跑校验套件（默认动作，顺序同 skill ①–⑧）
    python workspace/_tools/build.py modinfo    # 派生 .modinfo 到 workspace/gen/
    python workspace/_tools/build.py stage      # 部署到 workspace/gen/Mods/（不动游戏目录）
    python workspace/_tools/build.py verify     # 源工程 ↔ 暂存副本 一致性体检
    python workspace/_tools/build.py deploy     # 部署到游戏 Mods 目录（需要该目录的写权限）

## 退出码

0 全部通过 / 1 有失败项 / 2 环境问题（找不到工程、找不到 skill、副本未就绪）
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # workspace/_tools/build.py → 工程根
WS = os.path.join(PROJ, "workspace")
GEN = os.path.join(WS, "gen")
TMP = os.path.join(WS, "tmp")
STAGE_MODS = os.path.join(GEN, "Mods")


def locate_skill() -> str:
    """定位 civ6-modding skill 目录。

    依次在本机常见的 skill 根下找 civ6-modding/tools/_paths.py，找到即返回。
    不把本机绝对路径写死在脚本里 —— skill 换了存放位置、或工程被搬到别的机器时，
    这里会自己找到，不必改代码。
    """
    home = os.path.expanduser("~")
    roots = [
        os.path.join(home, ".agents", "skills"),
        os.path.join(home, ".config", "opencode", "skills"),
        os.path.join(home, ".claude", "skills"),
        os.path.join(home, ".codex", "skills"),
        os.path.join(home, ".dsh", "skills"),
    ]
    env = os.environ.get("CIV6_SKILL_ROOT")
    if env:
        roots.insert(0, env)
    for root in roots:
        cand = os.path.join(root, "civ6-modding")
        if os.path.isfile(os.path.join(cand, "tools", "_paths.py")):
            return cand
    raise SystemExit("找不到 civ6-modding skill（已查：%s）" % "、".join(roots))


SKILL = locate_skill()
TOOLS = os.path.join(SKILL, "tools")
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, TOOLS)
import _paths  # noqa: E402


def find_proj() -> str:
    hits = [f for f in os.listdir(PROJ) if f.endswith(".civ6proj")]
    if len(hits) != 1:
        raise SystemExit("工程根下应恰好有 1 个 .civ6proj，实际 %d 个" % len(hits))
    return os.path.join(PROJ, hits[0])


def run(label: str, cmd: list) -> int:
    print("=" * 66)
    print(">>> %s" % label)
    rc = subprocess.run(cmd).returncode
    print("<<< %s  退出码 %d" % (label, rc))
    return rc


def py(script: str, *args: str) -> list:
    return [sys.executable, script, *args]


def mod_name(proj: str) -> str:
    return os.path.splitext(os.path.basename(proj))[0]


def cmd_check(_args) -> int:
    """按 skill scripts/README.md「标准验证顺序」①–⑧ 执行，顺序不重排。"""
    os.makedirs(TMP, exist_ok=True)
    data, text = os.path.join(PROJ, "Data"), os.path.join(PROJ, "Text")
    s = lambda n: os.path.join(SCRIPTS, n)
    steps = [
        ("① SQL 可执行性（Data）", py(s("check_sql_exec.py"), "--root", data)),
        ("① SQL 可执行性（Text）", py(s("check_sql_exec.py"), "--root", text)),
        ("② 引用完整性", ["node", s("rgn_validate_runner.mjs"), data]),
        ("③ Types.Kind 合法性", py(s("check_types_kinds.py"), "--root", PROJ)),
        ("④ SQL 语义反模式（Data）", py(s("check_sql_antipatterns.py"), data)),
        ("④ SQL 语义反模式（Text）", py(s("check_sql_antipatterns.py"), text)),
        ("⑤ Content 清单闭合", py(s("check_proj_content.py"), PROJ)),
        ("⑥ .lua 注册路径", py(s("check_lua_registration.py"), PROJ)),
        ("⑦ Lua 跨上下文", py(s("check_lua_context.py"), PROJ)),
        ("⑧ pantry 卫生", py(s("check_pantry.py"), "--root", PROJ, "--quiet")),
        ("⑧ 换行分层", py(s("normalize_eol.py"), PROJ)),
    ]
    failed = [label for label, cmd in steps if run(label, cmd) != 0]
    print("=" * 66)
    if failed:
        print("FAIL 未通过 %d 项：%s" % (len(failed), "、".join(failed)))
        return 1
    print("PASS 校验套件全部通过（%d 项）" % len(steps))
    return 0


def cmd_modinfo(_args) -> int:
    os.makedirs(GEN, exist_ok=True)
    proj = find_proj()
    out = os.path.join(GEN, mod_name(proj) + ".modinfo")
    rc = run("派生 .modinfo", py(os.path.join(TOOLS, "modinfo_build.py"), proj, "--out", out))
    if rc == 0:
        print("产物：%s" % out)
    return rc


def cmd_stage(_args) -> int:
    """部署到 workspace/gen/Mods/：整条部署链（含引用闭合硬检查）在 workspace 内可反复验证。"""
    os.makedirs(STAGE_MODS, exist_ok=True)
    proj = find_proj()
    return run("部署到 workspace 暂存区", py(os.path.join(TOOLS, "modinfo_build.py"),
                                          proj, "--deploy", "--mods-root", STAGE_MODS))


def cmd_verify(args) -> int:
    # --src 收的是工程目录，不是 .civ6proj 文件路径
    mod_dir = args.mods or os.path.join(STAGE_MODS, mod_name(find_proj()))
    if not os.path.isdir(mod_dir):
        print("副本不存在：%s" % mod_dir)
        print("先跑 python workspace/_tools/build.py stage")
        return 2
    return run("交付包体检", py(os.path.join(TOOLS, "verify_mod_package.py"),
                                "--src", PROJ, "--mods", mod_dir))


def cmd_deploy(_args) -> int:
    """部署到游戏 Mods 目录。该目录在 workspace 之外，需要写权限；无权限时用 stage。"""
    mods = _paths.get("mods")
    if not mods:
        print("找不到游戏 Mods 目录，请检查 civ6-modding/local_paths.json")
        return 2
    os.makedirs(TMP, exist_ok=True)
    return run("部署到 %s" % mods, py(os.path.join(TOOLS, "modinfo_build.py"), find_proj(), "--deploy"))


def main() -> int:
    ap = argparse.ArgumentParser(description="%s 构建 / 校验入口" % os.path.basename(PROJ))
    ap.add_argument("action", nargs="?", default="check",
                    choices=["check", "modinfo", "stage", "verify", "deploy"])
    ap.add_argument("--mods", help="verify：指定要体检的 Mods 副本目录（默认用暂存区）")
    args = ap.parse_args()

    return {"check": cmd_check, "modinfo": cmd_modinfo, "stage": cmd_stage,
            "verify": cmd_verify, "deploy": cmd_deploy}[args.action](args)


if __name__ == "__main__":
    sys.exit(main())