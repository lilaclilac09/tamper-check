from PIL import Image, ImageDraw, ImageFilter
import numpy as np
def mask(fn, ells):
    W,H=1280,1000
    a=Image.new("L",(W,H),105); d=ImageDraw.Draw(a)
    for (cx,cy,rx,ry) in ells: d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=0)
    dim=np.asarray(a.filter(ImageFilter.GaussianBlur(28))).astype(float)/255
    g=Image.new("L",(W,H),0); gd=ImageDraw.Draw(g)
    for (cx,cy,rx,ry) in ells: gd.ellipse([cx-rx-6,cy-ry-6,cx+rx+6,cy+ry+6],outline=255,width=6)
    glow=np.asarray(g.filter(ImageFilter.GaussianBlur(6))).astype(float)/255*0.85
    A=glow+dim*(1-glow)
    col=np.array([255,226,120],float)
    rgb=(glow[...,None]*col)/np.maximum(A[...,None],1e-6)
    out=np.dstack([np.clip(rgb,0,255),A*255]).astype("uint8")
    Image.fromarray(out,"RGBA").save(fn)
mask("m_lcd1.png",[(440,402,170,80)])
mask("m_note.png",[(855,300,310,250)])
mask("m_lcd2.png",[(328,567,150,62),(952,567,150,62)])
mask("m_res2.png",[(480,920,370,75)])
