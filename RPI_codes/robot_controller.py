#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Road Marking Robot Controller
==============================

Main controller with state machine for autonomous road marking operations.

States:
- IDLE: Waiting for deployment command via MQTT
- NAVIGATING: GPS navigation to target coordinates
- POSITIONING: Coarse positioning using GPS
- ALIGNING: Fine alignment using camera + wheel encoders
- PAINTING: Execute painting operation (lower stencil, dispense, raise)
- COMPLETED: Report success and return to IDLE
- ERROR: Handle errors and recovery

Author: GIQ 2025 Team
"""

import time
import logging
import math
import json
import argparse
from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass

# Robot modules
from ev3_comm import EV3Controller, EV3CommunicationError
from stencil_aligner import StencilAligner, AlignmentInstruction
from MTI_rtk8_lib import MTiParser, IMUData

# Import configuration
try:
    from ev3_config import *
except ImportError:
    # Fallback defaults
    GPS_ARRIVAL_THRESHOLD = 0.5
    HEADING_CORRECTION_THRESHOLD = 10
    MAX_ALIGNMENT_ATTEMPTS = 10
    POSITION_TOLERANCE_CM = 2.0
    STENCIL_LOWER_WAIT = 1.0
    PAINT_DISPENSE_TIME = 3.0
    STENCIL_RAISE_WAIT = 1.0
    MQTT_BROKER = "broker.hivemq.com"
    MQTT_TOPIC_DEPLOY = "giq/robot/deploy"
    MQTT_TOPIC_STATUS = "giq/robot/status"
    SIMULATION_MODE = False

logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class RobotState(Enum):
    """Robot operational states"""
    IDLE = "IDLE"
    NAVIGATING = "NAVIGATING"
    POSITIONING = "POSITIONING"
    ALIGNING = "ALIGNING"
    PAINTING = "PAINTING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class Mission:
    """Mission parameters"""
    target_lat: float
    target_lon: float
    mission_id: str = "unknown"
    start_time: float = 0.0


# ============================================================================
# MAIN ROBOT CONTROLLER
# ============================================================================

class RoadMarkingRobot:
    """
    Main robot controller with state machine.

    Usage:
        robot = RoadMarkingRobot(simulate=True)
        robot.start()

        # Deploy mission
        robot.deploy_mission(1.3521, 103.8198)

        # Main loop
        while robot.is_running():
            robot.update()
            time.sleep(0.1)

        robot.stop()
    """

    def __init__(self, simulate: bool = SIMULATION_MODE):
        """
        Initialize robot controller.

        Args:
            simulate: If True, runs without hardware
        """
        self.simulate = simulate
        self.running = False

        # State machine
        self.state = RobotState.IDLE
        self.mission = None

        # Hardware interfaces
        self.ev3 = None
        self.aligner = None
        self.gps = None

        # State tracking
        self.alignment_attempts = 0
        self.last_status_time = 0

        logger.info(f"RoadMarkingRobot initialized (simulate={simulate})")

    def start(self) -> bool:
        """
        Initialize all hardware and prepare for operation.

        Returns:
            True if initialization successful
        """
        logger.info("Starting robot controller...")

        try:
            # Initialize EV3 motor controller
            logger.info("Connecting to EV3...")
            self.ev3 = EV3Controller(simulate=self.simulate)
            if not self.ev3.connect():
                raise Exception("Failed to connect to EV3")
            logger.info("✓ EV3 connected")

            # Initialize camera alignment
            logger.info("Starting camera alignment...")
            self.aligner = StencilAligner(simulate=self.simulate)
            if not self.aligner.start():
                raise Exception("Failed to start camera")
            logger.info("✓ Camera started")

            # Initialize GPS
            if not self.simulate:
                logger.info("Connecting to GPS...")
                self.gps = MTiParser()
                if not self.gps.connect():
                    logger.warning("GPS connection failed - navigation disabled")
                else:
                    logger.info("✓ GPS connected")
            else:
                logger.info("Simulation mode - GPS disabled")

            self.running = True
            self.state = RobotState.IDLE

            logger.info("✓ Robot controller started")
            return True

        except Exception as e:
            logger.error(f"Failed to start robot: {e}")
            self.stop()
            return False

    def deploy_mission(self, target_lat: float, target_lon: float, mission_id: str = None):
        """
        Deploy new mission.

        Args:
            target_lat: Target latitude
            target_lon: Target longitude
            mission_id: Optional mission identifier
        """
        if self.state not in [RobotState.IDLE, RobotState.COMPLETED]:
            logger.warning(f"Cannot deploy mission - robot in state {self.state}")
            return

        self.mission = Mission(
            target_lat=target_lat,
            target_lon=target_lon,
            mission_id=mission_id or f"mission_{int(time.time())}",
            start_time=time.time()
        )

        self.state = RobotState.NAVIGATING
        self.alignment_attempts = 0

        logger.info(f"✓ Mission deployed: {self.mission.mission_id}")
        logger.info(f"  Target: ({target_lat:.6f}, {target_lon:.6f})")

    def update(self):
        """
        Main update loop - executes current state logic.
        Call this repeatedly in a loop.
        """
        if not self.running:
            return

        # State machine dispatcher
        try:
            if self.state == RobotState.IDLE:
                self._state_idle()
            elif self.state == RobotState.NAVIGATING:
                self._state_navigating()
            elif self.state == RobotState.POSITIONING:
                self._state_positioning()
            elif self.state == RobotState.ALIGNING:
                self._state_aligning()
            elif self.state == RobotState.PAINTING:
                self._state_painting()
            elif self.state == RobotState.COMPLETED:
                self._state_completed()
            elif self.state == RobotState.ERROR:
                self._state_error()

        except Exception as e:
            logger.error(f"State {self.state} error: {e}")
            self._transition_to_error(str(e))

    def _transition_to(self, new_state: RobotState):
        """Transition to new state with logging"""
        logger.info(f"State: {self.state.value} → {new_state.value}")
        self.state = new_state

    def _transition_to_error(self, error_message: str):
        """Transition to error state"""
        logger.error(f"ERROR: {error_message}")
        self._transition_to(RobotState.ERROR)

    # ========================================================================
    # STATE IMPLEMENTATIONS
    # ========================================================================

    def _state_idle(self):
        """IDLE state - waiting for mission deployment"""
        # Nothing to do - waiting for deploy_mission() call
        time.sleep(0.5)

    def _state_navigating(self):
        """NAVIGATING state - GPS navigation to target"""
        if not self.mission:
            self._transition_to_error("No mission defined")
            return

        # Get current GPS position
        current_pos = self._get_gps_position()
        if not current_pos:
            logger.warning("No GPS fix - cannot navigate")
            time.sleep(1.0)
            return

        current_lat, current_lon = current_pos
        target_lat, target_lon = self.mission.target_lat, self.mission.target_lon

        # Calculate distance and bearing to target
        distance, bearing = self._calculate_distance_bearing(
            current_lat, current_lon,
            target_lat, target_lon
        )

        logger.info(f"Distance to target: {distance:.2f}m, Bearing: {bearing:.1f}°")

        # Check if arrived
        if distance < GPS_ARRIVAL_THRESHOLD:
            logger.info(f"✓ Arrived at target (within {GPS_ARRIVAL_THRESHOLD}m)")
            self._transition_to(RobotState.POSITIONING)
            return

        # TODO: Implement actual GPS navigation with heading correction
        # For now, just simulate approach
        if self.simulate:
            logger.info("[SIM] Moving towards target...")
            time.sleep(2.0)
            self._transition_to(RobotState.POSITIONING)
        else:
            # In real implementation:
            # 1. Correct heading if needed
            # 2. Move forward in increments
            # 3. Check for obstacles
            # 4. Repeat until within threshold
            time.sleep(1.0)

    def _state_positioning(self):
        """POSITIONING state - coarse positioning using GPS"""
        logger.info("Coarse positioning complete")
        # Once GPS says we're close enough, switch to camera alignment
        self._transition_to(RobotState.ALIGNING)

    def _state_aligning(self):
        """ALIGNING state - fine alignment using camera"""
        if self.alignment_attempts >= MAX_ALIGNMENT_ATTEMPTS:
            self._transition_to_error(f"Alignment failed after {MAX_ALIGNMENT_ATTEMPTS} attempts")
            return

        # Get alignment instruction from camera
        instruction = self.aligner.get_alignment_instruction()

        logger.info(f"Alignment: {instruction.message}")

        # Check if aligned
        if instruction.aligned:
            logger.info("✓ Alignment complete!")
            self._transition_to(RobotState.PAINTING)
            return

        # Execute correction movement
        if instruction.direction == "LEFT":
            self._move_lateral(-instruction.distance_cm)
        elif instruction.direction == "RIGHT":
            self._move_lateral(instruction.distance_cm)
        elif instruction.direction == "ERROR":
            logger.warning(f"Alignment error: {instruction.message}")
            time.sleep(1.0)
        else:
            logger.warning(f"Unknown direction: {instruction.direction}")

        self.alignment_attempts += 1
        time.sleep(0.5)  # Brief pause between alignment attempts

    def _state_painting(self):
        """PAINTING state - execute painting operation"""
        logger.info("Starting painting sequence...")

        try:
            # 1. Lower stencil
            logger.info("→ Lowering stencil...")
            if not self.ev3.lower_stencil():
                raise Exception("Failed to lower stencil")
            time.sleep(STENCIL_LOWER_WAIT)

            # 2. Dispense paint
            logger.info(f"→ Dispensing paint for {PAINT_DISPENSE_TIME}s...")
            if not self.ev3.dispense_paint():
                raise Exception("Failed to dispense paint")
            time.sleep(PAINT_DISPENSE_TIME)

            # 3. Raise stencil
            logger.info("→ Raising stencil...")
            if not self.ev3.raise_stencil():
                raise Exception("Failed to raise stencil")
            time.sleep(STENCIL_RAISE_WAIT)

            logger.info("✓ Painting complete!")
            self._transition_to(RobotState.COMPLETED)

        except Exception as e:
            self._transition_to_error(f"Painting failed: {e}")

    def _state_completed(self):
        """COMPLETED state - mission finished"""
        if self.mission:
            duration = time.time() - self.mission.start_time
            logger.info(f"✓ Mission {self.mission.mission_id} completed in {duration:.1f}s")
            self.mission = None

        # Return to IDLE
        self._transition_to(RobotState.IDLE)

    def _state_error(self):
        """ERROR state - error handling"""
        logger.error("Robot in error state - manual intervention required")
        # Emergency stop all motors
        if self.ev3:
            self.ev3.stop()
        # Stay in error state until manually reset
        time.sleep(1.0)

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    def _get_gps_position(self) -> Optional[Tuple[float, float]]:
        """
        Get current GPS position.

        Returns:
            Tuple of (latitude, longitude) or None
        """
        if self.simulate:
            # Simulate GPS position
            if self.mission:
                # Simulate being near target
                return (self.mission.target_lat + 0.00001, self.mission.target_lon + 0.00001)
            return None

        if not self.gps:
            return None

        try:
            latlon = self.gps.read_latlon(timeout=1.0)
            return latlon
        except Exception as e:
            logger.warning(f"GPS read error: {e}")
            return None

    def _calculate_distance_bearing(self, lat1: float, lon1: float,
                                   lat2: float, lon2: float) -> Tuple[float, float]:
        """
        Calculate distance and bearing between two GPS coordinates.
        Uses Haversine formula.

        Returns:
            Tuple of (distance_meters, bearing_degrees)
        """
        # Haversine formula
        R = 6371000  # Earth radius in meters

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        # Calculate bearing
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        bearing = math.degrees(math.atan2(y, x))
        bearing = (bearing + 360) % 360  # Normalize to 0-360

        return distance, bearing

    def _move_lateral(self, distance_cm: float):
        """
        Move robot laterally (sideways) using rotate-move-rotate technique.

        Args:
            distance_cm: Distance to move (positive=right, negative=left)
        """
        direction = "right" if distance_cm > 0 else "left"
        distance_cm = abs(distance_cm)

        logger.info(f"Moving {direction} {distance_cm:.1f}cm")

        try:
            # 1. Rotate 90° in direction
            rotate_angle = 90 if direction == "right" else -90
            self.ev3.rotate(rotate_angle, speed=PRECISION_SPEED)

            # 2. Move forward
            self.ev3.move_forward(distance_cm, speed=PRECISION_SPEED)

            # 3. Rotate back
            self.ev3.rotate(-rotate_angle, speed=PRECISION_SPEED)

            logger.info(f"✓ Lateral movement complete")

        except Exception as e:
            logger.error(f"Lateral movement failed: {e}")
            raise

    def is_running(self) -> bool:
        """Check if robot is running"""
        return self.running

    def stop(self):
        """Stop robot and cleanup"""
        logger.info("Stopping robot controller...")

        self.running = False

        # Stop motors
        if self.ev3:
            self.ev3.stop()
            self.ev3.disconnect()

        # Stop camera
        if self.aligner:
            self.aligner.stop()

        # Disconnect GPS
        if self.gps:
            self.gps.disconnect()

        logger.info("✓ Robot controller stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Road Marking Robot Controller')
    parser.add_argument('--simulate', action='store_true', help='Run in simulation mode')
    parser.add_argument('--deploy', nargs=2, type=float, metavar=('LAT', 'LON'),
                       help='Deploy mission with target coordinates')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 70)
    print("ROAD MARKING ROBOT CONTROLLER")
    print("=" * 70)
    print(f"Mode: {'SIMULATION' if args.simulate else 'HARDWARE'}")
    print("=" * 70 + "\n")

    try:
        # Initialize robot
        with RoadMarkingRobot(simulate=args.simulate) as robot:
            logger.info("✓ Robot initialized")

            # Deploy mission if specified
            if args.deploy:
                lat, lon = args.deploy
                robot.deploy_mission(lat, lon, mission_id="cli_mission")

            # Main loop
            logger.info("Entering main loop (Ctrl+C to exit)...")
            while robot.is_running():
                robot.update()
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
