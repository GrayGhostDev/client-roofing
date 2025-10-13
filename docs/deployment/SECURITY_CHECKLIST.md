# Production Security Checklist

**Last Updated:** October 13, 2025
**Version:** 2.0.0

## Overview

This checklist ensures all security best practices are followed before deploying to production.

---

## Pre-Deployment Security

### ✅ Secrets Management

- [ ] All secrets stored in environment variables (not in code)
- [ ] `.env` files added to `.gitignore`
- [ ] Secrets generated with secure methods (openssl, etc.)
- [ ] Secret key rotation plan documented
- [ ] Production secrets different from development/staging
- [ ] Secrets stored in secure vault (1Password, AWS Secrets Manager, etc.)
- [ ] Team members have minimum necessary access to secrets

**Generate Secure Secrets:**
```bash
# SECRET_KEY and JWT_SECRET_KEY (32 bytes hex)
openssl rand -hex 32

# REDIS_PASSWORD (24 bytes base64)
openssl rand -base64 32

# Store in password manager immediately
```

### ✅ Database Security

- [ ] PostgreSQL configured with SSL/TLS
- [ ] Database user has minimum necessary privileges
- [ ] Database password is strong (20+ characters)
- [ ] Connection pooling configured
- [ ] Row-level security (RLS) enabled in Supabase
- [ ] Regular automated backups configured
- [ ] Backup encryption enabled
- [ ] Backup restoration tested

**Supabase Security Settings:**
- Enable Row Level Security (RLS) for all tables
- Configure appropriate policies for each user role
- Enable WAL (Write-Ahead Logging) for point-in-time recovery
- Enable database audit logging

### ✅ API Security

- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled (100 requests/minute default)
- [ ] JWT tokens with reasonable expiration (24 hours default)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection enabled
- [ ] API keys rotated regularly
- [ ] Deprecated endpoints removed

**Backend Security Headers:**
```python
# In FastAPI middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

### ✅ Authentication & Authorization

- [ ] JWT-based authentication implemented
- [ ] Password hashing with bcrypt (cost factor 12+)
- [ ] Password minimum requirements (8+ chars, mixed case, numbers, symbols)
- [ ] Failed login attempt throttling
- [ ] Session timeout configured (24 hours default)
- [ ] Multi-factor authentication (MFA) enabled for admins
- [ ] Password reset with secure tokens
- [ ] Account lockout after failed attempts

### ✅ Server Hardening

- [ ] SSH access with key-based authentication only
- [ ] Root login disabled
- [ ] Firewall configured (UFW or cloud firewall)
- [ ] Only necessary ports open (22, 80, 443)
- [ ] Fail2ban installed and configured
- [ ] Automatic security updates enabled
- [ ] Non-root user for application
- [ ] File permissions properly configured (644 for files, 755 for dirs)

**UFW Configuration:**
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

**Fail2ban Configuration:**
```bash
# /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
maxretry = 10
bantime = 600
```

### ✅ SSL/TLS Configuration

- [ ] SSL certificate obtained (Let's Encrypt or commercial)
- [ ] TLS 1.2+ only (TLS 1.0/1.1 disabled)
- [ ] Strong cipher suites configured
- [ ] HSTS header enabled (Strict-Transport-Security)
- [ ] Certificate auto-renewal configured
- [ ] SSL Labs test score A or A+
- [ ] Mixed content warnings resolved

**Nginx SSL Configuration:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### ✅ Docker Security

- [ ] Docker images from trusted sources only
- [ ] Multi-stage builds to minimize image size
- [ ] No secrets in Dockerfile or images
- [ ] Non-root user in containers
- [ ] Read-only file systems where possible
- [ ] Container resource limits configured
- [ ] Regular image updates and vulnerability scanning
- [ ] Docker daemon socket not exposed

**Dockerfile Security Example:**
```dockerfile
FROM python:3.13-slim as production

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ✅ Logging & Monitoring

- [ ] Application logs configured (INFO level minimum)
- [ ] Access logs enabled (Nginx)
- [ ] Error logs enabled and monitored
- [ ] Log rotation configured (max 30 days)
- [ ] Sensitive data not logged (passwords, tokens, etc.)
- [ ] Log aggregation configured (Sentry, Papertrail, etc.)
- [ ] Uptime monitoring enabled (UptimeRobot, Pingdom, etc.)
- [ ] Health check endpoints configured
- [ ] Alerting configured for critical errors

**Uptime Monitoring Endpoints:**
- `https://api.yourdomain.com/health` (Backend)
- `https://crm.yourdomain.com/_stcore/health` (Frontend)

### ✅ Dependency Security

- [ ] All dependencies up to date
- [ ] Known vulnerabilities checked (pip-audit, safety)
- [ ] Dependency version pinning
- [ ] Regular security updates scheduled
- [ ] Unused dependencies removed
- [ ] Private package registry for proprietary code

**Check for Vulnerabilities:**
```bash
# Backend
cd backend
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check

# Frontend
cd ../frontend-streamlit
pip-audit
```

---

## Post-Deployment Security

### ✅ Penetration Testing

- [ ] OWASP Top 10 vulnerabilities tested
- [ ] SQL injection testing
- [ ] XSS testing
- [ ] CSRF testing
- [ ] Authentication bypass testing
- [ ] Authorization testing (privilege escalation)
- [ ] Session management testing
- [ ] Rate limiting testing

**Testing Tools:**
- OWASP ZAP
- Burp Suite
- Nikto
- SQLMap

### ✅ Security Scanning

- [ ] SSL Labs test (https://www.ssllabs.com/ssltest/)
- [ ] Security Headers test (https://securityheaders.com/)
- [ ] Mozilla Observatory test (https://observatory.mozilla.org/)
- [ ] Docker image vulnerability scan
- [ ] Dependency vulnerability scan

**Expected Scores:**
- SSL Labs: A or A+
- Security Headers: A or B+
- Mozilla Observatory: B+ or higher

### ✅ Compliance & Documentation

- [ ] Privacy policy documented
- [ ] Terms of service documented
- [ ] Data retention policy documented
- [ ] Incident response plan documented
- [ ] Security contact information published
- [ ] GDPR compliance reviewed (if applicable)
- [ ] CCPA compliance reviewed (if applicable)
- [ ] PCI DSS compliance reviewed (if handling payments)

---

## Ongoing Security Maintenance

### Daily

- [ ] Review error logs for anomalies
- [ ] Check uptime monitoring status
- [ ] Verify backups completed successfully

### Weekly

- [ ] Review access logs for suspicious activity
- [ ] Check for failed authentication attempts
- [ ] Review rate limiting logs
- [ ] Check SSL certificate expiration (auto-renewal)

### Monthly

- [ ] Update all dependencies
- [ ] Run security vulnerability scan
- [ ] Review and rotate API keys
- [ ] Test backup restoration
- [ ] Review user access permissions
- [ ] Update firewall rules if needed

### Quarterly

- [ ] Full penetration testing
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Review and update security policies
- [ ] Team security training

---

## Security Incident Response Plan

### 1. Detection

- Monitor logs and alerts
- User reports
- Automated security scanning

### 2. Containment

- Isolate affected systems
- Block malicious IPs
- Disable compromised accounts
- Preserve evidence

### 3. Investigation

- Identify attack vector
- Assess damage and data exposure
- Document timeline
- Determine root cause

### 4. Remediation

- Patch vulnerabilities
- Reset compromised credentials
- Update firewall rules
- Deploy fixes

### 5. Recovery

- Restore from clean backups
- Verify system integrity
- Resume normal operations
- Monitor for recurrence

### 6. Post-Incident

- Document lessons learned
- Update security measures
- Notify affected parties (if required)
- Report to authorities (if required)

---

## Security Contacts

### Internal

- **Technical Lead:** [Name/Email]
- **Security Officer:** [Name/Email]
- **DevOps Lead:** [Name/Email]

### External

- **Hosting Provider Support:** [Contact Info]
- **Supabase Support:** support@supabase.io
- **Pusher Support:** support@pusher.com
- **SSL Certificate Authority:** [Contact Info]

---

## Security Resources

### Documentation

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [PostgreSQL Security Guide](https://www.postgresql.org/docs/current/security.html)

### Tools

- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [OWASP ZAP](https://www.zaproxy.org/)
- [Burp Suite](https://portswigger.net/burp)

### Training

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Web Security Academy](https://portswigger.net/web-security)
- [Cybersecurity & Infrastructure Security Agency (CISA)](https://www.cisa.gov/)

---

## Checklist Summary

**Total Items:** 100+
**Completion Target:** 95%+

### Critical (Must Complete)

- Secrets management (7 items)
- Database security (8 items)
- API security (9 items)
- Server hardening (8 items)
- SSL/TLS configuration (7 items)

### Important (Should Complete)

- Authentication & authorization (8 items)
- Docker security (8 items)
- Logging & monitoring (9 items)
- Dependency security (6 items)

### Recommended (Nice to Have)

- Penetration testing (8 items)
- Security scanning (5 items)
- Compliance & documentation (8 items)

---

**Security is an ongoing process, not a one-time task. Review this checklist regularly and update as needed.**

**Last Updated:** October 13, 2025
**Next Review:** January 13, 2026
