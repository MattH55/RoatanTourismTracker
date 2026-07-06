"""
Generate complete static HTML site matching the Flask app exactly.
Produces static_site/index.html + static_site/YYYY-MM.html per month.
Each month page has all 13 charts, cruise schedule table, and day selector.
"""
import sys, os, json
sys.path.insert(0, '.')

from datetime import datetime

print("Importing Flask app functions...")
from app import (
    AVAILABLE_MONTHS, get_month_label, get_month_key,
    load_monthly_data, create_monthly_stats,
    create_monthly_calendar_chart, create_flight_traffic_chart,
    create_cruise_traffic_chart, create_combined_volume_chart,
    create_log_scale_chart, create_origin_pie_chart, create_origin_inflow_chart,
    create_hourly_pattern_chart, create_event_timeline_chart,
    create_airport_heatmap, create_cruise_port_heatmap, create_cruise_calendar,
    create_daily_hourly_chart, process_daily_data,
    enrich_cruise_with_itinerary, load_cruise_itinerary_data,
    _validate_port_order
)
from scraper import get_weather_data

OUTPUT_DIR = 'static_site'
os.makedirs(OUTPUT_DIR, exist_ok=True)

MONTH_KEYS = [get_month_key(y, m) for y, m in AVAILABLE_MONTHS]


def generate_cruise_schedule_rows(monthly_data, year, month):
    """Return list of cruise row dicts matching api_cruise_schedule output."""
    itinerary_data = load_cruise_itinerary_data()
    days = sorted(monthly_data['days'].keys())
    rows = []
    for d in days:
        for c in monthly_data['days'][d].get('cruises', []):
            c = dict(c)  # copy so we don't mutate the original
            c = enrich_cruise_with_itinerary(c, itinerary_data, cruise_date=d)
            prev_ports = list(c.get('previous_ports', []))
            next_ports = list(c.get('next_ports', []))
            prev_ports, next_ports = _validate_port_order(prev_ports, next_ports, d)
            while len(prev_ports) < 4: prev_ports.append('')
            while len(next_ports) < 4: next_ports.append('')
            rows.append({
                'date': d,
                'ship_name': c.get('ship_name', 'Unknown'),
                'arrival_hour': c.get('arrival_hour', 8),
                'departure_hour': c.get('departure_hour', 17),
                'estimated_passengers': c.get('estimated_passengers', 0),
                'segment': c.get('segment', ''),
                'avg_price': c.get('avg_price', 0),
                'prev4': prev_ports[3], 'prev3': prev_ports[2],
                'prev2': prev_ports[1], 'prev1': prev_ports[0],
                'next1': next_ports[0], 'next2': next_ports[1],
                'next3': next_ports[2], 'next4': next_ports[3],
            })
    return rows


def render_cruise_table(rows):
    """Render cruise schedule rows to HTML table string."""
    if not rows:
        return '<div style="color:#8b949e;text-align:center;padding:20px;">No cruise ships scheduled for this month.</div>'

    seg_colors = {'Budget': '#2ECC40', 'Mid-range': '#F18F01',
                  'Premium': '#A23B72', 'Luxury': '#FFD700'}

    h = '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
    h += '<thead><tr style="background:#0d1117;border-bottom:2px solid #30363d;">'
    for col, extra in [
        ('Date', ''), ('Ship Name', ''), ('Prev 4', ''), ('Prev 3', ''),
        ('Prev 2', ''), ('Prev 1', ''),
        ('&starf; ROATAN &starf;', 'background:#A23B72;color:white;'),
        ('Next 1', ''), ('Next 2', ''), ('Next 3', ''), ('Next 4', ''),
        ('Passengers', 'text-align:right;'), ('Segment', 'text-align:center;'),
        ('Avg Price', 'text-align:right;'),
    ]:
        h += f'<th style="padding:8px 6px;color:#8b949e;{extra}">{col}</th>'
    h += '</tr></thead><tbody>'

    for idx, c in enumerate(rows):
        bg = '#161b22' if idx % 2 == 0 else '#1a1f2e'
        date_obj = datetime.strptime(c['date'], '%Y-%m-%d')
        date_str = date_obj.strftime('%b %d, %Y')
        arr_h = f"{c['arrival_hour']:02d}:00"
        dep_h = f"{c['departure_hour']:02d}:00"
        pax = f"{c['estimated_passengers']:,}"
        price = f"${c['avg_price']:,}" if c['avg_price'] else 'N/A'
        seg = c['segment'] or 'N/A'
        seg_color = seg_colors.get(seg, '#8b949e')

        def pc(port):
            if not port:
                return '<td style="padding:6px;text-align:center;color:#30363d;font-size:11px;">&mdash;</td>'
            p = port.replace('<', '&lt;').replace('>', '&gt;')
            return f'<td style="padding:6px;text-align:center;color:#e0e0e0;font-size:11px;">{p}</td>'

        h += f'<tr style="border-bottom:1px solid #21262d;background:{bg};">'
        h += f'<td style="padding:8px 6px;white-space:nowrap;color:#e0e0e0;">{date_str}<br><span style="font-size:11px;color:#8b949e;">{arr_h} - {dep_h}</span></td>'
        h += f'<td style="padding:8px 6px;color:#A23B72;font-weight:bold;white-space:nowrap;">{c["ship_name"]}</td>'
        h += pc(c['prev4'])
        h += pc(c['prev3'])
        h += pc(c['prev2'])
        h += pc(c['prev1'])
        h += '<td style="padding:8px 10px;text-align:center;background:#A23B72;color:white;font-weight:bold;font-size:13px;">ROATAN</td>'
        h += pc(c['next1'])
        h += pc(c['next2'])
        h += pc(c['next3'])
        h += pc(c['next4'])
        h += f'<td style="padding:8px 6px;text-align:right;color:#e0e0e0;white-space:nowrap;">{pax}</td>'
        h += f'<td style="padding:8px 6px;text-align:center;color:{seg_color};font-weight:bold;">{seg}</td>'
        h += f'<td style="padding:8px 6px;text-align:right;color:#e0e0e0;white-space:nowrap;">{price}</td>'
        h += '</tr>'

    h += '</tbody></table>'
    return h


CSS = """
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
.month-nav { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.month-nav a, .month-nav span {
    padding: 6px 14px; border-radius: 6px;
    border: 1px solid #30363d; background: #161b22;
    color: #e0e0e0; font-size: 13px; text-decoration: none;
}
.month-nav a:hover { border-color: #2E86AB; color: #2E86AB; }
.month-nav .current { background: #2E86AB; border-color: #2E86AB; }
.day-controls {
    display: flex; gap: 8px; align-items: center;
    margin-bottom: 12px; flex-wrap: wrap;
}
.day-controls label { font-size: 13px; color: #8b949e; }
.day-controls select {
    padding: 6px 12px; border-radius: 6px;
    border: 1px solid #30363d; background: #161b22;
    color: #e0e0e0; font-size: 13px; cursor: pointer;
}
.day-controls select:hover { border-color: #2E86AB; }
.filter-btn {
    padding: 6px 14px; border-radius: 6px;
    border: 1px solid #30363d; background: #161b22;
    color: #e0e0e0; font-size: 13px; cursor: pointer;
}
.filter-btn:hover { border-color: #2E86AB; }
.filter-btn.active { background: #2E86AB; border-color: #2E86AB; color: white; }
.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px; margin-bottom: 20px;
}
.stat-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 15px; text-align: center;
}
.stat-card .value { font-size: 24px; font-weight: bold; color: #2E86AB; }
.stat-card .label { font-size: 12px; color: #8b949e; margin-top: 4px; }
.chart-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 16px; margin-bottom: 16px;
}
.chart-full { margin-bottom: 16px; }
.chart-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 10px;
}
.section-title {
    color: #A23B72; font-size: 18px; margin-bottom: 12px; padding: 0 4px;
}
@media (max-width: 900px) {
    .chart-grid { grid-template-columns: 1fr; }
    .header { flex-direction: column; align-items: flex-start; }
}
"""


def generate_month_page(year, month):
    """Generate a complete HTML page for one month."""
    mk = get_month_key(year, month)
    label = get_month_label(year, month)
    print(f"  [{mk}] Loading data...", end='', flush=True)

    monthly_data = load_monthly_data(year, month)
    weather_data = get_weather_data(year, month)
    days = sorted(monthly_data['days'].keys())

    print(" charts...", end='', flush=True)
    stats = create_monthly_stats(monthly_data)
    cal_chart    = create_monthly_calendar_chart(monthly_data, weather_data, year, month)
    flight_chart = create_flight_traffic_chart(monthly_data, year, month)
    cruise_chart = create_cruise_traffic_chart(monthly_data, year, month)
    combined     = create_combined_volume_chart(monthly_data, year, month)
    log_scale    = create_log_scale_chart(monthly_data, year, month)
    ori_pie      = create_origin_pie_chart(monthly_data, year, month)
    ori_inflow   = create_origin_inflow_chart(monthly_data, year, month)
    hrly_pat     = create_hourly_pattern_chart(monthly_data, year, month)
    evt_tl       = create_event_timeline_chart(monthly_data, year, month)
    ap_heat      = create_airport_heatmap(monthly_data, year, month)
    cp_heat      = create_cruise_port_heatmap(monthly_data, year, month)
    cruise_cal   = create_cruise_calendar(monthly_data, year, month)

    print(" day charts...", end='', flush=True)
    # Pre-compute hourly charts for every day x 3 filter modes
    day_charts = {}
    for d in days:
        ddata = monthly_data['days'][d]
        hourly = process_daily_data(ddata)
        day_charts[d] = {
            'all':     create_daily_hourly_chart(hourly, d, 'all'),
            'flights': create_daily_hourly_chart(hourly, d, 'flights'),
            'cruises': create_daily_hourly_chart(hourly, d, 'cruises'),
        }

    print(" cruise table...", end='', flush=True)
    cruise_rows = generate_cruise_schedule_rows(monthly_data, year, month)
    cruise_table_html = render_cruise_table(cruise_rows)

    # Prev/next month navigation
    idx = MONTH_KEYS.index(mk)
    prev_link = f'<a href="{MONTH_KEYS[idx-1]}.html">&larr; {get_month_label(*AVAILABLE_MONTHS[idx-1])}</a>' if idx > 0 else '<span style="opacity:0.3;">&larr; Prev</span>'
    next_link = f'<a href="{MONTH_KEYS[idx+1]}.html">{get_month_label(*AVAILABLE_MONTHS[idx+1])} &rarr;</a>' if idx < len(MONTH_KEYS)-1 else '<span style="opacity:0.3;">Next &rarr;</span>'

    stats_cards = ''.join([
        f'<div class="stat-card"><div class="value">{v}</div><div class="label">{l}</div></div>'
        for l, v in [
            ('Total Arrivals', f"{stats['total_arrivals']:,}"),
            ('Total Departures', f"{stats['total_departures']:,}"),
            ('Flight Arrivals', f"{stats['total_flight_arrivals']:,}"),
            ('Flight Departures', f"{stats['total_flight_departures']:,}"),
            ('Cruise Arrivals', f"{stats['total_cruise_arrivals']:,}"),
            ('Cruise Departures', f"{stats['total_cruise_departures']:,}"),
            ('Total Flights', f"{stats['total_flights']:,}"),
            ('Total Cruise Ships', f"{stats['total_cruise_ships']:,}"),
        ]
    ])

    day_options = ''.join(f'<option value="{d}">{d}</option>' for d in days)
    first_day = days[0] if days else ''

    # Embed day charts as JSON
    day_charts_json = json.dumps({
        d: {mode: json.loads(dc[mode])['data'] + [json.loads(dc[mode])['layout']]
            for mode in dc}
        for d, dc in day_charts.items()
    }, separators=(',', ':'))

    # Avoid this - it's 1 parse per day. Instead store raw JSON strings
    day_charts_raw = {}
    for d, modes in day_charts.items():
        day_charts_raw[d] = {mode: modes[mode] for mode in modes}

    day_charts_json_str = 'const dayCharts = {\n'
    for d, modes in day_charts_raw.items():
        day_charts_json_str += f'  {json.dumps(d)}: {{\n'
        for mode, chart_json in modes.items():
            day_charts_json_str += f'    {json.dumps(mode)}: {chart_json},\n'
        day_charts_json_str += '  },\n'
    day_charts_json_str += '};\n'

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
    <title>Roatan Cruise Schedule {label} | Previous &amp; Next Ports</title>
    <meta name="description" content="Roatan cruise schedule for {label}. See every ship visiting Roatan with previous and next ports, passenger counts, and daily traffic charts.">

    <!-- Open Graph -->
    <meta property="og:title" content="Roatan Cruise Schedule {label}">
    <meta property="og:description" content="See previous and next ports for every cruise stopping in Roatan in {label}.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://roatantourismtracker.online/{mk}.html">

    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "Roatan Cruise Schedule {label}",
      "url": "https://roatantourismtracker.online/{mk}.html",
      "description": "Cruise ship schedule for Roatan, Honduras in {label} with previous and next ports.",
      "isPartOf": {{
        "@type": "WebSite",
        "name": "Roatan Tourism Tracker",
        "url": "https://roatantourismtracker.online"
      }}
    }}
    </script>

    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>{CSS}</style>
</head>
<body>
    <div class="header">
        <h1>Roatan Tourism Tracker</h1>
        <div class="month-nav">
            <a href="index.html">All Months</a>
            {prev_link}
            <span class="current">{label}</span>
            {next_link}
        </div>
    </div>

    <div class="stats-row">{stats_cards}</div>

    <div class="chart-full chart-card">
        <div id="calendarChart"></div>
    </div>

    <div class="chart-full chart-card">
        <div class="day-controls">
            <label for="daySelector">Day:</label>
            <select id="daySelector" onchange="changeDay()" aria-label="Select day to view hourly traffic">{day_options}</select>
            <button class="filter-btn active" id="btnAll" onclick="setFilter('all')" aria-label="Show all traffic">All</button>
            <button class="filter-btn" id="btnFlights" onclick="setFilter('flights')" aria-label="Show flights only">Flights</button>
            <button class="filter-btn" id="btnCruises" onclick="setFilter('cruises')" aria-label="Show cruises only">Cruises</button>
        </div>
        <div id="hourlyChart"></div>
    </div>

    <div class="chart-grid">
        <div class="chart-card"><div id="flightChart"></div></div>
        <div class="chart-card"><div id="cruiseChart"></div></div>
    </div>
    <div class="chart-grid">
        <div class="chart-card"><div id="combinedVolumeChart"></div></div>
        <div class="chart-card"><div id="logScaleChart"></div></div>
    </div>
    <div class="chart-grid">
        <div class="chart-card"><div id="originPieChart"></div></div>
        <div class="chart-card"><div id="originInflowChart"></div></div>
    </div>
    <div class="chart-grid">
        <div class="chart-card"><div id="hourlyPatternChart"></div></div>
        <div class="chart-card"><div id="eventTimelineChart"></div></div>
    </div>
    <div class="chart-grid">
        <div class="chart-card"><div id="airportHeatmap"></div></div>
        <div class="chart-card"><div id="cruisePortHeatmap"></div></div>
    </div>
    <div class="chart-full chart-card">
        <div id="cruiseCalendar"></div>
    </div>

    <div class="chart-full chart-card">
        <div class="section-title">&#9875; Monthly Cruise Schedule &mdash; Previous Stops &rarr; Roatan &rarr; Next Stops</div>
        <div style="overflow-x:auto;">{cruise_table_html}</div>
    </div>

    <footer style="margin-top:32px;padding-top:16px;border-top:1px solid #21262d;font-size:12px;color:#484f58;">
        Last updated: 2026-06-25 &mdash; <a href="index.html" style="color:#484f58;">All months</a> &mdash; <a href="https://roatantourismtracker.online" style="color:#484f58;">roatantourismtracker.online</a>
    </footer>

    <script>
        let currentFilter = 'all';
        let currentDay = {json.dumps(first_day)};

        {day_charts_json_str}

        const monthlyCharts = {{
            calendarChart:       {cal_chart},
            flightChart:         {flight_chart},
            cruiseChart:         {cruise_chart},
            combinedVolumeChart: {combined},
            logScaleChart:       {log_scale},
            originPieChart:      {ori_pie},
            originInflowChart:   {ori_inflow},
            hourlyPatternChart:  {hrly_pat},
            eventTimelineChart:  {evt_tl},
            airportHeatmap:      {ap_heat},
            cruisePortHeatmap:   {cp_heat},
            cruiseCalendar:      {cruise_cal},
        }};

        function mergeLayout(layout) {{
            const merged = Object.assign({{}}, layout, {{
                autosize: true,
                margin: {{ l: 70, r: 30, t: 60, b: 50 }}
            }});
            merged.xaxis = Object.assign({{}}, layout.xaxis || {{}}, {{ automargin: false }});
            merged.yaxis = Object.assign({{}}, layout.yaxis || {{}}, {{ automargin: false }});
            return merged;
        }}

        function renderMonthlyCharts() {{
            Object.entries(monthlyCharts).forEach(([id, chart]) => {{
                Plotly.newPlot(id, chart.data, mergeLayout(chart.layout), {{responsive: true}});
            }});
        }}

        function renderHourlyChart() {{
            const chart = dayCharts[currentDay][currentFilter];
            Plotly.newPlot('hourlyChart', chart.data, mergeLayout(chart.layout), {{responsive: true}});
        }}

        function changeDay() {{
            currentDay = document.getElementById('daySelector').value;
            renderHourlyChart();
        }}

        function setFilter(mode) {{
            currentFilter = mode;
            ['All','Flights','Cruises'].forEach(m => {{
                const btn = document.getElementById('btn' + m);
                btn.classList.toggle('active', m.toLowerCase() === mode);
            }});
            renderHourlyChart();
        }}

        renderMonthlyCharts();
        renderHourlyChart();
    </script>
</body>
</html>"""

    print(" done.")
    return html


def generate_index_page():
    """Generate the index.html landing page with SEO."""
    cards = ''
    for year, month in AVAILABLE_MONTHS:
        mk = get_month_key(year, month)
        month_name = datetime(year, month, 1).strftime('%B')
        cards += f'''        <a href="{mk}.html" class="month-card" aria-label="{month_name} {year} cruise schedule">
            <div class="month-name">{month_name}</div>
            <div class="year-label">{year}</div>
        </a>\n'''

    return f"""<!DOCTYPE html>
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
    <title>Roatan Cruise Schedule 2026&ndash;2028 | Previous &amp; Next Ports</title>
    <meta name="description" content="View the full Roatan cruise schedule for 2026&ndash;2028. See which ships are coming to Roatan and the ports they visit before and after.">

    <!-- Open Graph -->
    <meta property="og:title" content="Roatan Cruise Schedule 2026&ndash;2028">
    <meta property="og:description" content="See previous and next ports for every cruise stopping in Roatan, Honduras.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://roatantourismtracker.online">

    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Roatan Tourism Tracker",
      "url": "https://roatantourismtracker.online",
      "description": "Roatan cruise schedule with previous and next ports for 2026&ndash;2028."
    }}
    </script>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #e0e0e0;
            padding: 40px;
        }}
        h1 {{
            font-size: 36px;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .subtitle {{ color: #8b949e; margin-bottom: 8px; font-size: 16px; }}
        .value-prop {{
            color: #c0c8d8;
            font-size: 15px;
            margin-bottom: 32px;
            padding: 10px 14px;
            border-left: 3px solid #A23B72;
            background: #161b22;
            border-radius: 0 6px 6px 0;
            max-width: 620px;
        }}
        h2 {{
            font-size: 18px;
            color: #8b949e;
            border-bottom: 1px solid #30363d;
            padding-bottom: 8px;
            margin-bottom: 14px;
            margin-top: 28px;
        }}
        .month-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 16px;
        }}
        .month-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 24px 16px;
            text-align: center;
            text-decoration: none;
            color: #e0e0e0;
            transition: border-color 0.2s, transform 0.1s;
        }}
        .month-card:hover {{
            border-color: #2E86AB;
            transform: translateY(-2px);
        }}
        .month-card .month-name {{ font-size: 20px; font-weight: bold; }}
        .month-card .year-label {{ font-size: 13px; color: #8b949e; margin-top: 6px; }}
        footer {{
            margin-top: 48px;
            font-size: 12px;
            color: #484f58;
            border-top: 1px solid #21262d;
            padding-top: 16px;
        }}
    </style>
</head>
<body>
    <h1>Roatan Tourism Tracker</h1>
    <p class="subtitle">Flight &amp; cruise analytics for Roatan, Honduras &mdash; June 2026 through November 2028</p>
    <p class="value-prop">See previous &amp; next ports for every cruise stopping in Roatan, plus flight traffic, passenger volumes, and hourly patterns by month.</p>

    <h2>Select a Month</h2>
    <div class="month-grid" role="navigation" aria-label="Monthly cruise schedule navigation">
{cards}    </div>

    <footer>
        <p>Last updated: 2026-06-25 &mdash; Data covers June 2026 through November 2028 &mdash; <a href="https://roatantourismtracker.online" style="color:#484f58;">roatantourismtracker.online</a></p>
    </footer>
</body>
</html>"""


if __name__ == '__main__':
    print(f"Generating static site into '{OUTPUT_DIR}/'...")
    total = len(AVAILABLE_MONTHS)
    for i, (year, month) in enumerate(AVAILABLE_MONTHS, 1):
        mk = get_month_key(year, month)
        print(f"[{i:2d}/{total}]", end=' ')
        html = generate_month_page(year, month)
        path = os.path.join(OUTPUT_DIR, f'{mk}.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        size_kb = os.path.getsize(path) / 1024
        print(f"  -> {path} ({size_kb:.0f} KB)")

    index_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(generate_index_page())
    print(f"\n[OK] {index_path}")
    print(f"[OK] Static site complete: {OUTPUT_DIR}/")
    print(f"[OK] Upload the entire '{OUTPUT_DIR}/' folder to your web host.")
    print(f"[OK] Open {OUTPUT_DIR}/index.html in a browser to preview.")
