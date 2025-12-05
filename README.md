# GDAMM - GDAC Automated Map Maker

A command-line tool for visualizing autonomous underwater vehicle (glider)
deployment tracks on interactive Leaflet maps. Designed for publication-quality
output with PNG export capability.

![Example GDAMM output](gdamm_map.png)

## Features

- Import glider deployment data from GeoJSON files
- Bulk import from directory trees
- Interactive Leaflet map with USGS Topo basemap
- Colorblind-friendly palette (Wong, 2011) for year-based track coloring
- Dynamic color assignment for any year in the dataset
- Optional start/end markers to distinguish overlapping tracks
- Optional title banner for presentations
- Deployment counts per year in legend
- Save to PNG button for publication-ready images
- DuckDB backend for efficient data storage

## Installation

```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Fetch Data from GDAC

```bash
# Create a file with deployment IDs (one per line)
# e.g., data/my_deployments.txt containing:
#   bass-20250601T0000
#   ori-20251001T0000

# Fetch GeoJSON for all deployments
python gdamm_fetch.py --deployments-file data/my_deployments.txt \
                      --output-path data/gcoos/2025
```

### Import GeoJSON Data

```bash
# Single file
python gdamm_gdac.py --data-file data/<region>/<year>/<file>.json \
                      --db data/db/gliders.db

# Bulk import (walks directory tree)
python gdamm_gdac.py --data-dir data --db data/db/gliders.db
```

Options:
- `--force`: Overwrite existing deployment data

### Generate Map

```bash
# Basic map
python gdamm_map.py --db data/db/gliders.db \
                     --output-path maps/glider_tracks.html

# With title and markers
python gdamm_map.py --db data/db/gliders.db \
                     --output-path maps/glider_tracks.html \
                     --title "My Glider Deployments" \
                     --markers
```

### View the Map

Open the generated HTML file in your web browser:

```bash
# macOS
open maps/glider_tracks.html

# Linux
xdg-open maps/glider_tracks.html

# Windows
start maps/glider_tracks.html
```

Or simply double-click the `.html` file in your file manager. **Note:** The
`.json` files in the `data/` directory are raw input data, not viewable maps.

Options:
- `--title`: Add title banner to map
- `--markers`: Show start/end markers on tracks

## Finding Deployment IDs

Deployment IDs can be found on the
[IOOS Glider DAC ERDDAP](https://gliders.ioos.us/erddap/tabledap/index.html).
Each deployment has an ID like `bass-20250601T0000` or `ori-20251001T0000`.

Create a text file with one deployment ID per line, then use `gdamm_fetch.py`
to download the GeoJSON data automatically.

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

## Color Palette

Track colors use the colorblind-friendly palette from
[Wong (2011) Nature Methods](https://www.nature.com/articles/nmeth.1618).
Colors are automatically assigned to years in chronological order.

## Regions

- **gcoos**: Gulf of America Coastal Ocean Observing System
- **caracoos**: Caribbean Coastal Ocean Observing System
- **maracoos**: Mid-Atlantic Regional Association Coastal Ocean Observing System
- **secoora**: Southeast Coastal Ocean Observing Regional Association

## Current Status

Tested with 30 deployments across 4 regions (2023-2025):

| Component | Status |
|-----------|--------|
| GDAC fetch | ✓ Passing |
| Data import (single file) | ✓ Passing |
| Data import (bulk) | ✓ Passing |
| Data import (--force) | ✓ Passing |
| Map generation | ✓ Passing |
| Title banner (--title) | ✓ Passing |
| Start/end markers (--markers) | ✓ Passing |
| PNG export | ✓ Passing |
| PEP-8 compliance | ✓ Passing |

## Coming Soon

### Integrated GDAC Fetch + Import

Future versions will support fetching and importing in a single command:

```bash
# Fetch from GDAC and import directly (planned)
python gdamm_gdac.py --fetch --region gcoos --year 2025 --db data/db/gliders.db
```
