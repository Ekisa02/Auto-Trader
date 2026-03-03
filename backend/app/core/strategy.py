'EOF'
"""
Three-Filter Trading Strategy
Combines trend, momentum, and volatility indicators
"""
import pandas as pd
import numpy as np
import ta
from ..core.mt5_compat import mt5
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreeFilterStrategy:
    """
    Trading strategy based on three filters:
    1. Trend Direction (EMA 50 & 200)
    2. Trend Strength (ADX)
    3. Saturation (RSI)
    """
    
    def __init__(self, symbol="EURUSD", timeframe=mt5.TIMEFRAME_H1, bars=200):
        self.symbol = symbol
        self.timeframe = timeframe
        self.bars = bars
        self.last_signal = None
        self.signal_count = 0
        
    def get_rates(self):
        """Fetch historical rates from MT5"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, self.bars)
            if rates is None or len(rates) == 0:
                logger.warning(f"No rates received for {self.symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        if df is None or len(df) < 100:
            return None
        
        try:
            # Make a copy to avoid warnings
            data = df.copy()
            
            # Filter 1: Trend Direction - EMAs
            data['ema_50'] = ta.trend.EMAIndicator(data['close'], window=50).ema_indicator()
            data['ema_200'] = ta.trend.EMAIndicator(data['close'], window=200).ema_indicator()
            
            # Filter 2: Trend Strength - ADX
            adx_indicator = ta.trend.ADXIndicator(data['high'], data['low'], data['close'], window=14)
            data['adx'] = adx_indicator.adx()
            data['plus_di'] = adx_indicator.adx_pos()
            data['minus_di'] = adx_indicator.adx_neg()
            
            # Filter 3: Saturation - RSI
            data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=14).rsi()
            
            # Additional indicators for confirmation
            data['macd'] = ta.trend.MACD(data['close']).macd()
            data['macd_signal'] = ta.trend.MACD(data['close']).macd_signal()
            data['macd_diff'] = ta.trend.MACD(data['close']).macd_diff()
            
            # Volatility
            bb = ta.volatility.BollingerBands(data['close'], window=20, window_dev=2)
            data['bb_high'] = bb.bollinger_hband()
            data['bb_low'] = bb.bollinger_lband()
            data['bb_width'] = (data['bb_high'] - data['bb_low']) / data['close']
            
            # Volume (if available)
            if 'tick_volume' in data.columns:
                data['volume_sma'] = data['tick_volume'].rolling(window=20).mean()
                data['volume_ratio'] = data['tick_volume'] / data['volume_sma']
            
            return data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
    
    def check_signal_strength(self, data):
        """Calculate signal strength (0-100)"""
        try:
            latest = data.iloc[-1]
            
            # Base strength
            strength = 50
            
            # ADX contribution (0-25)
            strength += min(latest['adx'] / 4, 25) if not pd.isna(latest['adx']) else 0
            
            # RSI contribution (0-15)
            if not pd.isna(latest['rsi']):
                if 40 <= latest['rsi'] <= 60:
                    strength += 15
                elif 30 <= latest['rsi'] <= 70:
                    strength += 10
                else:
                    strength += 5
            
            # Trend alignment (0-10)
            if not pd.isna(latest['ema_50']) and not pd.isna(latest['ema_200']):
                if latest['close'] > latest['ema_50'] > latest['ema_200']:
                    strength += 10
                elif latest['close'] < latest['ema_50'] < latest['ema_200']:
                    strength += 10
            
            return min(strength, 100)
            
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return 50
    
    def generate_signal(self):
        """
        Generate trading signal based on three filters
        Returns: (signal_type, price, strength)
        """
        # Fetch and calculate indicators
        df = self.get_rates()
        if df is None:
            return "NO_SIGNAL", None, 0
            
        data = self.calculate_indicators(df)
        if data is None or len(data) < 2:
            return "NO_SIGNAL", None, 0
        
        # Get current and previous values
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Check for NaN values
        if any(pd.isna(latest[key]) for key in ['ema_50', 'ema_200', 'adx', 'rsi']):
            return "NO_SIGNAL", None, 0
        
        # BUY Conditions
        buy_conditions = [
            latest['close'] > latest['ema_50'] > latest['ema_200'],  # Uptrend
            latest['adx'] > 25,                                      # Strong trend
            30 <= latest['rsi'] <= 70,                               # Not overbought
            latest['ema_50'] > prev['ema_50'],                       # EMA rising
        ]
        
        # SELL Conditions
        sell_conditions = [
            latest['close'] < latest['ema_50'] < latest['ema_200'],  # Downtrend
            latest['adx'] > 25,                                      # Strong trend
            30 <= latest['rsi'] <= 70,                               # Not oversold
            latest['ema_50'] < prev['ema_50'],                       # EMA falling
        ]
        
        # Additional confirmation
        ema_bullish_cross = prev['ema_50'] <= prev['ema_200'] and latest['ema_50'] > latest['ema_200']
        ema_bearish_cross = prev['ema_50'] >= prev['ema_200'] and latest['ema_50'] < latest['ema_200']
        
        # RSI momentum
        rsi_rising = latest['rsi'] > prev['rsi']
        
        # Calculate signal strength
        strength = self.check_signal_strength(data)
        
        # Generate signal with confirmation
        if all(buy_conditions) and (ema_bullish_cross or rsi_rising):
            signal = "BUY"
            logger.info(f"🔵 BUY signal generated for {self.symbol} (strength: {strength})")
            self.signal_count += 1
            self.last_signal = signal
            return signal, latest['close'], strength
            
        elif all(sell_conditions) and (ema_bearish_cross or not rsi_rising):
            signal = "SELL"
            logger.info(f"🔴 SELL signal generated for {self.symbol} (strength: {strength})")
            self.signal_count += 1
            self.last_signal = signal
            return signal, latest['close'], strength
        
        return "NO_SIGNAL", None, strength
    
    def get_market_regime(self):
        """Determine current market regime"""
        df = self.get_rates()
        if df is None:
            return "UNKNOWN"
            
        data = self.calculate_indicators(df)
        if data is None:
            return "UNKNOWN"
        
        latest = data.iloc[-1]
        
        # Check for NaN
        if pd.isna(latest['adx']) or pd.isna(latest['rsi']):
            return "UNKNOWN"
        
        # Determine regime
        if latest['adx'] > 30:
            if latest['rsi'] > 60:
                return "STRONG_UPTREND"
            elif latest['rsi'] < 40:
                return "STRONG_DOWNTREND"
            else:
                return "TRENDING"
        elif latest['adx'] < 20:
            return "RANGING"
        else:
            return "WEAK_TREND"
    
    def get_signal_summary(self):
        """Get summary of recent signals"""
        return {
            "symbol": self.symbol,
            "last_signal": self.last_signal,
            "total_signals": self.signal_count,
            "market_regime": self.get_market_regime()
        }
