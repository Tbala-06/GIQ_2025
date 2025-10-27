#!/usr/bin/env python3
"""
Configuration loader for robot controller.
Loads settings from .env file.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the robot"""
    
    # Robot Identification
    ROBOT_ID = os.getenv('ROBOT_ID', 'robot_001')
    ROBOT_NAME = os.getenv('ROBOT_NAME', 'PaintBot Alpha')
    
    # MQTT Configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'test.mosquitto.org')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', None) or None
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None) or None
    MQTT_TOPIC_COMMANDS = os.getenv('MQTT_TOPIC_COMMANDS', 'bot/commands/deploy')
    MQTT_TOPIC_STATUS = os.getenv('MQTT_TOPIC_STATUS', 'robot/status')
    MQTT_TOPIC_COMPLETE = os.getenv('MQTT_TOPIC_COMPLETE', 'robot/job/complete')
    
    # Hardware Configuration
    MTI_SERIAL_PORT = os.getenv('MTI_SERIAL_PORT', '/dev/serial0')
    MTI_BAUDRATE = int(os.getenv('MTI_BAUDRATE', 115200))
    MOTOR_LEFT_PWM = int(os.getenv('MOTOR_LEFT_PWM', 12))
    MOTOR_LEFT_DIR1 = int(os.getenv('MOTOR_LEFT_DIR1', 16))
    MOTOR_LEFT_DIR2 = int(os.getenv('MOTOR_LEFT_DIR2', 20))
    MOTOR_RIGHT_PWM = int(os.getenv('MOTOR_RIGHT_PWM', 13))
    MOTOR_RIGHT_DIR1 = int(os.getenv('MOTOR_RIGHT_DIR1', 19))
    MOTOR_RIGHT_DIR2 = int(os.getenv('MOTOR_RIGHT_DIR2', 26))
    STENCIL_SERVO_PIN = int(os.getenv('STENCIL_SERVO_PIN', 18))
    PAINT_DISPENSER_PIN = int(os.getenv('PAINT_DISPENSER_PIN', 23))
    
    # Navigation Configuration
    GPS_ACCURACY_THRESHOLD = float(os.getenv('GPS_ACCURACY_THRESHOLD', 5.0))
    ARRIVAL_TOLERANCE_METERS = float(os.getenv('ARRIVAL_TOLERANCE_METERS', 2.0))
    MAX_ROAD_SEARCH_DISTANCE = float(os.getenv('MAX_ROAD_SEARCH_DISTANCE', 50.0))
    ROAD_ALIGNMENT_TOLERANCE_DEGREES = float(os.getenv('ROAD_ALIGNMENT_TOLERANCE_DEGREES', 5.0))
    
    # Operation Configuration
    PAINT_DISPENSE_DURATION = float(os.getenv('PAINT_DISPENSE_DURATION', 5.0))
    STATUS_REPORT_INTERVAL = float(os.getenv('STATUS_REPORT_INTERVAL', 10.0))
    MAX_MISSION_DURATION = float(os.getenv('MAX_MISSION_DURATION', 300.0))
    
    # Safety Configuration
    MIN_GPS_SATELLITES = int(os.getenv('MIN_GPS_SATELLITES', 4))
    MIN_BATTERY_LEVEL = int(os.getenv('MIN_BATTERY_LEVEL', 20))
    MAX_TILT_ANGLE = float(os.getenv('MAX_TILT_ANGLE', 30))
    EMERGENCY_STOP_PIN = int(os.getenv('EMERGENCY_STOP_PIN', 21))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/home/pi/robot.log')
    
    # GeoJSON Data
    GEOJSON_ROADS_FILE = os.getenv('GEOJSON_ROADS_FILE', './data/roads.geojson')
    
    @classmethod
    def validate(cls):
        """Validate critical configuration values"""
        errors = []
        
        if not cls.MQTT_BROKER:
            errors.append("MQTT_BROKER is required")
        
        if cls.ARRIVAL_TOLERANCE_METERS <= 0:
            errors.append("ARRIVAL_TOLERANCE_METERS must be positive")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True

# Validate configuration on import
Config.validate()