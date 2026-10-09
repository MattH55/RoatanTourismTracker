"""
Fetch real Roatan (RTB) arrivals and departures from AeroDataBox and save them to
flights/RTB_YYYY-MM-DD.json for today and tomorrow (Roatan time).

AeroDataBox is a commercial flight-data API (https://aerodatabox.com). The key is read
from the AERODATABOX_API_KEY environment variable (a GitHub Actions secret); it is
called through RapidAPI. Each day costs two requests (two 12-hour windows), so the
daily run uses about 120 requests a month.

If the key is missing or a request fails, nothing is written for that day: the daily
message then leaves flights out rather than showing stale or guessed times.

Run:  AERODATABOX_API_KEY=... python update_flights.py
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

AIRPORT = 'RTB'
HOME_COUNTRY = 'HN'
FLIGHTS_DIR = 'flights'
ROATAN_TZ = timezone(timedelta(hours=-6))
API_HOST = os.environ.get('AERODATABOX_HOST', 'aerodatabox.p.rapidapi.com')
WINDOWS = [('00:00', '11:59'), ('12:00', '23:59')]  # the API allows at most 12 hours per call


def flights_path(day):
    return os.path.join(FLIGHTS_DIR, f'{AIRPORT}_{day.isoformat()}.json')


def _fetch_window(day, start, end, api_key):
    url = f'https://{API_HOST}/flights/airports/iata/{AIRPORT}/{day.isoformat()}T{start}/{day.isoformat()}T{end}'
    params = {
        'direction': 'Both',
        'withLeg': 'false',
        'withCancelled': 'true',
        'withCodeshared': 'false',   # one row per physical flight
        'withCargo': 'false',
        'withPrivate': 'false',
        'withLocation': 'false',
    }
    headers = {'X-RapidAPI-Key': api_key, 'X-RapidAPI-Host': API_HOST}
    response = requests.get(url, params=params, headers=headers, timeout=30)
    if response.status_code == 204:  # no flights in the window
        return {'arrivals': [], 'departures': []}
    response.raise_for_status()
    return response.json()


def _local_time(movement):
    """'2026-10-10 11:28-06:00' -> ('2026-10-10', '11:28')."""
    local = ((movement or {}).get('scheduledTime') or {}).get('local', '')
    m = re.match(r'(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})', local)
    return (m.group(1), m.group(2)) if m else (None, None)


def _normalise(flight, day):
    movement = flight.get('movement') or {}
    date, time = _local_time(movement)
    if date != day.isoformat():
        return None
    airport = movement.get('airport') or {}
    return {
        'time': time,
        'number': flight.get('number', '').strip(),
        'airline': (flight.get('airline') or {}).get('name', ''),
        'city': airport.get('municipalityName') or airport.get('shortName') or airport.get('name', ''),
        'airport_iata': airport.get('iata', ''),
        'country': airport.get('countryCode', ''),
        'international': bool(airport.get('countryCode')) and airport.get('countryCode') != HOME_COUNTRY,
        'status': flight.get('status', ''),
    }


def _dedupe(flights):
    """Drop remaining codeshares: same time and same other airport is one aircraft."""
    seen, out = set(), []
    for f in sorted(flights, key=lambda f: (f['time'], f['number'])):
        key = (f['time'], f['airport_iata'] or f['city'])
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def fetch_day(day, api_key):
    arrivals, departures = [], []
    for start, end in WINDOWS:
        data = _fetch_window(day, start, end, api_key)
        arrivals += [f for f in (_normalise(x, day) for x in data.get('arrivals', [])) if f]
        departures += [f for f in (_normalise(x, day) for x in data.get('departures', [])) if f]
    return {
        'airport': AIRPORT,
        'date': day.isoformat(),
        'source': 'AeroDataBox',
        'fetched_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
        'arrivals': _dedupe(arrivals),
        'departures': _dedupe(departures),
    }


def main():
    api_key = os.environ.get('AERODATABOX_API_KEY', '').strip()
    if not api_key:
        print('AERODATABOX_API_KEY not set; skipping flight update')
        sys.exit(1)
    os.makedirs(FLIGHTS_DIR, exist_ok=True)
    today = datetime.now(ROATAN_TZ).date()
    ok = 0
    for day in (today, today + timedelta(days=1)):
        try:
            data = fetch_day(day, api_key)
        except Exception as e:  # keep whatever is on file for this day
            print(f'[{day}] flight fetch failed: {e}')
            continue
        with open(flights_path(day), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        ok += 1
        print(f"[{day}] {len(data['arrivals'])} arrivals, {len(data['departures'])} departures")
    if ok == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
