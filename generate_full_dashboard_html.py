"""
Generate a complete static HTML dashboard of the entire Flask app.
Includes all charts, statistics, and cruise schedules.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics

def generate_full_dashboard():
    """Generate complete HTML dashboard."""

    # Load all cruise data
    all_cruises = []
    monthly_stats = {}

    for json_file in sorted(Path('.').glob('tourism_*.json')):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Extract year/month
            filename = json_file.stem  # tourism_2026_06
            parts = filename.split('_')
            year = int(parts[1])
            month = int(parts[2])
            month_key = f"{year}-{month:02d}"

            days = data.get('days', {})

            # Aggregate monthly stats
            month_passengers = 0
            month_cruises = 0

            for day_str in sorted(days.keys()):
                day_data = days[day_str]

                for cruise in day_data.get('cruises', []):
                    cruise['date'] = day_str
                    all_cruises.append(cruise)
                    month_passengers += cruise.get('estimated_passengers', 0)
                    month_cruises += 1

            if month_cruises > 0:
                monthly_stats[month_key] = {
                    'year': year,
                    'month': month,
                    'cruises': month_cruises,
                    'passengers': month_passengers,
                    'avg_passengers': month_passengers / month_cruises
                }

        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    # Aggregate statistics
    total_cruises = len(all_cruises)
    total_passengers = sum(c.get('estimated_passengers', 0) for c in all_cruises)
    unique_ships = len(set(c.get('ship_name', '') for c in all_cruises))
    months_covered = len(monthly_stats)

    # Get unique months for dropdown
    months = sorted(monthly_stats.keys())
    month_names = []
    for month_key in months:
        year, month = month_key.split('-')
        month_obj = datetime(int(year), int(month), 1)
        month_names.append((month_key, month_obj.strftime('%B %Y')))

    # Prepare chart data
    months_data = [m['month'] for m in monthly_stats.values()]
    passengers_data = [m['passengers'] for m in monthly_stats.values()]
    cruises_data = [m['cruises'] for m in monthly_stats.values()]

    # Ship statistics
    ship_stats = defaultdict(lambda: {'count': 0, 'passengers': 0})
    for cruise in all_cruises:
        ship = cruise.get('ship_name', '')
        ship_stats[ship]['count'] += 1
        ship_stats[ship]['passengers'] += cruise.get('estimated_passengers', 0)

    # Top 10 ships
    top_ships = sorted(ship_stats.items(), key=lambda x: x[1]['passengers'], reverse=True)[:10]

    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker - Complete Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        nav {
            background: white;
            padding: 15px 40px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        nav button {
            padding: 10px 20px;
            border: none;
            background: #f0f0f0;
            color: #333;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }

        nav button.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        nav button:hover {
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        section {
            display: none;
            animation: fadeIn 0.3s;
        }

        section.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .stat-label {
            color: #666;
            font-size: 1em;
        }

        .chart-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .chart-title {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }

        .chart-container {
            width: 100%;
            min-height: 400px;
        }

        .month-controls {
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }

        select {
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }

        .cruise-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        .cruise-table thead {
            background: #f8f9fa;
        }

        .cruise-table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }

        .cruise-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }

        .cruise-table tr:hover {
            background: #f8f9fa;
        }

        .ship-name {
            font-weight: 600;
            color: #667eea;
        }

        .ports {
            font-size: 0.9em;
            color: #555;
        }

        .prev-ports {
            color: #e74c3c;
        }

        .next-ports {
            color: #27ae60;
        }

        footer {
            background: white;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
            margin-top: 40px;
        }

        .search-box {
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
            width: 300px;
        }

        .top-ships-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .ship-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .ship-card h3 {
            color: #667eea;
            margin-bottom: 15px;
        }

        .ship-card-stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .ship-card-label {
            color: #666;
        }

        .ship-card-value {
            font-weight: 600;
            color: #333;
        }

        @media (max-width: 768px) {
            header h1 {
                font-size: 1.8em;
            }

            nav {
                flex-direction: column;
            }

            nav button {
                width: 100%;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .search-box {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>Roatan Tourism Tracker</h1>
        <p class="subtitle">Complete Dashboard 2026-2028</p>
    </header>

    <nav>
        <button class="tab-btn active" onclick="showTab('overview')">Overview</button>
        <button class="tab-btn" onclick="showTab('trends')">Trends & Analysis</button>
        <button class="tab-btn" onclick="showTab('ships')">Ships</button>
        <button class="tab-btn" onclick="showTab('schedule')">Cruise Schedule</button>
    </nav>

    <div class="container">
        <!-- OVERVIEW TAB -->
        <section id="overview" class="active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">""" + f"{total_cruises:,}" + """</div>
                    <div class="stat-label">Total Cruises</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + f"{total_passengers:,}" + """</div>
                    <div class="stat-label">Total Passengers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + f"{unique_ships}" + """</div>
                    <div class="stat-label">Unique Ships</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + f"{months_covered}" + """</div>
                    <div class="stat-label">Months Covered</div>
                </div>
            </div>

            <div class="chart-section">
                <div class="chart-title">Monthly Cruise Volume</div>
                <div id="cruises-chart" class="chart-container"></div>
            </div>

            <div class="chart-section">
                <div class="chart-title">Monthly Passenger Volume</div>
                <div id="passengers-chart" class="chart-container"></div>
            </div>
        </section>

        <!-- TRENDS TAB -->
        <section id="trends">
            <div class="month-controls">
                <label>View Month:</label>
                <select id="monthSelect" onchange="updateMonthView()">
                    <option value="">All Months</option>
""" + "\n".join([f'                    <option value="{mk}">{mn}</option>' for mk, mn in month_names]) + """
                </select>
            </div>

            <div class="chart-section">
                <div class="chart-title">Cumulative Cruise Trends</div>
                <div id="cumulative-chart" class="chart-container"></div>
            </div>

            <div class="chart-section">
                <div class="chart-title">Average Passengers Per Cruise by Month</div>
                <div id="avg-passengers-chart" class="chart-container"></div>
            </div>
        </section>

        <!-- SHIPS TAB -->
        <section id="ships">
            <h2 style="margin-bottom: 20px;">Top 10 Ships by Total Passengers</h2>
            <div class="top-ships-list">
""" + "\n".join([f"""
                <div class="ship-card">
                    <h3>{ship}</h3>
                    <div class="ship-card-stat">
                        <span class="ship-card-label">Total Cruises:</span>
                        <span class="ship-card-value">{stats['count']}</span>
                    </div>
                    <div class="ship-card-stat">
                        <span class="ship-card-label">Total Passengers:</span>
                        <span class="ship-card-value">{stats['passengers']:,}</span>
                    </div>
                    <div class="ship-card-stat">
                        <span class="ship-card-label">Avg Per Cruise:</span>
                        <span class="ship-card-value">{stats['passengers']//stats['count']:,}</span>
                    </div>
                </div>
""" for ship, stats in top_ships]) + """
            </div>
        </section>

        <!-- SCHEDULE TAB -->
        <section id="schedule">
            <div class="month-controls">
                <input type="text" class="search-box" id="shipSearch" placeholder="Search ship name..." onkeyup="filterSchedule()">
                <select id="scheduleMonth" onchange="filterSchedule()">
                    <option value="">All Months</option>
""" + "\n".join([f'                    <option value="{mk}">{mn}</option>' for mk, mn in month_names]) + """
                </select>
            </div>

            <div class="chart-section">
                <table class="cruise-table">
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
        </section>
    </div>

    <footer>
        <p>Generated """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """ | Data covers """ + all_cruises[0]['date'] + """ to """ + all_cruises[-1]['date'] + """</p>
    </footer>

    <script>
        const allCruises = """ + json.dumps(all_cruises) + """;
        const monthlyData = """ + json.dumps({k: v for k, v in monthly_stats.items()}) + """;

        function showTab(tabName) {
            // Hide all sections
            document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
            // Show selected section
            document.getElementById(tabName).classList.add('active');
            // Update button states
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            // Trigger chart rendering
            if (tabName === 'overview') {
                renderOverviewCharts();
            } else if (tabName === 'trends') {
                renderTrendCharts();
            } else if (tabName === 'schedule') {
                populateSchedule();
            }
        }

        function renderOverviewCharts() {
            const months = Object.keys(monthlyData).sort();
            const cruisesData = months.map(m => monthlyData[m].cruises);
            const passengersData = months.map(m => monthlyData[m].passengers);
            const monthLabels = months.map(m => {
                const [y, mo] = m.split('-');
                return new Date(y, mo - 1).toLocaleString('default', { month: 'short', year: '2-digit' });
            });

            // Cruises chart
            Plotly.newPlot('cruises-chart', [{
                x: monthLabels,
                y: cruisesData,
                type: 'bar',
                marker: { color: '#667eea' }
            }], {
                title: '',
                xaxis: { title: 'Month' },
                yaxis: { title: 'Number of Cruises' },
                template: 'plotly_white',
                responsive: true,
                margin: { b: 80 }
            }, { responsive: true });

            // Passengers chart
            Plotly.newPlot('passengers-chart', [{
                x: monthLabels,
                y: passengersData,
                type: 'bar',
                marker: { color: '#764ba2' }
            }], {
                title: '',
                xaxis: { title: 'Month' },
                yaxis: { title: 'Total Passengers' },
                template: 'plotly_white',
                responsive: true,
                margin: { b: 80 }
            }, { responsive: true });
        }

        function renderTrendCharts() {
            const months = Object.keys(monthlyData).sort();
            const monthLabels = months.map(m => {
                const [y, mo] = m.split('-');
                return new Date(y, mo - 1).toLocaleString('default', { month: 'short', year: '2-digit' });
            });

            // Cumulative cruises
            let cumulative = 0;
            const cumulativeCruises = months.map(m => {
                cumulative += monthlyData[m].cruises;
                return cumulative;
            });

            Plotly.newPlot('cumulative-chart', [{
                x: monthLabels,
                y: cumulativeCruises,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#667eea', width: 3 },
                marker: { size: 8 }
            }], {
                title: '',
                xaxis: { title: 'Month' },
                yaxis: { title: 'Cumulative Cruises' },
                template: 'plotly_white',
                responsive: true,
                margin: { b: 80 }
            }, { responsive: true });

            // Average passengers
            const avgPassengers = months.map(m =>
                Math.round(monthlyData[m].passengers / monthlyData[m].cruises)
            );

            Plotly.newPlot('avg-passengers-chart', [{
                x: monthLabels,
                y: avgPassengers,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#764ba2', width: 3 },
                marker: { size: 8 }
            }], {
                title: '',
                xaxis: { title: 'Month' },
                yaxis: { title: 'Average Passengers' },
                template: 'plotly_white',
                responsive: true,
                margin: { b: 80 }
            }, { responsive: true });
        }

        function formatPorts(ports) {
            if (!ports || ports.length === 0) return '(none)';
            return ports.slice(0, 2).join(' → ') + (ports.length > 2 ? ` ... +${ports.length - 2} more` : '');
        }

        function populateSchedule() {
            filterSchedule();
        }

        function filterSchedule() {
            const search = document.getElementById('shipSearch').value.toLowerCase();
            const month = document.getElementById('scheduleMonth').value;

            const filtered = allCruises.filter(c => {
                const matchesSearch = !search || c.ship_name.toLowerCase().includes(search);
                const matchesMonth = !month || c.date.startsWith(month);
                return matchesSearch && matchesMonth;
            });

            const tbody = document.getElementById('scheduleTable');
            tbody.innerHTML = filtered.slice(0, 200).map(c => `
                <tr>
                    <td style="white-space: nowrap;">${new Date(c.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</td>
                    <td class="ship-name">${c.ship_name}</td>
                    <td class="ports prev-ports">${formatPorts(c.previous_ports)}</td>
                    <td class="ports next-ports">${formatPorts(c.next_ports)}</td>
                    <td style="text-align: right;">${(c.estimated_passengers || 0).toLocaleString()}</td>
                </tr>
            `).join('');
        }

        // Initial render
        renderOverviewCharts();
    </script>
</body>
</html>
"""

    # Write HTML file
    output_file = 'roatan_tourism_dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Generated {output_file}")
    print(f"  Total cruises: {total_cruises:,}")
    print(f"  Total passengers: {total_passengers:,}")
    print(f"  Unique ships: {unique_ships}")
    print(f"  Months covered: {months_covered}")
    print(f"  File size: {len(html) / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    generate_full_dashboard()
