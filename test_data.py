"""Test data generation and app functionality."""
import sys
sys.path.insert(0, '.')
from app import load_monthly_data, create_monthly_stats, get_month_label, AVAILABLE_MONTHS

# Test loading June 2026
data = load_monthly_data(2026, 6)
print(f'June 2026: {len(data["days"])} days')
stats = create_monthly_stats(data)
print(f'  Total arrivals: {stats["total_arrivals"]:,}')
print(f'  Total departures: {stats["total_departures"]:,}')
print(f'  Flights: {stats["total_flights"]}')
print(f'  Cruise ships: {stats["total_cruise_ships"]}')

# Test loading a future month
data2 = load_monthly_data(2027, 3)
print(f'March 2027: {len(data2["days"])} days')
stats2 = create_monthly_stats(data2)
print(f'  Total arrivals: {stats2["total_arrivals"]:,}')
print(f'  Total departures: {stats2["total_departures"]:,}')
print(f'  Flights: {stats2["total_flights"]}')
print(f'  Cruise ships: {stats2["total_cruise_ships"]}')

# Test loading Nov 2028 (last month)
data3 = load_monthly_data(2028, 11)
print(f'Nov 2028: {len(data3["days"])} days')
stats3 = create_monthly_stats(data3)
print(f'  Total arrivals: {stats3["total_arrivals"]:,}')

print(f'\nAVAILABLE_MONTHS: {len(AVAILABLE_MONTHS)} months')
print(f'First: {get_month_label(2026, 6)}')
print(f'Last: {get_month_label(2028, 11)}')
print('\nAll tests passed!')
