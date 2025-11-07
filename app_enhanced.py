# app_enhanced.py - Options Pro Desktop UI with OI and Volume Tabs
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from core_enhanced import compute_exposures_dual, black_scholes_greeks
from schwab import get_options_chain, get_underlying_price, ACCESS_TOKEN, refresh_tokens_if_needed
from config import ALL_TICKERS
from trading_plan import generate_trading_plan, get_key_levels

# --------------------------------------------------------------
# Unusual Activity Detection Functions
# --------------------------------------------------------------
def detect_unusual_activity(df, ticker):
    """Detect unusual options activity patterns"""
    if df.empty:
        return []

    alerts = []

    # Calculate volume/OI ratios
    df['vol_oi_ratio'] = df['volume'] / (df['openInterest'] + 1)  # +1 to avoid division by zero

    # High volume/OI ratio (>2.0 is unusual)
    high_vol_oi = df[df['vol_oi_ratio'] > 2.0].copy()
    if not high_vol_oi.empty:
        for _, row in high_vol_oi.head(3).iterrows():
            alerts.append({
                'type': '🔥 High Vol/OI Ratio',
                'message': f"${row['strike']:.1f} {row['type']} - Vol/OI: {row['vol_oi_ratio']:.1f}x (Vol: {row['volume']:,}, OI: {row['openInterest']:,})",
                'severity': 'high' if row['vol_oi_ratio'] > 5.0 else 'medium'
            })

    # Large single option positions (>10k volume or >50k OI)
    large_volume = df[df['volume'] > 10000]
    if not large_volume.empty:
        for _, row in large_volume.head(2).iterrows():
            alerts.append({
                'type': '📈 Large Volume',
                'message': f"${row['strike']:.0f} {row['type']} - {row['volume']:,} contracts traded",
                'severity': 'high'
            })

    large_oi = df[df['openInterest'] > 50000]
    if not large_oi.empty:
        for _, row in large_oi.head(2).iterrows():
            alerts.append({
                'type': '🏗️ Large Open Interest',
                'message': f"${row['strike']:.1f} {row['type']} - {row['openInterest']:,} contracts open",
                'severity': 'medium'
            })

    # Unusual IV (>100% or <5%)
    high_iv = df[df['impliedVolatility'] > 1.0]  # >100%
    if not high_iv.empty:
        for _, row in high_iv.head(2).iterrows():
            alerts.append({
                'type': '⚡ High Implied Volatility',
                'message': f"${row['strike']:.0f} {row['type']} - IV: {row['impliedVolatility']:.1%}",
                'severity': 'medium'
            })

    return alerts[:8]  # Limit to 8 alerts

def display_unusual_activity(alerts):
    """Display unusual activity alerts"""
    if not alerts:
        st.info("🟢 No unusual activity detected")
        return

    st.markdown("### 🚨 **Unusual Activity Alerts**")

    for alert in alerts:
        if alert['severity'] == 'high':
            st.error(f"**{alert['type']}**: {alert['message']}")
        elif alert['severity'] == 'medium':
            st.warning(f"**{alert['type']}**: {alert['message']}")
        else:
            st.info(f"**{alert['type']}**: {alert['message']}")

def get_earnings_calendar():
    """Enhanced earnings calendar with 1-month forward view using Yahoo Finance API

    Uses persistent file-based caching to avoid API calls more than once per day.
    Only fetches new data if cache file is older than 24 hours or doesn't exist.
    """
    from datetime import datetime, timedelta
    import os
    import json
    from dotenv import load_dotenv

    try:
        import yfinance as yf
        YFINANCE_AVAILABLE = True
    except ImportError:
        print("⚠️ yfinance not available - earnings calendar disabled")
        YFINANCE_AVAILABLE = False

    # Load environment variables
    load_dotenv()

    # Cache file path
    cache_file = "earnings_cache.json"

    # Check if cache file exists and is less than 24 hours old
    if os.path.exists(cache_file):
        try:
            cache_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            if cache_age < 86400:  # Less than 24 hours (86400 seconds)
                print(f"📋 Using cached earnings data (cache age: {cache_age/3600:.1f} hours)")
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    return cached_data.get('earnings_data', {})
        except Exception as e:
            print(f"⚠️ Error reading cache file: {e}")
            # Continue to fetch fresh data if cache read fails

    # Get current date and next 30 days
    today = datetime.now().date()
    future_date = today + timedelta(days=30)

    # Check if yfinance is available and user wants to use real data
    USE_REAL_DATA = YFINANCE_AVAILABLE and os.getenv('FMP_API_KEY') and os.getenv('FMP_API_KEY') != "YOUR_FMP_API_KEY_HERE"

    if not YFINANCE_AVAILABLE:
        print("⚠️ yfinance not available - earnings calendar disabled")
        return {}
    elif not USE_REAL_DATA:
        print("⚠️ Real earnings data disabled, using sample data")
        return get_sample_earnings_data()

    try:
        print(f"📡 Fetching real earnings data from Yahoo Finance...")

        # Get our ticker list - filter out ETFs and indices that don't have earnings
        from config import ALL_TICKERS
        ticker_symbols = [t.symbol for t in ALL_TICKERS]

        # Filter out ETFs and indices that don't have earnings calendars
        etfs_and_indices = {'SPY', 'QQQ', 'IWM', 'VIX', 'XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLRE', 'XLU', 'GLD', 'SLV', 'TLT', 'HYG', 'LQD', 'EEM', 'FXI', 'EWJ', 'EWZ', 'RSX', 'GDXJ', 'GDX', 'XOP', 'XBI', 'IBB', 'XRT', 'IYR', 'KRE', 'SMH', 'SOXX', 'ARKK', 'ARKQ', 'ARKG', 'ARKW', 'ARKF'}
        company_tickers = [symbol for symbol in ticker_symbols if symbol not in etfs_and_indices]

        # Prioritize high-profile tickers that often have earnings (move to front)
        priority_tickers = ['PLTR', 'HIMS', 'RDDT', 'RBLX', 'COIN', 'HOOD', 'RIVN', 'ABNB', 'UBER', 'SPOT']

        # Reorder: priority tickers first, then the rest
        prioritized_tickers = []
        for ticker in priority_tickers:
            if ticker in company_tickers:
                prioritized_tickers.append(ticker)

        # Add remaining tickers (excluding those already added)
        for ticker in company_tickers:
            if ticker not in prioritized_tickers:
                prioritized_tickers.append(ticker)

        earnings_data = {}
        successful_fetches = 0

        # Fetch earnings for each company ticker (limit to first 50 to include priority tickers)
        for i, symbol in enumerate(prioritized_tickers[:50]):  # Increased limit to include priority tickers
            try:
                ticker = yf.Ticker(symbol)
                calendar = ticker.calendar

                if calendar is not None and isinstance(calendar, dict) and 'Earnings Date' in calendar:
                    earnings_dates = calendar['Earnings Date']
                    if earnings_dates and len(earnings_dates) > 0:
                        # Get the next earnings date (first in the list)
                        earnings_date = earnings_dates[0]

                        # Only include if within next 30 days
                        days_until = (earnings_date - today).days
                        if 0 <= days_until <= 30:
                            # Determine quarter based on current date
                            year = earnings_date.year
                            month = earnings_date.month

                            if month in [1, 2, 3]:
                                quarter = f"Q4 {year-1}"
                            elif month in [4, 5, 6]:
                                quarter = f"Q1 {year}"
                            elif month in [7, 8, 9]:
                                quarter = f"Q2 {year}"
                            else:
                                quarter = f"Q3 {year}"

                            # Default to AMC (most earnings are after market close)
                            earnings_data[symbol] = {
                                'date': earnings_date.strftime('%Y-%m-%d'),
                                'time': 'AMC',
                                'quarter': quarter
                            }
                            successful_fetches += 1

                            if successful_fetches % 10 == 0:
                                print(f"📊 Fetched {successful_fetches} earnings so far...")

            except Exception as e:
                # Skip individual ticker errors (but don't print them to avoid spam)
                continue

        if earnings_data:
            print(f"✅ Successfully fetched {len(earnings_data)} real earnings from Yahoo Finance")

            # Save to cache file for future use
            try:
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'earnings_data': earnings_data
                }
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                print(f"💾 Cached earnings data for next 24 hours")
            except Exception as cache_error:
                print(f"⚠️ Warning: Could not save cache file: {cache_error}")

            return earnings_data
        else:
            print("⚠️ No real earnings data found, using sample data")
            return get_sample_earnings_data()

    except Exception as e:
        print(f"❌ Error fetching earnings data: {e}")
        print("📋 Falling back to sample data")
        return get_sample_earnings_data()

def get_sample_earnings_data():
    """Fallback sample earnings data when API is not available"""
    # SAMPLE/DEMO DATA - Used as fallback when API is not configured
    earnings_data = {
        # Week 1 (Nov 4-8, 2025)
        'AAPL': {'date': '2025-11-07', 'time': 'AMC', 'quarter': 'Q4 2025'},
        'MSFT': {'date': '2025-11-06', 'time': 'AMC', 'quarter': 'Q1 2026'},
        'GOOGL': {'date': '2025-11-05', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'AMZN': {'date': '2025-11-07', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'META': {'date': '2025-11-06', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'TSLA': {'date': '2025-11-05', 'time': 'AMC', 'quarter': 'Q3 2025'},

        # Week 2 (Nov 11-15, 2025)
        'NVDA': {'date': '2025-11-13', 'time': 'AMC', 'quarter': 'Q3 2026'},
        'NFLX': {'date': '2025-11-12', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'DIS': {'date': '2025-11-14', 'time': 'AMC', 'quarter': 'Q4 2025'},
        'PYPL': {'date': '2025-11-12', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'UBER': {'date': '2025-11-13', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'ABNB': {'date': '2025-11-15', 'time': 'AMC', 'quarter': 'Q3 2025'},

        # Week 3 (Nov 18-22, 2025)
        'WMT': {'date': '2025-11-19', 'time': 'BMO', 'quarter': 'Q3 2026'},
        'TGT': {'date': '2025-11-20', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'HD': {'date': '2025-11-19', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'COST': {'date': '2025-11-21', 'time': 'AMC', 'quarter': 'Q1 2026'},
        'DDOG': {'date': '2025-11-21', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'SNOW': {'date': '2025-11-20', 'time': 'AMC', 'quarter': 'Q3 2026'},

        # Week 4 (Nov 25-29, 2025) - Thanksgiving week
        'DELL': {'date': '2025-11-26', 'time': 'AMC', 'quarter': 'Q3 2026'},
        'HPQ': {'date': '2025-11-26', 'time': 'AMC', 'quarter': 'Q4 2025'},

        # December Preview (Dec 2-6, 2025)
        'CRM': {'date': '2025-12-03', 'time': 'AMC', 'quarter': 'Q3 2026'},
        'OKTA': {'date': '2025-12-04', 'time': 'AMC', 'quarter': 'Q3 2026'},
        'CRWD': {'date': '2025-12-05', 'time': 'AMC', 'quarter': 'Q3 2026'},
        'ZS': {'date': '2025-12-05', 'time': 'AMC', 'quarter': 'Q1 2026'},
        'PANW': {'date': '2025-12-06', 'time': 'AMC', 'quarter': 'Q1 2026'},

        # Additional high-volume tickers
        'AMD': {'date': '2025-11-08', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'INTC': {'date': '2025-11-08', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'AVGO': {'date': '2025-11-14', 'time': 'AMC', 'quarter': 'Q4 2025'},
        'ORCL': {'date': '2025-11-11', 'time': 'AMC', 'quarter': 'Q2 2026'},
        'ADBE': {'date': '2025-11-15', 'time': 'AMC', 'quarter': 'Q4 2025'},
        'NOW': {'date': '2025-11-13', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'WDAY': {'date': '2025-11-21', 'time': 'AMC', 'quarter': 'Q3 2026'},
        'NET': {'date': '2025-11-14', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'MDB': {'date': '2025-11-21', 'time': 'AMC', 'quarter': 'Q3 2026'},

        # Financial sector
        'JPM': {'date': '2025-11-12', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'BAC': {'date': '2025-11-12', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'GS': {'date': '2025-11-13', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'MS': {'date': '2025-11-13', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'V': {'date': '2025-11-14', 'time': 'AMC', 'quarter': 'Q4 2025'},
        'MA': {'date': '2025-11-14', 'time': 'BMO', 'quarter': 'Q3 2025'},

        # Healthcare & Pharma
        'JNJ': {'date': '2025-11-19', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'PFE': {'date': '2025-11-19', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'ABBV': {'date': '2025-11-20', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'LLY': {'date': '2025-11-20', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'UNH': {'date': '2025-11-21', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'MRNA': {'date': '2025-11-21', 'time': 'AMC', 'quarter': 'Q3 2025'},
        'REGN': {'date': '2025-11-22', 'time': 'BMO', 'quarter': 'Q3 2025'},

        # Industrial & Energy
        'CAT': {'date': '2025-11-26', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'DE': {'date': '2025-11-26', 'time': 'BMO', 'quarter': 'Q4 2025'},
        'MMM': {'date': '2025-11-27', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'HON': {'date': '2025-11-27', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'LMT': {'date': '2025-11-28', 'time': 'BMO', 'quarter': 'Q3 2025'},

        # Consumer & Retail
        'KO': {'date': '2025-11-25', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'PEP': {'date': '2025-11-25', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'MCD': {'date': '2025-11-26', 'time': 'BMO', 'quarter': 'Q3 2025'},
        'SBUX': {'date': '2025-11-27', 'time': 'AMC', 'quarter': 'Q4 2025'},
    }

    return earnings_data

def get_real_earnings_calendar():
    """Example function showing how to integrate with real earnings APIs

    This is a template for connecting to real earnings data sources.
    Uncomment and configure with your API keys to use real data.
    """

    # Example 1: Alpha Vantage Earnings Calendar
    # Requires: pip install requests
    # API Key: Get free key from https://www.alphavantage.co/support/#api-key
    """
    import requests

    API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"  # Replace with your API key
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={API_KEY}"

    try:
        response = requests.get(url)
        # Parse CSV response and convert to our format
        # Implementation details depend on API response format
        pass
    except Exception as e:
        print(f"Error fetching earnings data: {e}")
    """

    # Example 2: Yahoo Finance using yfinance
    # Requires: pip install yfinance
    """
    try:
        import yfinance as yf
    except ImportError:
        return {}
    from datetime import datetime, timedelta

    earnings_data = {}
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # Your ticker list

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            if calendar is not None and not calendar.empty:
                # Extract earnings date and format for our calendar
                earnings_date = calendar.index[0].strftime('%Y-%m-%d')
                earnings_data[ticker] = {
                    'date': earnings_date,
                    'time': 'AMC',  # Default, would need to determine actual time
                    'quarter': 'Q3 2024'  # Would need to calculate based on date
                }
        except Exception as e:
            print(f"Error fetching {ticker} earnings: {e}")

    return earnings_data
    """

    # Example 3: Financial Modeling Prep API
    # Requires: pip install requests
    """
    import requests
    from datetime import datetime, timedelta

    API_KEY = "YOUR_FMP_API_KEY"  # Get from https://financialmodelingprep.com/
    today = datetime.now().strftime('%Y-%m-%d')
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    url = f"https://financialmodelingprep.com/api/v3/earning_calendar?from={today}&to={future_date}&apikey={API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        earnings_data = {}
        for earning in data:
            ticker = earning.get('symbol')
            date = earning.get('date')
            time = earning.get('time', 'AMC')

            if ticker and date:
                earnings_data[ticker] = {
                    'date': date,
                    'time': time,
                    'quarter': f"Q{earning.get('quarter', '?')} {earning.get('year', '?')}"
                }

        return earnings_data
    except Exception as e:
        print(f"Error fetching earnings data: {e}")
        return {}
    """

    # For now, return empty dict since this is just a template
    return {}

def display_earnings_info(ticker):
    """Display earnings information for the selected ticker"""
    earnings_data = get_earnings_calendar()

    if ticker in earnings_data:
        earnings_info = earnings_data[ticker]
        earnings_date = datetime.strptime(earnings_info['date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        days_until = (earnings_date - today).days

        if days_until >= 0 and days_until <= 14:  # Show if within 2 weeks
            if days_until == 0:
                st.error(f"📅 **{ticker} EARNINGS TODAY** - {earnings_info['time']} ({earnings_info['quarter']})")
            elif days_until <= 3:
                st.warning(f"📅 **{ticker} Earnings in {days_until} days** - {earnings_date} {earnings_info['time']} ({earnings_info['quarter']})")
            else:
                st.info(f"📅 **{ticker} Earnings**: {earnings_date} {earnings_info['time']} ({earnings_info['quarter']}) - {days_until} days")

            return True
    return False

def display_earnings_calendar():
    """Display comprehensive 1-month earnings calendar"""
    from datetime import datetime, timedelta
    import pandas as pd

    st.markdown("---")
    st.markdown("## 📅 **Upcoming Earnings Calendar (Next 30 Days)**")
    st.markdown("*Plan your options strategies around earnings announcements*")

    # Check if we're using real or sample data
    import os
    from dotenv import load_dotenv
    load_dotenv()

    USE_REAL_DATA = os.getenv('FMP_API_KEY') and os.getenv('FMP_API_KEY') != "YOUR_FMP_API_KEY_HERE"
    if not USE_REAL_DATA:
        st.warning("""
        ⚠️ **SAMPLE DATA MODE**: Using demonstration data. To enable real earnings data,
        set FMP_API_KEY in the .env file (any value will enable Yahoo Finance integration).
        """)
    else:
        st.success("""
        ✅ **LIVE DATA MODE**: Using real earnings data from Yahoo Finance API.
        """)
        st.info("📡 Fetching latest earnings data from Yahoo Finance... (updates every app refresh)")


    earnings_data = get_earnings_calendar()
    today = datetime.now().date()

    # Filter earnings for next 30 days and organize by date
    upcoming_earnings = []
    for ticker, info in earnings_data.items():
        earnings_date = datetime.strptime(info['date'], '%Y-%m-%d').date()
        days_until = (earnings_date - today).days

        if 0 <= days_until <= 30:  # Next 30 days
            upcoming_earnings.append({
                'Date': earnings_date,
                'Ticker': ticker,
                'Time': info['time'],
                'Quarter': info['quarter'],
                'Days Until': days_until,
                'Day of Week': earnings_date.strftime('%A')
            })

    if not upcoming_earnings:
        st.info("No earnings scheduled for the next 30 days.")
        return

    # Sort by date
    upcoming_earnings.sort(key=lambda x: x['Date'])

    # Group by week for better organization
    current_week = []
    weeks = []
    current_week_start = None

    for earning in upcoming_earnings:
        # Get Monday of the week for this earning
        earning_date = earning['Date']
        days_since_monday = earning_date.weekday()
        week_start = earning_date - timedelta(days=days_since_monday)

        if current_week_start != week_start:
            if current_week:
                weeks.append((current_week_start, current_week))
            current_week = []
            current_week_start = week_start

        current_week.append(earning)

    # Add the last week
    if current_week:
        weeks.append((current_week_start, current_week))

    # Display by weeks
    for week_start, week_earnings in weeks:
        week_end = week_start + timedelta(days=6)
        week_label = f"Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}"

        with st.expander(f"📊 **{week_label}** ({len(week_earnings)} earnings)", expanded=False):
            # Create columns for better layout
            cols = st.columns([2, 1, 1, 2, 1, 1])

            # Headers
            cols[0].markdown("**📈 Ticker**")
            cols[1].markdown("**📅 Date**")
            cols[2].markdown("**🕐 Time**")
            cols[3].markdown("**📊 Quarter**")
            cols[4].markdown("**⏰ Days**")
            cols[5].markdown("**📆 Day**")

            # Add separator
            st.markdown("---")

            for earning in week_earnings:
                cols = st.columns([2, 1, 1, 2, 1, 1])

                # Color code based on urgency
                if earning['Days Until'] == 0:
                    ticker_color = "🔴"
                    urgency_color = "#ff4444"
                elif earning['Days Until'] <= 3:
                    ticker_color = "🟡"
                    urgency_color = "#ffaa00"
                elif earning['Days Until'] <= 7:
                    ticker_color = "🟢"
                    urgency_color = "#44aa44"
                else:
                    ticker_color = "🔵"
                    urgency_color = "#4444ff"

                # Display earning info
                cols[0].markdown(f"{ticker_color} **{earning['Ticker']}**")
                cols[1].markdown(f"{earning['Date'].strftime('%m/%d')}")

                # Time with explanation
                time_text = earning['Time']
                if time_text == 'AMC':
                    time_display = "AMC (After Close)"
                elif time_text == 'BMO':
                    time_display = "BMO (Before Open)"
                else:
                    time_display = time_text
                cols[2].markdown(f"{time_display}")

                cols[3].markdown(f"{earning['Quarter']}")
                cols[4].markdown(f"<span style='color: {urgency_color}; font-weight: bold;'>{earning['Days Until']}</span>", unsafe_allow_html=True)
                cols[5].markdown(f"{earning['Day of Week'][:3]}")

    # Summary statistics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        today_earnings = [e for e in upcoming_earnings if e['Days Until'] == 0]
        st.metric("📅 Today", len(today_earnings))

    with col2:
        this_week_earnings = [e for e in upcoming_earnings if e['Days Until'] <= 7]
        st.metric("📊 This Week", len(this_week_earnings))

    with col3:
        next_week_earnings = [e for e in upcoming_earnings if 7 < e['Days Until'] <= 14]
        st.metric("📈 Next Week", len(next_week_earnings))

    with col4:
        total_earnings = len(upcoming_earnings)
        st.metric("🎯 Total (30d)", total_earnings)

    # Trading tips
    st.markdown("---")
    st.markdown("### 💡 **Options Trading Tips for Earnings**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🎯 Pre-Earnings Strategies:**
        - **Long Straddles/Strangles**: Bet on volatility
        - **Iron Condors**: Sell high IV before earnings
        - **Calendar Spreads**: Benefit from IV crush
        - **Protective Puts**: Hedge existing positions
        """)

    with col2:
        st.markdown("""
        **⚠️ Key Considerations:**
        - **IV Crush**: Options lose value after earnings
        - **Timing**: Enter 1-2 weeks before earnings
        - **Liquidity**: Stick to high-volume tickers
        - **Direction**: Consider analyst expectations
        """)



# --------------------------------------------------------------
# Page config – full desktop, dark theme
# --------------------------------------------------------------
st.set_page_config(
    page_title="Options Pro • Dealer Positioning Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Premium Options Pro styling with stunning visual effects
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Main app styling with animated gradient background */
    .main {
        background: linear-gradient(-45deg, #0a0a0a, #1a1a2e, #16213e, #0f0f23);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        min-height: 100vh;
    }
    .stApp {
        background: transparent;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Premium header styling with glow effects */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
        letter-spacing: -0.02em;
    }

    /* Premium dropdown styling with glass morphism */
    .stSelectbox > div > div {
        background: rgba(26, 26, 26, 0.8);
        backdrop-filter: blur(20px);
        color: #ffffff;
        border: 1px solid rgba(74, 222, 128, 0.2);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    .stSelectbox > div > div:hover {
        border-color: rgba(74, 222, 128, 0.4);
        box-shadow: 0 12px 40px rgba(74, 222, 128, 0.1);
        transform: translateY(-2px);
    }

    /* Premium label styling */
    .stSelectbox label {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        margin-bottom: 8px !important;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.3);
    }

    /* Main selectbox container with premium effects */
    .stSelectbox > div > div[data-baseweb="select"] {
        font-size: 20px !important;
        font-weight: 600 !important;
        min-height: 60px !important;
        padding: 18px 24px !important;
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.9), rgba(42, 42, 42, 0.9)) !important;
        border: 2px solid rgba(74, 222, 128, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease !important;
    }

    .stSelectbox > div > div[data-baseweb="select"]:hover {
        border-color: rgba(74, 222, 128, 0.5) !important;
        box-shadow: 0 12px 40px rgba(74, 222, 128, 0.15) !important;
        transform: translateY(-2px) !important;
    }

    /* Selected value text with glow */
    .stSelectbox > div > div[data-baseweb="select"] > div {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #ffffff !important;
        line-height: 1.2 !important;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.2);
    }

    /* Dropdown arrow with animation */
    .stSelectbox > div > div[data-baseweb="select"] svg {
        width: 24px !important;
        height: 24px !important;
        transition: transform 0.3s ease !important;
        filter: drop-shadow(0 0 5px rgba(74, 222, 128, 0.3));
    }

    .stSelectbox > div > div[data-baseweb="select"]:hover svg {
        transform: rotate(180deg) !important;
    }

    /* Premium heatmap colors with glow effects */
    .positive {
        background: linear-gradient(135deg, rgba(26, 77, 26, 0.8), rgba(34, 197, 94, 0.2)) !important;
        color: #4ade80 !important;
        font-weight: 600;
        border: 1px solid rgba(74, 222, 128, 0.3);
        box-shadow: 0 0 15px rgba(74, 222, 128, 0.2);
        transition: all 0.3s ease;
    }
    .positive:hover {
        box-shadow: 0 0 25px rgba(74, 222, 128, 0.4);
        transform: scale(1.02);
    }

    .negative {
        background: linear-gradient(135deg, rgba(77, 26, 26, 0.8), rgba(239, 68, 68, 0.2)) !important;
        color: #f87171 !important;
        font-weight: 600;
        border: 1px solid rgba(248, 113, 113, 0.3);
        box-shadow: 0 0 15px rgba(248, 113, 113, 0.2);
        transition: all 0.3s ease;
    }
    .negative:hover {
        box-shadow: 0 0 25px rgba(248, 113, 113, 0.4);
        transform: scale(1.02);
    }

    .highlight {
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.8), rgba(59, 130, 246, 0.3)) !important;
        color: #93c5fd !important;
        font-weight: bold;
        border: 2px solid #3b82f6;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.4); }
        50% { box-shadow: 0 0 30px rgba(59, 130, 246, 0.6); }
    }

    .highest-positive {
        background: linear-gradient(135deg, rgba(202, 138, 4, 0.8), rgba(251, 191, 36, 0.3)) !important;
        color: #fbbf24 !important;
        font-weight: bold;
        border: 2px solid #eab308;
        box-shadow: 0 0 25px rgba(234, 179, 8, 0.5);
        animation: goldGlow 3s ease-in-out infinite;
    }

    @keyframes goldGlow {
        0%, 100% { box-shadow: 0 0 25px rgba(234, 179, 8, 0.5); }
        50% { box-shadow: 0 0 35px rgba(234, 179, 8, 0.7); }
    }

    .highest-negative {
        background: linear-gradient(135deg, rgba(124, 45, 146, 0.8), rgba(192, 132, 252, 0.3)) !important;
        color: #c084fc !important;
        font-weight: bold;
        border: 2px solid #a855f7;
        box-shadow: 0 0 25px rgba(168, 85, 247, 0.5);
        animation: purpleGlow 3s ease-in-out infinite;
    }

    @keyframes purpleGlow {
        0%, 100% { box-shadow: 0 0 25px rgba(168, 85, 247, 0.5); }
        50% { box-shadow: 0 0 35px rgba(168, 85, 247, 0.7); }
    }

    /* Premium tab styling with glass morphism */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(26, 26, 26, 0.8);
        backdrop-filter: blur(20px);
        border-radius: 12px;
        padding: 6px;
        gap: 6px;
        border: 1px solid rgba(74, 222, 128, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #888;
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
        position: relative;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background: rgba(74, 222, 128, 0.1);
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(74, 222, 128, 0.2), rgba(34, 197, 94, 0.1));
        color: #ffffff;
        box-shadow: 0 4px 20px rgba(74, 222, 128, 0.3);
        border: 1px solid rgba(74, 222, 128, 0.4);
    }

    /* Table styling */
    .dataframe {
        background-color: #1a1a1a !important;
        border: 1px solid #333;
        border-radius: 8px;
        overflow: hidden;
    }
    .dataframe th {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        font-weight: 600;
        text-align: center;
        padding: 12px 8px;
        border-bottom: 2px solid #444;
        font-size: 13px;
    }
    .dataframe td {
        text-align: center !important;
        vertical-align: middle !important;
        padding: 8px;
        border-bottom: 1px solid #333;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        background-color: #1a1a1a;
    }

    /* Force center alignment for all table cells */
    .stDataFrame td, .stDataFrame th {
        text-align: center !important;
    }

    /* Center alignment for styled cells */
    .positive, .negative, .highlight, .highest-positive, .highest-negative {
        text-align: center !important;
        vertical-align: middle !important;
    }

    /* Premium button styling */
    .stButton > button {
        background: linear-gradient(135deg, rgba(74, 222, 128, 0.8), rgba(34, 197, 94, 0.8)) !important;
        color: #ffffff !important;
        border: 2px solid rgba(74, 222, 128, 0.4) !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 8px 25px rgba(74, 222, 128, 0.3) !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(74, 222, 128, 1), rgba(34, 197, 94, 1)) !important;
        border-color: rgba(74, 222, 128, 0.6) !important;
        box-shadow: 0 12px 35px rgba(74, 222, 128, 0.4) !important;
        transform: translateY(-3px) scale(1.02) !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5) !important;
    }

    .stButton > button:active {
        transform: translateY(-1px) scale(0.98) !important;
        box-shadow: 0 6px 20px rgba(74, 222, 128, 0.5) !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Mobile Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: wrap;
            gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 11px;
            padding: 6px 12px;
            min-width: auto;
        }
        .dataframe th, .dataframe td {
            padding: 4px 6px;
            font-size: 10px;
        }
        .stSelectbox label {
            font-size: 16px !important;
        }

        .stSelectbox > div > div[data-baseweb="select"] {
            font-size: 18px !important;
            min-height: 50px !important;
            padding: 12px 16px !important;
        }

        .stSelectbox > div > div[data-baseweb="select"] > div {
            font-size: 18px !important;
        }
        h1 { font-size: 1.5rem; }
        h2 { font-size: 1.3rem; }
        h3 { font-size: 1.1rem; }
    }

    @media (max-width: 480px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 9px;
            padding: 4px 8px;
        }
        .dataframe th, .dataframe td {
            font-size: 9px;
            padding: 3px 4px;
        }
        h1 { font-size: 1.2rem; }
        h2 { font-size: 1.1rem; }
        h3 { font-size: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------
# Token Status Check (for maintenance awareness)
# --------------------------------------------------------------
if ACCESS_TOKEN:
    try:
        token_status = refresh_tokens_if_needed()
        if "WARNING" in token_status or "EXPIRED" in token_status:
            st.warning(f"🔑 **Token Status:** {token_status}")
        elif "INFO" in token_status:
            st.info(f"🔑 **Token Status:** {token_status}")
    except Exception as e:
        # Don't show token status errors on Streamlit Cloud (tokens are in secrets)
        pass
else:
    st.error("🔑 **Schwab API token missing** - check .env file")

# --------------------------------------------------------------
# Auto-Refresh Configuration (using st.empty() for true auto-refresh)
# --------------------------------------------------------------
REFRESH_INTERVAL = 10  # seconds - fast updates for live trading

# Initialize session state for auto-refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0
if 'auto_refresh_enabled' not in st.session_state:
    st.session_state.auto_refresh_enabled = True

# Get current time for refresh calculations
current_time = time.time()

# Calculate time until next refresh for display
time_since_refresh = current_time - st.session_state.last_refresh
time_until_refresh = max(0, REFRESH_INTERVAL - time_since_refresh)

# Auto-refresh using st.empty() placeholder
if 'refresh_placeholder' not in st.session_state:
    st.session_state.refresh_placeholder = st.empty()

# --------------------------------------------------------------
# Professional Header - Options Pro Style
# --------------------------------------------------------------

# Premium app title and branding with stunning effects
st.markdown("""
<div style='
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95), rgba(22, 33, 62, 0.95));
    backdrop-filter: blur(20px);
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 30px;
    border: 2px solid rgba(74, 222, 128, 0.3);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 40px rgba(74, 222, 128, 0.1);
    position: relative;
    overflow: hidden;
'>
    <div style='
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(74, 222, 128, 0.05) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    '></div>
    <div style='display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 1;'>
        <div>
            <h1 style='
                margin: 0;
                background: linear-gradient(135deg, #ffffff, #4ade80, #60a5fa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 32px;
                font-weight: 800;
                letter-spacing: -0.02em;
                text-shadow: 0 0 30px rgba(74, 222, 128, 0.3);
                animation: titleGlow 3s ease-in-out infinite alternate;
            '>
                📊 Options Pro
            </h1>
            <p style='
                margin: 8px 0 0 0;
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 0.5px;
                text-shadow: 0 0 10px rgba(74, 222, 128, 0.2);
            '>
                Dealer Positioning Tracker • Real-time Options Flow Analysis
            </p>
        </div>
        <div style='text-align: right; position: relative;'>
            <div style='
                color: #4ade80;
                font-size: 14px;
                font-weight: 700;
                text-shadow: 0 0 15px rgba(74, 222, 128, 0.6);
                animation: livePulse 2s ease-in-out infinite;
            '>● LIVE</div>
            <div style='
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                font-weight: 500;
                margin-top: 2px;
            '>Market Data</div>
            <div style='
                position: absolute;
                top: -5px;
                right: -5px;
                width: 10px;
                height: 10px;
                background: #4ade80;
                border-radius: 50%;
                box-shadow: 0 0 20px rgba(74, 222, 128, 0.8);
                animation: livePulse 2s ease-in-out infinite;
            '></div>
        </div>
    </div>
</div>

<style>
@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes titleGlow {
    0% { text-shadow: 0 0 30px rgba(74, 222, 128, 0.3); }
    100% { text-shadow: 0 0 40px rgba(74, 222, 128, 0.5), 0 0 60px rgba(96, 165, 250, 0.3); }
}

@keyframes livePulse {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
        text-shadow: 0 0 15px rgba(74, 222, 128, 0.6);
    }
    50% {
        opacity: 0.7;
        transform: scale(1.05);
        text-shadow: 0 0 25px rgba(74, 222, 128, 0.8);
    }
}
</style>
""", unsafe_allow_html=True)

# Ticker selection and price display
col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    # Initialize selected ticker in session state with URL parameter support
    if 'selected_ticker' not in st.session_state:
        # Check if ticker is specified in URL parameters
        query_params = st.query_params
        url_ticker = query_params.get('ticker', [ALL_TICKERS[0].symbol])
        if isinstance(url_ticker, list):
            url_ticker = url_ticker[0] if url_ticker else ALL_TICKERS[0].symbol

        # Validate that the ticker exists in our list
        ticker_symbols = [t.symbol for t in ALL_TICKERS]
        if url_ticker in ticker_symbols:
            st.session_state.selected_ticker = url_ticker
        else:
            st.session_state.selected_ticker = ALL_TICKERS[0].symbol

    # Get current index for the selected ticker
    ticker_symbols = [t.symbol for t in ALL_TICKERS]
    try:
        current_index = ticker_symbols.index(st.session_state.selected_ticker)
    except ValueError:
        current_index = 0
        st.session_state.selected_ticker = ALL_TICKERS[0].symbol

    # Professional ticker selector
    selected = st.selectbox(
        "Select Ticker",
        options=ticker_symbols,
        format_func=lambda x: f"{x} – {next(t.name for t in ALL_TICKERS if t.symbol == x)}",
        index=current_index,
        key="ticker_select"
    )

    # Update session state and URL when selection changes
    if selected != st.session_state.selected_ticker:
        st.session_state.selected_ticker = selected
        # Update URL to preserve selection across refreshes
        st.query_params.ticker = selected

# --------------------------------------------------------------
# Auto-Refresh Debug Info (will be moved to end of script)
# --------------------------------------------------------------
# Calculate time since last refresh for display
time_since_refresh = current_time - st.session_state.last_refresh

# Debug info (remove after testing)
st.write(f"🔍 Debug: Time since refresh: {time_since_refresh:.1f}s, Interval: {REFRESH_INTERVAL}s, Count: #{st.session_state.refresh_count}")

# JavaScript fallback refresh (browser-based timer)
st.markdown(f"""
<script>
setTimeout(function() {{
    if (window.location.search.indexOf('refresh=') === -1) {{
        const url = new URL(window.location);
        url.searchParams.set('refresh', Date.now());
        window.location.href = url.toString();
    }}
}}, {REFRESH_INTERVAL * 1000});
</script>
""", unsafe_allow_html=True)

with col2:
    try:
        S = get_underlying_price(st.session_state.selected_ticker)
        last_update = datetime.now().strftime("%H:%M:%S")

        # Get ticker name
        ticker_name = next(t.name for t in ALL_TICKERS if t.symbol == st.session_state.selected_ticker)

        # Premium price display with stunning effects
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95), rgba(22, 33, 62, 0.95));
            backdrop-filter: blur(20px);
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            border: 2px solid rgba(74, 222, 128, 0.3);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3), 0 0 30px rgba(74, 222, 128, 0.1);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        ' onmouseover='this.style.transform="translateY(-5px)"; this.style.boxShadow="0 20px 50px rgba(0, 0, 0, 0.4), 0 0 40px rgba(74, 222, 128, 0.2)"'
          onmouseout='this.style.transform="translateY(0px)"; this.style.boxShadow="0 15px 40px rgba(0, 0, 0, 0.3), 0 0 30px rgba(74, 222, 128, 0.1)"'>
            <div style='
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(74, 222, 128, 0.03) 0%, transparent 70%);
                animation: priceRotate 15s linear infinite;
            '></div>
            <div style='position: relative; z-index: 1;'>
                <div style='
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    letter-spacing: 2px;
                    text-shadow: 0 0 15px rgba(74, 222, 128, 0.3);
                '>
                    {st.session_state.selected_ticker}
                </div>
                <div style='
                    background: linear-gradient(135deg, #4ade80, #22c55e, #16a34a);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 36px;
                    font-weight: 900;
                    margin-bottom: 8px;
                    text-shadow: 0 0 30px rgba(74, 222, 128, 0.5);
                    animation: priceGlow 2s ease-in-out infinite alternate;
                '>
                    ${S:,.2f}
                </div>
                <div style='
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 13px;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                '>
                    {ticker_name} • Updated {last_update}
                </div>
            </div>
        </div>

        <style>
        @keyframes priceRotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        @keyframes priceGlow {{
            0% {{ text-shadow: 0 0 30px rgba(74, 222, 128, 0.5); }}
            100% {{ text-shadow: 0 0 40px rgba(74, 222, 128, 0.7), 0 0 60px rgba(34, 197, 94, 0.4); }}
        }}
        </style>
        """, unsafe_allow_html=True)
    except:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1a1a1a, #2a2a2a); padding: 16px; border-radius: 8px; text-align: center; border: 1px solid #333;'>
            <div style='color: #ffffff; font-size: 28px; font-weight: 700; margin-bottom: 4px;'>
                {st.session_state.selected_ticker}
            </div>
            <div style='color: #f87171; font-size: 32px; font-weight: 800; margin-bottom: 4px;'>
                —
            </div>
            <div style='color: #888; font-size: 12px;'>
                Price unavailable
            </div>
        </div>
        """, unsafe_allow_html=True)
        S = 100.0

with col3:
    # Calculate time until next refresh
    time_since_refresh = current_time - st.session_state.last_refresh
    time_until_refresh = max(0, REFRESH_INTERVAL - time_since_refresh)

    # Premium refresh controls with stunning countdown
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95));
        backdrop-filter: blur(20px);
        padding: 20px;
        border-radius: 16px;
        border: 2px solid rgba(74, 222, 128, 0.3);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3), 0 0 30px rgba(74, 222, 128, 0.1);
        position: relative;
        overflow: hidden;
    '>
        <div style='
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, #4ade80, transparent);
            animation: refreshProgress 10s linear infinite;
        '></div>
        <div style='text-align: center; position: relative; z-index: 1;'>
            <div style='
                color: #4ade80;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 8px;
                text-shadow: 0 0 15px rgba(74, 222, 128, 0.6);
            '>
                🔄 Live Updates
            </div>
            <div class='refresh-countdown' style='
                background: linear-gradient(135deg, #ffffff, #4ade80);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 6px;
                text-shadow: 0 0 20px rgba(74, 222, 128, 0.4);
            '>
                {time_until_refresh:.0f}s
            </div>
            <div style='
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
                font-weight: 500;
                margin-bottom: 4px;
            '>
                10s interval • #{st.session_state.refresh_count}
            </div>
            <div style='
                color: rgba(255, 255, 255, 0.5);
                font-size: 10px;
                font-weight: 500;
                padding: 4px 8px;
                background: rgba(74, 222, 128, 0.1);
                border-radius: 12px;
                border: 1px solid rgba(74, 222, 128, 0.2);
            '>
                No page reload • Data only
            </div>
        </div>
    </div>

    <style>
    @keyframes refreshProgress {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}


    </style>
    """, unsafe_allow_html=True)

    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.session_state.last_refresh = current_time
        st.session_state.refresh_count += 1
        st.cache_data.clear()
        # Update URL to preserve ticker selection
        current_ticker = st.session_state.get('selected_ticker', 'SPY')
        st.query_params.ticker = current_ticker
        st.rerun()

# Display earnings information
display_earnings_info(st.session_state.selected_ticker)

if not ACCESS_TOKEN:
    st.error("Schwab API token missing – check .env file")
    st.stop()

# --------------------------------------------------------------
# Intraday Comparison Functions
# --------------------------------------------------------------
def get_market_open_time():
    """Get today's market open time (9:30 AM ET)"""
    import pytz
    from datetime import datetime, time

    est = pytz.timezone('US/Eastern')
    today = datetime.now(est).date()
    market_open = datetime.combine(today, time(9, 30))
    return est.localize(market_open)

def get_opening_volume_data(symbol: str):
    """Get volume data from market open (first 30 minutes)"""
    try:
        import sqlite3
        from contextlib import closing

        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        market_open = get_market_open_time()
        market_open_timestamp = int(market_open.timestamp())

        # Get data from first 30 minutes (9:30-10:00 AM)
        first_30_min_end = market_open_timestamp + (30 * 60)  # 30 minutes after open

        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT timestamp, call_volume, put_volume, call_centroid, put_centroid
                    FROM centroid_data
                    WHERE ticker = ? AND date = ?
                    AND timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp
                ''', (symbol, today, market_open_timestamp, first_30_min_end))

                opening_data = cursor.fetchall()

                if opening_data:
                    # Aggregate opening 30 minutes
                    total_call_vol = sum(int(row[1]) for row in opening_data)
                    total_put_vol = sum(int(row[2]) for row in opening_data)

                    # Volume-weighted average centroids
                    if total_call_vol > 0:
                        call_centroid = sum(float(row[3]) * int(row[1]) for row in opening_data) / total_call_vol
                    else:
                        call_centroid = 0

                    if total_put_vol > 0:
                        put_centroid = sum(float(row[4]) * int(row[2]) for row in opening_data) / total_put_vol
                    else:
                        put_centroid = 0

                    return {
                        'call_volume': total_call_vol,
                        'put_volume': total_put_vol,
                        'total_volume': total_call_vol + total_put_vol,
                        'call_centroid': call_centroid,
                        'put_centroid': put_centroid,
                        'call_put_ratio': total_call_vol / total_put_vol if total_put_vol > 0 else float('inf'),
                        'time_period': '9:30-10:00 AM'
                    }

        return None
    except Exception as e:
        print(f"Error getting opening volume data: {e}")
        return None

def get_current_session_data(symbol: str):
    """Get current session volume data (all day so far)"""
    try:
        import sqlite3
        from contextlib import closing

        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')

        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT timestamp, call_volume, put_volume, call_centroid, put_centroid
                    FROM centroid_data
                    WHERE ticker = ? AND date = ?
                    ORDER BY timestamp
                ''', (symbol, today))

                session_data = cursor.fetchall()

                if session_data:
                    # Aggregate entire session
                    total_call_vol = sum(int(row[1]) for row in session_data)
                    total_put_vol = sum(int(row[2]) for row in session_data)

                    # Volume-weighted average centroids
                    if total_call_vol > 0:
                        call_centroid = sum(float(row[3]) * int(row[1]) for row in session_data) / total_call_vol
                    else:
                        call_centroid = 0

                    if total_put_vol > 0:
                        put_centroid = sum(float(row[4]) * int(row[2]) for row in session_data) / total_put_vol
                    else:
                        put_centroid = 0

                    return {
                        'call_volume': total_call_vol,
                        'put_volume': total_put_vol,
                        'total_volume': total_call_vol + total_put_vol,
                        'call_centroid': call_centroid,
                        'put_centroid': put_centroid,
                        'call_put_ratio': total_call_vol / total_put_vol if total_put_vol > 0 else float('inf'),
                        'time_period': 'Full Session'
                    }

        return None
    except Exception as e:
        print(f"Error getting current session data: {e}")
        return None

# --------------------------------------------------------------
# Interval Data Storage for GEX Replay
# --------------------------------------------------------------
def store_interval_data_for_replay(symbol: str, price: float, df: pd.DataFrame):
    """Store strike-level GEX data for replay feature"""
    try:
        import sqlite3
        import pytz
        from contextlib import closing
        from datetime import datetime

        # Check if we're in market hours (9:30 AM - 4:00 PM ET, Monday-Friday)
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)

        if current_time_est.weekday() >= 5:  # Weekend
            return

        market_open = current_time_est.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = current_time_est.replace(hour=16, minute=0, second=0, microsecond=0)

        if not (market_open <= current_time_est <= market_close):
            return  # Outside market hours

        # Initialize database if needed
        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interval_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        price REAL NOT NULL,
                        strike REAL NOT NULL,
                        net_gamma REAL NOT NULL,
                        net_delta REAL NOT NULL,
                        net_vanna REAL NOT NULL,
                        date TEXT NOT NULL
                    )
                ''')
                conn.commit()

        current_time = int(current_time_est.timestamp())
        current_date = current_time_est.strftime('%Y-%m-%d')

        # Round to nearest 5-minute interval for more granular replay (300 seconds)
        interval_timestamp = (current_time // 300) * 300

        # Check if we already have data for this 5-minute interval
        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT id FROM interval_data
                    WHERE ticker = ? AND timestamp = ? AND date = ?
                    LIMIT 1
                ''', (symbol, interval_timestamp, current_date))

                if cursor.fetchone():
                    return  # Data already exists for this interval

        # Aggregate data by strike to get net exposures (like the main tabs do)
        strike_agg = df.groupby('strike').agg({
            'GEX_OI': 'sum',
            'DEX_OI': 'sum',
            'Vanna_OI': 'sum'
        }).reset_index()

        # Store strike-level data for replay
        strikes_to_store = []
        for _, row in strike_agg.iterrows():
            strike = float(row['strike'])
            net_gamma = float(row['GEX_OI'])  # Use OI-based GEX for replay
            net_delta = float(row['DEX_OI'])
            net_vanna = float(row['Vanna_OI'])

            # Only store strikes with significant exposure
            if abs(net_gamma) > 1000 or abs(net_delta) > 1000 or abs(net_vanna) > 1000:
                strikes_to_store.append((
                    symbol, interval_timestamp, float(price), strike,
                    net_gamma, net_delta, net_vanna, current_date
                ))

        # Batch insert for efficiency
        if strikes_to_store:
            with closing(sqlite3.connect('options_data.db')) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.executemany('''
                        INSERT INTO interval_data (ticker, timestamp, price, strike, net_gamma, net_delta, net_vanna, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', strikes_to_store)
                    conn.commit()
                    print(f"📊 Stored {len(strikes_to_store)} strikes for GEX replay: {symbol} at {current_time_est.strftime('%H:%M')}")

    except Exception as e:
        print(f"Error storing interval data for replay: {e}")

# --------------------------------------------------------------
# Data Load with Dual Calculations
# --------------------------------------------------------------
@st.cache_data(ttl=10, show_spinner=False)
def load_enhanced_data(symbol: str, n_exp: int = 4):
    try:
        S = get_underlying_price(symbol)
        df_raw = get_options_chain(symbol, n_exp)

        if df_raw.empty:
            return S, pd.DataFrame(), []

        # Get nearest expirations
        df_raw["exp_dt"] = pd.to_datetime(df_raw["expiry"])
        nearest = df_raw.drop_duplicates("expiry").sort_values("exp_dt").head(n_exp)["expiry"].tolist()
        df = df_raw[df_raw["expiry"].isin(nearest)].copy()

        # Get ticker config
        cfg = next(t for t in ALL_TICKERS if t.symbol == symbol)

        # Special handling for SPX - Apply multiplier BEFORE OI filtering
        if cfg.is_index and cfg.symbol == "SPX":
            df["openInterest"] = df["openInterest"] * 10

        # Filter by minimum OI (after SPX multiplier if applicable)
        # Special case: Skip OI filtering for SPX since it often has 0 OI but meaningful volume
        if cfg.symbol != "SPX":
            df = df[df["openInterest"] >= cfg.min_oi]

        # Filter out invalid strike increments for specific tickers
        # SPY should only have $1.00 increments (filter out 0.5 strikes that have zero OI)
        if symbol == "SPY":
            # Keep only whole dollar strikes for SPY
            df = df[df['strike'] % 1.0 == 0]
        elif symbol == "SPX":
            # Keep only $5.00 increment strikes for SPX
            df = df[df['strike'] % 5.0 == 0]
        # For other tickers, trust the Schwab API data (don't filter strikes)

        # Compute BOTH OI and Volume exposures
        df = compute_exposures_dual(df, S)

        # Store volume data for intraday tracking (only during market hours)
        try:
            store_volume_data_for_tracking(symbol, S, df)
        except Exception as e:
            print(f"Warning: Could not store volume tracking data: {e}")

        # Store interval data for GEX replay feature
        try:
            store_interval_data_for_replay(symbol, S, df)
        except Exception as e:
            print(f"Warning: Could not store interval data for replay: {e}")

        # Backfill morning data if this is the first load of the day
        try:
            backfill_morning_data(symbol, df, S)
        except Exception as e:
            print(f"Warning: Could not backfill morning data: {e}")

        return S, df, nearest
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return S, pd.DataFrame(), []

def store_volume_data_for_tracking(symbol: str, price: float, df: pd.DataFrame):
    """Store volume data for intraday tracking using the existing centroid system"""
    try:
        import sqlite3
        import pytz
        from contextlib import closing
        from datetime import datetime, time

        # Check if we're in market hours (9:30 AM - 4:00 PM ET, Monday-Friday)
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)

        if current_time_est.weekday() >= 5:  # Weekend
            return

        market_open = current_time_est.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = current_time_est.replace(hour=16, minute=0, second=0, microsecond=0)

        if not (market_open <= current_time_est <= market_close):
            return  # Outside market hours

        # Initialize database if needed
        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS centroid_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        price REAL NOT NULL,
                        call_centroid REAL NOT NULL,
                        put_centroid REAL NOT NULL,
                        call_volume INTEGER NOT NULL,
                        put_volume INTEGER NOT NULL,
                        date TEXT NOT NULL
                    )
                ''')
                conn.commit()

        current_time = int(current_time_est.timestamp())
        current_date = current_time_est.strftime('%Y-%m-%d')

        # Round to nearest 15-minute interval (900 seconds)
        interval_timestamp = (current_time // 900) * 900

        # Check if we already have data for this 15-minute interval
        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT id FROM centroid_data
                    WHERE ticker = ? AND timestamp = ? AND date = ?
                ''', (symbol, interval_timestamp, current_date))

                if cursor.fetchone():
                    return  # Data already exists for this interval

        # Calculate volume-weighted centroids
        calls = df[df['type'] == 'call'].copy()
        puts = df[df['type'] == 'put'].copy()

        call_volume = int(calls['volume'].sum())  # Ensure integer
        put_volume = int(puts['volume'].sum())    # Ensure integer

        # Calculate volume-weighted average strike (centroid)
        if call_volume > 0:
            call_centroid = float((calls['strike'] * calls['volume']).sum() / call_volume)
        else:
            call_centroid = 0.0

        if put_volume > 0:
            put_centroid = float((puts['strike'] * puts['volume']).sum() / put_volume)
        else:
            put_centroid = 0.0

        # Only store if we have volume data
        if call_volume > 0 or put_volume > 0:
            with closing(sqlite3.connect('options_data.db')) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute('''
                        INSERT INTO centroid_data (ticker, timestamp, price, call_centroid, put_centroid, call_volume, put_volume, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (symbol, interval_timestamp, float(price), call_centroid, put_centroid, call_volume, put_volume, current_date))
                    conn.commit()
                    print(f"📊 Stored volume data for {symbol}: C:{call_volume:,} P:{put_volume:,} at {current_time_est.strftime('%H:%M')}")

    except Exception as e:
        print(f"Error storing volume tracking data: {e}")


def backfill_morning_data(symbol: str, current_df: pd.DataFrame, current_price: float):
    """Backfill GEX replay data from 9:30 AM using current OI data"""
    try:
        import sqlite3
        import pytz
        from contextlib import closing
        from datetime import datetime, timedelta

        # Check if we already have morning data
        today = datetime.now().strftime('%Y-%m-%d')

        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT COUNT(*) FROM interval_data
                    WHERE ticker = ? AND date = ? AND timestamp < ?
                ''', (symbol, today, int(datetime.now().replace(hour=10, minute=0).timestamp())))

                morning_count = cursor.fetchone()[0]

                if morning_count > 0:
                    return  # Already have morning data

        print(f"🔄 Backfilling morning GEX data for {symbol}...")

        # Create synthetic timestamps from 9:30 AM to 10:00 AM (every 5 minutes)
        est = pytz.timezone('US/Eastern')
        today_date = datetime.now(est).date()

        # Start at 9:30 AM ET
        start_time = datetime.combine(today_date, datetime.min.time().replace(hour=9, minute=30))
        start_time = est.localize(start_time)

        # End at 10:00 AM ET
        end_time = datetime.combine(today_date, datetime.min.time().replace(hour=10, minute=0))
        end_time = est.localize(end_time)

        # Generate 5-minute intervals
        current_time = start_time
        synthetic_data = []

        # Aggregate current data by strike (like we do for real-time data)
        strike_agg = current_df.groupby('strike').agg({
            'GEX_OI': 'sum',
            'DEX_OI': 'sum',
            'Vanna_OI': 'sum'
        }).reset_index()

        while current_time <= end_time:
            timestamp = int(current_time.timestamp())

            # Use current OI data as proxy for morning levels
            # (OI doesn't change much intraday, so this gives us the structure)
            for _, row in strike_agg.iterrows():
                strike = float(row['strike'])
                net_gamma = float(row['GEX_OI'])
                net_delta = float(row['DEX_OI'])
                net_vanna = float(row['Vanna_OI'])

                # Only store strikes with significant exposure
                if abs(net_gamma) > 1000 or abs(net_delta) > 1000 or abs(net_vanna) > 1000:
                    synthetic_data.append((
                        symbol, timestamp, current_price, strike,
                        net_gamma, net_delta, net_vanna, today
                    ))

            current_time += timedelta(minutes=5)

        # Batch insert synthetic data
        if synthetic_data:
            with closing(sqlite3.connect('options_data.db')) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.executemany('''
                        INSERT INTO interval_data (ticker, timestamp, price, strike, net_gamma, net_delta, net_vanna, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', synthetic_data)
                    conn.commit()

                    intervals_created = len(set(data[1] for data in synthetic_data))
                    strikes_per_interval = len(synthetic_data) // intervals_created if intervals_created > 0 else 0
                    print(f"✅ Backfilled {intervals_created} intervals with ~{strikes_per_interval} strikes each from 9:30-10:00 AM")

    except Exception as e:
        print(f"Error backfilling morning data: {e}")


def get_replay_timestamps(symbol: str):
    """Get available timestamps for GEX replay"""
    try:
        import sqlite3
        from contextlib import closing
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')

        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT DISTINCT timestamp
                    FROM interval_data
                    WHERE ticker = ? AND date = ?
                    ORDER BY timestamp
                ''', (symbol, today))

                timestamps = [row[0] for row in cursor.fetchall()]
                return timestamps
    except Exception as e:
        print(f"Error getting replay timestamps: {e}")
        return []

def get_replay_data(symbol: str, timestamp: int):
    """Get GEX data for a specific timestamp"""
    try:
        import sqlite3
        from contextlib import closing
        from datetime import datetime

        today = datetime.now().strftime('%Y-%m-%d')

        with closing(sqlite3.connect('options_data.db')) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT price, strike, net_gamma, net_delta, net_vanna
                    FROM interval_data
                    WHERE ticker = ? AND timestamp = ? AND date = ?
                    ORDER BY strike
                ''', (symbol, timestamp, today))

                data = cursor.fetchall()
                if data:
                    return {
                        'price': data[0][0],
                        'strikes': [row[1] for row in data],
                        'net_gamma': [row[2] for row in data],
                        'net_delta': [row[3] for row in data],
                        'net_vanna': [row[4] for row in data]
                    }
                return None
    except Exception as e:
        print(f"Error getting replay data: {e}")
        return None

S, df, expirations = load_enhanced_data(st.session_state.selected_ticker, n_exp=4)

if df.empty:
    st.warning(f"No options data available for {st.session_state.selected_ticker}")
    st.stop()

# --------------------------------------------------------------
# Intraday Volume Comparison
# --------------------------------------------------------------
with st.expander("📊 **Intraday Volume Analysis** - Opening vs Current", expanded=False):
    col1, col2, col3 = st.columns(3)

    # Get opening and current session data
    opening_data = get_opening_volume_data(st.session_state.selected_ticker)
    current_data = get_current_session_data(st.session_state.selected_ticker)

    if opening_data and current_data:
        with col1:
            st.markdown("### 🌅 **Opening 30 Min**")
            st.markdown(f"**Time**: {opening_data['time_period']}")
            st.metric(
                "Total Volume",
                f"{opening_data['total_volume']:,}",
                help="Combined call + put volume in first 30 minutes"
            )
            st.metric(
                "Call Volume",
                f"{opening_data['call_volume']:,}",
                help="Call volume from 9:30-10:00 AM"
            )
            st.metric(
                "Put Volume",
                f"{opening_data['put_volume']:,}",
                help="Put volume from 9:30-10:00 AM"
            )

            # Call/Put Ratio with color coding
            cpr_open = opening_data['call_put_ratio']
            if cpr_open == float('inf'):
                cpr_display = "∞ (Calls Only)"
                cpr_color = "🔴"
            else:
                cpr_display = f"{cpr_open:.2f}"
                cpr_color = "🔴" if cpr_open > 1.5 else "🟢" if cpr_open < 0.67 else "🟡"

            st.markdown(f"**C/P Ratio**: {cpr_color} {cpr_display}")

        with col2:
            st.markdown("### 📈 **Current Session**")
            st.markdown(f"**Time**: {current_data['time_period']}")

            # Calculate changes
            vol_change = current_data['total_volume'] - opening_data['total_volume']
            vol_change_pct = (vol_change / opening_data['total_volume'] * 100) if opening_data['total_volume'] > 0 else 0

            call_change = current_data['call_volume'] - opening_data['call_volume']
            put_change = current_data['put_volume'] - opening_data['put_volume']

            st.metric(
                "Total Volume",
                f"{current_data['total_volume']:,}",
                delta=f"{vol_change:+,} ({vol_change_pct:+.1f}%)",
                help="Total session volume vs opening 30 minutes"
            )
            st.metric(
                "Call Volume",
                f"{current_data['call_volume']:,}",
                delta=f"{call_change:+,}",
                help="Session call volume vs opening"
            )
            st.metric(
                "Put Volume",
                f"{current_data['put_volume']:,}",
                delta=f"{put_change:+,}",
                help="Session put volume vs opening"
            )

            # Current Call/Put Ratio
            cpr_current = current_data['call_put_ratio']
            if cpr_current == float('inf'):
                cpr_current_display = "∞ (Calls Only)"
                cpr_current_color = "🔴"
            else:
                cpr_current_display = f"{cpr_current:.2f}"
                cpr_current_color = "🔴" if cpr_current > 1.5 else "🟢" if cpr_current < 0.67 else "🟡"

            st.markdown(f"**C/P Ratio**: {cpr_current_color} {cpr_current_display}")

        with col3:
            st.markdown("### 🎯 **Flow Analysis**")

            # Sentiment shift analysis
            if opening_data['call_put_ratio'] != float('inf') and current_data['call_put_ratio'] != float('inf'):
                ratio_change = current_data['call_put_ratio'] - opening_data['call_put_ratio']

                if ratio_change > 0.2:
                    sentiment = "🔴 **More Bullish**"
                    sentiment_desc = "Call buying increased"
                elif ratio_change < -0.2:
                    sentiment = "🟢 **More Bearish**"
                    sentiment_desc = "Put buying increased"
                else:
                    sentiment = "🟡 **Neutral Shift**"
                    sentiment_desc = "Balanced flow"

                st.markdown(sentiment)
                st.markdown(f"*{sentiment_desc}*")
                st.metric("Ratio Change", f"{ratio_change:+.2f}", help="Change in Call/Put ratio since open")

            # Volume acceleration
            if opening_data['total_volume'] > 0:
                # Estimate hourly run rate
                current_time = datetime.now()
                market_open = get_market_open_time().replace(tzinfo=None)
                hours_elapsed = max(0.5, (current_time - market_open).total_seconds() / 3600)

                hourly_rate = current_data['total_volume'] / hours_elapsed
                opening_rate = opening_data['total_volume'] / 0.5  # 30 minutes = 0.5 hours

                if hourly_rate > opening_rate * 1.2:
                    pace = "🚀 **Accelerating**"
                elif hourly_rate < opening_rate * 0.8:
                    pace = "🐌 **Slowing**"
                else:
                    pace = "📊 **Steady**"

                st.markdown(f"**Volume Pace**: {pace}")
                st.markdown(f"*{hourly_rate:,.0f}/hr current*")
                st.markdown(f"*{opening_rate:,.0f}/hr opening*")

    elif current_data:
        st.info("📊 **Current session data available** - Opening data will appear after 10:00 AM")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Session Volume", f"{current_data['total_volume']:,}")
            st.metric("Call Volume", f"{current_data['call_volume']:,}")
        with col2:
            st.metric("Put Volume", f"{current_data['put_volume']:,}")
            cpr = current_data['call_put_ratio']
            if cpr == float('inf'):
                st.markdown("**C/P Ratio**: 🔴 ∞ (Calls Only)")
            else:
                color = "🔴" if cpr > 1.5 else "🟢" if cpr < 0.67 else "🟡"
                st.markdown(f"**C/P Ratio**: {color} {cpr:.2f}")
    else:
        st.info("📊 **Intraday data will appear once volume tracking begins**")
        st.markdown("*Historical volume data is collected every 15 minutes during market hours*")

# --------------------------------------------------------------
# GEX Replay Feature
# --------------------------------------------------------------
with st.expander("⏯️ **GEX Replay - Intraday Evolution**", expanded=False):
    st.markdown("**Replay how Gamma Exposure levels evolved throughout the trading day**")

    # Get available timestamps for replay
    replay_timestamps = get_replay_timestamps(st.session_state.selected_ticker)

    if replay_timestamps:
        # Convert timestamps to readable times
        timestamp_options = {}
        for ts in replay_timestamps:
            time_str = datetime.fromtimestamp(ts).strftime('%H:%M')
            timestamp_options[time_str] = ts

        # Time slider
        selected_time = st.select_slider(
            "Select Time",
            options=list(timestamp_options.keys()),
            value=list(timestamp_options.keys())[-1] if timestamp_options else None,
            help="Drag to see how GEX levels evolved throughout the day"
        )

        if selected_time:
            selected_timestamp = timestamp_options[selected_time]
            replay_data = get_replay_data(st.session_state.selected_ticker, selected_timestamp)

            if replay_data:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Time", selected_time)
                    st.metric("Price", f"${replay_data['price']:.2f}")

                with col2:
                    # Find max gamma levels
                    max_gamma_idx = replay_data['net_gamma'].index(max(replay_data['net_gamma'], key=abs))
                    max_gamma_strike = replay_data['strikes'][max_gamma_idx]
                    max_gamma_value = replay_data['net_gamma'][max_gamma_idx]

                    st.metric("Max Gamma Strike", f"${max_gamma_strike:.0f}")
                    st.metric("Max Gamma Value", f"{max_gamma_value/1e6:.1f}M")

                with col3:
                    # Count significant levels
                    significant_strikes = sum(1 for gamma in replay_data['net_gamma'] if abs(gamma) > 1e6)
                    st.metric("Significant Levels", significant_strikes)
                    st.metric("Total Strikes", len(replay_data['strikes']))

                # Create a simple visualization of gamma levels
                st.markdown("**Gamma Exposure Levels:**")

                # Show top 5 positive and negative gamma strikes
                gamma_data = list(zip(replay_data['strikes'], replay_data['net_gamma']))
                gamma_data.sort(key=lambda x: abs(x[1]), reverse=True)

                for i, (strike, gamma) in enumerate(gamma_data[:10]):
                    if abs(gamma) > 1e6:  # Only show significant levels
                        color = "🔴" if gamma > 0 else "🟢"
                        st.write(f"{color} **${strike:.0f}**: {gamma/1e6:.1f}M GEX")
            else:
                st.info("No replay data available for selected time")
    else:
        st.info("📊 **GEX replay data will be available once intraday collection begins**")
        st.markdown("*Strike-level gamma data is collected every 5 minutes during market hours*")

# --------------------------------------------------------------
# Unusual Activity Detection
# --------------------------------------------------------------
with st.expander("🚨 **Unusual Activity Monitor**", expanded=False):
    alerts = detect_unusual_activity(df, st.session_state.selected_ticker)
    display_unusual_activity(alerts)

# --------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------
def make_pivot(df, metric):
    agg = df.groupby(["strike", "expiry"]).agg({metric: "sum"}).reset_index()
    pivot = agg.pivot(index="strike", columns="expiry", values=metric).fillna(0)
    pivot = pivot.reindex(columns=expirations, index=sorted(pivot.index))
    return pivot, agg

def fmt(val):
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        return f"${val/1_000:.1f}K"
    else:
        return f"${val:,.0f}"

def create_styled_table(pivot, agg, metric, mode_name, current_price=None):
    """Create styled HTML table with current price indicator"""
    if agg.empty:
        return f"<p>No {metric} data available</p>"

    # Find top hot-spot (highest absolute value)
    top_val = agg[metric].abs().max()
    top_idx = agg[metric].abs().idxmax()
    top_strike = agg.loc[top_idx, "strike"]
    top_expiry = agg.loc[top_idx, "expiry"]

    # Find highest positive and highest negative values
    positive_values = agg[agg[metric] > 0]
    negative_values = agg[agg[metric] < 0]

    highest_positive_val = positive_values[metric].max() if not positive_values.empty else None
    highest_negative_val = negative_values[metric].min() if not negative_values.empty else None

    # Get strike/expiry for highest positive and negative
    if highest_positive_val is not None:
        highest_pos_idx = positive_values[metric].idxmax()
        highest_pos_strike = positive_values.loc[highest_pos_idx, "strike"]
        highest_pos_expiry = positive_values.loc[highest_pos_idx, "expiry"]
    else:
        highest_pos_strike = highest_pos_expiry = None

    if highest_negative_val is not None:
        highest_neg_idx = negative_values[metric].idxmin()
        highest_neg_strike = negative_values.loc[highest_neg_idx, "strike"]
        highest_neg_expiry = negative_values.loc[highest_neg_idx, "expiry"]
    else:
        highest_neg_strike = highest_neg_expiry = None

    # Build HTML table
    html = "<table style='width:100%; border-collapse: collapse; font-family: monospace; font-size: 14px;'>"
    html += "<thead><tr><th style='background:#161b22; color:#00bfff; padding:8px; text-align:left;'>Strike</th>"
    for exp in expirations:
        html += f"<th style='background:#161b22; color:#00bfff; padding:8px; text-align:center;'>{exp}</th>"
    html += "</tr></thead><tbody>"

    # Find the closest strike to current price
    closest_strike = None
    if current_price is not None:
        strikes_list = sorted(pivot.index)
        closest_strike = min(strikes_list, key=lambda x: abs(x - current_price))

    for strike in sorted(pivot.index):
        # Create strike display with current price indicator (preserve decimals for stocks like AAPL)
        if strike == int(strike):
            strike_display = f"{int(strike)}.0"
        else:
            strike_display = f"{strike:.1f}"
        strike_style = "background:#1f2530; color:#fafafa; padding:8px; text-align:right; font-weight:600;"

        # Add indicators if price is provided
        if current_price is not None:
            if strike == closest_strike:  # Closest strike to current price
                strike_display += f" →"
                strike_style = "background:#2d4a22; color:#4ade80; padding:8px; text-align:right; font-weight:700; border-left: 3px solid #4ade80;"
            elif strike == top_strike:  # Highest VEX/GEX strike
                strike_display += f" 🔥"

        html += f"<tr><td style='{strike_style}'>{strike_display}</td>"
        for exp in expirations:
            val = pivot.loc[strike, exp] if exp in pivot.columns else 0
            formatted_val = fmt(val)

            # Determine cell class
            cell_class = ""
            if abs(val) == top_val and strike == top_strike and exp == top_expiry:
                cell_class = "highlight"
                formatted_val += "*"  # Add asterisk for highest absolute value
            elif (highest_positive_val is not None and val == highest_positive_val and
                  strike == highest_pos_strike and exp == highest_pos_expiry):
                cell_class = "highest-positive"
            elif (highest_negative_val is not None and val == highest_negative_val and
                  strike == highest_neg_strike and exp == highest_neg_expiry):
                cell_class = "highest-negative"
            elif val > 0:
                cell_class = "positive"
            elif val < 0:
                cell_class = "negative"
            
            if cell_class:
                html += f"<td style='padding:8px; text-align:right;' class='{cell_class}'><div class='{cell_class}'>{formatted_val}</div></td>"
            else:
                html += f"<td style='padding:8px; text-align:right; background:#1f2530; color:#fafafa;'>{formatted_val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    
    # Add hot spot info
    html += f"<div style='text-align:center; margin-top:20px; color:#aaa; font-size:13px;'>"
    # Format top strike properly (preserve decimals)
    if top_strike == int(top_strike):
        top_strike_display = f"{int(top_strike)}.0"
    else:
        top_strike_display = f"{top_strike:.1f}"
    html += f"<span style='color:#87ceeb;'>🔵 Top {mode_name}: <strong>{fmt(top_val)}*</strong> at strike <strong>{top_strike_display}</strong> on <strong>{top_expiry}</strong></span><br>"

    # Add highest positive and negative info
    if highest_positive_val is not None:
        # Format highest positive strike properly
        if highest_pos_strike == int(highest_pos_strike):
            highest_pos_display = f"{int(highest_pos_strike)}.0"
        else:
            highest_pos_display = f"{highest_pos_strike:.1f}"
        html += f"<span style='color:#ffd700;'>🟡 Highest Positive: <strong>{fmt(highest_positive_val)}</strong> at {highest_pos_display} on {highest_pos_expiry}</span>"
    if highest_negative_val is not None:
        if highest_positive_val is not None:
            html += " • "
        # Format highest negative strike properly
        if highest_neg_strike == int(highest_neg_strike):
            highest_neg_display = f"{int(highest_neg_strike)}.0"
        else:
            highest_neg_display = f"{highest_neg_strike:.1f}"
        html += f"<span style='color:#dda0dd;'>🟣 Highest Negative: <strong>{fmt(highest_negative_val)}</strong> at {highest_neg_display} on {highest_neg_expiry}</span>"

    html += f"</div>"
    
    return html, top_val, top_strike, top_expiry

# --------------------------------------------------------------
# Tabbed Interface
# --------------------------------------------------------------
st.markdown("### 📊 **Options Flow Analysis**")

# Add legend for price indicators
st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a1a, #2a2a2a); padding: 12px; border-radius: 6px; margin-bottom: 16px; border: 1px solid #333;'>
    <div style='color: #888; font-size: 12px; text-align: center;'>
        <strong>Strike Legend:</strong>
        <span style='color: #4ade80;'>→ Closest to Current Price</span> •
        <span style='color: #ff6b6b;'>🔥 Highest VEX/GEX</span>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🟢 NetGEX (OI)",
    "🔵 NetGEX (Volume)",
    "🟡 NetVEX (OI)",
    "🟠 NetVEX (Volume)"
])

# Tab 1: NetGEX based on Open Interest
with tab1:
    st.markdown(f"#### **NetGEX (Open Interest) – {st.session_state.selected_ticker}**")
    pivot_gex_oi, agg_gex_oi = make_pivot(df, "GEX_OI")
    
    if not agg_gex_oi.empty:
        html, top_val, top_strike, top_expiry = create_styled_table(pivot_gex_oi, agg_gex_oi, "GEX_OI", "NetGEX (OI)", S)
        st.markdown(html, unsafe_allow_html=True)
        
        # Trading Plan
        with st.expander("📊 **Trading Analysis (OI-Based)**", expanded=False):
            pivot_with_strike = pivot_gex_oi.reset_index()
            pivot_with_strike.rename(columns={'strike': 'Strike'}, inplace=True)
            
            try:
                trading_plan = generate_trading_plan(st.session_state.selected_ticker, "NetGEX", pivot_with_strike, S, is_volume_based=False)
                st.markdown(trading_plan)
                
                key_levels = get_key_levels(pivot_with_strike, S)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🟢 Support Levels:**")
                    for level in key_levels["support"]:
                        distance = ((level - S) / S) * 100
                        st.markdown(f"• ${level:.0f} ({distance:+.1f}%)")
                
                with col2:
                    st.markdown("**🔴 Resistance Levels:**")
                    for level in key_levels["resistance"]:
                        distance = ((level - S) / S) * 100
                        st.markdown(f"• ${level:.0f} ({distance:+.1f}%)")
            except Exception as e:
                st.error(f"Unable to generate trading plan: {e}")
    else:
        st.warning("No GEX (OI) data available")

# Tab 2: NetGEX based on Volume
with tab2:
    st.markdown(f"#### **NetGEX (Volume) – {st.session_state.selected_ticker}**")
    pivot_gex_vol, agg_gex_vol = make_pivot(df, "GEX_Vol")
    
    if not agg_gex_vol.empty:
        html, top_val, top_strike, top_expiry = create_styled_table(pivot_gex_vol, agg_gex_vol, "GEX_Vol", "NetGEX (Vol)", S)
        st.markdown(html, unsafe_allow_html=True)
        
        # Volume-based trading plan
        with st.expander("📈 **Volume Flow Trading Analysis**", expanded=False):
            pivot_with_strike = pivot_gex_vol.reset_index()
            pivot_with_strike.rename(columns={'strike': 'Strike'}, inplace=True)

            try:
                trading_plan = generate_trading_plan(st.session_state.selected_ticker, "NetGEX", pivot_with_strike, S, is_volume_based=True)
                st.markdown(trading_plan)

                # Volume-specific metrics
                total_call_vol = df[df['type'] == 'call']['volume'].sum()
                total_put_vol = df[df['type'] == 'put']['volume'].sum()
                vol_ratio = total_call_vol / max(total_put_vol, 1)

                st.markdown("---")
                st.markdown(f"""
                **📊 Volume Flow Metrics:**
                - **Call Volume**: {total_call_vol:,} contracts
                - **Put Volume**: {total_put_vol:,} contracts
                - **Call/Put Ratio**: {vol_ratio:.2f}
                - **Flow Bias**: {'Bullish' if vol_ratio > 1 else 'Bearish'} volume sentiment

                **💡 Volume Flow Insight:**
                Volume shows TODAY's trading activity and immediate sentiment.
                High volume GEX levels indicate where active trading is happening RIGHT NOW.
                """)
            except Exception as e:
                st.error(f"Unable to generate volume trading plan: {e}")
    else:
        st.warning("No GEX (Volume) data available")

# Tab 3: NetVEX based on Open Interest
with tab3:
    st.markdown(f"#### **NetVEX (Open Interest) – {st.session_state.selected_ticker}**")
    pivot_vanna_oi, agg_vanna_oi = make_pivot(df, "Vanna_OI")

    if not agg_vanna_oi.empty:
        html, top_val, top_strike, top_expiry = create_styled_table(pivot_vanna_oi, agg_vanna_oi, "Vanna_OI", "NetVEX (OI)", S)
        st.markdown(html, unsafe_allow_html=True)

        # Vanna Trading Plan
        with st.expander("🌊 **Volatility Trading Analysis (OI-Based)**", expanded=False):
            pivot_with_strike = pivot_vanna_oi.reset_index()
            pivot_with_strike.rename(columns={'strike': 'Strike'}, inplace=True)

            try:
                trading_plan = generate_trading_plan(st.session_state.selected_ticker, "NetVEX", pivot_with_strike, S, is_volume_based=False)
                st.markdown(trading_plan)
            except Exception as e:
                st.error(f"Unable to generate trading plan: {e}")
    else:
        st.warning("No Vanna (OI) data available")

# Tab 4: NetVEX based on Volume
with tab4:
    st.markdown(f"#### **NetVEX (Volume) – {st.session_state.selected_ticker}**")
    pivot_vanna_vol, agg_vanna_vol = make_pivot(df, "Vanna_Vol")

    if not agg_vanna_vol.empty:
        html, top_val, top_strike, top_expiry = create_styled_table(pivot_vanna_vol, agg_vanna_vol, "Vanna_Vol", "NetVEX (Vol)", S)
        st.markdown(html, unsafe_allow_html=True)

        # Volume-based Vanna trading plan
        with st.expander("⚡ **Volume-Based Volatility Trading Analysis**", expanded=False):
            pivot_with_strike = pivot_vanna_vol.reset_index()
            pivot_with_strike.rename(columns={'strike': 'Strike'}, inplace=True)

            try:
                trading_plan = generate_trading_plan(st.session_state.selected_ticker, "NetVEX", pivot_with_strike, S, is_volume_based=True)
                st.markdown(trading_plan)

                # Calculate volume-weighted average IV
                df['vol_weighted_iv'] = df['volume'] * df['impliedVolatility']
                avg_iv = df['vol_weighted_iv'].sum() / df['volume'].sum() if df['volume'].sum() > 0 else 0

                # Separate call/put volume analysis
                call_vol_iv = df[df['type'] == 'call']['vol_weighted_iv'].sum() / max(df[df['type'] == 'call']['volume'].sum(), 1)
                put_vol_iv = df[df['type'] == 'put']['vol_weighted_iv'].sum() / max(df[df['type'] == 'put']['volume'].sum(), 1)

                st.markdown("---")
                st.markdown(f"""
                **🌊 Volume-Weighted Volatility Metrics:**
                - **Average IV (Volume-Weighted)**: {avg_iv:.1%}
                - **Call Volume IV**: {call_vol_iv:.1%}
                - **Put Volume IV**: {put_vol_iv:.1%}
                - **IV Skew**: {put_vol_iv - call_vol_iv:+.1%} (Put premium vs Call)

                **💡 Volume Vanna Flow Insight:**
                Volume-based Vanna shows TODAY's volatility positioning and flow.
                High volume Vanna suggests active vol trading or hedging activity happening NOW.
                Compare with OI-based Vanna to distinguish new positioning from closing trades.
                """)
            except Exception as e:
                st.error(f"Unable to generate volume vanna trading plan: {e}")
    else:
        st.warning("No Vanna (Volume) data available")

# --------------------------------------------------------------
# Comparison Section
# --------------------------------------------------------------
st.markdown("---")
st.markdown("### 🔄 **OI vs Volume Comparison**")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### **📊 Data Summary**")

    # Calculate totals
    total_oi = df['openInterest'].sum()
    total_vol = df['volume'].sum()

    # GEX comparison
    total_gex_oi = df['GEX_OI'].sum()
    total_gex_vol = df['GEX_Vol'].sum()

    # Vanna comparison
    total_vanna_oi = df['Vanna_OI'].sum()
    total_vanna_vol = df['Vanna_Vol'].sum()

    st.markdown(f"""
    **Position Metrics:**
    - **Total Open Interest**: {total_oi:,} contracts
    - **Total Volume**: {total_vol:,} contracts
    - **Volume/OI Ratio**: {total_vol/max(total_oi, 1):.1f}x

    **Exposure Comparison:**
    - **Net GEX (OI)**: ${total_gex_oi/1000:,.0f}K
    - **Net GEX (Vol)**: ${total_gex_vol/1000:,.0f}K
    - **Net Vanna (OI)**: ${total_vanna_oi/1000:,.0f}K
    - **Net Vanna (Vol)**: ${total_vanna_vol/1000:,.0f}K
    """)

with col2:
    st.markdown("#### **🎯 Key Insights**")

    vol_oi_ratio = total_vol / max(total_oi, 1)

    if vol_oi_ratio > 3:
        activity_level = "🔥 **Very High Activity**"
        interpretation = "Heavy intraday trading, possible event-driven flow"
    elif vol_oi_ratio > 1.5:
        activity_level = "📈 **High Activity**"
        interpretation = "Active trading day, above-average volume"
    elif vol_oi_ratio > 0.5:
        activity_level = "📊 **Normal Activity**"
        interpretation = "Typical trading volume relative to open interest"
    else:
        activity_level = "📉 **Low Activity**"
        interpretation = "Quiet trading day, below-average volume"

    st.markdown(f"""
    **{activity_level}**

    *{interpretation}*

    **📋 Analysis Framework:**
    - **OI-Based**: Shows structural market maker positioning
    - **Volume-Based**: Shows today's trading sentiment and flow
    - **High Vol/OI**: Active day trading or position adjustments
    - **Low Vol/OI**: Quiet day, existing positions holding
    """)

# --------------------------------------------------------------
# Export Functionality
# --------------------------------------------------------------
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📥 Export GEX (OI)"):
        csv = pivot_gex_oi.to_csv()
        st.download_button("Download", csv, f"{st.session_state.selected_ticker}_GEX_OI.csv", "text/csv")

with col2:
    if st.button("📥 Export GEX (Vol)"):
        csv = pivot_gex_vol.to_csv()
        st.download_button("Download", csv, f"{st.session_state.selected_ticker}_GEX_Vol.csv", "text/csv")

with col3:
    if st.button("📥 Export Vanna (OI)"):
        csv = pivot_vanna_oi.to_csv()
        st.download_button("Download", csv, f"{st.session_state.selected_ticker}_Vanna_OI.csv", "text/csv")

with col4:
    if st.button("📥 Export Vanna (Vol)"):
        csv = pivot_vanna_vol.to_csv()
        st.download_button("Download", csv, f"{st.session_state.selected_ticker}_Vanna_Vol.csv", "text/csv")

# --------------------------------------------------------------
# Earnings Calendar Section
# --------------------------------------------------------------
display_earnings_calendar()

# --------------------------------------------------------------
# Final Auto-Refresh Check (must be at the very end)
# --------------------------------------------------------------
# This is the final check that triggers the refresh
# It must be at the end of the script to work properly
current_time_final = time.time()
time_since_refresh_final = current_time_final - st.session_state.last_refresh

if time_since_refresh_final >= REFRESH_INTERVAL:
    # Update refresh tracking
    st.session_state.last_refresh = current_time_final
    st.session_state.refresh_count += 1

    # Clear all cached data to force fresh API calls
    st.cache_data.clear()

    # Preserve ticker selection across refresh
    current_ticker = st.session_state.get('selected_ticker', 'SPY')
    st.query_params.ticker = current_ticker

    # Force the refresh - this MUST be the last line
    st.rerun()
