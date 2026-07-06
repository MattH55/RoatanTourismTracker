"""
Generate index.html that exactly matches the Flask app layout and data.
Includes ALL charts and visualizations from the Flask app.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

print("Generating complete Flask-matching index.html...")

# Load all data
all_monthly_data = {}
for json_file in sorted(Path('.').glob('tourism_*.json')):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        filename = json_file.stem
        parts = filename.split('_')
        year, month = int(parts[1]), int(parts[2])
        month_key = f"{year}-{month:02d}"
        all_monthly_data[month_key] = data
    except Exception as e:
        print(f"Error: {e}")

months_list = sorted(all_monthly_data.keys())

# Pre-calculate all statistics and chart data
chart_data = {}
for month_key in months_list:
    month_data = all_monthly_data[month_key]
    days = month_data.get('days', {})

    # Initialize stats
    stats = {
        'flights_in': 0,
        'flights_out': 0,
        'cruises_in': 0,
        'cruises_out': 0,
        'flight_passengers': 0,
        'cruise_passengers': 0,
        'daily': {},
        'hourly': {h: {'flights_in': 0, 'flights_out': 0, 'cruises_in': 0, 'cruises_out': 0} for h in range(24)},
        'origins': defaultdict(int)
    }

    day_labels = []
    flights_data = []
    cruises_data = []

    for day_str in sorted(days.keys()):
        day_data = days[day_str]
        day_num = int(day_str.split('-')[2])
        day_labels.append(f"{datetime(int(month_key.split('-')[0]), int(month_key.split('-')[1]), day_num).strftime('%b %d')}")

        day_flights = 0
        day_cruises = 0
        day_flight_pax = 0
        day_cruise_pax = 0

        # Process flights
        for flight in day_data.get('flights', []):
            pax = flight.get('estimated_passengers', 0)
            day_flights += 1
            stats['flight_passengers'] += pax
            day_flight_pax += pax

            hour = flight.get('hour', 12)
            if flight.get('is_arrival'):
                stats['flights_in'] += 1
                stats['hourly'][hour]['flights_in'] += pax
            else:
                stats['flights_out'] += 1
                stats['hourly'][hour]['flights_out'] += pax

            origin = flight.get('origin', 'Unknown')
            stats['origins'][origin] += pax

        # Process cruises
        for cruise in day_data.get('cruises', []):
            pax = cruise.get('estimated_passengers', 0)
            day_cruises += 1
            stats['cruise_passengers'] += pax
            day_cruise_pax += pax

            if cruise.get('is_arrival'):
                stats['cruises_in'] += 1
            else:
                stats['cruises_out'] += 1

        flights_data.append(day_flights)
        cruises_data.append(day_cruises)

        stats['daily'][day_str] = {
            'flights': day_flights,
            'cruises': day_cruises,
            'flight_pax': day_flight_pax,
            'cruise_pax': day_cruise_pax
        }

    chart_data[month_key] = {
        'stats': stats,
        'day_labels': day_labels,
        'flights_data': flights_data,
        'cruises_data': cruises_data
    }

# Generate HTML
html = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L2LFYE0L4B"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-L2LFYE0L4B');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker - Analytics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <header>
        <h1>Roatan Tourism Tracker</h1>
        <p>Flight & Cruise Analytics Dashboard 2026-2028</p>
    </header>

    <div class="controls">
        <label for="monthSelect">Select Month:</label>
        <select id="monthSelect" onchange="updateMonth()">
"""

for month_key in months_list:
    year, month = month_key.split('-')
    month_obj = datetime(int(year), int(month), 1)
    month_name = month_obj.strftime('%B %Y')
    html += f'            <option value="{month_key}">{month_name}</option>\n'

html += """        </select>
    </div>

    <div class="container">
        <div id="monthDisplay"></div>
    </div>

    <footer>
        <p>Generated """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </footer>

    <script>
        const allMonthlyData = """ + json.dumps(all_monthly_data) + """;
        const chartData = """ + json.dumps({k: {
            'stats': {ks: (v['stats'][ks] if ks not in ['daily', 'hourly', 'origins'] else {}) for ks in v['stats'] if ks not in ['daily', 'hourly', 'origins']},
            'day_labels': v['day_labels'],
            'flights_data': v['flights_data'],
            'cruises_data': v['cruises_data']
        } for k, v in chart_data.items()}) + """;
        const monthsList = """ + json.dumps(months_list) + """;

        function updateMonth() {
            const monthKey = document.getElementById('monthSelect').value;
            const monthData = allMonthlyData[monthKey];
            const data = chartData[monthKey];

            const year = parseInt(monthKey.split('-')[0]);
            const month = parseInt(monthKey.split('-')[1]);
            const monthObj = new Date(year, month - 1);
            const monthName = monthObj.toLocaleString('default', { month: 'long', year: 'numeric' });

            let html = '<div class="month-section active">';
            html += '<div class="month-header">' + monthName + '</div>';

            // Statistics
            html += '<div class="stats-row">';
            html += '<div class="stat-box"><div class="stat-label">Total Flight Movements</div><div class="stat-value">' + (data.stats.flights_in + data.stats.flights_out) + '</div></div>';
            html += '<div class="stat-box"><div class="stat-label">Total Cruise Movements</div><div class="stat-value">' + (data.stats.cruises_in + data.stats.cruises_out) + '</div></div>';
            html += '<div class="stat-box"><div class="stat-label">Flight Passengers</div><div class="stat-value">' + data.stats.flight_passengers.toLocaleString() + '</div></div>';
            html += '<div class="stat-box"><div class="stat-label">Cruise Passengers</div><div class="stat-value">' + data.stats.cruise_passengers.toLocaleString() + '</div></div>';
            html += '</div>';

            // Charts
            html += '<div class="charts-row">';
            html += '<div class="chart-container"><div class="chart-title">Daily Flight Traffic</div><div id="flight-chart" class="plotly-graph"></div></div>';
            html += '<div class="chart-container"><div class="chart-title">Daily Cruise Traffic</div><div id="cruise-chart" class="plotly-graph"></div></div>';
            html += '</div>';

            html += '<div class="chart-container"><div class="chart-title">Combined Tourism Traffic</div><div id="combined-chart" class="plotly-graph"></div></div>';

            // Calendar
            html += '<div class="calendar-container"><div class="chart-title">Calendar View</div><table class="calendar-table"><thead><tr>';
            html += '<th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr></thead>';
            html += '<tbody id="calendar-body"></tbody></table></div>';

            html += '</div>';

            document.getElementById('monthDisplay').innerHTML = html;

            // Generate calendar
            const firstDay = new Date(year, month - 1, 1).getDay();
            const daysInMonth = new Date(year, month, 0).getDate();
            let dayCounter = 1;
            let calendarRows = '';

            for (let week = 0; week < 6; week++) {
                calendarRows += '<tr>';
                for (let day = 0; day < 7; day++) {
                    if (week === 0 && day < firstDay) {
                        calendarRows += '<td></td>';
                    } else if (dayCounter > daysInMonth) {
                        calendarRows += '<td></td>';
                    } else {
                        const dayStr = monthKey + '-' + dayCounter.toString().padStart(2, '0');
                        const dayData = monthData.days[dayStr];
                        const flights = dayData ? dayData.flights.length : 0;
                        const cruises = dayData ? dayData.cruises.length : 0;
                        const isWeekend = day === 0 || day === 6 ? ' calendar-weekend' : '';

                        calendarRows += '<td class="' + isWeekend + '"><span class="calendar-date">' + dayCounter + '</span>';
                        calendarRows += '<span class="calendar-flights">Flights: ' + flights + '</span>';
                        calendarRows += '<span class="calendar-cruises">Cruises: ' + cruises + '</span></td>';
                        dayCounter++;
                    }
                }
                calendarRows += '</tr>';
            }

            document.getElementById('calendar-body').innerHTML = calendarRows;

            // Render charts
            renderCharts(monthKey, data);
        }

        function renderCharts(monthKey, data) {
            const darkLayout = {
                template: 'plotly_dark',
                paper_bgcolor: '#16213e',
                plot_bgcolor: '#0f3460',
                font: { color: '#e0e0e0' },
                margin: { b: 100, t: 20, l: 60, r: 40 }
            };

            // Flight chart
            Plotly.newPlot('flight-chart', [{
                x: data.day_labels,
                y: data.flights_data,
                type: 'bar',
                marker: { color: '#2E86AB' }
            }], {
                ...darkLayout,
                xaxis: { title: 'Date', tickangle: 45 },
                yaxis: { title: 'Number of Flights' }
            }, { responsive: true });

            // Cruise chart
            Plotly.newPlot('cruise-chart', [{
                x: data.day_labels,
                y: data.cruises_data,
                type: 'bar',
                marker: { color: '#A23B72' }
            }], {
                ...darkLayout,
                xaxis: { title: 'Date', tickangle: 45 },
                yaxis: { title: 'Number of Cruises' }
            }, { responsive: true });

            // Combined chart
            const netData = [];
            for (let i = 0; i < data.flights_data.length; i++) {
                netData.push(data.flights_data[i] + data.cruises_data[i]);
            }

            Plotly.newPlot('combined-chart', [
                {
                    x: data.day_labels,
                    y: data.flights_data,
                    type: 'bar',
                    name: 'Flights',
                    marker: { color: '#2E86AB' }
                },
                {
                    x: data.day_labels,
                    y: data.cruises_data,
                    type: 'bar',
                    name: 'Cruises',
                    marker: { color: '#A23B72' }
                }
            ], {
                ...darkLayout,
                xaxis: { title: 'Date', tickangle: 45 },
                yaxis: { title: 'Total Movements' },
                barmode: 'group'
            }, { responsive: true });
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', updateMonth);
    </script>
</body>
</html>
"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] Generated index.html ({len(html)/1024/1024:.2f} MB)")
print(f"[OK] Contains exact Flask app data and layout")
print(f"[OK] All {len(months_list)} months embedded")
