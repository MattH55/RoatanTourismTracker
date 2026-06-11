"""
Tourism Tracker - Web Application
Flask app showing inflow/outflow of tourists by flights and cruise ships
for Roatan, Honduras. Shows data over the whole month of June 2026.
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
from scraper import collect_all_data, get_aircraft_capacity, get_cruise_ship_capacity, LOAD_FACTOR, generate_monthly_data

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


def load_monthly_data():
    """Load monthly data from JSON file or generate fresh."""
    data_file = 'tourism_monthly.json'
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            if data.get('days') and len(data['days']) >= 28:
                return data
        except:
            pass
    # Generate fresh monthly data
    data = generate_monthly_data()
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


def create_daily_hourly_chart(hourly_data, date_str):
    """Create hourly inflow/outflow bar chart for a single day."""
    hours = list(range(24))
    labels = [f'{h:02d}:00' for h in hours]

    in_flights = [hourly_data[h]['in_flights'] for h in hours]
    out_flights = [hourly_data[h]['out_flights'] for h in hours]
    in_cruise = [hourly_data[h]['in_cruise'] for h in hours]
    out_cruise = [hourly_data[h]['out_cruise'] for h in hours]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Flight Arrivals', x=labels, y=in_flights,
        marker_color='#2E86AB',
        hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Flight Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Arrivals', x=labels, y=in_cruise,
        marker_color='#A23B72',
        hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Cruise Arrivals</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Flight Departures', x=labels, y=[-x for x in out_flights],
        marker_color='#F18F01',
        hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Flight Departures</extra>'
    ))
    fig.add_trace(go.Bar(
        name='Cruise Departures', x=labels, y=[-x for x in out_cruise],
        marker_color='#C73E1D',
        hovertemplate='%{y:,.0f} passengers<br>%{x}<extra>Cruise Departures</extra>'
    ))

    net = [hourly_data[h]['total_in'] - hourly_data[h]['total_out'] for h in hours]
    fig.add_trace(go.Scatter(
        name='Net Inflow', x=labels, y=net,
        mode='lines+markers', line=dict(color='#2ECC40', width=3),
        marker=dict(size=8),
        hovertemplate='Net: %{y:+,.0f} passengers<br>%{x}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=f'<b>Hourly Tourist Flow - {date_str}</b>', font=dict(size=18)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=labels[::2], ticktext=labels[::2]),
        yaxis=dict(title='Number of Passengers', tickformat=','),
        barmode='relative', hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=50, b=60),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )
    fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.3)

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_flight_traffic_chart(monthly_data):
    """Create a daily bar chart showing flight inflow/outflow across the whole month."""
    days = sorted(monthly_data['days'].keys())
    daily_in = []
    daily_out = []
    daily_net = []
    day_labels = []

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        in_f = sum(hourly[h]['in_flights'] for h in range(24))
        out_f = sum(hourly[h]['out_flights'] for h in range(24))
        daily_in.append(in_f)
        daily_out.append(out_f)
        daily_net.append(in_f - out_f)
        day_num = int(d.split('-')[2])
        day_labels.append(f'Jun {day_num}')

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

    fig.update_layout(
        title=dict(text='<b>✈️ Flight Traffic - June 2026</b>', font=dict(size=20)),
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


def create_cruise_traffic_chart(monthly_data):
    """Create a daily bar chart showing cruise inflow/outflow across the whole month."""
    days = sorted(monthly_data['days'].keys())
    daily_in = []
    daily_out = []
    daily_net = []
    day_labels = []

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        in_c = sum(hourly[h]['in_cruise'] for h in range(24))
        out_c = sum(hourly[h]['out_cruise'] for h in range(24))
        daily_in.append(in_c)
        daily_out.append(out_c)
        daily_net.append(in_c - out_c)
        day_num = int(d.split('-')[2])
        day_labels.append(f'Jun {day_num}')

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

    fig.update_layout(
        title=dict(text='<b>🚢 Cruise Ship Traffic - June 2026</b>', font=dict(size=20)),
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


def create_monthly_heatmap(monthly_data):
    """Create a calendar heatmap showing tourist density across days and hours."""
    days = sorted(monthly_data['days'].keys())
    day_labels = [f'Jun {int(d.split("-")[2])}' for d in days]

    # Calculate cumulative tourists at each hour for each day
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

    fig.update_layout(
        title=dict(text='<b>Tourist Density Calendar - June 2026</b>', font=dict(size=20)),
        xaxis=dict(title='Hour of Day', tickangle=45, tickmode='array',
                   tickvals=hours[::3], ticktext=hours[::3]),
        yaxis=dict(title='Date', autorange='reversed'),
        template='plotly_dark', height=600,
        margin=dict(l=80, r=80, t=60, b=80),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_log_scale_chart(monthly_data):
    """Create a log-scale chart showing daily passenger volumes with Y-axis floor of 10."""
    days = sorted(monthly_data['days'].keys())
    daily_in_flights = []
    daily_in_cruise = []
    daily_out_flights = []
    daily_out_cruise = []
    day_labels = []

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        daily_in_flights.append(sum(hourly[h]['in_flights'] for h in range(24)))
        daily_in_cruise.append(sum(hourly[h]['in_cruise'] for h in range(24)))
        daily_out_flights.append(sum(hourly[h]['out_flights'] for h in range(24)))
        daily_out_cruise.append(sum(hourly[h]['out_cruise'] for h in range(24)))
        day_num = int(d.split('-')[2])
        day_labels.append(f'Jun {day_num}')

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

    fig.update_layout(
        title=dict(text='<b>Daily Passenger Volume (Log Scale) - June 2026</b>', font=dict(size=20)),
        xaxis=dict(title='Date', tickangle=45, tickmode='array',
                   tickvals=day_labels[::3], ticktext=day_labels[::3]),
        yaxis=dict(title='Passengers (log scale)', type='log', tickformat=',',
                   range=[10, 20000]),  # Range from 10 to 20,000 on log scale
        hovermode='x unified', template='plotly_dark',
        height=400,
        margin=dict(l=60, r=20, t=60, b=80),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def create_origin_pie_chart(monthly_data):
    """Create a pie chart showing tourist origin breakdown from flight origins and cruise line data."""
    # Flight origin → region mapping
    airport_regions = {
        'MIA': 'United States', 'FLL': 'United States', 'IAH': 'United States',
        'ATL': 'United States', 'HOU': 'United States', 'TEB': 'United States',
        'PTY': 'Latin America / Other', 'SAL': 'Latin America / Other',
        'RTB': 'Latin America / Other',  # Domestic Roatan flights
    }

    # Cruise line → region composition (from CSV data)
    cruise_composition = {
        'Carnival': {'United States': 0.85, 'Canada': 0.07, 'United Kingdom / Europe': 0.03, 'Latin America / Other': 0.05},
        'Royal Caribbean': {'United States': 0.78, 'Canada': 0.10, 'United Kingdom / Europe': 0.07, 'Latin America / Other': 0.05},
        'Norwegian': {'United States': 0.75, 'Canada': 0.12, 'United Kingdom / Europe': 0.08, 'Latin America / Other': 0.05},
        'MSC': {'United States': 0.55, 'Canada': 0.08, 'United Kingdom / Europe': 0.28, 'Latin America / Other': 0.09},
        'Princess': {'United States': 0.80, 'Canada': 0.09, 'United Kingdom / Europe': 0.06, 'Latin America / Other': 0.05},
    }

    # Map cruise ship names to cruise lines
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
            ship_to_line[ship_name] = 'Royal Caribbean'  # Celebrity is owned by RCL
        elif 'Disney' in ship_name:
            ship_to_line[ship_name] = 'Royal Caribbean'  # Approximate as similar mix
        elif 'Holland America' in ship_name:
            ship_to_line[ship_name] = 'Princess'  # Both owned by Carnival Corp, similar demo
        elif 'Costa' in ship_name:
            ship_to_line[ship_name] = 'MSC'  # Italian line, similar European mix
        elif 'AIDA' in ship_name:
            ship_to_line[ship_name] = 'MSC'  # German line, European mix
        else:
            ship_to_line[ship_name] = 'Royal Caribbean'  # Default

    # Aggregate passenger origins
    region_totals = {
        'United States': 0,
        'Canada': 0,
        'United Kingdom / Europe': 0,
        'Latin America / Other': 0,
    }

    days = sorted(monthly_data['days'].keys())
    for d in days:
        day_data = monthly_data['days'][d]

        # Process flight arrivals by origin
        for f in day_data.get('flights', []):
            if f.get('is_arrival'):
                origin = f.get('origin', '')
                pax = f.get('estimated_passengers', 100)
                region = airport_regions.get(origin, 'Latin America / Other')
                region_totals[region] += pax

        # Process cruise arrivals by ship line composition
        for c in day_data.get('cruises', []):
            ship_name = c.get('ship_name', '')
            pax = c.get('estimated_passengers', 2000)
            line = ship_to_line.get(ship_name, 'Royal Caribbean')
            comp = cruise_composition.get(line, cruise_composition['Royal Caribbean'])
            for region, fraction in comp.items():
                region_totals[region] += int(pax * fraction)

    # Filter out zero values
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

    fig.update_layout(
        title=dict(text='<b>🌍 Tourist Origin Breakdown - June 2026</b>', font=dict(size=20)),
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


def create_origin_inflow_chart(monthly_data):
    """Create a multi-line chart showing daily inflows broken down by origin region."""
    # Same origin mapping as the pie chart
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
    day_labels = [f'Jun {int(d.split("-")[2])}' for d in days]

    # Daily inflow by region
    daily_by_region = {r: [] for r in regions}

    for d in days:
        day_data = monthly_data['days'][d]
        region_totals = {r: 0 for r in regions}

        # Flight arrivals by origin
        for f in day_data.get('flights', []):
            if f.get('is_arrival'):
                origin = f.get('origin', '')
                pax = f.get('estimated_passengers', 100)
                region = airport_regions.get(origin, 'Latin America / Other')
                region_totals[region] += pax

        # Cruise arrivals by ship line composition
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

    fig.update_layout(
        title=dict(text='<b>🌍 Daily Inflow by Origin Region - June 2026</b>', font=dict(size=20)),
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


def create_combined_volume_chart(monthly_data):
    """Create a linear-scale chart showing daily passenger volume for flights and cruise ships on the same chart."""
    days = sorted(monthly_data['days'].keys())
    daily_in_flights = []
    daily_in_cruise = []
    daily_out_flights = []
    daily_out_cruise = []
    day_labels = []

    for d in days:
        day_data = monthly_data['days'][d]
        hourly = process_daily_data(day_data)
        daily_in_flights.append(sum(hourly[h]['in_flights'] for h in range(24)))
        daily_in_cruise.append(sum(hourly[h]['in_cruise'] for h in range(24)))
        daily_out_flights.append(sum(hourly[h]['out_flights'] for h in range(24)))
        daily_out_cruise.append(sum(hourly[h]['out_cruise'] for h in range(24)))
        day_num = int(d.split('-')[2])
        day_labels.append(f'Jun {day_num}')

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
        <h1>🏝️ Roatan Tourism Tracker</h1>
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
        var flightTraffic = {{ flight_traffic | safe }};
        var cruiseTraffic = {{ cruise_traffic | safe }};
        var monthlyHeatmap = {{ monthly_heatmap | safe }};
        var logChart = {{ log_chart | safe }};
        var originPie = {{ origin_pie | safe }};
        var originInflow = {{ origin_inflow | safe }};
        var combinedVolume = {{ combined_volume | safe }};
        var cruiseCalendar = {{ cruise_calendar | safe }};
        var dailyDetail = {{ daily_detail | safe }};

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
        Plotly.newPlot('cruiseCalendar', cruiseCalendar.data, cruiseCalendar.layout, {
            responsive: true, displayModeBar: false
        });
        Plotly.newPlot('dailyDetail', dailyDetail.data, dailyDetail.layout, {
            responsive: true, displayModeBar: false
        });

        function loadDayData(dateStr) {
            fetch('/api/day/' + dateStr)
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
            Plotly.Plots.resize(document.getElementById('cruiseCalendar'));
            Plotly.Plots.resize(document.getElementById('dailyDetail'));
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
    cruise_calendar = create_cruise_calendar(monthly_data)

    # Default to first day's detail
    first_day = days[0]
    day_data = monthly_data['days'][first_day]
    hourly = process_daily_data(day_data)
    daily_detail = create_daily_hourly_chart(hourly, first_day)

    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        days=days,
        flight_traffic=flight_traffic,
        cruise_traffic=cruise_traffic,
        monthly_heatmap=monthly_heatmap,
        log_chart=log_chart,
        origin_pie=origin_pie,
        origin_inflow=origin_inflow,
        combined_volume=combined_volume,
        cruise_calendar=cruise_calendar,
        daily_detail=daily_detail
    )


@app.route('/api/day/<date_str>')
def api_day(date_str):
    """API endpoint for a specific day's data."""
    monthly_data = load_monthly_data()
    if date_str in monthly_data.get('days', {}):
        day_data = monthly_data['days'][date_str]
        hourly = process_daily_data(day_data)
        chart = create_daily_hourly_chart(hourly, date_str)
        return jsonify({'date': date_str, 'chart': chart})
    return jsonify({'error': 'Date not found'}), 404


@app.route('/api/monthly')
def api_monthly():
    """API endpoint for monthly statistics."""
    monthly_data = load_monthly_data()
    stats = create_monthly_stats(monthly_data)
    return jsonify(stats)


def generate_static_html():
    """Export the full dashboard as a single static HTML file."""
    with app.app_context():
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
        cruise_calendar = create_cruise_calendar(monthly_data)

        first_day = days[0]
        day_data = monthly_data['days'][first_day]
        hourly = process_daily_data(day_data)
        daily_detail = create_daily_hourly_chart(hourly, first_day)

        html = render_template_string(
            HTML_TEMPLATE,
            stats=stats,
            days=days,
            flight_traffic=flight_traffic,
            cruise_traffic=cruise_traffic,
            monthly_heatmap=monthly_heatmap,
            log_chart=log_chart,
            origin_pie=origin_pie,
            origin_inflow=origin_inflow,
            combined_volume=combined_volume,
            cruise_calendar=cruise_calendar,
            daily_detail=daily_detail
        )

        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Static site generated: index.html")
        return html


if __name__ == '__main__':
    print("=" * 60)
    print("ROATAN TOURISM TRACKER - JUNE 2026")
    print("=" * 60)
    print("Starting web server...")
    print("Open http://127.0.0.1:5000 in your browser")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
