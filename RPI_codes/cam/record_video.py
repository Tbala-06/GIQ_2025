#!/usr/bin/env python3
"""
Simple Video Recorder for Raspberry Pi
Records 1 minute of video from the camera.
"""

import cv2
import time
import os
from datetime import datetime

# Settings
DURATION = 60  # seconds (1 minute)
RESOLUTION = (640, 480)  # Width x Height
FPS = 30

print("\n" + "=" * 50)
print("RASPBERRY PI VIDEO RECORDER")
print("=" * 50)
print(f"\nDuration: {DURATION} seconds")
print(f"Resolution: {RESOLUTION[0]}x{RESOLUTION[1]}")
print(f"FPS: {FPS}")
print()

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"video_{timestamp}.mp4"

# Get script directory for saving
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, output_file)

print(f"Output: {output_file}")
print()

# Initialize camera
print("Initializing camera...", end=" ")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("FAILED!")
    print("\nERROR: Cannot open camera")
    print("Make sure camera is connected")
    exit(1)

# Set resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
cap.set(cv2.CAP_PROP_FPS, FPS)

print("OK")

# Setup video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, FPS, RESOLUTION)

if not out.isOpened():
    print("\nERROR: Cannot create video file")
    cap.release()
    exit(1)

print(f"\nRecording for {DURATION} seconds...")
print("Press Ctrl+C to stop early\n")

start_time = time.time()
frame_count = 0

try:
    while True:
        # Calculate elapsed time
        elapsed = time.time() - start_time

        # Check if duration reached
        if elapsed >= DURATION:
            break

        # Capture frame
        ret, frame = cap.read()

        if not ret:
            print("\nERROR: Failed to capture frame")
            break

        # Write frame
        out.write(frame)
        frame_count += 1

        # Show progress every second
        if frame_count % FPS == 0:
            remaining = DURATION - int(elapsed)
            progress = (elapsed / DURATION) * 100
            print(f"Recording... {int(elapsed)}s / {DURATION}s ({progress:.0f}%) - {remaining}s remaining")

except KeyboardInterrupt:
    print("\n\nStopped by user")

finally:
    # Cleanup
    elapsed = time.time() - start_time

    print(f"\nReleasing camera...")
    cap.release()
    out.release()

    print("\n" + "=" * 50)
    print("RECORDING COMPLETE")
    print("=" * 50)
    print(f"\nFrames captured: {frame_count}")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"File: {output_file}")
    print(f"Path: {output_path}")

    # Check file size
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"Size: {file_size:.2f} MB")

    print("\nDone!\n")
