#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Executor Module
Coordinates all subsystems to execute painting missions.
"""

import time
from typing import Optional, Dict
from utils.logger import get_logger
from control.robot_state import RobotState
from config import Config

logger = get_logger(__name__)


class MissionExecutor:
    """Executes road painting missions from start to finish"""

    def __init__(self, state_manager, gps_navigator, road_finder,
                 motor, stencil, paint, status_reporter):
        """
        Initialize Mission Executor.

        Args:
            state_manager: StateManager instance
            gps_navigator: GPSNavigator instance
            road_finder: RoadFinder instance
            motor: MotorController instance
            stencil: StencilController instance
            paint: PaintDispenser instance
            status_reporter: StatusReporter instance
        """
        self.state = state_manager
        self.gps = gps_navigator
        self.roads = road_finder
        self.motor = motor
        self.stencil = stencil
        self.paint = paint
        self.status = status_reporter

        self.current_mission = None
        self.mission_start_time = None

        logger.info("Mission Executor initialized")

    def start_mission(self, job_data: Dict):
        """
        Begin new painting mission.

        Args:
            job_data: Dictionary with job_id, latitude, longitude
        """
        if self.has_active_mission():
            logger.warning("Mission already active, aborting current mission")
            self.abort_mission("New mission requested")

        self.current_mission = {
            'job_id': job_data['job_id'],
            'target_lat': job_data['latitude'],
            'target_lon': job_data['longitude'],
            'step': 'navigation',  # navigation → positioning → painting → completion
            'progress': 0
        }

        self.mission_start_time = time.time()

        logger.info(f"🎯 Mission started: Job #{self.current_mission['job_id']}")
        logger.info(f"Target: ({self.current_mission['target_lat']:.6f}, {self.current_mission['target_lon']:.6f})")

        # Update status
        self.status.set_current_job(self.current_mission['job_id'])
        self.status.update_status("dispatched")

        # Transition to MOVING state
        self.state.set_state(RobotState.MOVING)

    def execute_mission_step(self):
        """Execute one step of current mission (called repeatedly in main loop)"""
        if not self.has_active_mission():
            return

        # Check mission timeout
        elapsed = time.time() - self.mission_start_time
        if elapsed > Config.MAX_MISSION_DURATION:
            logger.error(f"Mission timeout after {elapsed:.1f}s")
            self.abort_mission("Mission timeout")
            return

        # Execute appropriate step
        try:
            step = self.current_mission['step']

            if step == 'navigation':
                self._execute_navigation()
            elif step == 'positioning':
                self._execute_positioning()
            elif step == 'painting':
                self._execute_painting()
            elif step == 'completion':
                self._execute_completion()
            else:
                logger.error(f"Unknown mission step: {step}")
                self.abort_mission(f"Invalid step: {step}")

        except Exception as e:
            logger.error(f"Mission step error: {e}", exc_info=True)
            self.abort_mission(f"Error: {str(e)}")

    def abort_mission(self, reason: str):
        """
        Abort current mission.

        Args:
            reason: Reason for aborting
        """
        if not self.has_active_mission():
            return

        logger.warning(f"🛑 Aborting mission: {reason}")

        # Stop all hardware
        self.motor.stop()
        self.paint.stop_dispensing()
        self.stencil.home_position()

        # Report failure
        if self.current_mission:
            self.status.update_status("aborted")
            self.status.publish_job_complete(
                self.current_mission['job_id'],
                success=False,
                message=f"Mission aborted: {reason}"
            )

        # Clear mission
        self.current_mission = None
        self.mission_start_time = None
        self.status.set_current_job(None)

        # Return to IDLE
        self.state.reset_to_idle()

    def get_mission_progress(self) -> int:
        """
        Get mission progress percentage.

        Returns:
            Progress (0-100)
        """
        if not self.has_active_mission():
            return 0

        return self.current_mission.get('progress', 0)

    def has_active_mission(self) -> bool:
        """Check if mission is active"""
        return self.current_mission is not None

    def _execute_navigation(self):
        """Navigate to target GPS coordinates"""
        logger.info("📍 Executing navigation step")

        self.state.set_state(RobotState.MOVING)
        self.status.update_status("moving")

        # Navigate to target
        success = self.gps.navigate_to(
            self.current_mission['target_lat'],
            self.current_mission['target_lon'],
            tolerance_meters=Config.ARRIVAL_TOLERANCE_METERS,
            max_duration=Config.MAX_MISSION_DURATION * 0.6  # 60% of total time for navigation
        )

        if success:
            logger.info("✅ Navigation complete")
            self.current_mission['step'] = 'positioning'
            self.current_mission['progress'] = 30
        else:
            logger.error("❌ Navigation failed")
            self.abort_mission("Navigation failed")

    def _execute_positioning(self):
        """Find road and position robot perpendicularly"""
        logger.info("🎯 Executing positioning step")

        self.state.set_state(RobotState.POSITIONING)
        self.status.update_status("positioning")

        # Get current position
        current_pos = self.gps.get_current_position()
        if not current_pos:
            logger.error("Cannot get current position")
            self.abort_mission("Lost GPS signal")
            return

        # Find nearest road
        road = self.roads.find_nearest_road(
            current_pos[0], current_pos[1],
            max_distance_meters=Config.MAX_ROAD_SEARCH_DISTANCE
        )

        if not road:
            logger.error("No road found nearby")
            self.abort_mission("No road found")
            return

        logger.info(f"Found road at {road.distance:.2f}m, bearing {road.bearing:.1f}°")

        # Get current heading
        current_heading = self.gps.get_heading()
        if current_heading is None:
            current_heading = road.bearing  # Assume we're aligned

        # Calculate perpendicular bearing to road
        from utils.road_geometry import calculate_road_perpendicular_bearing, is_aligned_with_road
        target_bearing = calculate_road_perpendicular_bearing(road.bearing)

        # Turn to face perpendicular to road
        if not is_aligned_with_road(target_bearing, current_heading, Config.ROAD_ALIGNMENT_TOLERANCE_DEGREES):
            logger.info(f"Aligning to bearing {target_bearing:.1f}°")
            self.motor.turn_to_bearing(target_bearing, speed=40)
        else:
            logger.info("Already aligned with road")

        # Move to position next to road if needed
        if road.distance > 2.0:  # If more than 2m from road
            logger.info(f"Moving closer to road ({road.distance:.2f}m)")
            self.motor.move_forward(speed=40, distance_meters=road.distance - 1.0)

        logger.info("✅ Positioning complete")
        self.current_mission['step'] = 'painting'
        self.current_mission['progress'] = 60
        self.current_mission['road_bearing'] = road.bearing

    def _execute_painting(self):
        """Align stencil and dispense paint"""
        logger.info("🎨 Executing painting step")

        self.state.set_state(RobotState.PAINTING)
        self.status.update_status("painting")

        # Get road bearing from mission data
        road_bearing = self.current_mission.get('road_bearing', 0)

        # Get current heading
        robot_heading = self.gps.get_heading() or 0

        # Align stencil with road
        from utils.road_geometry import calculate_stencil_angle
        stencil_angle = calculate_stencil_angle(road_bearing, robot_heading)

        logger.info(f"Setting stencil angle: {stencil_angle:.1f}°")
        self.stencil.set_angle(stencil_angle)

        # Wait for servo to reach position
        time.sleep(1.0)

        # Dispense paint
        logger.info(f"Dispensing paint for {Config.PAINT_DISPENSE_DURATION}s")
        self.paint.dispense(duration_seconds=Config.PAINT_DISPENSE_DURATION)

        # Return stencil to home
        self.stencil.home_position()

        logger.info("✅ Painting complete")
        self.current_mission['step'] = 'completion'
        self.current_mission['progress'] = 90

    def _execute_completion(self):
        """Complete mission and report results"""
        logger.info("✅ Executing completion step")

        self.state.set_state(RobotState.COMPLETED)
        self.status.update_status("completed")

        # Report job completion
        job_id = self.current_mission['job_id']
        elapsed = time.time() - self.mission_start_time

        logger.info(f"🎉 Mission completed! Job #{job_id} in {elapsed:.1f}s")

        self.status.publish_job_complete(
            job_id,
            success=True,
            message=f"Mission completed successfully in {elapsed:.1f}s"
        )

        # Clear mission
        self.current_mission = None
        self.mission_start_time = None
        self.status.set_current_job(None)

        # Return to IDLE
        time.sleep(1.0)
        self.state.reset_to_idle()
        self.status.update_status("idle")

        logger.info("Ready for next mission")
