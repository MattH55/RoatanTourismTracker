"""
Embeddable widget and TV display, built with the site.

Copies into the site folder:
  widget.html   compact card other websites embed in an iframe (reads today.json)
  embed.js      loader script that inserts and auto-sizes the widget iframe
  tv.html       full-screen display for lobby and shop TVs (reads today.json)
  sponsors.json optional sponsor lines for tv.html, only if the file exists in the repo
and writes:
  embed.html    how-to page with live previews and copy-paste snippets

widget.html, embed.js and tv.html are plain files in widget_src/. Only the QR code
in tv.html is filled in here. All three read today.json, which seo_pages writes
alongside today.html.
"""
import json
import os
import shutil
from html import escape

from channel_page import _qr_svg
from seo_pages import page

SRC_DIR = 'widget_src'
SPONSORS = 'sponsors.json'
QR_SLOT = '<!--RTT_QR-->'

CARD_HEIGHT = 330     # starting iframe height in px; embed.js then sets the real height
COMPACT_HEIGHT = 90


def script_snippet(site_url, view='card', theme='auto', lang='en'):
    return (f'<div class="rtt-widget" data-view="{view}" data-theme="{theme}" data-lang="{lang}"></div>\n'
            f'<script src="{site_url}/embed.js" async></script>')


def iframe_snippet(site_url, view='card', theme='auto', lang='en'):
    title = 'Cruceros en Roatán hoy' if lang == 'es' else 'Roatan cruise ships today'
    size = ('width="100%" height="%d"' % COMPACT_HEIGHT if view == 'compact'
            else 'width="360" height="%d"' % CARD_HEIGHT)
    return (f'<iframe src="{site_url}/widget.html?view={view}&amp;theme={theme}&amp;lang={lang}" {size} '
            f'style="border:0;max-width:100%" loading="lazy" title="{title}"></iframe>')


EMBED_CSS = """
.previews { display: flex; flex-wrap: wrap; gap: 20px; margin: 10px 0 6px; }
.preview { flex: 1 1 320px; max-width: 420px; padding: 16px; border: 1px solid #30363d; border-radius: 10px; }
.preview.wide { flex-basis: 100%; max-width: none; }
.preview.on-light { background: #f3f5f8; }
.preview.on-dark { background: #0d1117; }
.preview h3 { font-size: 13px; font-weight: 600; margin-bottom: 10px; color: #8b949e; }
.preview.on-light h3 { color: #4b5563; }
.opts { display: flex; flex-wrap: wrap; gap: 14px; margin: 10px 0 14px; font-size: 14px; }
.opts select { margin-left: 6px; padding: 5px 8px; border-radius: 6px; border: 1px solid #30363d;
               background: #161b22; color: #e0e0e0; font-size: 14px; }
.snippet { position: relative; margin-bottom: 14px; }
.snippet pre { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 14px 44px;
               font: 13px/1.5 Consolas, 'Courier New', monospace; white-space: pre-wrap; word-break: break-all; color: #c9d1d9; }
.snippet button { position: absolute; right: 10px; bottom: 10px; padding: 6px 14px; border-radius: 6px; border: 0;
                  background: #2E86AB; color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; }
.snippet button:hover { background: #3a9cc4; }
"""

EMBED_JS = """
(function () {
  var SITE = %(site)s;
  var CARD_H = %(card_h)d, COMPACT_H = %(compact_h)d;
  function val(id) { return document.getElementById(id).value; }
  function update() {
    var view = val('optView'), theme = val('optTheme'), lang = val('optLang');
    document.getElementById('snipScript').textContent =
      '<div class="rtt-widget" data-view="' + view + '" data-theme="' + theme + '" data-lang="' + lang + '"></div>\\n' +
      '<script src="' + SITE + '/embed.js" async></' + 'script>';
    document.getElementById('snipIframe').textContent =
      '<iframe src="' + SITE + '/widget.html?view=' + view + '&amp;theme=' + theme + '&amp;lang=' + lang + '" ' +
      (view === 'compact' ? 'width="100%%" height="' + COMPACT_H + '"' : 'width="360" height="' + CARD_H + '"') +
      ' style="border:0;max-width:100%%" loading="lazy" title="' +
      (lang === 'es' ? 'Cruceros en Roat\\u00e1n hoy' : 'Roatan cruise ships today') + '"></iframe>';
  }
  ['optView', 'optTheme', 'optLang'].forEach(function (id) {
    document.getElementById(id).addEventListener('change', update);
  });
  function copied(btn) {
    var old = btn.textContent;
    btn.textContent = 'Copied';
    setTimeout(function () { btn.textContent = old; }, 1500);
  }
  Array.prototype.forEach.call(document.querySelectorAll('button[data-copy]'), function (btn) {
    btn.addEventListener('click', function () {
      var text = document.getElementById(btn.getAttribute('data-copy')).textContent;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { copied(btn); }, function () { fallback(text, btn); });
      } else { fallback(text, btn); }
    });
  });
  function fallback(text, btn) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { if (document.execCommand('copy')) copied(btn); } catch (e) { /* user can select the text */ }
    document.body.removeChild(ta);
  }
  update();
})();
"""


def embed_page(site_url, build_date):
    def card(theme, label):
        return (f'<div class="preview on-{theme}"><h3>{label}</h3>'
                f'<div class="rtt-widget" data-view="card" data-theme="{theme}" data-lang="en"></div></div>')

    def compact(theme, label):
        return (f'<div class="preview wide on-{theme}"><h3>{label}</h3>'
                f'<div class="rtt-widget" data-view="compact" data-theme="{theme}" data-lang="en"></div></div>')

    js = EMBED_JS % {'site': json.dumps(site_url), 'card_h': CARD_HEIGHT, 'compact_h': COMPACT_HEIGHT}
    body = f"""
    <p class="lead">A free widget for hotels, dive shops, tour operators and rental agencies: it shows your
    guests how many cruise ships are in Roatan today and how busy the island will be.</p>
    <p>It updates itself every day. Paste the code once and there is nothing else to maintain.
    It works in English and Spanish, in light and dark, and on phones.</p>

    <h2>Card</h2>
    <div class="previews">
        {card('light', 'Light')}
        {card('dark', 'Dark')}
    </div>

    <h2>Compact bar</h2>
    <div class="previews">
        {compact('light', 'Light, for a banner or sidebar')}
        {compact('dark', 'Dark')}
    </div>

    <h2>Add it to your website</h2>
    <div class="opts">
        <label>View <select id="optView"><option value="card">Card</option><option value="compact">Compact bar</option></select></label>
        <label>Colours <select id="optTheme"><option value="auto">Match the visitor's device</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
        <label>Language <select id="optLang"><option value="en">English</option><option value="es">Espa&ntilde;ol</option></select></label>
    </div>
    <p><strong>Recommended:</strong> paste this where the widget should appear. It sets its own height.</p>
    <div class="snippet"><pre id="snipScript">{escape(script_snippet(site_url))}</pre>
        <button type="button" data-copy="snipScript">Copy</button></div>
    <p><strong>If your website builder does not allow scripts,</strong> use this plain iframe instead.</p>
    <div class="snippet"><pre id="snipIframe">{escape(iframe_snippet(site_url))}</pre>
        <button type="button" data-copy="snipIframe">Copy</button></div>

    <h2>For a TV in your lobby or shop</h2>
    <p>Open <a href="tv.html">{site_url.split('://', 1)[1]}/tv.html</a> in the TV's browser and leave it running.
    It shows today's and tomorrow's ships, refreshes on its own, and has a QR code to the full schedule.
    Add <code>?lang=es</code> for Spanish, <code>?rotate=1</code> to alternate English and Spanish,
    or <code>?theme=light</code> for a light background.</p>

    <p class="note">The widget links back to roatantourismtracker.online; please keep that link visible.
    Cruise calls come from published port schedules and can change, and passenger figures are estimates.</p>
    <script src="embed.js"></script>
    <script>{js}</script>
"""
    return page(site_url, 'embed.html',
                'Roatan Cruise Ship Widget for Your Website | Roatan Tourism Tracker',
                'Free widget showing how many cruise ships are in Roatan today and how busy it will be. '
                'For hotels, dive shops, tour operators and rental agencies. Updates itself daily.',
                'Add Roatan Cruise Ships to Your Website', body, build_date,
                extra_head=f'<style>{EMBED_CSS}</style>')


def write_widget_pages(output_dir, site_url, build_date):
    """Write the widget, loader, TV page and how-to page. Returns the file names written."""
    written = []
    for name in ('widget.html', 'embed.js'):
        shutil.copyfile(os.path.join(SRC_DIR, name), os.path.join(output_dir, name))
        written.append(name)

    with open(os.path.join(SRC_DIR, 'tv.html'), encoding='utf-8') as f:
        tv = f.read()
    if QR_SLOT not in tv:
        raise RuntimeError(f'{SRC_DIR}/tv.html has no {QR_SLOT} placeholder for the QR code')
    with open(os.path.join(output_dir, 'tv.html'), 'w', encoding='utf-8') as f:
        f.write(tv.replace(QR_SLOT, _qr_svg(site_url + '/today.html')))
    written.append('tv.html')

    with open(os.path.join(output_dir, 'embed.html'), 'w', encoding='utf-8') as f:
        f.write(embed_page(site_url, build_date))
    written.append('embed.html')

    # Sponsors are optional: no file (or an empty list) means the TV shows no sponsor strip.
    target = os.path.join(output_dir, SPONSORS)
    if os.path.exists(SPONSORS):
        with open(SPONSORS, encoding='utf-8') as f:
            sponsors = json.load(f)
        if not isinstance(sponsors, list):
            raise RuntimeError(f'{SPONSORS} must be a JSON array of {{name, text, url, image}}')
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(sponsors, f, ensure_ascii=False)
        written.append(SPONSORS)
    elif os.path.exists(target):
        os.remove(target)
    return written


if __name__ == '__main__':
    # Quick rebuild of just these files (and today.json) without the 4-minute chart build:
    #   python widget_pages.py [output_dir]
    import sys
    from datetime import datetime, timezone

    from app import AVAILABLE_MONTHS, load_monthly_data
    from daily_message import roatan_today
    from seo_pages import TODAY_JSON, check_today_json, today_json, today_page

    out = sys.argv[1] if len(sys.argv) > 1 else 'static_site'
    site = 'https://roatantourismtracker.online'
    os.makedirs(out, exist_ok=True)
    build_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    all_data = {ym: load_monthly_data(*ym) for ym in AVAILABLE_MONTHS}
    today = roatan_today()
    data = today_json(site, all_data, today)
    problems = check_today_json(today_page(site, all_data, build_date, today), data, today)
    if problems:
        raise SystemExit('today.json does not match today.html: ' + '; '.join(problems))
    with open(os.path.join(out, TODAY_JSON), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('[OK]', ', '.join([TODAY_JSON] + write_widget_pages(out, site, build_date)))
