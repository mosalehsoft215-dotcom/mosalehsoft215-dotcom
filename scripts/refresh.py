#!/usr/bin/env python3
"""Rebuild the profile's SVG assets.

Career facts (roles, shipped systems, recognition) live in PROFILE below; the open-source counts are read live
from the public Reduction-Bench repository. Standard library only, so it runs unchanged on a GitHub Actions
runner. When the live counts match data/stats.json, nothing is rewritten (no empty daily commits); pass --force
to redraw anyway after editing PROFILE.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

USER = "mosalehsoft215-dotcom"
BENCH = "reduction-bench"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "stats.json"

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
INK, MUTED, DIM, RULE = "#F8FAFC", "#94A3B8", "#64748B", "#1E2A3D"
BLUE, TEAL, VIOLET, ORANGE, AMBER = "#4D7CFE", "#2DD4BF", "#9B7CFF", "#F0883E", "#FBBF24"
DOMAIN_COLOR = {"physical-sciences": BLUE, "engineering-sciences": ORANGE, "earth-sciences": TEAL}
DOMAIN_NAME = {"physical-sciences": "Physical Sciences", "engineering-sciences": "Engineering Sciences",
               "earth-sciences": "Earth Sciences"}

PROFILE = {
    "name": "MOHAMED SALEH",
    "role": "AI ENGINEER",
    "years": "3+",
    "in_production": 4,
    "records": "1.7M+",
    "ocr": "~95%",
    "kaggle": "2×",
    "capabilities": [
        ("AGENTIC AI SYSTEMS", VIOLET, ["Multi-agent orchestration,", "delegation, memory, validation", "and tool use over MCP, GraphQL", "and REST."]),
        ("DOCUMENT INTELLIGENCE", BLUE, ["OCR and MRZ pipelines,", "mixed-PDF extraction,", "enrichment and grounding for", "downstream agents."]),
        ("COMPUTER VISION", ORANGE, ["YOLO detection, facial", "recognition, perspective", "correction and image", "enhancement."]),
        ("AI EVALUATION", TEAL, ["Benchmarks, expert tasks,", "LLM and VLM evaluation and", "data quality for model", "training."]),
    ],
    "work": [
        ("Passport & ID document AI", "IN PRODUCTION", TEAL,
         ["YOLO detection, perspective correction,", "enhancement and a local MRZ model:", "~95% accuracy at lower LLM API cost."]),
        ("Multi-agent operations assistant", "IN PRODUCTION", TEAL,
         ["Orchestrator, delegation and a", "recommendation agent that guides users", "through complex operation statements."]),
        ("Travel booking assistant", "IN PRODUCTION", TEAL,
         ["Dynamic package and pricing logic, a", "preference-memory agent, price guard and", "VLM tools served over MCP."]),
        ("Hotel data platform", "1.7M+ RECORDS", BLUE,
         ["Entity resolution, deduplication and", "standardization of 1.7M+ records, with a", "GraphQL MCP layer and search agents."]),
        ("Document AI for marketplaces", "DEPLOYED PILOT", AMBER,
         ["Mixed-PDF extraction, OCR model trials,", "real and synthetic datasets and external", "enrichment tools for agent grounding."]),
        ("Facial recognition", "IN PRODUCTION", TEAL,
         ["Recognition pipeline across backend and", "frontend, shipped with desktop apps for", "testing and database management."]),
    ],
    "timeline": [
        ("2026", "Reduction-Bench · open source", "{bench} expert tasks that test AI agents on raw scientific and engineering data.", TEAL),
        ("2025 – NOW", "AI Developer · SafaSoft", "Production agents, document AI, computer vision and MCP integrations, owned end to end.", ORANGE),
        ("2023 – 2025", "AI Developer · Freelance", "Chatbots, NLP pipelines, model integrations and reusable data-processing tools.", BLUE),
        ("2023 – 2024", "AI training & evaluation", "Coding expert, then senior reviewer and task creator for model-quality programs.", VIOLET),
        ("2024", "B.Sc. Computer Science · Ain Shams University", "1st place, Kaggle neural-networks competition (2024).", AMBER),
        ("2021", "1st place · Kaggle computer-vision competition", "Early start in deep learning for images.", AMBER),
    ],
    "tools": [
        ("LANGUAGES", BLUE, ["Python", "SQL", "JavaScript", "C++", "Java", "C#"]),
        ("AI / ML", VIOLET, ["PyTorch", "TensorFlow", "scikit-learn", "YOLO", "OCR & MRZ", "LLM / VLM"]),
        ("AGENTS & APIS", ORANGE, ["MCP", "GraphQL", "REST", "Flask", "n8n", "Tool calling"]),
        ("DATA & DELIVERY", TEAL, ["pandas", "Selenium", "MySQL", "Docker", "Git", "Power BI"]),
    ],
}


# ------------------------------------------------------------------ data
def fetch(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-refresh", "Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and url.startswith("https://api.github.com"):
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8")
    return body if raw else json.loads(body)


def live_counts():
    tree = fetch(f"https://api.github.com/repos/{USER}/{BENCH}/git/trees/main?recursive=1")
    if tree.get("truncated"):
        raise RuntimeError("tree truncated")
    fields, cases = {}, 0
    for e in tree["tree"]:
        p = e["path"]
        if e["type"] == "blob":
            m = re.fullmatch(r"tasks/([^/]+)/([^/]+)/[^/]+/task\.toml", p)
            if m:
                key = f"{m.group(1)}/{m.group(2)}"
                fields[key] = fields.get(key, 0) + 1
        elif re.fullmatch(r"tasks/[^/]+/[^/]+/[^/]+/tests/[^/]+/[^/]+", p):
            cases += 1
    readme = fetch(f"https://raw.githubusercontent.com/{USER}/{BENCH}/main/README.md", raw=True)
    hours = re.search(r"about \*\*([\d,]+)\*\* hours", readme)
    repo = fetch(f"https://api.github.com/repos/{USER}/{BENCH}")
    return {"tasks": sum(fields.values()), "fields": fields, "domains": len({k.split('/')[0] for k in fields}),
            "cases": cases, "hours": int(hours.group(1).replace(",", "")) if hours else None,
            "stars": repo.get("stargazers_count", 0)}


# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(str(s), quote=True)


def num(n):
    return f"{n:,}"


def svg(w, h, title, desc, body, style=""):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="title desc">\n  <title id="title">{esc(title)}</title>\n'
            f'  <desc id="desc">{esc(desc)}</desc>\n{style}{body}\n</svg>\n')


def panel(w, h, rid):
    return (f'  <defs>\n    <linearGradient id="{rid}-bg" x1="0" y1="0" x2="1" y2="1">\n'
            f'      <stop offset="0" stop-color="#07111E"/><stop offset="1" stop-color="#150C2B"/>\n    </linearGradient>\n'
            f'    <pattern id="{rid}-grid" width="40" height="40" patternUnits="userSpaceOnUse">\n'
            f'      <path d="M40 0H0V40" stroke="#1B2638" stroke-width="1" opacity=".55"/>\n    </pattern>\n  </defs>\n'
            f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="22" fill="url(#{rid}-bg)" stroke="#23324A"/>\n'
            f'  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="22" fill="url(#{rid}-grid)"/>\n')


def text(x, y, s, size, fill=INK, family=MONO, weight=400, spacing=0, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def pill(x, y, label, col, size=10, h=24):
    w = len(label) * (size * 0.62 + 1.1) + 22
    return (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{col}" fill-opacity=".12" stroke="{col}" '
            f'stroke-opacity=".7"/>' + text(f"{x + 11:.1f}", y + h / 2 + size * 0.36, label, size, col, MONO, 700, 1.1)), w


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
def hero(s, day):
    P = PROFILE
    W, H = 1200, 420
    b = [panel(W, H, "h")]
    b.append('  <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#2DD4BF" stop-opacity=".20"/>'
             '<stop offset="1" stop-color="#2DD4BF" stop-opacity="0"/></radialGradient>')
    b.append('  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F0883E"/>'
             '<stop offset="1" stop-color="#FBBF24"/></linearGradient>')
    b.append(f'  <rect class="trace" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" stroke="{TEAL}" stroke-width="1.6" opacity=".7"/>')
    b.append('  <path d="M560 1 H640" stroke="#2DD4BF" stroke-width="2" opacity=".8"/>')
    b.append("  " + text(64, 88, f"{P['name']}  /  {P['role']}  ·  AGENTS · DOCUMENT AI · VISION", 12, TEAL, MONO, 700, 2.6,
                         extra=' class="rise r1"'))
    b.append("  " + text(64, 158, "I build AI systems", 50, INK, SANS, 800, -0.5, extra=' class="rise r2"'))
    b.append("  " + text(64, 216, "that hold up in", 50, INK, SANS, 800, -0.5, extra=' class="rise r3"'))
    b.append("  " + text(64, 274, "production.", 50, "url(#accent)", SANS, 800, -0.5, extra=' class="rise r4"'))
    b.append("  " + text(64, 318, "Agents, document AI and computer vision, owned from raw data to deployment.", 17, MUTED, SANS,
                         extra=' class="rise r5"'))
    b.append(f'  <path d="M64 344 H700" stroke="{RULE}" stroke-width="1"/>')
    b.append(f'  <circle class="pulse" cx="70" cy="368" r="4.5" fill="{TEAL}"/>')
    rail = (f"{P['years']} YEARS SHIPPING AI  ·  {P['in_production']} SYSTEMS IN PRODUCTION  ·  {P['records']} RECORDS "
            f"RECONCILED  ·  {num(s['tasks'])} OPEN BENCHMARK TASKS  ·  {P['kaggle']} KAGGLE 1ST PLACE")
    b.append("  " + text(84, 372, rail, 11, "#CBD5E1", MONO, 600, 1))
    b.append("  " + text(84, 394, f"BENCHMARK COUNT READ LIVE FROM GITHUB  ·  {day} UTC", 10, DIM, MONO, 400, 1))
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
    desc = (f"Mohamed Saleh, AI engineer: {P['years']} years shipping production AI, {P['in_production']} systems in production, "
            f"{P['records']} records reconciled, {s['tasks']} open benchmark tasks.")
    return svg(W, H, "Mohamed Saleh: I build AI systems that hold up in production", desc, "\n".join(b), MOTION)


# ------------------------------------------------------------------ impact tiles
def impact(s):
    P = PROFILE
    tiles = [(P["years"], "YEARS SHIPPING AI", ORANGE), (str(P["in_production"]), "SYSTEMS IN PRODUCTION", TEAL),
             (P["records"], "RECORDS RECONCILED", BLUE), (P["ocr"], "PASSPORT OCR ACCURACY", VIOLET),
             (num(s["tasks"]), "OPEN BENCHMARK TASKS", TEAL), (P["kaggle"], "KAGGLE 1ST PLACE", AMBER)]
    W, H, gap = 1200, 140, 14
    tw = (W - gap * (len(tiles) - 1)) / len(tiles)
    b = []
    for i, (n, lab, col) in enumerate(tiles):
        x = i * (tw + gap)
        b.append(f'  <rect x="{x + .5:.1f}" y=".5" width="{tw - 1:.1f}" height="{H - 1}" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{x + .5:.1f}" y=".5" width="{tw - 1:.1f}" height="5" rx="2.5" fill="{col}"/>')
        b.append("  " + text(f"{x + tw / 2:.1f}", 76, n, 40, INK, MONO, 700, 0, "middle"))
        b.append("  " + text(f"{x + tw / 2:.1f}", 108, lab, 10, MUTED, MONO, 600, 1, "middle"))
    return svg(W, H, "Impact at a glance", ", ".join(f"{n} {l.lower()}" for n, l, _ in tiles), "\n".join(b))


# ------------------------------------------------------------------ capabilities
def capabilities():
    caps = PROFILE["capabilities"]
    W, H = 1200, 250
    b = [panel(W, H, "c")]
    cw = (W - 72 - 20 * (len(caps) - 1)) / len(caps)
    for i, (t, col, lines) in enumerate(caps):
        x = 36 + i * (cw + 20)
        b.append(f'  <rect x="{x:.1f}" y="36" width="{cw:.1f}" height="178" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{x:.1f}" y="36" width="{cw:.1f}" height="4" rx="2" fill="{col}"/>')
        b.append(f'  <circle cx="{x + 30:.1f}" cy="76" r="9" fill="{col}" fill-opacity=".18" stroke="{col}"/>')
        b.append(f'  <circle cx="{x + 30:.1f}" cy="76" r="3" fill="{col}"/>')
        b.append("  " + text(f"{x + 50:.1f}", 81, t, 13, INK, MONO, 700, 1.2))
        for k, ln in enumerate(lines):
            b.append("  " + text(f"{x + 22:.1f}", 120 + k * 22, ln, 14, MUTED, SANS))
    return svg(W, H, "What I build", "; ".join(t.title() for t, _, _ in caps), "\n".join(b))


# ------------------------------------------------------------------ selected work
def work():
    items = PROFILE["work"]
    cols, cw_gap, rh = 3, 20, 168
    rows = (len(items) + cols - 1) // cols
    W, H = 1200, 36 * 2 + rows * rh + (rows - 1) * 20
    b = [panel(W, H, "w")]
    cw = (W - 72 - cw_gap * (cols - 1)) / cols
    for i, (t, status, col, lines) in enumerate(items):
        x = 36 + (i % cols) * (cw + cw_gap); y = 36 + (i // cols) * (rh + 20)
        b.append(f'  <rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{rh}" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{x:.1f}" y="{y}" width="5" height="{rh}" rx="2.5" fill="{col}"/>')
        p, _ = pill(x + 22, y + 20, status, col)
        b.append("  " + p)
        b.append("  " + text(f"{x + 22:.1f}", y + 74, t, 18, INK, SANS, 700))
        for k, ln in enumerate(lines):
            b.append("  " + text(f"{x + 22:.1f}", y + 104 + k * 21, ln, 13.5, MUTED, SANS))
    return svg(W, H, "Selected work", "; ".join(f"{t} ({s.lower()})" for t, s, _, _ in items), "\n".join(b))


# ------------------------------------------------------------------ timeline
def timeline(s):
    rows = PROFILE["timeline"]
    W, rh = 1200, 62
    H = 56 + len(rows) * rh
    b = [panel(W, H, "t")]
    lx = 268
    b.append(f'  <path d="M{lx} 46 V{H - 34}" stroke="#2A3A55" stroke-width="2"/>')
    for i, (when, title, sub, col) in enumerate(rows):
        y = 52 + i * rh
        b.append("  " + text(236, y + 16, when, 12.5, col, MONO, 700, 1.2, "end"))
        b.append(f'  <circle cx="{lx}" cy="{y + 11}" r="7" fill="#0B1220" stroke="{col}" stroke-width="2.5"/>')
        b.append(f'  <circle cx="{lx}" cy="{y + 11}" r="2.5" fill="{col}"/>')
        b.append("  " + text(298, y + 17, title, 17, INK, SANS, 700))
        b.append("  " + text(298, y + 40, sub.format(bench=num(s["tasks"])), 13.5, MUTED, SANS))
    return svg(W, H, "Experience", "; ".join(f"{w}: {t}" for w, t, _, _ in rows), "\n".join(b))


# ------------------------------------------------------------------ toolbox
def toolbox():
    groups = PROFILE["tools"]
    W, H = 1200, 232
    b = [panel(W, H, "x")]
    cw = (W - 72 - 3 * 20) / 4
    for i, (g, col, items) in enumerate(groups):
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
    return svg(W, H, "Toolbox", "; ".join(f"{g.title()}: {', '.join(i)}" for g, _, i in groups), "\n".join(b))


# ------------------------------------------------------------------ open-source card
def featured(s):
    W, H = 1200, 300
    b = [panel(W, H, "f")]
    b.append("  " + text(56, 66, "OPEN-SOURCE HIGHLIGHT", 12, ORANGE, MONO, 700, 3))
    b.append("  " + text(56, 116, "Reduction-Bench", 42, INK, SANS, 800, -0.5))
    for i, ln in enumerate(["A public benchmark for AI agents: each task hands the agent",
                            "raw scientific or engineering records and scores the program",
                            "it writes on sealed cases it has never seen."]):
        b.append("  " + text(56, 154 + i * 25, ln, 16.5, MUTED, SANS))
    x = 56
    for lab in ["HARBOR TASK FORMAT", "APACHE-2.0", f"★ {s['stars']} STARS"]:
        p, w = pill(x, 236, lab, "#CBD5E1", 10, 28)
        b.append("  " + p); x += w + 10
    tiles = [(num(s["tasks"]), "TASKS", ORANGE), (num(s["cases"]), "SEALED CASES", TEAL),
             (str(len(s["fields"])), "FIELDS", BLUE), (num(s["hours"]), "EXPERT HOURS", VIOLET)]
    for i, (n, lab, col) in enumerate(tiles):
        tx, ty = 690 + (i % 2) * 238, 40 + (i // 2) * 104
        b.append(f'  <rect x="{tx}" y="{ty}" width="222" height="90" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{tx}" y="{ty}" width="222" height="4" rx="2" fill="{col}"/>')
        b.append("  " + text(tx + 22, ty + 54, n, 34, INK, MONO, 700))
        b.append("  " + text(tx + 22, ty + 76, lab, 10.5, MUTED, MONO, 600, 1.8))
    total = s["tasks"]; x = 690.0
    doms = {}
    for k, v in s["fields"].items():
        doms[k.split("/")[0]] = doms.get(k.split("/")[0], 0) + v
    order = [d for d in ("physical-sciences", "engineering-sciences", "earth-sciences") if d in doms]
    for d in order:
        w = 460 * doms[d] / total
        b.append(f'  <rect x="{x:.1f}" y="256" width="{max(w - 3, 3):.1f}" height="8" rx="4" fill="{DOMAIN_COLOR[d]}"/>')
        x += w
    b.append("  " + text(690, 284, "  ·  ".join(f"{DOMAIN_NAME[d].upper()} {doms[d]}" for d in order), 10, DIM, MONO, 600, 1))
    return svg(W, H, "Reduction-Bench", f"{s['tasks']} tasks, {s['cases']} sealed cases.", "\n".join(b))


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


def main():
    old = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else None
    try:
        s = live_counts()
    except Exception as e:  # keep the last good assets when GitHub cannot be reached
        print("fetch failed:", e)
        if old is None:
            sys.exit(1)
        return
    if s["hours"] is None and old:
        s["hours"] = old.get("hours")
    keys = ("tasks", "fields", "domains", "cases", "hours", "stars")
    if old and "--force" not in sys.argv and all(old.get(k) == s[k] for k in keys):
        print("counts unchanged; nothing rewritten")
        return
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    s["day"] = day
    ASSETS.mkdir(exist_ok=True); DATA.parent.mkdir(exist_ok=True)
    for stale in ("build-loop.svg", "field-map.svg", "badge-harbor.svg", "badge-domains.svg"):
        (ASSETS / stale).unlink(missing_ok=True)
    out = {"hero.svg": hero(s, day), "impact.svg": impact(s), "capabilities.svg": capabilities(), "work.svg": work(),
           "timeline.svg": timeline(s), "toolbox.svg": toolbox(), "featured-reduction-bench.svg": featured(s),
           "badge-linkedin.svg": badge("LINKEDIN", "CONNECT", "#0A66C2"),
           "badge-bench.svg": badge("REDUCTION-BENCH", "OPEN SOURCE", "#D9622B"),
           "badge-kaggle.svg": badge("KAGGLE", "2× 1ST PLACE", "#1F8FC9"),
           "badge-follow.svg": badge("GITHUB", "FOLLOW", "#7C3AED")}
    for name, content in out.items():
        (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    DATA.write_text(json.dumps({k: s[k] for k in keys + ("day",)}, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("wrote", len(out), "assets;", {k: s[k] for k in ("tasks", "cases", "hours", "stars", "day")})


if __name__ == "__main__":
    main()
