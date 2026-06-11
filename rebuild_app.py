#!/usr/bin/env python3
"""Rebuild app.py by reading the truncated file and appending the missing parts."""
import sys

# Read the current truncated file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the truncation point - the incomplete fig.add_trace line
cutoff = content.rfind('    fig.add_trace')
if cutoff > 0:
    content = content[:cutoff]

# Now append the complete remaining content
# We'll write it as a separate file and concatenate
remaining = []
remaining.append('''    fig.add_trace(go.Bar(
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
''')

# Write the remaining content to a temp file
with open('_remaining.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(remaining))

print("Part 1 written successfully")
print(f"Content length: {len(content)}")
print(f"Remaining length: {sum(len(r) for r in remaining)}")
