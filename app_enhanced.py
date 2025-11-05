import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Test App",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Test App - Checking Dependencies")

try:
    st.write("✅ Streamlit imported successfully")
    
    # Test pandas
    df = pd.DataFrame({'test': [1, 2, 3]})
    st.write("✅ Pandas working")
    
    # Test numpy
    arr = np.array([1, 2, 3])
    st.write("✅ Numpy working")
    
    # Test schwabdev import
    try:
        import schwabdev
        st.write("✅ schwabdev imported successfully")
    except Exception as e:
        st.error(f"❌ schwabdev import failed: {e}")
    
    # Test our modules
    try:
        from core_enhanced import compute_exposures_dual
        st.write("✅ core_enhanced imported successfully")
    except Exception as e:
        st.error(f"❌ core_enhanced import failed: {e}")
    
    try:
        from schwab import get_options_chain
        st.write("✅ schwab module imported successfully")
    except Exception as e:
        st.error(f"❌ schwab module import failed: {e}")
    
    try:
        from config import ALL_TICKERS
        st.write("✅ config imported successfully")
        st.write(f"Found {len(ALL_TICKERS)} tickers")
    except Exception as e:
        st.error(f"❌ config import failed: {e}")
    
    # Test secrets
    try:
        if hasattr(st, 'secrets') and 'schwab' in st.secrets:
            st.write("✅ Schwab secrets found")
            if 'client_id' in st.secrets.schwab:
                st.write("✅ client_id found in secrets")
            if 'client_secret' in st.secrets.schwab:
                st.write("✅ client_secret found in secrets")
        else:
            st.warning("⚠️ No schwab secrets found")
    except Exception as e:
        st.error(f"❌ Secrets check failed: {e}")
        
    st.success("🎉 All basic tests passed!")
    
except Exception as e:
    st.error(f"❌ Critical error: {e}")
    import traceback
    st.code(traceback.format_exc())
