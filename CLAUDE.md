# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project: GDAMM (GDAC Automated Map Maker)

## Commands

### Import deployment data
```bash
# Single file (path must follow data/<region>/<year>/<name>.json structure)
python json2duckdb.py --data-file data/gcoos/2024/deployment.json \
                      --db data/db/gliders.db [--force]

# Bulk import (recursively finds all .json files)
python json2duckdb.py --data-dir data --db data/db/gliders.db [--force]
```

### Generate map
```bash
python create_map.py --db data/db/gliders.db --output-path maps/glider_tracks.html
```

Optional arguments:
- `--title "Title Text"`: Add title banner to map
- `--markers`: Show start/end markers on tracks

### Query database
```bash
python -c "import duckdb; \
  print(duckdb.connect('data/db/gliders.db').execute( \
    'SELECT * FROM deployments').fetchdf())"
```

## Architecture

### Data Pipeline
1. GeoJSON files (Point features with timestamps) stored in `data/<region>/<year>/`
2. `json2duckdb.py` parses GeoJSON, converts points to WKT LineString, stores in
   DuckDB with metadata (name, region, year, start/end times)
3. `create_map.py` queries DuckDB, renders Folium/Leaflet map with year-colored
   tracks, start/end markers, and PNG export capability

### Key Functions
- `json2duckdb.py`:
  - `extract_metadata()` - parses region/year/name from file path structure
  - `parse_geojson()` - reads GeoJSON, extracts time-sorted points
  - `points_to_linestring()` - converts points to WKT LineString
- `create_map.py`:
  - `create_map()` - builds Folium map with deployment tracks
  - `add_legend()` - adds Leaflet control with year colors and counts
  - `add_title()` - adds centered title banner via custom Leaflet control

### Database Schema (DuckDB)
- **deployments**: id, name, region, year, start_time, end_time, geometry (WKT)
- Unique constraint on (name, region, year)

### Map Features
- USGS Topo basemap (includes "Gulf of America" labeling)
- Colorblind-friendly palette from Wong (2011) Nature Methods
- Colors auto-assigned to years in chronological order
- Optional start/end markers (green=start, black=end)
- Optional title banner
- Deployment counts in legend
- PNG export via dom-to-image-more library

## Dependencies

- duckdb
- folium (includes branca)
- colorama
