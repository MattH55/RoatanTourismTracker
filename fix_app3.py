#!/usr/bin/env python3
"""Fix the truncated app.py by appending ALL missing content including HTML_TEMPLATE, routes, and main block."""
import os

# Read the current truncated file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the truncation point - remove the incomplete fig.add_trace line
cutoff = content.rfind('    fig.add_trace')
if cutoff > 0:
    content = content[:cutoff]

# Append ALL missing content
content += r"""    fig.add_trace(go.Bar(
        name='Flight Departures', x=day_labels, y=daily_out_flights,
        marker_color='#F18F01',
        hovertemplate='%{y:,.0f} departing by flight<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Departures', x=day_labels, y=daily_out_cruise,
        marker_color='#C73E1D',
        hovertemplate='%{y:,.0f} departing by cruise<br>%{x}<extra>Cruise Departures</extra>'
    ))

    fig.update_layout(
        title=dict(text='<b>Daily Passenger Volume by Source (Linear Scale) - June 2026</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers', tickformat=','),
        barmode='group', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_hourly_pattern_chart(monthly_data):
    """Create a chart showing average hourly arrival/departure rates by source (flight vs cruise)."""
    # Aggregate hourly data across all days
    hourly_totals = {h: {'in_flights': 0, 'out_flights': 0, 'in_cruise': 0, 'out_cruise': 0} for h in range(24)}

    days = sorted(monthly_data['days'].keys())
    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        for h in range(24):
            hourly_totals[h]['in_flights'] += hourly[h]['in_flights']
            hourly_totals[h]['out_flights'] += hourly[h]['out_flights']
            hourly_totals[h]['in_cruise'] += hourly[h]['in_cruise']
            hourly_totals[h]['out_cruise'] += hourly[h]['out_cruise']

    num_days = len(days)
    hours = list(range(24))
    labels = [f'{h:02d}:00' for h in hours]

    # Average hourly rates
    avg_in_flights = [hourly_totals[h]['in_flights'] / num_days for h in hours]
    avg_out_flights = [hourly_totals[h]['out_flights'] / num_days for h in hours]
    avg_in_cruise = [hourly_totals[h]['in_cruise'] / num_days for h in hours]
    avg_out_cruise = [hourly_totals[h]['out_cruise'] / num_days for h in hours]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name='Flight Arrivals', x=labels, y=avg_in_flights,
        mode='lines+markers', line=dict(color='#2E86AB', width=3),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='%{y:,.0f} passengers/hr<br>%{x}<extra>Flight Arrivals</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Flight Departures', x=labels, y=avg_out_flights,
        mode='lines+markers', line=dict(color='#F18F01', width=3),
        marker=dict(size=8, symbol='diamond'),
        hovertemplate='%{y:,.0f} passengers/hr<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Cruise Arrivals', x=labels, y=avg_in_cruise,
        mode='lines+markers', line=dict(color='#A23B72', width=3),
        marker=dict(size=8, symbol='square'),
        hovertemplate='%{y:,.0f} passengers/hr<br>%{x}<extra>Cruise Arrivals</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Cruise Departures', x=labels, y=avg_out_cruise,
        mode='lines+markers', line=dict(color='#C73E1D', width=3),
        marker=dict(size=8, symbol='x'),
        hovertemplate='%{y:,.0f} passengers/hr<br>%{x}<extra>Cruise Departures</extra>'
    ))

    fig.update_layout(
        title=dict(text='<b>Average Hourly Arrival & Departure Rates by Source - June 2026</b>', font=dict(size=20)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=labels[::2], ticktext=labels[::2]),
        yaxis=dict(title='Average Passengers per Hour', tickformat=','),
        hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_cruise_calendar(monthly_data):
    """Create a chart showing which cruise ships visit on which days."""
    days = sorted(monthly_data['days'].keys())
    day_labels = [f'Jun {int(d.split("-")[2])}' for d in days]

    # Collect all unique ship names
    all_ships = set()
    for d in days:
        for c in monthly_data['days'][d].get('cruises', []):
            all_ships.add(c['ship_name'])
    all_ships = sorted(all_ships)

    # Build presence matrix
    ship_presence = {ship: [] for ship in all_ships}
    ship_pax = {ship: [] for ship in all_ships}
    for d in days:
        ships_today = {c['ship_name']: c['estimated_passengers']
                       for c in monthly_data['days'][d].get('cruises', [])}
        for ship in all_ships:
            if ship in ships_today:
                ship_presence[ship].append(ships_today[ship])
                ship_pax[ship].append(ships_today[ship])
            else:
                ship_presence[ship].append(0)
                ship_pax[ship].append(0)

    fig = go.Figure()

    for ship in all_ships:
        fig.add_trace(go.Bar(
            name=ship,
            x=day_labels,
            y=ship_presence[ship],
            hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>' + ship + '</extra>'
        ))

    fig.update_layout(
        title=dict(text='<b>Cruise Ship Schedule - June 2026</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers', tickformat=','),
        barmode='stack', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_monthly_stats(monthly_data):
    """Calculate monthly summary statistics."""
    days = sorted(monthly_data['days'].keys())
    total_flights = 0
    total_cruises = 0
    total_flight_pax = 0
    total_cruise_pax = 0
    total_inflow = 0
    total_outflow = 0
    daily_totals = []

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        day_in = sum(hourly[h]['total_in'] for h in range(24))
        day_out = sum(hourly[h]['total_out'] for h in range(24))
        daily_totals.append(day_in - day_out)
        total_inflow += day_in
        total_outflow += day_out
        total_flights += len(day_data.get('flights', []))
        total_cruises += len(day_data.get('cruises', []))
        total_flight_pax += sum(f.get('estimated_passengers', 0) for f in day_data.get('flights', []))
        total_cruise_pax += sum(c.get('estimated_passengers', 0) for c in day_data.get('cruises', []))

    avg_daily_inflow = total_inflow / len(days)
    avg_daily_outflow = total_outflow / len(days)
    peak_day_idx = max(range(len(daily_totals)), key=lambda i: daily_totals[i])
    peak_day = days[peak_day_idx]

    return {
        'total_days': len(days),
        'total_flights': total_flights,
        'total_cruises': total_cruises,
        'total_flight_pax': total_flight_pax,
        'total_cruise_pax': total_cruise_pax,
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'net_visitors': total_inflow - total_outflow,
        'avg_daily_inflow': int(avg_daily_inflow),
        'avg_daily_outflow': int(avg_daily_outflow),
        'peak_day': peak_day,
        'peak_day_net': daily_totals[peak_day_idx],
    }


def create_monthly_calendar_chart(monthly_data, weather_data):
    """Create a calendar-style heatmap showing daily visitor counts with day-of-week and weather overlay.
    Uses Viridis color scheme from Plotly Express."""
    days = sorted(monthly_data['days'].keys())
    
    # Day of week names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Calculate daily totals (new arrivals = total inflow)
    daily_totals = []
    daily_labels = []
    daily_dow = []
    daily_weather_conditions = []
    daily_highs = []
    daily_lows = []
    
    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        total_in = sum(hourly[h]['total_in'] for h in range(24))
        daily_totals.append(total_in)
        
        day_num = int(d.split('-')[2])
        # June 1, 2026 is a Monday
        base_date = datetime(2026, 6, 1)
        current_date = datetime(2026, 6, day_num)
        dow = current_date.weekday()  # 0=Monday
        daily_dow.append(day_names[dow])
        daily_labels.append(f'Jun {day_num}')
        
        # Weather data
        w = weather_data.get(d, {})
        daily_weather_conditions.append(w.get('condition', 'N/A'))
        daily_highs.append(w.get('high_c', 30))
        daily_lows.append(w.get('low_c', 25))
    
    # Create a calendar grid: 5 rows (weeks) x 7 columns (days)
    # June 2026 starts on Monday
    calendar_grid = []
    weather_grid = []
    temp_grid = []
    week_labels = []
    
    for day_num in range(1, 31):
        idx = day_num - 1
        
        # Calculate week and day-of-week position
        # June 1 = Monday (col 0), June 7 = Sunday (col 6)
        col = (day_num - 1) % 7
        row = (day_num - 1) // 7
        
        if col == 0:
            calendar_grid.append([None] * 7)
            weather_grid.append([None] * 7)
            temp_grid.append([None] * 7)
            week_start = day_num
            week_end = min(day_num + 6, 30)
            week_labels.append(f'Jun {week_start}-{week_end}')
        
        calendar_grid[row][col] = daily_totals[idx]
        weather_grid[row][col] = daily_weather_conditions[idx]
        temp_grid[row][col] = f"{daily_highs[idx]}C / {daily_lows[idx]}C"
    
    # Fill remaining cells in last week
    last_row = len(calendar_grid) - 1
    for col in range(len(calendar_grid[last_row])):
        if calendar_grid[last_row][col] is None:
            calendar_grid[last_row][col] = 0
            weather_grid[last_row][col] = ''
            temp_grid[last_row][col] = ''
    
    # Create hover text
    hover_texts = []
    for row_idx in range(len(calendar_grid)):
        row_texts = []
        for col_idx in range(7):
            day_num = row_idx * 7 + col_idx + 1
            if day_num <= 30:
                date_str = f"2026-06-{day_num:02d}"
                w = weather_data.get(date_str, {})
                net_val = calendar_grid[row_idx][col_idx]
                text = (
                    f"<b>June {day_num}, 2026</b><br>"
                    f"<b>{daily_dow[day_num-1]}</b><br>"
                    f"New Arrivals: {net_val:,.0f}<br>"
                    f"Weather: {w.get('condition', 'N/A')}<br>"
                    f"High: {w.get('high_c', 'N/A')}C / Low: {w.get('low_c', 'N/A')}C<br>"
                    f"Humidity: {w.get('humidity_pct', 'N/A')}%<br>"
                    f"Precipitation: {w.get('precipitation_mm', 0)} mm"
                )
                row_texts.append(text)
            else:
                row_texts.append('')
        hover_texts.append(row_texts)
    
    # Get Viridis colorscale from Plotly Express
    viridis_colors = px.colors.sequential.Viridis
    # Convert to Plotly colorscale format [[position, color], ...]
    colorscale = [[i / (len(viridis_colors) - 1), c] for i, c in enumerate(viridis_colors)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=calendar_grid,
        x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        y=week_labels,
        text=hover_texts,
        hoverinfo='text',
        colorscale=colorscale,
        colorbar=dict(
            title=dict(text='New Arrivals', side='right'),
            tickformat=',',
            thickness=15,
        ),
        hovertemplate='%{text}<extra></extra>',
    ))
    
    # Add weather condition annotations
    annotations = []
    for row_idx in range(len(calendar_grid)):
        for col_idx in range(7):
            day_num = row_idx * 7 + col_idx + 1
            if day_num <= 30:
                w = weather_data.get(f"2026-06-{day_num:02d}", {})
                condition = w.get('condition', '')
                emoji = ''
                if 'Sunny' in condition:
                    emoji = '\u2600\ufe0f'
                elif 'Partly' in condition:
                    emoji = '\u26c5'
                elif 'Showers' in condition:
                    emoji = '\U0001f326\ufe0f'
                elif 'Thunder' in condition:
                    emoji = '\u26c8\ufe0f'
                
                annotations.append(dict(
                    x=col_idx,
                    y=row_idx,
                    xref='x',
                    yref='y',
                    text=emoji,
                    showarrow=False,
                    font=dict(size=14),
                ))
    
    fig.update_layout(
        title=dict(
            text='<b>Monthly Calendar - Visitors & Weather - June 2026</b>',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Day of Week',
            side='top',
            tickmode='array',
            tickvals=list(range(7)),
            ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        ),
        yaxis=dict(
            title='Week',
            autorange='reversed',
        ),
        template='plotly_dark',
        height=400,
        margin=dict(l=80, r=100, t=80, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
        annotations=annotations,
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


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
            // Update button active states
            document.querySelectorAll('.filter-btn').forEach(function(btn) {
                btn.classList.remove('active');
            });
            document.getElementById('filter' + filter.charAt(0).toUpperCase() + filter.slice(1)).classList.add('active');
            // Reload the day data with the new filter
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
            // Populate day selector
            var select = document.getElementById('daySelect');
            for (var d = 1; d <= 30; d++) {
                var opt = document.createElement('option');
                opt.value = '2026-06-' + (d < 10 ? '0' : '') + d;
                opt.textContent = 'June ' + d + ', 2026';
                select.appendChild(opt);
            }
            select.value = '2026-06-15';

            // Load monthly data
            fetch('/api/monthly')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    // Update stats
                    document.getElementById('totalFlights').textContent = data.stats.total_flights;
                    document.getElementById('totalCruises').textContent = data.stats.total_cruises;
                    document.getElementById('flightPax').textContent = data.stats.total_flight_pax.toLocaleString();
                    document.getElementById('cruisePax').textContent = data.stats.total_cruise_pax.toLocaleString();
                    document.getElementById('totalInflow').textContent = data.stats.total_inflow.toLocaleString();
                    document.getElementById('netVisitors').textContent = data.stats.net_visitors.toLocaleString();

                    // Render all monthly charts
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

            // Load initial day data
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
            // Update stats
            document.getElementById('totalFlights').textContent = data.stats.total_flights;
            document.getElementById('totalCruises').textContent = data.stats.total_cruises;
            document.getElementById('flightPax').textContent = data.stats.total_flight_pax.toLocaleString();
            document.getElementById('cruisePax').textContent = data.stats.total_cruise_pax.toLocaleString();
            document.getElementById('totalInflow').textContent = data.stats.total_inflow.toLocaleString();
            document.getElementById('netVisitors').textContent = data.stats.net_visitors.toLocaleString();

            // Render monthly charts
            Plotly.react('flightTrafficChart', data.charts.flight_traffic_chart, {responsive: true});
            Plotly.react('cruiseTrafficChart', data.charts.cruise_traffic_chart, {responsive: true});
            Plotly.react('combinedVolumeChart', data.charts.combined_volume_chart, {responsive: true});
            Plotly.react('logScaleChart', data.charts.log_scale_chart, {responsive: true});
            Plotly.react('originPieChart', data.charts.origin_pie_chart, {responsive: true});
