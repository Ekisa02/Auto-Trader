'EOF'
"""
Trade execution module
Handles opening, closing, and modifying trades
"""
from ..core.mt5_compat import mt5
from ..core.risk_manager import RiskManager
from ..config import settings
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class TradeExecutor:
    def __init__(self, symbol):
        self.symbol = symbol
        self.risk_manager = None
        self.magic_number = 234000  # Unique identifier for our bot
        
    def update_account_info(self):
        """Update account balance for risk management"""
        account_info = mt5.account_info()
        if account_info:
            self.risk_manager = RiskManager(account_info.balance)
            return account_info
        return None
    
    def get_symbol_info(self):
        """Get symbol information"""
        return mt5.symbol_info(self.symbol)
    
    def get_current_price(self):
        """Get current bid/ask prices"""
        tick = mt5.symbol_info_tick(self.symbol)
        return tick
    
    def open_trade(self, signal_type, entry_price=None, comment="ThreeFilterBot"):
        """
        Open a new trade with automatic SL and TP
        """
        if signal_type not in ["BUY", "SELL"]:
            return None
        
        # Update account info
        account_info = self.update_account_info()
        if not account_info:
            logger.error("Failed to get account info")
            return None
        
        # Get symbol info
        symbol_info = self.get_symbol_info()
        if not symbol_info:
            logger.error(f"Failed to get symbol info for {self.symbol}")
            return None
        
        # Get current price if not provided
        tick = self.get_current_price()
        if not tick:
            logger.error("Failed to get current price")
            return None
        
        # Determine entry price
        if signal_type == "BUY":
            price = tick.ask if not entry_price else entry_price
        else:
            price = tick.bid if not entry_price else entry_price
        
        # Calculate ATR for dynamic SL/TP
        from .strategy import ThreeFilterStrategy
        strategy = ThreeFilterStrategy(self.symbol)
        df = strategy.get_rates()
        if df is not None:
            atr = self.risk_manager.calculate_atr(df)
        else:
            atr = None
        
        # Calculate stop loss
        stop_loss = self.risk_manager.calculate_stop_loss(
            signal_type, price, atr or 0.0020, multiplier=2.0
        )
        
        # Calculate take profit (2:1 risk/reward)
        take_profit = self.risk_manager.calculate_take_profit(
            signal_type, price, stop_loss, risk_reward=2.0
        )
        
        # Calculate position size
        lot_size = self.risk_manager.calculate_position_size(
            symbol_info, price, stop_loss
        )
        
        # Prepare trade request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot_size,
            "type": mt5.ORDER_TYPE_BUY if signal_type == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": 20,
            "magic": self.magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        logger.info(f"Sending order: {request}")
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode}, {result.comment}")
            return None
        
        logger.info(f"✅ Trade opened successfully: {result.order}")
        
        # Log trade details
        self.log_trade({
            "ticket": result.order,
            "symbol": self.symbol,
            "type": signal_type,
            "volume": lot_size,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "comment": comment
        })
        
        return result
    
    def close_trade(self, ticket):
        """
        Close a specific trade by ticket number
        """
        # Get position info
        position = mt5.positions_get(ticket=ticket)
        if not position or len(position) == 0:
            logger.error(f"Position {ticket} not found")
            return None
        
        position = position[0]
        
        # Determine close order type
        tick = self.get_current_price()
        if position.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": self.magic_number,
            "comment": "Close by bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close order
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ Position {ticket} closed successfully")
            return result
        else:
            logger.error(f"Failed to close position {ticket}: {result.retcode}")
            return None
    
    def close_all_positions(self):
        """
        Close all open positions for this symbol
        """
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            logger.info(f"No open positions for {self.symbol}")
            return []
        
        results = []
        for position in positions:
            result = self.close_trade(position.ticket)
            if result:
                results.append(result)
            time.sleep(0.5)  # Small delay between closes
        
        logger.info(f"Closed {len(results)} positions")
        return results
    
    def modify_trade(self, ticket, sl=None, tp=None):
        """
        Modify stop loss and/or take profit for a trade
        """
        if not sl and not tp:
            logger.warning("No SL or TP provided for modification")
            return None
        
        # Get current position
        position = mt5.positions_get(ticket=ticket)
        if not position:
            logger.error(f"Position {ticket} not found")
            return None
        
        position = position[0]
        
        # Prepare modify request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": self.symbol,
        }
        
        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp
        
        # Send modify request
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ Modified position {ticket}")
            return result
        else:
            logger.error(f"Failed to modify position {ticket}: {result.retcode}")
            return None
    
    def set_trailing_stop(self, ticket, trail_points=50):
        """
        Implement trailing stop loss
        """
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return None
        
        position = position[0]
        tick = self.get_current_price()
        
        point = self.get_symbol_info().point
        trail_distance = trail_points * point
        
        if position.type == mt5.POSITION_TYPE_BUY:
            # For long positions
            new_sl = tick.bid - trail_distance
            if new_sl > position.sl:  # Only move SL up
                self.modify_trade(ticket, sl=new_sl)
                
        else:  # SELL position
            # For short positions
            new_sl = tick.ask + trail_distance
            if new_sl < position.sl:  # Only move SL down
                self.modify_trade(ticket, sl=new_sl)
    
    def log_trade(self, trade_info):
        """
        Log trade to file for record keeping
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} | {trade_info['ticket']} | {trade_info['symbol']} | "
        log_line += f"{trade_info['type']} | {trade_info['volume']} | {trade_info['price']} | "
        log_line += f"SL: {trade_info['sl']} | TP: {trade_info['tp']} | {trade_info['comment']}\n"
        
        try:
            with open("trades.log", "a") as f:
                f.write(log_line)
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
    
    def get_open_positions(self):
        """Get all open positions for this symbol"""
        return mt5.positions_get(symbol=self.symbol)
    
    def get_position_count(self):
        """Get number of open positions"""
        positions = self.get_open_positions()
        return len(positions) if positions else 0
