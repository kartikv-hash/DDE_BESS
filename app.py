"""
DDE BESS Platform — Single-file Streamlit app
Battery Energy Storage System Design & Engineering Tool
Zero submodule imports — works on Streamlit Cloud out of the box
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from datetime import datetime, date

st.set_page_config(
    page_title="DDE BESS Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
[data-testid="stSidebar"]{background:#12151c!important;border-right:1px solid rgba(255,255,255,0.07);}
[data-testid="stSidebar"] *{color:#e8eaf0!important;}
.bess-card{background:#1a1e28;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:20px 24px;margin-bottom:16px;}
.bess-card-accent{background:linear-gradient(135deg,#0d1a2e,#0f2040);border:1px solid rgba(0,212,255,0.2);border-radius:10px;padding:20px 24px;margin-bottom:16px;}
.metric-tile{background:#12151c;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:16px 20px;text-align:center;}
.metric-value{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:600;color:#00d4ff;line-height:1.2;}
.metric-label{font-size:11px;color:#8890a4;text-transform:uppercase;letter-spacing:0.08em;margin-top:4px;}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:500;font-family:'JetBrains Mono',monospace;}
.badge-green{background:rgba(0,229,160,0.12);color:#00e5a0;border:1px solid rgba(0,229,160,0.3);}
.badge-blue{background:rgba(0,212,255,0.12);color:#00d4ff;border:1px solid rgba(0,212,255,0.3);}
.badge-amber{background:rgba(255,179,71,0.12);color:#ffb347;border:1px solid rgba(255,179,71,0.3);}
.badge-purple{background:rgba(167,139,250,0.12);color:#a78bfa;border:1px solid rgba(167,139,250,0.3);}
.page-title{font-size:22px;font-weight:600;color:#e8eaf0;margin-bottom:4px;}
.page-sub{font-size:13px;color:#8890a4;margin-bottom:24px;}
.section-title{font-size:13px;font-weight:600;color:#8890a4;text-transform:uppercase;letter-spacing:0.08em;margin:20px 0 10px;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:6px;}
.stButton>button{background:rgba(0,212,255,0.1)!important;color:#00d4ff!important;border:1px solid rgba(0,212,255,0.3)!important;border-radius:6px!important;font-family:'DM Sans',sans-serif!important;font-weight:500!important;}
.stButton>button:hover{background:rgba(0,212,255,0.2)!important;}
div[data-testid="metric-container"]{background:#1a1e28;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:12px 16px;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace;color:#00d4ff!important;}
[data-testid="stMetricDelta"]{color:#00e5a0!important;}
</style>
""", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────────────
COMPONENT_CATALOGUE = {
    "battery_rack":   {"label":"Battery Rack",          "category":"Storage",    "icon":"🔋","color":"#00d4ff","unit_cost_usd":85000,  "specs":{"capacity_kwh":100,"voltage_v":768,"chemistry":"LFP","cycle_life":6000,"c_rate":0.5,"ip_rating":"IP54"}},
    "bms":            {"label":"BMS",                    "category":"Control",    "icon":"🖥️","color":"#00e5a0","unit_cost_usd":8500,   "specs":{"protocol":"CAN 2.0B","cell_channels":128,"temp_sensors":16,"balancing":"Active","fw":"v3.2.1"}},
    "pcs":            {"label":"PCS / Inverter",         "category":"Power",      "icon":"⚡","color":"#ffb347","unit_cost_usd":120000, "specs":{"power_kw":250,"efficiency_pct":98.5,"topology":"3L-NPC","ac_v":400,"response_ms":20}},
    "transformer":    {"label":"MV Transformer",         "category":"Power",      "icon":"🔄","color":"#a78bfa","unit_cost_usd":45000,  "specs":{"rating_kva":315,"hv_kv":11,"lv_v":400,"vector_group":"Dyn11","impedance_pct":4.5}},
    "vcb":            {"label":"Vacuum Circuit Breaker", "category":"Protection", "icon":"🔌","color":"#ff5566","unit_cost_usd":12000,  "specs":{"current_a":630,"voltage_kv":12,"breaking_ka":16,"standard":"IEC 62271-100"}},
    "acb":            {"label":"Air Circuit Breaker",    "category":"Protection", "icon":"🔌","color":"#ff5566","unit_cost_usd":9000,   "specs":{"current_a":1600,"voltage_v":1000,"type":"Air"}},
    "busbar":         {"label":"Busbar",                 "category":"Power",      "icon":"━", "color":"#8890a4","unit_cost_usd":3000,   "specs":{"rating_a":2000,"material":"Copper","size_mm":"100x10"}},
    "meter":          {"label":"Smart Meter",            "category":"Monitoring", "icon":"📊","color":"#00e5a0","unit_cost_usd":2500,   "specs":{"accuracy":"0.5S","measurements":"P/Q/E/PF","comm":"Modbus RTU"}},
    "ct":             {"label":"Current Transformer",    "category":"Monitoring", "icon":"🔁","color":"#a78bfa","unit_cost_usd":1200,   "specs":{"ratio":"1000:5 A","accuracy":"0.5","burden_va":5}},
    "relay":          {"label":"Protection Relay",       "category":"Protection", "icon":"🛡️","color":"#00e5a0","unit_cost_usd":6500,   "specs":{"functions":"87T/51/50/27/59","IEC_61850":"Yes","comm":"Modbus/IEC61850"}},
    "scada":          {"label":"SCADA / EMS",            "category":"Control",    "icon":"🖧","color":"#a78bfa","unit_cost_usd":35000,  "specs":{"protocol":"IEC 61850/MQTT","redundancy":"Hot-standby","cybersecurity":"IEC 62443"}},
    "grid_point":     {"label":"Grid Connection Point",  "category":"Grid",       "icon":"🔗","color":"#00d4ff","unit_cost_usd":0,      "specs":{"voltage_kv":11,"frequency_hz":50,"scc_ka":10}},
    "pv":             {"label":"PV Array",               "category":"Generation", "icon":"☀️","color":"#ffb347","unit_cost_usd":150000, "specs":{"power_kwp":500,"voc_v":900,"tech":"Mono PERC"}},
    "container_20ft": {"label":"20ft BESS Container",   "category":"Storage",    "icon":"📦","color":"#555d72","unit_cost_usd":25000,  "specs":{"length_m":6.1,"width_m":2.4,"height_m":2.6,"ip_rating":"IP54"}},
}

PROJECT_STATUSES = ["Planning","Design","Procurement","Construction","Commissioning","Operational"]

PT = dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
          font=dict(family="DM Sans",color="#8890a4",size=12),margin=dict(l=0,r=0,t=30,b=0))

def _seed():
    return [
        {"id":"PRJ-001","name":"BESS Site Alpha","location":"Manchester, UK","client":"National Grid ESO",
         "capacity_mwh":5.0,"power_mw":2.5,"status":"Design","start_date":"2024-03-01","end_date":"2025-09-30",
         "budget_usd":4_200_000,"spent_usd":680_000,"chemistry":"LFP","application":"Frequency Regulation",
         "rack_count":50,"pcs_count":4,"engineer":"K. Varma","progress_pct":32,
         "notes":"Grid connection approved. Transformer procurement in progress.",
         "milestones":[{"name":"Design Freeze","date":"2024-06-01","done":True},{"name":"Equipment Order","date":"2024-08-15","done":True},
                       {"name":"Civil Works Start","date":"2024-11-01","done":False},{"name":"Equipment Delivery","date":"2025-03-15","done":False},
                       {"name":"Commissioning Start","date":"2025-07-01","done":False},{"name":"Commercial Operation","date":"2025-09-30","done":False}]},
        {"id":"PRJ-002","name":"Solar+Storage Beta","location":"Birmingham, UK","client":"Sunpower Renewables",
         "capacity_mwh":10.0,"power_mw":5.0,"status":"Procurement","start_date":"2024-01-15","end_date":"2025-12-31",
         "budget_usd":8_500_000,"spent_usd":2_100_000,"chemistry":"NMC","application":"Peak Shaving",
         "rack_count":100,"pcs_count":8,"engineer":"K. Varma","progress_pct":55,
         "notes":"PCS units ordered. Civil works 40% complete.",
         "milestones":[{"name":"Design Freeze","date":"2024-03-01","done":True},{"name":"Equipment Order","date":"2024-05-01","done":True},
                       {"name":"Civil Works Start","date":"2024-07-01","done":True},{"name":"Equipment Delivery","date":"2025-01-15","done":False},
                       {"name":"Commissioning Start","date":"2025-09-01","done":False},{"name":"Commercial Operation","date":"2025-12-31","done":False}]},
        {"id":"PRJ-003","name":"Grid Freq. Regulation","location":"Leeds, UK","client":"Octopus Energy",
         "capacity_mwh":2.0,"power_mw":2.0,"status":"Commissioning","start_date":"2023-06-01","end_date":"2024-06-30",
         "budget_usd":2_000_000,"spent_usd":1_850_000,"chemistry":"LFP","application":"FFR / BM Participation",
         "rack_count":20,"pcs_count":2,"engineer":"K. Varma","progress_pct":88,
         "notes":"FAT complete. Site acceptance testing ongoing.",
         "milestones":[{"name":"Design Freeze","date":"2023-08-01","done":True},{"name":"Equipment Order","date":"2023-09-01","done":True},
                       {"name":"Civil Works Start","date":"2023-11-01","done":True},{"name":"Equipment Delivery","date":"2024-02-01","done":True},
                       {"name":"Commissioning Start","date":"2024-04-01","done":True},{"name":"Commercial Operation","date":"2024-06-30","done":False}]},
    ]

if "projects" not in st.session_state:
    st.session_state.projects = _seed()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style='display:flex;align-items:center;gap:10px;padding:10px 0 20px'>
      <div style='background:rgba(0,212,255,0.15);border:1px solid rgba(0,212,255,0.3);border-radius:8px;padding:8px'><span style='font-size:20px'>⚡</span></div>
      <div><div style='font-family:JetBrains Mono;font-size:14px;font-weight:600;color:#00d4ff'>DDE BESS</div>
           <div style='font-size:10px;color:#555d72;font-family:JetBrains Mono'>Platform v2.0</div></div></div>""", unsafe_allow_html=True)

    page = st.radio("Navigate", ["🏠  Dashboard","🎨  Design Canvas","🔋  Component Database","📋  Project Manager","📊  Reports & Export"], label_visibility="collapsed", key="nav_radio")
    st.markdown("<hr style='border-color:rgba(255,255,255,0.07);margin:16px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:10px;color:#555d72;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px'>Active Project</div>", unsafe_allow_html=True)
    st.selectbox("", [p["name"] for p in st.session_state.projects], label_visibility="collapsed", key="active_proj")
    st.markdown("<hr style='border-color:rgba(255,255,255,0.07);margin:16px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:10px;color:#555d72;text-align:center'>DDE Engineering Platform<br><span style='color:#00e5a0'>● System Online</span></div>", unsafe_allow_html=True)

# ═════════════════════════════  DASHBOARD  ════════════════════════════════════
def page_dashboard():
    P = st.session_state.projects
    st.markdown('<div class="page-title">⚡ BESS Engineering Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Fleet overview · Live KPIs · Project status</div>', unsafe_allow_html=True)
    tmh=sum(p["capacity_mwh"]for p in P); tmw=sum(p["power_mw"]for p in P)
    tbd=sum(p["budget_usd"]for p in P);  tsp=sum(p["spent_usd"]for p in P)
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Total Capacity",f"{tmh} MWh"); c2.metric("Total Power",f"{tmw} MW")
    c3.metric("Projects",len(P)); c4.metric("Budget",f"${tbd/1e6:.1f}M",f"${tsp/1e6:.1f}M spent")
    c5.metric("Budget Used",f"{round(tsp/tbd*100,1)}%")
    st.markdown("<br>",unsafe_allow_html=True)
    sc={"Planning":"#555d72","Design":"#00d4ff","Procurement":"#ffb347","Construction":"#a78bfa","Commissioning":"#00e5a0","Operational":"#00e5a0"}
    cl,cr=st.columns([3,2])
    with cl:
        st.markdown('<div class="section-title">Project Progress</div>',unsafe_allow_html=True)
        fig=go.Figure()
        for p in P:
            fig.add_trace(go.Bar(y=[p["name"]],x=[p["progress_pct"]],orientation="h",marker_color=sc.get(p["status"],"#555d72"),text=f'{p["progress_pct"]}%',textposition="inside",insidetextanchor="start",showlegend=False))
            fig.add_trace(go.Bar(y=[p["name"]],x=[100-p["progress_pct"]],orientation="h",marker_color="rgba(255,255,255,0.04)",showlegend=False,hoverinfo="skip"))
        fig.update_layout(**PT,barmode="stack",height=220,xaxis=dict(range=[0,100],showgrid=False,showticklabels=False),yaxis=dict(showgrid=False))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    with cr:
        st.markdown('<div class="section-title">Capacity by Chemistry</div>',unsafe_allow_html=True)
        chem={}
        for p in P: chem[p["chemistry"]]=chem.get(p["chemistry"],0)+p["capacity_mwh"]
        fig2=go.Figure(go.Pie(labels=list(chem.keys()),values=list(chem.values()),hole=0.6,marker_colors=["#00d4ff","#ffb347","#a78bfa"],textinfo="label+percent"))
        fig2.update_layout(**PT,height=220,annotations=[dict(text=f"{tmh}<br>MWh",x=0.5,y=0.5,font_size=14,font_color="#e8eaf0",showarrow=False)])
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
    st.markdown('<div class="section-title">Budget vs Spend</div>',unsafe_allow_html=True)
    fig3=go.Figure()
    fig3.add_trace(go.Bar(name="Budget",x=[p["name"]for p in P],y=[p["budget_usd"]/1e6 for p in P],marker_color="#1a2d4a"))
    fig3.add_trace(go.Bar(name="Spent", x=[p["name"]for p in P],y=[p["spent_usd"]/1e6  for p in P],marker_color="#00d4ff"))
    fig3.update_layout(**PT,barmode="overlay",height=200,yaxis=dict(title="$M",gridcolor="rgba(255,255,255,0.05)"),xaxis=dict(showgrid=False),legend=dict(bgcolor="rgba(0,0,0,0)",orientation="h",y=1.1))
    st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})
    st.markdown('<div class="section-title">Project Cards</div>',unsafe_allow_html=True)
    bm={"Planning":"badge-purple","Design":"badge-blue","Procurement":"badge-amber","Construction":"badge-amber","Commissioning":"badge-green","Operational":"badge-green"}
    for p in P:
        done=sum(1 for m in p["milestones"] if m["done"])
        st.markdown(f"""<div class="bess-card">
          <div style='display:flex;justify-content:space-between;align-items:flex-start'>
            <div><div style='font-size:15px;font-weight:600;color:#e8eaf0'>{p["name"]} <span style='font-family:JetBrains Mono;font-size:11px;color:#555d72'>{p["id"]}</span></div>
                 <div style='font-size:12px;color:#8890a4;margin-top:2px'>📍 {p["location"]} · 👤 {p["client"]}</div></div>
            <span class="badge {bm.get(p['status'],'badge-blue')}">{p["status"]}</span></div>
          <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0 10px'>
            <div><div style='font-size:10px;color:#555d72;text-transform:uppercase'>Capacity</div><div style='font-family:JetBrains Mono;font-size:16px;color:#00d4ff'>{p["capacity_mwh"]} MWh</div></div>
            <div><div style='font-size:10px;color:#555d72;text-transform:uppercase'>Power</div><div style='font-family:JetBrains Mono;font-size:16px;color:#e8eaf0'>{p["power_mw"]} MW</div></div>
            <div><div style='font-size:10px;color:#555d72;text-transform:uppercase'>Chemistry</div><div style='font-family:JetBrains Mono;font-size:16px;color:#ffb347'>{p["chemistry"]}</div></div>
            <div><div style='font-size:10px;color:#555d72;text-transform:uppercase'>Milestones</div><div style='font-family:JetBrains Mono;font-size:16px;color:#00e5a0'>{done}/{len(p["milestones"])}</div></div>
          </div>
          <div style='background:rgba(255,255,255,0.05);border-radius:4px;height:5px'><div style='background:#00d4ff;height:100%;width:{p["progress_pct"]}%;border-radius:4px'></div></div>
          <div style='display:flex;justify-content:space-between;margin-top:4px'>
            <span style='font-size:10px;color:#555d72'>{p["progress_pct"]}% complete</span>
            <span style='font-size:10px;color:#555d72'>Engineer: {p["engineer"]}</span></div></div>""",unsafe_allow_html=True)

# ═════════════════════════════  CANVAS  ══════════════════════════════════════
CAD_HTML='<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<style>\n@import url(\'https://fonts.googleapis.com/css2?family=Arial+Narrow&display=swap\');\n*{box-sizing:border-box;margin:0;padding:0}\nbody{font-family:Arial,Helvetica,sans-serif;background:#6b6b6b;display:flex;flex-direction:column;height:100vh;overflow:hidden;user-select:none}\n\n/* ── TOOLBAR ── */\n#toolbar{height:38px;background:#2d2d2d;display:flex;align-items:center;gap:3px;padding:0 8px;flex-shrink:0;border-bottom:1px solid #111}\n.tb{height:26px;padding:0 9px;border-radius:3px;font-size:11px;cursor:pointer;background:#3d3d3d;color:#ccc;border:1px solid #555;white-space:nowrap;font-family:Arial}\n.tb:hover{background:#4a4a4a;color:#fff}\n.tb.on{background:#1a6496;color:#fff;border-color:#2980b9}\n.tb.grn{background:#2e7d32;color:#fff;border-color:#388e3c}\n.tb.red{background:#c62828;color:#fff;border-color:#d32f2f}\n.tb.amber{background:#e65100;color:#fff;border-color:#f57c00}\n.sep2{width:1px;height:20px;background:#555;margin:0 3px}\n#layer-sel{height:22px;padding:0 5px;background:#3d3d3d;border:1px solid #555;color:#ccc;font-size:10px;border-radius:3px}\n#coords-bar{font-family:\'Courier New\',monospace;font-size:10px;color:#aaa;margin-left:auto;padding-right:4px}\n\n/* ── MAIN LAYOUT ── */\n#main{display:flex;flex:1;overflow:hidden}\n\n/* ── LEFT PANEL ── */\n#panel{width:160px;flex-shrink:0;background:#2d2d2d;border-right:1px solid #111;overflow-y:auto;padding:6px 5px}\n#panel::-webkit-scrollbar{width:4px}#panel::-webkit-scrollbar-thumb{background:#555}\n.p-sec{font-size:9px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.08em;padding:5px 3px 3px;margin-top:4px;border-bottom:1px solid #444}\n.comp-grid{display:grid;grid-template-columns:1fr 1fr;gap:3px;margin:4px 0}\n.ci{display:flex;flex-direction:column;align-items:center;gap:2px;padding:5px 2px;border:1px solid #444;border-radius:3px;cursor:grab;background:#383838;transition:all .12s}\n.ci:hover{border-color:#2980b9;background:#404040}\n.ci:active{cursor:grabbing;border-color:#1a6496}\n.ci svg{width:38px;height:28px}\n.ci span{font-size:8px;color:#999;text-align:center;line-height:1.2}\n\n/* ── CANVAS WRAP ── */\n#canvas-wrap{flex:1;overflow:hidden;position:relative;background:#6b6b6b}\n#canvas-scroll{width:100%;height:100%;overflow:auto;cursor:crosshair}\n#canvas-scroll.sel{cursor:default}\n#canvas-scroll.pan{cursor:grab}\n\n/* ── PAPER (engineering drawing) ── */\n#paper{position:relative;background:#fff;box-shadow:0 4px 20px rgba(0,0,0,0.5)}\n\n/* ── DRAWING SVG ── */\n#draw-svg{position:absolute;top:0;left:0}\n\n/* ── TITLE BLOCK (right side, rendered in SVG) ── */\n\n/* ── STATUS BAR ── */\n#statusbar{height:20px;background:#1a1a1a;border-top:1px solid #000;display:flex;align-items:center;padding:0 10px;gap:12px;font-size:9px;color:#888;font-family:\'Courier New\',monospace;flex-shrink:0}\n\n/* ── PRINT STYLES ── */\n@media print{\n  body{background:#fff}\n  #toolbar,#panel,#statusbar{display:none}\n  #main{display:block}\n  #canvas-wrap{overflow:visible}\n  #canvas-scroll{overflow:visible}\n  #paper{box-shadow:none;margin:0;transform:none!important}\n}\n\n/* ── PROPERTIES POPUP ── */\n#prop-panel{display:none;position:fixed;bottom:28px;right:10px;width:220px;background:#2d2d2d;border:1px solid #555;border-radius:4px;z-index:100;padding:10px;font-size:11px;color:#ccc}\n#prop-panel.show{display:block}\n.pp-row{margin-bottom:6px}\n.pp-row label{display:block;font-size:9px;color:#888;margin-bottom:2px;text-transform:uppercase}\n.pp-row input,.pp-row select{width:100%;padding:3px 5px;background:#3d3d3d;border:1px solid #555;color:#ddd;font-size:10px;border-radius:2px;font-family:Arial}\n</style>\n</head>\n<body>\n\n<!-- TOOLBAR -->\n<div id="toolbar">\n  <button class="tb on" id="bt-sel" onclick="setTool(\'sel\')" title="Select (V)">▲ Select</button>\n  <button class="tb" id="bt-line" onclick="setTool(\'line\')" title="Line (L)">╱ Line</button>\n  <button class="tb" id="bt-rect" onclick="setTool(\'rect\')" title="Rectangle (R)">□ Rect</button>\n  <button class="tb" id="bt-poly" onclick="setTool(\'poly\')" title="Polyline (P)">⌐ Poly</button>\n  <button class="tb" id="bt-circle" onclick="setTool(\'circle\')" title="Circle (C)">○ Circle</button>\n  <button class="tb" id="bt-text" onclick="setTool(\'text\')" title="Text (T)">T Text</button>\n  <button class="tb" id="bt-dim" onclick="setTool(\'dim\')" title="Dimension (D)">↔ Dim</button>\n  <div class="sep2"></div>\n  <select id="layer-sel" onchange="currentLayer=this.value">\n    <option value="0">Layer 0 – General</option>\n    <option value="SITE">SITE-BOUNDARY</option>\n    <option value="BATT">BATTERY</option>\n    <option value="MVT">MV-TRANSFORMER</option>\n    <option value="ROAD">ACCESS-ROAD</option>\n    <option value="FENCE">FENCE</option>\n    <option value="ELEC">ELECTRICAL</option>\n    <option value="TEXT">TEXT</option>\n    <option value="DIM">DIMENSION</option>\n  </select>\n  <div class="sep2"></div>\n  <button class="tb" onclick="snapOn=!snapOn;this.classList.toggle(\'on\')" id="bt-snap" title="Grid Snap (S)" class="tb on">⊞ Snap</button>\n  <button class="tb" onclick="gridVis=!gridVis;toggleGrid()" title="Grid (G)">⋮⋮ Grid</button>\n  <button class="tb" onclick="zoomFit()" title="Zoom Fit (F)">⊡ Fit</button>\n  <button class="tb" onclick="zoomIn()" title="Zoom In (+)">+ Zoom</button>\n  <button class="tb" onclick="zoomOut()" title="Zoom Out (-)">− Zoom</button>\n  <button class="tb" onclick="doUndo()" title="Undo (Ctrl+Z)">↩ Undo</button>\n  <div class="sep2"></div>\n  <button class="tb grn" onclick="exportSVG()" title="Export SVG">↓ SVG</button>\n  <button class="tb amber" onclick="exportDXF()" title="Export DXF/DWG">↓ DXF</button>\n  <button class="tb" onclick="exportDWG()" title="Export DWG (DXF format, AutoCAD compatible)" style="background:#5d4037;color:#fff;border-color:#795548">↓ DWG</button>\n  <button class="tb" onclick="exportPDF()" title="Print / Export PDF">↓ PDF</button>\n  <button class="tb red" onclick="clearDwg()" title="Clear Drawing">✕ Clear</button>\n  <div id="coords-bar">X: 0.00\'    Y: 0.00\'    Scale: 1"=30\'</div>\n</div>\n\n<!-- MAIN -->\n<div id="main">\n  <!-- LEFT COMPONENT PANEL -->\n  <div id="panel">\n    <div class="p-sec">Site Civil</div>\n    <div class="comp-grid">\n      <div class="ci" draggable="true" data-type="site_boundary" data-w="500" data-h="300" title="Site Boundary">\n        <svg viewBox="0 0 38 28"><rect x="2" y="2" width="34" height="24" rx="4" fill="none" stroke="#d32f2f" stroke-width="2"/></svg>\n        <span>Site Boundary</span>\n      </div>\n      <div class="ci" draggable="true" data-type="fence" data-w="200" data-h="10" title="Fence Line">\n        <svg viewBox="0 0 38 28"><line x1="2" y1="14" x2="36" y2="14" stroke="#333" stroke-width="1.5" stroke-dasharray="4 2"/><circle cx="10" cy="14" r="2" fill="#333"/><circle cx="20" cy="14" r="2" fill="#333"/><circle cx="30" cy="14" r="2" fill="#333"/></svg>\n        <span>Fence</span>\n      </div>\n      <div class="ci" draggable="true" data-type="access_road" data-w="200" data-h="30" title="Access Road">\n        <svg viewBox="0 0 38 28"><rect x="2" y="8" width="34" height="12" fill="#bcaaa4" stroke="#795548" stroke-width="1"/><line x1="19" y1="8" x2="19" y2="20" stroke="#fff" stroke-width="1" stroke-dasharray="3 2"/></svg>\n        <span>Access Road</span>\n      </div>\n      <div class="ci" draggable="true" data-type="stormwater" data-w="80" data-h="60" title="Stormwater Pond">\n        <svg viewBox="0 0 38 28"><ellipse cx="19" cy="14" rx="15" ry="10" fill="#bbdefb" stroke="#1565c0" stroke-width="1.2"/><path d="M9 14 Q14 10 19 14 Q24 18 29 14" fill="none" stroke="#1565c0" stroke-width="0.8"/></svg>\n        <span>Storm Pond</span>\n      </div>\n      <div class="ci" draggable="true" data-type="access_gate" data-w="20" data-h="20" title="Access Gate">\n        <svg viewBox="0 0 38 28"><line x1="19" y1="5" x2="19" y2="14" stroke="#333" stroke-width="1.5"/><line x1="19" y1="14" x2="10" y2="23" stroke="#333" stroke-width="1.5"/><line x1="19" y1="14" x2="28" y2="23" stroke="#333" stroke-width="1.5"/><rect x="16" y="2" width="6" height="4" fill="#333"/></svg>\n        <span>Access Gate</span>\n      </div>\n      <div class="ci" draggable="true" data-type="fire_staging" data-w="80" data-h="80" title="Fire Staging Area">\n        <svg viewBox="0 0 38 28"><rect x="4" y="4" width="30" height="20" fill="none" stroke="#b71c1c" stroke-width="1" stroke-dasharray="4 2"/><text x="19" y="12" text-anchor="middle" font-size="5" fill="#b71c1c">▲▲▲</text><text x="19" y="20" text-anchor="middle" font-size="5" fill="#b71c1c">FIRE</text></svg>\n        <span>Fire Staging</span>\n      </div>\n    </div>\n\n    <div class="p-sec">BESS Equipment</div>\n    <div class="comp-grid">\n      <div class="ci" draggable="true" data-type="megapack" data-w="60" data-h="20" title="Tesla Megapack 3 Container">\n        <svg viewBox="0 0 38 28"><rect x="2" y="6" width="34" height="16" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1.5"/><line x1="14" y1="6" x2="14" y2="22" stroke="#2e7d32" stroke-width="0.8"/><line x1="24" y1="6" x2="24" y2="22" stroke="#2e7d32" stroke-width="0.8"/><line x1="2" y1="14" x2="36" y2="14" stroke="#2e7d32" stroke-width="0.5"/><text x="19" y="11" text-anchor="middle" font-size="4.5" fill="#1b5e20" font-weight="bold">MP3</text></svg>\n        <span>Megapack 3</span>\n      </div>\n      <div class="ci" draggable="true" data-type="mv_transformer" data-w="20" data-h="20" title="MV Transformer">\n        <svg viewBox="0 0 38 28"><rect x="8" y="4" width="22" height="20" fill="#fce4ec" stroke="#c2185b" stroke-width="1.5"/><line x1="8" y1="14" x2="30" y2="14" stroke="#c2185b" stroke-width="0.7"/><text x="19" y="11" text-anchor="middle" font-size="4" fill="#880e4f">MVT</text><text x="19" y="20" text-anchor="middle" font-size="3.5" fill="#880e4f">34.5kV</text></svg>\n        <span>MV Transformer</span>\n      </div>\n      <div class="ci" draggable="true" data-type="site_control" data-w="40" data-h="40" title="Site Control Center">\n        <svg viewBox="0 0 38 28"><rect x="8" y="4" width="22" height="20" fill="#fff8e1" stroke="#f57f17" stroke-width="1.5"/><line x1="19" y1="4" x2="19" y2="24" stroke="#f57f17" stroke-width="0.7"/><line x1="8" y1="14" x2="30" y2="14" stroke="#f57f17" stroke-width="0.7"/><text x="19" y="12" text-anchor="middle" font-size="4" fill="#e65100">SCC</text></svg>\n        <span>Site Control</span>\n      </div>\n      <div class="ci" draggable="true" data-type="aux_transformer" data-w="30" data-h="30" title="Aux Transformer">\n        <svg viewBox="0 0 38 28"><rect x="10" y="4" width="18" height="20" fill="#f3e5f5" stroke="#7b1fa2" stroke-width="1.5"/><text x="19" y="12" text-anchor="middle" font-size="4" fill="#4a148c">AUX</text><text x="19" y="20" text-anchor="middle" font-size="3.5" fill="#4a148c">XFMR</text></svg>\n        <span>Aux Transformer</span>\n      </div>\n      <div class="ci" draggable="true" data-type="substation" data-w="80" data-h="60" title="POI/Project Substation">\n        <svg viewBox="0 0 38 28"><rect x="2" y="2" width="34" height="24" fill="#e8eaf6" stroke="#283593" stroke-width="1.5"/><text x="19" y="12" text-anchor="middle" font-size="4" fill="#1a237e">POI</text><text x="19" y="20" text-anchor="middle" font-size="3.5" fill="#1a237e">SUBSTATION</text></svg>\n        <span>Substation</span>\n      </div>\n      <div class="ci" draggable="true" data-type="spare_equip" data-w="60" data-h="40" title="Spare Equipment Area">\n        <svg viewBox="0 0 38 28"><rect x="4" y="4" width="30" height="20" fill="none" stroke="#666" stroke-width="1" stroke-dasharray="3 3"/><text x="19" y="16" text-anchor="middle" font-size="5" fill="#666">SPARE</text></svg>\n        <span>Spare Equip.</span>\n      </div>\n    </div>\n\n    <div class="p-sec">Electrical (SLD)</div>\n    <div class="comp-grid">\n      <div class="ci" draggable="true" data-type="vcb" data-w="15" data-h="40" title="Vacuum Circuit Breaker">\n        <svg viewBox="0 0 38 28"><line x1="19" y1="2" x2="19" y2="10" stroke="#b71c1c" stroke-width="2"/><rect x="13" y="10" width="12" height="8" fill="#ffebee" stroke="#b71c1c" stroke-width="1.2"/><line x1="19" y1="18" x2="19" y2="26" stroke="#b71c1c" stroke-width="2" stroke-dasharray="3 1"/><text x="19" y="16" text-anchor="middle" font-size="4" fill="#b71c1c">VCB</text></svg>\n        <span>VCB</span>\n      </div>\n      <div class="ci" draggable="true" data-type="busbar_el" data-w="120" data-h="8" title="MV Busbar">\n        <svg viewBox="0 0 38 28"><rect x="2" y="11" width="34" height="6" fill="#616161" stroke="#212121" stroke-width="1"/><line x1="10" y1="5" x2="10" y2="11" stroke="#616161" stroke-width="2"/><line x1="19" y1="5" x2="19" y2="11" stroke="#616161" stroke-width="2"/><line x1="28" y1="5" x2="28" y2="11" stroke="#616161" stroke-width="2"/></svg>\n        <span>34.5kV Busbar</span>\n      </div>\n      <div class="ci" draggable="true" data-type="pcs_el" data-w="25" data-h="30" title="PCS / Inverter">\n        <svg viewBox="0 0 38 28"><rect x="5" y="3" width="28" height="22" fill="#fff9c4" stroke="#f9a825" stroke-width="1.5"/><path d="M12 18L17 8 17 13 22 13 22 18 17 18 17 23Z" fill="none" stroke="#f57f17" stroke-width="1" stroke-linejoin="round"/><text x="29" y="17" text-anchor="middle" font-size="4" fill="#e65100">PCS</text></svg>\n        <span>PCS/Inverter</span>\n      </div>\n      <div class="ci" draggable="true" data-type="gsu_transformer" data-w="30" data-h="30" title="GSU Transformer 115kV">\n        <svg viewBox="0 0 38 28"><circle cx="14" cy="14" r="9" fill="none" stroke="#5c35a5" stroke-width="1.5"/><circle cx="24" cy="14" r="9" fill="none" stroke="#5c35a5" stroke-width="1.5"/><line x1="1" y1="14" x2="5" y2="14" stroke="#5c35a5" stroke-width="1.5"/><line x1="33" y1="14" x2="37" y2="14" stroke="#5c35a5" stroke-width="1.5"/></svg>\n        <span>GSU 115kV</span>\n      </div>\n    </div>\n\n    <div class="p-sec">Annotation</div>\n    <div class="comp-grid">\n      <div class="ci" draggable="true" data-type="north_arrow" data-w="40" data-h="40" title="North Arrow">\n        <svg viewBox="0 0 38 28"><line x1="19" y1="4" x2="19" y2="24" stroke="#333" stroke-width="1.5"/><path d="M14 12 L19 4 L24 12Z" fill="#333"/><text x="19" y="27" text-anchor="middle" font-size="6" font-weight="bold" fill="#333">N</text></svg>\n        <span>North Arrow</span>\n      </div>\n      <div class="ci" draggable="true" data-type="scale_bar" data-w="100" data-h="15" title="Scale Bar">\n        <svg viewBox="0 0 38 28"><rect x="2" y="12" width="34" height="5" fill="none" stroke="#333" stroke-width="1"/><rect x="2" y="12" width="8" height="5" fill="#333"/><rect x="18" y="12" width="8" height="5" fill="#333"/><text x="2" y="10" font-size="4" fill="#333">0</text><text x="36" y="10" text-anchor="end" font-size="4" fill="#333">150\'</text></svg>\n        <span>Scale Bar</span>\n      </div>\n    </div>\n  </div>\n\n  <!-- CANVAS AREA -->\n  <div id="canvas-wrap">\n    <div id="canvas-scroll">\n      <div id="paper">\n        <svg id="draw-svg" xmlns="http://www.w3.org/2000/svg">\n          <defs>\n            <pattern id="smallgrid" width="10" height="10" patternUnits="userSpaceOnUse">\n              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#e0e0e0" stroke-width="0.3"/>\n            </pattern>\n            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">\n              <rect width="50" height="50" fill="url(#smallgrid)"/>\n              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#bdbdbd" stroke-width="0.6"/>\n            </pattern>\n            <pattern id="hatch-veg" width="8" height="8" patternUnits="userSpaceOnUse">\n              <path d="M0 8 L8 0" stroke="#388e3c" stroke-width="1"/>\n            </pattern>\n            <pattern id="hatch-fire" width="8" height="8" patternUnits="userSpaceOnUse">\n              <path d="M0 8 L8 0M-2 2 L2 -2M6 10 L10 6" stroke="#b71c1c" stroke-width="1"/>\n            </pattern>\n            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">\n              <path d="M0 0L10 5L0 10Z" fill="#333"/>\n            </marker>\n            <marker id="dim-end" viewBox="-1 -4 2 8" refX="0" refY="0" markerWidth="4" markerHeight="8" orient="auto">\n              <line x1="0" y1="-4" x2="0" y2="4" stroke="#333" stroke-width="1.5"/>\n            </marker>\n          </defs>\n          <!-- GRID LAYER -->\n          <g id="g-grid"><rect id="grid-rect" fill="url(#grid)"/></g>\n          <!-- DRAWING LAYERS -->\n          <g id="g-0"></g>\n          <g id="g-SITE"></g>\n          <g id="g-BATT"></g>\n          <g id="g-MVT"></g>\n          <g id="g-ROAD"></g>\n          <g id="g-FENCE"></g>\n          <g id="g-ELEC"></g>\n          <g id="g-TEXT"></g>\n          <g id="g-DIM"></g>\n          <!-- TEMP LAYER -->\n          <g id="g-temp"></g>\n          <!-- BORDER & TITLE BLOCK (always on top) -->\n          <g id="g-border"></g>\n        </svg>\n      </div>\n    </div>\n  </div>\n</div>\n\n<!-- STATUS BAR -->\n<div id="statusbar">\n  <span id="sb-tool">Tool: Select</span>\n  <span>|</span><span id="sb-layer">Layer: 0</span>\n  <span>|</span><span id="sb-snap">Snap: ON</span>\n  <span>|</span><span id="sb-objs">Objects: 0</span>\n  <span>|</span><span id="sb-zoom">Zoom: 100%</span>\n  <span style="margin-left:auto;color:#555">V=Select L=Line R=Rect P=Poly T=Text D=Dim F=Fit ESC=Cancel Del=Delete Ctrl+Z=Undo</span>\n</div>\n\n<!-- PROPERTIES PANEL -->\n<div id="prop-panel">\n  <div style="font-size:11px;font-weight:bold;color:#ddd;margin-bottom:8px;display:flex;justify-content:space-between">\n    Properties <span style="cursor:pointer;color:#888" onclick="hideProp()">✕</span>\n  </div>\n  <div class="pp-row"><label>Label</label><input id="pp-label" onchange="updateProp(\'label\',this.value)"></div>\n  <div class="pp-row"><label>Layer</label>\n    <select id="pp-layer" onchange="updateProp(\'layer\',this.value)">\n      <option value="0">0 – General</option><option value="SITE">SITE-BOUNDARY</option>\n      <option value="BATT">BATTERY</option><option value="MVT">MV-TRANSFORMER</option>\n      <option value="ROAD">ACCESS-ROAD</option><option value="FENCE">FENCE</option>\n      <option value="ELEC">ELECTRICAL</option><option value="TEXT">TEXT</option>\n    </select>\n  </div>\n  <div class="pp-row"><label>Rotation (°)</label><input id="pp-rot" type="number" value="0" onchange="updateProp(\'rot\',this.value)"></div>\n  <div class="pp-row"><label>Width</label><input id="pp-w" type="number" onchange="updatePropSize(\'w\',this.value)"></div>\n  <div class="pp-row"><label>Height</label><input id="pp-h" type="number" onchange="updatePropSize(\'h\',this.value)"></div>\n  <div style="margin-top:6px">\n    <button class="tb red" style="width:100%;font-size:10px" onclick="deleteSelected()">Delete Object</button>\n  </div>\n</div>\n\n<script>\n// ═══════════════════════════════════════════════════════════════\n// CONSTANTS & STATE\n// ═══════════════════════════════════════════════════════════════\nconst SCALE = 30; // 1 inch = 30 feet → 1px = 1 foot at 1:30\nconst PAPER_W = 1100; // px (11" × 100dpi)\nconst PAPER_H = 700;  // px (7" drawing area + title block)\nconst TB_W = 220;     // title block width px\nconst DRAW_W = PAPER_W - TB_W;\nconst SNAP_GRID = 10; // snap every 10px = 10 feet\n\nlet tool = \'sel\', currentLayer = \'0\', snapOn = true, gridVis = true;\nlet objs = [], selObj = null, undoStack = [];\nlet idN = 0;\nlet drawing = false, startX = 0, startY = 0;\nlet polyPts = [];\nlet tempEl = null;\nlet dragType = null;\nlet zoomLevel = 1.0;\n\n// Title block state (editable)\nlet TB = {\n  projectName: \'BARNETT RD\\nFACILITY\',\n  subtitle: \'PRELIMINARY\\nDESIGN\',\n  location: \'GEORGIA\\nUSA\',\n  sheetName: \'CIVIL SITE PLAN\',\n  sheetNum: \'S-02\',\n  scale: "1\\":30\'",\n  drwn: \'AM\', revw: \'RB\', apprvd: \'AV\', size: \'11"×17"\',\n  latlong: \'33.536647°, -82.809725°\',\n  company: \'SunStripe\',\n  companyFull: \'Trusted Clean Energy Partners\',\n  address: \'6363 N State Highway 161, Ste 250 Irving, TX 75038\',\n  revisions: [\n    {rev:\'A\', desc:\'PRELIMINARY\', by:\'AM\', date:\'2026/01/21\'},\n    {rev:\'B\', desc:\'COMMENTS UPDATED\', by:\'AM\', date:\'2026/03/06\'},\n    {rev:\'C\', desc:\'COMMENTS UPDATED\', by:\'AM\', date:\'2026/03/10\'},\n    {rev:\'D\', desc:\'\', by:\'\', date:\'\'},\n    {rev:\'E\', desc:\'\', by:\'\', date:\'\'},\n  ],\n  copyright: \'THIS DRAWING IS THE PROPERTY OF SUNSTRIPE, Inc. ANY REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN PERMISSION OF SUNSTRIPE, Inc IS PROHIBITED.\',\n  disclaimer: \'FOR INFORMATION PURPOSES ONLY - NOT FOR CONSTRUCTION\',\n};\n\nconst LEGEND_ITEMS = [\n  {sym:\'line-red-solid\', label:\'SITE BOUNDARY\'},\n  {sym:\'line-black-dash\', label:\'FENCE\'},\n  {sym:\'fill-hatch-veg\', label:\'VEGETATION\'},\n  {sym:\'fill-blue-wave\', label:\'WETLANDS\'},\n  {sym:\'fill-blue-solid\', label:\'STORM WATER POND\'},\n  {sym:\'line-orange-dashdot\', label:\'FIRE BATTERY ACCESS ROAD\'},\n  {sym:\'line-tan-solid\', label:\'ACCESS ROAD\'},\n  {sym:\'gate-sym\', label:\'ACCESS GATE\'},\n  {sym:\'rect-green\', label:\'BATTERY CONTAINER\'},\n  {sym:\'rect-pink\', label:\'MV TRANSFORMER\'},\n  {sym:\'fill-hatch-fire\', label:\'FIRE STAGING AREA\'},\n];\n\n// Layer color map\nconst LAYER_COLORS = {\n  \'0\':\'#222\', \'SITE\':\'#d32f2f\', \'BATT\':\'#2e7d32\', \'MVT\':\'#c2185b\',\n  \'ROAD\':\'#795548\', \'FENCE\':\'#333\', \'ELEC\':\'#1565c0\', \'TEXT\':\'#222\', \'DIM\':\'#555\'\n};\n\n// ═══════════════════════════════════════════════════════════════\n// INIT\n// ═══════════════════════════════════════════════════════════════\nfunction init() {\n  const svg = document.getElementById(\'draw-svg\');\n  const paper = document.getElementById(\'paper\');\n  paper.style.width = PAPER_W + \'px\';\n  paper.style.height = PAPER_H + \'px\';\n  svg.setAttribute(\'width\', PAPER_W);\n  svg.setAttribute(\'height\', PAPER_H);\n  svg.setAttribute(\'viewBox\', `0 0 ${PAPER_W} ${PAPER_H}`);\n\n  document.getElementById(\'grid-rect\').setAttribute(\'width\', DRAW_W);\n  document.getElementById(\'grid-rect\').setAttribute(\'height\', PAPER_H);\n\n  drawBorder();\n  buildTitleBlock();\n  loadSampleLayout();\n\n  // Canvas scroll events\n  const cs = document.getElementById(\'canvas-scroll\');\n  cs.addEventListener(\'mousedown\', onMouseDown);\n  cs.addEventListener(\'mousemove\', onMouseMove);\n  cs.addEventListener(\'mouseup\', onMouseUp);\n  cs.addEventListener(\'dblclick\', onDblClick);\n  cs.addEventListener(\'wheel\', onWheel, {passive:false});\n  cs.addEventListener(\'dragover\', e => e.preventDefault());\n  cs.addEventListener(\'drop\', onDrop);\n\n  document.addEventListener(\'keydown\', onKey);\n  document.querySelectorAll(\'.ci\').forEach(el => {\n    el.addEventListener(\'dragstart\', ev => { dragType = el.dataset; });\n  });\n\n  document.getElementById(\'bt-snap\').classList.add(\'on\');\n  updateSB();\n}\n\n// ═══════════════════════════════════════════════════════════════\n// BORDER & TITLE BLOCK\n// ═══════════════════════════════════════════════════════════════\nfunction drawBorder() {\n  const g = document.getElementById(\'g-border\');\n  g.innerHTML = \'\';\n  const dw = DRAW_W, pw = PAPER_W, ph = PAPER_H;\n\n  // Outer border\n  makeSVG(g,\'rect\',{x:2,y:2,width:pw-4,height:ph-4,fill:\'none\',stroke:\'#000\',\'stroke-width\':\'2\'});\n  // Drawing area border\n  makeSVG(g,\'rect\',{x:8,y:8,width:dw-16,height:ph-16,fill:\'none\',stroke:\'#000\',\'stroke-width\':\'0.8\'});\n  // Vertical title block separator\n  makeSVG(g,\'line\',{x1:dw,y1:2,x2:dw,y2:ph-2,stroke:\'#000\',\'stroke-width\':\'1.5\'});\n}\n\nfunction buildTitleBlock() {\n  const g = document.getElementById(\'g-border\');\n  const x0 = DRAW_W + 2; // start x of title block\n  const tw = TB_W - 4;   // usable width\n  const ph = PAPER_H;\n\n  function txt(x,y,t,fs,opts={}) {\n    const el = makeSVG(g,\'text\',{x,y,\'font-size\':fs,\'font-family\':\'Arial\',fill:\'#000\',...opts});\n    // handle newlines\n    if(t.includes(\'\\n\')) {\n      t.split(\'\\n\').forEach((line, i) => {\n        const ts = makeSVG(el,\'tspan\',{x,dy: i===0?0:fs*1.2});\n        ts.textContent = line;\n      });\n    } else {\n      el.textContent = t;\n    }\n    return el;\n  }\n  function hline(y, stroke=\'#000\', sw=0.5) {\n    makeSVG(g,\'line\',{x1:x0,y1:y,x2:x0+tw,y2:y,stroke,stroke_width:sw});\n    // use setAttribute for stroke-width\n    const el = g.lastChild; el.setAttribute(\'stroke-width\', sw);\n    return el;\n  }\n  function vline(x, y1, y2) {\n    const el = makeSVG(g,\'line\',{x1:x,y1,x2:x,y2,stroke:\'#000\'});\n    el.setAttribute(\'stroke-width\',\'0.5\'); return el;\n  }\n\n  let cy = 2;\n\n  // Copyright header\n  const cpBox = makeSVG(g,\'rect\',{x:x0,y:cy,width:tw,height:16,fill:\'#fff\',stroke:\'#000\'});\n  cpBox.setAttribute(\'stroke-width\',\'0.5\');\n  const cpTxt = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+6,\'text-anchor\':\'middle\',\'font-size\':\'4.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n  cpTxt.setAttribute(\'font-weight\',\'bold\');\n  // wrap copyright text into 2 lines\n  const cpL1 = makeSVG(cpTxt,\'tspan\',{x:x0+tw/2,dy:0});\n  cpL1.textContent = \'THIS DRAWING IS THE PROPERTY OF SUNSTRIPE, Inc.\';\n  const cpL2 = makeSVG(cpTxt,\'tspan\',{x:x0+tw/2,dy:6});\n  cpL2.textContent = \'ANY REPRODUCTION WITHOUT WRITTEN PERMISSION IS PROHIBITED.\';\n  cy += 16;\n  hline(cy);\n\n  // LEGENDS section\n  const legH = LEGEND_ITEMS.length * 13 + 14;\n  txt(x0+tw/2, cy+8, \'LEGENDS\', 7, {\'text-anchor\':\'middle\',\'font-weight\':\'bold\'});\n  cy += 12; hline(cy);\n\n  LEGEND_ITEMS.forEach(item => {\n    drawLegendSymbol(g, x0+4, cy+2, item.sym);\n    const lt = makeSVG(g,\'text\',{x:x0+28,y:cy+8,\'font-size\':\'5.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n    lt.textContent = item.label;\n    cy += 12;\n  });\n  hline(cy); cy += 2;\n\n  // North arrow area\n  const naY = cy;\n  drawNorthArrow(g, x0+tw-28, cy+22);\n  cy += 48; hline(cy);\n\n  // Project title (large)\n  const titleH = 65;\n  const titleBox = makeSVG(g,\'rect\',{x:x0,y:cy,width:tw,height:titleH,fill:\'#fff\'});\n  TB.projectName.split(\'\\n\').forEach((line, i) => {\n    const t = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+14+i*14,\'text-anchor\':\'middle\',\'font-size\':\'12.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n    t.setAttribute(\'font-weight\',\'bold\'); t.textContent = line;\n  });\n  cy += TB.projectName.split(\'\\n\').length*14 + 4;\n  TB.subtitle.split(\'\\n\').forEach((line, i) => {\n    const t = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+i*12,\'text-anchor\':\'middle\',\'font-size\':\'10\',\'font-family\':\'Arial\',fill:\'#000\'});\n    t.setAttribute(\'font-weight\',\'bold\'); t.textContent = line;\n  });\n  cy += TB.subtitle.split(\'\\n\').length*12+2;\n  TB.location.split(\'\\n\').forEach((line, i) => {\n    const t = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+i*9,\'text-anchor\':\'middle\',\'font-size\':\'7\',\'font-family\':\'Arial\',fill:\'#000\'});\n    t.textContent = line;\n  });\n  cy = naY + titleH; hline(cy);\n\n  // Revision table\n  const revTableH = TB.revisions.length * 11 + 11;\n  const revCols = [x0, x0+12, x0+tw*0.5, x0+tw*0.75, x0+tw];\n  // Header\n  [\'REV\',\'DESCRIPTION\',\'BY\',\'DATE\'].forEach((h,i) => {\n    const t = makeSVG(g,\'text\',{x:revCols[i]+2,y:cy+8,\'font-size\':\'5.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n    t.setAttribute(\'font-weight\',\'bold\'); t.textContent = h;\n  });\n  cy += 10; hline(cy);\n  revCols.slice(1,-1).forEach(x => vline(x,cy-10,cy+TB.revisions.length*11));\n\n  TB.revisions.forEach(r => {\n    [r.rev, r.desc, r.by, r.date].forEach((v,i) => {\n      const t = makeSVG(g,\'text\',{x:revCols[i]+2,y:cy+8,\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#000\'});\n      t.textContent = v||\'\';\n    });\n    cy += 10; hline(cy);\n  });\n\n  // SunStripe branding\n  cy += 3;\n  const logoT = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+11,\'text-anchor\':\'middle\',\'font-size\':\'13\',\'font-family\':\'Arial\',fill:\'#d32f2f\'});\n  logoT.setAttribute(\'font-weight\',\'bold\'); logoT.setAttribute(\'font-style\',\'italic\');\n  logoT.textContent = \'SunStripe\';\n  cy += 14;\n  const subT = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+1,\'text-anchor\':\'middle\',\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#555\'});\n  subT.textContent = TB.companyFull;\n  cy += 7;\n  const addrT = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+1,\'text-anchor\':\'middle\',\'font-size\':\'4.5\',\'font-family\':\'Arial\',fill:\'#555\'});\n  addrT.textContent = TB.address;\n  cy += 8; hline(cy);\n\n  // Sheet name\n  txt(x0+4, cy+6, \'SHEET NAME:\', 5, {\'font-weight\':\'bold\'});\n  cy += 8;\n  const snT = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+7,\'text-anchor\':\'middle\',\'font-size\':\'7.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n  snT.setAttribute(\'font-weight\',\'bold\'); snT.textContent = TB.sheetName;\n  cy += 12; hline(cy);\n\n  // Lat/Long\n  txt(x0+4, cy+7, \'LAT/LONG: \'+TB.latlong, 4.8);\n  cy += 10; hline(cy);\n\n  // DRWN/REVW/APPRVD/SIZE\n  const botCols = [x0, x0+tw*0.33, x0+tw*0.6, x0+tw*0.8, x0+tw];\n  [\'DRWN\',\'REVW\',\'APPRVD\',\'SIZE\'].forEach((h,i) => {\n    const t = makeSVG(g,\'text\',{x:botCols[i]+2,y:cy+7,\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#000\'});\n    t.setAttribute(\'font-weight\',\'bold\'); t.textContent = h;\n  });\n  cy += 9; hline(cy);\n  botCols.slice(1,-1).forEach(x => vline(x,cy-9,cy+10));\n  [TB.drwn,TB.revw,TB.apprvd,TB.size].forEach((v,i) => {\n    const t = makeSVG(g,\'text\',{x:botCols[i]+2,y:cy+8,\'font-size\':\'5.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n    t.textContent = v;\n  });\n  cy += 10; hline(cy);\n\n  // Sheet number\n  const shT = makeSVG(g,\'text\',{x:x0+tw/2,y:cy+18,\'text-anchor\':\'middle\',\'font-size\':\'22\',\'font-family\':\'Arial\',fill:\'#000\'});\n  shT.setAttribute(\'font-weight\',\'bold\'); shT.textContent = TB.sheetNum;\n  hline(PAPER_H - 12);\n\n  // Bottom disclaimer\n  const discT = makeSVG(g,\'text\',{x:PAPER_W/2,y:PAPER_H-4,\'text-anchor\':\'middle\',\'font-size\':\'5.5\',\'font-family\':\'Arial\',fill:\'#000\'});\n  discT.setAttribute(\'font-weight\',\'bold\'); discT.textContent = TB.disclaimer;\n}\n\nfunction drawLegendSymbol(parent, x, y, type) {\n  switch(type) {\n    case \'line-red-solid\':\n      makeSVG(parent,\'line\',{x1:x,y1:y+5,x2:x+22,y2:y+5,stroke:\'#d32f2f\',\'stroke-width\':\'2\'}); break;\n    case \'line-black-dash\':\n      const dl=makeSVG(parent,\'line\',{x1:x,y1:y+5,x2:x+22,y2:y+5,stroke:\'#333\',\'stroke-width\':\'1.5\'});dl.setAttribute(\'stroke-dasharray\',\'4 2\'); break;\n    case \'fill-hatch-veg\':\n      const rv=makeSVG(parent,\'rect\',{x,y:y+1,width:22,height:9,fill:\'url(#hatch-veg)\',stroke:\'#388e3c\',\'stroke-width\':\'0.5\'}); break;\n    case \'fill-blue-wave\':\n      makeSVG(parent,\'path\',{d:`M${x} ${y+5}Q${x+5} ${y+2} ${x+11} ${y+5}Q${x+17} ${y+8} ${x+22} ${y+5}`,fill:\'none\',stroke:\'#1565c0\',\'stroke-width\':\'1.5\'}); break;\n    case \'fill-blue-solid\':\n      makeSVG(parent,\'rect\',{x,y:y+1,width:22,height:9,fill:\'#bbdefb\',stroke:\'#1565c0\',\'stroke-width\':\'0.8\'}); break;\n    case \'line-orange-dashdot\':\n      const ol=makeSVG(parent,\'line\',{x1:x,y1:y+5,x2:x+22,y2:y+5,stroke:\'#e65100\',\'stroke-width\':\'2\'});ol.setAttribute(\'stroke-dasharray\',\'6 2 1 2\'); break;\n    case \'line-tan-solid\':\n      makeSVG(parent,\'line\',{x1:x,y1:y+5,x2:x+22,y2:y+5,stroke:\'#795548\',\'stroke-width\':\'2\'}); break;\n    case \'gate-sym\':\n      makeSVG(parent,\'line\',{x1:x+11,y1:y,x2:x+11,y2:y+7,stroke:\'#333\',\'stroke-width\':\'1.2\'});\n      makeSVG(parent,\'line\',{x1:x+11,y1:y+7,x2:x+5,y2:y+11,stroke:\'#333\',\'stroke-width\':\'1.2\'});\n      makeSVG(parent,\'line\',{x1:x+11,y1:y+7,x2:x+17,y2:y+11,stroke:\'#333\',\'stroke-width\':\'1.2\'}); break;\n    case \'rect-green\':\n      makeSVG(parent,\'rect\',{x,y:y+1,width:22,height:9,fill:\'#e8f5e9\',stroke:\'#2e7d32\',\'stroke-width\':\'1.2\'}); break;\n    case \'rect-pink\':\n      makeSVG(parent,\'rect\',{x:x+4,y:y+1,width:14,height:9,fill:\'#fce4ec\',stroke:\'#c2185b\',\'stroke-width\':\'1.2\'}); break;\n    case \'fill-hatch-fire\':\n      makeSVG(parent,\'rect\',{x,y:y+1,width:22,height:9,fill:\'url(#hatch-fire)\',stroke:\'#b71c1c\',\'stroke-width\':\'0.8\'}); break;\n  }\n}\n\nfunction drawNorthArrow(parent, cx, cy) {\n  const r = 14;\n  makeSVG(parent,\'circle\',{cx,cy,r,fill:\'none\',stroke:\'#333\',\'stroke-width\':\'1\'});\n  makeSVG(parent,\'polygon\',{points:`${cx},${cy-r+2} ${cx-6},${cy+4} ${cx},${cy} ${cx+6},${cy+4}`,fill:\'#333\',stroke:\'#333\',\'stroke-width\':\'0.5\'});\n  makeSVG(parent,\'polygon\',{points:`${cx},${cy-r+2} ${cx-6},${cy+4} ${cx},${cy} ${cx+6},${cy+4}`,fill:\'none\',stroke:\'#333\',\'stroke-width\':\'0.5\'});\n  // Filled left half\n  makeSVG(parent,\'path\',{d:`M${cx} ${cy-r+2} L${cx-6} ${cy+4} L${cx} ${cy} Z`,fill:\'#333\'});\n  const nt = makeSVG(parent,\'text\',{x:cx,y:cy+r-2,\'text-anchor\':\'middle\',\'font-size\':\'7\',\'font-family\':\'Arial\',fill:\'#333\'});\n  nt.setAttribute(\'font-weight\',\'bold\'); nt.textContent=\'N\';\n}\n\n// ═══════════════════════════════════════════════════════════════\n// SVG HELPERS\n// ═══════════════════════════════════════════════════════════════\nfunction makeSVG(parent, tag, attrs) {\n  const el = document.createElementNS(\'http://www.w3.org/2000/svg\', tag);\n  for(const [k,v] of Object.entries(attrs)) el.setAttribute(k.replace(\'_\',\'-\'), v);\n  parent.appendChild(el);\n  return el;\n}\n\nfunction getLayer(name) {\n  return document.getElementById(\'g-\' + (name||\'0\')) || document.getElementById(\'g-0\');\n}\n\n// ═══════════════════════════════════════════════════════════════\n// COORDINATE HELPERS\n// ═══════════════════════════════════════════════════════════════\nfunction getSVGCoords(e) {\n  const paper = document.getElementById(\'paper\');\n  const rect = paper.getBoundingClientRect();\n  const sx = (e.clientX - rect.left) / zoomLevel;\n  const sy = (e.clientY - rect.top) / zoomLevel;\n  return snapOn ? {x: Math.round(sx/SNAP_GRID)*SNAP_GRID, y: Math.round(sy/SNAP_GRID)*SNAP_GRID} : {x:sx, y:sy};\n}\n\nfunction toFeet(px) { return (px / SCALE).toFixed(1); }\n\n// ═══════════════════════════════════════════════════════════════\n// TOOL MANAGEMENT\n// ═══════════════════════════════════════════════════════════════\nfunction setTool(t) {\n  tool = t;\n  drawing = false; polyPts = [];\n  clearTemp();\n  document.querySelectorAll(\'.tb[id^="bt-"]\').forEach(b => b.classList.remove(\'on\'));\n  const b = document.getElementById(\'bt-\'+t);\n  if(b) b.classList.add(\'on\');\n  const names = {sel:\'Select\',line:\'Line\',rect:\'Rectangle\',poly:\'Polyline\',circle:\'Circle\',text:\'Text\',dim:\'Dimension\'};\n  document.getElementById(\'sb-tool\').textContent = \'Tool: \' + (names[t]||t);\n  const cs = document.getElementById(\'canvas-scroll\');\n  cs.className = t===\'sel\' ? \'sel\' : \'\';\n}\n\n// ═══════════════════════════════════════════════════════════════\n// MOUSE EVENTS\n// ═══════════════════════════════════════════════════════════════\nlet panMode=false, panSX=0, panSY=0, scrollSX=0, scrollSY=0;\nlet dragObj=null, dragOX=0, dragOY=0;\n\nfunction onMouseDown(e) {\n  if(e.button===1 || (e.button===0 && e.altKey)) {\n    panMode=true; panSX=e.clientX; panSY=e.clientY;\n    scrollSX=e.currentTarget.scrollLeft; scrollSY=e.currentTarget.scrollTop;\n    return;\n  }\n  const {x,y} = getSVGCoords(e);\n  if(x >= DRAW_W) return; // don\'t draw in title block\n\n  if(tool===\'sel\') {\n    const hit = hitTest(x,y);\n    if(hit) {\n      selectObj(hit);\n      dragObj=hit; dragOX=x-hit.x; dragOY=y-hit.y;\n      saveUndo();\n    } else {\n      selectObj(null);\n    }\n    return;\n  }\n  if(tool===\'text\') { addText(x,y); return; }\n  if(tool===\'poly\') {\n    if(!drawing) { drawing=true; polyPts=[{x,y}]; }\n    else { polyPts.push({x,y}); }\n    drawTempPoly(x,y);\n    return;\n  }\n  if(tool===\'dim\') {\n    if(!drawing) { drawing=true; startX=x; startY=y; }\n    else { addDimension(startX,startY,x,y); drawing=false; clearTemp(); }\n    return;\n  }\n  drawing=true; startX=x; startY=y;\n}\n\nfunction onMouseMove(e) {\n  if(panMode) {\n    const cs = e.currentTarget;\n    cs.scrollLeft = scrollSX-(e.clientX-panSX);\n    cs.scrollTop  = scrollSY-(e.clientY-panSY);\n    return;\n  }\n  const {x,y} = getSVGCoords(e);\n  document.getElementById(\'coords-bar\').textContent =\n    `X: ${toFeet(x)}\'    Y: ${toFeet(y)}\'    Scale: 1"=30\'`;\n\n  if(dragObj && tool===\'sel\') {\n    dragObj.x = Math.round((x-dragOX)/SNAP_GRID)*SNAP_GRID;\n    dragObj.y = Math.round((y-dragOY)/SNAP_GRID)*SNAP_GRID;\n    renderObj(dragObj);\n    return;\n  }\n  if(!drawing) return;\n  clearTemp();\n  const tmp = document.getElementById(\'g-temp\');\n\n  if(tool===\'line\') drawTmpLine(tmp,startX,startY,x,y);\n  else if(tool===\'rect\') drawTmpRect(tmp,startX,startY,x,y);\n  else if(tool===\'circle\') drawTmpCircle(tmp,startX,startY,x,y);\n  else if(tool===\'poly\') { drawTempPoly(x,y); }\n  else if(tool===\'dim\') drawTmpDim(tmp,startX,startY,x,y);\n}\n\nfunction onMouseUp(e) {\n  if(panMode) { panMode=false; return; }\n  if(dragObj) { dragObj=null; return; }\n  if(!drawing) return;\n  const {x,y} = getSVGCoords(e);\n  if(x >= DRAW_W) { drawing=false; clearTemp(); return; }\n  if(tool===\'line\') { addLine(startX,startY,x,y); drawing=false; clearTemp(); }\n  else if(tool===\'rect\') { addRect(startX,startY,x,y); drawing=false; clearTemp(); }\n  else if(tool===\'circle\') { addCircle(startX,startY,x,y); drawing=false; clearTemp(); }\n}\n\nfunction onDblClick(e) {\n  if(tool===\'poly\' && polyPts.length>=2) { commitPoly(); }\n}\n\nfunction onWheel(e) {\n  if(e.ctrlKey||e.metaKey) {\n    e.preventDefault();\n    const f = e.deltaY<0 ? 1.12 : 0.89;\n    setZoom(zoomLevel*f);\n  }\n}\n\n// ═══════════════════════════════════════════════════════════════\n// TEMP DRAWING\n// ═══════════════════════════════════════════════════════════════\nfunction clearTemp() { document.getElementById(\'g-temp\').innerHTML=\'\'; }\n\nfunction drawTmpLine(p,x1,y1,x2,y2) {\n  const l=makeSVG(p,\'line\',{x1,y1,x2,y2,stroke:LAYER_COLORS[currentLayer]||\'#333\',\'stroke-width\':\'1\'});\n  l.setAttribute(\'stroke-dasharray\',\'4 2\'); l.setAttribute(\'opacity\',\'0.7\');\n}\nfunction drawTmpRect(p,x1,y1,x2,y2) {\n  const r=makeSVG(p,\'rect\',{x:Math.min(x1,x2),y:Math.min(y1,y2),width:Math.abs(x2-x1),height:Math.abs(y2-y1),fill:\'none\',stroke:LAYER_COLORS[currentLayer]||\'#333\',\'stroke-width\':\'1\'});\n  r.setAttribute(\'stroke-dasharray\',\'4 2\'); r.setAttribute(\'opacity\',\'0.7\');\n}\nfunction drawTmpCircle(p,cx,cy,x2,y2) {\n  const r=Math.hypot(x2-cx,y2-cy);\n  const c=makeSVG(p,\'circle\',{cx,cy,r,fill:\'none\',stroke:LAYER_COLORS[currentLayer]||\'#333\',\'stroke-width\':\'1\'});\n  c.setAttribute(\'stroke-dasharray\',\'4 2\'); c.setAttribute(\'opacity\',\'0.7\');\n}\nfunction drawTempPoly(x,y) {\n  clearTemp();\n  const tmp=document.getElementById(\'g-temp\');\n  if(polyPts.length<1) return;\n  const pts=[...polyPts,{x,y}];\n  const pl=makeSVG(tmp,\'polyline\',{points:pts.map(p=>p.x+\',\'+p.y).join(\' \'),fill:\'none\',stroke:LAYER_COLORS[currentLayer]||\'#333\',\'stroke-width\':\'1\'});\n  pl.setAttribute(\'stroke-dasharray\',\'4 2\'); pl.setAttribute(\'opacity\',\'0.7\');\n  // dots at each vertex\n  polyPts.forEach(pt => makeSVG(tmp,\'circle\',{cx:pt.x,cy:pt.y,r:\'3\',fill:\'#1565c0\',opacity:\'0.8\'}));\n}\nfunction drawTmpDim(p,x1,y1,x2,y2) {\n  const dx=x2-x1, dy=y2-y1;\n  const len=Math.sqrt(dx*dx+dy*dy);\n  const off=20; // offset pixels\n  // perpendicular\n  const nx=-dy/len*off, ny=dx/len*off;\n  makeSVG(p,\'line\',{x1:x1+nx,y1:y1+ny,x2:x2+nx,y2:y2+ny,stroke:\'#555\',\'stroke-width\':\'0.8\',\'marker-start\':\'url(#dim-end)\',\'marker-end\':\'url(#dim-end)\'});\n  makeSVG(p,\'line\',{x1,y1,x2:x1+nx*1.2,y2:y1+ny*1.2,stroke:\'#555\',\'stroke-width\':\'0.5\'});\n  makeSVG(p,\'line\',{x1:x2,y1:y2,x2:x2+nx*1.2,y2:y2+ny*1.2,stroke:\'#555\',\'stroke-width\':\'0.5\'});\n  const t=makeSVG(p,\'text\',{x:(x1+x2)/2+nx*1.1,y:(y1+y2)/2+ny*1.1,\'text-anchor\':\'middle\',\'font-size\':\'8\',\'font-family\':\'Arial\',fill:\'#555\'});\n  t.textContent = Math.round(len/SCALE * 10)/10 + "\'";\n}\n\n// ═══════════════════════════════════════════════════════════════\n// OBJECT CREATION\n// ═══════════════════════════════════════════════════════════════\nfunction newId() { return \'o\'+(++idN); }\n\nfunction addLine(x1,y1,x2,y2) {\n  if(Math.abs(x2-x1)<2 && Math.abs(y2-y1)<2) return;\n  saveUndo();\n  const o={id:newId(),type:\'line\',x1,y1,x2,y2,layer:currentLayer,label:\'\'};\n  objs.push(o); renderObj(o); updateSB();\n}\n\nfunction addRect(x1,y1,x2,y2) {\n  if(Math.abs(x2-x1)<2 || Math.abs(y2-y1)<2) return;\n  saveUndo();\n  const o={id:newId(),type:\'rect\',x:Math.min(x1,x2),y:Math.min(y1,y2),w:Math.abs(x2-x1),h:Math.abs(y2-y1),layer:currentLayer,label:\'\'};\n  objs.push(o); renderObj(o); updateSB();\n}\n\nfunction addCircle(cx,cy,x2,y2) {\n  const r=Math.hypot(x2-cx,y2-cy);\n  if(r<3) return;\n  saveUndo();\n  const o={id:newId(),type:\'circle\',x:cx,y:cy,r,layer:currentLayer,label:\'\'};\n  objs.push(o); renderObj(o); updateSB();\n}\n\nfunction commitPoly() {\n  if(polyPts.length<2) { drawing=false; polyPts=[]; clearTemp(); return; }\n  saveUndo();\n  const o={id:newId(),type:\'poly\',pts:[...polyPts],layer:currentLayer,label:\'\'};\n  objs.push(o); renderObj(o);\n  drawing=false; polyPts=[]; clearTemp(); updateSB();\n}\n\nfunction addText(x,y) {\n  const val = prompt(\'Enter text:\');\n  if(!val) return;\n  saveUndo();\n  const o={id:newId(),type:\'text\',x,y,text:val,fs:8,layer:\'TEXT\',label:val};\n  objs.push(o); renderObj(o); updateSB();\n}\n\nfunction addDimension(x1,y1,x2,y2) {\n  if(Math.abs(x2-x1)<2 && Math.abs(y2-y1)<2) return;\n  saveUndo();\n  const o={id:newId(),type:\'dim\',x1,y1,x2,y2,layer:\'DIM\',label:\'\'};\n  objs.push(o); renderObj(o); updateSB();\n}\n\nfunction addComponent(type, x, y, w, h) {\n  saveUndo();\n  const defs = getCompDef(type);\n  const o={id:newId(),type:\'comp\',compType:type,x,y,w:w||defs.w,h:h||defs.h,layer:defs.layer,label:defs.label,rot:0};\n  objs.push(o); renderObj(o); updateSB();\n}\n\nfunction getCompDef(type) {\n  const map = {\n    megapack:      {w:70,h:22,layer:\'BATT\',label:\'TESLA MEGAPACK 3\'},\n    mv_transformer:{w:22,h:22,layer:\'MVT\', label:\'MV TRANSFORMER\'},\n    site_boundary: {w:500,h:300,layer:\'SITE\',label:\'SITE BOUNDARY\'},\n    fence:         {w:200,h:10,layer:\'FENCE\',label:\'FENCE\'},\n    access_road:   {w:200,h:30,layer:\'ROAD\',label:\'ACCESS ROAD\'},\n    stormwater:    {w:80,h:60,layer:\'0\',label:\'STORM WATER POND\'},\n    access_gate:   {w:20,h:20,layer:\'0\',label:\'ACCESS GATE\'},\n    fire_staging:  {w:80,h:80,layer:\'0\',label:\'FIRE STAGING\'},\n    site_control:  {w:40,h:40,layer:\'0\',label:\'SITE CONTROL CENTER\'},\n    aux_transformer:{w:30,h:30,layer:\'MVT\',label:\'AUX TRANSFORMER\'},\n    substation:    {w:80,h:60,layer:\'ELEC\',label:\'POI SUBSTATION\'},\n    spare_equip:   {w:60,h:40,layer:\'0\',label:\'SPARE EQUIPMENT\'},\n    north_arrow:   {w:40,h:40,layer:\'0\',label:\'N\'},\n    scale_bar:     {w:100,h:15,layer:\'0\',label:"SCALE 1\\"=30\'"},\n    vcb:           {w:15,h:40,layer:\'ELEC\',label:\'VCB\'},\n    busbar_el:     {w:120,h:8,layer:\'ELEC\',label:\'34.5kV BUSBAR\'},\n    pcs_el:        {w:25,h:30,layer:\'ELEC\',label:\'PCS 2800kVA\'},\n    gsu_transformer:{w:30,h:30,layer:\'ELEC\',label:\'GSU 115kV\'},\n  };\n  return map[type]||{w:40,h:40,layer:\'0\',label:type};\n}\n\n// ═══════════════════════════════════════════════════════════════\n// RENDER OBJECTS\n// ═══════════════════════════════════════════════════════════════\nfunction renderObj(o) {\n  // Remove existing SVG element\n  const old = document.getElementById(\'svgo-\'+o.id);\n  if(old) old.parentNode.removeChild(old);\n\n  const layer = getLayer(o.layer);\n  const g = makeSVG(layer,\'g\',{id:\'svgo-\'+o.id,\'data-id\':o.id});\n  g.style.cursor=\'pointer\';\n\n  const c = LAYER_COLORS[o.layer]||\'#333\';\n  const isSelected = selObj && selObj.id === o.id;\n  const selSW = isSelected ? 2.5 : 1;\n  const selStroke = isSelected ? \'#1565c0\' : c;\n\n  switch(o.type) {\n    case \'line\': {\n      const l=makeSVG(g,\'line\',{x1:o.x1,y1:o.y1,x2:o.x2,y2:o.y2,stroke:selStroke,\'stroke-width\':selSW});\n      if(o.layer===\'FENCE\') l.setAttribute(\'stroke-dasharray\',\'6 3\');\n      if(o.layer===\'ROAD\') { l.setAttribute(\'stroke-width\',\'8\'); l.setAttribute(\'stroke\',\'#bcaaa4\'); l.setAttribute(\'opacity\',\'0.8\'); }\n      break;\n    }\n    case \'rect\': {\n      const fill = {SITE:\'none\',BATT:\'#e8f5e9\',MVT:\'#fce4ec\',ROAD:\'#efebe9\',FENCE:\'none\'}[o.layer]||\'none\';\n      const r=makeSVG(g,\'rect\',{x:o.x,y:o.y,width:o.w,height:o.h,fill,stroke:selStroke,\'stroke-width\':selSW});\n      if(o.layer===\'SITE\'){r.setAttribute(\'rx\',\'6\');r.setAttribute(\'stroke-width\',\'2.5\');}\n      if(o.layer===\'FENCE\') r.setAttribute(\'stroke-dasharray\',\'6 3\');\n      if(o.label){const t=makeSVG(g,\'text\',{x:o.x+o.w/2,y:o.y+o.h/2+3,\'text-anchor\':\'middle\',\'font-size\':\'6\',\'font-family\':\'Arial\',fill:c});t.textContent=o.label;}\n      break;\n    }\n    case \'circle\': {\n      makeSVG(g,\'circle\',{cx:o.x,cy:o.y,r:o.r,fill:\'none\',stroke:selStroke,\'stroke-width\':selSW});\n      break;\n    }\n    case \'poly\': {\n      const pl=makeSVG(g,\'polyline\',{points:o.pts.map(p=>p.x+\',\'+p.y).join(\' \'),fill:\'none\',stroke:selStroke,\'stroke-width\':selSW});\n      if(o.layer===\'FENCE\') pl.setAttribute(\'stroke-dasharray\',\'6 3\');\n      if(o.layer===\'ROAD\'){pl.setAttribute(\'stroke-width\',\'8\');pl.setAttribute(\'stroke\',\'#bcaaa4\');}\n      break;\n    }\n    case \'text\': {\n      const t=makeSVG(g,\'text\',{x:o.x,y:o.y,\'font-size\':o.fs||8,\'font-family\':\'Arial\',fill:selStroke});\n      t.textContent=o.text||o.label||\'\';\n      if(isSelected){const bb=t.getBBox?t.getBBox():null;if(bb)makeSVG(g,\'rect\',{x:bb.x-1,y:bb.y-1,width:bb.width+2,height:bb.height+2,fill:\'none\',stroke:\'#1565c0\',\'stroke-width\':\'0.8\',\'stroke-dasharray\':\'3 2\'});}\n      break;\n    }\n    case \'dim\': {\n      const dx=o.x2-o.x1, dy=o.y2-o.y1;\n      const len=Math.sqrt(dx*dx+dy*dy)||1;\n      const off=18;\n      const nx=-dy/len*off, ny=dx/len*off;\n      const dl=makeSVG(g,\'line\',{x1:o.x1+nx,y1:o.y1+ny,x2:o.x2+nx,y2:o.y2+ny,stroke:\'#555\',\'stroke-width\':\'0.8\'});\n      dl.setAttribute(\'marker-start\',\'url(#dim-end)\'); dl.setAttribute(\'marker-end\',\'url(#dim-end)\');\n      makeSVG(g,\'line\',{x1:o.x1,y1:o.y1,x2:o.x1+nx*1.3,y2:o.y1+ny*1.3,stroke:\'#555\',\'stroke-width\':\'0.5\'});\n      makeSVG(g,\'line\',{x1:o.x2,y1:o.y2,x2:o.x2+nx*1.3,y2:o.y2+ny*1.3,stroke:\'#555\',\'stroke-width\':\'0.5\'});\n      const t=makeSVG(g,\'text\',{x:(o.x1+o.x2)/2+nx*1.2,y:(o.y1+o.y2)/2+ny*1.2,\'text-anchor\':\'middle\',\'font-size\':\'7\',\'font-family\':\'Arial\',fill:\'#444\'});\n      t.textContent = Math.round(len/SCALE*10)/10 + "\'";\n      break;\n    }\n    case \'comp\': {\n      renderCompObj(g, o, selStroke, isSelected);\n      break;\n    }\n  }\n\n  g.addEventListener(\'click\', e => { if(tool===\'sel\'){e.stopPropagation();selectObj(o);} });\n}\n\nfunction renderCompObj(g, o, selStroke, isSelected) {\n  const {x,y,w,h,compType:ct,label} = o;\n  const sw = isSelected ? 2 : 1.5;\n\n  switch(ct) {\n    case \'megapack\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#e8f5e9\',stroke:isSelected?\'#1565c0\':\'#2e7d32\',\'stroke-width\':sw});\n      // internal grid lines matching PDF\n      for(let i=1;i<3;i++){makeSVG(g,\'line\',{x1:x+w*i/3,y1:y,x2:x+w*i/3,y2:y+h,stroke:\'#2e7d32\',\'stroke-width\':\'0.7\'});}\n      makeSVG(g,\'line\',{x1:x,y1:y+h/2,x2:x+w,y2:y+h/2,stroke:\'#2e7d32\',\'stroke-width\':\'0.5\'});\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':Math.min(w/8,5),\'font-family\':\'Arial\',fill:\'#1b5e20\'});\n      t.setAttribute(\'font-weight\',\'bold\'); t.textContent=\'MP3\';\n      break;\n    }\n    case \'mv_transformer\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#fce4ec\',stroke:isSelected?\'#1565c0\':\'#c2185b\',\'stroke-width\':sw});\n      makeSVG(g,\'line\',{x1:x,y1:y+h/2,x2:x+w,y2:y+h/2,stroke:\'#c2185b\',\'stroke-width\':\'0.6\'});\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':Math.min(w/4,5),\'font-family\':\'Arial\',fill:\'#880e4f\'});\n      t.textContent=\'MVT\'; break;\n    }\n    case \'site_boundary\': {\n      const r=makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'none\',stroke:isSelected?\'#1565c0\':\'#d32f2f\',\'stroke-width\':\'2.5\'});\n      r.setAttribute(\'rx\',\'8\');\n      const t=makeSVG(g,\'text\',{x:x+6,y:y+12,\'font-size\':\'7\',\'font-family\':\'Arial\',fill:\'#d32f2f\'});\n      t.setAttribute(\'font-weight\',\'bold\'); t.textContent=label||\'(N) SITE BOUNDARY AND FENCE\';\n      break;\n    }\n    case \'access_road\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#d7ccc8\',stroke:\'#795548\',\'stroke-width\':\'1\'});\n      const cl=makeSVG(g,\'line\',{x1:x,y1:y+h/2,x2:x+w,y2:y+h/2,stroke:\'#fff\',\'stroke-width\':\'1\'});\n      cl.setAttribute(\'stroke-dasharray\',\'10 5\');\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+3,\'text-anchor\':\'middle\',\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#4e342e\'});\n      t.textContent=label||\'ACCESS ROAD\'; break;\n    }\n    case \'stormwater\': {\n      makeSVG(g,\'ellipse\',{cx:x+w/2,cy:y+h/2,rx:w/2,ry:h/2,fill:\'#bbdefb\',stroke:\'#1565c0\',\'stroke-width\':\'1.2\'});\n      const wl=makeSVG(g,\'path\',{fill:\'none\',stroke:\'#1565c0\',\'stroke-width\':\'1\'});\n      wl.setAttribute(\'d\',`M${x+5} ${y+h/2}Q${x+w/4} ${y+h/2-6} ${x+w/2} ${y+h/2}Q${x+3*w/4} ${y+h/2+6} ${x+w-5} ${y+h/2}`);\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+h/4,\'text-anchor\':\'middle\',\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#0d47a1\'});\n      t.textContent=label||\'STORM WATER\\nPOND\'; break;\n    }\n    case \'access_gate\': {\n      makeSVG(g,\'line\',{x1:x+w/2,y1:y,x2:x+w/2,y2:y+h/2,stroke:\'#333\',\'stroke-width\':\'2\'});\n      makeSVG(g,\'line\',{x1:x+w/2,y1:y+h/2,x2:x,y2:y+h,stroke:\'#333\',\'stroke-width\':\'2\'});\n      makeSVG(g,\'line\',{x1:x+w/2,y1:y+h/2,x2:x+w,y2:y+h,stroke:\'#333\',\'stroke-width\':\'2\'});\n      makeSVG(g,\'rect\',{x:x+w/2-4,y:y-4,width:8,height:6,fill:\'#333\'}); break;\n    }\n    case \'fire_staging\': {\n      const fr=makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'url(#hatch-fire)\',stroke:\'#b71c1c\',\'stroke-width\':\'1\'});\n      fr.setAttribute(\'stroke-dasharray\',\'5 3\');\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'6\',\'font-family\':\'Arial\',fill:\'#b71c1c\'});\n      t.setAttribute(\'font-weight\',\'bold\'); t.textContent=\'FIRE STAGING\'; break;\n    }\n    case \'site_control\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#fff8e1\',stroke:isSelected?\'#1565c0\':\'#f57f17\',\'stroke-width\':\'1.5\'});\n      makeSVG(g,\'line\',{x1:x+w/2,y1:y,x2:x+w/2,y2:y+h,stroke:\'#f57f17\',\'stroke-width\':\'0.7\'});\n      makeSVG(g,\'line\',{x1:x,y1:y+h/2,x2:x+w,y2:y+h/2,stroke:\'#f57f17\',\'stroke-width\':\'0.7\'});\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2-2,\'text-anchor\':\'middle\',\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#e65100\'});\n      t.setAttribute(\'font-weight\',\'bold\'); t.textContent=\'SITE\';\n      const t2=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+6,\'text-anchor\':\'middle\',\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#e65100\'});\n      t2.setAttribute(\'font-weight\',\'bold\'); t2.textContent=\'CONTROL\'; break;\n    }\n    case \'aux_transformer\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#f3e5f5\',stroke:isSelected?\'#1565c0\':\'#7b1fa2\',\'stroke-width\':\'1.5\'});\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'5\',\'font-family\':\'Arial\',fill:\'#4a148c\'});\n      t.textContent=\'AUX XFMR\'; break;\n    }\n    case \'substation\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#e8eaf6\',stroke:isSelected?\'#1565c0\':\'#283593\',\'stroke-width\':\'1.5\'});\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'6\',\'font-family\':\'Arial\',fill:\'#1a237e\'});\n      t.setAttribute(\'font-weight\',\'bold\'); t.textContent=label||\'SUBSTATION\'; break;\n    }\n    case \'spare_equip\': {\n      const sr=makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'none\',stroke:isSelected?\'#1565c0\':\'#666\',\'stroke-width\':\'1\'});\n      sr.setAttribute(\'stroke-dasharray\',\'5 3\');\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'6\',\'font-family\':\'Arial\',fill:\'#666\'});\n      t.textContent=\'SPARE\'; break;\n    }\n    case \'north_arrow\': {\n      const cx=x+w/2, cy=y+h/2, r=Math.min(w,h)/2-2;\n      makeSVG(g,\'circle\',{cx,cy,r,fill:\'none\',stroke:isSelected?\'#1565c0\':\'#333\',\'stroke-width\':\'1\'});\n      makeSVG(g,\'path\',{d:`M${cx} ${cy-r+1} L${cx-r*0.4} ${cy+r*0.4} L${cx} ${cy} Z`,fill:\'#333\'});\n      makeSVG(g,\'path\',{d:`M${cx} ${cy-r+1} L${cx+r*0.4} ${cy+r*0.4} L${cx} ${cy} Z`,fill:\'none\',stroke:\'#333\',\'stroke-width\':\'1\'});\n      const t=makeSVG(g,\'text\',{x:cx,y:cy+r+8,\'text-anchor\':\'middle\',\'font-size\':\'8\',\'font-family\':\'Arial\',fill:\'#333\'});\n      t.setAttribute(\'font-weight\',\'bold\'); t.textContent=\'N\'; break;\n    }\n    case \'scale_bar\': {\n      makeSVG(g,\'rect\',{x,y:y+4,width:w,height:7,fill:\'none\',stroke:\'#333\',\'stroke-width\':\'1\'});\n      [0,.25,.5,.75,1].forEach((f,i) => {\n        if(i%2===0) makeSVG(g,\'rect\',{x:x+w*f,y:y+4,width:w*0.25,height:7,fill:\'#333\'});\n      });\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+2,\'text-anchor\':\'middle\',\'font-size\':\'6\',\'font-family\':\'Arial\',fill:\'#333\'});\n      t.textContent="SCALE 1\\"=30\'  0──150 FT"; break;\n    }\n    case \'vcb\': {\n      makeSVG(g,\'line\',{x1:x+w/2,y1:y,x2:x+w/2,y2:y+h*0.3,stroke:isSelected?\'#1565c0\':\'#b71c1c\',\'stroke-width\':\'1.5\'});\n      makeSVG(g,\'rect\',{x:x,y:y+h*0.3,width:w,height:h*0.4,fill:\'#ffebee\',stroke:isSelected?\'#1565c0\':\'#b71c1c\',\'stroke-width\':\'1.2\'});\n      makeSVG(g,\'line\',{x1:x+w/2,y1:y+h*0.7,x2:x+w/2,y2:y+h,stroke:isSelected?\'#1565c0\':\'#b71c1c\',\'stroke-width\':\'1.5\'}).setAttribute(\'stroke-dasharray\',\'3 2\');\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h*0.52,\'text-anchor\':\'middle\',\'font-size\':\'4\',\'font-family\':\'Arial\',fill:\'#b71c1c\'});\n      t.textContent=\'VCB\'; break;\n    }\n    case \'busbar_el\': {\n      makeSVG(g,\'rect\',{x,y:y+1,width:w,height:h-2,fill:\'#616161\',stroke:isSelected?\'#1565c0\':\'#212121\',\'stroke-width\':\'1\'});\n      for(let i=1;i<4;i++){\n        makeSVG(g,\'line\',{x1:x+w*i/4,y1:y-6,x2:x+w*i/4,y2:y+1,stroke:\'#333\',\'stroke-width\':\'1.5\'});\n      }\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'4.5\',\'font-family\':\'Arial\',fill:\'#fff\'});\n      t.textContent=\'34.5kV BUS\'; break;\n    }\n    case \'pcs_el\': {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'#fff9c4\',stroke:isSelected?\'#1565c0\':\'#f9a825\',\'stroke-width\':\'1.5\'});\n      makeSVG(g,\'path\',{d:`M${x+4} ${y+h*0.65}L${x+w*0.45} ${y+h*0.2}L${x+w*0.45} ${y+h*0.45}L${x+w*0.65} ${y+h*0.45}L${x+w*0.65} ${y+h*0.75}L${x+w*0.45} ${y+h*0.75}L${x+w*0.45} ${y+h*0.95}Z`,fill:\'none\',stroke:\'#f57f17\',\'stroke-width\':\'0.8\'});\n      const t=makeSVG(g,\'text\',{x:x+w-4,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'4.5\',\'font-family\':\'Arial\',fill:\'#e65100\'});\n      t.textContent=\'PCS\'; break;\n    }\n    case \'gsu_transformer\': {\n      makeSVG(g,\'circle\',{cx:x+w*0.38,cy:y+h/2,r:w*0.3,fill:\'none\',stroke:isSelected?\'#1565c0\':\'#5c35a5\',\'stroke-width\':\'1.5\'});\n      makeSVG(g,\'circle\',{cx:x+w*0.62,cy:y+h/2,r:w*0.3,fill:\'none\',stroke:isSelected?\'#1565c0\':\'#5c35a5\',\'stroke-width\':\'1.5\'});\n      makeSVG(g,\'line\',{x1:x,y1:y+h/2,x2:x+w*0.08,y2:y+h/2,stroke:\'#5c35a5\',\'stroke-width\':\'1.5\'});\n      makeSVG(g,\'line\',{x1:x+w*0.92,y1:y+h/2,x2:x+w,y2:y+h/2,stroke:\'#5c35a5\',\'stroke-width\':\'1.5\'}); break;\n    }\n    default: {\n      makeSVG(g,\'rect\',{x,y,width:w,height:h,fill:\'none\',stroke:isSelected?\'#1565c0\':\'#333\',\'stroke-width\':\'1.5\'});\n      const t=makeSVG(g,\'text\',{x:x+w/2,y:y+h/2+2,\'text-anchor\':\'middle\',\'font-size\':\'6\',\'font-family\':\'Arial\',fill:\'#333\'});\n      t.textContent=label||ct; break;\n    }\n  }\n}\n\n// ═══════════════════════════════════════════════════════════════\n// DROP FROM PANEL\n// ═══════════════════════════════════════════════════════════════\nfunction onDrop(e) {\n  e.preventDefault();\n  if(!dragType) return;\n  const {x,y} = getSVGCoords(e);\n  if(x>=DRAW_W) return;\n  const type = dragType.type;\n  const w = parseFloat(dragType.w)||60;\n  const h = parseFloat(dragType.h)||40;\n  addComponent(type, snapOn?Math.round((x-w/2)/SNAP_GRID)*SNAP_GRID:x-w/2,\n                     snapOn?Math.round((y-h/2)/SNAP_GRID)*SNAP_GRID:y-h/2, w, h);\n  dragType=null;\n}\n\n// ═══════════════════════════════════════════════════════════════\n// SELECTION & PROPERTIES\n// ═══════════════════════════════════════════════════════════════\nfunction hitTest(x,y) {\n  for(let i=objs.length-1;i>=0;i--) {\n    const o=objs[i];\n    if(o.type===\'comp\'||o.type===\'rect\') {\n      if(x>=o.x&&x<=o.x+o.w&&y>=o.y&&y<=o.y+o.h) return o;\n    }\n    if(o.type===\'text\'&&Math.abs(x-o.x)<50&&Math.abs(y-o.y)<10) return o;\n  }\n  return null;\n}\n\nfunction selectObj(o) {\n  const prev = selObj;\n  selObj = o;\n  if(prev) renderObj(prev);\n  if(o) { renderObj(o); showProp(o); } else hideProp();\n}\n\nfunction showProp(o) {\n  document.getElementById(\'pp-label\').value = o.label||o.text||\'\';\n  document.getElementById(\'pp-layer\').value = o.layer||\'0\';\n  document.getElementById(\'pp-rot\').value = o.rot||0;\n  document.getElementById(\'pp-w\').value = o.w||Math.round(Math.abs((o.x2||0)-(o.x1||0)))||\'\';\n  document.getElementById(\'pp-h\').value = o.h||Math.round(Math.abs((o.y2||0)-(o.y1||0)))||\'\';\n  document.getElementById(\'prop-panel\').classList.add(\'show\');\n}\nfunction hideProp() { document.getElementById(\'prop-panel\').classList.remove(\'show\'); }\n\nfunction updateProp(key,val) {\n  if(!selObj) return;\n  if(key===\'label\') { selObj.label=val; if(selObj.type===\'text\') selObj.text=val; }\n  if(key===\'layer\') { selObj.layer=val; }\n  if(key===\'rot\') { selObj.rot=parseFloat(val)||0; }\n  renderObj(selObj);\n}\nfunction updatePropSize(key,val) {\n  if(!selObj) return;\n  const v=parseFloat(val)||1;\n  if(key===\'w\') selObj.w=v; if(key===\'h\') selObj.h=v;\n  renderObj(selObj);\n}\n\nfunction deleteSelected() {\n  if(!selObj) return;\n  saveUndo();\n  const el=document.getElementById(\'svgo-\'+selObj.id);\n  if(el) el.parentNode.removeChild(el);\n  objs=objs.filter(o=>o.id!==selObj.id);\n  selObj=null; hideProp(); updateSB();\n}\n\n// ═══════════════════════════════════════════════════════════════\n// ZOOM\n// ═══════════════════════════════════════════════════════════════\nfunction setZoom(z) {\n  zoomLevel = Math.min(4, Math.max(0.2, z));\n  const paper = document.getElementById(\'paper\');\n  paper.style.transform = `scale(${zoomLevel})`;\n  paper.style.transformOrigin = \'top left\';\n  paper.style.margin = `0 0 ${PAPER_H*(zoomLevel-1)}px ${PAPER_W*(zoomLevel-1)}px`;\n  document.getElementById(\'sb-zoom\').textContent = \'Zoom: \'+Math.round(zoomLevel*100)+\'%\';\n}\nfunction zoomIn()  { setZoom(zoomLevel*1.2); }\nfunction zoomOut() { setZoom(zoomLevel/1.2); }\nfunction zoomFit() {\n  const wrap = document.getElementById(\'canvas-wrap\');\n  const z = Math.min((wrap.clientWidth-20)/PAPER_W, (wrap.clientHeight-20)/PAPER_H);\n  setZoom(z);\n  document.getElementById(\'canvas-scroll\').scrollTo(0,0);\n}\n\nfunction toggleGrid() {\n  const g = document.getElementById(\'g-grid\');\n  g.style.display = gridVis ? \'block\' : \'none\';\n}\n\n// ═══════════════════════════════════════════════════════════════\n// UNDO\n// ═══════════════════════════════════════════════════════════════\nfunction saveUndo() {\n  undoStack.push(JSON.parse(JSON.stringify(objs)));\n  if(undoStack.length>30) undoStack.shift();\n}\nfunction doUndo() {\n  if(!undoStack.length) return;\n  objs = undoStack.pop();\n  // re-render all\n  [\'0\',\'SITE\',\'BATT\',\'MVT\',\'ROAD\',\'FENCE\',\'ELEC\',\'TEXT\',\'DIM\'].forEach(l => {\n    const g=document.getElementById(\'g-\'+l); if(g) g.innerHTML=\'\';\n  });\n  objs.forEach(renderObj);\n  selObj=null; hideProp(); updateSB();\n}\n\n// ═══════════════════════════════════════════════════════════════\n// CLEAR\n// ═══════════════════════════════════════════════════════════════\nfunction clearDwg() {\n  if(!confirm(\'Clear all drawing objects? Title block will remain.\')) return;\n  saveUndo();\n  objs=[];\n  [\'0\',\'SITE\',\'BATT\',\'MVT\',\'ROAD\',\'FENCE\',\'ELEC\',\'TEXT\',\'DIM\'].forEach(l => {\n    const g=document.getElementById(\'g-\'+l); if(g) g.innerHTML=\'\';\n  });\n  selObj=null; hideProp(); updateSB();\n}\n\n// ═══════════════════════════════════════════════════════════════\n// STATUS BAR\n// ═══════════════════════════════════════════════════════════════\nfunction updateSB() {\n  document.getElementById(\'sb-objs\').textContent = \'Objects: \'+objs.length;\n  document.getElementById(\'sb-layer\').textContent = \'Layer: \'+(currentLayer||\'0\');\n  document.getElementById(\'sb-snap\').textContent = \'Snap: \'+(snapOn?\'ON\':\'OFF\');\n}\n\n// ═══════════════════════════════════════════════════════════════\n// KEYBOARD\n// ═══════════════════════════════════════════════════════════════\nfunction onKey(e) {\n  if([\'INPUT\',\'TEXTAREA\',\'SELECT\'].includes(e.target.tagName)) return;\n  if(e.key===\'v\'||e.key===\'V\') setTool(\'sel\');\n  if(e.key===\'l\'||e.key===\'L\') setTool(\'line\');\n  if(e.key===\'r\'||e.key===\'R\') setTool(\'rect\');\n  if(e.key===\'p\'||e.key===\'P\') setTool(\'poly\');\n  if(e.key===\'c\'||e.key===\'C\') setTool(\'circle\');\n  if(e.key===\'t\'||e.key===\'T\') setTool(\'text\');\n  if(e.key===\'d\'||e.key===\'D\') setTool(\'dim\');\n  if(e.key===\'f\'||e.key===\'F\') zoomFit();\n  if(e.key===\'s\'||e.key===\'S\') { snapOn=!snapOn; document.getElementById(\'bt-snap\').classList.toggle(\'on\',snapOn); updateSB(); }\n  if(e.key===\'g\'||e.key===\'G\') { gridVis=!gridVis; toggleGrid(); }\n  if(e.key===\'Escape\') { setTool(\'sel\'); drawing=false; polyPts=[]; clearTemp(); }\n  if(e.key===\'Delete\'||e.key===\'Backspace\') deleteSelected();\n  if(e.key===\'Enter\' && tool===\'poly\') commitPoly();\n  if((e.ctrlKey||e.metaKey)&&e.key===\'z\') { e.preventDefault(); doUndo(); }\n  if((e.ctrlKey||e.metaKey)&&e.key===\'+\') { e.preventDefault(); zoomIn(); }\n  if((e.ctrlKey||e.metaKey)&&e.key===\'-\') { e.preventDefault(); zoomOut(); }\n}\n\n// ═══════════════════════════════════════════════════════════════\n// EXPORT: SVG\n// ═══════════════════════════════════════════════════════════════\nfunction exportSVG() {\n  const svg = document.getElementById(\'draw-svg\');\n  const clone = svg.cloneNode(true);\n  clone.setAttribute(\'xmlns\',\'http://www.w3.org/2000/svg\');\n  // embed font\n  const style = document.createElementNS(\'http://www.w3.org/2000/svg\',\'style\');\n  style.textContent = "@import url(\'https://fonts.googleapis.com/css2?family=Arial+Narrow&display=swap\');";\n  clone.insertBefore(style, clone.firstChild);\n  const blob = new Blob([new XMLSerializer().serializeToString(clone)],{type:\'image/svg+xml\'});\n  dl(URL.createObjectURL(blob), \'BESS_Design.svg\');\n}\n\n// ═══════════════════════════════════════════════════════════════\n// EXPORT: DXF (AutoCAD compatible)\n// ═══════════════════════════════════════════════════════════════\nfunction buildDXF() {\n  let d = \'\';\n  d += \'0\\nSECTION\\n2\\nHEADER\\n\';\n  d += \'9\\n$ACADVER\\n1\\nAC1021\\n\';\n  d += \'9\\n$INSUNITS\\n70\\n1\\n\'; // inches\n  d += \'0\\nENDSEC\\n\';\n\n  // TABLES section with layers\n  d += \'0\\nSECTION\\n2\\nTABLES\\n\';\n  d += \'0\\nTABLE\\n2\\nLAYER\\n70\\n20\\n\';\n  const layerDefs = {\n    \'0\':\'7\',\'SITE\':\'1\',\'BATT\':\'3\',\'MVT\':\'6\',\'ROAD\':\'40\',\'FENCE\':\'7\',\'ELEC\':\'5\',\'TEXT\':\'7\',\'DIM\':\'8\'\n  };\n  for(const [name,color] of Object.entries(layerDefs)) {\n    d += `0\\nLAYER\\n2\\n${name}\\n70\\n0\\n62\\n${color}\\n6\\nCONTINUOUS\\n`;\n  }\n  d += \'0\\nENDTAB\\n0\\nENDSEC\\n\';\n\n  // ENTITIES\n  d += \'0\\nSECTION\\n2\\nENTITIES\\n\';\n  const S = SCALE;\n\n  objs.forEach(o => {\n    const lay = o.layer||\'0\';\n    if(o.type===\'line\') {\n      d += `0\\nLINE\\n8\\n${lay}\\n10\\n${o.x1/S}\\n20\\n${-o.y1/S}\\n30\\n0\\n11\\n${o.x2/S}\\n21\\n${-o.y2/S}\\n31\\n0\\n`;\n    }\n    else if(o.type===\'rect\'||o.type===\'comp\') {\n      const x=o.x/S, y=-o.y/S, w=o.w/S, h=o.h/S;\n      d += `0\\nLWPOLYLINE\\n8\\n${lay}\\n90\\n4\\n70\\n1\\n`;\n      d += `10\\n${x}\\n20\\n${y}\\n10\\n${x+w}\\n20\\n${y}\\n10\\n${x+w}\\n20\\n${y-h}\\n10\\n${x}\\n20\\n${y-h}\\n`;\n      if(o.label){d += `0\\nTEXT\\n8\\n${lay}\\n10\\n${x+w/2}\\n20\\n${y-h/2}\\n30\\n0\\n40\\n0.15\\n1\\n${o.label}\\n72\\n1\\n`;}\n    }\n    else if(o.type===\'poly\') {\n      d += `0\\nPOLYLINE\\n8\\n${lay}\\n66\\n1\\n`;\n      o.pts.forEach(pt => { d += `0\\nVERTEX\\n8\\n${lay}\\n10\\n${pt.x/S}\\n20\\n${-pt.y/S}\\n30\\n0\\n`; });\n      d += \'0\\nSEQLEND\\n\';\n    }\n    else if(o.type===\'circle\') {\n      d += `0\\nCIRCLE\\n8\\n${lay}\\n10\\n${o.x/S}\\n20\\n${-o.y/S}\\n30\\n0\\n40\\n${o.r/S}\\n`;\n    }\n    else if(o.type===\'text\') {\n      d += `0\\nTEXT\\n8\\nTEXT\\n10\\n${o.x/S}\\n20\\n${-o.y/S}\\n30\\n0\\n40\\n${(o.fs||8)/S*0.8}\\n1\\n${o.text||\'\'}\\n`;\n    }\n    else if(o.type===\'dim\') {\n      const dx=o.x2-o.x1, dy=o.y2-o.y1, len=Math.sqrt(dx*dx+dy*dy)||1;\n      const nx=-dy/len, ny=dx/len, off=0.6;\n      d += `0\\nDIMENSION\\n8\\nDIM\\n`;\n      d += `10\\n${(o.x1+o.x2)/2/S+nx*off}\\n20\\n${-(o.y1+o.y2)/2/S+ny*off}\\n30\\n0\\n`;\n      d += `13\\n${o.x1/S}\\n23\\n${-o.y1/S}\\n33\\n0\\n`;\n      d += `14\\n${o.x2/S}\\n24\\n${-o.y2/S}\\n34\\n0\\n`;\n      d += `70\\n1\\n`;\n    }\n  });\n\n  // Title block as text entities\n  d += `0\\nTEXT\\n8\\nTEXT\\n10\\n${(DRAW_W+TB_W/2)/S}\\n20\\n${-PAPER_H*0.4/S}\\n30\\n0\\n40\\n0.4\\n1\\n${TB.projectName.replace(\'\\n\',\' \')}\\n72\\n1\\n`;\n  d += `0\\nTEXT\\n8\\nTEXT\\n10\\n${(DRAW_W+TB_W/2)/S}\\n20\\n${-PAPER_H*0.85/S}\\n30\\n0\\n40\\n0.7\\n1\\n${TB.sheetNum}\\n72\\n1\\n`;\n\n  d += \'0\\nENDSEC\\n0\\nEOF\\n\';\n  return d;\n}\n\nfunction exportDXF() {\n  const blob = new Blob([buildDXF()],{type:\'application/dxf\'});\n  dl(URL.createObjectURL(blob), \'BESS_Design.dxf\');\n}\n\nfunction exportDWG() {\n  // DWG binary format requires Autodesk SDK — we export R2007 DXF which AutoCAD opens as DWG\n  const dxf = buildDXF();\n  const blob = new Blob([dxf],{type:\'application/acad\'});\n  dl(URL.createObjectURL(blob), \'BESS_Design_AutoCAD.dxf\');\n  // Inform user\n  setTimeout(()=>alert(\'DWG exported as DXF (AutoCAD R2007 format).\\nOpen in AutoCAD: File > Open > select the .dxf file.\\nAutoCAD will convert it to DWG on save.\'),100);\n}\n\n// ═══════════════════════════════════════════════════════════════\n// EXPORT: PDF (print with engineering layout)\n// ═══════════════════════════════════════════════════════════════\nfunction exportPDF() {\n  // inject print styles\n  const style = document.createElement(\'style\');\n  style.id = \'print-inject\';\n  style.textContent = `\n    @media print {\n      @page { size: 17in 11in landscape; margin: 0.1in; }\n      body { background: white !important; }\n      #toolbar, #panel, #statusbar, #prop-panel { display: none !important; }\n      #main { display: block !important; height: auto !important; }\n      #canvas-wrap { overflow: visible !important; width: 100% !important; height: auto !important; }\n      #canvas-scroll { overflow: visible !important; width: 100% !important; height: auto !important; }\n      #paper { transform: none !important; margin: 0 !important; box-shadow: none !important;\n               width: 100% !important; height: auto !important; }\n      #draw-svg { position: static !important; width: 100% !important; height: auto !important; }\n    }`;\n  document.head.appendChild(style);\n  window.print();\n  setTimeout(()=>{ const s=document.getElementById(\'print-inject\'); if(s) s.remove(); }, 2000);\n}\n\nfunction dl(url, name) {\n  const a=document.createElement(\'a\'); a.href=url; a.download=name; a.click();\n  setTimeout(()=>URL.revokeObjectURL(url),5000);\n}\n\n// ═══════════════════════════════════════════════════════════════\n// SAMPLE LAYOUT (matching PDF S-03 style)\n// ═══════════════════════════════════════════════════════════════\nfunction loadSampleLayout() {\n  // Site boundary (large rounded rect)\n  const sb={id:newId(),type:\'comp\',compType:\'site_boundary\',x:30,y:20,w:790,h:540,layer:\'SITE\',label:\'(N) SITE BOUNDARY AND FENCE\',rot:0};\n  objs.push(sb); renderObj(sb);\n\n  // Staging/spare area (left)\n  const staging={id:newId(),type:\'comp\',compType:\'fire_staging\',x:40,y:300,w:100,h:120,layer:\'0\',label:\'CONSTRUCTION\\nLAYDOWN/\\nO&M PARKING/\\nFIRE STAGING\',rot:0};\n  objs.push(staging); renderObj(staging);\n\n  // Site control center\n  const scc={id:newId(),type:\'comp\',compType:\'site_control\',x:145,y:300,w:50,h:45,layer:\'0\',label:\'SITE CONTROL\\nCENTER\',rot:0};\n  objs.push(scc); renderObj(scc);\n\n  // Aux transformer\n  const axt={id:newId(),type:\'comp\',compType:\'aux_transformer\',x:145,y:360,w:35,h:35,layer:\'MVT\',label:\'AUX XFMR\',rot:0};\n  objs.push(axt); renderObj(axt);\n\n  // Access road (horizontal)\n  const road1={id:newId(),type:\'comp\',compType:\'access_road\',x:30,y:250,w:800,h:25,layer:\'ROAD\',label:\'(N) ACCESS ROAD FOR BATTERIES\',rot:0};\n  objs.push(road1); renderObj(road1);\n\n  // Access gate (bottom)\n  const gate1={id:newId(),type:\'comp\',compType:\'access_gate\',x:380,y:540,w:25,h:25,layer:\'0\',label:\'(N) ACCESS GATE (TYP.)\',rot:0};\n  objs.push(gate1); renderObj(gate1);\n\n  // Access gate (top)\n  const gate2={id:newId(),type:\'comp\',compType:\'access_gate\',x:380,y:20,w:25,h:25,layer:\'0\',label:\'\',rot:0};\n  objs.push(gate2); renderObj(gate2);\n\n  // Battery containers - 4 rows × 13 columns = 52 pairs (104 total)\n  const bStartX=220, bStartY=60, bW=42, bH=18, bGapX=8, bGapY=10, rows=4, cols=13;\n  for(let row=0;row<rows;row++) {\n    for(let col=0;col<cols;col++) {\n      const bx = bStartX + col*(bW+bGapX);\n      const by = bStartY + row*(bH*2+bGapY+12);\n      // pair of megapacks\n      const b1={id:newId(),type:\'comp\',compType:\'megapack\',x:bx,y:by,w:bW,h:bH,layer:\'BATT\',label:\'\',rot:0};\n      const b2={id:newId(),type:\'comp\',compType:\'megapack\',x:bx,y:by+bH+4,w:bW,h:bH,layer:\'BATT\',label:\'\',rot:0};\n      objs.push(b1,b2); renderObj(b1); renderObj(b2);\n      // MV transformer next to each pair\n      const mvt={id:newId(),type:\'comp\',compType:\'mv_transformer\',x:bx+bW+3,y:by+bH/2,w:16,h:bH*2+4,layer:\'MVT\',label:\'\',rot:0};\n      objs.push(mvt); renderObj(mvt);\n    }\n  }\n\n  // Dimension lines\n  const dim1={id:newId(),type:\'dim\',x1:220,y1:560,x2:810,y2:560,layer:\'DIM\',label:\'\'};\n  objs.push(dim1); renderObj(dim1);\n  const dim2={id:newId(),type:\'dim\',x1:815,y1:20,x2:815,y2:225,layer:\'DIM\',label:\'\'};\n  objs.push(dim2); renderObj(dim2);\n\n  // Labels\n  const labels = [\n    {x:550,y:50,text:\'(N) 104 TESLA MEGABLOCK BATTERIES\',fs:7},\n    {x:700,y:70,text:\'(N) 52 MV TRANSFORMERS\',fs:7},\n    {x:170,y:295,text:\'(N) ON SITE MAINTENANCE\',fs:6},\n    {x:170,y:305,text:\'INFRASTRUCTURE\',fs:6},\n  ];\n  labels.forEach(l => {\n    const o={id:newId(),type:\'text\',x:l.x,y:l.y,text:l.text,fs:l.fs||7,layer:\'TEXT\',label:l.text};\n    objs.push(o); renderObj(o);\n  });\n\n  // North arrow\n  const na={id:newId(),type:\'comp\',compType:\'north_arrow\',x:DRAW_W-60,y:15,w:40,h:40,layer:\'0\',label:\'N\',rot:0};\n  objs.push(na); renderObj(na);\n\n  // Scale bar\n  const sc={id:newId(),type:\'comp\',compType:\'scale_bar\',x:200,y:600,w:120,h:14,layer:\'0\',label:"SCALE 1\\"=30\'",rot:0};\n  objs.push(sc); renderObj(sc);\n\n  // Scale label\n  const scLabel={id:newId(),type:\'text\',x:240,y:620,text:"1  BESS SITE PLAN    SCALE: 1\\"=30\'",fs:7,layer:\'TEXT\',label:\'\'};\n  objs.push(scLabel); renderObj(scLabel);\n\n  updateSB();\n}\n\n// ═══════════════════════════════════════════════════════════════\n// START\n// ═══════════════════════════════════════════════════════════════\nwindow.addEventListener(\'load\', () => { init(); setTimeout(zoomFit, 100); });\n</script>\n</body>\n</html>\n'


CAD_HTML=r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BESS Site Plan Designer</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<style>
/* ═══════════════ RESET & BASE ═══════════════ */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Courier New',monospace;background:#1c1e24;color:#c8cbd4;height:100vh;overflow:hidden;display:flex;flex-direction:column;font-size:12px}

/* ═══════════════ TOPBAR ═══════════════ */
#topbar{height:36px;background:#12141a;border-bottom:1px solid #2a2d35;display:flex;align-items:center;gap:0;flex-shrink:0;user-select:none;padding:0 6px;gap:3px}
.btn{height:24px;padding:0 9px;border-radius:3px;font-size:10px;font-weight:700;cursor:pointer;color:#8a8f9e;background:transparent;border:1px solid #2a2d35;font-family:'Courier New',monospace;transition:all .12s;white-space:nowrap;letter-spacing:.04em}
.btn:hover{background:#22252e;color:#c8cbd4;border-color:#3a3d48}
.btn.on{background:rgba(0,160,255,.15);color:#00a0ff;border-color:rgba(0,160,255,.4)}
.btn.svg-btn{color:#44cc88;border-color:rgba(68,204,136,.35)}
.btn.svg-btn:hover{background:rgba(68,204,136,.1)}
.btn.dxf-btn{color:#ffaa33;border-color:rgba(255,170,51,.35)}
.btn.dxf-btn:hover{background:rgba(255,170,51,.1)}
.btn.pdf-btn{color:#ff5566;border-color:rgba(255,85,102,.35)}
.btn.pdf-btn:hover{background:rgba(255,85,102,.1)}
.btn.clr-btn{color:#ff4455;border-color:rgba(255,68,85,.35)}
.vsep{width:1px;height:20px;background:#2a2d35;margin:0 3px;flex-shrink:0}
#coord{font-family:'Courier New',monospace;font-size:10px;color:#556070;margin-left:auto;padding-right:4px;min-width:180px;text-align:right}

/* ═══════════════ BODY LAYOUT ═══════════════ */
#body{display:flex;flex:1;overflow:hidden;min-height:0}

/* ═══════════════ LEFT SIDEBAR ═══════════════ */
#sidebar{width:148px;flex-shrink:0;background:#14161c;border-right:1px solid #2a2d35;overflow-y:auto;overflow-x:hidden}
#sidebar::-webkit-scrollbar{width:4px}
#sidebar::-webkit-scrollbar-thumb{background:#2a2d35;border-radius:2px}
.cat{font-size:8.5px;font-weight:700;color:#e8a020;text-transform:uppercase;letter-spacing:.1em;padding:7px 8px 4px;border-top:1px solid #2a2d35;margin-top:2px}
.cat:first-child{border-top:none;margin-top:0}
.items{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:0 6px 6px}
.item{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 4px 5px;border:1px solid #2a2d35;border-radius:4px;cursor:pointer;background:#1c1e26;transition:all .12s;user-select:none}
.item:hover{border-color:#e8a020;background:#22252f}
.item.active{border-color:#e8a020;background:rgba(232,160,32,.1)}
.item svg{width:44px;height:32px;display:block}
.item span{font-size:8px;color:#8a8f9e;text-align:center;line-height:1.25;max-width:60px}

/* ═══════════════ CANVAS AREA ═══════════════ */
#canvas-area{flex:1;overflow:hidden;position:relative;background:#2a2d35;cursor:default}
#canvas-scroll{width:100%;height:100%;overflow:auto;position:relative}
#canvas-scroll::-webkit-scrollbar{width:10px;height:10px}
#canvas-scroll::-webkit-scrollbar-track{background:#1c1e24}
#canvas-scroll::-webkit-scrollbar-thumb{background:#3a3d48;border-radius:4px}
#canvas-wrap{display:inline-block;position:relative;transform-origin:top left}
#main-svg{display:block;cursor:crosshair}
#main-svg.sel{cursor:default}
#main-svg.pan{cursor:grab}

/* ═══════════════ RIGHT PANEL ═══════════════ */
#right{width:210px;flex-shrink:0;background:#14161c;border-left:1px solid #2a2d35;overflow-y:auto;display:flex;flex-direction:column}
#right::-webkit-scrollbar{width:4px}
#right::-webkit-scrollbar-thumb{background:#2a2d35}
.rp-blk{border-bottom:1px solid #2a2d35;padding:8px 10px}
.rp-hd{font-size:8.5px;font-weight:700;color:#e8a020;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px}
.rp-row{margin-bottom:5px}
.rp-lbl{font-size:8px;color:#556070;display:block;margin-bottom:2px}
.rp-in{width:100%;padding:3px 6px;background:#1c1e26;border:1px solid #2a2d35;border-radius:3px;color:#c8cbd4;font-size:10px;font-family:'Courier New',monospace;outline:none}
.rp-in:focus{border-color:#e8a020}
select.rp-in{cursor:pointer}
.rev-grid{display:grid;grid-template-columns:20px 1fr 28px 56px;gap:2px;margin-bottom:3px}
.rev-hdr{font-size:7.5px;color:#556070;text-align:center}
.rev-in{padding:2px 4px;background:#1c1e26;border:1px solid #2a2d35;border-radius:2px;color:#c8cbd4;font-size:8.5px;font-family:'Courier New',monospace;outline:none;width:100%}
.rev-in:focus{border-color:#e8a020}
.rev-ltr{font-size:9px;color:#e8a020;text-align:center;padding-top:3px;font-weight:700}

/* ═══════════════ STATUSBAR ═══════════════ */
#statusbar{height:20px;background:#0e1014;border-top:1px solid #2a2d35;display:flex;align-items:center;gap:0;padding:0 10px;flex-shrink:0;font-size:9px;color:#556070;font-family:'Courier New',monospace}
#statusbar span{margin-right:14px}
#statusbar b{color:#c8cbd4}
</style>
</head>
<body>

<!-- TOPBAR -->
<div id="topbar">
  <button class="btn on" id="b-sel"    onclick="setTool('sel')">▲ Select</button>
  <button class="btn"    id="b-line"   onclick="setTool('line')">/ Line</button>
  <button class="btn"    id="b-rect"   onclick="setTool('rect')">□ Rect</button>
  <button class="btn"    id="b-poly"   onclick="setTool('poly')">⬡ Poly</button>
  <button class="btn"    id="b-circle" onclick="setTool('circle')">○ Circle</button>
  <button class="btn"    id="b-text"   onclick="setTool('text')">T Text</button>
  <button class="btn"    id="b-dim"    onclick="setTool('dim')">↔ Dim</button>
  <div class="vsep"></div>
  <button class="btn" id="b-snap" onclick="toggleSnap()">Snap ON</button>
  <button class="btn" id="b-grid" onclick="toggleGrid()">Grid ON</button>
  <button class="btn" onclick="zoomFit()">⊡ Fit</button>
  <button class="btn" onclick="zoomStep(1.2)">+</button>
  <button class="btn" onclick="zoomStep(0.83)">−</button>
  <div class="vsep"></div>
  <button class="btn" onclick="doUndo()">↩ Undo</button>
  <button class="btn" onclick="doRedo()">↪ Redo</button>
  <button class="btn" onclick="delSel()">✕ Del</button>
  <div class="vsep"></div>
  <button class="btn svg-btn" onclick="exportSVG()">↓ SVG</button>
  <button class="btn dxf-btn" onclick="exportDXF()">↓ DXF</button>
  <button class="btn pdf-btn" onclick="exportPDF()">↓ PDF</button>
  <button class="btn clr-btn" onclick="clearAll()">⊘ Clear</button>
  <div id="coord">X: 0.0m   Y: 0.0m   Scale: 1"=30'</div>
</div>

<!-- BODY -->
<div id="body">

<!-- LEFT SIDEBAR -->
<div id="sidebar">

  <div class="cat">Site Civil</div>
  <div class="items">
    <div class="item active" id="p-site_boundary" onclick="pickLayer('site_boundary','poly')">
      <svg viewBox="0 0 44 32"><rect x="3" y="4" width="38" height="24" fill="none" stroke="#ff3333" stroke-width="2.5"/></svg>
      <span>Site Boundary</span>
    </div>
    <div class="item" id="p-fence" onclick="pickLayer('fence','line')">
      <svg viewBox="0 0 44 32"><line x1="2" y1="16" x2="42" y2="16" stroke="#444" stroke-width="1.5" stroke-dasharray="5,3"/><line x1="9" y1="8" x2="9" y2="24" stroke="#444" stroke-width="1.2"/><line x1="22" y1="8" x2="22" y2="24" stroke="#444" stroke-width="1.2"/><line x1="35" y1="8" x2="35" y2="24" stroke="#444" stroke-width="1.2"/></svg>
      <span>Fence</span>
    </div>
    <div class="item" id="p-vegetation" onclick="pickLayer('vegetation','poly')">
      <svg viewBox="0 0 44 32"><rect x="2" y="3" width="40" height="26" fill="#88cc44" opacity=".55"/><path d="M2 26 Q11 14 22 26 Q33 14 42 26" fill="none" stroke="#558822" stroke-width="1.2"/><path d="M2 20 Q11 10 22 20 Q33 10 42 20" fill="none" stroke="#558822" stroke-width="0.8" opacity=".5"/></svg>
      <span>Vegetation</span>
    </div>
    <div class="item" id="p-wetlands" onclick="pickLayer('wetlands','poly')">
      <svg viewBox="0 0 44 32"><rect x="2" y="3" width="40" height="26" fill="#4499cc" opacity=".45"/><line x1="2" y1="10" x2="42" y2="10" stroke="#2266aa" stroke-width=".8"/><line x1="2" y1="17" x2="42" y2="17" stroke="#2266aa" stroke-width=".8"/><line x1="2" y1="24" x2="42" y2="24" stroke="#2266aa" stroke-width=".8"/></svg>
      <span>Wetlands</span>
    </div>
    <div class="item" id="p-access_road" onclick="pickLayer('access_road','poly')">
      <svg viewBox="0 0 44 32"><rect x="2" y="10" width="40" height="12" fill="#aa9966" opacity=".85"/><line x1="2" y1="16" x2="42" y2="16" stroke="#887744" stroke-width=".5" stroke-dasharray="6,3"/></svg>
      <span>Access Road</span>
    </div>
    <div class="item" id="p-pond" onclick="pickLayer('pond','poly')">
      <svg viewBox="0 0 44 32"><ellipse cx="22" cy="16" rx="18" ry="12" fill="#2266aa" opacity=".7"/><ellipse cx="22" cy="16" rx="10" ry="7" fill="#3388cc" opacity=".4"/></svg>
      <span>Storm Pond</span>
    </div>
    <div class="item" id="p-access_gate" onclick="pickLayer('access_gate','rect')">
      <svg viewBox="0 0 44 32"><line x1="2" y1="16" x2="12" y2="16" stroke="#555" stroke-width="2"/><line x1="32" y1="16" x2="42" y2="16" stroke="#555" stroke-width="2"/><path d="M12 8 L22 16 L32 8" fill="none" stroke="#555" stroke-width="2" stroke-linejoin="round"/><line x1="12" y1="8" x2="12" y2="24" stroke="#555" stroke-width="2"/><line x1="32" y1="8" x2="32" y2="24" stroke="#555" stroke-width="2"/></svg>
      <span>Access Gate</span>
    </div>
    <div class="item" id="p-fire_staging" onclick="pickLayer('fire_staging','poly')">
      <svg viewBox="0 0 44 32"><rect x="2" y="3" width="40" height="26" fill="#dd3333" opacity=".35"/><line x1="2" y1="3" x2="42" y2="29" stroke="#aa0000" stroke-width=".8"/><line x1="2" y1="16" x2="42" y2="29" stroke="#aa0000" stroke-width=".8"/><line x1="2" y1="3" x2="42" y2="16" stroke="#aa0000" stroke-width=".8"/><rect x="2" y="3" width="40" height="26" fill="none" stroke="#cc0000" stroke-width="1.2"/></svg>
      <span>Fire Staging</span>
    </div>
  </div>

  <div class="cat">BESS Equipment</div>
  <div class="items">
    <div class="item" id="p-battery" onclick="pickLayer('battery','rect')">
      <svg viewBox="0 0 44 32"><rect x="2" y="5" width="36" height="22" fill="#ddeeff" stroke="#2266bb" stroke-width="1.8"/><rect x="38" y="10" width="4" height="12" rx="1.5" fill="#2266bb"/><rect x="5" y="9" width="5" height="14" rx="1" fill="#2266bb" opacity=".6"/><rect x="12" y="9" width="5" height="14" rx="1" fill="#2266bb" opacity=".5"/><rect x="19" y="9" width="5" height="14" rx="1" fill="#2266bb" opacity=".35"/><rect x="26" y="9" width="5" height="14" rx="1" fill="#2266bb" opacity=".2"/><text x="22" y="30" text-anchor="middle" font-size="6" fill="#2266bb" font-family="Courier New" font-weight="bold">BESS</text></svg>
      <span>Battery Container</span>
    </div>
    <div class="item" id="p-mv_transformer" onclick="pickLayer('mv_transformer','rect')">
      <svg viewBox="0 0 44 32"><rect x="3" y="4" width="38" height="24" fill="#eeeef8" stroke="#444466" stroke-width="1.8"/><circle cx="16" cy="16" r="8" fill="none" stroke="#444466" stroke-width="1.2"/><circle cx="28" cy="16" r="8" fill="none" stroke="#444466" stroke-width="1.2"/><line x1="3" y1="16" x2="8" y2="16" stroke="#444466" stroke-width="1.2"/><line x1="36" y1="16" x2="41" y2="16" stroke="#444466" stroke-width="1.2"/></svg>
      <span>MV Transformer</span>
    </div>
    <div class="item" id="p-pcs" onclick="pickLayer('pcs','rect')">
      <svg viewBox="0 0 44 32"><rect x="3" y="4" width="38" height="24" fill="#fff8ee" stroke="#cc6600" stroke-width="1.8"/><path d="M12 16 L18 8 L18 13 L26 13 L26 19 L18 19 L18 24 Z" fill="#cc6600" opacity=".6"/><text x="32" y="21" text-anchor="middle" font-size="6.5" fill="#cc6600" font-family="Courier New" font-weight="bold">PCS</text></svg>
      <span>PCS / Inverter</span>
    </div>
    <div class="item" id="p-substation" onclick="pickLayer('substation','rect')">
      <svg viewBox="0 0 44 32"><rect x="3" y="4" width="38" height="24" fill="#f0f0ff" stroke="#333366" stroke-width="1.8"/><text x="22" y="14" text-anchor="middle" font-size="6" fill="#333366" font-family="Courier New" font-weight="bold">SUB</text><text x="22" y="24" text-anchor="middle" font-size="5.5" fill="#333366" font-family="Courier New">STATION</text></svg>
      <span>Substation</span>
    </div>
    <div class="item" id="p-relay" onclick="pickLayer('relay','rect')">
      <svg viewBox="0 0 44 32"><rect x="5" y="4" width="34" height="24" fill="#eeffee" stroke="#228833" stroke-width="1.8"/><text x="22" y="15" text-anchor="middle" font-size="7" fill="#228833" font-family="Courier New" font-weight="bold">87T</text><text x="22" y="25" text-anchor="middle" font-size="5.5" fill="#228833" font-family="Courier New">RELAY</text></svg>
      <span>Protection Relay</span>
    </div>
    <div class="item" id="p-scada" onclick="pickLayer('scada','rect')">
      <svg viewBox="0 0 44 32"><rect x="4" y="4" width="36" height="20" fill="#f0eeff" stroke="#554488" stroke-width="1.8"/><rect x="7" y="7" width="30" height="10" rx="1" fill="#554488" opacity=".15"/><text x="22" y="16" text-anchor="middle" font-size="6.5" fill="#554488" font-family="Courier New" font-weight="bold">SCADA</text><rect x="14" y="26" width="16" height="2" rx="1" fill="#554488" opacity=".5"/><line x1="22" y1="24" x2="22" y2="26" stroke="#554488" stroke-width="1"/></svg>
      <span>SCADA / EMS</span>
    </div>
  </div>

  <div class="cat">Electrical (SLD)</div>
  <div class="items">
    <div class="item" id="p-vcb" onclick="pickLayer('vcb','line')">
      <svg viewBox="0 0 44 32"><line x1="22" y1="2" x2="22" y2="11" stroke="#cc2222" stroke-width="1.8"/><circle cx="22" cy="16" r="5" fill="none" stroke="#cc2222" stroke-width="1.5"/><line x1="22" y1="21" x2="22" y2="30" stroke="#cc2222" stroke-width="1.8" stroke-dasharray="3,2"/><text x="28" y="29" font-size="6" fill="#cc2222" font-family="Courier New">VCB</text></svg>
      <span>VCB</span>
    </div>
    <div class="item" id="p-busbar" onclick="pickLayer('busbar','line')">
      <svg viewBox="0 0 44 32"><rect x="2" y="13" width="40" height="6" rx="1" fill="#888" opacity=".8"/><line x1="11" y1="6" x2="11" y2="13" stroke="#888" stroke-width="1.5"/><line x1="22" y1="6" x2="22" y2="13" stroke="#888" stroke-width="1.5"/><line x1="33" y1="6" x2="33" y2="13" stroke="#888" stroke-width="1.5"/></svg>
      <span>34.5kV Busbar</span>
    </div>
    <div class="item" id="p-meter" onclick="pickLayer('meter','rect')">
      <svg viewBox="0 0 44 32"><circle cx="22" cy="16" r="12" fill="none" stroke="#228866" stroke-width="1.5"/><path d="M10 22 Q22 6 34 22" fill="none" stroke="#446655" stroke-width=".8"/><line x1="22" y1="16" x2="28" y2="10" stroke="#228866" stroke-width="1.5" stroke-linecap="round"/><circle cx="22" cy="16" r="1.5" fill="#228866"/></svg>
      <span>Smart Meter</span>
    </div>
    <div class="item" id="p-cable" onclick="pickLayer('cable','line')">
      <svg viewBox="0 0 44 32"><path d="M4 16 Q12 8 22 16 Q32 24 40 16" fill="none" stroke="#cc6600" stroke-width="2.5"/><circle cx="4" cy="16" r="2" fill="#cc6600"/><circle cx="40" cy="16" r="2" fill="#cc6600"/></svg>
      <span>HV Cable</span>
    </div>
  </div>

  <div class="cat">Annotation</div>
  <div class="items">
    <div class="item" id="p-annotation" onclick="pickLayer('annotation','text')">
      <svg viewBox="0 0 44 32"><text x="6" y="24" font-size="20" fill="#c8cbd4" font-family="Courier New" font-weight="bold">Aa</text></svg>
      <span>Text Label</span>
    </div>
    <div class="item" id="p-dimension" onclick="pickLayer('dimension','dim')">
      <svg viewBox="0 0 44 32"><line x1="4" y1="16" x2="40" y2="16" stroke="#ddaa00" stroke-width="1"/><polygon points="4,13 4,19 10,16" fill="#ddaa00"/><polygon points="40,13 40,19 34,16" fill="#ddaa00"/><line x1="4" y1="8" x2="4" y2="24" stroke="#ddaa00" stroke-width=".8"/><line x1="40" y1="8" x2="40" y2="24" stroke="#ddaa00" stroke-width=".8"/><text x="22" y="12" text-anchor="middle" font-size="7" fill="#ddaa00" font-family="Courier New">25.0m</text></svg>
      <span>Dimension</span>
    </div>
  </div>

</div>

<!-- CANVAS AREA -->
<div id="canvas-area">
  <div id="canvas-scroll">
    <div id="canvas-wrap">
      <svg id="main-svg" xmlns="http://www.w3.org/2000/svg" class="sel"
        onmousedown="svgDown(event)"
        onmousemove="svgMove(event)"
        onmouseup="svgUp(event)"
        ondblclick="svgDbl(event)"
        onwheel="svgWheel(event)"
        ondragover="event.preventDefault()"
        ondrop="svgDrop(event)">

        <defs id="svg-defs">
          <!-- Hatch patterns -->
          <pattern id="hVeg" width="12" height="12" patternUnits="userSpaceOnUse">
            <rect width="12" height="12" fill="#88cc44" opacity=".45"/>
            <path d="M0 12 Q3 6 6 12 Q9 6 12 12" fill="none" stroke="#558822" stroke-width=".8"/>
          </pattern>
          <pattern id="hWet" width="10" height="10" patternUnits="userSpaceOnUse">
            <rect width="10" height="10" fill="#4499cc" opacity=".35"/>
            <line x1="0" y1="3" x2="10" y2="3" stroke="#2266aa" stroke-width=".7"/>
            <line x1="0" y1="7" x2="10" y2="7" stroke="#2266aa" stroke-width=".7"/>
          </pattern>
          <pattern id="hFire" width="8" height="8" patternUnits="userSpaceOnUse">
            <rect width="8" height="8" fill="#dd3333" opacity=".25"/>
            <line x1="0" y1="0" x2="8" y2="8" stroke="#aa0000" stroke-width=".7"/>
            <line x1="0" y1="4" x2="4" y2="8" stroke="#aa0000" stroke-width=".7"/>
            <line x1="4" y1="0" x2="8" y2="4" stroke="#aa0000" stroke-width=".7"/>
          </pattern>
          <pattern id="hPond" width="10" height="10" patternUnits="userSpaceOnUse">
            <rect width="10" height="10" fill="#2266aa" opacity=".6"/>
          </pattern>
          <pattern id="hRoad" width="10" height="10" patternUnits="userSpaceOnUse">
            <rect width="10" height="10" fill="#aa9966" opacity=".75"/>
          </pattern>
          <!-- Arrow for dimensions -->
          <marker id="arr-dim" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
            <polygon points="0,1 8,4 0,7" fill="#ddaa00"/>
          </marker>
          <marker id="arr-dim-rev" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse">
            <polygon points="0,1 8,4 0,7" fill="#ddaa00"/>
          </marker>
          <!-- Selection highlight filter -->
          <filter id="f-sel" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#ff9900" flood-opacity=".9"/>
          </filter>
        </defs>

        <!-- Layers in order -->
        <g id="l-grid"></g>
        <g id="l-sheet"></g>
        <g id="l-objects"></g>
        <g id="l-temp"></g>
        <g id="l-sel"></g>
      </svg>
    </div>
  </div>
</div>

<!-- RIGHT PANEL -->
<div id="right">
  <div class="rp-blk">
    <div class="rp-hd">Project Info</div>
    <div class="rp-row"><label class="rp-lbl">PROJECT NAME</label><input class="rp-in" id="f-proj" value="PROJECT NAME" oninput="updateTB()"></div>
    <div class="rp-row"><label class="rp-lbl">% DESIGN</label><input class="rp-in" id="f-pct" value="30" oninput="updateTB()" style="width:60px"></div>
    <div class="rp-row"><label class="rp-lbl">CLIENT NAME</label><input class="rp-in" id="f-client" value="CLIENT NAME" oninput="updateTB()"></div>
    <div class="rp-row"><label class="rp-lbl">PROJECT REF</label><input class="rp-in" id="f-ref" value="US_PROJECT_REF" oninput="updateTB()"></div>
  </div>
  <div class="rp-blk">
    <div class="rp-hd">Sheet Info</div>
    <div class="rp-row"><label class="rp-lbl">SHEET NAME</label><input class="rp-in" id="f-sname" value="CIVIL SITE PLAN" oninput="updateTB()"></div>
    <div class="rp-row"><label class="rp-lbl">SHEET NO</label><input class="rp-in" id="f-sno" value="S-01" oninput="updateTB()"></div>
    <div class="rp-row"><label class="rp-lbl">LAT / LONG</label><input class="rp-in" id="f-ll" value="33.0000 / -84.0000" oninput="updateTB()"></div>
    <div class="rp-row" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px">
      <div><label class="rp-lbl">DRWN</label><input class="rp-in" id="f-drwn" value="XX" oninput="updateTB()"></div>
      <div><label class="rp-lbl">REVW</label><input class="rp-in" id="f-revw" value="XX" oninput="updateTB()"></div>
      <div><label class="rp-lbl">APPRVD</label><input class="rp-in" id="f-apprvd" value="XX" oninput="updateTB()"></div>
    </div>
    <div class="rp-row"><label class="rp-lbl">SCALE</label>
      <select class="rp-in" id="f-scale" onchange="updateTB()">
        <option>1:500</option><option selected>1:1000</option>
        <option>1:2000</option><option>1:5000</option><option>NTS</option>
      </select>
    </div>
  </div>
  <div class="rp-blk">
    <div class="rp-hd">Revision Table</div>
    <div class="rev-grid" style="margin-bottom:4px">
      <div class="rev-hdr">REV</div><div class="rev-hdr">DESCRIPTION</div>
      <div class="rev-hdr">BY</div><div class="rev-hdr">DATE</div>
    </div>
    <div id="rev-body"></div>
  </div>
  <div class="rp-blk" id="props-blk">
    <div class="rp-hd">Selected Object</div>
    <div id="props-body" style="font-size:10px;color:#556070">No selection</div>
  </div>
</div>

</div><!-- /body -->

<!-- STATUSBAR -->
<div id="statusbar">
  <span>Tool: <b id="sb-tool">Select</b></span>
  <span>Layer: <b id="sb-layer" style="color:#e8a020">site_boundary</b></span>
  <span>Objects: <b id="sb-objs">0</b></span>
  <span>Zoom: <b id="sb-zoom">100%</b></span>
  <span style="margin-left:auto">V=Select  L=Line  R=Rect  P=Poly  C=Circle  T=Text  D=Dim  F=Fit  ESC=Cancel  Del=Delete  Ctrl+Z=Undo</span>
</div>

<!-- ═══════════════════════════════ SCRIPT ═══════════════════════════════ -->
<script>
'use strict';

// ─────────────────────────────────────────────
//  SHEET DIMENSIONS (SVG coordinate units = metres at 1:1000)
//  Full sheet: 17"×11" → 432mm × 279mm → ~432 × 279 "units"
//  We use 1 unit = 0.5m at 1:1000 for drawing feel
//  Sheet in SVG: 1600 × 1050 px-units
// ─────────────────────────────────────────────
const SW = 1600, SH = 1050;   // sheet width/height in SVG units
const MB = 40;                  // margin border
const TB_W = 310;               // title block width
const DA_X1 = MB, DA_Y1 = MB + 20;  // drawing area top-left
const DA_X2 = SW - TB_W - MB,  DA_Y2 = SH - MB - 20;
const DA_W  = DA_X2 - DA_X1,   DA_H  = DA_Y2 - DA_Y1;
const TB_X  = SW - TB_W - MB + 2, TB_Y = DA_Y1;
const TB_TW = TB_W - 4;

// ─────────────────────────────────────────────
//  LAYER DEFINITIONS
// ─────────────────────────────────────────────
const LD = {
  site_boundary: {n:'SITE BOUNDARY',    c:'#ff3333', lw:2.5,  dash:'',    fill:'none',     alpha:1,   hatch:null},
  fence:         {n:'FENCE',            c:'#333333', lw:1.5,  dash:'8,4', fill:'none',     alpha:1,   hatch:null},
  vegetation:    {n:'VEGETATION',       c:'#558822', lw:1,    dash:'',    fill:'#88cc44',  alpha:.55, hatch:'hVeg'},
  wetlands:      {n:'WETLANDS',         c:'#2266aa', lw:1,    dash:'',    fill:'#4499cc',  alpha:.45, hatch:'hWet'},
  access_road:   {n:'ACCESS ROAD',      c:'#887755', lw:1,    dash:'',    fill:'#aa9966',  alpha:.8,  hatch:'hRoad'},
  pond:          {n:'STORM WATER POND', c:'#1144aa', lw:1,    dash:'',    fill:'#2266aa',  alpha:.65, hatch:'hPond'},
  access_gate:   {n:'ACCESS GATE',      c:'#444444', lw:1.5,  dash:'',    fill:'#eeeeee',  alpha:.8,  hatch:null},
  fire_staging:  {n:'FIRE STAGING',     c:'#990000', lw:1.5,  dash:'',    fill:'#dd3333',  alpha:.4,  hatch:'hFire'},
  battery:       {n:'BATTERY CONTAINER',c:'#2266bb', lw:2,    dash:'',    fill:'#ddeeff',  alpha:.9,  hatch:null},
  mv_transformer:{n:'MV TRANSFORMER',   c:'#444466', lw:2,    dash:'',    fill:'#eeeef8',  alpha:.9,  hatch:null},
  pcs:           {n:'PCS/INVERTER',     c:'#cc6600', lw:2,    dash:'',    fill:'#fff8ee',  alpha:.9,  hatch:null},
  substation:    {n:'SUBSTATION',       c:'#333366', lw:2,    dash:'',    fill:'#f0f0ff',  alpha:.9,  hatch:null},
  relay:         {n:'PROTECTION RELAY', c:'#228833', lw:1.5,  dash:'',    fill:'#eeffee',  alpha:.9,  hatch:null},
  scada:         {n:'SCADA/EMS',        c:'#554488', lw:1.5,  dash:'',    fill:'#f0eeff',  alpha:.9,  hatch:null},
  vcb:           {n:'VCB',              c:'#cc2222', lw:1.5,  dash:'',    fill:'none',     alpha:1,   hatch:null},
  busbar:        {n:'BUSBAR',           c:'#888888', lw:3,    dash:'',    fill:'#888888',  alpha:.8,  hatch:null},
  meter:         {n:'SMART METER',      c:'#228866', lw:1.5,  dash:'',    fill:'#eeffee',  alpha:.9,  hatch:null},
  cable:         {n:'HV CABLE',         c:'#cc6600', lw:2,    dash:'',    fill:'none',     alpha:1,   hatch:null},
  annotation:    {n:'ANNOTATION',       c:'#222222', lw:1,    dash:'',    fill:'#222222',  alpha:1,   hatch:null},
  dimension:     {n:'DIMENSION',        c:'#ddaa00', lw:.8,   dash:'',    fill:'none',     alpha:1,   hatch:null},
};

// ─────────────────────────────────────────────
//  STATE
// ─────────────────────────────────────────────
let tool = 'sel', activeLyr = 'site_boundary';
let objs = [], selId = null, idN = 0;
let undoStk = [], redoStk = [];
let zoom = 1, snapOn = true, gridOn = true, snapSz = 20;
let isPan = false, panSX = 0, panSY = 0, panOX = 0, panOY = 0;
let drawing = false, dpts = [], dStart = null, tmpPt = null;

const NS = 'http://www.w3.org/2000/svg';
const svg = () => document.getElementById('main-svg');
const lObj  = () => document.getElementById('l-objects');
const lTemp = () => document.getElementById('l-temp');
const lSel  = () => document.getElementById('l-sel');
const lGrid = () => document.getElementById('l-grid');
const lSheet= () => document.getElementById('l-sheet');

// ─────────────────────────────────────────────
//  INIT
// ─────────────────────────────────────────────
window.addEventListener('load', () => {
  resizeSVG();
  buildSheet();
  buildGrid();
  buildRevRows();
  updateTB();
  fitView();
  pickLayer('site_boundary','poly');
});
window.addEventListener('resize', () => { resizeSVG(); });

function resizeSVG() {
  const s = svg();
  s.setAttribute('width',  SW);
  s.setAttribute('height', SH);
  s.setAttribute('viewBox', `0 0 ${SW} ${SH}`);
}

// ─────────────────────────────────────────────
//  SHEET TEMPLATE
// ─────────────────────────────────────────────
function e(tag, attrs, text) {
  const el = document.createElementNS(NS, tag);
  if (attrs) Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v));
  if (text !== undefined) el.textContent = text;
  return el;
}

function buildSheet() {
  const L = lSheet(); L.innerHTML = '';

  // White sheet background
  L.appendChild(e('rect',{x:0,y:0,width:SW,height:SH,fill:'#ffffff'}));

  // Outer thick border
  L.appendChild(e('rect',{x:12,y:12,width:SW-24,height:SH-24,fill:'none',stroke:'#000','stroke-width':'2'}));

  // Drawing area (light fill so it's distinct)
  L.appendChild(e('rect',{x:DA_X1,y:DA_Y1,width:DA_W,height:DA_H,fill:'#f9fafb',stroke:'#000','stroke-width':'0.8'}));

  // Top copyright text
  L.appendChild(e('text',{x:DA_X1+4,y:DA_Y1-5,'font-size':'5.5','font-family':'Arial','font-weight':'bold',fill:'#000'},
    'THIS DRAWING IS THE PROPERTY OF SUNSTRIPE, Inc. ANY REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN PERMISSION OF SUNSTRIPE, Inc IS PROHIBITED.'));

  // Bottom disclaimer
  L.appendChild(e('text',{x:SW/2,y:SH-MB+14,'text-anchor':'middle','font-size':'7','font-family':'Arial',
    'font-weight':'bold','font-style':'italic',fill:'#000'},'FOR INFORMATION PURPOSES ONLY - NOT FOR CONSTRUCTION'));

  buildTitleBlock(L);
}

function buildTitleBlock(L) {
  const X = TB_X, Y = TB_Y, W = TB_TW;
  let cy = Y;

  // TB outer border
  L.appendChild(e('rect',{x:X,y:Y,width:W,height:DA_H,fill:'#fff',stroke:'#000','stroke-width':'0.8'}));

  // ── North Arrow section ─────────────────────
  const NAH = 90;
  L.appendChild(e('rect',{x:X,y:cy,width:W,height:NAH,fill:'#f5f5f5',stroke:'#bbb','stroke-width':'.4'}));
  // Circle
  const NCX = X+W/2, NCY = cy+NAH/2, NR = 32;
  L.appendChild(e('circle',{cx:NCX,cy:NCY,r:NR,fill:'none',stroke:'#000','stroke-width':'1.2'}));
  // Needle – black half
  const nPts = `${NCX},${NCY-NR+3} ${NCX-9},${NCY+12} ${NCX},${NCY+6} ${NCX+9},${NCY+12}`;
  L.appendChild(e('polygon',{points:nPts,fill:'#000'}));
  // White left half overlay
  const nW = `${NCX},${NCY-NR+3} ${NCX-9},${NCY+12} ${NCX},${NCY+6}`;
  L.appendChild(e('polygon',{points:nW,fill:'#fff',stroke:'#000','stroke-width':'.5'}));
  // N text
  L.appendChild(e('text',{x:NCX,y:NCY-NR-5,'text-anchor':'middle','font-size':'14','font-family':'Arial','font-weight':'bold',fill:'#000'},'N'));
  cy += NAH;
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#000','stroke-width':'.8'}));

  // ── LEGENDS header ───────────────────────────
  const LHH = 16;
  L.appendChild(e('rect',{x:X,y:cy,width:W,height:LHH,fill:'#e8e8e8'}));
  L.appendChild(e('text',{x:X+W/2,y:cy+11,'text-anchor':'middle','font-size':'8.5',
    'font-family':'Arial','font-weight':'bold',fill:'#000'},'LEGENDS'));
  cy += LHH;

  // ── Legend rows ──────────────────────────────
  const legItems = [
    {sym:'sb',   label:'SITE BOUNDARY'},
    {sym:'fence',label:'FENCE'},
    {sym:'veg',  label:'VEGETATION'},
    {sym:'wet',  label:'WETLANDS'},
    {sym:'pond', label:'STORM WATER POND'},
    {sym:'fire', label:'FIRE BATTERY ACCESS ROAD'},
    {sym:'road', label:'ACCESS ROAD'},
    {sym:'gate', label:'ACCESS GATE'},
    {sym:'batt', label:'BATTERY CONTAINER'},
    {sym:'mvt',  label:'MV TRANSFORMER'},
    {sym:'fstg', label:'FIRE STAGING AREA'},
  ];
  const LRH = 18;
  const symW = 46, gap = 5;
  legItems.forEach(item => {
    L.appendChild(e('rect',{x:X,y:cy,width:W,height:LRH,fill:'none',stroke:'#ddd','stroke-width':'.3'}));
    drawLegSym(L, item.sym, X+3, cy+2, symW, LRH-4);
    L.appendChild(e('text',{x:X+symW+gap+3,y:cy+LRH/2+3,'font-size':'7',
      'font-family':'Arial',fill:'#000'},item.label));
    cy += LRH;
  });
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#000','stroke-width':'.8'}));

  // ── Project name block ───────────────────────
  const PNH = 88;
  L.appendChild(e('rect',{x:X,y:cy,width:W,height:PNH,fill:'#fff',stroke:'#bbb','stroke-width':'.4'}));
  L.appendChild(e('text',{id:'tb-pname',x:X+W/2,y:cy+32,'text-anchor':'middle',
    'font-size':'15','font-family':'Arial','font-weight':'bold',fill:'#000'},'PROJECT NAME'));
  L.appendChild(e('text',{id:'tb-pdesign',x:X+W/2,y:cy+52,'text-anchor':'middle',
    'font-size':'12','font-family':'Arial','font-weight':'bold',fill:'#000'},'30% DESIGN'));
  L.appendChild(e('text',{id:'tb-pclient',x:X+W/2,y:cy+67,'text-anchor':'middle',
    'font-size':'7.5','font-family':'Arial',fill:'#444'},'CLIENT NAME'));
  L.appendChild(e('text',{id:'tb-pref',x:X+W/2,y:cy+80,'text-anchor':'middle',
    'font-size':'7','font-family':'Arial',fill:'#666'},'US_PROJECT_REF'));
  cy += PNH;
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#000','stroke-width':'.8'}));

  // ── Revision table ───────────────────────────
  const RVHH = 14, RVRH = 13;
  L.appendChild(e('rect',{x:X,y:cy,width:W,height:RVHH,fill:'#e8e8e8'}));
  const rcols = [{t:'REV',w:22},{t:'DESCRIPTION',w:W-100},{t:'BY',w:30},{t:'DATE',w:48}];
  let rx = X;
  rcols.forEach(col => {
    L.appendChild(e('rect',{x:rx,y:cy,width:col.w,height:RVHH,fill:'none',stroke:'#bbb','stroke-width':'.4'}));
    L.appendChild(e('text',{x:rx+col.w/2,y:cy+10,'text-anchor':'middle',
      'font-size':'6.5','font-family':'Arial','font-weight':'bold',fill:'#000'},col.t));
    rx += col.w;
  });
  cy += RVHH;
  const REVS = ['A','B','C','D','E'];
  REVS.forEach((rev,ri) => {
    const RY = cy;
    L.appendChild(e('rect',{x:X,y:RY,width:W,height:RVRH,fill:'none',stroke:'#ddd','stroke-width':'.3'}));
    let rx2 = X;
    rcols.forEach((col,ci) => {
      L.appendChild(e('rect',{x:rx2,y:RY,width:col.w,height:RVRH,fill:'none',stroke:'#ddd','stroke-width':'.3'}));
      const vals = [rev,'','',''];
      if (vals[ci]) {
        L.appendChild(e('text',{id:`tb-rev${ri}-${ci}`,x:rx2+col.w/2,y:RY+9,'text-anchor':'middle',
          'font-size':'6','font-family':'Arial',fill:'#000'},vals[ci]));
      } else {
        L.appendChild(e('text',{id:`tb-rev${ri}-${ci}`,x:rx2+3,y:RY+9,
          'font-size':'6','font-family':'Arial',fill:'#000'},''));
      }
      rx2 += col.w;
    });
    cy += RVRH;
  });
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#000','stroke-width':'.8'}));

  // ── SunStripe brand ──────────────────────────
  const BRH = 50;
  L.appendChild(e('rect',{x:X,y:cy,width:W,height:BRH,fill:'#fff',stroke:'#bbb','stroke-width':'.4'}));
  L.appendChild(e('text',{x:X+W/2,y:cy+22,'text-anchor':'middle',
    'font-size':'16','font-family':'Arial','font-weight':'bold',fill:'#dd2200'},'SunStripe'));
  L.appendChild(e('text',{x:X+W/2,y:cy+34,'text-anchor':'middle',
    'font-size':'6.5','font-family':'Arial',fill:'#444'},'Trusted Clean Energy Partners'));
  L.appendChild(e('text',{x:X+W/2,y:cy+45,'text-anchor':'middle',
    'font-size':'6','font-family':'Arial',fill:'#555'},'6363 N State Highway 161, Ste 250 Irving, TX 75038'));
  cy += BRH;
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#000','stroke-width':'.8'}));

  // ── Sheet name ───────────────────────────────
  L.appendChild(e('text',{x:X+4,y:cy+12,'font-size':'7','font-family':'Arial','font-weight':'bold',fill:'#000'},'SHEET NAME:'));
  L.appendChild(e('text',{id:'tb-sname',x:X+W/2,y:cy+28,'text-anchor':'middle',
    'font-size':'10','font-family':'Arial','font-weight':'bold',fill:'#000'},'CIVIL SITE PLAN'));
  cy += 38;
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#bbb','stroke-width':'.4'}));

  // ── Lat/Long ─────────────────────────────────
  L.appendChild(e('text',{x:X+4,y:cy+12,'font-size':'6.5','font-family':'Arial',fill:'#000'},'LAT/LONG:'));
  L.appendChild(e('text',{id:'tb-ll',x:X+58,y:cy+12,'font-size':'6.5','font-family':'Arial',fill:'#000'},'33.0000 / -84.0000'));
  cy += 18;
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#bbb','stroke-width':'.4'}));

  // ── DRWN / REVW / APPRVD / SIZE ──────────────
  const DRW_H = 22, DRW_COLS = [{l:'DRWN',w:W*.22},{l:'REVW',w:W*.22},{l:'APPRVD',w:W*.28},{l:'SIZE',w:W*.28}];
  let dcx = X;
  DRW_COLS.forEach(col => {
    L.appendChild(e('rect',{x:dcx,y:cy,width:col.w,height:DRW_H,fill:'none',stroke:'#ccc','stroke-width':'.4'}));
    L.appendChild(e('text',{x:dcx+col.w/2,y:cy+9,'text-anchor':'middle',
      'font-size':'6.5','font-family':'Arial','font-weight':'bold',fill:'#000'},col.l));
    dcx += col.w;
  });
  cy += DRW_H/2;
  let dcx2 = X;
  const dwIDs = ['tb-drwn','tb-revw','tb-apprvd',''];
  DRW_COLS.forEach((col,i) => {
    if(dwIDs[i]) L.appendChild(e('text',{id:dwIDs[i],x:dcx2+col.w/2,y:cy+10,'text-anchor':'middle',
      'font-size':'7','font-family':'Arial',fill:'#000'},i<3?'XX':'11"X17"'));
    else L.appendChild(e('text',{x:dcx2+col.w/2,y:cy+10,'text-anchor':'middle',
      'font-size':'7','font-family':'Arial',fill:'#000'},'11"X17"'));
    dcx2 += col.w;
  });
  cy += DRW_H/2;
  L.appendChild(e('line',{x1:X,y1:cy,x2:X+W,y2:cy,stroke:'#000','stroke-width':'.8'}));

  // ── Sheet No ─────────────────────────────────
  L.appendChild(e('text',{x:X+4,y:cy+12,'font-size':'6.5','font-family':'Arial',fill:'#000'},'SHEET:'));
  L.appendChild(e('text',{id:'tb-sno',x:X+W/2,y:DA_Y1+DA_H-16,'text-anchor':'middle',
    'font-size':'20','font-family':'Arial','font-weight':'bold',fill:'#000'},'S-01'));

  // ── Scale bar in drawing area ─────────────────
  buildScaleBar(L);
}

function buildScaleBar(L) {
  const sbX = DA_X1 + 20, sbY = DA_Y2 - 28;
  L.appendChild(e('text',{x:sbX,y:sbY-3,'font-size':'7','font-family':'Arial','font-weight':'bold',fill:'#000','id':'tb-scale-txt'},'SCALE  1:1000'));
  // 5 alternating blocks × 30 units = 150m
  for (let i=0;i<5;i++) {
    L.appendChild(e('rect',{x:sbX+i*30,y:sbY,width:30,height:9,
      fill:i%2===0?'#000':'#fff',stroke:'#000','stroke-width':'.6'}));
  }
  ['0m','30m','60m','90m','120m','150m'].forEach((l,i) => {
    L.appendChild(e('text',{x:sbX+i*30,y:sbY+19,'text-anchor':'middle',
      'font-size':'6','font-family':'Arial',fill:'#000'},l));
  });
}

function drawLegSym(L, sym, x, y, w, h) {
  const mx=x+w/2, my=y+h/2;
  const R = (tag,attrs) => L.appendChild(e(tag,attrs));
  switch(sym) {
    case 'sb':    R('rect',{x,y,width:w,height:h,fill:'none',stroke:'#ff3333','stroke-width':'2.5'}); break;
    case 'fence': R('line',{x1:x,y1:my,x2:x+w,y2:my,stroke:'#333','stroke-width':'1.5','stroke-dasharray':'5,3'});
      [x+4,x+w/2,x+w-4].forEach(lx=>{R('line',{x1:lx,y1:y,x2:lx,y2:y+h,stroke:'#333','stroke-width':'1'});}); break;
    case 'veg':   R('rect',{x,y,width:w,height:h,fill:'url(#hVeg)',stroke:'#558822','stroke-width':'.6'}); break;
    case 'wet':   R('rect',{x,y,width:w,height:h,fill:'url(#hWet)',stroke:'#2266aa','stroke-width':'.6'}); break;
    case 'pond':  R('rect',{x,y,width:w,height:h,fill:'#2266aa',opacity:'.65'}); break;
    case 'fire':  R('rect',{x,y,width:w,height:h,fill:'url(#hFire)',stroke:'#884400','stroke-width':'.6'}); break;
    case 'road':  R('rect',{x,y,width:w,height:h,fill:'#aa9966',opacity:'.85'}); break;
    case 'gate':
      R('line',{x1:x,y1:my,x2:mx-6,y2:my,stroke:'#444','stroke-width':'1.5'});
      R('line',{x1:mx+6,y1:my,x2:x+w,y2:my,stroke:'#444','stroke-width':'1.5'});
      R('path',{d:`M${mx-6} ${y+2} L${mx} ${my} L${mx+6} ${y+2}`,fill:'none',stroke:'#444','stroke-width':'1.5','stroke-linejoin':'round'});
      break;
    case 'batt':  R('rect',{x,y,width:w,height:h,fill:'#ddeeff',stroke:'#2266bb','stroke-width':'1.5'}); break;
    case 'mvt':   R('rect',{x,y,width:w,height:h,fill:'#eeeef8',stroke:'#444466','stroke-width':'1.5'}); break;
    case 'fstg':  R('rect',{x,y,width:w,height:h,fill:'url(#hFire)',stroke:'#aa0000','stroke-width':'1'}); break;
  }
}

// ─────────────────────────────────────────────
//  GRID
// ─────────────────────────────────────────────
function buildGrid() {
  const L = lGrid(); L.innerHTML = '';
  if (!gridOn) return;
  const minor = snapSz, major = snapSz*5;
  for(let x=DA_X1;x<=DA_X2;x+=minor){
    const isMaj = (x-DA_X1)%major===0;
    L.appendChild(e('line',{x1:x,y1:DA_Y1,x2:x,y2:DA_Y2,
      stroke:isMaj?'#c8d0d8':'#dde2e8','stroke-width':isMaj?'.5':'.3'}));
  }
  for(let y=DA_Y1;y<=DA_Y2;y+=minor){
    const isMaj = (y-DA_Y1)%major===0;
    L.appendChild(e('line',{x1:DA_X1,y1:y,x2:DA_X2,y2:y,
      stroke:isMaj?'#c8d0d8':'#dde2e8','stroke-width':isMaj?'.5':'.3'}));
  }
}

// ─────────────────────────────────────────────
//  REVISION ROWS (right panel)
// ─────────────────────────────────────────────
const revData = [
  {rev:'A',desc:'PRELIMINARY',by:'XX',date:'XXXX/X/XX'},
  {rev:'B',desc:'',by:'',date:''},
  {rev:'C',desc:'',by:'',date:''},
  {rev:'D',desc:'',by:'',date:''},
  {rev:'E',desc:'',by:'',date:''},
];

function buildRevRows() {
  const cont = document.getElementById('rev-body');
  cont.innerHTML = '';
  revData.forEach((row,ri) => {
    const div = document.createElement('div');
    div.className = 'rev-grid';
    div.innerHTML = `
      <div class="rev-ltr">${row.rev}</div>
      <input class="rev-in" value="${row.desc}" placeholder="Description" oninput="revChange(${ri},1,this.value)">
      <input class="rev-in" value="${row.by}"   placeholder="BY"          oninput="revChange(${ri},2,this.value)" style="text-align:center">
      <input class="rev-in" value="${row.date}" placeholder="YYYY/M/DD"   oninput="revChange(${ri},3,this.value)">`;
    cont.appendChild(div);
  });
}

function revChange(ri, ci, val) {
  const keys = ['rev','desc','by','date'];
  revData[ri][keys[ci]] = val;
  const el = document.getElementById(`tb-rev${ri}-${ci}`);
  if (el) el.textContent = val;
}

// ─────────────────────────────────────────────
//  TITLE BLOCK LIVE UPDATE
// ─────────────────────────────────────────────
function updateTB() {
  const g = id => document.getElementById(id)?.value ?? '';
  const s = (id,val) => { const el=document.getElementById(id); if(el) el.textContent=val; };
  s('tb-pname',  g('f-proj'));
  s('tb-pdesign',g('f-pct')+'% DESIGN');
  s('tb-pclient',g('f-client'));
  s('tb-pref',   g('f-ref'));
  s('tb-sname',  g('f-sname'));
  s('tb-sno',    g('f-sno'));
  s('tb-ll',     g('f-ll'));
  s('tb-drwn',   g('f-drwn'));
  s('tb-revw',   g('f-revw'));
  s('tb-apprvd', g('f-apprvd'));
  s('tb-scale-txt','SCALE  '+ g('f-scale'));
  // Rev data from right panel
  revData.forEach((row,ri) => {
    s(`tb-rev${ri}-1`, row.desc);
    s(`tb-rev${ri}-2`, row.by);
    s(`tb-rev${ri}-3`, row.date);
  });
}

// ─────────────────────────────────────────────
//  COORDINATE TRANSFORM
// ─────────────────────────────────────────────
function svgCoord(clientX, clientY) {
  const wrap = document.getElementById('canvas-scroll');
  const r = document.getElementById('canvas-wrap').getBoundingClientRect();
  return {
    x: (clientX - r.left) / zoom,
    y: (clientY - r.top) / zoom
  };
}

function snap(v) { return snapOn ? Math.round(v/snapSz)*snapSz : v; }
function snp(pt) { return {x:snap(pt.x), y:snap(pt.y)}; }
function inDA(x,y){ return x>=DA_X1&&x<=DA_X2&&y>=DA_Y1&&y<=DA_Y2; }

// ─────────────────────────────────────────────
//  TOOL / LAYER
// ─────────────────────────────────────────────
function setTool(t) {
  tool = t;
  drawing = false; dpts = []; dStart = null; lTemp().innerHTML = '';
  document.querySelectorAll('.btn[id^="b-"]').forEach(b => b.classList.remove('on'));
  const btn = document.getElementById('b-'+t);
  if (btn) btn.classList.add('on');
  document.getElementById('sb-tool').textContent = t.toUpperCase();
  const s = svg();
  s.className.baseVal = t==='sel'?'sel sel':t==='pan'?'pan':'';
}

function pickLayer(lyr, suggestTool) {
  activeLyr = lyr;
  document.querySelectorAll('.item').forEach(i => i.classList.remove('active'));
  const p = document.getElementById('p-'+lyr);
  if (p) p.classList.add('active');
  document.getElementById('sb-layer').textContent = lyr;
  if (suggestTool) setTool(suggestTool);
}

// ─────────────────────────────────────────────
//  MOUSE EVENTS
// ─────────────────────────────────────────────
function svgDown(ev) {
  if (ev.button===1 || (ev.button===0 && ev.altKey)) {
    isPan=true; panSX=ev.clientX; panSY=ev.clientY;
    const wrap=document.getElementById('canvas-scroll');
    panOX=wrap.scrollLeft; panOY=wrap.scrollTop; ev.preventDefault(); return;
  }
  if (ev.button!==0) return;
  const raw = svgCoord(ev.clientX, ev.clientY);
  const pt = snp(raw);

  if (tool==='sel') { selectAt(raw.x, raw.y); return; }
  if (!inDA(pt.x, pt.y)) return;

  if (tool==='poly') {
    if (!drawing) { drawing=true; dpts=[pt]; }
    else dpts.push(pt);
  } else if (tool==='rect' || tool==='circle') {
    if (!drawing) { drawing=true; dStart=pt; }
  } else if (tool==='line') {
    if (!drawing) { drawing=true; dpts=[pt]; }
    else dpts.push(pt);
  } else if (tool==='dim') {
    if (!drawing) { drawing=true; dStart=pt; }
  } else if (tool==='text') {
    const txt = prompt('Enter label text:');
    if (txt) { saveU(); objs.push({id:'o'+(++idN),type:'text',lyr:activeLyr,x:pt.x,y:pt.y,text:txt}); renderAll(); }
  }
}

function svgMove(ev) {
  if (isPan) {
    const wrap=document.getElementById('canvas-scroll');
    wrap.scrollLeft = panOX-(ev.clientX-panSX);
    wrap.scrollTop  = panOY-(ev.clientY-panSY);
    return;
  }
  const raw = svgCoord(ev.clientX, ev.clientY);
  const pt = snp(raw);
  document.getElementById('coord').textContent =
    `X: ${(pt.x-DA_X1).toFixed(0)}m   Y: ${(DA_Y2-pt.y).toFixed(0)}m   Scale: ${document.getElementById('f-scale')?.value||'1:1000'}`;
  if (!drawing) return;

  lTemp().innerHTML='';
  const ld = LD[activeLyr]||LD.site_boundary;

  if ((tool==='poly'||tool==='line') && dpts.length>0) {
    dpts.forEach((p,i)=>{ if(i>0) drawTmpLine(dpts[i-1],p,ld); });
    drawTmpLine(dpts[dpts.length-1], pt, ld, true);
    addSnapDot(pt.x, pt.y);
  } else if ((tool==='rect') && dStart) {
    const tmp = document.createElementNS(NS,'rect');
    tmp.setAttribute('x',Math.min(dStart.x,pt.x)); tmp.setAttribute('y',Math.min(dStart.y,pt.y));
    tmp.setAttribute('width',Math.abs(pt.x-dStart.x)); tmp.setAttribute('height',Math.abs(pt.y-dStart.y));
    tmp.setAttribute('fill', ld.hatch?`url(#${ld.hatch})`:(ld.fill==='none'?'none':ld.fill));
    tmp.setAttribute('fill-opacity', ld.alpha);
    tmp.setAttribute('stroke',ld.c); tmp.setAttribute('stroke-width',ld.lw);
    tmp.setAttribute('stroke-dasharray','8,4'); tmp.setAttribute('opacity','.8');
    lTemp().appendChild(tmp);
    addSnapDot(pt.x, pt.y);
    // Show size
    const W2=Math.abs(pt.x-dStart.x), H2=Math.abs(pt.y-dStart.y);
    const tx=document.createElementNS(NS,'text');
    tx.setAttribute('x',(dStart.x+pt.x)/2); tx.setAttribute('y',Math.min(dStart.y,pt.y)-5);
    tx.setAttribute('text-anchor','middle'); tx.setAttribute('font-size','10');
    tx.setAttribute('font-family','Arial'); tx.setAttribute('fill','#000'); tx.setAttribute('font-weight','bold');
    tx.textContent = `${W2.toFixed(0)}m × ${H2.toFixed(0)}m`;
    lTemp().appendChild(tx);
  } else if (tool==='circle' && dStart) {
    const r=Math.sqrt((pt.x-dStart.x)**2+(pt.y-dStart.y)**2);
    const c=document.createElementNS(NS,'circle');
    c.setAttribute('cx',dStart.x);c.setAttribute('cy',dStart.y);c.setAttribute('r',r);
    c.setAttribute('fill','none');c.setAttribute('stroke',ld.c);c.setAttribute('stroke-width',ld.lw);
    c.setAttribute('stroke-dasharray','8,4');
    lTemp().appendChild(c);
  } else if (tool==='dim' && dStart) {
    drawTmpDim(dStart, pt);
  }
}

function svgUp(ev) {
  if (isPan) { isPan=false; return; }
  if (!drawing || ev.button!==0) return;
  const raw = svgCoord(ev.clientX, ev.clientY);
  const pt = snp(raw);

  if (tool==='rect' && dStart) {
    if (Math.abs(pt.x-dStart.x)>4 && Math.abs(pt.y-dStart.y)>4) {
      saveU();
      objs.push({id:'o'+(++idN),type:'rect',lyr:activeLyr,
        x:Math.min(dStart.x,pt.x),y:Math.min(dStart.y,pt.y),
        w:Math.abs(pt.x-dStart.x),h:Math.abs(pt.y-dStart.y)});
      renderAll();
    }
    drawing=false; dStart=null; lTemp().innerHTML='';
  } else if (tool==='circle' && dStart) {
    const r=Math.sqrt((pt.x-dStart.x)**2+(pt.y-dStart.y)**2);
    if (r>4) { saveU(); objs.push({id:'o'+(++idN),type:'circle',lyr:activeLyr,cx:dStart.x,cy:dStart.y,r}); renderAll(); }
    drawing=false; dStart=null; lTemp().innerHTML='';
  } else if (tool==='dim' && dStart) {
    if (Math.abs(pt.x-dStart.x)>4||Math.abs(pt.y-dStart.y)>4) {
      const dist=Math.sqrt((pt.x-dStart.x)**2+(pt.y-dStart.y)**2);
      saveU(); objs.push({id:'o'+(++idN),type:'dim',lyr:'dimension',
        x1:dStart.x,y1:dStart.y,x2:pt.x,y2:pt.y,val:dist.toFixed(1)+'m'});
      renderAll();
    }
    drawing=false; dStart=null; lTemp().innerHTML='';
  }
}

function svgDbl(ev) {
  if (!drawing) return;
  if ((tool==='poly'||tool==='line') && dpts.length>=2) {
    const raw=svgCoord(ev.clientX,ev.clientY); const pt=snp(raw);
    dpts.push(pt);
    saveU();
    objs.push({id:'o'+(++idN),type:'polyline',lyr:activeLyr,
      pts:[...dpts],closed:(tool==='poly')});
    drawing=false; dpts=[]; lTemp().innerHTML=''; renderAll();
  }
}

function svgWheel(ev) {
  ev.preventDefault();
  const factor = ev.deltaY<0?1.12:0.89;
  const raw = svgCoord(ev.clientX, ev.clientY);
  zoom = Math.min(4, Math.max(.15, zoom*factor));
  applyZoom(raw.x, raw.y, ev.clientX, ev.clientY);
}

function svgDrop(ev) {
  ev.preventDefault();
  const lyr = ev.dataTransfer?.getData('text/plain') || window._dragLyr;
  if (!lyr) return;
  const raw=svgCoord(ev.clientX,ev.clientY); const pt=snp(raw);
  if (!inDA(pt.x,pt.y)) return;
  pickLayer(lyr, 'rect');
  // Place with default size
  const sizes = {battery:[80,40],mv_transformer:[60,40],pcs:[70,40],substation:[80,50],relay:[55,40],scada:[70,45],meter:[45,45]};
  const [dw,dh] = sizes[lyr]||[60,40];
  saveU();
  objs.push({id:'o'+(++idN),type:'rect',lyr,x:pt.x-dw/2,y:pt.y-dh/2,w:dw,h:dh});
  renderAll();
}

// ─────────────────────────────────────────────
//  TEMP DRAWING HELPERS
// ─────────────────────────────────────────────
function drawTmpLine(p1,p2,ld,dashed=false){
  const l=document.createElementNS(NS,'line');
  l.setAttribute('x1',p1.x);l.setAttribute('y1',p1.y);l.setAttribute('x2',p2.x);l.setAttribute('y2',p2.y);
  l.setAttribute('stroke',ld.c);l.setAttribute('stroke-width',ld.lw);
  l.setAttribute('stroke-dasharray',dashed?'8,4':(ld.dash||''));
  lTemp().appendChild(l);
}
function drawTmpDim(p1,p2){
  const l=document.createElementNS(NS,'line');
  l.setAttribute('x1',p1.x);l.setAttribute('y1',p1.y);l.setAttribute('x2',p2.x);l.setAttribute('y2',p2.y);
  l.setAttribute('stroke','#ddaa00');l.setAttribute('stroke-width','1');
  l.setAttribute('marker-start','url(#arr-dim-rev)');l.setAttribute('marker-end','url(#arr-dim)');
  lTemp().appendChild(l);
  const dist=Math.sqrt((p2.x-p1.x)**2+(p2.y-p1.y)**2);
  const t=document.createElementNS(NS,'text');
  t.setAttribute('x',(p1.x+p2.x)/2);t.setAttribute('y',(p1.y+p2.y)/2-5);
  t.setAttribute('text-anchor','middle');t.setAttribute('font-size','11');
  t.setAttribute('font-family','Arial');t.setAttribute('fill','#ddaa00');t.setAttribute('font-weight','bold');
  t.textContent=dist.toFixed(1)+'m'; lTemp().appendChild(t);
}
function addSnapDot(x,y){
  const c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',x);c.setAttribute('cy',y);c.setAttribute('r','4');
  c.setAttribute('fill','#ff4444');c.setAttribute('opacity','.8');
  lTemp().appendChild(c);
}

// ─────────────────────────────────────────────
//  RENDER ALL OBJECTS
// ─────────────────────────────────────────────
function renderAll() {
  lObj().innerHTML='';
  objs.forEach(obj => renderObj(obj));
  document.getElementById('sb-objs').textContent = objs.length;
  if (selId) highlightSel(selId);
}

function renderObj(obj) {
  const ld = LD[obj.lyr]||LD.site_boundary;
  const fill = ld.hatch ? `url(#${ld.hatch})` : (ld.fill==='none'?'none':ld.fill);

  let el;
  if (obj.type==='polyline') {
    el = document.createElementNS(NS, obj.closed?'polygon':'polyline');
    el.setAttribute('points', obj.pts.map(p=>`${p.x},${p.y}`).join(' '));
    if (obj.closed) { el.setAttribute('fill',fill); el.setAttribute('fill-opacity',ld.alpha); }
    else el.setAttribute('fill','none');
    el.setAttribute('stroke',ld.c); el.setAttribute('stroke-width',ld.lw);
    if(ld.dash) el.setAttribute('stroke-dasharray',ld.dash);

  } else if (obj.type==='rect') {
    el = document.createElementNS(NS,'rect');
    el.setAttribute('x',obj.x);el.setAttribute('y',obj.y);
    el.setAttribute('width',obj.w);el.setAttribute('height',obj.h);
    el.setAttribute('fill',fill);el.setAttribute('fill-opacity',ld.alpha);
    el.setAttribute('stroke',ld.c);el.setAttribute('stroke-width',ld.lw);
    if(ld.dash) el.setAttribute('stroke-dasharray',ld.dash);
    // Inline label for equipment
    const lbmap={battery:'BESS',mv_transformer:'MVT',pcs:'PCS',substation:'SUB',relay:'87T',scada:'EMS',meter:'KWH'};
    if(lbmap[obj.lyr]){
      const t=document.createElementNS(NS,'text');
      t.setAttribute('x',obj.x+obj.w/2);t.setAttribute('y',obj.y+obj.h/2+3);
      t.setAttribute('text-anchor','middle');t.setAttribute('font-size',Math.min(obj.h*.28,11));
      t.setAttribute('font-family','Arial');t.setAttribute('fill',ld.c);t.setAttribute('font-weight','bold');
      t.setAttribute('pointer-events','none');t.textContent=lbmap[obj.lyr];
      lObj().appendChild(t);
    }

  } else if (obj.type==='circle') {
    el = document.createElementNS(NS,'circle');
    el.setAttribute('cx',obj.cx);el.setAttribute('cy',obj.cy);el.setAttribute('r',obj.r);
    el.setAttribute('fill',fill);el.setAttribute('fill-opacity',ld.alpha);
    el.setAttribute('stroke',ld.c);el.setAttribute('stroke-width',ld.lw);

  } else if (obj.type==='text') {
    el = document.createElementNS(NS,'text');
    el.setAttribute('x',obj.x);el.setAttribute('y',obj.y);
    el.setAttribute('font-size','12');el.setAttribute('font-family','Arial');
    el.setAttribute('fill','#000');el.textContent=obj.text;

  } else if (obj.type==='dim') {
    const g=document.createElementNS(NS,'g');
    const l=document.createElementNS(NS,'line');
    l.setAttribute('x1',obj.x1);l.setAttribute('y1',obj.y1);l.setAttribute('x2',obj.x2);l.setAttribute('y2',obj.y2);
    l.setAttribute('stroke','#ddaa00');l.setAttribute('stroke-width','1');
    l.setAttribute('marker-start','url(#arr-dim-rev)');l.setAttribute('marker-end','url(#arr-dim)');
    g.appendChild(l);
    [[obj.x1,obj.y1],[obj.x2,obj.y2]].forEach(([ex,ey])=>{
      const ext=document.createElementNS(NS,'line');
      ext.setAttribute('x1',ex);ext.setAttribute('y1',ey-10);ext.setAttribute('x2',ex);ext.setAttribute('y2',ey+10);
      ext.setAttribute('stroke','#ddaa00');ext.setAttribute('stroke-width','.8');g.appendChild(ext);
    });
    const t=document.createElementNS(NS,'text');
    t.setAttribute('x',(obj.x1+obj.x2)/2);t.setAttribute('y',(obj.y1+obj.y2)/2-7);
    t.setAttribute('text-anchor','middle');t.setAttribute('font-size','11');
    t.setAttribute('font-family','Arial');t.setAttribute('fill','#ddaa00');t.setAttribute('font-weight','bold');
    t.textContent=obj.val; g.appendChild(t);
    g.setAttribute('data-id',obj.id); g.style.cursor='pointer';
    g.addEventListener('click',()=>selectObj(obj.id));
    lObj().appendChild(g); return;
  }

  if (el) {
    el.setAttribute('data-id',obj.id); el.style.cursor='pointer';
    el.addEventListener('click',()=>selectObj(obj.id));
    lObj().appendChild(el);
  }
}

// ─────────────────────────────────────────────
//  SELECTION
// ─────────────────────────────────────────────
function selectAt(x,y) {
  const hit = objs.slice().reverse().find(o=>hitTest(o,x,y));
  selectObj(hit?hit.id:null);
}

function selectObj(id) {
  selId=id; lSel().innerHTML='';
  document.getElementById('props-body').innerHTML = id
    ? buildProps(objs.find(o=>o.id===id)) : 'No selection';
  if(!id) return;
  highlightSel(id);
}

function highlightSel(id) {
  lSel().innerHTML='';
  const obj=objs.find(o=>o.id===id); if(!obj) return;
  const bb=getBB(obj); if(!bb) return;
  const pad=6;
  const r=document.createElementNS(NS,'rect');
  r.setAttribute('x',bb.x-pad);r.setAttribute('y',bb.y-pad);
  r.setAttribute('width',bb.w+pad*2);r.setAttribute('height',bb.h+pad*2);
  r.setAttribute('fill','none');r.setAttribute('stroke','#ff9900');r.setAttribute('stroke-width','1.5');
  r.setAttribute('stroke-dasharray','8,4');r.setAttribute('pointer-events','none');
  lSel().appendChild(r);
  [[bb.x-pad,bb.y-pad],[bb.x+bb.w+pad,bb.y-pad],
   [bb.x-pad,bb.y+bb.h+pad],[bb.x+bb.w+pad,bb.y+bb.h+pad]].forEach(([hx,hy])=>{
    const h=document.createElementNS(NS,'rect');
    h.setAttribute('x',hx-4);h.setAttribute('y',hy-4);h.setAttribute('width','8');h.setAttribute('height','8');
    h.setAttribute('fill','#ff9900');h.setAttribute('pointer-events','none');
    lSel().appendChild(h);
  });
}

function buildProps(obj) {
  if (!obj) return 'No selection';
  const ld=LD[obj.lyr]||{n:obj.lyr};
  let h=`<div style="margin-bottom:4px"><span style="color:#e8a020;font-size:9px">${ld.n}</span></div>`;
  if(obj.type==='rect') h+=`<div style="font-size:9px">Size: <b>${Math.round(obj.w)}m × ${Math.round(obj.h)}m</b></div>`;
  if(obj.type==='text') h+=`<input class="rp-in" value="${obj.text}" oninput="updateObjTxt('${obj.id}',this.value)" style="margin-top:4px">`;
  h+=`<button onclick="delSel()" style="margin-top:8px;width:100%;padding:4px;background:rgba(255,68,85,.15);border:1px solid rgba(255,68,85,.3);border-radius:3px;color:#ff4455;font-size:9px;cursor:pointer;font-family:Courier New">DELETE OBJECT</button>`;
  return h;
}

function updateObjTxt(id,val){ const o=objs.find(x=>x.id===id);if(o){o.text=val;renderAll();} }

function hitTest(obj,x,y) {
  const bb=getBB(obj); if(!bb) return false;
  return x>=bb.x-8&&x<=bb.x+bb.w+8&&y>=bb.y-8&&y<=bb.y+bb.h+8;
}

function getBB(obj) {
  if(obj.type==='rect') return{x:obj.x,y:obj.y,w:obj.w,h:obj.h};
  if(obj.type==='circle') return{x:obj.cx-obj.r,y:obj.cy-obj.r,w:obj.r*2,h:obj.r*2};
  if(obj.type==='polyline'&&obj.pts?.length){
    const xs=obj.pts.map(p=>p.x),ys=obj.pts.map(p=>p.y);
    const x=Math.min(...xs),y=Math.min(...ys);
    return{x,y,w:Math.max(...xs)-x,h:Math.max(...ys)-y};
  }
  if(obj.type==='text') return{x:obj.x,y:obj.y-14,w:100,h:16};
  if(obj.type==='dim'){
    const x=Math.min(obj.x1,obj.x2),y=Math.min(obj.y1,obj.y2);
    return{x,y,w:Math.max(Math.abs(obj.x2-obj.x1),10),h:Math.max(Math.abs(obj.y2-obj.y1),10)};
  }
  return null;
}

// ─────────────────────────────────────────────
//  UNDO / REDO / DELETE / CLEAR
// ─────────────────────────────────────────────
function saveU(){ undoStk.push(JSON.stringify(objs)); if(undoStk.length>60)undoStk.shift(); redoStk=[]; }
function doUndo(){ if(!undoStk.length)return; redoStk.push(JSON.stringify(objs)); objs=JSON.parse(undoStk.pop()); selId=null;lSel().innerHTML='';selectObj(null);renderAll(); }
function doRedo(){ if(!redoStk.length)return; undoStk.push(JSON.stringify(objs)); objs=JSON.parse(redoStk.pop()); renderAll(); }
function delSel(){ if(!selId)return; saveU(); objs=objs.filter(o=>o.id!==selId); selId=null;lSel().innerHTML='';selectObj(null);renderAll(); }
function clearAll(){ if(!confirm('Clear all drawing objects?'))return; saveU(); objs=[];selId=null;lSel().innerHTML='';selectObj(null);renderAll(); }

// ─────────────────────────────────────────────
//  ZOOM / PAN / FIT
// ─────────────────────────────────────────────
function applyZoom(svgX, svgY, clientX, clientY) {
  const wrap=document.getElementById('canvas-wrap');
  wrap.style.transform=`scale(${zoom})`;
  wrap.style.transformOrigin='top left';
  const scroll=document.getElementById('canvas-scroll');
  scroll.scrollLeft = svgX*zoom - (clientX - scroll.getBoundingClientRect().left);
  scroll.scrollTop  = svgY*zoom - (clientY - scroll.getBoundingClientRect().top);
  document.getElementById('sb-zoom').textContent=Math.round(zoom*100)+'%';
}

function zoomStep(f) {
  zoom=Math.min(4,Math.max(.15,zoom*f));
  document.getElementById('canvas-wrap').style.transform=`scale(${zoom})`;
  document.getElementById('canvas-wrap').style.transformOrigin='top left';
  document.getElementById('sb-zoom').textContent=Math.round(zoom*100)+'%';
}

function fitView() {
  const area=document.getElementById('canvas-area');
  const aw=area.clientWidth, ah=area.clientHeight;
  zoom = Math.min(aw/SW, ah/SH)*0.95;
  const wrap=document.getElementById('canvas-wrap');
  wrap.style.transform=`scale(${zoom})`;
  wrap.style.transformOrigin='top left';
  // Centre scroll
  const scroll=document.getElementById('canvas-scroll');
  scroll.scrollLeft=(SW*zoom-aw)/2;
  scroll.scrollTop=(SH*zoom-ah)/2;
  document.getElementById('sb-zoom').textContent=Math.round(zoom*100)+'%';
}
function zoomFit(){ fitView(); }

// ─────────────────────────────────────────────
//  SNAP / GRID TOGGLE
// ─────────────────────────────────────────────
function toggleSnap(){
  snapOn=!snapOn;
  document.getElementById('b-snap').textContent='Snap '+(snapOn?'ON':'OFF');
}
function toggleGrid(){
  gridOn=!gridOn;
  document.getElementById('b-grid').textContent='Grid '+(gridOn?'ON':'OFF');
  buildGrid();
}

// ─────────────────────────────────────────────
//  KEYBOARD
// ─────────────────────────────────────────────
document.addEventListener('keydown',ev=>{
  if(['INPUT','TEXTAREA','SELECT'].includes(ev.target.tagName))return;
  const k=ev.key.toLowerCase();
  const km={'v':'sel','l':'line','r':'rect','p':'poly','c':'circle','t':'text','d':'dim','f':'fit'};
  if(km[k]){ if(k==='f')fitView(); else setTool(km[k]); }
  if(k==='escape'){drawing=false;dpts=[];dStart=null;lTemp().innerHTML='';setTool('sel');}
  if(k==='delete'||k==='backspace'){ev.preventDefault();delSel();}
  if((ev.ctrlKey||ev.metaKey)&&k==='z'){ev.preventDefault();doUndo();}
  if((ev.ctrlKey||ev.metaKey)&&k==='y'){ev.preventDefault();doRedo();}
});

// ─────────────────────────────────────────────
//  DRAG FROM PALETTE
// ─────────────────────────────────────────────
document.querySelectorAll('.item').forEach(el=>{
  el.setAttribute('draggable','true');
  el.addEventListener('dragstart',ev=>{
    window._dragLyr=el.id.replace('p-','');
    ev.dataTransfer?.setData('text/plain',window._dragLyr);
  });
});

// ─────────────────────────────────────────────
//  EXPORT — SVG
// ─────────────────────────────────────────────
function exportSVG(){
  const s=svg();
  const ser=new XMLSerializer();
  const str='<?xml version="1.0" encoding="UTF-8"?>\n'+ser.serializeToString(s);
  const blob=new Blob([str],{type:'image/svg+xml'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download=(document.getElementById('f-proj')?.value||'BESS_Site').replace(/\s+/g,'_')+'_SitePlan.svg';
  a.click();
}

// ─────────────────────────────────────────────
//  EXPORT — DXF
// ─────────────────────────────────────────────
function exportDXF(){
  const proj=document.getElementById('f-proj')?.value||'BESS_PROJECT';
  const scaleStr=document.getElementById('f-scale')?.value||'1:1000';
  const scNum=parseInt(scaleStr.split(':')[1])||1000;

  const layerColorMap={site_boundary:1,fence:7,vegetation:3,wetlands:5,pond:5,
    access_road:2,access_gate:7,fire_staging:1,battery:5,mv_transformer:6,
    pcs:2,substation:6,relay:3,scada:4,vcb:1,busbar:7,meter:3,cable:2,
    annotation:7,dimension:2};

  let dxf='999\nDDE BESS Site Plan Export\n0\nSECTION\n2\nHEADER\n';
  dxf+='9\n$ACADVER\n1\nAC1021\n9\n$INSUNITS\n70\n6\n9\n$MEASUREMENT\n70\n1\n';
  dxf+='0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n'+Object.keys(LD).length+'\n';
  Object.entries(LD).forEach(([k,v])=>{
    dxf+=`0\nLAYER\n2\n${k.toUpperCase()}\n70\n0\n62\n${layerColorMap[k]||7}\n6\nCONTINUOUS\n`;
  });
  dxf+='0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n';

  const M=v=>(v*scNum/1000).toFixed(4);
  const MY=v=>((SH-v)*scNum/1000).toFixed(4);

  objs.forEach(obj=>{
    const ln=obj.lyr.toUpperCase();
    if(obj.type==='polyline'){
      dxf+=`0\nLWPOLYLINE\n8\n${ln}\n90\n${obj.pts.length}\n70\n${obj.closed?1:0}\n`;
      obj.pts.forEach(p=>{dxf+=`10\n${M(p.x)}\n20\n${MY(p.y)}\n`;});
    } else if(obj.type==='rect'){
      dxf+=`0\nLWPOLYLINE\n8\n${ln}\n90\n4\n70\n1\n`;
      [[obj.x,obj.y],[obj.x+obj.w,obj.y],[obj.x+obj.w,obj.y+obj.h],[obj.x,obj.y+obj.h]]
        .forEach(([x,y])=>{dxf+=`10\n${M(x)}\n20\n${MY(y)}\n`;});
      const lbmap={battery:'BESS CONTAINER',mv_transformer:'MV TRANSFORMER',pcs:'PCS/INVERTER'};
      if(lbmap[obj.lyr]) dxf+=`0\nTEXT\n8\n${ln}\n10\n${M(obj.x+obj.w/2)}\n20\n${MY(obj.y+obj.h/2)}\n30\n0\n40\n3\n1\n${lbmap[obj.lyr]}\n72\n1\n11\n${M(obj.x+obj.w/2)}\n21\n${MY(obj.y+obj.h/2)}\n`;
    } else if(obj.type==='circle'){
      dxf+=`0\nCIRCLE\n8\n${ln}\n10\n${M(obj.cx)}\n20\n${MY(obj.cy)}\n40\n${M(obj.r)}\n`;
    } else if(obj.type==='text'){
      dxf+=`0\nTEXT\n8\nANNOTATION\n10\n${M(obj.x)}\n20\n${MY(obj.y)}\n30\n0\n40\n4\n1\n${obj.text}\n`;
    } else if(obj.type==='dim'){
      dxf+=`0\nLINE\n8\nDIMENSION\n10\n${M(obj.x1)}\n20\n${MY(obj.y1)}\n11\n${M(obj.x2)}\n21\n${MY(obj.y2)}\n`;
      const mx=(parseFloat(M(obj.x1))+parseFloat(M(obj.x2)))/2;
      const my=(parseFloat(MY(obj.y1))+parseFloat(MY(obj.y2)))/2;
      dxf+=`0\nTEXT\n8\nDIMENSION\n10\n${mx}\n20\n${my+2}\n30\n0\n40\n3\n1\n${obj.val}\n72\n1\n11\n${mx}\n21\n${my+2}\n`;
    }
  });
  dxf+='0\nENDSEC\n0\nEOF\n';

  dl(new Blob([dxf],{type:'application/dxf'}), proj.replace(/\s+/g,'_')+'_SitePlan.dxf');
  setTimeout(()=>{
    if(confirm('DXF exported!\n\nTo convert to native .DWG:\n→ Open in AutoCAD and Save As .dwg\n→ Or use free ODA File Converter\n\nOpen ODA download page?'))
      window.open('https://www.opendesign.com/guestfiles/oda_file_converter','_blank');
  },400);
}

function dl(blob, name){ const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click(); }

// ─────────────────────────────────────────────
//  EXPORT — PDF (SunStripe Template)
// ─────────────────────────────────────────────
function exportPDF(){
  const {jsPDF}=window.jspdf;
  // 17"×11" landscape
  const doc=new jsPDF({orientation:'landscape',unit:'mm',format:[431.8,279.4]});
  const PW=431.8, PH=279.4;
  const scX=PW/SW, scY=PH/SH;
  const mm=v=>v*scX, mmY=v=>v*scY;

  function hexRGB(hex){
    const v=hex.replace('#','');
    return[parseInt(v.slice(0,2),16)||0,parseInt(v.slice(2,4),16)||0,parseInt(v.slice(4,6),16)||0];
  }

  // White background
  doc.setFillColor(255,255,255); doc.rect(0,0,PW,PH,'F');

  // Outer border
  doc.setDrawColor(0); doc.setLineWidth(.5);
  doc.rect(mm(12),mmY(12),mm(SW-24),mmY(SH-24));

  // Drawing area
  doc.setFillColor(249,250,251); doc.setLineWidth(.3);
  doc.rect(mm(DA_X1),mmY(DA_Y1),mm(DA_W),mmY(DA_H),'FD');

  // Copyright
  doc.setFontSize(3.8); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text('THIS DRAWING IS THE PROPERTY OF SUNSTRIPE, Inc. ANY REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN PERMISSION OF SUNSTRIPE, Inc IS PROHIBITED.',
    mm(DA_X1+4),mmY(DA_Y1-5));

  // Bottom note
  doc.setFontSize(5.5); doc.setFont('helvetica','bolditalic');
  doc.text('FOR INFORMATION PURPOSES ONLY - NOT FOR CONSTRUCTION',PW/2,mmY(SH-MB+14),{align:'center'});

  // ── Title Block ──────────────────────────────
  const TX=TB_X, TW2=TB_TW;
  let cy=DA_Y1;

  doc.setFillColor(255,255,255); doc.setLineWidth(.3);
  doc.rect(mm(TX),mmY(cy),mm(TW2),mmY(DA_H),'FD');

  // North arrow
  const NAH=90;
  doc.setFillColor(245,245,245); doc.rect(mm(TX),mmY(cy),mm(TW2),mmY(NAH),'F');
  const NCX2=mm(TX+TW2/2), NCY2=mmY(cy+NAH/2), NR2=mm(32);
  doc.setDrawColor(0); doc.setLineWidth(.4);
  doc.circle(NCX2,NCY2,NR2);
  // North needle
  doc.setFillColor(0,0,0);
  doc.triangle(NCX2-mm(9),NCY2+mmY(12),NCX2,NCY2-mmY(NR2-3),NCX2+mm(9),NCY2+mmY(12),'F');
  doc.setFillColor(255,255,255);
  doc.triangle(NCX2-mm(9),NCY2+mmY(12),NCX2,NCY2-mmY(NR2-3),NCX2,NCY2+mmY(6),'F');
  doc.setFontSize(10); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text('N',NCX2,NCY2-NR2-2,{align:'center'});
  cy+=NAH; doc.setDrawColor(0); doc.setLineWidth(.5); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Legends header
  const LHH=16;
  doc.setFillColor(232,232,232); doc.rect(mm(TX),mmY(cy),mm(TW2),mmY(LHH),'F');
  doc.setFontSize(7); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text('LEGENDS',mm(TX+TW2/2),mmY(cy+11),{align:'center'});
  cy+=LHH;

  const legPDF=[
    ['sb','SITE BOUNDARY','#ff3333'],['fence','FENCE','#333'],
    ['veg','VEGETATION','#88cc44'],['wet','WETLANDS','#4499cc'],
    ['pond','STORM WATER POND','#2266aa'],['fire','FIRE BATTERY ACCESS ROAD','#cc7733'],
    ['road','ACCESS ROAD','#aa9966'],['gate','ACCESS GATE','#444'],
    ['batt','BATTERY CONTAINER','#ddeeff'],['mvt','MV TRANSFORMER','#eeeef8'],
    ['fstg','FIRE STAGING AREA','#dd3333'],
  ];
  const swW=mm(48), swH=mmY(17), lgX=mm(TX+3), lgTX=mm(TX+52);
  legPDF.forEach(([sym,label,col])=>{
    doc.setLineWidth(.15); doc.setDrawColor(200,200,200); doc.rect(mm(TX),mmY(cy),mm(TW2),swH);
    const [r2,g2,b2]=hexRGB(col);
    doc.setFillColor(r2,g2,b2); doc.setDrawColor(r2,g2,b2); doc.setLineWidth(.8);
    if(sym==='sb'){doc.setLineWidth(2);doc.line(lgX,mmY(cy)+swH/2,lgX+swW,mmY(cy)+swH/2);}
    else if(sym==='fence'){doc.setLineDashPattern([2,1.5],0);doc.line(lgX,mmY(cy)+swH/2,lgX+swW,mmY(cy)+swH/2);doc.setLineDashPattern([],0);}
    else{doc.rect(lgX,mmY(cy)+1,swW,swH-2,'FD');}
    doc.setFontSize(5.5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
    doc.text(label,lgTX,mmY(cy)+swH/2+1.5);
    cy+=17;
  });
  doc.setDrawColor(0); doc.setLineWidth(.5); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Project name
  const PNH=88;
  doc.setFontSize(12); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text(document.getElementById('f-proj')?.value||'PROJECT NAME',mm(TX+TW2/2),mmY(cy+30),{align:'center'});
  doc.setFontSize(10);
  doc.text((document.getElementById('f-pct')?.value||'30')+'% DESIGN',mm(TX+TW2/2),mmY(cy+48),{align:'center'});
  doc.setFontSize(6.5); doc.setFont('helvetica','normal'); doc.setTextColor(80);
  doc.text(document.getElementById('f-client')?.value||'CLIENT',mm(TX+TW2/2),mmY(cy+63),{align:'center'});
  doc.text(document.getElementById('f-ref')?.value||'REF',mm(TX+TW2/2),mmY(cy+75),{align:'center'});
  cy+=PNH; doc.setDrawColor(0); doc.setLineWidth(.5); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Revision table
  const RVHH=14;
  doc.setFillColor(232,232,232); doc.rect(mm(TX),mmY(cy),mm(TW2),mmY(RVHH),'F');
  doc.setFontSize(6); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  const rc3=[{t:'REV',w:22},{t:'DESCRIPTION',w:TW2-100},{t:'BY',w:30},{t:'DATE',w:48}];
  let rcx3=TX; rc3.forEach(col=>{
    doc.rect(mm(rcx3),mmY(cy),mm(col.w),mmY(RVHH));
    doc.text(col.t,mm(rcx3+col.w/2),mmY(cy+10),{align:'center'});
    rcx3+=col.w;
  });
  cy+=RVHH;
  revData.forEach(row=>{
    const RVRH=13;
    let rcx4=TX; rc3.forEach((col,ci)=>{
      doc.setLineWidth(.15); doc.setDrawColor(200,200,200);
      doc.rect(mm(rcx4),mmY(cy),mm(col.w),mmY(RVRH));
      doc.setFontSize(5.5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
      const vals=[row.rev,row.desc,row.by,row.date];
      if(vals[ci]) doc.text(vals[ci],mm(rcx4+2),mmY(cy+9));
      rcx4+=col.w;
    });
    cy+=13;
  });
  cy+=2; doc.setDrawColor(0); doc.setLineWidth(.5); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Sunstripe brand
  const BH=50;
  doc.setFontSize(13); doc.setFont('helvetica','bold'); doc.setTextColor(221,34,0);
  doc.text('SunStripe',mm(TX+TW2/2),mmY(cy+22),{align:'center'});
  doc.setFontSize(5.5); doc.setFont('helvetica','normal'); doc.setTextColor(80);
  doc.text('Trusted Clean Energy Partners',mm(TX+TW2/2),mmY(cy+33),{align:'center'});
  doc.text('6363 N State Highway 161, Ste 250 Irving, TX 75038',mm(TX+TW2/2),mmY(cy+43),{align:'center'});
  cy+=BH; doc.setDrawColor(0); doc.setLineWidth(.5); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Sheet name
  doc.setFontSize(5.5); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text('SHEET NAME:',mm(TX+3),mmY(cy+11));
  doc.setFontSize(8);
  doc.text(document.getElementById('f-sname')?.value||'CIVIL SITE PLAN',mm(TX+TW2/2),mmY(cy+24),{align:'center'});
  cy+=34; doc.setLineWidth(.3); doc.setDrawColor(180,180,180); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Lat/long
  doc.setFontSize(5.5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
  doc.text('LAT/LONG:',mm(TX+3),mmY(cy+11));
  doc.text(document.getElementById('f-ll')?.value||'XX/XX',mm(TX+52),mmY(cy+11));
  cy+=17; doc.setLineWidth(.3); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // DRWN row
  const dc4=[{l:'DRWN',v:document.getElementById('f-drwn')?.value||'XX',w:TW2*.22},
             {l:'REVW',v:document.getElementById('f-revw')?.value||'XX',w:TW2*.22},
             {l:'APPRVD',v:document.getElementById('f-apprvd')?.value||'XX',w:TW2*.28},
             {l:'SIZE',v:'11"X17"',w:TW2*.28}];
  let dx4=TX;
  doc.setFontSize(6); doc.setFont('helvetica','bold');
  dc4.forEach(col=>{
    doc.setLineWidth(.2); doc.setDrawColor(180,180,180); doc.rect(mm(dx4),mmY(cy),mm(col.w),mmY(22));
    doc.text(col.l,mm(dx4+col.w/2),mmY(cy+9),{align:'center'});
    doc.setFont('helvetica','normal'); doc.setFontSize(6.5);
    doc.text(col.v,mm(dx4+col.w/2),mmY(cy+18),{align:'center'});
    doc.setFont('helvetica','bold'); doc.setFontSize(6);
    dx4+=col.w;
  });
  cy+=22; doc.setDrawColor(0); doc.setLineWidth(.5); doc.line(mm(TX),mmY(cy),mm(TX+TW2),mmY(cy));

  // Sheet No
  doc.setFontSize(5.5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
  doc.text('SHEET:',mm(TX+3),mmY(cy+11));
  doc.setFontSize(16); doc.setFont('helvetica','bold');
  doc.text(document.getElementById('f-sno')?.value||'S-01',mm(TX+TW2/2),mmY(DA_Y1+DA_H-10),{align:'center'});

  // ── Scale bar in PDF ──────────────────────────
  const sbX2=mm(DA_X1+20), sbY2=mmY(DA_Y2-28);
  const scT=document.getElementById('f-scale')?.value||'1:1000';
  doc.setFontSize(6); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text('SCALE  '+scT, sbX2, sbY2-2);
  for(let i=0;i<5;i++){
    doc.setFillColor(i%2===0?0:255,i%2===0?0:255,i%2===0?0:255);
    doc.rect(sbX2+mm(i*30),sbY2,mm(30),mmY(9),'FD');
  }
  ['0m','30m','60m','90m','120m','150m'].forEach((l,i)=>{
    doc.setFontSize(5); doc.setFont('helvetica','normal');
    doc.text(l,sbX2+mm(i*30),sbY2+mmY(17),{align:'center'});
  });

  // ── Draw objects ──────────────────────────────
  objs.forEach(obj=>{
    const ld2=LD[obj.lyr]||LD.site_boundary;
    const [sr,sg,sb2]=hexRGB(ld2.c);
    doc.setDrawColor(sr,sg,sb2); doc.setLineWidth(ld2.lw*0.28);
    if(ld2.fill&&ld2.fill!=='none'){
      const [fr,fg,fb]=hexRGB(ld2.fill);
      doc.setFillColor(fr,fg,fb);
    }
    if(obj.type==='polyline'){
      if(obj.pts.length<2)return;
      for(let i=0;i<obj.pts.length-1;i++)
        doc.line(mm(obj.pts[i].x),mmY(obj.pts[i].y),mm(obj.pts[i+1].x),mmY(obj.pts[i+1].y));
      if(obj.closed) doc.line(mm(obj.pts[obj.pts.length-1].x),mmY(obj.pts[obj.pts.length-1].y),mm(obj.pts[0].x),mmY(obj.pts[0].y));
    } else if(obj.type==='rect'){
      if(ld2.fill&&ld2.fill!=='none') doc.rect(mm(obj.x),mmY(obj.y),mm(obj.w),mmY(obj.h),'FD');
      else doc.rect(mm(obj.x),mmY(obj.y),mm(obj.w),mmY(obj.h));
      const lbm={battery:'BESS',mv_transformer:'MVT',pcs:'PCS'};
      if(lbm[obj.lyr]){
        doc.setFontSize(5); doc.setFont('helvetica','bold'); doc.setTextColor(sr,sg,sb2);
        doc.text(lbm[obj.lyr],mm(obj.x+obj.w/2),mmY(obj.y+obj.h/2+1.5),{align:'center'});
      }
    } else if(obj.type==='circle'){
      doc.circle(mm(obj.cx),mmY(obj.cy),mm(obj.r));
    } else if(obj.type==='text'){
      doc.setFontSize(6); doc.setFont('helvetica','normal'); doc.setTextColor(0);
      doc.text(obj.text,mm(obj.x),mmY(obj.y));
    } else if(obj.type==='dim'){
      doc.setDrawColor(221,170,0); doc.setLineWidth(.25);
      doc.line(mm(obj.x1),mmY(obj.y1),mm(obj.x2),mmY(obj.y2));
      doc.setFontSize(5.5); doc.setTextColor(170,120,0);
      doc.text(obj.val,mm((obj.x1+obj.x2)/2),mmY((obj.y1+obj.y2)/2)-1.5,{align:'center'});
    }
  });

  const fname=(document.getElementById('f-proj')?.value||'BESS_Site').replace(/\s+/g,'_')+'_SitePlan.pdf';
  doc.save(fname);
}

</script>
</body>
</html>
"""

def page_canvas():
    st.markdown("""
    <style>
    .block-container{padding-top:0.5rem!important;padding-bottom:0!important;max-width:100%!important}
    iframe{border:none!important;display:block}
    </style>""", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0 4px">
      <div>
        <div class="page-title" style="margin-bottom:0">🖊 BESS Engineering CAD Canvas</div>
        <div class="page-sub" style="margin-bottom:0">AutoCAD-style drawing · SunStripe title block template · SVG / DXF / DWG / PDF export</div>
      </div>
      <div style="font-size:11px;color:#8890a4;text-align:right">
        <span style="color:#00d4ff">V</span>=Select &nbsp;
        <span style="color:#00d4ff">L</span>=Line &nbsp;
        <span style="color:#00d4ff">R</span>=Rect &nbsp;
        <span style="color:#00d4ff">P</span>=Poly &nbsp;
        <span style="color:#00d4ff">T</span>=Text &nbsp;
        <span style="color:#00d4ff">D</span>=Dim &nbsp;
        <span style="color:#00d4ff">F</span>=Fit &nbsp;
        <span style="color:#00d4ff">Enter</span>=Commit poly &nbsp;
        <span style="color:#00d4ff">Ctrl+Z</span>=Undo &nbsp;
        <span style="color:#00d4ff">Del</span>=Delete
      </div>
    </div>
    """, unsafe_allow_html=True)
    components.html(CAD_HTML, height=760, scrolling=False)

# ═══════════════════════════  COMPONENT DB  ══════════════════════════════════
def page_components():
    st.markdown('<div class="page-title">🔋 Component Database</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Searchable catalogue · Specifications · Cost data</div>', unsafe_allow_html=True)
    c1,c2,c3=st.columns([3,2,2])
    search=c1.text_input("Search",placeholder="battery, transformer…",label_visibility="collapsed")
    cats=["All"]+sorted(set(v["category"]for v in COMPONENT_CATALOGUE.values()))
    cat_f=c2.selectbox("Category",cats,label_visibility="collapsed")
    sort_by=c3.selectbox("Sort",["Name","Category","Cost ↑","Cost ↓"],label_visibility="collapsed")
    m1,m2,m3=st.columns(3)
    m1.metric("Component Types",len(COMPONENT_CATALOGUE)); m2.metric("Categories",len(cats)-1); m3.metric("Avg Unit Cost",f"${sum(v['unit_cost_usd']for v in COMPONENT_CATALOGUE.values())//len(COMPONENT_CATALOGUE):,.0f}")
    items=[{"key":k,**v}for k,v in COMPONENT_CATALOGUE.items()]
    if search: items=[i for i in items if search.lower()in i["label"].lower()or search.lower()in i["category"].lower()]
    if cat_f!="All": items=[i for i in items if i["category"]==cat_f]
    sk={"Name":lambda x:x["label"],"Category":lambda x:x["category"],"Cost ↑":lambda x:x["unit_cost_usd"],"Cost ↓":lambda x:-x["unit_cost_usd"]}
    items.sort(key=sk[sort_by])
    for item in items:
        with st.expander(f'{item["icon"]}  {item["label"]}  —  {item["category"]}'):
            cA,cB=st.columns([2,1])
            with cA:
                rows="".join(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04)"><span style="font-size:11px;color:#8890a4">{k.replace("_"," ").title()}</span><span style="font-family:JetBrains Mono;font-size:11px;color:#e8eaf0;background:#1a1e28;padding:2px 8px;border-radius:4px">{v}</span></div>'for k,v in item["specs"].items())
                st.markdown(f'<div>{rows}</div>',unsafe_allow_html=True)
            with cB:
                st.markdown(f'<div class="metric-tile"><div class="metric-value" style="color:{item["color"]}">${item["unit_cost_usd"]:,}</div><div class="metric-label">Unit Cost (USD)</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Export Catalogue</div>',unsafe_allow_html=True)
    df=pd.DataFrame([{"Component":v["label"],"Category":v["category"],"Unit Cost":v["unit_cost_usd"]}for v in COMPONENT_CATALOGUE.values()])
    st.download_button("⬇️ Download CSV",df.to_csv(index=False),"bess_components.csv","text/csv")
    st.dataframe(df,use_container_width=True,hide_index=True)

# ═══════════════════════════  PROJECT MANAGER  ═══════════════════════════════
def page_projects():
    P=st.session_state.projects
    st.markdown('<div class="page-title">📋 Project Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Milestones · Gantt · Budget · Create projects</div>', unsafe_allow_html=True)
    t1,t2,t3,t4=st.tabs(["Overview","Gantt Chart","Edit Project","New Project"])
    bm={"Planning":"badge-purple","Design":"badge-blue","Procurement":"badge-amber","Construction":"badge-amber","Commissioning":"badge-green","Operational":"badge-green"}
    with t1:
        for i,p in enumerate(P):
            done=sum(1 for m in p["milestones"]if m["done"])
            with st.expander(f'**{p["name"]}** — {p["status"]}',expanded=(i==0)):
                c1,c2,c3,c4=st.columns(4)
                c1.metric("Capacity",f'{p["capacity_mwh"]} MWh'); c2.metric("Power",f'{p["power_mw"]} MW')
                c3.metric("Budget Used",f'{round(p["spent_usd"]/p["budget_usd"]*100,1)}%',f'${p["spent_usd"]/1e6:.2f}M of ${p["budget_usd"]/1e6:.1f}M')
                c4.metric("Milestones",f'{done}/{len(p["milestones"])}',f'{p["progress_pct"]}% done')
                st.markdown('<div class="section-title">Milestones</div>',unsafe_allow_html=True)
                for m in p["milestones"]:
                    ic="✅"if m["done"]else"⏳"; co="#00e5a0"if m["done"]else"#ffb347"
                    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04)"><span>{ic}</span><span style="font-size:12px;color:#e8eaf0;flex:1">{m["name"]}</span><span style="font-family:JetBrains Mono;font-size:10px;color:{co}">{m["date"]}</span></div>',unsafe_allow_html=True)
                if p["notes"]: st.info(f'📝 {p["notes"]}')
    with t2:
        rows=[]
        for p in P:
            for m in p["milestones"]: rows.append({"Project":p["name"],"Task":m["name"],"Start":p["start_date"],"Finish":m["date"],"Status":"Complete"if m["done"]else p["status"]})
        df=pd.DataFrame(rows)
        sc2={"Complete":"#00e5a0","Design":"#00d4ff","Procurement":"#ffb347","Planning":"#555d72","Construction":"#a78bfa","Commissioning":"#00e5a0"}
        fig=px.timeline(df,x_start="Start",x_end="Finish",y="Project",color="Status",color_discrete_map=sc2,hover_data=["Task"])
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(**PT,height=380,xaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)"),yaxis=dict(showgrid=False),legend=dict(bgcolor="rgba(0,0,0,0)",orientation="h",y=1.1))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.dataframe(df[["Project","Task","Finish","Status"]].rename(columns={"Finish":"Target Date"}),use_container_width=True,hide_index=True)
    with t3:
        sn2=st.selectbox("Select project",[p["name"]for p in P],key="edit_proj_sel")
        proj=next(p for p in P if p["name"]==sn2); idx=P.index(proj)
        with st.form("edit_proj"):
            c1,c2=st.columns(2)
            nn=c1.text_input("Name",proj["name"]); nc=c2.text_input("Client",proj["client"])
            nl=c1.text_input("Location",proj["location"]); ne=c2.text_input("Engineer",proj["engineer"])
            ns=st.selectbox("Status",PROJECT_STATUSES,index=PROJECT_STATUSES.index(proj["status"]),key="edit_status_sel")
            c3,c4=st.columns(2)
            nca=c3.number_input("Capacity (MWh)",value=float(proj["capacity_mwh"]),step=0.5); npm=c4.number_input("Power (MW)",value=float(proj["power_mw"]),step=0.5)
            nch=c3.selectbox("Chemistry",["LFP","NMC","NCA","LTO"],index=["LFP","NMC","NCA","LTO"].index(proj["chemistry"]))
            c5,c6=st.columns(2)
            nb=c5.number_input("Budget (USD)",value=proj["budget_usd"],step=10000); nsp=c6.number_input("Spent (USD)",value=proj["spent_usd"],step=1000)
            npr=st.slider("Progress (%)",0,100,proj["progress_pct"],key="edit_prog_slider"); nno=st.text_area("Notes",proj["notes"],key="edit_notes_ta")
            if st.form_submit_button("💾 Save"):
                P[idx].update({"name":nn,"client":nc,"location":nl,"engineer":ne,"status":ns,"capacity_mwh":nca,"power_mw":npm,"chemistry":nch,"budget_usd":nb,"spent_usd":nsp,"progress_pct":npr,"notes":nno})
                st.session_state.projects=P; st.success("✓ Saved")
    with t4:
        with st.form("new_proj"):
            c1,c2=st.columns(2)
            an=c1.text_input("Name *"); ac2=c2.text_input("Client *")
            al2=c1.text_input("Location"); ae=c2.text_input("Engineer")
            ast2=st.selectbox("Status",PROJECT_STATUSES,key="new_status_sel")
            c3,c4=st.columns(2)
            aca=c3.number_input("Capacity (MWh)",0.1,1000.0,5.0,step=0.5); apm=c4.number_input("Power (MW)",0.1,1000.0,2.5,step=0.5)
            ach=c3.selectbox("Chemistry",["LFP","NMC","NCA","LTO"])
            c5,c6=st.columns(2)
            ab=c5.number_input("Budget (USD)",100000,100000000,4000000,step=50000); as2=c6.date_input("Start Date",date.today()); ae2=c5.date_input("End Date")
            ano=st.text_area("Notes",key="new_notes_ta")
            if st.form_submit_button("🚀 Create Project"):
                if not an or not ac2: st.error("Name and client are required.")
                else:
                    np2={"id":f"PRJ-{len(P)+1:03d}","name":an,"client":ac2,"location":al2,"engineer":ae,"capacity_mwh":aca,"power_mw":apm,"status":ast2,"chemistry":ach,"application":"","rack_count":0,"pcs_count":0,"budget_usd":ab,"spent_usd":0,"start_date":str(as2),"end_date":str(ae2),"progress_pct":0,"notes":ano,"milestones":[{"name":ms,"date":str(ae2),"done":False}for ms in["Design Freeze","Equipment Order","Civil Works Start","Equipment Delivery","Commissioning Start","Commercial Operation"]]}
                    st.session_state.projects.append(np2); st.success(f"✓ Created {np2['id']}: {an}")

# ═══════════════════════════  REPORTS  ═══════════════════════════════════════
def page_reports():
    P=st.session_state.projects
    st.markdown('<div class="page-title">📊 Reports & Export</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Technical reports · BoM · Cost analysis · Downloads</div>', unsafe_allow_html=True)
    t1,t2,t3,t4=st.tabs(["Summary Report","Bill of Materials","Cost Analysis","Data Export"])
    with t1:
        sel=st.selectbox("Project",["All Projects"]+[p["name"]for p in P],key="report_proj_sel")
        rps=P if sel=="All Projects" else[p for p in P if p["name"]==sel]
        tmh=sum(p["capacity_mwh"]for p in rps); tmw=sum(p["power_mw"]for p in rps)
        tbd=sum(p["budget_usd"]for p in rps); tsp=sum(p["spent_usd"]for p in rps)
        st.markdown(f'<div class="bess-card-accent"><div style="font-family:JetBrains Mono;font-size:11px;color:#555d72;margin-bottom:8px">GENERATED: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div><div style="font-size:20px;font-weight:600;color:#e8eaf0">DDE BESS Engineering Report</div><div style="font-size:13px;color:#8890a4;margin-top:4px">{sel} · {len(rps)} project(s)</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:20px"><div><div style="font-size:10px;color:#555d72;text-transform:uppercase">Capacity</div><div style="font-family:JetBrains Mono;font-size:22px;color:#00d4ff">{tmh} MWh</div></div><div><div style="font-size:10px;color:#555d72;text-transform:uppercase">Power</div><div style="font-family:JetBrains Mono;font-size:22px;color:#e8eaf0">{tmw} MW</div></div><div><div style="font-size:10px;color:#555d72;text-transform:uppercase">Budget</div><div style="font-family:JetBrains Mono;font-size:22px;color:#ffb347">${tbd/1e6:.1f}M</div></div><div><div style="font-size:10px;color:#555d72;text-transform:uppercase">Spent</div><div style="font-family:JetBrains Mono;font-size:22px;color:#00e5a0">${tsp/1e6:.1f}M</div></div></div></div>',unsafe_allow_html=True)
        df=pd.DataFrame([{"ID":p["id"],"Name":p["name"],"Status":p["status"],"Cap MWh":p["capacity_mwh"],"Power MW":p["power_mw"],"Chemistry":p["chemistry"],"Progress%":p["progress_pct"],"Budget $M":round(p["budget_usd"]/1e6,2),"Spent $M":round(p["spent_usd"]/1e6,2)}for p in rps])
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("⬇️ Download CSV",df.to_csv(index=False),"bess_summary.csv","text/csv")
    with t2:
        bp=st.selectbox("Project",[p["name"]for p in P],key="bom_p")
        proj=next(p for p in P if p["name"]==bp)
        bom=[{"Item":"Battery Rack","Qty":proj["rack_count"],"Unit":"Rack","Unit Cost":85000,"Spec":f'100 kWh {proj["chemistry"]}'},
             {"Item":"BMS","Qty":max(1,proj["rack_count"]//8),"Unit":"Unit","Unit Cost":8500,"Spec":"CAN 2.0B"},
             {"Item":"PCS / Inverter","Qty":proj["pcs_count"],"Unit":"Unit","Unit Cost":120000,"Spec":"250 kW 3L-NPC"},
             {"Item":"MV Transformer","Qty":max(1,proj["pcs_count"]//2),"Unit":"Unit","Unit Cost":45000,"Spec":"11kV/400V"},
             {"Item":"VCB","Qty":max(1,proj["pcs_count"]),"Unit":"Unit","Unit Cost":12000,"Spec":"630A 12kV"},
             {"Item":"Smart Meter","Qty":2,"Unit":"Unit","Unit Cost":2500,"Spec":"Class 0.5S"},
             {"Item":"Protection Relay","Qty":max(1,proj["pcs_count"]),"Unit":"Unit","Unit Cost":6500,"Spec":"87T/51/50"},
             {"Item":"SCADA / EMS","Qty":1,"Unit":"System","Unit Cost":35000,"Spec":"IEC 61850"},
             {"Item":"BESS Container","Qty":max(1,proj["rack_count"]//10),"Unit":"Unit","Unit Cost":25000,"Spec":"20ft IP54"},
             {"Item":"Cabling","Qty":1,"Unit":"Lot","Unit Cost":round(proj["budget_usd"]*0.05,-3),"Spec":"DC/AC/Control"},
             {"Item":"Civil Works","Qty":1,"Unit":"Lot","Unit Cost":round(proj["budget_usd"]*0.08,-3),"Spec":"Foundation"},
             {"Item":"Commissioning","Qty":1,"Unit":"Lot","Unit Cost":round(proj["budget_usd"]*0.04,-3),"Spec":"FAT+SAT"}]
        for r in bom: r["Total"]=r["Qty"]*r["Unit Cost"]
        df_b=pd.DataFrame(bom); total=df_b["Total"].sum()
        st.dataframe(df_b.style.format({"Unit Cost":"${:,.0f}","Total":"${:,.0f}"}),use_container_width=True,hide_index=True)
        c1,c2=st.columns(2); c1.metric("BoM Total",f"${total:,.0f}"); c2.metric("vs Budget",f"{round(total/proj['budget_usd']*100)}%")
        st.download_button("⬇️ Download BoM",df_b.to_csv(index=False),f'BoM_{proj["id"]}.csv',"text/csv")
    with t3:
        cp=st.selectbox("Project",[p["name"]for p in P],key="cost_p")
        proj=next(p for p in P if p["name"]==cp)
        cats2={"Battery Racks":proj["rack_count"]*85000,"BMS":max(1,proj["rack_count"]//8)*8500,"PCS":proj["pcs_count"]*120000,"Transformers":max(1,proj["pcs_count"]//2)*45000,"Protection":proj["pcs_count"]*18500,"Monitoring":40000,"Civil":round(proj["budget_usd"]*0.08,-3),"Cabling":round(proj["budget_usd"]*0.05,-3),"Engineering":round(proj["budget_usd"]*0.06,-3),"Commissioning":round(proj["budget_usd"]*0.04,-3)}
        tot=sum(cats2.values()); cpm=tot/proj["capacity_mwh"]if proj["capacity_mwh"]else 0
        c1,c2=st.columns([3,2])
        with c1:
            fig=go.Figure(go.Pie(labels=list(cats2.keys()),values=list(cats2.values()),hole=0.5,marker_colors=["#00d4ff","#00e5a0","#ffb347","#a78bfa","#ff5566","#555d72","#3d4a6b","#1a2d4a","#0d1a2e","#4a3a6b"],textinfo="label+percent",textfont_size=11))
            fig.update_layout(**PT,height=320,annotations=[dict(text=f'${tot/1e6:.1f}M',x=0.5,y=0.5,font_size=16,font_color="#e8eaf0",showarrow=False)])
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        with c2:
            st.metric("Cost per MWh",f"${cpm:,.0f}"); st.metric("Storage Duration",f'{round(proj["capacity_mwh"]/proj["power_mw"],1)} h'); st.metric("$/MW",f'${tot/proj["power_mw"]/1e6:.2f}M')
    with t4:
        c1,c2=st.columns(2)
        with c1:
            st.download_button("⬇️ Full Export (JSON)",json.dumps({"export_date":datetime.now().isoformat(),"platform":"DDE BESS v2.0","projects":P},indent=2),"dde_bess_export.json","application/json")
            df_all=pd.DataFrame([{"ID":p["id"],"Name":p["name"],"Status":p["status"],"Capacity MWh":p["capacity_mwh"],"Power MW":p["power_mw"],"Budget USD":p["budget_usd"],"Spent USD":p["spent_usd"],"Progress %":p["progress_pct"]}for p in P])
            st.download_button("⬇️ Projects CSV",df_all.to_csv(index=False),"projects.csv","text/csv")
        with c2:
            df_cat=pd.DataFrame([{"Key":k,"Label":v["label"],"Category":v["category"],"Unit Cost":v["unit_cost_usd"]}for k,v in COMPONENT_CATALOGUE.items()])
            st.download_button("⬇️ Component Catalogue CSV",df_cat.to_csv(index=False),"catalogue.csv","text/csv")
            ms_rows=[{"Project":p["name"],"Milestone":m["name"],"Date":m["date"],"Done":m["done"]}for p in P for m in p["milestones"]]
            st.download_button("⬇️ Milestones CSV",pd.DataFrame(ms_rows).to_csv(index=False),"milestones.csv","text/csv")

# ── ROUTER ────────────────────────────────────────────────────────────────────
if   "Dashboard"          in page: page_dashboard()
elif "Design Canvas"      in page: page_canvas()
elif "Component Database" in page: page_components()
elif "Project Manager"    in page: page_projects()
elif "Reports"            in page: page_reports()
