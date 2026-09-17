# -*- coding: utf-8 -*-
"""清除 AssetEditor 依赖缓存（可再生文件，按「备份规范」不备份、直接删）。

删除 %APPDATA%\\AssetCloud\\mod-<Mod>-asset-deps.json；下次启动 AssetEditor 会自动重建。

用法：
    python workspace/_tools/clear_ae_cache.py [--mod 示例工程] [--dry-run]
"""
import argparse
import os
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_mod = os.path.basename(os.path.abspath(os.path.join(here, '..', '..')))
    ap = argparse.ArgumentParser(description='清除 AssetEditor 依赖缓存')
    ap.add_argument('--mod', default=default_mod, help='mod 名（默认本工程目录名）')
    ap.add_argument('--dry-run', action='store_true', help='只显示将删除的路径')
    args = ap.parse_args()

    appdata = os.environ.get('APPDATA')
    if not appdata:
        print('ERROR: 找不到 APPDATA 环境变量')
        return 2
    cloud = os.path.join(appdata, 'AssetCloud')
    if not os.path.isdir(cloud):
        print('AssetCloud 目录不存在:', cloud)
        return 0

    target = os.path.join(cloud, 'mod-%s-asset-deps.json' % args.mod)
    if not os.path.exists(target):
        print('缓存不存在（无需清理）:', target)
        return 0
    if args.dry_run:
        print('[dry-run] 将删除:', target)
        return 0
    os.remove(target)
    print('已删除:', target)
    return 0


if __name__ == '__main__':
    sys.exit(main())
