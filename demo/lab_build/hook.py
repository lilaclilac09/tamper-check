from PIL import Image, ImageDraw, ImageFont
W,H=1280,1000; BG=(14,17,23)
F=lambda s,b=True: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if b else ''}.ttf",s)
def card(big,sub,fn,col=(230,230,230)):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.text((W/2,300),"tamper-check",fill=(63,185,80),font=F(30),anchor="mm")
    d.text((W/2,450),big,fill=col,font=F(110),anchor="mm"); d.text((W/2,570),sub,fill=(139,148,158),font=F(34,False),anchor="mm"); im.save(fn)
card("$86–93M","stolen with bugged, resold Ledgers (Oct 2026)","h1.png",(248,81,73))
card("300+","wallets drained","h2.png",(248,81,73))
card("PASSES","Ledger Genuine Check, even with the implant","h3.png",(210,153,34))
card("+0.3 g","an extra board has weight. A mg scale sees it.","h4.png",(63,185,80))
card("Faraday bag","until verified. Test it: call a phone inside.","h5.png",(210,153,34))
card("Weigh before you trust.","aileena.xyz/tools/tamper-check · numbers are examples","h6.png")
