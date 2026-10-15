# -*- coding: utf-8 -*-
"""Art.xml 增量接线：调用 civ6-modding/art/gen_modartxml.py 的 --ensure 系列。

调用方只拼需求清单，不接触 XML 结构。跨 skill 调用走子进程，不建立 sys.path 依赖。

kernel 定位链：本 skill 同级 civ6-modding/art → ~/.agents/skills/civ6-modding/art →
环境变量 CIV6_SKILLS_ROOT 指定的 skills 根。与 gen_suk_portrait.py 的 dds_io 定位同式。

输出捕获按本家族约定落临时文件再读回（受限宿主禁管道捕获）。
"""
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDS = [
    os.path.join(_HERE, "..", "..", "civ6-modding", "art"),
    os.path.join(os.path.expanduser("~"), ".agents", "skills", "civ6-modding", "art"),
]
if os.environ.get("CIV6_SKILLS_ROOT"):
    _CANDS.insert(0, os.path.join(os.environ["CIV6_SKILLS_ROOT"], "civ6-modding", "art"))


def kernel():
    """定位 gen_modartxml.py；找不到即报错，不静默降级。"""
    for cand in _CANDS:
        p = os.path.join(os.path.abspath(cand), "gen_modartxml.py")
        if os.path.isfile(p):
            return p
    raise SystemExit("找不到 civ6-modding/art/gen_modartxml.py；"
                     "可用环境变量 CIV6_SKILLS_ROOT 指向 skills 根目录。")


def ensure(project, consumers=(), libraries=(), required=()):
    """对工程 Art.xml 做增量接线，返回 (退出码, 输出文本)。

    退出码 0 = 无需改动；2 = 改写结果已入位 <工程>/workspace/gen/，
    由 AI 用文件编辑工具写入工程对应路径。
    """
    argv = [sys.executable, kernel(), str(project)]
    for consumer, artdef in consumers:
        argv += ["--ensure-consumer", "%s=%s" % (consumer, artdef)]
    for library, package in libraries:
        argv += ["--ensure-library", "%s=%s" % (library, package)]
    for package in required:
        argv += ["--ensure-required", package]
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "out.txt")
        with open(log, "wb") as fh:
            rc = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT).returncode
        text = open(log, encoding="utf-8", errors="replace").read()
    return rc, text
