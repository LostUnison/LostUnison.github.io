"""Wrap every page of the site in the shared layout: YouTube style header with a
search bar, collapsible guide sidebar, breadcrumb and previous/next links.
Also writes search.html and js/search-index.js (the data behind the search bar).
Safe to run again: it only keeps the content between the <main> tags and the
parts marked <!--nav--> are rebuilt.

The guide list comes from build-summary.json when build.py has written it.
Otherwise it is read from the guide cards of the current index.html.

Usage: python3 layout.py <site dir>
"""
import html as htmllib
import json
import re
import sys
from pathlib import Path

site = Path(sys.argv[1])
CATS = ["Leveling", "Professions", "Addons", "Gearing", "Reputation", "Gold making", "Game client"]


def cat_id(c):
    return c.lower().replace(" ", "-")


def guides_from_home():
    text = (site / "index.html").read_text(encoding="utf-8")
    cats = {cat_id(c): c for c in CATS}
    cur, out = None, []
    pat = r'<h2 id="([^"]+)">|<a class="guide-card" href="guides/([^"]+)\.html"[^>]*><span class="title">(.*?)</span>'
    for m in re.finditer(pat, text):
        if m.group(1):
            cur = cats.get(m.group(1))
        elif cur:
            out.append({"slug": m.group(2), "title": htmllib.unescape(m.group(3)), "cat": cur, "videos": []})
    return out


summary = site.parent / "build-summary.json"
if summary.exists():
    guides = json.load(open(summary))["guides"]
    if not any(g["slug"] == "first-aid" for g in guides):
        i = next(k for k, g in enumerate(guides) if g["slug"] == "fishing")
        guides.insert(i + 1, {"slug": "first-aid", "title": "First Aid 1 to 450 (x3)", "cat": "Professions", "videos": []})
else:
    guides = guides_from_home()

# guide-dates.json: publish date of the main video of each guide (from the Videos sheet of the xlsx).
# Guides not listed (no video posted yet) use "_default", the date the page was written.
DATES = json.load(open(Path(__file__).parent / "guide-dates.json"))


def guide_date(slug):
    return DATES.get(slug, DATES["_default"])


order = [g for c in CATS for g in guides if g["cat"] == c]
by_slug = {g["slug"]: g for g in order}
missing = {f.stem for f in (site / "guides").glob("*.html")} - set(by_slug)
if missing:
    sys.exit("guide pages without a card on the home page: " + ", ".join(sorted(missing)))

SHORT_CAT = {"Gold making": "Gold", "Game client": "Client"}

ICONS = {
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "back": '<path d="M19 12H5m6-6-6 6 6 6"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "home": '<path d="M4 11 12 4l8 7v8.5a.5.5 0 0 1-.5.5H14v-5.5h-4V20H4.5a.5.5 0 0 1-.5-.5z"/>',
    "Leveling": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "Professions": '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>',
    "Addons": '<path d="M12 3 4 7v10l8 4 8-4V7z"/><path d="M4 7l8 4 8-4M12 11v10"/>',
    "Gearing": '<path d="M12 3l7 3v5.5c0 4.3-3 7.7-7 9.5-4-1.8-7-5.2-7-9.5V6z"/>',
    "Reputation": '<path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.3-4.1 5.9-.9z"/>',
    "Gold making": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v9M14.5 9.5c-.5-1-1.5-1.5-2.5-1.5-1.4 0-2.5.8-2.5 2s1 1.7 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2c-1 0-2-.5-2.5-1.5"/>',
    "Game client": '<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M8 20h8M12 16.5V20"/>',
}


def icon(name, size=24):
    return (f'<svg class="ic" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def short(t):
    # shorter labels for the sidebar
    t = re.sub(r" \(x3\)", "", t)
    t = re.sub(r", Bonuses and Gold Making| and Bonuses|, Specializations and Gold Making", "", t)
    t = t.replace(", Find Fish, Sea Turtle and Heirloom Ring", "")
    return t


def header(root):
    return f"""<header class="site-header">
  <div class="bar">
    <div class="bar-start">
      <button class="icon-btn" id="sb-toggle" type="button" aria-label="Guide menu" aria-controls="sidebar" aria-expanded="true">{icon("menu")}</button>
      <a class="brand" href="{root}index.html">
        <img class="brand-logo" src="{root}images/logo.svg" width="32" height="32" alt="">
        <span class="brand-name">Lost Unison</span>
      </a>
    </div>
    <form class="search" id="search-form" role="search" action="{root}search.html" method="get" autocomplete="off">
      <button class="icon-btn search-back" id="search-back" type="button" aria-label="Close search">{icon("back")}</button>
      <div class="search-field">
        <input id="q" name="q" type="text" placeholder="Search guides" aria-label="Search guides" enterkeyhint="search" role="combobox" aria-expanded="false" aria-controls="suggest" aria-autocomplete="list" spellcheck="false">
        <kbd class="search-kbd" aria-hidden="true">/</kbd>
        <button class="search-clear" id="q-clear" type="button" aria-label="Clear search" hidden>{icon("close", 20)}</button>
      </div>
      <button class="search-btn" type="submit" aria-label="Search">{icon("search")}</button>
      <ul class="suggest" id="suggest" role="listbox" aria-label="Suggestions" hidden></ul>
    </form>
    <div class="bar-end">
      <button class="icon-btn search-open" id="search-open" type="button" aria-label="Search">{icon("search")}</button>
      <a class="bar-link" href="https://www.youtube.com/@lostunison">YouTube</a>
      <a class="bar-link" href="https://discord.gg/md4a6BgUTs">Discord</a>
    </div>
  </div>
</header>
"""


def foot(root):
    return f"""<footer class="site-footer">
  <div class="inner">
    <span>Guides by Lost Unison</span>
    <span><a href="https://www.youtube.com/@lostunison">YouTube</a> · <a href="https://discord.gg/md4a6BgUTs">Discord</a></span>
  </div>
</footer>
<script src="{root}js/search-index.js"></script>
<script src="{root}js/site.js"></script>
</body>
</html>
"""


def head(title, desc, root):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="{root}images/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}css/style.css">
<script>try{{if(localStorage.getItem('lu-sb')==='mini')document.documentElement.classList.add('sb-mini')}}catch(e){{}}</script>
</head>
<body data-root="{root}">
"""


def sidebar(root, gp, current, cur_cat):
    """current: guide slug, 'home' or 'search'. gp: path from the page to the guides folder."""
    home_cur = ' aria-current="page"' if current == "home" else ""
    out = ['<aside class="sidenav" id="sidebar" aria-label="Guides">\n<nav class="sb-full" aria-label="All guides">\n']
    out.append(f'<a class="sb-item" href="{root}index.html"{home_cur}>{icon("home")}<span>Home</span></a>\n<hr>\n')
    for c in CATS:
        gs = [g for g in order if g["cat"] == c]
        if not gs:
            continue
        out.append(f'<p class="sb-head">{c}</p>\n')
        for g in gs:
            here = ' aria-current="page"' if g["slug"] == current else ""
            out.append(f'<a class="sb-item" href="{gp}{g["slug"]}.html" title="{g["title"]}"{here}>{icon(c, 22)}<span>{short(g["title"])}</span></a>\n')
        out.append("<hr>\n")
    out.append('</nav>\n<nav class="sb-rail" aria-label="Categories">\n')
    out.append(f'<a class="mini-item" href="{root}index.html"{home_cur}>{icon("home")}<span>Home</span></a>\n')
    for c in CATS:
        here = ' aria-current="page"' if c == cur_cat else ""
        out.append(f'<a class="mini-item" href="{root}index.html#{cat_id(c)}"{here}>{icon(c)}<span>{SHORT_CAT.get(c, c)}</span></a>\n')
    out.append('</nav>\n</aside>\n<div class="sb-scrim" id="sb-scrim"></div>\n')
    return "".join(out)


def pager(slug):
    i = next(k for k, g in enumerate(order) if g["slug"] == slug)
    prev_g = order[i - 1] if i > 0 else None
    next_g = order[i + 1] if i < len(order) - 1 else None
    out = ['<nav class="pager" aria-label="Previous and next guide">']
    if prev_g:
        out.append(f'<a class="pager-prev" href="{prev_g["slug"]}.html"><span>Previous</span>{short(prev_g["title"])}</a>')
    else:
        out.append("<span></span>")
    if next_g:
        out.append(f'<a class="pager-next" href="{next_g["slug"]}.html"><span>Next</span>{short(next_g["title"])}</a>')
    out.append("</nav>")
    return "".join(out)


SORT_OPTIONS = {
    "home": [("", "Default order"), ("new", "Newest first"), ("old", "Oldest first")],
    "search": [("", "Relevance"), ("new", "Newest first"), ("old", "Oldest first")],
}


def sortbar(kind):
    opts = "".join(f'<option value="{v}">{t}</option>' for v, t in SORT_OPTIONS[kind])
    return f'<div class="sortbar"><label for="sort">Sort by</label><select id="sort">{opts}</select></div>'


def add_dates(body):
    """Home page: put data-date on every guide card and the date after its meta line. Safe to run again."""
    body = re.sub(r'<div class="sortbar">.*?</div>\n?', "", body, flags=re.S)
    body = re.sub(r' data-date="[^"]*"', "", body)
    body = re.sub(r' · \d{4}-\d{2}-\d{2}</span></a>', "</span></a>", body)

    def card(m):
        d = guide_date(m.group(2))
        return f'{m.group(1)} data-date="{d}"{m.group(3)} · {d}</span></a>'

    body = re.sub(r'(<a class="guide-card" href="guides/([^"]+)\.html")(.*?)</span></a>', card, body, flags=re.S)
    # category links at the top of the home page become filter buttons
    def chips(m):
        items = re.findall(r'<a href="#([^"]+)">(.*?)</a>', m.group(1))
        btns = ['<button class="chip" type="button" data-filter="all" aria-pressed="true">All</button>']
        btns += [f'<button class="chip" type="button" data-filter="{i}" aria-pressed="false">{t}</button>' for i, t in items]
        return '<div class="chips" role="group" aria-label="Filter guides">' + "".join(btns) + "</div>"

    body = re.sub(r'<nav class="chips" aria-label="Categories">(.*?)</nav>', chips, body, flags=re.S)
    return body.replace('<div class="cat-head">', sortbar("home") + "\n<div class=\"cat-head\">", 1)


def parts(text):
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
    desc = re.search(r'<meta name="description" content="(.*?)">', text, re.S).group(1)
    m = re.search(r"<main[^>]*>(.*)</main>", text, re.S)
    body = m.group(1)
    body = re.sub(r"<!--nav-->.*?<!--/nav-->", "", body, flags=re.S)
    return title, desc, body.strip()


def clean(s):
    return htmllib.unescape(re.sub(r"<[^>]+>", "", s)).strip()


# guide pages
index_rows = {}
for f in sorted((site / "guides").glob("*.html")):
    slug = f.stem
    g = by_slug[slug]
    title, desc, body = parts(f.read_text(encoding="utf-8"))
    heads = []
    for m in re.finditer(r"<h([23])([^>]*)>(.*?)</h\1>", body, re.S):
        t = clean(m.group(3))
        idm = re.search(r'id="([^"]+)"', m.group(2))
        if t:
            heads.append([t, idm.group(1) if idm else ""])
    index_rows[slug] = {"s": slug, "t": short(g["title"]), "c": g["cat"], "d": htmllib.unescape(desc), "h": heads, "dt": guide_date(slug)}
    crumb = (f'<!--nav--><nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Guides</a>'
             f'<span aria-hidden="true">/</span><a href="../index.html#{cat_id(g["cat"])}">{g["cat"]}</a>'
             f'<span aria-hidden="true">/</span><span>{short(g["title"])}</span></nav><!--/nav-->\n')
    page = (head(title, desc, "../") + header("../") + '<div class="page">\n' + sidebar("../", "", slug, g["cat"])
            + '<main class="guide">\n' + crumb + body + "\n<!--nav-->" + pager(slug) + "<!--/nav-->\n</main>\n</div>\n" + foot("../"))
    f.write_text(page, encoding="utf-8")

# home page
idx = site / "index.html"
title, desc, body = parts(idx.read_text(encoding="utf-8"))
idx.write_text(head(title, desc, "") + header("") + '<div class="page">\n' + sidebar("", "guides/", "home", None)
               + '<main class="home">\n' + add_dates(body) + "\n</main>\n</div>\n" + foot(""), encoding="utf-8")

# search page (results are drawn by js/site.js)
sbody = ('<h1>Search</h1>\n<p class="lede" id="result-summary"></p>\n<div class="chips" id="result-chips" role="group" aria-label="Filter results" hidden></div>\n' + sortbar("search") + '\n<ol class="results" id="results"></ol>')
(site / "search.html").write_text(
    head("Search | Lost Unison", "Search the Lost Unison guides", "") + header("") + '<div class="page">\n'
    + sidebar("", "guides/", "search", None) + '<main class="home">\n' + sbody + "\n</main>\n</div>\n" + foot(""), encoding="utf-8")

# search index
(site / "js").mkdir(exist_ok=True)
rows = [index_rows[g["slug"]] for g in order]
(site / "js" / "search-index.js").write_text("window.LU_INDEX=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print("layout ok:", len(order), "guides,", sum(len(r["h"]) for r in rows), "headings indexed")
