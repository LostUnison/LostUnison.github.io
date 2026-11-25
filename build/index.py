import json, sys
from pathlib import Path

site = Path(sys.argv[1])
data = json.load(open(site.parent / "build-summary.json"))
guides = data["guides"]
fa = {"slug": "first-aid", "title": "First Aid 1 to 450 (x3)", "cat": "Professions",
      "desc": "Every bandage, how many to craft, the cloth to buy and where to get the Heavy Frostweave manual.",
      "videos": []}
i = next(k for k, g in enumerate(guides) if g["slug"] == "fishing")
guides.insert(i + 1, fa)

cats = ["Leveling", "Professions", "Addons", "Gearing", "Reputation", "Gold making", "Game client"]
video_only = [
    ("5pSnmXrAAf8", "How to Unlock Ebon Blade Quartermaster"),
    ("g1cRvdPjSXg", "Sons of Hodir Questline, Unlock Quartermaster Fast"),
    ("aBMJCuHHwtM", "Artisan Riding 1000 Gold Discount"),
]

head = ('<title>Lost Unison Guides</title>\n<meta name="description" content="Clear and practical World of Warcraft WotLK guides for Warmane Icecrown (3.3.5a), by Lost Unison.">\n')
foot = ""
chips = "".join(f'<a href="#{c.lower().replace(" ", "-")}">{c}</a>' for c in cats if any(g["cat"] == c for g in guides)) + '<a href="#video-guides">Video guides</a>'
out = [head, "<main>\n<section class=\"hero\">\n<img class=\"hero-logo\" src=\"images/logo.svg\" width=\"150\" height=\"150\" alt=\"\">\n<div class=\"prose\">\n<h1>WotLK guides for Warmane Icecrown</h1>\n",
       f'<p class="lede">Clear and practical World of Warcraft guides for Warmane Icecrown (3.3.5a): {len(guides)} written guides on leveling, professions, gearing, reputations, addons and gold making. Most of them match a video on the YouTube channel.</p>\n</div>\n</section>\n', f'<nav class="chips" aria-label="Categories">{chips}</nav>\n']
for c in cats:
    gs = [g for g in guides if g["cat"] == c]
    if not gs:
        continue
    out.append(f'<div class="cat-head"><h2 id="{c.lower().replace(" ", "-")}">{c}</h2><span class="count">{len(gs)} guide{"s" if len(gs) > 1 else ""}</span></div>\n<div class="guide-grid">\n')
    for g in gs:
        meta = '<span class="meta"><span class="yt">Video</span> + written guide</span>' if g["videos"] else '<span class="meta">Written guide</span>'
        out.append(f'<a class="guide-card" href="guides/{g["slug"]}.html"><span class="title">{g["title"]}</span><span class="desc">{g["desc"]}</span>{meta}</a>\n')
    out.append("</div>\n")
out.append('<div class="cat-head"><h2 id="video-guides">Video guides</h2><span class="count">on YouTube</span></div>\n<div class="guide-grid">\n')
for vid, t in video_only:
    out.append(f'<a class="guide-card" href="https://www.youtube.com/watch?v={vid}"><span class="title">{t}</span><span class="meta"><span class="yt">Video</span> on YouTube</span></a>\n')
out.append("</div>\n</main>\n\n")
out.append(foot)
(site / "index.html").write_text("".join(out), encoding="utf-8")
print("index ok", len(guides))
