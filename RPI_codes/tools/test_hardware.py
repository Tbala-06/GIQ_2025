#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware Test Tool
Interactive menu for testing all robot hardware components.
"""

import sys
import time
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import setup_logging, get_logger
from config import Config

logger = get_logger(__name__)


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_mti_sensor():
    """Test MTi IMU/GPS sensor"""
    print_header("MTi IMU/GPS Sensor Test")

    try:
        from hardware.mti_parser import MTiParser

        mti = MTiParser(Config.MTI_SERIAL_PORT, Config.MTI_BAUDRATE)

        print(f"Connecting to MTi on {Config.MTI_SERIAL_PORT}...")
        if not mti.connect():
            print("❌ Failed to connect to MTi sensor")
            return False

        print("✅ Connected successfully")
        print("\nReading sensor data (10 samples)...")
        print("-" * 60)

        for i in range(10):
            data = mti.read_data(timeout=2.0)

            if data:
                print(f"\nSample {i+1}:")

                if data.latitude_longitude:
                    lat, lon = data.latitude_longitude
                    print(f"  GPS: {lat:.6f}, {lon:.6f}")

                if data.euler_angles:
                    roll, pitch, yaw = data.euler_angles
                    print(f"  Orientation: Roll={roll:.1f}° Pitch={pitch:.1f}° Yaw={yaw:.1f}°")

                gps_info = data.get_gps_info()
                print(f"  GPS Fix: {gps_info.get('fix', 'Unknown')}")
                print(f"  Satellites: {gps_info.get('satellites', 0)}")
            else:
                print(f"Sample {i+1}: No data")

            time.sleep(1.0)

        mti.disconnect()
        print("\n✅ MTi test complete")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_motors():
    """Test motor controller"""
    print_header("Motor Controller Test")

    try:
        from hardware.motor_controller import MotorController

        motor = MotorController(simulate=False)

        print("\n1. Testing forward movement...")
        motor.move_forward(speed=50, distance_meters=0.5)
        time.sleep(2)

        print("2. Testing backward movement...")
        motor.move_backward(speed=50, distance_meters=0.5)
        time.sleep(2)

        print("3. Testing left turn...")
        motor.turn_left(45, speed=50)
        time.sleep(2)

        print("4. Testing right turn...")
        motor.turn_right(45, speed=50)
        time.sleep(2)

        print("5. Stopping motors...")
        motor.stop()

        motor.cleanup()
        print("\n✅ Motor test complete")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_stencil_servo():
    """Test stencil servo controller"""
    print_header("Stencil Servo Test")

    try:
        from hardware.stencil_controller import StencilController

        stencil = StencilController(simulate=False)

        print("\n1. Moving to home position (90°)...")
        stencil.home_position()
        time.sleep(2)

        print("2. Sweeping left to right (0° to 180°)...")
        for angle in range(0, 181, 30):
            print(f"   Angle: {angle}°")
            stencil.set_angle(angle)
            time.sleep(1)

        print("3. Returning to home...")
        stencil.home_position()
        time.sleep(1)

        stencil.cleanup()
        print("\n✅ Stencil servo test complete")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_paint_dispenser():
    """Test paint dispenser"""
    print_header("Paint Dispenser Test")

    try:
        from hardware.paint_dispenser import PaintDispenser

        dispenser = PaintDispenser(simulate=False)

        print("\n1. Testing short dispense (2 seconds)...")
        dispenser.dispense(duration_seconds=2.0)
        time.sleep(3)

        print("2. Testing start/stop control...")
        print("   Starting dispenser...")
        dispenser.start_dispensing()
        time.sleep(2)
        print("   Stopping dispenser...")
        dispenser.stop_dispensing()

        dispenser.cleanup()
        print("\n✅ Paint dispenser test complete")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_navigation_simulation():
    """Test GPS navigation in simulation"""
    print_header("GPS Navigation Simulation Test")

    try:
        from hardware.mti_parser import MTiParser
        from hardware.motor_controller import MotorController
        from navigation.gps_navigator import GPSNavigator

        print("\nInitializing components...")
        mti = MTiParser(Config.MTI_SERIAL_PORT, Config.MTI_BAUDRATE)
        motor = MotorController(simulate=False)
        navigator = GPSNavigator(mti, motor)

        if not mti.connect():
            print("❌ Failed to connect to MTi sensor")
            return False

        print("✅ Components initialized")

        print("\n1. Testing GPS position reading...")
        pos = navigator.get_current_position(timeout=5.0)
        if pos:
            print(f"   Current position: {pos[0]:.6f}, {pos[1]:.6f}")
        else:
            print("   ⚠ No GPS position available")

        print("\n2. Testing heading reading...")
        heading = navigator.get_heading(timeout=2.0)
        if heading is not None:
            print(f"   Current heading: {heading:.1f}°")
        else:
            print("   ⚠ No heading available")

        print("\n3. Testing GPS quality...")
        quality = navigator.get_gps_quality()
        print(f"   Fix: {quality.get('fix', 'Unknown')}")
        print(f"   Satellites: {quality.get('satellites', 0)}")

        mti.disconnect()
        motor.cleanup()
        print("\n✅ Navigation test complete")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_safety_monitor():
    """Test safety monitoring system"""
    print_header("Safety Monitor Test")

    try:
        from hardware.mti_parser import MTiParser
        from control.safety_monitor import SafetyMonitor

        print("\nInitializing safety monitor...")
        mti = MTiParser(Config.MTI_SERIAL_PORT, Config.MTI_BAUDRATE)
        safety = SafetyMonitor(mti, simulate=False)

        if not mti.connect():
            print("⚠ MTi sensor not connected, some checks will be skipped")
        else:
            print("✅ MTi sensor connected")

        print("\nPerforming safety checks...")
        results = safety.perform_safety_checks()

        for check_name, (is_safe, reason) in results.items():
            status = "✅" if is_safe else "❌"
            print(f"{status} {check_name.upper()}: {reason}")

        print("\nOverall safety check...")
        is_safe, reason = safety.is_safe_to_operate()
        if is_safe:
            print(f"✅ SAFE TO OPERATE: {reason}")
        else:
            print(f"❌ NOT SAFE: {reason}")

        mti.disconnect()
        safety.cleanup()
        print("\n✅ Safety monitor test complete")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main_menu():
    """Display main test menu"""
    while True:
        clear_screen()
        print_header("Robot Hardware Test Menu")
        print("\n1. Test MTi IMU/GPS Sensor")
        print("2. Test Motor Controller")
        print("3. Test Stencil Servo")
        print("4. Test Paint Dispenser")
        print("5. Test GPS Navigation")
        print("6. Test Safety Monitor")
        print("7. Run All Tests")
        print("0. Exit")
        print("\n" + "=" * 60)

        choice = input("\nEnter choice (0-7): ").strip()

        if choice == '0':
            print("\nExiting...")
            break
        elif choice == '1':
            test_mti_sensor()
            input("\nPress Enter to continue...")
        elif choice == '2':
            test_motors()
            input("\nPress Enter to continue...")
        elif choice == '3':
            test_stencil_servo()
            input("\nPress Enter to continue...")
        elif choice == '4':
            test_paint_dispenser()
            input("\nPress Enter to continue...")
        elif choice == '5':
            test_navigation_simulation()
            input("\nPress Enter to continue...")
        elif choice == '6':
            test_safety_monitor()
            input("\nPress Enter to continue...")
        elif choice == '7':
            print_header("Running All Tests")
            test_mti_sensor()
            time.sleep(2)
            test_motors()
            time.sleep(2)
            test_stencil_servo()
            time.sleep(2)
            test_paint_dispenser()
            time.sleep(2)
            test_navigation_simulation()
            time.sleep(2)
            test_safety_monitor()
            print_header("All Tests Complete")
            input("\nPress Enter to continue...")
        else:
            print("\n❌ Invalid choice")
            time.sleep(1)


def main():
    """Main entry point"""
    # Setup logging
    setup_logging("/tmp/hardware_test.log", "INFO")

    print_header("Robot Hardware Test Tool")
    print("\nWARNING: This tool will directly control robot hardware.")
    print("Make sure the robot is in a safe position and area.")

    response = input("\nContinue? (y/n): ").strip().lower()
    if response != 'y':
        print("Exiting...")
        return

    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nGoodbye!")


if __name__ == '__main__':
    main()
