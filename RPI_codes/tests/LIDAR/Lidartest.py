# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
LDS-02RR Xiaomi LiDAR Live Map - Raspberry Pi 5
Wiring: +5V→Pin2, GND→Pin6, TX→GPIO15(Pin10), MOT_EN→3.3V(Pin1)
"""

import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import struct
import time

# RPi 5 uses /dev/ttyAMA0 for GPIO UART
LIDAR_PORT = '/dev/ttyAMA0'  # or try '/dev/serial0'
BAUD_RATE = 230400

print("\n=== LDS-02RR Xiaomi LiDAR (RPi5) ===")
print(f"Port: {LIDAR_PORT}")
print(f"Baud: {BAUD_RATE}")
print("\nWiring Check:")
print("  +5V     → Pin 2 (5V)")
print("  GND     → Pin 6 (GND)")
print("  TX      → Pin 10 (GPIO15/RX)")
print("  MOT_EN  → Pin 1 (3.3V)")
print()

class LDS02RR:
    def __init__(self, port, baudrate=230400):
        try:
            self.serial = serial.Serial(port, baudrate, timeout=0.5)
            print(f"[OK] Connected to {port}")
        except Exception as e:
            print(f"[ERROR] Cannot open {port}: {e}")
            raise
            
        self.distances = np.zeros(360)
        self.angles = np.arange(0, 360)
        
    def read_frame(self):
        """Read one packet from LDS-02RR"""
        try:
            # Look for start byte 0x54
            while True:
                byte = self.serial.read(1)
                if len(byte) == 0:
                    return False
                if byte == b'\x54':
                    break
            
            # Read rest of header
            header = self.serial.read(2)
            if len(header) < 2:
                return False
                
            packet_type = header[0]
            sample_count = header[1]
            
            if sample_count > 12:  # Sanity check
                return False
            
            # Read FSA (First Sample Angle)
            fsa_bytes = self.serial.read(2)
            if len(fsa_bytes) < 2:
                return False
            fsa = struct.unpack('<H', fsa_bytes)[0]
            start_angle = (fsa >> 1) / 64.0
            
            # Read LSA (Last Sample Angle)
            lsa_bytes = self.serial.read(2)
            if len(lsa_bytes) < 2:
                return False
            lsa = struct.unpack('<H', lsa_bytes)[0]
            end_angle = (lsa >> 1) / 64.0
            
            # Read checksum
            check_bytes = self.serial.read(2)
            if len(check_bytes) < 2:
                return False
            
            # Read sample data
            sample_data = self.serial.read(sample_count * 3)
            if len(sample_data) < sample_count * 3:
                return False
            
            # Calculate angle step
            if end_angle < start_angle:
                end_angle += 360
            angle_step = (end_angle - start_angle) / (sample_count - 1) if sample_count > 1 else 0
            
            # Parse samples
            for i in range(sample_count):
                offset = i * 3
                distance_bytes = sample_data[offset:offset+2]
                intensity = sample_data[offset+2]
                
                distance = struct.unpack('<H', distance_bytes)[0]
                angle = (start_angle + i * angle_step) % 360
                angle_idx = int(angle)
                
                # Store valid readings
                if 0 <= angle_idx < 360 and distance > 0 and distance < 12000:
                    self.distances[angle_idx] = distance
            
            return True
            
        except Exception as e:
            print(f"Read error: {e}")
            return False
    
    def get_data(self):
        """Get current 360° scan"""
        return self.angles, self.distances
    
    def close(self):
        self.serial.close()

# Initialize LiDAR
try:
    lidar = LDS02RR(LIDAR_PORT, BAUD_RATE)
    time.sleep(1)
    
    # Test read
    print("Testing data reception...", end=' ')
    for _ in range(10):
        if lidar.read_frame():
            print("[OK]")
            break
    else:
        print("[FAIL] - No data received!")
        print("\nTroubleshooting:")
        print("1. Check motor is spinning (MOT_EN connected?)")
        print("2. Check UART enabled: ls -l /dev/ttyAMA0")
        print("3. Try: sudo chmod 666 /dev/ttyAMA0")
        exit(1)
        
except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)

# Setup plot
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='polar')
ax.set_ylim(0, 6000)  # 6 meters max
ax.set_theta_zero_location('N')  # Forward = North
ax.set_theta_direction(-1)  # Clockwise
ax.set_title('LDS-02RR Live SLAM Map', fontsize=16, pad=20)
ax.grid(True, alpha=0.3)

# Plot elements
scatter = ax.scatter([], [], s=2, c='cyan', alpha=0.8)
text = ax.text(0, 6500, '', ha='center', fontsize=10)

def update(frame):
    """Update plot with new scan"""
    # Read multiple frames for smoother update
    for _ in range(5):
        lidar.read_frame()
    
    angles, distances = lidar.get_data()
    
    # Filter valid points
    valid = (distances > 50) & (distances < 8000)  # 5cm to 8m
    valid_angles = np.radians(angles[valid])
    valid_distances = distances[valid]
    
    if len(valid_distances) > 0:
        # Update scatter
        scatter.set_offsets(np.c_[valid_angles, valid_distances])
        
        # Color by distance
        colors = plt.cm.plasma(valid_distances / 6000)
        scatter.set_color(colors)
        
        # Stats
        text.set_text(f'Points: {len(valid_distances)} | Range: {valid_distances.min():.0f}-{valid_distances.max():.0f}mm')
    
    return scatter, text

print("\n[STARTING] Live map visualization...")
print("Close window to stop.\n")

ani = FuncAnimation(fig, update, interval=50, blit=True, cache_frame_data=False)

try:
    plt.show()
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    lidar.close()
    print("Disconnected.")