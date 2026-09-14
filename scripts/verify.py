"""校验晋升图标/模板: 轮廓 IoU + 配色采样 + 图形检查
用法: python verify.py <candidate.png> <gt1024.png> [--mode auto|template|final]
template: 中心应为空(无深色图形); final: 中心应有深色图形(对比度检查)
"""
import sys, numpy as np
from PIL import Image
def sil(p, size=256):
    return np.array(Image.open(p).convert('RGBA').resize((size,size),Image.LANCZOS)).astype(int)[:,:,3]>128
def lum(a): return 0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
def palette(p):
    a=np.array(Image.open(p).convert('RGBA')).astype(int)
    al=a[:,:,3]; ys,xs=np.where(al>200)
    cx=int((xs.min()+xs.max())/2); y0,y1=ys.min(),ys.max()
    pts=[]
    for fy in [0.15,0.5,0.85]:
        y=int(y0+(y1-y0)*fy); blk=a[y, max(0,cx-40):cx+40]; m=blk[:,3]>200
        pts.append(tuple(int(v) for v in blk[m][:,:3].mean(axis=0)) if m.any() else None)
    return pts
def main():
    cand, gt = sys.argv[1], sys.argv[2]
    mode = 'auto'
    if '--mode' in sys.argv: mode = sys.argv[sys.argv.index('--mode')+1]
    s1, s2 = sil(cand), sil(gt)
    iou = float((s1&s2).sum())/float(max((s1|s2).sum(),1))
    pal = palette(cand)
    a = np.array(Image.open(cand).convert('RGBA')).astype(int)
    al = a[:,:,3]; ys,xs = np.where(al>200)
    y0,y1,x0,x1 = ys.min(),ys.max(),xs.min(),xs.max()
    cy = int(y0+(y1-y0)*0.44); cx = int((x0+x1)/2)
    r = (a[cy-60:cy+60, cx-60:cx+60])
    dark_ratio = float(((lum(r)<70)&(r[...,3]>200)).mean())
    ok = iou>=0.94
    print(f"silhouette IoU: {iou:.3f}  (threshold 0.94) {'PASS' if ok else 'FAIL'}")
    print(f"palette top/mid/low: {pal}")
    print(f"center dark ratio (44%h, 120px window): {dark_ratio:.3f}")
    if mode=='template' and dark_ratio>0.05: print("WARN: template center not empty")
    if mode=='final' and dark_ratio<0.02: print("WARN: final icon glyph too faint")
    sys.exit(0 if ok else 1)
main()
