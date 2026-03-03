#!/usr/bin/env python3
"""
Complete verification script for Trading Bot setup
Tests all installed packages and their compatibility
"""

import sys
import platform
import importlib
from datetime import datetime

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD} {text}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}")

def print_success(text, details=""):
    print(f"  {GREEN}✅{RESET} {text:30} {details}")

def print_warning(text, details=""):
    print(f"  {YELLOW}⚠️ {RESET} {text:30} {details}")

def print_error(text, details=""):
    print(f"  {RED}❌{RESET} {text:30} {details}")

def print_info(text):
    print(f"  {BLUE}ℹ️ {RESET} {text}")

def get_version(module):
    """Safely get module version"""
    try:
        if hasattr(module, '__version__'):
            return module.__version__
        elif hasattr(module, 'version'):
            return module.version
        else:
            return 'installed'
    except:
        return 'unknown'

# Start verification
print_header("SYSTEM INFORMATION")
print_info(f"Python Version: {sys.version}")
print_info(f"Platform: {platform.system()} {platform.release()}")
print_info(f"Machine: {platform.machine()}")
print_info(f"Virtual Environment: {sys.prefix != sys.base_prefix}")
print_info(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Test Core Packages
print_header("CORE PACKAGES")

packages = [
    ('numpy', 'NumPy'),
    ('pandas', 'Pandas'),
    ('ta', 'Technical Analysis'),
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('websockets', 'WebSockets'),
    ('mt5linux', 'MT5Linux'),
    ('dotenv', 'Python DotEnv'),
]

for module_name, display_name in packages:
    try:
        module = importlib.import_module(module_name)
        version = get_version(module)
        print_success(display_name, f"v{version}")
    except ImportError as e:
        print_error(display_name, f"Failed: {e}")

# Test Package Compatibility
print_header("PACKAGE COMPATIBILITY")

try:
    import numpy as np
    import pandas as pd
    
    # Test NumPy
    np_test = np.array([1, 2, 3])
    print_success("NumPy array creation", f"Shape: {np_test.shape}")
    
    # Test Pandas
    df_test = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    print_success("Pandas DataFrame", f"Shape: {df_test.shape}")
    
    # Check Pandas version compatibility
    pd_version = tuple(map(int, pd.__version__.split('.')))
    if pd_version >= (2, 0, 0):
        print_success("Pandas version", f"{pd.__version__} (compatible)")
    else:
        print_warning("Pandas version", f"{pd.__version__} (older)")
        
except Exception as e:
    print_error("NumPy/Pandas compatibility", str(e))

# Test Technical Analysis Library
print_header("TECHNICAL ANALYSIS (TA)")

try:
    import ta
    import pandas as pd
    import numpy as np
    
    print_success("TA Library", f"v{ta.__version__ if hasattr(ta, '__version__') else 'unknown'}")
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=200, freq='D')
    data = pd.DataFrame({
        'open': np.random.randn(200) + 100,
        'high': np.random.randn(200) + 101,
        'low': np.random.randn(200) + 99,
        'close': np.random.randn(200) + 100,
        'volume': np.random.randint(1000, 10000, 200)
    }, index=dates)
    
    print_success("Sample data created", f"Shape: {data.shape}")
    
    # Calculate various indicators
    try:
        # RSI
        data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=14).rsi()
        print_success("RSI calculated", f"Last value: {data['rsi'].iloc[-1]:.2f}")
        
        # EMA
        data['ema_20'] = ta.trend.EMAIndicator(data['close'], window=20).ema_indicator()
        data['ema_50'] = ta.trend.EMAIndicator(data['close'], window=50).ema_indicator()
        print_success("EMA calculated", f"EMA20: {data['ema_20'].iloc[-1]:.2f}")
        
        # ADX
        adx = ta.trend.ADXIndicator(data['high'], data['low'], data['close'], window=14)
        data['adx'] = adx.adx()
        print_success("ADX calculated", f"Value: {data['adx'].iloc[-1]:.2f}")
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(data['close'], window=20, window_dev=2)
        data['bb_high'] = bb.bollinger_hband()
        data['bb_low'] = bb.bollinger_lband()
        print_success("Bollinger Bands", "Calculated")
        
        print_success("All indicators", "Successfully calculated")
        
    except Exception as e:
        print_error("Indicator calculation", str(e))
        
except Exception as e:
    print_error("TA Library test", str(e))

# Test mt5linux
print_header("MT5LINUX COMPATIBILITY")

try:
    from mt5linux import MetaTrader5 as mt5
    print_success("mt5linux imported", f"v{mt5.__version__ if hasattr(mt5, '__version__') else 'unknown'}")
    
    # Check available methods (without actually connecting)
    mt5_methods = [method for method in dir(mt5) if not method.startswith('_')]
    essential_methods = ['initialize', 'login', 'shutdown', 'account_info', 
                        'symbol_info', 'symbol_info_tick', 'copy_rates_from_pos',
                        'order_send', 'positions_get']
    
    available_methods = [m for m in essential_methods if hasattr(mt5, m)]
    missing_methods = [m for m in essential_methods if not hasattr(mt5, m)]
    
    print_success("Available methods", f"{len(available_methods)}/{len(essential_methods)}")
    if missing_methods:
        print_warning("Missing methods", f"{missing_methods}")
    else:
        print_success("All methods", "Available")
        
    print_info("Note: Actual connection requires running MT5 server")
    
except ImportError as e:
    print_error("mt5linux import", str(e))

# Test FastAPI
print_header("FASTAPI & WEB COMPONENTS")

try:
    from fastapi import FastAPI
    app = FastAPI(title="Test App")
    print_success("FastAPI app created", f"Title: {app.title}")
    
    @app.get("/test")
    async def test():
        return {"message": "OK"}
    print_success("Route created", "/test endpoint")
    
except Exception as e:
    print_error("FastAPI test", str(e))

try:
    import uvicorn
    print_success("Uvicorn", f"Available")
except Exception as e:
    print_error("Uvicorn", str(e))

try:
    import websockets
    print_success("WebSockets", f"v{websockets.__version__ if hasattr(websockets, '__version__') else 'unknown'}")
except Exception as e:
    print_error("WebSockets", str(e))

# Test Complete Trading Strategy
print_header("TRADING STRATEGY SIMULATION")

try:
    import pandas as pd
    import numpy as np
    import ta
    
    # Generate realistic price data
    np.random.seed(42)
    periods = 1000
    returns = np.random.randn(periods) * 0.02
    price = 100 * np.exp(np.cumsum(returns))
    
    # Create OHLC data
    data = pd.DataFrame({
        'open': price * (1 + np.random.randn(periods) * 0.001),
        'high': price * (1 + np.random.randn(periods) * 0.002),
        'low': price * (1 - np.random.randn(periods) * 0.002),
        'close': price,
        'volume': np.random.randint(100, 10000, periods)
    })
    
    # Calculate strategy indicators
    data['ema_50'] = ta.trend.EMAIndicator(data['close'], window=50).ema_indicator()
    data['ema_200'] = ta.trend.EMAIndicator(data['close'], window=200).ema_indicator()
    data['adx'] = ta.trend.ADXIndicator(data['high'], data['low'], data['close'], window=14).adx()
    data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=14).rsi()
    
    # Generate signals
    buy_signals = (
        (data['close'] > data['ema_50']) & 
        (data['ema_50'] > data['ema_200']) & 
        (data['adx'] > 25) & 
        (data['rsi'] < 70) & 
        (data['rsi'] > 30)
    )
    
    sell_signals = (
        (data['close'] < data['ema_50']) & 
        (data['ema_50'] < data['ema_200']) & 
        (data['adx'] > 25) & 
        (data['rsi'] < 70) & 
        (data['rsi'] > 30)
    )
    
    buy_count = buy_signals.sum()
    sell_count = sell_signals.sum()
    
    print_success("Strategy indicators", "All calculated")
    print_success("Buy signals generated", f"{buy_count} signals")
    print_success("Sell signals generated", f"{sell_count} signals")
    print_info(f"Latest price: {data['close'].iloc[-1]:.2f}")
    print_info(f"Latest RSI: {data['rsi'].iloc[-1]:.2f}")
    print_info(f"Latest ADX: {data['adx'].iloc[-1]:.2f}")
    
except Exception as e:
    print_error("Strategy simulation", str(e))

# Final Summary
print_header("VERIFICATION SUMMARY")

# Count successes and failures
success_count = 0
warning_count = 0
error_count = 0

# This is a simple summary - we'll just check imports
all_imports = ['numpy', 'pandas', 'ta', 'fastapi', 'uvicorn', 'websockets', 'mt5linux']
for module in all_imports:
    try:
        importlib.import_module(module)
        success_count += 1
    except ImportError:
        error_count += 1

if error_count == 0:
    print(f"{GREEN}{BOLD}✅ ALL SYSTEMS GO! All packages installed successfully.{RESET}")
    print(f"{GREEN}   You can now proceed with running the trading bot.{RESET}")
    print(f"\n{BLUE}Next steps:{RESET}")
    print(f"  1. Configure your .env file with MT5 credentials")
    print(f"  2. Start the backend server: python run.py")
    print(f"  3. Build and run the Android app")
else:
    print(f"{YELLOW}⚠️  Some issues detected. Check the red X marks above.{RESET}")

print(f"\n{BLUE}{BOLD}Happy Trading! 📈{RESET}")
