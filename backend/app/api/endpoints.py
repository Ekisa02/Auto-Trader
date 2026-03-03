'EOF'
"""
API endpoints for the trading bot
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from ..core.bot import TradingBot
from ..core.mt5_compat import mt5
from ..config import settings
import logging
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active bots
active_bots: Dict[str, TradingBot] = {}

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Trading Bot API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "GET /": "This help",
            "GET /health": "Health check",
            "GET /account": "Account information",
            "GET /positions": "Open positions",
            "GET /bots": "List all bots",
            "POST /bot/{symbol}/start": "Start bot for symbol",
            "POST /bot/{symbol}/stop": "Stop bot for symbol",
            "GET /bot/{symbol}/status": "Get bot status",
            "POST /positions/{ticket}/close": "Close position",
            "POST /positions/close-all": "Close all positions",
            "WS /ws": "WebSocket for real-time updates"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    mt5_status = False
    try:
        mt5_status = mt5.initialize()
        if mt5_status:
            mt5.shutdown()
    except:
        pass
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mt5_available": mt5_status,
        "active_bots": len(active_bots)
    }

@router.get("/account")
async def get_account():
    """Get account information"""
    try:
        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize MT5")
        
        account_info = mt5.account_info()
        if not account_info:
            raise HTTPException(status_code=500, detail="Failed to get account info")
        
        return {
            "login": account_info.login,
            "balance": account_info.balance,
            "equity": account_info.equity,
            "profit": account_info.profit,
            "margin": account_info.margin,
            "margin_free": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "leverage": account_info.leverage,
            "name": account_info.name,
            "server": account_info.server,
            "currency": account_info.currency
        }
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mt5.shutdown()

@router.get("/positions")
async def get_positions(symbol: str = None):
    """Get all open positions"""
    try:
        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize MT5")
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            return []
        
        result = []
        for pos in positions:
            result.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == 0 else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "sl": pos.sl,
                "tp": pos.tp,
                "price_current": pos.price_current,
                "profit": pos.profit,
                "swap": pos.swap,
                "comment": pos.comment,
                "magic": pos.magic,
                "time": datetime.fromtimestamp(pos.time).isoformat()
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mt5.shutdown()

@router.get("/bots")
async def list_bots():
    """List all active bots"""
    return {
        symbol: bot.get_status() for symbol, bot in active_bots.items()
    }

@router.post("/bot/{symbol}/start")
async def start_bot(symbol: str, timeframe: str = "H1"):
    """Start a trading bot for a symbol"""
    if symbol in active_bots and active_bots[symbol].is_running:
        return {"message": f"Bot already running for {symbol}", "status": "running"}
    
    # Map timeframe string to MT5 constant
    timeframe_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1
    }
    
    tf = timeframe_map.get(timeframe.upper(), mt5.TIMEFRAME_H1)
    
    try:
        bot = TradingBot(symbol=symbol, timeframe=tf)
        bot.start()
        active_bots[symbol] = bot
        
        # Broadcast update
        await manager.broadcast({
            "type": "bot_started",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": f"Bot started for {symbol}",
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bot/{symbol}/stop")
async def stop_bot(symbol: str):
    """Stop a trading bot"""
    if symbol not in active_bots:
        return {"message": f"No bot running for {symbol}"}
    
    try:
        active_bots[symbol].stop()
        del active_bots[symbol]
        
        # Broadcast update
        await manager.broadcast({
            "type": "bot_stopped",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"message": f"Bot stopped for {symbol}", "status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bot/{symbol}/status")
async def get_bot_status(symbol: str):
    """Get status of a specific bot"""
    if symbol not in active_bots:
        return {"running": False, "symbol": symbol}
    
    return active_bots[symbol].get_status()

@router.post("/positions/{ticket}/close")
async def close_position(ticket: int):
    """Close a specific position"""
    # Find which bot owns this position
    for symbol, bot in active_bots.items():
        if bot.is_running:
            result = bot.close_position(ticket)
            if result:
                return {"message": f"Position {ticket} closed", "success": True}
    
    # If not found in active bots, try direct close
    try:
        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize MT5")
        
        position = mt5.positions_get(ticket=ticket)
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {ticket} not found")
        
        # Create a temporary executor
        from ..core.trader import TradeExecutor
        executor = TradeExecutor(position[0].symbol)
        result = executor.close_trade(ticket)
        
        if result:
            return {"message": f"Position {ticket} closed", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to close position")
            
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        mt5.shutdown()

@router.post("/positions/close-all")
async def close_all_positions(symbol: str = None):
    """Close all positions (optionally for a specific symbol)"""
    results = []
    
    if symbol and symbol in active_bots:
        # Close using bot
        results = active_bots[symbol].close_all()
    else:
        # Close all positions directly
        try:
            if not mt5.initialize():
                raise HTTPException(status_code=500, detail="Failed to initialize MT5")
            
            positions = mt5.positions_get()
            if positions:
                for pos in positions:
                    from ..core.trader import TradeExecutor
                    executor = TradeExecutor(pos.symbol)
                    result = executor.close_trade(pos.ticket)
                    if result:
                        results.append(pos.ticket)
                    await asyncio.sleep(0.5)  # Rate limiting
                    
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            mt5.shutdown()
    
    return {
        "message": f"Closed {len(results)} positions",
        "closed_positions": results
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive client messages (if any)
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle client messages if needed
                logger.debug(f"Received WebSocket message: {message}")
            except:
                pass
            
            # Send periodic updates
            for _ in range(60):  # Send for 60 seconds then wait for next client message
                try:
                    # Get account info
                    if mt5.initialize():
                        account = mt5.account_info()
                        positions = mt5.positions_get()
                        
                        update = {
                            "type": "update",
                            "timestamp": datetime.now().isoformat(),
                            "account": {
                                "balance": account.balance if account else 0,
                                "equity": account.equity if account else 0,
                                "profit": account.profit if account else 0,
                            } if account else None,
                            "positions": [
                                {
                                    "ticket": p.ticket,
                                    "symbol": p.symbol,
                                    "type": "BUY" if p.type == 0 else "SELL",
                                    "volume": p.volume,
                                    "price": p.price_current,
                                    "profit": p.profit
                                } for p in (positions or [])
                            ],
                            "bots": {
                                symbol: {
                                    "running": bot.is_running,
                                    "positions": bot.executor.get_position_count() if bot.executor else 0
                                } for symbol, bot in active_bots.items()
                            }
                        }
                        
                        await websocket.send_json(update)
                        mt5.shutdown()
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error sending WebSocket update: {e}")
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
