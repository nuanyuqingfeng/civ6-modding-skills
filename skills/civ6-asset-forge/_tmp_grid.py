
import os, sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np

OUT = r"D:\documents\Firaxis ModBuddy\Civilization VI\Snezhnaya_Vodyanitsa\Snezhnaya_Vodyanitsa\workspace\tmp"
SRC = r"D:\desktop\沃雅妮莎_Civ6Mod前期准备"
files = {
 "qu": ("特色区域历史时刻.png", 1024, 512),
 "dan": ("特色单位历史时刻.png", 1024, 512),
 "gai": ("特色改良设施历史时刻.png", 840, 400),
}
def font(sz):
    for p in [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\arial.ttf"]:
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

for k,(fn,W,H) in files.items():
    im = Image.open(os.path.join(SRC, fn)).convert("RGB")
    assert im.size == (W,H), (k, im.size)
    # --- grid overlay (labels along edges only, light lines) ---
    sc = 1.0 if W <= 1024 else 0.75
    g = im.copy()
    d = ImageDraw.Draw(g)
    f = font(11)
    for x in range(0, W+1, 32):
        major = (x % 128 == 0)
        d.line([(x,0),(x,H)], fill=(255,80,80) if major else (255,190,190), width=1)
        if major:
            d.rectangle([x,0,x+34,12], fill=(0,0,0))
            d.text((x+1,1), str(x), font=f, fill=(255,255,0))
    for y in range(0, H+1, 32):
        major = (y % 128 == 0)
        d.line([(0,y),(W,y)], fill=(80,255,80) if major else (190,255,190), width=1)
        if major:
            d.rectangle([0,y,W if False else 34,y+12], fill=(0,0,0))
            d.text((1,y+1), str(y), font=f, fill=(0,255,255))
    p = os.path.join(OUT, f"grid_{k}.png")
    g.save(p)
    print("grid", k, p, g.size)
