# Road Painting Robot Bot 🤖🛣️

A comprehensive Telegram bot system for reporting damaged roads and managing road painting robot deployments.

## Features

### User Features
- 📸 Report damaged roads with photos
- 📍 Share location using Telegram's location picker
- 📊 Check submission status
- 🔔 Receive notifications on approval/rejection

### Inspector Features
- 🔍 Review pending submissions
- ✅ Approve submissions for robot deployment
- ❌ Reject submissions with reasons
- 📈 View statistics and analytics
- 📥 Export data to CSV
- 📚 View decision history

## Quick Start

### Prerequisites

- Python 3.8 or higher
- A Telegram account
- Basic knowledge of command line

### 1. Get Your Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send `/newbot`
3. Follow the instructions to create your bot
4. Copy the bot token (it looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. **Important**: Send `/setprivacy` to @BotFather, select your bot, and choose "Disable" to allow the bot to receive all messages in groups

### 2. Find Your Telegram User ID

To restrict inspector access to specific users:

1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Start a chat and it will show your user ID
3. Copy your user ID (it's a number like `123456789`)

### 3. Installation

```bash
# Clone or download this repository
cd road-painting-bot

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your favorite text editor
# Add your bot token and inspector IDs
```

Edit the `.env` file:

```env
# Required: Your Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: Comma-separated list of Telegram user IDs who can access inspector mode
# Leave empty for testing (allows anyone to be inspector)
INSPECTOR_CHAT_IDS=123456789,987654321

# Database (default is fine for most use cases)
DATABASE_PATH=road_painting.db

# Logging (default is fine)
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

### 5. Run the Bot

```bash
# Make sure your virtual environment is activated
python bot.py
```

You should see output like:
```
============================================================
Starting Road Painting Robot Bot
============================================================
2024-01-15 10:30:00 - __main__ - INFO - Configuration validated successfully
2024-01-15 10:30:00 - __main__ - INFO - Database initialized successfully
2024-01-15 10:30:00 - __main__ - INFO - Registering handlers...
2024-01-15 10:30:00 - __main__ - INFO - All handlers registered successfully
2024-01-15 10:30:00 - __main__ - INFO - Starting bot with polling...
2024-01-15 10:30:00 - __main__ - INFO - Bot is now running. Press Ctrl+C to stop.
============================================================
```

## Usage Guide

### For Users

1. **Start the bot**
   - Find your bot on Telegram (using the username you created)
   - Send `/start` to begin

2. **Report a damaged road**
   ```
   /report
   ```
   - Bot will ask for a photo - take or upload a picture of the damaged road
   - Bot will ask for location - tap "Share Location" button
   - Confirm your submission
   - You'll receive a unique submission ID

3. **Check your submissions**
   ```
   /status
   ```
   - View all your submissions and their status
   - See approval/rejection details

### For Inspectors

1. **Access inspector dashboard**
   ```
   /inspector
   ```
   - View overall statistics
   - See pending submissions count

2. **Review pending submissions**
   ```
   /pending
   ```
   - Bot will show each pending submission with:
     - Photo of damaged road
     - User information
     - Location coordinates
     - Submission timestamp
   - For each submission, you can:
     - ✅ Approve & Deploy - Approve and initiate robot deployment
     - ❌ Reject - Reject the submission
     - 📍 View on Map - See exact location on map

3. **View decision history**
   ```
   /history
   ```
   - See recent approval/rejection decisions
   - Track which inspector made each decision

4. **View detailed statistics**
   ```
   /stats
   ```
   - Total submissions, approvals, rejections
   - Today's activity
   - Approval rate

5. **Export data**
   ```
   /export
   ```
   - Download all submissions as CSV file
   - Great for analysis or reporting

## Project Structure

```
road-painting-bot/
├── .env                          # Environment variables (create from .env.example)
├── .env.example                  # Example environment file
├── .gitignore                    # Git ignore file
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── bot.py                        # Main bot entry point
├── config.py                     # Configuration loader
├── database.py                   # Database operations
├── bot.log                       # Log file (created on first run)
├── road_painting.db             # SQLite database (created on first run)
└── handlers/
    ├── __init__.py              # Package initialization
    ├── user_handlers.py         # User command handlers
    └── inspector_handlers.py    # Inspector command handlers
```

## Commands Reference

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and instructions |
| `/help` | Show help message |
| `/report` | Start new road damage report |
| `/status` | Check status of your submissions |
| `/cancel` | Cancel current report submission |

### Inspector Commands
| Command | Description |
|---------|-------------|
| `/inspector` | View inspector dashboard |
| `/pending` | Review pending submissions |
| `/history` | View recent decisions |
| `/stats` | Show detailed statistics |
| `/export` | Export submissions to CSV |

## Database Schema

### submissions table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| user_id | INTEGER | Telegram user ID |
| username | TEXT | Telegram username |
| first_name | TEXT | User's first name |
| last_name | TEXT | User's last name |
| photo_id | TEXT | Telegram photo file ID |
| latitude | REAL | Location latitude |
| longitude | REAL | Location longitude |
| timestamp | DATETIME | Submission timestamp |
| status | TEXT | Status: pending/approved/rejected |
| inspector_id | INTEGER | Inspector's Telegram user ID |
| inspector_username | TEXT | Inspector's username |
| decision_timestamp | DATETIME | When decision was made |
| rejection_reason | TEXT | Reason for rejection |
| notes | TEXT | Additional notes |

## Troubleshooting

### Bot doesn't respond
- Check if bot is running (`python bot.py`)
- Verify bot token in `.env` file
- Check logs in `bot.log` file

### Can't access inspector mode
- Verify your user ID is in `INSPECTOR_CHAT_IDS` in `.env`
- If `INSPECTOR_CHAT_IDS` is empty, anyone can access (useful for testing)
- Restart bot after changing `.env` file

### Database errors
- Delete `road_painting.db` file and restart bot (will create fresh database)
- Check file permissions

### Import errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Bot crashes on startup
- Check `bot.log` for error details
- Verify all required fields in `.env` are set
- Make sure Python 3.8+ is installed: `python --version`

## Development

### Running in Development Mode

```bash
# Set log level to DEBUG for verbose logging
# Edit .env:
LOG_LEVEL=DEBUG

# Run bot
python bot.py
```

### Adding Test Data

You can manually test the system by:
1. Running the bot
2. Opening Telegram
3. Sending `/report` and following the flow
4. Using a second account or asking a friend to test inspector mode

### Database Access

To view the database directly:

```bash
# Install SQLite browser or use command line
sqlite3 road_painting.db

# View submissions
SELECT * FROM submissions;

# Exit
.quit
```

## Security Considerations

### Production Deployment

1. **Set Inspector IDs**: Never leave `INSPECTOR_CHAT_IDS` empty in production
2. **Secure Bot Token**: Keep your bot token secret, never commit `.env` to git
3. **Database Backups**: Regularly backup `road_painting.db`
4. **Use HTTPS**: When using webhooks, always use HTTPS
5. **Monitor Logs**: Check `bot.log` regularly for suspicious activity

### Rate Limiting

The bot includes basic rate limiting (configurable in `.env`):
```env
RATE_LIMIT_PER_MINUTE=10
```

## Future Enhancements

### Webhook Mode (For Production)

Currently uses polling (good for testing). For production:

1. Get a domain with HTTPS
2. Set up webhook configuration in `.env`:
   ```env
   WEBHOOK_ENABLED=True
   WEBHOOK_URL=https://yourdomain.com/webhook
   WEBHOOK_PORT=8443
   ```

### Web Dashboard

Create a Flask/FastAPI app to:
- View submissions on a map
- Advanced analytics
- Bulk operations

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions:
1. Check this README
2. Check `bot.log` for error messages
3. Review the Troubleshooting section
4. Create an issue on GitHub

## Acknowledgments

- Built with [python-telegram-bot](https://python-telegram-bot.org/)
- Uses SQLite for data storage
- Inspired by smart city initiatives

---

Made with ❤️ for better roads 🛣️
