#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Verification Script
Verifies that the robot controller is properly configured and all dependencies are available.
"""

import sys
import os


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def check_hardware():
    """
    Check if GPIO hardware is available.

    Returns:
        (success, message) tuple
    """
    try:
        import RPi.GPIO as GPIO
        # Try to set mode to verify GPIO actually works
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()
            return (True, "GPIO available")
        except RuntimeError as e:
            return (False, f"GPIO error: {e}")
    except ImportError:
        return (False, "RPi.GPIO not installed or not on Raspberry Pi")
    except RuntimeError:
        return (False, "Not running on Raspberry Pi hardware")


def check_serial_port():
    """
    Check if MTi serial port exists.

    Returns:
        (success, message) tuple
    """
    try:
        from config import Config
        serial_port = Config.MTI_SERIAL_PORT

        if os.path.exists(serial_port):
            # Check if we have permission to access it
            if os.access(serial_port, os.R_OK | os.W_OK):
                return (True, f"Serial port {serial_port} exists and accessible")
            else:
                return (False, f"Serial port {serial_port} exists but no permission (add user to dialout group)")
        else:
            return (False, f"Serial port {serial_port} does not exist (enable UART in raspi-config)")
    except Exception as e:
        return (False, f"Error checking serial port: {e}")


def check_dependencies():
    """
    Check if all required dependencies are installed.

    Returns:
        (success, message) tuple
    """
    required_modules = [
        ('serial', 'pyserial'),
        ('paho.mqtt.client', 'paho-mqtt'),
        ('dotenv', 'python-dotenv'),
        ('geojson', 'geojson'),
    ]

    missing = []

    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        return (False, f"Missing packages: {', '.join(missing)}")
    else:
        return (True, "All dependencies installed")


def check_configuration():
    """
    Check if configuration is valid.

    Returns:
        (success, message) tuple
    """
    try:
        from config import Config
        Config.validate()
        return (True, "Configuration valid")
    except ValueError as e:
        return (False, f"Configuration error: {e}")
    except Exception as e:
        return (False, f"Error loading configuration: {e}")


def check_geojson_file():
    """
    Check if GeoJSON roads file exists.

    Returns:
        (success, message) tuple
    """
    try:
        from config import Config
        geojson_file = Config.GEOJSON_ROADS_FILE

        if os.path.exists(geojson_file):
            return (True, f"GeoJSON file found: {geojson_file}")
        else:
            return (False, f"GeoJSON file not found: {geojson_file} (use tools/download_roads.py)")
    except Exception as e:
        return (False, f"Error checking GeoJSON file: {e}")


def check_env_file():
    """
    Check if .env file exists.

    Returns:
        (success, message) tuple
    """
    env_file = ".env"
    if os.path.exists(env_file):
        return (True, f"Environment file {env_file} exists")
    else:
        return (False, f"Environment file {env_file} not found (copy from .env.example)")


def check_log_directory():
    """
    Check if log directory is writable.

    Returns:
        (success, message) tuple
    """
    try:
        from config import Config
        log_file = Config.LOG_FILE
        log_dir = os.path.dirname(log_file)

        if not log_dir:
            log_dir = "."

        if os.path.exists(log_dir):
            if os.access(log_dir, os.W_OK):
                return (True, f"Log directory {log_dir} is writable")
            else:
                return (False, f"Log directory {log_dir} is not writable")
        else:
            return (False, f"Log directory {log_dir} does not exist")
    except Exception as e:
        return (False, f"Error checking log directory: {e}")


def run_checks():
    """
    Run all verification checks.

    Returns:
        True if all checks pass, False otherwise
    """
    print_header("Robot Controller - Setup Verification")

    checks = [
        ("Hardware (GPIO)", check_hardware),
        ("Serial Port", check_serial_port),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Configuration", check_configuration),
        ("GeoJSON Data", check_geojson_file),
        ("Log Directory", check_log_directory),
    ]

    results = []

    for check_name, check_func in checks:
        success, message = check_func()
        results.append((check_name, success, message))

        status = "✅" if success else "❌"
        print(f"{status} {check_name}: {message}")

    print("\n" + "=" * 60)

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("✅ All checks passed! Ready to run.")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Serial port: sudo raspi-config → Interface → Serial Port")
        print("  - Permissions: sudo usermod -a -G dialout,gpio $USER")
        print("  - Environment: cp .env.example .env && nano .env")
        print("  - Road data: python tools/download_roads.py --help")

    print("=" * 60 + "\n")

    return all_passed


def main():
    """Main entry point"""
    try:
        all_passed = run_checks()
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
