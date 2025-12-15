# 🤖 AI Chatbot LMS - Backend API

Pure FastAPI backend service for AI Chatbot (Microservice Architecture)

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

# 4. Run the server
python -m app.main
# or
uvicorn app.main:app --reload
```

## 📡 API Endpoints

- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **API**: http://localhost:8000/api/*

## 🏗️ Project Structure
```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Configuration
│   ├── services/     # Business logic
│   ├── models/       # Pydantic models
│   ├── db/           # Database
│   └── utils/        # Utilities
├── data/             # Data storage
├── logs/             # Application logs
└── tests/            # Unit tests
```

## 🔧 Tech Stack

- FastAPI 0.104
- SQLite (AI Chat DB)
- PostgreSQL (LMS DB - read-only)
- Qdrant (Vector DB)
- DeepSeek API (LLM)

## 📝 Environment Variables

See `.env.example` for all required environment variables.

## 🧪 Testing
```bash
pytest tests/
```

## 📄 License

MIT License
