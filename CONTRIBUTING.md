# Contributing to DeckForge

Thanks for helping. Three things help the project scale fastest:

## 1. Add a new block type (biggest visual impact)
A block is a Python function `r_<type>(spec) -> html` registered in `RENDERERS`,
plus a matching entry in `SKILL.md`'s DSL table and an example in `examples/`.
Steps:
1. Add the renderer in `build.py` (see `r_cards`, `r_terminal` for patterns).
2. Register it in `RENDERERS = {...}`.
3. Add to `SKILL.md` **Blocks** section.
4. Add a usage to `examples/choosing-a-framework.json` so CI renders it.

## 2. Add a theme preset
Add one line to `PRESETS` in `build.py` — everything else (soft/ink/cards/light+dark)
is derived from the accent automatically:
```python
PRESETS = { ..., "forest": {"accent": "#2f8a3f"} }
```
Confirm it builds: `python3 build.py examples/choosing-a-framework.json -o /tmp/f.html --preset forest`.

## 2b. Add a frame (layout personality)
Frames change *layout*, not color. Append a `body[data-frame="myframe"] {...}` block in
`templates/base.css` and register `"myframe"` in `FRAMES` (build.py). Then it's selectable
via `--frame myframe`. Keep it theme-aware: read colors from `var(--accent)` / `var(--ink)`
so it works with any preset and in dark mode.

## 3. Add an inline icon
Append a `<symbol id="i-name" viewBox="0 0 24 24">` to `templates/icons.svg`.
Keep stroke style consistent (stroke-width ~1.9, round caps). Reference it as
`{icon: "name"}` in content (a leading `i-` also works) — CI will catch any
undefined reference.

## Style guidelines
- **Engine owns transport & styling.** Don't add your own `scroll-snap`, custom
  cursors, or per-deck CSS — that's what keeps quality consistent.
- Theme colors must come from the `:root` variables (`var(--accent)`,
  `var(--ink)`, ...) so preset/dark swap recolors automatically.
- Keep everything **zero-dependency and stdlib-only**.

## Running checks
```bash
python3 build.py --list-presets
node tools/validate.js          # builds all presets + JS/icon checks
python3 tools/posters.py        # regenerates gallery posters
```

## Commit style
Small, focused PRs. One block or one preset per PR where possible.
