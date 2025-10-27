# 🤖 Road Painting Robot Controller

Complete Raspberry Pi controller for autonomous road painting robot with GPS navigation, MQTT communication, and road alignment.

## 📋 Project Overview

This system receives deployment commands via MQTT, navigates to GPS coordinates, finds nearby roads using GeoJSON data, positions itself perpendicular to the road, aligns a stencil servo, and dispenses paint/sand material.

## 🎯 Key Features

- **GPS Navigation**: MTi IMU/GPS sensor integration for precise positioning
- **Road Finding**: GeoJSON-based road detection and alignment
- **MQTT Communication**: Real-time status updates and command reception
- **Safety Monitoring**: GPS signal, battery, tilt angle, emergency stop
- **Modular Architecture**: Clean separation of hardware, navigation, control, and communication
- **Simulation Mode**: Test without hardware using `--simulate` flag

## 📁 Project Structure

```
RPI_codes/
├── main.py                      # Main controller entry point
├── config.py                    # Configuration loader
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
│
├── hardware/                    # Hardware interface modules
│   ├── mti_parser.py           # MTi IMU/GPS sensor parser ✅
│   ├── motor_controller.py     # L298N motor driver ✅
│   ├── stencil_controller.py   # Servo controller ✅
│   └── paint_dispenser.py      # Paint/sand dispenser ✅
│
├── navigation/                  # GPS and road navigation
│   ├── gps_navigator.py        # GPS navigation logic
│   ├── road_finder.py          # GeoJSON road finder
│   └── path_planner.py         # Route planning
│
├── communication/               # MQTT communication
│   ├── mqtt_client.py          # MQTT broker connection
│   └── status_reporter.py      # Status reporting thread
│
├── control/                     # Robot control logic
│   ├── robot_state.py          # State machine
│   ├── mission_executor.py     # Mission coordination
│   └── safety_monitor.py       # Safety checks
│
├── utils/                       # Utility functions
│   ├── logger.py               # Logging setup ✅
│   ├── geo_utils.py            # Geodesic calculations ✅
│   └── road_geometry.py        # Road-specific geometry ✅
│
├── data/                        # Data files
│   └── roads.geojson           # Road network data
│
├── tests/                       # Unit tests
│   └── __init__.py
│
└── tools/                       # Utility scripts
    ├── test_hardware.py        # Hardware testing menu
    └── download_roads.py       # OpenStreetMap road downloader
```

## 🚀 Quick Start

### 1. Hardware Setup

**Required Components:**
- Raspberry Pi 4 (or newer)
- MTi IMU/GPS sensor (connected to `/dev/serial0`)
- L298N motor driver with 2 DC motors
- Servo motor for stencil alignment
- Solenoid valve or pump for paint/sand dispenser
- Emergency stop button

**GPIO Pin Connections:**
| Component | GPIO Pin | Purpose |
|-----------|----------|---------|
| Left Motor PWM | 12 | Speed control |
| Left Motor DIR1 | 16 | Direction 1 |
| Left Motor DIR2 | 20 | Direction 2 |
| Right Motor PWM | 13 | Speed control |
| Right Motor DIR1 | 19 | Direction 1 |
| Right Motor DIR2 | 26 | Direction 2 |
| Stencil Servo | 18 | PWM control |
| Paint Dispenser | 23 | On/Off control |
| Emergency Stop | 21 | Input with pull-up |

### 2. Software Installation

```bash
# Clone or navigate to project directory
cd RPI_codes

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Configuration

Edit `.env` file with your settings:

```env
# Robot Identity
ROBOT_ID=robot_001
ROBOT_NAME=PaintBot Alpha

# MQTT Broker
MQTT_BROKER=test.mosquitto.org  # Or your broker
MQTT_PORT=1883
MQTT_USERNAME=                   # If required
MQTT_PASSWORD=                   # If required

# Hardware Pins (adjust if different)
MTI_SERIAL_PORT=/dev/serial0
MOTOR_LEFT_PWM=12
# ... (see .env.example for all options)

# Navigation
GPS_ACCURACY_THRESHOLD=5.0
ARRIVAL_TOLERANCE_METERS=2.0

# Safety
MIN_GPS_SATELLITES=4
MIN_BATTERY_LEVEL=20

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/pi/robot.log
```

### 4. Run the Robot

```bash
# Test in simulation mode (no hardware required)
python main.py --simulate

# Run with hardware
python main.py

# Run with debug logging
python main.py --log-level DEBUG
```

## 📡 MQTT Integration

### Receive Commands

**Topic:** `bot/commands/deploy`

**Payload:**
```json
{
  "job_id": 123,
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

### Send Status Updates

**Topic:** `robot/status`

**Payload:**
```json
{
  "robot_id": "robot_001",
  "status": "moving",
  "lat": 37.7749,
  "lng": -122.4194,
  "battery": 85,
  "job_id": 123,
  "timestamp": 1698765432.0
}
```

### Send Job Completion

**Topic:** `robot/job/complete`

**Payload:**
```json
{
  "robot_id": "robot_001",
  "job_id": 123,
  "success": true,
  "message": "Mission completed successfully",
  "timestamp": 1698765432.0
}
```

## 🎯 Mission Workflow

1. **IDLE** - Wait for MQTT deploy command
2. **MOVING** - Navigate to GPS coordinates
3. **POSITIONING** - Find nearest road and align robot perpendicular
4. **PAINTING** - Align stencil servo and dispense paint
5. **COMPLETED** - Report completion via MQTT and return to IDLE

## 🔧 Testing

### Test Hardware Components

```bash
python tools/test_hardware.py
```

Interactive menu to test:
- MTi sensor (GPS and IMU)
- Motors (forward, backward, turns)
- Stencil servo (angles, sweep)
- Paint dispenser

### Download Road Data

```bash
python tools/download_roads.py --lat 37.7749 --lon -122.4194 --radius 500 --output data/roads.geojson
```

## 🛡️ Safety Features

- **GPS Signal Monitoring**: Requires minimum satellite count
- **Battery Level Check**: Stops if battery too low
- **Tilt Detection**: Emergency stop if robot tilts beyond threshold
- **Emergency Stop Button**: Hardware interrupt for immediate stop
- **Mission Timeout**: Abort if mission exceeds maximum duration

## 🐛 Troubleshooting

### MTi Sensor Not Connecting

- Check serial port: `ls -l /dev/serial*`
- Enable UART: `sudo raspi-config` → Interface Options → Serial Port
- Check baudrate matches sensor configuration

### Motors Not Moving

- Verify GPIO pin numbers in `.env`
- Check motor driver power supply
- Test individual motors using `tools/test_hardware.py`

### GPS Fix Not Acquired

- Ensure MTi has clear view of sky
- Wait longer for GPS lock (30-60 seconds)
- Check `MIN_GPS_SATELLITES` setting

### MQTT Not Connecting

- Verify broker address and port
- Check network connectivity: `ping test.mosquitto.org`
- Test with mosquitto_sub: `mosquitto_sub -h test.mosquitto.org -t robot/status`

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture overview
- **Code Documentation** - All functions have docstrings

## 🔄 Development Status

### Completed ✅
- Main controller framework
- Configuration system
- Hardware interfaces (MTi, motors, servo, dispenser)
- Utility modules (logging, geo calculations, road geometry)
- Project structure

### In Progress 🚧
- Navigation modules (GPS navigator, road finder, path planner)
- Communication modules (MQTT client, status reporter)
- Control modules (state machine, mission executor, safety monitor)
- Testing tools
- Documentation

### To Be Implemented 📝
- Complete navigation/gps_navigator.py
- Complete navigation/road_finder.py
- Complete navigation/path_planner.py
- Complete communication/mqtt_client.py
- Complete communication/status_reporter.py
- Complete control/robot_state.py
- Complete control/mission_executor.py
- Complete control/safety_monitor.py
- Complete tools/test_hardware.py
- Complete tools/download_roads.py
- Complete data/roads.geojson sample
- Unit tests in tests/
- QUICKSTART.md
- PROJECT_SUMMARY.md

## 🤝 Contributing

This is a competition robot project. All code follows:
- PEP 8 style guidelines
- Comprehensive docstrings
- Error handling with logging
- Type hints where applicable

## 📄 License

MIT License - Free to use and modify

## 🆘 Support

For issues or questions:
1. Check logs: `tail -f /home/pi/robot.log`
2. Run in simulation mode for debugging
3. Test individual components with tools/test_hardware.py
4. Check configuration in .env file

---

**Status**: Core framework complete, subsystems in development
**Version**: 1.0.0
**Last Updated**: 2024-10-27
