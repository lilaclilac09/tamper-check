import json, subprocess, re
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
M=json.load(open("marks.json")); RAW="lab_raw.mp4"; t=lambda k:M[k]["t"]; bx=lambda k:M[k]["box"][0]
def mask(fn,boxes,pad=18):
    W,H=1280,1000; a=Image.new("L",(W,H),105); d=ImageDraw.Draw(a)
    for x,y,w,h in boxes: d.rounded_rectangle([x-pad,y-pad,x+w+pad,y+h+pad],radius=24,fill=0)
    dim=np.asarray(a.filter(ImageFilter.GaussianBlur(24))).astype(float)/255
    g=Image.new("L",(W,H),0); gd=ImageDraw.Draw(g)
    for x,y,w,h in boxes: gd.rounded_rectangle([x-pad-6,y-pad-6,x+w+pad+6,y+h+pad+6],radius=28,outline=255,width=6)
    glow=np.asarray(g.filter(ImageFilter.GaussianBlur(6))).astype(float)/255*0.85
    A=glow+dim*(1-glow); col=np.array([255,226,120],float)
    rgb=(glow[...,None]*col)/np.maximum(A[...,None],1e-6)
    Image.fromarray(np.dstack([np.clip(rgb,0,255),A*255]).astype("uint8"),"RGBA").save(fn); return fn
SH=[("card","h1.png",2.5,"Oct 2026: Ledgers resold with a hidden eSIM board."),
("card","h2.png",2.2,"Seed phrases sent out over the cell network."),
("card","h3.png",2.5,"Genuine Check checks the chip, not extra boards."),
("card","h4.png",2.5,"So weigh it. Here's how, step by step."),
("clip",(t("gen1_start")-0.6,t("gen1_res")),"STEP 1 · Genuine Ledger Flex. Tare to 0.000 g,\nweigh 3 times, type each reading."),
("still","gen1_res",3.4,"Δ +0.007 g, inside ±0.050 g → LOOKS GENUINE.\nConfidence MEDIUM (HIGH once step 2 is centred)."),
("clip",(t("light1_start"),t("light1_res")),"A unit that's a little heavy."),
("still","light1_res",3.4,"Δ +0.082 g: over ±0.050 g, under 2× → SUSPICIOUS.\nConfidence LOW: could be a sticker or dust. Check step 2."),
("clip",(t("glue1_start"),t("glue1_res")),"Now the glued-in implant (+0.35 g)."),
("still","glue1_res",3.6,"Δ +0.351 g ≥ 0.3 g (board-sized) →\nTAMPERED: DO NOT USE · Confidence HIGH."),
("still","cards",4.0,"STEP 2 · Where is the extra mass? Two scales, a ruler,\nread L and R, rotate 180°, read again."),
("clip",(t("gen2_start"),t("gen2_res")),"Genuine: L = R before and after rotating."),
("still","gen2_res",3.0,"{\\an8}Offset +0.00 mm → CENTRED."),
("clip",(t("tam2_start"),t("tam2_res")),"Tampered: R heavier, then L heavier after 180°."),
("still","tam2_res",3.6,"{\\an8}The heavy side followed the wallet: mass inside that end.\n+0.85 mm > 0.7 mm → OFF-CENTRE · weight + CoM agree → HIGH."),
("still","crit",4.0,"{\\an8}How we judge: every threshold on one table.\nCalibrate with a known-genuine unit from the same batch."),
("card","h5.png",3.0,"Until it's verified, keep it in a Faraday bag."),
("card","h6.png",3.0,"All numbers in this demo are examples."),]
parts=[];cues=[];T0=0
com=["-r","25","-pix_fmt","yuv420p","-c:v","libx264","-preset","fast","-crf","20","-an"]
for i,sh in enumerate(SH):
    v=f"p{i}.mp4"
    if sh[0]=="clip": k,src,cap=sh; d=None
    else: k,src,d,cap=sh
    if k=="card": cmd=["ffmpeg","-y","-v","error","-loop","1","-t",str(d),"-i",src,*com,v]
    elif k=="clip": a,b=src; d=round(b-a,2); cmd=["ffmpeg","-y","-v","error","-ss",str(a),"-i",RAW,"-t",str(d),*com,v]
    else:
        m=mask(f"m_{src}.png",[bx(src)]); a=t(src)+0.2
        fc=(f"[0:v]trim=end_frame=1,tpad=stop_mode=clone:stop_duration={d+1}[b];"
            f"[1:v]format=rgba,fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st={d-0.5}:d=0.5:alpha=1[m];[b][m]overlay=0:0:shortest=0[o]")
        cmd=["ffmpeg","-y","-v","error","-ss",str(a),"-i",RAW,"-loop","1","-t",str(d),"-i",m,"-filter_complex",fc,"-map","[o]","-t",str(d),*com,v]
    subprocess.run(cmd,check=True); parts.append(v); cues.append((T0+0.05,T0+d-0.05,cap)); T0+=d
open("list.txt","w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-i","list.txt","-c","copy","ns.mp4"],check=True)
ts=lambda s: f"{int(s//3600):02}:{int(s%3600//60):02}:{int(s%60):02},{int(round(s%1*1000))%1000:03}"
open("final.srt","w").write("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{c}\n" for i,(a,b,c) in enumerate(cues)))
subprocess.run(["ffmpeg","-y","-v","error","-i","final.srt","final.ass"],check=True)
a=open("final.ass").read().replace("PlayResX: 384","PlayResX: 1280").replace("PlayResY: 288","PlayResY: 1000")
a=re.sub(r"Style: Default,.*",r"Style: Default,DejaVu Sans,38,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,4,0,2,40,40,36,1",a)
open("final.ass","w").write(a)
subprocess.run(["ffmpeg","-y","-v","error","-i","ns.mp4","-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-i","final.srt","-map","0:v","-map","1:a","-map","2","-vf","subtitles=final.ass","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","32k","-c:s","mov_text","-metadata:s:s:0","language=eng","-t",str(T0),"-movflags","+faststart","final.mp4"],check=True)
json.dump(SH,open("caps.json","w"),ensure_ascii=False); print("total",T0)
