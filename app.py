"""
DDE BESS Platform — Main Entry Point
Battery Energy Storage System Design & Engineering Tool
"""

import streamlit as st

st.set_page_config(
    page_title="DDE BESS Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.main { background: #0d0f14; }
[data-testid="stSidebar"] {
    background: #12151c !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] * { color: #e8eaf0 !important; }

/* Cards */
.bess-card {
    background: #1a1e28;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.bess-card-accent {
    background: linear-gradient(135deg, #0d1a2e 0%, #0f2040 100%);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

/* Metric tiles */
.metric-tile {
    background: #12151c;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 600;
    color: #00d4ff;
    line-height: 1.2;
}
.metric-label {
    font-size: 11px;
    color: #8890a4;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}
.metric-delta {
    font-size: 12px;
    color: #00e5a0;
    margin-top: 2px;
}
.metric-delta.neg { color: #ff5566; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
}
.badge-green  { background: rgba(0,229,160,0.12); color: #00e5a0; border: 1px solid rgba(0,229,160,0.3); }
.badge-blue   { background: rgba(0,212,255,0.12); color: #00d4ff; border: 1px solid rgba(0,212,255,0.3); }
.badge-amber  { background: rgba(255,179,71,0.12); color: #ffb347;  border: 1px solid rgba(255,179,71,0.3); }
.badge-red    { background: rgba(255,85,102,0.12); color: #ff5566;  border: 1px solid rgba(255,85,102,0.3); }
.badge-purple { background: rgba(167,139,250,0.12); color: #a78bfa; border: 1px solid rgba(167,139,250,0.3); }

/* Page title */
.page-title {
    font-size: 22px;
    font-weight: 600;
    color: #e8eaf0;
    margin-bottom: 4px;
}
.page-sub {
    font-size: 13px;
    color: #8890a4;
    margin-bottom: 24px;
}
.section-title {
    font-size: 13px;
    font-weight: 600;
    color: #8890a4;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 20px 0 10px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 6px;
}
hr.bess-hr { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 20px 0; }

/* Sidebar nav */
.nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; border-radius: 6px;
    font-size: 13px; color: #8890a4;
    cursor: pointer; transition: all 0.15s;
    margin-bottom: 2px;
    text-decoration: none;
}
.nav-item:hover { background: rgba(255,255,255,0.05); color: #e8eaf0; }
.nav-item.active { background: rgba(0,212,255,0.1); color: #00d4ff; border-left: 2px solid #00d4ff; }

/* Streamlit overrides */
.stButton > button {
    background: rgba(0,212,255,0.1) !important;
    color: #00d4ff !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}
.stButton > button:hover {
    background: rgba(0,212,255,0.2) !important;
    border-color: rgba(0,212,255,0.5) !important;
}
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1a1e28 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e8eaf0 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}
.stDataFrame { border-radius: 8px; overflow: hidden; }
div[data-testid="metric-container"] {
    background: #1a1e28;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace;
    color: #00d4ff !important;
}
[data-testid="stMetricDelta"] { color: #00e5a0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:10px;padding:10px 0 20px'>
      <div style='background:rgba(0,212,255,0.15);border:1px solid rgba(0,212,255,0.3);
                  border-radius:8px;padding:8px;display:flex;align-items:center;justify-content:center'>
        <span style='font-size:20px'>⚡</span>
      </div>
      <div>
        <div style='font-family:JetBrains Mono;font-size:14px;font-weight:600;color:#00d4ff'>DDE BESS</div>
        <div style='font-size:10px;color:#555d72;font-family:JetBrains Mono'>Platform v2.0</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["🏠  Dashboard", "🎨  Design Canvas", "🔋  Component Database",
         "📋  Project Manager", "📊  Reports & Export"],
        label_visibility="collapsed",
    )
    st.markdown("<hr style='border-color:rgba(255,255,255,0.07);margin:16px 0'>", unsafe_allow_html=True)

    # Quick project selector
    st.markdown("<div style='font-size:10px;color:#555d72;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px'>Active Project</div>", unsafe_allow_html=True)
    project = st.selectbox("", ["BESS Site Alpha — 5 MWh", "Solar+Storage Beta — 10 MWh", "Grid Freq. Regulation — 2 MWh"], label_visibility="collapsed")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.07);margin:16px 0'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:10px;color:#555d72;text-align:center'>
      DDE Engineering Platform<br>
      <span style='color:#00e5a0'>● System Online</span>
    </div>
    """, unsafe_allow_html=True)

# ── Page routing ─────────────────────────────────────────────────────────────
page_key = page.split("  ")[1] if "  " in page else page

if page_key == "Dashboard":
    from pages import dashboard
    dashboard.render()
elif page_key == "Design Canvas":
    from pages import canvas
    canvas.render()
elif page_key == "Component Database":
    from pages import components_db
    components_db.render()
elif page_key == "Project Manager":
    from pages import project_manager
    project_manager.render()
elif page_key == "Reports & Export":
    from pages import reports
    reports.render()
