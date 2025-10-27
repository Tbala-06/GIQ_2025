"""
Configuration module for Road Painting Bot
Loads environment variables and provides configuration settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for bot settings"""

    # Telegram Bot Token (required)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # Inspector Chat IDs (comma-separated list of authorized inspector user IDs)
    # If empty, any user can access inspector mode
    INSPECTOR_CHAT_IDS = os.getenv('INSPECTOR_CHAT_IDS', '')

    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///road_painting.db')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'road_painting.db')

    # Secret key for sessions (not used in current implementation but available for future)
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-to-random-secret-key')

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

    # Rate limiting (requests per minute per user)
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '10'))

    # Webhook configuration (for future use)
    WEBHOOK_ENABLED = os.getenv('WEBHOOK_ENABLED', 'False').lower() == 'true'
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8443'))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required in .env file")
        return True

    @classmethod
    def get_inspector_ids(cls):
        """Get list of authorized inspector user IDs"""
        if not cls.INSPECTOR_CHAT_IDS:
            return []
        return [int(id.strip()) for id in cls.INSPECTOR_CHAT_IDS.split(',') if id.strip()]

    @classmethod
    def is_inspector(cls, user_id: int) -> bool:
        """Check if user is authorized inspector"""
        inspector_ids = cls.get_inspector_ids()
        # If no inspector IDs configured, allow anyone (for testing)
        if not inspector_ids:
            return True
        return user_id in inspector_ids
