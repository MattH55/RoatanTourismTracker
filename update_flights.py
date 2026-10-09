"""
Fetch real Roatan (RTB) arrivals and departures from AeroDataBox and save them to
flights/RTB_YYYY-MM-DD.json for today and the next FLIGHT_DAYS_AHEAD days (default 1,
i.e. today and tomorrow, Roatan time). The same flights replace the modelled schedule
for those days in tourism_YYYY_MM.json, so the site's charts show real flights; days
without a fetch keep the modelled schedule.

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

from scraper import AIRCRAFT_CAPACITIES, LOAD_FACTOR

AIRPORT = 'RTB'
HOME_COUNTRY = 'HN'
FLIGHTS_DIR = 'flights'
ROATAN_TZ = timezone(timedelta(hours=-6))
API_HOST = os.environ.get('AERODATABOX_HOST', 'aerodatabox.p.rapidapi.com')
WINDOWS = [('00:00', '11:59'), ('12:00', '23:59')]  # the API allows at most 12 hours per call
DAYS_AHEAD = int(os.environ.get('FLIGHT_DAYS_AHEAD', '1'))
DEFAULT_SEATS = 100

# AeroDataBox spells models out ("Boeing 737-800"); the capacity table uses short keys.
MANUFACTURER_PREFIXES = [
    ('boeing ', 'B'), ('airbus ', ''), ('embraer ', 'E'), ('cessna ', 'C'), ('let ', ''),
    ('bombardier ', ''), ('de havilland ', ''), ('mcdonnell douglas ', ''), ('gulfstream ', 'G'),
]


def seats_for(model):
    """Seat count for an aircraft model string, or DEFAULT_SEATS if unrecognised."""
    key = (model or '').strip()
    low = key.lower()
    for prefix, short in MANUFACTURER_PREFIXES:
        if low.startswith(prefix):
            key, low = short + key[len(prefix):], (short + key[len(prefix):]).lower()
            break
    key = key.replace(' -', '-').replace('- ', '-')
    upper = key.upper().replace('L-410', 'L410').replace('DASH 8', 'DH8').replace('Q-400', 'Q400')
    if upper in AIRCRAFT_CAPACITIES:
        return AIRCRAFT_CAPACITIES[upper]
    exact = {k.upper(): v for k, v in AIRCRAFT_CAPACITIES.items()}
    if upper in exact:
        return exact[upper]
    # Longest table key that the model name starts with ("B737-800 (WL)" -> B737-800, "ATR 72-500" -> ATR 72)
    for k in sorted(exact, key=len, reverse=True):
        if upper.startswith(k):
            return exact[k]
    return DEFAULT_SEATS


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
        'aircraft': (flight.get('aircraft') or {}).get('model', ''),
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


def chart_record(f, is_arrival):
    """A flight in the shape the site's charts read from tourism_YYYY_MM.json."""
    hour, minute = map(int, f['time'].split(':'))
    other = f['airport_iata'] or f['city']
    return {
        'flight_number': f['number'],
        'airline': f['airline'],
        'aircraft': f['aircraft'],
        'origin': other if is_arrival else AIRPORT,
        'destination': AIRPORT if is_arrival else other,
        'country': f['country'],
        'hour': hour,
        'minute': minute,
        'is_arrival': is_arrival,
        'estimated_passengers': int(seats_for(f['aircraft']) * LOAD_FACTOR),
        'source': 'aerodatabox',
    }


def merge_into_tourism(data):
    """Replace the modelled flights for this day with the real ones, if the month file exists."""
    day = data['date']
    path = f"tourism_{day[:4]}_{day[5:7]}.json"
    if not os.path.exists(path):
        return False
    with open(path, encoding='utf-8') as f:
        month = json.load(f)
    if day not in month['days']:
        return False
    live = lambda fs: [f for f in fs if not str(f.get('status', '')).lower().startswith('cancel')]
    month['days'][day]['flights'] = ([chart_record(f, True) for f in live(data['arrivals'])]
                                     + [chart_record(f, False) for f in live(data['departures'])])
    month['days'][day]['flight_source'] = 'real'
    month['days'][day]['flights_fetched_at'] = data['fetched_at']
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(month, f, indent=2)
    return True


def main():
    api_key = os.environ.get('AERODATABOX_API_KEY', '').strip()
    if not api_key:
        print('AERODATABOX_API_KEY not set; skipping flight update')
        sys.exit(1)
    os.makedirs(FLIGHTS_DIR, exist_ok=True)
    today = datetime.now(ROATAN_TZ).date()
    ok = 0
    for day in (today + timedelta(days=i) for i in range(DAYS_AHEAD + 1)):
        try:
            data = fetch_day(day, api_key)
        except Exception as e:  # keep whatever is on file for this day
            print(f'[{day}] flight fetch failed: {e}')
            continue
        with open(flights_path(day), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        ok += 1
        merged = merge_into_tourism(data)
        print(f"[{day}] {len(data['arrivals'])} arrivals, {len(data['departures'])} departures"
              + (' -> charts updated' if merged else ' (no month file; charts unchanged)'))
    if ok == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
