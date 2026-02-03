# 🤖 AI Chatbot LMS - Backend API

Pure FastAPI backend service for AI Chatbot (Microservice Architecture)

## 🔐 Security Features

This API implements **production-grade security** without authentication:
- ✅ Input validation (XSS, SQL injection, path traversal protection)
- ✅ Security headers (XSS protection, clickjacking prevention)
- ✅ Rate limiting (20 requests/day per session)
- ✅ Request size limits (max 2000 chars)
- ✅ Log sanitization

**📖 Full security documentation**: [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md)

## 🚀 Quick Start
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your actual values

# 4. Apply security features
python apply_public_security.py

# 5. Run the server
python -m app.main
# or
uvicorn app.main:app --reload
```

## 📡 API Endpoints

- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Chat**: http://localhost:8000/api/message

## 🏗️ Project Structure
```
backend/
├── app/
│   ├── api/              # API routes
│   │   └── chat_public.py    # Public chat (no auth)
│   ├── core/             # Configuration
│   ├── services/         # Business logic
│   ├── models/           # Pydantic models
│   ├── middleware/       # Security middleware
│   │   └── security.py       # Input validation & headers
│   ├── db/               # Database
│   └── utils/            # Utilities
├── data/                 # Data storage
├── logs/                 # Application logs
└── tests/                # Unit tests
```

## 🔧 Tech Stack

- FastAPI 0.104
- SQLite (AI Chat DB)
- PostgreSQL (LMS DB - read-only)
- Qdrant (Vector DB)
- DeepSeek API (LLM)

## 📝 Environment Variables

See `.env.example` for all required environment variables.

Key variables:
- `DEBUG=False` - Production mode
- `ENVIRONMENT=production`
- `JWT_SECRET_KEY` - Strong random key (auto-generated)
- `DEEPSEEK_API_KEY` - Your DeepSeek API key
- `CORS_ORIGINS` - Allowed domains

## 🧪 Testing

### Test Security
```bash
# Test XSS protection
curl http://localhost:8000/api/message \
  -Method POST \
  -ContentType "application/json" \
  -Body '{"message":"<script>alert(1)</script>"}' \
  -UseBasicParsing

# Expected: HTTP 400 - "Invalid input detected"
```

### Test API
Open browser: http://localhost:8000/docs

## 🔒 Security

This API is production-ready with:
- Input validation against XSS, SQL injection, path traversal
- Security headers (HSTS, CSP, X-Frame-Options, etc)
- Rate limiting (20 requests/day per session)
- Request size limits
- Log sanitization

No authentication required - public access with security controls.

See [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md) for details.

## 📄 License

MIT License
