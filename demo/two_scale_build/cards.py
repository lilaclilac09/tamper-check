from PIL import Image, ImageDraw, ImageFont
W,H=1280,1000; BG=(14,17,23)
F=lambda s,b=True: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if b else ''}.ttf",s)
M=lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",s)
G=(63,185,80); Y=(210,153,34); R=(248,81,73); T=(230,230,230); D=(139,148,158)
def base(title,sub=None):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.text((W/2,60),"tamper-check",fill=G,font=F(26),anchor="mm"); d.text((W/2,115),title,fill=T,font=F(46),anchor="mm")
    if sub: d.text((W/2,165),sub,fill=D,font=F(22,False),anchor="mm")
    d.text((W-20,H-20),"numbers are simulated EXAMPLES",fill=D,font=F(16,False),anchor="rd"); return im,d
def rig(d,y,L,Rv,wx,mark=None,lab="wallet"):
    d.rectangle([140,y+60,360,y+150],fill=(48,54,61)); d.rectangle([920,y+60,1140,y+150],fill=(48,54,61))
    d.text((250,y+105),L,fill=T,font=M(34),anchor="mm"); d.text((1030,y+105),Rv,fill=T,font=M(34),anchor="mm")
    d.polygon([(250,y+60),(236,y+40),(264,y+40)],fill=D); d.polygon([(1030,y+60),(1016,y+40),(1044,y+40)],fill=D)
    d.rectangle([200,y+28,1080,y+40],fill=(196,160,100))
    d.rounded_rectangle([wx-180,y-32,wx+180,y+28],8,fill=(43,47,54),outline=G,width=3); d.text((wx,y-2),lab,fill=T,font=F(24),anchor="mm")
    if mark: d.rectangle([wx+mark-30,y-26,wx+mark+20,y+22],fill=R)
    d.text((250,y+175),"scale L",fill=D,font=F(20,False),anchor="mm"); d.text((1030,y+175),"scale R",fill=D,font=F(20,False),anchor="mm")
# card 1: setup
im,d=base("Two-scale balance: step by step","find WHERE added mass sits, with two milligram scales")
rig(d,330,"28.50 g","28.50 g",640)
d.line([(200,250),(1080,250)],fill=D,width=2); d.text((640,232),"span = 100 mm between supports",fill=D,font=F(20,False),anchor="mm")
steps=["1  Rigid ruler across two 0.001 g scales","2  Tare both scales with the ruler on","3  Lay the wallet centred on the ruler","4  Read L and R    (L = R  ->  centred)"]
for i,s in enumerate(steps): d.text((220,620+i*58),s,fill=T,font=F(32),anchor="lm")
im.save("card_setup.png")
# card 2: math + flip
im,d=base("Flip 180° to cancel placement error")
d.text((640,215),"x = (R − L) / (R + L) × span / 2",fill=Y,font=M(40),anchor="mm")
rig(d,330,"28.517","29.693",650,mark=140,lab="1st read")
d.text((640,555),"x1 = +1.01 mm   (true offset + placement error)",fill=T,font=M(26),anchor="mm")
d.text((640,620),"rotate the wallet 180° in place, read again:",fill=D,font=F(26,False),anchor="mm")
d.text((640,670),"x2 = −0.69 mm   (−true offset + same placement error)",fill=T,font=M(26),anchor="mm")
d.text((640,720),"offset = (x1 − x2) / 2 = +0.85 mm",fill=G,font=M(42),anchor="mm")
d.text((640,772),"placement (x1 + x2) / 2 = +0.16 mm  ->  cancelled",fill=D,font=M(24),anchor="mm")
d.text((640,828),"tolerance (example ref): 0.7 mm  ·  > 1.4 mm = high",fill=Y,font=F(26),anchor="mm")
im.save("card_flip.png")
# card 3: faraday
im,d=base("Until it's verified: Faraday bag")
d.rounded_rectangle([420,250,860,620],30,fill=(40,44,50),outline=D,width=4)
for i in range(6): d.line([(440,300+i*55),(840,300+i*55)],fill=(60,66,74),width=2)
d.rounded_rectangle([560,360,720,440],10,fill=(43,47,54),outline=G,width=3); d.text((640,400),"wallet",fill=T,font=F(24),anchor="mm")
d.rounded_rectangle([600,470,680,590],12,fill=(30,30,30),outline=T,width=2); 
d.text((640,530),"phone",fill=T,font=F(18),anchor="mm")
for i,(s,c) in enumerate([("Keep an unverified wallet in a Faraday bag:",T),("an implant can't reach the network.",T),("Test the bag: put a phone inside and call it.",Y),("If it rings, the bag doesn't work.",R)]):
    d.text((640,650+i*50),s,fill=c,font=F(32),anchor="mm")
im.save("card_faraday.png")
