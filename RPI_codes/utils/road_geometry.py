#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Road-specific geometry calculations.
Functions for road alignment, positioning, and painting calculations.
"""

import math
from typing import Tuple
from utils.geo_utils import destination_point, normalize_bearing, bearing_difference


def calculate_perpendicular_position(road_bearing: float,
                                    current_lat: float,
                                    current_lon: float,
                                    distance_from_road: float) -> Tuple[float, float]:
    """
    Calculate position perpendicular to road at specified distance.

    Args:
        road_bearing: Bearing of the road (degrees)
        current_lat: Current latitude
        current_lon: Current longitude
        distance_from_road: Distance to move perpendicular (meters, positive = right side)

    Returns:
        (lat, lon) of perpendicular position
    """
    # Perpendicular bearing is 90 degrees from road bearing
    perp_bearing = normalize_bearing(road_bearing + 90)

    return destination_point(current_lat, current_lon, perp_bearing, abs(distance_from_road))


def calculate_stencil_angle(road_bearing: float, robot_heading: float) -> float:
    """
    Calculate servo angle needed to align stencil with road.

    Args:
        road_bearing: Bearing of the road (degrees, 0-360)
        robot_heading: Current heading of robot (degrees, 0-360)

    Returns:
        Servo angle in degrees (0-180, where 90 is center)
    """
    # Calculate angle difference
    angle_diff = bearing_difference(robot_heading, road_bearing)

    # Convert to servo angle (90 is center, 0 is full left, 180 is full right)
    servo_angle = 90 + angle_diff

    # Clamp to valid servo range
    return max(0, min(180, servo_angle))


def is_aligned_with_road(road_bearing: float, robot_heading: float,
                        tolerance_degrees: float = 5.0) -> bool:
    """
    Check if robot is aligned with road within tolerance.

    Args:
        road_bearing: Bearing of the road (degrees)
        robot_heading: Current heading of robot (degrees)
        tolerance_degrees: Acceptable alignment error (degrees)

    Returns:
        True if aligned within tolerance
    """
    angle_diff = abs(bearing_difference(robot_heading, road_bearing))
    return angle_diff <= tolerance_degrees


def calculate_approach_angle(road_bearing: float, approach_bearing: float) -> float:
    """
    Calculate turn angle needed to approach road perpendicularly.

    Args:
        road_bearing: Bearing of the road (degrees)
        approach_bearing: Current approach bearing (degrees)

    Returns:
        Turn angle needed (degrees, positive = turn right, negative = turn left)
    """
    # Perpendicular approach is 90 degrees from road
    target_bearing = normalize_bearing(road_bearing + 90)

    return bearing_difference(approach_bearing, target_bearing)


def calculate_painting_position(road_lat: float,
                                road_lon: float,
                                road_bearing: float,
                                offset_meters: float = 1.0) -> Tuple[float, float]:
    """
    Calculate optimal robot position for painting.

    Args:
        road_lat: Latitude of point on road
        road_lon: Longitude of point on road
        road_bearing: Bearing of the road
        offset_meters: Distance from road (meters, positive = right side)

    Returns:
        (lat, lon) of optimal painting position
    """
    # Position robot perpendicular to road at specified offset
    return calculate_perpendicular_position(
        road_bearing,
        road_lat,
        road_lon,
        offset_meters
    )


def is_position_safe_for_painting(lat: float,
                                  lon: float,
                                  road_lat: float,
                                  road_lon: float,
                                  min_distance: float = 0.5,
                                  max_distance: float = 2.0) -> Tuple[bool, str]:
    """
    Check if current position is safe for painting operation.

    Args:
        lat: Current latitude
        lon: Current longitude
        road_lat: Target road latitude
        road_lon: Target road longitude
        min_distance: Minimum safe distance (meters)
        max_distance: Maximum effective distance (meters)

    Returns:
        (is_safe, reason) tuple
    """
    from utils.geo_utils import haversine_distance

    distance = haversine_distance(lat, lon, road_lat, road_lon)

    if distance < min_distance:
        return (False, f"Too close to road: {distance:.2f}m (min: {min_distance}m)")

    if distance > max_distance:
        return (False, f"Too far from road: {distance:.2f}m (max: {max_distance}m)")

    return (True, f"Position safe: {distance:.2f}m from road")


def calculate_road_perpendicular_bearing(road_bearing: float) -> float:
    """
    Calculate bearing perpendicular to road (for robot positioning).

    Args:
        road_bearing: Bearing of the road (degrees)

    Returns:
        Perpendicular bearing (degrees, 90 degrees clockwise from road)
    """
    return normalize_bearing(road_bearing + 90)
