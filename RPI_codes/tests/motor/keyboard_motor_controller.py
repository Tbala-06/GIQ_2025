#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard Motor Controller - Raspberry Pi 5 Optimized
Control 2 DC motors (front wheel drive) with L298N motor driver using keyboard input.

Hardware:
- Raspberry Pi 5 (also compatible with Pi 4/3)
- L298N Motor Driver
- 2 DC Motors (Left and Right)

Controls:
- W: Move forward
- S: Move backward
- A: Tilt left (slow turn)
- D: Tilt right (slow turn)
- Q: Increase speed
- E: Decrease speed
- SPACE: Stop/Brake
- ESC: Exit program

Author: GIQ_2025 Project
"""

import sys
import os
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try to import GPIO library - RPi 5 prefers gpiod, fallback to RPi.GPIO for Pi 4/3
GPIO_AVAILABLE = False
GPIO_BACKEND = None

try:
    import gpiod
    from gpiod.line import Direction, Value
    GPIO_AVAILABLE = True
    GPIO_BACKEND = 'gpiod'
    print("✅ Using gpiod (Raspberry Pi 5 native)")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
        GPIO_BACKEND = 'RPi.GPIO'
        print("✅ Using RPi.GPIO (Raspberry Pi 4/3 compatible)")
    except (ImportError, RuntimeError):
        GPIO_AVAILABLE = False
        GPIO_BACKEND = None
        print("⚠️  WARNING: No GPIO library available - Running in SIMULATION mode")

# Try to import keyboard input library
try:
    import tty
    import termios
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️  WARNING: termios not available - keyboard input may not work")

# Motor GPIO Pins (BCM numbering) - Same as README.md
# Left Motor
MOTOR_LEFT_PWM = 12
MOTOR_LEFT_DIR1 = 16
MOTOR_LEFT_DIR2 = 20

# Right Motor
MOTOR_RIGHT_PWM = 13
MOTOR_RIGHT_DIR1 = 19
MOTOR_RIGHT_DIR2 = 26

# PWM Frequency
PWM_FREQUENCY = 1000  # 1 kHz

# Movement settings
DEFAULT_SPEED = 50  # Default speed percentage
TILT_SPEED = 30     # Slow speed for tilting/turning
SPEED_INCREMENT = 10  # Speed change per keypress
MAX_SPEED = 100
MIN_SPEED = 20


class MotorController:
    """L298N Motor Controller for 2 DC motors - RPi 5 Optimized"""

    def __init__(self, simulate=False):
        """
        Initialize motor controller.

        Args:
            simulate: If True, simulate motor control without GPIO
        """
        self.simulate = simulate or not GPIO_AVAILABLE
        self.backend = GPIO_BACKEND
        self.left_pwm = None
        self.right_pwm = None
        self.left_pwm_duty = 0
        self.right_pwm_duty = 0

        # For gpiod backend
        self.chip = None
        self.lines = {}
        self.pwm_thread = None
        self.pwm_running = False

        if not self.simulate:
            if self.backend == 'gpiod':
                # Raspberry Pi 5 - Use gpiod
                self._setup_gpiod()
            elif self.backend == 'RPi.GPIO':
                # Raspberry Pi 4/3 - Use RPi.GPIO
                self._setup_rpi_gpio()

            print(f"✅ GPIO initialized ({self.backend}) - Motors ready")
        else:
            print("ℹ️  Simulation mode - No actual motor control")

    def _setup_gpiod(self):
        """Setup GPIO using gpiod for Raspberry Pi 5"""
        # Open GPIO chip
        self.chip = gpiod.Chip('/dev/gpiochip4')  # RPi 5 uses gpiochip4

        # Configure all pins as outputs
        pin_config = {
            'left_pwm': MOTOR_LEFT_PWM,
            'left_dir1': MOTOR_LEFT_DIR1,
            'left_dir2': MOTOR_LEFT_DIR2,
            'right_pwm': MOTOR_RIGHT_PWM,
            'right_dir1': MOTOR_RIGHT_DIR1,
            'right_dir2': MOTOR_RIGHT_DIR2,
        }

        for name, pin in pin_config.items():
            line = self.chip.get_line(pin)
            line.request(consumer="keyboard_controller", type=gpiod.LINE_REQ_DIR_OUT)
            self.lines[name] = line

        # Start software PWM thread for gpiod
        self.pwm_running = True
        self.pwm_thread = threading.Thread(target=self._software_pwm, daemon=True)
        self.pwm_thread.start()

    def _setup_rpi_gpio(self):
        """Setup GPIO using RPi.GPIO for Raspberry Pi 4/3"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Left motor pins
        GPIO.setup(MOTOR_LEFT_PWM, GPIO.OUT)
        GPIO.setup(MOTOR_LEFT_DIR1, GPIO.OUT)
        GPIO.setup(MOTOR_LEFT_DIR2, GPIO.OUT)

        # Right motor pins
        GPIO.setup(MOTOR_RIGHT_PWM, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_DIR1, GPIO.OUT)
        GPIO.setup(MOTOR_RIGHT_DIR2, GPIO.OUT)

        # Setup PWM
        self.left_pwm = GPIO.PWM(MOTOR_LEFT_PWM, PWM_FREQUENCY)
        self.right_pwm = GPIO.PWM(MOTOR_RIGHT_PWM, PWM_FREQUENCY)

        # Start PWM with 0% duty cycle
        self.left_pwm.start(0)
        self.right_pwm.start(0)

    def _software_pwm(self):
        """Software PWM implementation for gpiod backend"""
        period = 1.0 / PWM_FREQUENCY  # Period in seconds

        while self.pwm_running:
            # Left motor PWM
            if self.left_pwm_duty > 0:
                on_time = period * (self.left_pwm_duty / 100.0)
                off_time = period - on_time

                if on_time > 0:
                    self.lines['left_pwm'].set_value(1)
                    time.sleep(on_time)
                if off_time > 0:
                    self.lines['left_pwm'].set_value(0)
                    time.sleep(off_time)
            else:
                self.lines['left_pwm'].set_value(0)
                time.sleep(period)

            # Right motor PWM (interleaved for better performance)
            if self.right_pwm_duty > 0:
                on_time = period * (self.right_pwm_duty / 100.0)
                off_time = period - on_time

                if on_time > 0:
                    self.lines['right_pwm'].set_value(1)
                    time.sleep(on_time)
                if off_time > 0:
                    self.lines['right_pwm'].set_value(0)
                    time.sleep(off_time)
            else:
                self.lines['right_pwm'].set_value(0)
                time.sleep(period)

    def set_left_motor(self, speed: float):
        """
        Set left motor speed and direction.

        Args:
            speed: Speed from -100 (full reverse) to 100 (full forward)
        """
        speed = max(-100, min(100, speed))  # Clamp to -100..100

        if self.simulate:
            if abs(speed) > 1:
                print(f"LEFT:  {'FWD' if speed > 0 else 'REV'} {abs(speed):3.0f}%", end="  ")
            return

        if self.backend == 'gpiod':
            # gpiod backend
            if speed > 0:  # Forward
                self.lines['left_dir1'].set_value(1)
                self.lines['left_dir2'].set_value(0)
            elif speed < 0:  # Reverse
                self.lines['left_dir1'].set_value(0)
                self.lines['left_dir2'].set_value(1)
            else:  # Stop
                self.lines['left_dir1'].set_value(0)
                self.lines['left_dir2'].set_value(0)

            # Update PWM duty cycle
            self.left_pwm_duty = abs(speed)

        elif self.backend == 'RPi.GPIO':
            # RPi.GPIO backend
            if speed > 0:  # Forward
                GPIO.output(MOTOR_LEFT_DIR1, GPIO.HIGH)
                GPIO.output(MOTOR_LEFT_DIR2, GPIO.LOW)
            elif speed < 0:  # Reverse
                GPIO.output(MOTOR_LEFT_DIR1, GPIO.LOW)
                GPIO.output(MOTOR_LEFT_DIR2, GPIO.HIGH)
            else:  # Stop
                GPIO.output(MOTOR_LEFT_DIR1, GPIO.LOW)
                GPIO.output(MOTOR_LEFT_DIR2, GPIO.LOW)

            # Set speed
            self.left_pwm.ChangeDutyCycle(abs(speed))

    def set_right_motor(self, speed: float):
        """
        Set right motor speed and direction.

        Args:
            speed: Speed from -100 (full reverse) to 100 (full forward)
        """
        speed = max(-100, min(100, speed))  # Clamp to -100..100

        if self.simulate:
            if abs(speed) > 1:
                print(f"RIGHT: {'FWD' if speed > 0 else 'REV'} {abs(speed):3.0f}%")
            return

        if self.backend == 'gpiod':
            # gpiod backend
            if speed > 0:  # Forward
                self.lines['right_dir1'].set_value(1)
                self.lines['right_dir2'].set_value(0)
            elif speed < 0:  # Reverse
                self.lines['right_dir1'].set_value(0)
                self.lines['right_dir2'].set_value(1)
            else:  # Stop
                self.lines['right_dir1'].set_value(0)
                self.lines['right_dir2'].set_value(0)

            # Update PWM duty cycle
            self.right_pwm_duty = abs(speed)

        elif self.backend == 'RPi.GPIO':
            # RPi.GPIO backend
            if speed > 0:  # Forward
                GPIO.output(MOTOR_RIGHT_DIR1, GPIO.HIGH)
                GPIO.output(MOTOR_RIGHT_DIR2, GPIO.LOW)
            elif speed < 0:  # Reverse
                GPIO.output(MOTOR_RIGHT_DIR1, GPIO.LOW)
                GPIO.output(MOTOR_RIGHT_DIR2, GPIO.HIGH)
            else:  # Stop
                GPIO.output(MOTOR_RIGHT_DIR1, GPIO.LOW)
                GPIO.output(MOTOR_RIGHT_DIR2, GPIO.LOW)

            # Set speed
            self.right_pwm.ChangeDutyCycle(abs(speed))

    def stop(self):
        """Stop both motors"""
        self.set_left_motor(0)
        self.set_right_motor(0)

    def cleanup(self):
        """Cleanup GPIO"""
        self.stop()
        if not self.simulate:
            if self.backend == 'gpiod':
                # Stop PWM thread
                self.pwm_running = False
                if self.pwm_thread:
                    self.pwm_thread.join(timeout=1.0)

                # Release all lines
                for line in self.lines.values():
                    line.release()

                # Close chip
                if self.chip:
                    self.chip.close()

            elif self.backend == 'RPi.GPIO':
                if self.left_pwm:
                    self.left_pwm.stop()
                if self.right_pwm:
                    self.right_pwm.stop()
                GPIO.cleanup()

            print("✅ GPIO cleaned up")


class KeyboardInput:
    """Handle keyboard input for motor control"""

    def __init__(self):
        """Initialize keyboard input handler"""
        self.fd = None
        self.old_settings = None

    def setup(self):
        """Setup terminal for raw input"""
        if not KEYBOARD_AVAILABLE:
            return False

        try:
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
            return True
        except Exception as e:
            print(f"⚠️  Could not setup keyboard input: {e}")
            return False

    def cleanup(self):
        """Restore terminal settings"""
        if self.old_settings and self.fd:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self):
        """
        Get a single keypress.

        Returns:
            str: The key pressed, or empty string if none
        """
        if not KEYBOARD_AVAILABLE:
            return ''

        try:
            key = sys.stdin.read(1)
            # Handle escape sequences
            if key == '\x1b':  # ESC
                # Read next two chars for arrow keys
                next_chars = sys.stdin.read(2)
                if next_chars == '[A':
                    return 'UP'
                elif next_chars == '[B':
                    return 'DOWN'
                elif next_chars == '[C':
                    return 'RIGHT'
                elif next_chars == '[D':
                    return 'LEFT'
                else:
                    return 'ESC'
            return key.lower()
        except Exception:
            return ''


def move_forward(motors, speed):
    """Move both motors forward"""
    motors.set_left_motor(speed)
    motors.set_right_motor(speed)


def move_backward(motors, speed):
    """Move both motors backward"""
    motors.set_left_motor(-speed)
    motors.set_right_motor(-speed)


def tilt_left(motors):
    """Slow turn left - left motor slower than right"""
    motors.set_left_motor(TILT_SPEED * 0.3)  # Left motor at 30% of tilt speed
    motors.set_right_motor(TILT_SPEED)       # Right motor at full tilt speed


def tilt_right(motors):
    """Slow turn right - right motor slower than left"""
    motors.set_left_motor(TILT_SPEED)        # Left motor at full tilt speed
    motors.set_right_motor(TILT_SPEED * 0.3)  # Right motor at 30% of tilt speed


def main():
    """Main program"""
    print("\n" + "=" * 70)
    print("KEYBOARD MOTOR CONTROLLER - RASPBERRY PI 5 OPTIMIZED")
    print("=" * 70)
    print("\nControls:")
    print("  W          - Move forward")
    print("  S          - Move backward")
    print("  A          - Tilt left (slow turn)")
    print("  D          - Tilt right (slow turn)")
    print("  Q          - Increase speed")
    print("  E          - Decrease speed")
    print("  SPACE      - Stop/Brake")
    print("  ESC        - Exit program")
    print("=" * 70 + "\n")

    # Check for simulation mode override
    simulate = '--simulate' in sys.argv

    # Initialize keyboard input
    keyboard = KeyboardInput()
    if not keyboard.setup():
        print("❌ Failed to setup keyboard input")
        print("Run with: python3 keyboard_motor_controller.py")
        return

    try:
        # Initialize motors
        print("Initializing motor controller...")
        motors = MotorController(simulate=simulate)

        # Current speed setting
        current_speed = DEFAULT_SPEED
        print(f"\n✅ System ready! Current speed: {current_speed}%")
        print("Use W/A/S/D to control, Q/E to adjust speed, SPACE to stop, ESC to exit.\n")

        # Main control loop
        running = True
        last_key = ''

        while running:
            key = keyboard.get_key()

            if key and key != last_key:
                if key == 'w':
                    # Forward
                    move_forward(motors, current_speed)
                    print(f"\r⬆️  FORWARD at {current_speed}%     ", end='', flush=True)

                elif key == 's':
                    # Backward
                    move_backward(motors, current_speed)
                    print(f"\r⬇️  REVERSE at {current_speed}%     ", end='', flush=True)

                elif key == 'a':
                    # Tilt left (slow)
                    tilt_left(motors)
                    print(f"\r⬅️  TILT LEFT at {TILT_SPEED}% (slow)     ", end='', flush=True)

                elif key == 'd':
                    # Tilt right (slow)
                    tilt_right(motors)
                    print(f"\r➡️  TILT RIGHT at {TILT_SPEED}% (slow)     ", end='', flush=True)

                elif key == 'q':
                    # Increase speed
                    current_speed = min(MAX_SPEED, current_speed + SPEED_INCREMENT)
                    print(f"\r🔼 Speed increased to {current_speed}%     ", end='', flush=True)

                elif key == 'e':
                    # Decrease speed
                    current_speed = max(MIN_SPEED, current_speed - SPEED_INCREMENT)
                    print(f"\r🔽 Speed decreased to {current_speed}%     ", end='', flush=True)

                elif key == ' ':
                    # Stop
                    motors.stop()
                    print(f"\r🛑 STOPPED                    ", end='', flush=True)

                elif key == 'esc' or key == '\x03':  # ESC or Ctrl+C
                    print("\n\n👋 Exit requested")
                    running = False

                last_key = key

            # Small delay to prevent CPU overload
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\n\nCleaning up...")
        keyboard.cleanup()
        if 'motors' in locals():
            motors.cleanup()
        print("✅ Cleanup complete")
        print("\nGoodbye! 👋\n")


if __name__ == '__main__':
    main()
