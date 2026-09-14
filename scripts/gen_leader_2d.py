#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_leader_2d.py — Civ6 2D 领袖（立绘纸片人）注册文件生成器
根据 civ6-asset-forge skill 的 templates/ 模板生成全套美术注册文件。

用法:
  python gen_leader_2d.py --project <工程路径> [--pack 包名] [--abbr 缩写] \
      --leaders "Cartethyia:CTTH,Fleurdelys:FDL,Cantarella:CTRL,Ciaccona:CCN,Phoebe:PHB,Roccia:ROC"

  --project   Civ6 mod 工程根目录（含 XLPs/ ArtDefs/ Geometries/ 等子目录）
  --pack      包名，默认取工程目录名小写（如 示例工程 -> ragumna_pack）
  --abbr      文明缩写（如 RGN），默认 RGN
  --leaders   "LeaderName:FX缩写" 逗号分隔列表（FX缩写用于 ast 音频前缀）

注意:
  1. 本脚本只生成"注册文件"（XML），不处理素材（png/dds/fgx）。
  2. fgx/wig 通用平面模型、环境光 dds 等素材文件需另行复制，本脚本不做。
  3. 若素材未提供，.tex 的 SourceFilePath 会指向占位路径，需用户导入素材后更新。
"""
import argparse
import os
import re
import shutil
import sys

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')

# 单文件模板 -> 目标子目录
SINGLE_FILE_TEMPLATES = [
    ('LEAD_ABBR_Name_QYQXP.geo', 'Geometries', 'LEAD_{abbr}_{name}_QYQXP.geo'),
    ('LEAD_ABBR_Name_QYQXP_Camera.geo', 'Geometries', 'LEAD_{abbr}_{name}_QYQXP_Camera.geo'),
    ('LEAD_ABBR_Name_QYQXP_Material.mtl', 'Materials', 'LEAD_{abbr}_{name}_QYQXP_Material.mtl'),
    ('Name_QYQXP_LightRig.lrg', 'LightRigs', '{name}_QYQXP_LightRig.lrg'),
    ('Name_QYQXP_Environment.env', 'EnvironmentLights', '{name}_QYQXP_Environment.env'),
    ('LEADER_NAME_QYQXP_TEXTURE.tex', 'Textures', 'LEADER_{name_upper}_QYQXP_TEXTURE.tex'),
    ('LEADER_NAME_QYQXP_OPACITY.tex', 'Textures', 'LEADER_{name_upper}_QYQXP_OPACITY.tex'),
    ('LEAD_ABBR_Name_QYQXP.ast', 'Assets', 'LEAD_{abbr}_{name}_QYQXP.ast'),
]

# 聚合模板 -> 目标子目录
AGGREGATE_TEMPLATES = [
    ('leader_myciv_qyqxp.xlp', 'XLPs', 'leader_{pack}.xlp'),
    ('Leader_LightRigs.xlp', 'XLPs', 'Leader_LightRigs.xlp'),
    ('Leaders.artdef', 'ArtDefs', 'Leaders.artdef'),
]


def parse_leaders(s):
    leaders = []
    for item in s.split(','):
        item = item.strip()
        if not item:
            continue
        if ':' in item:
            name, fx = item.split(':', 1)
        else:
            name, fx = item, 'XXX'
        leaders.append((name.strip(), fx.strip().upper()))
    if not leaders:
        raise SystemExit('错误: --leaders 不能为空')
    return leaders


def fill_single(template_text, name, fx, abbr, pack):
    name_upper = name.upper()
    repl = {
        '{LEADER}': 'LEADER_%s_QYQXP' % name_upper,
        '{OBJ}': 'LEAD_%s_%s_QYQXP' % (abbr, name),
        '{TEX}': 'LEADER_%s_QYQXP_TEXTURE' % name_upper,
        '{OPAC}': 'LEADER_%s_QYQXP_OPACITY' % name_upper,
        '{LR}': '%s_QYQXP_LightRig' % name,
        '{ENV}': '%s_QYQXP_Environment' % name,
        '{FX}': fx,
        '{PACK}': pack,
        '{ABBR}': abbr,
    }
    out = template_text
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def fill_aggregate(template_text, leaders, abbr, pack):
    """聚合文件：模板中 <!-- LEADER_BLOCK_START --> ... <!-- LEADER_BLOCK_END -->
    之间的块为单个领袖样板，按领袖数复制 N 次并替换占位符。"""
    start_marker = '<!-- LEADER_BLOCK_START -->'
    end_marker = '<!-- LEADER_BLOCK_END -->'
    start = template_text.index(start_marker)
    end = template_text.index(end_marker) + len(end_marker)
    block = template_text[start:end]
    head = template_text[:start]
    tail = template_text[end:]

    blocks_out = []
    for name, fx in leaders:
        name_upper = name.upper()
        repl = {
            '{LEADER}': 'LEADER_%s_QYQXP' % name_upper,
            '{OBJ}': 'LEAD_%s_%s_QYQXP' % (abbr, name),
            '{LR}': '%s_QYQXP_LightRig' % name,
            '{ENV}': '%s_QYQXP_Environment' % name,
        }
        b = block
        for k, v in repl.items():
            b = b.replace(k, v)
        b = re.sub(r'[ \t]*<!-- LEADER_BLOCK_START -->\n', '', b)
        b = re.sub(r'\n[ \t]*<!-- LEADER_BLOCK_END -->', '', b)
        b = re.sub(r'[ \t]*<!-- LEADER_BLOCK_START -->', '', b)
        b = re.sub(r'<!-- LEADER_BLOCK_END -->', '', b)
        blocks_out.append(b)
    body = '\n'.join(blocks_out)
    out = head + body + tail
    out = out.replace('leader_{PACK}', 'leader_%s' % pack)
    out = out.replace('/leaders/leader_{PACK}', '/leaders/leader_%s' % pack)
    return out


def main():
    ap = argparse.ArgumentParser(description='Civ6 2D 领袖注册文件生成器')
    ap.add_argument('--project', required=True, help='Civ6 mod 工程根目录')
    ap.add_argument('--pack', default=None, help='包名（默认取工程目录名小写）')
    ap.add_argument('--abbr', default='RGN', help='文明缩写（默认 RGN）')
    ap.add_argument('--leaders', required=True, help='LeaderName:FX缩写 列表，逗号分隔')
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        raise SystemExit('错误: 工程目录不存在: %s' % project)
    pack = args.pack or os.path.basename(project).lower()
    abbr = args.abbr.upper()
    leaders = parse_leaders(args.leaders)
    if len(leaders) > 16:
        raise SystemExit('错误: 领袖数量超过模板槽位上限 (16)')

    print('工程: %s' % project)
    print('包名: %s  缩写: %s  领袖: %s' % (pack, abbr, ', '.join('%s:%s' % l for l in leaders)))

    # 单文件模板
    for tpl_name, subdir, out_fmt in SINGLE_FILE_TEMPLATES:
        tpl_path = os.path.join(TEMPLATE_DIR, tpl_name)
        with open(tpl_path, encoding='utf-8') as f:
            tpl = f.read()
        for name, fx in leaders:
            out_text = fill_single(tpl, name, fx, abbr, pack)
            out_name = out_fmt.format(abbr=abbr, name=name, name_upper=name.upper(), pack=pack)
            out_path = os.path.join(project, subdir, out_name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8', newline='') as f:
                f.write(out_text)
            print('  生成 %s\\%s' % (subdir, out_name))

    # 聚合文件
    for tpl_name, subdir, out_fmt in AGGREGATE_TEMPLATES:
        tpl_path = os.path.join(TEMPLATE_DIR, tpl_name)
        with open(tpl_path, encoding='utf-8') as f:
            tpl = f.read()
        out_text = fill_aggregate(tpl, leaders, abbr, pack)
        out_name = out_fmt.format(pack=pack)
        out_path = os.path.join(project, subdir, out_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            f.write(out_text)
        print('  生成 %s\\%s' % (subdir, out_name))

    print('\n完成。注意: fgx/wig/env dds 等素材需另行复制；立绘 png 可用 process_leader_png.py 生成 TEXTURE/OPACITY。')


if __name__ == '__main__':
    main()