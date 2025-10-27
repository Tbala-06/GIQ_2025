#!/usr/bin/env python3
"""
OpenStreetMap Road Downloader
Downloads road data from OpenStreetMap and saves as GeoJSON.
"""

import argparse
import json
import sys
import os
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests module not installed")
    print("Install with: pip install requests")
    sys.exit(1)


def download_roads(lat: float, lon: float, radius: int = 500, output_file: str = "roads.geojson") -> bool:
    """
    Download roads from OpenStreetMap Overpass API.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius: Radius in meters to search for roads
        output_file: Output GeoJSON file path

    Returns:
        True if successful, False otherwise
    """
    print(f"Downloading roads around ({lat}, {lon}) within {radius}m...")

    # Overpass API query for roads
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Query for major roads (primary, secondary, tertiary, residential)
    query = f"""
    [out:json][timeout:60];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential"]
          (around:{radius},{lat},{lon});
    );
    out geom;
    """

    try:
        print("Sending request to Overpass API...")
        response = requests.post(overpass_url, data={'data': query}, timeout=120)

        if response.status_code != 200:
            print(f"❌ Error: API returned status {response.status_code}")
            return False

        print("✅ Data received, processing...")

        # Parse OSM data
        osm_data = response.json()

        if 'elements' not in osm_data:
            print("❌ Error: No elements in response")
            return False

        # Convert to GeoJSON
        features = []

        for element in osm_data['elements']:
            if element['type'] != 'way':
                continue

            if 'geometry' not in element:
                continue

            # Extract coordinates (OSM is [lat, lon], GeoJSON needs [lon, lat])
            coordinates = [[point['lon'], point['lat']] for point in element['geometry']]

            if len(coordinates) < 2:
                continue

            # Extract properties
            tags = element.get('tags', {})
            properties = {
                'osm_id': element.get('id'),
                'name': tags.get('name', 'Unnamed Road'),
                'highway': tags.get('highway', 'unknown'),
                'surface': tags.get('surface', 'unknown'),
                'lanes': tags.get('lanes', '1'),
                'oneway': tags.get('oneway', 'no')
            }

            # Create GeoJSON feature
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coordinates
                },
                'properties': properties
            }

            features.append(feature)

        # Create GeoJSON FeatureCollection
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'center': [lat, lon],
                'radius_meters': radius,
                'road_count': len(features)
            }
        }

        # Save to file
        print(f"Writing {len(features)} roads to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"✅ Successfully saved {len(features)} roads to {output_file}")
        return True

    except requests.exceptions.Timeout:
        print("❌ Error: Request timeout. Try again or reduce radius.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: Network error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_geojson(filepath: str):
    """
    Validate and display GeoJSON file contents.

    Args:
        filepath: Path to GeoJSON file
    """
    try:
        print(f"\nValidating {filepath}...")

        with open(filepath, 'r') as f:
            data = json.load(f)

        if data.get('type') != 'FeatureCollection':
            print("❌ Error: Not a valid FeatureCollection")
            return

        features = data.get('features', [])
        metadata = data.get('metadata', {})

        print("\n" + "=" * 60)
        print("GeoJSON File Summary")
        print("=" * 60)

        if metadata:
            print(f"Center: {metadata.get('center', 'N/A')}")
            print(f"Radius: {metadata.get('radius_meters', 'N/A')}m")

        print(f"Total Roads: {len(features)}")

        # Count road types
        road_types = {}
        named_roads = 0

        for feature in features:
            props = feature.get('properties', {})
            highway_type = props.get('highway', 'unknown')
            road_types[highway_type] = road_types.get(highway_type, 0) + 1

            if props.get('name') and props.get('name') != 'Unnamed Road':
                named_roads += 1

        print(f"Named Roads: {named_roads}")

        print("\nRoad Types:")
        for road_type, count in sorted(road_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {road_type}: {count}")

        print("\n" + "=" * 60)

        # Display first few roads
        print("\nSample Roads:")
        for i, feature in enumerate(features[:5]):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [])
            print(f"\n{i+1}. {props.get('name', 'Unnamed')}")
            print(f"   Type: {props.get('highway', 'unknown')}")
            print(f"   Points: {len(coords)}")
            if coords:
                print(f"   Start: {coords[0]}")
                print(f"   End: {coords[-1]}")

        print("\n✅ GeoJSON file is valid")

    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Download road data from OpenStreetMap',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download roads near San Francisco
  python download_roads.py --lat 37.7749 --lon -122.4194 --radius 1000 --output roads.geojson

  # Download roads near current location (smaller radius)
  python download_roads.py --lat 51.5074 --lon -0.1278 --radius 500

  # Validate existing GeoJSON file
  python download_roads.py --validate roads.geojson
        """
    )

    parser.add_argument('--lat', type=float, help='Center latitude')
    parser.add_argument('--lon', type=float, help='Center longitude')
    parser.add_argument('--radius', type=int, default=500,
                       help='Search radius in meters (default: 500)')
    parser.add_argument('--output', type=str, default='roads.geojson',
                       help='Output GeoJSON file (default: roads.geojson)')
    parser.add_argument('--validate', type=str, metavar='FILE',
                       help='Validate existing GeoJSON file')

    args = parser.parse_args()

    print("=" * 60)
    print("OpenStreetMap Road Downloader")
    print("=" * 60)

    # Validation mode
    if args.validate:
        validate_geojson(args.validate)
        return

    # Download mode
    if args.lat is None or args.lon is None:
        print("\n❌ Error: --lat and --lon are required for download mode")
        print("\nUse --help for usage information")
        sys.exit(1)

    # Validate coordinates
    if not (-90 <= args.lat <= 90):
        print(f"❌ Error: Invalid latitude {args.lat} (must be -90 to 90)")
        sys.exit(1)

    if not (-180 <= args.lon <= 180):
        print(f"❌ Error: Invalid longitude {args.lon} (must be -180 to 180)")
        sys.exit(1)

    if args.radius < 100 or args.radius > 5000:
        print(f"❌ Error: Radius {args.radius}m out of range (100-5000m)")
        sys.exit(1)

    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Download roads
    success = download_roads(args.lat, args.lon, args.radius, args.output)

    if success:
        # Validate the downloaded file
        validate_geojson(args.output)
        print("\n✅ Done!")
        sys.exit(0)
    else:
        print("\n❌ Download failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
