// Roatan Tourism Tracker - Main Application

function initializeApp() {
    const selected = document.getElementById('monthSelect').value || monthsList[0];
    changeMonth(selected);
}

function changeMonth(monthKey = null) {
    const monthKey_ = monthKey || document.getElementById('monthSelect').value;

    // Hide all sections
    document.querySelectorAll('.month-section').forEach(s => s.classList.remove('active'));

    // Show selected section or create it
    let section = document.getElementById(`month-${monthKey_}`);
    if (!section) {
        section = createMonthSection(monthKey_);
        document.getElementById('chartsContainer').appendChild(section);
    }

    section.classList.add('active');
    renderCharts(monthKey_);
}

function processMonthlyData(monthData) {
    const days = monthData.days || {};
    let stats = {
        flights_in: 0,
        flights_out: 0,
        cruises_in: 0,
        cruises_out: 0,
        flight_passengers: 0,
        cruise_passengers: 0,
        daily: {}
    };

    for (const [dayStr, dayData] of Object.entries(days)) {
        let day_flights_in = 0, day_flights_out = 0, day_cruises_in = 0, day_cruises_out = 0;
        let day_flight_pax = 0, day_cruise_pax = 0;

        // Process flights
        for (const flight of (dayData.flights || [])) {
            const pax = flight.estimated_passengers || 0;
            if (flight.is_arrival) {
                stats.flights_in += 1;
                day_flights_in += 1;
                stats.flight_passengers += pax;
                day_flight_pax += pax;
            } else {
                stats.flights_out += 1;
                day_flights_out += 1;
                stats.flight_passengers += pax;
                day_flight_pax += pax;
            }
        }

        // Process cruises
        for (const cruise of (dayData.cruises || [])) {
            const pax = cruise.estimated_passengers || 0;
            if (cruise.is_arrival) {
                stats.cruises_in += 1;
                day_cruises_in += 1;
            } else {
                stats.cruises_out += 1;
                day_cruises_out += 1;
            }
            stats.cruise_passengers += pax;
            day_cruise_pax += pax;
        }

        stats.daily[dayStr] = {
            flights_in: day_flights_in,
            flights_out: day_flights_out,
            cruises_in: day_cruises_in,
            cruises_out: day_cruises_out,
            flight_pax: day_flight_pax,
            cruise_pax: day_cruise_pax
        };
    }

    return stats;
}

function createMonthSection(monthKey) {
    const monthData = allMonthlyData[monthKey];
    const [year, month] = monthKey.split('-');
    const monthObj = new Date(year, month - 1);
    const monthName = monthObj.toLocaleString('default', { month: 'long', year: 'numeric' });

    const stats = processMonthlyData(monthData);
    const days = monthData.days || {};
    const daysList = Object.keys(days).sort();

    // Chart data
    let flightData = [], cruiseData = [], netData = [];
    let dayLabels = [];

    for (const dayStr of daysList) {
        const day = parseInt(dayStr.split('-')[2]);
        dayLabels.push(`${monthObj.toLocaleString('default', {month: 'short'})} ${day}`);

        const dayStats = stats.daily[dayStr] || {};
        flightData.push(dayStats.flights_in + dayStats.flights_out);
        cruiseData.push(dayStats.cruises_in + dayStats.cruises_out);
        netData.push((dayStats.flights_in - dayStats.flights_out) + (dayStats.cruises_in - dayStats.cruises_out));
    }

    const section = document.createElement('div');
    section.id = `month-${monthKey}`;
    section.className = 'month-section';
    section.innerHTML = `
        <div class="month-header">${monthName}</div>

        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-label">Total Flight Movements</div>
                <div class="stat-value">${stats.flights_in + stats.flights_out}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Cruise Movements</div>
                <div class="stat-value">${stats.cruises_in + stats.cruises_out}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Flight Passengers</div>
                <div class="stat-value">${stats.flight_passengers.toLocaleString()}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Cruise Passengers</div>
                <div class="stat-value">${stats.cruise_passengers.toLocaleString()}</div>
            </div>
        </div>

        <div class="charts-row">
            <div class="chart-container">
                <div class="chart-title">Daily Flight Traffic</div>
                <div id="flights-chart-${monthKey}" class="plotly-graph"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Daily Cruise Traffic</div>
                <div id="cruises-chart-${monthKey}" class="plotly-graph"></div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Combined Tourism Traffic</div>
            <div id="combined-chart-${monthKey}" class="plotly-graph"></div>
        </div>

        <div class="calendar-container">
            <div class="chart-title">Calendar View</div>
            <table class="calendar-table">
                <thead>
                    <tr>
                        <th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th>
                    </tr>
                </thead>
                <tbody id="calendar-${monthKey}">
                </tbody>
            </table>
        </div>
    `;

    // Generate calendar
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    let dayCounter = 1;
    let calendarHTML = '';

    for (let week = 0; week < 6; week++) {
        calendarHTML += '<tr>';
        for (let day = 0; day < 7; day++) {
            if (week === 0 && day < firstDay) {
                calendarHTML += '<td></td>';
            } else if (dayCounter > daysInMonth) {
                calendarHTML += '<td></td>';
            } else {
                const dayStr = `${year}-${month.toString().padStart(2, '0')}-${dayCounter.toString().padStart(2, '0')}`;
                const dayData = stats.daily[dayStr] || {};
                const isWeekend = day === 0 || day === 6 ? ' calendar-weekend' : '';

                calendarHTML += `<td class="${isWeekend}">
                    <span class="calendar-date">${dayCounter}</span>
                    <span class="calendar-flights">Flights: ${dayData.flights_in + dayData.flights_out}</span>
                    <span class="calendar-cruises">Cruises: ${dayData.cruises_in + dayData.cruises_out}</span>
                </td>`;
                dayCounter++;
            }
        }
        calendarHTML += '</tr>';
    }

    document.getElementById(`calendar-${monthKey}`).innerHTML = calendarHTML;

    return section;
}

function renderCharts(monthKey) {
    const monthData = allMonthlyData[monthKey];
    const stats = processMonthlyData(monthData);
    const days = monthData.days || {};
    const daysList = Object.keys(days).sort();
    const [year, month] = monthKey.split('-');
    const monthObj = new Date(year, month - 1);

    let flightData = [], cruiseData = [], netData = [];
    let dayLabels = [];

    for (const dayStr of daysList) {
        const day = parseInt(dayStr.split('-')[2]);
        dayLabels.push(`${monthObj.toLocaleString('default', {month: 'short'})} ${day}`);

        const dayStats = stats.daily[dayStr] || {};
        flightData.push(dayStats.flights_in + dayStats.flights_out);
        cruiseData.push(dayStats.cruises_in + dayStats.cruises_out);
        netData.push((dayStats.flights_in - dayStats.flights_out) + (dayStats.cruises_in - dayStats.cruises_out));
    }

    const darkTemplate = {
        layout: {
            template: 'plotly_dark',
            paper_bgcolor: '#16213e',
            plot_bgcolor: '#0f3460',
            font: { color: '#e0e0e0' },
            margin: { b: 100, t: 20, l: 60, r: 40 }
        },
        config: { responsive: true }
    };

    // Flight traffic chart
    Plotly.newPlot(`flights-chart-${monthKey}`, [{
        x: dayLabels,
        y: flightData,
        type: 'bar',
        marker: { color: '#2E86AB' }
    }], {
        ...darkTemplate.layout,
        xaxis: { title: 'Date', tickangle: 45 },
        yaxis: { title: 'Number of Flights' }
    }, darkTemplate.config);

    // Cruise traffic chart
    Plotly.newPlot(`cruises-chart-${monthKey}`, [{
        x: dayLabels,
        y: cruiseData,
        type: 'bar',
        marker: { color: '#A23B72' }
    }], {
        ...darkTemplate.layout,
        xaxis: { title: 'Date', tickangle: 45 },
        yaxis: { title: 'Number of Cruises' }
    }, darkTemplate.config);

    // Combined chart
    Plotly.newPlot(`combined-chart-${monthKey}`, [
        {
            x: dayLabels,
            y: flightData,
            type: 'bar',
            name: 'Flights',
            marker: { color: '#2E86AB' }
        },
        {
            x: dayLabels,
            y: cruiseData,
            type: 'bar',
            name: 'Cruises',
            marker: { color: '#A23B72' }
        },
        {
            x: dayLabels,
            y: netData,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Net Flow',
            line: { color: '#2ECC40', width: 3 },
            marker: { size: 6 }
        }
    ], {
        ...darkTemplate.layout,
        xaxis: { title: 'Date', tickangle: 45 },
        yaxis: { title: 'Number of Movements' },
        barmode: 'group'
    }, darkTemplate.config);
}
