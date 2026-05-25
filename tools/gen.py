#!/usr/bin/env python3
"""Generate Made in Xiaolin x SYPP Cloud Bar mockups via Replicate nano-banana
(Gemini 2.5 Flash Image). Re-skins the real SYPP reference photos into the
lacquer-red + gold Made in Xiaolin brand. Idempotent; --force to overwrite."""
import os, sys, argparse, time
from pathlib import Path
import replicate, requests

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "img"
GEN = IMG / "gen"; GEN.mkdir(parents=True, exist_ok=True)

BRAND = (
    "Made in Xiaolin brand identity: deep glossy lacquer-red and warm gold, "
    "black walnut wood, the brand's octagonal temple seal logo (a red octagon "
    "with a gold border and a white calligraphic monogram inside), occasional "
    "fine gold dragon line-work. Premium, ceremonial, luxury cannabis "
    "hospitality. Warm cinematic lighting, editorial product photography, "
    "rich red and gold throughout, no gibberish text or watermarks."
)

# The ONLY device allowed in any scene is the real Made in Xiaolin CHALICE
# vaporizer (shopxiaolin.com/products/chalice): a clear faceted glass dome with
# a gold rim, the red octagonal Xiaolin seal on the glass, on a hexagonal base.
# Never the clear Zenco wine-style glasses, never red-liquid goblets, never cups.
CHALICE = (
    "THE Chalice vaporizer from the reference images is the ONLY device in the "
    "scene: a tall faceted diamond-shaped CLEAR glass dome with a polished gold "
    "rim around the top opening and the red octagonal Xiaolin seal printed on the "
    "glass, seated on a compact hexagonal puck base (black or lacquer-red) with a "
    "small black mouthpiece in the center; luminous warm white-and-gold vapor "
    "swirls inside the glass and rises from the top. Render this exact device "
    "design unchanged. STRICT: do NOT include any other vessels — no wine or "
    "cocktail glasses, no clear tumblers, no red-liquid goblets, no beakers, no "
    "disposable cups. Only this Chalice vaporizer. "
)
CHREF = ["chalice/c7.jpg", "chalice/c1.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"]

# (filename, [reference local files], prompt, aspect)
TARGETS = [
    ("hero-chalice.jpg", CHREF,
     "Museum-style luxury product photograph. " + CHALICE + "It stands on a deep "
     "lacquer-red surface with fine gold dragon line-work and warm gold rim light, "
     "luminous vapor swirling inside the glass and a wisp rising from the top. " + BRAND, "1:1"),

    ("popup-dispensary.jpg", CHREF,
     "A premium portable Cloud Bar pop-up podium, glossy lacquer-red with gold trim and "
     "a warm gold LED rim, the red-and-gold octagonal Xiaolin temple seal printed large "
     "and centered on the front. " + CHALICE + "Two or three of these identical Chalice "
     "vaporizers stand on top of the podium, vapor rising. Set inside an upscale modern "
     "cannabis dispensary with warm walnut shelving and premium retail lighting. " + BRAND, "4:3"),

    ("tasting-dispensary.jpg", CHREF,
     "An elegant ritual guide hosting a customer through a cloud tasting at a curved "
     "premium dispensary counter. " + CHALICE + "On the counter, a lacquer-red LED tray "
     "with gold trim holds two or three of these identical Chalice vaporizers, vapor "
     "rising. The red-and-gold octagonal Xiaolin temple seal appears on a small display "
     "card. Warm, intimate, premium retail interior with red and gold accent lighting. "
     "Candid editorial photograph. " + BRAND, "4:3"),

    ("installation-trays.jpg", CHREF,
     "Museum-style product display of a modular Cloud Bar LED tray, lacquer-red with gold "
     "metallic trim and a warm gold LED underglow. " + CHALICE + "Three identical Chalice "
     "vaporizers sit on the tray, vapor rising. Arranged on a black-and-red lacquer "
     "surface, the small gold octagonal Xiaolin seal etched on the tray. Dramatic premium "
     "product lighting, red and gold. " + BRAND, "4:3"),

    ("nightlife.jpg", CHREF,
     "A luxury nightlife lounge Cloud Ritual bar finished in lacquer-red and gold with "
     "warm gold LED underlighting. " + CHALICE + "A row of these identical Chalice "
     "vaporizers glows along the bar top, vapor rising. Atmospheric low light, elegantly "
     "dressed guests softly blurred in the background. The red-and-gold octagonal Xiaolin "
     "temple seal glows on the front of the bar. Cinematic editorial hospitality "
     "photograph. " + BRAND, "16:9"),

    ("xiaolin-blend-cart.jpg",
     ["Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png", "Photoroom_20241218_174339.jpg"],
     "A premium product photograph of a sleek Made in Xiaolin branded 510-thread vape "
     "cartridge standing upright, filled with glowing golden amber live-rosin oil, with "
     "a glossy black ceramic mouthpiece and a small red-and-gold octagonal Xiaolin temple "
     "seal printed on the cartridge. Beside it stands an elegant lacquer-red gift box "
     "stamped with the gold octagonal Xiaolin seal and fine gold dragon line-work. Deep "
     "lacquer-red and gold setting, warm museum product lighting, single hero subject. "
     "STRICT: only the cartridge and its box, no other devices, no gibberish text. " + BRAND, "1:1"),

    ("popup-set.jpg",
     ["installation-img-1024x1015.jpg", "img-events-popup-sypp.jpg", "chalice/c7.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A realistic candid documentary photograph inside a warm modern cannabis dispensary. "
     "In the foreground is a Made in Xiaolin Cloud Bar pop-up — a portable podium re-skinned "
     "in glossy lacquer-red with subtle gold trim, the red-and-gold octagonal Xiaolin temple "
     "seal and a small neat QR code on the front skirt, with a glowing warm-gold LED top. "
     + CHALICE + "Exactly three of these Chalice vaporizers are seated SLIGHTLY INSET and "
     "RECESSED into the glowing LED tabletop, each sitting in a circular cradle ringed with "
     "warm gold LED light exactly like the reference trays, vapor gently rising. A friendly "
     "brand ambassador in tasteful Made in Xiaolin branded apparel stands behind the podium "
     "welcoming guests. Two or three relaxed, well-dressed customers lean in and sample — "
     "sipping the cloud from the glass Chalice cups through clear straws, smiling and casual. "
     "Natural dispensary lighting, wood shelving with product softly blurred behind. Real, "
     "authentic, understated lifestyle photography — not a staged studio set. " + BRAND, "16:9"),

    ("event.jpg", CHREF,
     "A premium event activation Cloud Bar in lacquer-red and gold beneath a soft gold "
     "cloud canopy. " + CHALICE + "A row of these identical Chalice vaporizers glows along "
     "the bar, vapor rising. Fine gold dragon line-work, the red-and-gold octagonal "
     "Xiaolin temple seal as the hero logo on the bar front, a stylish product-launch "
     "setting with warm gold light and blurred guests. Cinematic editorial. " + BRAND, "16:9"),
]


def upload(name):
    with open(IMG / name, "rb") as f:
        return replicate.files.create(file=f).urls["get"]


def run_retry(model, inp, tries=4):
    for a in range(1, tries + 1):
        try:
            return replicate.run(model, input=inp)
        except Exception as e:
            if a == tries or not any(k in str(e).lower() for k in ("429", "throttl", "rate")):
                raise
            time.sleep(10 * a)


def save(out, dest):
    t = out[0] if isinstance(out, list) else out
    if hasattr(t, "read"):
        dest.write_bytes(t.read())
    else:
        dest.write_bytes(requests.get(str(t), timeout=120).content)
    return dest.stat().st_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="substring of filename to limit")
    args = ap.parse_args()
    if not os.environ.get("REPLICATE_API_TOKEN"):
        sys.exit("Set REPLICATE_API_TOKEN")

    cache = {}
    def url(n):
        if n not in cache:
            cache[n] = upload(n)
        return cache[n]

    todo = [t for t in TARGETS if (not args.only or args.only in t[0])]
    todo = [t for t in todo if args.force or not (GEN / t[0]).exists()]
    print(f"Generating {len(todo)} image(s) via google/nano-banana…")
    for i, (fn, refs, prompt, ar) in enumerate(todo, 1):
        dest = GEN / fn
        try:
            inp = {"prompt": prompt, "image_input": [url(r) for r in refs],
                   "output_format": "jpg", "aspect_ratio": ar}
            out = run_retry("google/nano-banana", inp)
            kb = save(out, dest) // 1024
            print(f"[{i}/{len(todo)}] OK {fn} ({kb} KB)")
        except Exception as e:
            print(f"[{i}/{len(todo)}] FAIL {fn}: {e}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
