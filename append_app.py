"""Script to append remaining content to app.py"""
import os

# Read current file
with open('app.py', 'r') as f:
    content = f.read()

# Find where it was truncated - it ends with "month" in create_combined_volume_chart
# The last complete line should be: day_labels = []
# Let's find the last occurrence of "day_labels = []"
last_idx = content.rfind("day_labels = []")
if last_idx > 0:
    # Truncate to just before this point
    content = content[:last_idx]

# Now append the complete remaining content
remaining = """_abbr = datetime(year, month, 1).strftime('%b')

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        daily_in_flights.append(sum(hourly[h]['in_flights'] for h in range(24)))
        daily_in_cruise.append(sum(hourly[h]['in_cruise'] for h in range(24)))
        daily_out_flights.append(sum(hourly[h]['out_flights'] for h in range(24)))
        daily_out_cruise.append(sum(hourly[h]['out_cruise'] for h in range(24)))
        day_num = int(d.split('-')[2])
        day_labels.append(f'{month_abbr} {day_num}')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Flight Arrivals', x=day_labels, y=daily_in_flights,
        marker_color='#2E86AB',
        hovertemplate='%{y:,.0f} arriving by flight<br>%{x}<extra>Flight Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Arrivals', x=day_labels, y=daily_in_cruise,
        marker_color='#A23B72',
        hovertemplate='%{y:,.0f} arriving by cruise<br>%{x}<extra>Cruise Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Flight Departures', x=day_labels, y=daily_out_flights,
        marker_color='#F18F01',
        hovertemplate='%{y:,.0f} departing by flight<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Departures', x=day_labels, y=daily_out_cruise,
        marker_color='#C73E1D',
        hovertemplate='%{y:,.0f} departing by cruise<br>%{x}<extra>Cruise Departures</extra>'
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Daily Passenger Volume by Source (Linear Scale) - {month_label}</b>', font=dict(size=20)),
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


def create_hourly_pattern_chart(monthly_data, year=2026, month=6):
    \"\"\"Create a chart showing average hourly arrival/departure rates by source (flight vs cruise).\"\"\"
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

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Average Hourly Arrival & Departure Rates by Source - {month_label}</b>', font=dict(size=20)),
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


def create_event_timeline_chart(monthly_data, year=2026, month=6):
    \"\"\"Create a chart showing specific arrival/departure events with exact times and passenger counts.\"\"\"
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split(\"-\")[2])}' for d in days]

    flight_arrivals = []
    flight_departures = []
    cruise_arrivals = []
    cruise_departures = []

    for d in days:
        day_data = monthly_data['days'][d]
        day_num = int(d.split('-')[2])
        day_label = f'{month_abbr} {day_num}'

        for f in day_data.get('flights', []):
            hour = f.get('hour', 12)
            minute = f.get('minute', 0)
            time_str = f'{hour:02d}:{minute:02d}'
            pax = f.get('estimated_passengers', 100)
            flight_num = f.get('flight_number', '')
            origin = f.get('origin', '')
            aircraft = f.get('aircraft', '')

            event = {
                'day': day_label,
                'day_num': day_num,
                'time': time_str,
                'hour_decimal': hour + minute / 60.0,
                'passengers': pax,
                'label': f'{flight_num} ({origin})',
                'detail': f'{aircraft}',
            }

            if f.get('is_arrival'):
                flight_arrivals.append(event)
            else:
                flight_departures.append(event)

        for c in day_data.get('cruises', []):
            pax = c.get('estimated_passengers', 2000)
            ship_name = c.get('ship_name', '')
            arr_hour = c.get('arrival_hour', 8)
            dep_hour = c.get('departure_hour', 17)

            cruise_arrivals.append({
                'day': day_label,
                'day_num': day_num,
                'time': f'{arr_hour:02d}:00',
                'hour_decimal': float(arr_hour),
                'passengers': pax,
                'label': ship_name,
                'detail': 'Arrival',
            })

            cruise_departures.append({
                'day': day_label,
                'day_num': day_num,
                'time': f'{dep_hour:02d}:00',
                'hour_decimal': float(dep_hour),
                'passengers': pax,
                'label': ship_name,
                'detail': 'Departure',
            })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name='Flight Arrivals',
        x=[e['day'] for e in flight_arrivals],
        y=[e['hour_decimal'] for e in flight_arrivals],
        mode='markers',
        marker=dict(
            symbol='circle',
            size=[max(6, min(e['passengers'] / 30, 20)) for e in flight_arrivals],
            color='#2E86AB',
            line=dict(width=1, color='white'),
        ),
        hovertemplate='<b>%{text}</b><br>%{customdata[0]}<br>Time: %{customdata[1]}<br>Passengers: %{customdata[2]:,}<extra>Flight Arrival</extra>',
        text=[e['label'] for e in flight_arrivals],
        customdata=[[e['detail'], e['time'], e['passengers']] for e in flight_arrivals],
    ))

    fig.add_trace(go.Scatter(
        name='Flight Departures',
        x=[e['day'] for e in flight_departures],
        y=[e['hour_decimal'] for e in flight_departures],
        mode='markers',
        marker=dict(
            symbol='diamond',
            size=[max(6, min(e['passengers'] / 30, 20)) for e in flight_departures],
            color='#F18F01',
            line=dict(width=1, color='white'),
        ),
        hovertemplate='<b>%{text}</b><br>%{customdata[0]}<br>Time: %{customdata[1]}<br>Passengers: %{customdata[2]:,}<extra>Flight Departure</extra>',
        text=[e['label'] for e in flight_departures],
        customdata=[[e['detail'], e['time'], e['passengers']] for e in flight_departures],
    ))

    fig.add_trace(go.Scatter(
        name='Cruise Arrivals',
        x=[e['day'] for e in cruise_arrivals],
        y=[e['hour_decimal'] for e in cruise_arrivals],
        mode='markers',
        marker=dict(
            symbol='square',
            size=[max(10, min(e['passengers'] / 200, 30)) for e in cruise_arrivals],
            color='#A23B72',
            line=dict(width=1, color='white'),
        ),
        hovertemplate='<b>%{text}</b><br>%{customdata[0]}<br>Time: %{customdata[1]}<br>Passengers: %{customdata[2]:,}<extra>Cruise Arrival</extra>',
        text=[e['label'] for e in cruise_arrivals],
        customdata=[[e['detail'], e['time'], e['passengers']] for e in cruise_arrivals],
    ))

    fig.add_trace(go.Scatter(
        name='Cruise Departures',
        x=[e['day'] for e in cruise_departures],
        y=[e['hour_decimal'] for e in cruise_departures],
        mode='markers',
        marker=dict(
            symbol='x',
            size=[max(10, min(e['passengers'] / 200, 30)) for e in cruise_departures],
            color='#C73E1D',
            line=dict(width=1, color='white'),
        ),
        hovertemplate='<b>%{text}</b><br>%{customdata[0]}<br>Time: %{customdata[1]}<br>Passengers: %{customdata[2]:,}<extra>Cruise Departure</extra>',
        text=[e['label'] for e in cruise_departures],
        customdata=[[e['detail'], e['time'], e['passengers']] for e in cruise_departures],
    ))

    y_ticks = [h + 0.5 for h in range(0, 24, 2)]
    y_labels = [f'{h:02d}:00' for h in range(0, 24, 2)]

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Event Timeline - Arrivals & Departures by Time - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Time of Day', tickmode='array',
                   tickvals=y_ticks, ticktext=y_labels,
                   range=[-0.5, 24]),
        hovermode='closest', template='plotly_dark',
        height=500,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    for h in range(0, 24, 4):
        fig.add_hline(y=h, line_dash='dot', line_color='rgba(255,255,255,0.08)')

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_cruise_calendar(monthly_data, year=2026, month=6):
    \"\"\"Create a chart showing which cruise ships visit on which days.\"\"\"
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split(\"-\")[2])}' for d in days]

    all_ships = set()
    for d in days:
        for c in monthly_data['days'][d].get('cruises', []):
            all_ships.add(c['ship_name'])
    all_ships = sorted(all_ships)

    ship_presence = {ship: [] for ship in all_ships}
    for d in days:
        ships_today = {c['ship_name']: c['estimated_passengers']
                       for c in monthly_data['days'][d].get('cruises', [])}
        for ship in all_ships:
            if ship in ships_today:
                ship_presence[ship].append(ships_today[ship])
            else:
                ship_presence[ship].append(0)

    hover_texts = []
    for i, d in enumerate(days):
        ships_today = {c['ship_name']: c['estimated_passengers']
                       for c in monthly_data['days'][d].get('cruises', [])}
        lines = [f'<b>{day_labels[i]}</b>']
        for ship in all_ships:
            pax = ships_today.get(ship, 0)
            if pax > 0:
                lines.append(f'{ship}: {pax:,} passengers')
        hover_texts.append('<br>'.join(lines))

    fig = go.Figure()

    colors = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1 + px.colors.qualitative.Set3
    for idx, ship in enumerate(all_ships):
        fig.add_trace(go.Bar(
            name=ship,
            x=day_labels,
            y=ship_presence[ship],
            marker_color=colors[idx % len(colors)],
            showlegend=False,
            hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>' + ship + '</extra>'
        ))

    fig.add_trace(go.Scatter(
        name='hover',
        x=day_labels,
        y=[0] * len(day_labels),
        mode='markers',
        marker=dict(size=0.01, opacity=0),
        hoverinfo='text',
        hovertext=hover_texts,
        showlegend=False,
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Cruise Ship Schedule - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers', tickformat=','),
        barmode='stack', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_monthly_stats(monthly_data):
    \"\"\"Calculate monthly summary statistics.\"\"\"
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


def create_monthly_calendar_chart(monthly_data, weather_data, year=2026, month=6):
    \"\"\"Create a calendar-style heatmap showing daily visitor counts with day-of-week and weather overlay.\"\"\"
    days = sorted(monthly_data['days'].keys())
    num_days = len(days)

    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    daily_totals = []
    daily_labels = []
    daily_dow = []
    daily_weather_conditions = []
    daily_highs = []
    daily_lows = []

    base_date = datetime(year, month, 1)

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        total_in = sum(hourly[h]['total_in'] for h in range(24))
        daily_totals.append(total_in)

        day_num = int(d.split('-')[2])
        current_date = datetime(year, month, day_num)
        dow = current_date.weekday()
        daily_dow.append(day_names[dow])
        month_abbr = datetime(year, month, 1).strftime('%b')
        daily_labels.append(f'{month_abbr} {day_num}')

        w = weather_data.get(d, {})
        daily_weather_conditions.append(w.get('condition', 'N/A'))
        daily_highs.append(w.get('high_c', 30))
        daily_lows.append(w.get('low_c', 25))

    calendar_grid = []
    weather_grid = []
    temp_grid = []
    week_labels = []

    for day_num in range(1, num_days + 1):
        idx = day_num - 1

        col = (base_date.weekday() + day_num - 1) % 7
        row = (base_date.weekday() + day_num - 1) // 7

        if col == 0:
            calendar_grid.append([None] * 7)
            weather_grid.append([None] * 7)
            temp_grid.append([None] * 7)
            week_start = day_num
            week_end = min(day_num + 6, num_days)
            month_abbr = datetime(year, month, 1).strftime('%b')
            week_labels.append(f'{month_abbr} {week_start}-{week_end}')

        calendar_grid[row][col] = daily_totals[idx]
        weather_grid[row][col] = daily_weather_conditions[idx]
        temp_grid[row][col] = f'{daily_highs[idx]}C / {daily_lows[idx]}C'

    last_row = len(calendar_grid) - 1
    for col in range(len(calendar_grid[last_row])):
        if calendar_grid[last_row][col] is None:
            calendar_grid[last_row][col] = 0
            weather_grid[last_row][col] = ''
            temp_grid[last_row][col] = ''

    hover_texts = []
    for row_idx in range(len(calendar_grid)):
        row_texts = []
        for col_idx in range(7):
            day_num = row_idx * 7 + col_idx + 1 - base_date.weekday()
            if 1 <= day_num <= num_days:
                date_str = f'{year:04d}-{month:02d}-{day_num:02d}'
                w = weather_data.get(date_str, {})
                net_val = calendar_grid[row_idx][col_idx]
                month_name = datetime(year, month, 1).strftime('%B')
                text = (
                    f'<b>{month_name} {day_num}, {year}</b><br>'
                    f'<b>{daily_dow[day_num-1]}</b><br>'
                    f'New Arrivals: {net_val:,.0f}<br>'
                    f'Weather: {w.get(\"condition\", \"N/A\")}<br>'
                    f'High: {w.get(\"high_c\", \"N/A\")}C / Low: {w.get(\"low_c\", \"N/A\")}C<br>'
                    f'Humidity: {w.get(\"humidity_pct\", \"N/A\")}%<br>'
                    f'Precipitation: {w.get(\"precipitation_mm\", 0)} mm'
                )
                row_texts.append(text)
            else:
                row_texts.append('')
        hover_texts.append(row_texts)

    viridis_colors = px.colors.sequential.Viridis
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

    annotations = []
    for row_idx in range(len(calendar_grid)):
        for col_idx in range(7):
            day_num = row_idx * 7 + col_idx + 1 - base_date.weekday()
            if 1 <= day_num <= num_days:
                w = weather_data.get(f'{year:04d}-{month:02d}-{day_num:02d}', {})
                condition = w.get('condition', '')
                emoji = ''
                if 'Sunny' in condition:
                    emoji = '\\u2600\\ufe0f'
                elif 'Partly' in condition:
                    emoji = '\\u26c5'
                elif 'Showers' in condition:
                    emoji = '\\U0001f326\\ufe0f'
                elif 'Thunder' in condition:
                    emoji = '\\u26c8\\ufe0f'

                annotations.append(dict(
                    x=col_idx,
                    y=row_idx,
                    xref='x',
                    yref='y',
                    text=emoji,
                    showarrow=False,
                    font=dict(size=14),
                ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(
            text=f'<b>Monthly Calendar - Visitors & Weather - {month_label}</b>',
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
    <title>Roatan Tourism Tracker</title>
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
        .selector-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .selector-row label {
            font-size: 1em;
            color: #ccc;
        }
        .selector-row select {
            background: #1a1a2e;
            color: #e0e0e0;
            border: 1px solid #2a2a4e;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            outline: none;
        }
        .selector-row select:hover { border-color: #2E86AB; }
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
        <p class="subtitle" id="subtitleText">Real-time monitoring of tourist inflow & outflow via flights and cruise ships</p>

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
            </div