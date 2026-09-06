---
name: deckforge
description: >-
  Generate a polished, animated, single-file HTML slide deck from a JSON content
  spec. Use when the user wants a presentation / slideshow / PPT-style deck about
  a topic, with smooth one-page-at-a-time scrolling, a theme accent color, nice
  inline icons, and no external dependencies or npm installs.
---

# DeckForge

You are the DeckForge agent. Given a topic, produce a **high-quality animated HTML
slide deck** and a matching `content.json`. Do NOT hand-write CSS/JS — use the
DeckForge engine so quality stays consistent and the deck stays maintainable.

## Workflow

1. **Clarify** (briefly): audience, number of slides, theme accent color, light/dark.
   If not stated, default accent `#12876f`, light theme, 5–8 slides.
2. **Outline** the deck: title slide, then 1 slide per key idea, ending with a
   takeaway. For compare/choose topics always include: *both tools*, a *comparison*,
   a *decision*, and a *hands-on tutorial*.
3. **Write `content.json`** using the block DSL below. Map each slide idea to the
   BEST block type (don't overuse `cards` — mix `vs`, `flow`, `terminal`,
   `steps`, `table`, `quote` for visual variety).
   - If the user just wants a starting point, use `--new "<title>"` (quick scaffold)
     or `--init` (interactive) instead of writing JSON from scratch.
4. **Build**:
   ```bash
   python3 build.py content.json -o out.html --accent "<color>" [--dark] [--frame clean|bold|minimal]
   ```
5. **Export (optional)** — real screenshots / PDF / PNG per slide:
   ```bash
   pip install playwright && python -m playwright install chromium
   python tools/capture.py out.html -o out.png  --format png    # tall PNG
   python tools/capture.py out.html -o out.pdf  --format pdf    # PDF
   python tools/capture.py out.html -o pages/   --format pages  # per-slide PNG
   ```
6. **Verify**: open `out.html` (or `--watch` while editing). Check that
   - content fits (long blocks → use a shorter list or `--dark`, or it inner-scrolls);
   - no overlong lines get clipped;
   - every referenced icon (`icon`/`tile`) exists in `templates/icons.svg`.
7. **Present** the output file to the user.

## Content DSL

Top level:
```json
{
  "title": "Deck title",
  "accent": "#12876f",
  "slides": [ { ... }, ... ]
}
```

A slide:
```jsonc
{
  "align": "left" | "center",      // optional
  "eyebrow": "01 · 背景",            // small label
  "title": "Headline",
  "grad": false,                    // put title through accent gradient
  "lead": "supporting line",
  "blocks": [ { ... } ]             // 1+ blocks
}
```

### Blocks

- **pills** — tag row. `{items:[{text, icon?, kind?"b"|"am"|"plain"}], align?, margin?}`
- **cards** — grid. `{cols:3, items:[{num?|tile?, title, text?}]}`
- **card-list** — icon list card. `{title?, items:[{icon?, text}]}`
- **terminal** — typewriter terminal. `{lines:[ "cmd", {color:"teal|amb|ok|dim|wt", text:"…"}, … ]}`
- **table** — comparison. `{header:[..], rows:[[..]], marks:[[y|n|p|""]]}` (first col auto labeled)
- **vs** — two columns + VS badge. `{left:{name,icon?,title,items:[..],tag?}, right:{...}}`
- **flow** — decision nodes. `{nodes:[{icon, title, desc, tag:"orca"|"her", tag_text}]}`
- **steps** — numbered tutorial steps. `{accent:"a"|"am", items:[{head, body, code?}]}`
- **warn** — tip box. `{text, margin?}`
- **quote** — emphasized line. `{text}`

**Inline markup**: `**bold**`, `` `code` ``, `[link](url)`, and `<br>` for line breaks.

**Icons**: reference by name (no `i-` prefix; a leading `i-` is also accepted). Available: orca, herdr, window, board,
phone, click, laptop, socket, loop, lock, eye, term, branch, merged, compass, note,
warn, robot, globe, stack. Extend in `templates/icons.svg`.

## Rules for good output

- **One idea per slide.** Title slides are centered; content slides left-aligned.
- **Use empty space.** Don't cram — `lead` + 1–2 blocks is plenty.
- **Prefer the right block**: compare → `table`+`vs`; tutorial → `steps`; decision → `flow`;
  agent status effects → `terminal`; recap → `quote`+`pills`.
- **Reveal animation** is automatic (`rv d1..d6`) — resist inline positioning that
  fights the grid.
- **Don't add `scroll-snap` or custom cursors yourself** — the engine owns transport.
- **Accessibility**: keep contrast high (dark text on light, light on dark terminals).

## Theme & layout

- `--frame <name>` picks a **layout** personality (not just color):
  - `clean` — default, balanced grid.
  - `bold` — huge tight headlines, no card borders, deeper shadows, hover lift.
  - `minimal` — airy whitespace, thin rules, transparent cards.
- `--preset <name>` swaps a whole themed set (teal/ocean/violet/sunset/rose/mono/emerald).
- `--accent <hex>` overrides a preset's accent color.
- `--dark` flips background/card/text/line automatically.
- Use the SAME accent across the deck; change only via CLI flag at build time.
- Frame rules live in `templates/base.css` under `body[data-frame="..."]`. To add a
  frame, append a `body[data-frame="myframe"]` block and register it in `FRAMES`.

## Traps the agent already knows (fixes baked into the engine)

These were real bugs and are now handled — do NOT reintroduce them:

1. **Icon file must be valid SVG-XML.** `templates/icons.svg` uses `<!-- ... -->`
   comments, NOT `/* ... */`. A `/* */` header renders as literal text on the page
   (you'll see a stray `<symbol id="i-...">` line and a pushed-down title). If you
   edit icons.svg, keep comment syntax `<!-- -->`.
2. **Wheel over-scroll.** One trackpad/mouse gesture emits many small `deltaY`s.
   The engine **accumulates** wheel deltas and only flips a page past a threshold
   (120px), ignores input mid-transition (`busy`), and decays the accumulator
   after ~240ms idle, so a single gesture = exactly ONE page. Never replace this
   with a naive `deltaY > 0 → next page`.
3. **Never hand-write the `<script>` transport** (pager, wheel, cursor, rail). It's
   owned by `templates/base.js`. Adding your own `scroll-snap`, `cursor:none`,
   or a second wheel handler will conflict.
4. **Theme colors must come from `:root` variables** (`--accent`, `--ink`, ...) so
   a preset/dark swap recolors everything. Don't hardcode hex in block content.

