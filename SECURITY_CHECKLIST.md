# 🔐 Security Checklist for Production

## Before Deployment:

### 1. Environment Variables
- [ ] Change JWT_SECRET_KEY to strong random string
- [ ] Set DEBUG=False
- [ ] Set ENVIRONMENT=production
- [ ] Use strong database passwords
- [ ] Store secrets in Railway/platform secret manager

### 2. Database Security
- [ ] LMS DB user is READ-ONLY
- [ ] Separate user for chatbot database
- [ ] Enable SSL for database connections
- [ ] Restrict database access by IP

### 3. API Security
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] JWT tokens expire in 24h
- [ ] Input validation on all endpoints

### 4. Infrastructure
- [ ] HTTPS enabled
- [ ] Firewall configured
- [ ] Only necessary ports open
- [ ] Monitoring enabled

### 5. Data Privacy
- [ ] No sensitive data in logs
- [ ] PII data encrypted
- [ ] Comply with data protection laws
- [ ] Regular backups

### 6. Code Security
- [ ] No hardcoded credentials
- [ ] Dependencies up to date
- [ ] No test files in production
- [ ] Error messages don't leak info

## Generate Secure JWT Secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Test Security:
```bash
# 1. Check for exposed secrets
git log --all -- '*.env'

# 2. Scan dependencies
pip install safety
safety check

# 3. Check for hardcoded secrets
grep -r "sk-" app/ --exclude-dir=venv
```
