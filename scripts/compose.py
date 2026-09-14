"""确定性合成器: 白色图标 + 盾形模板 -> 原版风格晋升图标"""
from PIL import Image, ImageFilter
import numpy as np, sys
def compose(tpl_path, glyph_path, out_path, scale=0.55, cy_frac=0.44, color=(18,8,4), shadow=True):
    tpl = Image.open(tpl_path).convert('RGBA')
    W,H = tpl.size
    # shield width from alpha bbox
    a = np.array(tpl)[:,:,3]
    ys,xs = np.where(a>128)
    sw = xs.max()-xs.min()+1
    scx, scy = (xs.min()+xs.max())/2, (ys.min()+ys.max())/2
    g = Image.open(glyph_path).convert('RGBA').resize((1024,1024), Image.LANCZOS)
    ga = np.array(g).astype(float)
    dark = np.zeros_like(ga)
    dark[...,0],dark[...,1],dark[...,2] = color
    dark[...,3] = ga[...,3]
    target = int(sw*scale)
    gl = Image.fromarray(dark.astype(np.uint8)).resize((target,target), Image.LANCZOS)
    out = tpl.copy()
    if shadow:
        sh = np.array(gl).astype(float); sh[...,:3]=0
        shim = Image.fromarray(sh.astype(np.uint8)).filter(ImageFilter.GaussianBlur(W*0.008))
        sh_a = np.array(shim).astype(float); sh_a[...,3]*=0.5
        shim = Image.fromarray(sh_a.astype(np.uint8))
        out.alpha_composite(shim, (int(scx-target/2), int(H*cy_frac-target/2)+int(W*0.02)))
    out.alpha_composite(gl, (int(scx-target/2), int(H*cy_frac-target/2)))
    out.save(out_path)
    out.resize((32,32), Image.LANCZOS).save(out_path.replace('.png','_32.png'))
    return out_path
if __name__ == '__main__':
    compose(sys.argv[1], sys.argv[2], sys.argv[3])
