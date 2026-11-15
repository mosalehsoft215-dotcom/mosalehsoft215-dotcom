#!/usr/bin/env python3
"""Rebuild the profile's SVG assets from live GitHub counts.

Reads the public Reduction-Bench tree and README plus the public profile, writes data/stats.json and every
asset under assets/. Standard library only, so it runs unchanged on a GitHub Actions runner. When the counts
are the same as the stored ones, nothing is rewritten (no empty daily commits).
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
FIELD_NAME = {"physics": "Physics", "chemistry": "Chemistry", "materials-science": "Materials Science",
              "astronomy": "Astronomy", "mechanical-engineering": "Mechanical", "electrical-engineering": "Electrical",
              "chemical-engineering": "Chemical", "civil-engineering": "Civil", "geosciences": "Geosciences"}


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
    fields, files, cases = {}, 0, 0
    for e in tree["tree"]:
        p = e["path"]
        if e["type"] == "blob":
            files += 1
            m = re.fullmatch(r"tasks/([^/]+)/([^/]+)/[^/]+/task\.toml", p)
            if m:
                key = f"{m.group(1)}/{m.group(2)}"
                fields[key] = fields.get(key, 0) + 1
        elif re.fullmatch(r"tasks/[^/]+/[^/]+/[^/]+/tests/[^/]+/[^/]+", p):
            cases += 1
    readme = fetch(f"https://raw.githubusercontent.com/{USER}/{BENCH}/main/README.md", raw=True)
    hours = re.search(r"about \*\*([\d,]+)\*\* hours", readme)
    repo = fetch(f"https://api.github.com/repos/{USER}/{BENCH}")
    prof = fetch(f"https://api.github.com/users/{USER}")
    return {"tasks": sum(fields.values()), "fields": fields, "domains": len({k.split('/')[0] for k in fields}),
            "cases": cases, "files": files, "hours": int(hours.group(1).replace(",", "")) if hours else None,
            "stars": repo.get("stargazers_count", 0), "public_repos": prof.get("public_repos", 0)}


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
    W, H = 1200, 420
    b = [panel(W, H, "h")]
    b.append('  <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#2DD4BF" stop-opacity=".20"/>'
             '<stop offset="1" stop-color="#2DD4BF" stop-opacity="0"/></radialGradient>')
    b.append('  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F0883E"/>'
             '<stop offset="1" stop-color="#FBBF24"/></linearGradient>')
    b.append(f'  <rect class="trace" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" stroke="{TEAL}" stroke-width="1.6" opacity=".7"/>')
    b.append('  <path d="M560 1 H640" stroke="#2DD4BF" stroke-width="2" opacity=".8"/>')
    # left column
    b.append("  " + text(64, 88, "M.SALE7  /  AI EVALUATION & SCIENTIFIC BENCHMARKS", 12, TEAL, MONO, 700, 3, extra=' class="rise r1"'))
    b.append("  " + text(64, 158, "I build benchmarks", 50, INK, SANS, 800, -0.5, extra=' class="rise r2"'))
    b.append("  " + text(64, 216, "where AI agents must", 50, INK, SANS, 800, -0.5, extra=' class="rise r3"'))
    b.append("  " + text(64, 274, "earn every number.", 50, "url(#accent)", SANS, 800, -0.5, extra=' class="rise r4"'))
    b.append("  " + text(64, 318, "Raw instrument records in. Certified results out. Checked on sealed cases.", 17, MUTED, SANS, 400, 0,
                         extra=' class="rise r5"'))
    b.append(f'  <path d="M64 344 H700" stroke="{RULE}" stroke-width="1"/>')
    b.append(f'  <circle class="pulse" cx="70" cy="368" r="4.5" fill="{TEAL}"/>')
    rail = (f"LIVE COUNT  ·  {num(s['tasks'])} BENCHMARK TASKS  /  {s['fields_n']} FIELDS  /  {s['domains']} DOMAINS  ·  "
            f"{num(s['cases'])} SEALED CASES  ·  {num(s['hours'])} EXPERT HOURS")
    b.append("  " + text(84, 372, rail, 11, "#CBD5E1", MONO, 600, 1))
    b.append("  " + text(84, 394, f"MACHINE-COUNTED FROM GITHUB  ·  {num(s['files'])} FILES SHIPPED  ·  {day} UTC", 10, DIM, MONO, 400, 1))
    # right visual
    cx, cy = 930, 200
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="190" fill="url(#glow)"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="150" stroke="#1E3A5F" stroke-width="1" stroke-dasharray="2 7"/>')
    b.append(f'  <g class="orbit"><circle cx="{cx}" cy="{cy}" r="118" stroke="{TEAL}" stroke-width="1.4" stroke-dasharray="40 22 4 22" opacity=".55"/></g>')
    b.append(f'  <g class="orbit rev"><circle cx="{cx}" cy="{cy}" r="96" stroke="{VIOLET}" stroke-width="1" stroke-dasharray="3 9" opacity=".6"/></g>')
    b.append(f'  <circle class="wave" cx="{cx}" cy="{cy}" r="66" stroke="{TEAL}" stroke-width="1.5"/>')
    b.append(f'  <circle class="wave d" cx="{cx}" cy="{cy}" r="66" stroke="{TEAL}" stroke-width="1.5"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="62" fill="#0A1C26" stroke="{TEAL}" stroke-width="2"/>')
    b.append(f'  <circle cx="{cx}" cy="{cy}" r="46" stroke="{TEAL}" stroke-width="1" opacity=".45"/>')
    # raw trace entering the core and a clean line leaving it
    b.append(f'  <path class="scan" d="M{cx - 42} {cy - 22} l7 -8 l6 16 l6 -20 l6 22 l6 -16 l6 8" stroke="{BLUE}" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="520" opacity=".0"/>')
    b.append(f'  <path class="check" d="M{cx - 20} {cy + 4} l14 14 l28 -30" stroke="{INK}" stroke-width="5" stroke-linecap="round" '
             'stroke-linejoin="round"/>')
    chips = [("RAW RECORDS", BLUE, cx - 230, cy - 118, "c1"), ("REDUCED", VIOLET, cx + 120, cy - 118, "c2"),
             ("SEALED", TEAL, cx - 210, cy + 112, "c3"), ("CERTIFIED", ORANGE, cx + 110, cy + 112, "c4")]
    for lab, col, x, y, c in chips:
        w = int(len(lab) * 8.2 + 34)
        mx, my = x + w / 2, y + 14
        b.append(f'  <path class="signal" d="M{mx:.0f} {my:.0f} L{cx + (mx - cx) * 0.47:.0f} {cy + (my - cy) * 0.47:.0f}" '
                 f'stroke="{col}" stroke-width="1.4" opacity=".75"/>')
        b.append(f'  <g class="chip {c}"><rect x="{x}" y="{y}" width="{w}" height="28" rx="14" fill="#0B1220" stroke="{col}" '
                 f'stroke-width="1.2"/><circle cx="{x + 15}" cy="{y + 14}" r="3.5" fill="{col}"/>'
                 + text(x + 26, y + 18, lab, 10.5, col, MONO, 700, 1.6) + "</g>")
    desc = (f"{num(s['tasks'])} benchmark tasks in {s['fields_n']} fields and {s['domains']} domains, "
            f"{num(s['cases'])} sealed cases, {num(s['hours'])} expert hours, counted {day}.")
    return svg(W, H, "m.sale7: AI evaluation and scientific benchmarks", desc, "\n".join(b), MOTION)


# ------------------------------------------------------------------ featured card
def featured(s):
    W, H = 1200, 330
    b = [panel(W, H, "f")]
    b.append("  " + text(56, 70, "FEATURED BENCHMARK", 12, ORANGE, MONO, 700, 3))
    b.append("  " + text(56, 122, "Reduction-Bench", 44, INK, SANS, 800, -0.5))
    for i, ln in enumerate(["Agentic tasks where an AI writes the program that turns raw",
                            "instrument records into certified figures, then has it run",
                            "on sealed cases it has never seen."]):
        b.append("  " + text(56, 160 + i * 26, ln, 17, MUTED, SANS))
    pills = ["HARBOR TASK FORMAT", "APACHE-2.0", f"★ {s['stars']} STARS", "PUBLIC"]
    x = 56
    for p in pills:
        w = int(len(p) * 7.6 + 26)
        b.append(f'  <rect x="{x}" y="252" width="{w}" height="28" rx="14" fill="#0B1220" stroke="#2A3A55"/>')
        b.append("  " + text(x + 13, 270, p, 10.5, "#CBD5E1", MONO, 700, 1.2))
        x += w + 10
    tiles = [(num(s["tasks"]), "TASKS", ORANGE), (num(s["cases"]), "SEALED CASES", TEAL),
             (str(s["fields_n"]), "FIELDS", BLUE), (num(s["hours"]), "EXPERT HOURS", VIOLET)]
    for i, (n, lab, col) in enumerate(tiles):
        tx, ty = 690 + (i % 2) * 238, 46 + (i // 2) * 112
        b.append(f'  <rect x="{tx}" y="{ty}" width="222" height="98" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{tx}" y="{ty}" width="222" height="4" rx="2" fill="{col}"/>')
        b.append("  " + text(tx + 22, ty + 58, n, 36, INK, MONO, 700))
        b.append("  " + text(tx + 22, ty + 82, lab, 10.5, MUTED, MONO, 600, 1.8))
    # domain split bar
    total = s["tasks"]; x = 690.0; bw = 460
    doms = {}
    for k, v in s["fields"].items():
        doms[k.split("/")[0]] = doms.get(k.split("/")[0], 0) + v
    for d in ("physical-sciences", "engineering-sciences", "earth-sciences"):
        if d not in doms:
            continue
        w = bw * doms[d] / total
        b.append(f'  <rect x="{x:.1f}" y="284" width="{max(w - 3, 3):.1f}" height="8" rx="4" fill="{DOMAIN_COLOR[d]}"/>')
        x += w
    legend = "  ·  ".join(f"{DOMAIN_NAME[d].upper()} {doms[d]}" for d in ("physical-sciences", "engineering-sciences", "earth-sciences") if d in doms)
    b.append("  " + text(690, 312, legend, 10, DIM, MONO, 600, 1))
    return svg(W, H, "Reduction-Bench", f"{s['tasks']} tasks, {s['cases']} sealed cases, {s['fields_n']} fields.", "\n".join(b))


# ------------------------------------------------------------------ build loop
def build_loop():
    W, H = 1200, 250
    steps = [("01", "RAW RECORDS", BLUE, ["Counts, traces, logs and", "sheets, kept the way the", "lab or plant keeps them."]),
             ("02", "STATED PHYSICS", VIOLET, ["Every law a reduction", "needs is written in the", "notes. Nothing is a trick."]),
             ("03", "SILENT CONDITIONS", TEAL, ["What no sheet records:", "a drifted zero, a clock,", "a geometry. Only data shows."]),
             ("04", "A PROGRAM", ORANGE, ["Agents ship code, never", "typed numbers. It must", "hold on unseen cases."]),
             ("05", "SEALED VERDICT", AMBER, ["Run offline on held-back", "cases. Reward 1 only if", "every result is in limit."])]
    b = [panel(W, H, "b")]
    cw, gap, x0 = 206, 24, 36
    for i, (n, t, col, lines) in enumerate(steps):
        x = x0 + i * (cw + gap)
        b.append(f'  <rect x="{x}" y="36" width="{cw}" height="178" rx="16" fill="#0B1220" stroke="#22314A"/>')
        b.append(f'  <rect x="{x}" y="36" width="5" height="178" rx="2.5" fill="{col}"/>')
        b.append("  " + text(x + 22, 70, n, 13, col, MONO, 700, 1))
        b.append("  " + text(x + 22, 100, t, 14.5, INK, MONO, 700, 0.6))
        for k, ln in enumerate(lines):
            b.append("  " + text(x + 22, 136 + k * 22, ln, 12.5, MUTED, SANS))
        if i < len(steps) - 1:
            ax = x + cw + 4
            b.append(f'  <path d="M{ax} 125 h14" stroke="#3B4B66" stroke-width="2"/><path d="M{ax + 14} 120 l6 5 l-6 5z" fill="#3B4B66"/>')
    return svg(W, H, "How every task is built", "Raw records, stated physics, silent conditions, a program, a sealed verdict.", "\n".join(b))


# ------------------------------------------------------------------ field map
def field_map(s):
    cols = [d for d in ("physical-sciences", "engineering-sciences", "earth-sciences") if any(k.startswith(d + "/") for k in s["fields"])]
    rows = max(sum(1 for k in s["fields"] if k.startswith(d + "/")) for d in cols)
    W, H = 1200, 110 + rows * 46
    b = [panel(W, H, "m")]
    mx = max(s["fields"].values())
    cw = (W - 72 - 24 * (len(cols) - 1)) / len(cols)
    for i, d in enumerate(cols):
        x = 36 + i * (cw + 24); col = DOMAIN_COLOR[d]
        items = sorted(((k.split("/")[1], v) for k, v in s["fields"].items() if k.startswith(d + "/")), key=lambda kv: (-kv[1], kv[0]))
        b.append(f'  <circle cx="{x + 7:.1f}" cy="52" r="6" fill="{col}"/>')
        b.append("  " + text(f"{x + 22:.1f}", 57, DOMAIN_NAME[d].upper(), 13, col, MONO, 700, 1.6))
        b.append("  " + text(f"{x + cw:.1f}", 57, str(sum(v for _, v in items)), 13, col, MONO, 700, 0, "end"))
        for j, (f, v) in enumerate(items):
            y = 92 + j * 46
            b.append("  " + text(f"{x:.1f}", y, FIELD_NAME.get(f, f), 14, INK, SANS, 600))
            b.append("  " + text(f"{x + cw:.1f}", y, str(v), 14, INK, MONO, 700, 0, "end"))
            b.append(f'  <rect x="{x:.1f}" y="{y + 10}" width="{cw:.1f}" height="7" rx="3.5" fill="#1A2436"/>')
            b.append(f'  <rect x="{x:.1f}" y="{y + 10}" width="{max(cw * v / mx, 6):.1f}" height="7" rx="3.5" fill="{col}"/>')
    return svg(W, H, "Fields covered", f"{s['tasks']} tasks across {s['fields_n']} fields.", "\n".join(b))


# ------------------------------------------------------------------ toolbox
def toolbox():
    groups = [("LANGUAGES", BLUE, ["Python", "Bash", "SQL"]),
              ("SCIENTIFIC STACK", TEAL, ["NumPy", "SciPy", "pandas", "Matplotlib"]),
              ("EVALUATION", ORANGE, ["Harbor", "pytest", "CTRF reports", "Docker"]),
              ("WORKFLOW", VIOLET, ["Git", "GitHub Actions", "Linux"])]
    W, H = 1200, 196
    b = [panel(W, H, "t")]
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
    return svg(W, H, "Toolbox", "Languages, scientific stack, evaluation and workflow tools.", "\n".join(b))


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
        s["hours"] = old["hours"]
    s["fields_n"] = len(s["fields"])
    counts = {k: v for k, v in s.items() if k != "day"}
    force = "--force" in sys.argv
    if old and not force and {k: v for k, v in old.items() if k != "day"} == counts:
        print("counts unchanged; nothing rewritten")
        return
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    s["day"] = day
    ASSETS.mkdir(exist_ok=True); DATA.parent.mkdir(exist_ok=True)
    out = {"hero.svg": hero(s, day), "featured-reduction-bench.svg": featured(s), "build-loop.svg": build_loop(),
           "field-map.svg": field_map(s), "toolbox.svg": toolbox(),
           "badge-bench.svg": badge("REDUCTION-BENCH", f"{s['tasks']} TASKS", "#D9622B"),
           "badge-harbor.svg": badge("HARBOR", "TASK FORMAT", "#2F6FDB"),
           "badge-domains.svg": badge("COVERAGE", f"{s['domains']} DOMAINS · {s['fields_n']} FIELDS", "#0F9F8F"),
           "badge-follow.svg": badge("GITHUB", "FOLLOW", "#7C3AED")}
    for name, content in out.items():
        (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    DATA.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("wrote", len(out), "assets;", {k: s[k] for k in ("tasks", "cases", "hours", "files", "stars", "day")})


if __name__ == "__main__":
    main()
