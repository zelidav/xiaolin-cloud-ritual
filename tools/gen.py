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
    "scene. The Chalice GLASS is a HAND-SIZED faceted diamond-shaped clear glass dome CUP — about "
    "5 to 6 inches tall, the size of a small tumbler that fits comfortably in one hand (see the "
    "hand reference for scale) — with a polished gold "
    "rim around the top opening and the red octagonal Xiaolin seal printed on the "
    "glass, seated on a compact hexagonal puck base (black or lacquer-red) with a "
    "small black mouthpiece in the center; luminous warm white-and-gold vapor "
    "swirls inside the glass and rises from the top. Keep the glass at correct hand-held scale. "
    "STRICT: do NOT include any other vessels — no wine or cocktail glasses, no tall vases, no "
    "wrong-shaped tumblers, no red-liquid goblets, no beakers, no disposable cups. When a guest "
    "holds it, they hold ONLY this hand-sized faceted glass dome cup. "
)
CHREF = ["chalice/c7.jpg", "chalice/c-hand.jpg", "chalice/c1.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"]

# (filename, [reference local files], prompt, aspect)
TARGETS = [
    ("hero-chalice.jpg", CHREF,
     "Museum-style luxury product photograph. " + CHALICE + "It stands on a deep "
     "lacquer-red surface with fine gold dragon line-work and warm gold rim light, "
     "luminous vapor swirling inside the glass and a wisp rising from the top. " + BRAND, "1:1"),

    ("popup-dispensary.jpg",
     ["popup-table-ref2.jpg", "chalice/c7.jpg", "chalice/c-hand.jpg", "joints/lineup.png", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A clean STANDALONE product photograph (NO people) of the complete Made in Xiaolin x SYPP "
     "Cloud Bar in-store pop-up: a portable stretch-fabric pop-up COUNTER of the same curved "
     "hourglass shape as the first reference (waist-high, hard flat top), tastefully wrapped in "
     "red-and-gold Xiaolin fabric with the octagonal seal and subtle gold dragon line-work. "
     "FITTED onto and COVERING THE ENTIRE TOP is a SLIM low-profile red-and-gold LED tray. "
     + CHALICE + "On that tray, TWO Chalice hexagonal bases sit DEEPLY INSET in gold-lit "
     "cradles set toward the BACK with vapor rising; built-in BACKLIT inset slots hold 3-4 "
     "different-sized Made in Xiaolin joints (a cannagar, a Soldato and a small Bambino) and a "
     "few cards, with a small brochure holder beside them. Keep branding SUBTLE — a small "
     "discreet 'Chalice available here' note and a quiet card-payment symbol blended into the "
     "fabric, no loud banner. The whole unit stands in an upscale dispensary, warm retail "
     "lighting, branded shelving softly blurred behind. Premium product-in-situ shot, all "
     "Chinese lacquer-red and gold. " + BRAND, "4:3"),

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
     ["chalice/c7.jpg", "chalice/c-hand.jpg", "installation-img-1024x1015.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
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
     ["popup-table-ref2.jpg", "gen/popup-dispensary.jpg", "chalice/c-hand.jpg", "chris-louie.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A realistic photograph inside an upscale modern cannabis dispensary. A portable "
     "STRETCH-FABRIC POP-UP COUNTER of the SAME curved hourglass shape as the first reference "
     "(a waist-high counter with a hard flat top), tastefully wrapped in Made in Xiaolin x "
     "SYPP red-and-gold fabric with the octagonal Xiaolin seal and subtle gold dragon "
     "line-work. FITTED onto and COVERING THE ENTIRE TOP of the counter is exactly the SLIM "
     "low-profile red-and-gold LED tray shown in the second reference image. " + CHALICE
     + "On that tray, TWO Chalice hexagonal bases sit DEEPLY INSET and RECESSED into gold-lit "
     "cradles set toward the BACK with vapor rising; built-in BACKLIT inset slots hold 3-4 "
     "different-sized Made in Xiaolin joints (a cannagar, a Soldato and a small Bambino) and a "
     "few cards, and beside them on the top sits a small holder of brochures. The tray is all "
     "Chinese lacquer-red and gold. Keep the Chalice advertising SUBTLE and tasteful — just a "
     "small discreet 'Chalice available here' note and a quiet card-payment symbol blended into "
     "the red-and-gold fabric, NOT a loud banner (this is a refined dispensary — understated). "
     "The brand ambassador is an attractive young Asian woman in a fitted Made in Xiaolin tee "
     "behind the counter. The two CUSTOMERS are diverse — ONE is a man who closely RESEMBLES "
     "the person in the founder reference photo (same face and features, his signature black "
     "cap with a small red emblem, sunglasses, a long single braid, black-and-red jacket); the "
     "other is a different diverse guest. Each holds ONLY the hand-sized clear glass DOME lifted "
     "off its base (just the glass in hand, not the base, not the whole device), sipping through "
     "a clear straw. Warm dispensary lighting, branded shelving softly blurred behind. " + BRAND, "16:9"),

    ("event.jpg", CHREF,
     "A premium event activation Cloud Bar in lacquer-red and gold beneath a soft gold "
     "cloud canopy. " + CHALICE + "A row of these identical Chalice vaporizers glows along "
     "the bar, vapor rising. Fine gold dragon line-work, the red-and-gold octagonal "
     "Xiaolin temple seal as the hero logo on the bar front, a stylish product-launch "
     "setting with warm gold light and blurred guests. Cinematic editorial. " + BRAND, "16:9"),

    ("reel-sample.jpg",
     ["gen/popup-dispensary.jpg", "chalice/c-hand.jpg", "chris-louie.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A vertical candid photo inside an upscale cannabis dispensary: the Made in Xiaolin x SYPP "
     "Cloud Bar pop-up (red-and-gold fabric counter with the LED tray on top, two chalices "
     "inset, vapor rising) with two diverse customers sampling — ONE a man who closely "
     "RESEMBLES the person in the founder reference photo (same face, black cap with a small "
     "red emblem, sunglasses, long single braid, black-and-red jacket) — each holding ONLY the "
     "hand-sized clear glass dome and sipping through a clear straw, smiling — and a "
     "young Asian woman brand ambassador in a Made in Xiaolin tee hosting. Warm dispensary "
     "lighting, real and lively. " + BRAND, "9:16"),

    ("reel-walkaway.jpg",
     ["chalice/c7.jpg", "chalice/c-hand.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A vertical candid photo: a happy young customer walking away from a dispensary checkout "
     "counter toward camera, holding a boxed Made in Xiaolin CHALICE (the gift box bears the "
     "red-and-gold octagonal Xiaolin seal) in their hands, smiling, a shopping moment. Warm "
     "modern dispensary interior softly blurred behind, register and budtender in the "
     "background. Real, authentic lifestyle photography. " + BRAND, "9:16"),

    ("led-topper.jpg",
     ["gen/popup-dispensary.jpg", "chalice/c7.jpg", "chalice/c-hand.jpg", "joints/lineup.png", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A clean close-up product photograph of the Made in Xiaolin x SYPP Cloud Bar LED TOPPER — "
     "the slim low-profile red-and-gold LED tray that fits over and covers the top of the "
     "pop-up counter (exactly the tray shown in the first reference). " + CHALICE + "TWO "
     "Chalice hexagonal bases sit DEEPLY INSET and RECESSED into gold-lit cradles set toward "
     "the BACK with vapor rising; built-in BACKLIT inset slots hold 3-4 different-sized Made in "
     "Xiaolin joints (a cannagar, a Soldato and a small Bambino) and a few cards, with a small "
     "brochure holder beside them. The tray is all Chinese lacquer-red and gold (no wood, no "
     "black). Warm, real-world product lighting on a clean surface, premium. " + BRAND, "4:3"),

    ("kit-bag.jpg",
     ["Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png", "logo-sypp.png"],
     "Premium product photograph of a Made in Xiaolin x SYPP branded SHOULDER / DUFFEL carry "
     "bag — structured matte-black with lacquer-red and gold accents, the red-and-gold "
     "octagonal Xiaolin seal embroidered on the side and a small tasteful 'SYPP CLOUD BAR' "
     "wordmark, gold zippers and a padded shoulder strap. Designed to hold the full pop-up "
     "kit. Studio product shot, warm premium lighting, dark red-and-gold backdrop. " + BRAND, "4:3"),

    ("bag-packed.jpg",
     ["popup-case-ref.jpg", "chalice/c7.jpg", "chalice/c-hand.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "An organized product photograph showing the WHOLE portable Cloud Bar kit as exactly TWO "
     "carry pieces, side by side. (1) A flat oval soft CARRY CASE of the same shape as the "
     "first reference — re-skinned matte black with red-and-gold Xiaolin trim and the octagonal "
     "seal, with a padded carry handle — lying open to reveal the folded red-and-gold "
     "stretch-fabric pop-up counter and its hard oval tabletop nested inside. (2) Beside it, "
     "the branded Made in Xiaolin x SYPP shoulder DUFFEL, open, holding the SLIM two-chalice "
     "LED tray, two Chalice vaporizers (clear glass domes + hexagonal bases), a few 510 carts "
     "in small SYPP pod boxes, and a stack of brochures. Together these two bags are the entire "
     "kit. Premium overhead product photograph, red and gold, warm lighting. " + BRAND, "16:9"),

    ("ambassador-carry.jpg",
     ["popup-case-ref.jpg", "Xiaolin_Logo_3_f952c9dd-0f8e-4fb8-bbce-12ca0981d697.png"],
     "A candid lifestyle photograph: an attractive young Asian woman brand ambassador in a "
     "fitted Made in Xiaolin tee walking into a modern cannabis dispensary carrying the ENTIRE "
     "kit herself — the flat oval pop-up counter CARRY CASE (matte black with the red-and-gold "
     "Xiaolin seal, like the reference) in one hand, and the branded Made in Xiaolin x SYPP "
     "shoulder DUFFEL over the other shoulder. Smiling, easy, arriving to set up. Conveys 'the "
     "whole bar in two bags, one person, deploys in minutes'. Warm dispensary interior softly "
     "blurred, real, authentic. " + BRAND, "4:3"),
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
