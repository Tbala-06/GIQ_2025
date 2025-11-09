# -*- coding: utf-8 -*-
"""
Enhanced Stencil Alignment System - Yellow Detection with Rotation
===================================================================

ENHANCED LOGIC:
- Detect orange stencil
- Detect yellow road marking
- Calculate LATERAL offset (left/right)
- Calculate ROTATION angle (degrees)
- Provide correction instructions for both position AND rotation
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
import os
import glob
import math


@dataclass
class EnhancedAlignmentResult:
    """Enhanced alignment results with rotation"""
    zone_detected: str  # "LEFT", "CENTER", "RIGHT", or "NONE"
    horizontal_offset: float  # Lateral offset in pixels
    offset_percentage: float  # Offset as percentage of stencil width
    rotation_angle: float  # Rotation angle in degrees (0 = aligned)
    rotate_direction: str  # "CW", "CCW", or "ALIGNED"
    position_aligned: bool  # Is lateral position aligned?
    rotation_aligned: bool  # Is rotation aligned?
    fully_aligned: bool  # Both position AND rotation aligned?
    instruction: str
    debug_image: np.ndarray


class EnhancedYellowAlignmentDetector:
    """Enhanced detector with rotation detection"""

    def __init__(self,
                 position_tolerance: float = 0.15,  # 15% lateral tolerance
                 rotation_tolerance: float = 5.0,   # 5 degrees rotation tolerance
                 debug: bool = True):
        """
        Args:
            position_tolerance: How much of the width counts as "center" (0.15 = 15%)
            rotation_tolerance: Maximum rotation angle to consider aligned (degrees)
            debug: Whether to generate debug visualization
        """
        self.position_tolerance = position_tolerance
        self.rotation_tolerance = rotation_tolerance
        self.debug = debug

    def detect_orange_stencil(self, image: np.ndarray) -> Optional[Tuple]:
        """
        Detect the orange stencil frame - returns bbox and angle
        Returns: (x, y, w, h, angle, rotated_rect) or None
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Bright orange color range
        lower_orange = np.array([5, 150, 150])
        upper_orange = np.array([20, 255, 255])

        orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)

        kernel = np.ones((5, 5), np.uint8)
        orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_CLOSE, kernel)
        orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        largest_contour = max(contours, key=cv2.contourArea)

        # Get regular bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Get minimum area rectangle (for rotation)
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]

        # Normalize angle to -45 to 45 degrees
        # OpenCV returns angle -90 to 0
        if angle < -45:
            angle = 90 + angle

        return (x, y, w, h, angle, rect)

    def detect_yellow_marking_angle(self, image: np.ndarray) -> Optional[float]:
        """
        Detect the angle of the yellow road marking
        Returns: angle in degrees or None
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Yellow range
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])

        # White range
        lower_white = np.array([0, 0, 98])
        upper_white = np.array([180, 199, 254])

        # Create masks
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        # Combine masks
        marking_mask = cv2.bitwise_or(yellow_mask, white_mask)

        # Clean up
        kernel_small = np.ones((2, 2), np.uint8)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_OPEN, kernel_small)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_CLOSE, kernel_small)

        # Filter out small regions
        contours, _ = cv2.findContours(marking_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Create filtered mask with only large regions
        img_h, img_w = image.shape[:2]
        filtered_mask = np.zeros_like(marking_mask)
        min_area = (img_w * img_h) * 0.02

        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                cv2.drawContours(filtered_mask, [contour], -1, 255, -1)
                valid_contours.append(contour)

        if not valid_contours:
            return None

        # Store for visualization
        self._yellow_mask = filtered_mask.copy()
        self._yellow_contours = valid_contours

        # Combine all valid contours into one
        all_points = np.vstack(valid_contours)

        # Get minimum area rectangle for the yellow marking
        rect = cv2.minAreaRect(all_points)
        angle = rect[2]

        # Store rectangle for visualization
        self._yellow_rect = rect

        # Normalize angle
        if angle < -45:
            angle = 90 + angle

        return angle

    def detect_yellow_in_zones(self, image: np.ndarray, stencil_bbox: Tuple[int, int, int, int]) -> Tuple[str, float, float]:
        """
        Detect which zone contains yellow pixels (existing lateral detection)
        Returns: (zone_name, offset_px, offset_percentage)
        """
        img_height, img_width = image.shape[:2]

        # ROI = entire image
        roi_x = 0
        roi_y = 0
        roi_w = img_width
        roi_h = img_height

        roi = image[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].copy()

        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Yellow range
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])

        # White range
        lower_white = np.array([0, 0, 98])
        upper_white = np.array([180, 199, 254])

        # Create masks
        yellow_mask = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
        white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)

        # Combine masks
        marking_mask = cv2.bitwise_or(yellow_mask, white_mask)

        # Clean up
        kernel_small = np.ones((2, 2), np.uint8)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_OPEN, kernel_small)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_CLOSE, kernel_small)

        # Filter out small regions
        contours, _ = cv2.findContours(marking_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        filtered_mask = np.zeros_like(marking_mask)
        min_area = (roi_w * roi_h) * 0.02

        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                cv2.drawContours(filtered_mask, [contour], -1, 255, -1)

        marking_mask = filtered_mask

        # Store for visualization
        self._debug_mask = marking_mask.copy()

        # Define zones
        left_boundary = int(roi_w * 0.33)
        right_boundary = int(roi_w * 0.67)

        # Split mask into zones
        left_zone = marking_mask[:, 0:left_boundary]
        center_zone = marking_mask[:, left_boundary:right_boundary]
        right_zone = marking_mask[:, right_boundary:]

        # Count pixels in each zone
        left_pixels = cv2.countNonZero(left_zone)
        center_pixels = cv2.countNonZero(center_zone)
        right_pixels = cv2.countNonZero(right_zone)

        # Calculate center of mass
        moments = cv2.moments(marking_mask)
        if moments["m00"] > 0:
            cx = moments["m10"] / moments["m00"]
            offset_px = cx - (roi_w / 2)
            offset_percent = (offset_px / roi_w) * 100
        else:
            cx = roi_w / 2
            offset_px = 0
            offset_percent = 0

        # Determine zone
        max_pixels = max(left_pixels, center_pixels, right_pixels)

        if max_pixels == 0:
            return "NONE", 0, 0

        min_threshold = 10

        if max_pixels < min_threshold:
            return "NONE", 0, 0

        if left_pixels == max_pixels:
            return "LEFT", offset_px, offset_percent
        elif right_pixels == max_pixels:
            return "RIGHT", offset_px, offset_percent
        else:
            return "CENTER", offset_px, offset_percent

    def analyze_alignment(self, image: np.ndarray) -> EnhancedAlignmentResult:
        """Main analysis method with rotation detection"""
        height, width = image.shape[:2]
        debug_img = image.copy() if self.debug else None

        # Initialize masks for visualization
        self._yellow_mask = None
        self._yellow_contours = None
        self._yellow_rect = None

        # Detect stencil
        stencil_data = self.detect_orange_stencil(image)

        if stencil_data is None:
            return EnhancedAlignmentResult(
                zone_detected="NONE",
                horizontal_offset=0,
                offset_percentage=0,
                rotation_angle=0,
                rotate_direction="UNKNOWN",
                position_aligned=False,
                rotation_aligned=False,
                fully_aligned=False,
                instruction="ERROR: Cannot detect orange stencil",
                debug_image=debug_img
            )

        x, y, w, h, stencil_angle, stencil_rect = stencil_data
        stencil_center_x = x + w/2

        # Detect yellow marking angle
        yellow_angle = self.detect_yellow_marking_angle(image)

        # Calculate rotation difference
        if yellow_angle is not None:
            rotation_diff = stencil_angle - yellow_angle

            # Normalize to -180 to 180
            while rotation_diff > 180:
                rotation_diff -= 360
            while rotation_diff < -180:
                rotation_diff += 360

            # Determine rotation direction
            if abs(rotation_diff) <= self.rotation_tolerance:
                rotate_direction = "ALIGNED"
                rotation_aligned = True
            elif rotation_diff > 0:
                rotate_direction = "CW"  # Need to rotate clockwise to align
                rotation_aligned = False
            else:
                rotate_direction = "CCW"  # Need to rotate counter-clockwise
                rotation_aligned = False
        else:
            rotation_diff = 0
            rotate_direction = "UNKNOWN"
            rotation_aligned = False

        # Detect lateral position (existing logic)
        zone, offset_px, offset_percent = self.detect_yellow_in_zones(image, (x, y, w, h))

        # Determine if position aligned
        position_aligned = (zone == "CENTER")

        # Fully aligned only if BOTH position and rotation are aligned
        fully_aligned = position_aligned and rotation_aligned

        # Generate instruction
        instructions = []

        if not position_aligned and zone != "NONE":
            if zone == "LEFT":
                instructions.append(f"Move LEFT {abs(offset_percent):.1f}%")
            elif zone == "RIGHT":
                instructions.append(f"Move RIGHT {abs(offset_percent):.1f}%")

        if not rotation_aligned and yellow_angle is not None:
            instructions.append(f"Rotate {rotate_direction} {abs(rotation_diff):.1f}°")

        if fully_aligned:
            instruction = "FULLY ALIGNED OK OK"
        elif len(instructions) == 0:
            if zone == "NONE":
                instruction = "WARNING: No yellow/white detected"
            else:
                instruction = "ALIGNED (position only)"
        else:
            instruction = " + ".join(instructions)

        # Draw debug visualization
        if self.debug:
            # Draw stencil bounding box
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 165, 255), 3)

            # Draw rotated rectangle for stencil
            box = cv2.boxPoints(stencil_rect)
            box = np.intp(box)
            cv2.drawContours(debug_img, [box], 0, (255, 0, 255), 2)

            cv2.putText(debug_img, f"STENCIL ({stencil_angle:.1f}°)", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            # Draw yellow marking rectangle if detected
            if self._yellow_rect is not None:
                yellow_box = cv2.boxPoints(self._yellow_rect)
                yellow_box = np.intp(yellow_box)
                cv2.drawContours(debug_img, [yellow_box], 0, (0, 255, 255), 2)

                ycx, ycy = int(self._yellow_rect[0][0]), int(self._yellow_rect[0][1])
                cv2.putText(debug_img, f"MARKING ({yellow_angle:.1f}°)",
                           (ycx-80, ycy-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Draw search area
            cv2.rectangle(debug_img, (0, 0), (width, height), (255, 0, 255), 3)
            cv2.putText(debug_img, "SEARCH AREA", (5, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

            # Draw zone boundaries
            left_boundary = int(width * 0.33)
            right_boundary = int(width * 0.67)

            cv2.line(debug_img, (left_boundary, 0), (left_boundary, height), (255, 255, 0), 2)
            cv2.line(debug_img, (right_boundary, 0), (right_boundary, height), (255, 255, 0), 2)

            # Label zones
            cv2.putText(debug_img, "LEFT", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            cv2.putText(debug_img, "CENTER", (left_boundary+10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            cv2.putText(debug_img, "RIGHT", (right_boundary+10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            # Draw center line
            cv2.line(debug_img, (int(stencil_center_x), 0), (int(stencil_center_x), height), (0, 255, 255), 2)

            # Highlight detected zone
            zone_color = (0, 255, 0) if fully_aligned else (0, 128, 255) if position_aligned else (0, 0, 255)
            if zone == "LEFT":
                zone_rect = (0, 0, left_boundary, height)
            elif zone == "CENTER":
                zone_rect = (left_boundary, 0, right_boundary-left_boundary, height)
            elif zone == "RIGHT":
                zone_rect = (right_boundary, 0, width-right_boundary, height)
            else:
                zone_rect = None

            if zone_rect:
                overlay = debug_img.copy()
                rx, ry, rw, rh = zone_rect
                cv2.rectangle(overlay, (rx, ry), (rx+rw, ry+rh), zone_color, -1)
                cv2.addWeighted(overlay, 0.2, debug_img, 0.8, 0, debug_img)

            # Info overlay
            overlay = debug_img.copy()
            box_height = 180
            cv2.rectangle(overlay, (0, 0), (width, box_height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, debug_img, 0.4, 0, debug_img)

            # Text info
            color = (0, 255, 0) if fully_aligned else (0, 128, 255) if (position_aligned or rotation_aligned) else (0, 0, 255)

            cv2.putText(debug_img, f"Position: {zone} ({offset_px:.1f}px, {offset_percent:.1f}%)",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(debug_img, f"Rotation: {rotation_diff:.1f}° ({rotate_direction})",
                       (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Status indicators
            pos_status = "OK" if position_aligned else "X"
            rot_status = "OK" if rotation_aligned else "X"
            cv2.putText(debug_img, f"Aligned: Pos {pos_status}  Rot {rot_status}",
                       (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.putText(debug_img, instruction,
                       (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            # Draw direction arrows
            if not fully_aligned:
                self._draw_correction_arrows(debug_img, zone, rotate_direction, width, height,
                                             position_aligned, rotation_aligned)

            # Show detection mask
            if hasattr(self, '_debug_mask') and self._debug_mask is not None:
                mask_vis = cv2.cvtColor(self._debug_mask, cv2.COLOR_GRAY2BGR)
                mask_vis = cv2.resize(mask_vis, (150, 100))

                debug_img[height-110:height-10, 10:160] = mask_vis
                cv2.rectangle(debug_img, (10, height-110), (160, height-10), (255, 255, 255), 2)
                cv2.putText(debug_img, "DETECTION", (15, height-115),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return EnhancedAlignmentResult(
            zone_detected=zone,
            horizontal_offset=offset_px,
            offset_percentage=offset_percent,
            rotation_angle=rotation_diff,
            rotate_direction=rotate_direction,
            position_aligned=position_aligned,
            rotation_aligned=rotation_aligned,
            fully_aligned=fully_aligned,
            instruction=instruction,
            debug_image=debug_img
        )

    def _draw_correction_arrows(self, img, zone, rotate_dir, width, height,
                                pos_aligned, rot_aligned):
        """Draw correction arrows for position and/or rotation"""
        arrow_y = height - 80

        # Position arrow (left side)
        if not pos_aligned and zone != "NONE":
            pos_x = 100
            arrow_length = 60

            if zone == "LEFT":
                cv2.arrowedLine(img, (pos_x + arrow_length//2, arrow_y),
                              (pos_x - arrow_length//2, arrow_y),
                              (0, 255, 255), 6, tipLength=0.3)
                cv2.putText(img, "LEFT", (pos_x-30, arrow_y-20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            elif zone == "RIGHT":
                cv2.arrowedLine(img, (pos_x - arrow_length//2, arrow_y),
                              (pos_x + arrow_length//2, arrow_y),
                              (0, 255, 255), 6, tipLength=0.3)
                cv2.putText(img, "RIGHT", (pos_x-35, arrow_y-20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Rotation arrow (right side)
        if not rot_aligned and rotate_dir in ["CW", "CCW"]:
            rot_x = width - 100
            rot_y = arrow_y
            radius = 40

            if rotate_dir == "CW":
                # Clockwise arc
                cv2.ellipse(img, (rot_x, rot_y), (radius, radius),
                           0, -90, 180, (255, 128, 0), 4)
                cv2.arrowedLine(img, (rot_x + radius, rot_y),
                              (rot_x + radius + 15, rot_y + 10),
                              (255, 128, 0), 6, tipLength=0.5)
                cv2.putText(img, "CW", (rot_x-20, rot_y-45),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 128, 0), 2)
            else:  # CCW
                # Counter-clockwise arc
                cv2.ellipse(img, (rot_x, rot_y), (radius, radius),
                           0, 90, 360, (255, 128, 0), 4)
                cv2.arrowedLine(img, (rot_x - radius, rot_y),
                              (rot_x - radius - 15, rot_y + 10),
                              (255, 128, 0), 6, tipLength=0.5)
                cv2.putText(img, "CCW", (rot_x-25, rot_y-45),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 128, 0), 2)


def process_images_batch(datas_folder: str, detector: EnhancedYellowAlignmentDetector):
    """Process all images in datas folder"""
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    image_files = []

    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(datas_folder, ext)))

    if not image_files:
        print("No images found in datas folder")
        return

    print(f"\nFound {len(image_files)} images")
    print("="*70)

    for img_path in sorted(image_files):
        image = cv2.imread(img_path)
        if image is None:
            continue

        print(f"\n{os.path.basename(img_path)}:")
        print("-"*70)

        result = detector.analyze_alignment(image)

        print(f"  Position: {result.zone_detected} ({result.offset_percentage:+.1f}%) - {'OK' if result.position_aligned else 'X'}")
        print(f"  Rotation: {result.rotation_angle:+.1f} deg ({result.rotate_direction}) - {'OK' if result.rotation_aligned else 'X'}")
        print(f"  Status: {result.instruction}")
        print(f"  Fully Aligned: {'YES OK OK' if result.fully_aligned else 'NO'}")

        if result.debug_image is not None:
            output_path = os.path.join(datas_folder, f"analyzed_{os.path.basename(img_path)}")
            cv2.imwrite(output_path, result.debug_image)
            print(f"  Saved: {os.path.basename(output_path)}")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("ENHANCED ALIGNMENT SYSTEM - Position + Rotation Detection")
    print("="*70)
    print("\nFeatures:")
    print("  • Lateral Position Detection (LEFT/CENTER/RIGHT)")
    print("  • Rotation Angle Detection (degrees)")
    print("  • Dual Alignment Check (position AND rotation)")
    print("  • Visual Debugging with Arrows")
    print("="*70 + "\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    datas_folder = os.path.join(script_dir, "datas")

    if not os.path.exists(datas_folder):
        print(f"ERROR: 'datas' folder not found: {datas_folder}")
        return

    print(f"Processing images in: {datas_folder}\n")

    detector = EnhancedYellowAlignmentDetector(
        position_tolerance=0.15,  # 15% center tolerance
        rotation_tolerance=5.0,    # 5 degrees rotation tolerance
        debug=True
    )

    process_images_batch(datas_folder, detector)

    print("\n" + "="*70)
    print("Done! Check 'analyzed_*.png' files in datas folder")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
