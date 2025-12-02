# TODO: Hurricane Glider Map Project

## Project Overview
Build a single-page web app displaying autonomous underwater vehicle deployment tracks on a Leaflet map.

## Data Regions
- gcoos
- caracoos
- maracoos
- secoora

## Timeline
Data coverage: 2023, 2024, 2025

## Tasks

### Phase 1: Core Infrastructure
- [ ] Design database schema for DuckDB
- [ ] Create standalone ingest app
  - Takes `--data-file` and `--db` arguments
  - Parses JSON linestring files
  - Updates DuckDB with deployment data

### Phase 2: Map Application
- [ ] Create map generation app
  - Takes `--db` and `--output-path` arguments
  - Produces HTML Leaflet map
- [ ] Implement Leaflet map visualization
  - Display deployment linestrings
  - Color by year (2023, 2024, 2025)
  - All regions use same color scheme (distinguish only by year)
- [ ] Add "Save to PNG" button for publication-quality images

### Phase 3: Testing & Iteration
- [ ] Test with initial gcoos sample file
- [ ] Add and test additional files from each region
- [ ] Validate data ingestion as new files are added
- [ ] Quality assurance for publication-ready output
