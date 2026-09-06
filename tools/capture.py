#!/usr/bin/env python3
"""DeckForge · capture/export a built deck with headless Chromium.

Renders an animated DeckForge deck and exports it to:
  * a single tall PNG (every slide stacked, slide-per-viewport)
  * one PNG per slide
  * a multi-page PDF (best for sharing / printing)

Uses Playwright (Chromium). Optional dependency — only needed for export, not for
the core builder. Written to be robust to the deck's transform-based paging: it
temporarily flattens the deck vertically, shows every slide, hides the fixed
transport overlay (cursor/rail/side label/dots), and waits for reveal/text animations.

Usage:
    pip install playwright && python -m playwright install chromium
    python tools/capture.py outputs/PPT-1.html -o export/PPT-1.png --format png   # tall PNG
    python tools/capture.py outputs/PPT-1.html -o export/PPT-1/ --format pages   # per-slide PNG (each slide.png)
    python tools/capture.py outputs/PPT-1.html -o export/PPT-1.pdf --format pdf
    python tools/capture.py outputs/PPT-1.html -o export/ --format gif-less      # (placeholder)
Common:
    --width 1280 --height 800 --padding 0 --delay 1200   # delay = settle time per slide
"""
import argparse, pathlib, sys, os


def _settle_js(width, height):
    """Flatten the deck so every slide is fully visible & settled, and hide overlays."""
    return f"""
    (function(){{
      var deck = document.getElementById('deck');
      var vp = document.querySelector('.viewport');
      var slides = document.querySelectorAll('.section');
      var wrap = 1080 > 0 ? 1080 : 1080;
      // make all slides visible & stacked
      slides.forEach(function(s){{ s.classList.add('in'); }});
      // flatten transform
      if(deck){{ deck.style.transform='none'; deck.style.height='auto'; }}
      if(vp){{ vp.style.overflow='visible'; vp.style.position='static'; }}
      // hide fixed transport overlays
      ['rail','side','cursor'].forEach(function(id){{
        var el=document.getElementById(id); if(el) el.style.display='none';
      }});
      var dots=document.getElementById('dots'); if(dots) dots.style.display='none';
      // ensure each section occupies exactly `height` px so pages stack cleanly
      slides.forEach(function(s){{ s.style.height='{height}px'; s.style.overflow='hidden'; }});
      // reset reveal animation triggers by re-adding 'in' (already done) — nothing more needed
      document.body.style.overflow='visible';
    }})();
    """


def capture(html_path, out, fmt, width, height, delay):
    """Return list of produced paths."""
    from playwright.sync_api import sync_playwright
    html = pathlib.Path(html_path).resolve()
    out_p = pathlib.Path(out).resolve()
    produced = []

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        page.goto(html.as_uri())
        # wait for fonts/anim to avoid blank renders
        page.wait_for_timeout(300)
        page.evaluate(_settle_js(width, height))
        page.wait_for_timeout(delay)

        if fmt == "png":
            out_p.parent.mkdir(parents=True, exist_ok=True)
            # full-height tall screenshot of the flattened deck
            page.screenshot(path=str(out_p), full_page=True)
            produced.append(out_p)
        elif fmt == "pages":
            dirp = out_p if out_p.suffix == "" else out_p
            dirp.mkdir(parents=True, exist_ok=True)
            n = page.evaluate("document.querySelectorAll('.section').length")
            for i in range(n):
                # scroll each section into the viewport then clip-shot
                page.evaluate(f"""
                  (function(){{ var s=document.querySelectorAll('.section')[{i}];
                    window.scrollTo(0, s.offsetTop); }})()
                """)
                page.wait_for_timeout(40)
                page.screenshot(path=str(dirp / f"slide-{i+1}.png"))
                produced.append(dirp / f"slide-{i+1}.png")
        elif fmt == "pdf":
            out_p.parent.mkdir(parents=True, exist_ok=True)
            page.pdf(path=str(out_p), print_background=True, width=f"{width}px",
                     height=f"{height}px", page_ranges="")
            produced.append(out_p)
        else:
            raise SystemExit(f"unknown format: {fmt}")
        b.close()
    return produced


def main():
    ap = argparse.ArgumentParser(description="Export a built DeckForge deck to PNG/PDF via headless Chromium.")
    ap.add_argument("html", help="path to a built .html deck")
    ap.add_argument("-o", "--out", required=True, help="output path (png file / dir for pages / pdf file)")
    ap.add_argument("--format", default="png", choices=["png", "pages", "pdf"])
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--delay", type=int, default=1400, help="settle ms after load")
    args = ap.parse_args()

    if not pathlib.Path(args.html).exists():
        raise SystemExit(f"deck html not found: {args.html}")

    produced = capture(args.html, args.out, args.format, args.width, args.height, args.delay)
    for f in produced:
        print(f"[capture] {f} ({os.path.getsize(f)//1024} KB)")


if __name__ == "__main__":
    main()
