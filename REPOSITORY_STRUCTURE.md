# GIQ 2025 - Repository Structure & Function Reference

**Autonomous Road Painting Robot System**
Citizen reporting via Telegram → Inspector approval → Autonomous GPS-guided robot deployment

---

## 📁 Top-Level Structure

```
GIQ_2025/
├── App_codes/              # Telegram Bot & Backend Application
├── RPI_codes/              # Raspberry Pi Robot Controller
├── GeoJson/                # Road Data Processing Utilities
├── .gitignore              # Git ignore rules
├── README.md               # Project overview (682 lines)
├── TESTING_GUIDE.md        # Testing procedures
└── GPS_NAVIGATION_IMPLEMENTATION.md  # GPS navigation guide
```

---

## 🤖 App_codes - Telegram Bot System

**Purpose**: Backend for road damage reporting, inspector review, and robot deployment

**Location**: `App_codes/road-painting-bot/`

### Core Files

| File | Lines | Function |
|------|-------|----------|
| **bot.py** | 201 | Main application coordinator - registers handlers, starts bot |
| **config.py** | 89 | Configuration loader - reads .env file, validates settings |
| **database.py** | 387 | SQLite database operations - CRUD for submissions, exports |
| **road_analyzer.py** | 156 | AI-based road damage analysis from photos |
| **web_dashboard.py** | 243 | Flask web server with OpenStreetMap visualization |
| **verify_setup.py** | 127 | Validates configuration and dependencies |
| **test_data_generator.py** | 98 | Generates test submissions for development |

### Handler Modules

**Location**: `handlers/`

| File | Function |
|------|----------|
| **user_handlers.py** | User commands: `/start`, `/help`, `/report`, `/status` |
| **inspector_handlers.py** | Inspector commands: `/inspector`, `/pending`, `/approve`, `/reject`, `/stats`, `/export` |
| **robot_handlers.py** | Robot integration: `deploy_mission()`, robot state machine background loop |

### Key Features

✅ **Multi-step report submission** (photo + GPS)
✅ **Inspector approval workflow** with decision history
✅ **Robot deployment trigger** (calls `robot_controller.deploy_mission()`)
✅ **Statistics dashboard** (pending, approved, rejected counts)
✅ **CSV export** functionality
✅ **Web dashboard** with Leaflet.js map

### Database Schema

**Table**: `submissions`

```sql
- id (PRIMARY KEY)
- user_id, username, first_name, last_name
- photo_id (Telegram file ID)
- latitude, longitude
- timestamp (ISO 8601)
- status (pending/approved/rejected)
- inspector_id, inspector_username
- decision_timestamp
- rejection_reason, notes
```

### Configuration (.env)

```env
TELEGRAM_BOT_TOKEN=your_bot_token
INSPECTOR_IDS=123456,789012  # Comma-separated Telegram user IDs
LOG_LEVEL=INFO
DATABASE_PATH=road_painting.db
```

---

## 🚗 RPI_codes - Raspberry Pi Robot Controller

**Purpose**: Autonomous robot control system with GPS navigation, camera alignment, and painting

**Location**: `RPI_codes/`

---

### 1️⃣ Main Entry Points

| File | Lines | Function |
|------|-------|----------|
| **main.py** | 303 | Production entry point - orchestrates all subsystems, MQTT integration |
| **maintest.py** | 487 | Test/development entry - Telegram bot integration for manual testing |
| **robot_controller.py** | 600+ | State machine controller - IDLE→NAVIGATING→POSITIONING→ALIGNING→PAINTING→COMPLETED |

#### State Machine Flow

```
IDLE (waiting for deployment)
  ↓ deploy_mission(lat, lon)
NAVIGATING (GPS navigation to target)
  ├─ Get current GPS position
  ├─ Calculate distance & bearing
  ├─ Correct heading if off >10°
  ├─ Move forward in increments (50cm→20cm→10cm)
  └─ Arrive within 0.5m → POSITIONING
POSITIONING (align to road direction)
  ├─ Get road heading from GeoJSON
  ├─ Align robot to road direction
  └─ Switch to camera alignment → ALIGNING
ALIGNING (fine camera-based alignment)
  ├─ Detect orange stencil
  ├─ Detect yellow road marking
  ├─ Calculate lateral offset
  ├─ Move left/right to center
  └─ Aligned → PAINTING
PAINTING (execute painting operation)
  ├─ Lower stencil
  ├─ Dispense paint (3 seconds)
  ├─ Raise stencil
  └─ Complete → COMPLETED
COMPLETED
  └─ Return to IDLE
```

---

### 2️⃣ Hardware Interface Modules

**Location**: `hardware/`

| Module | GPIO/Port | Function |
|--------|-----------|----------|
| **mti_parser.py** | UART `/dev/serial0` | MTi-8 RTK GPS/IMU sensor - reads lat/lon, heading, tilt |
| **motor_controller.py** | GPIO 12,13,16,19,20,26 | L298N motor driver - PWM speed control, direction |
| **stencil_controller.py** | GPIO 18 (PWM) | Servo control - rotates stencil to align with road |
| **paint_dispenser.py** | GPIO 23 | Solenoid/pump - activates paint dispensing |

#### Motor Controller Details

**Supports**: RPi 5 (gpiod) and RPi 4/3 (RPi.GPIO)

```python
# Pin Configuration
PWM_LEFT = 12   # Left motor speed
PWM_RIGHT = 13  # Right motor speed
DIR_LEFT_FWD = 16
DIR_LEFT_BACK = 19
DIR_RIGHT_FWD = 20
DIR_RIGHT_BACK = 26
EMERGENCY_STOP = 21  # Input with pull-up
```

**Methods**:
- `move_forward(distance_cm, speed_percent)` - Move straight
- `move_backward(distance_cm, speed_percent)` - Reverse
- `turn_left(angle_degrees, speed_percent)` - Rotate left
- `turn_right(angle_degrees, speed_percent)` - Rotate right
- `stop()` - Emergency stop all motors

---

### 3️⃣ EV3 Integration Modules

**Alternative motor control using LEGO EV3 brick**

| File | Location | Function |
|------|----------|----------|
| **ev3_comm.py** | RPI | SSH/USB communication to EV3 brick, auto IP detection |
| **ev3_controller.py** | EV3 Brick | Motor control script (runs on EV3), receives commands via stdin |
| **ev3_config.py** | RPI | Configuration - wheel circumference, motor ports, calibration |
| **stencil_aligner.py** | RPI | Integration layer - camera detection + EV3 movement |

#### EV3 Configuration

```python
EV3_IP_ADDRESS = '169.254.254.231'  # USB network IP
LEFT_MOTOR_PORT = 'A'   # Port A: Left drive wheel
RIGHT_MOTOR_PORT = 'B'  # Port B: Right drive wheel
PAINT_ARM_PORT = 'C'    # Port C: Paint dispenser/arm
MOTOR_POLARITY_INVERTED = True  # Motors mounted upside down

WHEEL_CIRCUMFERENCE = 17.5  # cm
WHEELBASE = 20.0  # cm
```

#### EV3 Communication Protocol

**RPI sends commands via SSH stdin**:
```
MOVE_FORWARD:50:40     # Move forward 50cm at 40% speed
ROTATE:90:30           # Rotate 90° clockwise at 30% speed
LOWER_STENCIL          # Lower paint stencil
DISPENSE_PAINT         # Activate paint dispenser
STOP                   # Emergency stop
```

**EV3 returns responses via stdout**:
```
DONE left=1234 right=5678  # Movement complete + encoder positions
ERROR: Motor stalled       # Error message
```

---

### 4️⃣ Navigation Modules

**Location**: `navigation/`

| File | Function |
|------|----------|
| **gps_navigator.py** | GPS navigation logic - calculate bearing, distance, navigation steps |
| **road_finder.py** | GeoJSON road detection - find nearest road segment, calculate road heading |
| **path_planner.py** | Route planning - plan path from current to target location |

#### GPS Navigation Algorithm

```python
def navigate_to_target(target_lat, target_lon):
    while True:
        # 1. Get current position from MTi sensor
        current_lat, current_lon = get_gps_position()

        # 2. Calculate distance and bearing to target
        distance, bearing = haversine(current_lat, current_lon, target_lat, target_lon)

        # 3. Check if arrived
        if distance < 0.5:  # Within 0.5 meters
            return True

        # 4. Get current heading from IMU
        current_heading = get_imu_heading()  # 0-360°, 0=North

        # 5. Calculate heading error
        heading_error = normalize_angle(bearing - current_heading)

        # 6. Correct heading if needed (>10° off)
        if abs(heading_error) > 10:
            rotate(heading_error)
            continue

        # 7. Move forward in increments
        if distance > 5.0:
            move_forward(50)  # 50cm steps when far
        elif distance > 1.0:
            move_forward(20)  # 20cm steps when close
        else:
            move_forward(10)  # 10cm steps when very close
```

#### Road Direction Calculation

```python
def calculate_road_heading(target_lat, target_lon):
    # Load GeoJSON road data
    roads = load_geojson('data/roads.geojson')

    # Find nearest road segment within 50m
    nearest_segment = None
    nearest_distance = float('inf')

    for road in roads:
        for i in range(len(road.coordinates) - 1):
            pt1 = road.coordinates[i]      # [lon, lat]
            pt2 = road.coordinates[i + 1]  # [lon, lat]

            # Distance from target to segment midpoint
            mid_lat = (pt1[1] + pt2[1]) / 2
            mid_lon = (pt1[0] + pt2[0]) / 2
            dist = haversine(target_lat, target_lon, mid_lat, mid_lon)

            if dist < nearest_distance and dist <= 50:
                nearest_distance = dist
                # Calculate segment bearing (pt1 → pt2)
                nearest_segment = calculate_bearing(pt1[1], pt1[0], pt2[1], pt2[0])

    return nearest_segment  # Heading in degrees (0-360)
```

---

### 5️⃣ Camera Vision System

**Location**: `cam/`

#### 🟢 Active Production Files

| File | Lines | Status | Function |
|------|-------|--------|----------|
| **testing.py** | 512 | ✅ **ACTIVE** | Main alignment system - orange stencil + yellow marking detection |

#### ⚠️ Experimental/Backup Files

| File | Status | Function |
|------|--------|----------|
| **testing_backup.py** | ⚠️ DUPLICATE | Identical copy of testing.py - **REDUNDANT** |
| **testing_enhanced.py** | 🔬 Experimental | Enhanced version with additional debug features |
| **centerline_align.py** | 🔬 Experimental | Alternative approach using centerline extraction |
| **mask_align.py** | 🔬 Experimental | Mask-based alignment approach |
| **debug_centerline.py** | 🛠️ Debug | Centerline debugging tool |
| **debug_centerline2.py** | 🛠️ Debug | Enhanced centerline debugging |

#### 🛠️ Utility Tools

| File | Function |
|------|----------|
| **colour_test.py** | Interactive HSV color range tuning |
| **tosend.py** | Camera resolution testing (VGA to 4K) |
| **record_video.py** | Video recording utility |
| **record_video_preview.py** | Video recording with live preview |
| **mask.py** | Color mask visualization |

#### Active Alignment Algorithm (testing.py)

```python
def get_alignment_instruction(frame):
    # 1. Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2. Detect orange stencil (bounding box)
    orange_lower = [5, 150, 150]
    orange_upper = [20, 255, 255]
    orange_mask = cv2.inRange(hsv, orange_lower, orange_upper)
    orange_rect = get_largest_contour_rect(orange_mask)

    # 3. Detect yellow road marking inside orange frame
    yellow_lower = [15, 80, 80]
    yellow_upper = [35, 255, 255]
    yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)

    # 4. Divide frame into 3 zones: LEFT | CENTER | RIGHT
    width = frame.shape[1]
    left_zone = (0, width // 3)
    center_zone = (width // 3, 2 * width // 3)
    right_zone = (2 * width // 3, width)

    # 5. Count yellow pixels in each zone
    yellow_pixels_left = count_pixels_in_zone(yellow_mask, left_zone)
    yellow_pixels_center = count_pixels_in_zone(yellow_mask, center_zone)
    yellow_pixels_right = count_pixels_in_zone(yellow_mask, right_zone)

    # 6. Determine alignment
    if yellow_pixels_center > threshold:
        return AlignmentInstruction("ALIGNED", 0)
    elif yellow_pixels_left > yellow_pixels_right:
        offset = calculate_offset(yellow_pixels_left)
        return AlignmentInstruction("MOVE_RIGHT", offset)
    else:
        offset = calculate_offset(yellow_pixels_right)
        return AlignmentInstruction("MOVE_LEFT", offset)
```

**HSV Color Ranges**:
- **Orange stencil**: H[5-20], S[150-255], V[150-255]
- **Yellow marking**: H[15-35], S[80-255], V[80-255]
- **White marking**: H[0-180], S[0-199], V[98-254]

---

### 6️⃣ Communication Modules

**Location**: `communication/`

| File | Function |
|------|----------|
| **mqtt_client.py** | MQTT broker connection - subscribe to deploy commands, publish status |
| **status_reporter.py** | Real-time status reporting thread (10 Hz updates) |

#### MQTT Topics

```python
# Subscribed (receive commands)
MQTT_TOPIC_COMMANDS = "bot/commands/deploy"
MQTT_TOPIC_ESTOP = "robot/emergency_stop"

# Published (send status)
MQTT_TOPIC_STATUS = "robot/status"
MQTT_TOPIC_JOB_COMPLETE = "robot/job/complete"
```

#### MQTT Message Format

**Deploy Command** (bot → robot):
```json
{
  "job_id": 123,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "timestamp": "2025-11-09T14:30:00Z"
}
```

**Status Update** (robot → bot):
```json
{
  "state": "NAVIGATING",
  "mission_id": "job_123",
  "position": {"lat": 37.7750, "lon": -122.4195},
  "heading": 45.2,
  "distance_remaining": 15.3,
  "timestamp": "2025-11-09T14:30:15Z"
}
```

---

### 7️⃣ Control Modules

**Location**: `control/`

| File | Function |
|------|----------|
| **robot_state.py** | State machine definitions and transitions |
| **mission_executor.py** | Mission coordination - orchestrates navigation→positioning→painting |
| **safety_monitor.py** | Safety checks - GPS signal, battery, tilt, emergency stop |

#### Safety Monitor Checks

```python
def check_safety():
    # GPS signal check
    if not has_gps_fix():
        raise SafetyError("No GPS signal")

    # Battery level check
    battery_voltage = read_battery_voltage()
    if battery_voltage < 11.0:  # 12V battery
        raise SafetyError(f"Low battery: {battery_voltage}V")

    # Tilt angle check (prevent rollover)
    roll, pitch, yaw = read_imu_euler()
    if abs(roll) > 30 or abs(pitch) > 30:
        raise SafetyError(f"Excessive tilt: roll={roll}°, pitch={pitch}°")

    # Emergency stop button
    if emergency_stop_pressed():
        raise SafetyError("Emergency stop activated")
```

---

### 8️⃣ Testing Utilities

**Location**: `tests/`

#### Motor Testing

| File | Status | Function |
|------|--------|----------|
| **test_gpio_rpi5.py** | ✅ **START HERE** | Quick 8-second GPIO connection test - **RUN FIRST!** |
| **ps3_motor_controller.py** | ✅ Production | Full robot control with PS3 gamepad |
| **keyboard_motor_controller.py** | ✅ Production | Simple W/A/S/D keyboard control |
| **testingMOTOR.py** | 🛠️ Basic | Basic motor movement test |
| **testM2.py** | 🛠️ Alternative | Motor test version 2 |

#### PS3 Controller Mapping

```
Left Analog Stick:  Forward/Backward movement
Right Analog Stick: Left/Right turning
L1: Low speed mode (30%)
L2: High speed mode (70%)
R1: Paint dispenser ON
R2: Paint dispenser OFF
START: Emergency stop
```

#### LiDAR Testing

| File | Function |
|------|----------|
| **Lidartest.py** | Test obstacle detection sensor (LDS-02RR) |

---

### 9️⃣ Utility Modules

**Location**: `utils/`

| File | Function |
|------|----------|
| **logger.py** | Logging configuration - console + file output |
| **geo_utils.py** | Geodesic calculations - Haversine distance, bearing |
| **road_geometry.py** | Road-specific geometry - perpendicular distance, alignment angles |

#### Geodesic Functions

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two GPS coordinates"""
    R = 6371000  # Earth radius in meters
    # ... Haversine formula
    return distance_meters

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2 (0-360°, 0=North)"""
    # ... Forward azimuth calculation
    return bearing_degrees

def normalize_angle(angle):
    """Normalize angle to -180 to +180 range"""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle
```

---

### 🔟 Configuration & Calibration

| File | Function |
|------|----------|
| **config.py** | Main configuration loader - reads .env file |
| **ev3_config.py** | EV3-specific configuration - wheel size, motor ports, speeds |
| **calibration_wizard.py** | Interactive calibration tool - wheel circumference, turn radius, camera FOV |

#### Configuration Parameters

```python
# GPS Navigation
GPS_ARRIVAL_THRESHOLD = 0.5  # meters
HEADING_CORRECTION_THRESHOLD = 10  # degrees
ROTATION_TOLERANCE_DEG = 5.0  # degrees

# Motor Speeds
DRIVE_SPEED = 50  # % (normal driving)
PRECISION_SPEED = 25  # % (fine positioning)
TURN_SPEED = 40  # % (rotation)

# Camera
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30

# Safety
MAX_TILT_ANGLE = 30  # degrees
MIN_BATTERY_VOLTAGE = 11.0  # volts
```

---

### 1️⃣1️⃣ Tools & Utilities

| File | Function |
|------|----------|
| **tools/test_hardware.py** | Interactive hardware testing menu |
| **tools/download_roads.py** | Download OpenStreetMap road data (GeoJSON) |
| **send_test_deploy.py** | Send test deployment command via MQTT |

#### Download Roads Usage

```bash
python tools/download_roads.py \
  --lat 37.7749 \
  --lon -122.4194 \
  --radius 500 \
  --output data/roads.geojson
```

---

### 1️⃣2️⃣ Data Files

**Location**: `data/`

| File | Format | Function |
|------|--------|----------|
| **roads.geojson** | GeoJSON | Road network data with LineString geometries |

#### GeoJSON Structure

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-122.4194, 37.7749],
          [-122.4184, 37.7759],
          [-122.4174, 37.7769]
        ]
      },
      "properties": {
        "name": "Main Street",
        "highway": "primary"
      }
    }
  ]
}
```

---

## 🗺️ GeoJson - Road Data Processing

**Purpose**: Process GeoJSON road data for navigation

**Location**: `GeoJson/`

| File | Lines | Function |
|------|-------|----------|
| **closestline.py** | 103 | Find closest road segment to GPS coordinates |
| **closest_line_finder_test.py** | 85 | Unit tests for road finding algorithms |
| **plotter.py** | 142 | Visualize roads and robot position with matplotlib |

---

## 🚨 Files to Clean Up

### ❌ Delete (Redundant/Duplicate)

1. **testing_backup.py** - Identical duplicate of testing.py (512 lines)
2. **bot.log** (root) - Duplicate log file (1.7 MB) - **LARGE FILE**
3. **road_painting.db** (root) - Duplicate database (24 KB)

### 📁 Archive (Experimental/Old)

Move to `RPI_codes/cam/experimental/`:

1. **testing_enhanced.py** - Experimental enhanced version
2. **centerline_align.py** - Alternative alignment approach
3. **mask_align.py** - Mask-based alignment approach
4. **debug_centerline.py** - Debug tool 1
5. **debug_centerline2.py** - Debug tool 2

### 🗑️ Clean (Git ignore)

Add to `.gitignore`:
```gitignore
# Logs
*.log
bot.log
robot.log

# Database
*.db
road_painting.db

# Python
__pycache__/
*.pyc
*.pyo

# Environment
.env
*.env

# Test data
cam/datas_archive/*.mp4
cam/datas_archive/*.avi

# IDE
.vscode/
.idea/
```

---

## 📊 Quick Reference Statistics

- **Total Python files**: 68
- **Total lines of code**: ~15,000
- **Main directories**: 3 (App_codes, RPI_codes, GeoJson)
- **Documentation files**: 27
- **Active production files**: ~45
- **Test/utility files**: ~12
- **Experimental files**: ~10
- **Redundant files**: 3 (to delete)

---

## 🔗 Component Dependencies

```
Telegram Bot (App_codes)
    └─→ MQTT Broker
        └─→ Robot Controller (RPI_codes/main.py)
            ├─→ GPS Navigator (navigation/)
            ├─→ Camera Aligner (cam/testing.py)
            ├─→ EV3 Controller (ev3_comm.py)
            ├─→ Road Finder (GeoJson/closestline.py)
            └─→ Safety Monitor (control/safety_monitor.py)
```

---

## 🎯 Next Steps for Repository Cleanup

1. ✅ **Delete redundant files** (testing_backup.py, duplicate logs/db)
2. ✅ **Update .gitignore** (exclude logs, databases, cache)
3. ✅ **Archive experimental files** to separate folder
4. ✅ **Add file headers** with purpose comments
5. ✅ **Create this master documentation**
6. ✅ **Test all active components** to ensure no dependencies broken

---

**Last Updated**: 2025-11-09
**Status**: Repository mapped and documented ✅
