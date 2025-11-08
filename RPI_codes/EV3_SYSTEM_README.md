# EV3-Based Road Marking Robot System

Complete implementation of road marking robot using Raspberry Pi 5 as main controller and EV3 brick as motor controller.

## 📁 System Architecture

```
Raspberry Pi 5 (Main Controller)
├── robot_controller.py      - State machine & mission logic
├── ev3_comm.py              - EV3 communication (USB/SSH)
├── stencil_aligner.py       - Camera-based alignment
├── MTI_rtk8_lib.py          - GPS/IMU interface
└── ev3_config.py            - Configuration parameters

EV3 Brick (Motor Controller)
└── ev3_controller.py         - Motor control (copy to EV3)

Tools
├── calibration_wizard.py    - Interactive calibration
└── cam/testing.py           - Alignment algorithm (existing)
```

## 🚀 Quick Start

### 1. Setup EV3 Brick

```bash
# On your development machine, copy controller to EV3
scp RPI_codes/ev3_controller.py robot@<EV3_IP>:/home/robot/

# SSH to EV3 and test
ssh robot@<EV3_IP>
python3 /home/robot/ev3_controller.py
# Should print "READY"
# Ctrl+C to exit
```

### 2. Setup Raspberry Pi

```bash
cd RPI_codes

# Install dependencies
pip3 install pyserial opencv-python numpy python-dotenv

# Test EV3 connection
python3 ev3_comm.py
# Should auto-detect EV3 and run test movements

# Test camera alignment
python3 stencil_aligner.py
```

### 3. Run Calibration

```bash
# Interactive calibration wizard
python3 calibration_wizard.py

# Follow prompts to calibrate:
# 1. Wheel circumference (drive 100cm test)
# 2. Turn factor (360° rotation test)
# 3. Camera pixels-per-cm
# 4. Paint arm dispense amount
# 5. Stencil motor positions
```

### 4. Test Full System

```bash
# Simulation mode (no hardware)
python3 robot_controller.py --simulate --deploy 1.3521 103.8198

# Hardware mode with test mission
python3 robot_controller.py --deploy 1.3521 103.8198

# Hardware mode, wait for MQTT command
python3 robot_controller.py
```

## 📋 Configuration

All tunable parameters are in `ev3_config.py`:

### Physical Parameters (NEEDS CALIBRATION)
```python
WHEEL_CIRCUMFERENCE = 17.5  # cm - Measure and adjust
WHEELBASE = 20.0  # cm - Measure and adjust
WHEEL_CALIBRATION_FACTOR = 1.0  # Tune with calibration wizard
TURN_CALIBRATION_FACTOR = 1.05  # Tune with calibration wizard
```

### Camera Parameters (NEEDS CALIBRATION)
```python
CAMERA_HEIGHT_CM = 30.0  # Measure camera height above ground
PIXELS_PER_CM = 10.0  # Use calibration wizard
```

### Motor Configuration (NEEDS TESTING)
```python
PAINT_ARM_DISPENSE_DEGREES = 360  # Test and adjust
STENCIL_LOWER_DEGREES = 90  # Test and adjust
STENCIL_RAISE_DEGREES = -90  # Test and adjust
```

### Stencil Detection
```python
# Orange stencil (calibrated from testing.py)
STENCIL_HSV_LOWER = [5, 150, 150]
STENCIL_HSV_UPPER = [20, 255, 255]
```

## 🔧 Component Details

### 1. EV3 Communication (ev3_comm.py)

**Features:**
- Auto-detects EV3 IP on usb0 interface
- Configures USB network automatically
- SSH-based command/response protocol
- Encoder feedback for all movements
- Timeout handling and retry logic
- Thread-safe command sending

**API:**
```python
from ev3_comm import EV3Controller

with EV3Controller() as ev3:
    # Movement commands (returns encoder positions)
    ev3.move_forward(50, speed=50)     # 50cm forward
    ev3.move_backward(25)               # 25cm backward
    ev3.rotate(90)                      # 90° clockwise
    ev3.rotate(-45)                     # 45° counter-clockwise

    # Stencil operations
    ev3.lower_stencil()
    ev3.raise_stencil()
    ev3.dispense_paint(degrees=360)

    # Encoder operations
    left, right = ev3.get_encoder_positions()
    ev3.reset_encoders()

    # Emergency stop
    ev3.stop()
```

### 2. EV3 Motor Controller (ev3_controller.py)

Runs on EV3 brick. Receives commands via stdin (SSH pipe).

**Command Protocol:**
```
MOVE_FORWARD <distance_cm> [speed]
MOVE_BACKWARD <distance_cm> [speed]
ROTATE <degrees> [speed]
LOWER_STENCIL
RAISE_STENCIL
DISPENSE_PAINT [degrees]
GET_ENCODERS
RESET_ENCODERS
STOP
EXIT
```

**Response Format:**
```
DONE left=<encoder> right=<encoder>  - Success with encoder positions
OK                                    - Acknowledged
ERROR <message>                       - Error occurred
```

### 3. Stencil Aligner (stencil_aligner.py)

**Features:**
- Threaded camera capture (non-blocking)
- Integrates with testing.py yellow detection
- Converts pixel offsets to physical movements
- Debug visualization

**API:**
```python
from stencil_aligner import StencilAligner

with StencilAligner() as aligner:
    instruction = aligner.get_alignment_instruction()

    print(f"Aligned: {instruction.aligned}")
    print(f"Direction: {instruction.direction}")  # LEFT, RIGHT, ALIGNED, ERROR
    print(f"Distance: {instruction.distance_cm} cm")
    print(f"Message: {instruction.message}")

    # Save debug visualization
    aligner.save_debug_image("debug.jpg")
```

### 4. Robot Controller (robot_controller.py)

**State Machine:**
```
IDLE → NAVIGATING → POSITIONING → ALIGNING → PAINTING → COMPLETED → IDLE
                                       ↓
                                    ERROR
```

**State Descriptions:**
- **IDLE**: Waiting for mission deployment
- **NAVIGATING**: GPS navigation to target coordinates
- **POSITIONING**: Coarse positioning using GPS (within 50cm)
- **ALIGNING**: Fine alignment using camera + encoders
- **PAINTING**: Execute painting sequence
- **COMPLETED**: Mission complete, report success
- **ERROR**: Handle errors, emergency stop

**API:**
```python
from robot_controller import RoadMarkingRobot

with RoadMarkingRobot(simulate=False) as robot:
    # Deploy mission
    robot.deploy_mission(lat=1.3521, lon=103.8198, mission_id="test_001")

    # Main loop
    while robot.is_running():
        robot.update()
        time.sleep(0.1)
```

## 🧪 Testing Procedures

### Phase 1: Component Testing

```bash
# Test EV3 communication
python3 ev3_comm.py
# Expected: Auto-detect IP, connect, run test movements

# Test camera alignment
python3 stencil_aligner.py
# Expected: Start camera, analyze test image, save debug image

# Test GPS
python3 -c "from MTI_rtk8_lib import MTiParser; m=MTiParser(); m.connect(); print(m.read_latlon())"
```

### Phase 2: Calibration

```bash
python3 calibration_wizard.py

# Follow wizard to calibrate:
# 1. Wheel circumference - drive 100cm, measure actual
# 2. Turn factor - rotate 360°, measure actual
# 3. Camera - click two points on known-size object
# 4. Paint arm - test different rotation amounts
# 5. Stencil - test lowering/raising positions
```

### Phase 3: Integration Testing

```bash
# Test full system in simulation
python3 robot_controller.py --simulate --deploy 1.3521 103.8198 --log-level DEBUG

# Test with hardware, manual mission
python3 robot_controller.py --deploy 1.3521 103.8198

# Test alignment only (position robot over marking)
python3 -c "
from robot_controller import RoadMarkingRobot
robot = RoadMarkingRobot()
robot.start()
robot.state = robot.RobotState.ALIGNING
for i in range(10):
    robot.update()
    time.sleep(1)
robot.stop()
"
```

### Phase 4: Field Testing

1. **Setup Test Area:**
   - Place yellow road marking
   - Position orange stencil frame over marking
   - Ensure GPS has clear sky view

2. **Manual Positioning Test:**
   ```bash
   python3 robot_controller.py --log-level DEBUG
   # Manually drive robot near marking
   # Deploy mission at current location
   # Observe alignment and painting
   ```

3. **Full Autonomous Test:**
   ```bash
   python3 robot_controller.py
   # Deploy mission from remote location (10-20m away)
   # Robot should navigate, align, and paint autonomously
   ```

## 🐛 Troubleshooting

### EV3 Connection Issues

**"Could not detect EV3 IP"**
```bash
# Check USB connection
lsusb  # Should show LEGO device

# Check usb0 interface
ip addr show usb0

# Check EV3 is reachable
ping 169.254.x.x  # Try common IPs

# Manual IP configuration
sudo ip addr add 169.254.144.1/16 dev usb0
ping 169.254.144.109
```

**"SSH connection failed"**
```bash
# Test SSH manually
ssh robot@169.254.x.x

# Check SSH keys
ssh-copy-id robot@169.254.x.x
```

### Camera Issues

**"Failed to open camera"**
```bash
# Check camera device
ls -l /dev/video*

# Test camera
python3 -c "import cv2; cap=cv2.VideoCapture(0); print(cap.isOpened())"

# Try different camera index
# Edit ev3_config.py: CAMERA_INDEX = 1
```

**"No alignment detected"**
- Check camera focus and lighting
- Verify orange stencil is visible
- Verify yellow marking is present
- Adjust HSV ranges in ev3_config.py
- Save debug image to see what camera sees

### Movement Issues

**Motors don't move**
- Check EV3 battery level
- Verify motor connections (Ports A, B, C, D)
- Test motors directly on EV3
- Check encoder feedback is being received

**Movement is inaccurate**
- Run calibration wizard
- Adjust WHEEL_CALIBRATION_FACTOR
- Adjust TURN_CALIBRATION_FACTOR
- Check for wheel slippage on surface

### GPS Issues

**"No GPS fix"**
- Ensure clear view of sky
- Wait 30-60 seconds for initial lock
- Check MTi-8 connection: `ls -l /dev/serial0`
- Test GPS: `python3 -c "from MTI_rtk8_lib import MTiParser; m=MTiParser(); m.connect(); print(m.read_latlon(timeout=10))"`

## 📊 Performance Expectations

### Accuracy
- **GPS Navigation**: ±10cm with RTK (±50cm without RTK)
- **Camera Alignment**: ±2cm position, ±5° rotation
- **Movement**: ±1cm over 100cm (after calibration)
- **Rotation**: ±2° over 360° (after calibration)

### Timing
- **EV3 Connection**: 5-10 seconds
- **Camera Start**: 2-3 seconds
- **GPS Fix**: 10-60 seconds (first fix)
- **Alignment**: 10-30 seconds (up to 10 attempts)
- **Painting Sequence**: 8-10 seconds
- **Complete Mission**: 2-5 minutes (depending on distance)

## 🔒 Safety Features

- Emergency stop via MQTT topic `giq/robot/emergency_stop`
- Motor brake on error states
- Timeout protection on all states
- Maximum speed limits (configurable)
- Maximum movement distance limits
- Encoder feedback validation

## 📈 Future Enhancements

### High Priority
- [ ] MQTT integration for remote deployment
- [ ] Obstacle avoidance using LiDAR
- [ ] GPS navigation with heading correction
- [ ] Battery level monitoring
- [ ] Status reporting to web dashboard

### Medium Priority
- [ ] Multiple stencil patterns
- [ ] Adaptive speed based on GPS accuracy
- [ ] Automatic retry on alignment failure
- [ ] Data logging and mission analytics

### Low Priority
- [ ] Web-based configuration interface
- [ ] OTA (Over-The-Air) updates
- [ ] Multi-robot coordination
- [ ] Advanced path planning

## 📝 Notes

### Calibration Tips
- Perform calibration on the actual operating surface
- Recalibrate if changing batteries (voltage affects speed)
- Recalibrate if changing wheels or terrain
- Test movements after calibration before field deployment

### Operating Tips
- Always start with simulation mode to test logic
- Use debug logging for troubleshooting
- Save alignment debug images for tuning
- Monitor encoder feedback for movement accuracy
- Keep EV3 battery charged (low voltage = inaccurate movements)

### Maintenance
- Clean camera lens before operation
- Check motor connections periodically
- Verify stencil mechanism operation
- Test paint dispenser regularly
- Update calibration values as needed

## 🆘 Support

### Log Files
- `robot.log` - Main robot controller log
- `alignment_debug.jpg` - Latest alignment visualization

### Debug Mode
```bash
python3 robot_controller.py --log-level DEBUG
```

### Test Individual Components
```bash
# Test EV3
python3 ev3_comm.py

# Test Camera
python3 stencil_aligner.py

# Test GPS
python3 -c "from MTI_rtk8_lib import MTiParser; m=MTiParser(); m.connect(); print(m.read_latlon())"

# Run Calibration
python3 calibration_wizard.py
```

---

**Ready to deploy!** 🚀

Start with `python3 calibration_wizard.py` to tune your robot, then test with `python3 robot_controller.py --simulate` before field deployment.
