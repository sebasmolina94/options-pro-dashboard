"""
Enhanced Core module with support for both OI and Volume-based calculations
"""
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.stats import norm

def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    """Calculate Black-Scholes Greeks"""
    if T <= 0 or sigma <= 0:
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        delta = norm.cdf(d1)
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                - r * K * np.exp(-r * T) * norm.cdf(d2))
        rho = K * T * np.exp(-r * T) * norm.cdf(d2)
    else:  # put
        delta = -norm.cdf(-d1)
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                + r * K * np.exp(-r * T) * norm.cdf(-d2))
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
    
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T)
    
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

def compute_exposures_dual(df, underlying_price, risk_free_rate=0.05):
    """
    Compute both OI-based and Volume-based exposures
    
    Returns dataframe with both sets of calculations:
    - GEX_OI, Vanna_OI, DEX_OI (based on Open Interest)
    - GEX_Vol, Vanna_Vol, DEX_Vol (based on Volume)
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Calculate time to expiration
    today = datetime.now().date()
    df['exp_dt'] = pd.to_datetime(df['expiry']).dt.date
    df['T'] = df['exp_dt'].apply(lambda x: max((x - today).days / 365.0, 1/365))
    
    # Initialize all exposure columns
    df['GEX_OI'] = 0.0
    df['Vanna_OI'] = 0.0
    df['DEX_OI'] = 0.0
    df['GEX_Vol'] = 0.0
    df['Vanna_Vol'] = 0.0
    df['DEX_Vol'] = 0.0
    
    for idx, row in df.iterrows():
        S = underlying_price
        K = row['strike']
        T = row['T']
        sigma = max(row['impliedVolatility'], 0.01)
        oi = row['openInterest']
        volume = row['volume']
        option_type = row['type']
        
        # Calculate Greeks if needed
        if pd.isna(row.get('gamma', np.nan)) or row.get('gamma', 0) == 0:
            greeks = black_scholes_greeks(S, K, T, risk_free_rate, sigma, option_type)
            df.at[idx, 'delta'] = float(greeks['delta'])
            df.at[idx, 'gamma'] = float(greeks['gamma'])
            df.at[idx, 'theta'] = float(greeks['theta'])
            df.at[idx, 'vega'] = float(greeks['vega'])
        
        delta = row.get('delta', 0)
        gamma = row.get('gamma', 0)
        vanna = calculate_vanna(S, K, T, risk_free_rate, sigma)
        
        multiplier = 100
        
        # Calculate OI-based exposures
        dex_oi = delta * oi * multiplier
        if option_type == 'call':
            gex_oi = gamma * oi * multiplier * S / 100
        else:
            gex_oi = -gamma * oi * multiplier * S / 100
        vanna_oi = vanna * oi * multiplier * S / 100
        
        # Calculate Volume-based exposures
        dex_vol = delta * volume * multiplier
        if option_type == 'call':
            gex_vol = gamma * volume * multiplier * S / 100
        else:
            gex_vol = -gamma * volume * multiplier * S / 100
        vanna_vol = vanna * volume * multiplier * S / 100
        
        # Store results
        df.at[idx, 'DEX_OI'] = dex_oi
        df.at[idx, 'GEX_OI'] = gex_oi
        df.at[idx, 'Vanna_OI'] = vanna_oi
        df.at[idx, 'DEX_Vol'] = dex_vol
        df.at[idx, 'GEX_Vol'] = gex_vol
        df.at[idx, 'Vanna_Vol'] = vanna_vol
    
    return df

def compute_exposures(df, underlying_price, risk_free_rate=0.05):
    """
    Original function for backward compatibility - uses Open Interest
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Calculate time to expiration
    today = datetime.now().date()
    df['exp_dt'] = pd.to_datetime(df['expiry']).dt.date
    df['T'] = df['exp_dt'].apply(lambda x: max((x - today).days / 365.0, 1/365))
    
    # Initialize exposure columns
    df['GEX'] = 0.0
    df['Vanna'] = 0.0
    df['DEX'] = 0.0
    
    for idx, row in df.iterrows():
        S = underlying_price
        K = row['strike']
        T = row['T']
        sigma = max(row['impliedVolatility'], 0.01)
        oi = row['openInterest']
        option_type = row['type']
        
        # Calculate Greeks if needed
        if pd.isna(row.get('gamma', np.nan)) or row.get('gamma', 0) == 0:
            greeks = black_scholes_greeks(S, K, T, risk_free_rate, sigma, option_type)
            df.at[idx, 'delta'] = float(greeks['delta'])
            df.at[idx, 'gamma'] = float(greeks['gamma'])
            df.at[idx, 'theta'] = float(greeks['theta'])
            df.at[idx, 'vega'] = float(greeks['vega'])
        
        delta = row.get('delta', 0)
        gamma = row.get('gamma', 0)
        vanna = calculate_vanna(S, K, T, risk_free_rate, sigma)
        
        multiplier = 100
        
        # Calculate exposures
        dex = delta * oi * multiplier
        if option_type == 'call':
            gex = gamma * oi * multiplier * S / 100
        else:
            gex = -gamma * oi * multiplier * S / 100
        vanna_exposure = vanna * oi * multiplier * S / 100
        
        df.at[idx, 'DEX'] = dex
        df.at[idx, 'GEX'] = gex
        df.at[idx, 'Vanna'] = vanna_exposure
    
    return df
