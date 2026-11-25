"""Build Lost Unison guide pages from the pandoc HTML of the Google Doc export.

Usage: python3 build.py <full.html> <media root> <site dir>
"""
import re
import sys
import json
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from PIL import Image

FULL, MEDIA_ROOT, SITE = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
html = open(FULL, encoding="utf-8").read()
YT = "https://www.youtube.com/watch?v="

# slug, title, category, start marker, end marker, videos [(id, label)], description
GUIDES = [
    ("power-leveling", "Power Leveling 1 to 80 (no boost)", "Leveling", 751, 13099,
     [("NwkLeox0IJ0", "How to Reach 80 with no Boost")],
     "Level a new character from 1 to 80 with dungeon runs and an alt, step by step."),
    ("paladin-leveling", "Paladin Leveling 1 to 80", "Leveling", 13099, 22717, [],
     "Race, talents, glyphs, skills and a leveling plan for Paladins."),
    ("alchemy", "Alchemy 1 to 450 (x3), Specializations and Gold Making", "Professions", 38030, 53248,
     [("aqbOYf7BQIc", "Alchemy 1 to 450")],
     "Mixology bonus, full leveling route, which specialization to pick and how to make gold."),
    ("blacksmithing", "Blacksmithing 1 to 450 (x3), Bonuses and Gold Making", "Professions", 53248, 66843,
     [("ltSB44-jh9U", "Blacksmithing 1 to 450")],
     "Socket bonus, materials, leveling route and what to craft for gold."),
    ("engineering", "Engineering 1 to 450 (x3), Bonuses and Gold Making", "Professions", 66843, 85245,
     [("PbE14MqDYAg", "Engineering 1 to 450")],
     "Tinkers, Nitro Boots, full leveling route and gold making."),
    ("enchanting", "Enchanting 1 to 450 (x3), Bonuses and Gold Making", "Professions", 85245, 115251,
     [("Xacr1i0HmpI", "Enchanting 1 to 450")],
     "Ring enchants, formulas, trainers, leveling route, vellums and scrolls for gold."),
    ("inscription", "Inscription 1 to 450 (x3) and Bonuses", "Professions", 115251, 142308,
     [("SLPWjKWKi1A", "Inscription 1 to 450")],
     "Shoulder inscriptions, pigments from milling and the full leveling route."),
    ("jewelcrafting", "Jewelcrafting 1 to 450 (x3) and Bonuses", "Professions", 142308, 158657,
     [("B_rpImoeogk", "Jewelcrafting 1 to 450")],
     "Dragon's Eye gems, daily tokens, trinkets, leveling route and the Saronite shuffle."),
    ("leatherworking", "Leatherworking 1 to 450 (x3) and Bonuses", "Professions", 158657, 175324,
     [("2GXSGoJqeeU", "Leatherworking 1 to 450")],
     "Fur linings, leveling route and what to craft for gold."),
    ("tailoring", "Tailoring 1 to 450 (x3), Bonuses and Gold Making", "Professions", 175324, 192538,
     [("N75EOPEzFv0", "Tailoring 1 to 450")],
     "Cloak embroideries, leveling route, bags, leg enchants and gear for gold."),
    ("skinning", "Skinning 1 to 450 (x3) and Bonuses", "Professions", 192538, 198896,
     [("RccTL-VHsIQ", "Skinning 1 to 450")],
     "Master of Anatomy, where to skin at each level and trainers."),
    ("mining", "Mining 1 to 450 (x3) and Bonuses", "Professions", 198896, 211491,
     [("-lhCVBJ3adA", "Mining 1 to 450")],
     "Toughness bonus, addons, smelting and mining routes, trainers."),
    ("herbalism", "Herbalism 1 to 450 (x3) and Bonuses", "Professions", 211491, 217701,
     [("fWLB_q8EoBg", "Herbalism 1 to 450")],
     "Lifeblood, addons, where to pick herbs at each level and trainers."),
    ("cooking", "Cooking 1 to 450", "Professions", 217701, 223724,
     [("CspaRVRIQWk", "Cooking 1 to 450")],
     "Recipes, materials, Northern Stew and the Dalaran daily quests."),
    ("fishing", "Fishing 1 to 450, Find Fish, Sea Turtle and Heirloom Ring", "Professions", 223724, 229038,
     [("NLPv-56PrdE", "Fishing 1 to 450"), ("LoX-TBme9S4", "Sea Turtle Mount"), ("umxfhgxVz4s", "Heirloom Ring")],
     "Fishing macro, leveling, the Find Fish book, the Sea Turtle and the Kalu'ak Fishing Derby."),
    ("tsm-part-1", "TSM (TradeSkill Master) Part 1", "Addons", 24032, 33683,
     [("iHRTpIqdHQY", "How to use TSM, Part 1")],
     "Download, install and configure TSM, then scan and buy on the Auction House."),
    ("all-264-boe", "All 264 Item Level BoE", "Gearing", 240373, 262291, [],
     "Every 264 item level Bind on Equip piece, by armor type and by class."),
    ("unlock-heroic-dungeons", "Unlock Heroic Dungeons", "Gearing", 262291, 272767, [],
     "Reach the item level needed for heroics with cheap BoE, trinkets and relics."),
    ("thorium-brotherhood", "Thorium Brotherhood Neutral to Revered", "Reputation", 237880, 240373,
     [("Tp2JVm3nl90", "Thorium Brotherhood to Revered")],
     "Materials, the repeatable quests and how to reach Lokhtos Darkbargainer."),
    ("ashen-verdict", "Ashen Verdict Reputation Farm", "Reputation", 376686, None, [],
     "Why farm the Ashen Verdict, requirements, how the farm works and rewards."),
    ("gold-farming", "Best Gold Farming (2,893 gold/h)", "Gold making", 367549, 376686,
     [("_bGr2ygqGQ8", "Best Gold Farming")],
     "Fishing and gathering routes with gold per hour, plus Stoneguard Band disenchanting."),
    ("windowed-mode", "Windowed Mode", "Game client", 237232, 237880, [],
     "Play the 3.3.5a client in a window with one line in Config.wtf."),
]

# heading text fixes (copy errors in the doc)
HEADING_FIXES = {
    "jewelcrafting": [("Leveling Enchanting from 1 to 450", "Leveling Jewelcrafting from 1 to 450")],
    "mining": [("Leveling Inscription From 1 to 450", "Leveling Mining from 1 to 450")],
}

img_cache = {}
issues = []


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def convert_image(src, slug, n):
    key = src
    if key in img_cache:
        return img_cache[key]
    p = MEDIA_ROOT / src.replace("media/", "", 1) if not (MEDIA_ROOT / src).exists() else MEDIA_ROOT / src
    im = Image.open(p)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    if im.width > 1400:
        im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
    out = SITE / "images" / f"{slug}-{n:02d}.webp"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "WEBP", quality=80, method=6)
    img_cache[key] = (f"../images/{out.name}", im.width, im.height)
    return img_cache[key]


def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s or "section"


def build(slug, start, end):
    frag = html[start:end] if end else html[start:]
    soup = BeautifulSoup(frag, "html.parser")

    # page title headings from the doc
    for h in soup.find_all(["h1"]):
        t = norm(h.get_text())
        if "by Lost" in t or t.startswith("Warmane Paladin") or t.startswith("WotLK Warmane") or t.startswith("WotLK -"):
            h.decompose()
    for p in soup.find_all("p"):
        t = norm(p.get_text())
        if t.endswith("by Lost Unison") and len(t) < 120:
            p.decompose()

    # Word table of contents: drop from "Table of Contents" to the next heading
    for p in soup.find_all("p"):
        if p.parent is None:
            continue
        if norm(p.get_text()) == "Table of Contents":
            nxt = p.find_next_sibling()
            p.decompose()
            while nxt is not None and not re.match(r"h[1-6]$", nxt.name or ""):
                cur, nxt = nxt, nxt.find_next_sibling()
                cur.decompose()

    # empty headings out, then demote h1..h5 by one level
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        if not norm(h.get_text()) and not h.find("img"):
            h.decompose()
    heads = soup.find_all(re.compile(r"^h[1-6]$"))
    shift = 2 - min((int(h.name[1]) for h in heads), default=1)
    for h in heads:
        lvl = int(h.name[1])
        h.name = f"h{max(2, min(lvl + shift, 6))}"
        h.attrs = {}
        txt = norm(h.get_text())
        for a, b in HEADING_FIXES.get(slug, []):
            if txt == a:
                h.string = b
                issues.append((slug, f'Heading "{a}" changed to "{b}"'))
        if h.get_text() != norm(h.get_text()):
            new = norm(h.get_text())
            if not h.find(["a", "img"]):
                h.string = new

    # ids and the page table of contents
    toc, used = [], set()
    for h in soup.find_all("h2"):
        base = slugify(h.get_text())
        sid, i = base, 2
        while sid in used:
            sid, i = f"{base}-{i}", i + 1
        used.add(sid)
        h["id"] = sid
        toc.append((sid, norm(h.get_text())))

    # images
    n = 0
    for img in soup.find_all("img"):
        n += 1
        style = img.get("style", "")
        m = re.search(r"width:([\d.]+)in", style)
        src, w, hgt = convert_image(img["src"], slug, n)
        img.attrs = {"src": src, "alt": "", "loading": "lazy", "width": str(w), "height": str(hgt)}
        if m:
            img["style"] = f"max-width:min(100%, {round(float(m.group(1)) * 96)}px)"

    # tables scroll on their own; drop pandoc column widths
    for t in soup.find_all("table"):
        for c in t.find_all("colgroup"):
            c.decompose()
        t.attrs = {}
        # Docs exports mark many rows as header rows: keep only the first one as header
        thead = t.find("thead")
        if thead:
            rows = thead.find_all("tr", recursive=False)
            if len(rows) > 1:
                tbody = t.find("tbody")
                if tbody is None:
                    tbody = soup.new_tag("tbody")
                    t.append(tbody)
                for r in reversed(rows[1:]):
                    for c in r.find_all("th", recursive=False):
                        c.name = "td"
                    tbody.insert(0, r.extract())
        wrap = soup.new_tag("div", attrs={"class": "table-wrap"})
        t.wrap(wrap)

    # links open the real target; doc-internal anchors to removed TOC are dropped
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href.startswith("#"):
            a.unwrap()
        else:
            a.attrs = {"href": href}

    # pandoc wraps list items in blockquotes for indented text
    for bq in soup.find_all("blockquote"):
        if bq.parent and bq.parent.name == "li":
            bq.unwrap()

    out = str(soup)
    out = out.replace("—", " - ")
    out = re.sub(r"<p>\s*</p>", "", out)
    return out, toc, n


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}css/style.css">
</head>
<body>
<header class="site-header">
  <div class="inner">
    <a class="brand" href="{root}index.html">
      <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true">
        <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="none" stroke="#8cc8ff" stroke-width="2"/>
        <text x="20" y="25.5" text-anchor="middle" font-family="Marcellus, Georgia, serif" font-size="14" fill="#e3b75e">LU</text>
      </svg>
      <span><span class="brand-name">Lost Unison</span><span class="brand-sub">WotLK Warmane Icecrown Guides</span></span>
    </a>
    <nav class="site-nav" aria-label="Main">
      <a href="{root}index.html"{cur}>Guides</a>
      <a href="https://www.youtube.com/@lostunison">YouTube</a>
      <a href="https://discord.gg/md4a6BgUTs">Discord</a>
    </nav>
  </div>
</header>
"""

FOOT = """
<footer class="site-footer">
  <div class="inner">
    <span>Guides by Lost Unison</span>
    <span><a href="https://www.youtube.com/@lostunison">YouTube</a> · <a href="https://discord.gg/md4a6BgUTs">Discord</a></span>
  </div>
</footer>
</body>
</html>
"""

summary = []
for slug, title, cat, start, end, videos, desc in GUIDES:
    body, toc, nimg = build(slug, start, end)
    full_title = f"WotLK Warmane Icecrown - {title}"
    parts = [HEAD.format(title=title, desc=desc.replace('"', "&quot;"), root="../", cur="")]
    parts.append('<main class="guide">\n<div class="prose">\n')
    parts.append(f"<h1>{full_title}</h1>\n")
    parts.append('<p class="byline">Guide by <strong>Lost Unison</strong></p>\n')
    parts.append(f'<p class="lede">{desc}</p>\n</div>\n')
    if videos:
        parts.append('<div class="video-links">')
        for vid, label in videos:
            parts.append(f'<a class="video-btn" href="{YT}{vid}"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5v11l9-5.5z" fill="currentColor"/></svg>Watch the video: {label}</a>')
        parts.append("</div>\n")
    if len(toc) >= 3:
        parts.append('<nav class="toc" aria-label="On this page"><span class="toc-title">On this page</span><ol>')
        parts += [f'<li><a href="#{i}">{t}</a></li>' for i, t in toc]
        parts.append("</ol></nav>\n")
    parts.append('<div class="doc">\n' + body + "\n</div>\n</main>\n")
    parts.append(FOOT)
    (SITE / "guides").mkdir(parents=True, exist_ok=True)
    (SITE / "guides" / f"{slug}.html").write_text("".join(parts), encoding="utf-8")
    summary.append({"slug": slug, "title": title, "cat": cat, "desc": desc, "videos": videos, "images": nimg, "sections": len(toc)})

json.dump({"guides": summary, "issues": issues}, open(SITE.parent / "build-summary.json", "w"), indent=1)
for s in summary:
    print(f'{s["slug"]:24} images={s["images"]:3} sections={s["sections"]}')
print(issues)
