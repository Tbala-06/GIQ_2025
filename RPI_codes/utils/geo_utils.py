#!/usr/bin/env python3
"""
Geospatial utility functions.
Provides calculations for GPS coordinates, bearings, and distances.
"""

import math
from typing import Tuple


EARTH_RADIUS_METERS = 6371000.0  # Earth's radius in meters


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)

    Returns:
        Distance in meters
    """
    # Convert to radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_METERS * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the initial bearing from point 1 to point 2.

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)

    Returns:
        Bearing in degrees (0-360, where 0 is North, 90 is East)
    """
    # Convert to radians
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlon = lon2_rad - lon1_rad

    x = math.sin(dlon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

    bearing = math.degrees(math.atan2(x, y))

    return normalize_bearing(bearing)


def normalize_bearing(bearing: float) -> float:
    """
    Normalize bearing to 0-360 degree range.

    Args:
        bearing: Bearing in degrees

    Returns:
        Normalized bearing (0-360)
    """
    return (bearing + 360) % 360


def bearing_difference(bearing1: float, bearing2: float) -> float:
    """
    Calculate the smallest angle between two bearings.

    Args:
        bearing1: First bearing (degrees)
        bearing2: Second bearing (degrees)

    Returns:
        Angle difference (-180 to 180 degrees)
    """
    diff = bearing2 - bearing1
    diff = (diff + 180) % 360 - 180
    return diff


def point_to_line_distance(point: Tuple[float, float],
                           line_start: Tuple[float, float],
                           line_end: Tuple[float, float]) -> float:
    """
    Calculate perpendicular distance from point to line segment.

    Args:
        point: (lat, lon) of the point
        line_start: (lat, lon) of line start
        line_end: (lat, lon) of line end

    Returns:
        Perpendicular distance in meters
    """
    # Project point onto line
    projected = project_point_onto_line(point, line_start, line_end)

    # Calculate distance from point to projected point
    return haversine_distance(point[0], point[1], projected[0], projected[1])


def project_point_onto_line(point: Tuple[float, float],
                            line_start: Tuple[float, float],
                            line_end: Tuple[float, float]) -> Tuple[float, float]:
    """
    Project a point onto a line segment.

    Args:
        point: (lat, lon) of the point
        line_start: (lat, lon) of line start
        line_end: (lat, lon) of line end

    Returns:
        (lat, lon) of closest point on line segment
    """
    # Convert to radians
    lat_p, lon_p = math.radians(point[0]), math.radians(point[1])
    lat_a, lon_a = math.radians(line_start[0]), math.radians(line_start[1])
    lat_b, lon_b = math.radians(line_end[0]), math.radians(line_end[1])

    # Calculate vectors
    ax = math.cos(lat_a) * math.cos(lon_a)
    ay = math.cos(lat_a) * math.sin(lon_a)
    az = math.sin(lat_a)

    bx = math.cos(lat_b) * math.cos(lon_b)
    by = math.cos(lat_b) * math.sin(lon_b)
    bz = math.sin(lat_b)

    px = math.cos(lat_p) * math.cos(lon_p)
    py = math.cos(lat_p) * math.sin(lon_p)
    pz = math.sin(lat_p)

    # Calculate projection parameter t
    abx, aby, abz = bx - ax, by - ay, bz - az
    apx, apy, apz = px - ax, py - ay, pz - az

    ab_dot_ab = abx * abx + aby * aby + abz * abz
    ap_dot_ab = apx * abx + apy * aby + apz * abz

    if ab_dot_ab == 0:
        return line_start

    t = ap_dot_ab / ab_dot_ab

    # Clamp t to [0, 1] to stay on segment
    t = max(0, min(1, t))

    # Calculate projected point
    qx = ax + t * abx
    qy = ay + t * aby
    qz = az + t * abz

    # Convert back to lat/lon
    lat_q = math.atan2(qz, math.sqrt(qx * qx + qy * qy))
    lon_q = math.atan2(qy, qx)

    return (math.degrees(lat_q), math.degrees(lon_q))


def destination_point(lat: float, lon: float, bearing: float, distance: float) -> Tuple[float, float]:
    """
    Calculate destination point given start point, bearing, and distance.

    Args:
        lat: Starting latitude (degrees)
        lon: Starting longitude (degrees)
        bearing: Bearing in degrees (0-360)
        distance: Distance in meters

    Returns:
        (lat, lon) of destination point
    """
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)

    angular_distance = distance / EARTH_RADIUS_METERS

    dest_lat = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
    )

    dest_lon = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(dest_lat)
    )

    return (math.degrees(dest_lat), math.degrees(dest_lon))
