"""
Trading Plan Generator based on GEX and Vanna Analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

def analyze_gex_levels(pivot_df: pd.DataFrame, current_price: float) -> Dict:
    """Analyze GEX levels to identify key support/resistance zones"""
    
    # Find strikes with highest absolute GEX
    gex_analysis = {}
    
    # Get all GEX values across all expirations
    all_gex = []
    for col in pivot_df.columns:
        if col != 'Strike':
            values = pivot_df[col].dropna()
            all_gex.extend(values.tolist())
    
    if not all_gex:
        return {"error": "No GEX data available"}
    
    # Find key levels
    max_positive_gex = max([x for x in all_gex if x > 0], default=0)
    max_negative_gex = min([x for x in all_gex if x < 0], default=0)
    
    # Find strikes corresponding to these levels
    positive_strikes = []
    negative_strikes = []
    
    for idx, row in pivot_df.iterrows():
        strike = row['Strike']
        for col in pivot_df.columns:
            if col != 'Strike':
                value = row[col]
                if pd.notna(value):
                    if value == max_positive_gex:
                        positive_strikes.append(strike)
                    elif value == max_negative_gex:
                        negative_strikes.append(strike)
    
    return {
        "max_positive_gex": max_positive_gex,
        "max_negative_gex": max_negative_gex,
        "positive_strikes": list(set(positive_strikes)),
        "negative_strikes": list(set(negative_strikes)),
        "current_price": current_price
    }

def analyze_vanna_exposure(pivot_df: pd.DataFrame, current_price: float) -> Dict:
    """Analyze Vanna exposure for volatility trading opportunities"""
    
    # Get all Vanna values
    all_vanna = []
    for col in pivot_df.columns:
        if col != 'Strike':
            values = pivot_df[col].dropna()
            all_vanna.extend(values.tolist())
    
    if not all_vanna:
        return {"error": "No Vanna data available"}
    
    total_vanna = sum(all_vanna)
    max_vanna = max(all_vanna, key=abs)
    
    return {
        "total_vanna": total_vanna,
        "max_vanna": max_vanna,
        "vanna_bias": "positive" if total_vanna > 0 else "negative",
        "current_price": current_price
    }

def generate_trading_plan(ticker: str, mode: str, pivot_df: pd.DataFrame, current_price: float, is_volume_based: bool = False) -> str:
    """Generate a comprehensive trading plan based on GEX/Vanna analysis"""

    if "GEX" in mode:
        analysis = analyze_gex_levels(pivot_df, current_price)
        plan = generate_gex_trading_plan(ticker, analysis, is_volume_based)
    else:  # Vanna/VEX
        analysis = analyze_vanna_exposure(pivot_df, current_price)
        plan = generate_vanna_trading_plan(ticker, analysis, is_volume_based)

    return plan

def generate_gex_trading_plan(ticker: str, analysis: Dict, is_volume_based: bool = False) -> str:
    """Generate trading plan based on GEX analysis"""

    if "error" in analysis:
        return f"❌ Unable to generate trading plan: {analysis['error']}"

    current_price = analysis["current_price"]
    max_pos_gex = analysis["max_positive_gex"]
    max_neg_gex = analysis["max_negative_gex"]
    pos_strikes = analysis["positive_strikes"]
    neg_strikes = analysis["negative_strikes"]

    # Different headers for volume vs OI analysis
    data_type = "VOLUME FLOW" if is_volume_based else "OPEN INTEREST"
    plan_type = "FLOW" if is_volume_based else "STRUCTURAL"

    plan = f"""
🎯 **{ticker} GEX {plan_type} TRADING PLAN**
Current Price: ${current_price:.2f}
Data Source: {data_type}

📊 **GEX ANALYSIS:**
• Max Positive GEX: ${max_pos_gex:,.0f}K ({'Flow support' if is_volume_based else 'Support levels'})
• Max Negative GEX: ${max_neg_gex:,.0f}K ({'Flow resistance' if is_volume_based else 'Resistance levels'})

🟢 **{'BULLISH FLOW ZONES' if is_volume_based else 'SUPPORT ZONES'}** (Positive GEX):
"""
    
    if pos_strikes:
        for strike in sorted(pos_strikes):
            distance = ((strike - current_price) / current_price) * 100
            plan += f"• ${strike:.0f} ({distance:+.1f}% from current)\n"

        if is_volume_based:
            plan += f"""
💡 **Volume Flow Strategy:**
- Heavy call volume/gamma buying at these levels TODAY
- Indicates bullish sentiment and momentum
- Consider following the flow with calls/long positions
- Watch for continuation if volume persists
"""
        else:
            plan += f"""
💡 **Structural Support Strategy:**
- Positive GEX creates buying pressure as MM hedge
- Look for bounces at ${min(pos_strikes):.0f} level
- Consider buying calls/selling puts near support
"""

    plan += f"\n🔴 **{'BEARISH FLOW ZONES' if is_volume_based else 'RESISTANCE ZONES'}** (Negative GEX):\n"
    
    if neg_strikes:
        for strike in sorted(neg_strikes):
            distance = ((strike - current_price) / current_price) * 100
            plan += f"• ${strike:.0f} ({distance:+.1f}% from current)\n"

        if is_volume_based:
            plan += f"""
💡 **Volume Flow Strategy:**
- Heavy put volume/gamma selling at these levels TODAY
- Indicates bearish sentiment and selling pressure
- Consider following the flow with puts/short positions
- Watch for breakdown if volume continues
"""
        else:
            plan += f"""
💡 **Structural Resistance Strategy:**
- Negative GEX creates selling pressure as MM hedge
- Expect rejection at ${max(neg_strikes):.0f} level
- Consider selling calls/buying puts near resistance
"""

    # Overall bias with volume-specific interpretation
    if max_pos_gex > abs(max_neg_gex):
        if is_volume_based:
            bias = "BULLISH FLOW (More call volume/gamma buying)"
            strategy = "Follow the bullish volume momentum"
        else:
            bias = "BULLISH (More positive GEX support)"
            strategy = "Look for dip-buying opportunities"
    else:
        if is_volume_based:
            bias = "BEARISH FLOW (More put volume/gamma selling)"
            strategy = "Follow the bearish volume momentum"
        else:
            bias = "BEARISH (More negative GEX resistance)"
            strategy = "Look for rally-selling opportunities"

    # Risk management section
    if is_volume_based:
        risk_section = f"""
⚠️ **VOLUME FLOW RISK MANAGEMENT:**
- Volume patterns can reverse quickly
- High volume = High conviction, but watch for exhaustion
- Compare with OI-based levels for confirmation
- Volume spikes often precede trend changes
- Monitor for volume divergences vs price action
"""
    else:
        risk_section = f"""
⚠️ **STRUCTURAL RISK MANAGEMENT:**
- Watch for GEX level breaks (momentum acceleration)
- High GEX = Low volatility environment
- Low GEX = High volatility potential
- Structural levels tend to hold over multiple sessions
"""

    plan += f"""
📈 **OVERALL BIAS:** {bias}
🎯 **PRIMARY STRATEGY:** {strategy}

{risk_section}
"""
    
    return plan

def generate_vanna_trading_plan(ticker: str, analysis: Dict, is_volume_based: bool = False) -> str:
    """Generate trading plan based on Vanna analysis"""

    if "error" in analysis:
        return f"❌ Unable to generate trading plan: {analysis['error']}"

    current_price = analysis["current_price"]
    total_vanna = analysis["total_vanna"]
    max_vanna = analysis["max_vanna"]
    vanna_bias = analysis["vanna_bias"]

    # Different headers for volume vs OI analysis
    data_type = "VOLUME FLOW" if is_volume_based else "OPEN INTEREST"
    plan_type = "FLOW" if is_volume_based else "STRUCTURAL"

    plan = f"""
🎯 **{ticker} VANNA {plan_type} TRADING PLAN**
Current Price: ${current_price:.2f}
Data Source: {data_type}

📊 **VANNA ANALYSIS:**
• Total Vanna Exposure: ${total_vanna:,.0f}K
• Max Single Vanna: ${max_vanna:,.0f}K
• Vanna Bias: {vanna_bias.upper()}

🌊 **{'VOLATILITY FLOW SCENARIOS' if is_volume_based else 'VOLATILITY SCENARIOS'}:**
"""
    
    if vanna_bias == "positive":
        if is_volume_based:
            plan += f"""
🟢 **POSITIVE VANNA FLOW (Volume-Based):**
• Heavy call volume creating positive vanna TODAY
• Rising Vol → More aggressive call buying
• Falling Vol → Reduced call interest

💡 **VOLUME FLOW STRATEGIES:**
1. **Follow the Flow:**
   - Today's call volume suggests bullish vol positioning
   - Consider joining the trend with similar positions

2. **Momentum Continuation:**
   - Volume-driven vanna often continues short-term
   - Look for vol expansion to amplify moves

3. **Flow Exhaustion Watch:**
   - Monitor for volume decline (flow reversal)
   - High volume days often followed by consolidation
"""
        else:
            plan += f"""
🟢 **POSITIVE VANNA ENVIRONMENT (Structural):**
• Rising Vol → Delta increases → Buying pressure
• Falling Vol → Delta decreases → Selling pressure

💡 **STRUCTURAL STRATEGIES:**
1. **Vol Expansion Play:**
   - Buy straddles/strangles before events
   - Positive vanna amplifies upward moves

2. **Momentum Strategy:**
   - Rising prices + rising vol = accelerated buying
   - Look for breakout continuation patterns

3. **Vol Crush Protection:**
   - Avoid naked long options after events
   - Consider spreads to limit vega exposure
"""
    else:
        if is_volume_based:
            plan += f"""
🔴 **NEGATIVE VANNA FLOW (Volume-Based):**
• Heavy put volume creating negative vanna TODAY
• Rising Vol → More aggressive put buying
• Falling Vol → Reduced put interest

💡 **VOLUME FLOW STRATEGIES:**
1. **Follow the Bearish Flow:**
   - Today's put volume suggests bearish vol positioning
   - Consider defensive or bearish strategies

2. **Contrarian Opportunity:**
   - Excessive put volume can signal capitulation
   - Watch for reversal if volume becomes extreme

3. **Vol Spike Trading:**
   - Put volume often drives vol higher
   - Consider vol selling after spikes
"""
        else:
            plan += f"""
🔴 **NEGATIVE VANNA ENVIRONMENT (Structural):**
• Rising Vol → Delta decreases → Selling pressure
• Falling Vol → Delta increases → Buying pressure

💡 **STRUCTURAL STRATEGIES:**
1. **Vol Contraction Play:**
   - Sell premium after high vol events
   - Negative vanna supports mean reversion

2. **Contrarian Strategy:**
   - Fading moves in high vol environments
   - Look for reversal patterns

3. **Range Trading:**
   - Negative vanna creates natural bounds
   - Iron condors/butterflies in range
"""
    
    # Volatility regime assessment
    if abs(total_vanna) > 1000000:  # 1M threshold
        vol_regime = "HIGH VANNA (Significant vol sensitivity)"
        impact = "Major price moves likely on vol changes"
    else:
        vol_regime = "LOW VANNA (Limited vol sensitivity)"
        impact = "Price moves less dependent on vol changes"
    
    plan += f"""
📊 **VOLATILITY REGIME:** {vol_regime}
🎯 **EXPECTED IMPACT:** {impact}

⚠️ **RISK MANAGEMENT:**
- Monitor VIX/vol indicators closely
- High vanna = High vol sensitivity
- Consider vol-adjusted position sizing
- Watch for vol regime changes (earnings, events)

🕐 **TIMING CONSIDERATIONS:**
- Pre-event: Vanna effects amplified
- Post-event: Vol crush impacts vanna exposure
- Intraday: Vanna effects strongest during vol spikes
"""
    
    return plan

def get_key_levels(pivot_df: pd.DataFrame, current_price: float) -> Dict:
    """Extract key support/resistance levels for quick reference"""
    
    levels = {
        "support": [],
        "resistance": [],
        "current_price": current_price
    }
    
    for idx, row in pivot_df.iterrows():
        strike = row['Strike']
        
        # Check if this strike has significant GEX across expirations
        total_gex = 0
        for col in pivot_df.columns:
            if col != 'Strike':
                value = row[col]
                if pd.notna(value):
                    total_gex += value
        
        if total_gex > 0:
            levels["support"].append(strike)
        elif total_gex < 0:
            levels["resistance"].append(strike)
    
    # Sort and limit to most relevant levels
    levels["support"] = sorted(levels["support"], key=lambda x: abs(x - current_price))[:3]
    levels["resistance"] = sorted(levels["resistance"], key=lambda x: abs(x - current_price))[:3]
    
    return levels
