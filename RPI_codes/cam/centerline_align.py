# -*- coding: utf-8 -*-
"""
Center Line Alignment Visualizer
=================================

Uses center lines to visualize alignment:
1. Vertical line through middle of image (stencil center)
2. Rectangle around yellow marking
3. Center line through narrower width of marking rectangle
4. Calculate angle between the two center lines

Usage:
    python centerline_align.py
"""

import cv2
import numpy as np
import os
import glob
import math


class CenterLineAlignmentVisualizer:
    """Visualizes alignment using center lines"""

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

    def create_centerline_visualization(self, image: np.ndarray):
        """
        Create alignment visualization with center lines

        Returns:
            Visualization image with alignment info
        """
        h, w = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create marking mask (yellow + white)
        yellow_mask = cv2.inRange(hsv, self.yellow_lower, self.yellow_upper)
        white_mask = cv2.inRange(hsv, self.white_lower, self.white_upper)
        marking_mask = cv2.bitwise_or(yellow_mask, white_mask)

        # Clean up mask
        kernel = np.ones((3, 3), np.uint8)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_CLOSE, kernel)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_OPEN, kernel)

        # Create visualization
        vis = image.copy()

        # 1. STENCIL CENTER LINE (vertical line through middle of image)
        stencil_center_x = w // 2
        stencil_line_p1 = (stencil_center_x, 0)
        stencil_line_p2 = (stencil_center_x, h)

        # Draw stencil center line (purple/magenta)
        cv2.line(vis, stencil_line_p1, stencil_line_p2, (255, 0, 255), 3)
        cv2.putText(vis, "STENCIL CENTER", (stencil_center_x + 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

        # 2. DETECT ORANGE STENCIL FIRST
        orange_mask = cv2.inRange(hsv, self.orange_lower, self.orange_upper)
        orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_CLOSE, kernel)
        orange_mask = cv2.morphologyEx(orange_mask, cv2.MORPH_OPEN, kernel)

        # Get orange stencil contour for its center line
        orange_contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        orange_center_line = None

        if orange_contours:
            largest_orange = max(orange_contours, key=cv2.contourArea)
            if cv2.contourArea(largest_orange) >= (w*h)*0.02:
                # Fit line through orange stencil
                [ovx, ovy, ox0, oy0] = cv2.fitLine(largest_orange, cv2.DIST_L2, 0, 0.01, 0.01)
                orange_angle = np.degrees(np.arctan2(ovx[0], ovy[0]))

                # Normalize angle
                while orange_angle > 90:
                    orange_angle -= 180
                while orange_angle < -90:
                    orange_angle += 180

                orange_center_line = {
                    'vx': ovx[0],
                    'vy': ovy[0],
                    'x0': ox0[0],
                    'y0': oy0[0],
                    'angle': orange_angle
                }

        # 3. MARKING RECTANGLE
        # Subtract orange from marking to get only the road marking underneath
        marking_only = cv2.bitwise_and(marking_mask, cv2.bitwise_not(orange_mask))

        marking_contours, _ = cv2.findContours(marking_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not marking_contours:
            cv2.putText(vis, "ERROR: No yellow/white marking detected",
                       (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return vis, None

        # Filter large contours only
        large_contours = [c for c in marking_contours if cv2.contourArea(c) >= (w*h)*0.01]

        if not large_contours:
            cv2.putText(vis, "ERROR: Marking too small",
                       (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return vis, None

        # Use the LARGEST contour (most prominent marking) instead of combining all
        # This captures the main diagonal road marking stripe
        largest_contour = max(large_contours, key=cv2.contourArea)
        all_points = largest_contour
        marking_rect = cv2.minAreaRect(all_points)

        # Get rectangle properties
        (rect_center_x, rect_center_y), (rect_width, rect_height), rect_angle = marking_rect

        # Get the 4 corner points
        marking_box = cv2.boxPoints(marking_rect)
        marking_box = np.intp(marking_box)

        # Draw the rectangle
        cv2.drawContours(vis, [marking_box], 0, (0, 255, 255), 2)

        # 3. FIT A LINE THROUGH THE MARKING POINTS
        # Use cv2.fitLine to get the actual orientation of the marking
        [vx, vy, x0, y0] = cv2.fitLine(all_points, cv2.DIST_L2, 0, 0.01, 0.01)

        # Calculate angle from the line direction vector
        # vy/vx gives the slope, atan2 gives the angle
        # We want angle from vertical (90 degrees), so we use atan2(vx, vy)
        centerline_angle = np.degrees(np.arctan2(vx[0], vy[0]))

        # Normalize angle to -90 to 90
        while centerline_angle > 90:
            centerline_angle -= 180
        while centerline_angle < -90:
            centerline_angle += 180

        # For dimensions, still use the rectangle
        if rect_width < rect_height:
            narrower_dim = rect_width
            longer_dim = rect_height
        else:
            narrower_dim = rect_height
            longer_dim = rect_width

        # 4. DRAW YELLOW MARKING EDGE BORDERS (extended)
        # Get the 4 corners of the rectangle
        # marking_box contains: [bottom-left, top-left, top-right, bottom-right] (approximately)
        # We need to find the two parallel edges (the long sides of the marking)

        # Sort box points to get the two longest edges
        # The rectangle has 4 edges - we want the two parallel ones that define the marking width
        box_sorted = sorted(marking_box, key=lambda p: (p[1], p[0]))  # Sort by y, then x

        # Get direction vector perpendicular to centerline (for width)
        perp_dx = -math.sin(math.radians(centerline_angle))
        perp_dy = math.cos(math.radians(centerline_angle))

        # Calculate offset distance (half the narrow width)
        offset_dist = narrower_dim / 2.0

        # Calculate the two edge lines (parallel to centerline, offset by half width)
        line_length = max(w, h) * 2

        # Edge 1 (one side of marking)
        edge1_center_x = rect_center_x + perp_dx * offset_dist
        edge1_center_y = rect_center_y + perp_dy * offset_dist
        edge1_p1 = (
            int(edge1_center_x - math.cos(math.radians(centerline_angle)) * line_length),
            int(edge1_center_y - math.sin(math.radians(centerline_angle)) * line_length)
        )
        edge1_p2 = (
            int(edge1_center_x + math.cos(math.radians(centerline_angle)) * line_length),
            int(edge1_center_y + math.sin(math.radians(centerline_angle)) * line_length)
        )

        # Edge 2 (other side of marking)
        edge2_center_x = rect_center_x - perp_dx * offset_dist
        edge2_center_y = rect_center_y - perp_dy * offset_dist
        edge2_p1 = (
            int(edge2_center_x - math.cos(math.radians(centerline_angle)) * line_length),
            int(edge2_center_y - math.sin(math.radians(centerline_angle)) * line_length)
        )
        edge2_p2 = (
            int(edge2_center_x + math.cos(math.radians(centerline_angle)) * line_length),
            int(edge2_center_y + math.sin(math.radians(centerline_angle)) * line_length)
        )

        # Draw edge borders (yellow)
        cv2.line(vis, edge1_p1, edge1_p2, (0, 255, 255), 2)
        cv2.line(vis, edge2_p1, edge2_p2, (0, 255, 255), 2)
        cv2.putText(vis, "EDGE 1", (edge1_p1[0]+5, edge1_p1[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.putText(vis, "EDGE 2", (edge2_p1[0]+5, edge2_p1[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # 5. DRAW MARKING CENTER LINE (middle between the two edges)
        marking_line_p1 = (
            int(rect_center_x - math.cos(math.radians(centerline_angle)) * line_length),
            int(rect_center_y - math.sin(math.radians(centerline_angle)) * line_length)
        )
        marking_line_p2 = (
            int(rect_center_x + math.cos(math.radians(centerline_angle)) * line_length),
            int(rect_center_y + math.sin(math.radians(centerline_angle)) * line_length)
        )

        # Draw marking center line (green - middle of yellow edges)
        cv2.line(vis, marking_line_p1, marking_line_p2, (0, 255, 0), 3)
        cv2.putText(vis, "MARKING CENTER", (int(rect_center_x) + 10, int(rect_center_y) + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw rectangle center point
        cv2.circle(vis, (int(rect_center_x), int(rect_center_y)), 8, (0, 255, 0), -1)

        # 6. DRAW ORANGE STENCIL CENTER LINE
        if orange_center_line:
            orange_line_p1 = (
                int(orange_center_line['x0'] - orange_center_line['vx'] * line_length),
                int(orange_center_line['y0'] - orange_center_line['vy'] * line_length)
            )
            orange_line_p2 = (
                int(orange_center_line['x0'] + orange_center_line['vx'] * line_length),
                int(orange_center_line['y0'] + orange_center_line['vy'] * line_length)
            )

            # Draw orange center line (orange)
            cv2.line(vis, orange_line_p1, orange_line_p2, (0, 165, 255), 3)
            cv2.putText(vis, f"ORANGE CENTER ({orange_center_line['angle']:.1f}deg)",
                       (int(orange_center_line['x0']) + 10, int(orange_center_line['y0']) - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        # 5. CALCULATE ANGLE BETWEEN CENTER LINES
        # Stencil line is vertical (90 degrees)
        # Marking line is at centerline_angle
        # Rotation difference = how much to rotate to align

        rotation_diff = centerline_angle - 90

        # Normalize to -90 to 90
        while rotation_diff > 90:
            rotation_diff -= 180
        while rotation_diff < -90:
            rotation_diff += 180

        # 6. CALCULATE LATERAL OFFSET
        # Horizontal distance between stencil center and marking center
        lateral_offset_px = rect_center_x - stencil_center_x
        lateral_offset_percent = (lateral_offset_px / w) * 100

        # 7. DETERMINE ALIGNMENT STATUS
        rotation_aligned = abs(rotation_diff) <= 5.0
        position_aligned = abs(lateral_offset_percent) <= 15.0
        fully_aligned = rotation_aligned and position_aligned

        # 8. DRAW INFO BOX
        info_box_h = 180
        overlay_info = vis.copy()
        cv2.rectangle(overlay_info, (0, 0), (w, info_box_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay_info, 0.7, vis, 0.3, 0, vis)

        # Status color
        color = (0, 255, 0) if fully_aligned else (0, 128, 255) if (rotation_aligned or position_aligned) else (0, 0, 255)

        # Text info
        if orange_center_line:
            cv2.putText(vis, f"Orange Stencil: {orange_center_line['angle']:.2f}deg",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.putText(vis, f"Marking Angle: {centerline_angle:.2f}deg",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            angle_between = orange_center_line['angle'] - centerline_angle
            cv2.putText(vis, f"Angle Between: {angle_between:+.2f}deg",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            cv2.putText(vis, f"Marking Angle: {centerline_angle:.2f}deg (from horizontal)",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(vis, f"Rotation Diff: {rotation_diff:+.2f}deg (from vertical)",
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(vis, f"Lateral Offset: {lateral_offset_px:+.1f}px ({lateral_offset_percent:+.1f}%)",
                   (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Status
        rot_status = "OK" if rotation_aligned else "ADJUST"
        pos_status = "OK" if position_aligned else "ADJUST"
        cv2.putText(vis, f"Rotation: {rot_status}  |  Position: {pos_status}",
                   (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Overall instruction
        if fully_aligned:
            status_text = "FULLY ALIGNED!"
        else:
            corrections = []
            if not position_aligned:
                if lateral_offset_percent > 0:
                    corrections.append(f"Move LEFT {abs(lateral_offset_percent):.1f}%")
                else:
                    corrections.append(f"Move RIGHT {abs(lateral_offset_percent):.1f}%")
            if not rotation_aligned:
                if rotation_diff > 0:
                    corrections.append(f"Rotate CCW {abs(rotation_diff):.1f}deg")
                else:
                    corrections.append(f"Rotate CW {abs(rotation_diff):.1f}deg")
            status_text = " + ".join(corrections) if corrections else "OK"

        cv2.putText(vis, status_text,
                   (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)

        # Add dimension annotations
        cv2.putText(vis, f"Rect: W={rect_width:.0f}px H={rect_height:.0f}px",
                   (10, h-40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(vis, f"Narrow={narrower_dim:.0f}px Long={longer_dim:.0f}px",
                   (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return vis, {
            'marking_angle': centerline_angle,
            'rotation_diff': rotation_diff,
            'lateral_offset_px': lateral_offset_px,
            'lateral_offset_percent': lateral_offset_percent,
            'rotation_aligned': rotation_aligned,
            'position_aligned': position_aligned,
            'fully_aligned': fully_aligned,
            'status': status_text,
            'rect_width': rect_width,
            'rect_height': rect_height,
            'narrower_dim': narrower_dim,
            'longer_dim': longer_dim
        }


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
                   for prefix in ['mask_', 'analyzed_', 'align_', 'centerline_'])]

    print(f"\nFound {len(image_files)} images")
    print("="*70)

    visualizer = CenterLineAlignmentVisualizer()

    for img_path in sorted(image_files):
        image = cv2.imread(img_path)
        if image is None:
            continue

        print(f"\n{os.path.basename(img_path)}:")
        print("-"*70)

        # Create visualization
        vis, alignment_info = visualizer.create_centerline_visualization(image)

        if alignment_info:
            print(f"  Marking Angle: {alignment_info['marking_angle']:.2f} deg")
            print(f"  Rotation Diff: {alignment_info['rotation_diff']:+.2f} deg")
            print(f"  Lateral Offset: {alignment_info['lateral_offset_px']:+.1f} px ({alignment_info['lateral_offset_percent']:+.1f}%)")
            print(f"  Rectangle: W={alignment_info['rect_width']:.0f}px H={alignment_info['rect_height']:.0f}px")
            print(f"  Narrow={alignment_info['narrower_dim']:.0f}px Long={alignment_info['longer_dim']:.0f}px")
            print(f"  Rotation Aligned: {'YES' if alignment_info['rotation_aligned'] else 'NO'}")
            print(f"  Position Aligned: {'YES' if alignment_info['position_aligned'] else 'NO'}")
            print(f"  Fully Aligned: {'YES' if alignment_info['fully_aligned'] else 'NO'}")
            print(f"  Action: {alignment_info['status']}")

        # Save
        output_path = os.path.join(datas_folder, f"centerline_{os.path.basename(img_path)}")
        cv2.imwrite(output_path, vis)
        print(f"  Saved: {os.path.basename(output_path)}")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("CENTER LINE ALIGNMENT VISUALIZER")
    print("="*70)
    print("\nMethod:")
    print("  1. Purple line = Stencil center (vertical through image middle)")
    print("  2. Cyan rectangle = Yellow/white marking boundary")
    print("  3. Cyan line = Marking center (through narrow width)")
    print("  4. Calculate angle between the two center lines")
    print("="*70 + "\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    datas_folder = os.path.join(script_dir, "datas")

    if not os.path.exists(datas_folder):
        print(f"ERROR: 'datas' folder not found: {datas_folder}")
        return

    print(f"Processing images in: {datas_folder}\n")

    process_images(datas_folder)

    print("\n" + "="*70)
    print("Done! Check 'centerline_*.png' files in datas folder")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
