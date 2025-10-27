# Road Painting Bot - Docker Configuration

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for database and logs
RUN mkdir -p /app/data /app/exports

# Volume for persistent data
VOLUME ["/app/data", "/app/exports"]

# Set database path to volume
ENV DATABASE_PATH=/app/data/road_painting.db
ENV LOG_FILE=/app/data/bot.log

# Expose port for web dashboard (optional)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/data/road_painting.db') else 1)"

# Run the bot
CMD ["python", "bot.py"]
