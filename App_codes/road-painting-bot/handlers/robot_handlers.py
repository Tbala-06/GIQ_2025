# -*- coding: utf-8 -*-
"""
Robot Control Handlers for Telegram Bot
Handles /simulate command for testing EV3 motors via RPI
"""

import logging
import sys
import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# Add RPI_codes to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RPI_codes'))

logger = logging.getLogger(__name__)

# Global robot controller instance
robot_controller = None
robot_update_task = None  # Background task for robot state machine


def initialize_robot_controller(simulate=False, ev3_ip=None):
    """
    Initialize the robot controller.
    This should be called once when the bot starts.

    Args:
        simulate: If True, runs in simulation mode (no hardware)
        ev3_ip: EV3 IP address (None for auto-detect)

    Returns:
        True if successful, False otherwise
    """
    global robot_controller, robot_update_task

    try:
        # Import the main robot controller (not just EV3)
        from robot_controller import RoadMarkingRobot

        logger.info("Initializing road marking robot controller...")
        logger.info("Mode: {}".format('SIMULATION' if simulate else 'HARDWARE'))

        robot_controller = RoadMarkingRobot(simulate=simulate)

        # Start the robot system
        if robot_controller.start():
            logger.info("✓ Robot controller initialized and started")

            # Start background task to run robot state machine
            import asyncio
            robot_update_task = asyncio.create_task(_robot_update_loop())
            logger.info("✓ Robot update loop started")

            return True
        else:
            logger.error("✗ Robot controller failed to start")
            robot_controller = None
            return False

    except ImportError as e:
        logger.error("Cannot import robot controller: {}".format(e))
        logger.error("Make sure RPI_codes/robot_controller.py is available")
        robot_controller = None
        return False
    except Exception as e:
        logger.error("Robot controller initialization error: {}".format(e))
        import traceback
        traceback.print_exc()
        robot_controller = None
        return False


async def _robot_update_loop():
    """
    Background task that runs the robot state machine.
    Calls robot_controller.update() repeatedly.
    """
    global robot_controller

    logger.info("Robot update loop running...")

    while robot_controller and robot_controller.is_running():
        try:
            robot_controller.update()
            await asyncio.sleep(0.1)  # 10Hz update rate
        except Exception as e:
            logger.error("Robot update error: {}".format(e))
            await asyncio.sleep(1.0)

    logger.info("Robot update loop stopped")


async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /simulate command - runs motor test sequence.

    Usage: /simulate
    """
    global robot_controller

    user_id = update.effective_user.id
    logger.info("Received /simulate command from user {}".format(user_id))

    # Check if robot controller is initialized
    if robot_controller is None:
        await update.message.reply_text(
            "❌ *Robot Controller Not Available*\n\n"
            "The robot controller is not initialized.\n"
            "This feature requires the RPI to be running.",
            parse_mode='Markdown'
        )
        return

    await update.message.reply_text(
        "🚀 *Motor Simulation Starting*\n\n"
        "Testing EV3 motors with 30cm forward/backward sequence...",
        parse_mode='Markdown'
    )

    try:
        # Test 1: Move forward
        logger.info("→ Test 1: Moving FORWARD 30cm...")
        await update.message.reply_text("→ Moving forward 30cm...")

        result = robot_controller.move_forward(30, speed=40)
        logger.info("   Response: {}".format(result))

        if result and "DONE" in str(result):
            await update.message.reply_text("✓ Forward complete")
        else:
            await update.message.reply_text("✗ Forward failed: {}".format(result))

        # Wait 2 seconds
        await asyncio.sleep(2)

        # Test 2: Move backward
        logger.info("→ Test 2: Moving BACKWARD 30cm...")
        await update.message.reply_text("→ Moving backward 30cm...")

        result = robot_controller.move_backward(30, speed=40)
        logger.info("   Response: {}".format(result))

        if result and "DONE" in str(result):
            await update.message.reply_text("✓ Backward complete")
        else:
            await update.message.reply_text("✗ Backward failed: {}".format(result))

        # Wait 2 seconds
        await asyncio.sleep(2)

        # Stop motors
        logger.info("→ Stopping motors...")
        robot_controller.stop()

        await update.message.reply_text(
            "✅ *Motor Test Complete!*\n\n"
            "All movements executed successfully.",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error("Motor test error: {}".format(e))
        import traceback
        traceback.print_exc()

        await update.message.reply_text(
            "✗ Motor test error: {}\n\n"
            "Check the logs for details.".format(str(e))
        )


async def robotstatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /robotstatus command - show robot controller status.

    Usage: /robotstatus
    """
    global robot_controller

    user_id = update.effective_user.id
    logger.info("Received /robotstatus command from user {}".format(user_id))

    if robot_controller is None:
        await update.message.reply_text(
            "❌ *Robot Status: OFFLINE*\n\n"
            "Controller is not initialized.",
            parse_mode='Markdown'
        )
        return

    # Get robot state
    mode = "SIMULATION" if robot_controller.simulate else "HARDWARE"
    state = robot_controller.state.value if robot_controller.state else "UNKNOWN"

    status_text = f"🤖 *Robot Status*\n\n"
    status_text += f"📊 *State:* {state}\n"
    status_text += f"🔧 *Mode:* {mode}\n"

    # Add mission info if available
    if robot_controller.mission:
        mission = robot_controller.mission
        status_text += f"\n📍 *Current Mission:*\n"
        status_text += f"   ID: {mission.mission_id}\n"
        status_text += f"   Target: ({mission.target_lat:.6f}, {mission.target_lon:.6f})\n"

    # Add EV3 connection status
    if hasattr(robot_controller, 'ev3') and robot_controller.ev3:
        if hasattr(robot_controller.ev3, 'connected') and robot_controller.ev3.connected:
            ev3_ip = robot_controller.ev3.ev3_ip if hasattr(robot_controller.ev3, 'ev3_ip') else "Unknown"
            status_text += f"\n✅ *EV3:* Connected (`{ev3_ip}`)"
        else:
            status_text += f"\n❌ *EV3:* Disconnected"

    await update.message.reply_text(status_text, parse_mode='Markdown')


def cleanup_robot_controller():
    """
    Cleanup robot controller on shutdown.
    Should be called when bot is stopping.
    """
    global robot_controller, robot_update_task

    if robot_update_task:
        logger.info("Canceling robot update task...")
        robot_update_task.cancel()
        robot_update_task = None

    if robot_controller:
        logger.info("Cleaning up robot controller...")
        try:
            robot_controller.stop()
        except:
            pass
        robot_controller = None
        logger.info("✓ Robot controller cleaned up")
