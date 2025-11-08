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
    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
"""

import time
import logging
import argparse
import sys
import os
import asyncio
from typing import Optional

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'App_codes', 'road-painting-bot'))

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

# Configuration
try:
    # Try to import from bot config
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'App_codes', 'road-painting-bot'))
    from config import Config
    TELEGRAM_BOT_TOKEN = Config.TELEGRAM_BOT_TOKEN
    MQTT_TOPIC_DEPLOY = Config.MQTT_TOPIC_COMMANDS
except ImportError:
    # Fallback to environment or default
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    MQTT_TOPIC_DEPLOY = "bot/commands/deploy"

logger = logging.getLogger(__name__)


class RobotTestController:
    """
    Robot test controller that integrates with Telegram bot.
    Receives commands via Telegram and controls EV3 motors.
    """

    def __init__(self, simulate=False):
        """
        Initialize test controller.

        Args:
            simulate: If True, simulates EV3 without hardware
        """
        self.simulate = simulate
        self.ev3 = None
        self.running = False
        self.telegram_app = None

        logger.info("=" * 70)
        logger.info("ROBOT TEST CONTROLLER - TELEGRAM INTEGRATION")
        logger.info("=" * 70)
        logger.info("Mode: {}".format('SIMULATION' if simulate else 'HARDWARE'))
        logger.info("=" * 70)

    async def start(self):
        """Start the controller"""
        try:
            # Connect to EV3
            logger.info("→ Connecting to EV3...")
            self.ev3 = EV3Controller(simulate=self.simulate)
            if not self.ev3.connect():
                logger.error("✗ EV3 connection failed")
                return False
            logger.info("✓ EV3 connected")

            self.running = True
            return True

        except Exception as e:
            logger.error("✗ Startup failed: {}".format(e))
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

            result = self.ev3.move_forward(30, speed=40)
            if result:
                left_enc, right_enc = result
                logger.info("   ✓ Forward complete")
                logger.info("     Encoders: Left={}, Right={}".format(left_enc, right_enc))
                if update:
                    await update.message.reply_text(
                        "✓ Forward complete\nEncoders: L={}, R={}".format(left_enc, right_enc)
                    )
            else:
                logger.error("   ✗ Forward failed")
                if update:
                    await update.message.reply_text("✗ Forward movement failed")

            # Wait
            logger.info("\n   Waiting 2 seconds...")
            await asyncio.sleep(2)

            # Test 2: Move backward
            logger.info("\n→ Test 2: Moving BACKWARD 30cm...")
            if update:
                await update.message.reply_text("→ Moving backward 30cm...")

            result = self.ev3.move_backward(30, speed=40)
            if result:
                left_enc, right_enc = result
                logger.info("   ✓ Backward complete")
                logger.info("     Encoders: Left={}, Right={}".format(left_enc, right_enc))
                if update:
                    await update.message.reply_text(
                        "✓ Backward complete\nEncoders: L={}, R={}".format(left_enc, right_enc)
                    )
            else:
                logger.error("   ✗ Backward failed")
                if update:
                    await update.message.reply_text("✗ Backward movement failed")

            # Wait
            logger.info("\n   Waiting 2 seconds...")
            await asyncio.sleep(2)

            # Test 3: Stop
            logger.info("\n→ Test 3: Stopping motors...")
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
            if update:
                await update.message.reply_text(
                    "✗ Motor test error: {}".format(e)
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
        if self.ev3:
            logger.info("  Stopping motors...")
            self.ev3.stop()
            logger.info("  Disconnecting EV3...")
            self.ev3.disconnect()

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

    # Get encoder positions
    if controller.ev3:
        try:
            left, right = controller.ev3.get_encoder_positions()
            status_text = (
                "✅ *Robot Status: ONLINE*\n\n"
                "🤖 *EV3 Controller:* Connected\n"
                "📊 *Encoders:*\n"
                "• Left: `{}`\n"
                "• Right: `{}`\n\n"
                "Mode: {}".format(
                    left, right,
                    'Simulation' if controller.simulate else 'Hardware'
                )
            )
        except:
            status_text = (
                "⚠️ *Robot Status: CONNECTED*\n\n"
                "EV3 connected but cannot read encoders.\n\n"
                "Mode: {}".format('Simulation' if controller.simulate else 'Hardware')
            )
    else:
        status_text = "❌ *Robot Status: EV3 DISCONNECTED*"

    await update.message.reply_text(status_text, parse_mode='Markdown')


# ============================================================================
# MAIN
# ============================================================================

async def main_async(simulate: bool, token: str):
    """Async main function"""
    global controller

    # Initialize controller
    controller = RobotTestController(simulate=simulate)
    if not await controller.start():
        logger.error("Failed to start controller")
        return

    if not TELEGRAM_AVAILABLE:
        logger.error("python-telegram-bot not installed - cannot start")
        controller.stop()
        return

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment or config")
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
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        controller.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Robot Test with Telegram Integration')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode (no EV3 hardware)')
    parser.add_argument('--token', type=str, default=TELEGRAM_BOT_TOKEN,
                       help='Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run async main
    try:
        asyncio.run(main_async(args.simulate, args.token))
    except KeyboardInterrupt:
        print("\n\nShutdown complete")


if __name__ == "__main__":
    main()
