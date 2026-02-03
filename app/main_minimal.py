"""
Minimal FastAPI app for Railway testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chatbot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Chatbot API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/message")
async def chat(request: dict):
    return {
        "success": True,
        "reply": "Hello! This is a test response. Full features coming soon.",
        "message": request.get("message", "")
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
