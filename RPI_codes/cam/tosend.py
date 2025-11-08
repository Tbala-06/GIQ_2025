#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Webcam Viewer with Resolution Testing
==================================================
Tests different resolutions to find max camera capabilities
"""
import cv2

print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Cannot open camera 0")
    print("Try changing to camera 1 or 2")
    exit()

print("Camera opened successfully!")

# Test different common resolutions
test_resolutions = [
    (320, 240, "QVGA"),
    (640, 480, "VGA"),
    (800, 600, "SVGA"),
    (1024, 768, "XGA"),
    (1280, 720, "HD 720p"),
    (1280, 1024, "SXGA"),
    (1920, 1080, "Full HD 1080p"),
    (2592, 1944, "5MP"),
    (3840, 2160, "4K UHD"),
]

print("\n=== Testing Camera Resolutions ===")
supported_resolutions = []

for width, height, name in test_resolutions:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if actual_width == width and actual_height == height:
        print(f"✓ {name}: {width}x{height} - SUPPORTED")
        supported_resolutions.append((width, height, name))
    else:
        print(f"✗ {name}: {width}x{height} - Not supported (got {actual_width}x{actual_height})")

if not supported_resolutions:
    print("\nNo test resolutions supported, using camera defaults")
    supported_resolutions.append((
        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "Default"
    ))

# Set to maximum supported resolution
max_res = supported_resolutions[-1]
cap.set(cv2.CAP_PROP_FRAME_WIDTH, max_res[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, max_res[1])

print(f"\n=== Using Maximum Resolution: {max_res[2]} ({max_res[0]}x{max_res[1]}) ===")

# Check actual FOV settings
print("\n=== Camera Properties ===")
print(f"Width: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}")
print(f"Height: {int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"FPS: {int(cap.get(cv2.CAP_PROP_FPS))}")

# Check if camera supports manual focus/zoom (rare on webcams)
try:
    print(f"Focus: {cap.get(cv2.CAP_PROP_FOCUS)}")
    print(f"Zoom: {cap.get(cv2.CAP_PROP_ZOOM)}")
except:
    print("Focus/Zoom properties not available")

print("\n=== Controls ===")
print("Press 'Q' to quit")
print("Press 'S' to save screenshot")
print("Press '1-9' to cycle through supported resolutions")

frame_count = 0
current_res_index = len(supported_resolutions) - 1  # Start with max

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("ERROR: Can't receive frame")
        break
    
    frame_count += 1
    
    # Get current resolution
    current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Show info overlay
    cv2.putText(frame, f"Resolution: {current_width}x{current_height}", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Frame: {frame_count}", (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"FOV: {supported_resolutions[current_res_index][2]}", (10, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Add grid overlay to see field of view better
    h, w = frame.shape[:2]
    cv2.line(frame, (w//2, 0), (w//2, h), (255, 0, 0), 1)  # Vertical center
    cv2.line(frame, (0, h//2), (w, h//2), (255, 0, 0), 1)  # Horizontal center
    cv2.circle(frame, (w//2, h//2), 50, (255, 0, 0), 2)    # Center circle
    
    cv2.imshow('USB Webcam - Resolution Test', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        print("\nQuitting...")
        break
    elif key == ord('s'):
        filename = f"webcam_{current_width}x{current_height}_{frame_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Screenshot saved: {filename}")
    elif ord('1') <= key <= ord('9'):
        # Cycle through resolutions
        res_num = key - ord('1')
        if res_num < len(supported_resolutions):
            current_res_index = res_num
            width, height, name = supported_resolutions[res_num]
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            print(f"\nSwitched to: {name} ({width}x{height})")

cap.release()
cv2.destroyAllWindows()
print("\nCamera closed")
print(f"\nMaximum supported resolution: {supported_resolutions[-1][2]} ({supported_resolutions[-1][0]}x{supported_resolutions[-1][1]})")