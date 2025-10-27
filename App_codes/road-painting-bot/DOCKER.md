# Docker Deployment Guide

This guide explains how to deploy the Road Painting Bot using Docker.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)
- Your Telegram Bot Token

## Quick Start with Docker

### 1. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your bot token
nano .env  # or use any text editor
```

### 2. Build and Run

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f road-painting-bot

# Stop the bot
docker-compose down
```

## Docker Commands

### Building

```bash
# Build the Docker image
docker build -t road-painting-bot .

# Build with docker-compose
docker-compose build
```

### Running

```bash
# Run bot only
docker-compose up -d road-painting-bot

# Run bot and web dashboard
docker-compose up -d

# Run in foreground (see logs)
docker-compose up
```

### Monitoring

```bash
# View logs
docker-compose logs -f

# View bot logs only
docker-compose logs -f road-painting-bot

# View dashboard logs only
docker-compose logs -f web-dashboard

# Check status
docker-compose ps
```

### Stopping

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database!)
docker-compose down -v
```

## Data Persistence

### Volumes

The bot uses two volumes for persistent data:

- `./data` - Database and logs
- `./exports` - CSV exports

These directories are created automatically and persist even if containers are removed.

### Backup

```bash
# Backup database
cp data/road_painting.db data/road_painting.db.backup

# Or create a timestamped backup
cp data/road_painting.db "data/backup_$(date +%Y%m%d_%H%M%S).db"
```

### Restore

```bash
# Stop the bot
docker-compose down

# Restore database
cp data/road_painting.db.backup data/road_painting.db

# Start the bot
docker-compose up -d
```

## Configuration

### Environment Variables

Edit `.env` file before starting:

```env
TELEGRAM_BOT_TOKEN=your_token_here
INSPECTOR_CHAT_IDS=123456789,987654321
DATABASE_PATH=/app/data/road_painting.db
LOG_FILE=/app/data/bot.log
```

### Custom Configuration

To use custom configuration:

1. Edit `docker-compose.yml`
2. Add environment variables or mount config files
3. Rebuild: `docker-compose up -d --build`

## Web Dashboard

### Access

If you started the web dashboard:

```bash
docker-compose up -d web-dashboard
```

Access at: http://localhost:5000

### Custom Port

Edit `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

## Troubleshooting

### Bot won't start

```bash
# Check logs
docker-compose logs road-painting-bot

# Check if container is running
docker-compose ps

# Restart
docker-compose restart road-painting-bot
```

### Database issues

```bash
# Enter container
docker-compose exec road-painting-bot bash

# Check database
ls -la /app/data/
sqlite3 /app/data/road_painting.db "SELECT COUNT(*) FROM submissions;"
```

### Permission issues

```bash
# Fix permissions on host
chmod -R 755 data exports

# Or set ownership
chown -R $(whoami):$(whoami) data exports
```

### Network issues

```bash
# Check if container can reach Telegram
docker-compose exec road-painting-bot ping -c 3 api.telegram.org
```

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml road-bot

# Check services
docker service ls

# Scale if needed
docker service scale road-bot_road-painting-bot=2
```

### Using Kubernetes

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: road-painting-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: road-painting-bot
  template:
    metadata:
      labels:
        app: road-painting-bot
    spec:
      containers:
      - name: bot
        image: road-painting-bot:latest
        env:
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: token
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: bot-data-pvc
```

Deploy:

```bash
kubectl apply -f k8s-deployment.yaml
```

### Security Best Practices

1. **Never commit .env to git**
2. **Use secrets management** for tokens
3. **Run as non-root user** (add to Dockerfile):
   ```dockerfile
   RUN useradd -m -u 1000 botuser
   USER botuser
   ```
4. **Limit resources** (add to docker-compose.yml):
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```

### Health Checks

The container includes a health check. Monitor:

```bash
docker inspect --format='{{.State.Health.Status}}' road-painting-bot
```

### Logging

View and manage logs:

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Export logs
docker-compose logs > bot_logs.txt
```

## Updating

### Update Code

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Update Dependencies

```bash
# Edit requirements.txt
# Then rebuild
docker-compose build --no-cache
docker-compose up -d
```

## Multi-Container Setup

For production, consider splitting services:

```yaml
# Example: Separate database service
services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: road_painting
      POSTGRES_USER: bot
      POSTGRES_PASSWORD: secret
    volumes:
      - db-data:/var/lib/postgresql/data

  bot:
    build: .
    depends_on:
      - database
    environment:
      DATABASE_URL: postgresql://bot:secret@database/road_painting
```

## Monitoring

### With Prometheus

Add to `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### With Grafana

```yaml
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Check container health: `docker-compose ps`
3. Verify environment: `docker-compose config`
4. Review this guide
5. Open an issue on GitHub

---

Happy deploying! 🚀
