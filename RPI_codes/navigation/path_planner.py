#!/usr/bin/env python3
"""
Path Planner Module
Creates waypoints and optimizes routes for navigation.
"""

from dataclasses import dataclass
from typing import List, Tuple
from utils.logger import get_logger
from utils.geo_utils import haversine_distance, calculate_bearing, destination_point

logger = get_logger(__name__)


@dataclass
class Waypoint:
    """Container for waypoint information"""
    lat: float
    lon: float
    bearing: float  # Bearing to next waypoint
    distance: float  # Distance to next waypoint


class PathPlanner:
    """Plan routes and generate waypoints"""

    def __init__(self):
        """Initialize Path Planner"""
        logger.info("Path Planner initialized")

    def plan_route(self, start_lat: float, start_lon: float,
                  end_lat: float, end_lon: float,
                  waypoint_interval: float = 10.0) -> List[Waypoint]:
        """
        Plan route from start to end with waypoints.

        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Ending latitude
            end_lon: Ending longitude
            waypoint_interval: Distance between waypoints (meters)

        Returns:
            List of Waypoint objects
        """
        logger.info(f"Planning route from ({start_lat:.6f}, {start_lon:.6f}) to ({end_lat:.6f}, {end_lon:.6f})")

        # Calculate total distance and bearing
        total_distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
        bearing = calculate_bearing(start_lat, start_lon, end_lat, end_lon)

        logger.info(f"Total distance: {total_distance:.2f}m, Bearing: {bearing:.1f}°")

        # Generate waypoints
        waypoints = self.calculate_waypoints(
            start_lat, start_lon,
            bearing, total_distance,
            waypoint_interval
        )

        # Add final destination
        waypoints.append(Waypoint(
            lat=end_lat,
            lon=end_lon,
            bearing=bearing,
            distance=0.0
        ))

        logger.info(f"Generated {len(waypoints)} waypoints")
        return waypoints

    def calculate_waypoints(self, start_lat: float, start_lon: float,
                           bearing: float, distance: float,
                           interval: float) -> List[Waypoint]:
        """
        Calculate waypoints along a bearing.

        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            bearing: Direction to travel (degrees)
            distance: Total distance to travel (meters)
            interval: Distance between waypoints (meters)

        Returns:
            List of Waypoint objects
        """
        waypoints = []
        current_lat, current_lon = start_lat, start_lon
        remaining_distance = distance

        while remaining_distance > interval:
            # Calculate next waypoint
            next_point = destination_point(current_lat, current_lon, bearing, interval)

            waypoints.append(Waypoint(
                lat=current_lat,
                lon=current_lon,
                bearing=bearing,
                distance=interval
            ))

            current_lat, current_lon = next_point
            remaining_distance -= interval

        # Add final waypoint before destination
        if remaining_distance > 0:
            waypoints.append(Waypoint(
                lat=current_lat,
                lon=current_lon,
                bearing=bearing,
                distance=remaining_distance
            ))

        return waypoints

    def avoid_obstacles(self, waypoints: List[Waypoint],
                       obstacles: List[Tuple[float, float]]) -> List[Waypoint]:
        """
        Modify route to avoid obstacles (placeholder for future implementation).

        Args:
            waypoints: Original waypoints
            obstacles: List of (lat, lon) obstacles to avoid

        Returns:
            Modified waypoints avoiding obstacles
        """
        # Placeholder: In a full implementation, this would use an algorithm
        # like A* or RRT to plan around obstacles
        logger.info(f"Obstacle avoidance: {len(obstacles)} obstacles (placeholder)")
        return waypoints

    def optimize_route(self, waypoints: List[Waypoint]) -> List[Waypoint]:
        """
        Optimize route by removing unnecessary waypoints.

        Args:
            waypoints: Original waypoints

        Returns:
            Optimized waypoints
        """
        if len(waypoints) <= 2:
            return waypoints

        optimized = [waypoints[0]]  # Keep start point

        # Simple optimization: remove waypoints that are nearly collinear
        for i in range(1, len(waypoints) - 1):
            prev = waypoints[i - 1]
            current = waypoints[i]
            next_wp = waypoints[i + 1]

            # Calculate bearing from prev to next
            direct_bearing = calculate_bearing(prev.lat, prev.lon, next_wp.lat, next_wp.lon)

            # If current waypoint's bearing is very close to direct bearing, skip it
            bearing_diff = abs(current.bearing - direct_bearing)
            if bearing_diff > 5.0:  # Keep waypoints with >5° deviation
                optimized.append(current)

        optimized.append(waypoints[-1])  # Keep end point

        removed = len(waypoints) - len(optimized)
        if removed > 0:
            logger.info(f"Optimized route: removed {removed} waypoints")

        return optimized

    def calculate_route_distance(self, waypoints: List[Waypoint]) -> float:
        """
        Calculate total distance of a route.

        Args:
            waypoints: List of waypoints

        Returns:
            Total distance in meters
        """
        if len(waypoints) < 2:
            return 0.0

        total = 0.0
        for i in range(len(waypoints) - 1):
            distance = haversine_distance(
                waypoints[i].lat, waypoints[i].lon,
                waypoints[i + 1].lat, waypoints[i + 1].lon
            )
            total += distance

        return total

    def estimate_travel_time(self, waypoints: List[Waypoint],
                            speed_mps: float = 0.5) -> float:
        """
        Estimate travel time for a route.

        Args:
            waypoints: List of waypoints
            speed_mps: Average speed in meters per second

        Returns:
            Estimated time in seconds
        """
        distance = self.calculate_route_distance(waypoints)
        time_seconds = distance / speed_mps if speed_mps > 0 else 0.0

        logger.info(f"Estimated travel time: {time_seconds:.1f}s for {distance:.2f}m at {speed_mps}m/s")
        return time_seconds
