# GPS Navigation Deployment Implementation

## Summary

Successfully implemented complete GPS-based navigation system that:
1. Deploys the robot when inspector approves a submission via Telegram
2. Navigates to exact GPS coordinates using IMU heading and motor encoders
3. Calculates road direction from GeoJSON data
4. Aligns robot to road heading before stencil placement

## Implementation Complete ✅

### 1. Telegram Bot → Robot Deployment Bridge

**File**: `App_codes/road-painting-bot/handlers/inspector_handlers.py`

**Changes**:
- Added robot controller import
- Added deployment trigger in approval callback (lines 187-200)
- Calls `robot_controller.deploy_mission()` with GPS coordinates

**How it works**:
```python
# When inspector approves submission:
robot_controller.deploy_mission(
    target_lat=submission['latitude'],
    target_lon=submission['longitude'],
    mission_id=f"job_{submission_id}"
)
```

### 2. Robot Controller Integration

**File**: `App_codes/road-painting-bot/handlers/robot_handlers.py`

**Changes**:
- Switched from `EV3Controller` to `RoadMarkingRobot`
- Added background task `_robot_update_loop()` to run state machine
- Updated initialization to start full robot system
- Updated status command to show mission and state info

**Key features**:
- Robot state machine runs in async background task at 10Hz
- Properly integrated with Telegram bot event loop
- Clean shutdown handling

### 3. GPS Navigation Implementation

**File**: `RPI_codes/robot_controller.py`

**New Methods Added**:

#### `_get_imu_heading()` (lines 404-437)
- Reads Euler angles from MTi-8 sensor
- Returns heading in degrees (0-360, 0=North)
- Simulates heading in simulation mode

#### `_normalize_angle()` (lines 505-519)
- Normalizes angles to -180 to +180 range
- Used for heading error calculations

#### `_calculate_road_heading()` (lines 521-580)
- Reads GeoJSON road data from `data/roads.geojson`
- Finds nearest road segment within 50m
- Calculates road bearing from LineString coordinates
- Returns heading for road alignment

**Updated Methods**:

#### `deploy_mission()` (lines 174-204)
- Added road heading calculation
- Stores road heading in Mission dataclass

#### `_state_navigating()` (lines 247-325)
**Replaced TODO with real implementation**:

1. Get current GPS position
2. Calculate distance and bearing to target
3. Check if arrived (within 0.5m threshold)
4. Get current IMU heading
5. Calculate heading error
6. **If heading error > 10°**: Rotate to correct heading
7. **Move forward in increments**:
   - 50cm steps when >5m away
   - 20cm steps when 1-5m away
   - 10cm steps when <1m away
8. Repeat until within threshold

#### `_state_positioning()` (lines 327-361)
**Added road alignment**:

1. Get road heading from mission
2. Get current IMU heading
3. Calculate heading error from road direction
4. **If error > 5°**: Rotate to align with road
5. Proceed to camera alignment

### 4. Mission Dataclass Enhancement

**File**: `RPI_codes/robot_controller.py` (line 77)

Added `road_heading` field:
```python
@dataclass
class Mission:
    target_lat: float
    target_lon: float
    mission_id: str = "unknown"
    start_time: float = 0.0
    road_heading: Optional[float] = None  # NEW
```

## Navigation Flow

### Complete Deployment-to-Painting Sequence:

```
1. TELEGRAM BOT
   ├─ User reports damaged road with photo + GPS
   ├─ Inspector reviews submission
   └─ Inspector approves → deploy_mission() called

2. IDLE → NAVIGATING
   ├─ Load mission with target GPS coordinates
   ├─ Calculate road heading from GeoJSON
   └─ Begin GPS navigation loop:
       ├─ Read current GPS position (MTi-8)
       ├─ Calculate distance & bearing to target
       ├─ Read current heading (IMU)
       ├─ IF heading error > 10°: Rotate
       ├─ Move forward (step size based on distance)
       └─ Repeat until within 0.5m

3. NAVIGATING → POSITIONING
   ├─ Arrived within GPS threshold
   ├─ Get road heading from GeoJSON
   ├─ Align robot to road direction
   └─ Prepare for fine alignment

4. POSITIONING → ALIGNING
   ├─ Use camera to detect orange stencil
   ├─ Calculate lateral offset
   ├─ Perform fine positioning adjustments
   └─ Align with marking

5. ALIGNING → PAINTING
   ├─ Lower stencil
   ├─ Dispense paint
   ├─ Raise stencil
   └─ Complete mission

6. PAINTING → COMPLETED → IDLE
   └─ Ready for next deployment
```

## GPS & IMU Data Sources

### MTi-8 RTK Sensor Integration

**GPS Position** (`read_latlon()`):
- Data ID: 0x5040
- Returns: `(latitude, longitude)`
- Accuracy: ~1cm with RTK correction

**IMU Heading** (`read_euler()`):
- Data ID: 0x2030
- Returns: `(roll, pitch, yaw)`
- Yaw converted to heading: `(yaw + 360) % 360`

### Motor Encoder Feedback

**Used for**:
- Movement confirmation
- Future enhancement: Dead reckoning if GPS fails

**Available**:
- `get_encoder_positions()` - Current positions
- `reset_encoders()` - Zero encoders
- All movement commands return encoder feedback

## GeoJSON Road Data

**File**: `RPI_codes/data/roads.geojson`

**Structure**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [lon, lat],  // Point 1
          [lon, lat],  // Point 2
          ...
        ]
      },
      "properties": {
        "name": "Main Street",
        "highway": "primary"
      }
    }
  ]
}
```

**Algorithm**:
1. For each road segment in GeoJSON
2. Calculate distance from target to segment midpoint
3. Keep track of nearest segment
4. Calculate bearing from point 1 to point 2 of nearest segment
5. Return as road heading

## Configuration Parameters

**From `ev3_config.py`**:

```python
# GPS Navigation
GPS_ARRIVAL_THRESHOLD = 0.5  # meters - within 50cm = arrived
GPS_CLOSE_THRESHOLD = 1.0    # meters - getting close
HEADING_CORRECTION_THRESHOLD = 10  # degrees - correct if off by >10°
HEADING_TOLERANCE = 5  # degrees - acceptable heading error
ROTATION_TOLERANCE_DEG = 5.0  # degrees - alignment tolerance

# Motor Speeds
DRIVE_SPEED = 50  # Normal driving
TURN_SPEED = 40   # Rotation speed
PRECISION_SPEED = 25  # Fine positioning
```

## Testing

### Simulation Mode
```python
# In bot.py, line 127:
robot_available = initialize_robot_controller(simulate=True, ev3_ip=None)
```

**Simulated behaviors**:
- GPS returns position near target
- IMU heading points toward target
- Motor commands execute without hardware
- State machine runs normally

### Hardware Mode
```python
robot_available = initialize_robot_controller(simulate=False, ev3_ip='169.254.47.159')
```

**Requirements**:
- EV3 brick connected via USB (169.254.47.159)
- MTi-8 sensor connected to RPI
- Camera available
- GeoJSON file present

## Troubleshooting

### "Robot controller not available"
- Check RPI_codes is in Python path
- Verify robot_controller.py exists
- Check import errors in logs

### "No GPS fix"
- Verify MTi-8 connection
- Check GPS antenna placement
- Wait for RTK lock (can take 1-2 minutes)

### "No road found within 50m"
- Update roads.geojson with actual road data
- Increase search_radius parameter
- Verify target coordinates are near roads

### "Heading correction failed"
- Check EV3 connection
- Verify motors are responding
- Check motor polarity settings

## Files Modified

1. **`App_codes/road-painting-bot/handlers/inspector_handlers.py`**
   - Added robot controller import (lines 6-21)
   - Added deployment trigger (lines 187-200)

2. **`App_codes/road-painting-bot/handlers/robot_handlers.py`**
   - Replaced EV3Controller with RoadMarkingRobot (lines 24-92)
   - Added background update loop (lines 75-92)
   - Updated status command (lines 174-216)
   - Updated cleanup (lines 220-239)

3. **`RPI_codes/robot_controller.py`**
   - Added road_heading to Mission (line 77)
   - Added `_get_imu_heading()` method (lines 404-437)
   - Added `_normalize_angle()` method (lines 505-519)
   - Added `_calculate_road_heading()` method (lines 521-580)
   - Implemented GPS navigation in `_state_navigating()` (lines 247-325)
   - Added road alignment in `_state_positioning()` (lines 327-361)
   - Updated `deploy_mission()` (lines 174-204)

## Next Steps

### Recommended Enhancements:

1. **Encoder-based Odometry**
   - Track position using motor encoders
   - Merge with GPS for smoother navigation
   - Handle GPS dropouts

2. **Obstacle Avoidance**
   - Integrate LiDAR data
   - Detect obstacles in path
   - Plan avoidance maneuvers

3. **Status Updates to Telegram**
   - Send progress updates during navigation
   - Report arrival and completion
   - Send photo of painted marking

4. **Mission Queue**
   - Accept multiple deployments
   - Queue missions
   - Execute in sequence

5. **Real GeoJSON Data**
   - Replace sample data with actual OpenStreetMap export
   - Cover operational area
   - Keep updated

---

**Status**: ✅ **COMPLETE AND READY FOR TESTING**

**Date**: 2025-11-09

**Implementation**: All components integrated and functional. System ready for field testing with actual hardware.
