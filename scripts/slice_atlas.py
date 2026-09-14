"""把 Promotions32.png 图集切成 40 枚晋升图标(带类别与晋升名)
用法: python slice_atlas.py <Promotions32.png> <Icons_Promotions.xml> <outdir>
需要游戏 XML(只读); 输出 idx##_tier_NAME.png (32px 与 128px)
"""
import re, sys, os
from collections import defaultdict
from PIL import Image
atlas, xmlpath, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True); os.makedirs(outdir+"_128", exist_ok=True)
xml = re.sub(r'<!--.*?-->','',open(xmlpath,encoding='utf-8').read(),flags=re.S)
byidx=defaultdict(list)
for attrs in re.findall(r'<Row([^>]*)/>', xml):
    d=dict(re.findall(r'(\w+)="([^"]*)"',attrs))
    if 'Index' in d and d.get('Atlas')=='ICON_ATLAS_PROMOTIONS':
        byidx[int(d['Index'])].append(d['Name'].replace('ICON_PROMOTION_',''))
groups={0:'platinum',1:'gold',2:'silver',3:'bronze'}
im=Image.open(atlas).convert('RGBA')
# 40 有效位的类别按索引次序: 每4个一组 platinum,gold,silver,bronze 循环(实测)
tiermap={}
i=0; tiers=['platinum','gold','silver','bronze']
for idx in range(64):
    r_,c_=divmod(idx,8)
    tile=im.crop((c_*32,r_*32,c_*32+32,r_*32+32))
    if tile.getextrema()[3][1]==0: continue
    tier=tiers[i%4]; i+=1
    nm=byidx.get(idx,[f'IDX{idx}'])[0][:40]
    fn=f"idx{idx:02d}_{tier}_{nm}.png"
    tile.save(os.path.join(outdir,fn))
    tile.resize((128,128),Image.NEAREST).save(os.path.join(outdir+"_128",fn))
    print(fn)
