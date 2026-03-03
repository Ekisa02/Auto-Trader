'EOF'
"""
Risk management module
Calculates position sizes, stop losses, and take profits
"""
import math
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, account_balance, risk_percentage=None):
        self.account_balance = account_balance
        self.risk_percentage = risk_percentage or settings.RISK_PERCENTAGE
        self.max_positions = settings.MAX_POSITIONS
        
    def calculate_position_size(self, symbol_info, entry_price, stop_loss_price):
        """
        Calculate position size based on risk percentage
        Uses the 1% rule: risk only 1% of account on any single trade
        """
        if not symbol_info or not entry_price or not stop_loss_price:
            return symbol_info.volume_min if symbol_info else 0.01
        
        # Calculate risk amount in account currency
        risk_amount = self.account_balance * (self.risk_percentage / 100)
        
        # Calculate stop loss distance in points
        sl_distance = abs(entry_price - stop_loss_price)
        if sl_distance == 0:
            return symbol_info.volume_min
        
        # Calculate pip value (simplified)
        pip_value = 10 ** (-symbol_info.digits) if hasattr(symbol_info, 'digits') else 0.0001
        
        # Calculate position size
        # Formula: Position Size = Risk Amount / (SL Distance * Pip Value * 100000)
        # This is simplified - actual calculation depends on pair and account currency
        position_size = risk_amount / (sl_distance / pip_value * 100000)
        
        # Round to nearest valid step
        if hasattr(symbol_info, 'volume_step'):
            position_size = round(position_size / symbol_info.volume_step) * symbol_info.volume_step
        
        # Ensure within limits
        if hasattr(symbol_info, 'volume_min') and hasattr(symbol_info, 'volume_max'):
            position_size = max(symbol_info.volume_min, 
                              min(position_size, symbol_info.volume_max))
        
        return round(position_size, 2)
    
    def calculate_stop_loss(self, signal_type, entry_price, atr_value, multiplier=2.0):
        """
        Calculate stop loss based on ATR
        Uses ATR * multiplier for dynamic stop loss
        """
        if not atr_value or atr_value <= 0:
            # Default to 20 pips if no ATR
            atr_value = 0.0020  # 20 pips for EURUSD
        
        sl_distance = atr_value * multiplier
        
        if signal_type == "BUY":
            stop_loss = entry_price - sl_distance
        else:  # SELL
            stop_loss = entry_price + sl_distance
        
        return stop_loss
    
    def calculate_take_profit(self, signal_type, entry_price, stop_loss, risk_reward=2.0):
        """
        Calculate take profit based on risk/reward ratio
        Default risk/reward = 2:1
        """
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * risk_reward
        
        if signal_type == "BUY":
            take_profit = entry_price + tp_distance
        else:  # SELL
            take_profit = entry_price - tp_distance
        
        return take_profit
    
    def calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        if df is None or len(df) < period:
            return None
            
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        tr = []
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr.append(max(hl, hc, lc))
        
        if len(tr) < period:
            return None
            
        atr = sum(tr[-period:]) / period
        return atr
    
    def check_max_positions(self, current_positions):
        """Check if we've reached maximum positions"""
        return len(current_positions) >= self.max_positions
    
    def check_daily_loss_limit(self, daily_loss, limit_percentage=5.0):
        """Check if daily loss limit is reached"""
        max_daily_loss = self.account_balance * (limit_percentage / 100)
        return abs(daily_loss) >= max_daily_loss
    
    def get_risk_report(self, open_positions, daily_pnl):
        """Generate risk report"""
        return {
            "account_balance": self.account_balance,
            "risk_percentage": self.risk_percentage,
            "max_positions": self.max_positions,
            "current_positions": len(open_positions),
            "daily_pnl": daily_pnl,
            "daily_loss_limit": self.account_balance * 0.05,  # 5% daily loss limit
            "remaining_positions": self.max_positions - len(open_positions),
            "risk_per_trade": self.account_balance * (self.risk_percentage / 100)
        }
