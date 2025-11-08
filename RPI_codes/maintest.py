#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Test Script with Telegram Bot Integration
===============================================

Integrates with Telegram bot to receive commands and test EV3 motors.

Commands:
- /simulation - Run motor test sequence (forward 30cm, backward 30cm)
- Deploy commands from bot - Display coordinates and test motors

Usage:
    python3 maintest.py                # Hardware mode
    python3 maintest.py --simulate     # Simulation mode (no EV3)
"""

import time
import logging
import argparse
import sys
import os
import asyncio
from typing import Optional

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import configuration
from config import Config

# Import EV3 controller
from ev3_comm import EV3Controller

# Import Telegram bot components
try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: python-telegram-bot not installed")
    print("   Install with: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False

# Get configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
MQTT_TOPIC_DEPLOY = Config.MQTT_TOPIC_DEPLOY  # Fixed: Use MQTT_TOPIC_DEPLOY

logger = logging.getLogger(__name__)


class RobotTestController:
    """
    Robot test controller that integrates with Telegram bot.
    Receives commands via Telegram and controls EV3 motors.
    """

    def __init__(self, simulate=False, ev3_ip=None):
        """
        Initialize test controller.

        Args:
            simulate: If True, simulates EV3 without hardware
            ev3_ip: EV3 IP address (None for auto-detect)
        """
        self.simulate = simulate
        self.ev3_ip = ev3_ip
        self.ev3 = None
        self.running = False
        self.telegram_app = None

        logger.info("=" * 70)
        logger.info("ROBOT TEST CONTROLLER - TELEGRAM INTEGRATION")
        logger.info("=" * 70)
        logger.info("Mode: {}".format('SIMULATION' if simulate else 'HARDWARE'))
        if ev3_ip:
            logger.info("EV3 IP: {}".format(ev3_ip))
        else:
            logger.info("EV3 IP: Auto-detect")
        logger.info("=" * 70)

    async def start(self):
        """Start the controller"""
        try:
            # Connect to EV3
            logger.info("→ Connecting to EV3...")
            self.ev3 = EV3Controller(ev3_ip=self.ev3_ip)
            
            if not self.simulate:
                if not self.ev3.connect():
                    logger.error("✗ EV3 connection failed")
                    return False
                logger.info("✓ EV3 connected at {}".format(self.ev3.ev3_ip))
            else:
                logger.info("✓ Simulation mode - no hardware connection")

            self.running = True
            return True

        except Exception as e:
            logger.error("✗ Startup failed: {}".format(e))
            import traceback
            traceback.print_exc()
            return False

    async def test_motors(self, update: Update = None, test_name: str = "Manual Test"):
        """
        Test EV3 motor movements.

        Args:
            update: Telegram update (for sending messages)
            test_name: Name of the test
        """
        try:
            if update:
                await update.message.reply_text(
                    "🤖 *Motor Test Starting*\n\n"
                    "Running motor test sequence...",
                    parse_mode='Markdown'
                )

            logger.info("")
            logger.info("🤖 Testing EV3 Motors - {}".format(test_name))
            logger.info("-" * 70)

            # Test 1: Move forward
            logger.info("\n→ Test 1: Moving FORWARD 30cm...")
            if update:
                await update.message.reply_text("→ Moving forward 30cm...")

            if self.simulate:
                logger.info("   ✓ [SIMULATED] Forward complete")
                if update:
                    await update.message.reply_text("✓ [SIMULATED] Forward complete")
            else:
                result = self.ev3.move_forward(30)
                logger.info("   Response: {}".format(result))
                if "DONE" in str(result):
                    logger.info("   ✓ Forward complete")
                    if update:
                        await update.message.reply_text("✓ Forward complete")
                else:
                    logger.error("   ✗ Forward failed: {}".format(result))
                    if update:
                        await update.message.reply_text("✗ Forward failed: {}".format(result))

            # Wait
            logger.info("\n   Waiting 2 seconds...")
            await asyncio.sleep(2)

            # Test 2: Move backward
            logger.info("\n→ Test 2: Moving BACKWARD 30cm...")
            if update:
                await update.message.reply_text("→ Moving backward 30cm...")

            if self.simulate:
                logger.info("   ✓ [SIMULATED] Backward complete")
                if update:
                    await update.message.reply_text("✓ [SIMULATED] Backward complete")
            else:
                result = self.ev3.move_backward(30)
                logger.info("   Response: {}".format(result))
                if "DONE" in str(result):
                    logger.info("   ✓ Backward complete")
                    if update:
                        await update.message.reply_text("✓ Backward complete")
                else:
                    logger.error("   ✗ Backward failed: {}".format(result))
                    if update:
                        await update.message.reply_text("✗ Backward failed: {}".format(result))

            # Wait
            logger.info("\n   Waiting 2 seconds...")
            await asyncio.sleep(2)

            # Test 3: Stop
            logger.info("\n→ Test 3: Stopping motors...")
            if not self.simulate:
                self.ev3.stop()
            logger.info("   ✓ Motors stopped")

            logger.info("\n" + "-" * 70)
            logger.info("✅ Motor test sequence complete!")
            logger.info("-" * 70)

            if update:
                await update.message.reply_text(
                    "✅ *Motor Test Complete!*\n\n"
                    "All movements executed successfully.",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error("\n✗ Motor test error: {}".format(e))
            import traceback
            traceback.print_exc()
            if update:
                await update.message.reply_text(
                    "✗ Motor test error: {}".format(str(e))
                )

    async def handle_deploy_command(self, job_id, latitude, longitude, update: Update = None):
        """
        Handle deploy command with coordinates.

        Args:
            job_id: Job identifier
            latitude: Target latitude
            longitude: Target longitude
            update: Telegram update (for sending messages)
        """
        logger.info("\n" + "🎯" * 35)
        logger.info("DEPLOY COMMAND RECEIVED!")
        logger.info("🎯" * 35)

        logger.info("\n📋 Deployment Information:")
        logger.info("   Job ID:    {}".format(job_id))
        logger.info("   Latitude:  {:.6f}".format(latitude))
        logger.info("   Longitude: {:.6f}".format(longitude))
        logger.info("\n" + "=" * 70)

        # Send Telegram response
        if update:
            await update.message.reply_text(
                "🎯 *Deploy Command Received*\n\n"
                "📋 *Deployment Info:*\n"
                "• Job ID: `{}`\n"
                "• Latitude: `{:.6f}`\n"
                "• Longitude: `{:.6f}`\n\n"
                "Starting motor test...".format(job_id, latitude, longitude),
                parse_mode='Markdown'
            )

        # Test motors
        await self.test_motors(update, "Deploy Test - Job {}".format(job_id))

        logger.info("\n" + "=" * 70)
        logger.info("✅ DEPLOY TEST COMPLETE")
        logger.info("=" * 70)

    def stop(self):
        """Stop and cleanup"""
        logger.info("\n→ Shutting down...")

        self.running = False

        # Stop EV3
        if self.ev3 and not self.simulate:
            logger.info("  Stopping motors...")
            try:
                self.ev3.stop()
            except:
                pass
            logger.info("  Disconnecting EV3...")
            try:
                self.ev3.close()
            except:
                pass

        logger.info("✓ Shutdown complete")


# ============================================================================
# TELEGRAM BOT HANDLERS
# ============================================================================

# Global controller instance
controller: Optional[RobotTestController] = None


async def simulation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /simulation command - runs motor test sequence.
    """
    global controller

    logger.info("Received /simulation command from user {}".format(update.effective_user.id))

    if not controller or not controller.running:
        await update.message.reply_text(
            "❌ Robot controller not initialized.\n"
            "Please start maintest.py first."
        )
        return

    await update.message.reply_text(
        "🚀 *Simulation Mode Activated*\n\n"
        "Running motor test sequence...",
        parse_mode='Markdown'
    )

    # Run motor test
    await controller.test_motors(update, "Telegram Simulation Command")


async def deploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /deploy command - test deployment with coordinates.

    Usage: /deploy <lat> <lon>
    """
    global controller

    if not controller or not controller.running:
        await update.message.reply_text(
            "❌ Robot controller not initialized.\n"
            "Please start maintest.py first."
        )
        return

    # Parse arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid format.\n\n"
            "Usage: `/deploy <latitude> <longitude>`\n\n"
            "Example: `/deploy 1.3521 103.8198`",
            parse_mode='Markdown'
        )
        return

    try:
        lat = float(context.args[0])
        lon = float(context.args[1])
        job_id = int(time.time())

        # Handle deploy
        await controller.handle_deploy_command(job_id, lat, lon, update)

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid coordinates.\n"
            "Please provide valid numbers for latitude and longitude."
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /robotstatus command - show robot status.
    """
    global controller

    if not controller or not controller.running:
        await update.message.reply_text(
            "❌ *Robot Status: OFFLINE*\n\n"
            "Controller is not running.",
            parse_mode='Markdown'
        )
        return

    # Get status
    if controller.ev3 and not controller.simulate:
        try:
            status_text = (
                "✅ *Robot Status: ONLINE*\n\n"
                "🤖 *EV3 Controller:* Connected\n"
                "📡 *EV3 IP:* `{}`\n\n"
                "Mode: Hardware".format(controller.ev3.ev3_ip)
            )
        except:
            status_text = (
                "⚠️ *Robot Status: CONNECTED*\n\n"
                "EV3 connected but status unavailable.\n\n"
                "Mode: Hardware"
            )
    elif controller.simulate:
        status_text = (
            "✅ *Robot Status: SIMULATION*\n\n"
            "Running in simulation mode.\n"
            "No hardware connected."
        )
    else:
        status_text = "❌ *Robot Status: EV3 DISCONNECTED*"

    await update.message.reply_text(status_text, parse_mode='Markdown')


# ============================================================================
# MAIN
# ============================================================================

async def main_async(simulate: bool, ev3_ip: str, token: str):
    """Async main function"""
    global controller

    # Print configuration
    Config.print_config()

    # Initialize controller
    controller = RobotTestController(simulate=simulate, ev3_ip=ev3_ip)
    if not await controller.start():
        logger.error("Failed to start controller")
        return

    if not TELEGRAM_AVAILABLE:
        logger.error("python-telegram-bot not installed - cannot start")
        logger.error("Install with: pip install python-telegram-bot")
        controller.stop()
        return

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        logger.error("Set it in environment: export TELEGRAM_BOT_TOKEN='your_token'")
        controller.stop()
        return

    # Create Telegram application
    logger.info("→ Starting Telegram bot...")
    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("simulation", simulation_command))
    application.add_handler(CommandHandler("deploy", deploy_command))
    application.add_handler(CommandHandler("robotstatus", status_command))

    logger.info("✓ Telegram bot handlers registered")
    logger.info("")
    logger.info("=" * 70)
    logger.info("🎯 READY - Bot is running!")
    logger.info("=" * 70)
    logger.info("Available commands:")
    logger.info("  /simulation - Run motor test sequence")
    logger.info("  /deploy <lat> <lon> - Test deployment with coordinates")
    logger.info("  /robotstatus - Show robot status")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 70)

    try:
        # Run the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

        # Keep running until interrupted
        while controller.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error("Fatal error: {}".format(e))
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        logger.info("Stopping bot...")
        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except:
            pass
        controller.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Robot Test with Telegram Integration')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode (no EV3 hardware)')
    parser.add_argument('--ev3-ip', type=str, default=None,
                       help='EV3 IP address (e.g., 169.254.14.120)')
    parser.add_argument('--token', type=str, default=TELEGRAM_BOT_TOKEN,
                       help='Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Run async main
    try:
        asyncio.run(main_async(args.simulate, args.ev3_ip, args.token))
    except KeyboardInterrupt:
        print("\n\nShutdown complete")


if __name__ == "__main__":
    main()