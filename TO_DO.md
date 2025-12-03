# TODO: GDAMM (GDAC Automated Map Maker)

## Project Overview
A command-line tool for importing glider deployment data and generating
publication-quality Leaflet maps.

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
  - Optional start/end markers (--markers)
  - Optional title banner (--title)
  - Deployment counts in legend
- [x] Add "Save to PNG" button for publication-quality images

### Phase 3: Testing & Iteration
- [x] Test with initial gcoos sample file
- [x] Add and test additional files from each region
- [x] Validate data ingestion as new files are added
- [x] Quality assurance for publication-ready output

## Phase 4: GDAC Integration via erddapy

### 4.1 Argument Parser Changes (`gdamm_gdac.py`)
- [ ] Add `--gdac` to mutually exclusive group (with --data-file, --data-dir)
- [ ] Add `--region` argument (gcoos, caracoos, maracoos, secoora)
- [ ] Add `--contributor` argument (filter by institution)
- [ ] Add `--start-date` argument (required with --gdac)
- [ ] Add `--end-date` argument (required with --gdac)
- [ ] Add validation: --gdac requires --start-date and --end-date
- [ ] Add validation: --gdac requires at least one of --region or --contributor

### 4.2 New Functions
- [ ] `fetch_gdac_deployments(region, contributor, start_date, end_date)`
  - Connect to IOOS Glider DAC ERDDAP (https://gliders.ioos.us/erddap/)
  - Build query with filters
  - Return list of deployment metadata
- [ ] `fetch_deployment_track(deployment_id)`
  - Fetch trajectory data for single deployment
  - Return points with timestamps
- [ ] `convert_erddap_to_linestring(track_data)`
  - Convert ERDDAP response to WKT LineString
  - Extract start/end times

### 4.3 Dependencies
- [ ] Add `erddapy` to requirements

### 4.4 Testing
- [ ] Args: `--gdac` without dates should error
- [ ] Args: `--gdac` without region/contributor should error
- [ ] Args: `--gdac` with only `--region` works
- [ ] Args: `--gdac` with only `--contributor` works
- [ ] Args: `--gdac` with both `--region` and `--contributor` works
- [ ] Integration: Fetch single deployment from GDAC
- [ ] Integration: Fetch multiple deployments with date range
- [ ] Integration: Verify data imports correctly to DuckDB
- [ ] End-to-end: Import via `--gdac`, generate map with `gdamm_map.py`

### 4.5 Documentation
- [ ] Update README.md with --gdac usage examples
- [ ] Update CLAUDE.md with new functions and arguments

## Future Enhancements

### Nice to Have
- [ ] Add `--list` mode to show available deployments without importing
- [ ] Add `--dry-run` to preview what would be imported
- [ ] Support additional ERDDAP filters (depth, platform type, etc.)
