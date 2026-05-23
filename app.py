# app.py
import streamlit as st
import json
import os

st.set_page_config(page_title="Instagram Audit Tool", page_icon="📊", layout="wide")
st.title("📊 Instagram Audit Tool")

username = st.text_input("Enter Instagram Username", placeholder="e.g., natgeo")

# --- Option 1: Auto-scrape (runs Chrome in the background) ---
if st.button("🔍 Run Audit", type="primary"):
    if not username:
        st.warning("Please enter a username first.")
        st.stop()

    with st.spinner("Scraping analytics (Chrome will open briefly)..."):
        try:
            from scraper import get_profile_data, save_to_json
            data = get_profile_data(username)
            save_to_json(data)
        except Exception as e:
            st.error(f"Scraping failed: {e}")
            st.info("💡 **Fallback**: Use the manual method below instead.")
            st.stop()

    st.success(f"✅ Scraped @{username} successfully!")
    st.json(data)

    with st.spinner("Generating audit report..."):
        try:
            from llm.client import generate_audit
            report = generate_audit(data)
            st.markdown(report)
        except Exception as e:
            st.error(f"Report generation failed: {e}")

st.divider()

# --- Option 2: Manual fallback (paste from console_scraper.js) ---
with st.expander("📋 Manual mode — paste data from console_scraper.js"):
    st.markdown("""
    If auto-scraping doesn't work (Cloudflare block, Chrome issues, etc.):
    1. Open `app.notjustanalytics.com/analysis/{username}` in Chrome
    2. Press F12 → Console → type `allow pasting` → Enter
    3. Paste the contents of `console_scraper.js` → Enter
    4. Paste the JSON output below:
    """)
    manual_json = st.text_area("Paste JSON here", height=200)
    if st.button("📊 Generate Report from Pasted Data"):
        try:
            data = json.loads(manual_json)
            # Save it to info.JSON for consistency
            script_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(script_dir, "info.JSON"), "w") as f:
                json.dump(data, f, indent=4)
            st.json(data)

            with st.spinner("Generating audit report..."):
                from llm.client import generate_audit
                report = generate_audit(data)
                st.markdown(report)
        except json.JSONDecodeError:
            st.error("Invalid JSON. Make sure you copied the full output.")
        except Exception as e:
            st.error(f"Error: {e}")
