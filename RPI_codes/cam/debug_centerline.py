# -*- coding: utf-8 -*-
"""
Debug Center Line Alignment
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

# Save debug images
cv2.imwrite('datas/debug_orange_mask.png', orange_mask)
cv2.imwrite('datas/debug_marking_mask.png', marking_mask)
cv2.imwrite('datas/debug_marking_only.png', marking_only)

# Find contours and rectangle
contours, _ = cv2.findContours(marking_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
large_contours = [c for c in contours if cv2.contourArea(c) >= (w*h)*0.01]

print(f"Total contours: {len(contours)}")
print(f"Large contours: {len(large_contours)}")

if large_contours:
    all_points = np.vstack(large_contours)
    marking_rect = cv2.minAreaRect(all_points)
    (rect_center_x, rect_center_y), (rect_width, rect_height), rect_angle = marking_rect

    print(f"Rectangle center: ({rect_center_x:.1f}, {rect_center_y:.1f})")
    print(f"Rectangle size: W={rect_width:.1f}px H={rect_height:.1f}px")
    print(f"Rectangle angle: {rect_angle:.2f} deg")

    # Draw rectangle on debug image
    debug_vis = image.copy()
    marking_box = cv2.boxPoints(marking_rect)
    marking_box = np.intp(marking_box)
    cv2.drawContours(debug_vis, [marking_box], 0, (0, 255, 255), 2)

    # Draw center
    cv2.circle(debug_vis, (int(rect_center_x), int(rect_center_y)), 8, (0, 255, 255), -1)

    cv2.imwrite('datas/debug_rectangle.png', debug_vis)
    print("Saved debug images")
else:
    print("No large contours found")
