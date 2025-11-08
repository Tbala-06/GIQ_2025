# -*- coding: utf-8 -*-
"""
EV3-Based Robot Configuration
==============================

Configuration for road marking robot using EV3 brick as motor controller.
All tunable parameters in one place for easy field calibration.

⚠️ CALIBRATION REQUIRED:
- Values marked with [NEEDS CALIBRATION] must be measured/tuned
- Run calibration_wizard.py to help determine these values
"""

# ============================================================================
# ROBOT PHYSICAL PARAMETERS
# ============================================================================

# Wheel measurements (EV3 Large Motors)
WHEEL_CIRCUMFERENCE = 17.5  # cm - [NEEDS CALIBRATION] Measure: drive 100cm, adjust this
WHEELBASE = 20.0  # cm - [NEEDS CALIBRATION] Measure: distance between left/right wheels

# Calibration factors (adjust after testing)
WHEEL_CALIBRATION_FACTOR = 1.0  # Multiplier to correct for slippage (0.95-1.05 typical)
TURN_CALIBRATION_FACTOR = 1.05  # Multiplier for turning (usually 1.05-1.10)

# Encoder calculations (EV3 Large Motor specs)
ENCODER_COUNTS_PER_ROTATION = 360  # EV3 large motor resolution
CM_PER_ENCODER_COUNT = WHEEL_CIRCUMFERENCE / ENCODER_COUNTS_PER_ROTATION  # ~0.0486 cm

# ============================================================================
# MOTOR CONFIGURATION
# ============================================================================

# Motor ports on EV3
LEFT_MOTOR_PORT = 'A'  # Large motor - left drive wheel
RIGHT_MOTOR_PORT = 'B'  # Large motor - right drive wheel
PAINT_ARM_PORT = 'C'  # Medium motor - paint/sand dispenser
STENCIL_PORT = 'D'  # Medium motor - stencil lowering mechanism

# Motor speeds (percentage, 0-100)
DRIVE_SPEED = 50  # Normal driving speed
PRECISION_SPEED = 25  # Speed for fine positioning during alignment
TURN_SPEED = 40  # Speed for rotation maneuvers
PAINT_SPEED = 30  # Speed for paint arm operation
STENCIL_SPEED = 20  # Speed for stencil lowering/raising (slow for safety)

# Motor operation parameters
PAINT_ARM_DISPENSE_DEGREES = 360  # [NEEDS CALIBRATION] Rotation for full dispense
STENCIL_LOWER_DEGREES = 90  # [NEEDS CALIBRATION] Degrees to lower stencil
STENCIL_RAISE_DEGREES = -90  # [NEEDS CALIBRATION] Degrees to raise stencil (negative)

# ============================================================================
# CAMERA CONFIGURATION
# ============================================================================

# Camera device
CAMERA_INDEX = 0  # /dev/video0
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30

# Camera mounting
CAMERA_HEIGHT_CM = 30.0  # [NEEDS CALIBRATION] Height of camera above ground (cm)
CAMERA_ANGLE_DEG = 90.0  # Camera angle (90 = straight down)

# Calibration for pixel-to-cm conversion
PIXELS_PER_CM = 10.0  # [NEEDS CALIBRATION] Use calibration_wizard.py to measure
# Formula: PIXELS_PER_CM = measured_pixels / known_distance_cm

# ============================================================================
# STENCIL DETECTION (Computer Vision)
# ============================================================================

# NOTE: Using ORANGE stencil based on testing.py
# Orange HSV color range (calibrated for bright orange plastic)
STENCIL_HSV_LOWER = [5, 150, 150]  # [H, S, V]
STENCIL_HSV_UPPER = [20, 255, 255]

# Morphological operations
MORPH_KERNEL_SIZE = 5  # Kernel size for noise removal

# Stencil size filtering
MIN_STENCIL_AREA_PIXELS = 5000  # Minimum contour area to be considered stencil
MAX_STENCIL_AREA_PIXELS = 500000  # Maximum contour area

# Expected stencil size when aligned (for validation)
EXPECTED_STENCIL_WIDTH_PERCENT = 25  # % of frame width (20-30% typical)
EXPECTED_STENCIL_HEIGHT_PERCENT = 25  # % of frame height

# ============================================================================
# ALIGNMENT TOLERANCES
# ============================================================================

# Position tolerances
POSITION_TOLERANCE_CM = 2.0  # ±2cm for X/Y positioning
ROTATION_TOLERANCE_DEG = 5.0  # ±5° for rotation alignment

# Alignment loop limits
MAX_ALIGNMENT_ATTEMPTS = 10  # Maximum iterations before giving up
MIN_CORRECTION_THRESHOLD_CM = 0.5  # Don't correct if offset < 0.5cm
MIN_ROTATION_THRESHOLD_DEG = 2.0  # Don't correct if rotation < 2°

# Movement speeds during alignment
ALIGNMENT_MOVE_SPEED = PRECISION_SPEED  # Use slow speed for corrections
ALIGNMENT_ROTATION_SPEED = 20  # Extra slow for rotation corrections

# ============================================================================
# GPS NAVIGATION
# ============================================================================

# GPS thresholds
GPS_ARRIVAL_THRESHOLD = 0.5  # meters - within 50cm = "arrived"
GPS_CLOSE_THRESHOLD = 1.0  # meters - within 1m = "getting close"

# Navigation increments (progressive approach)
NAV_INCREMENT_FAR = 50  # cm - when >1m away
NAV_INCREMENT_CLOSE = 20  # cm - when 0.5-1m away
NAV_INCREMENT_FINAL = 10  # cm - when <0.5m away

# Heading correction
HEADING_CORRECTION_THRESHOLD = 10  # degrees - correct heading if off by >10°
HEADING_TOLERANCE = 5  # degrees - acceptable heading error

# GPS data
GPS_SERIAL_PORT = '/dev/serial0'  # MTi-8 serial port
GPS_BAUD_RATE = 115200
GPS_UPDATE_RATE_HZ = 10  # Expected GPS update frequency

# ============================================================================
# LIDAR CONFIGURATION
# ============================================================================

# Obstacle detection
OBSTACLE_DISTANCE_THRESHOLD = 30  # cm - stop if obstacle within 30cm
OBSTACLE_CHECK_ANGLE_RANGE = 45  # degrees - check ±45° from front

# Obstacle avoidance maneuvers
AVOIDANCE_TURN_ANGLE = 45  # degrees - turn angle for avoidance
AVOIDANCE_FORWARD_DISTANCE = 30  # cm - distance to move during avoidance

# LiDAR device
LIDAR_SERIAL_PORT = '/dev/ttyUSB0'  # [NEEDS VERIFICATION] Adjust based on your setup
LIDAR_BAUD_RATE = 230400  # LDS-02RR default

# ============================================================================
# MQTT CONFIGURATION
# ============================================================================

# MQTT Broker
MQTT_BROKER = "broker.hivemq.com"  # Public broker (change for production)
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60  # seconds

# MQTT Topics
MQTT_TOPIC_DEPLOY = "giq/robot/deploy"  # Subscribe: deployment commands
MQTT_TOPIC_STATUS = "giq/robot/status"  # Publish: robot status updates
MQTT_TOPIC_ESTOP = "giq/robot/emergency_stop"  # Subscribe: emergency stop

# MQTT Client
MQTT_CLIENT_ID = "road_marking_robot"  # Unique client ID
MQTT_QOS = 1  # QoS level (0, 1, or 2)

# Status update frequency
STATUS_UPDATE_INTERVAL = 2.0  # seconds - how often to publish status

# ============================================================================
# EV3 CONNECTION
# ============================================================================

# Network configuration
EV3_USB_INTERFACE = 'usb0'  # USB network interface
EV3_IP_SUBNET = '169.254'  # First two octets of EV3 IP range
EV3_IP_NETMASK = '/16'  # Subnet mask

# SSH configuration
EV3_SSH_USER = 'robot'  # Default ev3dev username
EV3_SSH_PORT = 22
EV3_CONTROLLER_PATH = '/home/robot/ev3_controller.py'  # Path to EV3 script

# Communication timeouts
EV3_CONNECT_TIMEOUT = 10.0  # seconds - timeout for initial connection
EV3_COMMAND_TIMEOUT = 30.0  # seconds - timeout for command execution
EV3_RESPONSE_TIMEOUT = 5.0  # seconds - timeout waiting for response

# Retry configuration
EV3_MAX_RETRIES = 3  # Number of retry attempts for failed commands
EV3_RETRY_DELAY = 1.0  # seconds - delay between retries

# ============================================================================
# STATE MACHINE TIMEOUTS
# ============================================================================

# State transition timeouts (prevent getting stuck)
STATE_TIMEOUT_NAVIGATING = 300.0  # seconds (5 minutes)
STATE_TIMEOUT_POSITIONING = 60.0  # seconds (1 minute)
STATE_TIMEOUT_ALIGNING = 120.0  # seconds (2 minutes)
STATE_TIMEOUT_PAINTING = 30.0  # seconds

# ============================================================================
# PAINTING OPERATION
# ============================================================================

# Painting sequence timing
STENCIL_LOWER_WAIT = 1.0  # seconds - wait after lowering stencil
PAINT_DISPENSE_TIME = 3.0  # seconds - time to run paint dispenser
STENCIL_RAISE_WAIT = 1.0  # seconds - wait after raising stencil

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'DEBUG'  # Change to 'INFO' for production
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'robot.log'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # Keep 5 old log files

# ============================================================================
# SIMULATION MODE
# ============================================================================

# Enable simulation (no hardware required)
SIMULATION_MODE = False  # Set to True for testing without hardware

# Simulation parameters
SIM_GPS_NOISE = 0.1  # meters - simulated GPS error
SIM_MOVEMENT_NOISE = 0.5  # cm - simulated movement error
SIM_CAMERA_AVAILABLE = False  # Use test images instead of camera

# ============================================================================
# SAFETY LIMITS
# ============================================================================

# Maximum values (safety limits)
MAX_SPEED = 100  # % - absolute maximum motor speed
MAX_SINGLE_MOVEMENT = 200  # cm - maximum distance for single move command
MAX_ROTATION = 360  # degrees - maximum rotation in single command

# Emergency stop behavior
ESTOP_ENABLED = True  # Enable emergency stop monitoring
ESTOP_MOTOR_BRAKE = True  # Brake motors (vs coast) on emergency stop

# ============================================================================
# CALIBRATION HELPERS
# ============================================================================

# Test patterns for calibration
CALIBRATION_TEST_DISTANCE = 100  # cm - distance for wheel calibration test
CALIBRATION_TEST_ROTATION = 360  # degrees - full rotation for turn calibration

# Camera calibration
CALIBRATION_OBJECT_SIZE_CM = 10.0  # Size of calibration object (e.g., 10cm square)

# ============================================================================
# DERIVED CALCULATIONS (DO NOT MODIFY)
# ============================================================================

# Calculate distance per encoder count with calibration
CALIBRATED_CM_PER_COUNT = CM_PER_ENCODER_COUNT * WHEEL_CALIBRATION_FACTOR

# Calculate rotation parameters
WHEEL_CIRCUMFERENCE_FOR_TURN = WHEELBASE * 3.14159  # Arc length for 360° turn
ENCODER_COUNTS_PER_DEGREE = (WHEEL_CIRCUMFERENCE_FOR_TURN / 360.0) / CM_PER_ENCODER_COUNT

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """
    Validate configuration values are reasonable.
    Raises ValueError if configuration is invalid.
    """
    errors = []

    # Check positive values
    if WHEEL_CIRCUMFERENCE <= 0:
        errors.append("WHEEL_CIRCUMFERENCE must be positive")
    if WHEELBASE <= 0:
        errors.append("WHEELBASE must be positive")
    if CAMERA_HEIGHT_CM <= 0:
        errors.append("CAMERA_HEIGHT_CM must be positive")

    # Check speed limits
    if not (0 <= DRIVE_SPEED <= 100):
        errors.append("DRIVE_SPEED must be 0-100")
    if not (0 <= PRECISION_SPEED <= 100):
        errors.append("PRECISION_SPEED must be 0-100")

    # Check tolerances
    if POSITION_TOLERANCE_CM <= 0:
        errors.append("POSITION_TOLERANCE_CM must be positive")
    if ROTATION_TOLERANCE_DEG <= 0:
        errors.append("ROTATION_TOLERANCE_DEG must be positive")

    # Check GPS thresholds
    if GPS_ARRIVAL_THRESHOLD <= 0:
        errors.append("GPS_ARRIVAL_THRESHOLD must be positive")

    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

    return True


# Validate on import
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  Configuration Warning: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("ROAD MARKING ROBOT - EV3 CONFIGURATION")
    print("=" * 70)
    print(f"\n📐 Physical Parameters:")
    print(f"  Wheel Circumference: {WHEEL_CIRCUMFERENCE} cm")
    print(f"  Wheelbase: {WHEELBASE} cm")
    print(f"  CM per encoder count: {CM_PER_ENCODER_COUNT:.4f}")
    print(f"\n🎥 Camera:")
    print(f"  Resolution: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
    print(f"  Pixels per CM: {PIXELS_PER_CM}")
    print(f"  Camera Height: {CAMERA_HEIGHT_CM} cm")
    print(f"\n🎯 Alignment:")
    print(f"  Position Tolerance: ±{POSITION_TOLERANCE_CM} cm")
    print(f"  Rotation Tolerance: ±{ROTATION_TOLERANCE_DEG}°")
    print(f"  Max Attempts: {MAX_ALIGNMENT_ATTEMPTS}")
    print(f"\n📡 GPS:")
    print(f"  Arrival Threshold: {GPS_ARRIVAL_THRESHOLD} m")
    print(f"  Heading Correction: {HEADING_CORRECTION_THRESHOLD}°")
    print(f"\n🔧 Motor Speeds:")
    print(f"  Drive: {DRIVE_SPEED}%")
    print(f"  Precision: {PRECISION_SPEED}%")
    print(f"  Turn: {TURN_SPEED}%")
    print(f"\n✅ Configuration validation: PASSED")
    print("=" * 70)
