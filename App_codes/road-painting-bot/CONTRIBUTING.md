# Contributing to Road Painting Bot

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Quick Start for Contributors

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/road-painting-bot.git
   cd road-painting-bot
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment**
   ```bash
   cp .env.example .env
   # Add your test bot token
   ```

6. **Verify setup**
   ```bash
   python verify_setup.py
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add comments for complex logic
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run the bot
python bot.py

# Test with sample data
python test_data_generator.py

# Verify setup still works
python verify_setup.py
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Build process or auxiliary tool changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python Style

Follow PEP 8 with these specifics:

```python
# Good: Clear function names with docstrings
def get_pending_submissions(limit: int = 10) -> List[Dict]:
    """
    Get all pending submissions from database

    Args:
        limit: Maximum number of submissions to return

    Returns:
        List of submission dictionaries
    """
    # Implementation
    pass

# Good: Type hints
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

# Good: Descriptive variable names
submission_id = db.create_submission(...)
pending_count = db.get_pending_submissions()

# Bad: Unclear names
x = db.create(...)
n = db.get()
```

### Documentation

- Add docstrings to all public functions
- Update README.md for new features
- Add inline comments for complex logic
- Document configuration changes in .env.example

### Error Handling

Always use try-except for operations that can fail:

```python
try:
    db.update_submission_status(...)
    logger.info("Submission updated successfully")
except Exception as e:
    logger.error(f"Error updating submission: {e}")
    await update.message.reply_text("Error message")
```

### Logging

Use appropriate log levels:

```python
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
```

## Project Structure

When adding new files:

```
road-painting-bot/
├── bot.py                    # Main entry point - minimal changes
├── config.py                 # Add new config options here
├── database.py               # Add new database operations here
├── handlers/
│   ├── user_handlers.py     # Add user commands here
│   ├── inspector_handlers.py # Add inspector commands here
│   └── new_handlers.py      # Create new handler files as needed
├── utils/                    # Create for utility functions
│   └── helpers.py
└── tests/                    # Create for tests
    └── test_handlers.py
```

## Adding New Features

### Example: Adding a New User Command

1. **Add handler function** in `handlers/user_handlers.py`:

```python
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new command"""
    user = update.effective_user

    try:
        # Your logic here
        await update.message.reply_text("Response")
        logger.info(f"User {user.id} used /new command")
    except Exception as e:
        logger.error(f"Error in new command: {e}")
        await update.message.reply_text("Error occurred")
```

2. **Register handler** in `bot.py`:

```python
application.add_handler(CommandHandler("new", new_command))
```

3. **Update documentation**:
   - Add to README.md command list
   - Update help message in `start_command`

4. **Test the feature**

### Example: Adding Database Functionality

1. **Add method** in `database.py`:

```python
def get_submissions_by_status(self, status: str) -> List[Dict]:
    """Get submissions filtered by status"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM submissions WHERE status = ? ORDER BY timestamp DESC',
            (status,)
        )
        return [dict(row) for row in cursor.fetchall()]
```

2. **Add tests** (if test suite exists)

3. **Use in handlers**

## Testing Guidelines

### Manual Testing Checklist

Before submitting a PR, test:

- [ ] Bot starts without errors
- [ ] /start command works
- [ ] /report flow completes successfully
- [ ] Photo upload works
- [ ] Location sharing works
- [ ] /status shows submissions
- [ ] Inspector mode accessible
- [ ] /pending shows submissions
- [ ] Approve/reject buttons work
- [ ] User receives notifications
- [ ] CSV export works
- [ ] Web dashboard displays data
- [ ] No errors in logs

### Test Data

Use the test data generator:

```bash
python test_data_generator.py
# Option 1: Generate default test data
```

## Common Tasks

### Adding a Configuration Option

1. Add to `.env.example`:
```env
NEW_OPTION=default_value
```

2. Add to `config.py`:
```python
NEW_OPTION = os.getenv('NEW_OPTION', 'default_value')
```

3. Document in README.md

### Adding a Database Field

1. This requires database migration - discuss in an issue first
2. Add field to schema in `database.py`
3. Update all related queries
4. Create migration script if needed

### Adding a New Dependency

1. Add to `requirements.txt`:
```
new-package==1.0.0
```

2. Update `verify_setup.py` if it's critical:
```python
packages = {
    'new_module': 'new-package',
}
```

3. Document in README.md if needed

## Documentation

### README.md Updates

When adding features, update:
- Features list
- Commands reference
- Configuration section
- Screenshots (if applicable)

### Code Comments

```python
# Good: Explains WHY, not WHAT
# Using file_id instead of downloading to save bandwidth
photo_id = photo.file_id

# Bad: Explains obvious WHAT
# Set photo_id to photo.file_id
photo_id = photo.file_id
```

## Pull Request Process

1. **Update documentation**
   - README.md (if feature affects usage)
   - Code comments
   - Docstrings

2. **Test thoroughly**
   - Manual testing
   - Check logs for errors
   - Test edge cases

3. **Create Pull Request**
   - Clear title
   - Description of changes
   - Link related issues
   - List testing performed

4. **Respond to feedback**
   - Address review comments
   - Make requested changes
   - Ask questions if unclear

## PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested locally
- [ ] All existing features still work
- [ ] No errors in logs

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] All functions have docstrings
```

## Getting Help

- **Questions**: Open an issue with "Question:" prefix
- **Bugs**: Open an issue with "Bug:" prefix
- **Feature Requests**: Open an issue with "Feature:" prefix
- **Documentation**: Open an issue with "Docs:" prefix

## Code Review Process

Reviewers will check:
1. Code quality and style
2. Documentation completeness
3. Error handling
4. Logging appropriateness
5. Security considerations
6. Performance impact

## Security

### What NOT to commit:
- `.env` file
- API tokens
- Passwords
- Private keys
- Database files
- User data

### If you accidentally commit sensitive data:
1. Remove it immediately
2. Rotate all exposed credentials
3. Force push to remove from history (if caught early)
4. Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be:
- Listed in README.md (if desired)
- Mentioned in release notes
- Given credit in commit history

## Questions?

Don't hesitate to ask! Open an issue or reach out to maintainers.

---

Thank you for contributing to Road Painting Bot! 🙏
