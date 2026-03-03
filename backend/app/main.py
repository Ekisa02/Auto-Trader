'EOF'
"""
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .api import endpoints
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="Automated trading bot for MetaTrader 5",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Android app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(endpoints.router)

@app.on_event("startup")
async def startup_event():
    """Actions to run on application startup"""
    logger.info("🚀 Starting Trading Bot API")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Default symbol: {settings.DEFAULT_SYMBOL}")
    logger.info(f"Risk percentage: {settings.RISK_PERCENTAGE}%")
    logger.info(f"Max positions: {settings.MAX_POSITIONS}")

@app.on_event("shutdown")
async def shutdown_event():
    """Actions to run on application shutdown"""
    logger.info("🛑 Shutting down Trading Bot API")
    
    # Stop all active bots
    from .api.endpoints import active_bots
    for symbol, bot in list(active_bots.items()):
        logger.info(f"Stopping bot for {symbol}")
        bot.stop()
    
    logger.info("✅ Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
