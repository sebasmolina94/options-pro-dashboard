# 🚀 EzOptions Enhanced - Setup Instructions

## 📋 **Prerequisites**

- Python 3.8+ installed
- Schwab Developer Account (free)

## 🔑 **Step 1: Get Schwab API Credentials**

1. **Go to**: https://developer.schwab.com/
2. **Create account** (free developer account)
3. **Create new app**:
   - App Name: "EzOptions Personal"
   - Callback URL: `https://127.0.0.1:5001`
   - Description: "Personal options flow analysis"
4. **Copy your credentials**:
   - App Key (Consumer Key)
   - App Secret (Consumer Secret)

## ⚙️ **Step 2: Configure Environment**

1. **Copy the template**:
   ```bash
   cp .env.template .env
   ```

2. **Edit .env file** with your credentials:
   ```
   SCHWAB_APP_KEY="your_actual_app_key_here"
   SCHWAB_APP_SECRET="your_actual_app_secret_here"
   SCHWAB_CALLBACK_URL="https://127.0.0.1:5001"
   ```

## 📦 **Step 3: Install Dependencies**

```bash
pip install streamlit pandas numpy scipy python-dotenv schwabdev
```

## 🚀 **Step 4: Run the Application**

```bash
streamlit run app_enhanced.py --server.port 8502
```

## 📱 **Step 5: Access on Mobile**

1. **Find your computer's IP**:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **On your phone**, go to: `http://YOUR_IP_ADDRESS:8502`

## 🎯 **Features Included**

- ✅ **Real-time auto-refresh** (30 seconds)
- ✅ **31 high-volume tickers** (SPY, QQQ, AAPL, TSLA, etc.)
- ✅ **4-tab analysis**: NetGEX & NetVEX (both OI and Volume)
- ✅ **Unusual activity alerts**
- ✅ **Earnings calendar integration**
- ✅ **Mobile-responsive design**
- ✅ **AI trading plan generation**

## 🔧 **Troubleshooting**

### **"No ACCESS_TOKEN" Error**:
- Check your .env file has correct credentials
- Make sure .env is in the same folder as app_enhanced.py
- Restart the app after editing .env

### **"Module not found" Error**:
```bash
pip install --upgrade streamlit pandas numpy scipy python-dotenv schwabdev
```

### **API Rate Limits**:
- Schwab allows reasonable usage for personal accounts
- If you hit limits, wait a few minutes and try again

## 📊 **Usage Tips**

1. **Best tickers to start with**: SPY, QQQ, AAPL, TSLA, NVDA
2. **Compare OI vs Volume tabs** for different insights
3. **Watch unusual activity alerts** for trading opportunities
4. **Use mobile version** for monitoring on the go
5. **Auto-refresh keeps data current** during market hours

## 🎉 **You're Ready!**

Once setup is complete, you'll have a professional-grade options flow analysis platform comparable to SkylitAI and SpotGamma!

---

**Need help?** Check that your .env file is configured correctly and all dependencies are installed.
