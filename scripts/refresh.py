#!/usr/bin/env python3
"""Rebuild the profile's SVG assets and its Projects section.

The page itself is general (identity, capabilities, delivery loop, toolbox). Projects are read live from the
public repositories of the account: every non-empty, non-fork public repository except those in HIDE gets a
card under assets/projects/, and the block between the projects markers in README.md is rewritten. Standard
library only, so it runs unchanged on a GitHub Actions runner. Nothing is rewritten when the project list is
unchanged; pass --force to redraw after editing the text below.
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
HIDE = {USER, "reduction-bench"}          # repositories never shown as project cards
MAX_CARDS = 8
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "stats.json"
README = ROOT / "README.md"

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
INK, MUTED, DIM, RULE = "#F8FAFC", "#94A3B8", "#64748B", "#1E2A3D"
BLUE, TEAL, VIOLET, ORANGE, AMBER, PINK = "#4D7CFE", "#2DD4BF", "#9B7CFF", "#F0883E", "#FBBF24", "#F472B6"
LANG_COLOR = {"Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "JavaScript": "#F1E05A", "TypeScript": "#3178C6",
              "C++": "#F34B7D", "C#": "#178600", "Java": "#B07219", "HTML": "#E34C26", "CSS": "#663399",
              "Shell": "#89E051", "Go": "#00ADD8", "Rust": "#DEA584", "Scala": "#C22D40", "Dockerfile": "#2496ED"}

CAPABILITIES = [
    ("AGENTIC AI SYSTEMS", VIOLET, ["Multi-agent orchestration, planning,", "memory and tool use, wired to real", "APIs through MCP, GraphQL and REST."]),
    ("DOCUMENT INTELLIGENCE", BLUE, ["OCR, layout and field extraction from", "scans, IDs and mixed PDFs, with", "enrichment that grounds downstream AI."]),
    ("COMPUTER VISION", ORANGE, ["Detection, recognition and image", "restoration models trained for the", "conditions real cameras produce."]),
    ("MACHINE LEARNING & NLP", TEAL, ["From classical ML to deep learning:", "classification, prediction, language", "pipelines and model evaluation."]),
    ("DATA ENGINEERING", AMBER, ["Large-scale entity resolution,", "deduplication, acquisition and", "automated pipelines that stay clean."]),
    ("AI EVALUATION", PINK, ["Benchmarks, expert test sets and", "LLM and VLM evaluation that show", "whether a model is ready to ship."]),
]
DELIVERY = [
    ("01", "FRAME", BLUE, ["Turn a need into a", "measurable target", "before any code."]),
    ("02", "DATA", TEAL, ["Collect, clean and", "label the data the", "model will really see."]),
    ("03", "MODEL", VIOLET, ["Pick, train or", "orchestrate the right", "models for the job."]),
    ("04", "INTEGRATE", ORANGE, ["Wrap models in APIs,", "agents and tools that", "fit existing systems."]),
    ("05", "SHIP", AMBER, ["Deploy, monitor and", "support real users", "in production."]),
    ("06", "MEASURE", PINK, ["Evaluate against the", "target, learn and", "iterate."]),
]
WORK = [  # private repositories: shown as cards without links, no company or client names
    {"slug": "travel-booking-agents", "name": "Travel Booking Agents", "language": "Python",
     "description": "Router and specialist LLM agents for B2B travel over MCP tools, with role permissions, graph memory and evals.",
     "topics": ["multi-agent", "mcp", "graphql"]},
    {"slug": "travel-docparser-ai", "name": "Travel DocParser AI", "language": "Python",
     "description": "Turns PDFs and photos of travel documents into validated, enriched JSON with VLM OCR and a LangGraph agent.",
     "topics": ["document-ai", "langgraph", "fastapi"]},
    {"slug": "agentic-travel-backend", "name": "Agentic Travel Backend", "language": "Python",
     "description": "Agent harness with an orchestrator, an MCP tool service, per-agent models, run logging and an evaluation library.",
     "topics": ["agent-harness", "mcp", "evals"]},
    {"slug": "agentic-price-aggregator", "name": "Agentic Price Aggregator", "language": "Python",
     "description": "Multi-site price aggregation: cache, then self-healing browser replay, then LLM browser agents only when needed.",
     "topics": ["llm-agents", "playwright", "scraping"]},
    {"slug": "platform-infrastructure", "name": "Platform Infrastructure", "language": "Dockerfile",
     "description": "One-command local platform that mirrors production: gateway, queues, database, object storage and SSO.",
     "topics": ["docker", "traefik", "keycloak"]},
]
TOOLS = [
    ("LANGUAGES", BLUE, ["Python", "SQL", "JavaScript", "C++", "Java", "C#"]),
    ("AI / ML", VIOLET, ["PyTorch", "TensorFlow", "scikit-learn", "YOLO", "OCR", "LLM / VLM"]),
    ("AGENTS & APIS", ORANGE, ["MCP", "GraphQL", "REST", "Flask", "Streamlit", "n8n"]),
    ("DATA & DELIVERY", TEAL, ["pandas", "Selenium", "MySQL", "Docker", "Git", "GitHub Actions"]),
]


# ------------------------------------------------------------------ data
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-refresh", "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def projects():
    repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
    out = []
    for r in repos:
        if r["fork"] or r["private"] or r.get("archived") or r["size"] == 0 or r["name"] in HIDE:
            continue
        out.append({"name": r["name"], "url": r["html_url"], "description": (r.get("description") or "").strip(),
                    "language": r.get("language") or "", "stars": r.get("stargazers_count", 0),
                    "topics": (r.get("topics") or [])[:3], "pushed": (r.get("pushed_at") or "")[:10]})
    out.sort(key=lambda p: (p["stars"], p["pushed"]), reverse=True)
    return out[:MAX_CARDS]


# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(str(s), quote=True)


def svg(w, h, title, desc, body, style=""):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="title desc">\n  <title id="title">{esc(title)}</title>\n'
            f'  <desc id="desc">{esc(desc)}</desc>\n{style}{body}\n</svg>\n')


def panel(w, h, rid, rx=22):
    return (f'  <defs>\n    <linearGradient id="{rid}-bg" x1="0" y1="0" x2="1" y2="1">\n'
            f'      <stop offset="0" stop-color="#07111E"/><stop offset="1" stop-color="#150C2B"/>\n    </linearGradient>\n'
            f'    <pattern id="{rid}-grid" width="40" height="40" patternUnits="userSpaceOnUse">\n'
            f'      <path d="M40 0H0V40" stroke="#1B2638" stroke-width="1" opacity=".55"/>\n    </pattern>\n  </defs>\n'
            f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="url(#{rid}-bg)" stroke="#23324A"/>\n'
            f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="url(#{rid}-grid)"/>\n')


def text(x, y, s, size, fill=INK, family=MONO, weight=400, spacing=0, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


MOTION = """  <style>
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


# ------------------------------------------------------------------ hero
def hero():
    W, H = 1200, 420
    b = [panel(W, H, "h")]
    b.append('  <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#2DD4BF" stop-opacity=".20"/>'
             '<stop offset="1" stop-color="#2DD4BF" stop-opacity="0"/></radialGradient>')
    b.append('  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F0883E"/>'
             '<stop offset="1" stop-color="#FBBF24"/></linearGradient>')
    b.append(f'  <rect class="trace" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" stroke="{TEAL}" stroke-width="1.6" opacity=".7"/>')
    b.append('  <path d="M560 1 H640" stroke="#2DD4BF" stroke-width="2" opacity=".8"/>')
    b.append("  " + text(64, 88, "MOHAMED SALEH  /  AI ENGINEER", 12.5, TEAL, MONO, 700, 3, extra=' class="rise r1"'))
    b.append("  " + text(64, 158, "I build AI systems", 50, INK, SANS, 800, -0.5, extra=' class="rise r2"'))
    b.append("  " + text(64, 216, "that hold up in", 50, INK, SANS, 800, -0.5, extra=' class="rise r3"'))
    b.append("  " + text(64, 274, "production.", 50, "url(#accent)", SANS, 800, -0.5, extra=' class="rise r4"'))
    b.append("  " + text(64, 318, "From raw data to deployed models and agents, and the evaluation that proves they work.",
                         16.5, MUTED, SANS, extra=' class="rise r5"'))
    b.append(f'  <path d="M64 344 H700" stroke="{RULE}" stroke-width="1"/>')
    b.append(f'  <circle class="pulse" cx="70" cy="368" r="4.5" fill="{TEAL}"/>')
    b.append("  " + text(84, 372, "AGENTIC AI  ·  DOCUMENT INTELLIGENCE  ·  COMPUTER VISION  ·  MACHINE LEARNING  ·  NLP  ·  AI EVALUATION",
                         11, "#CBD5E1", MONO, 600, 1))
    b.append("  " + text(84, 394, "FRAME  →  DATA  →  MODEL  →  INTEGRATE  →  SHIP  →  MEASURE", 10, DIM, MONO, 400, 1.2))
    cx, cy = 930, 200
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="190" fill="url(#glow)"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="150" stroke="#1E3A5F" stroke-width="1" stroke-dasharray="2 7"/>')
    b.append(f'  <g class="orbit"><circle cx="{cx}" cy="{cy}" r="118" stroke="{TEAL}" stroke-width="1.4" stroke-dasharray="40 22 4 22" opacity=".55"/></g>')
    b.append(f'  <g class="orbit rev"><circle cx="{cx}" cy="{cy}" r="96" stroke="{VIOLET}" stroke-width="1" stroke-dasharray="3 9" opacity=".6"/></g>')
    b.append(f'  <circle class="wave" cx="{cx}" cy="{cy}" r="66" stroke="{TEAL}" stroke-width="1.5"/>')
    b.append(f'  <circle class="wave d" cx="{cx}" cy="{cy}" r="66" stroke="{TEAL}" stroke-width="1.5"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="62" fill="#0A1C26" stroke="{TEAL}" stroke-width="2"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="46" stroke="{TEAL}" stroke-width="1" opacity=".45"/>')
    b.append(f'  <path class="scan" d="M{cx - 42} {cy - 22} l7 -8 l6 16 l6 -20 l6 22 l6 -16 l6 8" stroke="{BLUE}" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="520" opacity=".0"/>')
    b.append(f'  <path class="check" d="M{cx - 20} {cy + 4} l14 14 l28 -30" stroke="{INK}" stroke-width="5" stroke-linecap="round" '
             'stroke-linejoin="round"/>')
    chips = [("PERCEIVE", BLUE, cx - 215, cy - 118, "c1"), ("REASON", VIOLET, cx + 125, cy - 118, "c2"),
             ("VERIFY", TEAL, cx - 205, cy + 112, "c4"), ("ACT", ORANGE, cx + 135, cy + 112, "c3")]
    for lab, col, x, y, c in chips:
        w = int(len(lab) * 8.2 + 34)
        mx, my = x + w / 2, y + 14
        b.append(f'  <path class="signal" d="M{mx:.0f} {my:.0f} L{cx + (mx - cx) * 0.47:.0f} {cy + (my - cy) * 0.47:.0f}" '
                 f'stroke="{col}" stroke-width="1.4" opacity=".75"/>')
        b.append(f'  <g class="chip {c}"><rect x="{x}" y="{y}" width="{w}" height="28" rx="14" fill="#0B1220" stroke="{col}" '
                 f'stroke-width="1.2"/><circle cx="{x + 15}" cy="{y + 14}" r="3.5" fill="{col}"/>'
                 + text(x + 26, y + 18, lab, 10.5, col, MONO, 700, 1.6) + "</g>")
    return svg(W, H, "Mohamed Saleh: I build AI systems that hold up in production",
               "AI engineer working across agentic AI, document intelligence, computer vision, machine learning, NLP and AI evaluation.",
               "\n".join(b), MOTION)


# ------------------------------------------------------------------ capabilities (3 x 2)
def capabilities():
    cols, gap, ch = 3, 20, 178
    rows = (len(CAPABILITIES) + cols - 1) // cols
    W, H = 1200, 72 + rows * ch + (rows - 1) * gap
    b = [panel(W, H, "c")]
    cw = (W - 72 - gap * (cols - 1)) / cols
    for i, (t, col, lines) in enumerate(CAPABILITIES):
        x = 36 + (i % cols) * (cw + gap); y = 36 + (i // cols) * (ch + gap)
        b.append(f'  <rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="4" rx="2" fill="{col}"/>')
        b.append(f'  <circle cx="{x + 32:.1f}" cy="{y + 42}" r="10" fill="{col}" fill-opacity=".16" stroke="{col}"/>')
        b.append(f'  <circle cx="{x + 32:.1f}" cy="{y + 42}" r="3.2" fill="{col}"/>')
        b.append("  " + text(f"{x + 54:.1f}", y + 47, t, 13.5, INK, MONO, 700, 1.2))
        for k, ln in enumerate(lines):
            b.append("  " + text(f"{x + 24:.1f}", y + 92 + k * 23, ln, 14.5, MUTED, SANS))
    return svg(W, H, "What I build", "; ".join(t.title() for t, _, _ in CAPABILITIES), "\n".join(b))


# ------------------------------------------------------------------ delivery loop
def delivery():
    W, H = 1200, 232
    b = [panel(W, H, "d")]
    n, gap = len(DELIVERY), 16
    cw = (W - 72 - gap * (n - 1)) / n
    for i, (num_, t, col, lines) in enumerate(DELIVERY):
        x = 36 + i * (cw + gap)
        b.append(f'  <rect x="{x:.1f}" y="36" width="{cw:.1f}" height="160" rx="14" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{x:.1f}" y="36" width="5" height="160" rx="2.5" fill="{col}"/>')
        b.append("  " + text(f"{x + 20:.1f}", 66, num_, 12.5, col, MONO, 700, 1))
        b.append("  " + text(f"{x + 20:.1f}", 94, t, 14, INK, MONO, 700, 0.8))
        for k, ln in enumerate(lines):
            b.append("  " + text(f"{x + 20:.1f}", 128 + k * 21, ln, 12.5, MUTED, SANS))
        if i < n - 1:
            ax = x + cw + 2
            b.append(f'  <path d="M{ax:.1f} 116 h8" stroke="#3B4B66" stroke-width="2"/><path d="M{ax + 8:.1f} 112 l5 4 l-5 4z" fill="#3B4B66"/>')
    return svg(W, H, "How I deliver", " then ".join(t.lower() for _, t, _, _ in DELIVERY), "\n".join(b))


# ------------------------------------------------------------------ toolbox
def toolbox():
    W, H = 1200, 232
    b = [panel(W, H, "x")]
    cw = (W - 72 - 3 * 20) / 4
    for i, (g, col, items) in enumerate(TOOLS):
        x = 36 + i * (cw + 20)
        b.append("  " + text(f"{x:.1f}", 56, g, 11.5, col, MONO, 700, 2))
        px, py = x, 76
        for it in items:
            w = len(it) * 8.4 + 30
            if px + w > x + cw:
                px, py = x, py + 42
            b.append(f'  <rect x="{px:.1f}" y="{py}" width="{w:.1f}" height="32" rx="16" fill="#0B1220" stroke="{col}" stroke-opacity=".55"/>')
            b.append("  " + text(f"{px + 15:.1f}", py + 21, it, 13, INK, SANS, 600))
            px += w + 10
    return svg(W, H, "Toolbox", "; ".join(f"{g.title()}: {', '.join(i)}" for g, _, i in TOOLS), "\n".join(b))


# ------------------------------------------------------------------ project card
def project_card(p, kicker="PROJECT", private=False):
    W, H = 600, 210
    b = [panel(W, H, "p", 18)]
    col = LANG_COLOR.get(p["language"], "#8B949E")
    b.append(f'  <rect x=".5" y=".5" width="{W - 1}" height="4" rx="2" fill="{col}"/>')
    b.append("  " + text(32, 46, kicker, 10.5, AMBER if private else TEAL, MONO, 700, 2.4))
    if private:  # padlock
        b.append(f'  <rect x="{W - 54}" y="38" width="18" height="14" rx="3" stroke="{MUTED}" stroke-width="1.8" fill="none"/>'
                 f'<path d="M{W - 50} 38 v-4 a5 5 0 0 1 10 0 v4" stroke="{MUTED}" stroke-width="1.8" fill="none"/>')
    else:
        b.append(f'  <path d="M{W - 50} 36 l8 8 l-8 8 M{W - 42} 44 h-16" stroke="{MUTED}" stroke-width="1.8" stroke-linecap="round" '
                 'stroke-linejoin="round" fill="none"/>')
    b.append("  " + text(32, 84, p["name"], 24, INK, SANS, 800, -0.2))
    desc = p["description"] or "Source code, setup and usage notes in the repository."
    for k, ln in enumerate(textwrap.wrap(desc, 62)[:3]):
        b.append("  " + text(32, 116 + k * 22, ln, 14.5, MUTED, SANS))
    x = 32
    if p["language"]:
        b.append(f'  <circle cx="{x + 6}" cy="186" r="6" fill="{col}"/>')
        b.append("  " + text(x + 18, 191, p["language"], 13, "#CBD5E1", SANS, 600))
        x += 18 + len(p["language"]) * 7.4 + 22
    if not private:
        b.append("  " + text(f"{x:.0f}", 191, f"★ {p['stars']}", 13, "#CBD5E1", SANS, 600))
        x += 52
    for t in p["topics"]:
        w = len(t) * 6.9 + 22
        if x + w > W - 28:
            break
        b.append(f'  <rect x="{x:.1f}" y="174" width="{w:.1f}" height="24" rx="12" fill="#0B1220" stroke="#2A3A55"/>')
        b.append("  " + text(f"{x + 11:.1f}", 190, t, 11, MUTED, MONO, 600))
        x += w + 8
    return svg(W, H, p["name"], desc, "\n".join(b))


# ------------------------------------------------------------------ badges
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


def work_block(stamp):
    lines = ['<p align="center">']
    for w in WORK:
        lines.append(f'  <img src="./assets/work/{w["slug"]}.svg?v={stamp}" width="49%" alt="{esc(w["name"])}: {esc(w["description"])}" />')
    lines.append("</p>")
    return "\n".join(lines)


def projects_block(ps, stamp):
    if not ps:
        return "<sub>New projects are on their way.</sub>"
    lines = ['<p align="center">']
    for p in ps:
        lines.append(f'  <a href="{p["url"]}"><img src="./assets/projects/{p["name"]}.svg?v={stamp}" width="49%" alt="{esc(p["name"])}: '
                     f'{esc(p["description"] or "project")}" /></a>')
    lines.append("</p>")
    return "\n".join(lines)


def main():
    old = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else None
    try:
        ps = projects()
    except Exception as e:  # keep the last good page when GitHub cannot be reached
        print("fetch failed:", e)
        if old is None:
            sys.exit(1)
        return
    if old and "--force" not in sys.argv and old.get("projects") == ps:
        print("projects unchanged; nothing rewritten")
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    ASSETS.mkdir(exist_ok=True); (ASSETS / "projects").mkdir(exist_ok=True); DATA.parent.mkdir(exist_ok=True)
    keep = {"hero.svg", "capabilities.svg", "delivery.svg", "toolbox.svg", "badge-linkedin.svg", "badge-projects.svg", "badge-follow.svg"}
    for f in ASSETS.glob("*.svg"):
        if f.name not in keep:
            f.unlink()
    for f in (ASSETS / "projects").glob("*.svg"):
        f.unlink()
    out = {"hero.svg": hero(), "capabilities.svg": capabilities(), "delivery.svg": delivery(), "toolbox.svg": toolbox(),
           "badge-linkedin.svg": badge("LINKEDIN", "CONNECT", "#0A66C2"),
           "badge-projects.svg": badge("PROJECTS", "EXPLORE", "#D9622B"),
           "badge-follow.svg": badge("GITHUB", "FOLLOW", "#7C3AED")}
    for name, content in out.items():
        (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    for p in ps:
        (ASSETS / "projects" / f"{p['name']}.svg").write_text(project_card(p), encoding="utf-8", newline="\n")
    (ASSETS / "work").mkdir(exist_ok=True)
    for f in (ASSETS / "work").glob("*.svg"):
        f.unlink()
    for w in WORK:
        (ASSETS / "work" / f"{w['slug']}.svg").write_text(project_card(w, "PRIVATE  ·  PRODUCTION SYSTEM", True),
                                                         encoding="utf-8", newline="\n")
    md = README.read_text(encoding="utf-8")
    md = re.sub(r"<!-- work:start -->.*?<!-- work:end -->",
                lambda m: "<!-- work:start -->\n" + work_block(stamp) + "\n<!-- work:end -->", md, flags=re.S)
    md = re.sub(r"<!-- projects:start -->.*?<!-- projects:end -->",
                lambda m: "<!-- projects:start -->\n" + projects_block(ps, stamp) + "\n<!-- projects:end -->", md, flags=re.S)
    md = re.sub(r'(\./assets/[a-z0-9-]+\.svg)(\?v=\d+)?"', lambda m: f'{m.group(1)}?v={stamp}"', md)
    README.write_text(md, encoding="utf-8", newline="\n")
    DATA.write_text(json.dumps({"projects": ps, "updated": stamp}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("wrote", len(out), "assets and", len(ps), "project cards:", [p["name"] for p in ps])


if __name__ == "__main__":
    main()
