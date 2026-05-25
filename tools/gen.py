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

    ("popup-dispensary.jpg",
     ["chalice/c7.jpg", "cannagars/godfather.png", "installation-img-1024x1015.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A clean retail photograph of the compact Made in Xiaolin x SYPP Cloud Bar countertop "
     "unit (about 36 x 18 inches, a SLIM LOW-PROFILE lacquer-red and gold LED tray only a couple "
     "inches thick — light and portable, not a bulky box) sitting on a dispensary retail counter. " + CHALICE + "TWO Chalice hexagonal bases sit inset in gold-lit "
     "cradles along the BACK with vapor rising, leaving plenty of room; built-in BACKLIT CUTOUT "
     "slots fill the rest of the tray holding a generous row of upright Made in Xiaolin cannagars (gold-tipped, red-and-gold bands, like the "
     "reference) glowing with the same warm gold backlight, plus a brochure slot. A small "
     "red-and-gold octagonal Xiaolin seal and a 'GET THE CHALICE - PAY BY CARD' card on the "
     "front face. Warm dispensary lighting, branded shelving softly blurred behind. Compact, "
     "clean, premium product-in-situ shot. " + BRAND, "4:3"),

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
     ["chalice/c7.jpg", "installation-img-1024x1015.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A warm, upscale cocktail bar at night — a normal stylish bar with a back-bar full of "
     "liquor bottles, cocktail glasses and soft pendant lighting, patrons mingling. Sitting "
     "ON THE BAR next to the bartender is a compact THREE-UNIT Made in Xiaolin x SYPP Cloud "
     "Bar LED tray (lacquer-red and gold, three Chalice hexagonal bases inset in gold-lit "
     "cradles, vapor rising). " + CHALICE + "The bartender is filling one Chalice and handing "
     "its clear glass dome cup to a customer across the bar. Other well-dressed customers "
     "stand around holding glass dome cups and sipping vapor through clear straws, mingling. "
     "Real candid nightlife photography, warm and natural — a regular cocktail bar with the "
     "Cloud Bar tray as a special feature, NOT an all-red themed club. " + BRAND, "16:9"),

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
     ["popup-table-ref2.jpg", "chalice/c7.jpg", "cannagars/godfather.png", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A realistic photograph inside a modern cannabis dispensary. A portable STRETCH-FABRIC "
     "POP-UP COUNTER of the SAME curved hourglass shape as the first reference (a waist-high "
     "counter about 33 inches wide and 40 inches tall with a hard flat top), fully wrapped in "
     "Made in Xiaolin x SYPP red-and-gold printed fabric: a large red-and-gold octagonal "
     "Xiaolin temple seal, fine gold dragon line-work, a clean 'GET THE CHALICE - SPECIAL "
     "PRICE' banner and a small 'PAY BY CARD' tag beside a QR code. Resting ON TOP of the "
     "counter is a SLIM, LOW-PROFILE two-chalice LED tray (lacquer-red and gold, only a couple "
     "inches thick). " + CHALICE + "TWO Chalice hexagonal bases sit inset in gold-lit cradles "
     "at the back of the tray with vapor rising; the rest of the slim tray has built-in "
     "BACKLIT CUTOUT slots holding a generous row of upright Made in Xiaolin cannagars "
     "(gold-tipped, red-and-gold bands, like the reference) glowing with warm gold backlight, "
     "plus a brochure slot. The clear glass dome cups lift off the bases. A young Asian woman "
     "brand ambassador in a Made in Xiaolin tee stands behind the counter handing a clear "
     "glass dome cup to a customer; another guest sips from a glass dome through a clear straw "
     "(guests hold only the glass). Warm dispensary lighting, branded shelving softly blurred "
     "behind. The whole rig is light and portable — counter plus tray pack into one carry bag. "
     + BRAND, "16:9"),

    ("event.jpg", CHREF,
     "A premium event activation Cloud Bar in lacquer-red and gold beneath a soft gold "
     "cloud canopy. " + CHALICE + "A row of these identical Chalice vaporizers glows along "
     "the bar, vapor rising. Fine gold dragon line-work, the red-and-gold octagonal "
     "Xiaolin temple seal as the hero logo on the bar front, a stylish product-launch "
     "setting with warm gold light and blurred guests. Cinematic editorial. " + BRAND, "16:9"),

    ("led-topper.jpg",
     ["installation-img-1024x1015.jpg", "chalice/c7.jpg", "cannagars/godfather.png", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "Museum-style product photograph of the compact Made in Xiaolin x SYPP Cloud Bar LED "
     "TRAY (about 36 x 18 inches): a SLIM, LOW-PROFILE lacquer-red and gold tray only a couple inches thick (light and portable, not a bulky box). The BACK row has TWO circular "
     "gold-lit cradles for the Chalice hexagonal bases (one Chalice seated with its clear glass "
     "dome and a wisp of vapor); the rest of the slim tray is given to built-in BACKLIT CUTOUT "
     "slots holding a generous row of upright Made in Xiaolin cannagars (gold-tipped, red-and-gold bands, like the reference), glowing with the same warm gold backlight as the "
     "cradles, plus a slim brochure slot. The "
     "red-and-gold octagonal Xiaolin seal on the front face. Clean studio hardware "
     "photography, dark red-and-gold backdrop, premium. " + BRAND, "4:3"),

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
