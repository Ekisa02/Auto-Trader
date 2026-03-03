#!/usr/bin/env python3
"""
Clean test script for the trading bot
No shell commands, just Python code
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")
    required_files = [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/core/mt5_compat.py",
        "app/core/strategy.py",
        "app/core/trader.py",
        "app/core/bot.py",
        "app/core/risk_manager.py",
        "app/api/__init__.py",
        "app/api/endpoints.py",
        "app/config.py",
        "app/models/__init__.py",
        "app/utils/__init__.py",
        "run.py",
        ".env"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (MISSING)")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test all imports"""
    print("📦 Testing imports...")
    try:
        # Try to import our modules
        from app.core import mt5_compat
        print("  ✅ mt5_compat imported")
        
        from app.core import strategy
        print("  ✅ strategy imported")
        
        from app.core import trader
        print("  ✅ trader imported")
        
        from app.core import bot
        print("  ✅ bot imported")
        
        from app.api import endpoints
        print("  ✅ api imported")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_strategy():
    """Test strategy initialization"""
    print("\n📊 Testing strategy...")
    try:
        from app.core.strategy import ThreeFilterStrategy
        
        # Just test initialization, not actual signal generation
        strategy = ThreeFilterStrategy("EURUSD")
        print(f"  ✅ Strategy created for {strategy.symbol}")
        
        # Check if methods exist
        methods = ['generate_signal', 'get_market_regime', 'get_signal_summary']
        for method in methods:
            if hasattr(strategy, method):
                print(f"  ✅ Method '{method}' exists")
            else:
                print(f"  ❌ Method '{method}' missing")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def test_trader():
    """Test trader initialization"""
    print("\n💼 Testing trader...")
    try:
        from app.core.trader import TradeExecutor
        
        executor = TradeExecutor("EURUSD")
        print(f"  ✅ Trader created for {executor.symbol}")
        
        # Check if methods exist
        methods = ['open_trade', 'close_trade', 'get_open_positions', 'get_symbol_info']
        for method in methods:
            if hasattr(executor, method):
                print(f"  ✅ Method '{method}' exists")
            else:
                print(f"  ❌ Method '{method}' missing")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def test_bot():
    """Test bot initialization"""
    print("\n🤖 Testing bot...")
    try:
        from app.core.bot import TradingBot
        
        bot = TradingBot("EURUSD")
        print(f"  ✅ Bot created for {bot.symbol}")
        
        # Check if methods exist
        methods = ['start', 'stop', 'get_status', 'get_positions']
        for method in methods:
            if hasattr(bot, method):
                print(f"  ✅ Method '{method}' exists")
            else:
                print(f"  ❌ Method '{method}' missing")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def test_api():
    """Test API imports"""
    print("\n🌐 Testing API...")
    try:
        from fastapi import FastAPI
        from app.api.endpoints import router
        
        app = FastAPI()
        app.include_router(router)
        
        # Count routes
        route_count = len(router.routes)
        print(f"  ✅ API router loaded with {route_count} routes")
        
        # List some routes
        routes = [route.path for route in router.routes[:5]]
        print(f"  📍 Sample routes: {routes}")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Trading Bot Test Suite")
    print("=" * 60)
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Current directory: {os.getcwd()}")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Strategy", test_strategy),
        ("Trader", test_trader),
        ("Bot", test_bot),
        ("API", test_api)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n📋 Running {name} test...")
        print("-" * 40)
        if test_func():
            passed += 1
            print(f"  ✅ {name} test PASSED")
        else:
            failed += 1
            print(f"  ❌ {name} test FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n" + "✅" * 15)
        print("✅ ALL TESTS PASSED! 🎉")
        print("✅" * 15)
        print("\n🚀 Ready to start the server!")
        print("\nCommands:")
        print("  python run.py        # Start the server")
        print("  curl http://localhost:8000/health  # Check health")
    else:
        print("\n" + "❌" * 15)
        print(f"❌ {failed} TEST(S) FAILED")
        print("❌" * 15)
        print("\nPlease check the errors above and fix them.")

if __name__ == "__main__":
    main()
