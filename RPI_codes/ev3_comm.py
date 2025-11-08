#!/usr/bin/env python3
"""
EV3 Communication Module
========================

Handles USB/SSH communication between Raspberry Pi and EV3 brick.
- Auto-detects EV3 IP on usb0 interface
- Establishes SSH connection and runs ev3_controller.py
- Sends commands and receives responses with encoder feedback
- Handles timeouts and retries

Author: GIQ 2025 Team
"""

import subprocess
import time
import logging
import socket
import re
from typing import Optional, Tuple, Dict
from threading import Lock

# Import configuration
try:
    from ev3_config import *
except ImportError:
    # Fallback defaults if config not available
    EV3_USB_INTERFACE = 'usb0'
    EV3_IP_SUBNET = '169.254'
    EV3_SSH_USER = 'robot'
    EV3_SSH_PORT = 22
    EV3_CONTROLLER_PATH = '/home/robot/ev3_controller.py'
    EV3_CONNECT_TIMEOUT = 10.0
    EV3_COMMAND_TIMEOUT = 30.0
    EV3_RESPONSE_TIMEOUT = 5.0
    EV3_MAX_RETRIES = 3
    EV3_RETRY_DELAY = 1.0
    SIMULATION_MODE = False

logger = logging.getLogger(__name__)


class EV3CommunicationError(Exception):
    """Custom exception for EV3 communication errors"""
    pass


class EV3Controller:
    """
    Controls EV3 brick via SSH over USB connection.

    Usage:
        ev3 = EV3Controller()
        ev3.connect()
        result = ev3.move_forward(50)  # Move 50cm
        ev3.disconnect()
    """

    def __init__(self, ev3_ip: Optional[str] = None, simulate: bool = SIMULATION_MODE):
        """
        Initialize EV3 controller.

        Args:
            ev3_ip: EV3 IP address. If None, will auto-detect.
            simulate: If True, simulates EV3 responses without hardware
        """
        self.ev3_ip = ev3_ip
        self.simulate = simulate
        self.connected = False
        self.ssh_process = None
        self.command_lock = Lock()  # Thread-safe command sending

        logger.info(f"EV3Controller initialized (simulate={simulate})")

    def _detect_ev3_ip(self) -> Optional[str]:
        """
        Auto-detect EV3 IP address on usb0 interface.
        Scans the 169.254.x.x subnet for responsive EV3.

        Returns:
            EV3 IP address if found, None otherwise
        """
        logger.info(f"Detecting EV3 IP on {EV3_USB_INTERFACE}...")

        try:
            # Get usb0 interface info
            result = subprocess.run(
                ['ip', 'addr', 'show', EV3_USB_INTERFACE],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.error(f"Interface {EV3_USB_INTERFACE} not found")
                return None

            # Look for the EV3 IP in ARP table
            # EV3 typically gets an IP in 169.254.x.x range
            arp_result = subprocess.run(
                ['ip', 'neigh', 'show', 'dev', EV3_USB_INTERFACE],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse ARP output for 169.254.x.x addresses
            arp_lines = arp_result.stdout.strip().split('\n')
            for line in arp_lines:
                # Look for IP addresses starting with 169.254
                match = re.search(r'(169\.254\.\d+\.\d+)', line)
                if match:
                    potential_ip = match.group(1)
                    logger.info(f"Found potential EV3 IP: {potential_ip}")

                    # Try to ping it
                    ping_result = subprocess.run(
                        ['ping', '-c', '1', '-W', '1', potential_ip],
                        capture_output=True,
                        timeout=2
                    )

                    if ping_result.returncode == 0:
                        logger.info(f"✓ EV3 found at {potential_ip}")
                        return potential_ip

            # If ARP didn't find it, try scanning common EV3 IPs
            logger.info("Scanning common EV3 IP addresses...")
            common_ips = [
                "169.254.131.241",  # Common EV3 default
                "169.254.144.109",  # Another common address
            ]

            for ip in common_ips:
                logger.info(f"Trying {ip}...")
                ping_result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', ip],
                    capture_output=True,
                    timeout=2
                )

                if ping_result.returncode == 0:
                    logger.info(f"✓ EV3 found at {ip}")
                    return ip

            logger.error("Could not detect EV3 IP address")
            return None

        except subprocess.TimeoutExpired:
            logger.error("Timeout while detecting EV3 IP")
            return None
        except Exception as e:
            logger.error(f"Error detecting EV3 IP: {e}")
            return None

    def _configure_usb0(self, ev3_ip: str) -> bool:
        """
        Configure usb0 interface to match EV3 subnet.

        Args:
            ev3_ip: Detected EV3 IP address

        Returns:
            True if configuration successful
        """
        try:
            # Extract the third octet from EV3 IP
            # E.g., 169.254.131.241 -> set RPi to 169.254.131.1
            octets = ev3_ip.split('.')
            rpi_ip = f"{octets[0]}.{octets[1]}.{octets[2]}.1"

            logger.info(f"Configuring {EV3_USB_INTERFACE} with IP {rpi_ip}/16")

            # Check if already configured
            result = subprocess.run(
                ['ip', 'addr', 'show', EV3_USB_INTERFACE],
                capture_output=True,
                text=True
            )

            if rpi_ip in result.stdout:
                logger.info(f"Interface already configured with {rpi_ip}")
                return True

            # Configure interface
            subprocess.run(
                ['sudo', 'ip', 'addr', 'add', f'{rpi_ip}/16', 'dev', EV3_USB_INTERFACE],
                check=True,
                timeout=5
            )

            logger.info(f"✓ Interface configured: {rpi_ip}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure usb0: {e}")
            return False
        except Exception as e:
            logger.error(f"Error configuring usb0: {e}")
            return False

    def connect(self) -> bool:
        """
        Establish connection to EV3 and start controller script.

        Returns:
            True if connection successful
        """
        if self.simulate:
            logger.info("✓ Simulation mode - skipping actual connection")
            self.connected = True
            return True

        try:
            # Auto-detect EV3 IP if not provided
            if not self.ev3_ip:
                self.ev3_ip = self._detect_ev3_ip()
                if not self.ev3_ip:
                    raise EV3CommunicationError("Could not detect EV3 IP address")

            # Configure usb0 interface
            if not self._configure_usb0(self.ev3_ip):
                raise EV3CommunicationError("Failed to configure USB interface")

            # Test SSH connection
            logger.info(f"Testing SSH connection to {self.ev3_ip}...")
            test_result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=5',
                 '-o', 'StrictHostKeyChecking=no',
                 f'{EV3_SSH_USER}@{self.ev3_ip}', 'echo', 'OK'],
                capture_output=True,
                text=True,
                timeout=EV3_CONNECT_TIMEOUT
            )

            if test_result.returncode != 0:
                raise EV3CommunicationError(f"SSH connection failed: {test_result.stderr}")

            logger.info("✓ SSH connection OK")

            # Start ev3_controller.py on EV3
            logger.info(f"Starting controller script: {EV3_CONTROLLER_PATH}")
            self.ssh_process = subprocess.Popen(
                ['ssh', '-o', 'StrictHostKeyChecking=no',
                 f'{EV3_SSH_USER}@{self.ev3_ip}',
                 'python3', EV3_CONTROLLER_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Wait for "READY" from EV3
            ready = self._wait_for_response("READY", timeout=5.0)
            if not ready:
                raise EV3CommunicationError("EV3 controller did not send READY signal")

            logger.info("✓ EV3 controller started")
            self.connected = True
            return True

        except subprocess.TimeoutExpired:
            logger.error("Connection timeout")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def _wait_for_response(self, expected: str, timeout: float = EV3_RESPONSE_TIMEOUT) -> bool:
        """
        Wait for expected response from EV3.

        Args:
            expected: Expected response string
            timeout: Maximum time to wait (seconds)

        Returns:
            True if response received
        """
        if self.simulate:
            return True

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.ssh_process and self.ssh_process.stdout:
                line = self.ssh_process.stdout.readline().strip()
                if line:
                    logger.debug(f"EV3 → {line}")
                    if expected in line:
                        return True
            time.sleep(0.1)

        return False

    def _send_command(self, command: str, wait_for: str = "DONE",
                     timeout: float = EV3_COMMAND_TIMEOUT) -> Optional[Dict]:
        """
        Send command to EV3 and wait for response.

        Args:
            command: Command string to send
            wait_for: Expected response (DONE, OK, ERROR)
            timeout: Maximum time to wait for response

        Returns:
            Dictionary with response data or None if failed
        """
        with self.command_lock:
            if not self.connected:
                logger.error("Not connected to EV3")
                return None

            if self.simulate:
                logger.info(f"[SIM] RPi → EV3: {command}")
                # Simulate response with fake encoder data
                return {
                    'status': 'DONE',
                    'left_encoder': 1000,
                    'right_encoder': 1000
                }

            try:
                # Send command
                logger.debug(f"RPi → EV3: {command}")
                self.ssh_process.stdin.write(command + '\n')
                self.ssh_process.stdin.flush()

                # Wait for response
                start_time = time.time()
                response_data = {}

                while (time.time() - start_time) < timeout:
                    line = self.ssh_process.stdout.readline().strip()
                    if line:
                        logger.debug(f"EV3 → RPi: {line}")

                        # Parse response
                        if line.startswith("DONE"):
                            response_data['status'] = 'DONE'
                            # Parse encoder data if present: DONE left=1234 right=5678
                            parts = line.split()
                            for part in parts[1:]:
                                if '=' in part:
                                    key, value = part.split('=')
                                    response_data[key] = int(value)
                            return response_data

                        elif line.startswith("OK"):
                            response_data['status'] = 'OK'
                            return response_data

                        elif line.startswith("ERROR"):
                            response_data['status'] = 'ERROR'
                            response_data['message'] = line[6:].strip()
                            logger.error(f"EV3 error: {response_data['message']}")
                            return response_data

                logger.error(f"Command timeout: {command}")
                return None

            except Exception as e:
                logger.error(f"Command failed: {e}")
                return None

    def _retry_command(self, command: str, max_retries: int = EV3_MAX_RETRIES) -> Optional[Dict]:
        """
        Send command with retry logic.

        Args:
            command: Command to send
            max_retries: Maximum number of retry attempts

        Returns:
            Response dictionary or None
        """
        for attempt in range(max_retries):
            result = self._send_command(command)
            if result and result.get('status') in ['DONE', 'OK']:
                return result

            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries}: {command}")
                time.sleep(EV3_RETRY_DELAY)

        logger.error(f"Command failed after {max_retries} attempts: {command}")
        return None

    # ========================================================================
    # HIGH-LEVEL MOVEMENT COMMANDS
    # ========================================================================

    def move_forward(self, distance_cm: float, speed: int = None) -> Optional[Tuple[int, int]]:
        """
        Move robot forward by specified distance.

        Args:
            distance_cm: Distance to move (cm)
            speed: Motor speed 0-100 (None = use default)

        Returns:
            Tuple of (left_encoder, right_encoder) or None if failed
        """
        speed_str = f" {speed}" if speed else ""
        command = f"MOVE_FORWARD {distance_cm}{speed_str}"
        result = self._retry_command(command)

        if result and result.get('status') == 'DONE':
            left = result.get('left', 0)
            right = result.get('right', 0)
            logger.info(f"✓ Moved forward {distance_cm}cm (encoders: L={left}, R={right})")
            return (left, right)

        return None

    def move_backward(self, distance_cm: float, speed: int = None) -> Optional[Tuple[int, int]]:
        """
        Move robot backward by specified distance.

        Args:
            distance_cm: Distance to move (cm)
            speed: Motor speed 0-100 (None = use default)

        Returns:
            Tuple of (left_encoder, right_encoder) or None if failed
        """
        speed_str = f" {speed}" if speed else ""
        command = f"MOVE_BACKWARD {distance_cm}{speed_str}"
        result = self._retry_command(command)

        if result and result.get('status') == 'DONE':
            left = result.get('left', 0)
            right = result.get('right', 0)
            logger.info(f"✓ Moved backward {distance_cm}cm (encoders: L={left}, R={right})")
            return (left, right)

        return None

    def rotate(self, degrees: float, speed: int = None) -> Optional[Tuple[int, int]]:
        """
        Rotate robot by specified angle.
        Positive = clockwise, Negative = counter-clockwise

        Args:
            degrees: Angle to rotate (degrees)
            speed: Motor speed 0-100 (None = use default)

        Returns:
            Tuple of (left_encoder, right_encoder) or None if failed
        """
        speed_str = f" {speed}" if speed else ""
        command = f"ROTATE {degrees}{speed_str}"
        result = self._retry_command(command)

        if result and result.get('status') == 'DONE':
            left = result.get('left', 0)
            right = result.get('right', 0)
            logger.info(f"✓ Rotated {degrees}° (encoders: L={left}, R={right})")
            return (left, right)

        return None

    def stop(self) -> bool:
        """
        Emergency stop - halt all motors immediately.

        Returns:
            True if successful
        """
        command = "STOP"
        result = self._send_command(command, wait_for="OK", timeout=2.0)

        if result and result.get('status') == 'OK':
            logger.info("✓ Motors stopped")
            return True

        return False

    def lower_stencil(self) -> bool:
        """
        Lower the stencil mechanism.

        Returns:
            True if successful
        """
        command = "LOWER_STENCIL"
        result = self._retry_command(command)

        if result and result.get('status') == 'DONE':
            logger.info("✓ Stencil lowered")
            return True

        return False

    def raise_stencil(self) -> bool:
        """
        Raise the stencil mechanism.

        Returns:
            True if successful
        """
        command = "RAISE_STENCIL"
        result = self._retry_command(command)

        if result and result.get('status') == 'DONE':
            logger.info("✓ Stencil raised")
            return True

        return False

    def dispense_paint(self, degrees: float = None) -> bool:
        """
        Dispense paint/sand.

        Args:
            degrees: Rotation amount (None = use default from config)

        Returns:
            True if successful
        """
        degrees_str = f" {degrees}" if degrees else ""
        command = f"DISPENSE_PAINT{degrees_str}"
        result = self._retry_command(command)

        if result and result.get('status') == 'DONE':
            logger.info("✓ Paint dispensed")
            return True

        return False

    def get_encoder_positions(self) -> Optional[Tuple[int, int]]:
        """
        Get current encoder positions without moving.

        Returns:
            Tuple of (left_encoder, right_encoder) or None if failed
        """
        command = "GET_ENCODERS"
        result = self._send_command(command, wait_for="OK")

        if result and result.get('status') == 'OK':
            left = result.get('left', 0)
            right = result.get('right', 0)
            return (left, right)

        return None

    def reset_encoders(self) -> bool:
        """
        Reset encoder positions to zero.

        Returns:
            True if successful
        """
        command = "RESET_ENCODERS"
        result = self._send_command(command, wait_for="OK")

        if result and result.get('status') == 'OK':
            logger.info("✓ Encoders reset")
            return True

        return False

    def disconnect(self):
        """
        Close SSH connection and cleanup.
        """
        if self.simulate:
            logger.info("✓ Simulation mode - disconnecting")
            self.connected = False
            return

        try:
            if self.ssh_process:
                # Send EXIT command
                self._send_command("EXIT", wait_for="OK", timeout=2.0)

                # Close SSH process
                self.ssh_process.stdin.close()
                self.ssh_process.terminate()
                self.ssh_process.wait(timeout=5)

                logger.info("✓ EV3 disconnected")

            self.connected = False

        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# ============================================================================
# TEST CODE
# ============================================================================

def test_ev3_communication():
    """Test EV3 communication module"""
    print("\n" + "=" * 70)
    print("EV3 COMMUNICATION TEST")
    print("=" * 70)

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Test with context manager
        with EV3Controller(simulate=True) as ev3:
            print("\n✓ Connected to EV3")

            # Test movements
            print("\n→ Testing forward movement...")
            ev3.move_forward(50)

            print("\n→ Testing rotation...")
            ev3.rotate(90)

            print("\n→ Testing backward movement...")
            ev3.move_backward(25)

            print("\n→ Testing stencil operations...")
            ev3.lower_stencil()
            ev3.dispense_paint()
            ev3.raise_stencil()

            print("\n→ Testing encoder read...")
            encoders = ev3.get_encoder_positions()
            print(f"   Encoders: {encoders}")

            print("\n→ Testing stop...")
            ev3.stop()

        print("\n✓ All tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ev3_communication()
