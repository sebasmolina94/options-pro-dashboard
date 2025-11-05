# 🚀 Options Pro - Professional Options Flow Analysis

## 🎯 **What This Is**

A **professional-grade options flow analysis platform** comparable to institutional trading platforms, built with Python and Streamlit.

## ✨ **Key Features**

- ✅ **Real-time auto-refresh** (30-second updates)
- ✅ **31 high-volume tickers** (SPY, QQQ, AAPL, TSLA, NVDA, etc.)
- ✅ **4-tab analysis system**: NetGEX & NetVEX (both OI and Volume)
- ✅ **Unusual activity alerts** (high vol/OI ratios, large prints)
- ✅ **Earnings calendar integration**
- ✅ **Mobile-responsive design** (works on phones/tablets)
- ✅ **AI-powered trading plan generation**
- ✅ **Professional dark theme UI**

## 🚀 **Quick Start**

### **Option 1: Automatic Installation**
```bash
./install.sh
```

### **Option 2: Manual Installation**
```bash
# Install dependencies
pip3 install -r requirements.txt

# Setup environment
cp .env.template .env
# Edit .env with your Schwab API credentials

# Run the app
streamlit run app_enhanced.py --server.port 8502
```

## 🔑 **API Setup Required**

1. **Get free Schwab Developer Account**: https://developer.schwab.com/
2. **Create new app** with callback URL: `https://127.0.0.1:5001`
3. **Copy credentials** to `.env` file
4. **No trading account required** - read-only market data access

## 📊 **What You Get**

### **Professional Analysis Tools**:
- **Gamma Exposure (GEX)** - Market maker hedging pressure
- **Vanna Exposure (VEX)** - Volatility sensitivity analysis
- **Open Interest vs Volume** - Structural vs flow analysis
- **Strike-by-strike breakdown** with color coding

### **Real-Time Monitoring**:
- **Live price updates** every 30 seconds
- **Unusual activity detection** (high vol/OI, large prints)
- **Earnings calendar awareness**
- **Mobile access** for monitoring anywhere

### **AI Trading Intelligence**:
- **Volume-based intraday strategies**
- **OI-based structural positioning**
- **Risk management guidance**
- **Key level identification**

## 📱 **Mobile Access**

1. **Find your computer's IP**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
2. **On phone/tablet**: Go to `http://YOUR_IP:8502`
3. **Full functionality** on mobile devices

## 🎯 **Best Tickers to Start With**

- **Major ETFs**: SPY, QQQ, IWM (daily expirations)
- **Tech Giants**: AAPL, MSFT, NVDA, GOOGL, AMZN
- **High Volatility**: TSLA, META, COIN, PLTR
- **Sector ETFs**: XLF, XLK, XLE

## 🔧 **Troubleshooting**

### **Common Issues**:
- **"No ACCESS_TOKEN"**: Check .env file credentials
- **"Module not found"**: Run `pip3 install -r requirements.txt`
- **Rate limits**: Wait a few minutes, Schwab allows reasonable usage

### **Performance Tips**:
- **Use during market hours** for best data
- **Start with major tickers** (SPY, QQQ, AAPL)
- **Compare OI vs Volume tabs** for different insights

## 🏆 **What Makes This Special**

### **Institutional-Grade Features**:
- **Accurate calculations** matching professional platforms
- **Real-time data processing** with smart caching
- **Comprehensive ticker coverage** (31 high-volume options)
- **Mobile-first design** for modern trading

### **Unique Advantages**:
- **Both OI and Volume analysis** (most tools only show one)
- **AI trading plan generation** with market context
- **Unusual activity detection** with smart filtering
- **Free and open-source** (no monthly subscriptions)

## 📈 **Use Cases**

- **Day Trading**: Volume-based flow analysis for intraday moves
- **Swing Trading**: OI-based structural positioning
- **Risk Management**: Gamma/vanna exposure monitoring
- **Market Research**: Unusual activity and earnings timing

## 🎉 **Ready to Trade Like a Pro**

Once setup is complete, you'll have access to the same level of options flow analysis used by professional trading desks and hedge funds.

**No monthly fees. No account minimums. Just professional-grade analysis.**

---

**Questions?** Check `SETUP_INSTRUCTIONS.md` for detailed setup help.
