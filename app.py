# app.py
import streamlit as st

st.set_page_config(page_title="Instagram Audit Tool", page_icon="📊", layout="wide")
st.title("📊 Instagram Audit Tool")

username = st.text_input("Enter Instagram Username", placeholder="e.g., natgeo")

if st.button("🔍 Run Audit", type="primary"):
    with st.spinner("Scraping analytics..."):
        data = scrape(username)        # Step 1
    with st.spinner("Generating report..."):
        report = generate_audit(data)  # Step 2
    st.markdown(report)
    
    if st.button("📧 Send via Email"):
        send_audit_email(email, username, report)
        st.success("Email sent!")
