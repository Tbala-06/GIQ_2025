# EV3 IP Address Configuration Guide

There are **three ways** to configure the EV3 IP address. The system checks them in this priority order:

## Priority Order

1. **Function argument** (passed directly to code)
2. **Environment variable** `EV3_IP_ADDRESS`
3. **Config file** `ev3_config.py`
4. **Auto-detection** (scans usb0 interface for 169.254.x.x)

## Method 1: Environment Variable (Recommended for Bot)

Set the IP address in your `.env` file:

```bash
# Edit .env or App_codes/road-painting-bot/.env
export EV3_IP_ADDRESS=169.254.14.120
```

Or set it in your shell session:

```bash
export EV3_IP_ADDRESS=169.254.14.120
python bot.py
```

**Advantages:**
- ✅ Easy to change without editing code
- ✅ Different IPs for different environments
- ✅ Works with the Telegram bot

## Method 2: Config File (Quick Testing)

Edit `RPI_codes/ev3_config.py`:

```python
# Line 24 - Change None to your IP address
EV3_IP_ADDRESS = os.getenv('EV3_IP_ADDRESS', '169.254.14.120')  # Set fixed IP here
```

Or directly set it without env fallback:

```python
# Ignore environment variable and use fixed IP
EV3_IP_ADDRESS = '169.254.14.120'
```

**Advantages:**
- ✅ Permanent configuration
- ✅ Good for dedicated robot setup

## Method 3: Auto-Detection (Default)

Leave both empty and the system will auto-detect:

```bash
# .env file
EV3_IP_ADDRESS=

# ev3_config.py
EV3_IP_ADDRESS = os.getenv('EV3_IP_ADDRESS', None)
```

The system will:
1. Check `usb0` interface
2. Scan ARP table for 169.254.x.x addresses
3. Ping each candidate
4. Use the first responsive EV3

**Advantages:**
- ✅ No configuration needed
- ✅ Works if IP changes
- ❌ Slower (takes 5-10 seconds)

## How to Find Your EV3 IP Address

### On EV3 Brick (ev3dev)

```bash
# SSH into EV3 first
ssh robot@169.254.14.120  # or whatever IP it has

# Then check IP
ip addr show usb0
# Look for: inet 169.254.14.120/16
```

### From Raspberry Pi

```bash
# Check network interface
ip addr show usb0

# Check ARP table
ip neigh show dev usb0

# Scan for EV3
nmap -sn 169.254.0.0/16 | grep -B 2 "LEGO"

# Or use our script
cd ~/GIQ_2025/RPI_codes
python -c "from ev3_comm import EV3Controller; c = EV3Controller(); print(c._detect_ev3_ip())"
```

## Usage Examples

### Example 1: Telegram Bot with Fixed IP

```bash
# Edit .env
echo "EV3_IP_ADDRESS=169.254.14.120" >> ~/GIQ_2025/App_codes/road-painting-bot/.env

# Run bot
cd ~/GIQ_2025/App_codes/road-painting-bot
python bot.py
```

### Example 2: Telegram Bot with Auto-Detect

```bash
# Make sure EV3_IP_ADDRESS is NOT set or empty in .env
cd ~/GIQ_2025/App_codes/road-painting-bot
python bot.py
```

The bot will auto-detect on startup.

### Example 3: Direct Python Script

```python
from ev3_comm import EV3Controller

# Method A: Use environment/config
controller = EV3Controller()  # Uses env -> config -> auto-detect
controller.connect()

# Method B: Force specific IP
controller = EV3Controller(ev3_ip='169.254.14.120')
controller.connect()

# Method C: Force auto-detect (ignore config)
controller = EV3Controller(ev3_ip=None)
controller.connect()
```

### Example 4: Change IP on the Fly

```bash
# Run with temporary IP override
EV3_IP_ADDRESS=169.254.14.120 python bot.py

# Or in code (bot.py line 121)
robot_available = initialize_robot_controller(simulate=False, ev3_ip='169.254.14.120')
```

## Configuration File Reference

### ev3_config.py (Lines 20-26)

```python
# EV3 IP Address
# Priority: 1. Environment variable EV3_IP_ADDRESS
#           2. This config value
#           3. Auto-detection on usb0 interface (169.254.x.x subnet)
EV3_IP_ADDRESS = os.getenv('EV3_IP_ADDRESS', None)  # Set to fixed IP like '169.254.14.120' or None for auto-detect
EV3_SSH_USERNAME = 'robot'  # Default ev3dev username
EV3_USB_INTERFACE = 'usb0'  # USB network interface name
```

### .env.example (Lines 30-34)

```bash
# EV3 Robot Configuration
# Set EV3 IP address for robot control
# Leave empty for auto-detection on usb0 interface
# Example: EV3_IP_ADDRESS=169.254.14.120
EV3_IP_ADDRESS=
```

## Troubleshooting

### "Cannot detect EV3 IP"

1. Check USB connection:
   ```bash
   lsusb | grep LEGO
   ```

2. Check usb0 interface exists:
   ```bash
   ip addr show usb0
   ```

3. Manually specify IP:
   ```bash
   export EV3_IP_ADDRESS=169.254.14.120
   ```

### "Connection refused"

- EV3 might not be running ev3dev
- SSH might not be enabled on EV3
- Try manual SSH: `ssh robot@169.254.14.120`

### "IP keeps changing"

- This is normal for USB connections
- Either:
  - Use auto-detection (slower but reliable)
  - Configure static IP on EV3

### "Want to use different IPs for testing"

```bash
# Development (auto-detect)
python bot.py

# Production (fixed IP)
EV3_IP_ADDRESS=169.254.14.120 python bot.py

# Testing with simulation
# Edit bot.py line 121: simulate=True
python bot.py
```

## Quick Reference

| Configuration | Location | When to Use |
|--------------|----------|-------------|
| `.env` file | `App_codes/road-painting-bot/.env` | Running Telegram bot |
| `ev3_config.py` | `RPI_codes/ev3_config.py` | Direct scripts, permanent config |
| Function arg | `bot.py` line 121 | Temporary override |
| Auto-detect | Leave all empty | IP changes frequently |

---

**Recommendation**: Use `.env` file for the Telegram bot, set to your current EV3 IP.
