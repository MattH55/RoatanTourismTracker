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

