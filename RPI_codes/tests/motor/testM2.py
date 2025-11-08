#!/usr/bin/env python3
"""
Motor Test with Speed Control - L298N
"""

import lgpio
import time

print("\n=== MOTOR TEST WITH SPEED CONTROL ===\n")

# Motor pins
L_PWM, L_D1, L_D2 = 12, 16, 20  # Left motor
R_PWM, R_D1, R_D2 = 13, 19, 26  # Right motor

# Open GPIO chip
h = lgpio.gpiochip_open(4)

# Set direction pins as outputs
for pin in [L_D1, L_D2, R_D1, R_D2]:
    lgpio.gpio_claim_output(h, pin)

# Set PWM pins with PWM capability
PWM_FREQ = 1000  # 1kHz frequency
lgpio.tx_pwm(h, L_PWM, PWM_FREQ, 0)  # Start at 0% duty cycle
lgpio.tx_pwm(h, R_PWM, PWM_FREQ, 0)

def set_motor(motor, direction, speed):
    """
    Control motor speed and direction
    motor: 'left' or 'right'
    direction: 'forward', 'reverse', or 'stop'
    speed: 0-100 (percentage)
    """
    speed = max(0, min(100, speed))  # Clamp between 0-100
    
    if motor == 'left':
        if direction == 'forward':
            lgpio.gpio_write(h, L_D1, 1)
            lgpio.gpio_write(h, L_D2, 0)
            lgpio.tx_pwm(h, L_PWM, PWM_FREQ, speed)
        elif direction == 'reverse':
            lgpio.gpio_write(h, L_D1, 0)
            lgpio.gpio_write(h, L_D2, 1)
            lgpio.tx_pwm(h, L_PWM, PWM_FREQ, speed)
        else:  # stop
            lgpio.gpio_write(h, L_D1, 0)
            lgpio.gpio_write(h, L_D2, 0)
            lgpio.tx_pwm(h, L_PWM, PWM_FREQ, 0)
    
    elif motor == 'right':
        if direction == 'forward':
            lgpio.gpio_write(h, R_D1, 1)
            lgpio.gpio_write(h, R_D2, 0)
            lgpio.tx_pwm(h, R_PWM, PWM_FREQ, speed)
        elif direction == 'reverse':
            lgpio.gpio_write(h, R_D1, 0)
            lgpio.gpio_write(h, R_D2, 1)
            lgpio.tx_pwm(h, R_PWM, PWM_FREQ, speed)
        else:  # stop
            lgpio.gpio_write(h, R_D1, 0)
            lgpio.gpio_write(h, R_D2, 0)
            lgpio.tx_pwm(h, R_PWM, PWM_FREQ, 0)

print("Press ENTER to start...", end='')
input()
print()

try:
    # Test at different speeds
    speeds = [30, 50, 75, 100]
    
    for speed in speeds:
        print(f"\n--- Testing at {speed}% speed ---")
        
        # Left forward
        print(f"Left forward {speed}%...")
        set_motor('left', 'forward', speed)
        time.sleep(2)
        set_motor('left', 'stop', 0)
        time.sleep(0.5)
        
        # Right forward
        print(f"Right forward {speed}%...")
        set_motor('right', 'forward', speed)
        time.sleep(2)
        set_motor('right', 'stop', 0)
        time.sleep(0.5)
        
        # Both forward (straight)
        print(f"Both forward {speed}%...")
        set_motor('left', 'forward', speed)
        set_motor('right', 'forward', speed)
        time.sleep(2)
        set_motor('left', 'stop', 0)
        set_motor('right', 'stop', 0)
        time.sleep(0.5)
    
    print("\n✅ Done! You saw different speeds?\n")

except KeyboardInterrupt:
    print("\nStopped")

finally:
    # Stop everything
    set_motor('left', 'stop', 0)
    set_motor('right', 'stop', 0)
    lgpio.gpiochip_close(h)