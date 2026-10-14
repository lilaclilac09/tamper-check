import asyncio, subprocess, json, re, edge_tts, os
os.chdir("/tmp/ts"); RAW="/workspace/tamper-check/demo/two_scale_raw.mp4"
BG="0x0e1117"
S=[("card","card_setup.png",None,"Weight tells you that mass was added. Two scales tell you where. Step one: lay a rigid ruler across two milligram scales, a hundred millimeters apart. Step two: tare both, with the ruler on. Step three: lay the wallet in the middle. Step four: read left and right. Equal readings mean the mass is centred."),
("card","card_flip.png",None,"The offset is right minus left, over the total, times half the span. But you never place it perfectly. So rotate the wallet a hundred eighty degrees, in place, and read again. The wallet's offset flips sign. Your placement error doesn't. Half the difference keeps the real offset, and cancels the placement error."),
("full",0.5,None,"In the tool, open section three: Two scales. The numbers here are simulated examples."),
("zoom",9.2,(36,606,580,80,"L / R readings + flipped pair"),"Here's a genuine unit. Left and right, then the flipped pair, and the span: a hundred millimeters."),
("zoom",10.5,(36,677,580,50,"computed offset"),"The tool computes x one and x two. About one millimeter of placement error is cancelled. The real offset: minus zero point two eight millimeters."),
("zoom",13,(655,140,600,270,"verdict + center of mass"),"The example tolerance is zero point seven millimeters. Inside it, the center of mass is normal. Likely genuine."),
("zoom",20.5,(36,677,580,50,"computed offset"),"Now the implant unit. The offset is plus zero point eight five millimeters, toward the right end."),
("zoom",22.5,(655,140,600,270,"verdict + center of mass"),"That's past the tolerance, so the center of mass is flagged. Past twice the tolerance, it would be high. With one point two extra grams, and radio bursts: tampered."),
("zoom",33,(665,350,575,300,"3D view - green expected, yellow measured x5, red added mass"),"In the 3D view, green is the expected center of mass. Yellow is the measured one, exaggerated five times. Red marks the end where mass was likely added."),
("card","card_faraday.png",None,"Until a wallet is verified, keep it in a Faraday bag, so an implant can't reach the network. Test the bag: put a phone inside and call it. If it rings, the bag doesn't work.")]
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
async def tts(t,f): await edge_tts.Communicate(t,"en-US-AndrewNeural",rate="+5%").save(f)
cues=[]; t0=0; parts=[]
for i,(k,src,z,txt) in enumerate(S):
    a=f"a{i}.mp3"
    for _ in range(5):
        asyncio.run(tts(txt,a)); ad=dur(a)
        if ad>len(txt)/25: break
    else: raise SystemExit("tts failed")
    n=round(ad+0.9,2)
    v=f"v{i}.mp4"; common=["-r","25","-pix_fmt","yuv420p","-c:v","libx264","-preset","fast","-crf","20"]
    if k=="card": cmd=["ffmpeg","-y","-v","error","-loop","1","-t",str(n),"-i",src,"-vf","scale=1280:1000",*common,v]
    else:
        if k=="full": vf="tpad=stop_mode=clone:stop_duration=60"
        else:
            x,y,w,h,lab=z; sc=min(1200/w,640/h); W2=int(w*sc)//2*2; H2=int(h*sc)//2*2; px=(1280-W2)//2; py=(1000-H2)//2-40
            vf=(f"crop={w}:{h}:{x}:{y},scale={W2}:{H2}:flags=lanczos,pad=1280:1000:{px}:{py}:color={BG},drawbox={px-4}:{py-4}:{W2+8}:{H2+8}:color=0x3fb950:t=4,"
                f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='ZOOM  {lab}':fontcolor=0x3fb950:fontsize=26:x=(w-tw)/2:y={py-50},"
                f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='simulated EXAMPLE data':fontcolor=0x8b949e:fontsize=16:x=w-tw-20:y=h-36,tpad=stop_mode=clone:stop_duration=60")
        cmd=["ffmpeg","-y","-v","error","-ss",str(src),"-i",RAW,"-t",str(n),"-vf",vf,*common,v]
    subprocess.run(cmd,check=True)
    av=f"s{i}.mp4"; subprocess.run(["ffmpeg","-y","-v","error","-i",v,"-i",a,"-filter_complex","[1]adelay=300|300,apad,aresample=44100[aa]","-map","0:v","-map","[aa]","-c:v","copy","-c:a","aac","-ac","2","-t",str(n),av],check=True)
    parts.append(av)
    # subtitle chunks
    ch=[]; cur=""
    for w_ in txt.split():
        if len(cur)+len(w_)+1>40 and cur: ch.append(cur); cur=w_
        else: cur=(cur+" "+w_).strip()
        if cur[-1] in ".:?" and len(cur)>14: ch.append(cur); cur=""
    if cur: ch.append(cur)
    # pair chunks into 2-line cues
    cc=[]; j=0
    while j<len(ch):
        if j+1<len(ch) and not ch[j].endswith(".") : cc.append(ch[j]+"\n"+ch[j+1]); j+=2
        else: cc.append(ch[j]); j+=1
    tot=sum(len(c) for c in cc); p=t0+0.3
    for c in cc:
        d=ad*len(c)/tot; cues.append((p,p+d-0.05,c)); p+=d
    t0+=n
open("list.txt","w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-i","list.txt","-c","copy","seg_nosub.mp4"],check=True)
ts=lambda s: f"{int(s//3600):02}:{int(s%3600//60):02}:{int(s%60):02},{int(round(s%1*1000))%1000:03}"
open("seg.srt","w").write("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{c}\n" for i,(a,b,c) in enumerate(cues)))
st="FontName=DejaVu Sans,Bold=1,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=14"
subprocess.run(["ffmpeg","-y","-v","error","-i","seg_nosub.mp4","-vf",f"subtitles=seg.srt:force_style='{st}'","-c:v","libx264","-preset","fast","-crf","20","-pix_fmt","yuv420p","-c:a","copy","seg.mp4"],check=True)
print(t0, dur("seg.mp4"))
