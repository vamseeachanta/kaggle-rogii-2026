# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build the kaggle-rogii-2026 static GitHub Pages site (stdlib only).

Renders the public narrative docs + a stats panel computed from the committed
DERIVED submission CSV. Raw Kaggle competition data is gitignored and never
read — this site uses only the team's own derived outputs and prose, honoring
the competition Terms of Service (no redistribution of raw data).

Run:  python3 scripts/build_pages.py   (writes public/, gitignored)
"""
from __future__ import annotations

import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ASSETS = PUBLIC / "assets"
SUBMISSION = ROOT / "submissions" / "00_carry_forward_submission.csv"

PAGES = {
    "index": ("README.md", "Overview"),
    "competition": ("docs/competition-overview.md", "Competition"),
    "task": ("docs/task-brief.md", "Task Brief"),
    "decisions": ("docs/decisions.md", "Decisions & What Failed"),
    "roadmap": ("docs/roadmap.md", "Roadmap"),
    "intel": ("docs/external-intel.md", "Domain Intel"),
}

_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_CODE = re.compile(r"`([^`]+)`")


def _inline(t: str) -> str:
    t = _CODE.sub(lambda m: f"<code>{html.escape(m.group(1))}</code>", t)
    t = _BOLD.sub(r"<strong>\1</strong>", t)
    t = _LINK.sub(r'<a href="\2">\1</a>', t)
    return t


def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    para: list[str] = []

    def flush():
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()

    while i < n:
        s = lines[i].strip()
        if s.startswith("```"):
            flush(); i += 1; code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(html.escape(lines[i])); i += 1
            i += 1
            out.append("<pre>" + "\n".join(code) + "</pre>"); continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            flush(); block = [lines[i], lines[i + 1]]; i += 2
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in block]
            head, _a, *body = cells
            t = ["<div class='tw'><table><thead><tr>"] + [f"<th>{_inline(c)}</th>" for c in head] + ["</tr></thead><tbody>"]
            for row in body:
                t.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
            out.append("".join(t) + "</tbody></table></div>"); continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush(); lvl = len(m.group(1)); out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>"); i += 1; continue
        if s in ("---", "***", "___"):
            flush(); out.append("<hr>"); i += 1; continue
        if re.match(r"^[-*]\s+", s):
            flush(); items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip())); i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>"); continue
        if not s:
            flush(); i += 1; continue
        para.append(s); i += 1
    flush()
    return "\n".join(out)


def stats_panel() -> str:
    if not SUBMISSION.exists():
        return ""
    vals = []
    with SUBMISSION.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                vals.append(float(row.get("tvt", "")))
            except (ValueError, TypeError):
                pass
    if not vals:
        return ""
    n = len(vals)
    lo, hi = min(vals), max(vals)
    mean = sum(vals) / n
    return (
        '<div class="stats"><h2>Baseline submission (derived data)</h2>'
        '<div class="cards">'
        f'<div class="stat"><b>{n:,}</b><span>predictions</span></div>'
        f'<div class="stat"><b>{mean:,.0f} ft</b><span>mean TVT</span></div>'
        f'<div class="stat"><b>{lo:,.0f}–{hi:,.0f} ft</b><span>TVT range</span></div>'
        f'<div class="stat"><b>11.53 ft</b><span>carry-forward RMSE floor</span></div>'
        '</div>'
        '<p class="note">Computed from <code>submissions/00_carry_forward_submission.csv</code> — '
        'the team\'s own derived output. Raw Kaggle competition data is never published (ToS).</p></div>'
    )


STYLE = """:root{--fg:#1a2230;--muted:#5b6675;--bg:#f7f8fa;--card:#fff;--line:#e2e6ec;--brand:#0a7d5a}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg)}
header.site,footer.site{padding:14px 22px;background:var(--card);border-bottom:1px solid var(--line);display:flex;gap:14px;flex-wrap:wrap;align-items:center}
footer.site{border-top:1px solid var(--line);border-bottom:0;color:var(--muted);font-size:14px;margin-top:48px}
.home{color:var(--brand);font-weight:700;text-decoration:none}
nav a{color:var(--muted);text-decoration:none;font-size:14px}
nav a:hover{color:var(--brand)}
main{max-width:900px;margin:0 auto;padding:28px 22px}
h1{font-size:28px}
.content h2{margin-top:1.5em;border-bottom:1px solid var(--line);padding-bottom:.2em}
.stats{margin:8px 0 24px}
.cards{display:flex;gap:14px;flex-wrap:wrap}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 20px;text-align:center;min-width:130px}
.stat b{display:block;font-size:22px;color:var(--brand)}
.stat span{font-size:13px;color:var(--muted)}
.note{font-size:13px;color:var(--muted)}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--card)}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left}
th{background:#f0f3f7}
pre{background:#0f1722;color:#cfe3ff;padding:14px;border-radius:8px;overflow-x:auto;font-size:13px}
code{background:#eef1f5;padding:1px 5px;border-radius:4px}
a{color:var(--brand)}
hr{border:0;border-top:1px solid var(--line);margin:1.4em 0}
"""


def nav_html() -> str:
    return '<nav>' + " · ".join(f'<a href="{s}.html">{t}</a>' for s, (_f, t) in PAGES.items()) + '</nav>'


def shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · ROGII Wellbore Geology</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body><header class="site"><a class="home" href="index.html">ROGII Wellbore Geology (TVT)</a>{nav_html()}</header>
<main>{body}</main>
<footer class="site"><p>Kaggle ROGII Wellbore Geology Prediction — derived outputs + methodology only; raw competition data not published (ToS). <a href="https://github.com/vamseeachanta/kaggle-rogii-2026">source</a></p></footer>
</body></html>"""


def build():
    PUBLIC.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "style.css").write_text(STYLE, encoding="utf-8")
    built = []
    for slug, (src, title) in PAGES.items():
        path = ROOT / src
        if not path.exists():
            continue
        body = md_to_html(path.read_text(encoding="utf-8"))
        if slug == "index":
            body = stats_panel() + f'<div class="content">{body}</div>'
        else:
            body = f'<div class="content">{body}</div>'
        (PUBLIC / f"{slug}.html").write_text(shell(title, body), encoding="utf-8")
        built.append(slug)
    print(f"Built {len(built)} pages: {', '.join(s + '.html' for s in built)}")


if __name__ == "__main__":
    build()
