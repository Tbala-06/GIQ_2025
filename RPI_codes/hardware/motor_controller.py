#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor Controller for Robot Movement
Handles differential drive motor control via GPIO
"""

import time
import math
from typing import Tuple, Optional

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("WARNING: RPi.GPIO not available, running in simulation mode")

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class MotorController:
    """Control motors for robot movement"""
    
    def __init__(self, simulate=False):
        """
        Initialize motor controller
        
        Args:
            simulate: If True, run in simulation mode without GPIO
        """
        self.simulate = simulate or not GPIO_AVAILABLE
        
        # Odometry tracking
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0  # degrees
        self.wheel_base = 0.3  # meters (distance between wheels)
        self.wheel_diameter = 0.1  # meters
        
        if not self.simulate:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Left motor pins
            GPIO.setup(Config.MOTOR_LEFT_PWM, GPIO.OUT)
            GPIO.setup(Config.MOTOR_LEFT_DIR1, GPIO.OUT)
            GPIO.setup(Config.MOTOR_LEFT_DIR2, GPIO.OUT)
            
            # Right motor pins
            GPIO.setup(Config.MOTOR_RIGHT_PWM, GPIO.OUT)
            GPIO.setup(Config.MOTOR_RIGHT_DIR1, GPIO.OUT)
            GPIO.setup(Config.MOTOR_RIGHT_DIR2, GPIO.OUT)
            
            # Setup PWM (1000 Hz frequency)
            self.left_pwm = GPIO.PWM(Config.MOTOR_LEFT_PWM, 1000)
            self.right_pwm = GPIO.PWM(Config.MOTOR_RIGHT_PWM, 1000)
            self.left_pwm.start(0)
            self.right_pwm.start(0)
            
            logger.info("Motor controller initialized (GPIO mode)")
        else:
            logger.info("Motor controller initialized (SIMULATION mode)")
        
        self.current_speed = 0
        self.is_moving = False
    
    def _set_left_motor(self, speed: int, forward: bool):
        """
        Set left motor speed and direction
        
        Args:
            speed: PWM duty cycle (0-100)
            forward: True for forward, False for backward
        """
        if self.simulate:
            return
        
        GPIO.output(Config.MOTOR_LEFT_DIR1, GPIO.HIGH if forward else GPIO.LOW)
        GPIO.output(Config.MOTOR_LEFT_DIR2, GPIO.LOW if forward else GPIO.HIGH)
        self.left_pwm.ChangeDutyCycle(abs(speed))
    
    def _set_right_motor(self, speed: int, forward: bool):
        """
        Set right motor speed and direction
        
        Args:
            speed: PWM duty cycle (0-100)
            forward: True for forward, False for backward
        """
        if self.simulate:
            return
        
        GPIO.output(Config.MOTOR_RIGHT_DIR1, GPIO.HIGH if forward else GPIO.LOW)
        GPIO.output(Config.MOTOR_RIGHT_DIR2, GPIO.LOW if forward else GPIO.HIGH)
        self.right_pwm.ChangeDutyCycle(abs(speed))
    
    def move_forward(self, speed: int = 50, distance_meters: Optional[float] = None):
        """
        Move robot forward
        
        Args:
            speed: Motor speed (0-100)
            distance_meters: If specified, move this distance and stop
        """
        logger.info(f"Moving forward at speed {speed}" + 
                   (f" for {distance_meters}m" if distance_meters else ""))
        
        self._set_left_motor(speed, True)
        self._set_right_motor(speed, True)
        self.current_speed = speed
        self.is_moving = True
        
        if distance_meters:
            # Calculate time needed (rough estimate)
            # Assuming speed 50 = ~0.5 m/s
            estimated_speed_ms = (speed / 100.0) * 0.5
            duration = distance_meters / estimated_speed_ms if estimated_speed_ms > 0 else 0
            
            time.sleep(duration)
            self.stop()
            
            # Update odometry
            self.x += distance_meters * math.cos(math.radians(self.heading))
            self.y += distance_meters * math.sin(math.radians(self.heading))
    
    def move_backward(self, speed: int = 50, distance_meters: Optional[float] = None):
        """
        Move robot backward
        
        Args:
            speed: Motor speed (0-100)
            distance_meters: If specified, move this distance and stop
        """
        logger.info(f"Moving backward at speed {speed}" + 
                   (f" for {distance_meters}m" if distance_meters else ""))
        
        self._set_left_motor(speed, False)
        self._set_right_motor(speed, False)
        self.current_speed = -speed
        self.is_moving = True
        
        if distance_meters:
            estimated_speed_ms = (speed / 100.0) * 0.5
            duration = distance_meters / estimated_speed_ms if estimated_speed_ms > 0 else 0
            
            time.sleep(duration)
            self.stop()
            
            # Update odometry
            self.x -= distance_meters * math.cos(math.radians(self.heading))
            self.y -= distance_meters * math.sin(math.radians(self.heading))
    
    def turn_left(self, angle_degrees: float, speed: int = 40):
        """
        Turn robot left by specified angle
        
        Args:
            angle_degrees: Angle to turn (degrees)
            speed: Motor speed (0-100)
        """
        logger.info(f"Turning left {angle_degrees} degrees")
        
        # Left motor backward, right motor forward for left turn
        self._set_left_motor(speed, False)
        self._set_right_motor(speed, True)
        
        # Calculate turn duration (rough estimate)
        # Assuming 360 degrees takes ~4 seconds at speed 50
        turn_rate = 90.0  # degrees per second at speed 50
        duration = (angle_degrees / turn_rate) * (50.0 / speed)
        
        time.sleep(duration)
        self.stop()
        
        # Update heading
        self.heading = (self.heading + angle_degrees) % 360
    
    def turn_right(self, angle_degrees: float, speed: int = 40):
        """
        Turn robot right by specified angle
        
        Args:
            angle_degrees: Angle to turn (degrees)
            speed: Motor speed (0-100)
        """
        logger.info(f"Turning right {angle_degrees} degrees")
        
        # Left motor forward, right motor backward for right turn
        self._set_left_motor(speed, True)
        self._set_right_motor(speed, False)
        
        # Calculate turn duration
        turn_rate = 90.0  # degrees per second at speed 50
        duration = (angle_degrees / turn_rate) * (50.0 / speed)
        
        time.sleep(duration)
        self.stop()
        
        # Update heading
        self.heading = (self.heading - angle_degrees) % 360
    
    def turn_to_bearing(self, target_bearing: float, speed: int = 40):
        """
        Turn robot to face a specific bearing
        
        Args:
            target_bearing: Target bearing in degrees (0-360)
            speed: Motor speed (0-100)
        """
        # Calculate shortest turn angle
        angle_diff = (target_bearing - self.heading) % 360
        
        if angle_diff > 180:
            # Turn right
            turn_angle = 360 - angle_diff
            self.turn_right(turn_angle, speed)
        else:
            # Turn left
            self.turn_left(angle_diff, speed)
    
    def stop(self):
        """Stop all motors"""
        logger.info("Stopping motors")
        
        if not self.simulate:
            self.left_pwm.ChangeDutyCycle(0)
            self.right_pwm.ChangeDutyCycle(0)
        
        self.current_speed = 0
        self.is_moving = False
    
    def get_odometry(self) -> Tuple[float, float, float]:
        """
        Get current robot position and heading
        
        Returns:
            (x, y, heading) - position in meters, heading in degrees
        """
        return (self.x, self.y, self.heading)
    
    def set_odometry(self, x: float, y: float, heading: float):
        """
        Manually set odometry (useful for GPS corrections)
        
        Args:
            x: X position in meters
            y: Y position in meters
            heading: Heading in degrees
        """
        self.x = x
        self.y = y
        self.heading = heading % 360
        logger.debug(f"Odometry updated: x={x:.2f}, y={y:.2f}, heading={heading:.1f}")
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        logger.info("Cleaning up motor controller")
        self.stop()
        
        if not self.simulate:
            self.left_pwm.stop()
            self.right_pwm.stop()
            GPIO.cleanup([
                Config.MOTOR_LEFT_PWM, Config.MOTOR_LEFT_DIR1, Config.MOTOR_LEFT_DIR2,
                Config.MOTOR_RIGHT_PWM, Config.MOTOR_RIGHT_DIR1, Config.MOTOR_RIGHT_DIR2
            ])