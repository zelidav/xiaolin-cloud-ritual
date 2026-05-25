#!/usr/bin/env python3
"""Generate a Chinese pop song ('Chalice Cloud Bar') and mux it onto the
already-rendered silent reel video (img/videos/_v2silent.mp4) -> reel.mp4.
Tries text-to-song models on Replicate (ACE-Step first)."""
import os, sys, subprocess
from pathlib import Path
import replicate, requests, imageio_ffmpeg

HERE = Path(__file__).resolve().parent
VID = HERE.parent / "img" / "videos"
FF = imageio_ffmpeg.get_ffmpeg_exe()
SILENT = VID / "_v2silent.mp4"
SONG = VID / "song"          # extension added on save
REEL = VID / "reel.mp4"

TAGS = ("psychedelic chinese pop rock and roll, electric guitar, fuzzy psychedelic, retro 70s, "
        "groovy, reverb, trippy, mandopop, driving drums, male and female vocals, catchy")
LYRICS = """[verse]
霓虹灯下 云吧门开
圣杯在手 心都打开
[chorus]
吸一口 飞上云端
小林的云 带我环绕
圣杯云吧 醉在云海
飘啊飘 不想下来"""

# (model, input-dict builder) — first success wins
def candidates():
    yield ("lucataco/ace-step", {"tags": TAGS, "lyrics": LYRICS, "duration": 20})
    yield ("ace-step/ace-step", {"tags": TAGS, "lyrics": LYRICS, "duration": 20})
    yield ("minimax/music-1.5", {"lyrics": LYRICS, "song_style": TAGS})
    yield ("minimax/music-01", {"lyrics": LYRICS})

def gen_song():
    last = None
    for model, inp in candidates():
        try:
            print("song: trying", model)
            o = replicate.run(model, input=inp)
            t = o[0] if isinstance(o, list) else o
            data = t.read() if hasattr(t, "read") else requests.get(str(t), timeout=600).content
            ext = ".wav" if data[:4] == b"RIFF" else ".mp3"
            p = SONG.with_suffix(ext); p.write_bytes(data)
            print("  got song via", model, "->", p.name, len(data)//1024, "KB")
            return p
        except Exception as e:
            print("  failed:", str(e)[:160]); last = e
    raise SystemExit(f"all song models failed: {last}")

def main():
    if not os.environ.get("REPLICATE_API_TOKEN"): sys.exit("Set REPLICATE_API_TOKEN")
    if not SILENT.exists(): sys.exit(f"missing {SILENT} — run make_reel.py first")
    song = gen_song()
    subprocess.run([FF,"-y","-i",str(SILENT),"-i",str(song),
        "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k",
        "-af","afade=t=in:st=0:d=0.4,afade=t=out:st=9.2:d=1.0","-shortest",str(REEL)],check=True)
    print("REEL with song:", REEL, REEL.stat().st_size//1024, "KB")

if __name__ == "__main__": main()
