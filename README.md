# Roatan Tourism Tracker

## Overview
Complete tourism analytics dashboard for Roatan, Honduras. Tracks flight and cruise ship arrivals/departures with comprehensive analytics and scheduling information.

## Features

### Main Dashboard (index.html)
- Monthly flight and cruise traffic analysis
- Daily movement statistics
- Combined tourism flow charts
- Calendar view with daily breakdown
- Month-by-month navigation

### Cruise Schedule (pages/schedule.html)
- Searchable cruise schedule database
- Ship itinerary information
- Previous and next port sequences
- Passenger capacity data
- Month filtering

### Analytics Dashboard (pages/dashboard.html)
- Summary statistics
- Monthly trends
- Historical data visualization
- Tourism volume analysis

## File Structure

```
roatan-tourism-tracker/
├── index.html                 # Main analytics dashboard
├── pages/
│   ├── schedule.html         # Cruise schedule
│   └── dashboard.html        # Summary analytics
├── assets/
│   ├── styles.css            # Shared styles
│   └── app.js                # JavaScript functions
└── README.md                 # This file
```

## Data Coverage

- **Date Range**: June 2026 - November 2028
- **Total Cruises**: 1,040+
- **Unique Ships**: 71+
- **Months Covered**: 30

## Technology

- **Charts**: Plotly.js (interactive visualization)
- **Styling**: CSS3 with dark theme
- **Data**: Embedded JSON in HTML files
- **Compatibility**: All modern browsers

## Deployment

1. Upload all files to your web server
2. Ensure `index.html` is in the root directory
3. Keep `pages/` and `assets/` folders intact
4. No backend server required - fully static site

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Responsive design

## Features by Page

### index.html
✓ Interactive monthly charts
✓ Flight traffic analysis
✓ Cruise traffic analysis
✓ Combined tourism metrics
✓ Calendar view
✓ Dark theme interface

### pages/schedule.html
✓ Search by ship name
✓ Filter by month
✓ Full itinerary data
✓ Port sequences
✓ Passenger information

### pages/dashboard.html
✓ Key statistics
✓ Monthly trends
✓ Tourism volume
✓ Historical analysis

## Navigation

Use the header navigation to switch between pages:
- **Analytics** - Main dashboard with charts
- **Cruise Schedule** - Searchable itinerary database
- **Dashboard** - Summary statistics

## Widget, TV display and today.json

The daily build (`generate_static_site.py`) also writes these into `static_site/`:

| File | What it is | Source |
| --- | --- | --- |
| `today.json` | Machine-readable ships, passengers and crowd level for the next 14 days | `today_json()` in `seo_pages.py`, written in the same step as `today.html` |
| `widget.html` | Card that other websites embed in an iframe | `widget_src/widget.html` |
| `embed.js` | Loader that inserts the iframe and sets its height | `widget_src/embed.js` |
| `embed.html` | How-to page with live previews and copy buttons | `embed_page()` in `widget_pages.py` |
| `tv.html` | Full-screen display for lobby and shop TVs | `widget_src/tv.html` (the build adds the QR code) |

To rebuild only these files, without the 4-minute chart build: `python widget_pages.py static_site`.

### Embed snippet

```html
<div class="rtt-widget" data-view="card" data-theme="auto" data-lang="en"></div>
<script src="https://roatantourismtracker.online/embed.js" async></script>
```

Options: `data-view` is `card` or `compact`, `data-theme` is `auto`, `light` or `dark`, and `data-lang` is `en` or `es`.
Where scripts are not allowed, use a plain iframe (fixed height):

```html
<iframe src="https://roatantourismtracker.online/widget.html?view=card&amp;theme=auto&amp;lang=en" width="360" height="330" style="border:0;max-width:100%" loading="lazy" title="Roatan cruise ships today"></iframe>
```

### today.json schema (version 1)

Other things read this file, so keep the keys stable and only add new ones.

```json
{
  "schema_version": 1,
  "generated_at": "2026-11-25T05:00:00-06:00",
  "timezone": "America/Tegucigalpa",
  "source_checked": "2026-11-24",
  "site_url": "https://roatantourismtracker.online",
  "crowd_levels": [
    {"key": "none", "label": "No cruise ships", "label_es": "Sin cruceros", "min": 0, "max": 0},
    {"key": "very_busy", "label": "Very busy", "label_es": "Muy ocupado", "min": 10000, "max": null}
  ],
  "days": [
    {
      "date": "2026-11-25", "ships_count": 6, "est_passengers": 19721, "crowd": "very_busy",
      "ships": [
        {"name": "Carnival Jubilee", "line": "Carnival Cruises", "arrive": "08:00", "depart": "17:00",
         "est_passengers": 5374, "prev_port": "Galveston", "next_port": "Cozumel"}
      ]
    }
  ],
  "disclaimer": "..."
}
```

- `days` has up to 14 entries starting today (Roatan time). Days with no schedule on file are left out, and unknown values are `null`.
- `crowd_levels` comes from `LEVELS` in `daily_message.py`, the same bands `today.html` uses (keys: `none`, `quiet`, `moderate`, `busy`, `very_busy`).
- The widget and TV page look up today's row by date, so yesterday's file still shows the right day if a build is late.
- Every build compares `today.json` with the numbers printed in `today.html` and stops if they differ (`check_today_json()`). The same check has unit tests: `python -m unittest test_today_json`.

### TV display

Open `tv.html` in the TV's browser. Options: `?lang=es`, `?rotate=1` (alternates English and Spanish every 30 seconds) and `?theme=light`.
It refetches the data every 10 minutes and reloads itself every 6 hours and just after 05:15 Roatan time.

Sponsors: copy `sponsors.example.json` to `sponsors.json` in the repo root and edit it. Each entry is `{name, text, url, image}`.
The TV rotates one sponsor line every 20 seconds. With no `sponsors.json`, or an empty list, no sponsor strip is shown.

Screenshots of every view and test case are in `docs/widget-screenshots/`.

## Support

For issues or updates, contact the tourism board.

---

Generated 2026-06-20
