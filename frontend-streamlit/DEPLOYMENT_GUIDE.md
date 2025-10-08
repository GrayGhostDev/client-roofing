# Streamlit Analytics Dashboard - Deployment Guide

## Overview

This guide covers deployment options for the iSwitch Roofs CRM Analytics Dashboard built with Streamlit.

**Dashboard Features:**
- 6 specialized analytics pages
- Real-time data visualization
- Export functionality (CSV/Excel)
- Responsive design
- API integration ready

---

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.11 or higher
- 2 GB RAM
- 500 MB disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

**Recommended:**
- Python 3.13
- 4 GB RAM
- 1 GB disk space
- Dedicated server or cloud hosting

### Dependencies

All dependencies are listed in `requirements.txt`:
- streamlit==1.40.2
- pandas==2.2.3
- numpy==2.2.1
- plotly==5.24.1
- openpyxl==3.1.5
- requests==2.32.3
- Plus additional Streamlit components

---

## Deployment Option 1: Local Development

### Quick Start

```bash
# Navigate to dashboard directory
cd frontend-streamlit

# Install dependencies
pip install -r requirements.txt

# Start dashboard
streamlit run app.py
```

**Access:** http://localhost:8501

### Configuration

Create `.streamlit/config.toml` for custom settings:

```toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### Advantages
- ✅ Quick setup
- ✅ Full control
- ✅ No external dependencies
- ✅ Great for testing

### Disadvantages
- ❌ Requires local machine running
- ❌ Not accessible remotely
- ❌ No automatic scaling

---

## Deployment Option 2: Streamlit Cloud (Recommended for Production)

### Overview

Streamlit Cloud is the official hosting platform for Streamlit apps.

**Features:**
- Free tier available
- One-click deployment
- Automatic updates from Git
- Built-in authentication
- SSL certificates included
- CDN for global access

### Step-by-Step Deployment

1. **Prepare Repository**
   ```bash
   # Ensure code is in Git repository
   cd frontend-streamlit
   git init
   git add .
   git commit -m "Initial dashboard deployment"
   
   # Push to GitHub
   git remote add origin https://github.com/yourusername/iswitch-roofs-dashboard.git
   git push -u origin main
   ```

2. **Create Streamlit Cloud Account**
   - Go to https://streamlit.io/cloud
   - Sign up with GitHub account
   - Authorize Streamlit to access repositories

3. **Deploy App**
   - Click "New app"
   - Select repository: `yourusername/iswitch-roofs-dashboard`
   - Branch: `main`
   - Main file path: `frontend-streamlit/app.py`
   - Click "Deploy"

4. **Configure Secrets**
   
   In Streamlit Cloud dashboard, add secrets:
   ```toml
   # .streamlit/secrets.toml
   [api]
   base_url = "https://your-backend-api.com/api"
   
   [authentication]
   jwt_secret = "your-secret-key-here"
   ```

5. **Custom Domain (Optional)**
   - Go to app settings
   - Add custom domain: `dashboard.iswitchroofs.com`
   - Update DNS CNAME record

### Deployment URL

Your app will be available at:
- **Default:** https://yourusername-iswitch-roofs-dashboard-main.streamlit.app
- **Custom:** https://dashboard.iswitchroofs.com (if configured)

### Advantages
- ✅ Free tier available
- ✅ Zero infrastructure management
- ✅ Automatic deployments from Git
- ✅ Built-in SSL/HTTPS
- ✅ Global CDN
- ✅ Easy scaling

### Disadvantages
- ❌ Requires public GitHub repository (for free tier)
- ❌ Limited customization
- ❌ Shared resources on free tier

---

## Deployment Option 3: Docker Container

### Dockerfile

Create `Dockerfile` in `frontend-streamlit/`:

```dockerfile
# Use official Python runtime as base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run dashboard
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  dashboard:
    build:
      context: ./frontend-streamlit
      dockerfile: Dockerfile
    container_name: iswitch-dashboard
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://backend:5000/api
      - STREAMLIT_THEME_PRIMARY_COLOR=#1E88E5
    volumes:
      - ./frontend-streamlit:/app
      - dashboard-cache:/root/.streamlit
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - iswitch-network

  backend:
    build: ./backend
    container_name: iswitch-backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/iswitch
    depends_on:
      - db
    networks:
      - iswitch-network

  db:
    image: postgres:15-alpine
    container_name: iswitch-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=iswitch
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - iswitch-network

volumes:
  dashboard-cache:
  postgres-data:

networks:
  iswitch-network:
    driver: bridge
```

### Build and Run

```bash
# Build image
docker build -t iswitch-dashboard ./frontend-streamlit

# Run container
docker run -d \
  --name iswitch-dashboard \
  -p 8501:8501 \
  -e API_BASE_URL=http://backend:5000/api \
  iswitch-dashboard

# Or use Docker Compose
docker-compose up -d
```

### Advantages
- ✅ Consistent environment
- ✅ Easy to scale
- ✅ Portable across platforms
- ✅ Integrated with backend

### Disadvantages
- ❌ Requires Docker knowledge
- ❌ More complex setup
- ❌ Resource overhead

---

## Deployment Option 4: Traditional Server (Linux)

### Server Setup (Ubuntu 22.04 LTS)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.13
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.13 python3.13-venv python3.13-dev

# Install Nginx (reverse proxy)
sudo apt install nginx

# Install Supervisor (process manager)
sudo apt install supervisor
```

### Application Setup

```bash
# Create app directory
sudo mkdir -p /var/www/iswitch-dashboard
cd /var/www/iswitch-dashboard

# Clone repository
git clone https://github.com/yourusername/iswitch-roofs-dashboard.git .

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r frontend-streamlit/requirements.txt
```

### Supervisor Configuration

Create `/etc/supervisor/conf.d/iswitch-dashboard.conf`:

```ini
[program:iswitch-dashboard]
directory=/var/www/iswitch-dashboard/frontend-streamlit
command=/var/www/iswitch-dashboard/venv/bin/streamlit run app.py --server.port=8501 --server.address=localhost
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/iswitch-dashboard/error.log
stdout_logfile=/var/log/iswitch-dashboard/access.log
environment=PATH="/var/www/iswitch-dashboard/venv/bin",API_BASE_URL="http://localhost:5000/api"
```

```bash
# Create log directory
sudo mkdir -p /var/log/iswitch-dashboard
sudo chown www-data:www-data /var/log/iswitch-dashboard

# Start service
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start iswitch-dashboard
```

### Nginx Configuration

Create `/etc/nginx/sites-available/iswitch-dashboard`:

```nginx
server {
    listen 80;
    server_name dashboard.iswitchroofs.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # WebSocket support
    location /_stcore/stream {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/iswitch-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d dashboard.iswitchroofs.com

# Auto-renewal (already configured by Certbot)
sudo certbot renew --dry-run
```

### Advantages
- ✅ Full control over environment
- ✅ Can run on internal network
- ✅ Custom security policies
- ✅ No external dependencies

### Disadvantages
- ❌ Requires server administration
- ❌ Manual scaling
- ❌ Security updates needed

---

## Deployment Option 5: AWS EC2

### Launch EC2 Instance

1. **Choose AMI:** Ubuntu Server 22.04 LTS
2. **Instance Type:** t3.medium (2 vCPU, 4 GB RAM)
3. **Configure Security Group:**
   - SSH (22) - Your IP only
   - HTTP (80) - Anywhere
   - HTTPS (443) - Anywhere
   - Custom (8501) - Anywhere (optional, for direct access)

### Setup Script

```bash
#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.13 python3.13-venv nginx supervisor git

# Clone application
cd /home/ubuntu
git clone https://github.com/yourusername/iswitch-roofs-dashboard.git
cd iswitch-roofs-dashboard/frontend-streamlit

# Setup virtual environment
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Supervisor (see above)
# Configure Nginx (see above)
```

### Auto-scaling (Optional)

Create Launch Template and Auto Scaling Group:
- Min instances: 1
- Max instances: 5
- Target CPU: 70%

### Advantages
- ✅ Scalable infrastructure
- ✅ AWS integrations available
- ✅ Load balancing support
- ✅ Multiple availability zones

### Disadvantages
- ❌ AWS costs (from $20/month)
- ❌ More complex setup
- ❌ Requires AWS knowledge

---

## Deployment Option 6: Heroku

### Procfile

Create `Procfile` in `frontend-streamlit/`:

```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### Heroku Configuration

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create app
heroku create iswitch-roofs-dashboard

# Add Python buildpack
heroku buildpacks:set heroku/python

# Deploy
git subtree push --prefix frontend-streamlit heroku main

# Scale dyno
heroku ps:scale web=1

# View logs
heroku logs --tail
```

### Advantages
- ✅ Simple deployment
- ✅ Git-based workflow
- ✅ Add-ons available (database, cache, etc.)
- ✅ Built-in monitoring

### Disadvantages
- ❌ Costs start at $7/month
- ❌ Limited free tier
- ❌ Less control

---

## Environment Variables

### Required Variables

```bash
# API Configuration
API_BASE_URL=http://localhost:5000/api
API_TIMEOUT=30

# Authentication (if implemented)
JWT_SECRET=your-secret-key-here
AUTH_TOKEN=optional-token

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

# Feature Flags
ENABLE_MOCK_DATA=false  # Set to true for demo mode
ENABLE_API_CACHE=true
CACHE_TTL=300  # 5 minutes

# Logging
LOG_LEVEL=INFO
```

### Setting Environment Variables

**Linux/Mac:**
```bash
export API_BASE_URL=http://api.iswitchroofs.com/api
```

**Windows:**
```cmd
set API_BASE_URL=http://api.iswitchroofs.com/api
```

**Docker:**
```yaml
environment:
  - API_BASE_URL=http://api.iswitchroofs.com/api
```

**Streamlit Cloud:**
Add in `.streamlit/secrets.toml` via web interface

---

## Performance Optimization

### Caching Strategy

The dashboard uses Streamlit's caching decorators:

```python
# API client cached (doesn't re-create on every interaction)
@st.cache_resource
def get_api_client():
    return APIClient(api_base_url, auth_token)

# Data cached for 5 minutes
@st.cache_data(ttl=300)
def cached_api_call(endpoint):
    return api_client.get(endpoint)
```

### Database Connection Pooling

If connecting directly to database:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20
    )
```

### Load Testing

Test with `locust` (load testing tool):

```python
# locustfile.py
from locust import HttpUser, task, between

class DashboardUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def view_overview(self):
        self.client.get("/")
    
    @task
    def view_leads(self):
        self.client.get("/?page=lead_analytics")
```

Run test:
```bash
locust -f locustfile.py --host=http://localhost:8501
```

---

## Monitoring & Logging

### Application Monitoring

**Option 1: Streamlit Native**
```python
import streamlit as st

# Track page views
if 'page_views' not in st.session_state:
    st.session_state.page_views = 0
st.session_state.page_views += 1
```

**Option 2: Google Analytics**
```python
# Add to app.py
import streamlit.components.v1 as components

def add_analytics():
    analytics_code = """
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX');
    </script>
    """
    components.html(analytics_code)
```

**Option 3: Sentry (Error Tracking)**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project",
    traces_sample_rate=1.0
)
```

### Logging Configuration

Create `logging_config.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger('iswitch_dashboard')
    logger.setLevel(logging.INFO)
    
    # File handler
    handler = RotatingFileHandler(
        'dashboard.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

---

## Security Considerations

### Authentication

Implement Streamlit authentication:

```python
import streamlit as st
import hashlib

def check_password():
    """Returns `True` if user has correct password."""
    
    def password_entered():
        """Checks whether password entered by user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and hashlib.sha256(st.session_state["password"].encode()).hexdigest()
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show login
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct
        return True

if check_password():
    # Main app code here
    st.write("Dashboard content")
```

### Secrets Management

In `.streamlit/secrets.toml`:

```toml
[passwords]
admin = "sha256_hash_of_admin_password"
manager = "sha256_hash_of_manager_password"

[api]
base_url = "https://api.iswitchroofs.com"
api_key = "your-api-key-here"
```

### HTTPS/SSL

Always use HTTPS in production:
- Streamlit Cloud: Automatic
- Nginx: Use Let's Encrypt (see above)
- AWS: Use ALB with ACM certificate

### Input Validation

Validate all user inputs:

```python
import re

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_date_range(start, end):
    if start > end:
        st.error("Start date must be before end date")
        return False
    if (end - start).days > 365:
        st.error("Date range cannot exceed 1 year")
        return False
    return True
```

---

## Backup & Recovery

### Database Backups

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/iswitch"

# Backup database
pg_dump -U postgres iswitch > "$BACKUP_DIR/db_$DATE.sql"

# Backup files
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" /var/www/iswitch-dashboard

# Delete old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

### Application State Backup

Save Streamlit session state to database:

```python
import json

def save_session_state():
    state_data = {
        'date_range': st.session_state.get('date_range'),
        'filters': st.session_state.get('filters'),
        'last_page': st.session_state.get('current_page')
    }
    # Save to database
    db.save('user_sessions', user_id, json.dumps(state_data))
```

---

## Maintenance

### Update Strategy

```bash
# 1. Backup current version
cp -r /var/www/iswitch-dashboard /var/www/iswitch-dashboard.backup

# 2. Pull updates
cd /var/www/iswitch-dashboard
git pull origin main

# 3. Update dependencies
source venv/bin/activate
pip install -r frontend-streamlit/requirements.txt --upgrade

# 4. Restart application
sudo supervisorctl restart iswitch-dashboard

# 5. Test
curl http://localhost:8501/_stcore/health

# 6. If issues, rollback
# sudo supervisorctl stop iswitch-dashboard
# rm -rf /var/www/iswitch-dashboard
# mv /var/www/iswitch-dashboard.backup /var/www/iswitch-dashboard
# sudo supervisorctl start iswitch-dashboard
```

### Health Monitoring

Create health check endpoint monitor:

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="http://localhost:8501/_stcore/health"
EMAIL="admin@iswitchroofs.com"

if ! curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "Dashboard health check failed!" | mail -s "Dashboard Alert" $EMAIL
    sudo supervisorctl restart iswitch-dashboard
fi
```

Add to crontab:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/health_check.sh
```

---

## Troubleshooting

### Common Issues

**Issue:** Dashboard won't start
```bash
# Check logs
sudo tail -f /var/log/iswitch-dashboard/error.log

# Check if port is in use
sudo lsof -i :8501

# Check Python version
python3.13 --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue:** WebSocket connection fails
```bash
# Check Nginx WebSocket configuration
sudo nginx -t

# Verify firewall
sudo ufw status
sudo ufw allow 8501/tcp
```

**Issue:** High memory usage
```bash
# Check process memory
ps aux | grep streamlit

# Restart application
sudo supervisorctl restart iswitch-dashboard

# Consider increasing swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Cost Estimation

### Monthly Costs by Option

| Option | Cost | Notes |
|--------|------|-------|
| **Local Development** | $0 | Requires existing machine |
| **Streamlit Cloud** | $0-$250 | Free tier available, $250/month for Pro |
| **AWS EC2 (t3.medium)** | $30-50 | Plus data transfer costs |
| **AWS ECS (Fargate)** | $50-100 | Auto-scaling included |
| **Heroku** | $7-25 | Basic dyno $7, Pro dyno $25 |
| **DigitalOcean Droplet** | $12-24 | Basic $12, Pro $24 |
| **Self-Hosted** | Variable | Server + maintenance costs |

---

## Deployment Checklist

Before deploying to production:

- [ ] All features tested locally
- [ ] Environment variables configured
- [ ] Backend API connected and tested
- [ ] Authentication implemented (if required)
- [ ] HTTPS/SSL certificate obtained
- [ ] Error logging configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Health check endpoint verified
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on dashboard use
- [ ] Rollback plan prepared
- [ ] DNS records configured (if using custom domain)

---

## Recommended Deployment Path

For iSwitch Roofs CRM:

**Phase 1: Development (Current)**
- Run locally on developer machines
- Use mock data for testing
- Iterate on features

**Phase 2: Staging**
- Deploy to Streamlit Cloud (free tier)
- Connect to staging backend API
- Conduct user acceptance testing
- Private URL for team testing

**Phase 3: Production**
- Deploy to AWS EC2 or Streamlit Cloud Pro
- Connect to production backend
- Custom domain: dashboard.iswitchroofs.com
- SSL certificate installed
- Monitoring and alerting active
- Daily backups configured

**Phase 4: Scale**
- Migrate to AWS ECS with auto-scaling
- Implement caching layer (Redis)
- Add CDN for global performance
- Set up multi-region deployment (if needed)

---

## Next Steps

1. **Complete Testing** (See TESTING_GUIDE.md)
2. **Choose Deployment Option** (Recommended: Streamlit Cloud for start)
3. **Configure Backend API Connection**
4. **Deploy to Staging**
5. **User Acceptance Testing**
6. **Deploy to Production**
7. **Monitor and Optimize**

---

**Document Version:** 1.0  
**Last Updated:** 2025-02-09  
**Contact:** Gray Ghost Data Consultants
