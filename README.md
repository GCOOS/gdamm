# Hurricane Glider Map

A web application for visualizing autonomous underwater vehicle (glider)
deployment tracks on an interactive Leaflet map. Designed for publication-quality
output with PNG export capability.

## Features

- Interactive Leaflet map with USGS Topo basemap
- Year-based color coding for deployment tracks (2023, 2024, 2025)
- Start/end markers (green/red) to distinguish overlapping tracks
- Save to PNG button for publication-ready images
- DuckDB backend for efficient data storage

## Installation

```bash
pip install duckdb folium colorama
```

## Usage

### Import GeoJSON Data

```bash
python json2duckdb.py --data-file data/<region>/<year>/<file>.json \
                      --db data/db/gliders.db
```

Options:
- `--force`: Overwrite existing deployment data

### Generate Map

```bash
python create_map.py --db data/db/gliders.db \
                     --output-path maps/glider_tracks.html
```

## Data Structure

```
data/
├── db/
│   └── gliders.db
├── gcoos/
│   └── 2023/
├── caracoos/
├── maracoos/
└── secoora/
```

GeoJSON files should contain Point features with `time` properties. The import
tool converts these to LineString geometries ordered by timestamp.

## Regions

- **gcoos**: Gulf of America Coastal Ocean Observing System
- **caracoos**: Caribbean Coastal Ocean Observing System
- **maracoos**: Mid-Atlantic Regional Association Coastal Ocean Observing System
- **secoora**: Southeast Coastal Ocean Observing Regional Association
