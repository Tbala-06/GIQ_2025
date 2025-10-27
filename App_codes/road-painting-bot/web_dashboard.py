"""
Simple Web Dashboard for Road Painting Bot
Displays submissions on a map and provides analytics
Requires: pip install flask folium
"""

from flask import Flask, render_template_string, jsonify
from database import get_db
from datetime import datetime
import json

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Road Painting Bot - Dashboard</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        .header p {
            opacity: 0.9;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }

        .stat-card h3 {
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }

        .stat-card.pending .value { color: #f59e0b; }
        .stat-card.approved .value { color: #10b981; }
        .stat-card.rejected .value { color: #ef4444; }
        .stat-card.total .value { color: #667eea; }

        .map-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
            margin-bottom: 2rem;
        }

        .map-header {
            padding: 1.5rem;
            border-bottom: 1px solid #e5e7eb;
        }

        .map-header h2 {
            font-size: 1.25rem;
            color: #333;
        }

        #map {
            height: 600px;
            width: 100%;
        }

        .legend {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .legend h3 {
            margin-bottom: 1rem;
            color: #333;
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 0.75rem;
        }

        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 0.75rem;
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .loading {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Road Painting Bot Dashboard</h1>
        <p>Real-time monitoring of road damage reports</p>
    </div>

    <div class="container">
        <div class="stats-grid">
            <div class="stat-card total">
                <h3>Total Submissions</h3>
                <div class="value" id="total-submissions">-</div>
            </div>
            <div class="stat-card pending">
                <h3>Pending Review</h3>
                <div class="value" id="pending-submissions">-</div>
            </div>
            <div class="stat-card approved">
                <h3>Approved</h3>
                <div class="value" id="approved-submissions">-</div>
            </div>
            <div class="stat-card rejected">
                <h3>Rejected</h3>
                <div class="value" id="rejected-submissions">-</div>
            </div>
        </div>

        <div class="map-container">
            <div class="map-header">
                <h2>📍 Submission Locations</h2>
            </div>
            <div id="map"></div>
        </div>

        <div class="legend">
            <h3>Legend</h3>
            <div class="legend-item">
                <div class="legend-color" style="background: #f59e0b;"></div>
                <span>Pending Review</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #10b981;"></div>
                <span>Approved</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ef4444;"></div>
                <span>Rejected</span>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Road Painting Bot Dashboard | Last updated: <span id="update-time">-</span></p>
    </div>

    <script>
        // Initialize map
        const map = L.map('map').setView([39.8283, -98.5795], 4); // Center of US

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        // Marker colors
        const markerColors = {
            'pending': '#f59e0b',
            'approved': '#10b981',
            'rejected': '#ef4444'
        };

        // Load data
        async function loadData() {
            try {
                const response = await fetch('/api/submissions');
                const data = await response.json();

                // Update statistics
                document.getElementById('total-submissions').textContent = data.stats.total_submissions;
                document.getElementById('pending-submissions').textContent = data.stats.total_pending;
                document.getElementById('approved-submissions').textContent = data.stats.total_approved;
                document.getElementById('rejected-submissions').textContent = data.stats.total_rejected;

                // Add markers to map
                data.submissions.forEach(submission => {
                    const color = markerColors[submission.status] || '#666';

                    const icon = L.divIcon({
                        className: 'custom-marker',
                        html: `<div style="background: ${color}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
                        iconSize: [24, 24],
                        iconAnchor: [12, 12]
                    });

                    const marker = L.marker([submission.latitude, submission.longitude], { icon: icon })
                        .addTo(map);

                    const popupContent = `
                        <div style="min-width: 200px;">
                            <h4 style="margin-bottom: 0.5rem;">Submission #${submission.id}</h4>
                            <p><strong>Status:</strong> ${submission.status}</p>
                            <p><strong>User:</strong> @${submission.username || 'N/A'}</p>
                            <p><strong>Date:</strong> ${new Date(submission.timestamp).toLocaleString()}</p>
                            ${submission.decision_timestamp ?
                                `<p><strong>Decision:</strong> ${new Date(submission.decision_timestamp).toLocaleString()}</p>` : ''}
                        </div>
                    `;

                    marker.bindPopup(popupContent);
                });

                // Auto-fit map to show all markers
                if (data.submissions.length > 0) {
                    const group = L.featureGroup(
                        data.submissions.map(s => L.marker([s.latitude, s.longitude]))
                    );
                    map.fitBounds(group.getBounds().pad(0.1));
                }

                // Update timestamp
                document.getElementById('update-time').textContent = new Date().toLocaleString();

            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        // Load data on page load
        loadData();

        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/api/submissions')
def api_submissions():
    """API endpoint for submissions data"""
    db = get_db()

    # Get all submissions
    import sqlite3
    from config import Config

    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions ORDER BY timestamp DESC')
    submissions = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Get statistics
    stats = db.get_statistics()

    return jsonify({
        'submissions': submissions,
        'stats': stats
    })


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics only"""
    db = get_db()
    stats = db.get_statistics()
    return jsonify(stats)


def main():
    """Run the web dashboard"""
    print()
    print("=" * 60)
    print("Road Painting Bot - Web Dashboard")
    print("=" * 60)
    print()
    print("Starting web server...")
    print()
    print("Dashboard URL: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
