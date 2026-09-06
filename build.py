#!/usr/bin/env python3
"""DeckForge · build a standalone, animated slide deck from a JSON content spec.

Zero runtime dependencies (pure stdlib). Single-file output, ready to open
in any browser — or to render into a GIF/screenshot for your README.

Usage:
    python build.py content.json -o out.html
    python build.py content.json -o out.html --accent "#1a73e8" --dark
    Watch (re-render on change):
    python build.py content.json -o out.html --watch
"""
import argparse, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
TEMP = HERE / "templates"


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------
def esc(s: str) -> str:
    """HTML-escape for text and attribute contexts."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def markup(s: str) -> str:
    """Inline conveniences: **bold**, `code`, [text](link), and <br> as a real line break.
    Everything else is escaped so raw user input can't inject markup."""
    s = str(s).replace("\x00", "")  # NUL is reserved for the <br> trick below
    # protect the literal <br> so it survives escaping as a real break
    s = s.replace("<br>", "\x00BR\x00")
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    s = s.replace("\x00BR\x00", "<br/>")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code style='color:var(--accent)'>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2" style="color:var(--accent)">\1</a>', s)
    return s


def _px(v, default):
    """Sanitize a JSON-supplied px length: only plain numbers survive."""
    try:
        return str(max(0.0, float(v)))
    except (TypeError, ValueError):
        return str(default)


_PILL_ALIGNS = ("center", "left", "right", "flex-start", "flex-end", "space-between")
_VALID_MARKS = ("y", "n", "p")


def icon(name, cls=""):
    """Embed a symbol reference. Accepts names with or without the `i-` prefix."""
    if not name:
        return ""
    ref = str(name).strip()
    if not ref.startswith("i-"):
        ref = "i-" + ref
    return f'<svg class="ico {cls}"><use href="#{esc(ref)}"/></svg>'


def tile(name, am=False):
    return f'<span class="tile{f" am" if am else ""}">{icon(name)}</span>' if name else ""


# ------------------------------------------------------------------
# block renderers
# ------------------------------------------------------------------
def r_pills(b):
    items = b.get("items", [])
    align = b.get("align", "center")
    if align not in _PILL_ALIGNS:
        align = "center"
    pills = []
    for it in items:
        cls = "pill"
        if it.get("kind") == "b": cls = "pill b"
        elif it.get("kind") == "am": cls = "pill am"
        pills.append(f'<span class="{cls}">{icon(it.get("icon"))} {markup(it.get("text", ""))}</span>')
    return ('<div style="display:flex;gap:12px;justify-content:' + align
            + ';flex-wrap:wrap;margin-top:' + _px(b.get("margin", 24), 24) + 'px">' + "".join(pills) + "</div>")


def r_cards(b):
    try:
        cols = min(max(int(b.get("cols", 3)), 1), 12)
    except (TypeError, ValueError):
        cols = 3
    items = []
    for c in b.get("items", []):
        head = (tile(c.get("tile")) if c.get("tile") else f'<div class="num">{esc(c.get("num", ""))}</div>')
        body = f'<h3 style="margin-top:12px">{markup(c["title"])}</h3>' if c.get("title") else ""
        if c.get("text"):
            body += f'<p style="margin:.5em 0 0;font-size:.95rem;line-height:1.65">{markup(c["text"])}</p>'
        items.append(f'<div class="card" style="padding:24px">{head}{body}</div>')
    return f'<div class="grid" style="grid-template-columns:repeat({cols},1fr)">{"".join(items)}</div>'


def UL(entries):
    lis = []
    for e in entries:
        if isinstance(e, dict):
            lis.append(f'<li>{icon(e.get("icon"))} {markup(e.get("text", ""))}</li>')
        else:
            lis.append(f"<li>{markup(e)}</li>")
    return '<ul style="list-style:none;margin-top:14px;display:grid;gap:11px;font-size:.95rem;color:var(--ink-dim)">' + "".join(lis) + "</ul>"


def r_card_ul(b):
    head = f'<h3>{markup(b["title"])}</h3>' if b.get("title") else ""
    return f'<div class="card">{head}{UL(b.get("items", []))}</div>'


def r_terminal(b):
    pre = []
    for i, ln in enumerate(b.get("lines", [])):
        delay = min(i * 0.12, 1.2)  # staggered per-line reveal; capped for exports
        if isinstance(ln, dict):
            t = esc(ln.get("text", ""))
            color = {"teal": "t-teal", "amb": "t-amb", "ok": "t-ok", "dim": "t-dim", "wt": "t-wt"}.get(ln.get("color", "wt"), "t-wt")
            pre.append(f'<span class="ln {color}" style="--d:{delay:.2f}s">{t}</span><br>')
        else:
            pre.append(f'<span class="ln" style="--d:{delay:.2f}s">{markup(ln)}</span><br>')
    return ('<div class="term"><div class="bar"><i></i><i></i><i></i></div>'
            f'<pre>{"".join(pre)}<span class="termcur"></span></pre></div>')


def r_table(b):
    headers = b.get("header", [])
    rows = b.get("rows", [])
    marks = b.get("marks", [])  # list of 'y'|'n'|'p'|'' per cell
    th = "".join(f'<th>{markup(h)}</th>' for h in headers)
    body = []
    for ri, row in enumerate(rows):
        c = []
        for ci, cell in enumerate(row):
            cls = marks[ri][ci] if ri < len(marks) and ci < len(marks[ri]) else ""
            if cls not in _VALID_MARKS:
                cls = ""
            if ci == 0:
                c.append(f'<td class="lbl">{markup(cell)}</td>')
            elif cls:
                c.append(f'<td><span class="{cls}">{markup(cell)}</span></td>')
            else:
                c.append(f"<td>{markup(cell)}</td>")
        body.append("<tr>" + "".join(c) + "</tr>")
    return (f'<div class="tabwrap"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


def r_vs(b):
    left, right = b["left"], b["right"]
    colA = (f'<div class="col a"><span style="font-weight:800;color:var(--accent);display:inline-flex;align-items:center;gap:.4em">'
            f'{icon(left.get("icon"))}{markup(left["name"])}</span>'
            f'<h3 style="margin-top:12px">{markup(left["title"])}</h3>{UL(left.get("items", []))}'
            f'<span class="tag orc">{markup(left.get("tag",""))}</span></div>')
    colB = (f'<div class="col b"><span style="font-weight:800;color:var(--accent-2);display:inline-flex;align-items:center;gap:.4em">'
            f'{icon(right.get("icon"))}{markup(right["name"])}</span>'
            f'<h3 style="margin-top:12px">{markup(right["title"])}</h3>{UL(right.get("items", []))}'
            f'<span class="tag her">{markup(right.get("tag",""))}</span></div>')
    mid = f'<div class="mid"><div class="vsbadge">{esc(b.get("badge","VS"))}</div></div>'
    return f'<div class="vs">{colA}{mid}{colB}</div>'


def r_flow(b):
    nodes = []
    for nd in b.get("nodes", []):
        am = nd.get("tag") == "her"
        nodes.append(f'<div class="node"><div class="icon">{tile(nd.get("icon"), am)}</div>'
                     f'<h4>{markup(nd["title"])}</h4><p>{markup(nd["desc"])}</p>'
                     f'<span class="tag {"her" if am else "orc"}">{markup(nd["tag_text"])}</span></div>')
    return f'<div class="flow">{"".join(nodes)}</div>'


def r_steps(b):
    lis = []
    for s in b.get("items", []):
        head = s.get("head")
        body = s.get("body", "")
        code = s.get("code")
        hh = f'<div><span class="s-head">{markup(head)}</span>' if head else "<div>"
        cc = (f'<div style="margin-top:10px;background:#0c1a16;border-radius:10px;padding:12px 14px;overflow-x:auto;'
              f'font-family:monospace;font-size:.78rem;line-height:1.75;color:#eafaf5;white-space:pre">{esc(code)}</div>') if code else ""
        lis.append(f'<li>{hh}<p style="color:var(--ink-dim);font-size:.93rem;line-height:1.6">{markup(body)}</p>{cc}</div></li>')
    return '<ol class="steps-ol">' + "".join(lis) + "</ol>"


def r_warn(b):
    return f'<div class="warn" style="margin-top:{_px(b.get("margin", 22), 22)}px">{icon("warn")} {markup(b["text"])}</div>'


def r_quote(b):
    return f'<div class="quote" style="max-width:880px;margin-left:auto;margin-right:auto">{markup(b["text"])}</div>'


RENDERERS = {
    "pills": r_pills, "cards": r_cards, "card-list": r_card_ul, "terminal": r_terminal,
    "table": r_table, "vs": r_vs, "flow": r_flow, "steps": r_steps, "warn": r_warn, "quote": r_quote,
}


# ------------------------------------------------------------------
# slide assembly
# ------------------------------------------------------------------
def build_slide(slide, i):
    align = slide.get("align", "left")
    parts = []
    if slide.get("eyebrow"):
        parts.append(f'<div class="rv d1"><span class="eyebrow">{markup(slide["eyebrow"])}</span></div>')
    if slide.get("title"):
        _cls = 'rv d2'
        if slide.get("grad"):
            _cls += ' grad'
        parts.append(f'<h2 class="{_cls}" style="margin:18px 0 6px">{markup(slide["title"])}</h2>')
    if slide.get("lead"):
        parts.append(f'<p class="rv d3" style="margin-top:0;max-width:820px">{markup(slide["lead"])}</p>')
    for j, block in enumerate(slide.get("blocks", [])):
        if not isinstance(block, dict):
            raise ValueError(f"第 {i+1} 页的 blocks[{j}] 必须是对象，得到 {type(block).__name__}")
        r = RENDERERS.get(block.get("type"))
        if r:
            parts.append(f'<div class="rv d{j+2}" style="margin-top:{_px(block.get("margin", 30), 30)}px">{r(block)}</div>')
        else:
            raise ValueError(f"第 {i+1} 页存在未知 block 类型「{block.get('type')}」，可用：{', '.join(RENDERERS)}")
    body = "".join(parts)
    return f'<section class="section{" center" if align=="center" else ""}" data-title="{esc(slide.get("title",""))}"><div class="wrap{" center" if align=="center" else ""}">{body}</div></section>'


# ------------------------------------------------------------------
# theme presets
# ------------------------------------------------------------------
# Each preset supplies the full set of CSS variables in light and dark.
# The engine (base.css) only ever reads these variables — so swapping a
# preset recolors the WHOLE deck (badges, cursor, rail, terminals, etc.).
LIGHT = {
    "bg": "#fff", "bg-soft": "#f4faf8", "card": "#fff",
    "card-2": "linear-gradient(180deg,#fff,#fbfdfc)",
    "ink": "#173029", "ink-dim": "#5d726b", "line": "#dbe9e4",
}
DARK = {
    "bg": "#0d1f1b", "bg-soft": "#0a1613", "card": "#122a24",
    "card-2": "linear-gradient(180deg,#143329,#10241f)",
    "ink": "#eafaf5", "ink-dim": "#9fc4ba",
    # NOTE: `line` is derived from the accent per theme (see theme_vars),
    # so dark mode stays consistent across every preset.
}

PRESETS = {
    "teal":   {"accent": "#12876f"},
    "ocean":  {"accent": "#1a73e8"},
    "violet": {"accent": "#7c3aed"},
    "sunset": {"accent": "#d9480f"},
    "rose":   {"accent": "#c2255c"},
    "mono":   {"accent": "#292929"},
    "emerald":{"accent": "#0b7a5c"},
}


def _hex_to_rgb(h):
    h = str(h).lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(hexc, alpha):
    r, g, b = _hex_to_rgb(hexc)
    return f"rgba({r},{g},{b},{alpha})"


def _shade(hexc, amt):
    """amt in (-1..1): negative darkens toward black, positive lightens toward white."""
    r, g, b = _hex_to_rgb(hexc)
    w = abs(amt)
    if amt >= 0:
        nr, ng, nb = int(r + (255 - r) * w), int(g + (255 - g) * w), int(b + (255 - b) * w)
    else:
        nr, ng, nb = int(r * (1 - w)), int(g * (1 - w)), int(b * (1 - w))
    return f"#{nr:02x}{ng:02x}{nb:02x}"


def _accent_arg(v):
    """argparse type for --accent: accepts #1a73e8, 1a73e8, #fff (short hex)."""
    s = str(v).strip()
    if s and not s.startswith("#"):
        s = "#" + s
    h = s[1:]
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise argparse.ArgumentTypeError(f"accent 需要 6 位 hex（如 #1a73e8），得到「{v}」")
    try:
        int(h, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(f"accent 不是合法 hex：「{v}」")
    return "#" + h.lower()


def theme_vars(accent_hex, dark=False):
    """Full :root CSS variable block for a theme, driven by ONE accent color."""
    base = DARK if dark else LIGHT
    a = accent_hex or "#12876f"
    # derive all accent-derived tokens from the single accent color
    parts = [
        f"--accent: {a}",
        f"--accent-ink: {_shade(a, -0.55)}",
        f"--accent-soft: {_mix(a, .12)}",
        f"--accent-soft-2: {_mix('#e08a2e', .16)}",
        f"--accent-2: {_shade('#e08a2e', 0)}",
    ]
    for k, v in base.items():
        parts.append(f"--{k}: {v}")
    if dark:
        # accent-derived hairline so borders follow the preset, not teal
        parts.append(f"--line: {_mix(a, .28)}")
    return ":root{" + ";".join(parts) + "}"


FRAMES = ["clean", "bold", "minimal"]


def build(content, accent=None, preset=None, dark=False, frame="clean", out=None, lang="zh-CN"):
    if frame not in FRAMES:
        raise ValueError(f"未知 frame「{frame}」，可选：{', '.join(FRAMES)}")
    if preset is not None and preset not in PRESETS:
        raise ValueError(f"未知 preset「{preset}」，可选：{', '.join(PRESETS)}")
    css = (TEMP / "base.css").read_text(encoding="utf-8")
    icons = (TEMP / "icons.svg").read_text(encoding="utf-8")
    js = (TEMP / "base.js").read_text(encoding="utf-8")

    # precedence: --accent > --preset > content accent > default teal
    if accent is None:
        accent = PRESETS[preset]["accent"] if preset else \
                 (content.get("accent") or PRESETS["teal"]["accent"])
    theme = "<style>" + theme_vars(accent, dark) + "</style>"

    slides = [build_slide(s, i) for i, s in enumerate(content["slides"])]

    doc = f"""<!DOCTYPE html>
<html lang="{esc(lang)}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(content.get("title","DeckForge"))}</title>
<style>{css}</style>
{theme}
</head>
<body data-frame="{frame}">
{icons}
<div class="side" id="side"></div>
<div class="rail" id="rail"><div class="halo" id="halo"></div><div class="marker" id="marker"></div></div>
<div class="nav" id="dots" style="position:fixed;bottom:22px;left:0;right:0;display:flex;justify-content:center;gap:10px;z-index:60"></div>
<div id="cursor" aria-hidden="true"><span class="ring"></span><span class="dot"></span></div>
<main class="viewport"><div class="deck" id="deck">
{chr(10).join(slides)}
</div></main>
<script>{js}</script>
</body>
</html>"""

    if out:
        p = pathlib.Path(out); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(doc, encoding="utf-8")
        print(f"[deckforge] wrote {p.resolve()} ({len(doc.encode('utf-8'))//1024} KB)")
    return doc


# ------------------------------------------------------------------
# init: interactive scaffolding
# ------------------------------------------------------------------
def _ask(msg, defa=""):
    """input() that degrades gracefully when stdin is closed (CI / agent use)."""
    try:
        return input(f"  {msg}" + (f" [{defa}]" if defa else "") + " » ") or defa
    except EOFError:
        return defa


def cmd_init(args):
    """Interactive creator — asks questions and writes a content.json (plus builds it)."""
    title = _ask("Deck 标题", "我的演示") or "我的演示"
    theme = _ask("主题 preset (teal/ocean/violet/sunset/rose/mono/emerald)", "teal") or "teal"
    if theme not in PRESETS:
        print(f"  ⚠ 未知 preset「{theme}」，改用 teal")
        theme = "teal"
    try:
        dark = input("  Dark 主题? [y/N] » ").strip().lower() in ("y", "yes")
    except EOFError:
        dark = False
    try:
        n = int(_ask("想生成几页内容示例?", "5") or "5")
    except ValueError:
        n = 5
    n = max(1, min(n, 10))
    topic = _ask("一句话主题关键词（用于示例文字）", "产品发布") or "产品发布"

    slides = [{
        "align": "center", "title": title, "grad": True,
        "lead": f"这是 {topic} 的封面。用 **DeckForge** 生成。",
        "blocks": [{"type": "pills", "items": [
            {"text": "亮点一", "icon": "globe", "kind": "b"},
            {"text": "亮点二", "icon": "play", "kind": "am"}]}],
    }]
    examples = [
        {"eyebrow": "01 · 背景", "title": "为什么值得关注", "lead": "用 **lead** 写一句话说明背景。",
         "blocks": [{"type": "cards", "cols": 3, "items": [
             {"num": "①", "title": "第一点", "text": "描述第一个要点。"},
             {"num": "②", "title": "第二点", "text": "描述第二个要点。"},
             {"num": "③", "title": "第三点", "text": "描述第三个要点。"}]}]},
        {"eyebrow": "02 · 对比", "title": "两种方案对比", "lead": "用 vs 块做对比。",
         "blocks": [{"type": "vs", "left": {"name": "方案 A", "icon": "orca", "title": "围绕任务", "tag": "A", "items": ["要点一", "要点二", "要点三"]},
                    "right": {"name": "方案 B", "icon": "herdr", "title": "围绕会话", "tag": "B", "items": ["要点一", "要点二", "要点三"]}}]},
        {"eyebrow": "03 · 决策", "title": "如何选择", "lead": "用 flow 块做决策。",
         "blocks": [{"type": "flow", "nodes": [
             {"icon": "eye", "title": "想看得见", "desc": "描述场景", "tag": "orca", "tag_text": "选 A"},
             {"icon": "term", "title": "想脚本化", "desc": "描述场景", "tag": "her", "tag_text": "选 B"},
             {"icon": "branch", "title": "不冲突", "desc": "描述场景", "tag": "orca", "tag_text": "先 A"},
             {"icon": "socket", "title": "不丢失", "desc": "描述场景", "tag": "her", "tag_text": "先 B"}]}]},
        {"eyebrow": "04 · 实操", "title": "一步步上手", "lead": "用 steps 做教程。",
         "blocks": [{"type": "steps", "items": [
             {"head": "第一步", "body": "描述这一步。", "code": "$ command here"},
             {"head": "第二步", "body": "描述这一步。"},
             {"head": "第三步", "body": "描述这一步。"}]},
            {"type": "warn", "text": "这里是提示条，用于强调注意事项。"}]},
    ]
    slides += examples[: max(0, n - 1)]

    content = {"title": title, "accent": PRESETS[theme]["accent"], "slides": slides}
    p = pathlib.Path(args.out or "content.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✔ 已生成 {p}")

    build(content, preset=theme, dark=dark, out=str(p.with_suffix(".html")))
    print("✔ 已构建预览页；编辑 " + str(p) + " 或加参数 --watch")


def cmd_new(args):
    """Non-interactive: scaffold a fresh content.json from a topic title."""
    t = args.new or "我的演示"
    content = {"title": t, "accent": "#12876f", "slides": [
        {"align": "center", "title": t, "grad": True, "lead": "用 **DeckForge** 生成的封面。",
         "blocks": [{"type": "pills", "items": [{"text": "标题一", "icon": "globe", "kind": "b"},
                                                {"text": "标题二", "icon": "play", "kind": "am"}]}]},
        {"eyebrow": "01", "title": "背景", "lead": "一句话说明背景。",
         "blocks": [{"type": "cards", "cols": 3, "items": [
             {"num": "①", "title": "要点", "text": "描述。"},
             {"num": "②", "title": "要点", "text": "描述。"},
             {"num": "③", "title": "要点", "text": "描述。"}]}]},
        {"eyebrow": "02", "title": "结论", "lead": "总结。",
         "blocks": [{"type": "quote", "text": "**这里写一句强调的话。**"}]},
    ]}
    p = pathlib.Path(args.out or "content.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ 模板已写入 {p}")


def load_content(path):
    """Read + validate content.json with friendly, actionable error messages."""
    p = pathlib.Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        sys.exit(f"[deckforge] ✘ 找不到内容文件：{path}")
    except IsADirectoryError:
        sys.exit(f"[deckforge] ✘ 这是目录不是 JSON 文件：{path}")
    except UnicodeDecodeError:
        sys.exit(f"[deckforge] ✘ 文件不是 UTF-8 编码，请用 UTF-8 保存：{path}")
    try:
        content = json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"[deckforge] ✘ JSON 解析失败：{path} 第 {e.lineno} 行第 {e.colno} 列 — {e.msg}")
    if not isinstance(content, dict):
        sys.exit("[deckforge] ✘ content.json 顶层必须是对象：{title, slides[]}")
    slides = content.get("slides")
    if not isinstance(slides, list) or not slides:
        sys.exit("[deckforge] ✘ content.json 需要非空的 slides 数组（至少一页）")
    return content


def main():
    ap = argparse.ArgumentParser(description="DeckForge — build an animated slide deck from JSON.")
    ap.add_argument("content", nargs="?", help="path to content.json")
    ap.add_argument("--init", action="store_true", help="interactive new-deck scaffold (writes content.json + builds)")
    ap.add_argument("--new", metavar="TITLE", help="scaffold a fresh content.json from a title")
    ap.add_argument("-o", "--out", default="dist/index.html", help="output .html")
    ap.add_argument("--accent", default=None, type=_accent_arg, help="override accent hex (e.g. #1a73e8, 1a73e8, #fff)")
    ap.add_argument("--preset", default=None, help="theme preset: " + ", ".join(PRESETS))
    ap.add_argument("--list-presets", action="store_true", help="list available presets and exit")
    ap.add_argument("--frame", default="clean", help="layout frame: " + ", ".join(FRAMES))
    ap.add_argument("--dark", action="store_true", help="dark theme")
    ap.add_argument("--lang", default="zh-CN", help="<html lang> value (e.g. zh-CN, en)")
    ap.add_argument("--watch", action="store_true", help="re-render on content/template change")
    args = ap.parse_args()

    if args.list_presets:
        for name, p in PRESETS.items():
            print(f"{name:10s} accent {p['accent']}")
        return

    if args.init:
        cmd_init(args)
        return
    if args.new is not None:
        cmd_new(args)
        return

    if not args.content:
        ap.error("content.json is required (or use --init / --new / --list-presets)")

    if args.preset and args.preset not in PRESETS:
        ap.error(f"未知 --preset「{args.preset}」，可选：{', '.join(PRESETS)}")
    if args.frame not in FRAMES:
        ap.error(f"未知 --frame「{args.frame}」，可选：{', '.join(FRAMES)}")

    try:
        content = load_content(args.content)
        build(content, accent=args.accent, preset=args.preset, dark=args.dark,
              frame=args.frame, out=args.out, lang=args.lang)
    except KeyError as e:
        sys.exit(f"[deckforge] ✘ content.json 缺少必需字段：{e}\n"
                 f"   各 block 的必需字段见 README「内置块类型」或 SKILL.md")
    except (TypeError, ValueError) as e:
        sys.exit(f"[deckforge] ✘ 内容字段不合法：{e}")

    if args.watch:
        print("[deckforge] watching content + templates for changes... Ctrl+C to stop")
        import time

        def snapshot():
            m = {os.path.abspath(args.content): os.path.getmtime(args.content)}
            for f in TEMP.iterdir():
                m[str(f)] = f.stat().st_mtime
            return m

        last = snapshot()
        try:
            while True:
                time.sleep(1)
                cur = snapshot()
                if cur != last:
                    last = cur
                    try:
                        content = load_content(args.content)
                        build(content, accent=args.accent, preset=args.preset, dark=args.dark,
                              frame=args.frame, out=args.out, lang=args.lang)
                    except (KeyError, TypeError, ValueError) as e:
                        print(f"[deckforge] ⚠ 重建失败：{e}（修正后会自动重试）")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
