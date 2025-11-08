# Robot Integration with Telegram Bot

The Telegram bot now includes robot control commands to test EV3 motors directly from Telegram.

## 🎯 What's New

Two new commands added to the existing bot:
- `/simulate` - Test EV3 motors (forward 30cm, backward 30cm)
- `/robotstatus` - Check robot controller connection status

## 🚀 Quick Start

### 1. Run the Bot (from RPI)

```bash
cd ~/GIQ_2025/App_codes/road-painting-bot

# Option A: Hardware mode (connect to real EV3)
python bot.py

# Option B: Simulation mode (no hardware required)
# Edit bot.py line 127: simulate=True
python bot.py
```

The bot will:
- ✅ Initialize database
- ✅ Connect to EV3 controller (if available)
- ✅ Start Telegram bot with all features

### 2. Use Telegram Commands

Open your Telegram bot and try:

```
/help          - Show all commands
/simulate      - Test motors (forward 30cm + backward 30cm)
/robotstatus   - Check EV3 connection status
```

## 📋 Features

### Motor Test Sequence (`/simulate`)

When you send `/simulate`, the bot will:

1. **Move Forward 30cm** at 40% speed
   - Sends: "→ Moving forward 30cm..."
   - Reports: "✓ Forward complete" or error

2. **Wait 2 seconds**

3. **Move Backward 30cm** at 40% speed
   - Sends: "→ Moving backward 30cm..."
   - Reports: "✓ Backward complete" or error

4. **Stop motors**
   - Confirms: "✅ Motor Test Complete!"

### Status Check (`/robotstatus`)

Shows:
- **Online** - EV3 connected and ready
- **Simulation** - Running in simulation mode
- **Offline** - Controller not initialized
- **Disconnected** - Connection lost

Displays EV3 IP address when connected.

## 🔧 Configuration

### Change to Simulation Mode

Edit `App_codes/road-painting-bot/bot.py` line 127:

```python
# Hardware mode (default)
robot_available = initialize_robot_controller(simulate=False, ev3_ip=None)

# Simulation mode (no hardware)
robot_available = initialize_robot_controller(simulate=True, ev3_ip=None)

# Specify EV3 IP manually
robot_available = initialize_robot_controller(simulate=False, ev3_ip='169.254.14.120')
```

### Environment Setup

Make sure these are set:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
```

And Python path includes RPI_codes:

```python
# Already handled in robot_handlers.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RPI_codes'))
```

## 📁 File Structure

```
App_codes/road-painting-bot/
├── bot.py                          # Main bot (updated with robot handlers)
├── handlers/
│   ├── user_handlers.py           # User commands (updated help text)
│   ├── inspector_handlers.py      # Inspector commands
│   └── robot_handlers.py          # NEW: Robot control commands
└── ROBOT_INTEGRATION.md           # This file

RPI_codes/
├── ev3_comm.py                     # EV3 communication module (used by bot)
├── ev3_controller.py               # EV3 motor controller (runs on EV3)
└── ev3_config.py                   # Configuration
```

## 🔍 How It Works

1. **Bot Startup**:
   - `bot.py` imports `robot_handlers.py`
   - `initialize_robot_controller()` creates EV3Controller instance
   - Connects to EV3 via SSH (if not simulating)

2. **User Sends `/simulate`**:
   - `simulate_command()` handler receives request
   - Uses global `robot_controller` to send motor commands
   - EV3Controller communicates with EV3 via SSH
   - Real-time updates sent back to Telegram

3. **Motor Execution**:
   ```
   Telegram → Bot → robot_handlers.py → ev3_comm.py → SSH → EV3 brick → Motors
   ```

## 🐛 Troubleshooting

### "Robot Controller Not Available"

**Problem**: `/simulate` shows "Robot Controller Not Available"

**Solution**:
1. Check EV3 is connected via USB
2. Check EV3 is running ev3dev
3. Check `ev3_controller.py` is on EV3 at `/home/robot/`
4. Check SSH keys are set up
5. Or enable simulation mode

```python
# In bot.py line 127
robot_available = initialize_robot_controller(simulate=True, ev3_ip=None)
```

### "Cannot import EV3 controller"

**Problem**: Import error when starting bot

**Solution**:
1. Make sure you're in RPI environment
2. Check RPI_codes directory exists
3. Check ev3_comm.py and ev3_config.py are present

### "EV3 connection failed"

**Problem**: Hardware mode can't connect to EV3

**Solution**:
```bash
# Check USB connection
lsusb | grep LEGO

# Check network interface
ip addr show usb0

# Test SSH manually
ssh robot@169.254.14.120 echo "OK"

# Or use simulation mode
```

## 📊 Testing Scenarios

### Scenario 1: Quick Motor Test (No Hardware)

```bash
# 1. Edit bot.py to use simulation
# 2. Start bot
cd ~/GIQ_2025/App_codes/road-painting-bot
python bot.py

# 3. In Telegram
/simulate
```

Expected: Simulated movements with success messages

### Scenario 2: Real Hardware Test

```bash
# 1. Connect EV3 via USB
# 2. Make sure bot.py has simulate=False
# 3. Start bot
python bot.py

# 4. In Telegram
/robotstatus  # Should show "ONLINE"
/simulate     # Motors actually move!
```

Expected: Physical motors move forward 30cm, then backward 30cm

### Scenario 3: Check Status During Disconnection

```bash
# 1. Start bot with hardware
# 2. Check status
/robotstatus  # Shows ONLINE

# 3. Disconnect EV3 USB cable
# 4. Check status again
/robotstatus  # Shows DISCONNECTED
```

## 🎓 Integration with Full System

This bot integration validates:
- ✅ Telegram bot can control EV3 motors
- ✅ SSH communication is working
- ✅ Motor commands execute correctly
- ✅ Real-time feedback to Telegram

Next steps:
1. Add deployment commands (`/deploy <lat> <lon>`)
2. Add GPS navigation testing
3. Add camera alignment testing
4. Add full painting sequence

## 🆘 Support

If you encounter issues:
1. Check bot logs in console
2. Check `logs/bot.log` file
3. Test EV3 connection manually: `python RPI_codes/ev3_comm.py`
4. Enable simulation mode for testing without hardware

---

**Happy Testing! 🚀**
