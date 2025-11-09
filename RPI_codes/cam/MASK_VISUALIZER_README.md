# Color Mask Visualizer - mask.py

## Purpose

Visualizes which colors the camera detects in your alignment images. Shows separate masks for orange stencil, yellow marking, white marking, and black background.

## Usage

```bash
cd ~/GIQ_2025/RPI_codes/cam
python mask.py
```

## What It Does

Processes all images in `datas/` folder and creates a 3x3 grid visualization showing:

### Row 1:
- **ORIGINAL** - Original image
- **ORANGE MASK** - Orange stencil detection (white = detected)
- **YELLOW MASK** - Yellow marking detection

### Row 2:
- **WHITE MASK** - White marking detection
- **BLACK MASK** - Black/dark background detection
- **MARKING (Y+W)** - Combined yellow + white (road marking)

### Row 3:
- **OVERLAY** - All colors overlaid on original
- **ORANGE COLORED** - Orange areas highlighted
- **YELLOW COLORED** - Yellow areas highlighted

## Output

Creates `mask_*.png` files in `datas/` folder with visualization grids.

Also prints statistics:
```
Color Detection Statistics:
--------------------------------------------------
ORANGE      :   167629 px (37.99%)
YELLOW      :     1553 px ( 0.35%)
WHITE       :   222755 px (50.49%)
BLACK       :    24186 px ( 5.48%)
MARKING     :   223320 px (50.61%)
--------------------------------------------------
```

## Color Ranges (HSV)

Detects these colors:

| Color | H Min | H Max | S Min | S Max | V Min | V Max |
|-------|-------|-------|-------|-------|-------|-------|
| Orange | 5 | 20 | 150 | 255 | 150 | 255 |
| Yellow | 15 | 35 | 80 | 255 | 80 | 255 |
| White | 0 | 180 | 0 | 199 | 98 | 254 |
| Black | 0 | 180 | 0 | 255 | 0 | 50 |

## Use Cases

1. **Debug color detection** - See exactly what the camera detects
2. **Calibrate HSV ranges** - Verify color ranges match your environment
3. **Check lighting** - Ensure good detection under current lighting
4. **Validate masks** - Confirm stencil and marking are detected properly

## Example Output

For image `A2.png`:
- **37.99%** of pixels detected as orange (stencil)
- **50.61%** of pixels detected as marking (yellow + white)
- **5.48%** of pixels detected as black (background)

This confirms good detection of both stencil and road marking!

## Integration

Use this to verify your alignment system is detecting colors correctly before running `testing.py` or `testing_enhanced.py`.

If masks look wrong:
1. Adjust lighting
2. Re-calibrate HSV ranges using `colour_test.py`
3. Update color ranges in `mask.py`, `testing.py`, and `testing_enhanced.py`

---

**Quick Check**: Run `python mask.py` to verify camera can see your stencil and road marking!
