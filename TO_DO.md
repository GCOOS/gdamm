# TODO: Hurricane Glider Map Project

## Project Overview
Build a single-page web app displaying autonomous underwater vehicle deployment
tracks on a Leaflet map.

## Data Regions
- gcoos
- caracoos
- maracoos
- secoora

## Timeline
Data coverage: 2023, 2024, 2025

## Tasks

### Phase 1: Core Infrastructure
- [x] Design database schema for DuckDB
- [x] Create standalone ingest app
  - Takes `--data-file` and `--db` arguments
  - Takes `--data-dir` for bulk import
  - Parses JSON linestring files
  - Updates DuckDB with deployment data

### Phase 2: Map Application
- [x] Create map generation app
  - Takes `--db` and `--output-path` arguments
  - Produces HTML Leaflet map
- [x] Implement Leaflet map visualization
  - Display deployment linestrings
  - Colorblind-friendly palette (Wong, 2011)
  - Dynamic color assignment for any year
  - Start/end markers to distinguish overlapping tracks
- [x] Add "Save to PNG" button for publication-quality images

### Phase 3: Testing & Iteration
- [x] Test with initial gcoos sample file
- [x] Add and test additional files from each region
- [x] Validate data ingestion as new files are added
- [ ] Quality assurance for publication-ready output

## Future Enhancements

### Nice to Have
- [ ] Integrate erddapy for direct GDAC data retrieval
  - Add `--gdac` argument to json2duckdb.py
  - Pull deployment data directly from IOOS Glider DAC ERDDAP
  - Eliminate manual download step
  - Reference: https://github.com/ioos/erddapy
