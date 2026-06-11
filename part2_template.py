"""
Part 2: HTML_TEMPLATE, API routes, generate_static_html, and main block
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #e0e0e0;
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .header h1 {
            font-size: 28px;
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .controls {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .controls select, .controls button {
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #30363d;
            background: #161b22;
            color: #e0e0e0;
            font-size: 14px;
            cursor: pointer;
        }
        .controls select:hover, .controls button:hover {
            border-color: #2E86AB;
        }
        .controls button.active {
            background: #2E86AB;
            border-color: #2E86AB;
            color: white;
        }
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .stat-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #2E86AB;
        }
        .stat-card .label {
            font-size: 12px;
            color: #8b949e;
            margin-top: 4px;
        }
        .chart-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }
        .chart-full {
            margin-bottom: 16px;
        }
        .chart-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 10px;
        }
        .chart-card .plotly-graph-div {
            width: 100% !important;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #8b949e;
            font-size: 18px;
        }
        .error {
            text-align: center;
            padding: 20px;
            color: #f85149;
        }
        @media (max-width: 900px) {
            .chart-grid { grid-template-columns: 1fr; }
            .header { flex-direction: column; align-items: flex-start; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Roatan Tourism Tracker</h1>
        <div class="controls">
            <select id="monthSelector" onchange="changeMonth()">
                {% for ym in available_months %}
                <option value="{{ ym[0] }}-{{ ym[1] }}" {% if ym[0] == selected_year and ym[1] == selected_month %}selected{% endif %}>
                    {{ get_month_label(ym[0], ym[1]) }}
                </option>
                {% endfor %}
            </select>
            <select id="daySelector" onchange="changeDay()">
                {% for d in days %}
                <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>{{ d }}</option>
                {% endfor %}
            </select>
            <button id="filterAll" class="active" onclick="setFilter('all')">All</button>
            <button id="filterFlights" onclick="setFilter('flights')">Flights</button>
            <button id="filterCruises" onclick="setFilter('cruises')">Cruises</button>
        </div>
    </div>

    <div id="statsRow" class="stats-row"></div>
    <div id="calendarChart" class="chart-full chart-card"></div>
    <div id="hourlyChart" class="chart-full chart-card"></div>
    <div class="chart-grid">
        <div id="flightChart" class="chart-card"></div>
        <div id="cruiseChart" class="chart-card"></div>
    </div>
    <div class="chart-grid">
        <div id="combinedVolumeChart" class="chart-card"></div>
        <div id="logScaleChart" class="chart-card"></div>
    </div>
    <div class="chart-grid">
        <div id="originPieChart" class="chart-card"></div>
        <div id="originInflowChart" class="chart-card"></div>
    </div>
    <div class="chart-grid">
        <div id="hourlyPatternChart" class="chart-card"></div>
        <div id="eventTimelineChart" class="chart-card"></div>
    </div>
    <div id="cruiseCalendar" class="chart-full chart-card"></div>

    <script>
        let currentFilter = 'all';
        let currentDate = '{{ selected_date }}';
        let currentYear = {{ selected_year }};
        let currentMonth = {{ selected_month }};

        function setFilter(mode) {
            currentFilter = mode;
            document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
            document.getElementById('filter' + mode.charAt(0).toUpperCase() + mode.slice(1)).classList.add('active');
            loadDayData(currentDate);
        }

        function changeMonth() {
            const sel = document.getElementById('monthSelector');
            const parts = sel.value.split('-');
            currentYear = parseInt(parts[0]);
            currentMonth = parseInt(parts[1]);
            loadMonthData();
        }

        function changeDay() {
            currentDate = document.getElementById('daySelector').value;
            loadDayData(currentDate);
        }

        function loadMonthData() {
            document.querySelectorAll('.chart-card').forEach(el => {
                el.innerHTML = '<div class="loading">Loading...</div>';
            });
            document.getElementById('statsRow').innerHTML = '<div class="loading">Loading statistics...</div>';

            fetch('/api/monthly?year=' + currentYear + '&month=' + currentMonth)
                .then(r => r.json())
                .then(data => {
                    const daySel = document.getElementById('daySelector');
                    daySel.innerHTML = data.days.map(d =>
                        '<option value="' + d + '" ' + (d === data.days[0] ? 'selected' : '') + '>' + d + '</option>'
                    ).join('');
                    currentDate = data.days[0] || currentDate;
                    renderStats(data.stats);
                    Plotly.newPlot('calendarChart', JSON.parse(data.calendar_chart));
                    Plotly.newPlot('flightChart', JSON.parse(data.flight_chart));
                    Plotly.newPlot('cruiseChart', JSON.parse(data.cruise_chart));
                    Plotly.newPlot('combinedVolumeChart', JSON.parse(data.combined_volume_chart));
                    Plotly.newPlot('logScaleChart', JSON.parse(data.log_scale_chart));
                    Plotly.newPlot('originPieChart', JSON.parse(data.origin_pie_chart));
                    Plotly.newPlot('originInflowChart', JSON.parse(data.origin_inflow_chart));
                    Plotly.newPlot('hourlyPatternChart', JSON.parse(data.hourly_pattern_chart));
                    Plotly.newPlot('eventTimelineChart', JSON.parse(data.event_timeline_chart));
                    Plotly.newPlot('cruiseCalendar', JSON.parse(data.cruise_calendar));
                    loadDayData(currentDate);
                })
                .catch(err => {
                    document.querySelectorAll('.chart-card').forEach(el => {
                        el.innerHTML = '<div class="error">Error loading data: ' + err.message + '</div>';
                    });
                });
        }

        function loadDayData(dateStr) {
            const el = document.getElementById('hourlyChart');
            el.innerHTML = '<div class="loading">Loading hourly data...</div>';
            fetch('/api/day/' + dateStr + '?filter=' + currentFilter + '&year=' + currentYear + '&month=' + currentMonth)
                .then(r => r.json())
                .then(data => {
                    Plotly.newPlot('hourlyChart', JSON.parse(data.chart));
                })
                .catch(err => {
                    el.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
                });
        }

        function renderStats(stats) {
            const row = document.getElementById('statsRow');
            row.innerHTML = '';
            const cards = [
                { label: 'Total Arrivals', value: stats.total_arrivals.toLocaleString() },
                { label: 'Total Departures', value: stats.total_departures.toLocaleString() },
                { label: 'Flight Arrivals', value: stats.total_flight_arrivals.toLocaleString() },
                { label: 'Flight Departures', value: stats.total_flight_departures.toLocaleString() },
                { label: 'Cruise Arrivals', value: stats.total_cruise_arrivals.toLocaleString() },
                { label: 'Cruise Departures', value: stats.total_cruise_departures.toLocaleString() },
                { label: 'Total Flights', value: stats.total_flights.toLocaleString() },
                { label: 'Total Cruise Ships', value: stats.total_cruise_ships.toLocaleString() },
            ];
            cards.forEach(c => {
                const div = document.createElement('div');
                div.className = 'stat-card';
                div.innerHTML = '<div class="value">' + c.value + '</div><div class="label">' + c.label + '</div>';
                row.appendChild(div);
            });
        }
    </script>
</body>
</html>"""


@app.route('/')
def index():
    """Main dashboard page."""
    year = request.args.get('year', 2026, type=int)
    month = request.args.get('month', 6, type=int)

    # Validate month range
    if (year, month) not in AVAILABLE_MONTHS:
        year, month = 2026, 6

    monthly_data = load_monthly_data(year, month)
    weather_data = get_weather_data(year, month)
    days = sorted(monthly_data['days'].keys())
    selected_date = days[0] if days else ''

    return render_template_string(
        HTML_TEMPLATE,
        available_months=AVAILABLE_MONTHS,
        selected_year=year,
        selected_month=month,
        selected_date=selected_date,
        days=days,
        get_month_label=get_month_label
    )


@app.route('/api/day/<date_str>')
def api_day_detail(date_str):
    """API endpoint for hourly data of a specific day."""
    filter_mode = request.args.get('filter', 'all')
    year = request.args.get('year', 2026, type=int)
    month = request.args.get('month', 6, type=int)

    monthly_data = load_monthly_data(year, month)
    day_data = monthly_data['days'].get(date_str)

    if not day_data:
        return jsonify({'error': 'Date not found'}), 404

    hourly = process_daily_data(day_data)
    chart_json = create_daily_hourly_chart(hourly, date_str, filter_mode)

    return jsonify({'chart': chart_json})


@app.route('/api/monthly')
def api_monthly():
    """API endpoint for all monthly chart data."""
    year = request.args.get('year', 2026, type=int)
    month = request.args.get('month', 6, type=int)

    monthly_data = load_monthly_data(year, month)
    weather_data = get_weather_data(year, month)
    days = sorted(monthly_data['days'].keys())

    stats = create_monthly_stats(monthly_data)
    calendar_chart = create_monthly_calendar_chart(monthly_data, weather_data, year, month)
    flight_chart = create_flight_traffic_chart(monthly_data, year, month)
    cruise_chart = create_cruise_traffic_chart(monthly_data, year, month)
    combined_volume_chart = create_combined_volume_chart(monthly_data, year, month)
    log_scale_chart = create_log_scale_chart(monthly_data, year, month)
    origin_pie_chart = create_origin_pie_chart(monthly_data, year, month)
    origin_inflow_chart = create_origin_inflow_chart(monthly_data, year, month)
    hourly_pattern_chart = create_hourly_pattern_chart(monthly_data, year, month)
    event_timeline_chart = create_event_timeline_chart(monthly_data, year, month)
    cruise_calendar = create_cruise_calendar(monthly_data, year, month)

    return jsonify({
        'days': days,
        'stats': stats,
        'calendar_chart': calendar_chart,
        'flight_chart': flight_chart,
        'cruise_chart': cruise_chart,
        'combined_volume_chart': combined_volume_chart,
        'log_scale_chart': log_scale_chart,
        'origin_pie_chart': origin_pie_chart,
        'origin_inflow_chart': origin_inflow_chart,
        'hourly_pattern_chart': hourly_pattern_chart,
        'event_timeline_chart': event_timeline_chart,
        'cruise_calendar': cruise_calendar,
    })


def generate_static_html():
    """Generate static HTML files for all months for GitHub Pages deployment."""
    import os

    output_dir = 'static_site'
    os.makedirs(output_dir, exist_ok=True)

    for year, month in AVAILABLE_MONTHS:
        print(f"Generating static page for {get_month_label(year, month)}...")

        monthly_data = load_monthly_data(year, month)
        weather_data = get_weather_data(year, month)
        days = sorted(monthly_data['days'].keys())
        selected_date = days[0] if days else ''

        # Generate all chart JSON
        stats = create_monthly_stats(monthly_data)
        calendar_chart = create_monthly_calendar_chart(monthly_data, weather_data, year, month)
        flight_chart = create_flight_traffic_chart(monthly_data, year, month)
        cruise_chart = create_cruise_traffic_chart(monthly_data, year, month)
        combined_volume_chart = create_combined_volume_chart(monthly_data, year, month)
        log_scale_chart = create_log_scale_chart(monthly_data, year, month)
        origin_pie_chart = create_origin_pie_chart(monthly_data, year, month)
        origin_inflow_chart = create_origin_inflow_chart(monthly_data, year, month)
        hourly_pattern_chart = create_hourly_pattern_chart(monthly_data, year, month)
        event_timeline_chart = create_event_timeline_chart(monthly_data, year, month)
        cruise_calendar = create_cruise_calendar(monthly_data, year, month)

        # Generate first day hourly chart
        first_day_data = monthly_data['days'].get(selected_date, {})
        first_hourly = process_daily_data(first_day_data)
        hourly_chart = create_daily_hourly_chart(first_hourly, selected_date, 'all')

        # Create static HTML with embedded data
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker - {get_month_label(year, month)}</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #e0e0e0;
            padding: 20px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .header h1 {{ font-size: 28px; }}
        .header h1 span {{ background: linear-gradient(135deg, #2E86AB, #A23B72); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .month-nav {{
            display: flex; gap: 8px; align-items: center;
        }}
        .month-nav a, .month-nav span {{
            padding: 6px 12px; border-radius: 6px;
            border: 1px solid #30363d; background: #161b22;
            color: #e0e0e0; font-size: 13px; text-decoration: none;
        }}
        .month-nav a:hover {{ border-color: #2E86AB; }}
        .month-nav .current {{ background: #2E86AB; border-color: #2E86AB; }}
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px; margin-bottom: 20px;
        }}
        .stat-card {{
            background: #161b22; border: 1px solid #30363d;
            border-radius: 8px; padding: 15px; text-align: center;
        }}
        .stat-card .value {{ font-size: 24px; font-weight: bold; color: #2E86AB; }}
        .stat-card .label {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
        .chart-grid {{
            display: grid; grid-template-columns: 1fr 1fr;
            gap: 16px; margin-bottom: 16px;
        }}
        .chart-full {{ margin-bottom: 16px; }}
        .chart-card {{
            background: #161b22; border: 1px solid #30363d;
            border-radius: 8px; padding: 10px;
        }}
        @media (max-width: 900px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1><span>Roatan Tourism Tracker</span></h1>
        <div class="month-nav">
            <a href="index.html">All Months</a>
            <span class="current">{get_month_label(year, month)}</span>
        </div>
    </div>

    <div class="stats-row" id="statsRow"></div>
    <div id="calendarChart" class="chart-full chart-card"></div>
    <div id="hourlyChart" class="chart-full chart-card"></div>
    <div class="chart-grid">
        <div id="flightChart" class="chart-card"></div>
        <div id="cruiseChart" class="chart-card"></div>
    </div>
    <div class="chart-grid">
        <div id="combinedVolumeChart" class="chart-card"></div>
        <div id="logScaleChart" class="chart-card"></div>
    </div>
    <div class="chart-grid">
        <div id="originPieChart" class="chart-card"></div>
        <div id="originInflowChart" class="chart-card"></div>
    </div>
    <div class="chart-grid">
        <div id="hourlyPatternChart" class="chart-card"></div>
        <div id="eventTimelineChart" class="chart-card"></div>
    </div>
    <div id="cruiseCalendar" class="chart-full chart-card"></div>

    <script>
        const stats = {json.dumps(stats)};
        const charts = {{
            calendarChart: {calendar_chart},
            flightChart: {flight_chart},
            cruiseChart: {cruise_chart},
            combinedVolumeChart: {combined_volume_chart},
            logScaleChart: {log_scale_chart},
            originPieChart: {origin_pie_chart},
            originInflowChart: {origin_inflow_chart},
            hourlyPatternChart: {hourly_pattern_chart},
            eventTimelineChart: {event_timeline_chart},
            cruiseCalendar: {cruise_calendar},
            hourlyChart: {hourly_chart},
        }};

        function renderStats(s) {{
            const row = document.getElementById('statsRow');
            const cards = [
                {{ label: 'Total Arrivals', value: s.total_arrivals.toLocaleString() }},
                {{ label: 'Total Departures', value: s.total_departures.toLocaleString() }},
                {{ label: 'Flight Arrivals', value: s.total_flight_arrivals.toLocaleString() }},
                {{ label: 'Flight Departures', value: s.total_flight_departures.toLocaleString() }},
                {{ label: 'Cruise Arrivals', value: s.total_cruise_arrivals.toLocaleString() }},
                {{ label: 'Cruise Departures', value: s.total_cruise_departures.toLocaleString() }},
                {{ label: 'Total Flights', value: s.total_flights.toLocaleString() }},
                {{ label: 'Total Cruise Ships', value: s.total_cruise_ships.toLocaleString() }},
            ];
            cards.forEach(c => {{
                const div = document.createElement('div');
                div.className = 'stat-card';
                div.innerHTML = '<div class=\"value\">' + c.value + '</div><div class=\"label\">' + c.label + '</div>';
                row.appendChild(div);
            }});
        }}

        renderStats(stats);
        Object.keys(charts).forEach(id => {{
            Plotly.newPlot(id, JSON.parse(charts[id]));
        }});
    </script>
</body>
</html>"""

        # Write the file
        month_key = get_month_key(year, month)
        filepath = os.path.join(output_dir, f'{month_key}.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  Generated {filepath}")

    # Generate index page
    print("Generating index page...")
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker - All Months</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #e0e0e0;
            padding: 40px;
        }
        h1 {
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { color: #8b949e; margin-bottom: 30px; font-size: 16px; }
        .month-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 16px;
        }
        .month-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            text-decoration: none;
            color: #e0e0e0;
            transition: border-color 0.2s;
        }
        .month-card:hover { border-color: #2E86AB; }
        .month-card .month-name { font-size: 18px; font-weight: bold; }
        .month-card .year-name { font-size: 14px; color: #8b949e; margin-top: 4px; }
    </style>
</head>
<body>
    <h1>Roatan Tourism Tracker</h1>
    <p class="subtitle">Monthly tourism data for Roatan, Honduras — June 2026 through November 2028</p>
    <div class="month-grid">
"""

    for year, month in AVAILABLE_MONTHS:
        month_key = get_month_key(year, month)
        month_label = get_month_label(year, month)
        index_html += f'        <a href="{month_key}.html" class="month-card">\n'
        index_html += f'            <div class="month-name">{datetime(year, month, 1).strftime("%B")}</div>\n'
        index_html += f'            <div class="year-name">{year}</div>\n'
        index_html += f'        </a>\n'

    index_html += """    </div>
</body>
</html>"""

    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"Generated {os.path.join(output_dir, 'index.html')}")
    print(f"Static site generated in '{output_dir}/' directory.")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'generate':
        with app.app_context():
            generate_static_html()
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
