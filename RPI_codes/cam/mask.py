# -*- coding: utf-8 -*-
"""
Color Mask Visualizer
=====================

Detects and highlights different colors in the image as separate masks.
Shows what the camera actually sees for each color range.

Usage:
    python mask.py

Put your test images in the 'datas' folder.
"""

import cv2
import numpy as np
import os
import glob


class ColorMaskVisualizer:
    """Visualizes color detection masks for alignment system"""

    def __init__(self):
        """Initialize with predefined color ranges"""

        # Orange stencil (HSV)
        self.orange_lower = np.array([5, 150, 150])
        self.orange_upper = np.array([20, 255, 255])

        # Yellow marking (HSV)
        self.yellow_lower = np.array([15, 80, 80])
        self.yellow_upper = np.array([35, 255, 255])

        # White marking (HSV)
        self.white_lower = np.array([0, 0, 98])
        self.white_upper = np.array([180, 199, 254])

        # Black/Dark asphalt (HSV)
        self.black_lower = np.array([0, 0, 0])
        self.black_upper = np.array([180, 255, 50])

    def create_masks(self, image: np.ndarray):
        """
        Create color masks for all detected colors

        Returns:
            Dictionary of color masks
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create individual masks
        masks = {}

        # Orange stencil
        masks['orange'] = cv2.inRange(hsv, self.orange_lower, self.orange_upper)

        # Yellow marking
        masks['yellow'] = cv2.inRange(hsv, self.yellow_lower, self.yellow_upper)

        # White marking
        masks['white'] = cv2.inRange(hsv, self.white_lower, self.white_upper)

        # Black/Dark background
        masks['black'] = cv2.inRange(hsv, self.black_lower, self.black_upper)

        # Combined yellow+white (road marking)
        masks['marking'] = cv2.bitwise_or(masks['yellow'], masks['white'])

        # Clean up masks with morphological operations
        kernel = np.ones((3, 3), np.uint8)
        for color_name in masks:
            masks[color_name] = cv2.morphologyEx(masks[color_name], cv2.MORPH_OPEN, kernel)
            masks[color_name] = cv2.morphologyEx(masks[color_name], cv2.MORPH_CLOSE, kernel)

        return masks

    def create_colored_overlay(self, image: np.ndarray, masks: dict):
        """
        Create an overlay showing all detected colors

        Returns:
            Image with colored overlays
        """
        overlay = image.copy()

        # Define colors for each mask (BGR format)
        colors = {
            'orange': (0, 165, 255),   # Orange
            'yellow': (0, 255, 255),   # Yellow
            'white': (255, 255, 255),  # White
            'black': (128, 128, 128),  # Gray (for black areas)
        }

        # Apply colored overlays
        for color_name, color_bgr in colors.items():
            if color_name in masks:
                mask = masks[color_name]
                colored_mask = np.zeros_like(image)
                colored_mask[:] = color_bgr

                # Apply mask with transparency
                alpha = 0.6
                overlay = np.where(mask[:, :, np.newaxis] > 0,
                                  cv2.addWeighted(overlay, 1-alpha, colored_mask, alpha, 0),
                                  overlay)

        return overlay

    def create_grid_visualization(self, image: np.ndarray, masks: dict):
        """
        Create a grid showing original + all masks

        Returns:
            Grid image with all visualizations
        """
        h, w = image.shape[:2]

        # Convert masks to BGR for display
        mask_images = {}
        for name, mask in masks.items():
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            mask_images[name] = mask_bgr

        # Create colored versions
        colored_masks = {}
        colors = {
            'orange': (0, 165, 255),
            'yellow': (0, 255, 255),
            'white': (255, 255, 255),
            'black': (128, 128, 128),
            'marking': (0, 255, 128),  # Green for combined marking
        }

        for name, mask in masks.items():
            if name in colors:
                colored = np.zeros((h, w, 3), dtype=np.uint8)
                colored[mask > 0] = colors[name]
                colored_masks[name] = colored

        # Create overlay
        overlay = self.create_colored_overlay(image, masks)

        # Create grid layout (3 rows x 3 columns)
        # Row 1: Original | Orange Mask | Yellow Mask
        # Row 2: White Mask | Black Mask | Combined Marking
        # Row 3: Overlay | Orange Colored | Yellow Colored

        # Resize for grid
        scale = 0.5
        new_w = int(w * scale)
        new_h = int(h * scale)

        def resize_img(img):
            return cv2.resize(img, (new_w, new_h))

        # Row 1
        row1_col1 = resize_img(image.copy())
        cv2.putText(row1_col1, "ORIGINAL", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row1_col2 = resize_img(mask_images['orange'])
        cv2.putText(row1_col2, "ORANGE MASK", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row1_col3 = resize_img(mask_images['yellow'])
        cv2.putText(row1_col3, "YELLOW MASK", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row1 = np.hstack([row1_col1, row1_col2, row1_col3])

        # Row 2
        row2_col1 = resize_img(mask_images['white'])
        cv2.putText(row2_col1, "WHITE MASK", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row2_col2 = resize_img(mask_images['black'])
        cv2.putText(row2_col2, "BLACK MASK", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row2_col3 = resize_img(mask_images['marking'])
        cv2.putText(row2_col3, "MARKING (Y+W)", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row2 = np.hstack([row2_col1, row2_col2, row2_col3])

        # Row 3
        row3_col1 = resize_img(overlay)
        cv2.putText(row3_col1, "OVERLAY", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row3_col2 = resize_img(colored_masks['orange'])
        cv2.putText(row3_col2, "ORANGE COLORED", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row3_col3 = resize_img(colored_masks['yellow'])
        cv2.putText(row3_col3, "YELLOW COLORED", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        row3 = np.hstack([row3_col1, row3_col2, row3_col3])

        # Combine all rows
        grid = np.vstack([row1, row2, row3])

        # Add title bar
        title_bar = np.zeros((60, grid.shape[1], 3), dtype=np.uint8)
        cv2.putText(title_bar, "COLOR MASK VISUALIZATION", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

        final = np.vstack([title_bar, grid])

        return final

    def analyze_image(self, image: np.ndarray, output_path: str = None):
        """
        Analyze image and create visualizations

        Args:
            image: Input image
            output_path: Path to save output (optional)

        Returns:
            Grid visualization image
        """
        # Create masks
        masks = self.create_masks(image)

        # Calculate statistics
        stats = {}
        total_pixels = image.shape[0] * image.shape[1]

        for name, mask in masks.items():
            pixel_count = cv2.countNonZero(mask)
            percentage = (pixel_count / total_pixels) * 100
            stats[name] = {
                'pixels': pixel_count,
                'percentage': percentage
            }

        # Print statistics
        print("\n  Color Detection Statistics:")
        print("  " + "-"*50)
        for name, stat in stats.items():
            print(f"  {name.upper():12s}: {stat['pixels']:8d} px ({stat['percentage']:5.2f}%)")
        print("  " + "-"*50)

        # Create visualization
        grid = self.create_grid_visualization(image, masks)

        # Save if path provided
        if output_path:
            cv2.imwrite(output_path, grid)
            print(f"  Saved: {os.path.basename(output_path)}")

        return grid


def process_images(datas_folder: str):
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

    visualizer = ColorMaskVisualizer()

    for img_path in sorted(image_files):
        # Skip already processed files
        if 'mask_' in os.path.basename(img_path):
            continue

        image = cv2.imread(img_path)
        if image is None:
            continue

        print(f"\n{os.path.basename(img_path)}:")
        print("-"*70)

        # Create output path
        output_path = os.path.join(datas_folder, f"mask_{os.path.basename(img_path)}")

        # Analyze and save
        grid = visualizer.analyze_image(image, output_path)

        # Show window (optional - comment out for batch processing)
        # cv2.imshow('Color Masks', grid)
        # cv2.waitKey(0)


def main():
    """Main function"""
    print("\n" + "="*70)
    print("COLOR MASK VISUALIZER")
    print("="*70)
    print("\nShows color detection masks for:")
    print("  • Orange (stencil)")
    print("  • Yellow (marking)")
    print("  • White (marking)")
    print("  • Black (background)")
    print("  • Combined marking (yellow + white)")
    print("="*70 + "\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    datas_folder = os.path.join(script_dir, "datas")

    if not os.path.exists(datas_folder):
        print(f"ERROR: 'datas' folder not found: {datas_folder}")
        return

    print(f"Processing images in: {datas_folder}\n")

    process_images(datas_folder)

    print("\n" + "="*70)
    print("Done! Check 'mask_*.png' files in datas folder")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
