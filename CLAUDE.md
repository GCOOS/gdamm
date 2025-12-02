# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Commands

### Import deployment data
```bash
# Single file
python json2duckdb.py --data-file <geojson> --db data/db/gliders.db [--force]

# Bulk import
python json2duckdb.py --data-dir data --db data/db/gliders.db [--force]
```

### Generate map
```bash
python create_map.py --db data/db/gliders.db --output-path maps/glider_tracks.html
```

### Query database
```bash
python -c "import duckdb; print(duckdb.connect('data/db/gliders.db').execute('SELECT * FROM deployments').fetchdf())"
```

## Architecture

### Data Pipeline
1. GeoJSON files (Point features with timestamps) stored in `data/<region>/<year>/`
2. `json2duckdb.py` parses GeoJSON, converts points to WKT LineString, stores in
   DuckDB with metadata (name, region, year, start/end times)
3. `create_map.py` queries DuckDB, renders Folium/Leaflet map with year-colored
   tracks, start/end markers, and PNG export capability

### Database Schema (DuckDB)
- **deployments**: id, name, region, year, start_time, end_time, geometry (WKT)
- Unique constraint on (name, region, year)

### Map Features
- USGS Topo basemap (includes "Gulf of America" labeling)
- Colorblind-friendly palette from Wong (2011) Nature Methods
- Colors auto-assigned to years in chronological order
- Green circle = deployment start, Black circle = deployment end
- PNG export via dom-to-image-more library

## Dependencies

- duckdb
- folium
- colorama
