# GIQ 2025 - Quick Start Guide

**Get up and running in 5 minutes**

---

## 📖 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) | Complete file reference - what each file does |
| [FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md) | Function lookup - all 150+ functions documented |
| [GPS_NAVIGATION_IMPLEMENTATION.md](GPS_NAVIGATION_IMPLEMENTATION.md) | GPS navigation system guide |
| [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) | Cleanup guide and repository organization |

---

## 🚀 Running the System

### Option 1: Full System (Telegram Bot + Robot)

```bash
# On Raspberry Pi
cd App_codes/road-painting-bot
python bot.py
```

**What happens**:
- ✅ Telegram bot starts
- ✅ Robot controller initializes in background
- ✅ When inspector approves → robot deploys automatically
- ✅ Use `/robotstatus` to monitor progress

### Option 2: Robot Only (No Telegram Bot)

```bash
cd RPI_codes
python main.py
```

### Option 3: Test Mode (Telegram Bot with Simulation)

```bash
cd App_codes/road-painting-bot
# Edit bot.py line 127: initialize_robot_controller(simulate=True)
python bot.py
```

---

## 🧪 Testing Hardware

### Step 1: GPIO Connection Test (8 seconds)

```bash
cd RPI_codes/tests/motor
python test_gpio_rpi5.py
```

**This is the FIRST thing to run** - verifies motor wiring.

### Step 2: Keyboard Control

```bash
cd RPI_codes/tests/motor
python keyboard_motor_controller.py
```

**Controls**: W=forward, S=backward, A/D=turn, Q/E=speed

### Step 3: PS3 Controller (Full Robot Control)

```bash
cd RPI_codes/tests/motor
python ps3_motor_controller.py
```

**Controls**:
- Left stick: Forward/Backward
- Right stick: Left/Right turning
- L1/L2: Speed modes
- R1: Paint ON
- START: Emergency stop

---

## 🛠️ Repository Cleanup

### Preview Changes

```bash
python cleanup_repository.py --dry-run
```

### Execute Cleanup

```bash
python cleanup_repository.py --execute
```

**What it does**:
- Deletes `testing_backup.py` (duplicate)
- Deletes duplicate log files
- Archives experimental camera files
- Removes `__pycache__` directories

---

## 📊 System Overview

### How It Works

```
User → Telegram Bot → Inspector → Approve
                                     ↓
                         Robot Controller (State Machine)
                                     ↓
                    IDLE → NAVIGATING → POSITIONING → ALIGNING → PAINTING → COMPLETED
```

### State Machine States

| State | What Happens |
|-------|--------------|
| **IDLE** | Waiting for deployment command |
| **NAVIGATING** | GPS navigation with heading correction |
| **POSITIONING** | Align to road direction from GeoJSON |
| **ALIGNING** | Camera-based fine alignment |
| **PAINTING** | Lower stencil, dispense paint, raise |
| **COMPLETED** | Mission complete, return to IDLE |

---

## 📁 Key Files

### Production Code (Active)

| File | Purpose |
|------|---------|
| `robot_controller.py` | Main state machine - navigation + alignment + painting |
| `ev3_comm.py` | EV3 motor control via SSH |
| `cam/testing.py` | Camera alignment system (orange + yellow detection) |
| `navigation/gps_navigator.py` | GPS navigation logic |
| `handlers/inspector_handlers.py` | Approval workflow + **robot deployment trigger** |

### Configuration

| File | Purpose |
|------|---------|
| `ev3_config.py` | EV3 settings (wheel size, motor ports, speeds) |
| `App_codes/road-painting-bot/.env` | Bot token, inspector IDs |
| `RPI_codes/.env` | MQTT, GPS settings |

### Data

| File | Purpose |
|------|---------|
| `data/roads.geojson` | Road network for navigation |
| `road_painting.db` | Submission database (SQLite) |

---

## 🔧 Common Tasks

### Update EV3 IP Address

**File**: `RPI_codes/ev3_config.py` line 24

```python
EV3_IP_ADDRESS = os.getenv('EV3_IP_ADDRESS', '169.254.254.231')  # ← CHANGE HERE
```

### Change GPS Arrival Threshold

**File**: `RPI_codes/ev3_config.py` line 128

```python
GPS_ARRIVAL_THRESHOLD = 0.5  # meters - arrived when within 0.5m
```

### Add Inspector to Telegram Bot

**File**: `App_codes/road-painting-bot/.env`

```env
INSPECTOR_IDS=123456,789012  # Add Telegram user IDs (comma-separated)
```

### Download Road Data

```bash
cd RPI_codes/tools
python download_roads.py --lat 37.7749 --lon -122.4194 --radius 500 --output ../data/roads.geojson
```

---

## 🐛 Troubleshooting

### "Robot controller not available"

**Fix**: Check RPI_codes is in Python path
```bash
export PYTHONPATH="/path/to/GIQ_2025/RPI_codes:$PYTHONPATH"
```

### "No GPS fix"

**Fix**:
1. Verify MTi-8 connection: `ls /dev/serial0`
2. Check GPS antenna placement (clear sky view)
3. Wait 1-2 minutes for RTK lock

### "EV3 connection failed"

**Fix**:
1. Check USB cable connection
2. Verify EV3 IP: `ping 169.254.254.231`
3. Update IP in `ev3_config.py` if changed

### "No road found"

**Fix**:
1. Update `data/roads.geojson` with real road data
2. Use `download_roads.py` for your area
3. Increase search radius in code

### Motors not moving

**Fix**:
1. Run `test_gpio_rpi5.py` first
2. Check motor wiring (GPIO pins 12,13,16,19,20,26)
3. Verify motor polarity in `ev3_config.py`

---

## 📞 Help & Support

### Documentation

- **Main README**: [README.md](README.md)
- **File Reference**: [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)
- **Function Reference**: [FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md)

### Bot Documentation

- **Bot Setup**: [App_codes/road-painting-bot/README.md](App_codes/road-painting-bot/README.md)
- **Architecture**: [App_codes/road-painting-bot/Documentation/ARCHITECTURE.md](App_codes/road-painting-bot/Documentation/ARCHITECTURE.md)

### Hardware Documentation

- **EV3 System**: [RPI_codes/EV3_SYSTEM_README.md](RPI_codes/EV3_SYSTEM_README.md)
- **PS3 Controller**: [RPI_codes/tests/motor/Documentation/PS3_MOTOR_SETUP.md](RPI_codes/tests/motor/Documentation/PS3_MOTOR_SETUP.md)

---

## ⚡ Commands Cheat Sheet

```bash
# Start full system
cd App_codes/road-painting-bot && python bot.py

# Test GPIO (8 seconds)
cd RPI_codes/tests/motor && python test_gpio_rpi5.py

# Keyboard control
cd RPI_codes/tests/motor && python keyboard_motor_controller.py

# PS3 controller
cd RPI_codes/tests/motor && python ps3_motor_controller.py

# Clean repository
python cleanup_repository.py --dry-run
python cleanup_repository.py --execute

# Download roads
cd RPI_codes/tools && python download_roads.py --lat LAT --lon LON --radius 500

# Check robot status (in Telegram)
/robotstatus

# View pending submissions (in Telegram)
/pending
```

---

## 🎯 Next Steps

1. ✅ **Read this guide** - You're here!
2. ✅ **Test GPIO** - Run `test_gpio_rpi5.py`
3. ✅ **Configure bot** - Add your bot token to `.env`
4. ✅ **Download roads** - Get GeoJSON data for your area
5. ✅ **Run cleanup** - `python cleanup_repository.py --execute`
6. ✅ **Start system** - `python bot.py`
7. ✅ **Test workflow** - Submit report → Approve → Watch robot navigate!

---

**Ready to go!** 🚀

**Last Updated**: 2025-11-09
