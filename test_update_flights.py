"""
Checks that the flight fetch spaces out its API calls and retries a 429.
Run:  python -m unittest test_update_flights

No network and no real waiting: requests.get and the clock are replaced.
"""
import unittest
from datetime import date
from unittest import mock

import requests

import update_flights


class FakeResponse:
    def __init__(self, status, headers=None):
        self.status_code = status
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f'{self.status_code} Client Error')

    def json(self):
        return {'arrivals': [], 'departures': []}


class FakeClock:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class RetryTest(unittest.TestCase):
    def run_fetch(self, responses):
        clock = FakeClock()
        update_flights._last_request = float('-inf')
        with mock.patch.object(update_flights.requests, 'get', side_effect=responses) as get, \
                mock.patch.object(update_flights.time, 'monotonic', clock.monotonic), \
                mock.patch.object(update_flights.time, 'sleep', clock.sleep), \
                mock.patch('builtins.print'):
            try:
                result = update_flights.fetch_day(date(2026, 11, 25), 'key')
            except requests.HTTPError as e:
                result = e
        return result, get.call_count, clock.sleeps

    def test_calls_are_spaced_out(self):
        result, calls, sleeps = self.run_fetch([FakeResponse(200), FakeResponse(200)])
        self.assertEqual(result['date'], '2026-11-25')
        self.assertEqual(calls, 2)
        self.assertEqual(sleeps, [update_flights.REQUEST_GAP])

    def test_429_is_retried(self):
        result, calls, sleeps = self.run_fetch([FakeResponse(200), FakeResponse(429), FakeResponse(200)])
        self.assertEqual(result['date'], '2026-11-25')
        self.assertEqual(calls, 3)
        self.assertIn(update_flights.RETRY_WAITS[0], sleeps)

    def test_retry_after_header_is_used_and_capped(self):
        _result, _calls, sleeps = self.run_fetch(
            [FakeResponse(429, {'Retry-After': '7'}), FakeResponse(429, {'Retry-After': '9999'}),
             FakeResponse(200), FakeResponse(200)])
        self.assertIn(7.0, sleeps)
        self.assertIn(update_flights.MAX_RETRY_WAIT, sleeps)

    def test_gives_up_after_the_last_retry(self):
        tries = len(update_flights.RETRY_WAITS) + 1
        result, calls, _sleeps = self.run_fetch([FakeResponse(429)] * tries)
        self.assertIsInstance(result, requests.HTTPError)
        self.assertEqual(calls, tries)

    def test_other_errors_are_not_retried(self):
        result, calls, _sleeps = self.run_fetch([FakeResponse(500)])
        self.assertIsInstance(result, requests.HTTPError)
        self.assertEqual(calls, 1)


if __name__ == '__main__':
    unittest.main()
