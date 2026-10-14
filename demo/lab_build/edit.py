import json, subprocess
M=json.load(open("marks.json")); RAW="lab_raw.mp4"; BG="0x0e1117"; FB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
t=lambda k:M[k]["t"]
S1=(137,47,1006,630); S2=(137,265,1006,725)
LCD1=(296,340,290,128); NOTE=(560,70,590,470); LCD2=(137,400,1006,230); RES2=(137,866,700,122)
SH=[("card","h1.png",2.5,None,"Oct 2026: Ledgers resold with a hidden eSIM board."),
("card","h2.png",2.2,None,"Seed phrases sent out over the cell network."),
("card","h3.png",2.5,None,"Genuine Check checks the chip, not extra boards."),
("card","h4.png",2.5,None,"So weigh it. Here's how, step by step."),
("clip",(t("gen1_start")-0.3,t("gen1_lcd0")+1.0),S1,None,"STEP 1 · Genuine Ledger Flex. TARE to 0.000 g,\nplace it, type the reading."),
("still",t("gen1_lcd0")+1.0,2.2,LCD1,"The scale shows 57.007 g."),
("clip",(t("gen1_lcd0")+1.0,t("gen1_res")+0.4),S1,None,"Each reading goes on the note. Re-tare, weigh 3 times."),
("still",t("gen1_res")+0.3,3.2,NOTE,"Average 57.007 g vs reference 57.000 g:\nΔ +0.007 g, inside ±0.050 g → LIKELY GENUINE."),
("clip",(t("tam1_start"),t("tam1_lcd0")+1.0),S1,None,"Now a tampered unit. Same steps."),
("still",t("tam1_lcd0")+1.0,2.0,LCD1,"58.209 g: already heavy."),
("clip",(t("tam1_lcd0")+1.0,t("tam1_res")+0.4),S1,None,"Three readings, all heavy."),
("still",t("tam1_res")+0.3,3.4,NOTE,"Δ +1.209 g: 24× the tolerance.\nSomething was added inside → SUSPICIOUS."),
("clip",(t("gen2_start"),t("gen2_rot")-0.1),S2,None,"STEP 2 · Where is the extra mass? Ruler across two\nmg scales, TARE both, wallet in the middle."),
("still",t("gen2_rot")-0.2,2.2,LCD2,"Genuine: L 28.504 = R 28.504."),
("clip",(t("gen2_rot"),t("gen2_res")+0.3),S2,None,"Rotate 180° in place (green edge moves). Read again."),
("still",t("gen2_res")+0.3,3.0,RES2,"Still equal → offset +0.00 mm → CENTRED."),
("clip",(t("tam2_start"),t("tam2_rot")-0.1),S2,None,"Tampered unit on the same setup."),
("still",t("tam2_rot")-0.2,2.2,LCD2,"R 29.693 is heavier than L 28.517."),
("clip",(t("tam2_rot"),t("tam2_res")+0.3),S2,None,"Rotate 180°: now L 29.505 is heavier."),
("still",t("tam2_res")+0.3,3.4,RES2,"The heavy side followed the wallet: extra mass in that end.\nOffset +0.85 mm > 0.7 mm tolerance → OFF-CENTRE."),
("card","h5.png",3.0,None,"Until it's verified, keep it in a Faraday bag."),
("card","h6.png",3.0,None,"All numbers in this demo are examples."),]
parts=[];cues=[];T0=0
com=["-r","25","-pix_fmt","yuv420p","-c:v","libx264","-preset","fast","-crf","20","-an"]
def fit(box):
    x,y,w,h=box; sc=min(1240/w,800/h); W2=int(w*sc)//2*2; H2=int(h*sc)//2*2; px=(1280-W2)//2; py=max(20,(880-H2)//2)
    return f"crop={w}:{h}:{x}:{y},scale={W2}:{H2}:flags=lanczos,pad=1280:1000:{px}:{py}:color={BG}",(px,py,W2,H2)
for i,sh in enumerate(SH):
    k=sh[0]; v=f"p{i}.mp4"
    if k=="card": _,src,d,_,cap=sh; cmd=["ffmpeg","-y","-v","error","-loop","1","-t",str(d),"-i",src,*com,v]
    elif k=="clip": _,(a,b),box,_,cap=sh; d=round(b-a,2); vf,_=fit(box); cmd=["ffmpeg","-y","-v","error","-ss",str(a),"-i",RAW,"-t",str(d),"-vf",vf,*com,v]
    else:
        _,a,d,box,cap=sh; vf,(px,py,W2,H2)=fit(box)
        vf+=f",drawbox={px-4}:{py-4}:{W2+8}:{H2+8}:color=0x3fb950:t=5,trim=end_frame=1,tpad=stop_mode=clone:stop_duration={d+1}"
        cmd=["ffmpeg","-y","-v","error","-ss",str(a),"-i",RAW,"-t",str(d),"-vf",vf,*com,v]
    subprocess.run(cmd,check=True); parts.append(v)
    if cap: cues.append((T0+0.05,T0+d-0.05,cap))
    T0+=d
open("list.txt","w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-i","list.txt","-c","copy","ns.mp4"],check=True)
ts=lambda s: f"{int(s//3600):02}:{int(s%3600//60):02}:{int(s%60):02},{int(round(s%1*1000))%1000:03}"
open("final.srt","w").write("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{c}\n" for i,(a,b,c) in enumerate(cues)))
stl="FontName=DejaVu Sans,Bold=1,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2.5,Shadow=0,MarginV=14"
subprocess.run(["ffmpeg","-y","-v","error","-i","ns.mp4","-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-i","final.srt","-map","0:v","-map","1:a","-map","2","-vf",f"subtitles=final.srt:force_style='{stl}'","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","32k","-c:s","mov_text","-metadata:s:s:0","language=eng","-t",str(T0),"-movflags","+faststart","final.mp4"],check=True)
json.dump([(s[0],s[-1]) for s in SH],open("caps.json","w")); print("total",T0)
