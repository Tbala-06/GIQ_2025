#!/usr/bin/env python3
"""
Road Finder Module
Finds nearest road from GeoJSON data and calculates road bearings.
"""

import json
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from utils.logger import get_logger
from utils.geo_utils import haversine_distance, calculate_bearing, point_to_line_distance, project_point_onto_line

logger = get_logger(__name__)


@dataclass
class RoadSegment:
    """Container for road segment information"""
    geometry: List[Tuple[float, float]]  # List of (lat, lon) points
    bearing: float  # Direction of road in degrees
    distance: float  # Distance from query point to road
    closest_point: Tuple[float, float]  # Nearest point on road
    properties: dict  # Road metadata (name, type, etc.)


class RoadFinder:
    """Find and analyze roads from GeoJSON data"""

    def __init__(self, geojson_file: Optional[str] = None):
        """
        Initialize Road Finder.

        Args:
            geojson_file: Path to GeoJSON file with road data
        """
        self.roads = []
        self.geojson_file = geojson_file

        if geojson_file:
            self.load_geojson(geojson_file)

        logger.info(f"Road Finder initialized with {len(self.roads)} roads")

    def load_geojson(self, filepath: str) -> bool:
        """
        Load road data from GeoJSON file.

        Args:
            filepath: Path to GeoJSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading roads from {filepath}")
            with open(filepath, 'r') as f:
                data = json.load(f)

            if data.get('type') != 'FeatureCollection':
                logger.error("Invalid GeoJSON: not a FeatureCollection")
                return False

            self.roads = []
            for feature in data.get('features', []):
                if feature.get('type') != 'Feature':
                    continue

                geometry = feature.get('geometry', {})
                if geometry.get('type') != 'LineString':
                    continue  # Only handle LineString for now

                coordinates = geometry.get('coordinates', [])
                if len(coordinates) < 2:
                    continue

                # Convert [lon, lat] to [lat, lon]
                coords = [(lat, lon) for lon, lat in coordinates]

                self.roads.append({
                    'geometry': coords,
                    'properties': feature.get('properties', {})
                })

            logger.info(f"Loaded {len(self.roads)} roads")
            return True

        except FileNotFoundError:
            logger.error(f"GeoJSON file not found: {filepath}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading GeoJSON: {e}")
            return False

    def find_nearest_road(self, lat: float, lon: float,
                         max_distance_meters: float = 50.0) -> Optional[RoadSegment]:
        """
        Find the nearest road to a given point.

        Args:
            lat: Query latitude
            lon: Query longitude
            max_distance_meters: Maximum search distance

        Returns:
            RoadSegment with nearest road info, or None if no road found
        """
        if not self.roads:
            logger.warning("No roads loaded")
            return None

        logger.info(f"Searching for nearest road to ({lat:.6f}, {lon:.6f})")

        nearest_road = None
        min_distance = float('inf')

        for road in self.roads:
            coords = road['geometry']

            # Check each segment of the road
            for i in range(len(coords) - 1):
                start = coords[i]
                end = coords[i + 1]

                # Calculate distance to this segment
                distance = point_to_line_distance((lat, lon), start, end)

                if distance < min_distance and distance <= max_distance_meters:
                    min_distance = distance

                    # Project point onto this segment
                    closest_point = project_point_onto_line((lat, lon), start, end)

                    # Calculate bearing of this road segment
                    bearing = calculate_bearing(start[0], start[1], end[0], end[1])

                    nearest_road = RoadSegment(
                        geometry=coords,
                        bearing=bearing,
                        distance=distance,
                        closest_point=closest_point,
                        properties=road['properties']
                    )

        if nearest_road:
            logger.info(f"Found road at {nearest_road.distance:.2f}m, bearing {nearest_road.bearing:.1f}°")
            if nearest_road.properties.get('name'):
                logger.info(f"Road name: {nearest_road.properties['name']}")
        else:
            logger.warning(f"No road found within {max_distance_meters}m")

        return nearest_road

    def get_road_bearing(self, road_coords: List[Tuple[float, float]]) -> float:
        """
        Calculate average bearing of a road.

        Args:
            road_coords: List of (lat, lon) points defining the road

        Returns:
            Average bearing in degrees (0-360)
        """
        if len(road_coords) < 2:
            return 0.0

        # Calculate bearing between first and last point
        start = road_coords[0]
        end = road_coords[-1]

        bearing = calculate_bearing(start[0], start[1], end[0], end[1])
        return bearing

    def project_point_to_road(self, lat: float, lon: float,
                             road: RoadSegment) -> Tuple[float, float]:
        """
        Project a point onto the nearest segment of a road.

        Args:
            lat: Point latitude
            lon: Point longitude
            road: RoadSegment to project onto

        Returns:
            (lat, lon) of projected point on road
        """
        coords = road.geometry
        if len(coords) < 2:
            return (lat, lon)

        # Find nearest segment
        min_distance = float('inf')
        closest_point = (lat, lon)

        for i in range(len(coords) - 1):
            start = coords[i]
            end = coords[i + 1]

            distance = point_to_line_distance((lat, lon), start, end)
            if distance < min_distance:
                min_distance = distance
                closest_point = project_point_onto_line((lat, lon), start, end)

        return closest_point

    def get_roads_in_area(self, lat: float, lon: float,
                         radius_meters: float = 100.0) -> List[RoadSegment]:
        """
        Get all roads within a radius of a point.

        Args:
            lat: Center latitude
            lon: Center longitude
            radius_meters: Search radius in meters

        Returns:
            List of RoadSegment objects within radius
        """
        roads_in_area = []

        for road in self.roads:
            coords = road['geometry']

            # Check if any point on the road is within radius
            for coord in coords:
                distance = haversine_distance(lat, lon, coord[0], coord[1])
                if distance <= radius_meters:
                    # Calculate bearing and closest point
                    for i in range(len(coords) - 1):
                        start = coords[i]
                        end = coords[i + 1]
                        dist = point_to_line_distance((lat, lon), start, end)
                        closest_point = project_point_onto_line((lat, lon), start, end)
                        bearing = calculate_bearing(start[0], start[1], end[0], end[1])

                        roads_in_area.append(RoadSegment(
                            geometry=coords,
                            bearing=bearing,
                            distance=dist,
                            closest_point=closest_point,
                            properties=road['properties']
                        ))
                        break  # Only add road once
                    break

        logger.info(f"Found {len(roads_in_area)} roads within {radius_meters}m")
        return roads_in_area

    def get_road_count(self) -> int:
        """Get number of roads loaded"""
        return len(self.roads)
