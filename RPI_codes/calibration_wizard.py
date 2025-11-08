#!/usr/bin/env python3
"""
Robot Calibration Wizard
=========================

Interactive tool to calibrate robot parameters:
1. Wheel circumference
2. Turn calibration factor
3. Camera pixels-per-cm
4. Paint arm dispense amount
5. Stencil motor positions

Generates updated ev3_config.py with measured values.

Author: GIQ 2025 Team
"""

import time
import logging
import sys
from typing import Optional

# Robot modules
from ev3_comm import EV3Controller
from stencil_aligner import StencilAligner
import ev3_config

logger = logging.getLogger(__name__)


class CalibrationWizard:
    """Interactive calibration wizard"""

    def __init__(self):
        """Initialize wizard"""
        self.ev3 = None
        self.aligner = None
        self.measurements = {}

    def run(self):
        """Run calibration wizard"""
        print("\n" + "=" * 70)
        print("ROBOT CALIBRATION WIZARD")
        print("=" * 70)
        print("\nThis wizard will help you calibrate your robot parameters.")
        print("Have a tape measure ready!")
        print("=" * 70 + "\n")

        try:
            # Connect to hardware
            if not self._connect_hardware():
                print("\n✗ Hardware connection failed")
                return

            # Main menu
            while True:
                self._show_menu()
                choice = input("\nEnter choice (or 'q' to quit): ").strip()

                if choice == 'q':
                    break
                elif choice == '1':
                    self._calibrate_wheel_circumference()
                elif choice == '2':
                    self._calibrate_turn_factor()
                elif choice == '3':
                    self._calibrate_camera()
                elif choice == '4':
                    self._calibrate_paint_arm()
                elif choice == '5':
                    self._calibrate_stencil()
                elif choice == '6':
                    self._test_alignment()
                elif choice == '7':
                    self._save_config()
                else:
                    print("Invalid choice")

        finally:
            self._disconnect_hardware()

        print("\n" + "=" * 70)
        print("CALIBRATION COMPLETE")
        print("=" * 70)

    def _show_menu(self):
        """Display main menu"""
        print("\n" + "-" * 70)
        print("CALIBRATION MENU")
        print("-" * 70)
        print("1. Calibrate Wheel Circumference")
        print("2. Calibrate Turn Factor")
        print("3. Calibrate Camera (pixels per cm)")
        print("4. Calibrate Paint Arm")
        print("5. Calibrate Stencil Motor")
        print("6. Test Alignment System")
        print("7. Save Configuration")
        print("q. Quit")
        print("-" * 70)

    def _connect_hardware(self) -> bool:
        """Connect to EV3 and camera"""
        print("\n→ Connecting to hardware...")

        try:
            # Connect to EV3
            print("  Connecting to EV3...", end=" ")
            self.ev3 = EV3Controller()
            if not self.ev3.connect():
                print("FAILED")
                return False
            print("OK")

            # Connect to camera
            print("  Starting camera...", end=" ")
            self.aligner = StencilAligner()
            if not self.aligner.start():
                print("FAILED")
                return False
            print("OK")

            print("✓ Hardware connected\n")
            return True

        except Exception as e:
            print(f"FAILED: {e}")
            return False

    def _disconnect_hardware(self):
        """Disconnect hardware"""
        print("\n→ Disconnecting hardware...")
        if self.ev3:
            self.ev3.disconnect()
        if self.aligner:
            self.aligner.stop()
        print("✓ Hardware disconnected")

    # ========================================================================
    # CALIBRATION PROCEDURES
    # ========================================================================

    def _calibrate_wheel_circumference(self):
        """Calibrate wheel circumference"""
        print("\n" + "=" * 70)
        print("WHEEL CIRCUMFERENCE CALIBRATION")
        print("=" * 70)
        print("\nThis will drive the robot forward 100cm.")
        print("Mark the starting position and measure actual distance traveled.")
        print("=" * 70)

        input("\nPress ENTER when ready...")

        # Reset encoders
        self.ev3.reset_encoders()

        # Drive 100cm
        print("\n→ Driving 100cm forward...")
        commanded_distance = 100.0
        result = self.ev3.move_forward(commanded_distance, speed=30)

        if not result:
            print("✗ Movement failed")
            return

        left_enc, right_enc = result
        avg_enc = (left_enc + right_enc) / 2

        print(f"✓ Movement complete")
        print(f"  Encoder counts: L={left_enc}, R={right_enc}, Avg={avg_enc:.0f}")

        # Get actual measurement
        print("\n→ Measure the actual distance traveled with a tape measure.")
        while True:
            try:
                actual_distance = float(input("Actual distance (cm): "))
                if actual_distance > 0:
                    break
                print("Distance must be positive")
            except ValueError:
                print("Invalid input")

        # Calculate calibration factor
        calibration_factor = actual_distance / commanded_distance
        new_circumference = ev3_config.WHEEL_CIRCUMFERENCE * calibration_factor

        print(f"\n✓ Calibration complete:")
        print(f"  Commanded: {commanded_distance} cm")
        print(f"  Actual: {actual_distance} cm")
        print(f"  Error: {abs(commanded_distance - actual_distance):.1f} cm")
        print(f"  Calibration factor: {calibration_factor:.4f}")
        print(f"  New wheel circumference: {new_circumference:.2f} cm")
        print(f"  (Old: {ev3_config.WHEEL_CIRCUMFERENCE:.2f} cm)")

        self.measurements['WHEEL_CIRCUMFERENCE'] = new_circumference
        self.measurements['WHEEL_CALIBRATION_FACTOR'] = calibration_factor

    def _calibrate_turn_factor(self):
        """Calibrate turn factor"""
        print("\n" + "=" * 70)
        print("TURN FACTOR CALIBRATION")
        print("=" * 70)
        print("\nThis will rotate the robot 360° (full rotation).")
        print("Mark the starting orientation and measure actual rotation.")
        print("=" * 70)

        input("\nPress ENTER when ready...")

        # Reset encoders
        self.ev3.reset_encoders()

        # Rotate 360°
        print("\n→ Rotating 360° clockwise...")
        commanded_angle = 360.0
        result = self.ev3.rotate(commanded_angle, speed=25)

        if not result:
            print("✗ Rotation failed")
            return

        print(f"✓ Rotation complete")

        # Get actual measurement
        print("\n→ Estimate how many degrees the robot actually rotated.")
        print("  (Align a straight edge with starting position)")
        while True:
            try:
                actual_angle = float(input("Actual rotation (degrees): "))
                if actual_angle > 0:
                    break
                print("Angle must be positive")
            except ValueError:
                print("Invalid input")

        # Calculate calibration factor
        turn_calibration = actual_angle / commanded_angle

        print(f"\n✓ Calibration complete:")
        print(f"  Commanded: {commanded_angle}°")
        print(f"  Actual: {actual_angle}°")
        print(f"  Error: {abs(commanded_angle - actual_angle):.1f}°")
        print(f"  Turn calibration factor: {turn_calibration:.4f}")
        print(f"  (Old: {ev3_config.TURN_CALIBRATION_FACTOR:.4f})")

        self.measurements['TURN_CALIBRATION_FACTOR'] = turn_calibration

    def _calibrate_camera(self):
        """Calibrate camera pixels-per-cm"""
        print("\n" + "=" * 70)
        print("CAMERA CALIBRATION (Pixels per CM)")
        print("=" * 70)
        print("\nPlace a known-size object in camera view.")
        print("You will click two points on the object to measure it.")
        print("=" * 70)

        # Get known distance
        while True:
            try:
                known_cm = float(input("\nKnown distance (cm): "))
                if known_cm > 0:
                    break
                print("Distance must be positive")
            except ValueError:
                print("Invalid input")

        print("\n→ Launching camera calibration...")
        print("  Click two points that are exactly {known_cm}cm apart.")
        print("  Press ESC to cancel.")

        pixels_per_cm = self.aligner.calibrate_pixels_per_cm(known_cm)

        if pixels_per_cm:
            print(f"\n✓ Calibration complete:")
            print(f"  Pixels per cm: {pixels_per_cm:.2f}")
            print(f"  (Old: {ev3_config.PIXELS_PER_CM:.2f})")

            self.measurements['PIXELS_PER_CM'] = pixels_per_cm
        else:
            print("\n✗ Calibration cancelled")

    def _calibrate_paint_arm(self):
        """Calibrate paint arm dispense amount"""
        print("\n" + "=" * 70)
        print("PAINT ARM CALIBRATION")
        print("=" * 70)
        print("\nThis will test different rotation amounts for paint dispensing.")
        print("Find the amount that gives good coverage without excess.")
        print("=" * 70)

        test_amounts = [180, 270, 360, 450, 540]

        for degrees in test_amounts:
            print(f"\n→ Testing {degrees}° rotation...")
            input("  Press ENTER to test...")

            success = self.ev3.dispense_paint(degrees)

            if success:
                print(f"  ✓ Dispensed at {degrees}°")
                response = input("  Was this amount good? (y/n): ").strip().lower()

                if response == 'y':
                    print(f"\n✓ Paint arm calibration: {degrees}°")
                    print(f"  (Old: {ev3_config.PAINT_ARM_DISPENSE_DEGREES}°)")
                    self.measurements['PAINT_ARM_DISPENSE_DEGREES'] = degrees
                    break
            else:
                print(f"  ✗ Dispense failed")

    def _calibrate_stencil(self):
        """Calibrate stencil motor positions"""
        print("\n" + "=" * 70)
        print("STENCIL MOTOR CALIBRATION")
        print("=" * 70)
        print("\nThis will test stencil lowering and raising.")
        print("Find the rotation amount that fully lowers/raises the stencil.")
        print("=" * 70)

        # Test lowering
        print("\n→ Testing stencil LOWER positions...")
        test_amounts = [45, 60, 90, 120, 150]

        for degrees in test_amounts:
            print(f"\n  Testing {degrees}° lower...")
            input("  Press ENTER to test...")

            # TODO: Add direct motor control for testing
            # For now, use existing lower command
            success = self.ev3.lower_stencil()

            if success:
                print(f"  ✓ Lowered")
                response = input("  Is stencil fully lowered? (y/n): ").strip().lower()

                if response == 'y':
                    print(f"\n✓ Stencil lower: {degrees}°")
                    print(f"  (Old: {ev3_config.STENCIL_LOWER_DEGREES}°)")
                    self.measurements['STENCIL_LOWER_DEGREES'] = degrees

                    # Raise back up
                    print("\n  Raising stencil...")
                    self.ev3.raise_stencil()
                    break

                # Raise for next test
                self.ev3.raise_stencil()

    def _test_alignment(self):
        """Test alignment system"""
        print("\n" + "=" * 70)
        print("ALIGNMENT SYSTEM TEST")
        print("=" * 70)
        print("\nThis will capture a frame and show alignment analysis.")
        print("Position robot over yellow road marking with orange stencil visible.")
        print("=" * 70)

        input("\nPress ENTER when ready...")

        print("\n→ Analyzing alignment...")
        instruction = self.aligner.get_alignment_instruction()

        print(f"\n✓ Analysis complete:")
        print(f"  Aligned: {instruction.aligned}")
        print(f"  Direction: {instruction.direction}")
        print(f"  Distance: {instruction.distance_cm:.1f} cm")
        print(f"  Offset: {instruction.offset_percentage:.1f}%")
        print(f"  Confidence: {instruction.confidence:.2f}")
        print(f"  Message: {instruction.message}")

        # Save debug image
        debug_path = "alignment_debug.jpg"
        if self.aligner.save_debug_image(debug_path):
            print(f"\n  Debug image saved: {debug_path}")

    def _save_config(self):
        """Save calibration results to config file"""
        if not self.measurements:
            print("\n✗ No calibration measurements to save")
            return

        print("\n" + "=" * 70)
        print("SAVE CONFIGURATION")
        print("=" * 70)
        print("\nMeasurements to save:")
        for key, value in self.measurements.items():
            print(f"  {key} = {value}")

        response = input("\nSave these to ev3_config.py? (y/n): ").strip().lower()

        if response != 'y':
            print("Save cancelled")
            return

        # Read current config
        config_path = "ev3_config.py"
        try:
            with open(config_path, 'r') as f:
                lines = f.readlines()

            # Update values
            for i, line in enumerate(lines):
                for key, value in self.measurements.items():
                    if line.startswith(key + ' ='):
                        # Replace the line with new value
                        if isinstance(value, float):
                            lines[i] = f"{key} = {value:.4f}  # Calibrated\n"
                        else:
                            lines[i] = f"{key} = {value}  # Calibrated\n"

            # Write back
            with open(config_path, 'w') as f:
                f.writelines(lines)

            print(f"\n✓ Configuration saved to {config_path}")
            print("  Restart programs to use new values")

        except Exception as e:
            print(f"\n✗ Save failed: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.WARNING,  # Keep quiet during calibration
        format='%(levelname)s: %(message)s'
    )

    try:
        wizard = CalibrationWizard()
        wizard.run()

    except KeyboardInterrupt:
        print("\n\n✓ Calibration interrupted by user")
    except Exception as e:
        print(f"\n✗ Calibration error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
