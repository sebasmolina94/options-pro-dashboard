import streamlit as st
import sys

st.title("Python Version Test")
st.write(f"Python version: {sys.version}")
st.write(f"Python version info: {sys.version_info}")

# Test if we can install schwabdev
try:
    import schwabdev
    st.success("✅ schwabdev imported successfully!")
    st.write(f"schwabdev version: {schwabdev.__version__ if hasattr(schwabdev, '__version__') else 'Unknown'}")
except ImportError as e:
    st.error(f"❌ Cannot import schwabdev: {e}")
except Exception as e:
    st.error(f"❌ Error with schwabdev: {e}")
