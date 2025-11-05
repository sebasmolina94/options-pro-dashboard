# SkylitAI Desktop UI Clone

A professional options flow dashboard that replicates the SkylitAI desktop interface with dark theme, real-time data, and advanced Greek exposures.

## Features

- **Dark Professional Theme** - Thinkorswim-style interface
- **Real-time Options Data** - Via Schwab API integration
- **Greek Exposures** - GEX (Gamma) and Vanna calculations
- **Interactive Table** - Strike prices vs expiration dates
- **Color-coded Cells** - Green (positive), Red (negative), Yellow (hotspots)
- **Live Price Display** - Current underlying prices
- **Export Functionality** - Download data as CSV

## Quick Start

### 1. Install Dependencies

```bash
python setup.py
```

Or manually:
```bash
pip install -r requirements.txt
```

### 2. Setup Schwab API Credentials

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` with your Schwab API credentials:
   ```
   SCHWAB_APP_KEY=your_app_key_here
   SCHWAB_APP_SECRET=your_app_secret_here
   SCHWAB_CALLBACK_URL=https://127.0.0.1
   ```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Schwab API Setup

1. Visit [Schwab Developer Portal](https://developer.schwab.com/)
2. Create a developer account
3. Register a new application
4. Get your App Key and App Secret
5. Set callback URL to `https://127.0.0.1`

## File Structure

```
├── app.py              # Main Streamlit application
├── core.py             # Core calculations (Greeks, exposures)
├── schwab.py           # Schwab API integration
├── config.py           # Ticker configurations
├── requirements.txt    # Python dependencies
├── .env.template       # Environment variables template
├── setup.py           # Setup script
└── README_SKYLITAI.md # This file
```

## Supported Tickers

### Indices & ETFs
- SPY - SPDR S&P 500 ETF
- SPX - S&P 500 Index
- IWM - iShares Russell 2000
- QQQ - Invesco QQQ Trust

### Magnificent 7
- AAPL - Apple
- MSFT - Microsoft
- NVDA - NVIDIA
- AMZN - Amazon
- GOOGL - Google
- META - Meta
- TSLA - Tesla

## Usage

1. **Select Ticker** - Choose from dropdown menu
2. **View Live Price** - Current underlying price displayed
3. **Toggle Mode** - Switch between NetGEX and NetVEX (Vanna)
4. **Analyze Table** - Strike prices (rows) vs expiration dates (columns)
5. **Identify Hotspots** - Yellow highlighted cells show maximum exposure
6. **Export Data** - Download current view as CSV

## Color Coding

- 🟢 **Green** - Positive exposure (supportive)
- 🔴 **Red** - Negative exposure (resistance)
- 🟡 **Yellow** - Maximum absolute exposure (hotspot)

## Calculations

### GEX (Gamma Exposure)
- Measures market maker hedging flow
- Positive GEX = Supportive (buy dips, sell rallies)
- Negative GEX = Amplifying (sell dips, buy rallies)

### Vanna Exposure
- Sensitivity of delta to volatility changes
- Important for understanding vol/price relationships

## Troubleshooting

### Common Issues

1. **"Schwab API token missing"**
   - Check your `.env` file exists and has correct credentials
   - Ensure you've completed Schwab API authentication

2. **"No options data available"**
   - Check ticker symbol is correct
   - Verify market hours (options data may be limited outside trading hours)
   - Try a different ticker

3. **Empty or missing data**
   - Increase minimum open interest threshold in `config.py`
   - Check network connection
   - Verify Schwab API limits haven't been exceeded

### Performance Tips

- Data is cached for 3 minutes to reduce API calls
- Use during market hours for best data quality
- Limit to 4 nearest expirations for optimal performance

## Development

To modify or extend the application:

1. **Add new tickers** - Edit `config.py`
2. **Adjust calculations** - Modify `core.py`
3. **Change UI styling** - Update CSS in `app.py`
4. **Add new metrics** - Extend exposure calculations

## License

This project is for educational and personal use only. Please respect Schwab API terms of service and rate limits.
