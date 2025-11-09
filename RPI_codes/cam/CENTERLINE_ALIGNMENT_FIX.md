# Center Line Alignment Fix

## Problem

The initial `centerline_align.py` incorrectly reported `image.png` as "FULLY ALIGNED" when it was actually misaligned by approximately 50 degrees.

**Incorrect Output:**
- Marking Angle: 90.00 deg
- Rotation Diff: +0.00 deg
- Status: FULLY ALIGNED!

**User Feedback:** "it is actually not aligned"

## Root Cause

The algorithm was combining ALL detected white/yellow marking regions and fitting a rectangle to all points. This caused the algorithm to average out the angles of multiple regions:

1. Large vertical white strips on left side (17% of image)
2. Large vertical white strips on right side (12% of image)
3. Diagonal road marking stripe at top-left (the actual marking we want)

When combined, these regions averaged to nearly vertical (90 degrees), masking the diagonal marking orientation.

## Solution

Changed from using ALL large contours to using only the **LARGEST single contour**:

```python
# BEFORE (incorrect):
all_points = np.vstack(large_contours)  # Combines all contours
marking_rect = cv2.minAreaRect(all_points)

# AFTER (correct):
largest_contour = max(large_contours, key=cv2.contourArea)  # Only largest
all_points = largest_contour
marking_rect = cv2.minAreaRect(all_points)
```

This focuses on the most prominent road marking (the diagonal stripe) rather than averaging all white regions.

## Additional Improvements

1. **Line Fitting**: Changed from using rectangle angle to `cv2.fitLine()` for more accurate angle detection
   ```python
   [vx, vy, x0, y0] = cv2.fitLine(all_points, cv2.DIST_L2, 0, 0.01, 0.01)
   centerline_angle = np.degrees(np.arctan2(vx[0], vy[0]))
   ```

2. **Orange Exclusion**: Subtract orange stencil from marking detection to avoid detecting stencil as marking
   ```python
   marking_only = cv2.bitwise_and(marking_mask, cv2.bitwise_not(orange_mask))
   ```

3. **NumPy Fix**: Fixed deprecation warning by properly extracting scalar values
   ```python
   # Before: np.arctan2(float(vx), float(vy))
   # After: np.arctan2(vx[0], vy[0])
   ```

## Correct Output

After the fix, `image.png` correctly shows:

- **Marking Angle:** -39.45 deg (from horizontal)
- **Rotation Diff:** +50.55 deg (from vertical)
- **Lateral Offset:** -297.5 px (-33.3%)
- **Status:** Move RIGHT 33.3% + Rotate CCW 50.5deg
- **Fully Aligned:** NO

## Visualization

The output now correctly shows:
- **Purple vertical line** = Stencil center (image middle)
- **Cyan diagonal line** = Marking center (follows the road marking stripe)
- **Clear angle difference** between the two lines (~50 degrees)

This matches the user's reference image showing the magenta diagonal line at an angle from the purple vertical line.

## Usage

```bash
cd ~/GIQ_2025/RPI_codes/cam
python centerline_align.py
```

The script processes all images in `datas/` folder and creates `centerline_*.png` output files with:
- Visual overlays showing both center lines
- Angle measurements
- Alignment status
- Correction instructions

## Integration

For robot control integration:

```python
from centerline_align import CenterLineAlignmentVisualizer

visualizer = CenterLineAlignmentVisualizer()
vis, alignment_info = visualizer.create_centerline_visualization(frame)

if alignment_info['fully_aligned']:
    # Proceed with painting
    start_painting()
else:
    # Apply corrections
    if not alignment_info['position_aligned']:
        move_robot(alignment_info['lateral_offset_percent'])
    if not alignment_info['rotation_aligned']:
        rotate_robot(alignment_info['rotation_diff'])
```

## Files Modified

- [centerline_align.py](centerline_align.py) - Lines 70-121 (marking detection and angle calculation)

## Test Results

**image.png:**
- Previously: FULLY ALIGNED (incorrect)
- Now: Rotation Diff +50.55 deg, Move RIGHT 33.3% (correct)

---

**Status:** ✅ Fixed - Correctly detects angular misalignment
**Date:** 2025-11-09
