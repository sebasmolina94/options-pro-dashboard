#!/usr/bin/env python3
"""
Debug script to trace where SPX data is getting lost in the processing pipeline
"""

import sys
sys.path.append('.')

import pandas as pd
from schwab import get_options_chain
from core_enhanced import compute_exposures_dual
from config import TickerConfig

def debug_spx_processing():
    print("🔍 Debugging SPX data processing pipeline...")
    
    try:
        # Step 1: Get raw data from API
        print("\n1️⃣ Getting raw data from Schwab API...")
        chain = get_options_chain('SPX', 2)
        print(f"   Raw API data: {len(chain)} rows")
        
        if len(chain) == 0:
            print("❌ No data from API!")
            return
            
        # Step 2: Convert to DataFrame
        print("\n2️⃣ Converting to DataFrame...")
        df = pd.DataFrame(chain)
        print(f"   DataFrame shape: {df.shape}")
        print(f"   DataFrame columns: {list(df.columns)}")
        
        # Step 3: Check for required columns
        print("\n3️⃣ Checking required columns...")
        required_cols = ['strike', 'openInterest', 'volume', 'type', 'expiry', 'impliedVolatility']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return
        else:
            print("✅ All required columns present")
            
        # Step 4: Apply strike filtering
        print("\n4️⃣ Applying strike filtering...")
        print(f"   Before filtering: {len(df)} rows")
        df_filtered = df[df['strike'] % 5.0 == 0]
        print(f"   After filtering: {len(df_filtered)} rows")
        
        if len(df_filtered) == 0:
            print("❌ All data filtered out by strike filter!")
            return
            
        # Step 5: Investigate SPX data values
        print("\n5️⃣ Investigating SPX data values...")
        print(f"   Sample OI values: {df_filtered['openInterest'].head().tolist()}")
        print(f"   Sample Volume values: {df_filtered['volume'].head().tolist()}")
        print(f"   OI stats: min={df_filtered['openInterest'].min()}, max={df_filtered['openInterest'].max()}, mean={df_filtered['openInterest'].mean():.2f}")
        print(f"   Volume stats: min={df_filtered['volume'].min()}, max={df_filtered['volume'].max()}, mean={df_filtered['volume'].mean():.2f}")

        # Count how many have OI > 0 vs Volume > 0
        oi_nonzero = (df_filtered['openInterest'] > 0).sum()
        vol_nonzero = (df_filtered['volume'] > 0).sum()
        print(f"   Contracts with OI > 0: {oi_nonzero}")
        print(f"   Contracts with Volume > 0: {vol_nonzero}")

        # Apply SPX multiplier
        print("\n6️⃣ Applying SPX multiplier...")
        df_filtered["openInterest"] = df_filtered["openInterest"] * 10
        print("✅ Applied 10x multiplier to openInterest")

        # For SPX, use a lower minimum OI threshold or skip OI filtering entirely
        print("\n7️⃣ Applying SPX-specific filtering...")
        print(f"   Before filtering: {len(df_filtered)} rows")

        # For SPX, don't filter by OI since it's often 0 after hours
        # Instead, keep all contracts or filter by volume
        print("   ✅ Skipping OI filter for SPX (keeping all contracts)")
        print(f"   After filtering: {len(df_filtered)} rows")
        
        # Step 8: Check data before compute_exposures_dual
        print("\n8️⃣ Data before compute_exposures_dual...")
        print(f"   Shape: {df_filtered.shape}")
        if len(df_filtered) > 0:
            print(f"   Sample data:")
            print(df_filtered[['strike', 'type', 'openInterest', 'volume', 'impliedVolatility']].head())
        else:
            print("   ❌ No data to show - DataFrame is empty!")
            return

        # Step 9: Call compute_exposures_dual
        print("\n9️⃣ Calling compute_exposures_dual...")
        S = 6771.55  # Current SPX price
        
        try:
            df_final = compute_exposures_dual(df_filtered, S)
            print(f"   After compute_exposures_dual: {df_final.shape}")
            
            if df_final.empty:
                print("❌ DataFrame became empty after compute_exposures_dual!")
                
                # Let's check what compute_exposures_dual expects
                print("\n🔍 Investigating compute_exposures_dual requirements...")
                print(f"   Input DataFrame columns: {list(df_filtered.columns)}")
                print(f"   Input DataFrame dtypes:")
                for col in df_filtered.columns:
                    print(f"     {col}: {df_filtered[col].dtype}")
                    
            else:
                print("✅ compute_exposures_dual succeeded!")
                print(f"   Final columns: {list(df_final.columns)}")
                
        except Exception as e:
            print(f"❌ Error in compute_exposures_dual: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error in debug pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_spx_processing()
