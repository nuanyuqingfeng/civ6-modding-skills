# -*- coding: utf-8 -*-
"""monorepo 同步：本地各 skill 仓库 → 云端总仓库 skills/<名>/ 子目录，不建本地镜像工作区。

流程：
  ① 临时克隆总仓库到 %TEMP%/civ6-mono；
  ② 逐个 skill 比对本地 HEAD 树与云端 skills/<名>/ 子树，只处理有差异的：fetch 本地仓库
     → git rm --cached → git read-tree --prefix=skills/<名>/ → git checkout-index -f -a。
     整棵子树替换，本地删掉的文件随之消失。不用 tar 导出：Windows bsdtar 解不开仓库里的
     中文路径（实测 database/api-verification-2026-09-08/ 下 7 个 CSV 报 Invalid empty pathname）；
  ③ 用 tools/monorepo_README.md 覆盖仓库根 README.md（总仓库首页的真源在本地）；
  ④ 提交、推送（直连失败自动改走 Clash 混合端口 127.0.0.1:7897）；
  ⑤ 核对云端 main 与本地提交一致、逐 skill 核对子树树、README 与源文件一致，删除临时目录。

用法：
    python sync_monorepo.py                        # 同步全部有改动的 skill
    python sync_monorepo.py --skills civ6-modding,civ6-tuner
    python sync_monorepo.py --message "sync: ..."   # 自定义提交说明
    python sync_monorepo.py --dry-run               # 建提交后停下：不推送、保留临时目录
    python sync_monorepo.py --keep                  # 推送后保留临时目录
    python sync_monorepo.py --proxy                 # 直连不通时从一开始就走 Clash 代理
    python sync_monorepo.py --url <地址>             # 覆盖总仓库地址（仅测试用）

退出码：0 已同步或云端已是最新 / 1 失败（配置错误、网络不可达、云端前进、核对不符）
"""
import argparse
import os
import shutil
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_ROOT = os.path.dirname(SKILL_DIR)
CLOUD_URL = "https://github.com/nuanyuqingfeng/civ6-modding-skills.git"
PROXY = "http://127.0.0.1:7897"
WORK = os.path.join(os.environ.get("TEMP") or r"C:\Windows\Temp", "civ6-mono")
README_SRC = os.path.join(SKILL_DIR, "tools", "monorepo_README.md")
GIT_FALLBACK = [r"E:\SoftWares\Git\cmd\git.exe", r"C:\Program Files\Git\cmd\git.exe"]


def rmtree_force(path):
    """删目录树；git 克隆出来的 pack 文件带只读属性，Windows 上直接删会被拒绝访问。"""
    def onexc(func, p, exc):
        os.chmod(p, 0o700)
        func(p)
    shutil.rmtree(path, onexc=onexc)


def git_exe():
    p = shutil.which("git")
    if p:
        return p
    for c in GIT_FALLBACK:
        if os.path.isfile(c):
            return c
    raise SystemExit("找不到 git 可执行文件：把 git 加入 PATH，或补进本脚本 GIT_FALLBACK")


def git(args, cwd=None, check=True, proxy=False):
    cmd = [git_exe()]
    if proxy:
        cmd += ["-c", "http.proxy=" + PROXY, "-c", "https.proxy=" + PROXY]
    cmd += list(args)
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit("FAIL git %s\n%s%s" % (" ".join(args), r.stdout, r.stderr))
    return r


FORCE_PROXY = False


def net(args, cwd=None, what="网络操作"):
    if not FORCE_PROXY:
        r = git(args, cwd=cwd, check=False)
        if r.returncode == 0:
            return r
        print("  直连失败，改走 Clash 代理 %s" % PROXY)
    r2 = git(args, cwd=cwd, check=False, proxy=True)
    if r2.returncode != 0:
        raise SystemExit("FAIL %s：%s\n%s%s"
                         % (what, "代理不可用" if FORCE_PROXY else "直连与代理均失败",
                            r2.stdout, r2.stderr))
    return r2


def tree_of(repo, rev="HEAD"):
    return git(["-C", repo, "rev-parse", "%s^{tree}" % rev]).stdout.strip()


def subtree(repo, name):
    r = git(["-C", repo, "rev-parse", "HEAD:skills/%s" % name], check=False)
    return r.stdout.strip() or None


def discover():
    out = []
    for n in sorted(os.listdir(SKILLS_ROOT)):
        if n.startswith("civ6-") and os.path.isdir(os.path.join(SKILLS_ROOT, n, ".git")):
            out.append(n)
    return out


def main():
    global FORCE_PROXY
    ap = argparse.ArgumentParser(description="本地 skill → 云端总仓库 skills/<名>/ 同步")
    ap.add_argument("--skills", default="", help="逗号分隔；缺省扫描 skills 根下全部 civ6-* 仓库")
    ap.add_argument("--url", default=CLOUD_URL, help="总仓库地址（缺省为文档地址）")
    ap.add_argument("--message", default="", help="提交说明；缺省 sync: <skill 列表>")
    ap.add_argument("--dry-run", action="store_true", help="建提交后停下：不推送、保留临时目录")
    ap.add_argument("--keep", action="store_true", help="推送完成后保留临时目录")
    ap.add_argument("--proxy", action="store_true", help="网络操作直接走 Clash 代理，不先试直连")
    a = ap.parse_args()
    FORCE_PROXY = a.proxy
    if FORCE_PROXY:
        print("网络操作：全程走 Clash 代理 %s" % PROXY)

    skills = [s.strip() for s in a.skills.split(",") if s.strip()] or discover()
    if not skills:
        raise SystemExit("没有可同步的 skill：%s 下未发现 civ6-* git 仓库" % SKILLS_ROOT)
    for n in skills:
        if not os.path.isdir(os.path.join(SKILLS_ROOT, n, ".git")):
            raise SystemExit("不是 git 仓库：%s" % os.path.join(SKILLS_ROOT, n))

    if a.url != CLOUD_URL:
        print("注意：本次使用覆盖地址（非文档地址）：%s" % a.url)
    print("总仓库  ：%s" % a.url)
    print("临时目录：%s" % WORK)

    if os.path.isdir(WORK):
        rmtree_force(WORK)
    net(["clone", "--quiet", "--depth", "1", a.url, WORK], what="克隆总仓库")
    base = git(["-C", WORK, "rev-parse", "HEAD"]).stdout.strip()

    readme_want = None
    readme_changed = False
    if os.path.isfile(README_SRC):
        readme_want = open(README_SRC, encoding="utf-8").read()
        dst = os.path.join(WORK, "README.md")
        have = open(dst, encoding="utf-8").read() if os.path.isfile(dst) else None
        readme_changed = have != readme_want
    else:
        print("WARN 找不到 %s，本次不动仓库根 README.md" % README_SRC)

    changed = []
    for n in skills:
        src = os.path.join(SKILLS_ROOT, n)
        if git(["-C", src, "status", "--porcelain"]).stdout.strip():
            print("WARN %s 有未提交改动，本次只同步已提交的 HEAD" % n)
        want = tree_of(src)
        have = subtree(WORK, n)
        if have == want:
            print("  跳过 %-22s 与云端一致" % n)
            continue
        git(["-C", WORK, "fetch", "--no-tags", src, "main:refs/sync/%s" % n])
        git(["-C", WORK, "rm", "-r", "--cached", "--quiet", "--ignore-unmatch", "skills/%s" % n])
        sub = os.path.join(WORK, "skills", n)
        if os.path.isdir(sub):
            rmtree_force(sub)
        git(["-C", WORK, "read-tree", "--prefix=skills/%s/" % n, "refs/sync/%s" % n])
        changed.append(n)
        print("  %-24s %s -> %s" % (n, (have or "云端新增")[:8], want[:8]))

    if not changed and not readme_changed:
        print("云端已是最新，无需提交。")
        if not a.keep:
            rmtree_force(WORK)
        return 0

    git(["-C", WORK, "checkout-index", "-f", "-a"])
    parts = list(changed)
    if readme_changed:
        # 必须放在 checkout-index 之后：它按索引重写整棵工作树，先写的 README 会被
        # 盖回旧内容，随后的 git add 暂存的就是旧版（实测提交被 README 核对挡下）。
        with open(os.path.join(WORK, "README.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(readme_want)
        git(["-C", WORK, "add", "README.md"])
        parts.append("README.md")
        print("  README.md 由 tools/monorepo_README.md 更新")
    msg = a.message or ("sync: " + "、".join(parts))
    git(["-C", WORK, "commit", "-q", "-m", msg])
    head = git(["-C", WORK, "rev-parse", "HEAD"]).stdout.strip()
    print("提交 %s  %s" % (head[:8], msg))

    bad = [n for n in skills if subtree(WORK, n) != tree_of(os.path.join(SKILLS_ROOT, n))]
    if bad:
        raise SystemExit("FAIL 提交内子树与本地 HEAD 不一致：%s" % "、".join(bad))
    print("子树核对：%d 个 skill 全部与本地 HEAD 树一致" % len(skills))

    if os.path.isfile(README_SRC):
        committed = git(["-C", WORK, "show", "HEAD:README.md"]).stdout
        want = open(README_SRC, encoding="utf-8").read()
        if committed.replace("\r\n", "\n").strip("\n") != want.replace("\r\n", "\n").strip("\n"):
            raise SystemExit("FAIL 提交内 README.md 与 tools/monorepo_README.md 不一致")
        print("README 核对：与 tools/monorepo_README.md 一致")

    if a.dry_run:
        print("--dry-run：未推送，临时目录保留在 %s" % WORK)
        return 0

    remote = net(["ls-remote", a.url, "refs/heads/main"], what="探测云端").stdout.split()
    remote_head = remote[0] if remote else ""
    if remote_head != base:
        raise SystemExit("云端 main 已从 %s 前进到 %s，本地提交基于旧基线，未推送；请重跑。"
                         % (base[:8], remote_head[:8]))
    net(["push", a.url, "main:main"], cwd=WORK, what="推送")
    after = net(["ls-remote", a.url, "refs/heads/main"], what="核对云端").stdout.split()
    after_head = after[0] if after else ""
    if after_head != head:
        raise SystemExit("FAIL 推送后云端 main = %s，本地提交 = %s" % (after_head[:8], head[:8]))
    print("云端 main = %s（与本地提交一致）" % after_head)
    if not a.keep:
        rmtree_force(WORK)
        print("临时目录已删除。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
