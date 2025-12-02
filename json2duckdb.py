#!/usr/bin/env python3
"""Import GeoJSON glider deployment data into DuckDB."""

import argparse
import json
import sys
from pathlib import Path

from colorama import Fore, Style, init as colorama_init
import duckdb

colorama_init()


def create_schema(con):
    """Create the deployments table if it doesn't exist."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            region VARCHAR NOT NULL,
            year INTEGER NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            geometry VARCHAR,
            UNIQUE(name, region, year)
        )
    """)
    con.execute("""
        CREATE SEQUENCE IF NOT EXISTS deployments_id_seq START 1
    """)


def extract_metadata(file_path):
    """Extract region, year, and name from file path.

    Expected path structure: .../data/{region}/{year}/{name}.json
    """
    path = Path(file_path)
    name = path.stem
    year = int(path.parent.name)
    region = path.parent.parent.name
    return name, region, year


def parse_geojson(file_path):
    """Parse GeoJSON and return sorted points with timestamps."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    points = []
    for feature in data.get('features', []):
        geom = feature.get('geometry', {})
        props = feature.get('properties', {})

        if geom.get('type') == 'Point':
            coords = geom.get('coordinates', [])
            time_str = props.get('time')
            if len(coords) >= 2 and time_str:
                points.append({
                    'lon': coords[0],
                    'lat': coords[1],
                    'time': time_str
                })

    # Sort by time
    points.sort(key=lambda p: p['time'])
    return points


def points_to_linestring(points):
    """Convert list of points to WKT LineString."""
    if len(points) < 2:
        return None

    coords = [f"{p['lon']} {p['lat']}" for p in points]
    return f"LINESTRING({', '.join(coords)})"


def check_existing(con, name, region, year):
    """Check if deployment already exists in database."""
    existing = con.execute(
        "SELECT id FROM deployments WHERE name = ? AND region = ? AND year = ?",
        [name, region, year]
    ).fetchone()
    return existing is not None


def import_deployment(con, file_path, force=False):
    """Import a single deployment file into the database."""
    name, region, year = extract_metadata(file_path)

    # Check if deployment already exists
    if check_existing(con, name, region, year):
        if not force:
            print(
                f"{Fore.YELLOW}This dataset already exists: "
                f"{name} ({region}/{year}){Style.RESET_ALL}"
            )
            print(
                f"{Fore.YELLOW}Use --force to overwrite{Style.RESET_ALL}"
            )
            return None  # Signal that we skipped (not an error)
        else:
            # Delete existing record
            con.execute(
                "DELETE FROM deployments "
                "WHERE name = ? AND region = ? AND year = ?",
                [name, region, year]
            )
            print(f"Deleted existing deployment: {name} ({region}/{year})")

    points = parse_geojson(file_path)

    if not points:
        print(f"{Fore.RED}Warning: No valid points in {file_path}")
        return False

    geometry = points_to_linestring(points)
    start_time = points[0]['time']
    end_time = points[-1]['time']

    print(f"{Fore.GREEN}Inserting deployment: {name} ({region}/{year})")
    con.execute("""
        INSERT INTO deployments (id, name, region, year,
                                 start_time, end_time, geometry)
        VALUES (nextval('deployments_id_seq'), ?, ?, ?, ?, ?, ?)
    """, [name, region, year, start_time, end_time, geometry])

    return True


def find_json_files(data_dir):
    """Recursively find all .json files in directory."""
    return sorted(Path(data_dir).rglob('*.json'))


def import_single_file(con, data_file, force):
    """Import a single file and return result."""
    if not Path(data_file).exists():
        print(f"{Fore.RED}Error: Data file not found: {data_file}")
        return False

    return import_deployment(con, data_file, force=force)


def import_directory(con, data_dir, force):
    """Import all JSON files from directory tree."""
    json_files = find_json_files(data_dir)

    if not json_files:
        print(f"{Fore.YELLOW}No JSON files found in {data_dir}")
        return False

    print(f"Found {len(json_files)} JSON files")

    stats = {'inserted': 0, 'skipped': 0, 'errors': 0}

    for json_file in json_files:
        result = import_deployment(con, str(json_file), force=force)
        if result is True:
            stats['inserted'] += 1
        elif result is None:
            stats['skipped'] += 1
        else:
            stats['errors'] += 1

    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Inserted: {stats['inserted']}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Skipped:  {stats['skipped']}{Style.RESET_ALL}")
    if stats['errors'] > 0:
        print(f"  {Fore.RED}Errors:   {stats['errors']}{Style.RESET_ALL}")

    return stats['errors'] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Import GeoJSON glider data into DuckDB'
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--data-file',
        help='Path to single GeoJSON file to import'
    )
    source_group.add_argument(
        '--data-dir',
        help='Path to directory tree to scan for JSON files'
    )
    parser.add_argument(
        '--db',
        required=True,
        help='Path to DuckDB database file'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing deployment data'
    )
    args = parser.parse_args()

    con = duckdb.connect(args.db)
    create_schema(con)

    if args.data_file:
        result = import_single_file(con, args.data_file, args.force)
        con.close()
        if result is True:
            print(f"{Fore.GREEN}Import completed successfully{Style.RESET_ALL}")
        elif result is None:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        if not Path(args.data_dir).is_dir():
            print(f"{Fore.RED}Error: Not a directory: {args.data_dir}")
            sys.exit(1)
        success = import_directory(con, args.data_dir, args.force)
        con.close()
        if not success:
            sys.exit(1)


if __name__ == '__main__':
    main()
