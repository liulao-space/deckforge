#!/usr/bin/env python3
"""DeckForge · poster generator.

Produce self-contained SVG "poster" previews (one per theme preset) that mirror
the real deck's look (accent color, cards, bars, rings) — great for a README
作品墙 / gallery where you don't (yet) have real screenshots. Replace these with
real screenshots as you publish. Pure stdlib.

Usage:
    python tools/posters.py -o posters       # writes posters/{name}.svg + tiled strip
"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from build import PRESETS, _shade  # reuse theme derivation


def poster(accent, name, w=720, h=480):
    """A stylized slide: header bar, title, two feature cards, an accent ring + rail."""
    bg = "#ffffff"
    card = "#ffffff"
    ink = "#173029"
    dim = "#5d726b"
    line = "#dbe9e4"
    accent_ink = _shade(accent, -0.55)

    card2 = "<rect x='40' y='250' width='300' height='150' rx='16' fill='%s' stroke='%s'/>" % (card, line)
    card3 = "<rect x='380' y='250' width='300' height='150' rx='16' fill='%s' stroke='%s'/>" % (card, line)
    title = "<rect x='40' y='170' width='420' height='26' rx='7' fill='%s'/>" % ink
    title2 = "<rect x='40' y='206' width='300' height='14' rx='7' fill='%s' opacity='.55'/>" % dim
    chips = "".join(
        "<rect x='66' y='%d' width='150' height='10' rx='5' fill='%s' opacity='.5'/>" % (cy, dim)
        for cy in (286, 320, 354))
    chipR = "".join(
        "<rect x='406' y='%d' width='150' height='10' rx='5' fill='%s' opacity='.5'/>" % (cy, dim)
        for cy in (286, 320, 354))

    # accent ring badge + rail indicator
    ring = ("<circle cx='585' cy='120' r='44' fill='%s' opacity='.14'/>"
            "<circle cx='585' cy='120' r='30' fill='none' stroke='%s' stroke-width='4'/>"
            "<circle cx='585' cy='120' r='7' fill='%s'/>") % (accent, accent, accent)
    rail = ("<rect x='672' y='90' width='4' height='150' rx='2' fill='%s' opacity='.18'/>"
            "<rect x='671' y='90' width='6' height='38' rx='3' fill='%s'/>") % (accent, accent)

    label = "<text x='40' y='80' font-family='sans-serif' font-size='15' fill='%s' font-weight='700'>DeckForge</text>" % accent_ink
    name_txt = "<text x='40' y='118' font-family='sans-serif' font-size='24' fill='%s' font-weight='800'>%s</text>" % (ink, name)

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 480" width="{w}" height="{h}">'
            f'<rect width="720" height="480" fill="{bg}"/>'
            f'{label}{name_txt}{title}{title2}{card2}{card3}{chips}{chipR}{ring}{rail}</svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="posters")
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)

    tiles = []
    for name, p in PRESETS.items():
        svg = poster(p["accent"], name)
        (out / f"{name}.svg").write_text(svg, encoding="utf-8")
        tiles.append(svg.replace('viewBox="0 0 720 480"', 'viewBox="0 0 360 240" width="360" height="240"'))
        print(f"[poster] {name}.svg")

    # a tiled contact sheet — every preset, wrapped into a 4-column grid
    COLS = 4
    rows = (len(tiles) + COLS - 1) // COLS
    strip = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {COLS*360} {rows*240}" '
             f'width="{COLS*360}" height="{rows*240}">'
             + "".join(f'<g transform="translate({(i % COLS)*360},{(i // COLS)*240})">{t}</g>'
                       for i, t in enumerate(tiles))
             + "</svg>")
    (out / "strip.svg").write_text(strip, encoding="utf-8")
    print(f"[poster] strip.svg")


if __name__ == "__main__":
    main()
