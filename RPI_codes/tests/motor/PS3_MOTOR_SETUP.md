# 🎮 PS3 Controller Motor Test - Setup Guide

Complete guide for controlling 2 DC motors with PS3 controller and L298N motor driver.

---

## 📋 Hardware Requirements

### Components Needed:
- ✅ **Raspberry Pi 5** (also compatible with Pi 4/3B+)
- ✅ **L298N Motor Driver Module**
- ✅ **2x DC Motors** (6-12V recommended)
- ✅ **PS3 DualShock 3 Controller** (Sony SIXAXIS/DualShock 3)
- ✅ **Power Supply** for motors (7-12V, 2A+ recommended)
- ✅ **USB Cable** (for PS3 controller)
- ✅ **Jumper Wires** (Female-to-Female)

---

## 🔌 Wiring Connections

### **Raspberry Pi GPIO to L298N Motor Driver**

#### **Pin Mapping Table**

| Component | RPI GPIO Pin | L298N Pin | Wire Color (Suggested) | Purpose |
|-----------|--------------|-----------|------------------------|---------|
| **LEFT MOTOR** |
| PWM | GPIO 12 (Pin 32) | ENA | Yellow | Speed control |
| Direction 1 | GPIO 16 (Pin 36) | IN1 | Green | Forward |
| Direction 2 | GPIO 20 (Pin 38) | IN2 | Blue | Reverse |
| **RIGHT MOTOR** |
| PWM | GPIO 13 (Pin 33) | ENB | Yellow | Speed control |
| Direction 1 | GPIO 19 (Pin 35) | IN3 | Green | Forward |
| Direction 2 | GPIO 26 (Pin 37) | IN4 | Blue | Reverse |
| **POWER** |
| Ground | GND (Pin 6, 9, etc.) | GND | Black | Common ground |

---

### **L298N Motor Driver Connections**

```
┌──────────────────────────────────────────────────────────────┐
│                      L298N MOTOR DRIVER                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Power Input:                                                 │
│  ┌─────┐                                                      │
│  │ +12V├─── Connect to battery/power supply (+)              │
│  │ GND ├─── Connect to power supply (-) AND RPI Ground       │
│  │ +5V ├─── (Optional) Can power RPI if jumper installed     │
│  └─────┘                                                      │
│                                                               │
│  Left Motor Control (Motor A):                               │
│  ┌─────┐                                                      │
│  │ ENA ├─── GPIO 12 (PWM for speed)                          │
│  │ IN1 ├─── GPIO 16 (Direction forward)                      │
│  │ IN2 ├─── GPIO 20 (Direction reverse)                      │
│  └─────┘                                                      │
│                                                               │
│  Right Motor Control (Motor B):                              │
│  ┌─────┐                                                      │
│  │ IN3 ├─── GPIO 19 (Direction forward)                      │
│  │ IN4 ├─── GPIO 26 (Direction reverse)                      │
│  │ ENB ├─── GPIO 13 (PWM for speed)                          │
│  └─────┘                                                      │
│                                                               │
│  Motor Outputs:                                              │
│  ┌─────────┐          ┌─────────┐                            │
│  │ OUT1    ├──────────┤ LEFT    │                            │
│  │ OUT2    ├──────────┤ MOTOR   │                            │
│  └─────────┘          └─────────┘                            │
│                                                               │
│  ┌─────────┐          ┌─────────┐                            │
│  │ OUT3    ├──────────┤ RIGHT   │                            │
│  │ OUT4    ├──────────┤ MOTOR   │                            │
│  └─────────┘          └─────────┘                            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

### **Detailed Connection Diagram**

```
RASPBERRY PI 4                    L298N DRIVER                DC MOTORS
┌─────────────┐                  ┌──────────┐
│             │                  │          │               ┌─────────┐
│  GPIO 12 ◄──┼──────────────────┤ ENA      │               │         │
│  GPIO 16 ◄──┼──────────────────┤ IN1      │               │  LEFT   │
│  GPIO 20 ◄──┼──────────────────┤ IN2      ├───OUT1────────┤  MOTOR  │
│             │                  │          ├───OUT2────────┤         │
│  GPIO 13 ◄──┼──────────────────┤ ENB      │               └─────────┘
│  GPIO 19 ◄──┼──────────────────┤ IN3      │
│  GPIO 26 ◄──┼──────────────────┤ IN4      ├───OUT3────────┐
│             │                  │          ├───OUT4────────┤
│  GND ◄──────┼──────────────────┤ GND      │               │
│             │                  │          │               │ ┌─────────┐
│             │    ┌─────────────┤ +12V     │               └─┤  RIGHT  │
│             │    │             │          │                 │  MOTOR  │
│             │    │             └──────────┘                 └─────────┘
│             │    │
│    USB Port ◄────┼─── PS3 Controller
│             │    │
└─────────────┘    │
                   │
              POWER SUPPLY
              (7-12V, 2A+)
              └─── + to L298N +12V
              └─── - to L298N GND (and RPI GND)
```

---

## ⚙️ Software Setup

### **1. Install Required Packages**

```bash
# Update system
sudo apt-get update

# Install Pygame (for PS3 controller)
sudo apt-get install python3-pygame

# Or using pip
pip install pygame

# FOR RASPBERRY PI 5:
# Install gpiod (native GPIO library for RPi 5)
sudo apt-get install python3-libgpiod

# FOR RASPBERRY PI 4/3:
# Install RPi.GPIO (traditional GPIO library)
sudo apt-get install python3-rpi.gpio

# The script will auto-detect which library to use
```

---

### **2. Connect PS3 Controller**

#### **Method 1: USB Connection (Easiest)**

1. Connect PS3 controller via USB cable
2. Wait for it to be detected
3. Test with: `ls /dev/input/js*` (should show `/dev/input/js0`)

#### **Method 2: Bluetooth Connection**

```bash
# Install bluetooth tools
sudo apt-get install bluetooth bluez bluez-tools

# Pair controller
sudo bluetoothctl
> agent on
> default-agent
> scan on
# Press PS button on controller
# Find controller MAC address (e.g., 00:1B:FB:XX:XX:XX)
> pair 00:1B:FB:XX:XX:XX
> trust 00:1B:FB:XX:XX:XX
> connect 00:1B:FB:XX:XX:XX
> quit
```

---

### **3. Run the Test**

```bash
# Navigate to tests directory
cd ~/GIQ_2025/RPI_codes/tests

# Make script executable
chmod +x ps3_motor_controller.py

# Run with hardware
python3 ps3_motor_controller.py

# Or run in simulation mode (no GPIO)
python3 ps3_motor_controller.py --simulate
```

---

## 🎮 Controller Mapping

### **PS3 DualShock 3 Controls**

```
         L2          L1               R1          R2
         ┌──┐      ┌──┐             ┌──┐      ┌──┐
         └──┘      └──┘             └──┘      └──┘

              ╔══════════════════╗
              ║                  ║
              ║   PLAYSTATION    ║
              ║                  ║
              ╚══════════════════╝

    ╔═══╗                              △
    ║   ║  LEFT STICK              ▢       ○
    ║ • ║  (Movement)                  ╳
    ╚═══╝

              [SELECT]    [START]
```

### **Button Functions:**

| Button | Function | Description |
|--------|----------|-------------|
| **Left Stick Y** | Forward/Backward | Main movement control |
| **Left Stick X** | Left/Right Turn | Steering control |
| **L1** | Slow Mode | 30% max speed (precise control) |
| **L2** | Medium Mode | 60% max speed (default) |
| **R1** | Fast Mode | 100% max speed (full power) |
| **Triangle (△)** | Emergency Stop | Immediately stop all motors |
| **Cross (✕)** | Reset | Stop motors and reset to medium speed |
| **Circle (○)** | Precision Mode | Halves all inputs for fine control |
| **Start** | Exit | Safely exit program |

---

## 🚗 Driving Guide

### **Basic Movement**

1. **Forward:** Push left stick UP
2. **Backward:** Push left stick DOWN
3. **Turn Left:** Push left stick LEFT while moving
4. **Turn Right:** Push left stick RIGHT while moving
5. **Spin Left:** Push left stick LEFT (while stationary)
6. **Spin Right:** Push left stick RIGHT (while stationary)

### **Speed Modes**

- **🐌 SLOW (L1):** For careful positioning and obstacles
- **🚶 MEDIUM (L2):** For general driving (default)
- **🏃 FAST (R1):** For open areas and speed

### **Precision Mode (Circle)**

- Reduces all inputs by 50%
- Perfect for fine adjustments
- Can be combined with any speed mode
- Toggle ON/OFF with Circle button

---

## 🔧 Troubleshooting

### **PS3 Controller Not Detected**

```bash
# Check if controller is connected
ls /dev/input/js*

# If not found, check USB devices
lsusb | grep -i sony

# Test controller with jstest
sudo apt-get install joystick
jstest /dev/input/js0
```

### **Motors Not Moving**

1. **Check Power Supply:**
   - L298N requires 7-12V for motors
   - Ensure power supply can provide 2A+
   - Check voltage with multimeter

2. **Check Wiring:**
   - Verify GPIO pins match code
   - Ensure common ground (RPI GND to L298N GND)
   - Check motor connections (not loose)

3. **Check GPIO:**
   ```bash
   # Test GPIO manually
   gpio -g mode 12 pwm
   gpio -g pwm 12 512  # 50% duty cycle
   gpio -g mode 16 out
   gpio -g write 16 1
   ```

4. **Check L298N Jumpers:**
   - ENA and ENB jumpers should be **REMOVED** for PWM control
   - If jumpers are on, remove them and connect GPIO PWM pins

### **Motors Run Backward**

Swap the motor wires (OUT1 ↔ OUT2 or OUT3 ↔ OUT4)

### **Motors Weak or Stuttering**

- Increase power supply voltage (use 12V instead of 7V)
- Check battery charge
- Reduce maximum speed in code temporarily

---

## ⚙️ Calibration

### **Dead Zone Adjustment**

If joystick drifts when centered:

```python
# Edit in ps3_motor_controller.py
DEAD_ZONE = 0.20  # Increase from 0.15
```

### **Speed Adjustment**

To change speed modes:

```python
# Edit in ps3_motor_controller.py
SPEED_MODES = {
    'SLOW': 25,    # Reduce slow mode
    'MEDIUM': 50,  # Reduce medium
    'FAST': 80     # Reduce fast (safety)
}
```

### **Motor Direction Reversal**

If left/right are swapped or forward/backward are swapped:

**Option 1:** Swap motor wires physically

**Option 2:** Change code in `set_left_motor()` or `set_right_motor()`:

```python
# Reverse direction logic
if speed > 0:  # Forward becomes reverse
    GPIO.output(MOTOR_LEFT_DIR1, GPIO.LOW)   # Swap HIGH/LOW
    GPIO.output(MOTOR_LEFT_DIR2, GPIO.HIGH)
```

---

## 🔒 Safety Tips

⚠️ **IMPORTANT SAFETY GUIDELINES:**

1. **Always have emergency stop ready** (Triangle button)
2. **Test in simulation mode first** (`--simulate` flag)
3. **Start with SLOW mode** when testing new setup
4. **Use proper motor power supply** (not from RPI pins)
5. **Don't exceed motor voltage ratings**
6. **Secure all connections** before powering on
7. **Test without wheels** first (motors in air)
8. **Keep fingers away** from moving parts
9. **Have a way to physically stop** the robot
10. **Monitor motor temperature** during use

---

## 📊 Technical Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| PWM Frequency | 1000 Hz | Standard for motor control |
| Update Rate | 50 Hz | Controller polling rate |
| Dead Zone | 0.15 | Joystick drift prevention |
| Max Speed | 0-100% | PWM duty cycle |
| Response Time | ~20ms | Very responsive |

---

## 🎯 Testing Checklist

Before driving:

- [ ] All wiring connections secure
- [ ] Power supply adequate (7-12V, 2A+)
- [ ] Common ground connected
- [ ] PS3 controller detected (`ls /dev/input/js0`)
- [ ] Motors tested individually
- [ ] Emergency stop works (Triangle button)
- [ ] All buttons mapped correctly
- [ ] Safe testing area prepared

---

## 🆘 Support

If you encounter issues:

1. **Check logs** in terminal output
2. **Run in simulation mode** to test controller
3. **Test GPIO** with manual commands
4. **Verify power supply** voltage and current
5. **Check physical connections**

---

## 📚 Additional Resources

- **L298N Datasheet:** https://www.st.com/resource/en/datasheet/l298.pdf
- **RPi GPIO Pinout:** https://pinout.xyz/
- **Pygame Documentation:** https://www.pygame.org/docs/

---

**Happy Testing! 🚗💨**
