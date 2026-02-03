# 🔐 Security Documentation

## Overview

Chatbot API ini menggunakan **public security model** - tidak memerlukan autentikasi, tetapi dilindungi dengan multiple security layers untuk mencegah attacks dan abuse.

---

## Security Features Implemented

### 1. ✅ Input Validation & Sanitization

**Technology**: Custom middleware dengan regex pattern matching

**Protection Against**:
- XSS (Cross-Site Scripting)
- SQL Injection
- Path Traversal
- Code Injection

**Implementation**: `app/middleware/security.py`

**Features**:
```python
# Dangerous patterns yang diblock:
- <script> tags
- javascript: protocol
- Event handlers (onclick, onerror, etc)
- SQL keywords (UNION, SELECT, DROP, etc)
- Path traversal (../, ..\)
```

**Limits**:
- Max message length: 2000 characters
- Max session ID length: 100 characters
- Alphanumeric validation untuk session IDs

**Example**:
```python
# Input: "<script>alert(1)</script>"
# Output: HTTP 400 - "Invalid input detected"
```

---

### 2. ✅ Security Headers

**Technology**: FastAPI Middleware

**Implementation**: `app/middleware/security.py` - `SecurityMiddleware`

**Headers Applied**:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

**Protection Against**:
- MIME type sniffing attacks
- Clickjacking
- XSS attacks
- Man-in-the-middle attacks
- Content injection

---

### 3. ✅ Rate Limiting

**Technology**: Custom rate limiter dengan SQLite storage

**Implementation**: `app/services/rate_limiter.py`

**Limits**:
- **Public users**: 20 requests per day per session
- Session-based tracking
- Automatic reset setiap 24 jam

**Response when exceeded**:
```json
{
  "success": false,
  "error": "Rate limit exceeded. Please try again tomorrow.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "rate_limit": {
    "limit": 20,
    "used": 20,
    "remaining": 0
  }
}
```

---

### 4. ✅ Request Size Limits

**Limits Applied**:
- Message content: 2000 characters
- Session ID: 100 characters
- History query: Max 100 messages

**Protection Against**:
- DoS (Denial of Service) attacks
- Memory exhaustion
- Database overload

---

### 5. ✅ Log Sanitization

**Implementation**: Custom logging dengan data masking

**Features**:
- Only log first 50 characters of messages
- Never log sensitive data (passwords, tokens, API keys)
- Generic error messages to users
- Detailed errors only in server logs

**Example**:
```python
# User sees: "Internal server error"
# Log shows: "Chat error: ValueError: Invalid input format"
```

---

### 6. ✅ CORS Configuration

**Technology**: FastAPI CORSMiddleware

**Configuration**: `.env` file
```
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

**Protection Against**:
- Unauthorized cross-origin requests
- CSRF attacks from malicious sites

---

### 7. ✅ Environment Security

**Technology**: Pydantic Settings + python-dotenv

**Secure Configuration**:
```
DEBUG=False                    # Disable debug mode in production
ENVIRONMENT="production"       # Production environment
JWT_SECRET_KEY="<strong-key>"  # Cryptographically secure random key
```

**API Keys Protection**:
- DeepSeek API key stored in environment variables
- Never committed to git (.gitignore)
- Loaded securely via Pydantic Settings

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Request                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CORS Middleware                           │
│  ✓ Check origin allowed                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Security Middleware                         │
│  ✓ Add security headers                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Input Validation                            │
│  ✓ Sanitize input                                           │
│  ✓ Check dangerous patterns                                 │
│  ✓ Validate length limits                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Rate Limiting                             │
│  ✓ Check request count                                      │
│  ✓ Enforce daily limits                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic                              │
│  ✓ Process chat request                                     │
│  ✓ Generate AI response                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Response + Headers                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Structure

```
app/
├── middleware/
│   └── security.py              # Security middleware & validation
├── api/
│   └── chat_public.py           # Public chat endpoint (no auth)
├── services/
│   └── rate_limiter.py          # Rate limiting service
└── core/
    ├── config.py                # Environment configuration
    └── security.py              # Security utilities (JWT, hashing)
```

---

## Testing Security

### Test XSS Protection
```bash
curl http://localhost:8000/api/message \
  -Method POST \
  -ContentType "application/json" \
  -Body '{"message":"<script>alert(1)</script>"}' \
  -UseBasicParsing

# Expected: HTTP 400 - "Invalid input detected"
```

### Test SQL Injection Protection
```bash
curl http://localhost:8000/api/message \
  -Method POST \
  -ContentType "application/json" \
  -Body '{"message":"test OR 1=1; DROP TABLE users;"}' \
  -UseBasicParsing

# Expected: HTTP 400 - "Invalid input detected"
```

### Test Rate Limiting
```bash
# Send 21 requests
for ($i=1; $i -le 21; $i++) {
  curl http://localhost:8000/api/message `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"message":"test"}' `
    -UseBasicParsing
}

# Expected: First 20 succeed, 21st returns HTTP 429
```

### Test Security Headers
```bash
curl -I http://localhost:8000/health

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000
```

---

## Production Checklist

### Before Deployment:
- [x] Input validation active
- [x] Security headers configured
- [x] Rate limiting enabled
- [x] Request size limits set
- [x] Log sanitization implemented
- [x] CORS properly configured
- [x] Strong JWT secret generated
- [x] DEBUG=False
- [x] ENVIRONMENT=production

### Recommended:
- [ ] Enable HTTPS
- [ ] Use CDN with DDoS protection
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Regular dependency updates
- [ ] Security audit
- [ ] Penetration testing

---

## Security Best Practices

### 1. Keep Dependencies Updated
```bash
pip list --outdated
pip install --upgrade <package>
```

### 2. Scan for Vulnerabilities
```bash
pip install safety
safety check
```

### 3. Monitor Logs
```bash
tail -f logs/app.log
```

### 4. Regular Backups
- Database: `data/databases/ai_chat.db`
- Configuration: `.env`

### 5. Incident Response
- Monitor rate limit violations
- Check for suspicious patterns
- Review error logs daily

---

## References

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **Python Security**: https://python.readthedocs.io/en/stable/library/security_warnings.html
- **Rate Limiting Best Practices**: https://cloud.google.com/architecture/rate-limiting-strategies

---

## Support

For security issues or questions:
1. Review this documentation
2. Check logs: `logs/app.log`
3. Test endpoints: `http://localhost:8000/docs`
4. Contact development team

---

**Last Updated**: 2026-02-03  
**Version**: 1.0.0  
**Security Level**: Production-Ready ✅
