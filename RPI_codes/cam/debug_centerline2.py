# -*- coding: utf-8 -*-
"""
Debug Center Line Alignment - Test different contour selection
"""

import cv2
import numpy as np

# Load image
image = cv2.imread('datas/image.png')
h, w = image.shape[:2]
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Color ranges
orange_lower = np.array([5, 150, 150])
orange_upper = np.array([20, 255, 255])
yellow_lower = np.array([15, 80, 80])
yellow_upper = np.array([35, 255, 255])
white_lower = np.array([0, 0, 98])
white_upper = np.array([180, 199, 254])

# Create masks
orange_mask = cv2.inRange(hsv, orange_lower, orange_upper)
yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
white_mask = cv2.inRange(hsv, white_lower, white_upper)
marking_mask = cv2.bitwise_or(yellow_mask, white_mask)

# Clean up
kernel = np.ones((3, 3), np.uint8)
orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_CLOSE, kernel)
orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_OPEN, kernel)
marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_CLOSE, kernel)
marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_OPEN, kernel)

# Subtract orange from marking
marking_only = cv2.bitwise_and(marking_mask, cv2.bitwise_not(orange_mask))

# Find contours
contours, _ = cv2.findContours(marking_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Sort contours by area
sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

print(f"Total contours: {len(contours)}")
print("\nTop 10 contours by area:")
for i, cnt in enumerate(sorted_contours[:10]):
    area = cv2.contourArea(cnt)
    area_pct = (area / (w*h)) * 100

    # Get rectangle for each contour
    if len(cnt) >= 5:
        rect = cv2.minAreaRect(cnt)
        (cx, cy), (rw, rh), angle = rect

        # Fit line
        [vx, vy, x0, y0] = cv2.fitLine(cnt, cv2.DIST_L2, 0, 0.01, 0.01)
        line_angle = np.degrees(np.arctan2(float(vx), float(vy)))

        print(f"  {i+1}. Area: {area:.0f}px ({area_pct:.2f}%) - Rect angle: {angle:.1f}° - Line angle: {line_angle:.1f}°")
        print(f"      Center: ({cx:.0f}, {cy:.0f}), Size: {rw:.0f}x{rh:.0f}")
