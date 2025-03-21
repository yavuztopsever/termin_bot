# Munich Termin Automator - Deployment Guide

## 1. Prerequisites

### 1.1 System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space
- Linux/macOS/Windows with WSL2

### 1.2 Required Accounts & Tokens
- Telegram Bot Token
- FriendlyCaptcha account and tokens
- Docker Hub account (optional for private registry)

### 1.3 Network Requirements
- Outbound access to:
  - api.telegram.org
  - stadt.muenchen.de
  - friendlycaptcha.com
  - Docker Hub

## 2. Local Development Setup

### 2.1 Environment Setup
```bash
# Clone repository
git clone https://github.com/yourusername/termin_bot.git
cd termin_bot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configurations
```

### 2.2 Local Development
```bash
# Start dependencies
docker-compose up -d redis

# Run the bot
python src/main.py

# Run tests
pytest tests/
```

## 3. Production Deployment

### 3.1 Docker Deployment

#### Single Host Deployment
```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Check service status
docker-compose ps

# Stop services
docker-compose down
```

#### Scaling Workers
```bash
# Scale worker containers
docker-compose up -d --scale celery_worker=3
```

### 3.2 Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster
- kubectl configured
- helm installed

#### Deployment Steps
```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami

# Install Redis
helm install redis bitnami/redis -f k8s/redis-values.yaml

# Deploy application
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 4. Configuration

### 4.1 Environment Variables
```bash
# Telegram Configuration
TELEGRAM_TOKEN=your_bot_token

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Captcha Configuration
CAPTCHA_SITE_KEY=your_site_key
CAPTCHA_SECRET_KEY=your_secret_key
CAPTCHA_TIMEOUT=30
CAPTCHA_TOKEN_LIFETIME=300
CAPTCHA_REFRESH_THRESHOLD=60

# Rate Limiting Configuration
RATE_LIMIT_TOKENS_PER_SECOND=10.0
RATE_LIMIT_BUCKET_CAPACITY=100.0
RATE_LIMIT_PATTERN_WINDOW_SIZE=60
RATE_LIMIT_MIN_INTERVAL_VARIANCE=0.1
RATE_LIMIT_MIN_REQUESTS_FOR_CHECK=5
RATE_LIMIT_THRESHOLD=0.8

# Anti-Bot Configuration
ANTI_BOT_MIN_REQUEST_INTERVAL=0.5
ANTI_BOT_MAX_REQUEST_INTERVAL=3.0
ANTI_BOT_PATTERN_WINDOW_SIZE=60
ANTI_BOT_VARIANCE_THRESHOLD=0.1
ANTI_BOT_MAX_REQUESTS_PER_SECOND=2.0
ANTI_BOT_MIN_REQUESTS_FOR_CHECK=5
ANTI_BOT_DETECTION_THRESHOLD=0.8

# Application Settings
LOG_LEVEL=INFO
CHECK_INTERVAL=15
RETRY_DELAY=2
MAX_RETRIES=3
NUM_WORKERS=3

# Monitoring
METRICS_ENABLED=true
MONITORING_PORT=8000
```

### 4.2 Scaling Configuration
```yaml
# docker-compose.yml worker configuration
celery_worker:
  deploy:
    resources:
      limits:
        cpus: '0.50'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 256M
```

## 5. Monitoring Setup

### 5.1 Prometheus & Grafana
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3000
# Default credentials: admin/admin
```

### 5.2 Logging
```bash
# View application logs
docker-compose logs -f bot

# View worker logs
docker-compose logs -f celery_worker

# View monitoring logs
docker-compose logs -f prometheus grafana

# View captcha service logs
docker-compose logs -f captcha_service

# View pattern analysis logs
docker-compose logs -f pattern_analyzer
```

## 6. Backup & Recovery

### 6.1 Database Backup
```bash
# Backup SQLite database
docker-compose exec bot sqlite3 /app/data/termin_bot.db ".backup '/backup/termin_bot_$(date +%Y%m%d).db'"

# Copy backup files locally
docker cp $(docker-compose ps -q bot):/backup ./backup
```

### 6.2 Recovery
```bash
# Restore SQLite database
docker-compose exec bot sqlite3 /app/data/termin_bot.db ".restore '/backup/termin_bot_20240320.db'"
```

## 7. Security Considerations

### 7.1 Production Security Checklist
- [ ] Use secrets management (e.g., Vault, K8s secrets)
- [ ] Configure Redis password
- [ ] Set up SSL/TLS
- [ ] Configure network policies
- [ ] Regular security updates
- [ ] Implement monitoring alerts
- [ ] Secure captcha token storage
- [ ] Implement rate limiting
- [ ] Configure bot detection
- [ ] Set up audit logging

### 7.2 Network Security
```yaml
# docker-compose.yml network configuration
networks:
  frontend:
    driver: overlay
    internal: false
  backend:
    driver: overlay
    internal: true
```

### 7.3 Captcha Security
```yaml
# docker-compose.yml captcha service configuration
captcha_service:
  environment:
    - CAPTCHA_SITE_KEY=${CAPTCHA_SITE_KEY}
    - CAPTCHA_SECRET_KEY=${CAPTCHA_SECRET_KEY}
    - CAPTCHA_TIMEOUT=${CAPTCHA_TIMEOUT}
    - CAPTCHA_TOKEN_LIFETIME=${CAPTCHA_TOKEN_LIFETIME}
    - CAPTCHA_REFRESH_THRESHOLD=${CAPTCHA_REFRESH_THRESHOLD}
  volumes:
    - ./data/captcha:/app/data
  networks:
    - backend
```

### 7.4 Pattern Analysis Security
```yaml
# docker-compose.yml pattern analyzer configuration
pattern_analyzer:
  environment:
    - PATTERN_WINDOW_SIZE=${ANTI_BOT_PATTERN_WINDOW_SIZE}
    - MIN_REQUESTS_FOR_CHECK=${ANTI_BOT_MIN_REQUESTS_FOR_CHECK}
    - DETECTION_THRESHOLD=${ANTI_BOT_DETECTION_THRESHOLD}
  volumes:
    - ./data/patterns:/app/data
  networks:
    - backend
```

## 8. Troubleshooting

### 8.1 Common Issues

#### Connection Issues
```bash
# Check network connectivity
docker-compose exec bot ping redis

# Check Redis connection
docker-compose exec bot python -c "import redis; redis.Redis(host='redis').ping()"

# Check captcha service
docker-compose exec bot curl -X POST http://captcha_service:8000/health

# Check pattern analyzer
docker-compose exec bot curl -X GET http://pattern_analyzer:8000/health
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check application metrics
curl http://localhost:8000/metrics

# Check captcha metrics
curl http://localhost:8000/metrics/captcha

# Check pattern analysis metrics
curl http://localhost:8000/metrics/patterns

# Profile application
docker-compose exec bot python -m cProfile -o output.prof src/main.py
```

### 8.2 Log Analysis
```bash
# Search for errors
docker-compose logs | grep -i error

# Check rate limiting
docker-compose logs | grep -i "rate limit"

# Check captcha issues
docker-compose logs | grep -i "captcha"

# Check pattern analysis
docker-compose logs | grep -i "pattern"

# Monitor API responses
docker-compose logs | grep -i "api response"
```

### 8.3 Captcha Troubleshooting
```bash
# Check captcha token validity
docker-compose exec bot python -c "from src.captcha.captcha_service import CaptchaService; print(CaptchaService().get_valid_token())"

# Check captcha rate limits
docker-compose exec redis redis-cli --eval "return redis.call('get', 'rate_limit:captcha')"

# View captcha service logs
docker-compose logs -f captcha_service
```

### 8.4 Pattern Analysis Troubleshooting
```bash
# Check pattern analysis status
docker-compose exec bot python -c "from src.patterns.pattern_analyzer import PatternAnalyzer; print(PatternAnalyzer().get_status())"

# View pattern analysis metrics
docker-compose exec bot curl http://localhost:8000/metrics/patterns

# Check pattern analysis logs
docker-compose logs -f pattern_analyzer
```

## 9. Maintenance

### 9.1 Regular Maintenance Tasks
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose pull

# Cleanup old containers
docker system prune

# Backup database
./scripts/backup_db.sh
```

### 9.2 Monitoring Maintenance
```bash
# Check disk usage
docker system df

# Check log sizes
du -h ./logs/

# Rotate logs
./scripts/rotate_logs.sh
```

## 10. Scaling Guidelines

### 10.1 Vertical Scaling
- Increase container resources
- Upgrade database tier
- Optimize application settings

### 10.2 Horizontal Scaling
- Add worker nodes
- Implement load balancing
- Configure database replication
- Use Redis cluster

## 11. Version Control

### 11.1 Release Process
```bash
# Create release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Deploy specific version
docker-compose pull
docker-compose up -d
```

### 11.2 Rollback Process
```bash
# Rollback to previous version
git checkout v0.9.0
docker-compose up -d --build

# Rollback database
./scripts/rollback_db.sh v0.9.0
``` 