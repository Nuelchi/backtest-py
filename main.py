"""
Main entry point for the Event-Driven Backtesting Platform.
"""

import uvicorn
from backend.api.main import app

if __name__ == "__main__":
    print("🚀 Starting Event-Driven Backtesting Platform...")
    print("📊 Open your browser to: http://localhost:8000")
    print("🔧 API documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 