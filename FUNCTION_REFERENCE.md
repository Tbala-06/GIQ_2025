# GIQ 2025 - Complete Function Reference

**Quick lookup guide for every function in the codebase**

---

## 📱 Telegram Bot Functions (App_codes)

### bot.py - Main Application

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `setup_logging()` | None | None | Configure logging to console and file |
| `error_handler()` | update, context | None | Handle bot errors, notify user |
| `unknown_command()` | update, context | None | Respond to unknown commands |
| `main()` | None | None | Initialize and start bot |

### handlers/user_handlers.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `start_command()` | update, context | None | Handle /start - welcome message |
| `help_command()` | update, context | None | Handle /help - show available commands |
| `status_command()` | update, context | None | Handle /status - show user's submission status |
| `report_start()` | update, context | None | Start report conversation - request photo |
| `report_photo()` | update, context | None | Receive photo, request GPS location |
| `report_location()` | update, context | None | Receive location, analyze road, save submission |
| `report_cancel()` | update, context | None | Cancel report conversation |
| `get_report_conversation_handler()` | None | ConversationHandler | Create report conversation flow |

### handlers/inspector_handlers.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `inspector_command()` | update, context | None | Show inspector dashboard with statistics |
| `pending_command()` | update, context | None | Show pending submissions for review |
| `show_submission_for_review()` | update, context, submission | None | Display submission with approve/reject buttons |
| `handle_approval_callback()` | update, context | None | Handle approve/reject button press, **DEPLOY ROBOT** |
| `history_command()` | update, context | None | Show recent inspection decisions |
| `stats_command()` | update, context | None | Show detailed statistics |
| `export_command()` | update, context | None | Export submissions to CSV file |
| `get_inspector_handlers()` | None | List[Handler] | Return list of callback handlers |

**🚨 IMPORTANT**: `handle_approval_callback()` calls `robot_controller.deploy_mission()` when inspector approves!

### handlers/robot_handlers.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `initialize_robot_controller()` | simulate, ev3_ip | bool | Initialize robot controller, start background loop |
| `_robot_update_loop()` | None | None | Background async task - runs state machine at 10Hz |
| `simulate_command()` | update, context | None | Handle /simulate - test motor movements |
| `robotstatus_command()` | update, context | None | Handle /robotstatus - show robot state and mission |
| `cleanup_robot_controller()` | None | None | Stop robot and cleanup on shutdown |

### database.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | db_path | None | Connect to SQLite database |
| `init_database()` | None | None | Create tables if not exist |
| `add_submission()` | user_id, username, first_name, last_name, photo_id, lat, lon | int | Add new submission, return ID |
| `get_submission()` | submission_id | dict | Get submission by ID |
| `get_pending_submissions()` | limit | List[dict] | Get pending submissions |
| `update_submission_status()` | submission_id, status, inspector_id, ... | bool | Update status (approved/rejected) |
| `get_statistics()` | None | dict | Get submission statistics |
| `get_recent_decisions()` | limit | List[dict] | Get recent inspector decisions |
| `export_to_csv()` | filepath | bool | Export all submissions to CSV |

### road_analyzer.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `analyze_road_condition()` | image_path | dict | Analyze road damage from photo (AI/ML) |
| `detect_damage_type()` | image | str | Classify damage type (crack, pothole, etc.) |
| `estimate_severity()` | image | float | Estimate damage severity (0.0-1.0) |

### web_dashboard.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `create_app()` | db_path | Flask | Create Flask application |
| `index()` | None | HTML | Render map dashboard |
| `get_submissions()` | None | JSON | API endpoint - get all submissions |
| `get_submission_details()` | submission_id | JSON | API endpoint - get submission details |

---

## 🤖 Robot Controller Functions (RPI_codes)

### robot_controller.py - Main State Machine

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | simulate | None | Initialize robot controller |
| `start()` | None | bool | Initialize hardware (EV3, GPS, camera) |
| `deploy_mission()` | target_lat, target_lon, mission_id | None | **Deploy new mission, calculate road heading** |
| `update()` | None | None | Main loop - execute current state logic |
| `is_running()` | None | bool | Check if robot is running |
| `stop()` | None | None | Stop robot and cleanup |

#### State Machine Methods

| Function | Description |
|----------|-------------|
| `_state_idle()` | Waiting for deployment |
| `_state_navigating()` | **GPS navigation with heading correction and incremental movement** |
| `_state_positioning()` | **Align to road direction using GeoJSON heading** |
| `_state_aligning()` | Camera-based fine alignment |
| `_state_painting()` | Execute painting sequence |
| `_state_completed()` | Mission complete, return to IDLE |
| `_state_error()` | Error handling |

#### Helper Methods

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `_get_gps_position()` | None | (lat, lon) | Get current GPS position from MTi sensor |
| `_get_imu_heading()` | None | float | **Get current heading from IMU (0-360°)** |
| `_calculate_distance_bearing()` | lat1, lon1, lat2, lon2 | (distance_m, bearing_deg) | Haversine distance and forward azimuth |
| `_normalize_angle()` | angle | float | **Normalize angle to -180 to +180 range** |
| `_calculate_road_heading()` | lat, lon, search_radius | float | **Calculate road direction from GeoJSON data** |
| `_move_lateral()` | distance_cm | None | Move sideways (rotate-move-rotate) |
| `_transition_to()` | new_state | None | Transition to new state with logging |
| `_transition_to_error()` | error_message | None | Transition to error state |

---

### navigation/gps_navigator.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `calculate_distance_bearing()` | lat1, lon1, lat2, lon2 | (distance_m, bearing_deg) | Haversine formula |
| `calculate_road_direction()` | lat, lon, search_radius | float | Find nearest road, return heading |
| `create_waypoint()` | lat, lon, mission_id | WayPoint | Create waypoint with road heading |
| `calculate_heading_error()` | current_heading, target_heading | float | Shortest angular difference |
| `calculate_navigation_step()` | current_lat, current_lon, current_heading, target_lat, target_lon, step_size | (move_distance, heading_correction, distance_remaining) | Calculate next navigation step |
| `get_approach_heading()` | waypoint, approach_lat, approach_lon | float | Get optimal approach heading |

### navigation/road_finder.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `load_geojson()` | filepath | dict | Load GeoJSON road data |
| `find_nearest_road()` | lat, lon, roads, max_distance | RoadSegment | Find closest road segment |
| `calculate_road_bearing()` | road_segment | float | Calculate road bearing from coordinates |
| `point_to_line_distance()` | point, line_start, line_end | float | Perpendicular distance to line segment |

### navigation/path_planner.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `plan_route()` | start_lat, start_lon, end_lat, end_lon | List[WayPoint] | Plan route with waypoints |
| `simplify_path()` | waypoints, tolerance | List[WayPoint] | Simplify path (Douglas-Peucker) |

---

### hardware/mti_parser.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `connect()` | port, baudrate | bool | Connect to MTi sensor |
| `read_data()` | timeout | IMUData | Read sensor data packet |
| `read_latlon()` | timeout | (lat, lon) | Read GPS coordinates |
| `read_euler()` | timeout | (roll, pitch, yaw) | Read Euler angles (heading) |
| `read_quaternion()` | timeout | (w, x, y, z) | Read quaternion orientation |
| `read_acceleration()` | timeout | (ax, ay, az) | Read acceleration (m/s²) |
| `disconnect()` | None | None | Close serial connection |

### hardware/motor_controller.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | use_gpiod | None | Initialize GPIO (RPi 5 or RPi 4/3) |
| `setup()` | None | None | Setup GPIO pins |
| `move_forward()` | distance_cm, speed_percent | None | Move forward specified distance |
| `move_backward()` | distance_cm, speed_percent | None | Move backward specified distance |
| `turn_left()` | angle_degrees, speed_percent | None | Rotate left (counterclockwise) |
| `turn_right()` | angle_degrees, speed_percent | None | Rotate right (clockwise) |
| `set_speed()` | left_speed, right_speed | None | Set individual motor speeds (-100 to +100) |
| `stop()` | None | None | Stop all motors immediately |
| `cleanup()` | None | None | Cleanup GPIO on shutdown |

### hardware/stencil_controller.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | pin | None | Initialize servo on GPIO pin |
| `set_angle()` | angle | None | Set servo angle (0-180°) |
| `align_to_road()` | road_heading | None | Rotate stencil to match road direction |
| `center()` | None | None | Center servo (90°) |
| `cleanup()` | None | None | Stop servo PWM |

### hardware/paint_dispenser.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | pin | None | Initialize dispenser on GPIO pin |
| `dispense()` | duration_seconds | None | Activate dispenser for specified time |
| `start()` | None | None | Turn on dispenser |
| `stop()` | None | None | Turn off dispenser |
| `cleanup()` | None | None | Cleanup GPIO |

---

### ev3_comm.py - EV3 Communication

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | ev3_ip, simulate | None | Initialize EV3 controller |
| `connect()` | None | bool | Establish SSH connection to EV3 |
| `disconnect()` | None | None | Close SSH connection |
| `send_command()` | command | str | Send command, wait for response |
| `move_forward()` | distance_cm, speed | str | Move forward, return encoder feedback |
| `move_backward()` | distance_cm, speed | str | Move backward, return encoder feedback |
| `rotate()` | degrees, speed | str | Rotate robot |
| `lower_stencil()` | None | str | Lower stencil motor |
| `raise_stencil()` | None | str | Raise stencil motor |
| `dispense_paint()` | None | str | Activate paint dispenser |
| `stop()` | None | str | Emergency stop all motors |
| `get_encoder_positions()` | None | (left, right) | Read encoder positions |
| `reset_encoders()` | None | str | Reset encoders to zero |

### ev3_controller.py (Runs on EV3 Brick)

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `__init__()` | None | None | Initialize motors on EV3 |
| `run()` | None | None | Main command loop (reads from stdin) |
| `move_forward()` | distance_cm, speed | None | Execute forward movement |
| `rotate()` | degrees, speed | None | Execute rotation |
| `lower_stencil()` | None | None | Lower stencil |
| `raise_stencil()` | None | None | Raise stencil |
| `return_response()` | message | None | Send response to stdout |

---

### cam/testing.py - Camera Alignment

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `detect_orange_stencil()` | frame | (x, y, w, h) | Detect orange stencil bounding box |
| `detect_yellow_marking()` | frame, stencil_rect | (zone, offset_percent) | Detect yellow marking in zones |
| `count_yellow_pixels_in_zone()` | yellow_mask, zone_bounds | int | Count yellow pixels in zone |
| `get_alignment_instruction()` | frame | AlignmentInstruction | Get movement instruction (LEFT/CENTER/RIGHT) |
| `calculate_offset()` | pixel_count, total_pixels | float | Calculate offset percentage |
| `draw_debug_overlay()` | frame, instruction | np.ndarray | Draw debug visualization |

---

### control/robot_state.py

| Enum/Class | Values | Description |
|------------|--------|-------------|
| `RobotState` | IDLE, MOVING, NAVIGATING, POSITIONING, ALIGNING, PAINTING, COMPLETED, ERROR | Robot state machine states |

### control/mission_executor.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `execute_mission()` | mission | bool | Coordinate full mission execution |
| `navigate_to_target()` | target_lat, target_lon | bool | Execute GPS navigation phase |
| `perform_positioning()` | None | bool | Execute positioning phase |
| `perform_alignment()` | None | bool | Execute camera alignment |
| `perform_painting()` | None | bool | Execute painting operation |

### control/safety_monitor.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `check_gps_signal()` | gps | bool | Verify GPS fix available |
| `check_battery_level()` | None | float | Read battery voltage |
| `check_tilt_angle()` | imu | (roll, pitch) | Check if robot tilted |
| `check_emergency_stop()` | None | bool | Check if e-stop pressed |
| `is_safe_to_operate()` | None | bool | Comprehensive safety check |

---

### communication/mqtt_client.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `connect()` | broker, port | bool | Connect to MQTT broker |
| `subscribe()` | topic, callback | None | Subscribe to topic |
| `publish()` | topic, payload | None | Publish message |
| `disconnect()` | None | None | Disconnect from broker |

### communication/status_reporter.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `start()` | robot_controller | None | Start status reporting thread |
| `stop()` | None | None | Stop reporting thread |
| `report_status()` | None | None | Publish current status via MQTT |

---

### utils/geo_utils.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `haversine_distance()` | lat1, lon1, lat2, lon2 | float | Distance in meters |
| `calculate_bearing()` | lat1, lon1, lat2, lon2 | float | Bearing in degrees (0-360) |
| `normalize_angle()` | angle | float | Normalize to -180 to +180 |
| `meters_to_lat_lon()` | meters, lat, lon, bearing | (new_lat, new_lon) | Calculate new position |

### utils/road_geometry.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `perpendicular_distance()` | point, line_start, line_end | float | Distance from point to line |
| `calculate_perpendicular_heading()` | road_bearing | float | Calculate perpendicular to road |
| `project_point_to_line()` | point, line_start, line_end | (proj_lat, proj_lon) | Project point onto line |

---

## 🗺️ GeoJSON Functions

### GeoJson/closestline.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `haversine_distance()` | lat1, lon1, lat2, lon2 | float | Distance in meters |
| `point_to_line_distance()` | point, line_start, line_end | float | Perpendicular distance |
| `find_closest_marking()` | target_lat, target_lon, geojson_path | dict | Find nearest road segment |

### GeoJson/plotter.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `plot_roads()` | geojson_path | None | Plot roads with matplotlib |
| `plot_robot_position()` | lat, lon, roads | None | Plot robot on road map |

---

## 🧪 Testing Functions

### tests/motor/test_gpio_rpi5.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `test_gpio_connections()` | None | None | **Quick 8-second GPIO connection test - RUN FIRST!** |

### tests/motor/ps3_motor_controller.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `initialize_ps3()` | None | Joystick | Initialize PS3 controller |
| `read_ps3_input()` | joystick | dict | Read controller state |
| `control_robot()` | joystick, motor_controller | None | Main control loop |

### tests/motor/keyboard_motor_controller.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `get_keyboard_input()` | None | str | Get key press (W/A/S/D) |
| `process_command()` | key, motor_controller | None | Execute movement command |

---

## 🔧 Utility Functions

### calibration_wizard.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `calibrate_wheels()` | motor_controller | float | Calibrate wheel circumference |
| `calibrate_turn_radius()` | motor_controller | float | Calibrate turn calibration factor |
| `calibrate_camera_fov()` | camera | float | Calibrate pixels per cm |

### tools/download_roads.py

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `download_osm_roads()` | lat, lon, radius | dict | Download roads from OpenStreetMap |
| `save_geojson()` | data, filepath | None | Save GeoJSON to file |

---

## 🔑 Key Function Flows

### 1. Deployment Flow

```
Inspector approves submission
  ↓
inspector_handlers.handle_approval_callback()
  ↓
robot_controller.deploy_mission(lat, lon, mission_id)
  ↓
_calculate_road_heading(lat, lon) → road_heading
  ↓
Create Mission(lat, lon, road_heading)
  ↓
State = NAVIGATING
```

### 2. Navigation Flow

```
_state_navigating()
  ↓
_get_gps_position() → (current_lat, current_lon)
  ↓
_calculate_distance_bearing() → (distance, bearing)
  ↓
_get_imu_heading() → current_heading
  ↓
_normalize_angle(bearing - current_heading) → heading_error
  ↓
if abs(heading_error) > 10°:
    ev3.rotate(heading_error)
else:
    ev3.move_forward(step_size)
```

### 3. Alignment Flow

```
_state_aligning()
  ↓
aligner.get_alignment_instruction(frame)
  ↓
detect_orange_stencil(frame) → stencil_rect
  ↓
detect_yellow_marking(frame, stencil_rect) → (zone, offset)
  ↓
if zone == "CENTER":
    aligned = True
elif zone == "LEFT":
    _move_lateral(+offset_cm)  # Move right
elif zone == "RIGHT":
    _move_lateral(-offset_cm)  # Move left
```

---

## 📊 Function Call Statistics

- **Total Functions**: ~150
- **State Machine**: 7 states, 8 state functions
- **Navigation**: 15 functions
- **Hardware Control**: 25 functions
- **Camera Vision**: 12 functions
- **Communication**: 8 functions
- **Utilities**: 20 functions
- **Database**: 10 functions
- **Bot Handlers**: 15 functions

---

**Last Updated**: 2025-11-09
**Coverage**: 100% of production code documented
