#!/usr/bin/env python3
"""
PS3 Controller Motor Test - Raspberry Pi 5 Optimized
Controls 2 DC motors (front wheel drive) with L298N motor driver using PS3 controller.

Hardware:
- Raspberry Pi 5 (also compatible with Pi 4/3)
- L298N Motor Driver
- 2 DC Motors (Left and Right)
- PS3 DualShock 3 Controller

Controls:
- Left Stick Y-axis: Forward/Backward
- Left Stick X-axis: Left/Right turning
- L1: Slow speed mode (30%)
- L2: Medium speed mode (60%)
- R1: Fast speed mode (100%)
- Triangle: Emergency stop
- Cross (X): Reset and re-center
- Circle: Toggle precision mode
- Start: Exit program
"""

import sys
import os
import time
import pygame

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

# Motor GPIO Pins (BCM numbering)
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

# Dead zone for joystick (prevents drift)
DEAD_ZONE = 0.15

# Speed modes
SPEED_MODES = {
    'SLOW': 30,
    'MEDIUM': 60,
    'FAST': 100
}


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
        import threading

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
            line.request(consumer="motor_controller", type=gpiod.LINE_REQ_DIR_OUT)
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


class PS3Controller:
    """PS3 DualShock 3 Controller Interface"""

    def __init__(self):
        """Initialize PS3 controller"""
        pygame.init()
        pygame.joystick.init()

        # Find PS3 controller
        self.joystick = None
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            if "Sony" in joy.get_name() or "PLAYSTATION" in joy.get_name() or "PS3" in joy.get_name():
                self.joystick = joy
                print(f"✅ PS3 Controller connected: {joy.get_name()}")
                break

        if not self.joystick:
            raise RuntimeError("No PS3 controller found! Please connect PS3 controller.")

        # Controller state
        self.left_x = 0.0
        self.left_y = 0.0
        self.speed_mode = 'MEDIUM'
        self.precision_mode = False
        self.running = True

    def apply_dead_zone(self, value: float) -> float:
        """Apply dead zone to joystick value"""
        if abs(value) < DEAD_ZONE:
            return 0.0
        return value

    def get_button_name(self, button: int) -> str:
        """Get button name from button index"""
        button_names = {
            0: "Cross (X)",
            1: "Circle",
            2: "Square",
            3: "Triangle",
            4: "L1",
            5: "R1",
            6: "L2",
            7: "R2",
            8: "Share",
            9: "Options",
            10: "L3",
            11: "R3",
            12: "PS Button",
        }
        return button_names.get(button, f"Button {button}")

    def update(self):
        """Update controller state"""
        pygame.event.pump()

        # Read left stick (axis 0 = X, axis 1 = Y)
        self.left_x = self.apply_dead_zone(self.joystick.get_axis(0))
        self.left_y = self.apply_dead_zone(-self.joystick.get_axis(1))  # Invert Y

    def process_events(self):
        """Process controller events"""
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                button_name = self.get_button_name(button)

                # Speed mode buttons
                if button == 4:  # L1 - Slow
                    self.speed_mode = 'SLOW'
                    print(f"\n🐌 SLOW mode ({SPEED_MODES['SLOW']}%)")
                elif button == 6:  # L2 - Medium
                    self.speed_mode = 'MEDIUM'
                    print(f"\n🚶 MEDIUM mode ({SPEED_MODES['MEDIUM']}%)")
                elif button == 5:  # R1 - Fast
                    self.speed_mode = 'FAST'
                    print(f"\n🏃 FAST mode ({SPEED_MODES['FAST']}%)")

                # Control buttons
                elif button == 3:  # Triangle - Emergency stop
                    print("\n🛑 EMERGENCY STOP!")
                    return 'STOP'
                elif button == 0:  # Cross - Reset
                    print("\n🔄 Reset")
                    return 'RESET'
                elif button == 1:  # Circle - Precision toggle
                    self.precision_mode = not self.precision_mode
                    print(f"\n🎯 Precision mode: {'ON' if self.precision_mode else 'OFF'}")
                elif button == 9:  # Start - Exit
                    print("\n👋 Exit requested")
                    self.running = False
                    return 'EXIT'

        return None


def calculate_motor_speeds(left_y: float, left_x: float, max_speed: float, precision: bool):
    """
    Calculate motor speeds from joystick input.

    Args:
        left_y: Forward/backward (-1 to 1)
        left_x: Left/right turning (-1 to 1)
        max_speed: Maximum speed percentage (0-100)
        precision: If True, reduce speed for precision control

    Returns:
        (left_speed, right_speed) tuple
    """
    # Apply precision mode
    if precision:
        left_y *= 0.5
        left_x *= 0.5

    # Tank drive algorithm
    # Forward/backward + turning
    left_speed = left_y + left_x
    right_speed = left_y - left_x

    # Normalize if values exceed -1..1
    max_val = max(abs(left_speed), abs(right_speed))
    if max_val > 1.0:
        left_speed /= max_val
        right_speed /= max_val

    # Scale to max_speed
    left_speed *= max_speed
    right_speed *= max_speed

    return left_speed, right_speed


def main():
    """Main program"""
    print("\n" + "=" * 70)
    print("PS3 CONTROLLER MOTOR TEST - FRONT WHEEL DRIVE")
    print("=" * 70)
    print("\nControls:")
    print("  Left Stick Y-axis: Forward/Backward")
    print("  Left Stick X-axis: Left/Right turning")
    print("  L1: Slow speed (30%)")
    print("  L2: Medium speed (60%)")
    print("  R1: Fast speed (100%)")
    print("  Triangle: Emergency stop")
    print("  Cross (X): Reset")
    print("  Circle: Toggle precision mode")
    print("  Start: Exit program")
    print("=" * 70 + "\n")

    # Check for simulation mode override
    simulate = '--simulate' in sys.argv

    try:
        # Initialize controller
        print("Initializing PS3 controller...")
        controller = PS3Controller()

        # Initialize motors
        print("Initializing motor controller...")
        motors = MotorController(simulate=simulate)

        print("\n✅ System ready! Use PS3 controller to control motors.\n")

        # Main control loop
        last_print = time.time()
        last_left_speed = 0
        last_right_speed = 0

        while controller.running:
            # Process button events
            event = controller.process_events()

            if event == 'EXIT':
                break
            elif event == 'STOP':
                motors.stop()
                continue
            elif event == 'RESET':
                motors.stop()
                controller.speed_mode = 'MEDIUM'
                controller.precision_mode = False
                continue

            # Update controller state
            controller.update()

            # Get max speed for current mode
            max_speed = SPEED_MODES[controller.speed_mode]

            # Calculate motor speeds
            left_speed, right_speed = calculate_motor_speeds(
                controller.left_y,
                controller.left_x,
                max_speed,
                controller.precision_mode
            )

            # Set motor speeds
            motors.set_left_motor(left_speed)
            motors.set_right_motor(right_speed)

            # Print status every 0.1 seconds (if changed)
            if time.time() - last_print > 0.1:
                if abs(left_speed - last_left_speed) > 1 or abs(right_speed - last_right_speed) > 1:
                    mode_indicator = "🎯" if controller.precision_mode else ""
                    print(f"\r{mode_indicator} Mode: {controller.speed_mode:6} | "
                          f"Stick: ({controller.left_x:+5.2f}, {controller.left_y:+5.2f}) | ", end="")

                    if not simulate:
                        print(f"L: {left_speed:+6.1f}% | R: {right_speed:+6.1f}%   ", end="")

                    last_left_speed = left_speed
                    last_right_speed = right_speed

                last_print = time.time()

            # Small delay to prevent CPU overload
            time.sleep(0.02)  # 50 Hz update rate

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\n\nCleaning up...")
        if 'motors' in locals():
            motors.cleanup()
        pygame.quit()
        print("✅ Cleanup complete")
        print("\nGoodbye! 👋\n")


if __name__ == '__main__':
    main()
