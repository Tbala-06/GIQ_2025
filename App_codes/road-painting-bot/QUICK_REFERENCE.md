# Quick Reference Card

**Road Painting Robot Bot** - Essential commands and information at a glance

## 🚀 Quick Start (30 seconds)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and add your bot token
# TELEGRAM_BOT_TOKEN=your_token_here

# 3. Run (Windows)
run.bat

# 3. Run (Linux/Mac)
chmod +x run.sh && ./run.sh
```

## 📋 File Overview

| File | Purpose | Edit? |
|------|---------|-------|
| `bot.py` | Main application | Rarely |
| `config.py` | Configuration loader | Rarely |
| `database.py` | Database operations | Sometimes |
| `handlers/user_handlers.py` | User commands | Often |
| `handlers/inspector_handlers.py` | Inspector commands | Often |
| `.env` | Your configuration | Always |
| `requirements.txt` | Dependencies | Rarely |

## 🎯 Common Tasks

### Setup New Instance
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env
python verify_setup.py
python bot.py
```

### Add Test Data
```bash
python test_data_generator.py
# Choose option 1
```

### Run Web Dashboard
```bash
python web_dashboard.py
# Open http://localhost:5000
```

### Export Data
```bash
# Via bot: Send /export to bot as inspector
# Or manually:
sqlite3 road_painting.db ".mode csv" ".output export.csv" "SELECT * FROM submissions;"
```

### Backup Database
```bash
cp road_painting.db road_painting.db.backup
```

### View Logs
```bash
tail -f bot.log
```

### Docker Quick Start
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## 💬 Telegram Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Start bot & show help |
| `/help` | Show help message |
| `/report` | Report damaged road |
| `/status` | Check submissions |
| `/cancel` | Cancel current operation |

### Inspector Commands
| Command | Description |
|---------|-------------|
| `/inspector` | Dashboard |
| `/pending` | Review pending |
| `/history` | View decisions |
| `/stats` | Statistics |
| `/export` | Export CSV |

## 🗄️ Database Quick Reference

### Connect to Database
```bash
sqlite3 road_painting.db
```

### Useful Queries
```sql
-- Count submissions by status
SELECT status, COUNT(*) FROM submissions GROUP BY status;

-- Recent submissions
SELECT * FROM submissions ORDER BY timestamp DESC LIMIT 10;

-- Pending submissions
SELECT * FROM submissions WHERE status = 'pending';

-- Today's submissions
SELECT * FROM submissions WHERE DATE(timestamp) = DATE('now');

-- Submissions by user
SELECT * FROM submissions WHERE user_id = 123456789;

-- Delete all submissions (⚠️ CAREFUL!)
DELETE FROM submissions;

-- Exit
.quit
```

## 🔧 Configuration (.env)

### Minimal Configuration
```env
TELEGRAM_BOT_TOKEN=your_token_here
```

### Full Configuration
```env
TELEGRAM_BOT_TOKEN=your_token_here
INSPECTOR_CHAT_IDS=123456789,987654321
DATABASE_PATH=road_painting.db
LOG_LEVEL=INFO
LOG_FILE=bot.log
RATE_LIMIT_PER_MINUTE=10
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot won't start | Check `.env` file, verify token |
| "Access Denied" | Add user ID to `INSPECTOR_CHAT_IDS` |
| Database errors | Delete `road_painting.db`, restart |
| Import errors | Run `pip install -r requirements.txt` |
| Can't send photos | Check Telegram API limits |
| Location not working | Enable location in Telegram settings |

## 📊 Database Schema (Quick)

```
submissions
├── id (PK)
├── user_id
├── username
├── first_name
├── last_name
├── photo_id
├── latitude
├── longitude
├── timestamp
├── status (pending/approved/rejected)
├── inspector_id
├── inspector_username
├── decision_timestamp
├── rejection_reason
└── notes
```

## 🔑 Getting Your Bot Token

1. Open Telegram
2. Search `@BotFather`
3. Send `/newbot`
4. Follow instructions
5. Copy token
6. Paste in `.env` file

## 🆔 Getting Your User ID

1. Open Telegram
2. Search `@userinfobot`
3. Start chat
4. Copy your ID
5. Add to `INSPECTOR_CHAT_IDS` in `.env`

## 📝 Adding New Features

### New User Command
1. Add function in `handlers/user_handlers.py`
2. Register in `bot.py`: `CommandHandler("cmd", function)`
3. Update help text in `start_command`

### New Inspector Command
1. Add function in `handlers/inspector_handlers.py`
2. Register in `bot.py`
3. Add authorization check: `Config.is_inspector(user.id)`

### New Database Field
1. Update schema in `database.py`
2. Delete old database or migrate
3. Update all queries using that table

## 🐳 Docker Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Status
docker-compose ps

# Execute command in container
docker-compose exec road-painting-bot bash
```

## 🧪 Testing Checklist

- [ ] Bot starts without errors
- [ ] `/start` works
- [ ] `/report` flow completes
- [ ] Photo upload works
- [ ] Location sharing works
- [ ] `/status` shows data
- [ ] Inspector can access `/pending`
- [ ] Approve/reject works
- [ ] Notifications sent
- [ ] `/export` generates CSV
- [ ] Web dashboard shows data

## 📈 Monitoring

### Check Bot Status
```bash
ps aux | grep bot.py
```

### Check Logs
```bash
tail -f bot.log | grep ERROR
```

### Check Database Size
```bash
ls -lh road_painting.db
```

### Check Disk Space
```bash
df -h
```

## 🔒 Security Checklist

- [ ] `.env` not committed to git
- [ ] Bot token is secret
- [ ] `INSPECTOR_CHAT_IDS` configured
- [ ] Database backups scheduled
- [ ] Logs reviewed regularly
- [ ] Dependencies up to date

## 📚 Documentation Files

| File | Content |
|------|---------|
| `README.md` | Main documentation |
| `DOCKER.md` | Docker deployment |
| `CONTRIBUTING.md` | Contribution guide |
| `PROJECT_SUMMARY.md` | Project overview |
| `ARCHITECTURE.md` | Technical architecture |
| `QUICK_REFERENCE.md` | This file |

## 🌐 URLs

| Service | URL |
|---------|-----|
| Web Dashboard | http://localhost:5000 |
| Bot API | https://api.telegram.org |
| BotFather | https://t.me/BotFather |
| UserInfoBot | https://t.me/userinfobot |

## 📞 Support

1. Check logs: `tail -f bot.log`
2. Verify setup: `python verify_setup.py`
3. Check this guide
4. Review README.md
5. Check ARCHITECTURE.md
6. Open GitHub issue

## 🎨 Emoji Reference

Used in bot messages:
- 🤖 Robot/Bot
- 🛣️ Road
- 📸 Photo
- 📍 Location
- ✅ Success/Approved
- ❌ Error/Rejected
- ⏳ Pending
- 📊 Statistics
- 🔍 Inspector
- 📝 Submission

## 💡 Pro Tips

1. **Test mode**: Leave `INSPECTOR_CHAT_IDS` empty to allow anyone as inspector
2. **Quick restart**: `Ctrl+C` then `python bot.py`
3. **Clean database**: Delete `road_painting.db` for fresh start
4. **View pretty logs**: `tail -f bot.log | grep -E "INFO|ERROR"`
5. **Multiple bots**: Copy folder, use different `.env`
6. **Development**: Set `LOG_LEVEL=DEBUG` in `.env`

## ⚡ Performance Tips

- Keep database under 100MB for best performance
- Restart bot weekly for memory cleanup
- Monitor log file size
- Use CSV export to archive old data
- Consider PostgreSQL for 10,000+ submissions

## 🔄 Common Workflows

### Daily Inspector Workflow
```
1. /inspector  (check pending count)
2. /pending    (review submissions)
3. Approve/reject each
4. /stats      (check today's work)
```

### Weekly Maintenance
```
1. Check logs for errors
2. Backup database
3. Export data (CSV)
4. Clear old logs
5. Update dependencies (if needed)
```

### New User Onboarding
```
1. /start      (read instructions)
2. /report     (try submitting)
3. /status     (check submission)
```

## 🎓 Learning Path

1. Read `README.md` - Understand basics
2. Run `verify_setup.py` - Check setup
3. Test as user - Submit report
4. Test as inspector - Approve report
5. Read `ARCHITECTURE.md` - Understand design
6. Modify handlers - Add features
7. Read `CONTRIBUTING.md` - Best practices

---

**Pro Tip**: Bookmark this file for quick reference! 🔖

**Version**: 1.0.0
**Last Updated**: 2024
