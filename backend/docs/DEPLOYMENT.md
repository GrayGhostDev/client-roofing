# Deployment Guide - iSwitch Roofs CRM

Complete deployment guide for all environments: development, staging, and production.

## Table of Contents
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
- [Environment Configuration](#environment-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Development (Local)
```bash
# 1. Clone repository
git clone <repository-url>
cd backend

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start services
docker-compose up -d

# 4. Initialize database
python scripts/init_database.py
python scripts/seed_data.py

# 5. Access application
# Backend API: http://localhost:8000
# Frontend Dashboard: http://localhost:8501
# API Docs: http://localhost:8000/docs
```

### Production (Docker)
```bash
# 1. Configure environment
cp .env.example .env.production
# Edit with production settings

# 2. Deploy
./scripts/deploy.sh --mode docker --env production

# 3. Verify health
./scripts/health_check.sh --exit-on-failure
```

---

## Deployment Methods

### 1. Docker Deployment (Recommended)

**Prerequisites:**
- Docker 24.0+
- Docker Compose 2.20+
- 2GB+ RAM
- 10GB+ disk space

**Development Environment:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

**Production Environment:**
```bash
# Build production image
docker build -t iswitch-crm-backend:latest \
  --target production \
  -f Dockerfile .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or run standalone
docker run -d \
  --name iswitch-crm-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e REDIS_URL="redis://..." \
  iswitch-crm-backend:latest
```

**Multi-Container Setup:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: iswitch-crm-backend:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  frontend:
    image: iswitch-crm-frontend:latest
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend

volumes:
  redis-data:
```

### 2. Systemd Deployment (VPS/Bare Metal)

**Prerequisites:**
- Ubuntu 22.04+ or Debian 11+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx 1.24+

**Initial Setup:**
```bash
# 1. Run setup script (as root)
sudo ./scripts/setup.sh --auto

# 2. Configure application
sudo nano /opt/iswitch-crm/backend/.env

# 3. Start service
sudo systemctl start iswitch-crm
sudo systemctl status iswitch-crm

# 4. Enable on boot
sudo systemctl enable iswitch-crm
```

**Service Management:**
```bash
# Start/stop/restart
sudo systemctl start iswitch-crm
sudo systemctl stop iswitch-crm
sudo systemctl restart iswitch-crm

# View logs
sudo journalctl -u iswitch-crm -f

# Check status
sudo systemctl status iswitch-crm
```

**systemd Service File** (`/etc/systemd/system/iswitch-crm.service`):
```ini
[Unit]
Description=iSwitch Roofs CRM Backend API
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=iswitch
WorkingDirectory=/opt/iswitch-crm/backend
Environment="PATH=/opt/iswitch-crm/venv/bin"
EnvironmentFile=/opt/iswitch-crm/backend/.env
ExecStart=/opt/iswitch-crm/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class gevent \
    --timeout 120 \
    --access-logfile /var/log/iswitch-crm/access.log \
    --error-logfile /var/log/iswitch-crm/error.log \
    "run:create_app()"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Kubernetes Deployment

**Prerequisites:**
- Kubernetes 1.28+
- kubectl configured
- Helm 3+ (optional)

**Deployment manifests** (`k8s/`):

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iswitch-crm-backend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: iswitch-crm-backend
  template:
    metadata:
      labels:
        app: iswitch-crm-backend
    spec:
      containers:
      - name: backend
        image: iswitch-crm-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: iswitch-crm-secrets
              key: database-url
        - name: REDIS_URL
          value: redis://redis-service:6379/0
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: iswitch-crm-backend
  namespace: production
spec:
  selector:
    app: iswitch-crm-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iswitch-crm-ingress
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.iswitchroofs.com
    secretName: iswitch-crm-tls
  rules:
  - host: api.iswitchroofs.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: iswitch-crm-backend
            port:
              number: 8000
```

**Deploy to Kubernetes:**
```bash
# Create namespace
kubectl create namespace production

# Create secrets
kubectl create secret generic iswitch-crm-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=supabase-key="..." \
  -n production

# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n production
kubectl logs -f deployment/iswitch-crm-backend -n production

# Scale deployment
kubectl scale deployment/iswitch-crm-backend --replicas=5 -n production
```

### 4. Cloud Platform Deployment

#### AWS (Elastic Beanstalk)
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker iswitch-crm --region us-east-1

# Create environment
eb create production \
  --instance-type t3.medium \
  --database.engine postgres \
  --database.version 15

# Deploy
eb deploy

# Configure environment variables
eb setenv DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..." \
  SUPABASE_URL="https://..."
```

#### Google Cloud Platform (Cloud Run)
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/iswitch-crm-backend

# Deploy to Cloud Run
gcloud run deploy iswitch-crm-backend \
  --image gcr.io/PROJECT_ID/iswitch-crm-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://...",REDIS_URL="redis://..."

# Set up Cloud SQL
gcloud sql instances create iswitch-crm-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

#### Azure (Container Apps)
```bash
# Create resource group
az group create --name iswitch-crm --location eastus

# Create container registry
az acr create --resource-group iswitch-crm --name iswitchcrm --sku Basic

# Build and push
az acr build --registry iswitchcrm --image iswitch-crm-backend:latest .

# Deploy to Container Apps
az containerapp create \
  --name iswitch-crm-backend \
  --resource-group iswitch-crm \
  --image iswitchcrm.azurecr.io/iswitch-crm-backend:latest \
  --environment production \
  --ingress external \
  --target-port 8000
```

---

## Environment Configuration

### Required Environment Variables

**Database:**
```bash
DATABASE_URL="postgresql://user:pass@host:5432/dbname?sslmode=require"
SUPABASE_URL="https://xxx.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Redis:**
```bash
REDIS_URL="redis://host:6379/0"
REDIS_PASSWORD=""  # Optional
```

**Authentication:**
```bash
JWT_SECRET="your-256-bit-secret-key-here"
JWT_ALGORITHM="HS256"
JWT_EXPIRATION_HOURS=24
```

**Real-Time:**
```bash
PUSHER_APP_ID="123456"
PUSHER_KEY="abcdef123456"
PUSHER_SECRET="secret123"
PUSHER_CLUSTER="us2"
```

**Server:**
```bash
API_HOST="0.0.0.0"
API_PORT=8000
DEBUG=false  # Set to false in production!
ENVIRONMENT="production"  # development, staging, production
```

---

## SSL/TLS Setup

### Let's Encrypt with Certbot

**Install Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

**Obtain Certificate:**
```bash
sudo certbot --nginx -d api.iswitchroofs.com
```

**Auto-renewal:**
```bash
# Test renewal
sudo certbot renew --dry-run

# Cron job (already configured by certbot)
sudo crontab -l | grep certbot
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### Custom SSL Certificate

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.iswitchroofs.com;

    ssl_certificate /etc/ssl/certs/iswitchroofs.crt;
    ssl_certificate_key /etc/ssl/private/iswitchroofs.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Monitoring & Logging

### Application Logs

**Docker:**
```bash
docker logs -f iswitch-crm-backend
docker logs --tail 100 iswitch-crm-backend
```

**systemd:**
```bash
journalctl -u iswitch-crm -f
journalctl -u iswitch-crm --since "1 hour ago"
```

**Log Files:**
```bash
tail -f /var/log/iswitch-crm/access.log
tail -f /var/log/iswitch-crm/error.log
```

### Health Checks

**Manual Check:**
```bash
./scripts/health_check.sh --component all --verbose
```

**Continuous Monitoring:**
```bash
# Start monitoring (checks every 60 seconds)
./scripts/monitoring.sh --interval 60 --export /var/log/metrics.csv

# With alerts
./scripts/monitoring.sh \
  --interval 30 \
  --alert-email admin@iswitchroofs.com \
  --slack-webhook https://hooks.slack.com/services/...
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
psql "$DATABASE_URL"

# Check firewall
sudo ufw status
sudo ufw allow from YOUR_IP to any port 5432

# Verify PostgreSQL is running
sudo systemctl status postgresql
```

### Redis Connection Issues
```bash
# Test connection
redis-cli -h HOST -p 6379 ping

# Check Redis status
sudo systemctl status redis

# View Redis logs
sudo journalctl -u redis -f
```

### Application Won't Start
```bash
# Check dependencies
pip list | grep -E "flask|sqlalchemy|redis"

# Verify environment variables
env | grep -E "DATABASE|REDIS|SUPABASE"

# Check port availability
sudo lsof -i :8000

# View startup logs
docker logs iswitch-crm-backend 2>&1 | less
```

### High Memory Usage
```bash
# Check memory
free -h
docker stats

# Restart services
docker-compose restart backend

# Or systemd
sudo systemctl restart iswitch-crm
```

For more troubleshooting scenarios, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
