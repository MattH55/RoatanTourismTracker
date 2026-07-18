"""
Patch deployed site files (repo root + static_site mirror):
1. Fix mojibake degree symbol (\\u00c2\\u00b0 -> \\u00b0) in month pages
2. Point month-page "All months" links at index.html#all (redirect escape hatch)
3. Add footer links to the new dive & map pages on month pages
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = [ROOT, ROOT / 'static_site']

MONTHS = [f"{y}-{m:02d}" for y in (2026, 2027, 2028)
          for m in range(1, 13)
          if (y, m) >= (2026, 6) and (y, m) <= (2028, 11)]

GA_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-L2LFYE0L4B"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-L2LFYE0L4B');
</script>
"""

FOOTER_LINKS = ('<a href="index.html#all" style="color:#484f58;">All months</a> &mdash; '
                '<a href="dive-certifications.html" style="color:#484f58;">Dive Certifications</a> &mdash; '
                '<a href="things-to-do.html" style="color:#484f58;">Map &amp; Things to Do</a>')

for d in DIRS:
    for mk in MONTHS:
        p = d / f"{mk}.html"
        if not p.exists():
            print(f"[skip] {p} (missing)")
            continue
        html = p.read_text(encoding='utf-8')
        orig = html

        # 1. Fix mojibake degree symbol in embedded Plotly JSON
        html = html.replace('\\u00c2\\u00b0', '\\u00b0')
        # also fix any literal mojibake outside JSON
        html = html.replace('Â°', '°')

        # 2. All-months links -> #all so index redirect can be bypassed
        html = html.replace('href="index.html"', 'href="index.html#all"')
        # avoid double-hash if run twice
        html = html.replace('index.html#all#all', 'index.html#all')

        # 3. Footer cross-links (replace the plain All months link once)
        html = html.replace(
            '<a href="index.html#all" style="color:#484f58;">All months</a>',
            FOOTER_LINKS, 1)
        # avoid duplicating if run twice
        html = html.replace(FOOTER_LINKS + ' &mdash; '
                            '<a href="dive-certifications.html" style="color:#484f58;">Dive Certifications</a> &mdash; '
                            '<a href="things-to-do.html" style="color:#484f58;">Map &amp; Things to Do</a>',
                            FOOTER_LINKS)

        # 4. Ensure GA present
        if 'G-L2LFYE0L4B' not in html:
            html = html.replace('<head>', '<head>\n' + GA_SNIPPET, 1)

        if html != orig:
            p.write_text(html, encoding='utf-8')
            print(f"[patched] {p.relative_to(ROOT)}")
        else:
            print(f"[ok] {p.relative_to(ROOT)} (no changes)")

print("Done.")
