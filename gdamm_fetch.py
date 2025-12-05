#!/usr/bin/env python3
"""Fetch glider deployment GeoJSON data from GDAC."""

import argparse
import sys
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

from gdac_client import fetch_deployment_geojson

colorama_init()


def read_deployment_ids(file_path):
    """Read deployment IDs from file, one per line.

    Args:
        file_path: Path to file containing deployment IDs

    Returns:
        List of deployment ID strings (whitespace stripped, blanks removed)
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]


def save_geojson(geojson_str, output_path, deployment_id):
    """Save GeoJSON string to file.

    Args:
        geojson_str: GeoJSON content as string
        output_path: Directory to save file
        deployment_id: Used for filename

    Returns:
        Path to saved file
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{deployment_id}.json"
    with open(file_path, 'w') as f:
        f.write(geojson_str)
    return file_path


def fetch_deployments(deployment_ids, output_path):
    """Fetch and save GeoJSON for multiple deployments.

    Args:
        deployment_ids: List of deployment IDs to fetch
        output_path: Directory to save GeoJSON files

    Returns:
        Tuple of (success_count, error_count)
    """
    stats = {'fetched': 0, 'errors': 0}

    for dep_id in deployment_ids:
        try:
            print(f"Fetching {dep_id}...", end=" ")
            geojson = fetch_deployment_geojson(dep_id)
            save_geojson(geojson, output_path, dep_id)
            print(f"{Fore.GREEN}OK{Style.RESET_ALL}")
            stats['fetched'] += 1
        except ValueError as e:
            print(f"{Fore.RED}FAILED: {e}{Style.RESET_ALL}")
            stats['errors'] += 1

    return stats['fetched'], stats['errors']


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch glider deployment GeoJSON from GDAC'
    )
    parser.add_argument(
        '--deployments-file',
        required=True,
        help='Path to file containing deployment IDs (one per line)'
    )
    parser.add_argument(
        '--output-path',
        required=True,
        help='Directory to save GeoJSON files'
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    if not Path(args.deployments_file).exists():
        print(f"{Fore.RED}Error: File not found: {args.deployments_file}")
        sys.exit(1)

    deployment_ids = read_deployment_ids(args.deployments_file)

    if not deployment_ids:
        print(f"{Fore.YELLOW}No deployment IDs found in file{Style.RESET_ALL}")
        sys.exit(0)

    print(f"Found {len(deployment_ids)} deployments to fetch\n")

    fetched, errors = fetch_deployments(deployment_ids, args.output_path)

    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Fetched: {fetched}{Style.RESET_ALL}")
    if errors > 0:
        print(f"  {Fore.RED}Errors:  {errors}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == '__main__':
    main()
