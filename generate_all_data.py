"""Generate data for all 30 months (June 2026 - November 2028)."""
import sys
sys.path.insert(0, '.')
from app import AVAILABLE_MONTHS, get_month_label, load_monthly_data
import time

print(f"Generating data for {len(AVAILABLE_MONTHS)} months...")
print("=" * 50)

for i, (year, month) in enumerate(AVAILABLE_MONTHS):
    label = get_month_label(year, month)
    print(f"[{i+1}/{len(AVAILABLE_MONTHS)}] {label}...", end=' ', flush=True)
    start = time.time()
    data = load_monthly_data(year, month)
    elapsed = time.time() - start
    days = len(data['days'])
    flights = sum(len(data['days'][d].get('flights', [])) for d in data['days'])
    cruises = sum(len(data['days'][d].get('cruises', [])) for d in data['days'])
    print(f"{days} days, {flights} flights, {cruises} cruise events ({elapsed:.1f}s)")

print("=" * 50)
print("All data generated successfully!")
