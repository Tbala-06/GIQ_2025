"""
Road Painting Robot Bot - Main Entry Point
A Telegram bot for reporting damaged roads and managing robot deployments
"""

import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Import configuration and database
from config import Config
from database import get_db

# Import handlers
from handlers.user_handlers import (
    start_command,
    help_command,
    status_command,
    get_report_conversation_handler
)
from handlers.inspector_handlers import (
    inspector_command,
    pending_command,
    history_command,
    stats_command,
    export_command,
    get_inspector_handlers
)
from handlers.robot_handlers import (
    simulate_command,
    robotstatus_command,
    initialize_robot_controller,
    cleanup_robot_controller
)


# Configure logging
def setup_logging():
    """Setup logging configuration"""
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce telegram library logging
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger = logging.getLogger(__name__)
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

    # Notify user of error
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Sorry, an error occurred while processing your request.\n"
                "Please try again later or contact support if the problem persists."
            )
        except Exception as e:
            logger.error(f"Error sending error message to user: {e}")


# Unknown command handler
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        "❓ Unknown command.\n\n"
        "Use /help to see available commands."
    )


def main():
    """Main function to run the bot"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Starting Road Painting Robot Bot")
    logger.info("=" * 60)

    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set")
        sys.exit(1)

    # Initialize database
    try:
        db = get_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        sys.exit(1)

    # Initialize robot controller (if available)
    # Set simulate=True to run without hardware, or specify ev3_ip
    robot_available = initialize_robot_controller(simulate=False, ev3_ip=None)
    if robot_available:
        logger.info("Robot controller initialized and ready")
    else:
        logger.warning("Robot controller not available - /simulate command will not work")

    # Create application
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    logger.info("Registering handlers...")

    # Register user command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))

    # Register report conversation handler
    application.add_handler(get_report_conversation_handler())

    # Register inspector command handlers
    application.add_handler(CommandHandler("inspector", inspector_command))
    application.add_handler(CommandHandler("pending", pending_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("export", export_command))

    # Register inspector callback handlers
    for handler in get_inspector_handlers():
        application.add_handler(handler)

    # Register robot command handlers
    application.add_handler(CommandHandler("simulate", simulate_command))
    application.add_handler(CommandHandler("robotstatus", robotstatus_command))

    # Register unknown command handler (should be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register error handler
    application.add_error_handler(error_handler)

    logger.info("All handlers registered successfully")

    # Show configuration info
    inspector_ids = Config.get_inspector_ids()
    if inspector_ids:
        logger.info(f"Authorized inspectors: {inspector_ids}")
    else:
        logger.warning("No inspector IDs configured - any user can access inspector mode!")

    # Start the bot
    logger.info("Starting bot with polling...")
    logger.info("Bot is now running. Press Ctrl+C to stop.")
    logger.info("=" * 60)

    try:
        # Run the bot until Ctrl+C
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup robot controller
        cleanup_robot_controller()
        logger.info("Bot stopped")
        logger.info("=" * 60)


if __name__ == '__main__':
    main()
