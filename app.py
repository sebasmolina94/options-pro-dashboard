# app.py - SkylitAI Desktop UI Clone
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from core import compute_exposures, black_scholes_greeks
from schwab import get_options_chain, get_underlying_price, ACCESS_TOKEN
from config import ALL_TICKERS
from trading_plan import generate_trading_plan, get_key_levels

# --------------------------------------------------------------
# Page config – full desktop, dark theme
# --------------------------------------------------------------
st.set_page_config(page_title="SkylitAI Pro", layout="wide")
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #00bfff; }
    .stSelectbox > div > div { background-color: #1f2530; color: #fafafa; }
    .stDataFrame { background-color: #1f2530; }
    .stDataFrame > div { border: none; }
    .stDataFrame th { background-color: #161b22; color: #00bfff; font-weight: 600; }
    .stDataFrame td { background-color: #1f2530; color: #fafafa; text-align: right; }
    .positive { background-color: #0a3d0a !important; color: #00ff00; }
    .negative { background-color: #3d0a0a !important; color: #ff4444; }
    .highlight { background-color: #ffd700 !important; color: #000; font-weight: bold; }
    .toggle-btn { background-color: #1f2530; color: #00bfff; border: 1px solid #00bfff; padding: 8px 16px; border-radius: 6px; }
    .toggle-btn.active { background-color: #00bfff; color: #0e1117; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'mode' not in st.session_state:
    st.session_state.mode = 'GEX'

# --------------------------------------------------------------
# Header – Ticker + Live Price
# --------------------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    selected = st.selectbox(
        "Ticker",
        options=[t.symbol for t in ALL_TICKERS],
        format_func=lambda x: f"{x} – {next(t.name for t in ALL_TICKERS if t.symbol == x)}",
        index=0
    )
with col2:
    try:
        S = get_underlying_price(selected)
        st.markdown(f"### **{selected}**  `${S:,.2f}`  <small style='color:#888'>Live Price</small>", unsafe_allow_html=True)
    except:
        st.markdown(f"### **{selected}**  `—`")
        S = 100.0

if not ACCESS_TOKEN:
    st.error("Schwab API token missing – check .env file")
    st.stop()

# --------------------------------------------------------------
# Data Load
# --------------------------------------------------------------
@st.cache_data(ttl=180, show_spinner=False)
def load_data(symbol: str, n_exp: int = 4):
    try:
        S = get_underlying_price(symbol)
        df_raw = get_options_chain(symbol, n_exp)
        
        if df_raw.empty:
            return S, pd.DataFrame(), []
        
        # Get nearest expirations
        df_raw["exp_dt"] = pd.to_datetime(df_raw["expiry"])
        nearest = df_raw.drop_duplicates("expiry").sort_values("exp_dt").head(n_exp)["expiry"].tolist()
        df = df_raw[df_raw["expiry"].isin(nearest)].copy()
        
        # Filter by minimum OI
        cfg = next(t for t in ALL_TICKERS if t.symbol == symbol)
        df = df[df["openInterest"] >= cfg.min_oi]
        
        # Special handling for SPX (index multiplier)
        if cfg.is_index and cfg.symbol == "SPX":
            df["openInterest"] = df["openInterest"] * 10
        
        # Compute exposures
        df = compute_exposures(df, S)
        return S, df, nearest
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return S, pd.DataFrame(), []

S, df, expirations = load_data(selected, n_exp=4)

if df.empty:
    st.warning(f"No options data available for {selected}")
    st.stop()

# --------------------------------------------------------------
# Pivot into Expiry Columns
# --------------------------------------------------------------
def make_pivot(df, metric):
    agg = df.groupby(["strike", "expiry"]).agg({metric: "sum"}).reset_index()
    pivot = agg.pivot(index="strike", columns="expiry", values=metric).fillna(0)
    pivot = pivot.reindex(columns=expirations, index=sorted(pivot.index))
    return pivot, agg

pivot_gex, agg_gex = make_pivot(df, "GEX")
pivot_vanna, agg_vanna = make_pivot(df, "Vanna")

# Format function
def fmt(val):
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        return f"${val/1_000:.1f}K"
    else:
        return f"${val:,.0f}"

# --------------------------------------------------------------
# Toggle: NetGEX vs NetVEX
# --------------------------------------------------------------
st.markdown("### Mode Selection")
col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("NetGEX", key="gex", help="Gamma Exposure"):
        st.session_state.mode = "GEX"
with col_b:
    if st.button("NetVEX", key="vex", help="Vanna Exposure"):
        st.session_state.mode = "Vanna"

mode = st.session_state.mode
metric = "GEX" if mode == "GEX" else "Vanna"

# --------------------------------------------------------------
# Build Table
# --------------------------------------------------------------
pivot = pivot_gex if mode == "GEX" else pivot_vanna
agg = agg_gex if mode == "GEX" else agg_vanna

if agg.empty:
    st.warning(f"No {metric} data available")
    st.stop()

# Find top hot-spot
top_val = agg[metric].abs().max()
top_idx = agg[metric].abs().idxmax()
top_strike = agg.loc[top_idx, "strike"]
top_expiry = agg.loc[top_idx, "expiry"]

# Build styled DataFrame
styled = pivot.copy()

# Apply formatting and colors
html = "<table style='width:100%; border-collapse: collapse; font-family: monospace; font-size: 14px;'>"
html += "<thead><tr><th style='background:#161b22; color:#00bfff; padding:8px; text-align:left;'>Strike</th>"
for exp in expirations:
    html += f"<th style='background:#161b22; color:#00bfff; padding:8px; text-align:center;'>{exp}</th>"
html += "</tr></thead><tbody>"

for strike in sorted(pivot.index):
    html += f"<tr><td style='background:#1f2530; color:#fafafa; padding:8px; text-align:right; font-weight:600;'>{int(strike)}.0</td>"
    for exp in expirations:
        val = pivot.loc[strike, exp] if exp in pivot.columns else 0
        formatted_val = fmt(val)
        
        # Determine cell class
        cell_class = ""
        if abs(val) == top_val and strike == top_strike and exp == top_expiry:
            cell_class = "highlight"
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

# --------------------------------------------------------------
# Render
# --------------------------------------------------------------
st.markdown(f"### **{mode} – {selected}**", unsafe_allow_html=True)
st.markdown(html, unsafe_allow_html=True)

# --------------------------------------------------------------
# Footer – Hot Spot Callout
# --------------------------------------------------------------
st.markdown(
    f"<div style='text-align:center; margin-top:20px; color:#aaa; font-size:13px;'>"
    f"Top {mode}: <strong>{fmt(top_val)}</strong> at strike <strong>{int(top_strike)}.0</strong> on <strong>{top_expiry}</strong>"
    f"</div>",
    unsafe_allow_html=True
)

# --------------------------------------------------------------
# Trading Plan Section
# --------------------------------------------------------------
st.markdown("---")
st.markdown("### 🎯 **AI Trading Plan**")

# Create pivot with Strike column for trading plan
pivot_with_strike = pivot.reset_index()
pivot_with_strike.rename(columns={'strike': 'Strike'}, inplace=True)

# Generate trading plan
try:
    trading_plan = generate_trading_plan(selected, f"Net{mode}", pivot_with_strike, S)

    # Display in expandable section
    with st.expander("📊 **View Trading Analysis & Strategy**", expanded=False):
        st.markdown(trading_plan)

        # Quick key levels summary
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

# Optional: Export functionality
st.markdown("---")
if st.button("Export CSV"):
    csv = pivot.to_csv()
    st.download_button("Download", csv, f"{selected}_{mode}.csv", "text/csv")
