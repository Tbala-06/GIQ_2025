"""
Road Marking Analyzer
Analyzes road images to detect types of lane markings using OpenCV
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RoadAnalysisResult:
    """Results from road marking analysis"""
    road_type: str  # Primary detected type
    confidence: str  # HIGH, MEDIUM, LOW
    details: str  # Detailed description
    detected_features: list  # List of all detected features


class RoadMarkingAnalyzer:
    """Analyze road images to detect lane marking types"""

    # Road marking types
    DOUBLE_YELLOW = "Double Yellow Line"
    SINGLE_YELLOW = "Single Yellow Line"
    DOUBLE_WHITE = "Double White Line"
    SINGLE_WHITE = "Single White Line"
    DASHED_WHITE = "Dashed White Line"
    DASHED_YELLOW = "Dashed Yellow Line"
    NO_MARKINGS = "No Clear Markings"
    MIXED_MARKINGS = "Mixed/Multiple Markings"

    def __init__(self):
        """Initialize the analyzer"""
        logger.info("Road Marking Analyzer initialized")

    def analyze_image(self, image_array: np.ndarray) -> RoadAnalysisResult:
        """
        Analyze road image for lane markings.

        Args:
            image_array: Image as numpy array (BGR format)

        Returns:
            RoadAnalysisResult with detected road type
        """
        try:
            if image_array is None or image_array.size == 0:
                return self._create_error_result("Invalid image")

            height, width = image_array.shape[:2]
            logger.info(f"Analyzing image: {width}x{height}")

            # Focus on bottom half of image (where road markings typically are)
            roi = image_array[height//2:, :]

            # Detect yellow and white markings
            yellow_mask, yellow_area = self._detect_yellow_markings(roi)
            white_mask, white_area = self._detect_white_markings(roi)

            # Analyze line patterns
            yellow_lines = self._count_lines(yellow_mask)
            white_lines = self._count_lines(white_mask)

            # Check if lines are dashed or continuous
            yellow_dashed = self._is_dashed(yellow_mask)
            white_dashed = self._is_dashed(white_mask)

            logger.info(f"Detection: Yellow lines={yellow_lines} (dashed={yellow_dashed}), "
                       f"White lines={white_lines} (dashed={white_dashed})")

            # Determine road type based on detected features
            return self._classify_road_type(
                yellow_lines, white_lines,
                yellow_dashed, white_dashed,
                yellow_area, white_area
            )

        except Exception as e:
            logger.error(f"Error analyzing image: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def _detect_yellow_markings(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """Detect yellow road markings"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Yellow range (optimized for road markings)
        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # Clean up noise
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        area = cv2.countNonZero(mask)
        return mask, area

    def _detect_white_markings(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """Detect white road markings"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # White range (low saturation, high value)
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 50, 255])

        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Clean up noise
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        area = cv2.countNonZero(mask)
        return mask, area

    def _count_lines(self, mask: np.ndarray) -> int:
        """
        Count number of distinct lines in mask.
        Uses horizontal projection to detect peaks.
        """
        if mask is None or cv2.countNonZero(mask) == 0:
            return 0

        # Horizontal projection (sum across columns)
        projection = np.sum(mask, axis=0)

        # Normalize
        if projection.max() > 0:
            projection = projection / projection.max()

        # Find peaks (regions with significant white pixels)
        threshold = 0.3
        in_peak = False
        peak_count = 0

        for val in projection:
            if val > threshold and not in_peak:
                peak_count += 1
                in_peak = True
            elif val <= threshold:
                in_peak = False

        # Limit to reasonable number (max 2 for double lines)
        return min(peak_count, 2)

    def _is_dashed(self, mask: np.ndarray) -> bool:
        """
        Determine if line is dashed or continuous.
        Uses vertical projection to detect gaps.
        """
        if mask is None or cv2.countNonZero(mask) == 0:
            return False

        # Vertical projection (sum across rows)
        projection = np.sum(mask, axis=1)

        # Normalize
        if projection.max() > 0:
            projection = projection / projection.max()

        # Count gaps (transitions from high to low)
        threshold = 0.2
        gap_count = 0
        was_high = False

        for val in projection:
            if val < threshold and was_high:
                gap_count += 1
                was_high = False
            elif val > threshold:
                was_high = True

        # If multiple gaps, it's dashed
        # Require at least 2 gaps to be confident it's dashed
        return gap_count >= 2

    def _classify_road_type(
        self,
        yellow_lines: int,
        white_lines: int,
        yellow_dashed: bool,
        white_dashed: bool,
        yellow_area: int,
        white_area: int
    ) -> RoadAnalysisResult:
        """Classify road type based on detected features"""

        detected_features = []

        # Build list of detected features
        if yellow_lines > 0:
            line_type = "dashed" if yellow_dashed else "continuous"
            count = "double" if yellow_lines >= 2 else "single"
            detected_features.append(f"{count} {line_type} yellow")

        if white_lines > 0:
            line_type = "dashed" if white_dashed else "continuous"
            count = "double" if white_lines >= 2 else "single"
            detected_features.append(f"{count} {line_type} white")

        # Determine primary type and confidence
        road_type = self.NO_MARKINGS
        confidence = "LOW"
        details = "Unable to clearly identify road markings"

        # Yellow line classification
        if yellow_area > white_area and yellow_lines > 0:
            if yellow_lines >= 2:
                road_type = self.DOUBLE_YELLOW
                confidence = "HIGH"
                details = "Double yellow center line detected (no passing zone)"
            elif yellow_dashed:
                road_type = self.DASHED_YELLOW
                confidence = "MEDIUM"
                details = "Dashed yellow line detected (passing allowed with caution)"
            else:
                road_type = self.SINGLE_YELLOW
                confidence = "MEDIUM"
                details = "Single yellow line detected (no passing)"

        # White line classification
        elif white_area > yellow_area and white_lines > 0:
            if white_lines >= 2:
                road_type = self.DOUBLE_WHITE
                confidence = "HIGH"
                details = "Double white line detected (lane separation)"
            elif white_dashed:
                road_type = self.DASHED_WHITE
                confidence = "HIGH"
                details = "Dashed white line detected (lane marker)"
            else:
                road_type = self.SINGLE_WHITE
                confidence = "MEDIUM"
                details = "Single white line detected (edge line or lane marker)"

        # Mixed markings
        elif yellow_area > 0 and white_area > 0:
            road_type = self.MIXED_MARKINGS
            confidence = "MEDIUM"
            details = f"Multiple marking types detected: {', '.join(detected_features)}"

        # No clear markings
        else:
            road_type = self.NO_MARKINGS
            confidence = "LOW"
            details = "No clear road markings detected in image"
            detected_features = ["none detected"]

        logger.info(f"Classification: {road_type} (confidence: {confidence})")

        return RoadAnalysisResult(
            road_type=road_type,
            confidence=confidence,
            details=details,
            detected_features=detected_features
        )

    def _create_error_result(self, error_msg: str) -> RoadAnalysisResult:
        """Create error result"""
        return RoadAnalysisResult(
            road_type="Error",
            confidence="LOW",
            details=f"Analysis failed: {error_msg}",
            detected_features=[]
        )


# Convenience function for bot integration
async def analyze_road_photo(file_path: str) -> RoadAnalysisResult:
    """
    Analyze road photo from file path.

    Args:
        file_path: Path to image file

    Returns:
        RoadAnalysisResult with detected road type
    """
    try:
        # Read image
        image = cv2.imread(file_path)

        if image is None:
            logger.error(f"Failed to read image: {file_path}")
            return RoadAnalysisResult(
                road_type="Error",
                confidence="LOW",
                details="Failed to read image file",
                detected_features=[]
            )

        # Analyze
        analyzer = RoadMarkingAnalyzer()
        result = analyzer.analyze_image(image)

        return result

    except Exception as e:
        logger.error(f"Error in analyze_road_photo: {e}", exc_info=True)
        return RoadAnalysisResult(
            road_type="Error",
            confidence="LOW",
            details=str(e),
            detected_features=[]
        )
