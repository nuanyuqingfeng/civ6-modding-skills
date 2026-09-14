# -*- coding: utf-8 -*-
"""
ensure_template.py -- 模板自适应保障
1) 检查内置瘦身模板 (assets/template_slim) 与完整模板 (local_paths.json: template_full / 默认教程路径)
2) 完整模板缺失且用户确认后: git clone --depth 1 官方教程仓库, 复制 WWiseProject/FelineJasperKitty 到 --to
3) 写 local_paths.json (template_full=...), 之后 new_bank_project/register 路径自适应
用法: python ensure_template.py [--to <目录>] [--repo https://github.com/dwughjsd/Civ6_Modding_Textbook]
注意: 涉及网络与写入, 运行前须获用户确认 (skill 铁律: 先问再做)。
"""
import os, sys, json, shutil, argparse, subprocess
import paths

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SLIM = os.path.join(SKILL, 'assets', 'template_slim', 'FelineJasperKitty')
LP = os.path.join(SKILL, 'local_paths.json')
DEF_FULL = paths.get('template_full') or '<未配置 template_full>'
DEFAULT_TO = os.path.join(os.path.expanduser('~'), 'Civ6_WWise_Template')
REPO = 'https://github.com/dwughjsd/Civ6_Modding_Textbook'

def load_lp():
    if os.path.exists(LP):
        return json.load(open(LP, encoding='utf-8'))
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--to', default=DEFAULT_TO)
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--confirmed', action='store_true', help='用户已确认下载')
    a = ap.parse_args()
    lp = load_lp()
    full = lp.get('template_full', DEF_FULL)
    print('[1] 内置瘦身模板:', 'OK' if os.path.isdir(SLIM) else '缺失!')
    print('[2] 完整模板 (%s):' % full, 'OK' if os.path.exists(os.path.join(full, 'Yuni.wproj')) else '缺失')
    if os.path.exists(os.path.join(full, 'Yuni.wproj')):
        print('[DONE] 完整模板可用, 无需拉取'); return
    if not a.confirmed:
        print('[ASK] 完整模板缺失 —— 请询问用户是否允许从 %s 拉取 (加 --confirmed 重跑)' % a.repo)
        sys.exit(2)
    to = a.to
    tmp = to + '_clone_tmp'
    if os.path.exists(tmp): shutil.rmtree(tmp)
    if not shutil.which('git'):
        raise SystemExit(
            '[FAIL] 未找到 git。\n'
            '  可安装 git 后重试，或手动下载 %s\n'
            '  并把 WWiseProject/FelineJasperKitty 路径写入 local_paths.json 的 template_full。' % a.repo)
    try:
        subprocess.run(['git', 'clone', '--depth', '1', a.repo, tmp], check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit(
            '[FAIL] git clone 失败: %s\n'
            '  请检查网络/仓库地址；也可手动下载 %s 后配置 template_full。' % (e, a.repo))
    src = os.path.join(tmp, 'WWiseProject', 'FelineJasperKitty')
    if not os.path.isdir(src):
        raise SystemExit('仓库内未找到 WWiseProject/FelineJasperKitty')
    if os.path.exists(to): shutil.rmtree(to)
    shutil.copytree(src, to)
    shutil.rmtree(tmp, ignore_errors=True)
    lp['template_full'] = to
    json.dump(lp, open(LP, 'w', encoding='utf-8'), indent=1)
    print('[DONE] 完整模板已就位: %s\n       路径已写入 local_paths.json (template_full)' % to)

if __name__ == '__main__':
    main()
