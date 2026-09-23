#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_leader_2d.py — Civ6 2D 领袖（立绘纸片人）注册文件生成器

根据 civ6-asset-forge skill 的 templates/ 模板生成全套美术注册文件。

## 命名来源铁律（重要）

**一切从 SQL 里该领袖的 `LeaderType` 派生，禁止任何硬编码的作者/模板后缀。**

    LeaderType = LEADER_CARTETHYIA_QYQXP
      -> LeaderSuffix = CARTETHYIA_QYQXP      （去掉 LEADER_ 前缀后的完整剩余部分）

`LeaderSuffix` **原样保留** LeaderType 自带的一切后缀 —— 它们是**结果**，不是**规则**。
历史上本脚本曾把某个作者的专用缩写写死进推导式，导致所有工程的产物都被强行加上该后缀；
现已移除。SQL 里没有该后缀的领袖，生成的命名里也就不会有。

用法:
  python gen_leader_2d.py --project <工程路径> --leader-types "LEADER_A_QYQXP,LEADER_B"
  python gen_leader_2d.py --project <工程路径> [--pack 包名] [--abbr 缩写] \
      --leaders "Cartethyia:CTTH,Fleurdelys:FDL"        # 旧写法（会自动补 --leader-types 缺省值）

  --project       Civ6 mod 工程根目录（含 XLPs/ ArtDefs/ Geometries/ 等子目录）
  --leader-types  **推荐**：SQL 里的 LeaderType 列表（逗号分隔），命名完全由它派生
  --pack          包名，默认取工程目录名小写
  --abbr          文明缩写（如 RGN），默认 RGN；用于 {OBJ} 与 ast 音频前缀
  --leaders       "Name:FX" 列表；可省略 --leader-types 时由它推导 LeaderType

注意:
  1. 本脚本只生成"注册文件"（XML），不处理素材（png/dds/fgx）。
  2. fgx/wig 通用平面模型、环境光 dds 等素材文件需另行复制，本脚本不做。
  3. 素材未提供时 .tex 的 SourceFilePath 指向占位路径，需导入素材后更新。
"""
import argparse
import os
import re
import sys

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')

# 单文件模板 -> 目标子目录。（模板文件名与输出文件名一律不含作者后缀）
SINGLE_FILE_TEMPLATES = [
    ('LEAD_ABBR_Name.geo', 'Geometries', 'LEAD_{abbr}_{name}.geo'),
    ('LEAD_ABBR_Name_Camera.geo', 'Geometries', 'LEAD_{abbr}_{name}_Camera.geo'),
    ('LEAD_ABBR_Name_Material.mtl', 'Materials', 'LEAD_{abbr}_{name}_Material.mtl'),
    ('Name_LightRig.lrg', 'LightRigs', '{name}_LightRig.lrg'),
    ('Name_Environment.env', 'EnvironmentLights', '{name}_Environment.env'),
    ('LEADER_NAME_TEXTURE.tex', 'Textures', 'LEADER_{suffix_upper}_TEXTURE.tex'),
    ('LEADER_NAME_OPACITY.tex', 'Textures', 'LEADER_{suffix_upper}_OPACITY.tex'),
    ('LEAD_ABBR_Name.ast', 'Assets', 'LEAD_{abbr}_{name}.ast'),
]

# 聚合模板 -> 目标子目录
AGGREGATE_TEMPLATES = [
    ('leader_myciv.xlp', 'XLPs', 'leader_{pack}.xlp'),
    ('Leader_LightRigs.xlp', 'XLPs', 'Leader_LightRigs.xlp'),
    ('Leaders.artdef', 'ArtDefs', 'Leaders.artdef'),
]


def leader_type_to_suffix(leader_type):
    """LEADER_CARTETHYIA_QYQXP -> CARTETHYIA_QYQXP（原样保留自带后缀）。"""
    return re.sub(r'^LEADER_', '', leader_type.strip(), flags=re.I)


def parse_leader_types(s):
    """解析 --leader-types：逗号分隔的 LeaderType 列表。"""
    out = []
    for item in s.split(','):
        item = item.strip()
        if not item:
            continue
        if not re.match(r'^LEADER_', item, re.I):
            raise SystemExit('错误: --leader-types 里必须是完整 LeaderType（以 LEADER_ 开头）: %s' % item)
        out.append(item.upper())
    return out


def parse_leaders(s):
    """解析 --leaders： "Name:FX" 列表（旧写法）。"""
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


def display_case(suffix, display_name):
    """把 SQL 后缀还原成工程惯用的混合大小写形式。

    工程惯例是 LEAD_{ABBR}_{Name}_{作者后缀}（如 LEAD_RGN_Cartethyia_QYQXP），
    其中 Name 是混合大小写的展示名，作者后缀保持大写。
    展示名无法从 LeaderType 反推（不知作者后缀边界在哪），所以由 --leaders 提供：
    若展示名（忽略大小写）确实是后缀的前缀，就把该段换成展示名的大小写，
    其余部分（即作者后缀）原样保留；对不上则整体用原样后缀（全大写）。

        suffix=CARTETHYIA_QYQXP, display=Cartethyia  ->  Cartethyia_QYQXP
        suffix=FHB_A_SHUAI,      display=（未给）    ->  FHB_A_SHUAI
    """
    if display_name:
        d = display_name.strip()
        if d and suffix.upper().startswith(d.upper()):
            return d + suffix[len(d):]
    return suffix


def build_repl(suffix, fx, abbr, pack, display_name=''):
    """占位符 -> 值。suffix 来自 SQL LeaderType，脚本不附加任何作者后缀。"""
    name = display_case(suffix, display_name)
    return {
        '{LEADER}': 'LEADER_%s' % suffix.upper(),
        '{OBJ}': 'LEAD_%s_%s' % (abbr, name),
        '{TEX}': 'LEADER_%s_TEXTURE' % suffix.upper(),
        '{OPAC}': 'LEADER_%s_OPACITY' % suffix.upper(),
        '{LR}': '%s_LightRig' % name,
        '{ENV}': '%s_Environment' % name,
        '{SUFFIX}': suffix,
        '{NAME}': name,
        '{FX}': fx,
        '{PACK}': pack,
        '{ABBR}': abbr,
    }


def fill_single(template_text, repl):
    out = template_text
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def fill_aggregate(template_text, entries, abbr, pack):
    """聚合文件：<!-- LEADER_BLOCK_START --> ... <!-- LEADER_BLOCK_END -->
    之间是单领袖样板，按领袖数复制 N 次并替换占位符。

    entries: [(suffix, fx, display_name), ...]
    """
    start_marker = '<!-- LEADER_BLOCK_START -->'
    end_marker = '<!-- LEADER_BLOCK_END -->'
    start = template_text.index(start_marker)
    end = template_text.index(end_marker) + len(end_marker)
    block = template_text[start:end]
    head = template_text[:start]
    tail = template_text[end:]

    blocks_out = []
    for suffix, fx, display in entries:
        b = block
        for k, v in build_repl(suffix, fx, abbr, pack, display).items():
            b = b.replace(k, v)
        b = re.sub(r'[ \t]*<!-- LEADER_BLOCK_START -->\n', '', b)
        b = re.sub(r'\n[ \t]*<!-- LEADER_BLOCK_END -->', '', b)
        b = re.sub(r'[ \t]*<!-- LEADER_BLOCK_START -->', '', b)
        b = re.sub(r'<!-- LEADER_BLOCK_END -->', '', b)
        blocks_out.append(b)
    out = head + '\n'.join(blocks_out) + tail
    out = out.replace('leader_{PACK}', 'leader_%s' % pack)
    out = out.replace('/leaders/leader_{PACK}', '/leaders/leader_%s' % pack)
    return out


def main():
    ap = argparse.ArgumentParser(description='Civ6 2D 领袖注册文件生成器')
    ap.add_argument('--project', required=True, help='Civ6 mod 工程根目录')
    ap.add_argument('--leader-types', default=None,
                    help='SQL 里的 LeaderType 列表（逗号分隔）—— 命名由它派生（推荐）')
    ap.add_argument('--pack', default=None, help='包名（默认取工程目录名小写）')
    ap.add_argument('--abbr', default='RGN', help='文明缩写（默认 RGN）')
    ap.add_argument('--leaders', default=None,
                    help='"Name:FX" 列表（旧写法；未给 --leader-types 时使用）')
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        raise SystemExit('错误: 工程目录不存在: %s' % project)
    pack = args.pack or os.path.basename(project).lower()
    abbr = args.abbr.upper()

    if not args.leader_types and not args.leaders:
        raise SystemExit('错误: 必须给出 --leader-types（推荐）或 --leaders')

    # 建立 entries: [(suffix, fx, display_name), ...]
    leaders_arg = parse_leaders(args.leaders) if args.leaders else []
    fx_by_name = {n.upper(): fx for n, fx in leaders_arg}
    display_by_name = {n.upper(): n for n, _ in leaders_arg}

    if args.leader_types:
        entries = []
        for lt in parse_leader_types(args.leader_types):
            s = leader_type_to_suffix(lt)
            # 展示名：--leaders 里哪个 name 是该后缀的前缀（忽略大小写）就用它
            disp = ''
            for n_up, n_orig in display_by_name.items():
                if s.upper().startswith(n_up) and len(n_up) > len(disp):
                    disp = n_orig
            fx = fx_by_name.get(disp.upper(), 'XXX') if disp else 'XXX'
            entries.append((s, fx, disp))
    else:
        # 旧写法：--leaders 的 name 直接当作 suffix（无后缀可派生）
        entries = [(n, fx, n) for n, fx in leaders_arg]

    if len(entries) > 16:
        raise SystemExit('错误: 领袖数量超过模板槽位上限 (16)')

    print('工程: %s' % project)
    print('包名: %s  缩写: %s' % (pack, abbr))
    print('领袖: %s' % ', '.join('%s->%s(FX=%s)' % (e[0], display_case(e[0], e[2]), e[1])
                                  for e in entries))

    # 单文件模板
    for tpl_name, subdir, out_fmt in SINGLE_FILE_TEMPLATES:
        tpl_path = os.path.join(TEMPLATE_DIR, tpl_name)
        if not os.path.exists(tpl_path):
            raise SystemExit('错误: 模板缺失 %s' % tpl_path)
        with open(tpl_path, encoding='utf-8') as f:
            tpl = f.read()
        for suffix, fx, display in entries:
            out_text = fill_single(tpl, build_repl(suffix, fx, abbr, pack, display))
            out_name = out_fmt.format(abbr=abbr, name=display_case(suffix, display),
                                      suffix=suffix, suffix_upper=suffix.upper(), pack=pack)
            out_path = os.path.join(project, subdir, out_name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8', newline='') as f:
                f.write(out_text)
            print('  生成 %s\\%s' % (subdir, out_name))

    # 聚合文件
    for tpl_name, subdir, out_fmt in AGGREGATE_TEMPLATES:
        tpl_path = os.path.join(TEMPLATE_DIR, tpl_name)
        if not os.path.exists(tpl_path):
            raise SystemExit('错误: 模板缺失 %s' % tpl_path)
        with open(tpl_path, encoding='utf-8') as f:
            tpl = f.read()
        out_text = fill_aggregate(tpl, entries, abbr, pack)
        out_name = out_fmt.format(pack=pack)
        out_path = os.path.join(project, subdir, out_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            f.write(out_text)
        print('  生成 %s\\%s' % (subdir, out_name))

    print('\n完成。注意: fgx/wig/env dds 等素材需另行复制；立绘 png 可用 process_leader_png.py 生成 TEXTURE/OPACITY。')


if __name__ == '__main__':
    main()
