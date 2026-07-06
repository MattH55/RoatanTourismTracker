"""
Generate a complete web-ready package with proper directory structure.
Creates index.html and supporting files for web upload.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def create_web_package():
    """Create complete web-ready package."""

    # Create directory structure
    dirs = ['pages', 'assets']
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)

    # Load all data
    all_monthly_data = {}
    all_cruises = []

    for json_file in sorted(Path('.').glob('tourism_*.json')):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            filename = json_file.stem
            parts = filename.split('_')
            year = int(parts[1])
            month = int(parts[2])
            month_key = f"{year}-{month:02d}"
            all_monthly_data[month_key] = data

            # Collect cruises
            days = data.get('days', {})
            for day_str in sorted(days.keys()):
                day_data = days[day_str]
                for cruise in day_data.get('cruises', []):
                    cruise['date'] = day_str
                    all_cruises.append(cruise)

        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    months_list = sorted(all_monthly_data.keys())

    print("[OK] Creating web package structure...")

    # ====== CREATE INDEX.HTML (Main Flask Replica) ======
    html_index = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <header>
        <h1>Roatan Tourism Tracker</h1>
        <p>Flight & Cruise Analytics Dashboard 2026-2028</p>
        <nav class="header-nav">
            <a href="index.html" class="nav-link active">Analytics</a>
            <a href="pages/schedule.html" class="nav-link">Cruise Schedule</a>
            <a href="pages/dashboard.html" class="nav-link">Dashboard</a>
        </nav>
    </header>

    <div class="controls">
        <label for="monthSelect">Select Month:</label>
        <select id="monthSelect" onchange="changeMonth()">
"""

    # Add month options
    for month_key in months_list:
        year, month = month_key.split('-')
        month_obj = datetime(int(year), int(month), 1)
        month_name = month_obj.strftime('%B %Y')
        html_index += f'            <option value="{month_key}">{month_name}</option>\n'

    html_index += """        </select>
    </div>

    <div class="container" id="chartsContainer">
        <!-- Month sections will be inserted here -->
    </div>

    <footer>
        <p>Generated """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """ | Data: June 2026 - November 2028</p>
        <p><a href="https://github.com" target="_blank">GitHub</a> |
           <a href="README.md" target="_blank">Documentation</a></p>
    </footer>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="assets/app.js"></script>
    <script>
        const allMonthlyData = """ + json.dumps(all_monthly_data) + """;
        const monthsList = """ + json.dumps(months_list) + """;

        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
        });
    </script>
</body>
</html>
"""

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_index)

    print("[OK] Created index.html (5.8 MB embedded)")

    # ====== CREATE ASSETS/STYLES.CSS ======
    css_content = """/* Roatan Tourism Tracker Styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #1a1a2e;
    color: #e0e0e0;
    padding: 20px;
}

header {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
    color: white;
    padding: 30px 40px;
    border-radius: 10px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

h1 {
    font-size: 2.2em;
    margin-bottom: 10px;
}

header p {
    font-size: 1.1em;
    opacity: 0.9;
    margin-bottom: 15px;
}

.header-nav {
    display: flex;
    gap: 20px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.2);
}

.nav-link {
    color: #e0e0e0;
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 5px;
    transition: all 0.3s;
    border: 1px solid transparent;
}

.nav-link:hover,
.nav-link.active {
    background: #e94560;
    color: white;
    border-color: #e94560;
}

.controls {
    background: #16213e;
    padding: 20px 40px;
    border-radius: 10px;
    margin-bottom: 30px;
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

select {
    padding: 10px 15px;
    background: #0f3460;
    color: white;
    border: 1px solid #e94560;
    border-radius: 5px;
    font-size: 1em;
    cursor: pointer;
    transition: all 0.3s;
}

select:hover {
    border-color: #ff6b6b;
}

select option {
    background: #0f3460;
    color: white;
}

label {
    color: #e0e0e0;
    font-weight: 600;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
}

.month-section {
    display: none;
}

.month-section.active {
    display: block;
    animation: fadeIn 0.3s;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.month-header {
    background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
    color: white;
    padding: 20px 40px;
    border-radius: 10px;
    margin-bottom: 20px;
    font-size: 1.8em;
    font-weight: bold;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-box {
    background: #16213e;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #e94560;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.stat-label {
    color: #b0b0b0;
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-value {
    font-size: 2em;
    font-weight: bold;
    color: #e94560;
    margin-top: 10px;
}

.chart-container {
    background: #16213e;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 30px;
    border: 1px solid #0f3460;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.chart-title {
    color: #e0e0e0;
    font-size: 1.3em;
    font-weight: bold;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e94560;
}

.plotly-graph {
    width: 100%;
    min-height: 400px;
}

.charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.calendar-container {
    background: #16213e;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 30px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    overflow-x: auto;
}

.calendar-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

.calendar-table thead {
    background: #0f3460;
}

.calendar-table th {
    padding: 10px;
    text-align: center;
    color: #e94560;
    font-weight: bold;
    border: 1px solid #0f3460;
}

.calendar-table td {
    padding: 10px;
    text-align: right;
    border: 1px solid #0f3460;
    height: 70px;
    vertical-align: top;
    background: #0f3460;
    font-size: 0.85em;
}

.calendar-date {
    display: block;
    font-weight: bold;
    color: #e0e0e0;
    margin-bottom: 5px;
    font-size: 1em;
}

.calendar-flights {
    display: block;
    color: #2E86AB;
    margin-bottom: 2px;
}

.calendar-cruises {
    display: block;
    color: #A23B72;
}

.calendar-weekend {
    background: #1a2e4a;
}

footer {
    background: #16213e;
    padding: 20px 40px;
    border-radius: 10px;
    text-align: center;
    color: #b0b0b0;
    margin-top: 40px;
    border: 1px solid #0f3460;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

footer a {
    color: #e94560;
    text-decoration: none;
    margin: 0 10px;
}

footer a:hover {
    text-decoration: underline;
}

/* Search and Filter Styles */
.search-box {
    padding: 10px 15px;
    background: #0f3460;
    color: white;
    border: 1px solid #e94560;
    border-radius: 5px;
    font-size: 1em;
    flex: 1;
    min-width: 200px;
}

.search-box::placeholder {
    color: #888;
}

/* Table Styles */
.data-table {
    width: 100%;
    border-collapse: collapse;
    background: #16213e;
    margin-top: 15px;
}

.data-table thead {
    background: #0f3460;
}

.data-table th {
    padding: 12px;
    text-align: left;
    font-weight: 600;
    color: #e94560;
    border-bottom: 2px solid #0f3460;
}

.data-table td {
    padding: 12px;
    border-bottom: 1px solid #0f3460;
}

.data-table tr:hover {
    background: #1a2e4a;
}

.ship-name {
    font-weight: 600;
    color: #e94560;
}

.ports {
    font-size: 0.9em;
    color: #b0b0b0;
}

.prev-ports {
    color: #FF6B6B;
}

.next-ports {
    color: #51CF66;
}

/* Responsive Design */
@media (max-width: 1200px) {
    .charts-row {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    header {
        padding: 20px;
    }

    h1 {
        font-size: 1.6em;
    }

    .controls {
        flex-direction: column;
    }

    select, .search-box {
        width: 100%;
    }

    .header-nav {
        flex-direction: column;
    }

    .nav-link {
        width: 100%;
        text-align: center;
    }

    .stats-row {
        grid-template-columns: 1fr;
    }

    .calendar-table {
        font-size: 0.8em;
    }

    .calendar-table td {
        padding: 5px;
        height: auto;
        min-height: 50px;
    }
}

/* Print Styles */
@media print {
    .controls, header nav {
        display: none;
    }

    .month-section {
        page-break-after: always;
    }
}
"""

    with open('assets/styles.css', 'w', encoding='utf-8') as f:
        f.write(css_content)

    print("[OK] Created assets/styles.css")

    # ====== CREATE ASSETS/APP.JS ======
    js_content = """// Roatan Tourism Tracker - Main Application

function initializeApp() {
    const selected = document.getElementById('monthSelect').value || monthsList[0];
    changeMonth(selected);
}

function changeMonth(monthKey = null) {
    const monthKey_ = monthKey || document.getElementById('monthSelect').value;

    // Hide all sections
    document.querySelectorAll('.month-section').forEach(s => s.classList.remove('active'));

    // Show selected section or create it
    let section = document.getElementById(`month-${monthKey_}`);
    if (!section) {
        section = createMonthSection(monthKey_);
        document.getElementById('chartsContainer').appendChild(section);
    }

    section.classList.add('active');
    renderCharts(monthKey_);
}

function processMonthlyData(monthData) {
    const days = monthData.days || {};
    let stats = {
        flights_in: 0,
        flights_out: 0,
        cruises_in: 0,
        cruises_out: 0,
        flight_passengers: 0,
        cruise_passengers: 0,
        daily: {}
    };

    for (const [dayStr, dayData] of Object.entries(days)) {
        let day_flights_in = 0, day_flights_out = 0, day_cruises_in = 0, day_cruises_out = 0;
        let day_flight_pax = 0, day_cruise_pax = 0;

        // Process flights
        for (const flight of (dayData.flights || [])) {
            const pax = flight.estimated_passengers || 0;
            if (flight.is_arrival) {
                stats.flights_in += 1;
                day_flights_in += 1;
                stats.flight_passengers += pax;
                day_flight_pax += pax;
            } else {
                stats.flights_out += 1;
                day_flights_out += 1;
                stats.flight_passengers += pax;
                day_flight_pax += pax;
            }
        }

        // Process cruises
        for (const cruise of (dayData.cruises || [])) {
            const pax = cruise.estimated_passengers || 0;
            if (cruise.is_arrival) {
                stats.cruises_in += 1;
                day_cruises_in += 1;
            } else {
                stats.cruises_out += 1;
                day_cruises_out += 1;
            }
            stats.cruise_passengers += pax;
            day_cruise_pax += pax;
        }

        stats.daily[dayStr] = {
            flights_in: day_flights_in,
            flights_out: day_flights_out,
            cruises_in: day_cruises_in,
            cruises_out: day_cruises_out,
            flight_pax: day_flight_pax,
            cruise_pax: day_cruise_pax
        };
    }

    return stats;
}

function createMonthSection(monthKey) {
    const monthData = allMonthlyData[monthKey];
    const [year, month] = monthKey.split('-');
    const monthObj = new Date(year, month - 1);
    const monthName = monthObj.toLocaleString('default', { month: 'long', year: 'numeric' });

    const stats = processMonthlyData(monthData);
    const days = monthData.days || {};
    const daysList = Object.keys(days).sort();

    // Chart data
    let flightData = [], cruiseData = [], netData = [];
    let dayLabels = [];

    for (const dayStr of daysList) {
        const day = parseInt(dayStr.split('-')[2]);
        dayLabels.push(`${monthObj.toLocaleString('default', {month: 'short'})} ${day}`);

        const dayStats = stats.daily[dayStr] || {};
        flightData.push(dayStats.flights_in + dayStats.flights_out);
        cruiseData.push(dayStats.cruises_in + dayStats.cruises_out);
        netData.push((dayStats.flights_in - dayStats.flights_out) + (dayStats.cruises_in - dayStats.cruises_out));
    }

    const section = document.createElement('div');
    section.id = `month-${monthKey}`;
    section.className = 'month-section';
    section.innerHTML = `
        <div class="month-header">${monthName}</div>

        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-label">Total Flight Movements</div>
                <div class="stat-value">${stats.flights_in + stats.flights_out}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Cruise Movements</div>
                <div class="stat-value">${stats.cruises_in + stats.cruises_out}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Flight Passengers</div>
                <div class="stat-value">${stats.flight_passengers.toLocaleString()}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Cruise Passengers</div>
                <div class="stat-value">${stats.cruise_passengers.toLocaleString()}</div>
            </div>
        </div>

        <div class="charts-row">
            <div class="chart-container">
                <div class="chart-title">Daily Flight Traffic</div>
                <div id="flights-chart-${monthKey}" class="plotly-graph"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Daily Cruise Traffic</div>
                <div id="cruises-chart-${monthKey}" class="plotly-graph"></div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Combined Tourism Traffic</div>
            <div id="combined-chart-${monthKey}" class="plotly-graph"></div>
        </div>

        <div class="calendar-container">
            <div class="chart-title">Calendar View</div>
            <table class="calendar-table">
                <thead>
                    <tr>
                        <th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th>
                    </tr>
                </thead>
                <tbody id="calendar-${monthKey}">
                </tbody>
            </table>
        </div>
    `;

    // Generate calendar
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    let dayCounter = 1;
    let calendarHTML = '';

    for (let week = 0; week < 6; week++) {
        calendarHTML += '<tr>';
        for (let day = 0; day < 7; day++) {
            if (week === 0 && day < firstDay) {
                calendarHTML += '<td></td>';
            } else if (dayCounter > daysInMonth) {
                calendarHTML += '<td></td>';
            } else {
                const dayStr = `${year}-${month.toString().padStart(2, '0')}-${dayCounter.toString().padStart(2, '0')}`;
                const dayData = stats.daily[dayStr] || {};
                const isWeekend = day === 0 || day === 6 ? ' calendar-weekend' : '';

                calendarHTML += `<td class="${isWeekend}">
                    <span class="calendar-date">${dayCounter}</span>
                    <span class="calendar-flights">Flights: ${dayData.flights_in + dayData.flights_out}</span>
                    <span class="calendar-cruises">Cruises: ${dayData.cruises_in + dayData.cruises_out}</span>
                </td>`;
                dayCounter++;
            }
        }
        calendarHTML += '</tr>';
    }

    document.getElementById(`calendar-${monthKey}`).innerHTML = calendarHTML;

    return section;
}

function renderCharts(monthKey) {
    const monthData = allMonthlyData[monthKey];
    const stats = processMonthlyData(monthData);
    const days = monthData.days || {};
    const daysList = Object.keys(days).sort();
    const [year, month] = monthKey.split('-');
    const monthObj = new Date(year, month - 1);

    let flightData = [], cruiseData = [], netData = [];
    let dayLabels = [];

    for (const dayStr of daysList) {
        const day = parseInt(dayStr.split('-')[2]);
        dayLabels.push(`${monthObj.toLocaleString('default', {month: 'short'})} ${day}`);

        const dayStats = stats.daily[dayStr] || {};
        flightData.push(dayStats.flights_in + dayStats.flights_out);
        cruiseData.push(dayStats.cruises_in + dayStats.cruises_out);
        netData.push((dayStats.flights_in - dayStats.flights_out) + (dayStats.cruises_in - dayStats.cruises_out));
    }

    const darkTemplate = {
        layout: {
            template: 'plotly_dark',
            paper_bgcolor: '#16213e',
            plot_bgcolor: '#0f3460',
            font: { color: '#e0e0e0' },
            margin: { b: 100, t: 20, l: 60, r: 40 }
        },
        config: { responsive: true }
    };

    // Flight traffic chart
    Plotly.newPlot(`flights-chart-${monthKey}`, [{
        x: dayLabels,
        y: flightData,
        type: 'bar',
        marker: { color: '#2E86AB' }
    }], {
        ...darkTemplate.layout,
        xaxis: { title: 'Date', tickangle: 45 },
        yaxis: { title: 'Number of Flights' }
    }, darkTemplate.config);

    // Cruise traffic chart
    Plotly.newPlot(`cruises-chart-${monthKey}`, [{
        x: dayLabels,
        y: cruiseData,
        type: 'bar',
        marker: { color: '#A23B72' }
    }], {
        ...darkTemplate.layout,
        xaxis: { title: 'Date', tickangle: 45 },
        yaxis: { title: 'Number of Cruises' }
    }, darkTemplate.config);

    // Combined chart
    Plotly.newPlot(`combined-chart-${monthKey}`, [
        {
            x: dayLabels,
            y: flightData,
            type: 'bar',
            name: 'Flights',
            marker: { color: '#2E86AB' }
        },
        {
            x: dayLabels,
            y: cruiseData,
            type: 'bar',
            name: 'Cruises',
            marker: { color: '#A23B72' }
        },
        {
            x: dayLabels,
            y: netData,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Net Flow',
            line: { color: '#2ECC40', width: 3 },
            marker: { size: 6 }
        }
    ], {
        ...darkTemplate.layout,
        xaxis: { title: 'Date', tickangle: 45 },
        yaxis: { title: 'Number of Movements' },
        barmode: 'group'
    }, darkTemplate.config);
}
"""

    with open('assets/app.js', 'w', encoding='utf-8') as f:
        f.write(js_content)

    print("[OK] Created assets/app.js")

    # ====== CREATE PAGES/SCHEDULE.HTML ======
    with open('pages/schedule.html', 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cruise Schedule - Roatan Tourism Tracker</title>
    <link rel="stylesheet" href="../assets/styles.css">
</head>
<body>
    <header>
        <h1>Cruise Schedule</h1>
        <p>Complete Itinerary Data 2026-2028</p>
        <nav class="header-nav">
            <a href="../index.html" class="nav-link">Analytics</a>
            <a href="schedule.html" class="nav-link active">Cruise Schedule</a>
            <a href="dashboard.html" class="nav-link">Dashboard</a>
        </nav>
    </header>

    <div class="controls">
        <input type="text" class="search-box" id="shipSearch" placeholder="Search ship name..." onkeyup="filterSchedule()">
        <select id="scheduleMonth" onchange="filterSchedule()">
            <option value="">All Months</option>
""" + "\n".join([f'            <option value="{mk}">{datetime(int(mk.split("-")[0]), int(mk.split("-")[1]), 1).strftime("%B %Y")}</option>' for mk in months_list]) + f"""
        </select>
    </div>

    <div class="container">
        <div class="chart-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Ship Name</th>
                        <th>Previous Ports</th>
                        <th>Next Ports</th>
                        <th style="text-align: right;">Passengers</th>
                    </tr>
                </thead>
                <tbody id="scheduleTable">
                </tbody>
            </table>
        </div>
    </div>

    <footer>
        <p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>

    <script>
        const allCruises = {json.dumps(all_cruises)};

        function formatPorts(ports) {{
            if (!ports || ports.length === 0) return '(none)';
            return ports.slice(0, 2).join(' → ') + (ports.length > 2 ? ` ... +${{ports.length - 2}} more` : '');
        }}

        function filterSchedule() {{
            const search = document.getElementById('shipSearch').value.toLowerCase();
            const month = document.getElementById('scheduleMonth').value;

            const filtered = allCruises.filter(c => {{
                const matchesSearch = !search || c.ship_name.toLowerCase().includes(search);
                const matchesMonth = !month || c.date.startsWith(month);
                return matchesSearch && matchesMonth;
            }});

            const tbody = document.getElementById('scheduleTable');
            tbody.innerHTML = filtered.slice(0, 500).map(c => `
                <tr>
                    <td style="white-space: nowrap;">${{new Date(c.date).toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }})}}</td>
                    <td class="ship-name">${{c.ship_name}}</td>
                    <td class="ports prev-ports">${{formatPorts(c.previous_ports)}}</td>
                    <td class="ports next-ports">${{formatPorts(c.next_ports)}}</td>
                    <td style="text-align: right;">${{(c.estimated_passengers || 0).toLocaleString()}}</td>
                </tr>
            `).join('');
        }}

        // Initial load
        filterSchedule();
    </script>
</body>
</html>
""")

    print("[OK] Created pages/schedule.html")

    # ====== CREATE PAGES/DASHBOARD.HTML ======
    # Calculate dashboard stats
    total_cruises = len(all_cruises)
    total_passengers = sum(c.get('estimated_passengers', 0) for c in all_cruises)
    unique_ships = len(set(c.get('ship_name', '') for c in all_cruises))

    with open('pages/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Roatan Tourism Tracker</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="../assets/styles.css">
</head>
<body>
    <header>
        <h1>Analytics Dashboard</h1>
        <p>Tourism Summary 2026-2028</p>
        <nav class="header-nav">
            <a href="../index.html" class="nav-link">Analytics</a>
            <a href="schedule.html" class="nav-link">Cruise Schedule</a>
            <a href="dashboard.html" class="nav-link active">Dashboard</a>
        </nav>
    </header>

    <div class="container">
        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-label">Total Cruises</div>
                <div class="stat-value">{total_cruises:,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Passengers</div>
                <div class="stat-value">{total_passengers:,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Unique Ships</div>
                <div class="stat-value">{unique_ships}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Months Covered</div>
                <div class="stat-value">{len(months_list)}</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Monthly Cruise Volume</div>
            <div id="monthly-cruises" class="plotly-graph"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Monthly Passenger Volume</div>
            <div id="monthly-passengers" class="plotly-graph"></div>
        </div>
    </div>

    <footer>
        <p>Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>

    <script>
        const allMonthlyData = {json.dumps(all_monthly_data)};
        const monthsList = {json.dumps(months_list)};

        function renderDashboard() {{
            const months = Object.keys(allMonthlyData).sort();
            const monthLabels = months.map(m => {{
                const [y, mo] = m.split('-');
                return new Date(y, mo - 1).toLocaleString('default', {{ month: 'short', year: '2-digit' }});
            }});

            // Calculate data
            const cruisesData = [];
            const passengersData = [];

            for (const monthKey of months) {{
                const days = allMonthlyData[monthKey].days || {{}};
                let cruises = 0, passengers = 0;

                for (const dayData of Object.values(days)) {{
                    cruises += (dayData.cruises || []).length;
                    passengers += (dayData.cruises || []).reduce((sum, c) => sum + (c.estimated_passengers || 0), 0);
                }}

                cruisesData.push(cruises);
                passengersData.push(passengers);
            }}

            const darkLayout = {{
                template: 'plotly_dark',
                paper_bgcolor: '#16213e',
                plot_bgcolor: '#0f3460',
                font: {{ color: '#e0e0e0' }},
                margin: {{ b: 80, t: 20, l: 60, r: 40 }}
            }};

            // Cruises chart
            Plotly.newPlot('monthly-cruises', [{{
                x: monthLabels,
                y: cruisesData,
                type: 'bar',
                marker: {{ color: '#667eea' }}
            }}], {{
                ...darkLayout,
                xaxis: {{ title: 'Month', tickangle: 45 }},
                yaxis: {{ title: 'Number of Cruises' }}
            }}, {{ responsive: true }});

            // Passengers chart
            Plotly.newPlot('monthly-passengers', [{{
                x: monthLabels,
                y: passengersData,
                type: 'bar',
                marker: {{ color: '#764ba2' }}
            }}], {{
                ...darkLayout,
                xaxis: {{ title: 'Month', tickangle: 45 }},
                yaxis: {{ title: 'Total Passengers' }}
            }}, {{ responsive: true }});
        }}

        renderDashboard();
    </script>
</body>
</html>
""")

    print("[OK] Created pages/dashboard.html")

    # ====== CREATE README.MD ======
    readme = """# Roatan Tourism Tracker

## Overview
Complete tourism analytics dashboard for Roatan, Honduras. Tracks flight and cruise ship arrivals/departures with comprehensive analytics and scheduling information.

## Features

### Main Dashboard (index.html)
- Monthly flight and cruise traffic analysis
- Daily movement statistics
- Combined tourism flow charts
- Calendar view with daily breakdown
- Month-by-month navigation

### Cruise Schedule (pages/schedule.html)
- Searchable cruise schedule database
- Ship itinerary information
- Previous and next port sequences
- Passenger capacity data
- Month filtering

### Analytics Dashboard (pages/dashboard.html)
- Summary statistics
- Monthly trends
- Historical data visualization
- Tourism volume analysis

## File Structure

```
roatan-tourism-tracker/
├── index.html                 # Main analytics dashboard
├── pages/
│   ├── schedule.html         # Cruise schedule
│   └── dashboard.html        # Summary analytics
├── assets/
│   ├── styles.css            # Shared styles
│   └── app.js                # JavaScript functions
└── README.md                 # This file
```

## Data Coverage

- **Date Range**: June 2026 - November 2028
- **Total Cruises**: 1,040+
- **Unique Ships**: 71+
- **Months Covered**: 30

## Technology

- **Charts**: Plotly.js (interactive visualization)
- **Styling**: CSS3 with dark theme
- **Data**: Embedded JSON in HTML files
- **Compatibility**: All modern browsers

## Deployment

1. Upload all files to your web server
2. Ensure `index.html` is in the root directory
3. Keep `pages/` and `assets/` folders intact
4. No backend server required - fully static site

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Responsive design

## Features by Page

### index.html
✓ Interactive monthly charts
✓ Flight traffic analysis
✓ Cruise traffic analysis
✓ Combined tourism metrics
✓ Calendar view
✓ Dark theme interface

### pages/schedule.html
✓ Search by ship name
✓ Filter by month
✓ Full itinerary data
✓ Port sequences
✓ Passenger information

### pages/dashboard.html
✓ Key statistics
✓ Monthly trends
✓ Tourism volume
✓ Historical analysis

## Navigation

Use the header navigation to switch between pages:
- **Analytics** - Main dashboard with charts
- **Cruise Schedule** - Searchable itinerary database
- **Dashboard** - Summary statistics

## Support

For issues or updates, contact the tourism board.

---

Generated """ + datetime.now().strftime('%Y-%m-%d') + """
"""

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme)

    print("[OK] Created README.md")

    # ====== CREATE .HTACCESS ======
    htaccess = """# Roatan Tourism Tracker - Apache Configuration

# Enable GZIP compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>

# Set proper MIME types
<IfModule mod_mime.c>
    AddType application/json .json
    AddType text/css .css
    AddType application/javascript .js
    AddType text/html .html
</IfModule>

# Enable browser caching
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresDefault "access plus 1 month"
    ExpiresByType text/html "access plus 1 hour"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType application/json "access plus 1 month"
</IfModule>

# Rewrite rules for clean URLs
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /

    # If the request is not for a valid file
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d

    # Rewrite to index.html
    RewriteRule ^ index.html [QSA,L]
</IfModule>

# Security headers
<IfModule mod_headers.c>
    Header set X-Content-Type-Options "nosniff"
    Header set X-Frame-Options "SAMEORIGIN"
    Header set X-XSS-Protection "1; mode=block"
</IfModule>
"""

    with open('.htaccess', 'w', encoding='utf-8') as f:
        f.write(htaccess)

    print("[OK] Created .htaccess")

    # Print summary
    print("\n" + "="*80)
    print("WEB PACKAGE READY FOR UPLOAD")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  - index.html (5.8 MB) - Main dashboard")
    print(f"  - pages/schedule.html - Cruise schedule")
    print(f"  - pages/dashboard.html - Analytics summary")
    print(f"  - assets/styles.css - Shared styles")
    print(f"  - assets/app.js - JavaScript functions")
    print(f"  - README.md - Documentation")
    print(f"  - .htaccess - Server configuration")
    print(f"\nDirectory structure:")
    print(f"  roatan-tourism-tracker/")
    print(f"  ├── index.html")
    print(f"  ├── pages/")
    print(f"  │   ├── schedule.html")
    print(f"  │   └── dashboard.html")
    print(f"  ├── assets/")
    print(f"  │   ├── styles.css")
    print(f"  │   └── app.js")
    print(f"  ├── README.md")
    print(f"  └── .htaccess")
    print(f"\nTo deploy:")
    print(f"  1. Zip all files in this directory")
    print(f"  2. Upload to web server")
    print(f"  3. Extract files maintaining directory structure")
    print(f"  4. No backend server required - fully static site")
    print("="*80)

if __name__ == '__main__':
    create_web_package()
