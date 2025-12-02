# Hurricane Glider Map

A web application for visualizing autonomous underwater vehicle (glider)
deployment tracks on an interactive Leaflet map. Designed for publication-quality
output with PNG export capability.

## Features

- Interactive Leaflet map with USGS Topo basemap
- Colorblind-friendly palette for year-based track coloring (Wong, 2011)
- Dynamic color assignment for any year in the dataset
- Start/end markers (green/black) to distinguish overlapping tracks
- Save to PNG button for publication-ready images
- DuckDB backend for efficient data storage

## Color Palette

Track colors use the colorblind-friendly palette from
[Wong (2011) Nature Methods](https://www.nature.com/articles/nmeth.1618).
Colors are automatically assigned to years in chronological order.

## Installation

```bash
pip install duckdb folium colorama
```

## Usage

### Import GeoJSON Data

```bash
# Single file
python json2duckdb.py --data-file data/<region>/<year>/<file>.json \
                      --db data/db/gliders.db

# Bulk import (walks directory tree)
python json2duckdb.py --data-dir data --db data/db/gliders.db
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
