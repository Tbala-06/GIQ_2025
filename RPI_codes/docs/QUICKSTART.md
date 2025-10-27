# 🚀 Quick Start Guide (5 Minutes)

Get your road painting robot up and running in 5 minutes!

## 📋 What You Need

### Hardware Required
- **Raspberry Pi 4** (or newer) with Raspbian OS
- **MTi IMU/GPS sensor** (connected to UART)
- **L298N motor driver** with 2 DC motors
- **Servo motor** for stencil alignment
- **Solenoid valve or pump** for paint dispenser
- **Emergency stop button**
- **Power supply** (5V for RPi, appropriate voltage for motors)

### Pin Connections
Refer to the table below for GPIO connections:

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
| MTi Sensor | UART `/dev/serial0` | TX/RX pins |

See [README.md](../README.md) for detailed wiring diagrams.

---

## ⚡ Installation

### Step 1: Clone or Copy Project

```bash
# If using git
git clone https://github.com/yourorg/road-robot.git ~/GIQ_2025
cd ~/GIQ_2025/RPI_codes

# Or if copying via USB/SCP
cd ~/GIQ_2025/RPI_codes
```

### Step 2: Run Installation Script

```bash
# Make installer executable
chmod +x scripts/install.sh

# Run installer
./scripts/install.sh
```

The installer will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Setup environment configuration
- ✅ Add user to gpio/dialout groups
- ✅ Verify system setup

**Important:** After installation, **logout and login again** for group permissions to take effect!

---

## ⚙️ Configuration

### Step 3: Configure Robot Settings

Edit the `.env` file with your robot's settings:

```bash
nano .env
```

**Key settings to change:**

```env
# Robot Identity
ROBOT_ID=robot_001          # Unique ID for your robot
ROBOT_NAME=PaintBot Alpha   # Friendly name

# MQTT Broker (for communication with bot server)
MQTT_BROKER=your-mqtt-broker.com
MQTT_PORT=1883
MQTT_USERNAME=your_username  # Optional
MQTT_PASSWORD=your_password  # Optional

# Hardware (adjust if you used different GPIO pins)
MTI_SERIAL_PORT=/dev/serial0
```

Leave other settings at defaults for now.

### Step 4: Enable UART (If Not Already Enabled)

```bash
sudo raspi-config
```

Navigate to:
- **Interface Options** → **Serial Port**
- Login shell over serial: **NO**
- Serial port hardware: **YES**
- Reboot: **YES**

### Step 5: Download Road Data

Download OpenStreetMap road data for your location:

```bash
source venv/bin/activate

# Replace with your coordinates
python tools/download_roads.py \
  --lat 37.7749 \
  --lon -122.4194 \
  --radius 500 \
  --output data/roads.geojson
```

Get your coordinates from [Google Maps](https://maps.google.com) (right-click → copy coordinates).

---

## 🎯 First Run

### Verify Setup

```bash
source venv/bin/activate
python verify_setup.py
```

You should see all green checkmarks ✅. If not, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Test Hardware Components

```bash
source venv/bin/activate
python tools/test_hardware.py
```

Interactive menu to test:
- MTi sensor (GPS/IMU)
- Motors
- Stencil servo
- Paint dispenser

**⚠️ Warning:** Ensure robot is in a safe position before testing!

### Run in Simulation Mode

Test the controller without hardware:

```bash
source venv/bin/activate
python main.py --simulate
```

This starts the robot in simulation mode. It will:
- Connect to MQTT broker
- Wait for deploy commands
- Simulate navigation and painting

### Run with Real Hardware

Once everything is tested:

```bash
source venv/bin/activate
python main.py
```

The robot will:
1. Initialize all hardware
2. Wait for GPS fix
3. Connect to MQTT broker
4. Wait for deploy commands from bot server

---

## 📡 Sending Commands

The robot listens for MQTT commands on topic `bot/commands/deploy`:

```json
{
  "job_id": 123,
  "latitude": 37.7749,
  "longitude": -122.4194
}
```

You can test with [MQTT Explorer](http://mqtt-explorer.com/) or mosquitto_pub:

```bash
mosquitto_pub -h test.mosquitto.org \
  -t "bot/commands/deploy" \
  -m '{"job_id":1,"latitude":37.7749,"longitude":-122.4194}'
```

---

## 🔄 Auto-Start on Boot (Optional)

To run the robot automatically when Raspberry Pi boots:

```bash
# Copy service file
sudo cp systemd/road-robot.service /etc/systemd/system/

# Enable auto-start
sudo systemctl enable road-robot.service

# Start now
sudo systemctl start road-robot.service

# Check status
sudo systemctl status road-robot.service

# View logs
journalctl -u road-robot.service -f
```

To disable auto-start:

```bash
sudo systemctl stop road-robot.service
sudo systemctl disable road-robot.service
```

---

## 📊 Monitoring

### Check Logs

```bash
# If running manually
tail -f /home/pi/robot.log

# If running as systemd service
journalctl -u road-robot.service -f
```

### Check Robot Status

The robot publishes status updates to MQTT topic `robot/status`:

```json
{
  "robot_id": "robot_001",
  "status": "idle",
  "lat": 37.7749,
  "lng": -122.4194,
  "battery": 85,
  "timestamp": 1698765432.0
}
```

---

## 🛑 Emergency Stop

**Physical Button:** Press the emergency stop button (GPIO 21) to immediately halt all operations.

**Software Stop:**
```bash
# If running manually
Ctrl+C

# If running as service
sudo systemctl stop road-robot.service
```

---

## 📚 Next Steps

- **Test individual components:** Use `tools/test_hardware.py`
- **Troubleshooting issues:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Full documentation:** See [README.md](../README.md)
- **Architecture details:** See project documentation

---

## ❓ Need Help?

1. **Check logs:** `tail -f /home/pi/robot.log`
2. **Run verification:** `python verify_setup.py`
3. **Test components:** `python tools/test_hardware.py`
4. **Review troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Ready to paint some roads! 🎨🤖**
