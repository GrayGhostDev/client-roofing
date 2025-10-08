# 🚀 Quick Reference: Environment Configuration

**For:** Developers, DevOps, System Administrators  
**Version:** 1.0  
**Last Updated:** October 6, 2025

---

## ⚡ Quick Commands

```bash
# Validate environment
python3 backend/validate_environment.py

# Generate new secrets
python3 backend/generate_secrets.py

# Generate .env template
python3 backend/validate_environment.py --generate-template

# Check environment
echo $FLASK_ENV

# Switch to development
export FLASK_ENV=development

# Switch to production
export FLASK_ENV=production

# Run with specific environment
FLASK_ENV=staging python3 backend/run.py
```

---

## 📁 Environment Files

| File | Purpose | Git? |
|------|---------|------|
| `.env` | Active environment | ❌ No |
| `.env.development` | Development config | ❌ No |
| `.env.production.example` | Production template | ✅ Yes |
| `.env.example` | General template | ✅ Yes |

---

## 🔐 Generate Secrets

```bash
$ python3 backend/generate_secrets.py

# Output:
SECRET_KEY=<64-char-url-safe-token>
JWT_SECRET_KEY=<64-char-url-safe-token>

# Copy to .env file
```

---

## ✅ Validation

### Run Validator
```bash
python3 backend/validate_environment.py
```

### Expected Output (Success)
```
================================================================================
Environment Configuration Validation - DEVELOPMENT
================================================================================

✅ All required environment variables are configured!

================================================================================
```

### Expected Output (Errors)
```
🚨 ERRORS (Must be fixed):
--------------------------------------------------------------------------------
❌ REQUIRED: SECRET_KEY is not set
❌ INVALID: SUPABASE_URL must be a valid URL
```

---

## ⚙️ Environment Configurations

### Development
```bash
export FLASK_ENV=development

# Features:
- DEBUG=True
- CORS=* (allow all)
- HTTP sessions allowed
- Full error details
- SQL query logging
```

### Staging
```bash
export FLASK_ENV=staging

# Features:
- DEBUG=False
- HTTPS only
- Rate limiting enabled
- Redis caching
- 50% error sampling
```

### Production
```bash
export FLASK_ENV=production

# Features:
- DEBUG=False
- HTTPS only (strict)
- Security headers
- Connection pooling
- 10% error sampling
- Rate limiting: 100/hour
```

---

## 🔧 Common Issues

### "SECRET_KEY is not set"
```bash
# Generate new key
python3 backend/generate_secrets.py

# Add to .env
SECRET_KEY=<generated-key>
```

### "DATABASE_URL must be a valid URL"
```bash
# Correct format:
DATABASE_URL=postgresql://postgres:password@host:5432/database

# Not:
DATABASE_URL=postgres://...  # Wrong scheme
```

### "SUPABASE_URL must be a valid URL"
```bash
# Correct format:
SUPABASE_URL=https://your-project.supabase.co

# Must start with https://
```

---

## 📝 Required Variables

### Core (3)
```bash
FLASK_ENV=development
SECRET_KEY=<64-char-token>
DEBUG=True
```

### Database (4)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SERVICE_KEY=<service-key>
DATABASE_URL=postgresql://...
```

### JWT (3)
```bash
JWT_SECRET_KEY=<64-char-token>
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
```

### External Services (4 core)
```bash
PUSHER_APP_ID=<pusher-app-id>
SENDGRID_API_KEY=<sendgrid-key>
TWILIO_ACCOUNT_SID=<twilio-sid>
CALLRAIL_API_KEY=<callrail-key>
```

---

## 🚀 Deployment

### Render
```bash
# In Render dashboard:
1. Environment tab
2. Add variables:
   FLASK_ENV=production
   SECRET_KEY=<key>
   ...
3. Deploy
```

### Docker
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

### AWS
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
    --name iswitch-roofs/SECRET_KEY \
    --secret-string "<your-key>"

# Retrieve in code
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='iswitch-roofs/SECRET_KEY')
```

---

## 🔒 Security Checklist

Before production:
- [ ] New secrets generated (not dev keys)
- [ ] DEBUG=False
- [ ] HTTPS enabled
- [ ] CORS restricted to domain
- [ ] Secrets in secrets manager
- [ ] Validation passing
- [ ] .env files gitignored

---

## 📚 Documentation

- **Full Guide:** `docs/ENVIRONMENT_CONFIGURATION_GUIDE.md`
- **Validator:** `backend/validate_environment.py`
- **Generator:** `backend/generate_secrets.py`
- **Configs:** `backend/app/config_environments.py`

---

## 🆘 Emergency Contacts

### Key Rotation
```bash
# 1. Generate new keys
python3 backend/generate_secrets.py

# 2. Update secrets manager
# 3. Deploy with new keys
# 4. Invalidate old sessions
```

### Validation Failing
```bash
# 1. Check error messages
python3 backend/validate_environment.py

# 2. Fix one error at a time
# 3. Re-validate
# 4. Repeat until passing
```

---

**Quick Reference Card v1.0**  
**Status:** Production Ready ✅
