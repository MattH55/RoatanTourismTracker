"""
Generate a static HTML file with all cruise schedule data.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def generate_html():
    """Generate static HTML cruise schedule."""

    # Collect all cruise data
    all_cruises = []

    for json_file in sorted(Path('.').glob('tourism_*.json')):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            days = data.get('days', {})
            for day_str in sorted(days.keys()):
                day_data = days[day_str]
                for cruise in day_data.get('cruises', []):
                    cruise['date'] = day_str
                    all_cruises.append(cruise)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")

    # Sort by date
    all_cruises.sort(key=lambda x: x.get('date', ''))

    # Generate HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Cruise Schedule 2026-2028</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .controls {
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }

        .search-box, .month-filter {
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }

        .search-box {
            flex: 1;
            min-width: 200px;
        }

        .stats {
            padding: 20px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .stat {
            text-align: center;
        }

        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            font-size: 0.9em;
        }

        .cruises-section {
            padding: 40px;
        }

        .month-group {
            margin-bottom: 40px;
        }

        .month-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-size: 1.3em;
            font-weight: bold;
        }

        .cruises-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }

        .cruises-table thead {
            background: #f0f0f0;
        }

        .cruises-table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
            background: #f8f9fa;
        }

        .cruises-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }

        .cruises-table tr:hover {
            background: #f8f9fa;
        }

        .ship-name {
            font-weight: 600;
            color: #667eea;
        }

        .date {
            color: #666;
            font-size: 0.9em;
        }

        .ports {
            font-size: 0.85em;
            color: #555;
        }

        .prev-ports {
            color: #e74c3c;
            margin-bottom: 5px;
        }

        .next-ports {
            color: #27ae60;
        }

        .passengers {
            text-align: right;
            color: #666;
            font-size: 0.9em;
        }

        .source {
            font-size: 0.75em;
            color: #999;
            padding: 2px 6px;
            background: #f0f0f0;
            border-radius: 3px;
            display: inline-block;
        }

        footer {
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #ddd;
        }

        @media (max-width: 768px) {
            .controls {
                flex-direction: column;
            }

            .search-box {
                min-width: 100%;
            }

            .cruises-table {
                font-size: 0.85em;
            }

            .cruises-table th,
            .cruises-table td {
                padding: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚢 Roatan Cruise Schedule</h1>
            <p class="subtitle">2026 - 2028 Complete Itinerary Data</p>
        </header>

        <div class="controls">
            <input type="text" class="search-box" id="searchInput" placeholder="Search by ship name...">
            <select class="month-filter" id="monthFilter">
                <option value="">All Months</option>
            </select>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number" id="totalCruises">0</div>
                <div class="stat-label">Total Cruises</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="totalPassengers">0</div>
                <div class="stat-label">Total Passengers</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="uniqueShips">0</div>
                <div class="stat-label">Unique Ships</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="dateRange">0</div>
                <div class="stat-label">Months Covered</div>
            </div>
        </div>

        <div class="cruises-section" id="cruisesContainer">
            <!-- Cruises will be inserted here -->
        </div>

        <footer>
            <p>Data compiled from CruiseMapper extraction and typical cruise itineraries. Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </footer>
    </div>

    <script>
        const allCruises = """ + json.dumps(all_cruises) + """;
        let filteredCruises = [...allCruises];

        // Update stats
        function updateStats() {
            document.getElementById('totalCruises').textContent = filteredCruises.length;
            document.getElementById('totalPassengers').textContent =
                filteredCruises.reduce((sum, c) => sum + (c.estimated_passengers || 0), 0).toLocaleString();
            document.getElementById('uniqueShips').textContent =
                new Set(filteredCruises.map(c => c.ship_name)).size;
            document.getElementById('dateRange').textContent =
                new Set(filteredCruises.map(c => c.date.substring(0, 7))).size;
        }

        // Populate month filter
        const months = [...new Set(allCruises.map(c => c.date.substring(0, 7)))].sort();
        months.forEach(month => {
            const option = document.createElement('option');
            option.value = month;
            const [year, m] = month.split('-');
            const monthName = new Date(year, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' });
            option.textContent = monthName;
            document.getElementById('monthFilter').appendChild(option);
        });

        // Format ports for display
        function formatPorts(ports) {
            if (!ports || ports.length === 0) return '(none)';
            return ports.slice(0, 3).join(' → ') + (ports.length > 3 ? ` ... +${ports.length - 3} more` : '');
        }

        // Render cruises
        function renderCruises() {
            const container = document.getElementById('cruisesContainer');
            container.innerHTML = '';

            // Group by month
            const grouped = {};
            filteredCruises.forEach(cruise => {
                const month = cruise.date.substring(0, 7);
                if (!grouped[month]) grouped[month] = [];
                grouped[month].push(cruise);
            });

            // Sort months and render
            Object.keys(grouped).sort().forEach(month => {
                const [year, m] = month.split('-');
                const monthName = new Date(year, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' });

                const monthGroup = document.createElement('div');
                monthGroup.className = 'month-group';

                const header = document.createElement('div');
                header.className = 'month-header';
                header.textContent = monthName + ` (${grouped[month].length} cruises)`;
                monthGroup.appendChild(header);

                const table = document.createElement('table');
                table.className = 'cruises-table';

                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr>
                        <th style="width: 15%;">Date</th>
                        <th style="width: 20%;">Ship Name</th>
                        <th style="width: 25%;">Previous Ports</th>
                        <th style="width: 25%;">Next Ports</th>
                        <th style="width: 10%; text-align: right;">Passengers</th>
                        <th style="width: 5%;">Source</th>
                    </tr>
                `;
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                grouped[month].forEach(cruise => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="date">${new Date(cruise.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</td>
                        <td class="ship-name">${cruise.ship_name}</td>
                        <td class="ports prev-ports">${formatPorts(cruise.previous_ports)}</td>
                        <td class="ports next-ports">${formatPorts(cruise.next_ports)}</td>
                        <td class="passengers">${(cruise.estimated_passengers || 0).toLocaleString()}</td>
                        <td><span class="source">${cruise.source || 'unknown'}</span></td>
                    `;
                    tbody.appendChild(tr);
                });

                table.appendChild(tbody);
                monthGroup.appendChild(table);
                container.appendChild(monthGroup);
            });

            updateStats();
        }

        // Filter by search
        document.getElementById('searchInput').addEventListener('input', (e) => {
            const search = e.target.value.toLowerCase();
            const month = document.getElementById('monthFilter').value;

            filteredCruises = allCruises.filter(c => {
                const matchesSearch = c.ship_name.toLowerCase().includes(search);
                const matchesMonth = !month || c.date.startsWith(month);
                return matchesSearch && matchesMonth;
            });

            renderCruises();
        });

        // Filter by month
        document.getElementById('monthFilter').addEventListener('change', (e) => {
            const search = document.getElementById('searchInput').value.toLowerCase();
            const month = e.target.value;

            filteredCruises = allCruises.filter(c => {
                const matchesSearch = c.ship_name.toLowerCase().includes(search);
                const matchesMonth = !month || c.date.startsWith(month);
                return matchesSearch && matchesMonth;
            });

            renderCruises();
        });

        // Initial render
        renderCruises();
    </script>
</body>
</html>
"""

    # Write HTML file
    output_file = 'roatan_cruise_schedule.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Generated {output_file}")
    print(f"  Total cruises: {len(all_cruises)}")
    print(f"  Date range: {all_cruises[0]['date']} to {all_cruises[-1]['date']}")
    print(f"  File size: {len(html) / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    generate_html()
