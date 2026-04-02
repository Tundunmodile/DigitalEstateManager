# Deployment Guide

## Overview

This guide covers deploying the Apex Residences Chatbot in various environments: development, staging, and production.

---

## Development Environment

### Local Setup

**1. Clone Repository**
```bash
git clone https://github.com/yourusername/DigitalEstateManager.git
cd DigitalEstateManager
```

**2. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Environment**
```bash
# Create .env file in project root
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
OPENAI_API_KEY=sk-...  # Optional
EOF
```

**5. Run Application**
```bash
# Web interface
python app.py --web --port 5000

# Or CLI
python app.py --cli

# Or interactive menu
python app.py
```

**Access**: http://localhost:5000

---

## Staging Environment

### Docker Container Setup

**1. Create Dockerfile**
```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["python", "app.py", "--web", "--port", "5000"]
```

**2. Build Docker Image**
```bash
docker build -t apex-residences-chatbot:latest .
docker tag apex-residences-chatbot:latest apex-residences-chatbot:1.0.0
```

**3. Run Container Locally**
```bash
docker run -p 5000:5000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e TAVILY_API_KEY=tvly-... \
  -e OPENAI_API_KEY=sk-... \
  -d \
  --name apex-chatbot \
  apex-residences-chatbot:latest
```

**4. Verify Container**
```bash
# Check logs
docker logs apex-chatbot

# Check health
curl http://localhost:5000/api/health

# Access web interface
open http://localhost:5000
```

### Docker Compose Setup

**1. Create docker-compose.yml**
```yaml
version: '3.8'

services:
  chatbot:
    image: apex-residences-chatbot:latest
    container_name: apex-chatbot
    ports:
      - "5000:5000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      TAVILY_API_KEY: ${TAVILY_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      FLASK_ENV: development
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Optional: Database for persistence
  postgres:
    image: postgres:15-alpine
    container_name: apex-db
    environment:
      POSTGRES_DB: apex_chatbot
      POSTGRES_USER: apex_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**2. Deploy with Docker Compose**
```bash
# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
OPENAI_API_KEY=sk-...
DB_PASSWORD=your_secure_password
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f chatbot

# Stop services
docker-compose down
```

---

## Production Environment

### AWS EC2 Deployment

**1. Launch EC2 Instance**
```bash
# Recommended: Ubuntu 22.04 LTS, t3.medium or larger
# Open security group ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

**2. Connect via SSH**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

**3. Install Dependencies**
```bash
sudo apt-get update
sudo apt-get install -y \
  python3.10 \
  python3.10-venv \
  python3-pip \
  git \
  curl \
  nginx \
  certbot \
  python3-certbot-nginx \
  supervisor
```

**4. Clone and Setup Application**
```bash
cd /opt
sudo git clone https://github.com/yourusername/DigitalEstateManager.git apex-chatbot
cd apex-chatbot

sudo python3.10 -m venv venv
sudo source venv/bin/activate
sudo pip install -r requirements.txt
```

**5. Configure Environment**
```bash
sudo cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
OPENAI_API_KEY=sk-...
FLASK_ENV=production
EOF

sudo chmod 600 .env
```

**6. Setup Systemd Service**
```bash
sudo cat > /etc/systemd/system/apex-chatbot.service << EOF
[Unit]
Description=Apex Residences Chatbot
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/apex-chatbot
Environment="PATH=/opt/apex-chatbot/venv/bin"
ExecStart=/opt/apex-chatbot/venv/bin/python app.py --web --port 5000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable apex-chatbot
sudo systemctl start apex-chatbot
```

**7. Setup Nginx Reverse Proxy**
```bash
sudo cat > /etc/nginx/sites-available/apex-chatbot << 'EOF'
upstream apex_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;
    gzip_min_length 1000;

    location / {
        proxy_pass http://apex_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /opt/apex-chatbot/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/apex-chatbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

**8. Setup SSL Certificate (Let's Encrypt)**
```bash
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com --agree-tos -m your-email@example.com
```

**9. Monitor Application**
```bash
# Check service status
sudo systemctl status apex-chatbot

# View logs
sudo journalctl -u apex-chatbot -f

# Check API health
curl https://your-domain.com/api/health
```

### Kubernetes Deployment

**1. Create Kubernetes Manifests**

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apex-chatbot
  labels:
    app: apex-chatbot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apex-chatbot
  template:
    metadata:
      labels:
        app: apex-chatbot
    spec:
      containers:
      - name: apex-chatbot
        image: apex-residences-chatbot:1.0.0
        ports:
        - containerPort: 5000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: apex-secrets
              key: anthropic-key
        - name: TAVILY_API_KEY
          valueFrom:
            secretKeyRef:
              name: apex-secrets
              key: tavily-key
        - name: FLASK_ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: apex-chatbot-service
spec:
  selector:
    app: apex-chatbot
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
```

**2. Deploy to Kubernetes**
```bash
# Create secrets
kubectl create secret generic apex-secrets \
  --from-literal=anthropic-key=sk-ant-... \
  --from-literal=tavily-key=tvly-...

# Apply manifests
kubectl apply -f deployment.yaml

# Check deployment
kubectl get deployments
kubectl get pods
kubectl logs -f deployment/apex-chatbot
```

### Heroku Deployment

**1. Create Procfile**
```
web: python app.py --web --port $PORT
```

**2. Create runtime.txt**
```
python-3.10.0
```

**3. Deploy**
```bash
heroku login
heroku create apex-residences-chatbot
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku config:set TAVILY_API_KEY=tvly-...
git push heroku main
```

**4. Monitor**
```bash
heroku logs --tail
heroku ps
```

---

## Environment Configuration

### Environment Variables

**Required:**
- `ANTHROPIC_API_KEY` - Claude API key from Anthropic

**Optional:**
- `TAVILY_API_KEY` - Web search API key
- `OPENAI_API_KEY` - Embeddings API key
- `FLASK_ENV` - Environment: development, staging, production
- `DATABASE_URL` - Database connection string
- `PORT` - Server port (default: 5000)

### Configuration Management

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///apex_chatbot.db")
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", "5"))
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

---

## Database Setup

### SQLite (Default)
```bash
# No setup needed, creates automatically
sqlite3 apex_chatbot.db
```

### PostgreSQL (Production)

**1. Install PostgreSQL**
```bash
sudo apt-get install -y postgresql postgresql-contrib
```

**2. Create Database**
```bash
sudo -u postgres psql << EOF
CREATE DATABASE apex_chatbot;
CREATE USER apex_user WITH PASSWORD 'secure_password';
ALTER ROLE apex_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE apex_chatbot TO apex_user;
EOF
```

**3. Update Configuration**
```bash
# In .env
DATABASE_URL=postgresql://apex_user:secure_password@localhost:5432/apex_chatbot
```

---

## Performance Tuning

### Database Indexing
```sql
-- Improve query performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_query_analytics_conversation_id ON query_analytics(conversation_id);
CREATE INDEX idx_query_analytics_intent ON query_analytics(intent);
```

### Caching
```python
# Add Redis caching for RAG results
from redis import Redis
cache = Redis(host='localhost', port=6379, db=0)

# Cache RAG queries for 1 hour
cache.setex(f"rag:{query_hash}", 3600, json.dumps(results))
```

### Load Balancing
```nginx
upstream apex_backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
    least_conn;
}
```

### Monitoring & Logging
```bash
# Setup centralized logging
# ELK Stack (Elasticsearch, Logstash, Kibana)
# OR CloudWatch (AWS)
# OR Datadog
```

---

## Security Considerations

### 1. API Key Management
```bash
# Use environment variables, never hardcode
# Use AWS Secrets Manager or HashiCorp Vault for production
# Rotate keys regularly (quarterly)
```

### 2. Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route("/api/chat", methods=["POST"])
@limiter.limit("10 per minute")
def chat():
    pass
```

### 3. CORS Configuration
```python
# Production: Limit CORS to specific domains
from flask_cors import CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-domain.com"],
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 4. SSL/TLS
```bash
# Always use HTTPS in production
# Use Let's Encrypt (free SSL)
certbot certonly --nginx -d your-domain.com
```

### 5. Backup Strategy
```bash
# Daily database backups
0 2 * * * pg_dump apex_chatbot > /backups/apex_$(date +\%Y\%m\%d).sql

# Store in S3 or similar
aws s3 cp /backups/apex_*.sql s3://your-backup-bucket/
```

---

## Monitoring & Logging

### Application Monitoring
```bash
# Check application health every 5 minutes
*/5 * * * * curl -f http://localhost:5000/api/health || alert

# Monitor disk space
df -h / | tail -1 | awk '{if ($5 > 80) print "Disk warning: " $5}'

# Monitor memory
free -h
```

### Structured Logging
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Alerting
```bash
# Setup email alerts for errors
# Using Sentry, DataDog, or PagerDuty
```

---

## Rollback Procedure

### Version Rollback
```bash
# Keep last 3 versions
docker image ls | grep apex | head -4

# Rollback to previous version
docker stop apex-chatbot
docker run -d \
  -p 5000:5000 \
  --name apex-chatbot \
  apex-residences-chatbot:1.0.0  # Previous version
```

### Database Rollback
```bash
# Restore from backup
pg_restore -d apex_chatbot /backups/apex_20260402.sql
```

---

## Maintenance & Updates

### Regular Maintenance
- **Weekly**: Check logs for errors, verify backups
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Full system audit, key rotation

### Dependency Updates
```bash
# Check for updates
pip list --outdated

# Update safely
pip install --upgrade package_name
python -m pytest  # Run tests

# Commit and deploy
git add requirements.txt
git commit -m "chore: update dependencies"
git push origin main
```

### Database Maintenance
```bash
# PostgreSQL optimization
VACUUM ANALYZE;
REINDEX DATABASE apex_chatbot;
```

---

## Troubleshooting Deployment

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common deployment issues and solutions.

