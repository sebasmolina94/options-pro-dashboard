# schwab.py - Schwab API integration for SkylitAI
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
try:
    import schwabdev
    SCHWABDEV_AVAILABLE = True
except ImportError:
    print("⚠️ schwabdev not available - using mock data")
    SCHWABDEV_AVAILABLE = False
    schwabdev = None

from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Schwab client
if SCHWABDEV_AVAILABLE:
    try:
        # Try Streamlit secrets first (for cloud deployment)
        try:
            import streamlit as st
            client_id = st.secrets["schwab"]["client_id"]
            client_secret = st.secrets["schwab"]["client_secret"]
            redirect_uri = st.secrets["schwab"]["redirect_uri"]
            print("Using Streamlit secrets for Schwab API")

            # Create tokens.json from secrets BEFORE creating client
            if "tokens" in st.secrets.get("schwab", {}):
                tokens = st.secrets["schwab"]["tokens"]
                import json
                token_data = {
                    "access_token_issued": tokens["access_token_issued"],
                    "refresh_token_issued": tokens["refresh_token_issued"],
                    "token_dictionary": {
                        "expires_in": 1800,
                        "token_type": "Bearer",
                        "scope": "api",
                        "refresh_token": tokens["refresh_token"],
                        "access_token": tokens["access_token"],
                        "id_token": ""
                    }
                }
                with open("tokens.json", "w") as f:
                    json.dump(token_data, f, indent=4)
                print("✅ Created tokens.json from Streamlit secrets")

        except Exception as e:
            print(f"Streamlit secrets error: {e}")
            # Fallback to environment variables (for local development)
            client_id = os.getenv('SCHWAB_APP_KEY')
            client_secret = os.getenv('SCHWAB_APP_SECRET')
            redirect_uri = os.getenv('SCHWAB_CALLBACK_URL')
            print("Using environment variables for Schwab API")

        # Now create client (should find tokens.json if it exists)
        client = schwabdev.Client(client_id, client_secret, redirect_uri)

        # Check token expiration and warn if refresh token is expiring soon
        try:
            if os.path.exists("tokens.json"):
                import json
                from datetime import datetime, timedelta
                with open("tokens.json", "r") as f:
                    token_data = json.load(f)

                refresh_issued = datetime.fromisoformat(token_data["refresh_token_issued"].replace('Z', '+00:00'))
                days_since_refresh = (datetime.now(refresh_issued.tzinfo) - refresh_issued).days

                if days_since_refresh >= 6:
                    print(f"⚠️ WARNING: Refresh token is {days_since_refresh} days old. Consider re-authenticating soon.")
                elif days_since_refresh >= 5:
                    print(f"📅 INFO: Refresh token is {days_since_refresh} days old. Will expire in {7-days_since_refresh} days.")
                else:
                    print(f"✅ Tokens are fresh ({days_since_refresh} days old)")
        except Exception as e:
            print(f"Could not check token age: {e}")

        ACCESS_TOKEN = True
    except Exception as e:
        print(f"Error initializing Schwab client: {e}")
        client = None
        ACCESS_TOKEN = False
else:
    print("⚠️ schwabdev not available - running in demo mode")
    client = None
    ACCESS_TOKEN = False

def refresh_tokens_if_needed():
    """Check if tokens need refreshing and provide instructions"""
    try:
        # Check if running on Streamlit Cloud (tokens in secrets) or local (tokens.json)
        if not os.path.exists("tokens.json"):
            # On Streamlit Cloud, tokens are in secrets, not files
            # Try to get token info from secrets if available
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'schwab' in st.secrets and 'tokens' in st.secrets.schwab:
                    refresh_issued_str = st.secrets.schwab.tokens.refresh_token_issued
                    from datetime import datetime
                    refresh_issued = datetime.fromisoformat(refresh_issued_str.replace('Z', '+00:00'))
                    days_since_refresh = (datetime.now(refresh_issued.tzinfo) - refresh_issued).days

                    if days_since_refresh >= 7:
                        return "🚨 EXPIRED: Tokens expired. Need full re-authentication."
                    elif days_since_refresh >= 6:
                        return f"⚠️ WARNING: Tokens expire in {7-days_since_refresh} day(s). Re-authenticate soon!"
                    elif days_since_refresh >= 5:
                        return f"📅 INFO: Tokens expire in {7-days_since_refresh} day(s)."
                    else:
                        return f"✅ Tokens are fresh ({days_since_refresh} days old, {7-days_since_refresh} days remaining)"
                else:
                    return "✅ Running on Streamlit Cloud with secrets"
            except:
                return "✅ Running on Streamlit Cloud"

        import json
        from datetime import datetime, timedelta
        with open("tokens.json", "r") as f:
            token_data = json.load(f)

        refresh_issued = datetime.fromisoformat(token_data["refresh_token_issued"].replace('Z', '+00:00'))
        days_since_refresh = (datetime.now(refresh_issued.tzinfo) - refresh_issued).days

        if days_since_refresh >= 7:
            return "🚨 EXPIRED: Tokens expired. Need full re-authentication."
        elif days_since_refresh >= 6:
            return f"⚠️ WARNING: Tokens expire in {7-days_since_refresh} day(s). Re-authenticate soon!"
        elif days_since_refresh >= 5:
            return f"📅 INFO: Tokens expire in {7-days_since_refresh} day(s)."
        else:
            return f"✅ Tokens are fresh ({days_since_refresh} days old, {7-days_since_refresh} days remaining)"

    except Exception as e:
        return f"✅ Token status check skipped"

def format_ticker(ticker, for_options_chain=False):
    """Format ticker for Schwab API

    Args:
        ticker: The ticker symbol
        for_options_chain: If True, use options-specific formatting
    """
    if not ticker:
        return ""
    ticker = ticker.upper()
    if ticker.startswith('/'):
        return ticker
    elif ticker in ['SPX', '$SPX']:
        # For SPX: Schwab uses $SPX for both underlying price and options chain
        return '$SPX'
    elif ticker in ['VIX', '$VIX']:
        return '$VIX'
    return ticker

def get_valid_expirations(ticker_config, n_expirations=4):
    """Get valid expiration dates based on ticker type"""
    from datetime import datetime, timedelta

    today = datetime.now().date()
    valid_expirations = []

    if ticker_config.has_daily_expirations:
        # For major indices/ETFs: current day + next 3 DTE
        print(f"Getting daily expirations for {ticker_config.symbol}")
        current_date = today
        days_added = 0

        while len(valid_expirations) < n_expirations:
            exp_date = current_date + timedelta(days=days_added)
            # Skip weekends for daily expirations
            if exp_date.weekday() < 5:  # Monday=0 to Friday=4
                valid_expirations.append(exp_date.strftime('%Y-%m-%d'))
            days_added += 1
    else:
        # For individual stocks: current week + next 3 weekly expirations
        print(f"Getting weekly expirations for {ticker_config.symbol}")

        # Find next Friday (weekly expiration day)
        days_until_friday = (4 - today.weekday()) % 7  # Friday = 4
        if days_until_friday == 0 and today.weekday() == 4:
            # If today is Friday, include it
            next_friday = today
        else:
            next_friday = today + timedelta(days=days_until_friday)

        # Get current week + next 3 weekly expirations
        for i in range(n_expirations):
            exp_date = next_friday + timedelta(weeks=i)
            valid_expirations.append(exp_date.strftime('%Y-%m-%d'))

    return valid_expirations

def get_underlying_price(ticker):
    """Get current underlying price"""
    if not SCHWABDEV_AVAILABLE or not ACCESS_TOKEN:
        # Return mock prices for demo mode
        mock_prices = {
            'SPY': 450.0, 'SPX': 6771.55, 'QQQ': 380.0, 'IWM': 200.0, 'AAPL': 180.0,
            'MSFT': 350.0, 'GOOGL': 140.0, 'AMZN': 150.0, 'TSLA': 250.0,
            'NVDA': 450.0, 'META': 320.0, '/ES': 4500.0, '/NQ': 15000.0
        }
        return mock_prices.get(ticker, 100.0)

    try:
        formatted_ticker = format_ticker(ticker)
        quote_response = client.quotes(formatted_ticker)
        if not quote_response.ok:
            return 100.0  # Default fallback
        quote = quote_response.json()
        if quote and formatted_ticker in quote:
            return float(quote[formatted_ticker]['quote']['lastPrice'])
        return 100.0
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return 100.0

def get_options_chain(ticker, n_expirations=4):
    """Get options chain data with smart filtering based on ticker type"""
    from config import ALL_TICKERS

    # Get ticker configuration
    ticker_config = next((t for t in ALL_TICKERS if t.symbol == ticker), None)
    if not ticker_config:
        print(f"Unknown ticker {ticker}, using default settings")
        ticker_config = type('Config', (), {'has_daily_expirations': False, 'symbol': ticker})()

    # Return mock data if schwabdev is not available
    if not SCHWABDEV_AVAILABLE or not ACCESS_TOKEN:
        print(f"⚠️ Using mock data for {ticker} options chain")
        return generate_sample_data(ticker, n_expirations)

    try:
        # Use different formatting for options chain vs underlying price
        options_ticker = format_ticker(ticker, for_options_chain=True)
        current_price = get_underlying_price(ticker)

        # Calculate strike range based on ticker type
        if ticker == "SPX":
            strike_range = 0.10  # ±10% for SPX (more focused range)
        else:
            strike_range = 0.30  # ±30% for other tickers (broader range)

        min_strike = current_price * (1 - strike_range)
        max_strike = current_price * (1 + strike_range)

        print(f"Fetching {ticker} options: Price=${current_price:.2f}, Strikes=${min_strike:.0f}-${max_strike:.0f}")

        # Get options chain with timeout handling
        chain_response = client.option_chains(
            symbol=options_ticker,
            contractType='ALL',
            strikeCount=50,  # Limit strikes to reduce data
            range='ITM'  # Focus on in-the-money and near-the-money
        )

        if not chain_response.ok:
            print(f"API response not OK for {ticker}: {chain_response.status_code}")
            print(f"Response text: {chain_response.text[:200]}...")
            return generate_sample_data(ticker, n_expirations)

        chain = chain_response.json()

        # Parse options data with filtering
        options_data = []
        valid_expirations = get_valid_expirations(ticker_config, n_expirations)

        print(f"Target expirations for {ticker}: {valid_expirations}")

        # Process calls
        if 'callExpDateMap' in chain:
            for exp_date, strikes in chain['callExpDateMap'].items():
                expiry = exp_date.split(':')[0]  # Get date part

                # Skip if not in our target expirations
                if expiry not in valid_expirations:
                    continue

                for strike_str, options in strikes.items():
                    strike = float(strike_str)

                    # Filter by strike range (±20%)
                    if strike < min_strike or strike > max_strike:
                        continue

                    for option in options:
                        # Include all options (even with 0 OI) - OI can be 0 after hours or for new strikes
                        # Only filter out options with no bid/ask (completely inactive)
                        bid = float(option.get('bid', 0))
                        ask = float(option.get('ask', 0))
                        if bid > 0 or ask > 0 or option.get('openInterest', 0) > 0:
                            options_data.append({
                                'symbol': option['symbol'],
                                'strike': strike,
                                'expiry': expiry,
                                'type': 'call',
                                'bid': float(option.get('bid', 0)),
                                'ask': float(option.get('ask', 0)),
                                'last': float(option.get('last', 0)),
                                'volume': int(option.get('totalVolume', 0)),
                                'openInterest': int(option.get('openInterest', 0)),
                                'impliedVolatility': float(option.get('volatility', 20.0)) / 100.0,  # API returns volatility as percentage
                                'delta': float(option.get('delta', 0)),
                                'gamma': float(option.get('gamma', 0)),
                                'theta': float(option.get('theta', 0)),
                                'vega': float(option.get('vega', 0))
                            })

        # Process puts
        if 'putExpDateMap' in chain:
            for exp_date, strikes in chain['putExpDateMap'].items():
                expiry = exp_date.split(':')[0]  # Get date part

                # Skip if not in our target expirations
                if expiry not in valid_expirations:
                    continue

                for strike_str, options in strikes.items():
                    strike = float(strike_str)

                    # Filter by strike range (±20%)
                    if strike < min_strike or strike > max_strike:
                        continue

                    for option in options:
                        # Include all options (even with 0 OI) - OI can be 0 after hours or for new strikes
                        # Only filter out options with no bid/ask (completely inactive)
                        bid = float(option.get('bid', 0))
                        ask = float(option.get('ask', 0))
                        if bid > 0 or ask > 0 or option.get('openInterest', 0) > 0:
                            options_data.append({
                                'symbol': option['symbol'],
                                'strike': strike,
                                'expiry': expiry,
                                'type': 'put',
                                'bid': float(option.get('bid', 0)),
                                'ask': float(option.get('ask', 0)),
                                'last': float(option.get('last', 0)),
                                'volume': int(option.get('totalVolume', 0)),
                                'openInterest': int(option.get('openInterest', 0)),
                                'impliedVolatility': float(option.get('volatility', 20.0)) / 100.0,  # API returns volatility as percentage
                                'delta': float(option.get('delta', 0)),
                                'gamma': float(option.get('gamma', 0)),
                                'theta': float(option.get('theta', 0)),
                                'vega': float(option.get('vega', 0))
                            })

        df = pd.DataFrame(options_data)
        if df.empty:
            print(f"No options data found for {ticker}, generating sample data")
            return generate_sample_data(ticker, n_expirations)

        # Sort by expiry and return top n_expirations
        df['exp_dt'] = pd.to_datetime(df['expiry'])
        df = df.sort_values('exp_dt')

        # Get unique expirations and limit to n_expirations
        unique_expirations = df['expiry'].unique()[:n_expirations]
        df = df[df['expiry'].isin(unique_expirations)]

        return df

    except Exception as e:
        print(f"Error fetching options chain for {ticker}: {e}")
        print(f"Falling back to sample data for demonstration")
        return generate_sample_data(ticker, n_expirations)

def generate_sample_data(ticker, n_expirations=4):
    """Generate sample options data for demonstration using same logic as real data"""
    from datetime import datetime, timedelta
    import numpy as np
    from config import ALL_TICKERS

    # Get ticker configuration
    ticker_config = next((t for t in ALL_TICKERS if t.symbol == ticker), None)
    if not ticker_config:
        ticker_config = type('Config', (), {'has_daily_expirations': False, 'symbol': ticker})()

    # Get current price for strike generation
    try:
        current_price = get_underlying_price(ticker)
        # If we got the real price, use it even if options chain fails
        if current_price != 100.0:
            print(f"Using real price for {ticker}: ${current_price:.2f}")
    except:
        current_price = 100.0

    # Use same expiration logic as real data
    expirations = get_valid_expirations(ticker_config, n_expirations)

    # Generate strikes with appropriate range based on ticker
    if ticker == "SPX":
        strike_range = 0.10  # ±10% for SPX (more focused range)
    else:
        strike_range = 0.30  # ±30% for other tickers (broader range)

    min_strike = current_price * (1 - strike_range)
    max_strike = current_price * (1 + strike_range)

    # Generate strikes with appropriate increments based on ticker
    if ticker == "SPY":
        strike_increment = 1.0  # SPY uses $1.00 increments
    elif ticker == "SPX":
        strike_increment = 5.0  # SPX uses $5.00 increments
    else:
        strike_increment = 1.0  # Default to $1.00 for most tickers

    strikes = []
    # Generate strikes using proper increments
    # Start from the nearest increment below min_strike
    start_strike = (int(min_strike / strike_increment) * strike_increment)
    current_strike = start_strike

    while current_strike <= max_strike and len(strikes) < 25:  # Limit to reasonable number
        if current_strike >= min_strike:  # Only include strikes in our range
            strikes.append(current_strike)
        current_strike += strike_increment

    print(f"Sample data: {ticker} Price=${current_price:.2f}, Strikes=${min_strike:.0f}-${max_strike:.0f}, Expirations={expirations}")

    options_data = []

    # Generate sample data for each expiry and strike
    for expiry in expirations:
        for strike in strikes:
            # Generate calls
            call_oi = np.random.randint(50, 1000)
            call_vol = max(0.1, np.random.normal(0.25, 0.1))

            options_data.append({
                'symbol': f'{ticker}_{expiry}C{strike}',
                'strike': strike,
                'expiry': expiry,
                'type': 'call',
                'bid': max(0.01, np.random.uniform(0.5, 5.0)),
                'ask': max(0.02, np.random.uniform(0.6, 5.5)),
                'last': max(0.01, np.random.uniform(0.5, 5.2)),
                'volume': np.random.randint(0, 500),
                'openInterest': call_oi,
                'impliedVolatility': call_vol,
                'delta': 0.0,  # Will be calculated
                'gamma': 0.0,  # Will be calculated
                'theta': 0.0,  # Will be calculated
                'vega': 0.0    # Will be calculated
            })

            # Generate puts
            put_oi = np.random.randint(50, 1000)
            put_vol = max(0.1, np.random.normal(0.25, 0.1))

            options_data.append({
                'symbol': f'{ticker}_{expiry}P{strike}',
                'strike': strike,
                'expiry': expiry,
                'type': 'put',
                'bid': max(0.01, np.random.uniform(0.5, 5.0)),
                'ask': max(0.02, np.random.uniform(0.6, 5.5)),
                'last': max(0.01, np.random.uniform(0.5, 5.2)),
                'volume': np.random.randint(0, 500),
                'openInterest': put_oi,
                'impliedVolatility': put_vol,
                'delta': 0.0,  # Will be calculated
                'gamma': 0.0,  # Will be calculated
                'theta': 0.0,  # Will be calculated
                'vega': 0.0    # Will be calculated
            })

    df = pd.DataFrame(options_data)

    # Ensure proper data types
    numeric_columns = ['strike', 'bid', 'ask', 'last', 'volume', 'openInterest',
                      'impliedVolatility', 'delta', 'gamma', 'theta', 'vega']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    print(f"Generated {len(df)} sample options contracts for {ticker}")
    return df
