#!/usr/bin/env python3
"""
FastAPI startup script for MoonbeamAI
"""

import os
import sys
import uvicorn

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Start the FastAPI application."""
    # Create log directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    print("🚀 MoonbeamAI: Financial News Sentiment Trading System")
    print("🌟 Powered by Alpha Vantage real-time financial news")
    print("⚡ FastAPI + Alpha Vantage Integration")
    print("=" * 50)
    print(f"🌐 Server starting at: http://localhost:8000")
    print(f"📊 System status: http://localhost:8000/system-status")
    print(f"📡 WebSocket: ws://localhost:8000/ws")
    print(f"📖 API docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Start the FastAPI server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
        access_log=True
    )

if __name__ == "__main__":
    main() 