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


def add_track_markers(m, coords, name):
    """Add start/end markers for a deployment track."""
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


def add_deployment_track(m, deployment, year_colors, show_markers):
    """Add a single deployment track to the map."""
    name, region, year, geometry = deployment
    coords = parse_linestring(geometry)
    if not coords:
        return

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
        add_track_markers(m, coords, name)


def create_map(deployments, year_colors, show_markers=False):
    """Create a Folium map with deployment tracks."""
    bounds = calculate_bounds(deployments)
    if not bounds:
        print("Error: No valid coordinates found")
        return None

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

    for deployment in deployments:
        add_deployment_track(m, deployment, year_colors, show_markers)

    m.fit_bounds(bounds)
    return m


def build_year_items_html(active_years, year_colors, year_counts):
    """Build HTML for year legend items."""
    items = ''
    for year in sorted(active_years):
        color = year_colors.get(year, '#999999')
        count = year_counts.get(year, 0)
        items += f'''
            <div style="display: flex; align-items: center; margin: 3px 0;">
                <span style="background-color: {color}; width: 20px;
                             height: 4px; margin-right: 8px;"></span>
                <span>{year}: {count}</span>
            </div>'''
    return items


def build_marker_legend_html():
    """Build HTML for start/end marker legend."""
    flex_style = 'display:flex;align-items:center;margin:3px 0'
    dot = 'width:10px;height:10px;border-radius:50%;margin-right:8px'
    return f'''
            <div style="border-top:1px solid #ccc;margin-top:8px;
                        padding-top:8px;">
                <div style="{flex_style};">
                    <span style="background-color:#009E73;{dot};"></span>
                    <span>Start</span>
                </div>
                <div style="{flex_style};">
                    <span style="background-color:black;{dot};"></span>
                    <span>End</span>
                </div>
            </div>'''


def build_legend_html(legend_items, total, marker_legend):
    """Build complete legend HTML."""
    total_row = f'''
            <div style="border-top: 1px solid #ccc; margin-top: 8px;
                        padding-top: 8px; font-weight: bold;">
                Total: {total}
            </div>'''

    return f'''
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
            {total_row}
            {marker_legend}
        </div>
    '''


def add_legend(m, active_years, year_colors, year_counts, show_markers=False):
    """Add a year-based legend as a map control (included in PNG export)."""
    from branca.element import MacroElement, Template

    legend_items = build_year_items_html(
        active_years, year_colors, year_counts
    )
    marker_legend = build_marker_legend_html() if show_markers else ''
    total = sum(year_counts.values())
    legend_html = build_legend_html(legend_items, total, marker_legend)

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


def get_save_button_css():
    """Return CSS for save button styling."""
    return '''
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
    </style>'''


def get_save_button_js():
    """Return JavaScript for save button functionality."""
    return '''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var mapContainer = document.querySelector('.folium-map');
        var btn = document.createElement('button');
        btn.className = 'save-button';
        btn.innerHTML = 'Save to PNG';
        mapContainer.appendChild(btn);
        function resetBtn() {
            btn.style.display = 'block';
            btn.disabled = false;
            btn.innerHTML = 'Save to PNG';
        }
        btn.onclick = function() {
            btn.disabled = true;
            btn.innerHTML = 'Generating...';
            btn.style.display = 'none';
            setTimeout(function() {
                domtoimage.toPng(mapContainer, {quality: 1.0, bgcolor: '#fff'})
                .then(function(dataUrl) {
                    var link = document.createElement('a');
                    link.download = 'hurricane_glider_map.png';
                    link.href = dataUrl;
                    link.click();
                    resetBtn();
                })
                .catch(function(e) {
                    console.error('Error:', e);
                    resetBtn();
                    alert('Error generating image. Try again.');
                });
            }, 500);
        };
    });
    </script>'''


def add_save_button(m):
    """Add Save to PNG button using dom-to-image for proper map capture."""
    lib_url = (
        'https://unpkg.com/dom-to-image-more@3.3.0/'
        'dist/dom-to-image-more.min.js'
    )
    save_script = f'''
    <script src="{lib_url}"></script>
    {get_save_button_css()}
    {get_save_button_js()}
    '''
    m.get_root().html.add_child(folium.Element(save_script))


def add_title(m, title):
    """Add a professional title banner to the map."""
    from branca.element import MacroElement, Template

    title_html = f'''
        <div id="map-title" style="
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 4px;
            border: 3px solid black;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
            font-family: 'Georgia', 'Times New Roman', serif;
            text-align: center;">
            <div style="font-size: 18px; font-weight: bold; color: #003366;
                        letter-spacing: 0.5px;">
                {title}
            </div>
        </div>
    '''

    class TitleControl(MacroElement):
        """Custom title control that renders at top center of map."""

        def __init__(self, html):
            super().__init__()
            self._template = Template(f'''
                {{% macro script(this, kwargs) %}}
                var mapObj = {{{{this._parent.get_name()}}}};
                var titleControl = L.control({{position: 'topcenter'}});

                // Add topcenter position to Leaflet if not exists
                if (!L.Control.prototype._topcenter) {{
                    var corners = mapObj._controlCorners;
                    var container = mapObj._controlContainer;
                    corners['topcenter'] = L.DomUtil.create(
                        'div', 'leaflet-top leaflet-center', container
                    );
                    corners['topcenter'].style.left = '50%';
                    corners['topcenter'].style.transform = 'translateX(-50%)';
                    corners['topcenter'].style.marginTop = '10px';
                }}

                titleControl.onAdd = function(map) {{
                    var div = L.DomUtil.create('div', 'title-control');
                    div.innerHTML = `{html}`;
                    return div;
                }};
                titleControl.addTo(mapObj);
                {{% endmacro %}}
            ''')

    m.add_child(TitleControl(title_html))


def parse_args():
    """Parse command line arguments."""
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
    parser.add_argument(
        '--title',
        help='Title to display on map'
    )
    return parser.parse_args()


def count_deployments_by_year(deployments):
    """Count deployments per year."""
    year_counts = {}
    for d in deployments:
        year_counts[d[2]] = year_counts.get(d[2], 0) + 1
    return year_counts


def main():
    """Main entry point."""
    args = parse_args()

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
    year_counts = count_deployments_by_year(deployments)
    print(f"Years: {sorted(active_years)}")

    m = create_map(deployments, year_colors, show_markers=args.markers)
    if not m:
        sys.exit(1)

    add_legend(
        m, active_years, year_colors, year_counts, show_markers=args.markers
    )
    add_save_button(m)
    if args.title:
        add_title(m, args.title)

    print(f"Saving map to {args.output_path}...")
    m.save(args.output_path)
    print("Map created successfully")


if __name__ == '__main__':
    main()
