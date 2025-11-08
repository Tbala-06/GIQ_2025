# GIQ_2025 - Complete Testing Guide

Quick reference for testing all components of the Road Painting Robot system.

---

## 🚀 Quick Start - Testing Order

Follow these steps in order to properly test your robot:

### 1️⃣ Test GPIO Connections (5 minutes)

**ALWAYS DO THIS FIRST** before trying any other control methods.

```bash
cd RPI_codes/tests
python3 test_gpio_rpi5.py
```

**What it does:**
- Tests left motor forward/reverse
- Tests right motor forward/reverse
- Tests both motors together
- Takes ~8 seconds total

**Expected output:**
```
==================================================
SIMPLE MOTOR CONNECTION TEST
==================================================

✅ Using gpiod (Raspberry Pi 5)

Pins: Left(12,16,20) Right(13,19,26)

Press ENTER to start test...

✅ GPIO ready

→ Left motor forward... Done
→ Left motor reverse... Done
→ Right motor forward... Done
→ Right motor reverse... Done
→ Both motors forward... Done

→ Stopping all motors...

==================================================
✅ TEST COMPLETE!
==================================================

If motors moved, connections are good!
```

**If motors don't move:**
- Check power supply (7-12V, 2A+)
- Verify wiring matches GPIO pins
- Remove ENA/ENB jumpers on L298N
- Check common ground connection

---

### 2️⃣ Test Manual Control (10 minutes)

Choose **ONE** of these options:

#### Option A: Keyboard Control (Easier, No Controller Needed)

```bash
cd RPI_codes/tests
python3 keyboard_motor_controller.py
```

**Controls:**
- **W** - Forward
- **S** - Reverse
- **A** - Tilt left (slow)
- **D** - Tilt right (slow)
- **Q** - Increase speed
- **E** - Decrease speed
- **SPACE** - Stop
- **ESC** - Exit

**Best for:**
- Quick testing
- Debugging
- No PS3 controller available
- Simple movements

See: [RPI_codes/tests/KEYBOARD_CONTROLLER_GUIDE.md](RPI_codes/tests/KEYBOARD_CONTROLLER_GUIDE.md)

#### Option B: PS3 Controller (Full Featured)

```bash
cd RPI_codes/tests
python3 ps3_motor_controller.py
```

**Controls:**
- Left stick - Forward/backward/turning
- L1 - Slow mode (30%)
- L2 - Medium mode (60%)
- R1 - Fast mode (100%)
- Triangle - Emergency stop
- Circle - Precision mode

**Best for:**
- Full operation
- Precise control
- Variable speed
- Complex maneuvers

See: [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md)

---

### 3️⃣ Test Telegram Bot (15 minutes)

```bash
cd App_codes/road-painting-bot
python bot.py
```

**Test sequence:**
1. Open Telegram and find your bot
2. Send `/start` - Check welcome message
3. Send `/report` - Upload photo and location
4. Send `/status` - Check submission status
5. Send `/inspector` - View inspector dashboard (if authorized)
6. Send `/pending` - Review and approve submissions

**Optional - Test Web Dashboard:**
```bash
python web_dashboard.py
# Open browser: http://localhost:5000
```

---

### 4️⃣ Test Full System Integration (Optional)

```bash
cd RPI_codes

# Test logic without hardware
python3 main.py --simulate

# Run with actual hardware
python3 main.py
```

---

## 📊 Testing Checklist

### Before Starting
- [ ] Raspberry Pi 5 powered on
- [ ] L298N motor driver connected
- [ ] Motors connected to L298N
- [ ] Power supply (7-12V) connected
- [ ] GPIO libraries installed (`python3-libgpiod`)

### GPIO Test
- [ ] Left motor spins forward
- [ ] Left motor spins reverse
- [ ] Right motor spins forward
- [ ] Right motor spins reverse
- [ ] Both motors work together
- [ ] No error messages

### Manual Control Test
- [ ] Forward movement works (W or stick up)
- [ ] Reverse movement works (S or stick down)
- [ ] Left turning works (A or stick left)
- [ ] Right turning works (D or stick right)
- [ ] Stop/brake works (SPACE or Triangle)
- [ ] Speed adjustment works (Q/E or L1/L2/R1)

### Telegram Bot Test
- [ ] Bot responds to `/start`
- [ ] Can submit report with photo
- [ ] Can submit location
- [ ] Status tracking works
- [ ] Inspector mode accessible
- [ ] Approval workflow works

---

## 🐛 Common Issues

### GPIO Test Fails

**"No GPIO library found"**
```bash
sudo apt-get install python3-libgpiod
```

**"Permission denied"**
```bash
sudo chmod 666 /dev/gpiochip4
# Or run with sudo
sudo python3 test_gpio_rpi5.py
```

**Motors don't move but no errors**
1. Check power supply is ON
2. Check ENA/ENB jumpers are REMOVED
3. Verify wiring connections
4. Test motor power supply voltage (should be 7-12V)

### Keyboard Controller Issues

**"Could not setup keyboard input"**
- Run directly on Pi (not via SSH)
- Or use proper terminal: `ssh -t pi@raspberrypi`

**Keys not responding**
- Make sure terminal is in focus
- Don't run in background
- Try pressing keys one at a time

### PS3 Controller Issues

**"No PS3 controller found"**
```bash
# Check connection
ls /dev/input/js*
# Should show: /dev/input/js0

# Install pygame if missing
sudo apt-get install python3-pygame
```

### Telegram Bot Issues

**Bot doesn't respond**
- Check bot token in `.env` file
- Verify bot is running
- Check `bot.log` for errors

---

## 🎯 Testing Best Practices

### 1. Always Start Simple
- Test GPIO connections FIRST
- Then test keyboard control
- Finally try PS3 controller or full system

### 2. Test in Safe Environment
- Start with motors in the air (not on ground)
- Use SLOW mode first
- Keep emergency stop ready
- Test each direction separately

### 3. Document Issues
- Note which tests pass/fail
- Record error messages
- Check wiring if specific motor fails

### 4. Progressive Testing
```
GPIO Test (8 sec) → Keyboard Control (2 min) → PS3 Control (5 min) → Full System
     ✅                    ✅                      ✅                    ✅
```

---

## 📁 Test Files Reference

| File | Purpose | Duration |
|------|---------|----------|
| `test_gpio_rpi5.py` | Quick connection test | ~8 seconds |
| `keyboard_motor_controller.py` | W/A/S/D control | Interactive |
| `ps3_motor_controller.py` | PS3 gamepad control | Interactive |
| `bot.py` | Telegram bot | Continuous |
| `web_dashboard.py` | Web interface | Continuous |
| `main.py` | Full robot system | Continuous |

---

## 🔄 Testing Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    START TESTING                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  1. GPIO Connection   │
         │     Test (8 sec)      │
         └──────────┬────────────┘
                    │
             ┌──────▼──────┐
             │   Success?   │
             └──┬────────┬──┘
         No     │        │     Yes
    ┌───────────┘        └──────────┐
    │                                │
    ▼                                ▼
┌──────────────┐        ┌────────────────────────┐
│ Fix Wiring   │        │  2. Manual Control     │
│ Check Power  │        │  (Keyboard or PS3)     │
└──────────────┘        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  3. Test Telegram     │
                        │     Bot (Optional)    │
                        └──────────┬────────────┘
                                   │
                                   ▼
                        ┌───────────────────────┐
                        │  4. Full System Test  │
                        │     (Optional)        │
                        └───────────────────────┘
```

---

## 🎓 Next Steps

After successful testing:

1. **Calibration**: Fine-tune motor speeds and turning
2. **Mission Planning**: Test GPS navigation
3. **Integration**: Connect bot to robot via MQTT
4. **Field Testing**: Test in actual environment
5. **Optimization**: Adjust parameters based on performance

---

## 📞 Support

Need help? Check:
1. This testing guide
2. Component-specific guides in `RPI_codes/tests/`
3. Main README.md troubleshooting section
4. Log files (`bot.log`, `robot.log`)

---

**Happy Testing! 🚗✨**
