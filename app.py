"""
Tourism Tracker - Web Application
Flask app showing inflow/outflow of tourists by flights and cruise ships
for Roatan, Honduras. Shows data over multiple months (Jun 2026 - Nov 2028).
"""

from flask import Flask, render_template_string, jsonify, request
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
import plotly.express as px
import pandas as pd
import numpy as np
from scraper import collect_all_data, get_aircraft_capacity, get_cruise_ship_capacity, LOAD_FACTOR, generate_monthly_data, get_weather_data
import calendar

app = Flask(__name__)

# Roatan island areas for heatmap
ROATAN_AREAS = {
    'West End / West Bay': {'lat': 16.3000, 'lon': -86.6000, 'weight': 0.35},
    'Coxen Hole': {'lat': 16.3167, 'lon': -86.5333, 'weight': 0.25},
    'French Harbour': {'lat': 16.3333, 'lon': -86.4667, 'weight': 0.15},
    'Oak Ridge': {'lat': 16.3500, 'lon': -86.4167, 'weight': 0.10},
    'Punta Gorda': {'lat': 16.3667, 'lon': -86.3667, 'weight': 0.05},
    'Sandy Bay': {'lat': 16.3167, 'lon': -86.5667, 'weight': 0.10},
}

# Cruise port locations
CRUISE_PORTS = {
    'Town Center': {'lat': 16.3167, 'lon': -86.5333, 'weight': 0.6},
    'Mahogany Bay': {'lat': 16.3000, 'lon': -86.5000, 'weight': 0.4},
}

# Airport location
AIRPORT_LOC = {'lat': 16.3167, 'lon': -86.5167}


# Available months for the dashboard (Jun 2026 - Nov 2028)
AVAILABLE_MONTHS = []
for y in range(2026, 2029):
    start_m = 6 if y == 2026 else 1
    end_m = 12 if y < 2028 else 11
    for m in range(start_m, end_m + 1):
        AVAILABLE_MONTHS.append((y, m))


def get_month_label(year, month):
    """Get a human-readable label for a year/month."""
    return datetime(year, month, 1).strftime('%B %Y')


def get_month_abbr(year, month):
    """Get abbreviated month string for URL construction."""
    return datetime(year, month, 1).strftime('%b').lower()


def get_month_key(year, month):
    """Get a unique key string for a year/month."""
    return f"{year:04d}-{month:02d}"


def load_monthly_data(year=2026, month=6):
    """Load monthly data from JSON file or generate fresh for a specific year/month."""
    data_file = f'tourism_{year:04d}_{month:02d}.json'
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            if data.get('days') and len(data['days']) >= 28:
                return data
        except:
            pass
    # Generate fresh monthly data
    data = generate_monthly_data(year, month)
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def process_daily_data(day_data):
    """Process a single day's data into hourly inflow/outflow counts."""
    hourly = {h: {'in_flights': 0, 'out_flights': 0, 'in_cruise': 0, 'out_cruise': 0,
                   'total_in': 0, 'total_out': 0} for h in range(24)}

    # Process flights
    for f in day_data.get('flights', []):
        h = f.get('hour', 12)
        pax = f.get('estimated_passengers', 100)
        if f.get('is_arrival'):
            hourly[h]['in_flights'] += pax
            hourly[h]['total_in'] += pax
        else:
            hourly[h]['out_flights'] += pax
            hourly[h]['total_out'] += pax

    # Process cruise ships
    for c in day_data.get('cruises', []):
        arr_h = c.get('arrival_hour', 8)
        dep_h = c.get('departure_hour', 17)
        pax = c.get('estimated_passengers', 2000)

        # Cruise passengers arrive over a 2-hour window
        for dh in range(2):
            h = (arr_h + dh) % 24
            hourly[h]['in_cruise'] += pax // 2
            hourly[h]['total_in'] += pax // 2

        # Cruise passengers depart over a 2-hour window
        for dh in range(2):
            h = (dep_h + dh) % 24
            hourly[h]['out_cruise'] += pax // 2
            hourly[h]['total_out'] += pax // 2

    return hourly


def create_daily_hourly_chart(hourly_data, date_str, filter_mode='all'):
    """Create hourly inflow/outflow bar chart for a single day.
    filter_mode: 'all', 'flights', or 'cruises'"""
    hours = list(range(24))
    labels = [f'{h:02d}:00' for h in hours]

    in_flights = [hourly_data[h]['in_flights'] for h in hours]
    out_flights = [hourly_data[h]['out_flights'] for h in hours]
    in_cruise = [hourly_data[h]['in_cruise'] for h in hours]
    out_cruise = [hourly_data[h]['out_cruise'] for h in hours]

    fig = go.Figure()

    show_flights = filter_mode in ('all', 'flights')
    show_cruises = filter_mode in ('all', 'cruises')

    if show_flights:
        fig.add_trace(go.Bar(
            name='Flight Arrivals', x=labels, y=in_flights,
            marker_color='#2E86AB',
            hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Flight Arrivals</extra>'
        ))
        fig.add_trace(go.Bar(
            name='Flight Departures', x=labels, y=[-x for x in out_flights],
            marker_color='#F18F01',
            hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Flight Departures</extra>'
        ))

    if show_cruises:
        fig.add_trace(go.Bar(
            name='Cruise Arrivals', x=labels, y=in_cruise,
            marker_color='#A23B72',
            hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Cruise Arrivals</extra>'
        ))
        fig.add_trace(go.Bar(
            name='Cruise Departures', x=labels, y=[-x for x in out_cruise],
            marker_color='#C73E1D',
            hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Cruise Departures</extra>'
        ))

    # Net inflow line
    if show_flights and show_cruises:
        net = [hourly_data[h]['total_in'] - hourly_data[h]['total_out'] for h in hours]
        net_name = 'Net Inflow'
    elif show_flights:
        net = [hourly_data[h]['in_flights'] - hourly_data[h]['out_flights'] for h in hours]
        net_name = 'Net Flight Flow'
    elif show_cruises:
        net = [hourly_data[h]['in_cruise'] - hourly_data[h]['out_cruise'] for h in hours]
        net_name = 'Net Cruise Flow'
    else:
        net = [0] * 24
        net_name = 'Net'

    fig.add_trace(go.Scatter(
        name=net_name, x=labels, y=net,
        mode='lines+markers', line=dict(color='#2ECC40', width=3),
        marker=dict(size=8),
        hovertemplate='Net: %{y:+,.0f} passengers<br>%{x}<extra></extra>'
    ))

    if filter_mode == 'all':
        subtitle = 'All Traffic'
    elif filter_mode == 'flights':
        subtitle = 'Flights Only'
    else:
        subtitle = 'Cruises Only'

    fig.update_layout(
        title=dict(text=f'<b>Hourly Tourist Flow - {date_str}</b><br><span style="font-size:14px;color:#888;">{subtitle}</span>', font=dict(size=18)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=labels[::2], ticktext=labels[::2]),
        yaxis=dict(title='Number of Passengers', tickformat=','),
        barmode='relative', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=60),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )
    fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.3)

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_flight_traffic_chart(monthly_data, year=2026, month=6):
    """Create a daily bar chart showing flight inflow/outflow across the whole month."""
    days = sorted(monthly_data['days'].keys())
    daily_in = []
    daily_out = []
    daily_net = []
    day_labels = []
    month_abbr = datetime(year, month, 1).strftime('%b')

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        in_f = sum(hourly[h]['in_flights'] for h in range(24))
        out_f = sum(hourly[h]['out_flights'] for h in range(24))
        daily_in.append(in_f)
        daily_out.append(out_f)
        daily_net.append(in_f - out_f)
        day_num = int(d.split('-')[2])
        day_labels.append(f'{month_abbr} {day_num}')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Arrivals', x=day_labels, y=daily_in,
        marker_color='#2E86AB',
        hovertemplate='%{y:,.0f} arriving by flight<br>%{x}<extra>Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Departures', x=day_labels, y=daily_out,
        marker_color='#F18F01',
        hovertemplate='%{y:,.0f} departing by flight<br>%{x}<extra>Departures</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Net', x=day_labels, y=daily_net,
        mode='lines+markers', line=dict(color='#2ECC40', width=3),
        marker=dict(size=6),
        hovertemplate='Net: %{y:+,.0f}<br>%{x}<extra></extra>'
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Flight Traffic - {month_label}</b>', font=dict(size=20)),
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


def create_cruise_traffic_chart(monthly_data, year=2026, month=6):
    """Create a daily bar chart showing cruise inflow/outflow across the whole month."""
    days = sorted(monthly_data['days'].keys())
    daily_in = []
    daily_out = []
    daily_net = []
    day_labels = []
    month_abbr = datetime(year, month, 1).strftime('%b')

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        in_c = sum(hourly[h]['in_cruise'] for h in range(24))
        out_c = sum(hourly[h]['out_cruise'] for h in range(24))
        daily_in.append(in_c)
        daily_out.append(out_c)
        daily_net.append(in_c - out_c)
        day_num = int(d.split('-')[2])
        day_labels.append(f'{month_abbr} {day_num}')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Arrivals', x=day_labels, y=daily_in,
        marker_color='#A23B72',
        hovertemplate='%{y:,.0f} arriving by cruise<br>%{x}<extra>Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Departures', x=day_labels, y=daily_out,
        marker_color='#C73E1D',
        hovertemplate='%{y:,.0f} departing by cruise<br>%{x}<extra>Departures</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Net', x=day_labels, y=daily_net,
        mode='lines+markers', line=dict(color='#2ECC40', width=3),
        marker=dict(size=6),
        hovertemplate='Net: %{y:+,.0f}<br>%{x}<extra></extra>'
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Cruise Ship Traffic - {month_label}</b>', font=dict(size=20)),
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


def create_monthly_heatmap(monthly_data, year=2026, month=6):
    """Create a calendar heatmap showing tourist density across days and hours."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split("-")[2])}' for d in days]

    heatmap_z = []
    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        cumulative = 0
        row = []
        for h in range(24):
            cumulative += hourly[h]['total_in'] - hourly[h]['total_out']
            if cumulative < 0:
                cumulative = 0
            row.append(cumulative)
        heatmap_z.append(row)

    hours = [f'{h:02d}:00' for h in range(24)]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=heatmap_z,
        x=hours,
        y=day_labels,
        colorscale=[
            [0, '#1a1a2e'], [0.2, '#16213e'], [0.4, '#0f3460'],
            [0.6, '#e94560'], [0.8, '#f5a623'], [1, '#ffd700']
        ],
        hovertemplate='<b>%{y}</b><br>Hour: %{x}<br>Tourists: %{z:,.0f}<extra></extra>',
        colorbar=dict(title=dict(text='Tourists on Island', side='right'), tickformat=',')
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Tourist Density Calendar - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=hours[::3], ticktext=hours[::3]),
        yaxis=dict(title='Date', autorange='reversed'),
        template='plotly_dark', height=600,
        margin=dict(l=80, r=80, t=60, b=80),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_log_scale_chart(monthly_data, year=2026, month=6):
    """Create a linear-scale chart showing daily passenger volumes."""
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

    fig.add_trace(go.Scatter(
        name='Flight Arrivals', x=day_labels, y=daily_in_flights,
        mode='lines+markers', line=dict(color='#2E86AB', width=2),
        marker=dict(size=6, symbol='circle'),
        hovertemplate='%{y:,.0f} arriving by flight<br>%{x}<extra>Flight Arrivals</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Cruise Arrivals', x=day_labels, y=daily_in_cruise,
        mode='lines+markers', line=dict(color='#A23B72', width=2),
        marker=dict(size=6, symbol='square'),
        hovertemplate='%{y:,.0f} arriving by cruise<br>%{x}<extra>Cruise Arrivals</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Flight Departures', x=day_labels, y=daily_out_flights,
        mode='lines+markers', line=dict(color='#F18F01', width=2),
        marker=dict(size=6, symbol='diamond'),
        hovertemplate='%{y:,.0f} departing by flight<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Scatter(
        name='Cruise Departures', x=day_labels, y=daily_out_cruise,
        mode='lines+markers', line=dict(color='#C73E1D', width=2),
        marker=dict(size=6, symbol='x'),
        hovertemplate='%{y:,.0f} departing by cruise<br>%{x}<extra>Cruise Departures</extra>'
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Daily Passenger Volume (Linear Scale) - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers', type='linear', tickformat=','),
        hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_origin_pie_chart(monthly_data, year=2026, month=6):
    """Create a pie chart showing tourist origin breakdown from flight origins and cruise line data."""
    airport_regions = {
        'MIA': 'United States', 'FLL': 'United States', 'IAH': 'United States',
        'ATL': 'United States', 'HOU': 'United States', 'TEB': 'United States',
        'PTY': 'Latin America / Other', 'SAL': 'Latin America / Other',
        'RTB': 'Latin America / Other',
    }

    cruise_composition = {
        'Carnival': {'United States': 0.85, 'Canada': 0.07, 'United Kingdom / Europe': 0.03, 'Latin America / Other': 0.05},
        'Royal Caribbean': {'United States': 0.78, 'Canada': 0.10, 'United Kingdom / Europe': 0.07, 'Latin America / Other': 0.05},
        'Norwegian': {'United States': 0.75, 'Canada': 0.12, 'United Kingdom / Europe': 0.08, 'Latin America / Other': 0.05},
        'MSC': {'United States': 0.55, 'Canada': 0.08, 'United Kingdom / Europe': 0.28, 'Latin America / Other': 0.09},
        'Princess': {'United States': 0.80, 'Canada': 0.09, 'United Kingdom / Europe': 0.06, 'Latin America / Other': 0.05},
    }

    ship_to_line = {}
    for ship_name in [
        'Carnival Magic', 'Carnival Vista',
        'Royal Caribbean Harmony of the Seas', 'Royal Caribbean Oasis of the Seas',
        'Norwegian Bliss', 'Norwegian Epic',
        'MSC Seaside', 'MSC Meraviglia',
        'Princess Royal',
        'Celebrity Edge', 'Celebrity Apex', 'Disney Fantasy',
        'Holland America Nieuw Amsterdam', 'Costa Smeralda', 'AIDAnova'
    ]:
        if 'Carnival' in ship_name:
            ship_to_line[ship_name] = 'Carnival'
        elif 'Royal Caribbean' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'
        elif 'Norwegian' in ship_name:
            ship_to_line[ship_name] = 'Norwegian'
        elif 'MSC' in ship_name:
            ship_to_line[ship_name] = 'MSC'
        elif 'Princess' in ship_name:
            ship_to_line[ship_name] = 'Princess'
        elif 'Celebrity' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'
        elif 'Disney' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'
        elif 'Holland America' in ship_name:
            ship_to_line[ship_name] = 'Princess'
        elif 'Costa' in ship_name:
            ship_to_line[ship_name] = 'MSC'
        elif 'AIDA' in ship_name:
            ship_to_line[ship_name] = 'MSC'
        else:
            ship_to_line[ship_name] = 'Royal Caribbean'

    region_totals = {
        'United States': 0,
        'Canada': 0,
        'United Kingdom / Europe': 0,
        'Latin America / Other': 0,
    }

    days = sorted(monthly_data['days'].keys())
    for d in days:
        day_data = monthly_data['days'][d]

        for f in day_data.get('flights', []):
            if f.get('is_arrival'):
                origin = f.get('origin', '')
                pax = f.get('estimated_passengers', 100)
                region = airport_regions.get(origin, 'Latin America / Other')
                region_totals[region] += pax

        for c in day_data.get('cruises', []):
            ship_name = c.get('ship_name', '')
            pax = c.get('estimated_passengers', 2000)
            line = ship_to_line.get(ship_name, 'Royal Caribbean')
            comp = cruise_composition.get(line, cruise_composition['Royal Caribbean'])
            for region, fraction in comp.items():
                region_totals[region] += int(pax * fraction)

    labels = []
    values = []
    colors = ['#2E86AB', '#F18F01', '#A23B72', '#2ECC40']
    for region, color in zip(['United States', 'Canada', 'United Kingdom / Europe', 'Latin America / Other'], colors):
        if region_totals[region] > 0:
            labels.append(region)
            values.append(region_totals[region])

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors[:len(labels)]),
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} tourists<br>%{percent}<extra></extra>',
        pull=[0.05 if v == max(values) else 0 for v in values],
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Tourist Origin Breakdown - {month_label}</b>', font=dict(size=20)),
        template='plotly_dark',
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
        showlegend=False,
        annotations=[dict(
            text=f"Based on flight origins & cruise line demographics",
            x=0.5, y=-0.15, showarrow=False,
            font=dict(size=11, color='#888')
        )]
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_origin_inflow_chart(monthly_data, year=2026, month=6):
    """Create a multi-line chart showing daily inflows broken down by origin region."""
    airport_regions = {
        'MIA': 'United States', 'FLL': 'United States', 'IAH': 'United States',
        'ATL': 'United States', 'HOU': 'United States', 'TEB': 'United States',
        'PTY': 'Latin America / Other', 'SAL': 'Latin America / Other',
        'RTB': 'Latin America / Other',
    }

    cruise_composition = {
        'Carnival': {'United States': 0.85, 'Canada': 0.07, 'United Kingdom / Europe': 0.03, 'Latin America / Other': 0.05},
        'Royal Caribbean': {'United States': 0.78, 'Canada': 0.10, 'United Kingdom / Europe': 0.07, 'Latin America / Other': 0.05},
        'Norwegian': {'United States': 0.75, 'Canada': 0.12, 'United Kingdom / Europe': 0.08, 'Latin America / Other': 0.05},
        'MSC': {'United States': 0.55, 'Canada': 0.08, 'United Kingdom / Europe': 0.28, 'Latin America / Other': 0.09},
        'Princess': {'United States': 0.80, 'Canada': 0.09, 'United Kingdom / Europe': 0.06, 'Latin America / Other': 0.05},
    }

    ship_to_line = {}
    for ship_name in [
        'Carnival Magic', 'Carnival Vista',
        'Royal Caribbean Harmony of the Seas', 'Royal Caribbean Oasis of the Seas',
        'Norwegian Bliss', 'Norwegian Epic',
        'MSC Seaside', 'MSC Meraviglia',
        'Princess Royal',
        'Celebrity Edge', 'Celebrity Apex', 'Disney Fantasy',
        'Holland America Nieuw Amsterdam', 'Costa Smeralda', 'AIDAnova'
    ]:
        if 'Carnival' in ship_name:
            ship_to_line[ship_name] = 'Carnival'
        elif 'Royal Caribbean' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'
        elif 'Norwegian' in ship_name:
            ship_to_line[ship_name] = 'Norwegian'
        elif 'MSC' in ship_name:
            ship_to_line[ship_name] = 'MSC'
        elif 'Princess' in ship_name:
            ship_to_line[ship_name] = 'Princess'
        elif 'Celebrity' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'
        elif 'Disney' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'
        elif 'Holland America' in ship_name:
            ship_to_line[ship_name] = 'Princess'
        elif 'Costa' in ship_name:
            ship_to_line[ship_name] = 'MSC'
        elif 'AIDA' in ship_name:
            ship_to_line[ship_name] = 'MSC'
        else:
            ship_to_line[ship_name] = 'Royal Caribbean'

    regions = ['United States', 'Canada', 'United Kingdom / Europe', 'Latin America / Other']
    region_colors = {'United States': '#2E86AB', 'Canada': '#F18F01',
                     'United Kingdom / Europe': '#A23B72', 'Latin America / Other': '#2ECC40'}

    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split("-")[2])}' for d in days]

    daily_by_region = {r: [] for r in regions}

    for d in days:
        day_data = monthly_data['days'][d]
        region_totals = {r: 0 for r in regions}

        for f in day_data.get('flights', []):
            if f.get('is_arrival'):
                origin = f.get('origin', '')
                pax = f.get('estimated_passengers', 100)
                region = airport_regions.get(origin, 'Latin America / Other')
                region_totals[region] += pax

        for c in day_data.get('cruises', []):
            ship_name = c.get('ship_name', '')
            pax = c.get('estimated_passengers', 2000)
            line = ship_to_line.get(ship_name, 'Royal Caribbean')
            comp = cruise_composition.get(line, cruise_composition['Royal Caribbean'])
            for region, fraction in comp.items():
                region_totals[region] += int(pax * fraction)

        for r in regions:
            daily_by_region[r].append(region_totals[r])

    fig = go.Figure()

    for region in regions:
        fig.add_trace(go.Scatter(
            name=region,
            x=day_labels,
            y=daily_by_region[region],
            mode='lines+markers',
            line=dict(color=region_colors[region], width=3),
            marker=dict(size=6),
            hovertemplate='%{y:,.0f} arriving<br>%{x}<extra>' + region + '</extra>'
        ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Daily Inflow by Origin Region - {month_label}</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Incoming Passengers', tickformat=','),
        hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

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


def load_cruise_itinerary_data():
    """Load enriched cruise itinerary data from public/data/cruise-ships-today.json."""
    itinerary_file = os.path.join('public', 'data', 'cruise-ships-today.json')
    if os.path.exists(itinerary_file):
        try:
            with open(itinerary_file, 'r') as f:
                data = json.load(f)
            return data.get('shipsInPort', [])
        except:
            return []
    return []


def enrich_cruise_with_itinerary(cruise_entry, itinerary_data, cruise_date=None):
    """Enrich cruise entry with segment and pricing data from itinerary_data.

    IMPORTANT: Does NOT overwrite previous_ports and next_ports if they already exist.
    The JSON files contain the correct dated ports for each specific sailing, which must
    be preserved. This function only adds marketing/pricing enrichment.
    """
    ship_name = cruise_entry.get('ship_name', '').lower()
    for ship in itinerary_data:
        if ship['shipName'].lower() == ship_name:
            # Only enrich with segment, price, and marketing info
            # DO NOT overwrite ports - use the dated ports from the JSON files
            cruise_entry['segment'] = ship.get('segment', '')
            cruise_entry['avg_price'] = ship.get('avgPrice', 0)
            cruise_entry['marketing_notes'] = ship.get('marketingNotes', '')
            cruise_entry['price_range'] = ship.get('priceRange', {})
            return cruise_entry
    return cruise_entry


def create_event_timeline_chart(monthly_data, year=2026, month=6):
    """Create a scatter plot showing each arrival/departure event with size representing passenger count."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')

    # Load itinerary data for enrichment
    itinerary_data = load_cruise_itinerary_data()

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
            # Enrich with itinerary data (pass cruise date for date-based matching)
            c = enrich_cruise_with_itinerary(c, itinerary_data, cruise_date=d)
            prev_ports = c.get('previous_ports', [])
            next_ports = c.get('next_ports', [])
            segment = c.get('segment', '')
            avg_price = c.get('avg_price', 0)
            prev_str = ' → '.join(prev_ports) if prev_ports else 'N/A'
            next_str = ' → '.join(next_ports) if next_ports else 'N/A'
            all_cruise_arrivals.append(dict(x=day_num, y=arr_h, size=pax, label=day_label, ship=ship,
                                           prev=prev_str, next=next_str, seg=segment, price=avg_price))
            all_cruise_departures.append(dict(x=day_num, y=dep_h, size=pax, label=day_label, ship=ship,
                                            prev=prev_str, next=next_str, seg=segment, price=avg_price))

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
            hovertemplate='<b>Flight Arrival</b><br>Day: %{x}<br>Time: %{y:.1f}h<br>Flight: %{customdata[0]}<br>Aircraft: %{customdata[1]}<br>Origin: %{customdata[2]}<br>Passengers: %{customdata[3]}<extra></extra>',
            customdata=[[e.get('flight', ''), e.get('aircraft', ''), e.get('origin', ''), e.get('size', 0)] for e in all_flight_arrivals]
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
            hovertemplate='<b>Flight Departure</b><br>Day: %{x}<br>Time: %{y:.1f}h<br>Flight: %{customdata[0]}<br>Aircraft: %{customdata[1]}<br>Destination: %{customdata[2]}<br>Passengers: %{customdata[3]}<extra></extra>',
            customdata=[[e.get('flight', ''), e.get('aircraft', ''), e.get('origin', ''), e.get('size', 0)] for e in all_flight_departures]
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
            hovertemplate='<b>Cruise Arrival</b><br>Day: %{x}<br>Time: %{y:.0f}:00<br>Ship: %{customdata[0]}<br>Passengers: %{customdata[1]}<br>Previous: %{customdata[2]}<br>Next: %{customdata[3]}<br>Segment: %{customdata[4]}<br>Avg Price: $%{customdata[5]}<extra></extra>',
            customdata=[[e.get('ship', ''), e.get('size', 0), e.get('prev', 'N/A'), e.get('next', 'N/A'), e.get('seg', ''), e.get('price', 0)] for e in all_cruise_arrivals]
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
            hovertemplate='<b>Cruise Departure</b><br>Day: %{x}<br>Time: %{y:.0f}:00<br>Ship: %{customdata[0]}<br>Passengers: %{customdata[1]}<br>Previous: %{customdata[2]}<br>Next: %{customdata[3]}<br>Segment: %{customdata[4]}<br>Avg Price: $%{customdata[5]}<extra></extra>',
            customdata=[[e.get('ship', ''), e.get('size', 0), e.get('prev', 'N/A'), e.get('next', 'N/A'), e.get('seg', ''), e.get('price', 0)] for e in all_cruise_departures]
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


def create_airport_heatmap(monthly_data, year=2026, month=6):
    """Create a heatmap showing flight passenger volume at the airport by day and hour."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split("-")[2])}' for d in days]

    # Build a 2D grid: days x hours, values = total flight passengers (arrivals + departures)
    z_data = []
    for d in days:
        day_data = monthly_data['days'][d]
        row = [0] * 24
        for f in day_data.get('flights', []):
            h = f.get('hour', 12)
            pax = f.get('estimated_passengers', 100)
            row[h] += pax
        z_data.append(row)

    hours = [f'{h:02d}:00' for h in range(24)]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=z_data,
        x=hours,
        y=day_labels,
        colorscale='Viridis',
        hovertemplate='<b>%{y}</b><br>Time: %{x}<br>Flight Passengers: %{z:,.0f}<extra>Airport</extra>',
        colorbar=dict(title=dict(text='Passengers', side='right'), tickformat=',')
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Airport Traffic Heatmap - {month_label}</b><br><span style="font-size:14px;color:#888;">Flight arrivals & departures by time and date</span>', font=dict(size=20)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=hours[::2], ticktext=hours[::2]),
        yaxis=dict(title='Date', autorange='reversed'),
        template='plotly_dark', height=500,
        margin=dict(l=80, r=80, t=60, b=80),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_cruise_port_heatmap(monthly_data, year=2026, month=6):
    """Create a heatmap showing cruise passenger volume at the port by day and hour."""
    days = sorted(monthly_data['days'].keys())
    month_abbr = datetime(year, month, 1).strftime('%b')
    day_labels = [f'{month_abbr} {int(d.split("-")[2])}' for d in days]

    # Build a 2D grid: days x hours, values = total cruise passengers (arrivals + departures)
    z_data = []
    for d in days:
        day_data = monthly_data['days'][d]
        row = [0] * 24
        for c in day_data.get('cruises', []):
            arr_h = c.get('arrival_hour', 8)
            dep_h = c.get('departure_hour', 17)
            pax = c.get('estimated_passengers', 2000)
            # Spread cruise passengers over arrival and departure hours
            row[arr_h] += pax
            row[dep_h] += pax
        z_data.append(row)

    hours = [f'{h:02d}:00' for h in range(24)]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=z_data,
        x=hours,
        y=day_labels,
        colorscale='Plasma',
        hovertemplate='<b>%{y}</b><br>Time: %{x}<br>Cruise Passengers: %{z:,.0f}<extra>Cruise Port</extra>',
        colorbar=dict(title=dict(text='Passengers', side='right'), tickformat=',')
    ))

    month_label = datetime(year, month, 1).strftime('%B %Y')
    fig.update_layout(
        title=dict(text=f'<b>Cruise Port Traffic Heatmap - {month_label}</b><br><span style="font-size:14px;color:#888;">Cruise arrivals & departures by time and date</span>', font=dict(size=20)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=hours[::2], ticktext=hours[::2]),
        yaxis=dict(title='Date', autorange='reversed'),
        template='plotly_dark', height=500,
        margin=dict(l=80, r=80, t=60, b=80),
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
                    temp = weather.get('high_c', 30)
                    condition = weather.get('condition', '')
                    annotations.append(dict(
                        x=di, y=wi,
                        text=f'{day_num}<br><span style="font-size:9px;">{temp}Â°C</span>',
                        showarrow=False,
                        font=dict(color='white' if v and v > (max(max(row) for row in z_data) / 2) else 'black', size=11),
                        hovertext=f'{date_str}: {v:,} arrivals, {temp}Â°C {condition}'
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


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L2LFYE0L4B"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-L2LFYE0L4B');
    </script>
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
    <div class="chart-grid">
        <div id="airportHeatmap" class="chart-card"></div>
        <div id="cruisePortHeatmap" class="chart-card"></div>
    </div>
    <div id="cruiseCalendar" class="chart-full chart-card"></div>
    <div id="cruiseScheduleTable" class="chart-full chart-card">
        <h3 style="color:#A23B72;font-size:18px;margin-bottom:12px;">🚢 Monthly Cruise Schedule — Previous Stops → Roatan → Next Stops</h3>
        <div id="cruiseScheduleContent" style="overflow-x:auto;">
            <div class="loading">Loading cruise schedule...</div>
        </div>
    </div>
    <div id="cruiseItineraryPanel" class="chart-full chart-card" style="display:none;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <h3 style="color:#A23B72;font-size:18px;">🚢 Cruise Itinerary Details</h3>
            <button onclick="document.getElementById('cruiseItineraryPanel').style.display='none'" style="background:none;border:none;color:#8b949e;font-size:20px;cursor:pointer;">✕</button>
        </div>
        <div id="cruiseItineraryContent"></div>
    </div>

    <script>
        let currentFilter = 'all';
        let currentDate = '{{ selected_date }}';
        let currentYear = {{ selected_year }};
        let currentMonth = {{ selected_month }};
        let cruiseItineraryCache = null;

        // Load cruise itinerary data on page load
        fetch('/api/cruise-itineraries')
            .then(r => r.json())
            .then(data => {
                cruiseItineraryCache = data.shipsInPort || [];
            })
            .catch(() => {});

        function showCruiseItinerary(shipName, dateStr) {
            const panel = document.getElementById('cruiseItineraryPanel');
            const content = document.getElementById('cruiseItineraryContent');
            
            // Find ship in cache
            let shipData = null;
            if (cruiseItineraryCache) {
                shipData = cruiseItineraryCache.find(s => 
                    s.shipName.toLowerCase() === shipName.toLowerCase()
                );
            }
            
            if (!shipData) {
                content.innerHTML = '<div style="color:#8b949e;">No itinerary data available for <strong>' + shipName + '</strong> on ' + dateStr + '.</div>';
                panel.style.display = 'block';
                return;
            }
            
            const prevPorts = shipData.previousPorts || [];
            const nextPorts = shipData.nextPorts || [];
            const priceRange = shipData.priceRange || {};
            const segment = shipData.segment || 'N/A';
            const marketingNotes = shipData.marketingNotes || '';
            
            const segmentColors = {
                'Budget': '#2ECC40',
                'Mid-range': '#F18F01',
                'Premium': '#A23B72',
                'Luxury': '#FFD700'
            };
            const segColor = segmentColors[segment] || '#8b949e';
            
            content.innerHTML = `
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                    <div>
                        <h4 style="color:#e0e0e0;margin-bottom:8px;">📍 Route</h4>
                        <div style="background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;">
                            <div style="color:#8b949e;font-size:12px;margin-bottom:4px;">Previous Ports</div>
                            <div style="color:#e0e0e0;">${prevPorts.length ? prevPorts.join(' → ') : 'N/A'}</div>
                            <div style="color:#A23B72;text-align:center;margin:8px 0;font-size:18px;">⬇ Roatan ⬇</div>
                            <div style="color:#8b949e;font-size:12px;margin-bottom:4px;">Next Ports</div>
                            <div style="color:#e0e0e0;">${nextPorts.length ? nextPorts.join(' → ') : 'N/A'}</div>
                        </div>
                    </div>
                    <div>
                        <h4 style="color:#e0e0e0;margin-bottom:8px;">💰 Pricing & Segment</h4>
                        <div style="background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                                <span style="color:#8b949e;">Inside:</span>
                                <span style="color:#e0e0e0;">$${priceRange.inside || 'N/A'}</span>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                                <span style="color:#8b949e;">Oceanview:</span>
                                <span style="color:#e0e0e0;">$${priceRange.oceanview || 'N/A'}</span>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                                <span style="color:#8b949e;">Balcony:</span>
                                <span style="color:#e0e0e0;">$${priceRange.balcony || 'N/A'}</span>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                                <span style="color:#8b949e;">Suite:</span>
                                <span style="color:#e0e0e0;">$${priceRange.suite || 'N/A'}</span>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-top:8px;padding-top:8px;border-top:1px solid #30363d;">
                                <span style="color:#8b949e;">Segment:</span>
                                <span style="color:${segColor};font-weight:bold;">${segment}</span>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-top:4px;">
                                <span style="color:#8b949e;">Avg Price:</span>
                                <span style="color:#e0e0e0;">$${(shipData.avgPrice || 0).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
                ${marketingNotes ? `
                <div style="margin-top:12px;background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;">
                    <div style="color:#8b949e;font-size:12px;margin-bottom:4px;">📋 Marketing Notes</div>
                    <div style="color:#e0e0e0;font-size:14px;">${marketingNotes}</div>
                </div>` : ''}
            `;
            panel.style.display = 'block';
        }

        function loadCruiseSchedule() {
            const content = document.getElementById('cruiseScheduleContent');
            content.innerHTML = '<div class="loading">Loading cruise schedule...</div>';

            fetch('/api/cruise-schedule?year=' + currentYear + '&month=' + currentMonth)
                .then(r => r.json())
                .then(data => {
                    const cruises = data.cruises || [];
                    if (cruises.length === 0) {
                        content.innerHTML = '<div style="color:#8b949e;text-align:center;padding:20px;">No cruise ships scheduled for this month.</div>';
                        return;
                    }

                    let html = '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
                    html += '<thead><tr style="background:#0d1117;border-bottom:2px solid #30363d;">';
                    html += '<th style="padding:8px 6px;text-align:left;color:#8b949e;">Date</th>';
                    html += '<th style="padding:8px 6px;text-align:left;color:#8b949e;">Ship Name</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Prev 4</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Prev 3</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Prev 2</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Prev 1</th>';
                    html += '<th style="padding:8px 10px;text-align:center;background:#A23B72;color:white;font-weight:bold;">★ ROATAN ★</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Next 1</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Next 2</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Next 3</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Next 4</th>';
                    html += '<th style="padding:8px 6px;text-align:right;color:#8b949e;">Passengers</th>';
                    html += '<th style="padding:8px 6px;text-align:center;color:#8b949e;">Segment</th>';
                    html += '<th style="padding:8px 6px;text-align:right;color:#8b949e;">Avg Price</th>';
                    html += '</tr></thead><tbody>';

                    cruises.forEach((c, idx) => {
                        const bgColor = idx % 2 === 0 ? '#161b22' : '#1a1f2e';
                        const dateObj = new Date(c.date + 'T12:00:00');
                        const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                        const arrH = c.arrival_hour !== undefined ? c.arrival_hour.toString().padStart(2, '0') + ':00' : '--';
                        const depH = c.departure_hour !== undefined ? c.departure_hour.toString().padStart(2, '0') + ':00' : '--';
                        const pax = (c.estimated_passengers || 0).toLocaleString();
                        const price = c.avg_price ? '$' + c.avg_price.toLocaleString() : 'N/A';
                        const segment = c.segment || 'N/A';

                        const segmentColors = {
                            'Budget': '#2ECC40',
                            'Mid-range': '#F18F01',
                            'Premium': '#A23B72',
                            'Luxury': '#FFD700'
                        };
                        const segColor = segmentColors[segment] || '#8b949e';

                        function portCell(port) {
                            if (!port) return '<td style="padding:6px;text-align:center;color:#30363d;font-size:11px;">—</td>';
                            return '<td style="padding:6px;text-align:center;color:#e0e0e0;font-size:11px;">' + port + '</td>';
                        }

                        html += '<tr style="border-bottom:1px solid #21262d;background:' + bgColor + ';">';
                        html += '<td style="padding:8px 6px;white-space:nowrap;color:#e0e0e0;">' + dateStr + '<br><span style="font-size:11px;color:#8b949e;">' + arrH + ' - ' + depH + '</span></td>';
                        html += '<td style="padding:8px 6px;color:#A23B72;font-weight:bold;white-space:nowrap;">' + c.ship_name + '</td>';
                        html += portCell(c.prev4 || '');
                        html += portCell(c.prev3 || '');
                        html += portCell(c.prev2 || '');
                        html += portCell(c.prev1 || '');
                        html += '<td style="padding:8px 10px;text-align:center;background:#A23B72;color:white;font-weight:bold;font-size:13px;">ROATAN</td>';
                        html += portCell(c.next1 || '');
                        html += portCell(c.next2 || '');
                        html += portCell(c.next3 || '');
                        html += portCell(c.next4 || '');
                        html += '<td style="padding:8px 6px;text-align:right;color:#e0e0e0;white-space:nowrap;">' + pax + '</td>';
                        html += '<td style="padding:8px 6px;text-align:center;color:' + segColor + ';font-weight:bold;">' + segment + '</td>';
                        html += '<td style="padding:8px 6px;text-align:right;color:#e0e0e0;white-space:nowrap;">' + price + '</td>';
                        html += '</tr>';
                    });

                    html += '</tbody></table>';
                    content.innerHTML = html;
                })
                .catch(err => {
                    content.innerHTML = '<div class="error">Error loading cruise schedule: ' + err.message + '</div>';
                });
        }

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
            document.querySelectorAll('.chart-card:not(#cruiseScheduleTable)').forEach(el => {
                el.innerHTML = '<div class="loading">Loading...</div>';
            });
            document.getElementById('statsRow').innerHTML = '<div class="loading">Loading statistics...</div>';
            // Keep cruise schedule content intact but show loading
            const cruiseContent = document.getElementById('cruiseScheduleContent');
            if (cruiseContent) {
                cruiseContent.innerHTML = '<div class="loading">Loading cruise schedule...</div>';
            }

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
                    Plotly.newPlot('airportHeatmap', JSON.parse(data.airport_heatmap));
                    Plotly.newPlot('cruisePortHeatmap', JSON.parse(data.cruise_port_heatmap));
                    Plotly.newPlot('cruiseCalendar', JSON.parse(data.cruise_calendar));
                    loadCruiseSchedule();
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


@app.route('/api/cruise-itineraries')
def api_cruise_itineraries():
    """API endpoint for enriched cruise itinerary data."""
    itinerary_data = load_cruise_itinerary_data()
    return jsonify({
        'shipsInPort': itinerary_data,
        'lastUpdated': datetime.now().strftime('%Y-%m-%d'),
    })


def _validate_port_order(prev_ports, next_ports, cruise_date):
    """Check if ports are in chronological order. If not, convert to T-minus notation.

    prev_ports: [prev1 (latest, closest to Roatan), prev2, prev3, prev4 (earliest, furthest)]
    next_ports: [next1 (earliest, closest after Roatan), next2, next3, next4 (latest, furthest)]
    cruise_date: the date the ship visits Roatan (e.g., '2026-06-11')

    T-minus notation uses actual day offsets from Roatan arrival:
    T-1 = 1 day before Roatan, T+1 = 1 day after Roatan, etc.

    Returns (fixed_prev, fixed_next) with T-minus notation if order is broken.
    """
    import re
    from datetime import datetime

    def extract_day_num(port_str):
        """Extract day number from a port string like 'Jun 22: Tampa' or '22: Tampa'."""
        if not port_str:
            return None
        # Try to match "Mon DD:" or "DD:" at the start
        m = re.match(r'([A-Za-z]+\s+)?(\d+):', port_str)
        if m:
            return int(m.group(2))
        return None

    def extract_month_num(port_str):
        """Extract month number from a port string like 'Jun 22: Tampa'.
        Returns 1-12 or None if no month found."""
        if not port_str:
            return None
        m = re.match(r'([A-Za-z]+)\s+\d+:', port_str)
        if m:
            month_abbr = m.group(1).lower()[:3]
            months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
                     'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
            return months.get(month_abbr)
        return None

    def get_port_sort_key(port_str):
        """Get a sortable key (month_num * 100 + day_num) for a port string."""
        if not port_str:
            return None
        month = extract_month_num(port_str)
        day = extract_day_num(port_str)
        if month is not None and day is not None:
            return month * 100 + day
        if day is not None:
            return day
        return None

    def to_t_minus(port_str, day_offset):
        """Convert a port string to T-minus notation with actual day offset."""
        if not port_str:
            return port_str
        # Remove the date prefix (e.g., "Jun 22: " or "22: ")
        cleaned = re.sub(r'^[A-Za-z]+\s+\d+:\s*', '', port_str)
        cleaned = re.sub(r'^\d+:\s*', '', cleaned)
        if day_offset < 0:
            return f'T{day_offset}: {cleaned}'
        elif day_offset > 0:
            return f'T+{day_offset}: {cleaned}'
        else:
            return f'T-0: {cleaned}'

    # Check previous ports (should be decreasing: prev1 > prev2 > prev3 > prev4)
    # because prev1 is latest and prev4 is earliest
    prev_keys = [get_port_sort_key(p) for p in prev_ports]
    prev_has_break = False
    for i in range(len(prev_keys) - 1):
        if prev_keys[i] is not None and prev_keys[i+1] is not None:
            if prev_keys[i] <= prev_keys[i+1]:
                prev_has_break = True
                break

    # Check next ports (should be increasing: next1 < next2 < next3 < next4)
    # because next1 is earliest after Roatan and next4 is latest
    next_keys = [get_port_sort_key(p) for p in next_ports]
    next_has_break = False
    for i in range(len(next_keys) - 1):
        if next_keys[i] is not None and next_keys[i+1] is not None:
            if next_keys[i] >= next_keys[i+1]:
                next_has_break = True
                break

    # If no breaks, return as-is
    if not prev_has_break and not next_has_break:
        return prev_ports, next_ports

    # Convert to T-minus notation using position-based offsets
    # prev1 (closest to Roatan) = T-1, prev2 = T-2, prev3 = T-3, prev4 = T-4
    # next1 (closest after Roatan) = T+1, next2 = T+2, next3 = T+3, next4 = T+4
    fixed_prev = []
    for i, p in enumerate(prev_ports):
        offset = -(i + 1)  # T-1, T-2, T-3, T-4
        fixed_prev.append(to_t_minus(p, offset))

    fixed_next = []
    for i, p in enumerate(next_ports):
        offset = i + 1  # T+1, T+2, T+3, T+4
        fixed_next.append(to_t_minus(p, offset))

    return fixed_prev, fixed_next


@app.route('/api/cruise-schedule')
def api_cruise_schedule():
    """API endpoint for monthly cruise schedule with itinerary details as a table."""
    year = request.args.get('year', 2026, type=int)
    month = request.args.get('month', 6, type=int)

    monthly_data = load_monthly_data(year, month)
    itinerary_data = load_cruise_itinerary_data()
    days = sorted(monthly_data['days'].keys())

    cruises = []
    for d in days:
        day_data = monthly_data['days'][d]
        for c in day_data.get('cruises', []):
            c = enrich_cruise_with_itinerary(c, itinerary_data, cruise_date=d)
            prev_ports = c.get('previous_ports', [])
            next_ports = c.get('next_ports', [])
            # Previous ports are stored latest-first in JSON (e.g., Jun 14, Jun 13, Jun 12)
            # We keep them as-is: prev1=latest, prev2, prev3, prev4=earliest
            # Next ports are stored chronologically (earliest-first) and stay as-is
            # Validate chronological order - use T-minus notation if broken
            prev_ports, next_ports = _validate_port_order(prev_ports, next_ports, d)
            # Pad to up to 4 ports each side
            while len(prev_ports) < 4:
                prev_ports.append('')
            while len(next_ports) < 4:
                next_ports.append('')
            cruises.append({
                'date': d,
                'ship_name': c.get('ship_name', 'Unknown'),
                'arrival_hour': c.get('arrival_hour', 8),
                'departure_hour': c.get('departure_hour', 17),
                'estimated_passengers': c.get('estimated_passengers', 0),
                'segment': c.get('segment', ''),
                'avg_price': c.get('avg_price', 0),
                'prev1': prev_ports[0] if len(prev_ports) > 0 else '',
                'prev2': prev_ports[1] if len(prev_ports) > 1 else '',
                'prev3': prev_ports[2] if len(prev_ports) > 2 else '',
                'prev4': prev_ports[3] if len(prev_ports) > 3 else '',
                'next1': next_ports[0] if len(next_ports) > 0 else '',
                'next2': next_ports[1] if len(next_ports) > 1 else '',
                'next3': next_ports[2] if len(next_ports) > 2 else '',
                'next4': next_ports[3] if len(next_ports) > 3 else '',
            })

    return jsonify({
        'year': year,
        'month': month,
        'cruises': cruises,
    })


@app.route('/api/cruise-itineraries/<date_str>')
def api_cruise_itineraries_by_date(date_str):
    """API endpoint for cruise itinerary data filtered by date."""
    itinerary_data = load_cruise_itinerary_data()
    # Filter ships that match the requested date
    ships_for_date = [s for s in itinerary_data if s.get('date') == date_str]
    return jsonify({
        'date': date_str,
        'shipsInPort': ships_for_date,
        'lastUpdated': datetime.now().strftime('%Y-%m-%d'),
    })


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
    airport_heatmap = create_airport_heatmap(monthly_data, year, month)
    cruise_port_heatmap = create_cruise_port_heatmap(monthly_data, year, month)
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
        'airport_heatmap': airport_heatmap,
        'cruise_port_heatmap': cruise_port_heatmap,
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
        airport_heatmap = create_airport_heatmap(monthly_data, year, month)
        cruise_port_heatmap = create_cruise_port_heatmap(monthly_data, year, month)
        cruise_calendar = create_cruise_calendar(monthly_data, year, month)

        # Generate first day hourly chart
        first_day_data = monthly_data['days'].get(selected_date, {})
        first_hourly = process_daily_data(first_day_data)
        hourly_chart = create_daily_hourly_chart(first_hourly, selected_date, 'all')

        # Create static HTML with embedded data
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L2LFYE0L4B"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-L2LFYE0L4B');
    </script>
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
    <div class="chart-grid">
        <div id="airportHeatmap" class="chart-card"></div>
        <div id="cruisePortHeatmap" class="chart-card"></div>
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
            airportHeatmap: {airport_heatmap},
            cruisePortHeatmap: {cruise_port_heatmap},
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
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L2LFYE0L4B"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-L2LFYE0L4B');
    </script>
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
    <p class="subtitle">Monthly tourism data for Roatan, Honduras â€” June 2026 through November 2028</p>
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
