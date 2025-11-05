#!/usr/bin/env python3
"""
Test script for SkylitAI Desktop UI
"""
import sys
import pandas as pd
from schwab import get_underlying_price, get_options_chain, ACCESS_TOKEN
from core import compute_exposures
from config import ALL_TICKERS

def test_api_connection():
    """Test Schwab API connection"""
    print("🔍 Testing Schwab API connection...")
    
    if not ACCESS_TOKEN:
        print("❌ Schwab API token not available")
        return False
    
    try:
        # Test with SPY
        price = get_underlying_price("SPY")
        print(f"✅ SPY price: ${price:.2f}")
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_options_data():
    """Test options data retrieval"""
    print("\n🔍 Testing options data retrieval...")
    
    try:
        df = get_options_chain("SPY", n_expirations=2)
        if df.empty:
            print("❌ No options data retrieved")
            return False
        
        print(f"✅ Retrieved {len(df)} options contracts")
        print(f"   Expirations: {df['expiry'].unique()}")
        print(f"   Strike range: ${df['strike'].min():.0f} - ${df['strike'].max():.0f}")
        return True
    except Exception as e:
        print(f"❌ Options data retrieval failed: {e}")
        return False

def test_calculations():
    """Test Greek calculations"""
    print("\n🔍 Testing Greek calculations...")
    
    try:
        # Get sample data
        df = get_options_chain("SPY", n_expirations=1)
        if df.empty:
            print("❌ No data for calculations")
            return False
        
        # Test with first few rows
        sample_df = df.head(10).copy()
        price = get_underlying_price("SPY")
        
        # Compute exposures
        result_df = compute_exposures(sample_df, price)
        
        if 'GEX' not in result_df.columns or 'Vanna' not in result_df.columns:
            print("❌ Missing exposure calculations")
            return False
        
        print(f"✅ Calculated exposures for {len(result_df)} contracts")
        print(f"   GEX range: ${result_df['GEX'].min():,.0f} to ${result_df['GEX'].max():,.0f}")
        print(f"   Vanna range: ${result_df['Vanna'].min():,.0f} to ${result_df['Vanna'].max():,.0f}")
        return True
    except Exception as e:
        print(f"❌ Calculations failed: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    
    try:
        print(f"✅ Loaded {len(ALL_TICKERS)} tickers:")
        for ticker in ALL_TICKERS[:5]:  # Show first 5
            print(f"   {ticker.symbol} - {ticker.name}")
        if len(ALL_TICKERS) > 5:
            print(f"   ... and {len(ALL_TICKERS) - 5} more")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing SkylitAI Desktop UI Components\n")
    
    tests = [
        ("Configuration", test_config),
        ("API Connection", test_api_connection),
        ("Options Data", test_options_data),
        ("Calculations", test_calculations)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The SkylitAI app should work correctly.")
        print("\nTo run the app:")
        print("streamlit run app.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
