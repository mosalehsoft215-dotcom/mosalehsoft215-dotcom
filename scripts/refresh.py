#!/usr/bin/env python3
"""Build the whole profile: README.md plus every SVG under assets/.

Each panel is drawn twice, for GitHub's dark and light themes, and the README picks the right one with <picture>.
Live data: the public repositories of the account (project cards) and the flagship benchmark's counts. Standard
library only, so it runs unchanged on a GitHub Actions runner. Nothing is rewritten when the live data are
unchanged; pass --force after editing the text below.
"""
import datetime
import html
import json
import os
import re
import sys
import textwrap
import urllib.request
from pathlib import Path

USER = "mosalehsoft215-dotcom"
FLAGSHIP = "reduction-bench"
HIDE = {USER}                       # never shown as a card (empty repos and forks are skipped too)
MAX_CARDS = 8
LINKEDIN = "https://www.linkedin.com/in/mohamed-saleh-013726274"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "stats.json"
README = ROOT / "README.md"

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
DARK = dict(BG0="#07111E", BG1="#150C2B", GRID="#1B2638", GRIDO=".55", FRAME="#23324A", CARD="#0B1220", CARD_STROKE="#22314A",
            CHIP_STROKE="#2A3A55", ARROW="#3B4B66", TRACK="#1A2436", INK="#F8FAFC", MUTED="#94A3B8", DIM="#64748B",
            SOFT="#CBD5E1", BLUE="#4D7CFE", TEAL="#2DD4BF", VIOLET="#9B7CFF", ORANGE="#F0883E", AMBER="#FBBF24", PINK="#F472B6")
LIGHT = dict(BG0="#FFFFFF", BG1="#F1F4F9", GRID="#E6EBF2", GRIDO=".9", FRAME="#D0D7DE", CARD="#FFFFFF", CARD_STROKE="#D8DEE6",
             CHIP_STROKE="#CBD5E1", ARROW="#94A3B8", TRACK="#E5E9F0", INK="#0F172A", MUTED="#475569", DIM="#64748B",
             SOFT="#334155", BLUE="#2563EB", TEAL="#0F9F8F", VIOLET="#7C3AED", ORANGE="#EA580C", AMBER="#B45309", PINK="#DB2777")
THEMES = {"dark": DARK, "light": LIGHT}
LANG_COLOR = {"Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "JavaScript": "#F1E05A", "TypeScript": "#3178C6",
              "C++": "#F34B7D", "C#": "#178600", "Java": "#B07219", "HTML": "#E34C26", "Shell": "#89E051",
              "Dockerfile": "#2496ED", "Go": "#00ADD8", "Rust": "#DEA584"}
DOMAIN = {"physical-sciences": ("Physical Sciences", "BLUE"), "engineering-sciences": ("Engineering Sciences", "ORANGE"),
          "earth-sciences": ("Earth Sciences", "TEAL")}

ROLES = ["Agentic AI systems", "Document intelligence", "Computer vision", "AI evaluation & benchmarks"]
CAPABILITIES = [
    ("AGENTIC AI SYSTEMS", "VIOLET", ["Multi-agent systems that plan,", "remember and use real tools."]),
    ("DOCUMENT INTELLIGENCE", "BLUE", ["Reading documents, scans and", "forms into clean, usable data."]),
    ("COMPUTER VISION", "ORANGE", ["Vision models built for the", "images the real world produces."]),
    ("MACHINE LEARNING & NLP", "TEAL", ["Models for prediction,", "classification and language."]),
    ("DATA ENGINEERING", "AMBER", ["Pipelines that collect, clean", "and connect data at scale."]),
    ("AI EVALUATION", "PINK", ["Benchmarks and tests that show", "when a model is ready to ship."]),
]
DELIVERY = [
    ("01", "FRAME", "BLUE", ["Clear goal,", "clear target."]),
    ("02", "DATA", "TEAL", ["Real data,", "made ready."]),
    ("03", "MODEL", "VIOLET", ["The right model", "for the job."]),
    ("04", "INTEGRATE", "ORANGE", ["Fits the systems", "already in place."]),
    ("05", "SHIP", "AMBER", ["Live, monitored,", "supported."]),
    ("06", "MEASURE", "PINK", ["Evaluate, learn,", "improve."]),
]
WORK = [  # private repositories: cards without links, never a company or client name
    {"slug": "travel-booking-agents", "name": "Travel Booking Agents", "language": "Python", "repos": 1,
     "description": "A team of AI agents that handles bookings, search and support.", "topics": ["multi-agent", "llm"]},
    {"slug": "travel-docparser-ai", "name": "Travel DocParser AI", "language": "Python", "repos": 1,
     "description": "Turns travel documents into clean, structured data.", "topics": ["document-ai", "ocr"]},
    {"slug": "agentic-travel-backend", "name": "Agentic Travel Backend", "language": "Python", "repos": 1,
     "description": "An agent platform with built-in tools, logging and evaluation.", "topics": ["agents", "evaluation"]},
    {"slug": "agentic-price-aggregator", "name": "Agentic Price Aggregator", "language": "Python", "repos": 1,
     "description": "Compares prices across many websites with smart automation.", "topics": ["automation", "llm-agents"]},
    {"slug": "platform-infrastructure", "name": "Platform Infrastructure", "language": "Dockerfile", "repos": 1,
     "description": "The shared environment that services run on, from laptop to production.", "topics": ["devops", "docker"]},
    {"slug": "evaluation-suites", "name": "Scientific Evaluation Suites", "language": "Python", "repos": 2,
     "description": "Expert test suites that measure AI agents on scientific work.", "topics": ["ai-evaluation", "benchmarks"]},
]
DESC_OVERRIDE = {  # short, general lines for public repositories
    "reduction-bench": "A benchmark that tests AI agents on real scientific and engineering work.",
    "Mosalehchatbot": "A multi-chat AI assistant with image understanding.",
}
TOOLS = [
    ("LANGUAGES", "BLUE", ["Python", "SQL", "JavaScript", "C++", "Java", "C#"]),
    ("AI / ML", "VIOLET", ["PyTorch", "TensorFlow", "scikit-learn", "YOLO", "OCR", "LLM / VLM"]),
    ("AGENTS & APIS", "ORANGE", ["MCP", "GraphQL", "REST", "Flask", "Streamlit", "n8n"]),
    ("DATA & DELIVERY", "TEAL", ["pandas", "Selenium", "MySQL", "Docker", "Git", "GitHub Actions"]),
]
KAGGLE_WINS = 2  # 1st places listed on the CV (2021, 2024)


# ------------------------------------------------------------------ data
def fetch(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-refresh", "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and url.startswith("https://api.github.com"):
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8")
    return body if raw else json.loads(body)


def public_projects():
    out = []
    for r in fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"):
        if r["fork"] or r["private"] or r.get("archived") or r["size"] == 0 or r["name"] in HIDE:
            continue
        out.append({"name": r["name"], "url": r["html_url"], "description": (r.get("description") or "").strip(),
                    "language": r.get("language") or "", "stars": r.get("stargazers_count", 0),
                    "topics": (r.get("topics") or [])[:3], "pushed": (r.get("pushed_at") or "")[:10]})
    out.sort(key=lambda p: (p["stars"], p["pushed"]), reverse=True)
    return out[:MAX_CARDS]


def flagship_counts():
    tree = fetch(f"https://api.github.com/repos/{USER}/{FLAGSHIP}/git/trees/main?recursive=1")
    fields, cases = {}, 0
    for e in tree["tree"]:
        m = re.fullmatch(r"tasks/([^/]+)/([^/]+)/[^/]+/task\.toml", e["path"])
        if e["type"] == "blob" and m:
            fields[f"{m.group(1)}/{m.group(2)}"] = fields.get(f"{m.group(1)}/{m.group(2)}", 0) + 1
        elif e["type"] == "tree" and re.fullmatch(r"tasks/[^/]+/[^/]+/[^/]+/tests/[^/]+/[^/]+", e["path"]):
            cases += 1
    readme = fetch(f"https://raw.githubusercontent.com/{USER}/{FLAGSHIP}/main/README.md", raw=True)
    hours = re.search(r"about \*\*([\d,]+)\*\* hours", readme)
    repo = fetch(f"https://api.github.com/repos/{USER}/{FLAGSHIP}")
    return {"tasks": sum(fields.values()), "fields": fields, "cases": cases, "stars": repo.get("stargazers_count", 0),
            "hours": int(hours.group(1).replace(",", "")) if hours else None, "url": repo["html_url"]}


# ------------------------------------------------------------------ drawing helpers
def esc(s):
    return html.escape(str(s), quote=True)


def svg(w, h, title, desc, body, style=""):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="title desc">\n  <title id="title">{esc(title)}</title>\n'
            f'  <desc id="desc">{esc(desc)}</desc>\n{style}{body}\n</svg>\n')


def panel(T, w, h, rid, rx=22):
    return (f'  <defs>\n    <linearGradient id="{rid}-bg" x1="0" y1="0" x2="1" y2="1">\n'
            f'      <stop offset="0" stop-color="{T["BG0"]}"/><stop offset="1" stop-color="{T["BG1"]}"/>\n    </linearGradient>\n'
            f'    <pattern id="{rid}-grid" width="40" height="40" patternUnits="userSpaceOnUse">\n'
            f'      <path d="M40 0H0V40" stroke="{T["GRID"]}" stroke-width="1" opacity="{T["GRIDO"]}"/>\n    </pattern>\n  </defs>\n'
            f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="url(#{rid}-bg)" stroke="{T["FRAME"]}"/>\n'
            f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="url(#{rid}-grid)"/>\n')


def text(x, y, s, size, fill, family=MONO, weight=400, spacing=0, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def card(T, x, y, w, h, col=None, side=False):
    s = f'  <rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="16" fill="{T["CARD"]}" stroke="{T["CARD_STROKE"]}"/>'
    if col:
        s += (f'\n  <rect x="{x:.1f}" y="{y}" width="5" height="{h}" rx="2.5" fill="{col}"/>' if side else
              f'\n  <rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="4" rx="2" fill="{col}"/>')
    return s


# ------------------------------------------------------------------ hero (always dark: it is the banner)
HERO_MOTION = """  <style>
    .orbit { transform-box: fill-box; transform-origin: center; animation: orbit 24s linear infinite; }
    .orbit.rev { animation-direction: reverse; animation-duration: 36s; }
    .signal { stroke-dasharray: 6 9; animation: signal 2.4s linear infinite; }
    .pulse { animation: pulse 2.6s ease-in-out infinite; }
    .wave { transform-box: fill-box; transform-origin: center; animation: wave 4.8s cubic-bezier(.16,1,.3,1) infinite; }
    .wave.d { animation-delay: 2.4s; }
    .check { stroke-dasharray: 60; stroke-dashoffset: 60; animation: check 5s cubic-bezier(.16,1,.3,1) infinite; }
    .chip { animation: chip 8s cubic-bezier(.16,1,.3,1) infinite; }
    .c2 { animation-delay: 2s; } .c3 { animation-delay: 4s; } .c4 { animation-delay: 6s; }
    .rise { opacity: .3; animation: rise .9s cubic-bezier(.16,1,.3,1) forwards; }
    .r1 { animation-delay: .1s; } .r2 { animation-delay: .22s; } .r3 { animation-delay: .34s; } .r4 { animation-delay: .5s; } .r5 { animation-delay: .66s; }
    .trace { stroke-dasharray: 120 2600; animation: trace 12s linear infinite; }
    .scan { animation: scan 6s cubic-bezier(.76,0,.24,1) infinite; }
    @keyframes orbit { to { transform: rotate(360deg); } }
    @keyframes signal { to { stroke-dashoffset: -30; } }
    @keyframes pulse { 0%, 100% { opacity: .45; } 50% { opacity: 1; } }
    @keyframes wave { 0% { opacity: .5; transform: scale(.7); } 75%, 100% { opacity: 0; transform: scale(1.5); } }
    @keyframes check { 0%, 12% { stroke-dashoffset: 60; opacity: .3; } 32%, 84% { stroke-dashoffset: 0; opacity: 1; } 100% { stroke-dashoffset: 0; opacity: .4; } }
    @keyframes chip { 0%, 22%, 100% { opacity: .55; } 6%, 15% { opacity: 1; } }
    @keyframes rise { from { opacity: .3; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes trace { to { stroke-dashoffset: -2720; } }
    @keyframes scan { 0% { stroke-dashoffset: 520; opacity: 0; } 15% { opacity: 1; } 70% { stroke-dashoffset: 0; opacity: 1; } 100% { stroke-dashoffset: 0; opacity: 0; } }
    @media (prefers-reduced-motion: reduce) {
      .orbit, .signal, .pulse, .wave, .check, .chip, .rise, .trace, .scan { animation: none; opacity: 1; transform: none; stroke-dashoffset: 0; }
      .wave { display: none; }
    }
  </style>
"""


def hero():
    T = DARK; W, H = 1200, 420
    b = [panel(T, W, H, "h")]
    b.append('  <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#2DD4BF" stop-opacity=".20"/>'
             '<stop offset="1" stop-color="#2DD4BF" stop-opacity="0"/></radialGradient>')
    b.append('  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F0883E"/>'
             '<stop offset="1" stop-color="#FBBF24"/></linearGradient>')
    b.append(f'  <rect class="trace" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" stroke="{T["TEAL"]}" stroke-width="1.6" opacity=".7"/>')
    b.append('  <path d="M560 1 H640" stroke="#2DD4BF" stroke-width="2" opacity=".8"/>')
    b.append("  " + text(64, 88, "MOHAMED SALEH  /  AI ENGINEER", 12.5, T["TEAL"], MONO, 700, 3, extra=' class="rise r1"'))
    b.append("  " + text(64, 158, "I build AI systems", 50, T["INK"], SANS, 800, -0.5, extra=' class="rise r2"'))
    b.append("  " + text(64, 216, "that hold up in", 50, T["INK"], SANS, 800, -0.5, extra=' class="rise r3"'))
    b.append("  " + text(64, 274, "production.", 50, "url(#accent)", SANS, 800, -0.5, extra=' class="rise r4"'))
    b.append("  " + text(64, 318, "From raw data to deployed models and agents, and the evaluation that proves they work.",
                         16.5, T["MUTED"], SANS, extra=' class="rise r5"'))
    b.append(f'  <path d="M64 344 H700" stroke="#1E2A3D" stroke-width="1"/>')
    b.append(f'  <circle class="pulse" cx="70" cy="368" r="4.5" fill="{T["TEAL"]}"/>')
    b.append("  " + text(84, 372, "AGENTIC AI  ·  DOCUMENT INTELLIGENCE  ·  COMPUTER VISION  ·  MACHINE LEARNING  ·  NLP  ·  AI EVALUATION",
                         11, T["SOFT"], MONO, 600, 1))
    b.append("  " + text(84, 394, "FRAME  →  DATA  →  MODEL  →  INTEGRATE  →  SHIP  →  MEASURE", 10, T["DIM"], MONO, 400, 1.2))
    cx, cy = 930, 200
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="190" fill="url(#glow)"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="150" stroke="#1E3A5F" stroke-width="1" stroke-dasharray="2 7"/>')
    b.append(f'  <g class="orbit"><circle cx="{cx}" cy="{cy}" r="118" stroke="{T["TEAL"]}" stroke-width="1.4" stroke-dasharray="40 22 4 22" opacity=".55"/></g>')
    b.append(f'  <g class="orbit rev"><circle cx="{cx}" cy="{cy}" r="96" stroke="{T["VIOLET"]}" stroke-width="1" stroke-dasharray="3 9" opacity=".6"/></g>')
    b.append(f'  <circle class="wave" cx="{cx}" cy="{cy}" r="66" stroke="{T["TEAL"]}" stroke-width="1.5"/>')
    b.append(f'  <circle class="wave d" cx="{cx}" cy="{cy}" r="66" stroke="{T["TEAL"]}" stroke-width="1.5"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="62" fill="#0A1C26" stroke="{T["TEAL"]}" stroke-width="2"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="46" stroke="{T["TEAL"]}" stroke-width="1" opacity=".45"/>')
    b.append(f'  <path class="scan" d="M{cx - 42} {cy - 22} l7 -8 l6 16 l6 -20 l6 22 l6 -16 l6 8" stroke="{T["BLUE"]}" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="520" opacity=".0"/>')
    b.append(f'  <path class="check" d="M{cx - 20} {cy + 4} l14 14 l28 -30" stroke="{T["INK"]}" stroke-width="5" stroke-linecap="round" '
             'stroke-linejoin="round"/>')
    for lab, col, x, y, c in [("PERCEIVE", T["BLUE"], cx - 215, cy - 118, "c1"), ("REASON", T["VIOLET"], cx + 125, cy - 118, "c2"),
                              ("VERIFY", T["TEAL"], cx - 205, cy + 112, "c4"), ("ACT", T["ORANGE"], cx + 135, cy + 112, "c3")]:
        w = int(len(lab) * 8.2 + 34); mx, my = x + w / 2, y + 14
        b.append(f'  <path class="signal" d="M{mx:.0f} {my:.0f} L{cx + (mx - cx) * 0.47:.0f} {cy + (my - cy) * 0.47:.0f}" '
                 f'stroke="{col}" stroke-width="1.4" opacity=".75"/>')
        b.append(f'  <g class="chip {c}"><rect x="{x}" y="{y}" width="{w}" height="28" rx="14" fill="{T["CARD"]}" stroke="{col}" '
                 f'stroke-width="1.2"/><circle cx="{x + 15}" cy="{y + 14}" r="3.5" fill="{col}"/>'
                 + text(x + 26, y + 18, lab, 10.5, col, MONO, 700, 1.6) + "</g>")
    return svg(W, H, "Mohamed Saleh: I build AI systems that hold up in production",
               "AI engineer working across agentic AI, document intelligence, computer vision, machine learning, NLP and AI evaluation.",
               "\n".join(b), HERO_MOTION)


# ------------------------------------------------------------------ rotating roles line
def roles(T):
    W, H, n, step = 1000, 48, len(ROLES), 3
    total = n * step
    css = ["  <style>",
           f"    .role {{ opacity: 0; animation: role {total}s cubic-bezier(.16,1,.3,1) infinite; }}",
           f"    @keyframes role {{ 0% {{ opacity: 0; transform: translateY(10px); }} 3% {{ opacity: 1; transform: translateY(0); }} "
           f"{100 / n - 3:.1f}% {{ opacity: 1; transform: translateY(0); }} {100 / n:.1f}%, 100% {{ opacity: 0; transform: translateY(-10px); }} }}",
           "    .caret { animation: caret 1s steps(1) infinite; }  @keyframes caret { 50% { opacity: 0; } }",
           "    @media (prefers-reduced-motion: reduce) { .role { animation: none; } .role.r0 { opacity: 1; } .caret { animation: none; } }",
           "  </style>"]
    b = ["  " + text(W / 2 - 10, 31, "AI ENGINEER  /", 15, T["TEAL"], MONO, 700, 2.4, "end")]
    for i, r in enumerate(ROLES):
        b.append(f'  <g class="role r{i}" style="animation-delay:{i * step - 0.5}s">' + text(W / 2 + 6, 32, r, 22, T["INK"], SANS, 700) + "</g>")
    b.append(f'  <rect class="caret" x="{W / 2 + 6 + max(len(r) for r in ROLES) * 11.6:.0f}" y="12" width="3" height="26" rx="1.5" fill="{T["ORANGE"]}" opacity="0"/>')
    return svg(W, H, "What I do", " / ".join(ROLES), "\n".join(b), "\n".join(css) + "\n")


# ------------------------------------------------------------------ at a glance
def glance(T, fl, n_projects):
    tiles = [(f"{fl['tasks']:,}", "BENCHMARK TASKS", "ORANGE"), (f"{fl['cases']:,}", "SEALED TEST CASES", "TEAL"),
             (str(len(fl["fields"])), "SCIENTIFIC FIELDS", "BLUE"), (str(n_projects), "AI PROJECTS ON GITHUB", "VIOLET"),
             (f"{KAGGLE_WINS}×", "KAGGLE 1ST PLACE", "AMBER")]
    W, H, gap = 1200, 136, 14
    tw = (W - gap * (len(tiles) - 1)) / len(tiles)
    b = []
    for i, (n, lab, c) in enumerate(tiles):
        x = i * (tw + gap)
        b.append(card(T, x + .5, 1, tw - 1, H - 2, T[c]))
        b.append("  " + text(f"{x + tw / 2:.1f}", 74, n, 42, T["INK"], MONO, 700, 0, "middle"))
        b.append("  " + text(f"{x + tw / 2:.1f}", 106, lab, 10.5, T["MUTED"], MONO, 600, 1.2, "middle"))
    return svg(W, H, "At a glance", ", ".join(f"{n} {l.lower()}" for n, l, _ in tiles), "\n".join(b))


# ------------------------------------------------------------------ capabilities, delivery, toolbox
def capabilities(T):
    cols, gap, ch = 3, 20, 140
    rows = (len(CAPABILITIES) + cols - 1) // cols
    W, H = 1200, 72 + rows * ch + (rows - 1) * gap
    b = [panel(T, W, H, "c")]
    cw = (W - 72 - gap * (cols - 1)) / cols
    for i, (t, c, lines) in enumerate(CAPABILITIES):
        x = 36 + (i % cols) * (cw + gap); y = 36 + (i // cols) * (ch + gap); col = T[c]
        b.append(card(T, x, y, cw, ch, col))
        b.append(f'  <circle cx="{x + 32:.1f}" cy="{y + 42}" r="10" fill="{col}" fill-opacity=".16" stroke="{col}"/>')
        b.append(f'  <circle cx="{x + 32:.1f}" cy="{y + 42}" r="3.2" fill="{col}"/>')
        b.append("  " + text(f"{x + 54:.1f}", y + 47, t, 13.5, T["INK"], MONO, 700, 1.2))
        for k, ln in enumerate(lines):
            b.append("  " + text(f"{x + 24:.1f}", y + 92 + k * 23, ln, 14.5, T["MUTED"], SANS))
    return svg(W, H, "What I build", "; ".join(t.title() for t, _, _ in CAPABILITIES), "\n".join(b))


def delivery(T):
    W, H, n, gap = 1200, 212, len(DELIVERY), 16
    b = [panel(T, W, H, "d")]
    cw = (W - 72 - gap * (n - 1)) / n
    for i, (num, t, c, lines) in enumerate(DELIVERY):
        x = 36 + i * (cw + gap); col = T[c]
        b.append(card(T, x, 36, cw, 140, col, side=True))
        b.append("  " + text(f"{x + 20:.1f}", 66, num, 12.5, col, MONO, 700, 1))
        b.append("  " + text(f"{x + 20:.1f}", 94, t, 14, T["INK"], MONO, 700, 0.8))
        for k, ln in enumerate(lines):
            b.append("  " + text(f"{x + 20:.1f}", 128 + k * 21, ln, 12.5, T["MUTED"], SANS))
        if i < n - 1:
            ax = x + cw + 2
            b.append(f'  <path d="M{ax:.1f} 106 h8" stroke="{T["ARROW"]}" stroke-width="2"/><path d="M{ax + 8:.1f} 102 l5 4 l-5 4z" fill="{T["ARROW"]}"/>')
    return svg(W, H, "How I deliver", " then ".join(t.lower() for _, t, _, _ in DELIVERY), "\n".join(b))


def toolbox(T):
    W, H = 1200, 232
    b = [panel(T, W, H, "x")]
    cw = (W - 72 - 3 * 20) / 4
    for i, (g, c, items) in enumerate(TOOLS):
        x = 36 + i * (cw + 20); col = T[c]
        b.append("  " + text(f"{x:.1f}", 56, g, 11.5, col, MONO, 700, 2))
        px, py = x, 76
        for it in items:
            w = len(it) * 8.4 + 30
            if px + w > x + cw:
                px, py = x, py + 42
            b.append(f'  <rect x="{px:.1f}" y="{py}" width="{w:.1f}" height="32" rx="16" fill="{T["CARD"]}" stroke="{col}" stroke-opacity=".6"/>')
            b.append("  " + text(f"{px + 15:.1f}", py + 21, it, 13, T["INK"], SANS, 600))
            px += w + 10
    return svg(W, H, "Toolbox", "; ".join(f"{g.title()}: {', '.join(i)}" for g, _, i in TOOLS), "\n".join(b))


# ------------------------------------------------------------------ flagship
def flagship(T, fl):
    W, H = 1200, 320
    b = [panel(T, W, H, "f")]
    b.append(f'  <rect x="56" y=".5" width="120" height="3" rx="1.5" fill="{T["ORANGE"]}"/>')
    b.append("  " + text(56, 64, "FLAGSHIP  ·  OPEN-SOURCE BENCHMARK", 12, T["ORANGE"], MONO, 700, 2.8))
    b.append("  " + text(56, 114, "Reduction-Bench", 44, T["INK"], SANS, 800, -0.5))
    for i, ln in enumerate(["A benchmark for AI agents on real scientific and engineering",
                            "work: each task hands the agent raw instrument records and",
                            "scores the program it writes on sealed cases it never saw."]):
        b.append("  " + text(56, 154 + i * 25, ln, 16.5, T["MUTED"], SANS))
    x = 56
    for lab in ["HARBOR TASK FORMAT", "APACHE-2.0", f"★ {fl['stars']} STARS", "OPEN SOURCE"]:
        w = len(lab) * 7.6 + 26
        b.append(f'  <rect x="{x:.1f}" y="250" width="{w:.1f}" height="28" rx="14" fill="{T["CARD"]}" stroke="{T["CHIP_STROKE"]}"/>')
        b.append("  " + text(f"{x + 13:.1f}", 268.5, lab, 10.5, T["SOFT"], MONO, 700, 1.2))
        x += w + 10
    tiles = [(f"{fl['tasks']:,}", "TASKS", "ORANGE"), (f"{fl['cases']:,}", "SEALED CASES", "TEAL"),
             (str(len(fl["fields"])), "FIELDS", "BLUE"), (f"{fl['hours']:,}" if fl["hours"] else "—", "EXPERT HOURS", "VIOLET")]
    for i, (n, lab, c) in enumerate(tiles):
        tx, ty = 690 + (i % 2) * 238, 40 + (i // 2) * 104
        b.append(card(T, tx, ty, 222, 90, T[c]))
        b.append("  " + text(tx + 22, ty + 54, n, 34, T["INK"], MONO, 700))
        b.append("  " + text(tx + 22, ty + 76, lab, 10.5, T["MUTED"], MONO, 600, 1.8))
    doms = {}
    for k, v in fl["fields"].items():
        doms[k.split("/")[0]] = doms.get(k.split("/")[0], 0) + v
    order = [d for d in DOMAIN if d in doms]; x = 690.0
    for d in order:
        w = 460 * doms[d] / fl["tasks"]
        b.append(f'  <rect x="{x:.1f}" y="256" width="{max(w - 3, 3):.1f}" height="8" rx="4" fill="{T[DOMAIN[d][1]]}"/>')
        x += w
    b.append("  " + text(690, 284, "  ·  ".join(f"{DOMAIN[d][0].upper()} {doms[d]}" for d in order), 10, T["DIM"], MONO, 600, 1))
    return svg(W, H, "Reduction-Bench", f"{fl['tasks']} tasks, {fl['cases']} sealed cases, {len(fl['fields'])} fields.", "\n".join(b))


# ------------------------------------------------------------------ project cards
def project_card(T, p, kicker="PROJECT", private=False):
    W, H = 600, 210
    b = [panel(T, W, H, "p", 18)]
    col = LANG_COLOR.get(p["language"], "#8B949E")
    b.append(f'  <rect x=".5" y=".5" width="{W - 1}" height="4" rx="2" fill="{col}"/>')
    b.append("  " + text(32, 46, kicker, 10.5, T["AMBER"] if private else T["TEAL"], MONO, 700, 2.4))
    if private:
        b.append(f'  <rect x="{W - 54}" y="38" width="18" height="14" rx="3" stroke="{T["MUTED"]}" stroke-width="1.8" fill="none"/>'
                 f'<path d="M{W - 50} 38 v-4 a5 5 0 0 1 10 0 v4" stroke="{T["MUTED"]}" stroke-width="1.8" fill="none"/>')
    else:
        b.append(f'  <path d="M{W - 50} 36 l8 8 l-8 8 M{W - 42} 44 h-16" stroke="{T["MUTED"]}" stroke-width="1.8" stroke-linecap="round" '
                 'stroke-linejoin="round" fill="none"/>')
    b.append("  " + text(32, 84, p["name"], 24, T["INK"], SANS, 800, -0.2))
    desc = DESC_OVERRIDE.get(p["name"]) or p["description"] or "Source code, setup and usage notes in the repository."
    head = re.match(r"([^:]{2,40}):\s+(.+)", desc)
    if head and re.sub(r"[^a-z0-9]", "", head.group(1).lower()) == re.sub(r"[^a-z0-9]", "", p["name"].lower()):
        desc = head.group(2)[:1].upper() + head.group(2)[1:]
    for k, ln in enumerate(textwrap.wrap(desc, 62)[:3]):
        b.append("  " + text(32, 116 + k * 22, ln, 14.5, T["MUTED"], SANS))
    x = 32
    if p["language"]:
        b.append(f'  <circle cx="{x + 6}" cy="186" r="6" fill="{col}"/>')
        b.append("  " + text(x + 18, 191, p["language"], 13, T["SOFT"], SANS, 600))
        x += 18 + len(p["language"]) * 7.4 + 22
    if not private:
        b.append("  " + text(f"{x:.0f}", 191, f"★ {p['stars']}", 13, T["SOFT"], SANS, 600))
        x += 52
    for t in p["topics"]:
        w = len(t) * 6.9 + 22
        if x + w > W - 28:
            break
        b.append(f'  <rect x="{x:.1f}" y="174" width="{w:.1f}" height="24" rx="12" fill="{T["CARD"]}" stroke="{T["CHIP_STROKE"]}"/>')
        b.append("  " + text(f"{x + 11:.1f}", 190, t, 11, T["MUTED"], MONO, 600))
        x += w + 8
    return svg(W, H, p["name"], desc, "\n".join(b))


def badge(label, msg, col):
    lw, mw = int(len(label) * 8.6 + 28), int(len(msg) * 8.6 + 28)
    w = lw + mw
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="30" role="img" aria-label="{esc(label)}: {esc(msg)}">'
            f'<title>{esc(label)}: {esc(msg)}</title>'
            f'<rect width="{w}" height="30" rx="4" fill="#0B1220"/><rect width="{lw}" height="30" rx="4" fill="{col}"/>'
            f'<rect x="{lw - 4}" width="4" height="30" fill="{col}"/>'
            f'<text x="{lw / 2:.1f}" y="19.5" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11" '
            f'font-weight="700" letter-spacing="1" fill="#fff">{esc(label)}</text>'
            f'<text x="{lw + mw / 2:.1f}" y="19.5" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
            f'font-size="11" font-weight="700" letter-spacing="1" fill="#fff">{esc(msg)}</text></svg>\n')


# ------------------------------------------------------------------ README
def pic(path, stamp, alt, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/{path}-dark.svg?v={stamp}" />'
            f'<img src="./assets/{path}-light.svg?v={stamp}" width="{width}" alt="{esc(alt)}" /></picture>')


def readme(stamp, fl, ps):
    work = "\n".join(f'  {pic("work/" + w["slug"], stamp, w["name"] + ": " + w["description"], "49%")}' for w in WORK)
    if ps:
        projects = "\n".join(f'  <a href="{p["url"]}">{pic("projects/" + p["name"], stamp, p["name"] + ": " + (p["description"] or "project"), "49%")}</a>'
                             for p in ps)
    else:
        projects = "  <sub>More open-source projects are on their way.</sub>"
    return f"""<div align="center">

<img src="./assets/hero.svg?v={stamp}" width="100%" alt="Mohamed Saleh, AI engineer: I build AI systems that hold up in production. From raw data to deployed models and agents, and the evaluation that proves they work." />

<br />

<a href="{LINKEDIN}"><img src="./assets/badge-linkedin.svg?v={stamp}" height="30" alt="LinkedIn: connect" /></a>
<a href="#projects"><img src="./assets/badge-projects.svg?v={stamp}" height="30" alt="Projects: explore" /></a>
<a href="#lets-connect"><img src="./assets/badge-kaggle.svg?v={stamp}" height="30" alt="Kaggle: 2x 1st place" /></a>
<a href="https://github.com/{USER}?tab=followers"><img src="./assets/badge-follow.svg?v={stamp}" height="30" alt="Follow on GitHub" /></a>

<br />
<br />

{pic("roles", stamp, "AI engineer: " + ", ".join(ROLES), "760")}

<br />

<a href="#about"><b>About</b></a> &nbsp;&middot;&nbsp;
<a href="#what-i-build"><b>What I build</b></a> &nbsp;&middot;&nbsp;
<a href="#selected-work"><b>Selected work</b></a> &nbsp;&middot;&nbsp;
<a href="#projects"><b>Projects</b></a> &nbsp;&middot;&nbsp;
<a href="#toolbox"><b>Toolbox</b></a> &nbsp;&middot;&nbsp;
<a href="#lets-connect"><b>Contact</b></a>

</div>

## About

**I build AI systems that hold up in production.**

From the first dataset to the deployed service, I design, build and ship complete AI systems, and I measure them before they reach users.

## What I build

{pic("capabilities", stamp, "Agentic AI systems, document intelligence, computer vision, machine learning and NLP, data engineering, AI evaluation")}

## How I deliver

{pic("delivery", stamp, "Frame, data, model, integrate, ship, measure")}

## Selected work

<sub>Private repositories. Walkthroughs available on request.</sub>

<p align="center">
{work}
</p>

## Projects

<p align="center">
{projects}
</p>

## Toolbox

{pic("toolbox", stamp, "Languages, AI and ML frameworks, agents and APIs, data and delivery tools")}

## How I work

- **Production first**: built to run for real users.
- **Measured**: every system has a clear target and a test.
- **End to end**: data, models, integration and deployment.
- **Cost-aware**: efficient by design.
- **Private by default**: secrets and personal data stay protected.

## Let's connect

<div align="center">

**Open to conversations about AI engineering roles, collaborations and ambitious AI products.**

<a href="{LINKEDIN}"><img src="./assets/badge-linkedin.svg?v={stamp}" height="30" alt="LinkedIn: connect" /></a>
<a href="https://github.com/{USER}?tab=repositories"><img src="./assets/badge-repos.svg?v={stamp}" height="30" alt="Repositories: explore" /></a>

<br />
<br />

<sub>This page adapts to your GitHub theme and refreshes its project cards daily.</sub>

</div>
"""


def main():
    old = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else None
    try:
        ps = public_projects()
    except Exception as e:  # keep the last good page when GitHub cannot be reached
        print("fetch failed:", e)
        if old is None:
            sys.exit(1)
        return
    fl = None
    others = ps
    live = {"projects": ps}
    if old and "--force" not in sys.argv and {k: old.get(k) for k in live} == live:
        print("live data unchanged; nothing rewritten")
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    for sub in ("", "projects", "work"):
        (ASSETS / sub).mkdir(parents=True, exist_ok=True)
        for f in (ASSETS / sub).glob("*.svg"):
            f.unlink()
    DATA.parent.mkdir(exist_ok=True)
    files = {"hero.svg": hero(),
             "badge-linkedin.svg": badge("LINKEDIN", "CONNECT", "#0A66C2"),
             "badge-projects.svg": badge("PROJECTS", "EXPLORE", "#D9622B"),
             "badge-kaggle.svg": badge("KAGGLE", f"{KAGGLE_WINS}× 1ST PLACE", "#1F8FC9"),
             "badge-repos.svg": badge("REPOSITORIES", "EXPLORE", "#0F9F8F"),
             "badge-follow.svg": badge("GITHUB", "FOLLOW", "#7C3AED")}
    for th, T in THEMES.items():
        files[f"roles-{th}.svg"] = roles(T)
        files[f"capabilities-{th}.svg"] = capabilities(T)
        files[f"delivery-{th}.svg"] = delivery(T)
        files[f"toolbox-{th}.svg"] = toolbox(T)
        for w in WORK:
            files[f"work/{w['slug']}-{th}.svg"] = project_card(T, w, "PRIVATE REPOSITORY", True)
        for p in others:
            files[f"projects/{p['name']}-{th}.svg"] = project_card(T, p)
    for name, content in files.items():
        (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    README.write_text(readme(stamp, fl, others), encoding="utf-8", newline="\n")
    DATA.write_text(json.dumps({**live, "updated": stamp}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("wrote", len(files), "assets; projects", [p["name"] for p in others])


if __name__ == "__main__":
    main()
