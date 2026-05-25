#!/usr/bin/env python3
"""Build a ~10s 9:16 Instagram reel for Made in Xiaolin x SYPP Cloud Bar.
Animates two stills via Replicate I2V (kling-v1.6-standard, 9:16, 5s each),
then stitches with ffmpeg: fill-to-1080x1920, a MiX seal cut-in at each shot
start, and a persistent 'Powered by SYPP Cloud Bar' corner badge.
Requires REPLICATE_API_TOKEN. ffmpeg comes from imageio_ffmpeg."""
import os, sys, subprocess
from pathlib import Path
import replicate, requests, imageio_ffmpeg

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "img"
VID = IMG / "videos"; VID.mkdir(parents=True, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
SEAL = IMG / "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"
BADGE = IMG / "reel" / "badge.png"

CLIPS = [
    ("reel-sample.jpg", "reel-sample.mp4", 0.9,
     "Subtle living motion: warm vapor gently rises and swirls from the chalice glasses, the "
     "guests sip through straws and smile, the brand ambassador gestures warmly. Gentle handheld "
     "feel, no scene cut, photoreal."),
    ("reel-walkaway.jpg", "reel-walkaway.mp4", 0.7,
     "The happy customer walks toward the camera, away from the register, holding the boxed "
     "Chalice, smiling; slow handheld follow, warm dispensary bokeh behind. Photoreal, no cut."),
]

def i2v(still, out, motion, force):
    dest = VID / out
    if dest.exists() and not force:
        print("skip (exists)", out); return dest
    url = replicate.files.create(file=open(IMG/"gen"/still, "rb")).urls["get"]
    print("I2V", still, "->", out)
    o = replicate.run("kwaivgi/kling-v1.6-standard", input={
        "start_image": url, "prompt": motion,
        "duration": 5, "aspect_ratio": "9:16", "cfg_scale": 0.5})
    t = o[0] if isinstance(o, list) else o
    data = t.read() if hasattr(t, "read") else requests.get(str(t), timeout=600).content
    dest.write_bytes(data); print("  saved", len(data)//1024, "KB"); return dest

def process(inp, out, seal_dur):
    # fill 1080x1920, 30fps, MiX seal cut-in at start, SYPP badge bottom-right
    fc = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,fps=30,trim=0:5,setpts=PTS-STARTPTS[v];"
        "[1:v]scale=720:-1[s];"
        f"[v][s]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{seal_dur})'[v1];"
        "[2:v]scale=470:-1[b];"
        "[v1][b]overlay=W-w-46:H-h-58[outv]"
    )
    subprocess.run([FF,"-y","-i",str(inp),"-i",str(SEAL),"-i",str(BADGE),
        "-filter_complex",fc,"-map","[outv]","-an",
        "-c:v","libx264","-pix_fmt","yuv420p","-r","30","-t","5",str(out)],check=True)

def main():
    force = "--force" in sys.argv
    if not os.environ.get("REPLICATE_API_TOKEN"): sys.exit("Set REPLICATE_API_TOKEN")
    raws=[]
    for still,out,sd,motion in CLIPS:
        raws.append((i2v(still,out,motion,force), sd))
    proc=[]
    for i,(raw,sd) in enumerate(raws):
        p=VID/f"_proc{i}.mp4"; process(raw,p,sd); proc.append(p)
    lst=VID/"_list.txt"; lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in proc))
    reel=VID/"reel.mp4"
    subprocess.run([FF,"-y","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(reel)],check=True)
    print("REEL:", reel, reel.stat().st_size//1024, "KB")

if __name__=="__main__": main()
