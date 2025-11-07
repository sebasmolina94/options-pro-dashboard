import streamlit as st
import os

st.title("🔍 Secrets Diagnostic Test")

st.write("## Environment Check")
st.write(f"Running on Streamlit Cloud: {os.getenv('STREAMLIT_SHARING_MODE') is not None}")

st.write("## Secrets Check")

try:
    # Check if secrets exist
    if hasattr(st, 'secrets'):
        st.success("✅ st.secrets is available")
        
        # Check schwab section
        if 'schwab' in st.secrets:
            st.success("✅ [schwab] section found")
            
            # Check individual keys
            schwab_keys = ['app_key', 'app_secret', 'callback_url', 'access_token', 'refresh_token', 'refresh_token_issued']
            for key in schwab_keys:
                if key in st.secrets.schwab:
                    st.success(f"✅ schwab.{key} found")
                else:
                    st.error(f"❌ schwab.{key} missing")
        else:
            st.error("❌ [schwab] section not found in secrets")
            
        # Show available sections
        st.write("### Available secret sections:")
        st.write(list(st.secrets.keys()))
        
    else:
        st.error("❌ st.secrets not available")
        
except Exception as e:
    st.error(f"❌ Error accessing secrets: {e}")

st.write("## Environment Variables Check")
env_vars = ['SCHWAB_APP_KEY', 'SCHWAB_APP_SECRET', 'SCHWAB_CALLBACK_URL']
for var in env_vars:
    value = os.getenv(var)
    if value:
        st.success(f"✅ {var} found")
    else:
        st.warning(f"⚠️ {var} not found in environment")

st.write("## Test Schwab Import")
try:
    from schwabdev import Client
    st.success("✅ schwabdev import successful")
except ImportError as e:
    st.error(f"❌ schwabdev import failed: {e}")

st.write("## Test Core Import")
try:
    from core_enhanced import compute_exposures_dual
    st.success("✅ core_enhanced import successful")
except ImportError as e:
    st.error(f"❌ core_enhanced import failed: {e}")
