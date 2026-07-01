"""
Generate a standalone index.html with all code embedded.
No external dependencies except Plotly.js
"""

import json
from pathlib import Path
from datetime import datetime

def generate_standalone():
    """Generate fully self-contained index.html"""

    # Load all data
    all_monthly_data = {}

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
        except Exception as e:
            print(f"Error: {e}")

    months_list = sorted(all_monthly_data.keys())

    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
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
        }

        select {
            padding: 10px 15px;
            background: #0f3460;
            color: white;
            border: 1px solid #e94560;
            border-radius: 5px;
            font-size: 1em;
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
        }

        .month-header {
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            color: white;
            padding: 20px 40px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: bold;
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
        }

        .stat-label {
            color: #b0b0b0;
            font-size: 0.9em;
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
            height: 400px;
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
            overflow-x: auto;
        }

        .calendar-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        .calendar-table th {
            padding: 10px;
            text-align: center;
            color: #e94560;
            font-weight: bold;
            border: 1px solid #0f3460;
            background: #0f3460;
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
        }

        @media (max-width: 768px) {
            .controls { flex-direction: column; }
            select { width: 100%; }
            .charts-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <header>
        <h1>Roatan Tourism Tracker</h1>
        <p>Flight & Cruise Analytics Dashboard 2026-2028</p>
    </header>

    <div class="controls">
        <label for="monthSelect">Select Month:</label>
        <select id="monthSelect" onchange="changeMonth()">
"""

    # Add options
    for month_key in months_list:
        year, month = month_key.split('-')
        month_obj = datetime(int(year), int(month), 1)
        month_name = month_obj.strftime('%B %Y')
        html += f'            <option value="{month_key}">{month_name}</option>\n'

    html += """        </select>
    </div>

    <div class="container" id="chartsContainer">
        <!-- Charts will be rendered here -->
    </div>

    <footer>
        <p>Generated """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """ | Data: June 2026 - November 2028</p>
    </footer>

    <script>
        // Embedded data
        const allMonthlyData = """ + json.dumps(all_monthly_data) + """;
        const monthsList = """ + json.dumps(months_list) + """;
        const monthConfigs = {};

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

            let flightData = [], cruiseData = [], netData = [];
            let dayLabels = [];

            for (const dayStr of daysList) {
                const day = parseInt(dayStr.split('-')[2]);
                dayLabels.push(monthObj.toLocaleString('default', {month: 'short'}) + ' ' + day);

                const dayStats = stats.daily[dayStr] || {};
                flightData.push(dayStats.flights_in + dayStats.flights_out);
                cruiseData.push(dayStats.cruises_in + dayStats.cruises_out);
                netData.push((dayStats.flights_in - dayStats.flights_out) + (dayStats.cruises_in - dayStats.cruises_out));
            }

            let html = `
                <div class="month-section" id="month-${monthKey}">
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
                            <span class="calendar-flights">✈ ${dayData.flights_in + dayData.flights_out}</span>
                            <span class="calendar-cruises">🚢 ${dayData.cruises_in + dayData.cruises_out}</span>
                        </td>`;
                        dayCounter++;
                    }
                }
                calendarHTML += '</tr>';
            }

            return { html, stats, dayLabels, flightData, cruiseData, netData, monthKey };
        }

        // Build all sections and render first month
        function initApp() {
            const container = document.getElementById('chartsContainer');

            for (const monthKey of monthsList) {
                const config = createMonthSection(monthKey);
                monthConfigs[monthKey] = config;

                const div = document.createElement('div');
                div.innerHTML = config.html;
                container.appendChild(div.firstElementChild);

                // Set calendar
                const calendarBody = document.getElementById(`calendar-${monthKey}`);
                const tbody = document.createElement('tbody');
                tbody.innerHTML = config.html.match(/id="calendar-[^"]*"[^>]*>([\\s\\S]*?)<\\/tbody>/)[1];

                // Generate calendar properly
                const firstDay = new Date(monthKey.split('-')[0], monthKey.split('-')[1] - 1, 1).getDay();
                const daysInMonth = new Date(monthKey.split('-')[0], monthKey.split('-')[1], 0).getDate();
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
                            const dayStr = `${monthKey}-${dayCounter.toString().padStart(2, '0')}`;
                            const dayData = config.stats.daily[dayStr] || {};
                            const isWeekend = day === 0 || day === 6 ? ' calendar-weekend' : '';

                            calendarRows += `<td class="${isWeekend}">
                                <span class="calendar-date">${dayCounter}</span>
                                <span class="calendar-flights">Flights: ${dayData.flights_in + dayData.flights_out}</span>
                                <span class="calendar-cruises">Cruises: ${dayData.cruises_in + dayData.cruises_out}</span>
                            </td>`;
                            dayCounter++;
                        }
                    }
                    calendarRows += '</tr>';
                }
                calendarBody.innerHTML = calendarRows;
            }

            // Show first month
            changeMonth(monthsList[0]);
        }

        function changeMonth(monthKey = null) {
            const key = monthKey || document.getElementById('monthSelect').value;
            const config = monthConfigs[key];

            // Hide all
            document.querySelectorAll('.month-section').forEach(s => s.classList.remove('active'));
            // Show selected
            document.getElementById(`month-${key}`).classList.add('active');

            // Render charts
            renderCharts(key, config);
        }

        function renderCharts(monthKey, config) {
            const { dayLabels, flightData, cruiseData, netData } = config;

            const darkLayout = {
                template: 'plotly_dark',
                paper_bgcolor: '#16213e',
                plot_bgcolor: '#0f3460',
                font: { color: '#e0e0e0' },
                margin: { b: 100, t: 20, l: 60, r: 40 }
            };

            // Flight chart
            Plotly.newPlot(`flights-chart-${monthKey}`, [{
                x: dayLabels,
                y: flightData,
                type: 'bar',
                marker: { color: '#2E86AB' }
            }], {
                ...darkLayout,
                xaxis: { title: 'Date', tickangle: 45 },
                yaxis: { title: 'Number of Flights' }
            }, { responsive: true });

            // Cruise chart
            Plotly.newPlot(`cruises-chart-${monthKey}`, [{
                x: dayLabels,
                y: cruiseData,
                type: 'bar',
                marker: { color: '#A23B72' }
            }], {
                ...darkLayout,
                xaxis: { title: 'Date', tickangle: 45 },
                yaxis: { title: 'Number of Cruises' }
            }, { responsive: true });

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
                ...darkLayout,
                xaxis: { title: 'Date', tickangle: 45 },
                yaxis: { title: 'Movements' },
                barmode: 'group'
            }, { responsive: true });
        }

        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
"""

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Generated standalone index.html ({len(html)/1024/1024:.2f} MB)")
    print(f"[OK] {len(months_list)} months of data embedded")
    print("[OK] All JavaScript embedded - no external dependencies except Plotly.js")

if __name__ == '__main__':
    generate_standalone()
