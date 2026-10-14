import json, subprocess, os
os.chdir("/tmp/ts"); RAW="/workspace/tamper-check/demo/walk_raw.mp4"; M=json.load(open("/workspace/tamper-check/demo/walk_marks.json"))
BG="0x0e1117"; FB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def t(k): return M[k]["t"]
def bx(k,maxh=340):
    b=M[k]["box"]; x0=max(0,b["x0"]-14); y0=max(0,b["y0"]-14); x1=min(1280,b["x1"]+14); y1=min(1000,b["y1"]+14,y0+maxh)
    return int(x0),int(y0),int(x1-x0)//2*2,int(y1-y0)//2*2
# (kind, src/start, dur, box, label, caption)
S=[("card","hook1.png",3.5,None,None,"Oct 2026: resold Ledgers carried a hidden eSIM board\nthat leaked seed phrases."),
("card","hook2.png",3.5,None,None,"Genuine Check can't see it. A milligram scale can."),
("full",t("overview")-1,3,None,None,"tamper-check: enter scale readings, get a verdict.\nAll numbers are simulated examples."),
("type","genuine",None,"#w","1 · GENUINE  readings","Weigh 3 times on a 0.001 g scale (re-zero between).\nType the readings."),
("zoom",t("genuine_res"),3.5,"genuine_res","1 · GENUINE  result","Average +0.007 g vs the example reference 57.000 g.\nInside ±0.050 g → LIKELY GENUINE, risk 0."),
("zoom",t("implant_res"),4,"implant_res","2 · LTE IMPLANT  result","+1.2 g, plus cellular bursts every ~30 s while OFF\nin a Faraday bag → TAMPERED, risk 100."),
("zoom",t("implant_3d"),3,"implant_3d","2 · LTE IMPLANT  3D","Red = suspected added mass. Rings = radio bursts."),
("type","glue",None,"#w","3 · GLUE / RESEALED  readings","A reopened, re-glued case: type the readings."),
("zoom",t("glue_res"),3.5,"glue_res","3 · GLUE  result","+0.359 g: over 2× the tolerance.\nToo light for a board, but it was opened → SUSPICIOUS."),
("zoom",t("glue_3d"),3,"glue_3d","3 · GLUE  3D","Green = expected center of mass, yellow = measured."),
("type","kitchen",None,"#w","4 · KITCHEN SCALE (1 g)  readings","Same tampered unit on a 1 g kitchen scale: 57, 57, 57."),
("zoom",t("kitchen_res"),3.5,"kitchen_res","4 · KITCHEN SCALE  result","0.3 g rounds away → missed.\nThe tool warns: 1 g scales are demo-only."),
("type","mg",None,"#w","5 · MILLIGRAM SCALE (0.001 g)  readings","Same unit on a 0.001 g scale."),
("zoom",t("mg_res"),3,"mg_res","5 · MILLIGRAM SCALE  result","+0.312 g caught → SUSPICIOUS, risk 50."),
("zoomfwd",t("mg_check"),4,"mg_check","5 · CHECKLIST","Flagged: don't enter a seed. Move funds to a new\nwallet bought direct from Ledger, with a new seed."),
("card","card_setup.png",4.5,None,None,"Center of mass at home: ruler on two tared mg scales,\nwallet centred, read left (L) and right (R)."),
("card","card_flip.png",5,None,None,"Rotate 180° and read again. Half the difference\ncancels your placement error."),
("typ2","ts_gen_lr","ts_gen_flip","ts_gen_lr","6 · TWO SCALES, GENUINE  L / R","Type L and R."),
("typ2","ts_gen_flip","ts_gen_off","ts_gen_lr","6 · TWO SCALES, GENUINE  rotated 180°","Rotate 180°, type the second L and R."),
("zoom",t("ts_gen_off"),3,"ts_gen_off","6 · computed offset","Offset −0.28 mm. About 1 mm of placement error cancelled."),
("zoom",t("ts_gen_res"),3,"ts_gen_res","6 · result","Under the 0.7 mm example tolerance → normal. LIKELY GENUINE."),
("typ2","ts_imp_lr","ts_imp_off","ts_imp_lr","7 · TWO SCALES, IMPLANT  L / R + rotated","Implant unit: both pairs of readings."),
("zoom",t("ts_imp_off"),3,"ts_imp_off","7 · computed offset","Offset +0.85 mm toward the right end."),
("zoom",t("ts_imp_res"),3.5,"ts_imp_res","7 · result","Past 0.7 mm → CoM flagged. With +1.2 g → TAMPERED."),
("zoom",t("ts_3d"),3,"ts_3d","7 · 3D","Yellow dot shifted (×5) toward the red end."),
("card","card_faraday.png",4.5,None,None,"Until verified, keep it in a Faraday bag.\nTest the bag: call a phone inside it."),
("card","end.png",3,None,None,""),]
parts=[]; cues=[]; T0=0
for i,(k,a,d,b,lab,cap) in enumerate(S):
    v=f"w{i}.mp4"; com=["-r","25","-pix_fmt","yuv420p","-c:v","libx264","-preset","fast","-crf","20","-an"]
    if k=="type": st=t(a+"_type"); d=round(t(a+"_typed")+0.5-st,2); box=bx(a+"_type")
    elif k=="typ2": st=t(a); d=round(t(d)+0.4-st,2); box=bx(b)
    elif k in("zoom","zoomfwd"): st=a; box=bx(b)
    if k=="card": cmd=["ffmpeg","-y","-v","error","-loop","1","-t",str(d),"-i",a,"-vf","scale=1280:1000",*com,v]
    elif k=="full": cmd=["ffmpeg","-y","-v","error","-ss",str(a),"-i",RAW,"-t",str(d),"-vf","tpad=stop_mode=clone:stop_duration=30",*com,v]
    else:
        x,y,w,h=box; sc=min(1200/w,620/h,3.0); W2=int(w*sc)//2*2; H2=int(h*sc)//2*2; px=(1280-W2)//2; py=max(90,(860-H2)//2)
        vf=(f"crop={w}:{h}:{x}:{y},scale={W2}:{H2}:flags=lanczos,pad=1280:1000:{px}:{py}:color={BG},drawbox={px-4}:{py-4}:{W2+8}:{H2+8}:color=0x3fb950:t=4,"
            f"drawtext=fontfile={FB}:text='{lab}':fontcolor=0x3fb950:fontsize=26:x=(w-tw)/2:y={py-48},tpad=stop_mode=clone:stop_duration=30")
        if k=="zoom" and not b.endswith("3d"): st=st+0.3; vf=vf.replace(",tpad=stop_mode=clone:stop_duration=30",f",trim=end_frame=1,tpad=stop_mode=clone:stop_duration={d+1}")
        cmd=["ffmpeg","-y","-v","error","-ss",str(st),"-i",RAW,"-t",str(d),"-vf",vf,*com,v]
    subprocess.run(cmd,check=True); parts.append(v)
    if cap: cues.append((T0+0.1,T0+d-0.1,cap))
    T0+=d
open("list2.txt","w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-i","list2.txt","-c","copy","silent_nosub.mp4"],check=True)
ts=lambda s: f"{int(s//3600):02}:{int(s%3600//60):02}:{int(s%60):02},{int(round(s%1*1000))%1000:03}"
open("silent.srt","w").write("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{c}\n" for i,(a,b,c) in enumerate(cues)))
stl="FontName=DejaVu Sans,Bold=1,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=16"
subprocess.run(["ffmpeg","-y","-v","error","-i","silent_nosub.mp4","-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-i","silent.srt","-map","0:v","-map","1:a","-map","2",
  "-vf",f"subtitles=silent.srt:force_style='{stl}'","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","32k","-c:s","mov_text","-metadata:s:s:0","language=eng","-t","93.92","-movflags","+faststart","silent.mp4"],check=True)
print("total",T0)
