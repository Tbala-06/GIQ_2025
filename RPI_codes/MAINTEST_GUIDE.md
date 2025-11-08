# Main Test Guide

Simple test system to verify MQTT communication and EV3 motor control.

## 🎯 What It Does

1. **Listens for MQTT deploy commands** on topic `giq/robot/deploy`
2. **Displays received coordinates** (latitude, longitude, job ID)
3. **Tests EV3 motors** by moving forward 30cm and backward 30cm

## 🚀 Quick Start

### Option 1: Test with Simulation (No Hardware)

```bash
# Terminal 1: Start the robot test (simulation mode)
cd RPI_codes
python3 maintest.py --simulate

# Terminal 2: Send a test deploy command
python3 send_test_deploy.py --lat 1.3521 --lon 103.8198
```

### Option 2: Test with Real Hardware

```bash
# Make sure EV3 is connected via USB

# Terminal 1: Start the robot test (hardware mode)
cd RPI_codes
python3 maintest.py

# Terminal 2: Send a test deploy command
python3 send_test_deploy.py --lat 1.3521 --lon 103.8198
```

## 📋 What You'll See

### When maintest.py Starts:

```
==================================================
SIMPLE ROBOT TEST
==================================================
Mode: HARDWARE
MQTT Broker: broker.hivemq.com
Deploy Topic: giq/robot/deploy
==================================================

→ Connecting to EV3...
✓ EV3 connected

→ Connecting to MQTT...
✓ MQTT connected

==================================================
🎯 READY - Waiting for deploy command...
   Listening on: giq/robot/deploy
   Press Ctrl+C to exit
==================================================
```

### When Deploy Command is Received:

```
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
DEPLOY COMMAND RECEIVED!
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯

📋 Deployment Information:
   Job ID:    1699876543
   Latitude:  1.352100
   Longitude: 103.819800

==================================================

🤖 Testing EV3 Motors...
----------------------------------------------------------------------

→ Test 1: Moving FORWARD 30cm...
   ✓ Forward complete
     Encoders: Left=1234, Right=1230

   Waiting 2 seconds...

→ Test 2: Moving BACKWARD 30cm...
   ✓ Backward complete
     Encoders: Left=50, Right=48

   Waiting 2 seconds...

→ Test 3: Stopping motors...
   ✓ Motors stopped

----------------------------------------------------------------------
✅ Motor test sequence complete!
----------------------------------------------------------------------

==================================================
✅ TEST COMPLETE
==================================================

Waiting for next deploy command...
(Press Ctrl+C to exit)
```

## 🔧 Usage Options

### maintest.py

```bash
# Hardware mode
python3 maintest.py

# Simulation mode (no EV3 needed)
python3 maintest.py --simulate
```

### send_test_deploy.py

```bash
# Send default coordinates (1.3521, 103.8198)
python3 send_test_deploy.py

# Send custom coordinates
python3 send_test_deploy.py --lat 1.3550 --lon 103.8200

# Send with specific job ID
python3 send_test_deploy.py --lat 1.3521 --lon 103.8198 --job-id 42
```

## 📡 MQTT Details

- **Broker**: `broker.hivemq.com` (public MQTT broker)
- **Topic**: `giq/robot/deploy`
- **Message Format**:
  ```json
  {
    "job_id": 1699876543,
    "latitude": 1.352100,
    "longitude": 103.819800,
    "timestamp": 1699876543.123,
    "command": "DEPLOY"
  }
  ```

## 🤖 Motor Test Sequence

When a deploy command is received, the robot automatically runs this sequence:

1. **Move Forward 30cm** at 40% speed
2. **Wait 2 seconds**
3. **Move Backward 30cm** at 40% speed
4. **Wait 2 seconds**
5. **Stop motors**

Each movement reports encoder positions for verification.

## 🧪 Testing Scenarios

### Test 1: MQTT Communication Only

```bash
# Terminal 1
python3 maintest.py --simulate

# Terminal 2
python3 send_test_deploy.py
```

**Expected**: Deploy message received and displayed, simulated motor movements

### Test 2: EV3 Motors Only

```bash
# Terminal 1
python3 maintest.py

# Terminal 2
python3 send_test_deploy.py
```

**Expected**: Deploy message received, actual EV3 motors move forward and backward

### Test 3: Multiple Deploy Commands

```bash
# Terminal 1
python3 maintest.py

# Terminal 2 - send multiple commands
python3 send_test_deploy.py --lat 1.3521 --lon 103.8198 --job-id 1
python3 send_test_deploy.py --lat 1.3530 --lon 103.8190 --job-id 2
python3 send_test_deploy.py --lat 1.3540 --lon 103.8200 --job-id 3
```

**Expected**: Robot receives and processes each deploy command in sequence

## 🐛 Troubleshooting

### "MQTT connection failed"

```bash
# Check if you can reach the broker
ping broker.hivemq.com

# Try alternative broker
# Edit maintest.py: MQTT_BROKER = "test.mosquitto.org"
```

### "EV3 connection failed"

```bash
# Check USB connection
lsusb  # Should show LEGO device

# Check usb0 interface
ip addr show usb0

# Try manual IP configuration
sudo ip addr add 169.254.144.1/16 dev usb0
```

### No deploy message received

1. Make sure both scripts are running
2. Check they're using the same broker and topic
3. Check terminal output for error messages
4. Verify MQTT broker is accessible

### Motors don't move

1. Check EV3 battery level
2. Verify motor connections (Ports A and B)
3. Test motors directly on EV3 brick
4. Check encoder feedback is being printed

## 📊 Expected Output Summary

| Event | What Happens |
|-------|-------------|
| Start maintest.py | Connects to EV3 and MQTT, waits for commands |
| Send deploy command | Terminal 1 shows deploy message received |
| Motor test starts | Robot moves forward 30cm |
| After 2 seconds | Robot moves backward 30cm |
| After 2 seconds | Motors stop, ready for next command |

## 🔄 Integration with Full System

This test validates:
- ✅ MQTT communication is working
- ✅ Deploy command format is correct
- ✅ EV3 connection is stable
- ✅ Motor control is functioning
- ✅ Encoder feedback is accurate

Once this test passes, you can move to the full robot_controller.py which adds:
- GPS navigation
- Camera alignment
- Complete painting sequence
- Full state machine

## 📝 Next Steps

After successful testing:

1. **Calibrate the robot**: `python3 calibration_wizard.py`
2. **Test full system**: `python3 robot_controller.py --simulate`
3. **Deploy for real**: `python3 robot_controller.py`

## 🆘 Need Help?

Check the logs and error messages. Common issues:
- Network/firewall blocking MQTT port 1883
- EV3 not properly connected via USB
- Wrong MQTT topic or broker
- Missing dependencies (paho-mqtt)

Install dependencies:
```bash
pip3 install paho-mqtt
```

---

**Happy Testing! 🚀**
