#!/usr/bin/env python3
"""
Entry point for running the trading bot server
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Trading Bot Server")
    print("=" * 50)
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Default Symbol: {settings.DEFAULT_SYMBOL}")
    print(f"Risk: {settings.RISK_PERCENTAGE}%")
    print(f"Max Positions: {settings.MAX_POSITIONS}")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )