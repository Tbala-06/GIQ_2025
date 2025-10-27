#!/usr/bin/env python3
"""
Safety Monitor Module
Monitors robot safety parameters (GPS, battery, tilt, emergency stop).
"""

import time
from typing import Tuple, Dict
from utils.logger import get_logger
from config import Config

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False

logger = get_logger(__name__)


class SafetyMonitor:
    """Monitor safety parameters and emergency stop"""

    def __init__(self, mti_parser, simulate: bool = False):
        """
        Initialize Safety Monitor.

        Args:
            mti_parser: MTiParser instance for GPS/IMU data
            simulate: If True, skip GPIO setup
        """
        self.mti = mti_parser
        self.simulate = simulate
        self.emergency_stop_triggered = False

        # Setup emergency stop button
        if not simulate and GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(Config.EMERGENCY_STOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

                # Add interrupt for emergency stop
                GPIO.add_event_detect(
                    Config.EMERGENCY_STOP_PIN,
                    GPIO.FALLING,
                    callback=self._emergency_stop_callback,
                    bouncetime=300
                )

                logger.info(f"Emergency stop configured on GPIO {Config.EMERGENCY_STOP_PIN}")
            except Exception as e:
                logger.error(f"Failed to setup emergency stop: {e}")
        elif simulate:
            logger.info("Safety Monitor in simulation mode (GPIO disabled)")
        else:
            logger.warning("GPIO not available, emergency stop disabled")

        logger.info("Safety Monitor initialized")

    def check_gps_signal(self) -> Tuple[bool, str]:
        """
        Verify GPS has adequate signal quality.

        Returns:
            (is_safe, reason) tuple
        """
        try:
            if self.simulate:
                return (True, "GPS check skipped (simulation)")

            data = self.mti.read_data(timeout=2.0)
            if not data:
                return (False, "No GPS data available")

            gps_info = data.get_gps_info()
            fix_type = gps_info.get("fix", "Unknown")
            satellites = gps_info.get("satellites", 0)

            # Check if we have a valid fix
            if "3D" not in fix_type and "DGPS" not in fix_type:
                return (False, f"Insufficient GPS fix: {fix_type}")

            # Check satellite count
            if satellites < Config.MIN_GPS_SATELLITES:
                return (False, f"Low satellite count: {satellites}/{Config.MIN_GPS_SATELLITES}")

            return (True, f"GPS OK: {fix_type}, {satellites} satellites")

        except Exception as e:
            logger.error(f"Error checking GPS: {e}")
            return (False, f"GPS check error: {str(e)}")

    def check_battery_level(self) -> Tuple[bool, str]:
        """
        Check robot battery level.

        Returns:
            (is_safe, reason) tuple

        Note: This is a placeholder. In a real implementation, you would read
              battery level from an ADC connected to a voltage divider.
        """
        try:
            if self.simulate:
                # Simulate healthy battery
                battery_level = 85
            else:
                # TODO: Implement actual battery reading via ADC
                # Example: Read from MCP3008 ADC or similar
                # For now, assume battery is OK
                battery_level = 100

            if battery_level < Config.MIN_BATTERY_LEVEL:
                return (False, f"Low battery: {battery_level}%")

            return (True, f"Battery OK: {battery_level}%")

        except Exception as e:
            logger.error(f"Error checking battery: {e}")
            return (False, f"Battery check error: {str(e)}")

    def check_tilt(self) -> Tuple[bool, str]:
        """
        Check robot tilt angle from IMU.

        Returns:
            (is_safe, reason) tuple
        """
        try:
            if self.simulate:
                return (True, "Tilt check skipped (simulation)")

            data = self.mti.read_data(timeout=2.0)
            if not data or not data.euler_angles:
                return (True, "No tilt data (assuming level)")

            roll, pitch, yaw = data.euler_angles

            # Check if tilt exceeds safety threshold
            max_tilt = max(abs(roll), abs(pitch))

            if max_tilt > Config.MAX_TILT_ANGLE:
                return (False, f"Excessive tilt: {max_tilt:.1f}° (max: {Config.MAX_TILT_ANGLE}°)")

            return (True, f"Tilt OK: {max_tilt:.1f}°")

        except Exception as e:
            logger.error(f"Error checking tilt: {e}")
            return (True, "Tilt check error (assuming safe)")

    def emergency_stop(self):
        """Trigger emergency stop"""
        if not self.emergency_stop_triggered:
            logger.critical("🚨 EMERGENCY STOP TRIGGERED")
            self.emergency_stop_triggered = True

    def reset_emergency_stop(self):
        """Clear emergency stop condition"""
        if self.emergency_stop_triggered:
            logger.info("Emergency stop reset")
            self.emergency_stop_triggered = False

    def is_emergency_stop_triggered(self) -> bool:
        """
        Check if emergency stop is active.

        Returns:
            True if emergency stop triggered
        """
        # Also check physical button if available
        if not self.simulate and GPIO_AVAILABLE:
            try:
                button_pressed = GPIO.input(Config.EMERGENCY_STOP_PIN) == GPIO.LOW
                if button_pressed and not self.emergency_stop_triggered:
                    self.emergency_stop()
            except Exception as e:
                logger.error(f"Error reading emergency stop button: {e}")

        return self.emergency_stop_triggered

    def is_safe_to_operate(self) -> Tuple[bool, str]:
        """
        Comprehensive safety check.

        Returns:
            (is_safe, reason) tuple
        """
        # Check emergency stop first
        if self.is_emergency_stop_triggered():
            return (False, "Emergency stop active")

        # Check GPS signal
        gps_safe, gps_reason = self.check_gps_signal()
        if not gps_safe:
            return (False, gps_reason)

        # Check battery
        battery_safe, battery_reason = self.check_battery_level()
        if not battery_safe:
            return (False, battery_reason)

        # Check tilt
        tilt_safe, tilt_reason = self.check_tilt()
        if not tilt_safe:
            return (False, tilt_reason)

        return (True, "All safety checks passed")

    def perform_safety_checks(self) -> Dict[str, Tuple[bool, str]]:
        """
        Perform all safety checks and return results.

        Returns:
            Dictionary with check results
        """
        results = {
            "emergency_stop": (not self.is_emergency_stop_triggered(), "Emergency stop active" if self.is_emergency_stop_triggered() else "OK"),
            "gps": self.check_gps_signal(),
            "battery": self.check_battery_level(),
            "tilt": self.check_tilt()
        }

        return results

    def cleanup(self):
        """Cleanup GPIO resources"""
        if not self.simulate and GPIO_AVAILABLE:
            try:
                GPIO.cleanup(Config.EMERGENCY_STOP_PIN)
                logger.info("Safety Monitor GPIO cleanup complete")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")

    def _emergency_stop_callback(self, channel):
        """GPIO interrupt callback for emergency stop button"""
        logger.warning("Emergency stop button pressed!")
        self.emergency_stop()
