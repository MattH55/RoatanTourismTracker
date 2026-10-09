"""
WhatsApp Channel sign-up: /canal.html (also prints as a flyer) and the
"daily update" bar shown on the other pages.

Set WHATSAPP_CHANNEL_URL below to your Channel's invite link
(WhatsApp Business app: Updates > your channel > Channel info > Share link).
Until it is set, canal.html says "coming soon" and the bar is hidden.
"""
import html
import io
import os
import re
from datetime import timedelta

import qrcode
import qrcode.image.svg

from daily_message import build_message, roatan_today

WHATSAPP_CHANNEL_URL = ''  # e.g. 'https://whatsapp.com/channel/0029Va...'

PAGE = 'canal.html'


def channel_url():
    return os.environ.get('WHATSAPP_CHANNEL_URL', WHATSAPP_CHANNEL_URL).strip()


def channel_bar_html():
    """Small bar linking to the sign-up page; empty until the Channel link is set."""
    if not channel_url():
        return ''
    return (f'<a class="wa-bar" href="{PAGE}">📲 <strong>Aviso diario de cruceros por WhatsApp</strong> '
            f'· Daily cruise ship update on WhatsApp → <u>Seguir / Follow</u></a>')


CHANNEL_BAR_CSS = """
.wa-bar {
    display: block; margin: 0 0 16px; padding: 10px 14px; border-radius: 8px;
    background: #12301f; border: 1px solid #25a35a; color: #e6e9ee;
    text-decoration: none; font-size: 14px; line-height: 1.4;
}
.wa-bar:hover { border-color: #3ccf77; }
.wa-bar strong { color: #3ccf77; }
"""


def _qr_svg(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2,
                      error_correction=qrcode.constants.ERROR_CORRECT_Q)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode('utf-8')
    svg = re.sub(r'^<\?xml[^>]*\?>\s*', '', svg)
    # Scale with its container instead of a fixed size in mm.
    return re.sub(r'\swidth="[^"]*"\sheight="[^"]*"', ' role="img" aria-label="QR code"', svg, count=1)


def write_channel_page(output_dir, site_url):
    url = channel_url()
    sample = build_message(roatan_today() + timedelta(days=1), 'MAÑANA', 'TOMORROW')
    if url:
        action = (f'<a class="follow" href="{html.escape(url)}">Seguir en WhatsApp / Follow on WhatsApp</a>'
                  f'<div class="qr">{_qr_svg(url)}</div>'
                  f'<p class="scan">Escanee con la cámara del teléfono · Scan with your phone camera</p>')
    else:
        action = '<p class="soon">Canal disponible pronto · Channel coming soon</p>'

    page = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aviso diario de cruceros en Roatán por WhatsApp | Roatan Tourism Tracker</title>
<meta name="description" content="Siga el canal de WhatsApp: qué cruceros llegan a Roatán cada día, horarios, cuántos visitantes y qué tan ocupado estará. Daily Roatan cruise ship update on WhatsApp.">
<link rel="canonical" href="{site_url}/{PAGE}">
<meta property="og:title" content="Aviso diario de cruceros en Roatán · Daily Roatan cruise update">
<meta property="og:description" content="Ships, times and crowd level for tomorrow, every evening on WhatsApp.">
<meta property="og:url" content="{site_url}/{PAGE}">
<meta property="og:type" content="website">
<style>
  :root {{ --bg: #0d1117; --card: #161b22; --text: #e6e9ee; --muted: #8b949e; --border: #30363d; --green: #25a35a; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 20px 16px; background: var(--bg); color: var(--text);
         font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; line-height: 1.45; }}
  main {{ max-width: 620px; margin: 0 auto; text-align: center; }}
  h1 {{ font-size: 28px; margin: 8px 0 4px; }}
  .en {{ color: var(--muted); font-size: 17px; margin: 0 0 20px; }}
  .follow {{ display: inline-block; padding: 16px 22px; border-radius: 12px; background: var(--green);
            color: #fff; font-size: 19px; font-weight: 700; text-decoration: none; }}
  .qr {{ width: 220px; margin: 20px auto 6px; padding: 10px; background: #fff; border-radius: 10px; }}
  .qr svg {{ width: 100%; height: auto; display: block; }}
  .scan, .soon {{ color: var(--muted); font-size: 14px; }}
  .soon {{ font-size: 18px; padding: 14px; border: 1px dashed var(--border); border-radius: 10px; }}
  ul {{ text-align: left; display: inline-block; margin: 20px auto; padding-left: 20px; }}
  li {{ margin-bottom: 8px; }}
  li span {{ color: var(--muted); }}
  .sample {{ text-align: left; background: var(--card); border: 1px solid var(--border); border-radius: 12px;
            padding: 14px; margin: 8px 0 20px; }}
  .sample h2 {{ font-size: 14px; color: var(--muted); margin: 0 0 8px; text-transform: uppercase; letter-spacing: .5px; }}
  pre {{ white-space: pre-wrap; margin: 0; font: 14px/1.45 -apple-system, 'Segoe UI', Roboto, sans-serif; }}
  .fine {{ color: var(--muted); font-size: 13px; }}
  a {{ color: #3ccf77; }}
  @media print {{
    @page {{ size: letter; margin: 0.6in; }}
    body {{ background: #fff; color: #000; padding: 0; }}
    .en, .scan, .fine, li span {{ color: #333; }}
    .follow, .sample, .print-hide {{ display: none; }}
    h1 {{ font-size: 34pt; }}
    .qr {{ width: 3.6in; border: 1px solid #ccc; }}
    li {{ font-size: 15pt; }}
  }}
</style>
</head>
<body>
<main>
  <h1>🛳️ Cruceros en Roatán: aviso diario por WhatsApp</h1>
  <p class="en">Roatán cruise ships: daily update on WhatsApp</p>
  {action}
  <ul>
    <li>🚢 Qué barcos llegan y a qué hora <span>· Which ships arrive and when</span></li>
    <li>👥 Cuántos visitantes y qué tan ocupado <span>· How many visitors, how busy</span></li>
    <li>⏰ Hora de regreso al barco <span>· Return-to-ship rush</span></li>
    <li>📅 Pronóstico de 3 días <span>· 3-day outlook</span></li>
    <li>🆓 Gratis · Free</li>
  </ul>
  <div class="sample print-hide">
    <h2>Ejemplo / Sample</h2>
    <pre>{html.escape(sample)}</pre>
  </div>
  <p class="fine">Es un canal: solo publicamos nosotros y su número no es visible para otros.
    Puede dejar de seguirlo cuando quiera.<br>
    It's a WhatsApp Channel: only we post, and your number isn't shown to anyone. Unfollow any time.</p>
  <p class="fine print-hide"><a href="index.html">Roatan Tourism Tracker</a> · {site_url.split('://', 1)[1]}</p>
</main>
</body>
</html>
'''
    with open(os.path.join(output_dir, PAGE), 'w', encoding='utf-8') as f:
        f.write(page)
