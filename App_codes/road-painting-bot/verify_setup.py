"""
Setup Verification Script
Checks if all requirements are met before running the bot
"""

import sys
import os
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_status(item, status, message=""):
    """Print status line"""
    symbol = "✓" if status else "✗"
    status_text = "OK" if status else "FAIL"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"

    print(f"{color}{symbol}{reset} {item:.<40} {status_text}")
    if message:
        print(f"  → {message}")


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    is_ok = version.major == 3 and version.minor >= 8

    print_status(
        "Python Version (3.8+)",
        is_ok,
        f"Found: Python {version.major}.{version.minor}.{version.micro}"
    )
    return is_ok


def check_file_exists(filename, description):
    """Check if a file exists"""
    exists = Path(filename).exists()
    print_status(description, exists, f"Path: {filename}")
    return exists


def check_dependencies():
    """Check if required packages are installed"""
    packages = {
        'telegram': 'python-telegram-bot',
        'dotenv': 'python-dotenv',
    }

    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print_status(f"Package: {package}", True)
        except ImportError:
            print_status(
                f"Package: {package}",
                False,
                f"Install with: pip install {package}"
            )
            all_ok = False

    return all_ok


def check_env_file():
    """Check .env file and required variables"""
    if not Path('.env').exists():
        print_status(".env file", False, "Copy .env.example to .env")
        return False

    print_status(".env file", True)

    # Try to load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token or bot_token == 'your_bot_token_here':
            print_status(
                "TELEGRAM_BOT_TOKEN",
                False,
                "Please set your bot token in .env file"
            )
            return False

        print_status("TELEGRAM_BOT_TOKEN", True, "Token configured")
        return True

    except Exception as e:
        print_status(".env configuration", False, str(e))
        return False


def check_project_structure():
    """Check if all required files exist"""
    files = {
        'bot.py': 'Main bot file',
        'config.py': 'Configuration module',
        'database.py': 'Database module',
        'handlers/user_handlers.py': 'User handlers',
        'handlers/inspector_handlers.py': 'Inspector handlers',
        'requirements.txt': 'Dependencies list',
        'README.md': 'Documentation',
    }

    all_ok = True
    for file, desc in files.items():
        if not check_file_exists(file, desc):
            all_ok = False

    return all_ok


def check_database():
    """Check if database can be initialized"""
    try:
        from database import get_db
        db = get_db()
        print_status("Database initialization", True, "SQLite ready")
        return True
    except Exception as e:
        print_status("Database initialization", False, str(e))
        return False


def check_config():
    """Check if configuration is valid"""
    try:
        from config import Config
        Config.validate()
        print_status("Configuration validation", True)
        return True
    except Exception as e:
        print_status("Configuration validation", False, str(e))
        return False


def main():
    """Main verification function"""
    print_header("Road Painting Bot - Setup Verification")

    print("\n📋 Checking System Requirements...")
    python_ok = check_python_version()

    print("\n📦 Checking Dependencies...")
    deps_ok = check_dependencies()

    print("\n📁 Checking Project Structure...")
    structure_ok = check_project_structure()

    print("\n⚙️  Checking Configuration...")
    env_ok = check_env_file()
    config_ok = check_config() if env_ok else False

    print("\n💾 Checking Database...")
    db_ok = check_database()

    # Final summary
    print_header("Verification Summary")

    all_checks = [
        ("Python Version", python_ok),
        ("Dependencies", deps_ok),
        ("Project Structure", structure_ok),
        ("Configuration", config_ok),
        ("Database", db_ok),
    ]

    for check_name, status in all_checks:
        print_status(check_name, status)

    print("\n" + "=" * 60)

    if all(status for _, status in all_checks):
        print("\n✅ All checks passed! You're ready to run the bot.")
        print("\nTo start the bot, run:")
        print("  python bot.py")
        print("\nFor help, see:")
        print("  README.md - Full documentation")
        print("  DOCKER.md - Docker deployment")
        print("\n" + "=" * 60 + "\n")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Copy .env.example to .env")
        print("  3. Add your TELEGRAM_BOT_TOKEN to .env")
        print("  4. Check Python version: python --version")
        print("\nFor detailed help, see README.md")
        print("\n" + "=" * 60 + "\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
