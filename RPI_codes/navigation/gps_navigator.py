#!/usr/bin/env python3
"""
GPS Navigator Module
Handles GPS navigation using MTi sensor and motor controller.
"""

import time
import math
from typing import Optional, Tuple
from utils.logger import get_logger
from utils.geo_utils import haversine_distance, calculate_bearing, bearing_difference, normalize_bearing

logger = get_logger(__name__)


class GPSNavigator:
    """GPS navigation using MTi sensor and motor control"""

    def __init__(self, mti_parser, motor_controller):
        """
        Initialize GPS Navigator.

        Args:
            mti_parser: MTiParser instance for GPS/IMU data
            motor_controller: MotorController instance for movement
        """
        self.mti = mti_parser
        self.motor = motor_controller
        self.last_position = None
        self.last_heading = None

        logger.info("GPS Navigator initialized")

    def get_current_position(self, timeout=5.0) -> Optional[Tuple[float, float]]:
        """
        Get current GPS position from MTi sensor.

        Args:
            timeout: Maximum time to wait for GPS data (seconds)

        Returns:
            (latitude, longitude) tuple or None if unavailable
        """
        try:
            data = self.mti.read_data(timeout=timeout)
            if data and data.latitude_longitude:
                lat, lon = data.latitude_longitude
                self.last_position = (lat, lon)
                logger.debug(f"GPS position: {lat:.6f}, {lon:.6f}")
                return (lat, lon)
            else:
                logger.warning("No GPS data available")
                return self.last_position
        except Exception as e:
            logger.error(f"Error reading GPS position: {e}")
            return self.last_position

    def get_heading(self, timeout=2.0) -> Optional[float]:
        """
        Get current compass heading from MTi sensor.

        Args:
            timeout: Maximum time to wait for IMU data (seconds)

        Returns:
            Heading in degrees (0-360) or None if unavailable
        """
        try:
            data = self.mti.read_data(timeout=timeout)
            if data and data.euler_angles:
                roll, pitch, yaw = data.euler_angles
                # Convert yaw to heading (0-360)
                heading = normalize_bearing(yaw)
                self.last_heading = heading
                logger.debug(f"Heading: {heading:.1f}°")
                return heading
            else:
                logger.warning("No heading data available")
                return self.last_heading
        except Exception as e:
            logger.error(f"Error reading heading: {e}")
            return self.last_heading

    def calculate_bearing_to(self, target_lat: float, target_lon: float) -> Optional[float]:
        """
        Calculate bearing to target from current position.

        Args:
            target_lat: Target latitude
            target_lon: Target longitude

        Returns:
            Bearing in degrees (0-360) or None if position unavailable
        """
        current_pos = self.get_current_position()
        if not current_pos:
            logger.error("Cannot calculate bearing: no GPS position")
            return None

        bearing = calculate_bearing(current_pos[0], current_pos[1], target_lat, target_lon)
        logger.debug(f"Bearing to target: {bearing:.1f}°")
        return bearing

    def calculate_distance_to(self, target_lat: float, target_lon: float) -> Optional[float]:
        """
        Calculate distance to target from current position.

        Args:
            target_lat: Target latitude
            target_lon: Target longitude

        Returns:
            Distance in meters or None if position unavailable
        """
        current_pos = self.get_current_position()
        if not current_pos:
            logger.error("Cannot calculate distance: no GPS position")
            return None

        distance = haversine_distance(current_pos[0], current_pos[1], target_lat, target_lon)
        logger.debug(f"Distance to target: {distance:.2f}m")
        return distance

    def navigate_to(self, target_lat: float, target_lon: float,
                   tolerance_meters: float = 2.0, max_duration: float = 300.0) -> bool:
        """
        Navigate to target GPS coordinates.

        Args:
            target_lat: Target latitude
            target_lon: Target longitude
            tolerance_meters: Acceptable arrival distance (meters)
            max_duration: Maximum navigation time (seconds)

        Returns:
            True if successfully arrived, False otherwise
        """
        logger.info(f"Navigating to ({target_lat:.6f}, {target_lon:.6f})")
        logger.info(f"Tolerance: {tolerance_meters}m, Max duration: {max_duration}s")

        start_time = time.time()
        move_speed = 50  # Motor speed (0-100)
        turn_speed = 40

        while time.time() - start_time < max_duration:
            # Get current position
            current_pos = self.get_current_position(timeout=2.0)
            if not current_pos:
                logger.warning("GPS position lost, waiting...")
                time.sleep(1.0)
                continue

            # Calculate distance to target
            distance = haversine_distance(
                current_pos[0], current_pos[1],
                target_lat, target_lon
            )

            logger.info(f"Distance to target: {distance:.2f}m")

            # Check if arrived
            if distance <= tolerance_meters:
                logger.info("✅ Arrived at target!")
                self.motor.stop()
                return True

            # Calculate bearing to target
            target_bearing = calculate_bearing(
                current_pos[0], current_pos[1],
                target_lat, target_lon
            )

            # Get current heading
            current_heading = self.get_heading(timeout=2.0)
            if current_heading is None:
                logger.warning("Heading unavailable, continuing...")
                current_heading = target_bearing  # Assume we're pointed the right way

            # Calculate heading error
            heading_error = bearing_difference(current_heading, target_bearing)

            logger.debug(f"Current: {current_heading:.1f}°, Target: {target_bearing:.1f}°, Error: {heading_error:.1f}°")

            # Adjust heading if needed
            if abs(heading_error) > 10:  # If more than 10 degrees off
                logger.info(f"Correcting heading: {heading_error:.1f}° error")
                if heading_error > 0:
                    self.motor.turn_right(abs(heading_error), speed=turn_speed)
                else:
                    self.motor.turn_left(abs(heading_error), speed=turn_speed)
                time.sleep(0.5)
            else:
                # Move forward toward target
                move_distance = min(distance, 1.0)  # Move up to 1 meter at a time
                logger.debug(f"Moving forward {move_distance:.2f}m")
                self.motor.move_forward(speed=move_speed, distance_meters=move_distance)
                time.sleep(0.5)

            # Small delay between iterations
            time.sleep(0.1)

        # Timeout reached
        logger.warning(f"Navigation timeout after {max_duration}s")
        self.motor.stop()
        return False

    def get_gps_quality(self) -> dict:
        """
        Get GPS signal quality information.

        Returns:
            Dictionary with fix type and satellite count
        """
        try:
            data = self.mti.read_data(timeout=2.0)
            if data:
                gps_info = data.get_gps_info()
                logger.debug(f"GPS quality: {gps_info}")
                return gps_info
            else:
                return {"fix": "No data", "satellites": 0}
        except Exception as e:
            logger.error(f"Error reading GPS quality: {e}")
            return {"fix": "Error", "satellites": 0}

    def wait_for_gps_fix(self, min_satellites: int = 4, timeout: float = 60.0) -> bool:
        """
        Wait for valid GPS fix.

        Args:
            min_satellites: Minimum number of satellites required
            timeout: Maximum wait time (seconds)

        Returns:
            True if GPS fix acquired, False if timeout
        """
        logger.info(f"Waiting for GPS fix (min {min_satellites} satellites)...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            gps_info = self.get_gps_quality()
            fix_type = gps_info.get("fix", "Unknown")
            satellites = gps_info.get("satellites", 0)

            logger.info(f"GPS: {fix_type}, Satellites: {satellites}/{min_satellites}")

            if "3D" in fix_type or "DGPS" in fix_type or "RTK" in fix_type:
                if satellites >= min_satellites:
                    logger.info(f"✅ GPS fix acquired: {fix_type} with {satellites} satellites")
                    return True

            time.sleep(2.0)

        logger.warning(f"GPS fix timeout after {timeout}s")
        return False
