HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker - June 2026</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a1a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 2.2em;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #2a2a4e;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-2px); }
        .stat-card .label { font-size: 0.85em; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
        .stat-card .value { font-size: 1.8em; font-weight: bold; }
        .stat-card .value.flights { color: #2E86AB; }
        .stat-card .value.cruises { color: #A23B72; }
        .stat-card .value.inflow { color: #2ECC40; }
        .stat-card .value.outflow { color: #F18F01; }
        .stat-card .value.net { color: #ffd700; }
        .chart-container {
            background: #111128;
            border: 1px solid #2a2a4e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }
        .chart-container .plotly-graph-div { margin: 0 auto; }
        .day-selector {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .day-selector label {
            font-size: 1em;
            color: #ccc;
        }
        .day-selector select {
            background: #1a1a2e;
            color: #e0e0e0;
            border: 1px solid #2a2a4e;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            outline: none;
        }
        .day-selector select:hover { border-color: #2E86AB; }
        .filter-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .filter-group label {
            font-size: 0.9em;
            color: #aaa;
        }
        .filter-btn {
            background: #1a1a2e;
            color: #ccc;
            border: 1px solid #2a2a4e;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.2s;
        }
        .filter-btn:hover {
            border-color: #2E86AB;
            color: #fff;
        }
        .filter-btn.active {
            background: #2E86AB;
            color: #fff;
            border-color: #2E86AB;
        }
        .footer {
            text-align: center;
            color: #555;
            font-size: 0.85em;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #2a2a4e;
        }
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            h1 { font-size: 1.6em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Roatan Tourism Tracker</h1>
        <p class="subtitle">Real-time monitoring of tourist inflow & outflow via flights and cruise ships &bull; June 2026</p>

        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div class="label">Total Flights</div>
                <div class="value flights" id="totalFlights">--</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Cruise Ships</div>
                <div class="value cruises" id="totalCruises">--</div>
            </div>
            <div class="stat-card">
                <div class="label">Flight Passengers</div>
                <div class="value flights" id="flightPax">--</div>
            </div>
            <div class="stat-card">
                <div class="label">Cruise Passengers</div>
                <div class="value cruises" id="cruisePax">--</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Inflow</div>
                <div class="value inflow" id="totalInflow">--</div>
            </div>
            <div class="stat-card">
                <div class="label">Net Visitors</div>
                <div class="value net" id="netVisitors">--</div>
            </div>
        </div>

        <div class="day-selector">
            <label for="daySelect">Select Day:</label>
            <select id="daySelect" onchange="loadDayData()"></select>
            <div class="filter-group">
                <label>Filter:</label>
                <button class="filter-btn active" id="filterAll" onclick="setFilter('all')">All</button>
                <button class="filter-btn" id="filterFlights" onclick="setFilter('flights')">Flights</button>
                <button class="filter-btn" id="filterCruises" onclick="setFilter('cruises')">Cruises</button>
            </div>
        </div>

        <div class="chart-container" id="hourlyChart"></div>

        <div class="chart-container" id="flightTrafficChart"></div>
        <div class="chart-container" id="cruiseTrafficChart"></div>
        <div class="chart-container" id="combinedVolumeChart"></div>
        <div class="chart-container" id="logScaleChart"></div>
        <div class="chart-container" id="originPieChart"></div>
        <div class="chart-container" id="originInflowChart"></div>
        <div class="chart-container" id="hourlyPatternChart"></div>
        <div class="chart-container" id="cruiseCalendar"></div>
        <div class="chart-container" id="monthlyCalendarChart"></div>

        <div class="footer">
            Data sourced from flight schedules and cruise line timetables &bull; Updated daily
        </div>
    </div>

    <script>
        let currentFilter = 'all';

        function setFilter(filter) {
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(function(btn) {
                btn.classList.remove('active');
            });
            document.getElementById('filter' + filter.charAt(0).toUpperCase() + filter.slice(1)).classList.add('active');
            loadDayData();
        }

        function loadDayData() {
            var select = document.getElementById('daySelect');
            var dateStr = select.value;
            if (!dateStr) return;
            fetch('/api/day/' + dateStr + '?filter=' + currentFilter)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    Plotly.react('hourlyChart', data.hourly_chart, {responsive: true});
                });
        }

        function init() {
            var select = document.getElementById('daySelect');
            for (var d = 1; d <= 30; d++) {
                var opt = document.createElement('option');
                opt.value = '2026-06-' + (d < 10 ? '0' : '') + d;
                opt.textContent = 'June ' + d + ', 2026';
                select.appendChild(opt);
            }
            select.value = '2026-06-15';

            fetch('/api/monthly')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    document.getElementById('totalFlights').textContent = data.stats.total_flights;
                    document.getElementById('totalCruises').textContent = data.stats.total_cruises;
                    document.getElementById('flightPax').textContent = data.stats.total_flight_pax.toLocaleString();
                    document.getElementById('cruisePax').textContent = data.stats.total_cruise_pax.toLocaleString();
                    document.getElementById('totalInflow').textContent = data.stats.total_inflow.toLocaleString();
                    document.getElementById('netVisitors').textContent = data.stats.net_visitors.toLocaleString();

                    Plotly.react('flightTrafficChart', data.flight_traffic_chart, {responsive: true});
                    Plotly.react('cruiseTrafficChart', data.cruise_traffic_chart, {responsive: true});
                    Plotly.react('combinedVolumeChart', data.combined_volume_chart, {responsive: true});
                    Plotly.react('logScaleChart', data.log_scale_chart, {responsive: true});
                    Plotly.react('originPieChart', data.origin_pie_chart, {responsive: true});
                    Plotly.react('originInflowChart', data.origin_inflow_chart, {responsive: true});
                    Plotly.react('hourlyPatternChart', data.hourly_pattern_chart, {responsive: true});
                    Plotly.react('cruiseCalendar', data.cruise_calendar, {responsive: true});
                    Plotly.react('monthlyCalendarChart', data.monthly_calendar_chart, {responsive: true});
                });

            loadDayData();
        }

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/day/<date_str>')
def api_day_data(date_str):
    """Return hourly chart data for a specific day, with optional filter."""
    filter_mode = request.args.get('filter', 'all')
    if filter_mode not in ('all', 'flights', 'cruises'):
        filter_mode = 'all'

    monthly_data = load_monthly_data()
    if date_str not in monthly_data.get('days', {}):
        return jsonify({'error': 'Date not found'}), 404

    day_data = monthly_data['days'][date_str]
    hourly = process_daily_data(day_data)
    hourly_chart = create_daily_hourly_chart(hourly, date_str, filter_mode)

    return jsonify({
        'date': date_str,
        'hourly_chart': json.loads(hourly_chart),
    })


@app.route('/api/monthly')
def api_monthly_data():
    """Return all monthly chart data and statistics."""
    monthly_data = load_monthly_data()
    weather_data = get_weather_data()

    stats = create_monthly_stats(monthly_data)

    return jsonify({
        'stats': stats,
        'flight_traffic_chart': json.loads(create_flight_traffic_chart(monthly_data)),
        'cruise_traffic_chart': json.loads(create_cruise_traffic_chart(monthly_data)),
        'combined_volume_chart': json.loads(create_combined_volume_chart(monthly_data)),
        'log_scale_chart': json.loads(create_log_scale_chart(monthly_data)),
        'origin_pie_chart': json.loads(create_origin_pie_chart(monthly_data)),
        'origin_inflow_chart': json.loads(create_origin_inflow_chart(monthly_data)),
        'hourly_pattern_chart': json.loads(create_hourly_pattern_chart(monthly_data)),
        'cruise_calendar': json.loads(create_cruise_calendar(monthly_data)),
        'monthly_calendar_chart': json.loads(create_monthly_calendar_chart(monthly_data, weather_data)),
    })


def generate_static_html():
    """Generate a complete static HTML file with all charts embedded."""
    monthly_data = load_monthly_data()
    weather_data = get_weather_data()
    stats = create_monthly_stats(monthly_data)

    # Generate all chart JSON
    charts = {
        'flight_traffic_chart': create_flight_traffic_chart(monthly_data),
        'cruise_traffic_chart': create_cruise_traffic_chart(monthly_data),
        'combined_volume_chart': create_combined_volume_chart(monthly_data),
        'log_scale_chart': create_log_scale_chart(monthly_data),
        'origin_pie_chart': create_origin_pie_chart(monthly_data),
        'origin_inflow_chart': create_origin_inflow_chart(monthly_data),
        'hourly_pattern_chart': create_hourly_pattern_chart(monthly_data),
        'cruise_calendar': create_cruise_calendar(monthly_data),
        'monthly_calendar_chart': create_monthly_calendar_chart(monthly_data, weather_data),
    }

    # Generate hourly chart for each day (using default 'all' filter)
    hourly_charts = {}
    for d in sorted(monthly_data['days'].keys()):
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        hourly_charts[d] = create_daily_hourly_chart(hourly, d, 'all')

    # Build the static HTML
    html = HTML_TEMPLATE.replace('</body>', '').replace('</html>', '')

    # Add script to embed all data
    html += '<script>\n'
    html += 'var STATIC_DATA = ' + json.dumps({
        'stats': stats,
        'charts': {k: json.loads(v) for k, v in charts.items()},
        'hourly_charts': {k: json.loads(v) for k, v in hourly_charts.items()},
    }) + ';\n'
    html += '''
        function renderStatic() {
            var data = STATIC_DATA;
            document.getElementById('totalFlights').textContent = data.stats.total_flights;
            document.getElementById('totalCruises').textContent = data.stats.total_cruises;
            document.getElementById('flightPax').textContent = data.stats.total_flight_pax.toLocaleString();
            document.getElementById('cruisePax').textContent = data.stats.total_cruise_pax.toLocaleString();
            document.getElementById('totalInflow').textContent = data.stats.total_inflow.toLocaleString();
            document.getElementById('netVisitors').textContent = data.stats.net_visitors.toLocaleString();

            Plotly.react('flightTrafficChart', data.charts.flight_traffic_chart, {responsive: true});
            Plotly.react('cruiseTrafficChart', data.charts.cruise_traffic_chart, {responsive: true});
            Plotly.react('combinedVolumeChart', data.charts.combined_volume_chart, {responsive: true});
            Plotly.react('logScaleChart', data.charts.log_scale_chart, {responsive: true});
            Plotly.react('originPieChart', data.charts.origin_pie_chart, {responsive: true});
            Plotly.react('originInflowChart', data.charts.origin_inflow_chart, {responsive: true});
            Plotly.react('hourlyPatternChart', data.charts.hourly_pattern_chart, {responsive: true});
            Plotly.react('cruiseCalendar', data.charts.cruise_calendar, {responsive: true});
            Plotly.react('monthlyCalendarChart', data.charts.monthly_calendar_chart, {responsive: true});

            // Render hourly chart for selected day
            var select = document.getElementById('daySelect');
            var renderHourly = function() {
                var d = select.value;
                if (data.hourly_charts[d]) {
                    Plotly.react('hourlyChart', data.hourly_charts[d], {responsive: true});
                }
            };
            select.addEventListener('change', renderHourly);
            renderHourly();
        }
        document.addEventListener('DOMContentLoaded', renderStatic);
    </script>
</body>
</html>
'''

    return html


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
