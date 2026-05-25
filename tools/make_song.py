#!/usr/bin/env python3
"""Generate the psychedelic Chinese pop-rock song '圣杯云吧 / Chalice Cloud Bar'
via Replicate minimax/music-2.6 (prompt = style, lyrics = Chinese hook) and mux
it onto the rendered silent reel (img/videos/_v2silent.mp4) -> reel.mp4."""
import os, sys, re, time, subprocess
from pathlib import Path
import replicate, requests, imageio_ffmpeg

HERE = Path(__file__).resolve().parent
VID = HERE.parent / "img" / "videos"
FF = imageio_ffmpeg.get_ffmpeg_exe()
SILENT = VID / "_v2silent.mp4"
REEL = VID / "reel.mp4"
SONG = VID / "song.mp3"

MODEL = "minimax/music-2.6"
STYLE = ("psychedelic rock that OPENS with a heavy Jimi-Hendrix-style fuzzy distorted electric "
         "guitar riff and a powerful pounding drum fill to bring it in, wah-wah, bluesy psychedelic "
         "lead guitar, hard-driving 70s rock drums, then breaks into catchy Mandarin Chinese "
         "pop-rock vocals (male and female), reverb, trippy, groovy, big and energetic")
LYRICS = ("霓虹灯下 云吧门开\n圣杯在手 心都打开\n"
          "吸一口 飞上云端\n小林的云 带我环绕\n"
          "圣杯云吧 醉在云海\n飘啊飘 不想下来\n"
          "吸一口 飞上云端\n圣杯云吧 不想下来")

def run_retry(tries=6):
    for a in range(1, tries+1):
        try:
            return replicate.run(MODEL, input={"lyrics": LYRICS, "prompt": STYLE, "audio_format": "mp3"})
        except Exception as e:
            msg=str(e)
            if "429" not in msg and "throttl" not in msg.lower():
                raise
            m=re.search(r"in ~?(\d+)\s*s", msg); wait=max(int(m.group(1))+3, 12) if m else 15*a
            print(f"  throttled (attempt {a}/{tries}); waiting {wait}s…"); time.sleep(wait)
    raise SystemExit("song: throttled out")

def main():
    if not os.environ.get("REPLICATE_API_TOKEN"): sys.exit("Set REPLICATE_API_TOKEN")
    if not SILENT.exists(): sys.exit(f"missing {SILENT}")
    print("song: minimax/music-2.6 …")
    o=run_retry()
    t=o[0] if isinstance(o,list) else o
    data=t.read() if hasattr(t,"read") else requests.get(str(t),timeout=600).content
    SONG.write_bytes(data); print("  song:", len(data)//1024,"KB")
    subprocess.run([FF,"-y","-i",str(SILENT),"-i",str(SONG),
        "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k",
        "-af","afade=t=in:st=0:d=0.3,afade=t=out:st=9.4:d=1.0","-shortest",str(REEL)],check=True)
    print("REEL with song:", REEL, REEL.stat().st_size//1024,"KB")

if __name__=="__main__": main()
