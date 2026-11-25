# Deploy checklist (2026-11-25)

Site folder: `site/` (static, 8 MB, no build step at deploy time). Checked: 0 broken internal links, no local or preview URLs inside pages.

## Before each deploy
1. Run `python3 build/build.py`, `python3 build/index.py`, `python3 build/layout.py` (in this order) if guides changed.
2. Run `python3 build/make-sitemap.py <final base URL>`.

## Option A: GitHub Pages (workflow ready)
1. Create a GitHub repository. Use `06 Website/` as the repository root.
2. Push to branch `main`.
3. In the repository, open Settings > Pages and set Source to GitHub Actions.
4. The workflow `.github/workflows/pages.yml` publishes `site/`.
5. For a repository page (user.github.io/repo), links use relative paths and work. The 404 page link `/` needs the domain root: use a custom domain, or edit the link.

## Option B: own domain
1. Upload the content of `site/` to the host root.
2. For GitHub Pages with a custom domain, add a `site/CNAME` file with the domain name.

## Decisions still open
- Hosting choice and final domain.
- Then change the guide line in the YouTube descriptions to the website page.
- Pages have no Open Graph tags (link previews on Discord and social networks show no image). Add them in `layout.py` if wanted.
- Fonts load from Google Fonts (external request).
