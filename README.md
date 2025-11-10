# GIQ_2025 - Autonomous Road Painting Robot System

A complete end-to-end system for autonomous road marking and repair, featuring GPS-guided navigation, road damage reporting via Telegram, and intelligent road alignment for precise paint application.

---

## 🎯 Project Vision

An integrated robotics solution that bridges citizen reporting and automated road maintenance. Citizens report damaged roads through a Telegram bot, inspectors review and approve submissions, and autonomous robots navigate to locations using GPS and GeoJSON road data to apply paint markings accurately.

---

## 📁 Project Structure

```
GIQ_2025/
├── App_codes/                      # Backend application & Telegram bot
│   └── road-painting-bot/         # Telegram bot for damage reporting
│       ├── bot.py                 # Main bot application
│       ├── handlers/              # User & inspector command handlers
│       ├── database.py            # SQLite database operations
│       ├── web_dashboard.py       # Web dashboard with map visualization
│       └── test_data_generator.py # Generate test submissions
│
├── RPI_codes/                     # Raspberry Pi robot controller
│   ├── main.py                    # Main robot controller
│   ├── robot_controller.py        # State machine (uses EV3)
│   │
│   ├── ✅ EV3 Motor Control (PRIMARY)  # ACTIVE motor control system
│   ├── ev3_comm.py                # RPI-side EV3 communication (SSH/USB)
│   ├── ev3_controller.py          # Runs ON EV3 brick (ev3dev)
│   ├── ev3_config.py              # EV3 configuration (IP, ports, speeds)
│   │
│   ├── hardware/                  # Hardware interface modules
│   │   ├── mti_parser.py         # MTi IMU/GPS sensor
│   │   ├── stencil_controller.py # Servo for stencil alignment
│   │   ├── paint_dispenser.py    # Paint/sand dispenser
│   │   └── ⚠️ motor_controller.py # ⚠️ BACKUP: L298N (NOT used in production)
│   ├── navigation/                # GPS & road navigation
│   │   ├── gps_navigator.py      # GPS navigation logic
│   │   ├── road_finder.py        # GeoJSON road detection
│   │   └── path_planner.py       # Route planning
│   ├── communication/             # MQTT communication
│   │   ├── mqtt_client.py        # MQTT broker connection
│   │   └── status_reporter.py    # Real-time status updates
│   ├── control/                   # Robot control logic
│   │   ├── robot_state.py        # State machine
│   │   ├── mission_executor.py   # Mission coordination
│   │   └── safety_monitor.py     # Safety checks
│   ├── tests/                     # Testing tools
│   │   ├── test_gpio_rpi5.py          # Simple GPIO connection test
│   │   ├── ps3_motor_controller.py    # PS3 controller for manual testing
│   │   └── keyboard_motor_controller.py # Keyboard (W/A/S/D) control
│   └── tools/                     # Utility scripts
│       ├── test_hardware.py       # Hardware component testing
│       └── download_roads.py      # Download road data from OpenStreetMap
│
└── GeoJson/                       # Road data processing
    ├── closestline.py            # Find closest road to coordinates
    ├── closest_line_finder_test.py # Test road finding algorithms
    └── plotter.py                # Visualize roads and robot position
```

---

## 🏗️ System Architecture

### ✅ PRIMARY MOTOR CONTROL SYSTEM

```
┌─────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 5 (RPI_codes/)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  robot_controller.py (State Machine)                 │   │
│  │  - IDLE → NAVIGATING → POSITIONING → ALIGNING        │   │
│  │  - PAINTING → COMPLETED                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│              ┌─────────────┼─────────────┐                  │
│              │             │             │                   │
│         GPS/IMU        Camera       ev3_comm.py              │
│       (MTi-8 RTK)    (USB Webcam)  (SSH/USB)                │
│       /dev/serial0   Orange+Yellow    Port 22               │
└──────────────────────────────────────│──────────────────────┘
                                       │
                                SSH/USB Connection
                                       │
                          ┌────────────▼────────────┐
                          │   LEGO EV3 BRICK        │
                          │   (ev3dev OS)           │
                          │                         │
                          │  ev3_controller.py      │
                          │  - Port A: Left Motor   │
                          │  - Port B: Right Motor  │
                          │  - Port C: Paint Arm    │
                          │                         │
                          │  IP: 169.254.47.159     │
                          └─────────────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                    Left Motor    Right Motor   Paint Motor
                    (Port A)      (Port B)      (Port C)
                  Front Wheel   Front Wheel    Stencil Arm
                  Drive         Drive          Mechanism
```

### System Layers

### 1. **Reporting Layer** (Telegram Bot)
- **Technology**: Python, python-telegram-bot, SQLite
- **Purpose**: Citizen reporting interface
- **Features**:
  - Photo upload of damaged roads
  - GPS location sharing
  - Submission tracking
  - Inspector approval workflow
  - Web dashboard with map visualization
  - **Robot deployment trigger** (calls robot_controller.deploy_mission())

### 2. **Navigation Layer** (GeoJSON Processing)
- **Technology**: Python, GeoJSON, Haversine calculations
- **Purpose**: Road detection and alignment
- **Features**:
  - Find nearest road to GPS coordinates
  - Calculate road heading from LineString coordinates
  - Road segment analysis
  - Distance and bearing calculations

### 3. **Robot Controller** (Raspberry Pi 5 + EV3)
- **Technology**: Python, EV3 (ev3dev), SSH/USB communication
- **Purpose**: Autonomous robot operation
- **Features**:
  - GPS-guided navigation with IMU heading correction
  - **Motor control via EV3 brick** (PRIMARY system)
  - Road alignment using GeoJSON heading
  - Camera-based fine alignment (orange stencil + yellow marking)
  - Paint/stencil application
  - State machine (IDLE → NAVIGATING → POSITIONING → ALIGNING → PAINTING → COMPLETED)
  - Safety monitoring (GPS signal, battery, tilt)

### ⚠️ Backup System (NOT used in production)
- **L298N Motor Controller**: Direct GPIO control (hardware/motor_controller.py)
- **Status**: Exists for testing/development only
- **Used by**: test_gpio_rpi5.py, keyboard_motor_controller.py, ps3_motor_controller.py

---

## 🚀 Quick Start

### Prerequisites

- **For Telegram Bot**:
  - Python 3.8+
  - Telegram account and bot token

- **For Robot**:
  - Raspberry Pi 5 (or Pi 4/3)
  - MTi-8 RTK IMU/GPS sensor
  - **LEGO EV3 Brick with ev3dev OS** (PRIMARY motor control)
  - EV3 motors (2x drive wheels + 1x paint arm)
  - USB Webcam (camera alignment)
  - Servo motor for stencil alignment
  - L298N motor driver (backup system only)

### 1. Setup Telegram Bot

```bash
cd App_codes/road-painting-bot

# Install dependencies
pip install -r requirements.txt

# Configure bot
cp .env.example .env
nano .env  # Add your Telegram bot token

# Run bot
python bot.py

# Optional: Run web dashboard
python web_dashboard.py  # Access at http://localhost:5000
```

See [App_codes/road-painting-bot/README.md](App_codes/road-painting-bot/README.md) for detailed setup.

### 2. Setup EV3 Brick (Motor Controller)

```bash
# 1. Flash ev3dev OS to EV3 brick
# Download from: https://www.ev3dev.org/downloads/

# 2. Connect EV3 to Raspberry Pi via USB
# EV3 will get IP: 169.254.47.159

# 3. Copy EV3 controller to EV3 brick
scp RPI_codes/ev3_controller.py robot@169.254.47.159:/home/robot/

# 4. Connect motors to EV3
# - Port A: Left drive motor (front wheel)
# - Port B: Right drive motor (front wheel)
# - Port C: Paint arm motor
```

### 3. Setup Raspberry Pi Robot Controller

```bash
cd RPI_codes

# Install dependencies for Raspberry Pi 5
sudo apt-get update
sudo apt-get install python3-pygame python3-libgpiod
pip install -r requirements.txt

# Configure EV3 connection
nano ev3_config.py  # Verify EV3_IP_ADDRESS = '169.254.47.159'

# Test EV3 connection
ssh robot@169.254.47.159  # Should connect successfully

# Run full system (Telegram Bot + Robot Controller)
cd ../App_codes/road-painting-bot
python bot.py  # Starts bot + robot controller with EV3
```

**Note**: test_gpio_rpi5.py, keyboard_motor_controller.py, and ps3_motor_controller.py are for testing the BACKUP L298N system only, NOT the production EV3 system.

See [RPI_codes/README.md](RPI_codes/README.md) and [RPI_codes/EV3_SYSTEM_README.md](RPI_codes/EV3_SYSTEM_README.md) for detailed setup.

### 4. Test System Integration

```bash
# 1. Start Telegram bot (receives reports)
cd App_codes/road-painting-bot
python bot.py

# 2. Report a damaged road via Telegram
#    - Send /report to your bot
#    - Upload photo and share location

# 3. Inspect and approve (via Telegram)
#    - Send /pending to view submissions
#    - Approve submission for robot deployment

# 4. Robot receives deployment command
#    - Robot navigates to GPS coordinates using IMU heading
#    - Finds nearest road using GeoJSON
#    - Aligns to road direction
#    - Camera fine alignment (orange stencil + yellow marking)
#    - Applies paint marking via EV3 motor control
```

---

## 🔧 Hardware Setup (Robot)

### Required Components (PRIMARY System)

| Component | Purpose | Connection |
|-----------|---------|------------|
| **Raspberry Pi 5** | Main controller | - |
| **MTi-8 RTK GPS/IMU** | Position & heading | `/dev/serial0` (UART) |
| **LEGO EV3 Brick** | Motor controller | USB (SSH: 169.254.47.159) |
| **EV3 Motors (3x)** | Drive + paint arm | EV3 Ports A, B, C |
| **USB Webcam** | Camera alignment | USB |
| **Servo Motor** | Stencil alignment | GPIO 18 (PWM) |
| **Solenoid/Pump** | Paint dispenser | GPIO 23 |

### EV3 Motor Configuration

```
LEGO EV3 Brick (IP: 169.254.47.159):

Port A: Left Drive Motor
└─ Front wheel drive (mounted upside down)

Port B: Right Drive Motor
└─ Front wheel drive (mounted upside down)

Port C: Paint Arm Motor
└─ Stencil/dispenser mechanism
```

### Raspberry Pi GPIO Mapping

```
Raspberry Pi 5 GPIO Pins:

MTi-8 RTK GPS/IMU:
├─ TX → RX (GPIO 15, Pin 10)
└─ RX → TX (GPIO 14, Pin 8)

USB Webcam:
└─ USB port (camera alignment)

Stencil Servo:
└─ GPIO 18 (Pin 12) → PWM control

Paint Dispenser:
└─ GPIO 23 (Pin 16) → On/Off control
```

### ⚠️ Backup L298N System (NOT used in production)

```
L298N Motor Driver (Backup/Testing Only):

Left Motor:
├─ GPIO 12 (Pin 32) → ENA (PWM speed control)
├─ GPIO 16 (Pin 36) → IN1 (direction)
└─ GPIO 20 (Pin 38) → IN2 (direction)

Right Motor:
├─ GPIO 13 (Pin 33) → ENB (PWM speed control)
├─ GPIO 19 (Pin 35) → IN3 (direction)
└─ GPIO 26 (Pin 37) → IN4 (direction)

Emergency Stop:
└─ GPIO 21 (Pin 40) → Input (pull-up)
```

See [RPI_codes/EV3_SYSTEM_README.md](RPI_codes/EV3_SYSTEM_README.md) for EV3 setup details.

---

## 📡 Communication Flow

### Bot → Robot (Direct Function Call)

**Deployment Trigger** (Inspector approval in bot):
```python
# App_codes/road-painting-bot/handlers/inspector_handlers.py
# When inspector approves submission:

robot_controller.deploy_mission(
    target_lat=submission['latitude'],
    target_lon=submission['longitude'],
    mission_id=f"job_{submission_id}"
)
```

**Robot State Machine Updates** (Background loop at 10Hz):
```python
# App_codes/road-painting-bot/handlers/robot_handlers.py
# Background task continuously calls:

robot_controller.update()  # Runs state machine
```

### Optional: MQTT Topics (If using MQTT broker)

**1. Deployment Command** (Bot → Robot)
```
Topic: bot/commands/deploy
Payload: {
  "job_id": 123,
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

**2. Status Updates** (Robot → Bot)
```
Topic: robot/status
Payload: {
  "robot_id": "robot_001",
  "state": "NAVIGATING",
  "lat": 37.7749,
  "lng": -122.4194,
  "heading": 45.2,
  "distance_remaining": 15.3,
  "job_id": 123,
  "timestamp": 1698765432.0
}
```

**3. Job Completion** (Robot → Bot)
```
Topic: robot/job/complete
Payload: {
  "robot_id": "robot_001",
  "job_id": 123,
  "success": true,
  "message": "Mission completed successfully"
}
```

---

## 🎮 Operation Modes

### Mode 1: Autonomous Operation (PRIMARY - EV3 System)
1. Bot receives damage report
2. Inspector approves location
3. **Direct function call**: `robot_controller.deploy_mission(lat, lon)`
4. Robot state machine: IDLE → NAVIGATING → POSITIONING → ALIGNING → PAINTING → COMPLETED
5. **NAVIGATING**: GPS navigation with IMU heading correction (incremental movement)
6. **POSITIONING**: Align to road direction from GeoJSON
7. **ALIGNING**: Camera-based fine alignment (orange stencil + yellow marking)
8. **PAINTING**: EV3 motor control for paint application
9. Robot reports completion

**Run Full System**:
```bash
cd App_codes/road-painting-bot
python bot.py  # Starts bot + robot controller with EV3
```

### Mode 2: Manual Control Options (⚠️ BACKUP L298N System Only)

**Note**: These test scripts use the BACKUP L298N motor controller, NOT the production EV3 system.

#### Option A: Keyboard Control (Simple)
- **Purpose**: Quick testing of L298N system, debugging
- **System**: L298N motor driver (GPIO control)
- **Controls**:
  - **W**: Move forward
  - **S**: Move backward (reverse)
  - **A**: Tilt left (slow turn)
  - **D**: Tilt right (slow turn)
  - **Q/E**: Increase/decrease speed
  - **SPACE**: Stop
  - **ESC**: Exit

```bash
python3 tests/keyboard_motor_controller.py
```

See [RPI_codes/tests/KEYBOARD_CONTROLLER_GUIDE.md](RPI_codes/tests/KEYBOARD_CONTROLLER_GUIDE.md) for details.

#### Option B: PS3 Controller (Full Operation)
- **Purpose**: Full L298N system testing, precise control
- **System**: L298N motor driver (GPIO control)
- **Controls**:
  - Left stick: Forward/backward/turning (analog)
  - L1: Slow mode (30% speed)
  - L2: Medium mode (60% speed)
  - R1: Fast mode (100% speed)
  - Triangle: Emergency stop
  - Circle: Precision mode

```bash
python3 tests/ps3_motor_controller.py
```

See [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md) for full controller guide.

### Mode 3: Simulation Mode
```bash
# Test robot logic without hardware
cd App_codes/road-painting-bot
python bot.py  # Edit bot.py line 127: initialize_robot_controller(simulate=True)
```

---

## 🗺️ GeoJSON Road Processing

The system uses GeoJSON data to find and align with roads:

```python
# Example: Find closest road
from GeoJson.closestline import find_closest_marking

result = find_closest_marking(
    'data/roads.geojson',
    user_lat=37.7749,
    user_lon=-122.4194
)

print(f"Closest road: {result['name']}")
print(f"Distance: {result['distance']:.2f} meters")
print(f"Bearing: {result['bearing']:.1f}°")
```

### Download Road Data

```bash
cd RPI_codes
python tools/download_roads.py \
  --lat 37.7749 \
  --lon -122.4194 \
  --radius 500 \
  --output data/roads.geojson
```

---

## 🔒 Safety Features

### Robot Safety Systems
- ✅ GPS signal monitoring (minimum satellites required)
- ✅ Battery level checking (auto-return on low battery)
- ✅ Tilt detection (emergency stop on excessive tilt)
- ✅ Hardware emergency stop button
- ✅ Mission timeout (abort if exceeds time limit)
- ✅ Obstacle detection (future feature)

### Bot Security
- ✅ Inspector authorization by user ID
- ✅ Input validation and sanitization
- ✅ Rate limiting
- ✅ Secure token storage

---

## 🧪 Testing

### Production System Testing (EV3)

**Step 1: Test EV3 Connection**
```bash
# Verify EV3 is connected via USB
ping 169.254.47.159

# Test SSH connection
ssh robot@169.254.47.159

# Copy EV3 controller to EV3 brick (if not already done)
scp RPI_codes/ev3_controller.py robot@169.254.47.159:/home/robot/
```

**Step 2: Run Full System (Bot + Robot Controller)**
```bash
cd App_codes/road-painting-bot
python bot.py  # Starts bot + robot controller with EV3
```

**Step 3: Test Deployment**
1. Open Telegram bot
2. Send `/report` - upload photo and share location
3. Send `/pending` - view submission
4. Approve submission - robot will deploy automatically
5. Send `/robotstatus` - monitor robot state

### Backup System Testing (L298N - Development Only)

**Note**: These tests use the BACKUP L298N motor controller, NOT the production EV3 system.

**Step 1: Test GPIO Connections**
```bash
cd RPI_codes/tests
python3 test_gpio_rpi5.py
```
This test runs each motor forward and backward to verify L298N wiring. Takes ~8 seconds.

**Step 2: Test Manual Control (L298N)**

Option A - Keyboard Control:
```bash
cd RPI_codes/tests
python3 keyboard_motor_controller.py
# Use W/A/S/D keys to control motors
```

Option B - PS3 Controller:
```bash
cd RPI_codes/tests
python3 ps3_motor_controller.py
# Connect PS3 controller via USB first
```

### Telegram Bot Testing

**1. Test Telegram Bot**
```bash
cd App_codes/road-painting-bot
python bot.py
# Open Telegram and send /report
```

**2. Test Web Dashboard**
```bash
cd App_codes/road-painting-bot
python web_dashboard.py
# Open http://localhost:5000
```

**3. Generate Test Data**
```bash
cd App_codes/road-painting-bot
python test_data_generator.py
```

---

## 🛠️ Development

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Bot Backend** | Python 3.8+, python-telegram-bot, SQLite |
| **Web Dashboard** | Flask, Leaflet.js, OpenStreetMap |
| **Robot Controller** | Python 3.8+, RoadMarkingRobot state machine |
| **Motor Control (PRIMARY)** | EV3 brick (ev3dev), SSH/USB communication |
| **Motor Control (BACKUP)** | gpiod (RPi 5), RPi.GPIO (RPi 4/3), L298N |
| **Navigation** | MTi-8 RTK GPS/IMU, GeoJSON, Haversine |
| **Camera Alignment** | OpenCV, USB Webcam, HSV color detection |
| **Communication** | Direct function calls (optional: MQTT) |

### Key Features Implemented

#### ✅ Telegram Bot (Complete)
- Multi-step report submission
- Photo and GPS location handling
- Inspector approval workflow
- **Robot deployment trigger** (direct function call)
- Status tracking and notifications
- Statistics and analytics
- CSV export
- Web dashboard with map

#### ✅ Robot Controller (Complete)
- **State machine**: IDLE → NAVIGATING → POSITIONING → ALIGNING → PAINTING → COMPLETED
- **EV3 motor control** via ev3dev (PRIMARY system)
- **GPS navigation** with IMU heading correction
- **Road direction** calculation from GeoJSON
- **Camera alignment** (orange stencil + yellow marking)
- Hardware interfaces (MTi-8 RTK, camera, servo, dispenser)
- L298N backup system (GPIO control)
- Logging and error handling

#### ✅ Complete Features
- GPS-guided navigation to target coordinates
- Incremental movement with heading correction
- GeoJSON road heading calculation
- Camera-based fine alignment
- EV3 motor control protocol
- Background state machine loop (10Hz)
- Inspector approval → robot deployment integration

---

## 📚 Documentation

### Main Documentation
- [README.md](README.md) - This file (project overview)
- [QUICK_START.md](QUICK_START.md) - ⭐ Quick start guide (5 minutes)
- [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) - Complete file reference
- [FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md) - All 150+ functions documented
- [GPS_NAVIGATION_IMPLEMENTATION.md](GPS_NAVIGATION_IMPLEMENTATION.md) - GPS navigation guide
- [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) - Repository organization
- [ARCHITECTURE_CORRECTION.md](ARCHITECTURE_CORRECTION.md) - Architecture documentation

### Component Documentation

**Robot Controller:**
- [RPI_codes/README.md](RPI_codes/README.md) - Robot controller setup
- [RPI_codes/EV3_SYSTEM_README.md](RPI_codes/EV3_SYSTEM_README.md) - ⭐ EV3 setup guide (PRIMARY system)
- [RPI_codes/tests/motor/Documentation/PS3_MOTOR_SETUP.md](RPI_codes/tests/motor/Documentation/PS3_MOTOR_SETUP.md) - PS3 controller (backup system)

**Telegram Bot:**
- [App_codes/road-painting-bot/README.md](App_codes/road-painting-bot/README.md) - Telegram bot setup
- [App_codes/road-painting-bot/Documentation/ARCHITECTURE.md](App_codes/road-painting-bot/Documentation/ARCHITECTURE.md) - Bot architecture

---

## 🐛 Troubleshooting

### Telegram Bot Issues

**Bot doesn't respond:**
```bash
# Check bot token
cat App_codes/road-painting-bot/.env

# Check logs
tail -f App_codes/road-painting-bot/bot.log

# Restart bot
cd App_codes/road-painting-bot
python bot.py
```

**Can't access inspector mode:**
- Add your Telegram user ID to `INSPECTOR_CHAT_IDS` in `.env`
- Get your ID from [@userinfobot](https://t.me/userinfobot)
- Restart bot after changing `.env`

### Robot Issues

**GPIO permission denied (RPi 5):**
```bash
# Option 1: Add user to gpio group
sudo usermod -a -G gpio $USER
# Log out and back in

# Option 2: Run with sudo
sudo python main.py

# Option 3: Fix permissions
sudo chmod 666 /dev/gpiochip4
```

**PS3 controller not detected:**
```bash
# Check if connected
ls /dev/input/js*

# Should show: /dev/input/js0

# Check USB devices
lsusb | grep -i sony
```

**EV3 connection failed (Primary System):**
1. Check USB cable connection (RPI ↔ EV3)
2. Verify EV3 IP: `ping 169.254.47.159`
3. Update IP in `RPI_codes/ev3_config.py`:24 if changed
4. Ensure EV3 is running ev3dev OS
5. Check SSH connection: `ssh robot@169.254.47.159`
6. Verify motors connected to EV3 Ports A, B, C
7. Check motor polarity setting (MOTOR_POLARITY_INVERTED = True)

**Motors not moving (Backup L298N System):**
1. **First, test connections**: `python3 RPI_codes/tests/test_gpio_rpi5.py`
2. Check power supply (7-12V, 2A+)
3. Verify GPIO wiring matches pin diagram above
4. Remove ENA/ENB jumpers on L298N
5. Check common ground (RPI GND to L298N GND)

**GPS not getting fix:**
- Ensure clear view of sky (RTK GPS needs open area)
- Wait 1-2 minutes for RTK lock
- Check MTi-8 sensor connection: `ls -l /dev/serial0`

---

## 🎯 Use Cases

### Use Case 1: Pothole Marking
1. Citizen reports pothole via Telegram
2. Inspector approves location
3. Robot navigates to pothole
4. Robot marks outline with paint for repair crew

### Use Case 2: Road Lane Marking
1. Inspector submits coordinates for lane marking
2. Robot navigates to road
3. Robot aligns perpendicular to road direction
4. Robot applies lane marking stencil

### Use Case 3: Crosswalk Marking
1. Approved location for new crosswalk
2. Robot receives multiple waypoints
3. Robot positions at each waypoint
4. Robot applies zebra crossing pattern

---

## 🌟 Key Innovations

1. **EV3 Motor Control via ev3dev** - Uses LEGO EV3 brick as motor controller with SSH/USB communication
2. **GPS Navigation with IMU Heading** - Incremental movement with heading correction using MTi-8 RTK sensor
3. **GeoJSON Road Alignment** - Calculates road heading from LineString coordinates for positioning
4. **Camera-Based Fine Alignment** - Orange stencil + yellow marking detection for precise alignment
5. **State Machine Architecture** - IDLE → NAVIGATING → POSITIONING → ALIGNING → PAINTING → COMPLETED
6. **Direct Bot Integration** - Inspector approval directly calls robot_controller.deploy_mission()
7. **Integrated Reporting** - Citizens report → Inspector approves → Robot executes autonomously
8. **Dual Motor Systems** - Primary EV3 (production) + Backup L298N (testing)

---

## 📊 Project Status

| Component | Status | Progress |
|-----------|--------|----------|
| Telegram Bot | ✅ Complete | 100% |
| Web Dashboard | ✅ Complete | 100% |
| Inspector Approval → Robot Deployment | ✅ Complete | 100% |
| **EV3 Motor Control (PRIMARY)** | ✅ Complete | 100% |
| **GPS Navigation with IMU** | ✅ Complete | 100% |
| **GeoJSON Road Heading** | ✅ Complete | 100% |
| **Camera Alignment System** | ✅ Complete | 100% |
| **State Machine** | ✅ Complete | 100% |
| L298N Backup System | ✅ Complete | 100% |
| PS3 Controller (L298N) | ✅ Complete | 100% |
| Keyboard Controller (L298N) | ✅ Complete | 100% |
| Safety Monitor | ✅ Complete | 100% |
| Documentation | ✅ Complete | 100% |

---

## 🤝 Contributing

This is a competition robot project. Code follows:
- PEP 8 style guidelines
- Comprehensive docstrings
- Type hints where applicable
- Error handling with logging
- Modular architecture

---

## 📄 License

MIT License - Free to use and modify

---

## 🆘 Support

### Quick Links

**Getting Started:**
- Bot Setup: [App_codes/road-painting-bot/README.md](App_codes/road-painting-bot/README.md)
- Robot Setup: [RPI_codes/README.md](RPI_codes/README.md)
- RPi 5 Guide: [RPI_codes/tests/RPI5_UPDATES.md](RPI_codes/tests/RPI5_UPDATES.md)

**Robot Control:**
- Keyboard Control: [RPI_codes/tests/KEYBOARD_CONTROLLER_GUIDE.md](RPI_codes/tests/KEYBOARD_CONTROLLER_GUIDE.md)
- PS3 Controller: [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md)

### Getting Help
1. Check relevant documentation above
2. Check log files (`bot.log` or `robot.log`)
3. Run in simulation mode for debugging
4. Test individual components with test scripts

---

## 🎓 Learning Resources

- **Telegram Bots**: [python-telegram-bot docs](https://python-telegram-bot.org/)
- **Raspberry Pi GPIO**: [gpiod documentation](https://libgpiod.readthedocs.io/)
- **GeoJSON**: [GeoJSON specification](https://geojson.org/)
- **MQTT**: [MQTT.org](https://mqtt.org/)
- **OpenStreetMap**: [OSM Wiki](https://wiki.openstreetmap.org/)

---

## 🏆 Project Goals

The GIQ_2025 project aims to:
- ✅ Enable easy citizen reporting of road damage
- ✅ Streamline inspector approval workflow
- ✅ Automate road marking and repair indication
- ✅ Reduce manual labor in routine marking tasks
- ✅ Provide real-time tracking and status updates
- ✅ Create modular, maintainable robotics platform

---

**Made with 🤖 for better roads 🛣️**

**Version**: 1.0.0
**Last Updated**: 2025-01-05
