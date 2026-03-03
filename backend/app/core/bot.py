'EOF'
"""
Main Trading Bot
Orchestrates strategy, risk management, and trade execution
"""
import threading
import time
import logging
from datetime import datetime
from ..core.mt5_compat import mt5
from ..core.strategy import ThreeFilterStrategy
from ..core.trader import TradeExecutor
from ..config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, symbol=settings.DEFAULT_SYMBOL, timeframe=mt5.TIMEFRAME_H1):
        self.symbol = symbol
        self.timeframe = timeframe
        self.strategy = None
        self.executor = None
        self.is_running = False
        self.thread = None
        self.check_interval = 60  # Check every minute
        self.last_check_time = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
    def start(self):
        """Start the trading bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        logger.info(f"🚀 Starting trading bot for {self.symbol}")
        
        # Initialize MT5 connection
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            return
        
        logger.info("✅ MT5 initialized")
        
        # Login if credentials provided
        if settings.MT5_LOGIN and settings.MT5_PASSWORD and settings.MT5_SERVER:
            login_result = mt5.login(
                login=settings.MT5_LOGIN,
                password=settings.MT5_PASSWORD,
                server=settings.MT5_SERVER
            )
            if not login_result:
                logger.error(f"Login failed: {mt5.last_error()}")
            else:
                account_info = mt5.account_info()
                logger.info(f"✅ Logged in as {account_info.login} (Balance: {account_info.balance})")
        
        # Initialize strategy and executor
        self.strategy = ThreeFilterStrategy(self.symbol, self.timeframe)
        self.executor = TradeExecutor(self.symbol)
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"✅ Bot started for {self.symbol}")
    
    def stop(self):
        """Stop the trading bot"""
        logger.info(f"🛑 Stopping trading bot for {self.symbol}")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=10)
        
        # Close all positions? (Optional - depends on your strategy)
        # if self.executor:
        #     self.executor.close_all_positions()
        
        mt5.shutdown()
        logger.info("✅ Bot stopped")
    
    def _run_loop(self):
        """Main trading loop"""
        logger.info(f"🔄 Trading loop started (interval: {self.check_interval}s)")
        
        while self.is_running:
            try:
                self._tick()
                self.consecutive_errors = 0  # Reset error counter on success
                
            except Exception as e:
                self.consecutive_errors += 1
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.critical("Too many consecutive errors. Stopping bot.")
                    self.stop()
                    break
            
            # Wait for next check
            time.sleep(self.check_interval)
    
    def _tick(self):
        """Execute one trading cycle"""
        self.last_check_time = datetime.now()
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            logger.debug(f"Balance: {account_info.balance:.2f}, Equity: {account_info.equity:.2f}")
        
        # Check if we've reached max positions
        current_positions = self.executor.get_position_count()
        if current_positions >= settings.MAX_POSITIONS:
            logger.info(f"Max positions reached ({current_positions}/{settings.MAX_POSITIONS})")
            return
        
        # Generate trading signal
        signal, price, strength = self.strategy.generate_signal()
        
        # Log market regime
        regime = self.strategy.get_market_regime()
        logger.debug(f"Market regime: {regime}, Signal: {signal}, Strength: {strength}")
        
        # Execute trade if signal is strong enough
        if signal in ["BUY", "SELL"] and strength >= 60:
            logger.info(f"💡 Strong signal: {signal} (strength: {strength})")
            
            # Double-check we haven't exceeded max positions
            if current_positions < settings.MAX_POSITIONS:
                result = self.executor.open_trade(signal, price)
                if result:
                    logger.info(f"✅ Trade executed: {result.order}")
            else:
                logger.info("Max positions reached, skipping trade")
        
        # Manage existing positions (trailing stop, etc.)
        self._manage_positions()
    
    def _manage_positions(self):
        """Manage existing positions"""
        positions = self.executor.get_open_positions()
        if not positions:
            return
        
        for position in positions:
            # Check if we should trail stop
            if position.profit > 0:
                # If in profit, start trailing
                profit_pips = abs(position.profit) / position.volume / 10
                if profit_pips > 20:  # After 20 pips profit
                    self.executor.set_trailing_stop(position.ticket, trail_points=30)
    
    def get_status(self):
        """Get bot status"""
        account_info = mt5.account_info()
        
        return {
            "running": self.is_running,
            "symbol": self.symbol,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "account": {
                "balance": account_info.balance if account_info else 0,
                "equity": account_info.equity if account_info else 0,
                "profit": account_info.profit if account_info else 0
            } if account_info else None,
            "strategy": self.strategy.get_signal_summary() if self.strategy else None,
            "positions": self.executor.get_position_count() if self.executor else 0,
            "consecutive_errors": self.consecutive_errors
        }
    
    def get_positions(self):
        """Get all open positions"""
        return self.executor.get_open_positions() if self.executor else []
    
    def close_position(self, ticket):
        """Close a specific position"""
        return self.executor.close_trade(ticket) if self.executor else None
    
    def close_all(self):
        """Close all positions"""
        return self.executor.close_all_positions() if self.executor else None
