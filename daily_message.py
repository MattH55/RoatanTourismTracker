"""
Daily WhatsApp update text, generated with the site.

Writes into the site folder:
  hoy.txt       today's ships (post in the morning)
  manana.txt    tomorrow's ships (post in the evening)
  whatsapp.html both messages with copy buttons

Dates are Roatan local time (UTC-6, no daylight saving).
"""
import html
import json
import os
from datetime import datetime, timedelta, timezone

SITE = 'roatantourismtracker.online'
FLIGHTS_DIR = 'flights'
ROATAN_TZ = timezone(timedelta(hours=-6))
OUTLOOK_DAYS = 3

DAYS_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
MONTHS_ES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

# (minimum cruise visitors, icon, Spanish, English)
LEVELS = [
    (10000, '🔴', 'Muy ocupado', 'Very busy'),
    (6000, '🟠', 'Ocupado', 'Busy'),
    (3000, '🟡', 'Moderado', 'Moderate'),
    (1, '🟢', 'Tranquilo', 'Quiet'),
    (0, '⚪', 'Sin cruceros', 'No cruise ships'),
]


def roatan_today():
    return datetime.now(ROATAN_TZ).date()


def _cruises_on(day, cache):
    key = (day.year, day.month)
    if key not in cache:
        path = f'tourism_{day.year:04d}_{day.month:02d}.json'
        cache[key] = None
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                cache[key] = json.load(f)
    data = cache[key]
    if data is None or day.isoformat() not in data['days']:
        return None
    cruises = data['days'][day.isoformat()].get('cruises', [])
    return sorted(cruises, key=lambda c: (c.get('arrival_hour', 0), c.get('ship_name', '')))


def _level(pax):
    for minimum, icon, es, en in LEVELS:
        if pax >= minimum:
            return icon, es, en
    return LEVELS[-1][1:]


def _hour(h):
    h = int(h) % 24
    suffix = 'am' if h < 12 else 'pm'
    return f'{h % 12 or 12}{suffix}'


def _clock(hhmm):
    h, m = map(int, hhmm.split(':'))
    return f"{h % 12 or 12}:{m:02d}{'am' if h < 12 else 'pm'}"


def _shift(hhmm, minutes):
    t = datetime(2000, 1, 1, *map(int, hhmm.split(':'))) + timedelta(minutes=minutes)
    return f'{t:%H:%M}'


def _flights_on(day):
    """Real flights saved by update_flights.py, or None if none were fetched for this day."""
    path = os.path.join(FLIGHTS_DIR, f'RTB_{day.isoformat()}.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# Short hops within Central America carry few tourists; the airport rush follows the
# long-haul flights (US, Canada, Europe).
CENTRAL_AMERICA = {'HN', 'BZ', 'GT', 'SV', 'NI', 'CR', 'PA'}


def flight_lines(day):
    data = _flights_on(day)
    if data is None:
        return []
    live = lambda fs: [f for f in fs if not str(f.get('status', '')).lower().startswith('cancel')]
    arrivals, departures = live(data['arrivals']), live(data['departures'])
    intl_arr = [f for f in arrivals if f['international']]
    intl_dep = [f for f in departures if f['international']]
    regional = len(arrivals) - len(intl_arr)

    lines = ['', '✈️ VUELOS INTERNACIONALES / INTERNATIONAL FLIGHTS']
    if not intl_arr and not intl_dep:
        lines.append('Sin vuelos internacionales / No international flights')
    if intl_arr:
        lines.append('🛬 Llegadas / Arrivals:')
        lines += [f" {_clock(f['time'])} {f['airline']} – {f['city']}" for f in intl_arr]
    if intl_dep:
        lines.append('🛫 Salidas / Departures:')
        lines += [f" {_clock(f['time'])} {f['airline']} – {f['city']}" for f in intl_dep]
    long_arr = [f for f in intl_arr if f.get('country') not in CENTRAL_AMERICA] or intl_arr
    long_dep = [f for f in intl_dep if f.get('country') not in CENTRAL_AMERICA] or intl_dep
    if long_arr or long_dep:
        lines.append('🚕 Hora pico aeropuerto / Airport rush:')
        if long_dep:
            lines.append(f" Llevar / Drop-offs: {_clock(_shift(long_dep[0]['time'], -150))}–"
                         f"{_clock(_shift(long_dep[-1]['time'], -120))}")
        if long_arr:
            lines.append(f" Recoger / Pick-ups: {_clock(long_arr[0]['time'])}–"
                         f"{_clock(_shift(long_arr[-1]['time'], 45))}")
    if regional:
        lines.append(f'👇 {regional} vuelos nacionales en el siguiente mensaje / '
                     f'{regional} domestic arrivals in the next message')
    return lines


def _short_airline(name):
    return 'Sosa' if 'sosa' in name.lower() else name


def domestic_message(day, heading_es, heading_en):
    """Second message: every domestic (Honduras) flight, posted after the main update.

    None when there are no domestic flights or no flight data for the day."""
    data = _flights_on(day)
    if data is None:
        return None
    live = lambda fs: [f for f in fs if not str(f.get('status', '')).lower().startswith('cancel')]
    arrivals = [f for f in live(data['arrivals']) if not f['international']]
    departures = [f for f in live(data['departures']) if not f['international']]
    if not arrivals and not departures:
        return None
    row = lambda f: f" {_clock(f['time'])} {_short_airline(f['airline'])} – {f['city']}"
    lines = [f'🇭🇳 VUELOS NACIONALES {heading_es} / DOMESTIC FLIGHTS {heading_en}',
             f'{_label_es(day)} · {_label_en(day)}', '']
    if arrivals:
        lines += [f'🛬 Llegadas / Arrivals ({len(arrivals)}):'] + [row(f) for f in arrivals]
    if departures:
        lines += ['', f'🛫 Salidas / Departures ({len(departures)}):'] + [row(f) for f in departures]
    lines += ['', 'Horarios estimados, pueden cambiar. / Estimates; times can change.', SITE]
    return '\n'.join(lines) + '\n'


def _approx(n):
    return f'{round(n, -2):,}' if n >= 1000 else str(n)


def _label_es(day):
    return f'{DAYS_ES[day.weekday()]} {day.day} {MONTHS_ES[day.month - 1]}'


def _label_en(day):
    return f'{day:%a} {day:%b} {day.day}'


def build_message(day, heading_es, heading_en, cache=None):
    """Plain-text message for one day plus a short outlook."""
    cache = {} if cache is None else cache
    cruises = _cruises_on(day, cache)
    plane = '✈️' if _flights_on(day) is not None else ''
    lines = [f'🛳️{plane} ROATÁN {heading_es} / {heading_en}', f'{_label_es(day)} · {_label_en(day)}', '']

    lines.append('🚢 CRUCEROS / CRUISE SHIPS')
    if cruises is None:
        lines += ['Sin datos para esta fecha / No schedule data for this date']
    else:
        pax = sum(c.get('estimated_passengers', 0) for c in cruises)
        icon, es, en = _level(pax)
        if cruises:
            lines.append(f'{icon} {es} / {en}: ~{_approx(pax)} cruceristas / cruise visitors')
            lines.append('')
            for c in cruises:
                lines.append(f"🚢 {c['ship_name']}: {_hour(c['arrival_hour'])}–{_hour(c['departure_hour'])} "
                             f"(~{_approx(c.get('estimated_passengers', 0))})")
            departures = sorted({c['departure_hour'] for c in cruises})
            rush = ', '.join(f'{_hour(h - 1)}–{_hour(h)}' for h in departures)
            lines += ['', f'⏰ Regreso al barco / Return rush: {rush}']
        else:
            lines.append(f'{icon} {es} / {en}')

    lines += flight_lines(day)

    outlook = []
    for i in range(1, OUTLOOK_DAYS + 1):
        d = day + timedelta(days=i)
        cs = _cruises_on(d, cache)
        if cs is None:
            continue
        pax = sum(c.get('estimated_passengers', 0) for c in cs)
        icon = _level(pax)[0]
        ships = f'{len(cs)} 🚢 ~{_approx(pax)}' if cs else '—'
        outlook.append(f'{icon} {_label_es(d)}: {ships}')
    if outlook:
        lines += ['', '📅 Próximos días / Next days:'] + outlook

    footer = 'Horarios estimados, pueden cambiar. / Estimates; times can change.'
    if _flights_on(day) is not None:
        footer += '\nVuelos / Flights: AeroDataBox'
    lines += ['', footer, SITE]
    return '\n'.join(lines) + '\n'


def write_daily_messages(output_dir, today=None):
    today = today or roatan_today()
    cache = {}
    tomorrow = today + timedelta(days=1)
    messages = [
        ('hoy', 'Hoy / Today (morning post)', build_message(today, 'HOY', 'TODAY', cache)),
        ('hoy_vuelos', 'Hoy – vuelos nacionales / Today – domestic flights (post right after)',
         domestic_message(today, 'HOY', 'TODAY')),
        ('manana', 'Mañana / Tomorrow (evening post)', build_message(tomorrow, 'MAÑANA', 'TOMORROW', cache)),
        ('manana_vuelos', 'Mañana – vuelos nacionales / Tomorrow – domestic flights (post right after)',
         domestic_message(tomorrow, 'MAÑANA', 'TOMORROW')),
    ]
    for key, _, text in messages:
        path = os.path.join(output_dir, f'{key}.txt')
        if text is None:
            if os.path.exists(path):
                os.remove(path)
            continue
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    with open(os.path.join(output_dir, 'whatsapp.html'), 'w', encoding='utf-8') as f:
        f.write(_copy_page([m for m in messages if m[2] is not None], today))


def _copy_page(messages, today):
    blocks = ''.join(f'''
  <section>
    <h2>{title}</h2>
    <pre id="{key}">{html.escape(text)}</pre>
    <button onclick="copyText('{key}', this)">Copiar / Copy</button>
    <a class="button" href="https://wa.me/?text={_urlquote(text)}">Abrir en WhatsApp</a>
  </section>''' for key, title, text in messages)
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>Roatan Daily Update</title>
<style>
  :root {{ --bg: #0d1117; --card: #161b22; --text: #e6e9ee; --muted: #8b949e; --border: #30363d; --brand: #25a35a; }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg: #f6f7f9; --card: #fff; --text: #14181f; --muted: #5b6472; --border: #d9dde3; }}
  }}
  body {{ margin: 0; padding: 16px; background: var(--bg); color: var(--text);
         font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; }}
  main {{ max-width: 560px; margin: 0 auto; }}
  h1 {{ font-size: 20px; }} h2 {{ font-size: 16px; color: var(--muted); }}
  section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 16px; }}
  pre {{ white-space: pre-wrap; font: 15px/1.45 -apple-system, 'Segoe UI', Roboto, sans-serif; margin: 0 0 12px; }}
  button, .button {{ display: inline-block; padding: 10px 14px; margin: 4px 4px 0 0; border-radius: 8px; border: 0;
                    background: var(--brand); color: #fff; font-size: 15px; font-weight: 600; text-decoration: none; cursor: pointer; }}
  .button {{ background: transparent; color: var(--brand); border: 1px solid var(--border); }}
  p {{ color: var(--muted); font-size: 13px; }}
</style>
</head>
<body>
<main>
  <h1>Roatán – actualización diaria</h1>
  <p>Generado / Generated {today.isoformat()} · también en / also at /hoy.txt, /manana.txt y /manana_vuelos.txt</p>
  {blocks}
</main>
<script>
  function copyText(id, btn) {{
    navigator.clipboard.writeText(document.getElementById(id).innerText).then(() => {{
      btn.textContent = '✓ Copiado';
      setTimeout(() => {{ btn.textContent = 'Copiar / Copy'; }}, 1500);
    }});
  }}
</script>
</body>
</html>
'''


def _urlquote(text):
    from urllib.parse import quote
    return quote(text, safe='')


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    write_daily_messages(out)
    print(open(os.path.join(out, 'manana.txt'), encoding='utf-8').read())
