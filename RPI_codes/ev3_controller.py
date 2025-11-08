#!/usr/bin/env python3
"""
EV3 Motor Controller Script
============================

Runs on EV3 brick - receives commands via stdin and controls motors.
Communicates with Raspberry Pi via SSH pipe.

This script should be copied to /home/robot/ev3_controller.py on the EV3.

Command Protocol:
-----------------
MOVE_FORWARD <distance_cm> [speed]
MOVE_BACKWARD <distance_cm> [speed]
ROTATE <degrees> [speed]
LOWER_STENCIL
RAISE_STENCIL
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

Author: GIQ 2025 Team
"""

import sys
import time
import math

try:
    from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
    from ev3dev2.motor import SpeedPercent
    EV3_AVAILABLE = True
except ImportError:
    print("WARNING: ev3dev2 not available - simulation mode", file=sys.stderr)
    EV3_AVAILABLE = False

# ============================================================================
# CONFIGURATION (match ev3_config.py on RPi)
# ============================================================================

# Motor ports
LEFT_MOTOR_PORT = OUTPUT_A
RIGHT_MOTOR_PORT = OUTPUT_B
PAINT_ARM_PORT = OUTPUT_C
STENCIL_PORT = OUTPUT_D

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
STENCIL_SPEED = 20

# Motor operation parameters
PAINT_ARM_DISPENSE_DEGREES = 360
STENCIL_LOWER_DEGREES = 90
STENCIL_RAISE_DEGREES = -90

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

        if not EV3_AVAILABLE:
            print("ERROR: ev3dev2 library not available", file=sys.stderr)
            sys.exit(1)

        try:
            # Initialize drive motors
            self.left_motor = LargeMotor(LEFT_MOTOR_PORT)
            self.right_motor = LargeMotor(RIGHT_MOTOR_PORT)

            # Initialize accessory motors
            self.paint_arm = MediumMotor(PAINT_ARM_PORT)
            self.stencil_motor = MediumMotor(STENCIL_PORT)

            # Reset encoder positions
            self.left_motor.reset()
            self.right_motor.reset()
            self.paint_arm.reset()
            self.stencil_motor.reset()

            # Stop all motors
            self.stop_all()

            self.ready = True
            print("READY", flush=True)

        except Exception as e:
            print(f"ERROR Motor initialization failed: {e}", flush=True)
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
        self.left_motor.reset()
        self.right_motor.reset()
        return (0, 0)

    def stop_all(self):
        """Emergency stop - brake all motors"""
        self.left_motor.stop(stop_action='brake')
        self.right_motor.stop(stop_action='brake')
        self.paint_arm.stop(stop_action='brake')
        self.stencil_motor.stop(stop_action='brake')

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

            # Reset encoders to zero for accurate measurement
            start_left = self.left_motor.position
            start_right = self.right_motor.position

            # Move both motors forward
            self.left_motor.on_for_degrees(
                SpeedPercent(speed),
                counts,
                brake=True,
                block=False
            )
            self.right_motor.on_for_degrees(
                SpeedPercent(speed),
                counts,
                brake=True,
                block=True
            )

            # Wait for both motors to complete
            self.left_motor.wait_until_not_moving()
            self.right_motor.wait_until_not_moving()

            # Return final encoder positions
            return self.get_encoder_positions()

        except Exception as e:
            print(f"ERROR move_forward failed: {e}", flush=True, file=sys.stderr)
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

            # Move both motors backward
            self.left_motor.on_for_degrees(
                SpeedPercent(speed),
                counts,
                brake=True,
                block=False
            )
            self.right_motor.on_for_degrees(
                SpeedPercent(speed),
                counts,
                brake=True,
                block=True
            )

            # Wait for completion
            self.left_motor.wait_until_not_moving()
            self.right_motor.wait_until_not_moving()

            return self.get_encoder_positions()

        except Exception as e:
            print(f"ERROR move_backward failed: {e}", flush=True, file=sys.stderr)
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
            # One motor forward, one backward for in-place rotation
            counts = int(abs(degrees) * ENCODER_COUNTS_PER_DEGREE)

            if degrees > 0:
                # Clockwise: left forward, right backward
                self.left_motor.on_for_degrees(
                    SpeedPercent(speed),
                    counts,
                    brake=True,
                    block=False
                )
                self.right_motor.on_for_degrees(
                    SpeedPercent(speed),
                    -counts,
                    brake=True,
                    block=True
                )
            else:
                # Counter-clockwise: left backward, right forward
                self.left_motor.on_for_degrees(
                    SpeedPercent(speed),
                    -counts,
                    brake=True,
                    block=False
                )
                self.right_motor.on_for_degrees(
                    SpeedPercent(speed),
                    counts,
                    brake=True,
                    block=True
                )

            # Wait for completion
            self.left_motor.wait_until_not_moving()
            self.right_motor.wait_until_not_moving()

            return self.get_encoder_positions()

        except Exception as e:
            print(f"ERROR rotate failed: {e}", flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def lower_stencil(self):
        """Lower the stencil mechanism"""
        try:
            self.stencil_motor.on_for_degrees(
                SpeedPercent(STENCIL_SPEED),
                STENCIL_LOWER_DEGREES,
                brake=True,
                block=True
            )
            return True
        except Exception as e:
            print(f"ERROR lower_stencil failed: {e}", flush=True, file=sys.stderr)
            raise

    def raise_stencil(self):
        """Raise the stencil mechanism"""
        try:
            self.stencil_motor.on_for_degrees(
                SpeedPercent(STENCIL_SPEED),
                STENCIL_RAISE_DEGREES,
                brake=True,
                block=True
            )
            return True
        except Exception as e:
            print(f"ERROR raise_stencil failed: {e}", flush=True, file=sys.stderr)
            raise

    def dispense_paint(self, degrees: float = PAINT_ARM_DISPENSE_DEGREES):
        """Dispense paint/sand"""
        try:
            self.paint_arm.on_for_degrees(
                SpeedPercent(PAINT_SPEED),
                degrees,
                brake=True,
                block=True
            )
            return True
        except Exception as e:
            print(f"ERROR dispense_paint failed: {e}", flush=True, file=sys.stderr)
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
                return f"DONE left={left} right={right}"

            elif command == "MOVE_BACKWARD":
                distance = float(parts[1])
                speed = int(parts[2]) if len(parts) > 2 else DRIVE_SPEED
                left, right = self.move_backward(distance, speed)
                return f"DONE left={left} right={right}"

            elif command == "ROTATE":
                degrees = float(parts[1])
                speed = int(parts[2]) if len(parts) > 2 else TURN_SPEED
                left, right = self.rotate(degrees, speed)
                return f"DONE left={left} right={right}"

            elif command == "STOP":
                self.stop_all()
                return "OK"

            # ===== STENCIL COMMANDS =====

            elif command == "LOWER_STENCIL":
                self.lower_stencil()
                return "DONE"

            elif command == "RAISE_STENCIL":
                self.raise_stencil()
                return "DONE"

            # ===== PAINT COMMANDS =====

            elif command == "DISPENSE_PAINT":
                degrees = float(parts[1]) if len(parts) > 1 else PAINT_ARM_DISPENSE_DEGREES
                self.dispense_paint(degrees)
                return "DONE"

            # ===== ENCODER COMMANDS =====

            elif command == "GET_ENCODERS":
                left, right = self.get_encoder_positions()
                return f"OK left={left} right={right}"

            elif command == "RESET_ENCODERS":
                left, right = self.reset_encoders()
                return f"OK left={left} right={right}"

            # ===== CONTROL COMMANDS =====

            elif command == "EXIT":
                self.stop_all()
                return "OK"

            else:
                return f"ERROR Unknown command: {command}"

        except IndexError:
            return f"ERROR Invalid command format: {command_line}"
        except ValueError as e:
            return f"ERROR Invalid parameter: {e}"
        except Exception as e:
            return f"ERROR Command execution failed: {e}"


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
                print(f"ERROR Command processing error: {e}", flush=True, file=sys.stderr)
                continue

    except Exception as e:
        print(f"ERROR Fatal error: {e}", flush=True, file=sys.stderr)
        sys.exit(1)

    finally:
        # Cleanup
        if controller:
            controller.stop_all()
        print("OK", flush=True)


if __name__ == "__main__":
    main()
