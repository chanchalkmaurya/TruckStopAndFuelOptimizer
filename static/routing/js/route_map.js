let map, routeLayer, markersLayer;

function initMap() {
    map = L.map('map').setView([39.5, -95], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
}

function getCookie(name) {
    let value = null;
    document.cookie.split(';').forEach(cookie => {
        const [key, val] = cookie.trim().split('=');
        if (key === name) value = decodeURIComponent(val);
    });
    return value;
}

function showError(message) {
    const box = document.getElementById('error-box');
    box.textContent = message;
    box.style.display = 'block';
}

function hideError() {
    document.getElementById('error-box').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    initMap();

    const form = document.getElementById('route-form');
    const submitBtn = document.getElementById('submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const start = document.getElementById('start').value.trim();
        const end = document.getElementById('end').value.trim();

        if (!start || !end) {
            showError('Please enter both a start and end location.');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Loading...';

        try {
            const resp = await fetch('/api/route/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ start, end })
            });

            const data = await resp.json();

            if (!resp.ok) {
                showError(data.error || 'Something went wrong while fetching the route.');
                return;
            }

            renderResult(data);
        } catch (err) {
            showError('Network error: ' + err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Get Route';
        }
    });
});

function renderResult(data) {
    document.getElementById('summary-cards').style.display = 'grid';
    document.getElementById('dist-val').textContent = `${data.total_distance_miles} mi`;
    document.getElementById('cost-val').textContent = `$${data.total_fuel_cost.toFixed(2)}`;
    document.getElementById('stops-val').textContent = data.fuel_stops.length;

    if (routeLayer) map.removeLayer(routeLayer);
    if (markersLayer) map.removeLayer(markersLayer);

    routeLayer = L.polyline(data.route_geometry, { color: '#0ec049', weight: 4 }).addTo(map);
    map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });

    markersLayer = L.layerGroup().addTo(map);

    const startCoord = data.route_geometry[0];
    const endCoord = data.route_geometry[data.route_geometry.length - 1];

    L.marker(startCoord).bindPopup('<b>Start</b>').addTo(markersLayer);
    L.marker(endCoord).bindPopup('<b>Finish</b>').addTo(markersLayer);

    data.fuel_stops.forEach((stop, i) => {
        L.circleMarker([stop.latitude, stop.longitude], {
            radius: 8,
            color: '#c9f81f',
            fillColor: '#1D9E75',
            fillOpacity: 1,
            weight: 2
        })
        .bindPopup(
            `<b>Stop ${i + 1}: ${stop.station_name}</b><br>` +
            `${stop.city}, ${stop.state}<br>` +
            `$${stop.price.toFixed(3)}/gal &mdash; ${stop.gallons_purchased} gal &mdash; $${stop.cost.toFixed(2)}`
        )
        .addTo(markersLayer);
    });
    

    renderTable(data.fuel_stops);
}

function renderTable(stops) {
    const container = document.getElementById('fuel-stops');

    if (!stops.length) {
        container.innerHTML = '<p>No fuel stops needed for this route.</p>';
        return;
    }

    let html = `<table>
        <thead>
            <tr>
                <th>#</th><th>Station</th><th>Location</th>
                <th>Price/gal</th><th>Distance into route</th>
                <th>Gallons</th><th>Cost</th>
            </tr>
        </thead>
        <tbody>`;

    stops.forEach((s, i) => {
        html += `<tr>
            <td>${i + 1}</td>
            <td>${s.station_name}</td>
            <td>${s.city}, ${s.state}</td>
            <td>$${s.price.toFixed(3)}</td>
            <td>${s.distance_into_route_miles} mi</td>
            <td>${s.gallons_purchased}</td>
            <td>$${s.cost.toFixed(2)}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}