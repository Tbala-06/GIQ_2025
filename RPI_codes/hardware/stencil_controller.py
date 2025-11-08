#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stencil Controller for Servo Positioning
Adjusts stencil angle based on road orientation
"""

import time
from typing import Optional

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("WARNING: RPi.GPIO not available, running in simulation mode")

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class StencilController:
    """Control stencil positioning servo"""
    
    # Servo pulse width in microseconds
    MIN_PULSE = 500   # 0 degrees
    MAX_PULSE = 2500  # 180 degrees
    HOME_ANGLE = 90   # Default position
    
    def __init__(self, simulate=False):
        """
        Initialize stencil controller
        
        Args:
            simulate: If True, run in simulation mode without GPIO
        """
        self.simulate = simulate or not GPIO_AVAILABLE
        self.current_angle = self.HOME_ANGLE
        
        if not self.simulate:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(Config.STENCIL_SERVO_PIN, GPIO.OUT)
            
            # Setup PWM for servo (50 Hz)
            self.servo = GPIO.PWM(Config.STENCIL_SERVO_PIN, 50)
            self.servo.start(0)
            
            logger.info("Stencil controller initialized (GPIO mode)")
        else:
            logger.info("Stencil controller initialized (SIMULATION mode)")
        
        # Move to home position
        self.home_position()
    
    def _angle_to_duty_cycle(self, angle: float) -> float:
        """
        Convert angle to PWM duty cycle
        
        Args:
            angle: Servo angle (0-180 degrees)
            
        Returns:
            Duty cycle percentage
        """
        # Constrain angle
        angle = max(0, min(180, angle))
        
        # Calculate pulse width
        pulse_width = self.MIN_PULSE + (angle / 180.0) * (self.MAX_PULSE - self.MIN_PULSE)
        
        # Convert to duty cycle (50 Hz = 20ms period)
        duty_cycle = (pulse_width / 20000.0) * 100.0
        
        return duty_cycle
    
    def set_angle(self, angle: float):
        """
        Set stencil servo to specific angle
        
        Args:
            angle: Target angle (0-180 degrees)
                  0 = fully left
                  90 = center/perpendicular
                  180 = fully right
        """
        # Constrain angle
        angle = max(0, min(180, angle))
        
        logger.info(f"Setting stencil angle to {angle:.1f} degrees")
        
        if not self.simulate:
            duty_cycle = self._angle_to_duty_cycle(angle)
            self.servo.ChangeDutyCycle(duty_cycle)
            time.sleep(0.5)  # Allow servo to reach position
            self.servo.ChangeDutyCycle(0)  # Stop sending pulses to avoid jitter
        else:
            time.sleep(0.3)  # Simulate movement time
        
        self.current_angle = angle
    
    def align_to_road(self, road_bearing: float, robot_heading: float = 0.0):
        """
        Calculate and set optimal stencil angle for road alignment
        
        Args:
            road_bearing: Direction of the road (0-360 degrees)
            robot_heading: Current robot heading (0-360 degrees)
        """
        # Calculate relative angle between robot and road
        relative_angle = (road_bearing - robot_heading) % 360
        
        # Convert to stencil angle
        # Assuming stencil is mounted perpendicular to robot at 90 degrees
        # We want stencil to align with road
        if relative_angle > 180:
            relative_angle -= 360
        
        # Map relative angle to servo range
        # -90 to +90 degrees -> 0 to 180 servo angle
        servo_angle = self.HOME_ANGLE + relative_angle
        
        # Constrain to valid range
        servo_angle = max(0, min(180, servo_angle))
        
        logger.info(f"Aligning stencil: road_bearing={road_bearing:.1f}°, "
                   f"robot_heading={robot_heading:.1f}°, "
                   f"servo_angle={servo_angle:.1f}°")
        
        self.set_angle(servo_angle)
    
    def home_position(self):
        """Return stencil to home/center position"""
        logger.info("Moving stencil to home position")
        self.set_angle(self.HOME_ANGLE)
    
    def sweep_test(self):
        """
        Perform a sweep test for calibration
        Moves from 0 to 180 degrees and back
        """
        logger.info("Starting stencil sweep test")
        
        # Sweep right
        for angle in range(self.HOME_ANGLE, 181, 10):
            self.set_angle(angle)
            time.sleep(0.2)
        
        # Sweep left
        for angle in range(180, -1, -10):
            self.set_angle(angle)
            time.sleep(0.2)
        
        # Return to home
        self.home_position()
        
        logger.info("Sweep test complete")
    
    def get_angle(self) -> float:
        """
        Get current stencil angle
        
        Returns:
            Current angle in degrees
        """
        return self.current_angle
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        logger.info("Cleaning up stencil controller")
        
        # Return to home position before cleanup
        self.home_position()
        
        if not self.simulate:
            self.servo.stop()
            GPIO.cleanup([Config.STENCIL_SERVO_PIN])