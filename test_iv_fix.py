#!/usr/bin/env python3
"""
Test script to debug the IV issue completely fresh
"""

from dotenv import load_dotenv
load_dotenv()

import os
import pandas as pd
from schwabdev import Client
from datetime import datetime, timedelta

def get_amzn_options_fresh():
    """Get AMZN options with corrected IV parsing"""
    
    # Initialize client
    app_key = os.getenv('SCHWAB_APP_KEY')
    app_secret = os.getenv('SCHWAB_APP_SECRET')
    callback_url = os.getenv('SCHWAB_CALLBACK_URL')
    
    if not all([app_key, app_secret, callback_url]):
        print("Missing API credentials")
        return pd.DataFrame()
    
    try:
        client = Client(app_key, app_secret, callback_url, 'tokens.json')
        
        # Get options chain
        response = client.option_chains(
            symbol='AMZN',
            contractType='ALL',
            strikeCount=10
        )
        
        if not response.ok:
            print(f"API Error: {response.status_code}")
            return pd.DataFrame()
        
        chain = response.json()
        options_data = []
        
        # Process calls
        if 'callExpDateMap' in chain:
            for exp_date, strikes in chain['callExpDateMap'].items():
                expiry = exp_date.split(':')[0]  # Get date part
                
                for strike_str, options in strikes.items():
                    strike = float(strike_str)
                    
                    for option in options:
                        raw_iv = option.get('volatility', 200.0)
                        
                        # TEST DIFFERENT CONVERSIONS
                        iv_div_100 = raw_iv / 100.0
                        iv_div_1000 = raw_iv / 1000.0
                        
                        options_data.append({
                            'symbol': option['symbol'],
                            'strike': strike,
                            'expiry': expiry,
                            'type': 'call',
                            'openInterest': int(option.get('openInterest', 0)),
                            'raw_iv': raw_iv,
                            'iv_div_100': iv_div_100,
                            'iv_div_1000': iv_div_1000,
                        })
                        
                        # Only process first few for testing
                        if len(options_data) >= 5:
                            break
                    if len(options_data) >= 5:
                        break
                if len(options_data) >= 5:
                    break
        
        return pd.DataFrame(options_data)
        
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    print("=== FRESH IV DEBUGGING ===")
    
    df = get_amzn_options_fresh()
    
    if not df.empty:
        print("Raw API data with different IV conversions:")
        print()
        
        for _, row in df.iterrows():
            print(f"Strike ${row['strike']:.0f} {row['type']}:")
            print(f"  Raw IV from API: {row['raw_iv']}")
            print(f"  ÷ 100: {row['iv_div_100']:.4f} ({row['iv_div_100']:.1%})")
            print(f"  ÷ 1000: {row['iv_div_1000']:.4f} ({row['iv_div_1000']:.1%})")
            print(f"  OI: {row['openInterest']:,}")
            print()
            
        print("Which conversion gives reasonable IV for AMZN (15-30%)?")
        
    else:
        print("No data retrieved")
