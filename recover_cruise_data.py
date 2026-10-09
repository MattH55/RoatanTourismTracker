"""
Restore cruise calls into tourism_YYYY_MM.json from the published month pages.

The JSON files committed in f272b8c ("Expanded flight data...") were regenerated
with empty `cruises` lists (and random sample ships for Nov 2028), because the
cruisetimetables.com scraper no longer finds the schedule table. The last good
cruise schedule survives in the rendered cruise table of each month page
(static_site/YYYY-MM.html, falling back to the root YYYY-MM.html).

Run once:  python recover_cruise_data.py
"""
import html
import json
import os
import re
from datetime import datetime

from app import AVAILABLE_MONTHS, get_month_key

SNAPSHOT_SOURCES = ['static_site', '.']


def _cell_text(td):
    return html.unescape(re.sub(r'<[^>]+>', '|', td)).strip('|').strip()


def _is_t_notation(port):
    return port.startswith(('T-', 'T+'))


def parse_cruise_table(path):
    """Return cruise dicts from a rendered month page, or None if no table."""
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        s = f.read()
    start = s.find('<tbody>')
    if start < 0:
        return None
    end = s.find('</tbody>', start)

    cruises = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', s[start:end], re.S):
        cells = [_cell_text(td) for td in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if len(cells) < 12:
            continue
        date_part, _, time_part = cells[0].partition('||')
        arr, _, dep = time_part.partition(' - ')
        ports = ['' if p == '—' else p for p in cells[2:11]]
        prev4, prev3, prev2, prev1, _roatan, next1, next2, next3, next4 = ports
        cruises.append({
            'date': datetime.strptime(date_part.strip(), '%b %d, %Y').strftime('%Y-%m-%d'),
            'ship_name': cells[1],
            'arrival_hour': int(arr.split(':')[0]),
            'departure_hour': int(dep.split(':')[0]),
            'estimated_passengers': int(cells[11].replace(',', '') or 0),
            'previous_ports': [p for p in (prev1, prev2, prev3, prev4) if p],
            'next_ports': [p for p in (next1, next2, next3, next4) if p],
            'is_arrival': True,
        })
    return cruises


def load_snapshot(month_key):
    """Prefer the newest snapshot; per row, avoid T-notation ports when possible."""
    snapshots = [parse_cruise_table(os.path.join(d, f'{month_key}.html')) for d in SNAPSHOT_SOURCES]
    snapshots = [s for s in snapshots if s]
    if not snapshots:
        return None, None
    primary = snapshots[0]
    for fallback in snapshots[1:]:
        if len(fallback) != len(primary):
            continue
        for i, row in enumerate(primary):
            ports = row['previous_ports'] + row['next_ports']
            alt = fallback[i]
            if (any(_is_t_notation(p) for p in ports)
                    and (alt['date'], alt['ship_name']) == (row['date'], row['ship_name'])
                    and not any(_is_t_notation(p) for p in alt['previous_ports'] + alt['next_ports'])):
                primary[i] = alt
    return primary, SNAPSHOT_SOURCES[0]


def main():
    total = 0
    for year, month in AVAILABLE_MONTHS:
        mk = get_month_key(year, month)
        data_file = f'tourism_{year:04d}_{month:02d}.json'
        with open(data_file, encoding='utf-8') as f:
            data = json.load(f)

        cruises, _ = load_snapshot(mk)
        if cruises is None:
            print(f'  {mk}: no snapshot found, leaving as-is')
            continue

        for day in data['days'].values():
            day['cruises'] = []
        for c in cruises:
            date = c.pop('date')
            data['days'].setdefault(date, {'flights': [], 'cruises': []})['cruises'].append(c)

        data['meta'] = {
            'flight_source': 'modelled',
            'cruise_source': 'recovered',
            'cruise_source_note': 'Restored from the published schedule snapshot of 2026-06-20.',
        }
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        total += len(cruises)
        print(f'  {mk}: {len(cruises)} cruise calls restored')
    print(f'Restored {total} cruise calls.')


if __name__ == '__main__':
    main()
