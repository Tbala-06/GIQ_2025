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


def initialize_robot_controller(simulate=False, ev3_ip=None):
    """
    Initialize the robot controller.
    This should be called once when the bot starts.

    Args:
        simulate: If True, runs in simulation mode (no EV3 hardware)
        ev3_ip: EV3 IP address (None for auto-detect)

    Returns:
        True if successful, False otherwise
    """
    global robot_controller

    try:
        # Import here to avoid issues if EV3 not available
        from ev3_comm import EV3Controller

        logger.info("Initializing robot controller...")
        logger.info("Mode: {}".format('SIMULATION' if simulate else 'HARDWARE'))
        if ev3_ip:
            logger.info("EV3 IP: {}".format(ev3_ip))

        robot_controller = EV3Controller(ev3_ip=ev3_ip, simulate=simulate)

        if not simulate:
            if robot_controller.connect():
                logger.info("✓ Robot controller connected at {}".format(robot_controller.ev3_ip))
                return True
            else:
                logger.error("✗ Robot controller connection failed")
                robot_controller = None
                return False
        else:
            logger.info("✓ Robot controller in simulation mode")
            return True

    except ImportError as e:
        logger.error("Cannot import EV3 controller: {}".format(e))
        logger.error("Make sure RPI_codes/ev3_comm.py is available")
        robot_controller = None
        return False
    except Exception as e:
        logger.error("Robot controller initialization error: {}".format(e))
        robot_controller = None
        return False


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

    # Check if it's in simulation mode
    if hasattr(robot_controller, 'simulate') and robot_controller.simulate:
        status_text = (
            "✅ *Robot Status: SIMULATION*\n\n"
            "Running in simulation mode.\n"
            "No hardware connected."
        )
    elif robot_controller.connected:
        try:
            status_text = (
                "✅ *Robot Status: ONLINE*\n\n"
                "🤖 *EV3 Controller:* Connected\n"
                "📡 *EV3 IP:* `{}`\n\n"
                "Mode: Hardware".format(robot_controller.ev3_ip)
            )
        except:
            status_text = (
                "⚠️ *Robot Status: CONNECTED*\n\n"
                "EV3 connected but status unavailable.\n\n"
                "Mode: Hardware"
            )
    else:
        status_text = "❌ *Robot Status: EV3 DISCONNECTED*"

    await update.message.reply_text(status_text, parse_mode='Markdown')


def cleanup_robot_controller():
    """
    Cleanup robot controller on shutdown.
    Should be called when bot is stopping.
    """
    global robot_controller

    if robot_controller:
        logger.info("Cleaning up robot controller...")
        try:
            robot_controller.stop()
            robot_controller.disconnect()
        except:
            pass
        robot_controller = None
        logger.info("✓ Robot controller cleaned up")
