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
    TickerConfig("SPX", "S&P 500 Index", multiplier=100, has_daily_expirations=True),
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
    TickerConfig("WDC", "Western Digital", multiplier=100),
    TickerConfig("SMCI", "Super Micro Computer", multiplier=100),
]

# ============================================================================
# ENTERPRISE SOFTWARE & SAAS
# ============================================================================
ENTERPRISE_SAAS = [
    TickerConfig("CRM", "Salesforce", multiplier=100),
    TickerConfig("ORCL", "Oracle", multiplier=100),
    TickerConfig("DDOG", "Datadog", multiplier=100),
    TickerConfig("NET", "Cloudflare", multiplier=100),
    TickerConfig("WDAY", "Workday", multiplier=100),
    TickerConfig("ADBE", "Adobe", multiplier=100),
    TickerConfig("NOW", "ServiceNow", multiplier=100),
    TickerConfig("SNOW", "Snowflake", multiplier=100),
    TickerConfig("MDB", "MongoDB", multiplier=100),
]

# ============================================================================
# CYBERSECURITY & IDENTITY
# ============================================================================
CYBERSECURITY = [
    TickerConfig("CRWD", "CrowdStrike", multiplier=100),
    TickerConfig("OKTA", "Okta", multiplier=100),
    TickerConfig("ZS", "Zscaler", multiplier=100),
    TickerConfig("PANW", "Palo Alto Networks", multiplier=100),
    TickerConfig("FTNT", "Fortinet", multiplier=100),
]

# ============================================================================
# INVESTMENT BANKING & FINANCIAL SERVICES
# ============================================================================
INVESTMENT_BANKING = [
    TickerConfig("BRK.B", "Berkshire Hathaway", multiplier=100),
    TickerConfig("GS", "Goldman Sachs", multiplier=100),
    TickerConfig("MS", "Morgan Stanley", multiplier=100),
    TickerConfig("JPM", "JPMorgan Chase", multiplier=100),
    TickerConfig("BAC", "Bank of America", multiplier=100),
    TickerConfig("AXP", "American Express", multiplier=100),
    TickerConfig("COF", "Capital One", multiplier=100),
]

# ============================================================================
# PAYMENTS & FINTECH
# ============================================================================
PAYMENTS_FINTECH = [
    TickerConfig("PYPL", "PayPal", multiplier=100),
    TickerConfig("MA", "Mastercard", multiplier=100),
    TickerConfig("V", "Visa", multiplier=100),
    TickerConfig("XYZ", "Block (formerly Square)", multiplier=100),
    TickerConfig("AFRM", "Affirm", multiplier=100),
    TickerConfig("COIN", "Coinbase", multiplier=100),
]

# ============================================================================
# RETAIL & CONSUMER
# ============================================================================
RETAIL_CONSUMER = [
    TickerConfig("WMT", "Walmart", multiplier=100),
    TickerConfig("TGT", "Target", multiplier=100),
    TickerConfig("COST", "Costco", multiplier=100),
    TickerConfig("HD", "Home Depot", multiplier=100),
    TickerConfig("SHOP", "Shopify", multiplier=100),
    TickerConfig("CMG", "Chipotle Mexican Grill", multiplier=100),
]

# ============================================================================
# FOOD & BEVERAGE
# ============================================================================
FOOD_BEVERAGE = [
    TickerConfig("KO", "Coca-Cola", multiplier=100),
    TickerConfig("PEP", "PepsiCo", multiplier=100),
    TickerConfig("MCD", "McDonald's", multiplier=100),
    TickerConfig("SBUX", "Starbucks", multiplier=100),
]

# ============================================================================
# STREAMING & MEDIA
# ============================================================================
STREAMING_MEDIA = [
    TickerConfig("NFLX", "Netflix", multiplier=100),
    TickerConfig("DIS", "Disney", multiplier=100),
    TickerConfig("SPOT", "Spotify", multiplier=100),
    TickerConfig("ROKU", "Roku", multiplier=100),
]

# ============================================================================
# GAMING & METAVERSE
# ============================================================================
GAMING_METAVERSE = [
    TickerConfig("RBLX", "Roblox", multiplier=100),
    TickerConfig("U", "Unity Software", multiplier=100),
]

# ============================================================================
# TRAVEL & HOSPITALITY
# ============================================================================
TRAVEL_HOSPITALITY = [
    TickerConfig("ABNB", "Airbnb", multiplier=100),
    TickerConfig("UBER", "Uber", multiplier=100),
    TickerConfig("UPS", "United Parcel Service", multiplier=100),
    TickerConfig("FDX", "FedEx", multiplier=100),
]

# ============================================================================
# BIG PHARMA & HEALTHCARE
# ============================================================================
BIG_PHARMA = [
    TickerConfig("JNJ", "Johnson & Johnson", multiplier=100),
    TickerConfig("PFE", "Pfizer", multiplier=100),
    TickerConfig("ABBV", "AbbVie", multiplier=100),
    TickerConfig("LLY", "Eli Lilly", multiplier=100),
    TickerConfig("UNH", "UnitedHealth Group", multiplier=100),
]

# ============================================================================
# BIOTECH & PHARMA
# ============================================================================
BIOTECH_PHARMA = [
    TickerConfig("MRNA", "Moderna", multiplier=100),
    TickerConfig("REGN", "Regeneron Pharmaceuticals", multiplier=100),
]

# ============================================================================
# MEDICAL DEVICES & LIFE SCIENCES
# ============================================================================
MEDICAL_DEVICES = [
    TickerConfig("ISRG", "Intuitive Surgical", multiplier=100),
    TickerConfig("TMO", "Thermo Fisher Scientific", multiplier=100),
    TickerConfig("DHR", "Danaher", multiplier=100),
]

# ============================================================================
# AUTOMOTIVE & TRANSPORTATION
# ============================================================================
AUTOMOTIVE = [
    TickerConfig("F", "Ford", multiplier=100),
    TickerConfig("GM", "General Motors", multiplier=100),
    TickerConfig("RIVN", "Rivian", multiplier=100),
]

# ============================================================================
# INDUSTRIAL & MANUFACTURING
# ============================================================================
INDUSTRIAL_MANUFACTURING = [
    TickerConfig("CAT", "Caterpillar", multiplier=100),
    TickerConfig("DE", "Deere & Company", multiplier=100),
    TickerConfig("MMM", "3M", multiplier=100),
    TickerConfig("HON", "Honeywell", multiplier=100),
    TickerConfig("BA", "Boeing", multiplier=100),
]

# ============================================================================
# DEFENSE & AEROSPACE
# ============================================================================
DEFENSE_AEROSPACE = [
    TickerConfig("LMT", "Lockheed Martin", multiplier=100),
]

# ============================================================================
# TELECOM & COMMUNICATIONS
# ============================================================================
TELECOM = [
    TickerConfig("VZ", "Verizon", multiplier=100),
    TickerConfig("T", "AT&T", multiplier=100),
    TickerConfig("TMUS", "T-Mobile", multiplier=100),
]

# ============================================================================
# ENERGY & OIL
# ============================================================================
ENERGY_OIL = [
    TickerConfig("XOM", "Exxon Mobil", multiplier=100),
    TickerConfig("CVX", "Chevron", multiplier=100),
]

# ============================================================================
# CLEAN ENERGY & UTILITIES
# ============================================================================
CLEAN_ENERGY = [
    TickerConfig("ENPH", "Enphase Energy", multiplier=100),
    TickerConfig("FSLR", "First Solar", multiplier=100),
    TickerConfig("NEE", "NextEra Energy", multiplier=100),
    TickerConfig("DUK", "Duke Energy", multiplier=100),
]

# ============================================================================
# REAL ESTATE & INFRASTRUCTURE
# ============================================================================
REAL_ESTATE = [
    TickerConfig("PLD", "Prologis", multiplier=100),
    TickerConfig("AMT", "American Tower", multiplier=100),
    TickerConfig("EQIX", "Equinix", multiplier=100),
]

# ============================================================================
# MATERIALS & CHEMICALS
# ============================================================================
MATERIALS_CHEMICALS = [
    TickerConfig("LIN", "Linde", multiplier=100),
    TickerConfig("APD", "Air Products", multiplier=100),
    TickerConfig("SHW", "Sherwin-Williams", multiplier=100),
    TickerConfig("ECL", "Ecolab", multiplier=100),
]

# ============================================================================
# CONSTRUCTION & INFRASTRUCTURE
# ============================================================================
CONSTRUCTION_INFRASTRUCTURE = [
    TickerConfig("UNP", "Union Pacific", multiplier=100),
    TickerConfig("CSX", "CSX Corporation", multiplier=100),
]

# ============================================================================
# ENTERPRISE HARDWARE
# ============================================================================
ENTERPRISE_HARDWARE = [
    TickerConfig("DELL", "Dell Technologies", multiplier=100),
    TickerConfig("HPQ", "HP Inc.", multiplier=100),
]

# ============================================================================
# EMERGING TECH & GROWTH
# ============================================================================
EMERGING_TECH = [
    TickerConfig("PLTR", "Palantir", multiplier=100),
    TickerConfig("RDDT", "Reddit", multiplier=100),
    TickerConfig("BABA", "Alibaba", multiplier=100),
    TickerConfig("HIMS", "Hims & Hers Health", multiplier=100),
    TickerConfig("NBIS", "Nebius Group", multiplier=100),
    TickerConfig("APP", "AppLovin", multiplier=100),
    TickerConfig("ALAB", "Astera Labs", multiplier=100),
    TickerConfig("RKLB", "Rocket Lab", multiplier=100),
    TickerConfig("ASTS", "AST SpaceMobile", multiplier=100),
    TickerConfig("MP", "MP Materials", multiplier=100),
    TickerConfig("BE", "Bloom Energy", multiplier=100),
    TickerConfig("IREN", "Iris Energy", multiplier=100),
    TickerConfig("UPST", "Upstart", multiplier=100),
    TickerConfig("RGTI", "Rigetti Computing", multiplier=100),
    TickerConfig("RKT", "Rocket Companies", multiplier=100),
    TickerConfig("HOOD", "Robinhood", multiplier=100),
    TickerConfig("CVNA", "Carvana", multiplier=100),
    TickerConfig("CRWV", "Crown Electrokinetics", multiplier=100),
    TickerConfig("CRCL", "Circle Internet Financial", multiplier=100),
]

# ============================================================================
# ALL TICKERS (Organized by Groups)
# ============================================================================
ALL_TICKERS = (
    TOP_PRIORITY +
    MAG7 +
    SECTOR_ETFS +
    SEMICONDUCTORS +
    ENTERPRISE_SAAS +
    CYBERSECURITY +
    INVESTMENT_BANKING +
    PAYMENTS_FINTECH +
    RETAIL_CONSUMER +
    FOOD_BEVERAGE +
    STREAMING_MEDIA +
    GAMING_METAVERSE +
    TRAVEL_HOSPITALITY +
    BIG_PHARMA +
    BIOTECH_PHARMA +
    MEDICAL_DEVICES +
    AUTOMOTIVE +
    INDUSTRIAL_MANUFACTURING +
    DEFENSE_AEROSPACE +
    TELECOM +
    ENERGY_OIL +
    CLEAN_ENERGY +
    REAL_ESTATE +
    MATERIALS_CHEMICALS +
    CONSTRUCTION_INFRASTRUCTURE +
    ENTERPRISE_HARDWARE +
    EMERGING_TECH
)
