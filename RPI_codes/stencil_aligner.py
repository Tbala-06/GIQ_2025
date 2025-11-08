#!/usr/bin/env python3
"""
Stencil Alignment Module
========================

Wrapper for camera-based stencil alignment using the yellow detection method.
Integrates with testing.py's SimpleYellowAlignmentDetector.

The alignment strategy:
1. Detect orange stencil frame
2. Detect yellow road marking within frame
3. Determine which zone (LEFT/CENTER/RIGHT) contains yellow
4. Calculate offset and provide movement instructions

Author: GIQ 2025 Team
"""

import cv2
import numpy as np
import logging
import threading
import time
from typing import Optional, Tuple
from dataclasses import dataclass

# Import the existing alignment detector from testing.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cam'))

try:
    from testing import SimpleYellowAlignmentDetector, AlignmentResult
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False
    logging.warning("Could not import SimpleYellowAlignmentDetector - alignment disabled")

# Import configuration
try:
    from ev3_config import *
except ImportError:
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 1920
    CAMERA_HEIGHT = 1080
    PIXELS_PER_CM = 10.0
    POSITION_TOLERANCE_CM = 2.0
    SIMULATION_MODE = False

logger = logging.getLogger(__name__)


@dataclass
class AlignmentInstruction:
    """
    Alignment instruction with physical measurements.
    """
    aligned: bool  # True if robot is aligned
    direction: str  # "LEFT", "RIGHT", "FORWARD", "BACKWARD", "ALIGNED", "ERROR"
    distance_cm: float  # Distance to move (0 if aligned)
    offset_percentage: float  # How far off we are (%)
    confidence: float  # Confidence 0-1 (based on stencil detection)
    message: str  # Human-readable instruction
    debug_image: Optional[np.ndarray] = None  # Debug visualization


class StencilAligner:
    """
    Camera-based stencil alignment system.

    Features:
    - Threaded camera capture for non-blocking operation
    - Integration with existing yellow detection algorithm
    - Converts pixel offsets to physical movements (cm)
    - Provides debug visualization

    Usage:
        aligner = StencilAligner()
        aligner.start()

        instruction = aligner.get_alignment_instruction()
        if not instruction.aligned:
            print(f"Move {instruction.direction} by {instruction.distance_cm}cm")

        aligner.stop()
    """

    def __init__(self,
                 camera_index: int = CAMERA_INDEX,
                 pixels_per_cm: float = PIXELS_PER_CM,
                 tolerance_cm: float = POSITION_TOLERANCE_CM,
                 simulate: bool = SIMULATION_MODE):
        """
        Initialize stencil aligner.

        Args:
            camera_index: Camera device index
            pixels_per_cm: Calibration factor for pixel-to-cm conversion
            tolerance_cm: Alignment tolerance (cm)
            simulate: If True, uses test images instead of camera
        """
        self.camera_index = camera_index
        self.pixels_per_cm = pixels_per_cm
        self.tolerance_cm = tolerance_cm
        self.simulate = simulate

        # Camera capture
        self.camera = None
        self.capture_thread = None
        self.running = False
        self.frame_lock = threading.Lock()
        self.latest_frame = None

        # Alignment detector
        if DETECTOR_AVAILABLE:
            self.detector = SimpleYellowAlignmentDetector(debug=True)
        else:
            self.detector = None
            logger.warning("Alignment detector not available")

        logger.info(f"StencilAligner initialized (simulate={simulate}, px/cm={pixels_per_cm})")

    def start(self) -> bool:
        """
        Start camera capture thread.

        Returns:
            True if started successfully
        """
        if self.simulate:
            logger.info("Simulation mode - no camera started")
            return True

        try:
            # Open camera
            self.camera = cv2.VideoCapture(self.camera_index)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False

            # Start capture thread
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

            # Wait for first frame
            timeout = 5.0
            start_time = time.time()
            while self.latest_frame is None and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.latest_frame is None:
                logger.error("Camera timeout - no frames captured")
                return False

            logger.info("✓ Camera started")
            return True

        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False

    def _capture_loop(self):
        """Background thread for continuous camera capture"""
        logger.info("Camera capture thread started")

        while self.running:
            try:
                ret, frame = self.camera.read()
                if ret:
                    with self.frame_lock:
                        self.latest_frame = frame
                else:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.1)

        logger.info("Camera capture thread stopped")

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent camera frame.

        Returns:
            Latest frame or None if not available
        """
        if self.simulate:
            # In simulation, try to load a test image
            test_image_path = os.path.join(os.path.dirname(__file__), 'cam', 'datas', 'test_image.jpg')
            if os.path.exists(test_image_path):
                return cv2.imread(test_image_path)
            else:
                # Create a blank test image
                return np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)

        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def get_alignment_instruction(self) -> AlignmentInstruction:
        """
        Analyze current frame and get alignment instruction.

        Returns:
            AlignmentInstruction with movement command
        """
        # Get latest frame
        frame = self.get_latest_frame()

        if frame is None:
            return AlignmentInstruction(
                aligned=False,
                direction="ERROR",
                distance_cm=0,
                offset_percentage=0,
                confidence=0.0,
                message="No camera frame available"
            )

        if not self.detector:
            return AlignmentInstruction(
                aligned=False,
                direction="ERROR",
                distance_cm=0,
                offset_percentage=0,
                confidence=0.0,
                message="Alignment detector not available"
            )

        try:
            # Run alignment detection
            result = self.detector.analyze_alignment(frame)

            # Convert to physical instruction
            instruction = self._result_to_instruction(result)

            return instruction

        except Exception as e:
            logger.error(f"Alignment analysis failed: {e}")
            return AlignmentInstruction(
                aligned=False,
                direction="ERROR",
                distance_cm=0,
                offset_percentage=0,
                confidence=0.0,
                message=f"Analysis error: {e}"
            )

    def _result_to_instruction(self, result: AlignmentResult) -> AlignmentInstruction:
        """
        Convert AlignmentResult to physical movement instruction.

        Args:
            result: AlignmentResult from detector

        Returns:
            AlignmentInstruction with movement commands
        """
        # Check if aligned
        is_aligned = result.aligned

        # Calculate distance to move based on offset
        # Using percentage of frame width as proxy for distance
        # This is approximate - may need tuning based on camera height
        distance_cm = abs(result.offset_percentage) * 2.0  # Scale factor to convert % to cm

        # Determine direction
        zone = result.zone_detected

        if zone == "CENTER" or is_aligned:
            direction = "ALIGNED"
            distance_cm = 0
            message = "✓ Aligned - ready to paint"
            confidence = 0.9

        elif zone == "LEFT":
            direction = "LEFT"
            message = f"Move LEFT {distance_cm:.1f}cm"
            confidence = 0.8

        elif zone == "RIGHT":
            direction = "RIGHT"
            message = f"Move RIGHT {distance_cm:.1f}cm"
            confidence = 0.8

        elif zone == "NONE":
            direction = "ERROR"
            distance_cm = 0
            message = "Cannot detect yellow marking - reposition robot"
            confidence = 0.0

        else:
            direction = "ERROR"
            distance_cm = 0
            message = f"Unknown zone: {zone}"
            confidence = 0.0

        # Apply tolerance
        if distance_cm < self.tolerance_cm and direction in ["LEFT", "RIGHT"]:
            direction = "ALIGNED"
            distance_cm = 0
            is_aligned = True
            message = "✓ Aligned (within tolerance)"
            confidence = 0.85

        return AlignmentInstruction(
            aligned=is_aligned,
            direction=direction,
            distance_cm=distance_cm,
            offset_percentage=result.offset_percentage,
            confidence=confidence,
            message=message,
            debug_image=result.debug_image
        )

    def save_debug_image(self, filepath: str) -> bool:
        """
        Save current alignment visualization.

        Args:
            filepath: Path to save image

        Returns:
            True if saved successfully
        """
        try:
            instruction = self.get_alignment_instruction()
            if instruction.debug_image is not None:
                cv2.imwrite(filepath, instruction.debug_image)
                logger.info(f"Debug image saved: {filepath}")
                return True
            else:
                logger.warning("No debug image available")
                return False
        except Exception as e:
            logger.error(f"Failed to save debug image: {e}")
            return False

    def calibrate_pixels_per_cm(self, known_distance_cm: float) -> Optional[float]:
        """
        Calibration helper: measure known distance in pixels.

        Args:
            known_distance_cm: Known distance in centimeters

        Returns:
            Calculated pixels_per_cm value or None if failed
        """
        frame = self.get_latest_frame()
        if frame is None:
            logger.error("No frame available for calibration")
            return None

        # Show frame and let user click two points
        logger.info(f"Click two points {known_distance_cm}cm apart")

        points = []

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                points.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                cv2.imshow('Calibration', frame)
                if len(points) == 2:
                    cv2.line(frame, points[0], points[1], (0, 255, 0), 2)
                    cv2.imshow('Calibration', frame)

        cv2.namedWindow('Calibration')
        cv2.setMouseCallback('Calibration', mouse_callback)
        cv2.imshow('Calibration', frame)

        while len(points) < 2:
            if cv2.waitKey(1) == 27:  # ESC
                cv2.destroyAllWindows()
                return None

        # Calculate distance in pixels
        pixel_distance = np.sqrt((points[1][0] - points[0][0])**2 +
                                (points[1][1] - points[0][1])**2)

        pixels_per_cm = pixel_distance / known_distance_cm

        logger.info(f"Measured: {pixel_distance:.1f}px = {known_distance_cm}cm")
        logger.info(f"Calculated: {pixels_per_cm:.2f} pixels/cm")

        cv2.waitKey(2000)
        cv2.destroyAllWindows()

        return pixels_per_cm

    def stop(self):
        """Stop camera capture and cleanup"""
        logger.info("Stopping stencil aligner...")

        self.running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        if self.camera:
            self.camera.release()

        cv2.destroyAllWindows()

        logger.info("✓ Stencil aligner stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# ============================================================================
# TEST CODE
# ============================================================================

def test_alignment():
    """Test stencil alignment system"""
    print("\n" + "=" * 70)
    print("STENCIL ALIGNMENT TEST")
    print("=" * 70)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Test with simulation
        with StencilAligner(simulate=True) as aligner:
            print("\n✓ Aligner started (simulation mode)")

            # Get alignment instruction
            print("\n→ Getting alignment instruction...")
            instruction = aligner.get_alignment_instruction()

            print(f"\n   Aligned: {instruction.aligned}")
            print(f"   Direction: {instruction.direction}")
            print(f"   Distance: {instruction.distance_cm:.1f} cm")
            print(f"   Offset: {instruction.offset_percentage:.1f}%")
            print(f"   Confidence: {instruction.confidence:.2f}")
            print(f"   Message: {instruction.message}")

            # Save debug image
            if instruction.debug_image is not None:
                debug_path = "alignment_debug.jpg"
                aligner.save_debug_image(debug_path)
                print(f"\n   Debug image saved: {debug_path}")

        print("\n✓ All tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_alignment()
