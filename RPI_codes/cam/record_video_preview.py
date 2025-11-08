#!/usr/bin/env python3
"""
Video Recorder with Preview for Raspberry Pi
Records video with live preview window.
Press 'q' to stop early, or it stops automatically after 1 minute.
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
print("VIDEO RECORDER WITH PREVIEW")
print("=" * 50)
print(f"\nDuration: {DURATION} seconds")
print(f"Resolution: {RESOLUTION[0]}x{RESOLUTION[1]}")
print(f"FPS: {FPS}")
print("\nControls:")
print("  Q - Stop recording")
print("  S - Save screenshot")
print("=" * 50)
print()

# Generate filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"video_{timestamp}.mp4"
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, output_file)

print(f"Output: {output_file}\n")

# Initialize camera
print("Initializing camera...", end=" ")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("FAILED!")
    print("\nERROR: Cannot open camera")
    exit(1)

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

print("\nStarting in 3 seconds...")
time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)
print("RECORDING!\n")

start_time = time.time()
frame_count = 0

try:
    while True:
        elapsed = time.time() - start_time

        # Check duration
        if elapsed >= DURATION:
            print("\nDuration reached - stopping")
            break

        # Capture frame
        ret, frame = cap.read()

        if not ret:
            print("\nERROR: Failed to capture frame")
            break

        # Write frame
        out.write(frame)
        frame_count += 1

        # Add recording indicator
        remaining = DURATION - int(elapsed)

        # Draw red recording circle
        cv2.circle(frame, (20, 20), 10, (0, 0, 255), -1)

        # Draw timer
        timer_text = f"{int(elapsed)}s / {DURATION}s"
        cv2.putText(frame, timer_text, (40, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Draw remaining time
        remaining_text = f"{remaining}s left"
        cv2.putText(frame, remaining_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Show preview
        cv2.imshow('Recording - Press Q to stop', frame)

        # Check for key press
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("\nStopped by user")
            break
        elif key == ord('s'):
            screenshot = f"screenshot_{timestamp}_{frame_count}.jpg"
            screenshot_path = os.path.join(script_dir, screenshot)
            cv2.imwrite(screenshot_path, frame)
            print(f"Screenshot saved: {screenshot}")

except KeyboardInterrupt:
    print("\n\nStopped by Ctrl+C")

finally:
    # Cleanup
    elapsed = time.time() - start_time

    print(f"\nCleaning up...")
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 50)
    print("RECORDING COMPLETE")
    print("=" * 50)
    print(f"\nFrames: {frame_count}")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"File: {output_file}")

    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Size: {file_size:.2f} MB")

    print("\nDone!\n")
