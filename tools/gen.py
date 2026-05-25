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

    ("nightlife.jpg",
     ["installation-img-1024x1015.jpg", "chalice/c7.jpg", "chalice/c1.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A high-energy upscale New York City nightclub. A long bar runs through the room with a "
     "glowing warm-gold LED top. " + CHALICE + "A row of these Chalice vaporizers is seated "
     "INSET into the glowing LED bar top, each in a circular gold-lit cradle, vapor rising. "
     "Around the bar and on the floor, stylish well-dressed guests are HOLDING the glass "
     "Chalice cups in their hands and sipping the cloud through clear straws, mingling and "
     "enjoying — a lively NYC club crowd. The red-and-gold octagonal Xiaolin temple seal "
     "glows on the front of the bar. Deep lacquer-red and gold with moody club lighting, "
     "colored light accents, bokeh, a DJ glow in the background. Cinematic nightlife "
     "photography, atmospheric and energetic. " + BRAND, "16:9"),

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
     ["chalice/c7.jpg", "cannagars/godfather.png", "installation-img-1024x1015.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A realistic candid photograph inside a warm modern cannabis dispensary. A long "
     "RECTANGULAR Made in Xiaolin x SYPP Cloud Bar pop-up TABLE, heavily branded in glossy "
     "lacquer-red and gold — a large red-and-gold octagonal Xiaolin temple seal and fine "
     "gold dragon line-work across the front skirt, with a clean gold promo banner reading "
     "'GET THE CHALICE - SPECIAL PRICE' and a small 'PAY BY CARD' tag beside a QR code. The "
     "lacquer-red and gold LED TOPPER spans the table. Along the BACK row, " + CHALICE
     + "three Chalice hexagonal bases sit INSET in circular gold-lit cradles with vapor "
     "rising, shifted toward the back. Built INTO the front of the topper are integrated "
     "display holders: an upright row of Made in Xiaolin pre-roll cannagars (gold-tipped, "
     "red-and-gold Xiaolin bands, like the reference) in a milled holder, and angled slots "
     "holding glossy brochures and cards. The clear glass dome cups lift off the bases. The "
     "brand ambassador — a pretty young Asian woman in a fitted Made in Xiaolin tee — is "
     "HANDING one clear glass dome cup across the table to a customer; another guest stands "
     "sipping the cloud from a glass dome through a clear straw. Guests hold ONLY the glass "
     "dome, never the base. Warm dispensary lighting, branded shelving softly blurred behind. "
     "Real, authentic lifestyle photography. " + BRAND, "16:9"),

    ("event.jpg", CHREF,
     "A premium event activation Cloud Bar in lacquer-red and gold beneath a soft gold "
     "cloud canopy. " + CHALICE + "A row of these identical Chalice vaporizers glows along "
     "the bar, vapor rising. Fine gold dragon line-work, the red-and-gold octagonal "
     "Xiaolin temple seal as the hero logo on the bar front, a stylish product-launch "
     "setting with warm gold light and blurred guests. Cinematic editorial. " + BRAND, "16:9"),

    ("led-topper.jpg",
     ["installation-img-1024x1015.jpg", "chalice/c7.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "Museum-style product photograph of the Made in Xiaolin x SYPP Cloud Bar LED TOPPER — a "
     "sleek rectangular lacquer-red and gold panel with several circular gold-lit LED cradles "
     "that hold the Chalice hexagonal bases, glowing warm gold. The red-and-gold octagonal "
     "Xiaolin seal is on the panel. One Chalice base sits in a cradle with its clear glass "
     "dome and a wisp of vapor. Clean studio hardware photography on a dark red-and-gold "
     "surface, premium. " + BRAND, "4:3"),

    ("kit-bag.jpg",
     ["Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png", "logo-sypp.png"],
     "Premium product photograph of a Made in Xiaolin x SYPP branded SHOULDER / DUFFEL carry "
     "bag — structured matte-black with lacquer-red and gold accents, the red-and-gold "
     "octagonal Xiaolin seal embroidered on the side and a small tasteful 'SYPP CLOUD BAR' "
     "wordmark, gold zippers and a padded shoulder strap. Designed to hold the full pop-up "
     "kit. Studio product shot, warm premium lighting, dark red-and-gold backdrop. " + BRAND, "4:3"),

    ("bag-packed.jpg",
     ["installation-img-1024x1015.jpg", "chalice/c7.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "An organized kit flat-lay: an open Made in Xiaolin x SYPP branded shoulder bag with the "
     "complete Cloud Bar pop-up kit packed neatly inside and laid beside it — the folded "
     "lacquer-red pop-up table cover, the red-and-gold LED topper panel, several Chalice "
     "vaporizers (clear glass domes + hexagonal bases), a few 510 carts in small branded "
     "boxes, and a stack of brochures. Everything fits in one carry bag. Premium overhead kit "
     "photograph, red and gold, warm lighting. " + BRAND, "16:9"),

    ("ambassador-carry.jpg",
     ["Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A candid lifestyle photograph: a stylish young Asian woman brand ambassador in a fitted "
     "Made in Xiaolin tee walking into a modern cannabis dispensary, carrying the branded "
     "Made in Xiaolin x SYPP shoulder bag (with the red-and-gold octagonal Xiaolin seal) "
     "easily over one shoulder, smiling, arriving to set up. Conveys 'one person carries the "
     "whole bar and deploys in minutes'. Warm dispensary interior softly blurred, real, "
     "authentic. " + BRAND, "4:3"),
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
