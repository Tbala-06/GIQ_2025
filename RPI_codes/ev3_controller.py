#!/usr/bin/env python3
"""
EV3 Motor Controller Script
============================

Runs on EV3 brick - receives commands via stdin and controls motors.
Communicates with Raspberry Pi via SSH pipe.

This script should be copied to /home/robot/ev3_controller.py on the EV3.

Uses ev3dev (original) library format, not ev3dev2.

Command Protocol:
-----------------
MOVE_FORWARD <distance_cm> [speed]
MOVE_BACKWARD <distance_cm> [speed]
ROTATE <degrees> [speed]
DISPENSE_PAINT [degrees]
GET_ENCODERS
RESET_ENCODERS
STOP
EXIT

Response Format:
----------------
DONE left=<encoder> right=<encoder>  - Command completed successfully
OK left=<encoder> right=<encoder>     - Command acknowledged
ERROR <message>                        - Error occurred
READY                                  - Controller ready for commands

Motor Configuration:
--------------------
Port A: Left drive motor (Large Motor)
Port B: Right drive motor (Large Motor)
Port C: Paint arm/dispenser (Medium Motor)

Author: GIQ 2025 Team
"""

import sys
import time
import math

try:
    import ev3dev.ev3 as ev3
    EV3_AVAILABLE = True
except ImportError:
    print("ERROR: ev3dev library not available", file=sys.stderr)
    print("Install with: sudo apt-get install python3-ev3dev", file=sys.stderr)
    sys.exit(1)

# ============================================================================
# CONFIGURATION (match ev3_config.py on RPi)
# ============================================================================

# Motor ports
LEFT_MOTOR_PORT = ev3.OUTPUT_A
RIGHT_MOTOR_PORT = ev3.OUTPUT_B
PAINT_ARM_PORT = ev3.OUTPUT_C

# Physical parameters
WHEEL_CIRCUMFERENCE = 17.5  # cm
WHEELBASE = 20.0  # cm
WHEEL_CALIBRATION_FACTOR = 1.0
TURN_CALIBRATION_FACTOR = 1.05

# Motor speeds (percentage)
DRIVE_SPEED = 50
PRECISION_SPEED = 25
TURN_SPEED = 40
PAINT_SPEED = 30

# Motor operation parameters
PAINT_ARM_DISPENSE_DEGREES = 360

# Encoder calculations
ENCODER_COUNTS_PER_ROTATION = 360
CM_PER_ENCODER_COUNT = WHEEL_CIRCUMFERENCE / ENCODER_COUNTS_PER_ROTATION
CALIBRATED_CM_PER_COUNT = CM_PER_ENCODER_COUNT * WHEEL_CALIBRATION_FACTOR

# Turning calculations
WHEEL_CIRCUMFERENCE_FOR_TURN = WHEELBASE * math.pi
ENCODER_COUNTS_PER_DEGREE = (WHEEL_CIRCUMFERENCE_FOR_TURN / 360.0) / CM_PER_ENCODER_COUNT * TURN_CALIBRATION_FACTOR

# ============================================================================
# EV3 MOTOR CONTROLLER CLASS
# ============================================================================

class EV3MotorController:
    """Controls EV3 motors based on commands from Raspberry Pi"""

    def __init__(self):
        """Initialize motors"""
        self.ready = False

        try:
            # Initialize drive motors (Large Motors)
            self.left_motor = ev3.LargeMotor(LEFT_MOTOR_PORT)
            self.right_motor = ev3.LargeMotor(RIGHT_MOTOR_PORT)

            # Initialize paint arm (Medium Motor)
            self.paint_arm = ev3.MediumMotor(PAINT_ARM_PORT)

            # Check if motors are connected
            if not self.left_motor.connected:
                raise Exception("Left motor (Port A) not connected")
            if not self.right_motor.connected:
                raise Exception("Right motor (Port B) not connected")
            if not self.paint_arm.connected:
                raise Exception("Paint arm motor (Port C) not connected")

            # Reset encoder positions
            self.left_motor.position = 0
            self.right_motor.position = 0
            self.paint_arm.position = 0

            # Stop all motors
            self.stop_all()

            self.ready = True
            print("READY", flush=True)

        except Exception as e:
            print("ERROR Motor initialization failed: {}".format(e), flush=True)
            sys.exit(1)

    def get_encoder_positions(self):
        """
        Get current encoder positions.

        Returns:
            Tuple of (left_position, right_position)
        """
        return (self.left_motor.position, self.right_motor.position)

    def reset_encoders(self):
        """Reset drive motor encoders to zero"""
        self.left_motor.position = 0
        self.right_motor.position = 0
        return (0, 0)

    def stop_all(self):
        """Emergency stop - brake all motors"""
        self.left_motor.stop(stop_action='brake')
        self.right_motor.stop(stop_action='brake')
        self.paint_arm.stop(stop_action='brake')

    def move_forward(self, distance_cm: float, speed: int = DRIVE_SPEED):
        """
        Move robot forward by specified distance using encoder feedback.

        Args:
            distance_cm: Distance to travel (cm)
            speed: Motor speed 0-100

        Returns:
            Tuple of (left_encoder, right_encoder)
        """
        try:
            # Calculate encoder counts needed
            counts = int(distance_cm / CALIBRATED_CM_PER_COUNT)

            # Set motor speeds (convert percentage to deg/sec)
            # EV3 Large Motor max speed ~1050 deg/sec
            speed_deg_sec = int(1050 * speed / 100)

            # Move both motors forward
            self.left_motor.run_to_rel_pos(
                position_sp=counts,
                speed_sp=speed_deg_sec,
                stop_action='brake'
            )
            self.right_motor.run_to_rel_pos(
                position_sp=counts,
                speed_sp=speed_deg_sec,
                stop_action='brake'
            )

            # Wait for both motors to complete
            self.left_motor.wait_while('running')
            self.right_motor.wait_while('running')

            # Return final encoder positions
            return self.get_encoder_positions()

        except Exception as e:
            print("ERROR move_forward failed: {}".format(e), flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def move_backward(self, distance_cm: float, speed: int = DRIVE_SPEED):
        """
        Move robot backward by specified distance.

        Args:
            distance_cm: Distance to travel (cm)
            speed: Motor speed 0-100

        Returns:
            Tuple of (left_encoder, right_encoder)
        """
        try:
            # Calculate encoder counts (negative for backward)
            counts = -int(distance_cm / CALIBRATED_CM_PER_COUNT)

            # Set motor speeds
            speed_deg_sec = int(1050 * speed / 100)

            # Move both motors backward
            self.left_motor.run_to_rel_pos(
                position_sp=counts,
                speed_sp=speed_deg_sec,
                stop_action='brake'
            )
            self.right_motor.run_to_rel_pos(
                position_sp=counts,
                speed_sp=speed_deg_sec,
                stop_action='brake'
            )

            # Wait for completion
            self.left_motor.wait_while('running')
            self.right_motor.wait_while('running')

            return self.get_encoder_positions()

        except Exception as e:
            print("ERROR move_backward failed: {}".format(e), flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def rotate(self, degrees: float, speed: int = TURN_SPEED):
        """
        Rotate robot in place.
        Positive degrees = clockwise (right turn)
        Negative degrees = counter-clockwise (left turn)

        Args:
            degrees: Rotation angle (degrees)
            speed: Motor speed 0-100

        Returns:
            Tuple of (left_encoder, right_encoder)
        """
        try:
            # Calculate encoder counts for rotation
            counts = int(abs(degrees) * ENCODER_COUNTS_PER_DEGREE)

            # Set motor speeds
            speed_deg_sec = int(1050 * speed / 100)

            if degrees > 0:
                # Clockwise: left forward, right backward
                self.left_motor.run_to_rel_pos(
                    position_sp=counts,
                    speed_sp=speed_deg_sec,
                    stop_action='brake'
                )
                self.right_motor.run_to_rel_pos(
                    position_sp=-counts,
                    speed_sp=speed_deg_sec,
                    stop_action='brake'
                )
            else:
                # Counter-clockwise: left backward, right forward
                self.left_motor.run_to_rel_pos(
                    position_sp=-counts,
                    speed_sp=speed_deg_sec,
                    stop_action='brake'
                )
                self.right_motor.run_to_rel_pos(
                    position_sp=counts,
                    speed_sp=speed_deg_sec,
                    stop_action='brake'
                )

            # Wait for completion
            self.left_motor.wait_while('running')
            self.right_motor.wait_while('running')

            return self.get_encoder_positions()

        except Exception as e:
            print("ERROR rotate failed: {}".format(e), flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def dispense_paint(self, degrees: float = PAINT_ARM_DISPENSE_DEGREES):
        """
        Dispense paint/sand by rotating paint arm motor.

        Args:
            degrees: Rotation amount (default from config)

        Returns:
            True if successful
        """
        try:
            # Set motor speed
            speed_deg_sec = int(1050 * PAINT_SPEED / 100)

            # Rotate paint arm
            self.paint_arm.run_to_rel_pos(
                position_sp=int(degrees),
                speed_sp=speed_deg_sec,
                stop_action='brake'
            )

            # Wait for completion
            self.paint_arm.wait_while('running')

            return True

        except Exception as e:
            print("ERROR dispense_paint failed: {}".format(e), flush=True, file=sys.stderr)
            raise

    def process_command(self, command_line: str):
        """
        Parse and execute command from Raspberry Pi.

        Args:
            command_line: Command string from stdin

        Returns:
            Response string to send back
        """
        try:
            parts = command_line.strip().split()
            if not parts:
                return None

            command = parts[0].upper()

            # ===== MOVEMENT COMMANDS =====

            if command == "MOVE_FORWARD":
                distance = float(parts[1])
                speed = int(parts[2]) if len(parts) > 2 else DRIVE_SPEED
                left, right = self.move_forward(distance, speed)
                return "DONE left={} right={}".format(left, right)

            elif command == "MOVE_BACKWARD":
                distance = float(parts[1])
                speed = int(parts[2]) if len(parts) > 2 else DRIVE_SPEED
                left, right = self.move_backward(distance, speed)
                return "DONE left={} right={}".format(left, right)

            elif command == "ROTATE":
                degrees = float(parts[1])
                speed = int(parts[2]) if len(parts) > 2 else TURN_SPEED
                left, right = self.rotate(degrees, speed)
                return "DONE left={} right={}".format(left, right)

            elif command == "STOP":
                self.stop_all()
                return "OK"

            # ===== PAINT COMMANDS =====

            elif command == "DISPENSE_PAINT":
                degrees = float(parts[1]) if len(parts) > 1 else PAINT_ARM_DISPENSE_DEGREES
                self.dispense_paint(degrees)
                return "DONE"

            # ===== ENCODER COMMANDS =====

            elif command == "GET_ENCODERS":
                left, right = self.get_encoder_positions()
                return "OK left={} right={}".format(left, right)

            elif command == "RESET_ENCODERS":
                left, right = self.reset_encoders()
                return "OK left={} right={}".format(left, right)

            # ===== LEGACY COMMANDS (for compatibility) =====

            elif command == "LOWER_STENCIL":
                # No stencil motor - just acknowledge
                return "DONE"

            elif command == "RAISE_STENCIL":
                # No stencil motor - just acknowledge
                return "DONE"

            # ===== CONTROL COMMANDS =====

            elif command == "EXIT":
                self.stop_all()
                return "OK"

            else:
                return "ERROR Unknown command: {}".format(command)

        except IndexError:
            return "ERROR Invalid command format: {}".format(command_line)
        except ValueError as e:
            return "ERROR Invalid parameter: {}".format(e)
        except Exception as e:
            return "ERROR Command execution failed: {}".format(e)


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    """Main command processing loop"""
    try:
        # Initialize controller
        controller = EV3MotorController()

        # Command processing loop
        while True:
            try:
                # Read command from stdin (from Raspberry Pi via SSH)
                command_line = sys.stdin.readline()

                if not command_line:
                    # EOF reached (SSH connection closed)
                    break

                command_line = command_line.strip()
                if not command_line:
                    continue

                # Process command
                response = controller.process_command(command_line)

                if response:
                    # Send response back to Raspberry Pi
                    print(response, flush=True)

                # Exit if EXIT command received
                if command_line.upper().startswith("EXIT"):
                    break

            except KeyboardInterrupt:
                print("ERROR Interrupted by user", flush=True)
                break

            except Exception as e:
                print("ERROR Command processing error: {}".format(e), flush=True, file=sys.stderr)
                continue

    except Exception as e:
        print("ERROR Fatal error: {}".format(e), flush=True, file=sys.stderr)
        sys.exit(1)

    finally:
        # Cleanup
        if controller:
            controller.stop_all()
        print("OK", flush=True)


if __name__ == "__main__":
    main()
