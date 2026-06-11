"""
Tourism Tracker - Data Scraper
Scrapes cruise ship schedules from CruiseTimetables and generates flight data
for Roatan, Honduras (MHRO airport and Roatan cruise ports).
Supports any year/month from June 2026 through November 2028.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
from datetime import datetime, timedelta
import calendar

AIRCRAFT_CAPACITIES = {
    'B737': 150, 'B737-700': 148, 'B737-800': 175, 'B737-900': 180,
    'B737 MAX 8': 178, 'B737 MAX 9': 193, 'B737-200': 120, 'B737-300': 149,
    'B737-400': 168, 'B737-500': 132, 'B767': 250, 'B767-300': 269,
    'B767-400': 304, 'B757': 200, 'B757-200': 200, 'B757-300': 243,
    'B777': 350, 'B777-200': 314, 'B777-300': 396, 'B787': 280,
    'B787-8': 242, 'B787-9': 290, 'B787-10': 330, 'B717': 110,
    'B727': 150, 'B747': 400, 'B747-400': 416, 'B737 MAX': 178,
    'A319': 140, 'A320': 180, 'A320neo': 195, 'A321': 220, 'A321neo': 244,
    'A330': 300, 'A330-200': 293, 'A330-300': 335, 'A330-900': 330,
    'A340': 335, 'A350': 350, 'A350-900': 350, 'A350-1000': 410,
    'A380': 500, 'A220': 130, 'A220-300': 130, 'A318': 120,
    'E170': 78, 'E175': 88, 'E190': 100, 'E195': 124, 'E195-E2': 146,
    'ERJ 145': 50, 'ERJ-145': 50, 'ERJ 135': 37,
    'CRJ200': 50, 'CRJ700': 78, 'CRJ900': 90, 'CRJ1000': 104,
    'DH8D': 78, 'DH8A': 39, 'DH8C': 56, 'Q400': 78,
    'AT72': 74, 'ATR 72': 74, 'ATR 42': 48,
    'C172': 4, 'C208': 14, 'C152': 2, 'C182': 4, 'C206': 6,
    'PA28': 4, 'PA34': 6,
    'C525': 8, 'C550': 10, 'C560': 10, 'C680': 12, 'C750': 12,
    'G150': 8, 'G200': 10, 'G280': 10, 'G450': 14, 'G550': 16, 'G650': 18,
    'GLEX': 14, 'GLF4': 14, 'GLF5': 16, 'GLF6': 18,
    'CL30': 10, 'CL35': 10, 'CL60': 12,
    'E550': 10, 'E650': 12,
    'F2TH': 8, 'F900': 12, 'F7X': 14, 'F8X': 14,
    'H25B': 10, 'HDJT': 8,
    'LJ31': 8, 'LJ35': 8, 'LJ45': 10, 'LJ55': 10, 'LJ60': 10, 'LJ75': 10,
    'P180': 9, 'TBM7': 6, 'TBM8': 6, 'TBM9': 6,
    'PC12': 9, 'PC24': 10, 'SR22': 4, 'SR20': 4,
    'BE20': 8, 'BE30': 8, 'BE40': 8, 'B350': 8, 'B190': 19,
    'C25A': 8, 'C25B': 8, 'C25C': 8, 'C510': 8,
    'R22': 2, 'R44': 4, 'B206': 5, 'B407': 7, 'B429': 8, 'B430': 8,
    'A109': 8, 'A119': 8, 'A139': 15, 'EC35': 8, 'EC45': 10,
    'S76': 12, 'S92': 19,
    'C130': 128, 'C17': 336, 'C5': 500,
    'DC10': 380, 'MD80': 172, 'MD90': 172, 'MD11': 350,
    'F100': 100, 'F70': 80, 'F50': 58, 'F28': 85,
    'BA11': 119, 'BA46': 112, 'SF34': 34, 'SB20': 50,
    'D328': 32, 'D228': 19, 'J328': 32,
    'E135': 37, 'E145': 50, 'L410': 19, 'C212': 26, 'CN35': 48,
    'B463': 180, 'DC3': 32, 'CONC': 100,
    'IL76': 350, 'AN12': 100, 'AN24': 50, 'AN26': 50,
    'AN72': 68, 'AN124': 400, 'AN225': 600,
    'TU34': 180, 'TU54': 180, 'YK40': 40, 'YK42': 120,
}

LOAD_FACTOR = 0.85

CRUISE_SHIP_CAPACITIES = {
    'OASIS': 6000, 'ALLURE': 6000, 'HARMONY': 6000, 'SYMPHONY': 6000,
    'WONDER': 6000, 'UTOPIA': 6000, 'ICON': 7600, 'STAR': 7600,
    'FREEDOM': 4000, 'LIBERTY': 4000, 'INDEPENDENCE': 4000,
    'VOYAGER': 3800, 'EXPLORER': 3800, 'ADVENTURE': 3800,
    'NAVIGATOR': 3800, 'MARINER': 3800,
    'QUANTUM': 4900, 'ANTHEM': 4900, 'OVATION': 4900,
    'SPECTRUM': 4900, 'ODYSSEY': 4900,
    'RADIANCE': 2500, 'BRILLIANCE': 2500, 'SERENADE': 2500, 'JEWEL': 2500,
    'VISION': 2400, 'ENCHANTMENT': 2400, 'GRANDEUR': 2400, 'RAPSODY': 2400,
    'SOVEREIGN': 2800, 'MONARCH': 2800, 'MAJESTY': 2800, 'EMPRESS': 1800,
    'CARNIVAL': 4000, 'MAGIC': 4000, 'DREAM': 4000, 'BREEZE': 4000,
    'VISTA': 4000, 'HORIZON': 4000, 'PANORAMA': 4000,
    'MARDIGRAS': 6500, 'CELEBRATION': 6500, 'JUBILEE': 6500,
    'CONQUEST': 3000, 'GLORY': 3000, 'VALOR': 3000,
    'SPLENDOR': 3000, 'PRIDE': 2200, 'LEGEND': 2200, 'MIRACLE': 2200,
    'PARADISE': 2200, 'ELATION': 2200, 'SENSATION': 2200,
    'FANTASY': 2200, 'ECSTASY': 2200, 'SUNSHINE': 3000,
    'MSC': 4000, 'SEASIDE': 5000, 'SEAVIEW': 5000,
    'MERAVIGLIA': 6000, 'BELLISSIMA': 6000, 'GRANDIOSA': 6000,
    'WORLD': 6000, 'EURIBIA': 4000, 'DIVINA': 4000, 'PREZIOSA': 4000,
    'SPLENDIDA': 4000, 'FANTASIA': 4000,
    'MAGNIFICA': 3000, 'POESIA': 3000, 'ORCHESTRA': 3000,
    'MUSICA': 3000, 'OPERA': 2200, 'LYRICA': 2200,
    'ARMONIA': 2200, 'SINFONIA': 2200,
    'NORWEGIAN': 4000, 'BLISS': 4000, 'JOY': 4000, 'ENCORE': 4000,
    'PRIMA': 3500, 'VIVA': 3500, 'AQUA': 3500,
    'EPIC': 4200, 'BREAKAWAY': 4000, 'GETAWAY': 4000, 'ESCAPE': 4200,
    'GEM': 2400, 'JADE': 2400, 'PEARL': 2400, 'DAWN': 2400,
    'SUN': 2000, 'SKY': 2000, 'SPIRIT': 2000,
    'CELEBRITY': 3000, 'EDGE': 3000, 'APEX': 3000, 'BEYOND': 3000,
    'ASCENT': 3000, 'SOLSTICE': 3000, 'EQUINOX': 3000,
    'ECLIPSE': 3000, 'SILHOUETTE': 3000, 'REFLECTION': 3000,
    'MILLENNIUM': 2200, 'INFINITY': 2200, 'SUMMIT': 2200,
    'CONSTELLATION': 2200,
    'ROTTERDAM': 2700, 'NIEUW': 2700, 'KONINGSDAM': 2700, 'EURODAM': 2700,
    'OOSTERDAM': 2000, 'ZAANDAM': 1500, 'VOLENDAM': 1500,
    'AMSTERDAM': 1500, 'WESTERDAM': 2000, 'NOORDAM': 2000, 'VEENDAM': 2000,
    'PRINCESS': 3600, 'ROYAL': 3600, 'REGAL': 3600, 'MAJESTIC': 3600,
    'SKY': 3600, 'ENCHANTED': 3600, 'DISCOVERY': 3600,
    'GRAND': 2600, 'DIAMOND': 2700, 'SAPPHIRE': 2700,
    'CARIBBEAN': 2600, 'CROWN': 3100, 'EMERALD': 3100, 'RUBY': 3100,
    'CORAL': 2000, 'ISLAND': 2000,
    'DISNEY': 4000, 'WISH': 4000, 'DREAM': 4000, 'FANTASY': 4000,
    'MAGIC': 2700, 'WONDER': 2700, 'TREASURE': 4000, 'ADVENTURE': 4000,
    'COSTA': 3000, 'SMERALDA': 6000, 'FIRENZE': 4000, 'TOSCANA': 6000,
    'FORTUNA': 3500, 'MAGICA': 3500, 'PACIFICA': 3500, 'FAVOLOSA': 3500,
    'LUMINOSA': 3000, 'DELIZIOSA': 3000, 'NEO': 2200,
    'AIDA': 2500, 'PRIMA': 2500, 'BELLA': 2500, 'LUNA': 2500, 'SOL': 2500,
    'STELLA': 2500, 'PERLA': 2500, 'DIVA': 2500, 'MAR': 2500, 'NOVA': 2500,
    'COSMA': 2500,
    'IONA': 5200, 'ARVIA': 5200, 'BRITANNIA': 3600,
    'AZURA': 3100, 'VENTURA': 3100, 'ARCADIA': 2100, 'AURORA': 1900,
    'QUEEN': 2700, 'QM2': 2700, 'QV': 2000, 'QE': 2100, 'QAN': 3000,
}

TYPICAL_CRUISE_ARRIVAL_HOUR = 8
TYPICAL_CRUISE_DEPARTURE_HOUR = 17


def get_aircraft_capacity(model_str):
    if not model_str:
        return 100
    model_upper = model_str.upper()
    if model_upper in AIRCRAFT_CAPACITIES:
        return AIRCRAFT_CAPACITIES[model_upper]
    for key, cap in sorted(AIRCRAFT_CAPACITIES.items(), key=lambda x: -len(x[0])):
        if key in model_upper or model_upper in key:
            return cap
    nums = re.findall(r'\d+', model_str)
    if nums:
        if len(nums[0]) == 3:
            base = int(nums[0])
            if 700 <= base <= 900:
                return 150 + (base - 700) * 15
            if 300 <= base <= 500:
                return 120 + (base - 300) * 10
    return 100


def get_cruise_ship_capacity(ship_name):
    if not ship_name:
        return 2500
    name_upper = ship_name.upper()
    if name_upper in CRUISE_SHIP_CAPACITIES:
        return CRUISE_SHIP_CAPACITIES[name_upper]
    for key, cap in sorted(CRUISE_SHIP_CAPACITIES.items(), key=lambda x: -len(x[0])):
        if key in name_upper:
            return cap
    mega = ['OASIS', 'ICON', 'WORLD', 'MARDIGRAS', 'CELEBRATION', 'JUBILEE',
            'SMERALDA', 'TOSCANA', 'GRANDIOSA', 'BELLISSIMA', 'MERAVIGLIA',
            'IONA', 'ARVIA']
    large = ['FREEDOM', 'LIBERTY', 'INDEPENDENCE', 'CONQUEST', 'GLORY', 'VALOR',
             'VOYAGER', 'EXPLORER', 'ADVENTURE', 'NAVIGATOR', 'MARINER',
             'QUANTUM', 'ANTHEM', 'OVATION', 'SPECTRUM', 'ODYSSEY',
             'MAGIC', 'DREAM', 'BREEZE', 'VISTA', 'HORIZON', 'PANORAMA',
             'SUNSHINE', 'PRIMA', 'VIVA', 'AQUA', 'EPIC', 'BREAKAWAY',
             'GETAWAY', 'ESCAPE', 'BLISS', 'JOY', 'ENCORE',
             'ROYAL', 'REGAL', 'MAJESTIC', 'SKY', 'ENCHANTED', 'DISCOVERY',
             'WISH', 'TREASURE', 'ADVENTURE']
    medium = ['RADIANCE', 'BRILLIANCE', 'SERENADE', 'JEWEL', 'VISION',
              'ENCHANTMENT', 'GRANDEUR', 'RAPSODY', 'SOVEREIGN', 'MONARCH',
              'GEM', 'JADE', 'PEARL', 'DAWN', 'STAR',
              'EDGE', 'APEX', 'BEYOND', 'ASCENT', 'SOLSTICE', 'EQUINOX',
              'ECLIPSE', 'SILHOUETTE', 'REFLECTION',
              'MILLENNIUM', 'INFINITY', 'SUMMIT', 'CONSTELLATION',
              'ROTTERDAM', 'NIEUW', 'KONINGSDAM', 'EURODAM',
              'OOSTERDAM', 'WESTERDAM', 'NOORDAM', 'VEENDAM',
              'GRAND', 'DIAMOND', 'SAPPHIRE', 'CARIBBEAN', 'CROWN',
              'EMERALD', 'RUBY', 'CORAL', 'ISLAND',
              'FORTUNA', 'MAGICA', 'PACIFICA', 'FAVOLOSA',
              'BRITANNIA', 'AZURA', 'VENTURA', 'ARCADIA', 'AURORA',
              'QM2', 'QV', 'QE', 'QAN']
    small = ['EMPRESS', 'PRIDE', 'LEGEND', 'MIRACLE', 'PARADISE',
             'ELATION', 'SENSATION', 'FANTASY', 'ECSTASY',
             'SPIRIT', 'ZAANDAM', 'VOLENDAM', 'AMSTERDAM',
             'OPERA', 'LYRICA', 'ARMONIA', 'SINFONIA']
    if any(w in name_upper for w in mega):
        return 6000
    if any(w in name_upper for w in large):
        return 4000
    if any(w in name_upper for w in medium):
        return 2500
    if any(w in name_upper for w in small):
        return 2000
    return 2500


def scrape_cruise_ships(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    print(f"Fetching cruise schedule from: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching cruise data: {e}")
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    ships = []
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on page")
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            ship_name = cells[0].get_text(strip=True) if len(cells) > 0 else ''
            if not ship_name or len(ship_name) < 3:
                ship_name = cells[1].get_text(strip=True) if len(cells) > 1 else ''
            skip_words = ['SHIP', 'DATE', 'DAY', 'TIME', 'ARRIVE', 'DEPART',
                          'SCHEDULE', 'CRUISE', 'PORT', 'ROATAN']
            if any(s in ship_name.upper() for s in skip_words):
                continue
            if len(ship_name) < 3:
                continue
            date_str = ''
            for cell in cells:
                text = cell.get_text(strip=True)
                if re.match(r'[A-Z][a-z]{2}\s+\d{1,2}', text) or re.match(r'\d{1,2}/\d{1,2}/\d{4}', text):
                    date_str = text
                    break
            arrival = TYPICAL_CRUISE_ARRIVAL_HOUR
            departure = TYPICAL_CRUISE_DEPARTURE_HOUR
            for cell in cells:
                text = cell.get_text(strip=True)
                time_match = re.findall(r'(\d{1,2}):(\d{2})', text)
                if time_match and len(time_match) >= 1:
                    try:
                        arrival = int(time_match[0][0])
                    except:
                        pass
                if time_match and len(time_match) >= 2:
                    try:
                        departure = int(time_match[1][0])
                    except:
                        pass
            capacity = get_cruise_ship_capacity(ship_name)
            estimated_passengers = int(capacity * 0.95)
            ship_info = {
                'ship_name': ship_name,
                'date_str': date_str,
                'arrival_hour': arrival,
                'departure_hour': departure,
                'capacity': capacity,
                'estimated_passengers': estimated_passengers,
                'type': 'cruise',
                'source_url': url,
            }
            ships.append(ship_info)
            print(f"  Found ship: {ship_name} | Date: {date_str} | "
                  f"Arr: {arrival}:00 Dep: {departure}:00 | Pax: {estimated_passengers}")
    if not ships:
        print("No ships found via table parsing, trying alternative methods...")
        page_text = soup.get_text()
        ship_patterns = re.finditer(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+.*?(?:arrive|depart|am|pm)',
            page_text, re.IGNORECASE)
        for match in ship_patterns:
            name = match.group(1).strip()
            skip = ['HTTP', 'WWW', 'CRUISE', 'SCHEDULE', 'ROATAN', 'HONDURAS']
            if len(name) > 5 and not any(s in name.upper() for s in skip):
                capacity = get_cruise_ship_capacity(name)
                ships.append({
                    'ship_name': name,
                    'date_str': '',
                    'arrival_hour': TYPICAL_CRUISE_ARRIVAL_HOUR,
                    'departure_hour': TYPICAL_CRUISE_DEPARTURE_HOUR,
                    'capacity': capacity,
                    'estimated_passengers': int(capacity * 0.95),
                    'type': 'cruise',
                    'source_url': url,
                })
                print(f"  Found ship (alt): {name} | Pax: {int(capacity * 0.95)}")
    return ships


def get_sample_flight_data():
    typical_flights = [
        ('AA1234', 'B737-800', 'MIA', 'MHRO', 8, 30, True),
        ('AA1235', 'B737-800', 'MIA', 'MHRO', 13, 15, True),
        ('UA1234', 'B737-800', 'IAH', 'MHRO', 9, 45, True),
        ('UA1235', 'B737-800', 'IAH', 'MHRO', 14, 30, True),
        ('DL1234', 'B737-800', 'ATL', 'MHRO', 10, 0, True),
        ('DL1235', 'B737-800', 'ATL', 'MHRO', 15, 0, True),
        ('WN1234', 'B737-800', 'HOU', 'MHRO', 11, 0, True),
        ('WN1235', 'B737-800', 'HOU', 'MHRO', 16, 0, True),
        ('CM1234', 'B737-800', 'PTY', 'MHRO', 9, 0, True),
        ('CM1235', 'B737-800', 'PTY', 'MHRO', 14, 0, True),
        ('AV1234', 'A320', 'SAL', 'MHRO', 10, 30, True),
        ('AV1235', 'A320', 'SAL', 'MHRO', 15, 30, True),
        ('TB1234', 'A320', 'FLL', 'MHRO', 11, 30, True),
        ('TB1235', 'A320', 'FLL', 'MHRO', 16, 30, True),
        ('AA2234', 'B737-800', 'MHRO', 'MIA', 9, 30, False),
        ('AA2235', 'B737-800', 'MHRO', 'MIA', 14, 15, False),
        ('UA2234', 'B737-800', 'MHRO', 'IAH', 10, 45, False),
        ('UA2235', 'B737-800', 'MHRO', 'IAH', 15, 30, False),
        ('DL2234', 'B737-800', 'MHRO', 'ATL', 11, 0, False),
        ('DL2235', 'B737-800', 'MHRO', 'ATL', 16, 0, False),
        ('WN2234', 'B737-800', 'MHRO', 'HOU', 12, 0, False),
        ('WN2235', 'B737-800', 'MHRO', 'HOU', 17, 0, False),
        ('CM2234', 'B737-800', 'MHRO', 'PTY', 10, 0, False),
        ('CM2235', 'B737-800', 'MHRO', 'PTY', 15, 0, False),
        ('AV2234', 'A320', 'MHRO', 'SAL', 11, 30, False),
        ('AV2235', 'A320', 'MHRO', 'SAL', 16, 30, False),
        ('TB2234', 'A320', 'MHRO', 'FLL', 12, 30, False),
        ('TB2235', 'A320', 'MHRO', 'FLL', 17, 30, False),
        ('9N1234', 'AT72', 'RTB', 'MHRO', 7, 0, True),
        ('9N1235', 'AT72', 'MHRO', 'RTB', 7, 45, False),
        ('9N1236', 'AT72', 'RTB', 'MHRO', 12, 0, True),
        ('9N1237', 'AT72', 'MHRO', 'RTB', 12, 45, False),
        ('9N1238', 'AT72', 'RTB', 'MHRO', 16, 0, True),
        ('9N1239', 'AT72', 'MHRO', 'RTB', 16, 45, False),
        ('N1PC', 'C680', 'FLL', 'MHRO', 10, 0, True),
        ('N2PC', 'C680', 'MHRO', 'FLL', 14, 0, False),
        ('N3GX', 'G650', 'TEB', 'MHRO', 11, 0, True),
        ('N4GX', 'G650', 'MHRO', 'TEB', 15, 0, False),
    ]
    flights = []
    for fn, ac, origin, dest, hour, minute, is_arr in typical_flights:
        capacity = get_aircraft_capacity(ac)
        flights.append({
            'flight_number': fn,
            'aircraft': ac,
            'origin': origin,
            'destination': dest,
            'hour': hour,
            'minute': minute,
            'is_arrival': is_arr,
            'capacity': capacity,
            'estimated_passengers': int(capacity * LOAD_FACTOR),
            'type': 'flight',
            'source_url': 'sample_data',
        })
    return flights


def get_sample_cruise_data():
    sample_ships = [
        ('Carnival Magic', 8, 17, 4000),
        ('Norwegian Bliss', 7, 16, 4000),
        ('Royal Caribbean Harmony of the Seas', 8, 18, 6000),
        ('MSC Seaside', 9, 17, 5000),
        ('Celebrity Edge', 8, 16, 3000),
        ('Disney Fantasy', 7, 15, 4000),
        ('Princess Royal', 8, 17, 3600),
        ('Holland America Nieuw Amsterdam', 9, 18, 2700),
        ('Carnival Vista', 8, 16, 4000),
        ('Norwegian Epic', 7, 17, 4200),
    ]
    ships = []
    for name, arr, dep, cap in sample_ships:
        ships.append({
            'ship_name': name,
            'date_str': '',
            'arrival_hour': arr,
            'departure_hour': dep,
            'capacity': cap,
            'estimated_passengers': int(cap * 0.95),
            'type': 'cruise',
            'source_url': 'sample_data',
        })
    return ships


def get_weather_data(year, month):
    """Generate realistic weather data for Roatan for a given year/month."""
    random.seed(year * 100 + month)

    num_days = calendar.monthrange(year, month)[1]

    if month in [1, 2, 3, 4]:
        base_high = 29.0
        base_low = 23.0
        rain_prob = 0.15
        avg_precip = 2.0
    elif month in [5, 6]:
        base_high = 31.0
        base_low = 25.0
        rain_prob = 0.35
        avg_precip = 4.0
    elif month in [7, 8]:
        base_high = 32.0
        base_low = 26.0
        rain_prob = 0.40
        avg_precip = 5.0
    elif month in [9, 10]:
        base_high = 31.0
        base_low = 25.0
        rain_prob = 0.55
        avg_precip = 7.0
    else:
        base_high = 29.0
        base_low = 24.0
        rain_prob = 0.30
        avg_precip = 3.5

    weather_data = {}

    for day in range(1, num_days + 1):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"

        high_temp = round(base_high + random.uniform(-2, 2), 1)
        low_temp = round(base_low + random.uniform(-1.5, 1.5), 1)

        has_precipitation = random.random() < rain_prob
        if has_precipitation:
            precipitation = round(random.uniform(0.5, avg_precip * 2), 1)
        else:
            precipitation = 0.0

        if precipitation == 0:
            condition = 'Sunny'
        elif precipitation < 3:
            condition = 'Partly Cloudy'
        elif precipitation < 8:
            condition = 'Showers'
        else:
            condition = 'Thunderstorms'

        humidity = random.randint(75, 92)
        wind_speed = random.randint(8, 25)

        weather_data[date_str] = {
            'high_c': high_temp,
            'low_c': low_temp,
            'high_f': round(high_temp * 9/5 + 32, 1),
            'low_f': round(low_temp * 9/5 + 32, 1),
            'precipitation_mm': precipitation,
            'condition': condition,
            'humidity_pct': humidity,
            'wind_kmh': wind_speed,
        }

    return weather_data


def generate_monthly_data(year=2026, month=6):
    """Generate full month of data for a given year/month with daily variations."""
    random.seed(year * 1000 + month)

    num_days = calendar.monthrange(year, month)[1]
    month_abbr = datetime(year, month, 1).strftime('%b').lower()
    month_name = datetime(year, month, 1).strftime('%B')

    all_cruise_ships = [
        ('Carnival Magic', 8, 17, 4000),
        ('Norwegian Bliss', 7, 16, 4000),
        ('Royal Caribbean Harmony of the Seas', 8, 18, 6000),
        ('MSC Seaside', 9, 17, 5000),
        ('Celebrity Edge', 8, 16, 3000),
        ('Disney Fantasy', 7, 15, 4000),
        ('Princess Royal', 8, 17, 3600),
        ('Holland America Nieuw Amsterdam', 9, 18, 2700),
        ('Carnival Vista', 8, 16, 4000),
        ('Norwegian Epic', 7, 17, 4200),
        ('Royal Caribbean Oasis of the Seas', 8, 18, 6000),
        ('MSC Meraviglia', 8, 17, 6000),
        ('Celebrity Apex', 8, 16, 3000),
        ('Costa Smeralda', 8, 17, 6000),
        ('AIDAnova', 8, 17, 2500),
    ]

    flight_template = [
        ('AA1234', 'B737-800', 'MIA', 'MHRO', 8, 30, True),
        ('AA1235', 'B737-800', 'MIA', 'MHRO', 13, 15, True),
        ('UA1234', 'B737-800', 'IAH', 'MHRO', 9, 45, True),
        ('UA1235', 'B737-800', 'IAH', 'MHRO', 14, 30, True),
        ('DL1234', 'B737-800', 'ATL', 'MHRO', 10, 0, True),
        ('DL1235', 'B737-800', 'ATL', 'MHRO', 15, 0, True),
        ('WN1234', 'B737-800', 'HOU', 'MHRO', 11, 0, True),
        ('WN1235', 'B737-800', 'HOU', 'MHRO', 16, 0, True),
        ('CM1234', 'B737-800', 'PTY', 'MHRO', 9, 0, True),
        ('CM1235', 'B737-800', 'PTY', 'MHRO', 14, 0, True),
        ('AV1234', 'A320', 'SAL', 'MHRO', 10, 30, True),
        ('AV1235', 'A320', 'SAL', 'MHRO', 15, 30, True),
        ('TB1234', 'A320', 'FLL', 'MHRO', 11, 30, True),
        ('TB1235', 'A320', 'FLL', 'MHRO', 16, 30, True),
        ('AA2234', 'B737-800', 'MHRO', 'MIA', 9, 30, False),
        ('AA2235', 'B737-800', 'MHRO', 'MIA', 14, 15, False),
        ('UA2234', 'B737-800', 'MHRO', 'IAH', 10, 45, False),
        ('UA2235', 'B737-800', 'MHRO', 'IAH', 15, 30, False),
        ('DL2234', 'B737-800', 'MHRO', 'ATL', 11, 0, False),
        ('DL2235', 'B737-800', 'MHRO', 'ATL', 16, 0, False),
        ('WN2234', 'B737-800', 'MHRO', 'HOU', 12, 0, False),
        ('WN2235', 'B737-800', 'MHRO', 'HOU', 17, 0, False),
        ('CM2234', 'B737-800', 'MHRO', 'PTY', 10, 0, False),
        ('CM2235', 'B737-800', 'MHRO', 'PTY', 15, 0, False),
        ('AV2234', 'A320', 'MHRO', 'SAL', 11, 30, False),
        ('AV2235', 'A320', 'MHRO', 'SAL', 16, 30, False),
        ('TB2234', 'A320', 'MHRO', 'FLL', 12, 30, False),
        ('TB2235', 'A320', 'MHRO', 'FLL', 17, 30, False),
        ('9N1234', 'AT72', 'RTB', 'MHRO', 7, 0, True),
        ('9N1235', 'AT72', 'MHRO', 'RTB', 7, 45, False),
        ('9N1236', 'AT72', 'RTB', 'MHRO', 12, 0, True),
        ('9N1237', 'AT72', 'MHRO', 'RTB', 12, 45, False),
        ('9N1238', 'AT72', 'RTB', 'MHRO', 16, 0, True),
        ('9N1239', 'AT72', 'MHRO', 'RTB', 16, 45, False),
        ('N1PC', 'C680', 'FLL', 'MHRO', 10, 0, True),
        ('N2PC', 'C680', 'MHRO', 'FLL', 14, 0, False),
        ('N3GX', 'G650', 'TEB', 'MHRO', 11, 0, True),
        ('N4GX', 'G650', 'MHRO', 'TEB', 15, 0, False),
    ]

    # Try to scrape real cruise data
    cruise_url = f"https://www.cruisetimetables.com/roatanhondurasschedule-{month_abbr}{year}.html"
    scraped_ships = scrape_cruise_ships(cruise_url)

    monthly_data = {'days': {}}

    for day in range(1, num_days + 1):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        day_data = {'flights': [], 'cruises': []}

        # Add flights (daily repeating schedule with slight variations)
        for fn, ac, origin, dest, hour, minute, is_arr in flight_template:
            # Slight variation in passenger count per day
            base_pax = int(get_aircraft_capacity(ac) * LOAD_FACTOR)
            variation = random.randint(-10, 15)
            pax = max(0, base_pax + variation)

            day_data['flights'].append({
                'flight_number': fn,
                'aircraft': ac,
                'origin': origin,
                'destination': dest,
                'hour': hour,
                'minute': minute,
                'is_arrival': is_arr,
                'estimated_passengers': pax,
            })

        # Add cruise ships (rotating schedule - different ships on different days)
        if scraped_ships:
            # Use scraped data - assign ships to days based on date_str matching
            for ship in scraped_ships:
                ship_date = ship.get('date_str', '')
                if ship_date:
                    try:
                        parsed = datetime.strptime(ship_date, '%b %d')
                        ship_day = parsed.day
                        if ship_day == day:
                            day_data['cruises'].append({
                                'ship_name': ship['ship_name'],
                                'arrival_hour': ship['arrival_hour'],
                                'departure_hour': ship['departure_hour'],
                                'estimated_passengers': ship['estimated_passengers'],
                                'is_arrival': True,
                            })
                    except:
                        pass
        else:
            # Use sample data rotation
            ships_per_day = random.randint(1, 3)
            selected = random.sample(all_cruise_ships, min(ships_per_day, len(all_cruise_ships)))
            for name, arr, dep, cap in selected:
                pax = int(cap * 0.95)
                day_data['cruises'].append({
                    'ship_name': name,
                    'arrival_hour': arr,
                    'departure_hour': dep,
                    'estimated_passengers': pax,
                    'is_arrival': True,
                })

        monthly_data['days'][date_str] = day_data

    print(f"Generated data for {month_name} {year}: {num_days} days, "
          f"{sum(len(d['flights']) for d in monthly_data['days'].values())} flights, "
          f"{sum(len(d['cruises']) for d in monthly_data['days'].values())} cruise events")
    return monthly_data


def collect_all_data():
    """Legacy function - generates data for June 2026."""
    return generate_monthly_data(2026, 6)
