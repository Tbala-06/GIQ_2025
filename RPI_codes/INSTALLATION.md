# Installation Guide - Road Marking Robot

Complete setup instructions for Raspberry Pi 5 with EV3 motor controller.

## 📋 Hardware Requirements

- **Raspberry Pi 5** (4GB+ RAM recommended)
- **EV3 Brick** (running ev3dev)
- **USB Cable** (RPi ↔ EV3 connection)
- **USB Camera** (1920x1080 capable)
- **MTi-8 RTK GPS/IMU** (connected via serial)
- **LiDAR LDS-02RR** (optional, for obstacle avoidance)
- **SD Card** (32GB+ for Raspberry Pi)
- **Power Supply** (for Raspberry Pi)
- **EV3 Battery** (rechargeable recommended)

## 🔧 Software Requirements

- **Raspberry Pi OS** (64-bit, Bookworm or later)
- **Python 3.9+** (comes with Raspberry Pi OS)
- **ev3dev** on EV3 brick

---

## 📦 Installation Steps

### 1. Setup Raspberry Pi 5

#### Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

#### Install System Dependencies
```bash
# GPIO libraries for Raspberry Pi 5
sudo apt-get install -y python3-libgpiod

# OpenCV dependencies
sudo apt-get install -y \
    python3-opencv \
    libopencv-dev \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test

# Camera support
sudo apt-get install -y v4l-utils

# Serial port support
sudo apt-get install -y python3-serial

# Network tools
sudo apt-get install -y net-tools

# SSH client (for EV3 connection)
sudo apt-get install -y openssh-client

# Optional: PS3 controller support
sudo apt-get install -y python3-pygame
```

#### Enable Required Interfaces
```bash
# Enable serial port (for MTi-8 GPS)
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# - "Would you like a login shell..." → No
# - "Would you like the serial port hardware..." → Yes

# Enable USB gadget mode (for EV3 connection)
# Already enabled by default on RPi 5
```

### 2. Install Python Dependencies

```bash
cd /path/to/GIQ_2025/RPI_codes

# Install from requirements.txt
pip3 install -r requirements.txt

# Verify installation
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import paho.mqtt.client as mqtt; print('MQTT: OK')"
python3 -c "import serial; print('Serial: OK')"
```

### 3. Setup EV3 Brick

#### Install ev3dev on EV3 (if not already done)

1. Download ev3dev from https://www.ev3dev.org/downloads/
2. Flash to microSD card using Etcher
3. Insert SD card into EV3
4. Boot EV3 from SD card

#### Install Python Libraries on EV3

```bash
# SSH to EV3 (connect via USB or WiFi first)
ssh robot@ev3dev.local
# Default password: maker

# Update package list
sudo apt-get update

# Install ev3dev2 Python library
sudo apt-get install python3-ev3dev2

# Verify installation
python3 -c "from ev3dev2.motor import LargeMotor; print('ev3dev2: OK')"
```

#### Copy EV3 Controller Script

```bash
# From your development machine
scp RPI_codes/ev3_controller.py robot@ev3dev.local:/home/robot/

# Verify it's there
ssh robot@ev3dev.local ls -l /home/robot/ev3_controller.py

# Test it
ssh robot@ev3dev.local python3 /home/robot/ev3_controller.py
# Should print "READY" - press Ctrl+C to exit
```

### 4. Configure USB Connection (RPi ↔ EV3)

#### Setup SSH Keys (for passwordless connection)

```bash
# On Raspberry Pi
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""

# Copy key to EV3 (you'll be prompted for password)
ssh-copy-id robot@ev3dev.local

# Test passwordless SSH
ssh robot@ev3dev.local echo "Connection OK"
# Should not ask for password
```

#### Configure USB Network Interface

The EV3 communication module will auto-configure this, but you can test manually:

```bash
# Connect EV3 via USB
# Wait ~10 seconds for USB network to initialize

# Check if usb0 interface exists
ip addr show usb0

# If it exists, ping common EV3 IPs
ping -c 1 169.254.144.109
ping -c 1 169.254.131.241

# If found, configure network (example)
sudo ip addr add 169.254.144.1/16 dev usb0
ping 169.254.144.109
```

### 5. Configure GPS/MTi-8

```bash
# Check serial port
ls -l /dev/serial0
# Should show: /dev/serial0 -> ttyAMA0

# Add user to dialout group (for serial access)
sudo usermod -a -G dialout $USER

# Reboot to apply group changes
sudo reboot

# After reboot, test GPS
python3 -c "from MTI_rtk8_lib import MTiParser; m=MTiParser(); m.connect(); print(m.read_latlon(timeout=5))"
```

### 6. Configure Camera

```bash
# List available cameras
ls -l /dev/video*

# Test camera with OpenCV
python3 -c "import cv2; cap=cv2.VideoCapture(0); print('Camera:', cap.isOpened()); cap.release()"

# Test camera capture
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
ret, frame = cap.read()
print(f"Captured: {ret}, Shape: {frame.shape if ret else 'N/A'}")
cap.release()
EOF
```

### 7. Setup Environment Configuration

```bash
cd /path/to/GIQ_2025/RPI_codes

# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env

# Set required values:
# ROBOT_ID=robot_001
# MQTT_BROKER=broker.hivemq.com
# MTI_SERIAL_PORT=/dev/serial0
# etc.
```

---

## ✅ Verification Tests

### Test 1: Python Dependencies
```bash
python3 << EOF
print("Testing imports...")
import cv2
import numpy
import serial
import paho.mqtt.client
import geojson
import shapely
print("✓ All imports successful")
EOF
```

### Test 2: EV3 Communication
```bash
cd RPI_codes
python3 ev3_comm.py
# Should auto-detect EV3 and run test movements
```

### Test 3: Camera System
```bash
cd RPI_codes
python3 stencil_aligner.py
# Should start camera and analyze test image
```

### Test 4: GPS/MTi-8
```bash
python3 -c "from MTI_rtk8_lib import MTiParser; m=MTiParser(); m.connect(); print('GPS:', m.read_latlon(timeout=10))"
# Should print coordinates after ~10 seconds
```

### Test 5: MQTT Communication
```bash
# Terminal 1
cd RPI_codes
python3 maintest.py --simulate

# Terminal 2
python3 send_test_deploy.py
# Should see deploy message in Terminal 1
```

### Test 6: Full System (Simulation)
```bash
cd RPI_codes
python3 robot_controller.py --simulate --deploy 1.3521 103.8198
# Should run through state machine without errors
```

---

## 🎓 Calibration

After installation, run calibration wizard:

```bash
cd RPI_codes
python3 calibration_wizard.py

# Follow interactive prompts to calibrate:
# 1. Wheel circumference
# 2. Turn factor
# 3. Camera pixels-per-cm
# 4. Paint arm
# 5. Stencil motor
```

---

## 🐛 Troubleshooting

### EV3 Connection Issues

**Problem**: Cannot detect EV3 IP
```bash
# Check USB connection
lsusb | grep LEGO

# Check usb0 interface
ip addr show usb0

# Try manual network config
sudo ip addr add 169.254.144.1/16 dev usb0
ping 169.254.144.109
```

**Problem**: SSH connection refused
```bash
# Make sure EV3 is running ev3dev
# Check network settings on EV3 screen
# Verify SSH is enabled

# Test connection
ssh -v robot@169.254.144.109
```

### GPIO Issues

**Problem**: "No GPIO library found"
```bash
# For Raspberry Pi 5
sudo apt-get install python3-libgpiod

# Verify
python3 -c "import gpiod; print('gpiod OK')"
```

**Problem**: "Permission denied" accessing GPIO
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Or run with sudo (not recommended)
sudo python3 script.py
```

### Camera Issues

**Problem**: "Failed to open camera"
```bash
# List cameras
ls -l /dev/video*

# Try different index
python3 -c "import cv2; print([cv2.VideoCapture(i).isOpened() for i in range(4)])"

# Check camera permissions
sudo chmod 666 /dev/video0
```

### GPS/Serial Issues

**Problem**: "Permission denied" on /dev/serial0
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, then test
ls -l /dev/serial0
```

**Problem**: No GPS data
```bash
# Check serial port
sudo cat /dev/serial0
# Should show binary data

# Check baud rate
stty -F /dev/serial0
# Should show 115200

# Test with MTi parser
python3 -c "from MTI_rtk8_lib import MTiParser; m=MTiParser(); m.connect(); import time; time.sleep(5); print(m.read_data())"
```

### MQTT Issues

**Problem**: Cannot connect to broker
```bash
# Test broker connectivity
ping broker.hivemq.com

# Test MQTT port
nc -zv broker.hivemq.com 1883

# Try alternative broker
# Edit ev3_config.py: MQTT_BROKER = "test.mosquitto.org"
```

---

## 📊 Post-Installation Checklist

- [ ] Raspberry Pi OS updated
- [ ] All system packages installed
- [ ] Python dependencies installed
- [ ] EV3 running ev3dev
- [ ] ev3_controller.py copied to EV3
- [ ] SSH keys configured (passwordless)
- [ ] USB network connection working
- [ ] GPS/MTi-8 connected and tested
- [ ] Camera detected and working
- [ ] MQTT connection tested
- [ ] Environment variables configured
- [ ] Calibration completed

---

## 🚀 Quick Start After Installation

```bash
# 1. Test MQTT + EV3
python3 maintest.py

# 2. In another terminal, send test deploy
python3 send_test_deploy.py

# 3. Run calibration
python3 calibration_wizard.py

# 4. Test full system
python3 robot_controller.py --simulate

# 5. Deploy for real
python3 robot_controller.py
```

---

## 📚 Additional Resources

- **Raspberry Pi Documentation**: https://www.raspberrypi.com/documentation/
- **ev3dev Documentation**: https://www.ev3dev.org/
- **OpenCV Documentation**: https://docs.opencv.org/
- **MQTT Documentation**: https://mqtt.org/

---

## 🆘 Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review log files (`robot.log`, `alignment_debug.jpg`)
3. Test components individually
4. Check hardware connections
5. Verify software versions

**Installation complete! Ready to deploy.** 🎉
