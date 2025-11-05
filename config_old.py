# config.py
from dataclasses import dataclass

@dataclass
class TickerConfig:
    symbol: str
    name: str
    multiplier: float = 100.0
    is_index: bool = False
    min_oi: int = 10
    has_daily_expirations: bool = False  # True for major indices/ETFs with daily options

# ============================================================================
# TOP PRIORITY TICKERS (Always at top of dropdown)
# ============================================================================
TOP_PRIORITY = [
    TickerConfig("SPY", "SPDR S&P 500 ETF", multiplier=100, has_daily_expirations=True),
    TickerConfig("QQQ", "Invesco QQQ Trust", multiplier=100, has_daily_expirations=True),
    TickerConfig("IWM", "iShares Russell 2000", multiplier=100, has_daily_expirations=True),
    TickerConfig("VIX", "CBOE Volatility Index", multiplier=100, has_daily_expirations=True),
]

# ============================================================================
# MAGNIFICENT 7 (Mega-Cap Tech Leaders)
# ============================================================================
MAG7 = [
    TickerConfig("AAPL", "Apple", multiplier=100),
    TickerConfig("MSFT", "Microsoft", multiplier=100),
    TickerConfig("NVDA", "NVIDIA", multiplier=100),
    TickerConfig("AMZN", "Amazon", multiplier=100),
    TickerConfig("GOOGL", "Google", multiplier=100),
    TickerConfig("META", "Meta", multiplier=100),
    TickerConfig("TSLA", "Tesla", multiplier=100),
]

# ============================================================================
# SECTOR ETFs & POPULAR FUNDS
# ============================================================================
SECTOR_ETFS = [
    TickerConfig("XLF", "Financial Select Sector SPDR", multiplier=100),
    TickerConfig("XLK", "Technology Select Sector SPDR", multiplier=100),
    TickerConfig("XLE", "Energy Select Sector SPDR", multiplier=100),
    TickerConfig("GLD", "SPDR Gold Trust", multiplier=100),
    TickerConfig("TLT", "iShares 20+ Year Treasury Bond", multiplier=100),
]

# ============================================================================
# SEMICONDUCTORS & CHIP EQUIPMENT
# ============================================================================
SEMICONDUCTORS = [
    TickerConfig("AMD", "Advanced Micro Devices", multiplier=100),
    TickerConfig("INTC", "Intel", multiplier=100),
    TickerConfig("AVGO", "Broadcom", multiplier=100),
    TickerConfig("ARM", "Arm Holdings", multiplier=100),
    TickerConfig("LRCX", "Lam Research", multiplier=100),
    TickerConfig("AMAT", "Applied Materials", multiplier=100),
    TickerConfig("KLAC", "KLA Corporation", multiplier=100),
]

# Technology & Growth Stocks
TECH_GROWTH = [
    TickerConfig("ARM", "Arm Holdings", multiplier=100),
    TickerConfig("LRCX", "Lam Research", multiplier=100),
    TickerConfig("CRWD", "CrowdStrike", multiplier=100),
    TickerConfig("RDDT", "Reddit", multiplier=100),
    TickerConfig("ORCL", "Oracle", multiplier=100),
    TickerConfig("AVGO", "Broadcom", multiplier=100),
    TickerConfig("WDC", "Western Digital", multiplier=100),
    TickerConfig("SMCI", "Super Micro Computer", multiplier=100),
    TickerConfig("BABA", "Alibaba", multiplier=100),
]

# Healthcare & Biotech
HEALTHCARE = [
    TickerConfig("HIMS", "Hims & Hers Health", multiplier=100),
    TickerConfig("NBIS", "Nebius Group", multiplier=100),
    TickerConfig("LLY", "Eli Lilly", multiplier=100),
    TickerConfig("UNH", "UnitedHealth Group", multiplier=100),
]

# Industrial & Energy
INDUSTRIAL_ENERGY = [
    TickerConfig("BA", "Boeing", multiplier=100),
    TickerConfig("XOM", "Exxon Mobil", multiplier=100),
    TickerConfig("CVX", "Chevron", multiplier=100),
    TickerConfig("RKLB", "Rocket Lab", multiplier=100),
    TickerConfig("BE", "Bloom Energy", multiplier=100),
    TickerConfig("ASTS", "AST SpaceMobile", multiplier=100),
    TickerConfig("MP", "MP Materials", multiplier=100),
    TickerConfig("IREN", "Iris Energy", multiplier=100),
]

# Software & Apps
SOFTWARE_APPS = [
    TickerConfig("APP", "AppLovin", multiplier=100),
    TickerConfig("ALAB", "Astera Labs", multiplier=100),
    TickerConfig("CRWV", "Crown Electrokinetics", multiplier=100),
    TickerConfig("CRCL", "Circle Internet Financial", multiplier=100),
]

# Financial & Consumer
FINANCIAL_CONSUMER = [
    TickerConfig("UPST", "Upstart", multiplier=100),
    TickerConfig("RGTI", "Rigetti Computing", multiplier=100),
    TickerConfig("RKT", "Rocket Companies", multiplier=100),
    TickerConfig("CMG", "Chipotle Mexican Grill", multiplier=100),
    TickerConfig("HOOD", "Robinhood", multiplier=100),
    TickerConfig("CVNA", "Carvana", multiplier=100),
]

# Cloud & Data Platforms
CLOUD_DATA = [
    TickerConfig("SNOW", "Snowflake", multiplier=100),
    TickerConfig("MDB", "MongoDB", multiplier=100),
]

# Major Banks & Financial Services
BANKS_FINANCE = [
    TickerConfig("JPM", "JPMorgan Chase", multiplier=100),
    TickerConfig("BAC", "Bank of America", multiplier=100),
    TickerConfig("XYZ", "Block (formerly Square)", multiplier=100),
    TickerConfig("V", "Visa", multiplier=100),
]

# E-commerce & Consumer Tech
ECOMMERCE_CONSUMER = [
    TickerConfig("SHOP", "Shopify", multiplier=100),
    TickerConfig("ROKU", "Roku", multiplier=100),
    TickerConfig("DIS", "Disney", multiplier=100),
]

# Clean Energy & Utilities
CLEAN_ENERGY = [
    TickerConfig("ENPH", "Enphase Energy", multiplier=100),
    TickerConfig("FSLR", "First Solar", multiplier=100),
]

# Cybersecurity & Identity
CYBERSECURITY = [
    TickerConfig("OKTA", "Okta", multiplier=100),
    TickerConfig("ZS", "Zscaler", multiplier=100),
    TickerConfig("PANW", "Palo Alto Networks", multiplier=100),
]

# Biotech & Pharma
BIOTECH_PHARMA = [
    TickerConfig("MRNA", "Moderna", multiplier=100),
    TickerConfig("REGN", "Regeneron Pharmaceuticals", multiplier=100),
]

# Media & Entertainment
MEDIA_ENTERTAINMENT = [
    TickerConfig("SPOT", "Spotify", multiplier=100),
]

# Industrial & Manufacturing
INDUSTRIAL_MANUFACTURING = [
    TickerConfig("CAT", "Caterpillar", multiplier=100),
    TickerConfig("DE", "Deere & Company", multiplier=100),
]

# Travel & Hospitality
TRAVEL_HOSPITALITY = [
    TickerConfig("ABNB", "Airbnb", multiplier=100),
]

# Enterprise Software & SaaS
ENTERPRISE_SAAS = [
    TickerConfig("DDOG", "Datadog", multiplier=100),
    TickerConfig("NET", "Cloudflare", multiplier=100),
    TickerConfig("WDAY", "Workday", multiplier=100),
    TickerConfig("ADBE", "Adobe", multiplier=100),
    TickerConfig("NOW", "ServiceNow", multiplier=100),
]

# Payments & Fintech
PAYMENTS_FINTECH = [
    TickerConfig("PYPL", "PayPal", multiplier=100),
    TickerConfig("MA", "Mastercard", multiplier=100),
    TickerConfig("AFRM", "Affirm", multiplier=100),
]

# Retail & Consumer
RETAIL_CONSUMER = [
    TickerConfig("WMT", "Walmart", multiplier=100),
    TickerConfig("TGT", "Target", multiplier=100),
    TickerConfig("COST", "Costco", multiplier=100),
    TickerConfig("HD", "Home Depot", multiplier=100),
]

# Gaming & Metaverse
GAMING_METAVERSE = [
    TickerConfig("RBLX", "Roblox", multiplier=100),
    TickerConfig("U", "Unity Software", multiplier=100),
]

# Big Pharma & Healthcare
BIG_PHARMA = [
    TickerConfig("JNJ", "Johnson & Johnson", multiplier=100),
    TickerConfig("PFE", "Pfizer", multiplier=100),
    TickerConfig("ABBV", "AbbVie", multiplier=100),
]

# Automotive & Transportation
AUTOMOTIVE = [
    TickerConfig("F", "Ford", multiplier=100),
    TickerConfig("GM", "General Motors", multiplier=100),
    TickerConfig("RIVN", "Rivian", multiplier=100),
]

# Defense & Aerospace
DEFENSE_AEROSPACE = [
    TickerConfig("LMT", "Lockheed Martin", multiplier=100),
]

# Telecom & Communications
TELECOM = [
    TickerConfig("VZ", "Verizon", multiplier=100),
    TickerConfig("T", "AT&T", multiplier=100),
    TickerConfig("TMUS", "T-Mobile", multiplier=100),
]

# Investment Banking & Financial Services
INVESTMENT_BANKING = [
    TickerConfig("BRK.B", "Berkshire Hathaway", multiplier=100),
    TickerConfig("GS", "Goldman Sachs", multiplier=100),
    TickerConfig("MS", "Morgan Stanley", multiplier=100),
]

# Food & Beverage
FOOD_BEVERAGE = [
    TickerConfig("KO", "Coca-Cola", multiplier=100),
    TickerConfig("PEP", "PepsiCo", multiplier=100),
    TickerConfig("MCD", "McDonald's", multiplier=100),
    TickerConfig("SBUX", "Starbucks", multiplier=100),
]

# Industrial Conglomerates
INDUSTRIAL_CONGLOMERATES = [
    TickerConfig("MMM", "3M", multiplier=100),
    TickerConfig("HON", "Honeywell", multiplier=100),
]

ALL_TICKERS = TICKERS + MAG7 + HIGH_VOLUME_STOCKS + POPULAR_ETFS + TECH_GROWTH + HEALTHCARE + INDUSTRIAL_ENERGY + SOFTWARE_APPS + FINANCIAL_CONSUMER + CLOUD_DATA + BANKS_FINANCE + ECOMMERCE_CONSUMER + CLEAN_ENERGY + CYBERSECURITY + BIOTECH_PHARMA + MEDIA_ENTERTAINMENT + INDUSTRIAL_MANUFACTURING + TRAVEL_HOSPITALITY + ENTERPRISE_SAAS + PAYMENTS_FINTECH + RETAIL_CONSUMER + GAMING_METAVERSE + BIG_PHARMA + AUTOMOTIVE + DEFENSE_AEROSPACE + TELECOM + INVESTMENT_BANKING + FOOD_BEVERAGE + INDUSTRIAL_CONGLOMERATES
