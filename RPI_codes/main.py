#!/usr/bin/env python3
"""
Road Painting Robot Controller - Main Entry Point
Complete Raspberry Pi controller for autonomous road painting robot.
"""

import argparse
import signal
import sys
import time
from utils.logger import setup_logging, get_logger
from config import Config

logger = get_logger(__name__)


class RobotController:
    """Main robot controller coordinating all subsystems"""

    def __init__(self, simulate=False):
        """
        Initialize robot controller.

        Args:
            simulate: If True, run without hardware (for testing)
        """
        self.simulate = simulate
        self.running = False
        self.subsystems_initialized = False

        logger.info(f"Initializing Robot Controller (simulate={simulate})")

        # Initialize subsystems (lazy loading to avoid import errors without hardware)
        self.mti_parser = None
        self.motor_controller = None
        self.stencil_controller = None
        self.paint_dispenser = None
        self.gps_navigator = None
        self.road_finder = None
        self.mqtt_client = None
        self.status_reporter = None
        self.safety_monitor = None
        self.state_manager = None
        self.mission_executor = None

    def startup(self):
        """Initialize and start all subsystems"""
        logger.info("=" * 60)
        logger.info("ROBOT STARTUP SEQUENCE")
        logger.info("=" * 60)

        try:
            # Import and initialize hardware
            logger.info("Initializing hardware subsystems...")
            from hardware.mti_parser import MTiParser
            from hardware.motor_controller import MotorController
            from hardware.stencil_controller import StencilController
            from hardware.paint_dispenser import PaintDispenser

            self.mti_parser = MTiParser(Config.MTI_SERIAL_PORT, Config.MTI_BAUDRATE)
            self.motor_controller = MotorController(simulate=self.simulate)
            self.stencil_controller = StencilController(simulate=self.simulate)
            self.paint_dispenser = PaintDispenser(simulate=self.simulate)

            # Connect MTi sensor
            if not self.simulate:
                logger.info(f"Connecting to MTi sensor on {Config.MTI_SERIAL_PORT}...")
                if not self.mti_parser.connect():
                    raise RuntimeError("Failed to connect to MTi sensor")
                logger.info("MTi sensor connected successfully")

            # Initialize navigation
            logger.info("Initializing navigation subsystems...")
            from navigation.gps_navigator import GPSNavigator
            from navigation.road_finder import RoadFinder

            self.gps_navigator = GPSNavigator(self.mti_parser, self.motor_controller)
            self.road_finder = RoadFinder(Config.GEOJSON_ROADS_FILE)

            # Initialize communication
            logger.info("Initializing communication subsystems...")
            from communication.mqtt_client import MQTTClient
            from communication.status_reporter import StatusReporter

            self.mqtt_client = MQTTClient(client_id=Config.ROBOT_ID)
            self.mqtt_client.on_deploy_command(self._handle_deploy_command)
            self.mqtt_client.connect()

            self.status_reporter = StatusReporter(self.mqtt_client)
            self.status_reporter.start_reporting(Config.STATUS_REPORT_INTERVAL)

            # Initialize control systems
            logger.info("Initializing control subsystems...")
            from control.robot_state import StateManager, RobotState
            from control.mission_executor import MissionExecutor
            from control.safety_monitor import SafetyMonitor

            self.state_manager = StateManager(initial_state=RobotState.IDLE)
            self.safety_monitor = SafetyMonitor(self.mti_parser, simulate=self.simulate)

            self.mission_executor = MissionExecutor(
                state_manager=self.state_manager,
                gps_navigator=self.gps_navigator,
                road_finder=self.road_finder,
                motor=self.motor_controller,
                stencil=self.stencil_controller,
                paint=self.paint_dispenser,
                status_reporter=self.status_reporter
            )

            # Wait for GPS fix (unless simulating)
            if not self.simulate:
                logger.info("Waiting for GPS fix...")
                if not self.gps_navigator.wait_for_gps_fix(Config.MIN_GPS_SATELLITES, timeout=30):
                    logger.warning("GPS fix not acquired, continuing anyway...")
                else:
                    logger.info("GPS fix acquired")

            self.subsystems_initialized = True
            logger.info("=" * 60)
            logger.info("ROBOT STARTUP COMPLETE")
            logger.info(f"Robot ID: {Config.ROBOT_ID}")
            logger.info(f"Robot Name: {Config.ROBOT_NAME}")
            logger.info(f"State: {self.state_manager.get_state()}")
            logger.info("=" * 60)

            self.status_reporter.update_status("ready")

        except Exception as e:
            logger.error(f"Startup failed: {e}", exc_info=True)
            self.shutdown()
            raise

    def shutdown(self):
        """Cleanup and shutdown all subsystems"""
        logger.info("=" * 60)
        logger.info("ROBOT SHUTDOWN SEQUENCE")
        logger.info("=" * 60)

        self.running = False

        # Stop mission if active
        if self.mission_executor and self.mission_executor.has_active_mission():
            logger.info("Aborting active mission...")
            self.mission_executor.abort_mission("System shutdown")

        # Stop status reporting
        if self.status_reporter:
            logger.info("Stopping status reporter...")
            self.status_reporter.stop_reporting()

        # Disconnect MQTT
        if self.mqtt_client:
            logger.info("Disconnecting MQTT...")
            self.mqtt_client.disconnect()

        # Cleanup hardware
        if self.motor_controller:
            logger.info("Stopping motors...")
            self.motor_controller.stop()
            self.motor_controller.cleanup()

        if self.stencil_controller:
            logger.info("Returning stencil to home position...")
            self.stencil_controller.home_position()
            self.stencil_controller.cleanup()

        if self.paint_dispenser:
            logger.info("Stopping paint dispenser...")
            self.paint_dispenser.stop_dispensing()
            self.paint_dispenser.cleanup()

        if self.safety_monitor:
            logger.info("Cleanup safety monitor...")
            self.safety_monitor.cleanup()

        if self.mti_parser:
            logger.info("Disconnecting MTi sensor...")
            self.mti_parser.disconnect()

        logger.info("=" * 60)
        logger.info("ROBOT SHUTDOWN COMPLETE")
        logger.info("=" * 60)

    def run(self):
        """Main control loop"""
        if not self.subsystems_initialized:
            raise RuntimeError("Robot not initialized. Call startup() first.")

        self.running = True
        logger.info("Entering main control loop...")

        last_safety_check = 0
        safety_check_interval = 5.0  # Check safety every 5 seconds

        try:
            while self.running:
                current_time = time.time()

                # Periodic safety checks
                if current_time - last_safety_check >= safety_check_interval:
                    is_safe, reason = self.safety_monitor.is_safe_to_operate()
                    if not is_safe:
                        logger.error(f"Safety check failed: {reason}")
                        if self.mission_executor.has_active_mission():
                            self.mission_executor.abort_mission(f"Safety: {reason}")
                        self.state_manager.emergency_stop()
                    last_safety_check = current_time

                # Execute mission step if active
                if self.mission_executor.has_active_mission():
                    try:
                        self.mission_executor.execute_mission_step()
                    except Exception as e:
                        logger.error(f"Mission step error: {e}", exc_info=True)
                        self.mission_executor.abort_mission(f"Error: {str(e)}")

                # Sleep to avoid busy waiting
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def _handle_deploy_command(self, command_data):
        """
        Handle deploy command from MQTT.

        Args:
            command_data: Dictionary with job_id, latitude, longitude
        """
        logger.info(f"Received deploy command: {command_data}")

        try:
            job_id = command_data.get('job_id')
            latitude = command_data.get('latitude')
            longitude = command_data.get('longitude')

            if not all([job_id, latitude, longitude]):
                logger.error("Invalid deploy command: missing required fields")
                return

            # Check if already on a mission
            if self.mission_executor.has_active_mission():
                logger.warning("Already on mission, ignoring new deploy command")
                return

            # Start mission
            self.mission_executor.start_mission(command_data)

        except Exception as e:
            logger.error(f"Error handling deploy command: {e}", exc_info=True)

    def _signal_handler(self, signum, frame):
        """Handle system signals (SIGINT, SIGTERM)"""
        logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Road Painting Robot Controller')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode (no hardware required)')
    parser.add_argument('--log-level', default=Config.LOG_LEVEL,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level')
    args = parser.parse_args()

    # Setup logging
    setup_logging(Config.LOG_FILE, args.log_level)

    logger.info("=" * 60)
    logger.info("ROAD PAINTING ROBOT CONTROLLER")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Mode: {'SIMULATION' if args.simulate else 'HARDWARE'}")
    logger.info("=" * 60)

    # Create and start robot controller
    robot = RobotController(simulate=args.simulate)

    # Setup signal handlers
    signal.signal(signal.SIGINT, robot._signal_handler)
    signal.signal(signal.SIGTERM, robot._signal_handler)

    try:
        robot.startup()
        robot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
