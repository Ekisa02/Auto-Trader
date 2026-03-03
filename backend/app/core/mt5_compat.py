"""
MetaTrader5 compatibility layer for Linux
Connects to real MT5 running on Kali via Wine
"""
import sys
import platform
import os
import time
from pathlib import Path

# Load credentials from .env
from dotenv import load_dotenv
load_dotenv()

MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")

print("=" * 60)
print("🔌 MT5 Connection Module")
print("=" * 60)
print(f"📋 Credentials loaded:")
print(f"   Login: {MT5_LOGIN}")
print(f"   Server: {MT5_SERVER}")
print("=" * 60)

# Flag to track if we're using real MT5
USING_REAL_MT5 = False

# Try to connect to real MT5
try:
    # First try mt5-remote (most reliable on Linux)
    try:
        from mt5_remote import MetaTrader5 as mt5_remote
        print("📡 Trying mt5-remote connection...")
        
        # Initialize connection
        if mt5_remote.initialize():
            # Try to login with credentials
            if mt5_remote.login(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER):
                account = mt5_remote.account_info()
                if account and account.balance > 0:
                    USING_REAL_MT5 = True
                    mt5 = mt5_remote
                    print(f"\n✅✅✅ CONNECTED TO REAL MT5! ✅✅✅")
                    print(f"   Account: {account.login}")
                    print(f"   Balance: {account.balance}")
                    print(f"   Equity: {account.equity}")
                    print(f"   Server: {account.server}")
                else:
                    print("⚠️ Connected but couldn't get account info")
            else:
                print("❌ Login failed with provided credentials")
        else:
            print("❌ mt5-remote initialization failed")
            
    except ImportError:
        print("📡 mt5-remote not installed, trying mt5linux...")
        
        # Try mt5linux as fallback
        try:
            from mt5linux import MetaTrader5 as mt5_linux
            
            # First try connecting to local server (if running)
            print("   Attempting connection to local mt5linux server...")
            mt5 = mt5_linux(host='localhost', port=18812)
            
            if mt5.initialize():
                # Try to login
                if mt5.login(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER):
                    account = mt5.account_info()
                    if account and account.balance > 0:
                        USING_REAL_MT5 = True
                        print(f"\n✅✅✅ CONNECTED TO REAL MT5! ✅✅✅")
                        print(f"   Account: {account.login}")
                        print(f"   Balance: {account.balance}")
                        print(f"   Equity: {account.equity}")
                    else:
                        print("⚠️ Connected but couldn't get account info")
                else:
                    print("❌ Login failed")
            else:
                print("❌ Could not connect to mt5linux server")
                print("   Make sure MT5 is running and the bridge is started")
                
        except ImportError:
            print("❌ Neither mt5-remote nor mt5linux is installed")
            print("   Run: pip install mt5-remote")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

# If we couldn't connect to real MT5, raise an error instead of using mock
if not USING_REAL_MT5:
    print("\n" + "❌" * 60)
    print("❌ CRITICAL: Could not connect to REAL MT5!")
    print("❌" * 60)
    print("\nPlease check:")
    print("1. Is MT5 running?")
    print("   Run: wine 'C:/Program Files/MetaTrader 5/terminal64.exe'")
    print("2. Is your account logged in?")
    print("3. Are your credentials correct in .env?")
    print("4. Is the mt5linux bridge running?")
    print("   Run: python simple_bridge.py")
    print("\n❌ Cannot continue with mock data - please fix connection issues.")
    sys.exit(1)

# Export the mt5 instance
__all__ = ['mt5', 'USING_REAL_MT5']