"""
Refresh cruise calls in tourism_YYYY_MM.json from cruisetimetables.com.

Runs daily before the site build. Only the current and future months are refreshed
(past months are no longer published). The current month's page drops days that have
already passed, so those days keep the calls on file. Flight data is left untouched, and
previous/next ports already on file are kept for ship calls that are still on the schedule.

A month is left unchanged when its page can't be fetched or read completely, or when
the number of upcoming calls would collapse (to zero, or by more than half), so a site
outage or layout change never wipes good data. Set FORCE_CRUISE_UPDATE=1 to accept a
genuine large change.

Run:  python update_cruise_schedule.py
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

from scraper import scrape_cruise_ships, cruise_entry, cruise_schedule_url

MAX_DROP_FRACTION = 0.5
FIRST_MONTH = (2026, 6)
LAST_MONTH = (2028, 11)
REQUEST_DELAY_SECONDS = 2


def months_to_refresh(today):
    y, m = max((today.year, today.month), FIRST_MONTH)
    while (y, m) <= LAST_MONTH:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def refresh_month(year, month, today_str):
    data_file = f'tourism_{year:04d}_{month:02d}.json'
    if not os.path.exists(data_file):
        print(f'  {data_file} missing, skipping')
        return None
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)

    ships = scrape_cruise_ships(year, month)
    if ships is None:
        return None

    # Keep ports already on file for the same ship on the same day.
    known_ports = {}
    for date, day in data['days'].items():
        for c in day.get('cruises', []):
            known_ports[(date, c['ship_name'].lower())] = (c.get('previous_ports'), c.get('next_ports'))

    old_count = sum(len(d.get('cruises', [])) for d in data['days'].values())
    old_upcoming = sum(len(d.get('cruises', [])) for date, d in data['days'].items() if date >= today_str)
    new_upcoming = sum(1 for s in ships if s['date'] >= today_str)
    collapsed = old_upcoming > 0 and (new_upcoming == 0 or new_upcoming < old_upcoming * (1 - MAX_DROP_FRACTION))
    if collapsed and os.environ.get('FORCE_CRUISE_UPDATE') != '1':
        print(f'  Upcoming calls would drop from {old_upcoming} to {new_upcoming}; '
              'keeping existing data (set FORCE_CRUISE_UPDATE=1 to accept)')
        return None

    for date, day in data['days'].items():
        if date >= today_str:
            day['cruises'] = []
    for ship in ships:
        if ship['date'] < today_str:
            continue  # already happened; keep what's on file
        if ship['date'] not in data['days']:
            print(f"  Ignoring {ship['ship_name']} on unknown date {ship['date']}")
            continue
        prev_ports, next_ports = known_ports.get((ship['date'], ship['ship_name'].lower()), (None, None))
        data['days'][ship['date']]['cruises'].append(cruise_entry(ship, prev_ports, next_ports))

    meta = data.setdefault('meta', {})
    meta.update({
        'flight_source': meta.get('flight_source', 'modelled'),
        'cruise_source': 'scraped',
        'cruise_source_url': cruise_schedule_url(year, month),
        'cruise_checked': today_str,
    })
    meta.pop('cruise_source_note', None)

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return old_count, sum(len(d['cruises']) for d in data['days'].values())


def main():
    today = datetime.now(timezone.utc)
    today_str = today.strftime('%Y-%m-%d')
    updated = failed = 0
    for i, (year, month) in enumerate(months_to_refresh(today)):
        if i:
            time.sleep(REQUEST_DELAY_SECONDS)
        result = refresh_month(year, month, today_str)
        if result is None:
            failed += 1
            print(f'[{year}-{month:02d}] not updated, keeping existing data')
        else:
            updated += 1
            print(f'[{year}-{month:02d}] {result[0]} -> {result[1]} cruise calls')
    print(f'Updated {updated} month(s); {failed} kept as before.')
    # Fail loudly only when nothing at all could be refreshed (site down or layout changed).
    if updated == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
