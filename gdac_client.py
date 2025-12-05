#!/usr/bin/env python3
"""GDAC ERDDAP client for fetching glider deployment data."""

import urllib.request
import urllib.error

GDAC_BASE_URL = "https://gliders.ioos.us/erddap/tabledap"
DEFAULT_VARIABLES = ["time", "latitude", "longitude"]


def build_erddap_url(deployment_id, variables=None, fmt="geoJson"):
    """Build ERDDAP tabledap URL for a deployment.

    Args:
        deployment_id: GDAC deployment identifier (e.g., 'bass-20250601T0000')
        variables: List of variables to fetch (default: time, lat, lon)
        fmt: Output format (default: geoJson)

    Returns:
        Full ERDDAP URL string
    """
    if variables is None:
        variables = DEFAULT_VARIABLES
    var_str = ",".join(variables)
    return f"{GDAC_BASE_URL}/{deployment_id}.{fmt}?{var_str}"


def fetch_deployment_geojson(deployment_id, variables=None):
    """Fetch GeoJSON data for a deployment from GDAC.

    Args:
        deployment_id: GDAC deployment identifier
        variables: List of variables to fetch (default: time, lat, lon)

    Returns:
        GeoJSON string on success

    Raises:
        ValueError: If deployment not found or request fails
    """
    url = build_erddap_url(deployment_id, variables, fmt="geoJson")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Deployment not found: {deployment_id}")
        raise ValueError(f"HTTP error {e.code}: {deployment_id}")
    except urllib.error.URLError as e:
        raise ValueError(f"Network error: {e.reason}")
