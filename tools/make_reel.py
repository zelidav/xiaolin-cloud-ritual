#!/usr/bin/env python3
"""Made in Xiaolin x SYPP Cloud Bar reel (v3) — ~19s 9:16.
Opens on a MiX logo title card, then cuts to people: wide dispensary pull-back ->
group sipping -> close sip -> chalice lift -> walk-away with boxed Chalice -> end card.
Persistent 'Powered by SYPP Cloud Bar' bug, burned-in English subtitles, and the
psychedelic Chinese pop-rock song. kling-v1.6-pro I2V; ffmpeg via imageio_ffmpeg."""
import os, sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import replicate, requests, imageio_ffmpeg

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "img"; GEN = IMG/"gen"; VID = IMG/"videos"; REELDIR = IMG/"reel"
VID.mkdir(parents=True, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
SEAL = IMG/"Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"
BADGE = REELDIR/"badge.png"; ENDCARD = REELDIR/"endcard.jpg"; SONG = VID/"song.mp3"
# Default to the lower-cost standard model (~$0.20/clip vs ~$0.40 pro). Pass --pro for premium.
MODEL = "kwaivgi/kling-v1.6-pro" if "--pro" in sys.argv else "kwaivgi/kling-v1.6-standard"

# still, clip-file, motion, slice-seconds, subtitle
SHOTS = [
 ("reel-wide.jpg","v3-wide.mp4",
  "Slow cinematic camera pull-back / dolly out revealing the whole dispensary, people sip and "
  "mingle around the Cloud Bar, vapor rising. Gentle, photoreal, no cut.",3.6,
  "Under the neon, the Cloud Bar opens"),
 ("reel-group.jpg","v3-group.mp4",
  "Lively motion: a group of friends sip the cloud through straws, laugh and talk, vapor swirls "
  "up. Handheld energy, photoreal, no cut.",3.6,
  "Chalice in hand — every heart opens"),
 ("reel-sample.jpg","v3-sample.mp4",
  "The guests sip the cloud and smile, warm vapor rises, the ambassador gestures. Subtle "
  "handheld, photoreal, no cut.",3.2,
  "One draw, and we fly to the clouds"),
 ("reel-lift.jpg","v3-lift.mp4",
  "A hand lifts the glass dome up and away from the base in slow motion; dense white-gold vapor "
  "pours and billows down. Mesmerizing, photoreal, no cut.",3.4,
  "Xiaolin's cloud carries us around"),
 ("reel-walkaway.jpg","v3-walk.mp4",
  "The happy customer walks toward camera away from the register holding the small Chalice "
  "box, smiling; slow handheld follow, warm bokeh. Photoreal, no cut.",2.8,
  "Take the cloud home with you"),
 ("reel-home.jpg","v3-home.mp4",
  "At home on the couch the friends relax and sip the cloud; the customer in front looks right "
  "at the camera and WINKS with a smile at the end. Warm, gentle, photoreal, no cut.",3.6,
  "Chalice Cloud Bar — never coming down"),
]
OPENER_DUR=1.0; ENDCARD_DUR=1.6

def ff(a): subprocess.run([FF,"-y",*a],check=True)

def i2v(still,out,motion,force):
    import re,time
    dest=VID/out
    if dest.exists() and not force: print("skip",out); return dest
    url=replicate.files.create(file=open(GEN/still,"rb")).urls["get"]
    print("I2V(pro)",still,"->",out)
    o=None
    for a in range(1,7):
        try:
            o=replicate.run(MODEL,input={"start_image":url,"prompt":motion,"duration":5,
                                         "aspect_ratio":"9:16","cfg_scale":0.5}); break
        except Exception as e:
            if "429" not in str(e) and "throttl" not in str(e).lower(): raise
            m=re.search(r"in ~?(\d+)\s*s",str(e)); w=max(int(m.group(1))+3,12) if m else 15*a
            print(f"  throttled {a}/6; wait {w}s"); time.sleep(w)
    if o is None: raise SystemExit("i2v throttled out")
    t=o[0] if isinstance(o,list) else o
    data=t.read() if hasattr(t,"read") else requests.get(str(t),timeout=600).content
    dest.write_bytes(data); print("  saved",len(data)//1024,"KB"); return dest

def font(sz):
    for p in ["C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/Arial.ttf"]:
        try: return ImageFont.truetype(p,sz)
        except: pass
    return ImageFont.load_default()

def sub_png(txt,path):
    W,H=1080,150; im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); f=font(52)
    tw=d.textlength(txt,font=f); x=(W-tw)//2; y=40
    for dx in(-3,-2,2,3):
        for dy in(-3,-2,2,3): d.text((x+dx,y+dy),txt,font=f,fill=(0,0,0,235))
    d.text((x,y),txt,font=f,fill=(255,255,255,255)); im.save(path)

def opener_png(path):
    W,H=1080,1920; c=Image.new("RGB",(W,H),(124,13,21)); d=ImageDraw.Draw(c)
    d.rectangle([26,26,W-26,H-26],outline=(240,207,134),width=3)
    s=Image.open(SEAL).convert("RGBA"); sw=560; sh=int(s.height*sw/s.width); s=s.resize((sw,sh),Image.LANCZOS)
    c.paste(s,((W-sw)//2,560),s)
    f=font(64); t="MADE IN XIAOLIN"; d.text(((W-d.textlength(t,font=f))//2,560+sh+50),t,font=f,fill=(247,239,221))
    f2=font(40); t2="× SYPP CLOUD BAR"; d.text(((W-d.textlength(t2,font=f2))//2,560+sh+135),t2,font=f2,fill=(240,207,134))
    c.save(path)

def card_seg(img,dur,out,zoom=True):
    if zoom:
        fc=(f"[0:v]scale=1188:2112,zoompan=z='min(zoom+0.0009,1.10)':d={int(dur*30)}:s=1080x1920:fps=30,setsar=1[outv]")
        ff(["-loop","1","-i",str(img),"-filter_complex",fc,"-map","[outv]","-an","-t",str(dur),
            "-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(out)])
    else:
        ff(["-loop","1","-i",str(img),"-vf","scale=1080:1920,setsar=1,fps=30","-an","-t",str(dur),
            "-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(out)])

def process(inp,out,slc,subpng):
    fc=("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
        f"fps=30,trim=0:{slc},setpts=PTS-STARTPTS[v];"
        "[1:v]scale=470:-1[b];[v][b]overlay=W-w-46:H-h-58[vb];"
        "[vb][2:v]overlay=(W-w)/2:1470[outv]")
    ff(["-i",str(inp),"-i",str(BADGE),"-i",str(subpng),"-filter_complex",fc,"-map","[outv]",
        "-an","-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(out)])

def main():
    force="--force" in sys.argv
    if not os.environ.get("REPLICATE_API_TOKEN"): sys.exit("Set REPLICATE_API_TOKEN")
    segs=[]
    # logo opener
    op_png=REELDIR/"opener.jpg"; opener_png(op_png)
    op=VID/"_v3opener.mp4"; card_seg(op_png,OPENER_DUR,op,zoom=True); segs.append(op)
    # people shots
    for i,(still,out,motion,slc,sub) in enumerate(SHOTS):
        raw=i2v(still,out,motion,force)
        sp=VID/f"_v3sub{i}.png"; sub_png(sub,sp)
        p=VID/f"_v3seg{i}.mp4"; process(raw,p,slc,sp); segs.append(p)
    # end card
    ec=VID/"_v3end.mp4"; card_seg(ENDCARD,ENDCARD_DUR,ec,zoom=True); segs.append(ec)
    lst=VID/"_v3list.txt"; lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs))
    silent=VID/"_v3silent.mp4"; ff(["-f","concat","-safe","0","-i",str(lst),"-c","copy",str(silent)])
    # duration -> for audio fade
    import json
    dur=sum([OPENER_DUR]+[s[3] for s in SHOTS]+[ENDCARD_DUR])
    reel=VID/"reel.mp4"
    if SONG.exists():
        ff(["-i",str(silent),"-i",str(SONG),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac",
            "-b:a","192k","-af",f"afade=t=in:st=0:d=0.3,afade=t=out:st={dur-1.0:.1f}:d=1.0","-shortest",str(reel)])
    else:
        ff(["-i",str(silent),"-c","copy",str(reel)])
    print("REEL v3:",reel,reel.stat().st_size//1024,"KB | dur ~",round(dur,1),"s")

if __name__=="__main__": main()
