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
# CONFIGURATION
# ============================================================================

LEFT_MOTOR_PORT = OUTPUT_A
RIGHT_MOTOR_PORT = OUTPUT_B
PAINT_ARM_PORT = OUTPUT_C
STENCIL_PORT = OUTPUT_D

WHEEL_CIRCUMFERENCE = 17.5  # cm
WHEELBASE = 20.0  # cm
WHEEL_CALIBRATION_FACTOR = 1.0
TURN_CALIBRATION_FACTOR = 1.05

DRIVE_SPEED = 50
PRECISION_SPEED = 25
TURN_SPEED = 40
PAINT_SPEED = 30
STENCIL_SPEED = 20

PAINT_ARM_DISPENSE_DEGREES = 360
STENCIL_LOWER_DEGREES = 90
STENCIL_RAISE_DEGREES = -90

ENCODER_COUNTS_PER_ROTATION = 360
CM_PER_ENCODER_COUNT = WHEEL_CIRCUMFERENCE / ENCODER_COUNTS_PER_ROTATION
CALIBRATED_CM_PER_COUNT = CM_PER_ENCODER_COUNT * WHEEL_CALIBRATION_FACTOR

WHEEL_CIRCUMFERENCE_FOR_TURN = WHEELBASE * math.pi
ENCODER_COUNTS_PER_DEGREE = (WHEEL_CIRCUMFERENCE_FOR_TURN / 360.0) / CM_PER_ENCODER_COUNT * TURN_CALIBRATION_FACTOR

# ============================================================================
# EV3 MOTOR CONTROLLER CLASS
# ============================================================================

class EV3MotorController:
    """Controls EV3 motors based on commands from Raspberry Pi"""

    def __init__(self):
        self.ready = False

        if not EV3_AVAILABLE:
            print("ERROR: ev3dev2 library not available", file=sys.stderr)
            sys.exit(1)

        try:
            self.left_motor = LargeMotor(LEFT_MOTOR_PORT)
            self.right_motor = LargeMotor(RIGHT_MOTOR_PORT)
            self.paint_arm = MediumMotor(PAINT_ARM_PORT)
            self.stencil_motor = MediumMotor(STENCIL_PORT)

            self.left_motor.reset()
            self.right_motor.reset()
            self.paint_arm.reset()
            self.stencil_motor.reset()

            self.stop_all()
            self.ready = True
            print("READY", flush=True)

        except Exception as e:
            print("ERROR Motor initialization failed: {}".format(e), flush=True)
            sys.exit(1)

    def get_encoder_positions(self):
        return (self.left_motor.position, self.right_motor.position)

    def reset_encoders(self):
        self.left_motor.reset()
        self.right_motor.reset()
        return (0, 0)

    def stop_all(self):
        self.left_motor.stop(stop_action='brake')
        self.right_motor.stop(stop_action='brake')
        self.paint_arm.stop(stop_action='brake')
        self.stencil_motor.stop(stop_action='brake')

    def move_forward(self, distance_cm, speed=DRIVE_SPEED):
        try:
            counts = int(distance_cm / CALIBRATED_CM_PER_COUNT)
            start_left = self.left_motor.position
            start_right = self.right_motor.position

            self.left_motor.on_for_degrees(SpeedPercent(speed), counts, brake=True, block=False)
            self.right_motor.on_for_degrees(SpeedPercent(speed), counts, brake=True, block=True)

            self.left_motor.wait_until_not_moving()
            self.right_motor.wait_until_not_moving()

            return self.get_encoder_positions()

        except Exception as e:
            print("ERROR move_forward failed: {}".format(e), flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def move_backward(self, distance_cm, speed=DRIVE_SPEED):
        try:
            counts = -int(distance_cm / CALIBRATED_CM_PER_COUNT)

            self.left_motor.on_for_degrees(SpeedPercent(speed), counts, brake=True, block=False)
            self.right_motor.on_for_degrees(SpeedPercent(speed), counts, brake=True, block=True)

            self.left_motor.wait_until_not_moving()
            self.right_motor.wait_until_not_moving()

            return self.get_encoder_positions()

        except Exception as e:
            print("ERROR move_backward failed: {}".format(e), flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def rotate(self, degrees, speed=TURN_SPEED):
        try:
            counts = int(abs(degrees) * ENCODER_COUNTS_PER_DEGREE)

            if degrees > 0:
                self.left_motor.on_for_degrees(SpeedPercent(speed), counts, brake=True, block=False)
                self.right_motor.on_for_degrees(SpeedPercent(speed), -counts, brake=True, block=True)
            else:
                self.left_motor.on_for_degrees(SpeedPercent(speed), -counts, brake=True, block=False)
                self.right_motor.on_for_degrees(SpeedPercent(speed), counts, brake=True, block=True)

            self.left_motor.wait_until_not_moving()
            self.right_motor.wait_until_not_moving()

            return self.get_encoder_positions()

        except Exception as e:
            print("ERROR rotate failed: {}".format(e), flush=True, file=sys.stderr)
            self.stop_all()
            raise

    def lower_stencil(self):
        try:
            self.stencil_motor.on_for_degrees(SpeedPercent(STENCIL_SPEED), STENCIL_LOWER_DEGREES, brake=True, block=True)
            return True
        except Exception as e:
            print("ERROR lower_stencil failed: {}".format(e), flush=True, file=sys.stderr)
            raise

    def raise_stencil(self):
        try:
            self.stencil_motor.on_for_degrees(SpeedPercent(STENCIL_SPEED), STENCIL_RAISE_DEGREES, brake=True, block=True)
            return True
        except Exception as e:
            print("ERROR raise_stencil failed: {}".format(e), flush=True, file=sys.stderr)
            raise

    def dispense_paint(self, degrees=PAINT_ARM_DISPENSE_DEGREES):
        try:
            self.paint_arm.on_for_degrees(SpeedPercent(PAINT_SPEED), degrees, brake=True, block=True)
            return True
        except Exception as e:
            print("ERROR dispense_paint failed: {}".format(e), flush=True, file=sys.stderr)
            raise

    def process_command(self, command_line):
        try:
            parts = command_line.strip().split()
            if not parts:
                return None

            command = parts[0].upper()

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

            elif command == "LOWER_STENCIL":
                self.lower_stencil()
                return "DONE"

            elif command == "RAISE_STENCIL":
                self.raise_stencil()
                return "DONE"

            elif command == "DISPENSE_PAINT":
                degrees = float(parts[1]) if len(parts) > 1 else PAINT_ARM_DISPENSE_DEGREES
                self.dispense_paint(degrees)
                return "DONE"

            elif command == "GET_ENCODERS":
                left, right = self.get_encoder_positions()
                return "OK left={} right={}".format(left, right)

            elif command == "RESET_ENCODERS":
                left, right = self.reset_encoders()
                return "OK left={} right={}".format(left, right)

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
    try:
        controller = EV3MotorController()

        while True:
            try:
                command_line = sys.stdin.readline()

                if not command_line:
                    break

                command_line = command_line.strip()
                if not command_line:
                    continue

                response = controller.process_command(command_line)

                if response:
                    print(response, flush=True)

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
        if 'controller' in locals() and controller:
            controller.stop_all()
        print("OK", flush=True)

if __name__ == "__main__":
    main()
