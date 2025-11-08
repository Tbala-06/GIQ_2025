# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Dead Simple Motor Test - L298N
"""

import lgpio
import time

print("\n=== SIMPLE MOTOR TEST ===\n")

# Motor pins
L_PWM, L_D1, L_D2 = 12, 16, 20  # Left motor
R_PWM, R_D1, R_D2 = 13, 19, 26  # Right motor

# Open GPIO chip
h = lgpio.gpiochip_open(4)

# Set all pins as outputs
for pin in [L_PWM, L_D1, L_D2, R_PWM, R_D1, R_D2]:
    lgpio.gpio_claim_output(h, pin)

print("Press ENTER to start...", end='')
input()
print()

try:
    # Left forward
    print("Left forward...")
    lgpio.gpio_write(h, L_D1, 1)
    lgpio.gpio_write(h, L_D2, 0)
    lgpio.gpio_write(h, L_PWM, 1)
    time.sleep(2)
    lgpio.gpio_write(h, L_PWM, 0)
    time.sleep(0.5)
    
    # Left reverse
    print("Left reverse...")
    lgpio.gpio_write(h, L_D1, 0)
    lgpio.gpio_write(h, L_D2, 1)
    lgpio.gpio_write(h, L_PWM, 1)
    time.sleep(2)
    lgpio.gpio_write(h, L_PWM, 0)
    time.sleep(0.5)
    
    # Right forward
    print("Right forward...")
    lgpio.gpio_write(h, R_D1, 1)
    lgpio.gpio_write(h, R_D2, 0)
    lgpio.gpio_write(h, R_PWM, 1)
    time.sleep(2)
    lgpio.gpio_write(h, R_PWM, 0)
    time.sleep(0.5)
    
    # Right reverse
    print("Right reverse...")
    lgpio.gpio_write(h, R_D1, 0)
    lgpio.gpio_write(h, R_D2, 1)
    lgpio.gpio_write(h, R_PWM, 1)
    time.sleep(2)
    lgpio.gpio_write(h, R_PWM, 0)
    time.sleep(0.5)
    
    # Both forward (straight)
    print("Straight forward...")
    lgpio.gpio_write(h, L_D1, 1)
    lgpio.gpio_write(h, L_D2, 0)
    lgpio.gpio_write(h, R_D1, 1)
    lgpio.gpio_write(h, R_D2, 0)
    lgpio.gpio_write(h, L_PWM, 1)
    lgpio.gpio_write(h, R_PWM, 1)
    time.sleep(2)
    lgpio.gpio_write(h, L_PWM, 0)
    lgpio.gpio_write(h, R_PWM, 0)
    time.sleep(0.5)
    
    # Both reverse (straight back)
    print("Straight back...")
    lgpio.gpio_write(h, L_D1, 0)
    lgpio.gpio_write(h, L_D2, 1)
    lgpio.gpio_write(h, R_D1, 0)
    lgpio.gpio_write(h, R_D2, 1)
    lgpio.gpio_write(h, L_PWM, 1)
    lgpio.gpio_write(h, R_PWM, 1)
    time.sleep(2)
    lgpio.gpio_write(h, L_PWM, 0)
    lgpio.gpio_write(h, R_PWM, 0)
    
    print("\n✅ Done! Did motors work?\n")

except KeyboardInterrupt:
    print("\nStopped")

finally:
    # Stop everything
    for pin in [L_PWM, L_D1, L_D2, R_PWM, R_D1, R_D2]:
        lgpio.gpio_write(h, pin, 0)
    lgpio.gpiochip_close(h)