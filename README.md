# GDAMM - GDAC Automated Map Maker

A command-line tool for visualizing autonomous underwater vehicle (glider)
deployment tracks on interactive Leaflet maps. Designed for publication-quality
output with PNG export capability.

![Example GDAMM output](gdamm_map.png)

## Features

- Fetch deployment data directly from IOOS Glider DAC
- Import GeoJSON files from any directory structure
- Year automatically extracted from deployment ID (e.g., `bass-20250601T0000`)
- Interactive HTML map with USGS Topo basemap
- Colorblind-friendly palette (Wong, 2011) for year-based track coloring
- Custom title banner for presentations
- Optional start/end markers to distinguish overlapping tracks
- Save to PNG button for publication-ready images
- Fast: 30 deployments fetched, imported, and mapped in under a minute
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

Create a text file with deployment IDs (one per line):

```text
bass-20250601T0000
ori-20251001T0000
mote-holly-20250805T0000
```

Then fetch the GeoJSON data:

```bash
python gdamm_fetch.py --deployments-file data/my_deployments.txt \
                      --output-path data/gcoos
```

You can organize files however you like. The year is extracted automatically
from each deployment ID filename, so no specific folder structure is required.

### Import GeoJSON Data

```bash
# Single file
python gdamm_gdac.py --data-file data/gcoos/bass-20250601T0000.json \
                      --db data/db/gdamm.db

# Bulk import (walks directory tree)
python gdamm_gdac.py --data-dir data/gcoos --db data/db/gdamm.db
```

The import tool extracts metadata from each filename:
- **Year**: From the timestamp (e.g., `20250601` → 2025)
- **Name**: Everything before the timestamp (e.g., `mote-holly`)
- **Region**: The parent folder name

Files with invalid names are skipped with a warning.

Options:
- `--force`: Overwrite existing deployment data

### Generate Map

```bash
# Basic map
python gdamm_map.py --db data/db/gdamm.db \
                     --output-path maps/glider_tracks.html

# With title and markers
python gdamm_map.py --db data/db/gdamm.db \
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

GeoJSON files can be stored anywhere. The import tool extracts metadata from
filenames, so no specific folder structure is required.

The database name and location are user-defined via the `--db` argument. You
can create separate databases for different projects:

```bash
python gdamm_gdac.py --data-dir data/gcoos --db data/db/gcoos.db
python gdamm_gdac.py --data-dir data/secoora --db data/db/secoora.db
```

## Color Palette

Track colors use the colorblind-friendly palette from
[Wong (2011) Nature Methods](https://www.nature.com/articles/nmeth.1618).
Colors are automatically assigned to years in chronological order.

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

Future versions will support fetching and importing in a single command:

```bash
# Fetch from GDAC and import directly (planned)
python gdamm_gdac.py --fetch --deployments-file data/list.txt \
                      --db data/db/gdamm.db
```
