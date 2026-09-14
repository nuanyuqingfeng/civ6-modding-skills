# -*- coding: utf-8 -*-
"""旧模板 -> 四类金属重着色 (保浮雕) v2: 分级细节增强 + 高光提亮 + 行基色广播"""
import numpy as np, os, sys
from PIL import Image, ImageFilter
from scipy import ndimage

PALETTES = {
 'platinum': [(224,216,224),(184,168,184),(120,112,112)],
 'gold':     [(232,232,128),(208,208,112),(120,104,64)],
 'silver':   [(120,112,112),(112,104,104),(88,80,88)],
 'bronze':   [(192,168,120),(120,104,64),(80,66,40)],
}
K   = {'platinum':1.8,'gold':1.35,'silver':1.5,'bronze':1.15}   # 细节对比系数
SPEC= {'platinum':120,'gold':80,'silver':100,'bronze':55}       # 高光提亮强度

def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    a = np.array(Image.open(src).convert('RGB')).astype(float)
    H,W,_ = a.shape
    bg = np.median(np.concatenate([a[:40,:40].reshape(-1,3),a[:40,-40:].reshape(-1,3),
                                   a[-40:,:40].reshape(-1,3),a[-40:,-40:].reshape(-1,3)]),axis=0)
    dist = np.sqrt(((a-bg)**2).sum(axis=2))
    mask = dist>55
    mask = ndimage.binary_fill_holes(mask)
    lbl,n = ndimage.label(mask)
    if n>1:
        sizes = ndimage.sum(mask,lbl,range(1,n+1))
        mask = lbl == (1+int(np.argmax(sizes)))
    mask = ndimage.binary_opening(mask, np.ones((5,5)))
    mask = ndimage.binary_fill_holes(mask)
    ys,xs = np.where(mask)
    y0,y1,x0,x1 = ys.min(),ys.max(),xs.min(),xs.max()
    print(f"badge bbox: x{x0}-{x1} y{y0}-{y1} ({(x1-x0+1)/W:.0%}x{(y1-y0+1)/H:.0%})")
    alpha = np.clip((ndimage.gaussian_filter(mask.astype(float),2.0)-0.3)/0.4,0,1)
    L = 0.299*a[:,:,0]+0.587*a[:,:,1]+0.114*a[:,:,2]
    Lb = ndimage.gaussian_filter(L,14.0)
    rel0 = np.clip(L/np.maximum(Lb,1),0.30,1.75)
    v_rows = np.clip((np.arange(H)-y0)/max(y1-y0,1),0,1)   # (H,)
    for metal, stops in PALETTES.items():
        t = v_rows[:,None]
        top,mid,low = map(np.array,stops)
        base_rows = np.where(t<0.5, top*(1-t*2)+mid*(t*2), mid*(1-(t-0.5)*2)+low*((t-0.5)*2))  # (H,3)
        base = np.broadcast_to(base_rows[:,None,:],(H,W,3))
        rel = np.clip(1.0+(rel0-1.0)*K[metal], 0.22, 2.1)
        out = np.clip(base*rel[:,:,None],0,255)
        spec = np.clip(rel-1.25,0,None)*SPEC[metal]
        out = np.clip(out + spec[:,:,None]*np.array([1.0,1.0,1.0]),0,255)
        # 锐化恢复被平滑的棱线
        outf = Image.fromarray(out.astype(np.uint8),'RGB').filter(ImageFilter.UnsharpMask(radius=4, percent=90, threshold=2))
        out = np.array(outf).astype(float)
        rgba = np.dstack([out, alpha*255]).astype(np.uint8)
        img = Image.fromarray(rgba,'RGBA')
        wbg = Image.new('RGBA',img.size,(255,255,255,255)); wbg.alpha_composite(img)
        wbg.convert('RGB').save(os.path.join(outdir,f'{metal}_full.png'))
        img.save(os.path.join(outdir,f'{metal}_alpha.png'))
        img.resize((1024,1024),Image.LANCZOS).save(os.path.join(outdir,f'{metal}_1024.png'))
        bw,bh = x1-x0+1, y1-y0+1
        scale = min(24.0/32*bw and (24/32)*32/bw, (27/32)*32/bh)
        scale = min((24/32)*32/bw,(27/32)*32/bh)
        nw,nh = int(round(bw*scale)), int(round(bh*scale))
        g32 = Image.new('RGBA',(32,32),(0,0,0,0))
        badge = img.crop((x0,y0,x1+1,y1+1)).resize((nw,nh),Image.LANCZOS)
        g32.alpha_composite(badge,((32-nw)//2, int(round(32*4/32)) + max(0,(int(32*27/32)-nh)//2)))
        g32.save(os.path.join(outdir,f'{metal}_game32.png'))
        print(metal,'done')
if __name__=='__main__':
    main(sys.argv[1],sys.argv[2])
