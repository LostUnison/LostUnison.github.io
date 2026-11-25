"""Write site/sitemap.xml and add the Sitemap line to site/robots.txt.
Usage: python3 make-sitemap.py https://example.com   (no trailing slash; for a repo page: https://user.github.io/repo)
"""
import sys, glob, os
base = sys.argv[1].rstrip('/')
site = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
pages = ['index.html'] + sorted(glob.glob('guides/*.html', root_dir=site))
urls = ['%s/' % base if p == 'index.html' else '%s/%s' % (base, p) for p in pages]
xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join('<url><loc>%s</loc></url>\n' % u for u in urls) + '</urlset>\n'
open(os.path.join(site, 'sitemap.xml'), 'w', encoding='utf-8').write(xml)
open(os.path.join(site, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % base)
print(len(urls), 'urls')
