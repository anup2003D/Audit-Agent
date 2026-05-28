# app.py — Instagram Influencer Audit Agent UI

import streamlit as st
import json
import os
import time

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Influencer Audit Agent",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — dark premium theme ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Dark background ── */
.stApp {
    background: linear-gradient(135deg, #0d0d1a 0%, #111827 60%, #0d1f2d 100%);
    min-height: 100vh;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
}
.hero-badge {
    display: inline-block;
    background: linear-gradient(90deg, #7c3aed22, #2563eb22);
    border: 1px solid #7c3aed55;
    color: #a78bfa;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.35rem 1rem;
    border-radius: 999px;
    margin-bottom: 1rem;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 0.6rem;
}
.hero-sub {
    color: #94a3b8;
    font-size: 1.05rem;
    font-weight: 400;
}

/* ── Input area card ── */
.input-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 2rem;
    margin: 1.5rem 0;
    backdrop-filter: blur(10px);
}

/* ── Streamlit input override ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    font-size: 1.05rem !important;
    padding: 0.75rem 1.1rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
}
.stTextInput > label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

/* ── Primary button override ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    width: 100% !important;
    transition: opacity 0.2s, transform 0.15s !important;
    letter-spacing: 0.02em;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* ── Step status row ── */
.step-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.7rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
    font-weight: 500;
    transition: background 0.3s;
}
.step-row.done   { background: rgba(52,211,153,0.08); color: #34d399; }
.step-row.active { background: rgba(96,165,250,0.10); color: #93c5fd; }
.step-row.fail   { background: rgba(248,113,113,0.10); color: #f87171; }
.step-row.idle   { background: rgba(255,255,255,0.03); color: #64748b; }
.step-icon { font-size: 1.1rem; min-width: 1.4rem; text-align:center; }

/* ── Metric grid ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
}
.metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1.1;
}
.metric-sub {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 0.25rem;
}

/* ── Report card ── */
.report-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 2rem 2.2rem;
    margin-top: 1.5rem;
    color: #cbd5e1;
    line-height: 1.75;
}
.report-card h1, .report-card h2, .report-card h3 {
    color: #f1f5f9;
}
.report-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #a78bfa;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Divider ── */
.custom-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin: 1.5rem 0;
}

/* ── Error / warning box ── */
.stAlert {
    border-radius: 12px !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #7c3aed !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helper: format large numbers ──────────────────────────────────────────────
def fmt_num(n):
    if n is None:
        return "—"
    n = float(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{int(n):,}"


# ── Helper: render metric cards ───────────────────────────────────────────────
def render_metrics(data: dict):
    html = '<div class="metric-grid">'
    metrics = [
        ("👥", "Followers",      fmt_num(data.get("followers")),       ""),
        ("➡️", "Following",      fmt_num(data.get("following")),       ""),
        ("🖼️", "Posts",          fmt_num(data.get("posts_count")),     ""),
        ("❤️", "Avg Likes",      fmt_num(data.get("avg_likes")),       "per post"),
        ("💬", "Avg Comments",   fmt_num(data.get("avg_comments")),    "per post"),
        ("📈", "Engagement",     f"{data.get('engagement_rate', 0):.2f}%", "rate"),
        ("🚀", "Growth",         f"{data.get('growth_rate', 0):+.1f}%", "monthly"),
        ("🛡️", "Authenticity",   f"{data.get('authenticity_score', 0):.0f}%", "score"),
    ]
    for icon, label, value, sub in metrics:
        html += f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Helper: render a step row ─────────────────────────────────────────────────
def step_html(icon, text, state="idle"):
    return f'<div class="step-row {state}"><span class="step-icon">{icon}</span>{text}</div>'


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN UI
# ══════════════════════════════════════════════════════════════════════════════

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">🤖 AI-Powered Agent</div>
    <div class="hero-title">Influencer Audit Agent</div>
    <div class="hero-sub">Enter an Instagram username and the agent will scrape, analyze,<br>and generate a full professional audit report.</div>
</div>
""", unsafe_allow_html=True)

# ── Input card ────────────────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)
username = st.text_input(
    "Instagram Username",
    placeholder="e.g.  natgeo  or  cristiano",
    label_visibility="visible",
)
run = st.button("🚀  Run Audit Agent", type="primary")
st.markdown('</div>', unsafe_allow_html=True)

# ── Agent execution ───────────────────────────────────────────────────────────
if run:
    if not username.strip():
        st.warning("⚠️  Please enter an Instagram username before running.")
        st.stop()

    username = username.strip().lstrip("@")

    # ── Step tracker placeholder ───────────────────────────────────────────
    status_box = st.empty()

    def render_steps(steps):
        """steps = list of (icon, label, state)"""
        html = "".join(step_html(i, l, s) for i, l, s in steps)
        status_box.markdown(html, unsafe_allow_html=True)

    steps = [
        ("🌐", f"Launching Chrome → notjustanalytics.com/@{username}", "active"),
        ("📡", "Extracting metrics from page",                         "idle"),
        ("🤖", "Generating AI audit report via Gemini",                "idle"),
    ]
    render_steps(steps)

    # ── Step 1 : scrape ────────────────────────────────────────────────────
    data = None
    try:
        from scraper import get_profile_data, save_to_json
        data = get_profile_data(username)
        save_to_json(data)

        steps[0] = ("✅", f"Scraped @{username} successfully", "done")
        steps[1] = ("📡", "Extracting metrics from page",      "done")
        render_steps(steps)

    except Exception as e:
        err_msg = str(e)
        steps[0] = ("❌", f"Scraping failed: {err_msg[:120]}", "fail")
        render_steps(steps)
        st.error(f"**Scraping failed:** {err_msg}")
        st.stop()

    # ── Metric cards ──────────────────────────────────────────────────────
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(f"### 📊 Metrics for **@{username}**")
    render_metrics(data)

    # ── Step 3 : LLM report ───────────────────────────────────────────────
    steps[2] = ("🤖", "Generating AI audit report via Gemini…", "active")
    render_steps(steps)

    report = None
    try:
        from llm.client import generate_audit
        report = generate_audit(data)

        steps[2] = ("✅", "Audit report generated", "done")
        render_steps(steps)

    except Exception as e:
        steps[2] = ("❌", f"Report generation failed: {e}", "fail")
        render_steps(steps)
        st.error(f"LLM error: {e}")
        st.stop()

    # ── Report display ────────────────────────────────────────────────────
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown('<div class="report-title">📋 Audit Report</div>', unsafe_allow_html=True)
    st.markdown(report)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Raw JSON expander ─────────────────────────────────────────────────
    with st.expander("🔍 View raw scraped data"):
        st.json(data)
