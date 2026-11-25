"""
Checks that today.json agrees with today.html.   Run:  python -m unittest test_today_json

Uses a small made-up schedule, so it needs no network and no data files. The same
check_today_json() also runs inside every build and stops it on a mismatch.
"""
import copy
import unittest
from datetime import date, datetime

from daily_message import LEVELS, ROATAN_TZ
from seo_pages import TODAY_JSON_DAYS, check_today_json, crowd_levels, today_json, today_page

SITE = 'https://example.test'
TODAY = date(2026, 11, 28)   # the 14 days run into December


def ship(name, pax, arrive=8, depart=17, line='Test Line', prev=None, nxt=None):
    c = {'ship_name': name, 'cruise_line': line, 'arrival_hour': arrive, 'departure_hour': depart,
         'estimated_passengers': pax}
    if prev is not None:
        c['previous_ports'] = prev
    if nxt is not None:
        c['next_ports'] = nxt
    return c


def schedule():
    nov = {'meta': {'cruise_source': 'scraped', 'cruise_checked': '2026-11-27'},
           'days': {f'2026-11-{d:02d}': {'cruises': []} for d in range(1, 31)}}
    dec = {'meta': {'cruise_source': 'scraped', 'cruise_checked': '2026-11-27'},
           'days': {f'2026-12-{d:02d}': {'cruises': []} for d in range(1, 32)}}
    nov['days']['2026-11-28']['cruises'] = [
        ship('Zulu & Sons <Star>', 2382, 9, 18, prev=['Nov 27, 2026: At Sea', 'Nov 26, 2026: Grand Cayman'],
             nxt=['Nov 29, 2026: Jamaica']),
        ship('Alpha', 5000, 8, 17),
        ship('Bravo', 3146, 7, 16, line=''),
    ]
    nov['days']['2026-11-29']['cruises'] = [ship('Solo', 2999)]            # top of "quiet"
    nov['days']['2026-11-30']['cruises'] = [ship('Edge', 3000)]            # bottom of "moderate"
    dec['days']['2026-12-01']['cruises'] = [ship('A', 5999), ship('B', 1)]  # 6,000: "busy"
    dec['days']['2026-12-02']['cruises'] = [ship('C', 9999)]
    dec['days']['2026-12-03']['cruises'] = [ship('D', 10000)]              # "very busy"
    return {(2026, 11): nov, (2026, 12): dec}


def build(all_data, today=TODAY):
    html = today_page(SITE, all_data, '2026-11-28', today)
    data = today_json(SITE, all_data, today, now=datetime(2026, 11, 28, 5, 0, tzinfo=ROATAN_TZ))
    return html, data


class TodayJsonTest(unittest.TestCase):
    def test_matches_today_html(self):
        html, data = build(schedule())
        self.assertEqual(check_today_json(html, data, TODAY), [])

    def test_schema(self):
        _html, data = build(schedule())
        self.assertEqual(data['schema_version'], 1)
        self.assertEqual(data['generated_at'], '2026-11-28T05:00:00-06:00')
        self.assertEqual(data['timezone'], 'America/Tegucigalpa')
        self.assertEqual(data['source_checked'], '2026-11-27')
        self.assertEqual(len(data['days']), TODAY_JSON_DAYS)
        self.assertEqual(TODAY_JSON_DAYS, 14)
        self.assertEqual(data['days'][0]['date'], '2026-11-28')
        self.assertEqual(data['days'][-1]['date'], '2026-12-11')
        day = data['days'][0]
        self.assertEqual((day['ships_count'], day['est_passengers'], day['crowd']), (3, 10528, 'very_busy'))
        self.assertEqual([s['name'] for s in day['ships']], ['Bravo', 'Alpha', 'Zulu & Sons <Star>'])
        self.assertEqual(day['ships'][2], {
            'name': 'Zulu & Sons <Star>', 'line': 'Test Line', 'arrive': '09:00', 'depart': '18:00',
            'est_passengers': 2382, 'prev_port': 'Grand Cayman', 'next_port': 'Jamaica'})
        # Unknown values are null, never made up.
        self.assertIsNone(day['ships'][0]['line'])
        self.assertIsNone(day['ships'][0]['prev_port'])
        self.assertIsNone(day['ships'][0]['next_port'])

    def test_crowd_levels_come_from_the_site(self):
        levels = crowd_levels()
        self.assertEqual([(lv['key'], lv['min'], lv['max']) for lv in levels], [
            ('none', 0, 0), ('quiet', 1, 2999), ('moderate', 3000, 5999),
            ('busy', 6000, 9999), ('very_busy', 10000, None)])
        self.assertEqual(sorted(lv['min'] for lv in levels), sorted(lv[0] for lv in LEVELS))
        _html, data = build(schedule())
        crowd = {d['date']: d['crowd'] for d in data['days']}
        self.assertEqual([crowd[d] for d in ('2026-11-29', '2026-11-30', '2026-12-01', '2026-12-02',
                                             '2026-12-03', '2026-12-04')],
                         ['quiet', 'moderate', 'busy', 'busy', 'very_busy', 'none'])

    def test_no_ships_today(self):
        all_data = schedule()
        all_data[(2026, 11)]['days']['2026-11-28']['cruises'] = []
        html, data = build(all_data)
        self.assertEqual(data['days'][0]['crowd'], 'none')
        self.assertEqual(check_today_json(html, data, TODAY), [])

    def test_days_without_data_are_left_out(self):
        all_data = schedule()
        del all_data[(2026, 12)]
        html, data = build(all_data)
        self.assertEqual([d['date'] for d in data['days']], ['2026-11-28', '2026-11-29', '2026-11-30'])
        self.assertEqual(check_today_json(html, data, TODAY), [])

    def test_check_catches_a_wrong_total(self):
        html, data = build(schedule())
        for path in (('days', 0, 'est_passengers'), ('days', 0, 'ships_count'), ('days', 3, 'est_passengers')):
            bad = copy.deepcopy(data)
            bad[path[0]][path[1]][path[2]] += 1
            self.assertTrue(check_today_json(html, bad, TODAY), path)
        bad = copy.deepcopy(data)
        bad['days'][0]['ships'][1]['est_passengers'] -= 1
        self.assertTrue(check_today_json(html, bad, TODAY))
        bad = copy.deepcopy(data)
        bad['days'][2]['crowd'] = 'busy'
        self.assertTrue(check_today_json(html, bad, TODAY))
        bad = copy.deepcopy(data)
        del bad['days'][0]
        self.assertTrue(check_today_json(html, bad, TODAY))


if __name__ == '__main__':
    unittest.main()
