# 🔧 Troubleshooting Guide

Common issues and solutions for the Road Painting Robot Controller.

---

## 📋 General Diagnostic Steps

Before diving into specific issues, try these general diagnostic steps:

### 1. Run Setup Verification

```bash
source venv/bin/activate
python verify_setup.py
```

This checks:
- ✅ Hardware (GPIO availability)
- ✅ Serial port access
- ✅ Dependencies installed
- ✅ Configuration validity
- ✅ Required files exist

### 2. Check Logs

```bash
# If running manually
tail -f /home/pi/robot.log

# If running as systemd service
journalctl -u road-robot.service -f

# View recent errors only
journalctl -u road-robot.service -p err -n 50
```

### 3. Test Individual Components

```bash
source venv/bin/activate
python tools/test_hardware.py
```

Use the interactive menu to test each hardware component separately.

---

## 🔌 MTi Sensor Issues

### Problem: MTi Sensor Not Connecting

**Symptoms:**
- `Failed to connect to MTi sensor`
- `Serial port /dev/serial0 not found`
- `Permission denied: /dev/serial0`

**Solutions:**

#### 1. Check Serial Port Exists

```bash
ls -l /dev/serial*
```

If `/dev/serial0` doesn't exist:

```bash
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# Login shell: NO
# Serial hardware: YES
# Reboot when prompted
```

#### 2. Check Permissions

```bash
ls -l /dev/serial0
# Should show: crw-rw---- 1 root dialout

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login for changes to take effect
```

#### 3. Check UART Configuration

Edit `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

Ensure these lines are present:

```
enable_uart=1
dtoverlay=disable-bt
```

Then reboot:

```bash
sudo reboot
```

#### 4. Verify Baudrate

The MTi sensor expects 115200 baud by default. Check your `.env` file:

```env
MTI_BAUDRATE=115200
```

#### 5. Test Serial Port Directly

```bash
# Install minicom if not available
sudo apt-get install minicom

# Test serial port
minicom -D /dev/serial0 -b 115200
```

Press `Ctrl+A` then `X` to exit. If you see data, the port works.

### Problem: GPS Fix Not Acquired

**Symptoms:**
- `Waiting for GPS fix...`
- `GPS: No Fix, Satellites: 0/4`

**Solutions:**

1. **Ensure Clear Sky View:** MTi sensor needs clear view of sky. Move away from buildings, trees, and indoors.

2. **Wait Longer:** First GPS fix can take 30-60 seconds. Be patient.

3. **Check Antenna:** Ensure GPS antenna is properly connected to MTi module.

4. **Lower Satellite Requirement:** Edit `.env`:

   ```env
   MIN_GPS_SATELLITES=3  # Reduce from 4 to 3
   ```

5. **Check MTi Data:**

   ```bash
   source venv/bin/activate
   python -c "
   from hardware.mti_parser import MTiParser
   mti = MTiParser('/dev/serial0', 115200)
   mti.connect()
   for i in range(10):
       data = mti.read_data(timeout=2.0)
       if data:
           print(data.get_gps_info())
       import time
       time.sleep(1)
   "
   ```

---

## ⚙️ Motor Issues

### Problem: Motors Not Moving

**Symptoms:**
- Motors don't respond
- `Motor test failed`
- No sound from motors

**Solutions:**

#### 1. Check GPIO Permissions

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login again
```

#### 2. Verify Pin Numbers

Check your `.env` file matches your wiring:

```env
MOTOR_LEFT_PWM=12
MOTOR_LEFT_DIR1=16
MOTOR_LEFT_DIR2=20
MOTOR_RIGHT_PWM=13
MOTOR_RIGHT_DIR1=19
MOTOR_RIGHT_DIR2=26
```

Pin numbers use **BCM numbering**, not physical pin numbers.

#### 3. Check Power Supply

- L298N motor driver needs **separate power** (7-12V)
- Ensure motor power supply is connected
- Check power supply voltage and current rating

#### 4. Test Motor Driver

```bash
# Test GPIO pins manually
gpio -g mode 12 pwm
gpio -g pwm 12 512  # 50% duty cycle
gpio -g mode 16 out
gpio -g write 16 1
```

If motors work now, GPIO is fine. Issue is in software.

#### 5. Check Wiring

- Verify all connections are tight
- Check for shorts or loose wires
- Ensure motor driver enable pins are high

#### 6. Test in Simulation Mode

```bash
python main.py --simulate
```

If this works, hardware issue is confirmed.

---

## 📡 MQTT Connection Issues

### Problem: MQTT Not Connecting

**Symptoms:**
- `Failed to connect to MQTT broker`
- `Connection timeout`
- `Connection refused`

**Solutions:**

#### 1. Check Network Connectivity

```bash
# Ping MQTT broker
ping test.mosquitto.org

# Check if port 1883 is accessible
telnet test.mosquitto.org 1883
```

#### 2. Verify MQTT Credentials

Edit `.env` file:

```env
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883
MQTT_USERNAME=  # Leave empty for anonymous
MQTT_PASSWORD=  # Leave empty for anonymous
```

#### 3. Test MQTT Connection Manually

```bash
# Install mosquitto clients if not available
sudo apt-get install mosquitto-clients

# Subscribe to status topic
mosquitto_sub -h test.mosquitto.org -t "robot/status" -v

# Publish test message (in another terminal)
mosquitto_pub -h test.mosquitto.org -t "robot/status" -m "test"
```

If this works, MQTT broker is accessible.

#### 4. Check Firewall

```bash
# Check if firewall is blocking
sudo iptables -L

# Temporarily disable firewall for testing
sudo iptables -F  # Use with caution!
```

#### 5. Try Alternative Broker

Edit `.env` to use local broker:

```env
MQTT_BROKER=localhost
```

Install local broker:

```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### Problem: Not Receiving Commands

**Symptoms:**
- Robot connects to MQTT but doesn't respond to commands
- No errors in logs

**Solutions:**

1. **Check Topic Names:** Ensure `.env` matches bot server topics:

   ```env
   MQTT_TOPIC_COMMANDS=bot/commands/deploy
   ```

2. **Test Command Manually:**

   ```bash
   mosquitto_pub -h test.mosquitto.org \
     -t "bot/commands/deploy" \
     -m '{"job_id":123,"latitude":37.7749,"longitude":-122.4194}'
   ```

3. **Check JSON Format:** Ensure JSON is valid and contains required fields.

---

## 🗺️ Navigation and Road Finding Issues

### Problem: No Road Found

**Symptoms:**
- `No road found nearby`
- `Mission aborted: No road found`

**Solutions:**

1. **Check GeoJSON File Exists:**

   ```bash
   ls -l data/roads.geojson
   ```

2. **Download Road Data:**

   ```bash
   source venv/bin/activate
   python tools/download_roads.py \
     --lat YOUR_LAT --lon YOUR_LON \
     --radius 500 \
     --output data/roads.geojson
   ```

3. **Validate GeoJSON:**

   ```bash
   python tools/download_roads.py --validate data/roads.geojson
   ```

4. **Increase Search Radius:** Edit `.env`:

   ```env
   MAX_ROAD_SEARCH_DISTANCE=100.0  # Increase from 50
   ```

5. **Check Coordinates:** Ensure target coordinates are within GeoJSON data area.

### Problem: Robot Won't Navigate

**Symptoms:**
- `Navigation failed`
- Robot doesn't move toward target

**Solutions:**

1. **Check GPS Fix:** Robot needs valid GPS before navigating.

2. **Increase Tolerance:** Edit `.env`:

   ```env
   ARRIVAL_TOLERANCE_METERS=5.0  # Increase from 2.0
   ```

3. **Test Motors:** Use `tools/test_hardware.py` to verify motors work.

4. **Check Heading:** IMU must provide valid heading data.

---

## 🔒 Permission Issues

### Problem: Permission Denied Errors

**Symptoms:**
- `Permission denied: /dev/serial0`
- `Permission denied: /dev/gpiomem`
- `RuntimeError: No access to /dev/mem`

**Solutions:**

#### 1. Add User to Required Groups

```bash
sudo usermod -a -G gpio,dialout,i2c,spi $USER

# Logout and login again
```

#### 2. Verify Group Membership

```bash
groups
# Should show: pi gpio dialout i2c spi ...
```

#### 3. Check File Permissions

```bash
ls -l /dev/serial0
ls -l /dev/gpiomem

# Fix permissions if needed
sudo chmod a+rw /dev/gpiomem
```

#### 4. Run Without GPIO for Testing

```bash
python main.py --simulate
```

---

## 🔋 Power and Safety Issues

### Problem: Robot Stops Unexpectedly

**Symptoms:**
- `Safety check failed`
- `Emergency stop triggered`
- Robot stops during mission

**Solutions:**

#### 1. Check Battery Level

The robot monitors battery level. Edit `.env` to lower threshold:

```env
MIN_BATTERY_LEVEL=10  # Reduce from 20
```

#### 2. Check Emergency Stop Button

Verify button is not stuck or shorted:

```bash
# Check GPIO 21 state
gpio -g read 21
# Should be 1 (HIGH) when not pressed
```

#### 3. Check Tilt Angle

Robot stops if tilted too much. Edit `.env`:

```env
MAX_TILT_ANGLE=45.0  # Increase from 30
```

#### 4. Disable Safety Checks (Testing Only)

**⚠️ Use with caution!** Only for debugging:

Edit `control/safety_monitor.py` to bypass checks in simulation mode.

---

## 🐛 Debugging Tips

### Enable Debug Logging

```bash
python main.py --log-level DEBUG
```

This provides verbose output for troubleshooting.

### Check System Resources

```bash
# Check CPU and memory
top

# Check disk space
df -h

# Check USB devices
lsusb

# Check GPIO status
gpio readall
```

### Restart Services

```bash
# If running as service
sudo systemctl restart road-robot.service

# View startup messages
journalctl -u road-robot.service -b
```

### Reset to Clean State

```bash
# Stop robot
sudo systemctl stop road-robot.service

# Clear logs
sudo rm /home/pi/robot.log

# Reset configuration
cp .env.example .env
nano .env

# Re-run verification
python verify_setup.py
```

---

## 🆘 Getting Additional Help

If you're still having issues:

### 1. Collect Diagnostic Information

```bash
# System info
uname -a
cat /proc/device-tree/model

# Python version
python3 --version

# Installed packages
pip list

# Configuration
cat .env

# Recent logs
tail -n 100 /home/pi/robot.log
```

### 2. Run Full Diagnostics

```bash
# Run verification
python verify_setup.py > diagnostics.txt 2>&1

# Test hardware
python tools/test_hardware.py

# Check all services
systemctl status road-robot.service >> diagnostics.txt
```

### 3. Check Documentation

- [QUICKSTART.md](QUICKSTART.md) - Setup guide
- [README.md](../README.md) - Full documentation
- Code comments and docstrings

---

## 📝 Common Error Messages

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| `Failed to connect to MTi sensor` | Serial port issue | Check UART enabled, permissions |
| `No GPS fix` | No satellite signal | Move to open area, wait longer |
| `Failed to connect to MQTT broker` | Network/config issue | Check broker address, network |
| `No road found nearby` | Missing GeoJSON data | Download road data with tools |
| `Permission denied: /dev/gpiomem` | Not in gpio group | Add user to gpio group, logout |
| `Safety check failed` | Battery, tilt, or GPS | Check safety parameters in .env |
| `Mission timeout` | Navigation taking too long | Increase MAX_MISSION_DURATION |
| `Invalid deploy command` | Wrong JSON format | Check JSON has job_id, lat, lon |

---

## ✅ Emergency Procedures

### Immediate Stop

1. **Press emergency stop button** (GPIO 21)
2. **Ctrl+C** if running manually
3. **Unplug power** as last resort

### Safe Shutdown

```bash
# Stop service
sudo systemctl stop road-robot.service

# Stop all GPIO
gpio reset

# Shutdown RPi
sudo shutdown -h now
```

### Factory Reset

```bash
cd ~/GIQ_2025/RPI_codes

# Remove configuration
rm .env

# Remove virtual environment
rm -rf venv

# Re-run installation
./scripts/install.sh
```

---

**Still stuck? Double-check wiring, permissions, and logs. Most issues are configuration related! 🔍**
