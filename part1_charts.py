"""
Part 1: Chart functions (create_combined_volume_chart through create_monthly_calendar_chart)
"""
import json
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils
import plotly.express as px
import calendar


def create_combined_volume_chart(monthly_data, year=2026, month=6):
    """Create a linear-scale chart showing daily passenger volume for flights and cruise ships on the same chart."""
    days = sorted(monthly_data['days'].keys())
    daily_in_flights = []
    daily_in_cruise = []
    daily_out_flights = []
    daily_out_cruise = []
    day_labels = []
    month_abbr = datetime(year, month, 1).strftime('%b')

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
        name='Flight Departures', x=day_labels, y=daily_out_flights,
        marker_color='#F18F01',
        hovertemplate='%{y:,.0f} departing by flight<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Arrivals', x=day_labels, y=daily_in_cruise,
        marker_color='#A23B72',
        hovertemplate='%{y:,.0f} arriving by cruise<br>%{x}<extra>Cruise Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Departures', x=day_labels, y=daily_out_cruise,
        marker_color='#C73E1D',
        hovertemplate='%{y:,.0f} departing by cruise<br>%{x}<extra>Cruise Departures</extra>'
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Daily Passenger Volume by Source - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers', type='linear', tickformat=','),
        barmode='group', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_hourly_pattern_chart(monthly_data, year=2026, month=6):
    """Create a chart showing average hourly inflow/outflow rates by source (flights vs cruise)."""
    days = sorted(monthly_data['days'].keys())
    hours = list(range(24))
    labels = [f'{h:02d}:00' for h in hours]

    avg_in_flights = [0] * 24
    avg_out_flights = [0] * 24
    avg_in_cruise = [0] * 24
    avg_out_cruise = [0] * 24

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        for h in hours:
            avg_in_flights[h] += hourly[h]['in_flights']
            avg_out_flights[h] += hourly[h]['out_flights']
            avg_in_cruise[h] += hourly[h]['in_cruise']
            avg_out_cruise[h] += hourly[h]['out_cruise']

    num_days = len(days)
    for h in hours:
        avg_in_flights[h] //= num_days
        avg_out_flights[h] //= num_days
        avg_in_cruise[h] //= num_days
        avg_out_cruise[h] //= num_days

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Flight Arrivals', x=labels, y=avg_in_flights,
        marker_color='#2E86AB',
        hovertemplate='Avg %{y:,.0f} arriving by flight<br>%{x}<extra>Flight Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Flight Departures', x=labels, y=[-x for x in avg_out_flights],
        marker_color='#F18F01',
        hovertemplate='Avg %{y:,.0f} departing by flight<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Arrivals', x=labels, y=avg_in_cruise,
        marker_color='#A23B72',
        hovertemplate='Avg %{y:,.0f} arriving by cruise<br>%{x}<extra>Cruise Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Departures', x=labels, y=[-x for x in avg_out_cruise],
        marker_color='#C73E1D',
        hovertemplate='Avg %{y:,.0f} departing by cruise<br>%{x}<extra>Cruise Departures</extra>'
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Average Hourly Flow - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=labels[::2], ticktext=labels[::2]),
        yaxis=dict(title='Avg Passengers per Hour', tickformat=','),
        barmode='relative', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=60),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )
    fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.3)

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_event_timeline_chart(monthly_data, year=2026, month=6):
    """Create a scatter plot showing each arrival/departure event with size representing passenger count."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')

    fig = go.Figure()

    all_flight_arrivals = []
    all_flight_departures = []
    all_cruise_arrivals = []
    all_cruise_departures = []

    for d in days:
        day_data = monthly_data['days'][d]
        day_num = int(d.split('-')[2])
        day_label = f'{month_abbr} {day_num}'

        for f in day_data.get('flights', []):
            h = f.get('hour', 12)
            m = f.get('minute', 0)
            time_val = h + m / 60.0
            pax = f.get('estimated_passengers', 100)
            event = dict(x=day_num, y=time_val, size=pax, label=day_label,
                        flight=f.get('flight_number', ''), aircraft=f.get('aircraft', ''),
                        origin=f.get('origin', ''))
            if f.get('is_arrival'):
                all_flight_arrivals.append(event)
            else:
                all_flight_departures.append(event)

        for c in day_data.get('cruises', []):
            arr_h = c.get('arrival_hour', 8)
            dep_h = c.get('departure_hour', 17)
            pax = c.get('estimated_passengers', 2000)
            ship = c.get('ship_name', '')
            all_cruise_arrivals.append(dict(x=day_num, y=arr_h, size=pax, label=day_label, ship=ship))
            all_cruise_departures.append(dict(x=day_num, y=dep_h, size=pax, label=day_label, ship=ship))

    # Flight arrivals
    if all_flight_arrivals:
        fig.add_trace(go.Scatter(
            name='Flight Arrivals',
            x=[e['x'] for e in all_flight_arrivals],
            y=[e['y'] for e in all_flight_arrivals],
            mode='markers',
            marker=dict(
                size=[max(6, e['size'] / 20) for e in all_flight_arrivals],
                color='#2E86AB', opacity=0.7,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>Flight Arrival</b><br>Day: %{x}<br>Time: %{y:.1f}h<br>Flight: %{customdata[0]}<br>Aircraft: %{customdata[1]}<br>Origin: %{customdata[2]}<br>Passengers: %{marker.size:.0f}<extra></extra>',
            customdata=[[e.get('flight', ''), e.get('aircraft', ''), e.get('origin', '')] for e in all_flight_arrivals]
        ))

    # Flight departures
    if all_flight_departures:
        fig.add_trace(go.Scatter(
            name='Flight Departures',
            x=[e['x'] for e in all_flight_departures],
            y=[e['y'] for e in all_flight_departures],
            mode='markers',
            marker=dict(
                size=[max(6, e['size'] / 20) for e in all_flight_departures],
                color='#F18F01', opacity=0.7,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>Flight Departure</b><br>Day: %{x}<br>Time: %{y:.1f}h<br>Flight: %{customdata[0]}<br>Aircraft: %{customdata[1]}<br>Destination: %{customdata[2]}<br>Passengers: %{marker.size:.0f}<extra></extra>',
            customdata=[[e.get('flight', ''), e.get('aircraft', ''), e.get('origin', '')] for e in all_flight_departures]
        ))

    # Cruise arrivals
    if all_cruise_arrivals:
        fig.add_trace(go.Scatter(
            name='Cruise Arrivals',
            x=[e['x'] for e in all_cruise_arrivals],
            y=[e['y'] for e in all_cruise_arrivals],
            mode='markers',
            marker=dict(
                size=[max(10, e['size'] / 100) for e in all_cruise_arrivals],
                color='#A23B72', opacity=0.7,
                symbol='square',
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>Cruise Arrival</b><br>Day: %{x}<br>Time: %{y:.0f}:00<br>Ship: %{customdata[0]}<br>Passengers: %{marker.size:.0f}<extra></extra>',
            customdata=[[e.get('ship', '')] for e in all_cruise_arrivals]
        ))

    # Cruise departures
    if all_cruise_departures:
        fig.add_trace(go.Scatter(
            name='Cruise Departures',
            x=[e['x'] for e in all_cruise_departures],
            y=[e['y'] for e in all_cruise_departures],
            mode='markers',
            marker=dict(
                size=[max(10, e['size'] / 100) for e in all_cruise_departures],
                color='#C73E1D', opacity=0.7,
                symbol='diamond',
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>Cruise Departure</b><br>Day: %{x}<br>Time: %{y:.0f}:00<br>Ship: %{customdata[0]}<br>Passengers: %{marker.size:.0f}<extra></extra>',
            customdata=[[e.get('ship', '')] for e in all_cruise_departures]
        ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Event Timeline - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Day of Month', dtick=1, tickmode='linear'),
        yaxis=dict(title='Hour of Day', tickmode='array',
                   tickvals=list(range(0, 24, 2)),
                   ticktext=[f'{h:02d}:00' for h in range(0, 24, 2)]),
        hovermode='closest', template='plotly_dark',
        height=500,
        margin=dict(l=60, r=20, t=60, b=60),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_cruise_calendar(monthly_data, year=2026, month=6):
    """Create a stacked bar chart showing cruise ship schedule for each day."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split("-")[2])}' for d in days]

    fig = go.Figure()

    # Collect all unique ship names across the month
    all_ships = set()
    for d in days:
        day_data = monthly_data['days'][d]
        for c in day_data.get('cruises', []):
            all_ships.add(c.get('ship_name', 'Unknown'))

    all_ships = sorted(all_ships)
    ship_colors = px.colors.qualitative.Set2[:len(all_ships)]
    if len(all_ships) > len(ship_colors):
        ship_colors = ship_colors * (len(all_ships) // len(ship_colors) + 1)

    # For each ship, create a trace showing passengers per day
    for idx, ship in enumerate(all_ships):
        daily_pax = []
        for d in days:
            day_data = monthly_data['days'][d]
            pax = 0
            for c in day_data.get('cruises', []):
                if c.get('ship_name') == ship:
                    pax += c.get('estimated_passengers', 0)
            daily_pax.append(pax)

        fig.add_trace(go.Bar(
            name=ship,
            x=day_labels,
            y=daily_pax,
            marker_color=ship_colors[idx],
            hovertemplate=f'<b>{ship}</b><br>%{{x}}<br>%{{y:,.0f}} passengers<extra></extra>',
            text=[f'{pax:,}' if pax > 0 else '' for pax in daily_pax],
            textposition='inside',
            textfont=dict(size=9, color='white'),
        ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Cruise Ship Schedule - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers', tickformat=','),
        barmode='stack', hovermode='x unified', template='plotly_dark',
        height=500,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                   font=dict(size=10)),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
        showlegend=True
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_monthly_stats(monthly_data):
    """Calculate monthly statistics."""
    days = sorted(monthly_data['days'].keys())
    total_flight_arrivals = 0
    total_flight_departures = 0
    total_cruise_arrivals = 0
    total_cruise_departures = 0
    total_flights = 0
    total_cruise_ships = 0
    busiest_day = ''
    busiest_count = 0

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        day_total = sum(hourly[h]['total_in'] for h in range(24))

        if day_total > busiest_count:
            busiest_count = day_total
            busiest_day = d

        for f in day_data.get('flights', []):
            total_flights += 1
            pax = f.get('estimated_passengers', 100)
            if f.get('is_arrival'):
                total_flight_arrivals += pax
            else:
                total_flight_departures += pax

        for c in day_data.get('cruises', []):
            total_cruise_ships += 1
            pax = c.get('estimated_passengers', 2000)
            if c.get('is_arrival'):
                total_cruise_arrivals += pax
            else:
                total_cruise_departures += pax

    total_arrivals = total_flight_arrivals + total_cruise_arrivals
    total_departures = total_flight_departures + total_cruise_departures

    return {
        'total_flights': total_flights,
        'total_cruise_ships': total_cruise_ships,
        'total_arrivals': total_arrivals,
        'total_departures': total_departures,
        'total_flight_arrivals': total_flight_arrivals,
        'total_flight_departures': total_flight_departures,
        'total_cruise_arrivals': total_cruise_arrivals,
        'total_cruise_departures': total_cruise_departures,
        'busiest_day': busiest_day,
        'busiest_count': busiest_count,
        'num_days': len(days),
    }


def create_monthly_calendar_chart(monthly_data, weather_data, year=2026, month=6):
    """Create a calendar heatmap showing daily arrivals with weather overlay using Viridis colorscale."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')

    # Get first day of month and number of days
    _, num_days = calendar.monthrange(year, month)
    first_weekday = datetime(year, month, 1).weekday()  # Monday=0, Sunday=6

    # Build a grid: weeks x days (7 columns)
    all_days = []
    for d in range(1, num_days + 1):
        date_str = f"{year:04d}-{month:02d}-{d:02d}"
        all_days.append(date_str)

    # Pad with empty cells for days before the 1st
    empty_prefix = first_weekday

    # Calculate total arrivals for each day
    daily_arrivals = {}
    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        total_in = sum(hourly[h]['total_in'] for h in range(24))
        daily_arrivals[d] = total_in

    # Build week rows
    weeks = []
    current_week = [None] * empty_prefix
    for d in range(1, num_days + 1):
        date_str = f"{year:04d}-{month:02d}-{d:02d}"
        arrivals = daily_arrivals.get(date_str, 0)
        current_week.append(arrivals)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    # Pad last week
    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)

    # Create heatmap
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    week_labels = [f'Week {i+1}' for i in range(len(weeks))]

    fig = go.Figure()

    # Add heatmap for arrivals
    z_data = []
    for w in weeks:
        z_data.append([v if v is not None else 0 for v in w])

    fig.add_trace(go.Heatmap(
        z=z_data,
        x=day_names,
        y=week_labels,
        colorscale=px.colors.sequential.Viridis,
        hovertemplate='<b>%{y}</b><br>%{x}<br>Arrivals: %{z:,.0f}<extra></extra>',
        colorbar=dict(title=dict(text='Arrivals', side='right'), tickformat=','),
        zmin=0,
        zmax=max(max(row) for row in z_data) if any(any(v for v in row) for row in z_data) else 1,
    ))

    # Add day numbers as annotations
    annotations = []
    for wi, w in enumerate(weeks):
        for di, v in enumerate(w):
            if v is not None:
                day_num = wi * 7 + di - empty_prefix + 1
                if 1 <= day_num <= num_days:
                    date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                    weather = weather_data.get(date_str, {})
                    temp = weather.get('temp_max', weather.get('temp', 30))
                    condition = weather.get('condition', '')
                    annotations.append(dict(
                        x=di, y=wi,
                        text=f'{day_num}<br><span style="font-size:9px;">{temp}°C</span>',
                        showarrow=False,
                        font=dict(color='white' if v and v > (max(max(row) for row in z_data) / 2) else 'black', size=11),
                        hovertext=f'{date_str}: {v:,} arrivals, {temp}°C {condition}'
                    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Monthly Calendar - {month_label}</b><br><span style="font-size:14px;color:#888;">Arrivals by day with weather</span>', font=dict(size=20)),
        template='plotly_dark',
        height=350,
        margin=dict(l=40, r=80, t=60, b=40),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
        xaxis=dict(side='top'),
        yaxis=dict(autorange='reversed'),
        annotations=annotations
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
