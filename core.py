# core.py - Core calculations for SkylitAI
import numpy as np
import pandas as pd
from scipy.stats import norm
import math
from datetime import datetime

def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate Black-Scholes Greeks
    
    Parameters:
    S: Current stock price
    K: Strike price
    T: Time to expiration (in years)
    r: Risk-free rate
    sigma: Volatility
    option_type: 'call' or 'put'
    """
    if T <= 0 or sigma <= 0:
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Calculate Greeks
    if option_type == 'call':
        delta = norm.cdf(d1)
        rho = K * T * np.exp(-r * T) * norm.cdf(d2)
    else:  # put
        delta = norm.cdf(d1) - 1
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
    
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
             - r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type == 'call' else norm.cdf(-d2)))
    vega = S * np.sqrt(T) * norm.pdf(d1)
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta / 365,  # Convert to daily theta
        'vega': vega / 100,    # Convert to 1% vega
        'rho': rho / 100       # Convert to 1% rho
    }

def calculate_vanna(S, K, T, r, sigma):
    """Calculate Vanna (sensitivity of delta to volatility)"""
    if T <= 0 or sigma <= 0:
        return 0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    vanna = -norm.pdf(d1) * d2 / sigma
    return vanna

def compute_exposures(df, underlying_price, risk_free_rate=0.05):
    """
    Compute GEX and Vanna exposures for options dataframe
    
    Parameters:
    df: DataFrame with options data
    underlying_price: Current underlying price
    risk_free_rate: Risk-free rate (default 5%)
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Calculate time to expiration
    today = datetime.now().date()
    df['exp_dt'] = pd.to_datetime(df['expiry']).dt.date
    df['T'] = df['exp_dt'].apply(lambda x: max((x - today).days / 365.0, 1/365))  # Min 1 day
    
    # Initialize exposure columns
    df['GEX'] = 0.0
    df['Vanna'] = 0.0
    df['DEX'] = 0.0
    
    for idx, row in df.iterrows():
        S = underlying_price
        K = row['strike']
        T = row['T']
        sigma = max(row['impliedVolatility'], 0.01)  # Min 1% vol
        oi = row['openInterest']
        option_type = row['type']
        
        # Calculate Greeks if we don't have them
        if pd.isna(row.get('gamma', np.nan)) or row.get('gamma', 0) == 0:
            greeks = black_scholes_greeks(S, K, T, risk_free_rate, sigma, option_type)
            df.at[idx, 'delta'] = float(greeks['delta'])
            df.at[idx, 'gamma'] = float(greeks['gamma'])
            df.at[idx, 'theta'] = float(greeks['theta'])
            df.at[idx, 'vega'] = float(greeks['vega'])
        
        # Use existing Greeks
        delta = row.get('delta', 0)
        gamma = row.get('gamma', 0)
        
        # Calculate Vanna
        vanna = calculate_vanna(S, K, T, risk_free_rate, sigma)
        
        # Calculate exposures (per $1 move in underlying)
        # Standard options multiplier is 100
        multiplier = 100
        
        # Delta Exposure (DEX)
        dex = delta * oi * multiplier
        
        # Gamma Exposure (GEX) - Market makers are short gamma for customer long positions
        # Positive GEX means supportive (market makers buy dips, sell rallies)
        if option_type == 'call':
            gex = gamma * oi * multiplier * S / 100  # Normalize by underlying price
        else:  # put
            gex = -gamma * oi * multiplier * S / 100  # Puts have negative GEX
        
        # Vanna Exposure - sensitivity of delta to volatility
        vanna_exposure = vanna * oi * multiplier * S / 100
        
        df.at[idx, 'DEX'] = dex
        df.at[idx, 'GEX'] = gex
        df.at[idx, 'Vanna'] = vanna_exposure
    
    return df
