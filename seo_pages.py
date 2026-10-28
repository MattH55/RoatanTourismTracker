"""
Plain-HTML pages built from the cruise data already on file:

  today.html       ships in port today (Roatan time) and the next 7 days
  2026.html ...    one page per year: month-by-month calls and busiest days
  statistics.html  cruise calls and estimated cruise passengers by year, month and line

Also month_summary(), the 2-3 sentences shown above each month's table.

Every number here is counted from tourism_YYYY_MM.json. Passenger figures are the
schedule's estimates (published passenger count, or ship capacity when none is
published), not official arrival counts. Flight figures are modelled and left out.
"""
import calendar
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta
from html import escape

from daily_message import LEVELS, roatan_today, _level, _hour

CRUISE_FIELDS = ('ship_name', 'cruise_line', 'arrival_hour', 'departure_hour', 'estimated_passengers')


def _port(p):
    """'Nov 30, 2026: Belize City' -> 'Belize City'."""
    return p.split(': ', 1)[1] if ': ' in (p or '') else (p or '')


def load_all(months, loader):
    """{(year, month): data} for every month, using the app's loader."""
    return {(y, m): loader(y, m) for y, m in months}


def cruises_by_day(data):
    """{'YYYY-MM-DD': [cruise, ...]} including days with no ships."""
    return {d: data['days'][d].get('cruises', []) for d in sorted(data['days'])}


def day_pax(cruises):
    return sum(c.get('estimated_passengers', 0) for c in cruises)


def month_figures(data):
    days = cruises_by_day(data)
    calls = sum(len(cs) for cs in days.values())
    ship_days = [d for d, cs in days.items() if cs]
    pax = sum(day_pax(cs) for cs in days.values())
    busiest = max(ship_days, key=lambda d: (day_pax(days[d]), len(days[d]), d)) if ship_days else None
    lines = Counter(c.get('cruise_line') or 'Unknown' for cs in days.values() for c in cs)
    ships = Counter(c.get('ship_name') or 'Unknown' for cs in days.values() for c in cs)
    return {
        'days': days, 'num_days': len(days), 'calls': calls, 'ship_days': len(ship_days),
        'empty_days': len(days) - len(ship_days), 'pax': pax, 'busiest': busiest,
        'lines': lines, 'ships': ships,
    }


def _date_label(d):
    dt = datetime.strptime(d, '%Y-%m-%d')
    return f'{dt:%A}, {dt:%B} {dt.day}'


def _short_date(d):
    dt = datetime.strptime(d, '%Y-%m-%d')
    return f'{dt:%a} {dt:%b} {dt.day}'


def _plural(n, word, plural=None):
    return f"{n:,} {word if n == 1 else (plural or word + 's')}"


def source_note(meta):
    src = (meta or {}).get('cruise_source')
    if src == 'scraped':
        return f"published port schedule, checked {meta.get('cruise_checked')}" if meta.get('cruise_checked') else 'published port schedule'
    if src == 'recovered':
        return 'published port schedules, snapshot of 2026-06-20'
    return 'placeholder estimate, not a confirmed schedule'


def month_summary(label, data, prev_label=None, prev_data=None):
    """2-3 sentences about one month, counted from its data."""
    f = month_figures(data)
    meta = data.get('meta', {})
    if not f['calls']:
        return (f'No cruise ship calls are listed for Roatan in {label} yet. '
                'The schedule is refreshed every day from the published port schedule.')
    busiest = f['days'][f['busiest']]
    s1 = (f"Roatan has {_plural(f['calls'], 'cruise ship call')} in {label}, spread over "
          f"{f['ship_days']} of the month's {f['num_days']} days, for an estimated "
          f"{f['pax']:,} cruise passengers in all.")
    s2 = (f"The busiest day is {_date_label(f['busiest'])}, with {_plural(len(busiest), 'ship')} "
          f"and about {day_pax(busiest):,} passengers")
    s2 += (f"; {_plural(f['empty_days'], 'day has', 'days have')} no ship in port." if f['empty_days']
           else '; every day has at least one ship in port.')
    line, line_calls = f['lines'].most_common(1)[0]
    s3 = f"{line} has the most calls ({line_calls})"
    if prev_data is not None and prev_label:
        prev_calls = month_figures(prev_data)['calls']
        diff = f['calls'] - prev_calls
        if diff:
            s3 += f", and the month has {abs(diff)} {'more' if diff > 0 else 'fewer'} calls than {prev_label} ({prev_calls})"
        else:
            s3 += f", and the month has the same number of calls as {prev_label}"
    s3 += '.'
    out = ' '.join([s1, s2, s3])
    if meta.get('cruise_source') not in ('scraped', 'recovered'):
        out += ' These calls are placeholder estimates, not a confirmed schedule.'
    return out


# ---------------------------------------------------------------- page shell

PAGE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117;
       color: #e0e0e0; padding: 24px 16px; line-height: 1.5; }
main { max-width: 1000px; margin: 0 auto; }
h1 { font-size: 30px; margin-bottom: 8px; color: #6cb4d8; }
h2 { font-size: 19px; color: #c0c8d8; margin: 28px 0 10px; border-bottom: 1px solid #30363d; padding-bottom: 6px; }
p { margin-bottom: 10px; }
a { color: #6cb4d8; }
.nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.nav a { padding: 6px 12px; border: 1px solid #30363d; border-radius: 6px; background: #161b22;
         color: #e0e0e0; text-decoration: none; font-size: 13px; }
.nav a:hover { border-color: #2E86AB; }
.lead { color: #c0c8d8; font-size: 16px; max-width: 760px; }
.note { font-size: 13px; color: #8b949e; padding: 8px 12px; border-left: 3px solid #F18F01;
        background: #161b22; border-radius: 0 6px 6px 0; margin: 12px 0; }
.big { font-size: 22px; font-weight: bold; }
.wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 8px; }
th { text-align: left; color: #8b949e; font-weight: 600; padding: 8px 6px; border-bottom: 2px solid #30363d; }
td { padding: 7px 6px; border-bottom: 1px solid #21262d; vertical-align: top; }
td.num, th.num { text-align: right; white-space: nowrap; }
.bar { display: inline-block; height: 10px; background: #2E86AB; border-radius: 3px; vertical-align: middle; }
footer { margin-top: 36px; padding-top: 14px; border-top: 1px solid #21262d; font-size: 12px; color: #6e7681; }
footer a { color: #8b949e; }
"""


def page(site_url, path, title, description, h1, body, build_date, extra_head=''):
    url = f'{site_url}/{path}'
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'WebPage', 'name': h1, 'url': url,
        'description': description, 'dateModified': build_date, 'inLanguage': 'en',
        'about': {'@type': 'Place', 'name': 'Roatan, Bay Islands, Honduras'},
        'isPartOf': {'@type': 'WebSite', 'name': 'Roatan Tourism Tracker', 'url': f'{site_url}/'},
    }, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L2LFYE0L4B"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-L2LFYE0L4B');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}">
    <link rel="canonical" href="{url}">
    <meta property="og:site_name" content="Roatan Tourism Tracker">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(description)}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta name="twitter:card" content="summary">
    <script type="application/ld+json">{ld}</script>
    <style>{PAGE_CSS}</style>
    {extra_head}
</head>
<body>
<main>
    <nav class="nav" aria-label="Site">
        <a href="index.html">All months</a>
        <a href="today.html">Ships in port today</a>
        <a href="2026.html">2026</a>
        <a href="2027.html">2027</a>
        <a href="2028.html">2028</a>
        <a href="statistics.html">Statistics</a>
    </nav>
    <h1>{escape(h1)}</h1>
{body}
    <footer>
        <p>Last updated {build_date} &mdash; <a href="index.html">roatantourismtracker.online</a></p>
        <p>Cruise calls come from published port schedules and can change. Passenger figures are estimates
        (the published passenger count, or the ship's capacity when none is published), not official arrival counts.</p>
    </footer>
</main>
</body>
</html>
"""


def _level_legend():
    parts = []
    bands = [lv for lv in LEVELS if lv[0] > 0]
    for i, (minimum, icon, _es, en) in enumerate(bands):
        upper = bands[i - 1][0] - 1 if i > 0 else None
        rng = f'{minimum:,}+' if upper is None else f'{minimum:,}&ndash;{upper:,}'
        parts.append(f'{icon} {en}: {rng}')
    return ' &middot; '.join(reversed(parts))


def _ship_rows(cruises):
    rows = ''
    for c in sorted(cruises, key=lambda c: (c.get('arrival_hour', 0), c.get('ship_name', ''))):
        prev = next((_port(p) for p in c.get('previous_ports', []) if _port(p) and _port(p) != 'At Sea'), '')
        nxt = next((_port(p) for p in c.get('next_ports', []) if _port(p) and _port(p) != 'At Sea'), '')
        rows += (f"<tr><td><strong>{escape(c.get('ship_name', ''))}</strong></td>"
                 f"<td>{escape(c.get('cruise_line', '') or '')}</td>"
                 f"<td class=\"num\">{_hour(c.get('arrival_hour', 8))}&ndash;{_hour(c.get('departure_hour', 17))}</td>"
                 f"<td class=\"num\">{c.get('estimated_passengers', 0):,}</td>"
                 f"<td>{escape(prev) or '&mdash;'}</td><td>{escape(nxt) or '&mdash;'}</td></tr>")
    return rows


def _find_day(all_data, d):
    data = all_data.get((d.year, d.month))
    if data is None or d.isoformat() not in data['days']:
        return None
    return data['days'][d.isoformat()].get('cruises', [])


def today_page(site_url, all_data, build_date, today=None):
    today = today or roatan_today()
    cruises = _find_day(all_data, today)
    label = f'{today:%A}, {today:%B} {today.day}, {today.year}'
    mk = f'{today.year:04d}-{today.month:02d}'
    body = ''
    if cruises is None:
        body += f'<p class="lead">There is no schedule data on file for {label}.</p>'
    elif not cruises:
        body += f'<p class="lead">No cruise ships are scheduled in Roatan today, {label}.</p>'
    else:
        pax = day_pax(cruises)
        icon, _es, en = _level(pax)
        rush = ', '.join(f'{_hour(h - 1)}&ndash;{_hour(h)}' for h in sorted({c["departure_hour"] for c in cruises}))
        body += (f'<p class="lead">{label}: <span class="big">{_plural(len(cruises), "cruise ship")}</span> in port, '
                 f'about <strong>{pax:,}</strong> cruise passengers. Crowd level: {icon} <strong>{en}</strong>.</p>'
                 f'<p>Expect the return-to-ship rush around {rush}.</p>'
                 '<h2>Ships in port today</h2><div class="wrap"><table><thead><tr><th>Ship</th><th>Line</th>'
                 '<th class="num">In port</th><th class="num">Est. passengers</th><th>Previous port</th>'
                 f'<th>Next port</th></tr></thead><tbody>{_ship_rows(cruises)}</tbody></table></div>')
    body += f'<p class="note">Crowd levels by estimated cruise visitors: {_level_legend()}. ' \
            'This page is rebuilt every morning at 5am Roatan time; times can change.</p>'

    rows = ''
    for i in range(1, 8):
        d = today + timedelta(days=i)
        cs = _find_day(all_data, d)
        if cs is None:
            continue
        pax = day_pax(cs)
        icon, _es, en = _level(pax)
        names = ', '.join(escape(c.get('ship_name', '')) for c in cs) or '&mdash;'
        dmk = f'{d.year:04d}-{d.month:02d}'
        rows += (f'<tr><td><a href="{dmk}.html">{_short_date(d.isoformat())}</a></td><td class="num">{len(cs)}</td>'
                 f'<td class="num">{pax:,}</td><td>{icon} {en}</td><td>{names}</td></tr>')
    if rows:
        body += ('<h2>Next 7 days</h2><div class="wrap"><table><thead><tr><th>Date</th><th class="num">Ships</th>'
                 '<th class="num">Est. passengers</th><th>Crowd level</th><th>Ships</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div>')
    body += f'<p><a href="{mk}.html">Full {today:%B %Y} cruise ship schedule &rarr;</a></p>'
    # If the page is older than the visitor's Roatan date, say so.
    body += ('<p class="note" id="stale" hidden>This page was built for ' + today.isoformat() +
             '. It may not have refreshed yet; see the month schedule for today.</p>'
             '<script>(function(){var n=new Date(Date.now()-6*3600e3).toISOString().slice(0,10);'
             f'if(n!=="{today.isoformat()}")document.getElementById("stale").hidden=false;}})();</script>')
    n = len(cruises or [])
    desc = (f'How many cruise ships are in Roatan today ({today:%b} {today.day}, {today.year}): '
            f'{_plural(n, "ship")}, estimated passengers, crowd level and the next 7 days.')
    return page(site_url, 'today.html', 'Cruise Ships in Roatan Today: Ships, Times & Crowd Level',
                desc, 'Cruise Ships in Roatan Today', body, build_date)


def year_page(site_url, year, all_data, build_date, years):
    months = sorted(k for k in all_data if k[0] == year)
    figs = {k: month_figures(all_data[k]) for k in months}
    calls = sum(f['calls'] for f in figs.values())
    pax = sum(f['pax'] for f in figs.values())
    first, last = calendar.month_name[months[0][1]], calendar.month_name[months[-1][1]]
    span = f'{first} to {last} {year}' if len(months) < 12 else f'all of {year}'

    rows = ''
    peak = max(figs.values(), key=lambda f: f['pax'])
    max_pax = peak['pax'] or 1
    for (y, m), f in figs.items():
        mk, mlabel = f'{y:04d}-{m:02d}', f'{calendar.month_name[m]} {y}'
        busiest = (f"{_short_date(f['busiest'])} ({len(f['days'][f['busiest']])} ships)" if f['busiest'] else '&mdash;')
        rows += (f'<tr><td><a href="{mk}.html">{mlabel}</a></td><td class="num">{f["calls"]}</td>'
                 f'<td class="num">{f["ship_days"]}</td><td class="num">{f["pax"]:,}</td>'
                 f'<td><span class="bar" style="width:{round(120 * f["pax"] / max_pax)}px"></span></td>'
                 f'<td>{busiest}</td><td>{escape(source_note(all_data[(y, m)].get("meta")))}</td></tr>')
    peak_key = max(figs, key=lambda k: (figs[k]['calls'], figs[k]['pax']))
    low_key = min(figs, key=lambda k: (figs[k]['calls'], figs[k]['pax']))

    all_days = [(d, cs) for f in figs.values() for d, cs in f['days'].items() if cs]
    top_days = sorted(all_days, key=lambda x: (-day_pax(x[1]), x[0]))[:10]
    day_rows = ''.join(
        f'<tr><td><a href="{d[:7]}.html">{_short_date(d)}, {year}</a></td><td class="num">{len(cs)}</td>'
        f'<td class="num">{day_pax(cs):,}</td><td>{", ".join(escape(c.get("ship_name", "")) for c in cs)}</td></tr>'
        for d, cs in top_days)
    ships = Counter()
    for f in figs.values():
        ships.update(f['ships'])
    ship_rows = ''.join(f'<tr><td>{escape(s)}</td><td class="num">{n}</td></tr>' for s, n in ships.most_common(10))

    intro = (f'<p class="lead">This page covers {span}. Roatan has {_plural(calls, "cruise ship call")} on file '
             f'for that period, with an estimated {pax:,} cruise passengers. The busiest month is '
             f'{calendar.month_name[peak_key[1]]} ({figs[peak_key]["calls"]} calls) and the quietest is '
             f'{calendar.month_name[low_key[1]]} ({figs[low_key]["calls"]} calls).</p>')
    nav = []
    if year - 1 in years:
        nav.append(f'<a href="{year - 1}.html">&larr; {year - 1} schedule</a>')
    if year + 1 in years:
        nav.append(f'<a href="{year + 1}.html">{year + 1} schedule &rarr;</a>')
    body = (intro +
            '<h2>Month by month</h2><div class="wrap"><table><thead><tr><th>Month</th><th class="num">Ship calls</th>'
            '<th class="num">Days with ships</th><th class="num">Est. passengers</th><th></th><th>Busiest day</th>'
            f'<th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<h2>Busiest days in {year}</h2><div class="wrap"><table><thead><tr><th>Date</th><th class="num">Ships</th>'
            f'<th class="num">Est. passengers</th><th>Ships in port</th></tr></thead><tbody>{day_rows}</tbody></table></div>'
            f'<h2>Most frequent ships in {year}</h2><div class="wrap"><table><thead><tr><th>Ship</th>'
            f'<th class="num">Calls</th></tr></thead><tbody>{ship_rows}</tbody></table></div>'
            f'<p>{" &nbsp; ".join(nav)}</p>')
    desc = (f'Roatan cruise ship schedule {year}: {calls:,} ship calls {"from " + first + " to " + last if len(months) < 12 else "by month"}, '
            f'busiest days and most frequent ships, with links to every month.')
    return page(site_url, f'{year}.html', f'Roatan Cruise Ship Schedule {year}: Every Month & Busiest Days',
                desc, f'Roatan Cruise Ship Schedule {year}', body, build_date)


def statistics_page(site_url, all_data, build_date):
    keys = sorted(all_data)
    figs = {k: month_figures(all_data[k]) for k in keys}
    years = sorted({y for y, _ in keys})

    year_rows = ''
    for y in years:
        ks = [k for k in keys if k[0] == y]
        calls = sum(figs[k]['calls'] for k in ks)
        pax = sum(figs[k]['pax'] for k in ks)
        span = f'{calendar.month_abbr[ks[0][1]]}&ndash;{calendar.month_abbr[ks[-1][1]]}'
        avg = round(pax / calls) if calls else 0
        peak = max(ks, key=lambda k: figs[k]['pax'])
        year_rows += (f'<tr><td><a href="{y}.html">{y}</a></td><td>{span} ({len(ks)} months)</td>'
                      f'<td class="num">{calls:,}</td><td class="num">{pax:,}</td><td class="num">{avg:,}</td>'
                      f'<td>{calendar.month_name[peak[1]]}</td></tr>')

    max_pax = max(f['pax'] for f in figs.values()) or 1
    month_rows = ''.join(
        f'<tr><td><a href="{y:04d}-{m:02d}.html">{calendar.month_abbr[m]} {y}</a></td><td class="num">{figs[(y, m)]["calls"]}</td>'
        f'<td class="num">{figs[(y, m)]["pax"]:,}</td>'
        f'<td><span class="bar" style="width:{round(160 * figs[(y, m)]["pax"] / max_pax)}px"></span></td></tr>'
        for y, m in keys)

    # Calendar-month averages over the months on file (seasonality).
    by_cal = {}
    for (y, m), f in figs.items():
        by_cal.setdefault(m, []).append(f['calls'])
    season = sorted(by_cal, key=lambda m: -sum(by_cal[m]) / len(by_cal[m]))
    top3 = ', '.join(calendar.month_name[m] for m in season[:3])
    low3 = ', '.join(calendar.month_name[m] for m in season[-3:])

    lines = Counter()
    line_pax = Counter()
    for f in figs.values():
        for cs in f['days'].values():
            for c in cs:
                ln = c.get('cruise_line') or 'Unknown'
                lines[ln] += 1
                line_pax[ln] += c.get('estimated_passengers', 0)
    total_calls = sum(lines.values()) or 1
    line_rows = ''.join(
        f'<tr><td>{escape(ln)}</td><td class="num">{n:,}</td><td class="num">{100 * n / total_calls:.1f}%</td>'
        f'<td class="num">{line_pax[ln]:,}</td></tr>' for ln, n in lines.most_common(12))

    total_pax = sum(f['pax'] for f in figs.values())
    first, last = keys[0], keys[-1]
    span = f'{calendar.month_name[first[1]]} {first[0]} to {calendar.month_name[last[1]]} {last[0]}'
    intro = (f'<p class="lead">From {span}, Roatan has {total_calls:,} cruise ship calls on file and an estimated '
             f'{total_pax:,} cruise passengers. On average the busiest calendar months are {top3}; the quietest are {low3}.</p>'
             '<p class="note">These are counts from the published cruise schedule, with passengers estimated per call. '
             'They are not official government arrival statistics. Months further ahead can gain calls as lines '
             'publish itineraries. Flight figures on this site are modelled estimates and are not included here.</p>')
    body = (intro +
            '<h2>Cruise ship calls by year</h2><div class="wrap"><table><thead><tr><th>Year</th><th>Months on file</th>'
            '<th class="num">Ship calls</th><th class="num">Est. passengers</th><th class="num">Avg. per call</th>'
            f'<th>Peak month</th></tr></thead><tbody>{year_rows}</tbody></table></div>'
            '<h2>Estimated cruise passengers by month</h2><div class="wrap"><table><thead><tr><th>Month</th>'
            f'<th class="num">Ship calls</th><th class="num">Est. passengers</th><th></th></tr></thead><tbody>{month_rows}</tbody></table></div>'
            '<h2>Cruise lines</h2><div class="wrap"><table><thead><tr><th>Line</th><th class="num">Calls</th>'
            f'<th class="num">Share</th><th class="num">Est. passengers</th></tr></thead><tbody>{line_rows}</tbody></table></div>')
    desc = (f'Roatan cruise tourism statistics: {total_calls:,} cruise ship calls and about {total_pax:,} estimated '
            f'cruise passengers from {span}, by year, month and cruise line.')
    return page(site_url, 'statistics.html', 'Roatan Cruise Tourism Statistics 2026–2028: Ships & Passengers',
                desc, 'Roatan Cruise Tourism Statistics', body, build_date)


def write_seo_pages(output_dir, site_url, all_data, build_date):
    years = sorted({y for y, _ in all_data})
    pages = {'today.html': today_page(site_url, all_data, build_date),
             'statistics.html': statistics_page(site_url, all_data, build_date)}
    for y in years:
        pages[f'{y}.html'] = year_page(site_url, y, all_data, build_date, years)
    for name, html in pages.items():
        with open(os.path.join(output_dir, name), 'w', encoding='utf-8') as f:
            f.write(html)
    return list(pages)
