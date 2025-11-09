# -*- coding: utf-8 -*-
"""
Mask-Based Alignment Visualizer
================================

Uses color masks to visualize alignment between orange stencil and yellow/white marking.
Shows reference lines and angles for both to help align them.

Usage:
    python mask_align.py
"""

import cv2
import numpy as np
import os
import glob
import math


class MaskAlignmentVisualizer:
    """Visualizes alignment using color masks with reference lines"""

    def __init__(self):
        """Initialize with color ranges"""

        # Orange stencil (HSV)
        self.orange_lower = np.array([5, 150, 150])
        self.orange_upper = np.array([20, 255, 255])

        # Yellow marking (HSV)
        self.yellow_lower = np.array([15, 80, 80])
        self.yellow_upper = np.array([35, 255, 255])

        # White marking (HSV)
        self.white_lower = np.array([0, 0, 98])
        self.white_upper = np.array([180, 199, 254])

    def create_alignment_visualization(self, image: np.ndarray):
        """
        Create alignment visualization with reference lines

        Returns:
            Visualization image with alignment info
        """
        h, w = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create masks
        orange_mask = cv2.inRange(hsv, self.orange_lower, self.orange_upper)
        yellow_mask = cv2.inRange(hsv, self.yellow_lower, self.yellow_upper)
        white_mask = cv2.inRange(hsv, self.white_lower, self.white_upper)

        # Combined marking (yellow + white)
        marking_mask = cv2.bitwise_or(yellow_mask, white_mask)

        # Clean up masks
        kernel = np.ones((3, 3), np.uint8)
        orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_CLOSE, kernel)
        orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_OPEN, kernel)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_CLOSE, kernel)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        orange_contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        marking_contours, _ = cv2.findContours(marking_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Create visualization
        vis = image.copy()

        # Analyze orange stencil
        orange_info = None
        if orange_contours:
            largest_orange = max(orange_contours, key=cv2.contourArea)
            orange_rect = cv2.minAreaRect(largest_orange)
            orange_box = cv2.boxPoints(orange_rect)
            orange_box = np.intp(orange_box)

            # Get center and angle
            orange_center = orange_rect[0]
            orange_angle = orange_rect[2]

            # Normalize angle
            if orange_angle < -45:
                orange_angle = 90 + orange_angle

            # Get top edge for reference line
            sorted_pts = sorted(orange_box, key=lambda p: p[1])
            top_edge = sorted_pts[:2]

            orange_info = {
                'rect': orange_rect,
                'box': orange_box,
                'center': orange_center,
                'angle': orange_angle,
                'top_edge': top_edge
            }

        # Analyze marking
        marking_info = None
        if marking_contours:
            # Filter large contours only
            large_contours = [c for c in marking_contours if cv2.contourArea(c) >= (w*h)*0.02]

            if large_contours:
                # Combine all large contours
                all_points = np.vstack(large_contours)
                marking_rect = cv2.minAreaRect(all_points)
                marking_box = cv2.boxPoints(marking_rect)
                marking_box = np.intp(marking_box)

                # Get center and angle
                marking_center = marking_rect[0]
                marking_angle = marking_rect[2]

                # Normalize angle
                if marking_angle < -45:
                    marking_angle = 90 + marking_angle

                # Get top edge for reference line
                sorted_pts = sorted(marking_box, key=lambda p: p[1])
                top_edge = sorted_pts[:2]

                marking_info = {
                    'rect': marking_rect,
                    'box': marking_box,
                    'center': marking_center,
                    'angle': marking_angle,
                    'top_edge': top_edge
                }

        # Draw alignment visualization
        # Create overlay for colored regions
        overlay = vis.copy()

        # Highlight orange regions
        orange_colored = np.zeros_like(image)
        orange_colored[orange_mask > 0] = (0, 165, 255)  # Orange in BGR
        cv2.addWeighted(overlay, 0.7, orange_colored, 0.3, 0, overlay)

        # Highlight marking regions (yellow/white as green for contrast)
        marking_colored = np.zeros_like(image)
        marking_colored[marking_mask > 0] = (0, 255, 128)  # Green
        cv2.addWeighted(overlay, 0.7, marking_colored, 0.3, 0, overlay)

        vis = overlay

        # Draw orange stencil analysis
        if orange_info:
            # Draw bounding box
            cv2.drawContours(vis, [orange_info['box']], 0, (0, 165, 255), 3)

            # Draw reference line (top edge)
            pt1 = tuple(orange_info['top_edge'][0].astype(int))
            pt2 = tuple(orange_info['top_edge'][1].astype(int))
            cv2.line(vis, pt1, pt2, (255, 128, 0), 4)

            # Draw center point
            cx, cy = int(orange_info['center'][0]), int(orange_info['center'][1])
            cv2.circle(vis, (cx, cy), 8, (0, 165, 255), -1)

            # Extend reference line for visualization
            dx = pt2[0] - pt1[0]
            dy = pt2[1] - pt1[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                # Normalize and extend
                dx_norm = dx / length
                dy_norm = dy / length
                extend = 200
                ext_pt1 = (int(pt1[0] - dx_norm * extend), int(pt1[1] - dy_norm * extend))
                ext_pt2 = (int(pt2[0] + dx_norm * extend), int(pt2[1] + dy_norm * extend))
                cv2.line(vis, ext_pt1, ext_pt2, (255, 128, 0), 2, cv2.LINE_AA)

            # Label
            cv2.putText(vis, f"ORANGE: {orange_info['angle']:.1f}deg",
                       (cx-80, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        # Draw marking analysis
        if marking_info:
            # Draw bounding box
            cv2.drawContours(vis, [marking_info['box']], 0, (0, 255, 128), 3)

            # Draw reference line (top edge)
            pt1 = tuple(marking_info['top_edge'][0].astype(int))
            pt2 = tuple(marking_info['top_edge'][1].astype(int))
            cv2.line(vis, pt1, pt2, (0, 255, 255), 4)

            # Draw center point
            cx, cy = int(marking_info['center'][0]), int(marking_info['center'][1])
            cv2.circle(vis, (cx, cy), 8, (0, 255, 128), -1)

            # Extend reference line
            dx = pt2[0] - pt1[0]
            dy = pt2[1] - pt1[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx_norm = dx / length
                dy_norm = dy / length
                extend = 200
                ext_pt1 = (int(pt1[0] - dx_norm * extend), int(pt1[1] - dy_norm * extend))
                ext_pt2 = (int(pt2[0] + dx_norm * extend), int(pt2[1] + dy_norm * extend))
                cv2.line(vis, ext_pt1, ext_pt2, (0, 255, 255), 2, cv2.LINE_AA)

            # Label
            cv2.putText(vis, f"MARKING: {marking_info['angle']:.1f}deg",
                       (cx-80, cy+40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)

        # Calculate alignment info
        if orange_info and marking_info:
            # Angle difference
            angle_diff = orange_info['angle'] - marking_info['angle']

            # Normalize to -180 to 180
            while angle_diff > 180:
                angle_diff -= 360
            while angle_diff < -180:
                angle_diff += 360

            # Center offset
            orange_cx = orange_info['center'][0]
            marking_cx = marking_info['center'][0]
            offset_x = orange_cx - marking_cx
            offset_percent = (offset_x / w) * 100

            # Determine alignment status
            rotation_aligned = abs(angle_diff) <= 5.0
            position_aligned = abs(offset_percent) <= 15.0
            fully_aligned = rotation_aligned and position_aligned

            # Draw alignment info box
            info_box_h = 160
            overlay_info = vis.copy()
            cv2.rectangle(overlay_info, (0, 0), (w, info_box_h), (0, 0, 0), -1)
            cv2.addWeighted(overlay_info, 0.7, vis, 0.3, 0, vis)

            # Status color
            color = (0, 255, 0) if fully_aligned else (0, 128, 255) if (rotation_aligned or position_aligned) else (0, 0, 255)

            # Text info
            cv2.putText(vis, f"Rotation Diff: {angle_diff:+.2f}deg",
                       (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(vis, f"Lateral Offset: {offset_x:+.1f}px ({offset_percent:+.1f}%)",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Status
            rot_status = "OK" if rotation_aligned else "NEEDS ADJUST"
            pos_status = "OK" if position_aligned else "NEEDS ADJUST"
            cv2.putText(vis, f"Rotation: {rot_status}  |  Position: {pos_status}",
                       (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Overall status
            if fully_aligned:
                status_text = "FULLY ALIGNED!"
            elif rotation_aligned:
                if offset_percent > 0:
                    status_text = f"Move RIGHT {abs(offset_percent):.1f}%"
                else:
                    status_text = f"Move LEFT {abs(offset_percent):.1f}%"
            elif position_aligned:
                if angle_diff > 0:
                    status_text = f"Rotate CW {abs(angle_diff):.1f}deg"
                else:
                    status_text = f"Rotate CCW {abs(angle_diff):.1f}deg"
            else:
                corrections = []
                if offset_percent > 0:
                    corrections.append(f"RIGHT {abs(offset_percent):.1f}%")
                else:
                    corrections.append(f"LEFT {abs(offset_percent):.1f}%")
                if angle_diff > 0:
                    corrections.append(f"CW {abs(angle_diff):.1f}deg")
                else:
                    corrections.append(f"CCW {abs(angle_diff):.1f}deg")
                status_text = "Move " + " + ".join(corrections)

            cv2.putText(vis, status_text,
                       (10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

            return vis, {
                'angle_diff': angle_diff,
                'offset_x': offset_x,
                'offset_percent': offset_percent,
                'rotation_aligned': rotation_aligned,
                'position_aligned': position_aligned,
                'fully_aligned': fully_aligned,
                'status': status_text
            }
        else:
            # No alignment info available
            cv2.putText(vis, "ERROR: Cannot detect both stencil and marking",
                       (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return vis, None


def process_images(datas_folder: str):
    """Process all images in datas folder"""

    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    image_files = []

    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(datas_folder, ext)))

    if not image_files:
        print("No images found in datas folder")
        return

    # Filter out already processed files
    image_files = [f for f in image_files if not any(prefix in os.path.basename(f)
                   for prefix in ['mask_', 'analyzed_', 'align_'])]

    print(f"\nFound {len(image_files)} images")
    print("="*70)

    visualizer = MaskAlignmentVisualizer()

    for img_path in sorted(image_files):
        image = cv2.imread(img_path)
        if image is None:
            continue

        print(f"\n{os.path.basename(img_path)}:")
        print("-"*70)

        # Create visualization
        vis, alignment_info = visualizer.create_alignment_visualization(image)

        if alignment_info:
            print(f"  Rotation Difference: {alignment_info['angle_diff']:+.2f} deg")
            print(f"  Lateral Offset: {alignment_info['offset_x']:+.1f} px ({alignment_info['offset_percent']:+.1f}%)")
            print(f"  Rotation Aligned: {'YES' if alignment_info['rotation_aligned'] else 'NO'}")
            print(f"  Position Aligned: {'YES' if alignment_info['position_aligned'] else 'NO'}")
            print(f"  Fully Aligned: {'YES' if alignment_info['fully_aligned'] else 'NO'}")
            print(f"  Action: {alignment_info['status']}")

        # Save
        output_path = os.path.join(datas_folder, f"align_{os.path.basename(img_path)}")
        cv2.imwrite(output_path, vis)
        print(f"  Saved: {os.path.basename(output_path)}")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("MASK-BASED ALIGNMENT VISUALIZER")
    print("="*70)
    print("\nShows:")
    print("  • Orange stencil reference line (orange)")
    print("  • Yellow/white marking reference line (cyan)")
    print("  • Rotation angle for both")
    print("  • Alignment status and corrections needed")
    print("="*70 + "\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    datas_folder = os.path.join(script_dir, "datas")

    if not os.path.exists(datas_folder):
        print(f"ERROR: 'datas' folder not found: {datas_folder}")
        return

    print(f"Processing images in: {datas_folder}\n")

    process_images(datas_folder)

    print("\n" + "="*70)
    print("Done! Check 'align_*.png' files in datas folder")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
