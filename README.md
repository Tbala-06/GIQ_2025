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
│   ├── hardware/                  # Hardware interface modules
│   │   ├── mti_parser.py         # MTi IMU/GPS sensor
│   │   ├── motor_controller.py   # L298N motor driver
│   │   ├── stencil_controller.py # Servo for stencil alignment
│   │   └── paint_dispenser.py    # Paint/sand dispenser
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
│   │   ├── ps3_motor_controller.py    # PS3 controller for manual testing
│   │   └── test_gpio_rpi5.py          # GPIO testing for RPi 5
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

### 1. **Reporting Layer** (Telegram Bot)
- **Technology**: Python, python-telegram-bot, SQLite
- **Purpose**: Citizen reporting interface
- **Features**:
  - Photo upload of damaged roads
  - GPS location sharing
  - Submission tracking
  - Inspector approval workflow
  - Web dashboard with map visualization

### 2. **Navigation Layer** (GeoJSON Processing)
- **Technology**: Python, GeoJSON, Haversine calculations
- **Purpose**: Road detection and alignment
- **Features**:
  - Find nearest road to GPS coordinates
  - Calculate perpendicular positioning
  - Road segment analysis
  - Distance calculations

### 3. **Robot Controller** (Raspberry Pi 5)
- **Technology**: Python, MQTT, gpiod, pygame
- **Purpose**: Autonomous robot operation
- **Features**:
  - GPS-guided navigation
  - Motor control (L298N driver)
  - Road alignment and positioning
  - Paint/stencil application
  - Real-time status reporting via MQTT
  - Safety monitoring (GPS signal, battery, tilt)

---

## 🚀 Quick Start

### Prerequisites

- **For Telegram Bot**:
  - Python 3.8+
  - Telegram account and bot token

- **For Robot**:
  - Raspberry Pi 5 (or Pi 4/3)
  - MTi IMU/GPS sensor
  - L298N motor driver + DC motors
  - Servo motor for stencil
  - PS3 controller (for manual testing)

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

### 2. Setup Raspberry Pi Robot

```bash
cd RPI_codes

# Install dependencies for Raspberry Pi 5
sudo apt-get update
sudo apt-get install python3-pygame python3-libgpiod
pip install -r requirements.txt

# Configure robot
cp .env.example .env
nano .env  # Configure MQTT, GPS, and GPIO settings

# Test GPIO and motors
python tests/test_gpio_rpi5.py

# Test with PS3 controller (manual control)
python tests/ps3_motor_controller.py

# Run robot controller
python main.py
```

See [RPI_codes/README.md](RPI_codes/README.md) for detailed setup.

### 3. Test System Integration

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

# 4. Robot receives deployment via MQTT
#    - Robot navigates to GPS coordinates
#    - Finds nearest road using GeoJSON
#    - Aligns perpendicular to road
#    - Applies paint marking
```

---

## 🔧 Hardware Setup (Robot)

### Required Components

| Component | Purpose | Connection |
|-----------|---------|------------|
| **Raspberry Pi 5** | Main controller | - |
| **MTi IMU/GPS** | Position & orientation | `/dev/serial0` (UART) |
| **L298N Motor Driver** | Drive 2 DC motors | GPIO 12,13,16,19,20,26 |
| **Servo Motor** | Stencil alignment | GPIO 18 (PWM) |
| **Solenoid/Pump** | Paint dispenser | GPIO 23 |
| **Emergency Stop** | Safety button | GPIO 21 (pull-up) |
| **PS3 Controller** | Manual control (testing) | USB |

### GPIO Pin Mapping

```
Raspberry Pi 5 GPIO Pins:

Left Motor:
├─ GPIO 12 (Pin 32) → ENA (PWM speed control)
├─ GPIO 16 (Pin 36) → IN1 (direction)
└─ GPIO 20 (Pin 38) → IN2 (direction)

Right Motor:
├─ GPIO 13 (Pin 33) → ENB (PWM speed control)
├─ GPIO 19 (Pin 35) → IN3 (direction)
└─ GPIO 26 (Pin 37) → IN4 (direction)

Stencil Servo:
└─ GPIO 18 (Pin 12) → PWM control

Paint Dispenser:
└─ GPIO 23 (Pin 16) → On/Off control

Emergency Stop:
└─ GPIO 21 (Pin 40) → Input (pull-up)

MTi Sensor:
├─ TX → RX (GPIO 15, Pin 10)
└─ RX → TX (GPIO 14, Pin 8)
```

See [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md) for detailed wiring diagrams.

---

## 📡 Communication Flow

### MQTT Topics

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
  "status": "moving",
  "lat": 37.7749,
  "lng": -122.4194,
  "battery": 85,
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

### Mode 1: Autonomous Operation
1. Bot receives damage report
2. Inspector approves location
3. MQTT command sent to robot
4. Robot navigates to coordinates
5. Robot finds nearest road (GeoJSON)
6. Robot aligns perpendicular to road
7. Robot applies paint marking
8. Robot reports completion

### Mode 2: Manual Control (PS3 Controller)
- **Purpose**: Testing, calibration, manual operation
- **Controls**:
  - Left stick: Forward/backward/turning
  - L1: Slow mode (30% speed)
  - L2: Medium mode (60% speed)
  - R1: Fast mode (100% speed)
  - Triangle: Emergency stop
  - Circle: Precision mode

See [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md) for full controller guide.

### Mode 3: Simulation Mode
```bash
# Test robot logic without hardware
python main.py --simulate

# Test PS3 controller without GPIO
python tests/ps3_motor_controller.py --simulate
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

### Test Individual Components

**1. Test GPIO (Raspberry Pi 5)**
```bash
cd RPI_codes/tests
python test_gpio_rpi5.py
```

**2. Test Motors with PS3 Controller**
```bash
cd RPI_codes/tests
python ps3_motor_controller.py
```

**3. Test Telegram Bot**
```bash
cd App_codes/road-painting-bot
python bot.py
# Open Telegram and send /report
```

**4. Test Web Dashboard**
```bash
cd App_codes/road-painting-bot
python web_dashboard.py
# Open http://localhost:5000
```

**5. Generate Test Data**
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
| **Robot Controller** | Python 3.8+, gpiod (RPi 5), MQTT |
| **GPIO Control** | gpiod (RPi 5), RPi.GPIO (RPi 4/3) |
| **Navigation** | MTi IMU/GPS, GeoJSON, Haversine |
| **Communication** | MQTT (Mosquitto) |
| **Manual Control** | Pygame (PS3 controller) |

### Key Features Implemented

#### ✅ Telegram Bot (Complete)
- Multi-step report submission
- Photo and GPS location handling
- Inspector approval workflow
- Status tracking and notifications
- Statistics and analytics
- CSV export
- Web dashboard with map

#### ✅ Robot Controller (Core Complete)
- Hardware interfaces (MTi, motors, servo, dispenser)
- GPIO control for RPi 5 (gpiod) and RPi 4/3 (RPi.GPIO)
- Configuration management
- Logging and error handling
- PS3 controller for manual testing

#### 🚧 In Progress
- Navigation modules (GPS navigator, road finder)
- MQTT communication
- Mission executor and state machine
- Safety monitoring system

---

## 📚 Documentation

### Main Documentation
- [README.md](README.md) - This file (project overview)
- [App_codes/road-painting-bot/README.md](App_codes/road-painting-bot/README.md) - Telegram bot setup
- [RPI_codes/README.md](RPI_codes/README.md) - Robot controller setup

### Detailed Guides
- [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md) - PS3 controller + motor setup
- [RPI_codes/tests/RPI5_UPDATES.md](RPI_codes/tests/RPI5_UPDATES.md) - Raspberry Pi 5 specific changes
- [RPI_codes/tests/RPI5_QUICK_START.txt](RPI_codes/tests/RPI5_QUICK_START.txt) - Quick reference for RPi 5
- [App_codes/road-painting-bot/DOCKER.md](App_codes/road-painting-bot/DOCKER.md) - Docker deployment guide
- [App_codes/road-painting-bot/PROJECT_SUMMARY.md](App_codes/road-painting-bot/PROJECT_SUMMARY.md) - Bot architecture

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

**Motors not moving:**
1. Check power supply (7-12V, 2A+)
2. Verify GPIO wiring matches code
3. Remove ENA/ENB jumpers on L298N
4. Test with: `python RPI_codes/tests/test_gpio_rpi5.py`

**GPS not getting fix:**
- Ensure clear view of sky
- Wait 30-60 seconds for initial lock
- Check MTi sensor connection: `ls -l /dev/serial0`

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

1. **Dual GPIO Backend** - Supports both RPi 5 (gpiod) and RPi 4/3 (RPi.GPIO) with auto-detection
2. **GeoJSON Road Alignment** - Uses OpenStreetMap data to find and align with roads
3. **PS3 Manual Override** - Test and manually control robot with game controller
4. **Integrated Reporting** - Citizens report → Inspector approves → Robot executes
5. **Real-time MQTT Updates** - Live status tracking from field to control center

---

## 📊 Project Status

| Component | Status | Progress |
|-----------|--------|----------|
| Telegram Bot | ✅ Complete | 100% |
| Web Dashboard | ✅ Complete | 100% |
| Hardware Interfaces | ✅ Complete | 100% |
| PS3 Controller | ✅ Complete | 100% |
| RPi 5 GPIO Support | ✅ Complete | 100% |
| GeoJSON Processing | ✅ Complete | 100% |
| MQTT Communication | 🚧 In Progress | 60% |
| Navigation System | 🚧 In Progress | 50% |
| Mission Executor | 🚧 In Progress | 40% |
| Safety Monitor | 🚧 In Progress | 30% |

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
- Bot Setup: [App_codes/road-painting-bot/README.md](App_codes/road-painting-bot/README.md)
- Robot Setup: [RPI_codes/README.md](RPI_codes/README.md)
- PS3 Controller: [RPI_codes/tests/PS3_MOTOR_SETUP.md](RPI_codes/tests/PS3_MOTOR_SETUP.md)
- RPi 5 Guide: [RPI_codes/tests/RPI5_UPDATES.md](RPI_codes/tests/RPI5_UPDATES.md)

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
