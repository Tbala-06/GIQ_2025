"""
Simple Stencil Alignment System - Yellow Detection Method

SIMPLE LOGIC:
- Detect orange stencil
- Divide it into 3 zones: LEFT | CENTER | RIGHT
- Check which zone has YELLOW pixels (road marking)
- If yellow in LEFT → Move RIGHT
- If yellow in RIGHT → Move LEFT
- If yellow in CENTER → ALIGNED!
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
import os
import glob


@dataclass
class AlignmentResult:
    """Simple alignment results"""
    zone_detected: str  # "LEFT", "CENTER", "RIGHT", or "NONE"
    horizontal_offset: float  # Approximate offset in pixels
    offset_percentage: float  # Offset as percentage of stencil width
    aligned: bool
    instruction: str
    debug_image: np.ndarray


class SimpleYellowAlignmentDetector:
    """Simple detector based on yellow pixel location"""
    
    def __init__(self, 
                 alignment_tolerance: float = 0.15,  # 15% tolerance
                 debug: bool = True):
        """
        Args:
            alignment_tolerance: How much of the width counts as "center" (0.15 = 15%)
            debug: Whether to generate debug visualization
        """
        self.alignment_tolerance = alignment_tolerance
        self.debug = debug
        
    def detect_orange_stencil(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detect the orange stencil frame - returns (x, y, w, h)"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Bright orange color range (calibrated for your stencil)
        # This matches the bright orange plastic material shown in your image
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
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        return (x, y, w, h)
    
    def detect_yellow_in_zones(self, image: np.ndarray, stencil_bbox: Tuple[int, int, int, int]) -> Tuple[str, float, float]:
        """
        Detect which zone contains yellow pixels
        Returns: (zone_name, offset_px, offset_percentage)
        """
        # IGNORE stencil_bbox - use entire image instead
        img_height, img_width = image.shape[:2]

        # ROI = entire image, full width and height
        roi_x = 0
        roi_y = 0  # Start from top
        roi_w = img_width
        roi_h = img_height  # Full height

        roi = image[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w].copy()
        
        # Convert to HSV
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Yellow/white color range - USING VALUES FROM COLOR DETECTION TOOL
        # These values were tested and confirmed to work with your setup
        
        # Yellow range (for yellow markings)
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])
        
        # White range - FROM YOUR TESTING: H:0-180, S:0-199, V:121-254
        lower_white = np.array([0, 0, 98])
        upper_white = np.array([180, 199, 254])
        
        # Create masks
        yellow_mask = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
        white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)
        
        # Combine masks
        marking_mask = cv2.bitwise_or(yellow_mask, white_mask)
        
        # Apply lighter morphological operations to clean up noise but keep thin lines
        kernel_small = np.ones((2, 2), np.uint8)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_OPEN, kernel_small)
        marking_mask = cv2.morphologyEx(marking_mask, cv2.MORPH_CLOSE, kernel_small)
        
        # FILTER OUT SMALL REGIONS - Only keep large chunks
        # Find all contours
        contours, _ = cv2.findContours(marking_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create new mask with only large regions
        filtered_mask = np.zeros_like(marking_mask)
        min_area = (roi_w * roi_h) * 0.02  # Must be at least 2% of search area
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                cv2.drawContours(filtered_mask, [contour], -1, 255, -1)
        
        marking_mask = filtered_mask
        
        # DEBUG: Save the mask for visualization
        self._debug_mask = marking_mask.copy()
        self._debug_roi_location = (roi_x, roi_y, roi_w, roi_h)
        
        # Define zones in the cleaned ROI
        # Left zone: 0 to 33%
        # Center zone: 33% to 67% 
        # Right zone: 67% to 100%
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
        
        # Calculate center of mass of all yellow pixels
        moments = cv2.moments(marking_mask)
        if moments["m00"] > 0:
            cx = moments["m10"] / moments["m00"]
            # Offset from center (in ROI coordinates)
            offset_px = cx - (roi_w / 2)
            # Calculate offset as percentage of width
            offset_percent = (offset_px / roi_w) * 100
        else:
            cx = roi_w / 2
            offset_px = 0
            offset_percent = 0
        
        # Determine which zone has the most yellow
        max_pixels = max(left_pixels, center_pixels, right_pixels)
        
        if max_pixels == 0:
            return "NONE", 0, 0
        
        # Require significant pixel count to declare a zone (reduces noise)
        min_threshold = 10  # Reduced from 20 to catch thinner lines
        
        if max_pixels < min_threshold:
            return "NONE", 0, 0
        
        if left_pixels == max_pixels:
            return "LEFT", offset_px, offset_percent
        elif right_pixels == max_pixels:
            return "RIGHT", offset_px, offset_percent
        else:
            return "CENTER", offset_px, offset_percent
    
    def analyze_alignment(self, image: np.ndarray) -> AlignmentResult:
        """Main analysis method"""
        height, width = image.shape[:2]
        debug_img = image.copy() if self.debug else None
        
        # Detect stencil
        stencil_bbox = self.detect_orange_stencil(image)

        if stencil_bbox is None:
            return AlignmentResult(
                zone_detected="NONE",
                horizontal_offset=0,
                offset_percentage=0,
                aligned=False,
                instruction="ERROR: Cannot detect orange stencil",
                debug_image=debug_img
            )
        
        x, y, w, h = stencil_bbox
        stencil_center_x = x + w/2
        
        # Detect yellow in zones
        zone, offset_px, offset_percent = self.detect_yellow_in_zones(image, stencil_bbox)
        
        # Determine if aligned
        is_aligned = (zone == "CENTER")
        
        # Generate instruction (FIXED LOGIC: LEFT->LEFT, RIGHT->RIGHT)
        if is_aligned:
            instruction = "ALIGNED ✓"
        elif zone == "LEFT":
            instruction = f"Move LEFT {abs(offset_percent):.1f}%"
        elif zone == "RIGHT":
            instruction = f"Move RIGHT {abs(offset_percent):.1f}%"
        else:
            instruction = "WARNING: No yellow/white detected"
        
        # Draw debug visualization
        if self.debug:
            # Draw stencil
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 165, 255), 3)
            cv2.putText(debug_img, "ORANGE STENCIL", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            # Draw ACTUAL search area - entire screen
            search_x = 0
            search_y = 0  # Start from top of frame
            search_w = width
            search_h = height  # Full height

            cv2.rectangle(debug_img, (search_x, search_y),
                         (search_x + search_w, search_y + search_h),
                         (255, 0, 255), 3)
            cv2.putText(debug_img, "SEARCH AREA (FULL SCREEN)", (search_x + 5, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

            # Draw zone boundaries (cyan vertical lines) - in the search area
            left_boundary = int(search_x + search_w * 0.33)
            right_boundary = int(search_x + search_w * 0.67)

            cv2.line(debug_img, (left_boundary, search_y),
                    (left_boundary, search_y + search_h), (255, 255, 0), 2)
            cv2.line(debug_img, (right_boundary, search_y),
                    (right_boundary, search_y + search_h), (255, 255, 0), 2)

            # Label zones
            cv2.putText(debug_img, "LEFT", (search_x+10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            cv2.putText(debug_img, "CENTER", (left_boundary+10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            cv2.putText(debug_img, "RIGHT", (right_boundary+10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw center line
            cv2.line(debug_img, (int(stencil_center_x), 0), 
                    (int(stencil_center_x), height), (0, 255, 255), 2)
            
            # Highlight detected zone
            zone_color = (0, 255, 0) if is_aligned else (0, 0, 255)
            if zone == "LEFT":
                zone_rect = (search_x, search_y, left_boundary-search_x, search_h)
            elif zone == "CENTER":
                zone_rect = (left_boundary, search_y, right_boundary-left_boundary, search_h)
            elif zone == "RIGHT":
                zone_rect = (right_boundary, search_y, search_x+search_w-right_boundary, search_h)
            else:
                zone_rect = None
            
            if zone_rect:
                overlay = debug_img.copy()
                rx, ry, rw, rh = zone_rect
                cv2.rectangle(overlay, (rx, ry), (rx+rw, ry+rh), zone_color, -1)
                cv2.addWeighted(overlay, 0.2, debug_img, 0.8, 0, debug_img)
            
            # Info overlay
            overlay = debug_img.copy()
            box_height = 140
            cv2.rectangle(overlay, (0, 0), (width, box_height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, debug_img, 0.4, 0, debug_img)
            
            # Text info
            color = (0, 255, 0) if is_aligned else (0, 0, 255)
            
            cv2.putText(debug_img, f"Zone: {zone}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(debug_img, f"Offset: {offset_px:.1f}px ({offset_percent:.1f}%)", 
                       (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(debug_img, instruction, 
                       (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Draw direction arrow
            if not is_aligned and zone != "NONE":
                self._draw_direction_arrow(debug_img, zone, width, height)
            
            # DEBUG: Show what pixels were detected (in corner)
            if hasattr(self, '_debug_mask') and self._debug_mask is not None:
                mask_vis = cv2.cvtColor(self._debug_mask, cv2.COLOR_GRAY2BGR)
                mask_vis = cv2.resize(mask_vis, (150, 100))
                
                # Place in bottom-left corner
                debug_img[height-110:height-10, 10:160] = mask_vis
                cv2.rectangle(debug_img, (10, height-110), (160, height-10), (255, 255, 255), 2)
                cv2.putText(debug_img, "DETECTION", (15, height-115), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return AlignmentResult(
            zone_detected=zone,
            horizontal_offset=offset_px,
            offset_percentage=offset_percent,
            aligned=is_aligned,
            instruction=instruction,
            debug_image=debug_img
        )
    
    def _draw_direction_arrow(self, img, zone, width, height):
        """Draw large directional arrow"""
        center_x = width - 100
        center_y = height - 100
        arrow_length = 60
        
        if zone == "LEFT":
            # Yellow in left → Move LEFT
            cv2.arrowedLine(img, (center_x + arrow_length//2, center_y), 
                          (center_x - arrow_length//2, center_y), 
                          (0, 255, 255), 6, tipLength=0.3)
            cv2.putText(img, "MOVE LEFT", (center_x-90, center_y-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        elif zone == "RIGHT":
            # Yellow in right → Move RIGHT
            cv2.arrowedLine(img, (center_x - arrow_length//2, center_y), 
                          (center_x + arrow_length//2, center_y), 
                          (0, 255, 255), 6, tipLength=0.3)
            cv2.putText(img, "MOVE RIGHT", (center_x-90, center_y-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)


def find_input_file(datas_folder: str):
    """Find image or video in datas folder"""
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv']
    
    for ext in image_extensions:
        files = glob.glob(os.path.join(datas_folder, ext))
        if files:
            return files[0], 'image'
    
    for ext in video_extensions:
        files = glob.glob(os.path.join(datas_folder, ext))
        if files:
            return files[0], 'video'
    
    return None, None


def process_image(image_path: str, detector: SimpleYellowAlignmentDetector):
    """Process single image"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"ERROR: Cannot read image: {image_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"Processing Image: {os.path.basename(image_path)}")
    print(f"{'='*70}\n")
    
    result = detector.analyze_alignment(image)
    
    print(f"Zone Detected: {result.zone_detected}")
    print(f"Horizontal Offset: {result.horizontal_offset:.1f} pixels ({result.offset_percentage:.1f}%)")
    print(f"Status: {result.instruction}")
    print(f"Aligned: {'YES ✓' if result.aligned else 'NO ✗'}")
    
    if result.debug_image is not None:
        output_dir = os.path.dirname(image_path)
        output_path = os.path.join(output_dir, f"analyzed_{os.path.basename(image_path)}")
        cv2.imwrite(output_path, result.debug_image)
        print(f"\nOutput saved to: {output_path}")
        
        display_img = result.debug_image.copy()
        max_height = 800
        if display_img.shape[0] > max_height:
            scale = max_height / display_img.shape[0]
            new_width = int(display_img.shape[1] * scale)
            display_img = cv2.resize(display_img, (new_width, max_height))
        
        cv2.imshow('SIMPLE Yellow Detection Alignment', display_img)
        print("\nPress any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    print(f"\n{'='*70}\n")


def process_video(video_path: str, detector: SimpleYellowAlignmentDetector):
    """Process video"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {video_path}")
        return
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n{'='*70}")
    print(f"Processing Video: {os.path.basename(video_path)}")
    print(f"Resolution: {width}x{height}, FPS: {fps}, Frames: {total_frames}")
    print(f"{'='*70}\n")
    
    output_dir = os.path.dirname(video_path)
    output_path = os.path.join(output_dir, f"analyzed_{os.path.basename(video_path)}")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print(f"Saving to: {output_path}\n")
    print("Controls: SPACE=Pause, S=Save frame, Q=Quit\n")
    
    frame_count = 0
    paused = False
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            result = detector.analyze_alignment(frame)
            display_frame = result.debug_image if result.debug_image is not None else frame
            
            cv2.putText(display_frame, f"Frame: {frame_count}/{total_frames}", 
                       (width - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            out.write(display_frame)
            
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% - {result.instruction}")
        else:
            display_frame = result.debug_image if result.debug_image is not None else frame
        
        cv2.imshow('SIMPLE Yellow Detection - Video', display_frame)
        
        key = cv2.waitKey(1 if not paused else 0) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
            print("\n" + ("PAUSED" if paused else "RESUMED"))
        elif key == ord('s'):
            frame_path = os.path.join(output_dir, f"frame_{frame_count}.png")
            cv2.imwrite(frame_path, display_frame)
            print(f"\nSaved: {frame_path}")
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"\n{'='*70}")
    print(f"Complete! Processed {frame_count} frames")
    print(f"{'='*70}\n")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("SIMPLE YELLOW DETECTION ALIGNMENT SYSTEM")
    print("="*70)
    print("\nStencil: ORANGE")
    print("Logic: Detect which zone contains yellow/white pixels")
    print("  LEFT zone → Move LEFT")
    print("  CENTER zone → ALIGNED ✓")
    print("  RIGHT zone → Move RIGHT")
    print("="*70 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datas_folder = os.path.join(script_dir, "datas")
    
    if not os.path.exists(datas_folder):
        print(f"ERROR: 'datas' folder not found!")
        print(f"Create: {datas_folder}")
        input("\nPress Enter to exit...")
        return
    
    print(f"Looking in: {datas_folder}")
    input_file, file_type = find_input_file(datas_folder)
    
    if input_file is None:
        print("\nERROR: No image/video found!")
        print("Add a file to 'datas' folder")
        input("\nPress Enter to exit...")
        return
    
    print(f"Found {file_type}: {os.path.basename(input_file)}\n")
    
    detector = SimpleYellowAlignmentDetector(
        alignment_tolerance=0.15,  # 15% center tolerance
        debug=True
    )
    
    if file_type == 'image':
        process_image(input_file, detector)
    else:
        process_video(input_file, detector)
    
    print("\nDone! Output in 'datas' folder")


if __name__ == "__main__":
    main()