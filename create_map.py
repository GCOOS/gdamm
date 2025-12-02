#!/usr/bin/env python3
"""Generate a Leaflet map from glider deployment data in DuckDB."""

import argparse
import sys
from pathlib import Path

import duckdb
import folium


# Colorblind-friendly palette (based on Wong, 2011 - Nature Methods)
# https://www.nature.com/articles/nmeth.1618
COLORBLIND_PALETTE = [
    '#0072B2',  # Blue
    '#D55E00',  # Vermillion
    '#009E73',  # Bluish green
    '#CC79A7',  # Reddish purple
    '#F0E442',  # Yellow
    '#56B4E9',  # Sky blue
    '#E69F00',  # Orange
]


def generate_year_colors(years):
    """Generate color mapping for years using colorblind-friendly palette."""
    sorted_years = sorted(years)
    colors = {}
    for i, year in enumerate(sorted_years):
        colors[year] = COLORBLIND_PALETTE[i % len(COLORBLIND_PALETTE)]
    return colors


def get_deployments(db_path):
    """Fetch all deployments from the database."""
    con = duckdb.connect(db_path, read_only=True)
    query = """
        SELECT name, region, year, geometry
        FROM deployments
        WHERE geometry IS NOT NULL
        ORDER BY year, region, name
    """
    results = con.execute(query).fetchall()
    con.close()
    return results


def parse_linestring(wkt):
    """Parse WKT LineString to list of [lat, lon] coordinates."""
    # WKT format: LINESTRING(lon1 lat1, lon2 lat2, ...)
    if not wkt or not wkt.startswith('LINESTRING('):
        return []

    coords_str = wkt[11:-1]  # Remove 'LINESTRING(' and ')'
    coords = []

    for pair in coords_str.split(', '):
        parts = pair.strip().split(' ')
        if len(parts) >= 2:
            lon, lat = float(parts[0]), float(parts[1])
            coords.append([lat, lon])  # Leaflet uses [lat, lon]

    return coords


def calculate_bounds(deployments):
    """Calculate map bounds from all deployments."""
    all_lats = []
    all_lons = []

    for _, _, _, geometry in deployments:
        coords = parse_linestring(geometry)
        for lat, lon in coords:
            all_lats.append(lat)
            all_lons.append(lon)

    if not all_lats:
        return None

    return [[min(all_lats), min(all_lons)], [max(all_lats), max(all_lons)]]


def create_map(deployments, year_colors, show_markers=False):
    """Create a Folium map with deployment tracks."""
    bounds = calculate_bounds(deployments)
    if not bounds:
        print("Error: No valid coordinates found")
        return None

    # Create map centered on data
    center_lat = (bounds[0][0] + bounds[1][0]) / 2
    center_lon = (bounds[0][1] + bounds[1][1]) / 2

    usgs_topo = (
        'https://basemap.nationalmap.gov/arcgis/rest/services/'
        'USGSTopo/MapServer/tile/{z}/{y}/{x}'
    )
    usgs_attr = 'U.S. Department of the Interior | U.S. Geological Survey'

    m = folium.Map(
        location=[center_lat, center_lon],
        tiles=usgs_topo,
        attr=usgs_attr,
        zoom_start=6,
        max_zoom=16
    )

    # Add deployment tracks with start/end markers
    for name, region, year, geometry in deployments:
        coords = parse_linestring(geometry)
        if not coords:
            continue

        color = year_colors.get(year, '#999999')
        tooltip = f"{name} ({region}, {year})"

        folium.PolyLine(
            locations=coords,
            weight=2,
            color=color,
            opacity=0.8,
            tooltip=tooltip
        ).add_to(m)

        if show_markers:
            # Start marker (Wong bluish green)
            folium.CircleMarker(
                location=coords[0],
                radius=4,
                color='#009E73',
                fill=True,
                fill_color='#009E73',
                fill_opacity=1.0,
                tooltip=f"Start: {name}"
            ).add_to(m)

            # End marker (black)
            folium.CircleMarker(
                location=coords[-1],
                radius=4,
                color='black',
                fill=True,
                fill_color='black',
                fill_opacity=1.0,
                tooltip=f"End: {name}"
            ).add_to(m)

    # Fit map to bounds
    m.fit_bounds(bounds)

    return m


def add_legend(m, active_years, year_colors, show_markers=False):
    """Add a year-based legend as a map control (included in PNG export)."""
    legend_items = ''
    for year in sorted(active_years):
        color = year_colors.get(year, '#999999')
        legend_items += f'''
            <div style="display: flex; align-items: center; margin: 3px 0;">
                <span style="background-color: {color}; width: 20px;
                             height: 4px; margin-right: 8px;"></span>
                <span>{year}</span>
            </div>'''

    marker_legend = ''
    if show_markers:
        marker_legend = '''
            <div style="border-top: 1px solid #ccc; margin-top: 8px;
                        padding-top: 8px;">
                <div style="display: flex; align-items: center; margin: 3px 0;">
                    <span style="background-color: #009E73; width: 10px;
                                 height: 10px; border-radius: 50%;
                                 margin-right: 8px;"></span>
                    <span>Start</span>
                </div>
                <div style="display: flex; align-items: center; margin: 3px 0;">
                    <span style="background-color: black; width: 10px;
                                 height: 10px; border-radius: 50%;
                                 margin-right: 8px;"></span>
                    <span>End</span>
                </div>
            </div>'''

    legend_html = f'''
        <div id="map-legend" style="
            padding: 10px 14px;
            background: white;
            border-radius: 5px;
            border: 2px solid rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;">
            <div style="font-weight: bold; margin-bottom: 5px;">
                Deployment Year
            </div>
            {legend_items}
            {marker_legend}
        </div>
    '''

    from branca.element import MacroElement, Template

    class LegendControl(MacroElement):
        """Custom legend control that renders inside the map."""

        def __init__(self, html):
            super().__init__()
            self._template = Template(f'''
                {{% macro script(this, kwargs) %}}
                var legend = L.control({{position: 'bottomleft'}});
                legend.onAdd = function(map) {{
                    var div = L.DomUtil.create('div', 'legend-control');
                    div.innerHTML = `{html}`;
                    return div;
                }};
                legend.addTo({{{{this._parent.get_name()}}}});
                {{% endmacro %}}
            ''')

    m.add_child(LegendControl(legend_html))


def add_save_button(m):
    """Add Save to PNG button using dom-to-image for proper map capture."""
    save_script = '''
    <script src="https://unpkg.com/dom-to-image-more@3.3.0/dist/dom-to-image-more.min.js"></script>
    <style>
        .save-button {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-family: Arial, sans-serif;
        }
        .save-button:hover { background-color: #45a049; }
        .save-button:disabled { background-color: #cccccc; cursor: wait; }
    </style>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var mapContainer = document.querySelector('.folium-map');
        var btn = document.createElement('button');
        btn.className = 'save-button';
        btn.innerHTML = 'Save to PNG';
        mapContainer.appendChild(btn);

        btn.onclick = function() {
            btn.disabled = true;
            btn.innerHTML = 'Generating...';

            // Hide the button during capture
            btn.style.display = 'none';

            // Wait for tiles to finish loading
            setTimeout(function() {
                domtoimage.toPng(mapContainer, {
                    quality: 1.0,
                    bgcolor: '#ffffff',
                    style: {
                        'transform': 'none'
                    }
                })
                .then(function(dataUrl) {
                    var link = document.createElement('a');
                    link.download = 'hurricane_glider_map.png';
                    link.href = dataUrl;
                    link.click();

                    btn.style.display = 'block';
                    btn.disabled = false;
                    btn.innerHTML = 'Save to PNG';
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    btn.style.display = 'block';
                    btn.disabled = false;
                    btn.innerHTML = 'Save to PNG';
                    alert('Error generating image. Try again.');
                });
            }, 500);
        };
    });
    </script>
    '''
    m.get_root().html.add_child(folium.Element(save_script))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Leaflet map from glider deployment data'
    )
    parser.add_argument(
        '--db',
        required=True,
        help='Path to DuckDB database file'
    )
    parser.add_argument(
        '--output-path',
        required=True,
        help='Path to save the HTML map'
    )
    parser.add_argument(
        '--markers',
        action='store_true',
        help='Show start/end markers on tracks'
    )
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"Error: Database not found: {args.db}")
        sys.exit(1)

    print("Fetching deployments from database...")
    deployments = get_deployments(args.db)
    print(f"Found {len(deployments)} deployments")

    if not deployments:
        print("Error: No deployments found in database")
        sys.exit(1)

    print("Creating map...")
    active_years = set(d[2] for d in deployments)
    year_colors = generate_year_colors(active_years)
    print(f"Years: {sorted(active_years)}")

    m = create_map(deployments, year_colors, show_markers=args.markers)
    if not m:
        sys.exit(1)

    add_legend(m, active_years, year_colors, show_markers=args.markers)
    add_save_button(m)

    print(f"Saving map to {args.output_path}...")
    m.save(args.output_path)
    print("Map created successfully")


if __name__ == '__main__':
    main()
