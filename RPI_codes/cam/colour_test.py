# -*- coding: utf-8 -*-
"""
Interactive Color Detection Tool
Helps you find the perfect HSV color ranges for your application

Usage:
1. Put an image in 'datas' folder
2. Run the script
3. Adjust HSV sliders to isolate your target color
4. Press 'S' to save the values
5. Press 'Q' to quit
"""

import cv2
import numpy as np
import os
import glob


class ColorDetectionTool:
    """Interactive tool to find HSV color ranges"""
    
    def __init__(self):
        self.window_name = "Color Detection Tool"
        self.image = None
        self.hsv_image = None
        
        # Default HSV ranges (for white)
        self.h_min = 0
        self.h_max = 180
        self.s_min = 0
        self.s_max = 30
        self.v_min = 200
        self.v_max = 255
        
    def load_image(self, image_path):
        """Load image and create trackbars"""
        self.image = cv2.imread(image_path)
        if self.image is None:
            print(f"ERROR: Cannot read image: {image_path}")
            return False
        
        # Resize if too large
        max_width = 1200
        height, width = self.image.shape[:2]
        if width > max_width:
            scale = max_width / width
            new_height = int(height * scale)
            self.image = cv2.resize(self.image, (max_width, new_height))
        
        self.hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        
        # Create window and trackbars
        cv2.namedWindow(self.window_name)
        
        cv2.createTrackbar('H Min', self.window_name, self.h_min, 179, self.on_trackbar)
        cv2.createTrackbar('H Max', self.window_name, self.h_max, 179, self.on_trackbar)
        cv2.createTrackbar('S Min', self.window_name, self.s_min, 255, self.on_trackbar)
        cv2.createTrackbar('S Max', self.window_name, self.s_max, 255, self.on_trackbar)
        cv2.createTrackbar('V Min', self.window_name, self.v_min, 255, self.on_trackbar)
        cv2.createTrackbar('V Max', self.window_name, self.v_max, 255, self.on_trackbar)
        
        return True
    
    def on_trackbar(self, val):
        """Trackbar callback"""
        pass  # Update happens in main loop
    
    def update_values(self):
        """Get current trackbar values"""
        self.h_min = cv2.getTrackbarPos('H Min', self.window_name)
        self.h_max = cv2.getTrackbarPos('H Max', self.window_name)
        self.s_min = cv2.getTrackbarPos('S Min', self.window_name)
        self.s_max = cv2.getTrackbarPos('S Max', self.window_name)
        self.v_min = cv2.getTrackbarPos('V Min', self.window_name)
        self.v_max = cv2.getTrackbarPos('V Max', self.window_name)
    
    def process_frame(self):
        """Process and display the frame with current HSV values"""
        self.update_values()
        
        # Create mask with current HSV values
        lower = np.array([self.h_min, self.s_min, self.v_min])
        upper = np.array([self.h_max, self.s_max, self.v_max])
        
        mask = cv2.inRange(self.hsv_image, lower, upper)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create output image
        output = self.image.copy()
        
        # Draw all contours and bounding boxes
        total_pixels = 0
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 20:  # Minimum area to reduce noise
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Draw contour in green
                cv2.drawContours(output, [contour], -1, (0, 255, 0), 2)
                
                # Draw bounding box in blue
                cv2.rectangle(output, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Add label with area
                label = f"#{i+1}: {int(area)}px"
                cv2.putText(output, label, (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                
                total_pixels += area
        
        # Create mask visualization (colorize it)
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_colored[mask > 0] = [0, 255, 255]  # Yellow for detected areas
        
        # Blend mask with original
        blended = cv2.addWeighted(output, 0.7, mask_colored, 0.3, 0)
        
        # Add info panel
        info_height = 120
        info_panel = np.zeros((info_height, blended.shape[1], 3), dtype=np.uint8)
        
        # Display current HSV values
        cv2.putText(info_panel, f"HSV Range:", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(info_panel, f"H: {self.h_min}-{self.h_max}  S: {self.s_min}-{self.s_max}  V: {self.v_min}-{self.v_max}", 
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.putText(info_panel, f"Detected: {len(contours)} regions, {int(total_pixels)} pixels", 
                   (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.putText(info_panel, "Press 'S' to save values | 'R' to reset | 'Q' to quit", 
                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Combine everything
        final = np.vstack([info_panel, blended])
        
        return final, mask, len(contours), total_pixels
    
    def save_values(self, output_dir):
        """Save current HSV values to file"""
        output_path = os.path.join(output_dir, "hsv_values.txt")
        
        with open(output_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("DETECTED HSV COLOR RANGE\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("Python/OpenCV Format:\n")
            f.write(f"lower = np.array([{self.h_min}, {self.s_min}, {self.v_min}])\n")
            f.write(f"upper = np.array([{self.h_max}, {self.s_max}, {self.v_max}])\n\n")
            
            f.write("Individual Values:\n")
            f.write(f"H (Hue):        {self.h_min} - {self.h_max}\n")
            f.write(f"S (Saturation): {self.s_min} - {self.s_max}\n")
            f.write(f"V (Value):      {self.v_min} - {self.v_max}\n\n")
            
            f.write("Color Guide:\n")
            f.write("- H (Hue): 0-10=Red, 10-30=Orange/Yellow, 30-90=Green, 90-130=Cyan/Blue, 130-170=Purple\n")
            f.write("- S (Saturation): 0=Gray/White, 255=Pure color\n")
            f.write("- V (Value): 0=Black, 255=Bright\n")
        
        print(f"\n✓ Values saved to: {output_path}")
        print(f"\nCopy this into your code:")
        print(f"lower = np.array([{self.h_min}, {self.s_min}, {self.v_min}])")
        print(f"upper = np.array([{self.h_max}, {self.s_max}, {self.v_max}])")
    
    def load_preset(self, preset_name):
        """Load preset HSV values"""
        presets = {
            'white': {'h': (0, 180), 's': (0, 30), 'v': (200, 255)},
            'yellow': {'h': (15, 35), 's': (80, 255), 'v': (80, 255)},
            'red': {'h': (0, 10), 's': (100, 255), 'v': (100, 255)},
            'green': {'h': (40, 80), 's': (50, 255), 'v': (50, 255)},
            'blue': {'h': (90, 130), 's': (50, 255), 'v': (50, 255)},
            'all': {'h': (0, 180), 's': (0, 255), 'v': (0, 255)},
        }
        
        if preset_name in presets:
            p = presets[preset_name]
            cv2.setTrackbarPos('H Min', self.window_name, p['h'][0])
            cv2.setTrackbarPos('H Max', self.window_name, p['h'][1])
            cv2.setTrackbarPos('S Min', self.window_name, p['s'][0])
            cv2.setTrackbarPos('S Max', self.window_name, p['s'][1])
            cv2.setTrackbarPos('V Min', self.window_name, p['v'][0])
            cv2.setTrackbarPos('V Max', self.window_name, p['v'][1])
            print(f"Loaded preset: {preset_name}")
    
    def run(self, image_path, output_dir):
        """Main loop"""
        if not self.load_image(image_path):
            return
        
        print("\n" + "="*60)
        print("COLOR DETECTION TOOL")
        print("="*60)
        print("\nControls:")
        print("  Adjust sliders to isolate your target color")
        print("  S - Save HSV values to file")
        print("  R - Reset to white detection")
        print("  1 - Preset: White")
        print("  2 - Preset: Yellow")
        print("  3 - Preset: Red")
        print("  4 - Preset: Show All")
        print("  Q - Quit")
        print("\n" + "="*60 + "\n")
        
        while True:
            # Process and display
            display, mask, num_regions, total_pixels = self.process_frame()
            cv2.imshow(self.window_name, display)
            
            # Handle keyboard
            key = cv2.waitKey(30) & 0xFF
            
            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord('s'):
                self.save_values(output_dir)
            elif key == ord('r'):
                self.load_preset('white')
            elif key == ord('1'):
                self.load_preset('white')
            elif key == ord('2'):
                self.load_preset('yellow')
            elif key == ord('3'):
                self.load_preset('red')
            elif key == ord('4'):
                self.load_preset('all')
        
        cv2.destroyAllWindows()


def find_input_file(datas_folder):
    """Find image in datas folder"""
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
    
    for ext in image_extensions:
        files = glob.glob(os.path.join(datas_folder, ext))
        if files:
            return files[0]
    
    return None


def main():
    """Main function"""
    print("\n" + "="*60)
    print("HSV COLOR DETECTION TOOL")
    print("="*60 + "\n")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datas_folder = os.path.join(script_dir, "datas")
    
    # Check if datas folder exists
    if not os.path.exists(datas_folder):
        print(f"ERROR: 'datas' folder not found!")
        print(f"Expected location: {datas_folder}")
        print("\nPlease create the folder and add your image:")
        print(f"  mkdir {datas_folder}")
        print(f"  # Copy your image to {datas_folder}")
        input("\nPress Enter to exit...")
        return
    
    # Find input file
    print(f"Looking for image in: {datas_folder}")
    input_file = find_input_file(datas_folder)
    
    if input_file is None:
        print("\nERROR: No image found in 'datas' folder!")
        print("\nSupported formats: .png, .jpg, .jpeg, .bmp")
        print(f"Please add an image to: {datas_folder}")
        input("\nPress Enter to exit...")
        return
    
    print(f"Found image: {os.path.basename(input_file)}\n")
    
    # Run the tool
    tool = ColorDetectionTool()
    tool.run(input_file, datas_folder)
    
    print("\n" + "="*60)
    print("Done! Check 'datas/hsv_values.txt' for saved values")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()