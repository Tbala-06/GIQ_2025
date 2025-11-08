# Keyboard Motor Controller Guide

Simple keyboard control for the robot using W/A/S/D keys.

---

## 🎮 Controls

| Key | Action | Speed |
|-----|--------|-------|
| **W** | Move Forward | Current speed setting |
| **S** | Move Backward | Current speed setting |
| **A** | Tilt Left (slow turn) | 30% (fixed) |
| **D** | Tilt Right (slow turn) | 30% (fixed) |
| **Q** | Increase Speed | +10% |
| **E** | Decrease Speed | -10% |
| **SPACE** | Stop/Brake | 0% |
| **ESC** | Exit Program | - |

---

## 🚀 Quick Start

### Installation

The keyboard controller uses the same GPIO connections as the PS3 controller.

```bash
cd RPI_codes/tests

# No additional dependencies needed!
# Uses same setup as PS3 controller

# Run the controller
python3 keyboard_motor_controller.py

# Or in simulation mode
python3 keyboard_motor_controller.py --simulate
```

---

## 🔌 Wiring

Uses the **same connections** as documented in the main README:

```
Left Motor:
├─ GPIO 12 (Pin 32) → ENA (PWM speed control)
├─ GPIO 16 (Pin 36) → IN1 (direction)
└─ GPIO 20 (Pin 38) → IN2 (direction)

Right Motor:
├─ GPIO 13 (Pin 33) → ENB (PWM speed control)
├─ GPIO 19 (Pin 35) → IN3 (direction)
└─ GPIO 26 (Pin 37) → IN4 (direction)
```

See [PS3_MOTOR_SETUP.md](PS3_MOTOR_SETUP.md) for detailed wiring diagrams.

---

## 📋 Features

### Speed Control
- **Default Speed**: 50%
- **Speed Range**: 20% - 100%
- **Adjustment**: ±10% per keypress (Q/E keys)

### Movement Modes

**1. Forward/Backward (W/S)**
- Both motors run at the same speed
- Uses current speed setting
- Adjustable with Q/E keys

**2. Tilt Left/Right (A/D)**
- Slow, controlled turning
- Fixed at 30% speed for safety
- One motor runs at 30%, other at ~10%
- Perfect for precise positioning

**3. Stop (SPACE)**
- Immediate brake
- Both motors stop

---

## 🎯 Usage Tips

### Starting Out
1. Start with default speed (50%)
2. Test forward (W) and backward (S) first
3. Try tilting (A/D) - these are intentionally slow
4. Adjust speed with Q/E as needed

### Tilting/Turning
- **A (Tilt Left)**: Left motor at 10%, right motor at 30%
- **D (Tilt Right)**: Left motor at 30%, right motor at 10%
- Slower speeds = more precise control
- Use for alignment and positioning

### Speed Management
- Press **Q** multiple times to increase speed gradually
- Press **E** to reduce speed for careful maneuvers
- Current speed shown after each adjustment
- Speed affects W/S only (not A/D tilts)

### Emergency Stop
- Press **SPACE** for immediate stop
- Press **ESC** to exit program safely
- Motors automatically stopped on exit

---

## 🔧 Advanced Usage

### Custom Speed Settings

Edit the script to change default values:

```python
DEFAULT_SPEED = 50  # Default speed percentage
TILT_SPEED = 30     # Slow speed for tilting/turning
SPEED_INCREMENT = 10  # Speed change per keypress
MAX_SPEED = 100
MIN_SPEED = 20
```

### Tilt Ratio Adjustment

To change tilt behavior (currently 30% vs 10%):

```python
def tilt_left(motors):
    motors.set_left_motor(TILT_SPEED * 0.3)   # Change 0.3 to adjust ratio
    motors.set_right_motor(TILT_SPEED)

def tilt_right(motors):
    motors.set_left_motor(TILT_SPEED)
    motors.set_right_motor(TILT_SPEED * 0.3)  # Change 0.3 to adjust ratio
```

---

## 🛡️ Safety Features

- ✅ Speed clamping (20-100%)
- ✅ Slow tilt speeds for control
- ✅ Immediate stop with SPACE
- ✅ Automatic cleanup on exit
- ✅ GPIO state restoration
- ✅ Compatible with emergency stop button

---

## 🧪 Testing

### Test in Simulation Mode

```bash
# Test without hardware
python3 keyboard_motor_controller.py --simulate

# You'll see motor commands printed:
# LEFT:  FWD  50%  RIGHT: FWD  50%
```

### Test with Hardware

```bash
# Run normally
python3 keyboard_motor_controller.py

# Expected output:
# ✅ Using gpiod (Raspberry Pi 5 native)
# ✅ GPIO initialized (gpiod) - Motors ready
# ✅ System ready! Current speed: 50%
```

### Test Sequence

1. **Press W** - Both motors forward at 50%
2. **Press SPACE** - Motors stop
3. **Press Q twice** - Speed increases to 70%
4. **Press S** - Both motors reverse at 70%
5. **Press A** - Slow left tilt
6. **Press D** - Slow right tilt
7. **Press ESC** - Clean exit

---

## 🐛 Troubleshooting

### "Could not setup keyboard input"

This means the terminal doesn't support raw input mode.

**Solution**:
```bash
# Make sure you're running directly on the Pi, not via SSH
# Or use SSH with proper terminal:
ssh -t pi@raspberrypi

# Or install screen/tmux:
sudo apt-get install screen
screen
python3 keyboard_motor_controller.py
```

### Motors Not Responding

Same troubleshooting as PS3 controller:

1. **Check power supply** (7-12V, 2A+)
2. **Verify wiring** matches GPIO pins
3. **Remove jumpers** on L298N (ENA/ENB)
4. **Test GPIO**: `python3 test_gpio_rpi5.py`

### Permission Denied (RPi 5)

```bash
# Option 1: Add user to gpio group
sudo usermod -a -G gpio $USER
# Log out and back in

# Option 2: Run with sudo
sudo python3 keyboard_motor_controller.py

# Option 3: Fix permissions
sudo chmod 666 /dev/gpiochip4
```

### Keys Not Working

- Make sure terminal window is in focus
- Don't run in background
- Press keys one at a time
- Check if terminal supports raw input

---

## 📊 Comparison with PS3 Controller

| Feature | Keyboard | PS3 Controller |
|---------|----------|----------------|
| **Ease of Use** | Simple | More complex |
| **Precision** | Binary (on/off) | Analog (variable) |
| **Speed Control** | Q/E keys | L1/L2/R1 buttons |
| **Turning** | Slow tilts | Full tank control |
| **Portability** | Any keyboard | Need PS3 controller |
| **Best For** | Testing, debugging | Full operation |

---

## 🎯 When to Use

### Use Keyboard Controller For:
- ✅ Quick testing without controller
- ✅ Simple forward/backward tests
- ✅ Slow, precise positioning
- ✅ Debugging motor connections
- ✅ Development and testing

### Use PS3 Controller For:
- ✅ Full robot operation
- ✅ Smooth, variable speed control
- ✅ Complex maneuvers
- ✅ Long operation sessions
- ✅ Precision mode and multiple speeds

---

## 🔗 Related Documentation

- [PS3_MOTOR_SETUP.md](PS3_MOTOR_SETUP.md) - PS3 controller setup
- [RPI5_UPDATES.md](RPI5_UPDATES.md) - Raspberry Pi 5 changes
- [test_gpio_rpi5.py](test_gpio_rpi5.py) - GPIO testing script
- [Main README](../../README.md) - Project overview

---

## 💡 Tips & Tricks

### For Testing
- Start with simulation mode to verify keyboard input
- Use SPACE frequently to stop between tests
- Keep hand on SPACE for quick stops

### For Precision Work
- Use E to reduce speed to minimum (20%)
- Use A/D tilts for fine adjustments
- W/S for longer movements

### For Development
- Easy to add new keys/functions
- Simple to understand and modify
- Great for learning motor control basics

---

## 🆘 Support

If you encounter issues:

1. **Test GPIO**: `python3 test_gpio_rpi5.py`
2. **Check logs**: Look for error messages
3. **Try simulation**: `python3 keyboard_motor_controller.py --simulate`
4. **Verify wiring**: Compare with PS3_MOTOR_SETUP.md
5. **Check power**: Ensure adequate motor power supply

---

**Happy Driving! 🚗⌨️**
