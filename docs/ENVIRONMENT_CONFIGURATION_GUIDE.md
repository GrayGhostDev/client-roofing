# Environment Configuration & Secrets Management

## ✅ Status: COMPLETE

This document describes the environment configuration system for the iSwitch Roofs CRM application.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Environment Files](#environment-files)
3. [Configuration Validation](#configuration-validation)
4. [Secret Key Generation](#secret-key-generation)
5. [Environment-Specific Settings](#environment-specific-settings)
6. [Deployment Guide](#deployment-guide)
7. [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

The application supports multiple environments with environment-specific configurations:

- **Development** - Local development with debug enabled
- **Staging** - Pre-production testing environment
- **Production** - Live production environment
- **Testing** - Automated testing environment

Each environment has its own configuration class in `app/config_environments.py`.

---

## 📁 Environment Files

### File Structure

```
.
├── .env                          # Main environment file (gitignored)
├── .env.development              # Development-specific settings
├── .env.production.example       # Production template (committed)
├── .env.example                  # General template (committed)
└── backend/
    ├── generate_secrets.py       # Secret key generator
    ├── validate_environment.py   # Environment validator
    └── app/
        └── config_environments.py # Environment-specific configs
```

### Which File to Use

| File | Purpose | Committed to Git? |
|------|---------|-------------------|
| `.env` | Active environment variables | ❌ No (gitignored) |
| `.env.development` | Development defaults | ❌ No (gitignored) |
| `.env.production.example` | Production template | ✅ Yes |
| `.env.example` | General template | ✅ Yes |

---

## ✅ Configuration Validation

### Running the Validator

```bash
# Validate current environment
python backend/validate_environment.py

# Generate .env template
python backend/validate_environment.py --generate-template
```

### Validation Output

The validator checks:
- ✅ All required variables are set
- ✅ Variables have valid formats (URLs, emails, etc.)
- ✅ No placeholder values in required fields
- ⚠️  Recommended variables for production

Example output:
```
================================================================================
Environment Configuration Validation - DEVELOPMENT
================================================================================

✅ All required environment variables are configured!
   (3 optional/recommended variables missing)

================================================================================
```

---

## 🔐 Secret Key Generation

### Generating Secure Keys

```bash
python backend/generate_secrets.py
```

Output:
```
================================================================================
Secure Secret Key Generator
================================================================================

Copy these values to your .env file:

# Flask Secret Key (for session management)
SECRET_KEY=ehiHFkz5zLFbciGtLGbP8HyxE-xYFfQUU2ZI2PwY03BmkGABUszFzmtxdD-dl2dWHw6fGb_jbaSP2l5Q_eKDFg

# JWT Secret Key (for token signing)
JWT_SECRET_KEY=_5Tn5tpkNaOHD5uQNtYXk2g9eBc-L7QdujW30GavPuRrpBGOJiqElpvbND1H1XLiwdQZLTqzBano2DZa2aRumQ

================================================================================
⚠️  SECURITY NOTES:
  1. Never commit these keys to version control
  2. Use different keys for each environment
  3. Rotate keys periodically
  4. Store production keys in a secrets manager
================================================================================
```

### Key Requirements

| Key | Length | Purpose |
|-----|--------|---------|
| `SECRET_KEY` | 64 bytes | Flask session encryption |
| `JWT_SECRET_KEY` | 64 bytes | JWT token signing |

---

## ⚙️ Environment-Specific Settings

### Development Configuration

**File:** `app/config_environments.py` → `DevelopmentConfig`

```python
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"
    CORS_ORIGINS = ["*"]  # Allow all origins
    SESSION_COOKIE_SECURE = False  # Allow HTTP
    SENTRY_TRACES_SAMPLE_RATE = 1.0  # 100% sampling
```

**Features:**
- Debug mode enabled
- SQL query logging
- Relaxed CORS policy
- Detailed error messages
- HTTP sessions allowed

### Staging Configuration

**File:** `app/config_environments.py` → `StagingConfig`

```python
class StagingConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "INFO"
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SENTRY_TRACES_SAMPLE_RATE = 0.5  # 50% sampling
    RATELIMIT_ENABLED = True
```

**Features:**
- Production-like settings
- HTTPS required
- Rate limiting enabled
- Redis caching
- Moderate error sampling

### Production Configuration

**File:** `app/config_environments.py` → `ProductionConfig`

```python
class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_SAMESITE = "Strict"
    SENTRY_TRACES_SAMPLE_RATE = 0.1  # 10% sampling
    RATELIMIT_DEFAULT = "100 per hour"
```

**Features:**
- Debug disabled
- Strict security headers
- Connection pooling
- Rate limiting
- Error sampling (10%)

---

## 🚀 Deployment Guide

### Step 1: Prepare Environment

1. **Generate New Secret Keys**
   ```bash
   python backend/generate_secrets.py
   ```

2. **Copy Production Template**
   ```bash
   cp .env.production.example .env.production
   ```

3. **Fill in Production Values**
   - Database credentials
   - API keys for external services
   - Generated secret keys
   - Domain URLs

### Step 2: Configure Deployment Platform

#### Render.com

1. Go to your service dashboard
2. Navigate to "Environment" tab
3. Add environment variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=<generated-key>
   JWT_SECRET_KEY=<generated-key>
   SUPABASE_URL=<your-supabase-url>
   ...
   ```

#### AWS (using Systems Manager Parameter Store)

```bash
# Store secret
aws ssm put-parameter \
    --name "/iswitch-roofs/production/SECRET_KEY" \
    --value "your-secret-key" \
    --type "SecureString"

# Retrieve secret
aws ssm get-parameter \
    --name "/iswitch-roofs/production/SECRET_KEY" \
    --with-decryption \
    --query "Parameter.Value" \
    --output text
```

#### Docker Environment

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env.production
```

### Step 3: Validate Configuration

```bash
# On deployment server
FLASK_ENV=production python backend/validate_environment.py
```

---

## 🔒 Security Best Practices

### 1. Secret Key Management

✅ **DO:**
- Generate unique keys for each environment
- Use cryptographically secure random keys
- Store production keys in secrets manager
- Rotate keys periodically (quarterly)
- Use different keys for Flask and JWT

❌ **DON'T:**
- Commit secrets to version control
- Reuse development keys in production
- Share secrets via email or chat
- Use predictable or short keys
- Hard-code secrets in application code

### 2. Environment File Security

```bash
# Ensure .env files are gitignored
echo ".env*" >> .gitignore
echo "!.env.example" >> .gitignore
echo "!.env.production.example" >> .gitignore

# Set proper permissions
chmod 600 .env
chmod 600 .env.production
```

### 3. Production Checklist

Before deploying to production:

- [ ] All required variables configured
- [ ] New secret keys generated
- [ ] DEBUG=False
- [ ] HTTPS enforced (SESSION_COOKIE_SECURE=True)
- [ ] CORS origins restricted to your domain
- [ ] Sentry DSN configured for error tracking
- [ ] Database credentials secured
- [ ] API keys from production accounts
- [ ] Rate limiting enabled
- [ ] Secrets stored in secrets manager
- [ ] Environment validation passing

### 4. API Key Security

| Service | Key Type | Security Level |
|---------|----------|----------------|
| Supabase | Service Role Key | 🔴 Critical |
| SendGrid | API Key | 🟡 Important |
| Twilio | Auth Token | 🟡 Important |
| CallRail | API Key | 🟡 Important |
| Pusher | Secret | 🟢 Medium |

---

## 📊 Configuration Overview

### Required Variables

| Variable | Type | Required | Default |
|----------|------|----------|---------|
| `FLASK_ENV` | String | ✅ | development |
| `SECRET_KEY` | Secret | ✅ | None |
| `DEBUG` | Boolean | ✅ | False |
| `SUPABASE_URL` | URL | ✅ | None |
| `SUPABASE_KEY` | Secret | ✅ | None |
| `JWT_SECRET_KEY` | Secret | ✅ | None |
| `PUSHER_APP_ID` | String | ✅ | None |
| `SENDGRID_API_KEY` | Secret | ✅ | None |
| `TWILIO_ACCOUNT_SID` | String | ✅ | None |
| `CALLRAIL_API_KEY` | Secret | ✅ | None |

### Optional Variables

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `REDIS_URL` | URL | redis://localhost:6379/0 | Caching |
| `SENTRY_DSN` | URL | None | Error tracking |
| `CLOUDFLARE_API_TOKEN` | Secret | None | CDN/DNS |
| `GOOGLE_LSA_API_KEY` | Secret | None | Ads integration |

---

## 🔄 Key Rotation

### When to Rotate Keys

- **Quarterly** - Regular scheduled rotation
- **Immediately** - If key compromised
- **Team changes** - When staff with access leaves
- **Security incident** - After any security breach

### Rotation Process

1. **Generate New Keys**
   ```bash
   python backend/generate_secrets.py
   ```

2. **Update Production Secrets**
   - Update in secrets manager
   - Update deployment configuration

3. **Deploy with New Keys**
   ```bash
   # Gradual rollout
   kubectl set env deployment/backend SECRET_KEY=<new-key>
   ```

4. **Verify Application**
   - Check health endpoints
   - Monitor error rates
   - Test authentication flow

5. **Invalidate Old Sessions**
   - Old JWT tokens will be invalid
   - Users will need to re-authenticate

---

## 🆘 Troubleshooting

### Missing Required Variable

**Error:**
```
❌ REQUIRED: SECRET_KEY is not set
```

**Solution:**
```bash
python backend/generate_secrets.py
# Copy SECRET_KEY to .env file
```

### Invalid Format

**Error:**
```
❌ INVALID: SUPABASE_URL must be a valid URL
```

**Solution:**
```bash
# Ensure URL starts with https://
SUPABASE_URL=https://your-project.supabase.co
```

### Placeholder Values

**Error:**
```
❌ INVALID: SENDGRID_API_KEY contains placeholder value
```

**Solution:**
```bash
# Get real API key from SendGrid dashboard
# https://app.sendgrid.com/settings/api_keys
SENDGRID_API_KEY=SG.real_key_here
```

---

## 📚 Additional Resources

- [Environment Configuration Class](../backend/app/config_environments.py)
- [Validation Script](../backend/validate_environment.py)
- [Secret Generator](../backend/generate_secrets.py)
- [Flask Configuration Docs](https://flask.palletsprojects.com/en/latest/config/)
- [12-Factor App Methodology](https://12factor.net/config)

---

## ✅ Completion Checklist

- [x] Environment validation script created
- [x] Secret key generator implemented
- [x] Environment-specific config classes defined
- [x] Development environment configured
- [x] Production template created
- [x] Documentation completed
- [x] Security best practices documented
- [x] Deployment guides provided

**Status:** ✅ **COMPLETE - Ready for Production**

---

**Last Updated:** October 6, 2025
**Maintained By:** Development Team
