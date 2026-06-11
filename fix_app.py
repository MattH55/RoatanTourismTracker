# Script to fix the truncated app.py by appending the missing content
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the truncation point
cutoff = content.rfind('    fig.add_trace')
if cutoff > 0:
    content = content[:cutoff]

# Now append the complete remaining content
remaining = '''    fig.add_trace(go.Bar(
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


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roatan Tourism Tracker - June 2026</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 50%, #0c0c1d 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(90deg, #1a1a3e, #2d2d6b);
            padding: 30px 20px;
            text-align: center;
            border-bottom: 3px solid #e94560;
            box-shadow: 0 4px 20px rgba(233, 69, 96, 0.3);
        }
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #2E86AB, #A23B72, #F18F01);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header p { color: #b0b0b0; margin-top: 8px; font-size: 1.1em; }
        .header .subtitle { color: #888; font-size: 0.9em; margin-top: 4px; }
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 18px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        .stat-card .value { font-size: 1.8em; font-weight: bold; margin: 5px 0; }
        .stat-card .label { font-size: 0.8em; color: #b0b0b0; text-transform: uppercase; letter-spacing: 1px; }
        .stat-card.flights .value { color: #2E86AB; }
        .stat-card.cruises .value { color: #A23B72; }
        .stat-card.total .value { color: #F18F01; }
        .stat-card.peak .value { color: #e94560; }
        .stat-card.net .value { color: #2ECC40; }
        .stat-card.avg .value { color: #f5a623; }
        .chart-container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }
        .chart-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        .chart-row .chart-container { margin: 0; }
        .day-selector {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
            text-align: center;
        }
        .day-selector select {
            background: rgba(255,255,255,0.1);
            color: #e0e0e0;
            border: 1px solid rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
        }
        .day-selector select:focus { outline: none; border-color: #e94560; }
        .day-selector label { margin-right: 10px; font-size: 1.1em; }
        .filter-btn {
            background: rgba(255,255,255,0.1);
            color: #e0e0e0;
            border: 1px solid rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.9em;
            cursor: pointer;
            margin: 0 3px;
            transition: all 0.3s;
        }
        .filter-btn:hover {
            background: rgba(255,255,255,0.2);
            border-color: #e94560;
        }
        .filter-btn.active {
            background: #e94560;
            border-color: #e94560;
            color: #fff;
            font-weight: bold;
        }
        .footer { text-align: center; padding: 30px; color: #666; font-size: 0.9em; }
        .footer a { color: #2E86AB; text-decoration: none; }
        .data-source {
            text-align: center; padding: 10px 20px; color: #888; font-size: 0.85em;
        }
        @media (max-width: 900px) {
            .chart-row { grid-template-columns: 1fr; }
            .header h1 { font-size: 1.8em; }
            .stats-container { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Roatan Tourism Tracker</h1>
        <p>Monthly tourist inflow & outflow monitoring • June 2026</p>
        <div class="subtitle">Flights & Cruise Ships • Passenger estimates based on aircraft/ship models with average occupancy rates</div>
    </div>

    <div class="stats-container">
        <div class="stat-card flights">
            <div class="label">Total Flights (June)</div>
            <div class="value">{{ "{:,}".format(stats.total_flights) }}</div>
            <div style="font-size:0.85em;color:#2E86AB;">{{ "{:,}".format(stats.total_flight_pax) }} passengers</div>
        </div>
        <div class="stat-card cruises">
            <div class="label">Total Cruise Visits</div>
            <div class="value">{{ "{:,}".format(stats.total_cruises) }}</div>
            <div style="font-size:0.85em;color:#A23B72;">{{ "{:,}".format(stats.total_cruise_pax) }} passengers</div>
        </div>
        <div class="stat-card total">
            <div class="label">Total Inflow</div>
            <div class="value">{{ "{:,}".format(stats.total_inflow) }}</div>
            <div style="font-size:0.85em;color:#F18F01;">over {{ stats.total_days }} days</div>
        </div>
        <div class="stat-card avg">
            <div class="label">Avg Daily Inflow</div>
            <div class="value">{{ "{:,}".format(stats.avg_daily_inflow) }}</div>
            <div style="font-size:0.85em;color:#f5a623;">{{ "{:,}".format(stats.avg_daily_outflow) }} departing</div>
        </div>
        <div class="stat-card net">
            <div class="label">Net Visitors (June)</div>
            <div class="value">{{ "{:,}".format(stats.net_visitors) }}</div>
            <div style="font-size:0.85em;color:#2ECC40;">inflow - outflow</div>
        </div>
        <div class="stat-card peak">
            <div class="label">Peak Day</div>
            <div class="value">{{ stats.peak_day.replace("2026-06-", "Jun ") }}</div>
            <div style="font-size:0.85em;color:#e94560;">{{ "{:,}".format(stats.peak_day_net) }} net visitors</div>
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-container">
            <div id="flightTraffic"></div>
        </div>
        <div class="chart-container">
            <div id="cruiseTraffic"></div>
        </div>
    </div>

    <div class="chart-container">
        <div id="monthlyHeatmap"></div>
    </div>

    <div class="chart-row">
        <div class="chart-container">
            <div id="logChart"></div>
        </div>
        <div class="chart-container">
            <div id="originPie"></div>
        </div>
    </div>

    <div class="chart-container">
        <div id="originInflow"></div>
    </div>

    <div class="chart-container">
        <div id="combinedVolume"></div>
    </div>

    <div class="chart-container">
        <div id="hourlyPattern"></div>
    </div>

    <div class="chart-container">
        <div id="monthlyCalendar"></div>
    </div>

    <div class="chart-row">
        <div class="chart-container">
            <div id="cruiseCalendar"></div>
        </div>
        <div class="chart-container">
            <div id="dailyDetail"></div>
        </div>
    </div>

    <div class="day-selector">
        <label for="daySelect">View details for:</label>
        <select id="daySelect" onchange="loadDayData(this.value)">
            {% for day in days %}
            <option value="{{ day }}" {% if loop.first %}selected{% endif %}>{{ day.replace("2026-06-", "June ") }}</option>
            {% endfor %}
        </select>
        <span style="margin-left:20px;">
            <label>Filter:</label>
            <button class="filter-btn active" id="filterAll" onclick="setFilter('all')">All</button>
            <button class="filter-btn" id="filterFlights" onclick="setFilter('flights')">Flights</button>
            <button class="filter-btn" id="filterCruises" onclick="setFilter('cruises')">Cruises</button>
        </span>
    </div>


    <div class="data-source">
        Data sources:
        <a href="https://www.flightaware.com/live/airport/MHRO" target="_blank">FlightAware (MHRO)</a> •
        <a href="https://www.cruisetimetables.com/roatanhondurasschedule-jun2026.html" target="_blank">CruiseTimetables</a>
        • Passenger estimates based on aircraft/ship models with average occupancy rates
    </div>

    <div class="footer">
        <p>Roatan Tourism Tracker • June 2026 Monthly Report</p>
    </div>

    <script>
        var currentFilter = 'all';

        var flightTraffic = {{ flight_traffic | safe }};
        var cruiseTraffic = {{ cruise_traffic | safe }};
        var monthlyHeatmap = {{ monthly_heatmap | safe }};
        var logChart = {{ log_chart | safe }};
        var originPie = {{ origin_pie | safe }};
        var originInflow = {{ origin_inflow | safe }};
        var combinedVolume = {{ combined_volume | safe }};
        var hourlyPattern = {{ hourly_pattern | safe }};
        var cruiseCalendar = {{ cruise_calendar | safe }};
        var dailyDetail = {{ daily_detail | safe }};
        var monthlyCalendar = {{ monthly_calendar | safe }};

        Plotly.newPlot('flightTraffic', flightTraffic.data, flightTraffic.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('cruiseTraffic', cruiseTraffic.data, cruiseTraffic.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('monthlyHeatmap', monthlyHeatmap.data, monthlyHeatmap.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('logChart', logChart.data, logChart.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('originPie', originPie.data, originPie.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('originInflow', originInflow.data, originInflow.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('combinedVolume', combinedVolume.data, combinedVolume.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('hourlyPattern', hourlyPattern.data, hourlyPattern.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('cruiseCalendar', cruiseCalendar.data, cruiseCalendar.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('dailyDetail', dailyDetail.data, dailyDetail.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('monthlyCalendar', monthlyCalendar.data, monthlyCalendar.layout, {
            responsive: true, displayModeBar: false
        });

        function setFilter(mode) {
            currentFilter = mode;
            // Update button active states
            document.getElementById('filterAll').className = 'filter-btn' + (mode === 'all' ? ' active' : '');
            document.getElementById('filterFlights').className = 'filter-btn' + (mode === 'flights' ? ' active' : '');
            document.getElementById('filterCruises').className = 'filter-btn' + (mode === 'cruises' ? ' active' : '');
            // Reload the chart with the current date and new filter
            var daySelect = document.getElementById('daySelect');
            loadDayData(daySelect.value);
        }

        function loadDayData(dateStr) {
            fetch('/api/day/' + dateStr + '?filter=' + currentFilter)
                .then(r => r.json())
                .then(data => {
                    var fig = JSON.parse(data.chart);
                    Plotly.react('dailyDetail', fig.data, fig.layout, {
                        responsive: true, displayModeBar: false
                    });
                });
        }

        window.addEventListener('resize', function() {
            Plotly.Plots.resize(document.getElementById('flightTraffic'));
            Plotly.Plots.resize(document.getElementById('cruiseTraffic'));
            Plotly.Plots.resize(document.getElementById('monthlyHeatmap'));
            Plotly.Plots.resize(document.getElementById('logChart'));
            Plotly.Plots.resize(document.getElementById('originPie'));
            Plotly.Plots.resize(document.getElementById('originInflow'));
            Plotly.Plots.resize(document.getElementById('combinedVolume'));
            Plotly.Plots.resize(document.getElementById('hourlyPattern'));
            Plotly.Plots.resize(document.getElementById('cruiseCalendar'));
            Plotly.Plots.resize(document.getElementById('dailyDetail'));
            Plotly.Plots.resize(document.getElementById('monthlyCalendar'));
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Main dashboard page showing monthly data."""
    monthly_data = load_monthly_data()
    days = sorted(monthly_data['days'].keys())

    stats = create_monthly_stats(monthly_data)
    flight_traffic = create_flight_traffic_chart(monthly_data)
    cruise_traffic = create_cruise_traffic_chart(monthly_data)
    monthly_heatmap = create_monthly_heatmap(monthly_data)
    log_chart = create_log_scale_chart(monthly_data)
    origin_pie = create_origin_pie_chart(monthly_data)
    origin_inflow = create_origin_inflow_chart(monthly_data)
    combined_volume = create_combined_volume_chart(monthly_data)
    hourly_pattern = create_hourly_pattern_chart(monthly_data)
    cruise_calendar = create_cruise_calendar(monthly_data)

    # Weather data and monthly calendar chart
    weather_data = get_weather_data()
    monthly_calendar = create_monthly_calendar_chart(monthly_data, weather_data)

    # Default to first day's detail
    first_day = days[0]
    day_data = monthly_data['days'][first_day]
    hourly = process_daily_data(day_data)
    daily_detail = create_daily_hourly_chart(hourly, first_day)

    return render_template