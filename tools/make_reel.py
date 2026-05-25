#!/usr/bin/env python3
"""Build the ~10s 9:16 Made in Xiaolin x SYPP Cloud Bar reel (v2).
4 shots animated via Replicate kling-v1.6-PRO (sip -> pour -> cloud -> walk-away),
trimmed and stitched with a MiX seal cut-in, a persistent 'Powered by SYPP Cloud
Bar' corner bug, an end card, and a generated music bed. ffmpeg via imageio_ffmpeg."""
import os, sys, subprocess
from pathlib import Path
import replicate, requests, imageio_ffmpeg

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "img"
GEN = IMG / "gen"
VID = IMG / "videos"; VID.mkdir(parents=True, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
SEAL = IMG / "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"
BADGE = IMG / "reel" / "badge.png"
ENDCARD = IMG / "reel" / "endcard.jpg"
MODEL = "kwaivgi/kling-v1.6-pro"

# (still, clip-name, motion prompt, slice seconds)
CLIPS = [
    ("reel-sample.jpg", "v2-sample.mp4",
     "Gentle living motion: the guests sip the cloud through straws and smile, warm vapor "
     "rises from the chalices, the ambassador gestures warmly. Subtle handheld, no cut.", 2.4),
    ("reel-pour.jpg", "v2-pour.mp4",
     "The ambassador lifts the vapor-filled glass dome off its base; dense white-gold cloud "
     "billows and swirls upward in slow motion. Premium, photoreal, no cut.", 2.2),
    ("reel-cloud.jpg", "v2-cloud.mp4",
     "Macro: dense white vapor swirls and curls slowly inside the glass dome, the gold rim "
     "glints, a slow gentle push-in. Mesmerizing, photoreal, no cut.", 2.1),
    ("reel-walkaway.jpg", "v2-walk.mp4",
     "The happy customer walks toward camera, away from the register, holding the boxed "
     "Chalice, smiling; slow handheld follow, warm bokeh. Photoreal, no cut.", 2.3),
]
ENDCARD_DUR = 1.4
MUSIC_PROMPT = ("warm confident cinematic lo-fi hip-hop instrumental, mellow Rhodes keys, soft "
                "boom-bap drums, subtle oriental plucked strings, premium lounge vibe, no vocals")


def i2v(still, out, motion, force):
    dest = VID / out
    if dest.exists() and not force:
        print("skip", out); return dest
    url = replicate.files.create(file=open(GEN/still, "rb")).urls["get"]
    print("I2V(pro)", still, "->", out)
    o = replicate.run(MODEL, input={"start_image": url, "prompt": motion,
                                    "duration": 5, "aspect_ratio": "9:16", "cfg_scale": 0.5})
    t = o[0] if isinstance(o, list) else o
    data = t.read() if hasattr(t, "read") else requests.get(str(t), timeout=600).content
    dest.write_bytes(data); print("  saved", len(data)//1024, "KB"); return dest


def ff(args): subprocess.run([FF, "-y", *args], check=True)


def process(inp, out, slc, seal_cut):
    seal_ov = (f"[1:v]scale=720:-1[s];[v][s]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,0.7)'[v1];"
               if seal_cut else "[v]copy[v1];")
    fc = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
          f"fps=30,trim=0:{slc},setpts=PTS-STARTPTS[v];" + seal_ov +
          "[2:v]scale=470:-1[b];[v1][b]overlay=W-w-46:H-h-58[outv]")
    ff(["-i",str(inp),"-i",str(SEAL),"-i",str(BADGE),"-filter_complex",fc,
        "-map","[outv]","-an","-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(out)])


def endcard(out):
    # slow zoom on the end card
    fc=(f"[0:v]scale=1188:2112,zoompan=z='min(zoom+0.0008,1.08)':d={int(ENDCARD_DUR*30)}:"
        "s=1080x1920:fps=30,setsar=1[outv]")
    ff(["-loop","1","-i",str(ENDCARD),"-filter_complex",fc,"-map","[outv]","-an",
        "-t",str(ENDCARD_DUR),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",str(out)])


def main():
    force = "--force" in sys.argv
    if not os.environ.get("REPLICATE_API_TOKEN"): sys.exit("Set REPLICATE_API_TOKEN")
    segs=[]
    for i,(still,out,motion,slc) in enumerate(CLIPS):
        raw=i2v(still,out,motion,force)
        p=VID/f"_v2seg{i}.mp4"; process(raw,p,slc,seal_cut=(i==0)); segs.append(p)
    ec=VID/"_v2end.mp4"; endcard(ec); segs.append(ec)
    lst=VID/"_v2list.txt"; lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs))
    silent=VID/"_v2silent.mp4"
    ff(["-f","concat","-safe","0","-i",str(lst),"-c","copy",str(silent)])
    # music
    music=VID/"_music.mp3"
    try:
        print("music: musicgen…")
        o=replicate.run("meta/musicgen",input={"prompt":MUSIC_PROMPT,"duration":11,
                        "model_version":"stereo-large","output_format":"mp3","normalization_strategy":"loudness"})
        t=o[0] if isinstance(o,list) else o
        music.write_bytes(t.read() if hasattr(t,"read") else requests.get(str(t),timeout=600).content)
        print("  music", music.stat().st_size//1024,"KB")
        reel=VID/"reel.mp4"
        ff(["-i",str(silent),"-i",str(music),"-map","0:v","-map","1:a",
            "-c:v","copy","-c:a","aac","-b:a","160k","-shortest",
            "-af","afade=t=out:st=9:d=1",str(reel)])
    except Exception as e:
        print("music failed, using silent:",e)
        reel=VID/"reel.mp4"; ff(["-i",str(silent),"-c","copy",str(reel)])
    print("REEL v2:", reel, reel.stat().st_size//1024,"KB")

if __name__=="__main__": main()
