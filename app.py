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

    page = st.radio("Navigate", ["🏠  Dashboard","🎨  Design Canvas","🔋  Component Database","📋  Project Manager","📊  Reports & Export"], label_visibility="collapsed")
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
        sn2=st.selectbox("Select project",[p["name"]for p in P])
        proj=next(p for p in P if p["name"]==sn2); idx=P.index(proj)
        with st.form("edit_proj"):
            c1,c2=st.columns(2)
            nn=c1.text_input("Name",proj["name"]); nc=c2.text_input("Client",proj["client"])
            nl=c1.text_input("Location",proj["location"]); ne=c2.text_input("Engineer",proj["engineer"])
            ns=st.selectbox("Status",PROJECT_STATUSES,index=PROJECT_STATUSES.index(proj["status"]))
            c3,c4=st.columns(2)
            nca=c3.number_input("Capacity (MWh)",value=float(proj["capacity_mwh"]),step=0.5); npm=c4.number_input("Power (MW)",value=float(proj["power_mw"]),step=0.5)
            nch=c3.selectbox("Chemistry",["LFP","NMC","NCA","LTO"],index=["LFP","NMC","NCA","LTO"].index(proj["chemistry"]))
            c5,c6=st.columns(2)
            nb=c5.number_input("Budget (USD)",value=proj["budget_usd"],step=10000); nsp=c6.number_input("Spent (USD)",value=proj["spent_usd"],step=1000)
            npr=st.slider("Progress (%)",0,100,proj["progress_pct"]); nno=st.text_area("Notes",proj["notes"])
            if st.form_submit_button("💾 Save"):
                P[idx].update({"name":nn,"client":nc,"location":nl,"engineer":ne,"status":ns,"capacity_mwh":nca,"power_mw":npm,"chemistry":nch,"budget_usd":nb,"spent_usd":nsp,"progress_pct":npr,"notes":nno})
                st.session_state.projects=P; st.success("✓ Saved")
    with t4:
        with st.form("new_proj"):
            c1,c2=st.columns(2)
            an=c1.text_input("Name *"); ac2=c2.text_input("Client *")
            al2=c1.text_input("Location"); ae=c2.text_input("Engineer")
            ast2=st.selectbox("Status",PROJECT_STATUSES)
            c3,c4=st.columns(2)
            aca=c3.number_input("Capacity (MWh)",0.1,1000.0,5.0,step=0.5); apm=c4.number_input("Power (MW)",0.1,1000.0,2.5,step=0.5)
            ach=c3.selectbox("Chemistry",["LFP","NMC","NCA","LTO"])
            c5,c6=st.columns(2)
            ab=c5.number_input("Budget (USD)",100000,100000000,4000000,step=50000); as2=c6.date_input("Start Date",date.today()); ae2=c5.date_input("End Date")
            ano=st.text_area("Notes")
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
        sel=st.selectbox("Project",["All Projects"]+[p["name"]for p in P])
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
CAD_HTML=r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BESS Site Plan Designer — SunStripe Template</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<style>
:root{
  --bg:#1a1d23;--bg2:#22262f;--bg3:#2a2f3a;--border:rgba(255,255,255,0.08);
  --accent:#e8a020;--text:#d0d4dc;--text2:#7a8090;--red:#e02020;
  --sheet:#ffffff;--grid:#e8edf2;--grid2:#cdd5dd;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Courier New',monospace;height:100vh;display:flex;flex-direction:column;overflow:hidden;font-size:12px;}

/* TOOLBAR */
#toolbar{height:38px;background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:2px;padding:0 8px;flex-shrink:0;user-select:none;}
.tb-group{display:flex;align-items:center;gap:2px;padding:0 4px;border-right:1px solid var(--border);}
.tb-btn{height:26px;padding:0 8px;border-radius:3px;font-size:10px;font-weight:600;cursor:pointer;color:var(--text2);background:transparent;border:1px solid transparent;font-family:'Courier New',monospace;transition:all 0.12s;white-space:nowrap;letter-spacing:0.03em;}
.tb-btn:hover{background:var(--bg3);color:var(--text);border-color:var(--border);}
.tb-btn.active{background:rgba(232,160,32,0.15);color:var(--accent);border-color:rgba(232,160,32,0.4);}
.tb-btn.export{color:#4db8ff;border-color:rgba(77,184,255,0.3);}
.tb-btn.export:hover{background:rgba(77,184,255,0.1);}
.tb-btn.export-dwg{color:#ff9d4d;border-color:rgba(255,157,77,0.3);}
.tb-btn.export-dwg:hover{background:rgba(255,157,77,0.1);}
.tb-btn.export-pdf{color:#ff6b6b;border-color:rgba(255,107,107,0.3);}
.tb-btn.export-pdf:hover{background:rgba(255,107,107,0.1);}
.tb-sep{width:1px;height:20px;background:var(--border);margin:0 2px;}
#snap-indicator{font-size:9px;color:var(--accent);font-family:'Courier New',monospace;margin-left:4px;}
#coord-display{font-family:'Courier New',monospace;font-size:10px;color:var(--text2);margin-left:auto;padding-right:8px;}

/* MAIN LAYOUT */
#main{display:flex;flex:1;overflow:hidden;}

/* LEFT PALETTE */
#palette{width:160px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);overflow-y:auto;padding:6px;}
#palette::-webkit-scrollbar{width:3px;}
#palette::-webkit-scrollbar-thumb{background:var(--bg3);}
.pal-section{font-size:9px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:0.1em;padding:6px 4px 4px;border-bottom:1px solid var(--border);margin-bottom:4px;}
.pal-item{display:flex;align-items:center;gap:6px;padding:5px 6px;border:1px solid var(--border);border-radius:3px;cursor:pointer;margin-bottom:3px;background:var(--bg3);transition:all 0.12s;}
.pal-item:hover{border-color:var(--accent);background:rgba(232,160,32,0.06);}
.pal-item.active-layer{border-color:var(--accent);background:rgba(232,160,32,0.1);}
.pal-icon{width:28px;height:18px;flex-shrink:0;}
.pal-label{font-size:9px;color:var(--text2);line-height:1.2;}

/* CANVAS WRAP */
#canvas-wrap{flex:1;overflow:auto;background:#2c3038;position:relative;cursor:crosshair;}
#canvas-wrap.mode-select{cursor:default;}
#canvas-wrap.mode-pan{cursor:grab;}
#drawing-svg{display:block;}

/* RIGHT PANEL - TITLE BLOCK EDITOR */
#right-panel{width:220px;flex-shrink:0;background:var(--bg2);border-left:1px solid var(--border);overflow-y:auto;display:flex;flex-direction:column;}
#right-panel::-webkit-scrollbar{width:3px;}
#right-panel::-webkit-scrollbar-thumb{background:var(--bg3);}
.rp-section{border-bottom:1px solid var(--border);padding:8px;}
.rp-title{font-size:9px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;}
.rp-field{margin-bottom:5px;}
.rp-label{font-size:9px;color:var(--text2);margin-bottom:2px;display:block;}
.rp-input{width:100%;padding:3px 6px;background:var(--bg3);border:1px solid var(--border);border-radius:2px;color:var(--text);font-size:10px;font-family:'Courier New',monospace;outline:none;}
.rp-input:focus{border-color:var(--accent);}
.rev-row{display:grid;grid-template-columns:18px 1fr 26px 50px;gap:2px;margin-bottom:2px;}
.rev-cell{padding:2px 3px;background:var(--bg3);border:1px solid var(--border);border-radius:2px;color:var(--text);font-size:9px;font-family:'Courier New',monospace;outline:none;}
.rev-cell:focus{border-color:var(--accent);}
.props-empty{font-size:10px;color:var(--text2);text-align:center;padding:20px 10px;}

/* STATUS BAR */
#statusbar{height:20px;background:var(--bg2);border-top:1px solid var(--border);display:flex;align-items:center;gap:12px;padding:0 10px;font-size:9px;color:var(--text2);font-family:'Courier New',monospace;flex-shrink:0;}
.sb-item{display:flex;align-items:center;gap:4px;}
#sb-mode-dot{width:6px;height:6px;border-radius:50%;background:#00e5a0;}

/* LEGEND SYMBOLS (used in palette SVGs) */
.leg-site-boundary{stroke:#ff4444;stroke-width:2.5;fill:none;}
.leg-fence{stroke:#333;stroke-width:1.5;stroke-dasharray:4 2;fill:none;}
.leg-veg{fill:#88bb44;opacity:0.7;}
.leg-wetlands{fill:#4499cc;opacity:0.6;}
.leg-pond{fill:#2266aa;opacity:0.7;}
.leg-fire-road{fill:#cc7733;opacity:0.7;}
.leg-road{fill:#aa9966;opacity:0.7;}
.leg-batt{fill:none;stroke:#3388cc;stroke-width:1.5;}
.leg-mvt{fill:none;stroke:#555577;stroke-width:1.5;}
.leg-fire-stage{fill:#dd3333;opacity:0.5;}
</style>
</head>
<body>

<!-- TOOLBAR -->
<div id="toolbar">
  <div class="tb-group">
    <span style="color:var(--accent);font-size:10px;font-weight:700;letter-spacing:0.1em;margin-right:4px;">BESS SITE PLAN</span>
  </div>
  <div class="tb-group">
    <button class="tb-btn active" id="btn-select" onclick="setTool('select')" title="Select/Move (V)">SELECT</button>
    <button class="tb-btn" id="btn-polyline" onclick="setTool('polyline')" title="Polyline (P)">PLINE</button>
    <button class="tb-btn" id="btn-rect" onclick="setTool('rect')" title="Rectangle (R)">RECT</button>
    <button class="tb-btn" id="btn-polygon" onclick="setTool('polygon')" title="Polygon (G)">POLY</button>
    <button class="tb-btn" id="btn-circle" onclick="setTool('circle')" title="Circle (C)">CIRCLE</button>
    <button class="tb-btn" id="btn-text" onclick="setTool('text')" title="Text (T)">TEXT</button>
    <button class="tb-btn" id="btn-dim" onclick="setTool('dim')" title="Dimension (D)">DIM</button>
  </div>
  <div class="tb-group">
    <button class="tb-btn" onclick="toggleSnap()" id="btn-snap" title="Snap to grid">SNAP:ON</button>
    <button class="tb-btn" onclick="toggleGrid()" id="btn-grid" title="Toggle grid">GRID:ON</button>
    <button class="tb-btn" onclick="zoomFit()" title="Zoom to fit (F)">FIT</button>
    <button class="tb-btn" onclick="zoomIn()">Z+</button>
    <button class="tb-btn" onclick="zoomOut()">Z-</button>
  </div>
  <div class="tb-group">
    <button class="tb-btn" onclick="doUndo()" title="Undo (Ctrl+Z)">UNDO</button>
    <button class="tb-btn" onclick="doRedo()" title="Redo (Ctrl+Y)">REDO</button>
    <button class="tb-btn danger" onclick="deleteSelected()" title="Delete (Del)" style="color:#ff6b6b;">DELETE</button>
    <button class="tb-btn" onclick="clearAll()" style="color:#ff6b6b;">CLEAR</button>
  </div>
  <div class="tb-group">
    <button class="tb-btn export" onclick="exportSVG()">↓ SVG</button>
    <button class="tb-btn export-dwg" onclick="exportDXF()">↓ DXF/DWG</button>
    <button class="tb-btn export-pdf" onclick="exportPDF()">↓ PDF</button>
  </div>
  <div id="snap-indicator"></div>
  <div id="coord-display">X: 0.00   Y: 0.00</div>
</div>

<!-- MAIN -->
<div id="main">

  <!-- LEFT PALETTE -->
  <div id="palette">
    <div class="pal-section">Site Elements</div>

    <div class="pal-item" onclick="setActiveLayer('site_boundary')" id="pal-site_boundary" title="Draw site boundary">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="2" y="4" width="24" height="10" fill="none" stroke="#ff4444" stroke-width="2.5"/></svg>
      <span class="pal-label">SITE<br>BOUNDARY</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('fence')" id="pal-fence">
      <svg class="pal-icon" viewBox="0 0 28 18"><line x1="2" y1="9" x2="26" y2="9" stroke="#333" stroke-width="1.5" stroke-dasharray="4 2"/><line x1="6" y1="5" x2="6" y2="13" stroke="#333" stroke-width="1"/><line x1="14" y1="5" x2="14" y2="13" stroke="#333" stroke-width="1"/><line x1="22" y1="5" x2="22" y2="13" stroke="#333" stroke-width="1"/></svg>
      <span class="pal-label">FENCE</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('vegetation')" id="pal-vegetation">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="2" y="2" width="24" height="14" fill="#88cc44" opacity="0.6"/><path d="M2 14 Q7 8 12 14 Q17 8 22 14 Q25 9 26 14" fill="none" stroke="#558822" stroke-width="1"/></svg>
      <span class="pal-label">VEGETATION</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('wetlands')" id="pal-wetlands">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="2" y="2" width="24" height="14" fill="#4499cc" opacity="0.5"/><line x1="2" y1="6" x2="26" y2="6" stroke="#2266aa" stroke-width="0.7"/><line x1="2" y1="10" x2="26" y2="10" stroke="#2266aa" stroke-width="0.7"/><line x1="2" y1="14" x2="26" y2="14" stroke="#2266aa" stroke-width="0.7"/></svg>
      <span class="pal-label">WETLANDS</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('pond')" id="pal-pond">
      <svg class="pal-icon" viewBox="0 0 28 18"><ellipse cx="14" cy="9" rx="11" ry="7" fill="#2266aa" opacity="0.7"/></svg>
      <span class="pal-label">STORM WATER<br>POND</span>
    </div>

    <div class="pal-section" style="margin-top:6px">Roads</div>

    <div class="pal-item" onclick="setActiveLayer('fire_road')" id="pal-fire_road">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="2" y="5" width="24" height="8" fill="#cc7733" opacity="0.7"/><line x1="2" y1="5" x2="26" y2="13" stroke="#aa5500" stroke-width="0.8"/><line x1="2" y1="7" x2="26" y2="15" stroke="#aa5500" stroke-width="0.8" visibility="hidden"/></svg>
      <span class="pal-label">FIRE BATT<br>ACCESS RD</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('access_road')" id="pal-access_road">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="2" y="5" width="24" height="8" fill="#aa9966" opacity="0.8"/></svg>
      <span class="pal-label">ACCESS ROAD</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('access_gate')" id="pal-access_gate">
      <svg class="pal-icon" viewBox="0 0 28 18"><line x1="2" y1="9" x2="8" y2="9" stroke="#333" stroke-width="1.5"/><line x1="20" y1="9" x2="26" y2="9" stroke="#333" stroke-width="1.5"/><path d="M8 4 L14 9 L20 4" fill="none" stroke="#333" stroke-width="1.5" stroke-linejoin="round"/></svg>
      <span class="pal-label">ACCESS GATE</span>
    </div>

    <div class="pal-section" style="margin-top:6px">Equipment</div>

    <div class="pal-item" onclick="setActiveLayer('battery_container')" id="pal-battery_container">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="3" y="3" width="22" height="12" fill="#ddeeff" stroke="#3388cc" stroke-width="1.5"/><text x="14" y="12" text-anchor="middle" font-size="5" fill="#3388cc" font-family="Courier New">BESS</text></svg>
      <span class="pal-label">BATTERY<br>CONTAINER</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('mv_transformer')" id="pal-mv_transformer">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="3" y="3" width="22" height="12" fill="#eeeef8" stroke="#555577" stroke-width="1.5"/><text x="14" y="12" text-anchor="middle" font-size="5" fill="#555577" font-family="Courier New">MVT</text></svg>
      <span class="pal-label">MV<br>TRANSFORMER</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('fire_staging')" id="pal-fire_staging">
      <svg class="pal-icon" viewBox="0 0 28 18"><rect x="2" y="2" width="24" height="14" fill="#dd3333" opacity="0.4"/><line x1="2" y1="2" x2="26" y2="16" stroke="#aa0000" stroke-width="0.8"/><line x1="2" y1="8" x2="20" y2="16" stroke="#aa0000" stroke-width="0.8"/><line x1="8" y1="2" x2="26" y2="10" stroke="#aa0000" stroke-width="0.8"/></svg>
      <span class="pal-label">FIRE STAGING<br>AREA</span>
    </div>

    <div class="pal-section" style="margin-top:6px">Utilities</div>
    <div class="pal-item" onclick="setActiveLayer('annotation')" id="pal-annotation">
      <svg class="pal-icon" viewBox="0 0 28 18"><text x="4" y="13" font-size="11" fill="#d0d4dc" font-family="Courier New" font-weight="bold">Aa</text></svg>
      <span class="pal-label">ANNOTATION</span>
    </div>
    <div class="pal-item" onclick="setActiveLayer('dimension')" id="pal-dimension">
      <svg class="pal-icon" viewBox="0 0 28 18"><line x1="3" y1="9" x2="25" y2="9" stroke="#ffcc44" stroke-width="1"/><line x1="3" y1="6" x2="3" y2="12" stroke="#ffcc44" stroke-width="1"/><line x1="25" y1="6" x2="25" y2="12" stroke="#ffcc44" stroke-width="1"/><text x="14" y="8" text-anchor="middle" font-size="5" fill="#ffcc44">25.0m</text></svg>
      <span class="pal-label">DIMENSION</span>
    </div>
  </div>

  <!-- CANVAS -->
  <div id="canvas-wrap"
    onmousedown="onMouseDown(event)"
    onmousemove="onMouseMove(event)"
    onmouseup="onMouseUp(event)"
    ondblclick="onDblClick(event)"
    onwheel="onWheel(event)"
    ondragover="event.preventDefault()"
    ondrop="onDrop(event)">
    <svg id="drawing-svg" xmlns="http://www.w3.org/2000/svg"></svg>
  </div>

  <!-- RIGHT: TITLE BLOCK EDITOR -->
  <div id="right-panel">
    <div class="rp-section">
      <div class="rp-title">Project Info</div>
      <div class="rp-field"><label class="rp-label">PROJECT NAME</label><input class="rp-input" id="tb-project" value="PROJECT NAME" oninput="updateTitleBlock()"></div>
      <div class="rp-field"><label class="rp-label">% DESIGN</label><input class="rp-input" id="tb-design-pct" value="30" oninput="updateTitleBlock()"></div>
      <div class="rp-field"><label class="rp-label">CLIENT NAME</label><input class="rp-input" id="tb-client" value="CLIENT NAME" oninput="updateTitleBlock()"></div>
      <div class="rp-field"><label class="rp-label">PROJECT REF</label><input class="rp-input" id="tb-ref" value="US_PROJECT_REF" oninput="updateTitleBlock()"></div>
    </div>
    <div class="rp-section">
      <div class="rp-title">Sheet Info</div>
      <div class="rp-field"><label class="rp-label">SHEET NAME</label><input class="rp-input" id="tb-sheet-name" value="SITE PLAN" oninput="updateTitleBlock()"></div>
      <div class="rp-field"><label class="rp-label">SHEET NO</label><input class="rp-input" id="tb-sheet-no" value="C-001" oninput="updateTitleBlock()"></div>
      <div class="rp-field"><label class="rp-label">LAT / LONG</label><input class="rp-input" id="tb-latlong" value="XX.XX / -XX.XX" oninput="updateTitleBlock()"></div>
      <div class="rp-field"><label class="rp-label">DRWN</label><input class="rp-input" id="tb-drwn" value="XX" oninput="updateTitleBlock()" style="width:60px;display:inline"></div>
      <label class="rp-label" style="display:inline;margin:0 4px">REVW</label><input class="rp-input" id="tb-revw" value="XX" oninput="updateTitleBlock()" style="width:60px;display:inline">
      <div class="rp-field" style="margin-top:4px"><label class="rp-label">APPRVD</label><input class="rp-input" id="tb-apprvd" value="XX" oninput="updateTitleBlock()"></div>
    </div>
    <div class="rp-section">
      <div class="rp-title">Revision Table</div>
      <div style="display:grid;grid-template-columns:18px 1fr 26px 54px;gap:2px;margin-bottom:4px;">
        <span style="font-size:8px;color:var(--text2);text-align:center">REV</span>
        <span style="font-size:8px;color:var(--text2)">DESCRIPTION</span>
        <span style="font-size:8px;color:var(--text2)">BY</span>
        <span style="font-size:8px;color:var(--text2)">DATE</span>
      </div>
      <div id="rev-rows"></div>
    </div>
    <div class="rp-section">
      <div class="rp-title">Drawing Scale</div>
      <div class="rp-field"><label class="rp-label">SCALE</label>
        <select class="rp-input" id="tb-scale" onchange="updateTitleBlock()">
          <option value="1:500">1:500</option>
          <option value="1:1000" selected>1:1000</option>
          <option value="1:2000">1:2000</option>
          <option value="1:5000">1:5000</option>
          <option value="NTS">NTS</option>
        </select>
      </div>
    </div>
    <div class="rp-section" id="props-section">
      <div class="rp-title">Selected Object</div>
      <div class="props-empty" id="props-empty">No object selected</div>
      <div id="props-fields" style="display:none"></div>
    </div>
  </div>
</div>

<!-- STATUS BAR -->
<div id="statusbar">
  <div class="sb-item"><div id="sb-mode-dot"></div><span id="sb-tool">SELECT</span></div>
  <span>|</span>
  <div class="sb-item">Layer: <span id="sb-layer" style="color:var(--accent)">SITE_BOUNDARY</span></div>
  <span>|</span>
  <div class="sb-item">Objects: <span id="sb-count">0</span></div>
  <span>|</span>
  <div class="sb-item">Zoom: <span id="sb-zoom">100%</span></div>
  <span>|</span>
  <div class="sb-item">Snap: <span id="sb-snap">20m</span></div>
  <div style="flex:1"></div>
  <span>V=select  P=pline  R=rect  G=polygon  C=circle  T=text  D=dim  ESC=cancel  DEL=delete  Ctrl+Z=undo</span>
</div>

<script>
// ═══════════════════════════════════════════════
//  CONSTANTS & CONFIG
// ═══════════════════════════════════════════════

// Sheet dimensions in SVG units (1 unit = 1m at 1:1000 scale)
// 11"×17" at 1:1000 → drawing area ~280m × 175m
const SHEET_W = 1700;   // SVG units (pts) for full sheet
const SHEET_H = 1100;
const MARGIN  = 40;
const TB_W    = 280;    // title block width
const DRAW_X1 = MARGIN;
const DRAW_Y1 = MARGIN + 24; // space for copyright line
const DRAW_X2 = SHEET_W - TB_W - MARGIN;
const DRAW_Y2 = SHEET_H - MARGIN - 20; // space for bottom note
const DRAW_W  = DRAW_X2 - DRAW_X1;
const DRAW_H  = DRAW_Y2 - DRAW_Y1;
const TB_X    = SHEET_W - TB_W - MARGIN;
const TB_Y    = DRAW_Y1;

// Layer definitions — colors, styles, draw mode
const LAYERS = {
  site_boundary:    {name:'SITE BOUNDARY',    color:'#ff3333', lw:2.5, dash:'',        fill:'none',     alpha:1,   drawMode:'polyline', closed:true},
  fence:            {name:'FENCE',             color:'#222222', lw:1.5, dash:'8,4',     fill:'none',     alpha:1,   drawMode:'polyline'},
  vegetation:       {name:'VEGETATION',        color:'#558822', lw:1,   dash:'',        fill:'#88cc44',  alpha:0.55,drawMode:'polygon',  closed:true, hatch:'veg'},
  wetlands:         {name:'WETLANDS',          color:'#2266aa', lw:1,   dash:'',        fill:'#4499cc',  alpha:0.5, drawMode:'polygon',  closed:true, hatch:'hz'},
  pond:             {name:'STORM WATER POND',  color:'#1144aa', lw:1,   dash:'',        fill:'#2266aa',  alpha:0.65,drawMode:'polygon',  closed:true},
  fire_road:        {name:'FIRE BATT ACCESS',  color:'#aa5500', lw:1,   dash:'',        fill:'#cc7733',  alpha:0.7, drawMode:'polygon',  closed:true, hatch:'diag'},
  access_road:      {name:'ACCESS ROAD',       color:'#887755', lw:1,   dash:'',        fill:'#aa9966',  alpha:0.75,drawMode:'polygon',  closed:true},
  access_gate:      {name:'ACCESS GATE',       color:'#222222', lw:1.5, dash:'',        fill:'none',     alpha:1,   drawMode:'rect'},
  battery_container:{name:'BATTERY CONTAINER', color:'#2266bb', lw:2,   dash:'',        fill:'#ddeeff',  alpha:0.85,drawMode:'rect'},
  mv_transformer:   {name:'MV TRANSFORMER',    color:'#444466', lw:2,   dash:'',        fill:'#eeeef8',  alpha:0.85,drawMode:'rect'},
  fire_staging:     {name:'FIRE STAGING AREA', color:'#990000', lw:1.5, dash:'',        fill:'#dd3333',  alpha:0.4, drawMode:'polygon',  closed:true, hatch:'diag2'},
  annotation:       {name:'ANNOTATION',        color:'#222222', lw:1,   dash:'',        fill:'#222222',  alpha:1,   drawMode:'text'},
  dimension:        {name:'DIMENSION',         color:'#cc9900', lw:0.8, dash:'',        fill:'none',     alpha:1,   drawMode:'dim'},
};

// ═══════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════
let tool = 'select';
let activeLayer = 'site_boundary';
let objects = [];          // all drawing objects
let selected = null;
let idN = 0;
let undoStack = [], redoStack = [];

// Pan/zoom
let vpX = 0, vpY = 0, vpZoom = 0.55;
let isPan = false, panSX = 0, panSY = 0;

// Drawing state
let isDrawing = false;
let drawPoints = [];        // current polyline/polygon points
let drawStart = null;       // rect/circle start
let snapOn = true;
let gridOn = true;
let snapSize = 20;          // snap to 20 SVG units

// Title block data
let tbData = {};

// Revision rows
let revData = [
  {rev:'A', desc:'PRELIMINARY', by:'XX', date:'XXXX/X/XX'},
  {rev:'B', desc:'', by:'', date:''},
  {rev:'C', desc:'', by:'', date:''},
  {rev:'D', desc:'', by:'', date:''},
  {rev:'E', desc:'', by:'', date:''},
];

// ═══════════════════════════════════════════════
//  DEFS — hatch patterns
// ═══════════════════════════════════════════════
const SVG_NS = 'http://www.w3.org/2000/svg';

function initSVG() {
  const svg = document.getElementById('drawing-svg');
  const w = SHEET_W, h = SHEET_H;
  svg.setAttribute('width', w * vpZoom);
  svg.setAttribute('height', h * vpZoom);
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.style.transform = `translate(${vpX}px,${vpY}px)`;

  // Defs
  const defs = document.createElementNS(SVG_NS,'defs');

  // Hatch patterns
  const patterns = [
    {id:'hatch-veg',  bg:'#88cc44', lines:[{x1:0,y1:0,x2:10,y2:10},{x1:-2,y1:8,x2:2,y2:12}], stroke:'#558822', sw:0.8},
    {id:'hatch-hz',   bg:'#4499cc', lines:[{x1:0,y1:3,x2:10,y2:3},{x1:0,y1:7,x2:10,y2:7}], stroke:'#2266aa', sw:0.7},
    {id:'hatch-diag', bg:'#cc7733', lines:[{x1:0,y1:0,x2:10,y2:10},{x1:0,y1:5,x2:5,y2:10},{x1:5,y1:0,x2:10,y2:5}], stroke:'#884400', sw:0.7},
    {id:'hatch-diag2',bg:'#dd3333', lines:[{x1:0,y1:0,x2:8,y2:8},{x1:0,y1:4,x2:4,y2:8},{x1:4,y1:0,x2:8,y2:4}], stroke:'#880000', sw:0.7},
  ];
  patterns.forEach(pd => {
    const pat = document.createElementNS(SVG_NS,'pattern');
    pat.setAttribute('id', pd.id);
    pat.setAttribute('width','10'); pat.setAttribute('height','10');
    pat.setAttribute('patternUnits','userSpaceOnUse');
    const bg = document.createElementNS(SVG_NS,'rect');
    bg.setAttribute('width','10'); bg.setAttribute('height','10'); bg.setAttribute('fill',pd.bg); bg.setAttribute('opacity','0.5');
    pat.appendChild(bg);
    pd.lines.forEach(l => {
      const line = document.createElementNS(SVG_NS,'line');
      line.setAttribute('x1',l.x1);line.setAttribute('y1',l.y1);line.setAttribute('x2',l.x2);line.setAttribute('y2',l.y2);
      line.setAttribute('stroke',pd.stroke);line.setAttribute('stroke-width',pd.sw);
      pat.appendChild(line);
    });
    defs.appendChild(pat);
  });

  // Arrow marker for dimensions
  const mark = document.createElementNS(SVG_NS,'marker');
  mark.setAttribute('id','dim-arrow');mark.setAttribute('viewBox','0 0 10 10');
  mark.setAttribute('refX','5');mark.setAttribute('refY','5');
  mark.setAttribute('markerWidth','6');mark.setAttribute('markerHeight','6');
  mark.setAttribute('orient','auto-start-reverse');
  const marrowPath = document.createElementNS(SVG_NS,'path');
  marrowPath.setAttribute('d','M0 0 L10 5 L0 10 Z'); marrowPath.setAttribute('fill','#cc9900');
  mark.appendChild(marrowPath);
  defs.appendChild(mark);

  svg.appendChild(defs);

  // Layers
  ['grid-layer','sheet-layer','draw-layer','temp-layer','sel-layer'].forEach(id => {
    const g = document.createElementNS(SVG_NS,'g');
    g.setAttribute('id',id); svg.appendChild(g);
  });

  drawSheet();
  drawGrid();
  buildRevRows();
  updateTitleBlock();
}

// ═══════════════════════════════════════════════
//  SHEET — template background
// ═══════════════════════════════════════════════
function drawSheet() {
  const layer = document.getElementById('sheet-layer');
  layer.innerHTML = '';
  const W = SHEET_W, H = SHEET_H;

  function el(tag, attrs, text) {
    const e = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([k,v]) => e.setAttribute(k,v));
    if(text) e.textContent = text;
    return e;
  }

  // White sheet background
  layer.appendChild(el('rect',{x:0,y:0,width:W,height:H,fill:'#ffffff'}));

  // Outer border
  layer.appendChild(el('rect',{x:10,y:10,width:W-20,height:H-20,fill:'none',stroke:'#000',
    'stroke-width':'1.5'}));

  // Inner border (drawing area)
  layer.appendChild(el('rect',{x:DRAW_X1,y:DRAW_Y1,width:DRAW_W,height:DRAW_H,fill:'#f8f9fa',stroke:'#000','stroke-width':'0.8'}));

  // Copyright line at top
  const cText = 'THIS DRAWING IS THE PROPERTY OF SUNSTRIPE, Inc. ANY REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN PERMISSION OF SUNSTRIPE, Inc IS PROHIBITED.';
  layer.appendChild(el('text',{x:DRAW_X1+4,y:DRAW_Y1-6,
    'font-size':'5','font-family':'Arial','fill':'#000','font-weight':'bold'},cText));

  // Bottom note
  layer.appendChild(el('text',{x:W/2,y:H-MARGIN+10,'text-anchor':'middle',
    'font-size':'7','font-family':'Arial','fill':'#000','font-weight':'bold',
    'font-style':'italic'},'FOR INFORMATION PURPOSES ONLY - NOT FOR CONSTRUCTION'));

  // ─── TITLE BLOCK ───────────────────────────────
  const TX = TB_X, TY = TB_Y, TW = TB_W - 6, TH = DRAW_H;

  // Title block outer border
  layer.appendChild(el('rect',{x:TX,y:TY,width:TW,height:TH,fill:'#ffffff',stroke:'#000','stroke-width':'0.8'}));

  let cy = TY + 4;

  // ── North Arrow ──────────────────────
  const northH = 80;
  layer.appendChild(el('rect',{x:TX,y:cy,width:TW,height:northH,fill:'#f0f0f0',stroke:'#000','stroke-width':'0.5'}));
  const ncx = TX + TW/2, ncy = cy + northH/2;
  layer.appendChild(el('circle',{cx:ncx,cy:ncy,r:28,fill:'none',stroke:'#000','stroke-width':'1'}));
  // North arrow needle
  layer.appendChild(el('polygon',{points:`${ncx},${ncy-24} ${ncx-8},${ncy+10} ${ncx},${ncy+4} ${ncx+8},${ncy+10}`,fill:'#000'}));
  layer.appendChild(el('polygon',{points:`${ncx},${ncy-24} ${ncx-8},${ncy+10} ${ncx},${ncy+4}`,fill:'#ffffff',stroke:'#000','stroke-width':'0.5'}));
  // N label
  layer.appendChild(el('text',{x:ncx,y:ncy-30,'text-anchor':'middle','font-size':'12','font-family':'Arial','font-weight':'bold','fill':'#000'},'N'));
  cy += northH;

  // Separator
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.8'}));

  // ── Legends ──────────────────────────
  const legHeader = 14;
  layer.appendChild(el('rect',{x:TX,y:cy,width:TW,height:legHeader,fill:'#e8e8e8',stroke:'#000','stroke-width':'0.5'}));
  layer.appendChild(el('text',{x:TX+TW/2,y:cy+10,'text-anchor':'middle','font-size':'8','font-family':'Arial','font-weight':'bold','fill':'#000'},'LEGENDS'));
  cy += legHeader;

  const legendItems = [
    {sym:'line-solid-red', text:'SITE BOUNDARY'},
    {sym:'line-dash',      text:'FENCE'},
    {sym:'fill-veg',       text:'VEGETATION'},
    {sym:'fill-wet',       text:'WETLANDS'},
    {sym:'fill-pond',      text:'STORM WATER POND'},
    {sym:'fill-fireroad',  text:'FIRE BATTERY ACCESS ROAD'},
    {sym:'fill-road',      text:'ACCESS ROAD'},
    {sym:'gate-sym',       text:'ACCESS GATE'},
    {sym:'fill-batt',      text:'BATTERY CONTAINER'},
    {sym:'fill-mvt',       text:'MV TRANSFORMER'},
    {sym:'fill-fire',      text:'FIRE STAGING AREA'},
  ];
  const legRowH = 16;
  legendItems.forEach(item => {
    layer.appendChild(el('rect',{x:TX,y:cy,width:TW,height:legRowH,fill:'none',stroke:'#ccc','stroke-width':'0.3'}));
    const symW = 40;
    // Draw symbol
    drawLegendSym(layer, item.sym, TX+2, cy+2, symW-4, legRowH-4, el);
    // Text
    layer.appendChild(el('text',{x:TX+symW+3,y:cy+10,'font-size':'6.5','font-family':'Arial','fill':'#000'},item.text));
    cy += legRowH;
  });
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.8'}));

  // ── Project Name ──────────────────────
  const projH = 80;
  const projectBox = el('g',{id:'tb-proj-block'});
  projectBox.appendChild(el('rect',{x:TX,y:cy,width:TW,height:projH,fill:'#ffffff',stroke:'#000','stroke-width':'0.5'}));
  projectBox.appendChild(el('text',{id:'tb-svg-project',x:TX+TW/2,y:cy+28,'text-anchor':'middle',
    'font-size':'14','font-family':'Arial','font-weight':'bold','fill':'#000'},'PROJECT NAME'));
  projectBox.appendChild(el('text',{id:'tb-svg-design',x:TX+TW/2,y:cy+46,'text-anchor':'middle',
    'font-size':'12','font-family':'Arial','font-weight':'bold','fill':'#000'},'30% DESIGN'));
  projectBox.appendChild(el('text',{id:'tb-svg-client',x:TX+TW/2,y:cy+60,'text-anchor':'middle',
    'font-size':'7','font-family':'Arial','fill':'#555'},'CLIENT NAME'));
  projectBox.appendChild(el('text',{id:'tb-svg-ref',x:TX+TW/2,y:cy+70,'text-anchor':'middle',
    'font-size':'7','font-family':'Arial','fill':'#555'},'US_PROJECT_REF'));
  layer.appendChild(projectBox);
  cy += projH;
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.8'}));

  // ── Revision Table ──────────────────────
  const revH = 12;
  // Header
  layer.appendChild(el('rect',{x:TX,y:cy,width:TW,height:revH+2,fill:'#e8e8e8'}));
  ['REV','DESCRIPTION','BY','DATE'].forEach((h,i) => {
    const rx = TX + [0,18,TW-50,TW-28][i];
    const rw = [18,TW-68,28,28][i];
    layer.appendChild(el('rect',{x:rx,y:cy,width:rw,height:revH+2,fill:'none',stroke:'#888','stroke-width':'0.4'}));
    layer.appendChild(el('text',{x:rx+rw/2,y:cy+9,'text-anchor':'middle','font-size':'6','font-family':'Arial','font-weight':'bold','fill':'#000'},h));
  });
  cy += revH + 2;
  // Data rows
  const revBlockG = el('g',{id:'tb-svg-revs'});
  revData.forEach((row, ri) => {
    const ry = cy + ri*(revH+1);
    ['rev','desc','by','date'].forEach((k,i) => {
      const rx2 = TX + [0,18,TW-50,TW-28][i];
      const rw2 = [18,TW-68,28,28][i];
      revBlockG.appendChild(el('rect',{x:rx2,y:ry,width:rw2,height:revH,'fill':'none',stroke:'#ccc','stroke-width':'0.3'}));
      revBlockG.appendChild(el('text',{id:`tb-svg-rev${ri}-${k}`,x:rx2+3,y:ry+8,'font-size':'5.5','font-family':'Arial','fill':'#000'},row[k]||''));
    });
  });
  layer.appendChild(revBlockG);
  cy += revData.length*(revH+1) + 4;
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.8'}));

  // ── SunStripe Branding ──────────────────
  const brandH = 46;
  const brandG = el('g',{});
  brandG.appendChild(el('rect',{x:TX,y:cy,width:TW,height:brandH,fill:'#ffffff',stroke:'#000','stroke-width':'0.5'}));
  brandG.appendChild(el('text',{x:TX+TW/2,y:cy+20,'text-anchor':'middle',
    'font-size':'15','font-family':'Arial','font-weight':'bold','fill':'#dd2200'},'SunStripe'));
  brandG.appendChild(el('text',{x:TX+TW/2,y:cy+30,'text-anchor':'middle',
    'font-size':'6','font-family':'Arial','fill':'#444'},'Trusted Clean Energy Partners'));
  brandG.appendChild(el('text',{x:TX+TW/2,y:cy+40,'text-anchor':'middle',
    'font-size':'5.5','font-family':'Arial','fill':'#444'},'6363 N State Highway 161, Ste 250 Irving, TX 75038'));
  layer.appendChild(brandG);
  cy += brandH;
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.8'}));

  // ── Sheet Name ──────────────────────────
  const snH = 32;
  const snG = el('g',{});
  snG.appendChild(el('text',{x:TX+4,y:cy+10,'font-size':'6','font-family':'Arial','fill':'#000'},'SHEET NAME:'));
  snG.appendChild(el('text',{id:'tb-svg-sheet-name',x:TX+TW/2,y:cy+24,'text-anchor':'middle',
    'font-size':'9','font-family':'Arial','font-weight':'bold','fill':'#000'},'SITE PLAN'));
  layer.appendChild(snG);
  cy += snH;
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.5'}));

  // ── Lat/Long ──────────────────────────
  layer.appendChild(el('text',{x:TX+4,y:cy+10,'font-size':'6','font-family':'Arial','fill':'#000'},'LAT/LONG:'));
  layer.appendChild(el('text',{id:'tb-svg-latlong',x:TX+50,y:cy+10,'font-size':'6','font-family':'Arial','fill':'#000'},'XX.XX / -XX.XX'));
  cy += 14;
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.5'}));

  // ── DRWN/REVW/APPRVD/SIZE ──────────────
  const cols4 = [{l:'DRWN',w:TW*0.22},{l:'REVW',w:TW*0.22},{l:'APPRVD',w:TW*0.28},{l:'SIZE',w:TW*0.28}];
  let cx4 = TX;
  cols4.forEach(col => {
    layer.appendChild(el('rect',{x:cx4,y:cy,width:col.w,height:20,fill:'none',stroke:'#888','stroke-width':'0.4'}));
    layer.appendChild(el('text',{x:cx4+col.w/2,y:cy+8,'text-anchor':'middle','font-size':'5.5','font-family':'Arial','font-weight':'bold','fill':'#000'},col.l));
    cx4 += col.w;
  });
  cy += 10;
  let cx5 = TX;
  const initIds = ['drwn','revw','apprvd'];
  cols4.forEach((col,i) => {
    const val = i < 3 ? (document.getElementById(`tb-${initIds[i]}`)?.value||'XX') : '11"X17"';
    layer.appendChild(el('text',{id:i<3?`tb-svg-${initIds[i]}`:'',x:cx5+col.w/2,y:cy+10,
      'text-anchor':'middle','font-size':'6','font-family':'Arial','fill':'#000'},val));
    cx5 += col.w;
  });
  cy += 10;
  layer.appendChild(el('line',{x1:TX,y1:cy,x2:TX+TW,y2:cy,stroke:'#000','stroke-width':'0.8'}));

  // ── Sheet No ──────────────────────────
  layer.appendChild(el('text',{x:TX+4,y:cy+10,'font-size':'6','font-family':'Arial','fill':'#000'},'SHEET:'));
  layer.appendChild(el('text',{id:'tb-svg-sheet-no',x:TX+TW/2,y:cy+TH-cy+TY-4,
    'text-anchor':'middle','font-size':'16','font-family':'Arial','font-weight':'bold','fill':'#000'},'C-001'));

  // Scale bar in drawing area
  drawScaleBar(layer, el);
}

function drawLegendSym(layer, sym, x, y, w, h, el) {
  const mx = x + w/2, my = y + h/2;
  switch(sym) {
    case 'line-solid-red':
      layer.appendChild(el('line',{x1:x,y1:my,x2:x+w,y2:my,stroke:'#ff3333','stroke-width':'2.5'}));
      break;
    case 'line-dash':
      layer.appendChild(el('line',{x1:x,y1:my,x2:x+w,y2:my,stroke:'#000','stroke-width':'1.5','stroke-dasharray':'5,3'}));
      [x+2,x+w/2-2,x+w-4].forEach(lx => {
        layer.appendChild(el('line',{x1:lx,y1:y,x2:lx,y2:y+h,stroke:'#000','stroke-width':'0.8'}));
      });
      break;
    case 'fill-veg':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'url(#hatch-veg)',stroke:'#558822','stroke-width':'0.5'}));
      break;
    case 'fill-wet':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'url(#hatch-hz)',stroke:'#2266aa','stroke-width':'0.5'}));
      break;
    case 'fill-pond':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'#2266aa',opacity:'0.7'}));
      break;
    case 'fill-fireroad':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'url(#hatch-diag)',stroke:'#884400','stroke-width':'0.5'}));
      break;
    case 'fill-road':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'#aa9966',opacity:'0.8'}));
      break;
    case 'gate-sym':
      layer.appendChild(el('line',{x1:x,y1:my,x2:x+w*0.3,y2:my,stroke:'#000','stroke-width':'1.5'}));
      layer.appendChild(el('line',{x1:x+w*0.7,y1:my,x2:x+w,y2:my,stroke:'#000','stroke-width':'1.5'}));
      layer.appendChild(el('path',{d:`M${x+w*0.3} ${my-h/3} L${mx} ${my} L${x+w*0.7} ${my-h/3}`,fill:'none',stroke:'#000','stroke-width':'1.5','stroke-linejoin':'round'}));
      break;
    case 'fill-batt':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'#ddeeff',stroke:'#3388cc','stroke-width':'1.5'}));
      break;
    case 'fill-mvt':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'#eeeef8',stroke:'#555577','stroke-width':'1.5'}));
      break;
    case 'fill-fire':
      layer.appendChild(el('rect',{x,y,width:w,height:h,fill:'url(#hatch-diag2)',stroke:'#880000','stroke-width':'0.5'}));
      break;
  }
}

function drawScaleBar(layer, el) {
  // Scale bar at bottom of drawing area
  const sbY = DRAW_Y2 - 20;
  const sbX = DRAW_X1 + 20;
  const sbLen = 120; // 120 units at current scale
  layer.appendChild(el('text',{x:sbX,y:sbY-2,'font-size':'6','font-family':'Arial','fill':'#000'},'SCALE 1:1000'));
  layer.appendChild(el('rect',{x:sbX,y:sbY,width:sbLen,height:8,fill:'#fff',stroke:'#000','stroke-width':'0.8'}));
  [0,1,2,3,4].forEach(i => {
    layer.appendChild(el('rect',{x:sbX+i*30,y:sbY,width:30,height:8,fill:i%2===0?'#000':'#fff',stroke:'#000','stroke-width':'0.5'}));
  });
  ['0','30','60','90','120'].forEach((label,i) => {
    layer.appendChild(el('text',{x:sbX+i*30,y:sbY+16,'text-anchor':'middle','font-size':'5','font-family':'Arial','fill':'#000'},label+'m'));
  });
}

// ═══════════════════════════════════════════════
//  GRID
// ═══════════════════════════════════════════════
function drawGrid() {
  const layer = document.getElementById('grid-layer');
  layer.innerHTML = '';
  if (!gridOn) return;

  const gs = snapSize; // minor grid
  const gm = gs * 5;  // major grid

  // Minor grid
  for (let x = DRAW_X1; x <= DRAW_X2; x += gs) {
    const l = document.createElementNS(SVG_NS,'line');
    l.setAttribute('x1',x); l.setAttribute('y1',DRAW_Y1);
    l.setAttribute('x2',x); l.setAttribute('y2',DRAW_Y2);
    l.setAttribute('stroke','#dde2e8'); l.setAttribute('stroke-width','0.3');
    layer.appendChild(l);
  }
  for (let y = DRAW_Y1; y <= DRAW_Y2; y += gs) {
    const l = document.createElementNS(SVG_NS,'line');
    l.setAttribute('x1',DRAW_X1); l.setAttribute('y1',y);
    l.setAttribute('x2',DRAW_X2); l.setAttribute('y2',y);
    l.setAttribute('stroke','#dde2e8'); l.setAttribute('stroke-width','0.3');
    layer.appendChild(l);
  }
  // Major grid
  for (let x = DRAW_X1; x <= DRAW_X2; x += gm) {
    const l = document.createElementNS(SVG_NS,'line');
    l.setAttribute('x1',x); l.setAttribute('y1',DRAW_Y1);
    l.setAttribute('x2',x); l.setAttribute('y2',DRAW_Y2);
    l.setAttribute('stroke','#c8d0d8'); l.setAttribute('stroke-width','0.5');
    layer.appendChild(l);
  }
  for (let y = DRAW_Y1; y <= DRAW_Y2; y += gm) {
    const l = document.createElementNS(SVG_NS,'line');
    l.setAttribute('x1',DRAW_X1); l.setAttribute('y1',y);
    l.setAttribute('x2',DRAW_X2); l.setAttribute('y2',y);
    l.setAttribute('stroke','#c8d0d8'); l.setAttribute('stroke-width','0.5');
    layer.appendChild(l);
  }
}

// ═══════════════════════════════════════════════
//  COORDINATE TRANSFORM
// ═══════════════════════════════════════════════
function clientToSVG(clientX, clientY) {
  const wrap = document.getElementById('canvas-wrap');
  const rect = wrap.getBoundingClientRect();
  const svgX = (clientX - rect.left - vpX) / vpZoom;
  const svgY = (clientY - rect.top - vpY) / vpZoom;
  return { x: svgX, y: svgY };
}

function snapPt(x, y) {
  if (!snapOn) return {x, y};
  return {
    x: Math.round(x / snapSize) * snapSize,
    y: Math.round(y / snapSize) * snapSize
  };
}

function inDrawArea(x, y) {
  return x >= DRAW_X1 && x <= DRAW_X2 && y >= DRAW_Y1 && y <= DRAW_Y2;
}

// ═══════════════════════════════════════════════
//  TOOL MANAGEMENT
// ═══════════════════════════════════════════════
function setTool(t) {
  tool = t;
  isDrawing = false; drawPoints = []; drawStart = null;
  clearTemp();
  document.querySelectorAll('.tb-btn[id^=btn-]').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('btn-' + t);
  if (btn) btn.classList.add('active');
  document.getElementById('sb-tool').textContent = t.toUpperCase();
  const wrap = document.getElementById('canvas-wrap');
  wrap.className = t === 'select' ? 'mode-select' : '';
}

function setActiveLayer(layerKey) {
  activeLayer = layerKey;
  document.querySelectorAll('.pal-item').forEach(el => el.classList.remove('active-layer'));
  const pal = document.getElementById('pal-' + layerKey);
  if (pal) pal.classList.add('active-layer');
  document.getElementById('sb-layer').textContent = layerKey.toUpperCase().replace('_',' ');
  // Auto-set tool based on layer draw mode
  const ld = LAYERS[layerKey];
  if (ld) {
    const modeMap = {polyline:'polyline', polygon:'polygon', rect:'rect', text:'text', dim:'dim'};
    const sugTool = modeMap[ld.drawMode] || 'polyline';
    setTool(sugTool);
  }
}

// ═══════════════════════════════════════════════
//  MOUSE EVENTS
// ═══════════════════════════════════════════════
function onMouseDown(e) {
  if (e.button === 1 || (e.button === 0 && e.altKey)) {
    isPan = true; panSX = e.clientX - vpX; panSY = e.clientY - vpY;
    return;
  }
  if (e.button !== 0) return;

  const raw = clientToSVG(e.clientX, e.clientY);
  const pt = snapPt(raw.x, raw.y);

  if (tool === 'select') {
    handleSelect(raw.x, raw.y);
    return;
  }

  if (!inDrawArea(pt.x, pt.y)) return;

  if (tool === 'polyline' || tool === 'polygon') {
    if (!isDrawing) {
      isDrawing = true; drawPoints = [pt];
    } else {
      drawPoints.push(pt);
      renderTempPolyline(pt);
    }
  } else if (tool === 'rect') {
    if (!isDrawing) {
      isDrawing = true; drawStart = pt;
    }
  } else if (tool === 'circle') {
    if (!isDrawing) {
      isDrawing = true; drawStart = pt;
    }
  } else if (tool === 'text') {
    const label = prompt('Enter annotation text:');
    if (label) {
      saveUndo();
      objects.push({id:'o'+(++idN), type:'text', layer:activeLayer, x:pt.x, y:pt.y, text:label});
      renderAll();
    }
  } else if (tool === 'dim') {
    if (!isDrawing) {
      isDrawing = true; drawStart = pt;
    }
  }
}

function onMouseMove(e) {
  const raw = clientToSVG(e.clientX, e.clientY);
  const pt = snapPt(raw.x, raw.y);

  // Update coordinate display
  document.getElementById('coord-display').textContent =
    `X: ${(pt.x - DRAW_X1).toFixed(0)}m   Y: ${(DRAW_Y2 - pt.y).toFixed(0)}m`;

  // Snap indicator
  if (snapOn && inDrawArea(raw.x, raw.y)) {
    document.getElementById('snap-indicator').textContent = `●`;
  } else {
    document.getElementById('snap-indicator').textContent = '';
  }

  if (isPan) {
    vpX = e.clientX - panSX; vpY = e.clientY - panSY;
    document.getElementById('drawing-svg').style.transform = `translate(${vpX}px,${vpY}px)`;
    return;
  }

  if (!isDrawing) return;
  clearTemp();

  if (tool === 'polyline' || tool === 'polygon') {
    renderTempPolylinePreview(pt);
  } else if (tool === 'rect' && drawStart) {
    renderTempRect(drawStart, pt);
  } else if (tool === 'circle' && drawStart) {
    renderTempCircle(drawStart, pt);
  } else if (tool === 'dim' && drawStart) {
    renderTempDim(drawStart, pt);
  }
}

function onMouseUp(e) {
  if (isPan) { isPan = false; return; }
  if (!isDrawing) return;

  const raw = clientToSVG(e.clientX, e.clientY);
  const pt = snapPt(raw.x, raw.y);

  if (tool === 'rect' && drawStart) {
    if (Math.abs(pt.x - drawStart.x) > 2 && Math.abs(pt.y - drawStart.y) > 2) {
      saveUndo();
      objects.push({id:'o'+(++idN), type:'rect', layer:activeLayer,
        x:Math.min(drawStart.x,pt.x), y:Math.min(drawStart.y,pt.y),
        w:Math.abs(pt.x-drawStart.x), h:Math.abs(pt.y-drawStart.y)});
      renderAll();
    }
    isDrawing = false; drawStart = null; clearTemp();
  } else if (tool === 'circle' && drawStart) {
    const r = Math.sqrt((pt.x-drawStart.x)**2+(pt.y-drawStart.y)**2);
    if (r > 2) {
      saveUndo();
      objects.push({id:'o'+(++idN), type:'circle', layer:activeLayer,
        cx:drawStart.x, cy:drawStart.y, r});
      renderAll();
    }
    isDrawing = false; drawStart = null; clearTemp();
  } else if (tool === 'dim' && drawStart) {
    saveUndo();
    const dist = Math.sqrt((pt.x-drawStart.x)**2+(pt.y-drawStart.y)**2);
    objects.push({id:'o'+(++idN), type:'dim', layer:'dimension',
      x1:drawStart.x, y1:drawStart.y, x2:pt.x, y2:pt.y,
      value: dist.toFixed(1)+'m'});
    renderAll();
    isDrawing = false; drawStart = null; clearTemp();
  }
}

function onDblClick(e) {
  if ((tool === 'polyline' || tool === 'polygon') && isDrawing && drawPoints.length >= 2) {
    const raw = clientToSVG(e.clientX, e.clientY);
    const pt = snapPt(raw.x, raw.y);
    drawPoints.push(pt);
    saveUndo();
    const closed = tool === 'polygon' || LAYERS[activeLayer]?.closed;
    objects.push({id:'o'+(++idN), type:'polyline', layer:activeLayer,
      points:[...drawPoints], closed});
    isDrawing = false; drawPoints = []; clearTemp();
    renderAll();
  }
}

function onWheel(e) {
  e.preventDefault();
  const factor = e.deltaY < 0 ? 1.12 : 0.89;
  const raw = clientToSVG(e.clientX, e.clientY);
  vpZoom = Math.min(3, Math.max(0.15, vpZoom * factor));
  const wrap = document.getElementById('canvas-wrap');
  const rect = wrap.getBoundingClientRect();
  vpX = e.clientX - rect.left - raw.x * vpZoom;
  vpY = e.clientY - rect.top  - raw.y * vpZoom;
  const svg = document.getElementById('drawing-svg');
  svg.style.transform = `translate(${vpX}px,${vpY}px)`;
  svg.setAttribute('width', SHEET_W * vpZoom);
  svg.setAttribute('height', SHEET_H * vpZoom);
  document.getElementById('sb-zoom').textContent = Math.round(vpZoom*100)+'%';
}

// ═══════════════════════════════════════════════
//  TEMP PREVIEW RENDERING
// ═══════════════════════════════════════════════
function clearTemp() {
  document.getElementById('temp-layer').innerHTML = '';
}

function renderTempPolyline(pt) {}

function renderTempPolylinePreview(pt) {
  const tmpL = document.getElementById('temp-layer');
  tmpL.innerHTML = '';
  const ld = LAYERS[activeLayer] || LAYERS.site_boundary;
  if (drawPoints.length > 0) {
    // Committed segments
    for (let i=0; i<drawPoints.length-1; i++) {
      const l = document.createElementNS(SVG_NS,'line');
      l.setAttribute('x1',drawPoints[i].x);l.setAttribute('y1',drawPoints[i].y);
      l.setAttribute('x2',drawPoints[i+1].x);l.setAttribute('y2',drawPoints[i+1].y);
      l.setAttribute('stroke',ld.color);l.setAttribute('stroke-width',ld.lw);
      if(ld.dash)l.setAttribute('stroke-dasharray',ld.dash);
      tmpL.appendChild(l);
    }
    // Rubber band
    const last = drawPoints[drawPoints.length-1];
    const l2 = document.createElementNS(SVG_NS,'line');
    l2.setAttribute('x1',last.x);l2.setAttribute('y1',last.y);
    l2.setAttribute('x2',pt.x);l2.setAttribute('y2',pt.y);
    l2.setAttribute('stroke',ld.color);l2.setAttribute('stroke-width',ld.lw);
    l2.setAttribute('stroke-dasharray','6,3');l2.setAttribute('opacity','0.7');
    tmpL.appendChild(l2);
    // Snap dot
    addSnapDot(tmpL, pt.x, pt.y);
  }
}

function renderTempRect(start, end) {
  const tmpL = document.getElementById('temp-layer');
  const ld = LAYERS[activeLayer] || LAYERS.battery_container;
  const r = document.createElementNS(SVG_NS,'rect');
  r.setAttribute('x',Math.min(start.x,end.x)); r.setAttribute('y',Math.min(start.y,end.y));
  r.setAttribute('width',Math.abs(end.x-start.x)); r.setAttribute('height',Math.abs(end.y-start.y));
  r.setAttribute('fill', ld.fill==='none'?'none':ld.fill);
  r.setAttribute('fill-opacity',ld.alpha);
  r.setAttribute('stroke',ld.color); r.setAttribute('stroke-width',ld.lw);
  r.setAttribute('stroke-dasharray','6,3');
  tmpL.appendChild(r);
  addSnapDot(tmpL, end.x, end.y);
}

function renderTempCircle(center, pt) {
  const tmpL = document.getElementById('temp-layer');
  const r = Math.sqrt((pt.x-center.x)**2+(pt.y-center.y)**2);
  const c = document.createElementNS(SVG_NS,'circle');
  c.setAttribute('cx',center.x);c.setAttribute('cy',center.y);c.setAttribute('r',r);
  c.setAttribute('fill','none');c.setAttribute('stroke','#aaa');c.setAttribute('stroke-width','1');
  c.setAttribute('stroke-dasharray','6,3');
  tmpL.appendChild(c);
}

function renderTempDim(start, end) {
  const tmpL = document.getElementById('temp-layer');
  const dist = Math.sqrt((end.x-start.x)**2+(end.y-start.y)**2);
  const mid = {x:(start.x+end.x)/2, y:(start.y+end.y)/2};
  const l = document.createElementNS(SVG_NS,'line');
  l.setAttribute('x1',start.x);l.setAttribute('y1',start.y);
  l.setAttribute('x2',end.x);l.setAttribute('y2',end.y);
  l.setAttribute('stroke','#cc9900');l.setAttribute('stroke-width','0.8');
  l.setAttribute('marker-start','url(#dim-arrow)');l.setAttribute('marker-end','url(#dim-arrow)');
  tmpL.appendChild(l);
  const t = document.createElementNS(SVG_NS,'text');
  t.setAttribute('x',mid.x);t.setAttribute('y',mid.y-4);t.setAttribute('text-anchor','middle');
  t.setAttribute('font-size','8');t.setAttribute('font-family','Arial');t.setAttribute('fill','#cc9900');
  t.textContent = dist.toFixed(1)+'m';
  tmpL.appendChild(t);
}

function addSnapDot(layer, x, y) {
  const c = document.createElementNS(SVG_NS,'circle');
  c.setAttribute('cx',x);c.setAttribute('cy',y);c.setAttribute('r','3');
  c.setAttribute('fill','#ff4444');c.setAttribute('opacity','0.8');
  layer.appendChild(c);
}

// ═══════════════════════════════════════════════
//  RENDER ALL OBJECTS
// ═══════════════════════════════════════════════
function renderAll() {
  const layer = document.getElementById('draw-layer');
  layer.innerHTML = '';
  objects.forEach(obj => renderObject(obj, layer));
  updateCountDisplay();
}

function renderObject(obj, layer) {
  const ld = LAYERS[obj.layer] || LAYERS.site_boundary;
  const fillVal = getFill(ld);

  if (obj.type === 'polyline') {
    const el = document.createElementNS(SVG_NS, obj.closed ? 'polygon' : 'polyline');
    const pts = obj.points.map(p=>p.x+','+p.y).join(' ');
    el.setAttribute('points', pts);
    el.setAttribute('fill', obj.closed ? fillVal : 'none');
    if(obj.closed) el.setAttribute('fill-opacity', ld.alpha);
    el.setAttribute('stroke', ld.color);
    el.setAttribute('stroke-width', ld.lw);
    if (ld.dash) el.setAttribute('stroke-dasharray', ld.dash);
    el.setAttribute('data-id', obj.id);
    el.style.cursor = 'pointer';
    el.addEventListener('click', () => selectObject(obj.id));
    layer.appendChild(el);

    // Labels for equipment
    if (obj.layer === 'battery_container' || obj.layer === 'mv_transformer') {
      addLabel(layer, obj.points, obj.layer === 'battery_container' ? 'BESS' : 'MVT', ld.color);
    }
  } else if (obj.type === 'rect') {
    const r = document.createElementNS(SVG_NS,'rect');
    r.setAttribute('x',obj.x); r.setAttribute('y',obj.y);
    r.setAttribute('width',obj.w); r.setAttribute('height',obj.h);
    r.setAttribute('fill', fillVal);
    r.setAttribute('fill-opacity', ld.alpha);
    r.setAttribute('stroke', ld.color); r.setAttribute('stroke-width', ld.lw);
    r.setAttribute('data-id',obj.id);
    r.style.cursor='pointer';
    r.addEventListener('click',()=>selectObject(obj.id));
    layer.appendChild(r);
    // Label inside rect
    const cx = obj.x + obj.w/2, cy = obj.y + obj.h/2;
    const labMap = {battery_container:'BESS CONTAINER', mv_transformer:'MV TRANSFORMER', access_gate:'GATE', fire_staging:'FIRE STAGING'};
    if (labMap[obj.layer]) {
      const t = document.createElementNS(SVG_NS,'text');
      t.setAttribute('x',cx);t.setAttribute('y',cy+3);t.setAttribute('text-anchor','middle');
      t.setAttribute('font-size',Math.min(obj.h*0.2, 10));t.setAttribute('font-family','Arial');
      t.setAttribute('fill',ld.color);t.setAttribute('font-weight','bold');
      t.setAttribute('pointer-events','none');t.textContent=labMap[obj.layer];
      layer.appendChild(t);
    }
  } else if (obj.type === 'circle') {
    const c = document.createElementNS(SVG_NS,'circle');
    c.setAttribute('cx',obj.cx);c.setAttribute('cy',obj.cy);c.setAttribute('r',obj.r);
    c.setAttribute('fill',fillVal);c.setAttribute('fill-opacity',ld.alpha);
    c.setAttribute('stroke',ld.color);c.setAttribute('stroke-width',ld.lw);
    c.setAttribute('data-id',obj.id);c.style.cursor='pointer';
    c.addEventListener('click',()=>selectObject(obj.id));
    layer.appendChild(c);
  } else if (obj.type === 'text') {
    const t = document.createElementNS(SVG_NS,'text');
    t.setAttribute('x',obj.x);t.setAttribute('y',obj.y);
    t.setAttribute('font-size','12');t.setAttribute('font-family','Arial');
    t.setAttribute('fill','#000');t.setAttribute('data-id',obj.id);
    t.style.cursor='pointer';
    t.textContent=obj.text;
    t.addEventListener('click',()=>selectObject(obj.id));
    layer.appendChild(t);
  } else if (obj.type === 'dim') {
    const mid = {x:(obj.x1+obj.x2)/2, y:(obj.y1+obj.y2)/2};
    const l = document.createElementNS(SVG_NS,'line');
    l.setAttribute('x1',obj.x1);l.setAttribute('y1',obj.y1);
    l.setAttribute('x2',obj.x2);l.setAttribute('y2',obj.y2);
    l.setAttribute('stroke','#cc9900');l.setAttribute('stroke-width','0.8');
    l.setAttribute('marker-start','url(#dim-arrow)');l.setAttribute('marker-end','url(#dim-arrow)');
    l.setAttribute('data-id',obj.id);l.style.cursor='pointer';
    l.addEventListener('click',()=>selectObject(obj.id));
    layer.appendChild(l);
    // Extension lines
    [[obj.x1,obj.y1],[obj.x2,obj.y2]].forEach(([ex,ey]) => {
      const ext = document.createElementNS(SVG_NS,'line');
      ext.setAttribute('x1',ex);ext.setAttribute('y1',ey-8);
      ext.setAttribute('x2',ex);ext.setAttribute('y2',ey+8);
      ext.setAttribute('stroke','#cc9900');ext.setAttribute('stroke-width','0.6');
      layer.appendChild(ext);
    });
    const t = document.createElementNS(SVG_NS,'text');
    t.setAttribute('x',mid.x);t.setAttribute('y',mid.y-6);t.setAttribute('text-anchor','middle');
    t.setAttribute('font-size','9');t.setAttribute('font-family','Arial');t.setAttribute('fill','#cc9900');
    t.setAttribute('font-weight','bold');t.textContent=obj.value;
    layer.appendChild(t);
  }
}

function getFill(ld) {
  if(ld.fill==='none') return 'none';
  const hatchMap = {veg:'url(#hatch-veg)', hz:'url(#hatch-hz)', diag:'url(#hatch-diag)', diag2:'url(#hatch-diag2)'};
  if(ld.hatch && hatchMap[ld.hatch]) return hatchMap[ld.hatch];
  return ld.fill;
}

function addLabel(layer, points, text, color) {
  if (!points || points.length < 3) return;
  let cx=0, cy=0;
  points.forEach(p=>{cx+=p.x;cy+=p.y;});
  cx/=points.length; cy/=points.length;
  const t = document.createElementNS(SVG_NS,'text');
  t.setAttribute('x',cx);t.setAttribute('y',cy+3);t.setAttribute('text-anchor','middle');
  t.setAttribute('font-size','10');t.setAttribute('font-family','Arial');
  t.setAttribute('fill',color);t.setAttribute('font-weight','bold');
  t.setAttribute('pointer-events','none');t.textContent=text;
  layer.appendChild(t);
}

// ═══════════════════════════════════════════════
//  SELECTION
// ═══════════════════════════════════════════════
function handleSelect(x, y) {
  // Check if clicking an existing object
  const hit = objects.find(obj => hitTest(obj, x, y));
  selectObject(hit ? hit.id : null);
}

function selectObject(id) {
  selected = id;
  const selLayer = document.getElementById('sel-layer');
  selLayer.innerHTML = '';
  if (!id) {
    document.getElementById('props-empty').style.display='block';
    document.getElementById('props-fields').style.display='none';
    return;
  }
  const obj = objects.find(o=>o.id===id);
  if (!obj) return;

  // Highlight with bounding box
  const bb = getBBox(obj);
  if (bb) {
    const r = document.createElementNS(SVG_NS,'rect');
    r.setAttribute('x',bb.x-3);r.setAttribute('y',bb.y-3);
    r.setAttribute('width',bb.w+6);r.setAttribute('height',bb.h+6);
    r.setAttribute('fill','none');r.setAttribute('stroke','#ff9900');
    r.setAttribute('stroke-width','1.5');r.setAttribute('stroke-dasharray','6,3');
    r.setAttribute('pointer-events','none');
    selLayer.appendChild(r);
    // Corner handles
    [[bb.x-3,bb.y-3],[bb.x+bb.w+3,bb.y-3],[bb.x-3,bb.y+bb.h+3],[bb.x+bb.w+3,bb.y+bb.h+3]].forEach(([hx,hy])=>{
      const h = document.createElementNS(SVG_NS,'rect');
      h.setAttribute('x',hx-3);h.setAttribute('y',hy-3);h.setAttribute('width','6');h.setAttribute('height','6');
      h.setAttribute('fill','#ff9900');h.setAttribute('pointer-events','none');
      selLayer.appendChild(h);
    });
  }

  // Show properties
  document.getElementById('props-empty').style.display='none';
  const pf = document.getElementById('props-fields');
  pf.style.display='block';
  const ld = LAYERS[obj.layer];
  pf.innerHTML = `
    <div class="rp-field"><label class="rp-label">TYPE</label><span style="font-size:10px;color:var(--text)">${obj.type.toUpperCase()}</span></div>
    <div class="rp-field"><label class="rp-label">LAYER</label><span style="font-size:10px;color:var(--accent)">${ld?.name||obj.layer}</span></div>
    ${obj.type==='rect'?`<div class="rp-field"><label class="rp-label">SIZE</label><span style="font-size:10px;color:var(--text)">${Math.round(obj.w)}m × ${Math.round(obj.h)}m</span></div>`:'' }
    ${obj.type==='text'?`<div class="rp-field"><label class="rp-label">TEXT</label><input class="rp-input" value="${obj.text}" oninput="updateObjProp('${obj.id}','text',this.value)"></div>`:''}
    <button class="rp-input" style="margin-top:6px;cursor:pointer;color:#ff6b6b;background:rgba(255,107,107,0.1);border-color:rgba(255,107,107,0.3);" onclick="deleteSelected()">DELETE OBJECT</button>
  `;
}

function hitTest(obj, x, y) {
  const bb = getBBox(obj);
  if (!bb) return false;
  return x >= bb.x-5 && x <= bb.x+bb.w+5 && y >= bb.y-5 && y <= bb.y+bb.h+5;
}

function getBBox(obj) {
  if (obj.type === 'rect') return {x:obj.x, y:obj.y, w:obj.w, h:obj.h};
  if (obj.type === 'circle') return {x:obj.cx-obj.r, y:obj.cy-obj.r, w:obj.r*2, h:obj.r*2};
  if (obj.type === 'polyline' && obj.points?.length) {
    const xs = obj.points.map(p=>p.x), ys = obj.points.map(p=>p.y);
    const x=Math.min(...xs),y=Math.min(...ys);
    return {x, y, w:Math.max(...xs)-x, h:Math.max(...ys)-y};
  }
  if (obj.type === 'text') return {x:obj.x-2, y:obj.y-14, w:100, h:16};
  if (obj.type === 'dim') {
    const x=Math.min(obj.x1,obj.x2),y=Math.min(obj.y1,obj.y2);
    return {x, y, w:Math.abs(obj.x2-obj.x1)||10, h:Math.abs(obj.y2-obj.y1)||10};
  }
  return null;
}

// ═══════════════════════════════════════════════
//  UNDO / REDO
// ═══════════════════════════════════════════════
function saveUndo() {
  undoStack.push(JSON.stringify(objects));
  if (undoStack.length > 50) undoStack.shift();
  redoStack = [];
}

function doUndo() {
  if (!undoStack.length) return;
  redoStack.push(JSON.stringify(objects));
  objects = JSON.parse(undoStack.pop());
  selected = null;
  document.getElementById('sel-layer').innerHTML='';
  renderAll();
}

function doRedo() {
  if (!redoStack.length) return;
  undoStack.push(JSON.stringify(objects));
  objects = JSON.parse(redoStack.pop());
  renderAll();
}

function deleteSelected() {
  if (!selected) return;
  saveUndo();
  objects = objects.filter(o=>o.id!==selected);
  selected = null;
  document.getElementById('sel-layer').innerHTML='';
  selectObject(null);
  renderAll();
}

function clearAll() {
  if (!confirm('Clear all drawing objects?')) return;
  saveUndo();
  objects = []; selected = null;
  document.getElementById('sel-layer').innerHTML='';
  selectObject(null);
  renderAll();
}

function updateObjProp(id, key, val) {
  const obj = objects.find(o=>o.id===id);
  if (obj) { obj[key]=val; renderAll(); }
}

// ═══════════════════════════════════════════════
//  TITLE BLOCK UPDATE
// ═══════════════════════════════════════════════
function updateTitleBlock() {
  const get = id => document.getElementById(id)?.value || '';
  const set = (id, val) => { const el=document.getElementById(id); if(el) el.textContent=val; };

  set('tb-svg-project', get('tb-project'));
  set('tb-svg-design', get('tb-design-pct') + '% DESIGN');
  set('tb-svg-client', get('tb-client'));
  set('tb-svg-ref', get('tb-ref'));
  set('tb-svg-sheet-name', get('tb-sheet-name'));
  set('tb-svg-sheet-no', get('tb-sheet-no'));
  set('tb-svg-latlong', get('tb-latlong'));
  set('tb-svg-drwn', get('tb-drwn'));
  set('tb-svg-revw', get('tb-revw'));
  set('tb-svg-apprvd', get('tb-apprvd'));

  // Update revision rows
  document.querySelectorAll('[id^="rev-input-"]').forEach(input => {
    const parts = input.id.replace('rev-input-','').split('-');
    const ri = parseInt(parts[0]);
    const key = parts[1];
    if (revData[ri]) {
      revData[ri][key] = input.value;
      const svgEl = document.getElementById(`tb-svg-rev${ri}-${key}`);
      if (svgEl) svgEl.textContent = input.value;
    }
  });
}

function buildRevRows() {
  const container = document.getElementById('rev-rows');
  container.innerHTML = '';
  revData.forEach((row, i) => {
    const div = document.createElement('div');
    div.className = 'rev-row';
    div.innerHTML = `
      <div style="font-size:9px;color:var(--accent);text-align:center;padding-top:4px">${row.rev}</div>
      <input class="rev-cell" id="rev-input-${i}-desc" value="${row.desc}" oninput="updateTitleBlock()" placeholder="Description">
      <input class="rev-cell" id="rev-input-${i}-by"   value="${row.by}"   oninput="updateTitleBlock()" placeholder="BY">
      <input class="rev-cell" id="rev-input-${i}-date" value="${row.date}" oninput="updateTitleBlock()" placeholder="YYYY/M/DD">
    `;
    container.appendChild(div);
  });
}

// ═══════════════════════════════════════════════
//  ZOOM / PAN
// ═══════════════════════════════════════════════
function toggleSnap() {
  snapOn = !snapOn;
  document.getElementById('btn-snap').textContent = 'SNAP:'+(snapOn?'ON':'OFF');
  document.getElementById('sb-snap').textContent = snapOn?'20m':'OFF';
}

function toggleGrid() {
  gridOn = !gridOn;
  document.getElementById('btn-grid').textContent = 'GRID:'+(gridOn?'ON':'OFF');
  drawGrid();
}

function zoomFit() {
  const wrap = document.getElementById('canvas-wrap');
  const ww = wrap.clientWidth, wh = wrap.clientHeight;
  const zx = ww / SHEET_W, zy = wh / SHEET_H;
  vpZoom = Math.min(zx, zy) * 0.95;
  vpX = (ww - SHEET_W*vpZoom)/2;
  vpY = (wh - SHEET_H*vpZoom)/2;
  const svg = document.getElementById('drawing-svg');
  svg.style.transform = `translate(${vpX}px,${vpY}px)`;
  svg.setAttribute('width', SHEET_W*vpZoom);
  svg.setAttribute('height', SHEET_H*vpZoom);
  document.getElementById('sb-zoom').textContent = Math.round(vpZoom*100)+'%';
}

function zoomIn() { fakeWheel(-1); }
function zoomOut() { fakeWheel(1); }

function fakeWheel(dir) {
  const factor = dir < 0 ? 1.2 : 0.83;
  const cx = SHEET_W/2, cy = SHEET_H/2;
  vpZoom = Math.min(3, Math.max(0.15, vpZoom * factor));
  const svg = document.getElementById('drawing-svg');
  svg.style.transform = `translate(${vpX}px,${vpY}px)`;
  svg.setAttribute('width', SHEET_W*vpZoom);
  svg.setAttribute('height', SHEET_H*vpZoom);
  document.getElementById('sb-zoom').textContent = Math.round(vpZoom*100)+'%';
}

function updateCountDisplay() {
  document.getElementById('sb-count').textContent = objects.length;
}

// ═══════════════════════════════════════════════
//  KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════
document.addEventListener('keydown', e => {
  if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
  const k = e.key.toLowerCase();
  if(k==='v')setTool('select');
  if(k==='p')setTool('polyline');
  if(k==='r')setTool('rect');
  if(k==='g')setTool('polygon');
  if(k==='c')setTool('circle');
  if(k==='t')setTool('text');
  if(k==='d')setTool('dim');
  if(k==='f')zoomFit();
  if(k==='escape'){setTool('select');isDrawing=false;drawPoints=[];drawStart=null;clearTemp();}
  if(k==='delete'||k==='backspace'){e.preventDefault();deleteSelected();}
  if((e.ctrlKey||e.metaKey)&&k==='z'){e.preventDefault();doUndo();}
  if((e.ctrlKey||e.metaKey)&&k==='y'){e.preventDefault();doRedo();}
});

// ═══════════════════════════════════════════════
//  DRAG & DROP from palette
// ═══════════════════════════════════════════════
let dragLayerKey = null;
document.querySelectorAll('.pal-item').forEach(el => {
  el.setAttribute('draggable','true');
  el.addEventListener('dragstart', ev => {
    dragLayerKey = el.id.replace('pal-','');
    ev.dataTransfer?.setData('text/plain', dragLayerKey);
  });
});

function onDrop(e) {
  e.preventDefault();
  const key = e.dataTransfer?.getData('text/plain') || dragLayerKey;
  if (!key) return;
  const raw = clientToSVG(e.clientX, e.clientY);
  const pt = snapPt(raw.x, raw.y);
  if (!inDrawArea(pt.x, pt.y)) return;
  setActiveLayer(key);

  // Auto-place rect-type components
  const ld = LAYERS[key];
  if (ld && (ld.drawMode === 'rect' || key === 'battery_container' || key === 'mv_transformer')) {
    const defW = key==='battery_container'?80:key==='mv_transformer'?60:key==='access_gate'?40:60;
    const defH = key==='battery_container'?40:key==='mv_transformer'?40:key==='access_gate'?30:40;
    saveUndo();
    objects.push({id:'o'+(++idN), type:'rect', layer:key,
      x:pt.x-defW/2, y:pt.y-defH/2, w:defW, h:defH});
    renderAll();
  }
}

// ═══════════════════════════════════════════════
//  EXPORT — SVG
// ═══════════════════════════════════════════════
function exportSVG() {
  const svg = document.getElementById('drawing-svg');
  const serializer = new XMLSerializer();
  const svgStr = '<?xml version="1.0" encoding="UTF-8"?>\\n' + serializer.serializeToString(svg);
  const blob = new Blob([svgStr], {type:'image/svg+xml'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (document.getElementById('tb-project')?.value||'BESS_Site').replace(/\\s+/g,'_') + '_SitePlan.svg';
  a.click();
}

// ═══════════════════════════════════════════════
//  EXPORT — DXF (AutoCAD compatible)
// ═══════════════════════════════════════════════
function exportDXF() {
  const proj = document.getElementById('tb-project')?.value || 'BESS_PROJECT';
  const scale = document.getElementById('tb-scale')?.value || '1:1000';
  const scaleNum = parseInt(scale.split(':')[1]) || 1000;

  // DXF layer colors (ACI color codes)
  const layerColors = {
    site_boundary:8,fence:7,vegetation:3,wetlands:5,pond:5,
    fire_road:1,access_road:2,access_gate:7,battery_container:5,
    mv_transformer:6,fire_staging:1,annotation:7,dimension:2
  };

  let dxf = '';
  // HEADER
  dxf += '0\\nSECTION\\n2\\nHEADER\\n';
  dxf += '9\\n$ACADVER\\n1\\nAC1021\\n'; // AutoCAD 2007
  dxf += '9\\n$INSUNITS\\n70\\n6\\n'; // meters
  dxf += '9\\n$MEASUREMENT\\n70\\n1\\n'; // metric
  dxf += '0\\nENDSEC\\n';

  // TABLES
  dxf += '0\\nSECTION\\n2\\nTABLES\\n';
  dxf += '0\\nTABLE\\n2\\nLAYER\\n70\\n'+Object.keys(LAYERS).length+'\\n';
  Object.entries(LAYERS).forEach(([key, ld]) => {
    dxf += `0\\nLAYER\\n2\\n${key.toUpperCase()}\\n70\\n0\\n62\\n${layerColors[key]||7}\\n6\\nCONTINUOUS\\n`;
  });
  dxf += '0\\nENDTAB\\n0\\nENDSEC\\n';

  // ENTITIES
  dxf += '0\\nSECTION\\n2\\nENTITIES\\n';

  // Sheet border
  const toReal = v => (v * scaleNum / 1000).toFixed(4);
  const toRealY = v => ((SHEET_H - v) * scaleNum / 1000).toFixed(4); // flip Y

  objects.forEach(obj => {
    const layerName = obj.layer?.toUpperCase() || 'OBJECTS';
    if (obj.type === 'polyline' || obj.type === 'polygon') {
      dxf += `0\\nLWPOLYLINE\\n8\\n${layerName}\\n90\\n${obj.points.length}\\n70\\n${obj.closed?1:0}\\n`;
      obj.points.forEach(p => {
        dxf += `10\\n${toReal(p.x)}\\n20\\n${toRealY(p.y)}\\n`;
      });
    } else if (obj.type === 'rect') {
      // Output as closed polyline
      dxf += `0\\nLWPOLYLINE\\n8\\n${layerName}\\n90\\n4\\n70\\n1\\n`;
      [[obj.x,obj.y],[obj.x+obj.w,obj.y],[obj.x+obj.w,obj.y+obj.h],[obj.x,obj.y+obj.h]].forEach(([x,y])=>{
        dxf += `10\\n${toReal(x)}\\n20\\n${toRealY(y)}\\n`;
      });
      // Add text label for equipment
      const labMap = {battery_container:'BESS CONTAINER',mv_transformer:'MV TRANSFORMER'};
      if(labMap[obj.layer]) {
        dxf += `0\\nTEXT\\n8\\n${layerName}\\n10\\n${toReal(obj.x+obj.w/2)}\\n20\\n${toRealY(obj.y+obj.h/2)}\\n30\\n0\\n40\\n${toReal(8)}\\n1\\n${labMap[obj.layer]}\\n72\\n1\\n11\\n${toReal(obj.x+obj.w/2)}\\n21\\n${toRealY(obj.y+obj.h/2)}\\n`;
      }
    } else if (obj.type === 'circle') {
      dxf += `0\\nCIRCLE\\n8\\n${layerName}\\n10\\n${toReal(obj.cx)}\\n20\\n${toRealY(obj.cy)}\\n40\\n${toReal(obj.r)}\\n`;
    } else if (obj.type === 'text') {
      dxf += `0\\nTEXT\\n8\\nANNOTATION\\n10\\n${toReal(obj.x)}\\n20\\n${toRealY(obj.y)}\\n30\\n0\\n40\\n${toReal(10)}\\n1\\n${obj.text}\\n`;
    } else if (obj.type === 'dim') {
      const mx = (parseFloat(toReal(obj.x1))+parseFloat(toReal(obj.x2)))/2;
      const my = (parseFloat(toRealY(obj.y1))+parseFloat(toRealY(obj.y2)))/2;
      dxf += `0\\nLINE\\n8\\nDIMENSION\\n10\\n${toReal(obj.x1)}\\n20\\n${toRealY(obj.y1)}\\n11\\n${toReal(obj.x2)}\\n21\\n${toRealY(obj.y2)}\\n`;
      dxf += `0\\nTEXT\\n8\\nDIMENSION\\n10\\n${mx}\\n20\\n${my+3}\\n30\\n0\\n40\\n${toReal(8)}\\n1\\n${obj.value}\\n72\\n1\\n11\\n${mx}\\n21\\n${my+3}\\n`;
    }
  });

  // Title block as DXF text entities
  const tbData2 = {
    'PROJECT': document.getElementById('tb-project')?.value||'',
    'SHEET NAME': document.getElementById('tb-sheet-name')?.value||'',
    'SHEET NO': document.getElementById('tb-sheet-no')?.value||'',
    'DRAWN BY': document.getElementById('tb-drwn')?.value||'',
    'SCALE': scale,
  };
  let ty = 5;
  Object.entries(tbData2).forEach(([k,v]) => {
    dxf += `0\\nTEXT\\n8\\nTITLEBLOCK\\n10\\n${toReal(SHEET_W-TB_W/2)}\\n20\\n${ty}\\n30\\n0\\n40\\n3\\n1\\n${k}: ${v}\\n72\\n1\\n11\\n${toReal(SHEET_W-TB_W/2)}\\n21\\n${ty}\\n`;
    ty += 5;
  });

  dxf += '0\\nENDSEC\\n0\\nEOF\\n';

  const filename = proj.replace(/\\s+/g,'_') + '_SitePlan.dxf';
  const blob = new Blob([dxf], {type:'application/dxf'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; a.click();

  // Also offer DWG note
  setTimeout(()=>{
    if(confirm('DXF exported!\\n\\nTo convert to .DWG format:\\n• Open in AutoCAD → Save As → AutoCAD DWG\\n• Or use free tool: ODA File Converter (opendesign.com)\\n\\nClick OK to open ODA File Converter download page.')) {
      window.open('https://www.opendesign.com/guestfiles/oda_file_converter','_blank');
    }
  }, 300);
}

// ═══════════════════════════════════════════════
//  EXPORT — PDF with SunStripe template
// ═══════════════════════════════════════════════
function exportPDF() {
  const { jsPDF } = window.jspdf;

  // 17"×11" landscape = 432×279mm
  const doc = new jsPDF({orientation:'landscape', unit:'mm', format:[432,279]});
  const PW = 432, PH = 279;

  // Scale factor: SHEET_W SVG units → PW mm
  const scX = PW / SHEET_W;
  const scY = PH / SHEET_H;

  function mm(svgX) { return svgX * scX; }
  function mmY(svgY) { return svgY * scY; }

  // White background
  doc.setFillColor(255,255,255);
  doc.rect(0,0,PW,PH,'F');

  // Outer border
  doc.setDrawColor(0,0,0); doc.setLineWidth(0.4);
  doc.rect(mm(10),mmY(10),mm(SHEET_W-20),mmY(SHEET_H-20));

  // Drawing area border
  doc.setFillColor(248,249,250);
  doc.rect(mm(DRAW_X1),mmY(DRAW_Y1),mm(DRAW_W),mmY(DRAW_H),'FD');

  // Copyright line
  doc.setFontSize(4); doc.setFont('helvetica','bold'); doc.setTextColor(0,0,0);
  doc.text('THIS DRAWING IS THE PROPERTY OF SUNSTRIPE, Inc. ANY REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN PERMISSION OF SUNSTRIPE, Inc IS PROHIBITED.',
    mm(DRAW_X1+4), mmY(DRAW_Y1-6));

  // Bottom note
  doc.setFontSize(5); doc.setFont('helvetica','bolditalic');
  doc.text('FOR INFORMATION PURPOSES ONLY - NOT FOR CONSTRUCTION', PW/2, mmY(SHEET_H-MARGIN+10), {align:'center'});

  // ── Title block ─────────────────────────────
  const TX = TB_X, TY2 = TB_Y, TW = TB_W-6;
  doc.setFillColor(255,255,255);
  doc.setDrawColor(0,0,0); doc.setLineWidth(0.3);
  doc.rect(mm(TX), mmY(TY2), mm(TW), mmY(DRAW_H),'FD');

  let cy2 = TY2 + 4;

  // North arrow box
  const northH = 80;
  doc.setFillColor(240,240,240);
  doc.rect(mm(TX),mmY(cy2),mm(TW),mmY(northH),'F');
  doc.setDrawColor(0); doc.setLineWidth(0.2);
  doc.rect(mm(TX),mmY(cy2),mm(TW),mmY(northH));
  // North circle
  const ncx2 = mm(TX+TW/2), ncy2 = mmY(cy2+northH/2);
  doc.setDrawColor(0); doc.setLineWidth(0.3);
  doc.circle(ncx2, ncy2, mm(28));
  // Arrow (simplified)
  doc.setFillColor(0,0,0);
  doc.triangle(ncx2-mm(8),ncy2+mm(10), ncx2,ncy2-mm(24), ncx2+mm(8),ncy2+mm(10),'F');
  doc.setFontSize(10); doc.setFont('helvetica','bold');
  doc.text('N', ncx2, ncy2-mmY(30), {align:'center'});
  cy2 += northH;

  doc.setLineWidth(0.4);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // Legends
  const legHeaderH = 14;
  doc.setFillColor(232,232,232);
  doc.rect(mm(TX),mmY(cy2),mm(TW),mmY(legHeaderH),'F');
  doc.setFontSize(5.5); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text('LEGENDS', mm(TX+TW/2), mmY(cy2+10), {align:'center'});
  cy2 += legHeaderH;

  const legendPDF = [
    ['─────','SITE BOUNDARY','#ff3333'],
    ['- - -','FENCE','#222'],
    ['▓▓▓▓','VEGETATION','#558822'],
    ['≡≡≡≡','WETLANDS','#2266aa'],
    ['████','STORM WATER POND','#2266aa'],
    ['////','FIRE BATTERY ACCESS ROAD','#cc7733'],
    ['████','ACCESS ROAD','#aa9966'],
    ['⊿⊿⊿','ACCESS GATE','#222'],
    ['□□□□','BATTERY CONTAINER','#3388cc'],
    ['□□□□','MV TRANSFORMER','#555577'],
    ['XXXX','FIRE STAGING AREA','#990000'],
  ];
  const legRH = 16;
  legendPDF.forEach(([sym,label,color]) => {
    doc.setLineWidth(0.2); doc.setDrawColor(200,200,200);
    doc.rect(mm(TX),mmY(cy2),mm(TW),mmY(legRH));
    // Color swatch
    const rgb = hexToRGB(color);
    doc.setFillColor(rgb.r,rgb.g,rgb.b);
    doc.rect(mm(TX+2),mmY(cy2+3),mm(14),mmY(legRH-6),'F');
    doc.setFontSize(5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
    doc.text(label, mm(TX+18), mmY(cy2+10));
    cy2 += legRH;
  });
  doc.setLineWidth(0.4);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // Project name
  const projH2 = 80;
  doc.setFontSize(11); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  doc.text(document.getElementById('tb-project')?.value||'PROJECT NAME',
    mm(TX+TW/2), mmY(cy2+28), {align:'center'});
  doc.setFontSize(9);
  doc.text((document.getElementById('tb-design-pct')?.value||'30')+'% DESIGN',
    mm(TX+TW/2), mmY(cy2+44), {align:'center'});
  doc.setFontSize(6); doc.setFont('helvetica','normal'); doc.setTextColor(80);
  doc.text(document.getElementById('tb-client')?.value||'CLIENT NAME',
    mm(TX+TW/2), mmY(cy2+58), {align:'center'});
  doc.text(document.getElementById('tb-ref')?.value||'REF',
    mm(TX+TW/2), mmY(cy2+68), {align:'center'});
  cy2 += projH2;
  doc.setDrawColor(0); doc.setLineWidth(0.4);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // Revision table
  const revHdr = 12;
  doc.setFillColor(232,232,232);
  doc.rect(mm(TX),mmY(cy2),mm(TW),mmY(revHdr+2),'F');
  doc.setLineWidth(0.2); doc.setDrawColor(150,150,150);
  doc.setFontSize(5); doc.setFont('helvetica','bold'); doc.setTextColor(0);
  const revCols2 = [{l:'REV',w:18},{l:'DESCRIPTION',w:TW-96},{l:'BY',w:28},{l:'DATE',w:50}];
  let rcx = TX;
  revCols2.forEach(col => {
    doc.rect(mm(rcx),mmY(cy2),mm(col.w),mmY(revHdr+2));
    doc.text(col.l, mm(rcx+col.w/2), mmY(cy2+9), {align:'center'});
    rcx += col.w;
  });
  cy2 += revHdr+2;
  const revRH = 11;
  revData.forEach((row,ri) => {
    let rcx2=TX;
    revCols2.forEach((col,ci) => {
      doc.setLineWidth(0.15); doc.setDrawColor(200,200,200);
      doc.rect(mm(rcx2),mmY(cy2),mm(col.w),mmY(revRH));
      doc.setFontSize(4.5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
      const vals = [row.rev, row.desc, row.by, row.date];
      if(vals[ci]) doc.text(vals[ci], mm(rcx2+2), mmY(cy2+7.5));
      rcx2 += col.w;
    });
    cy2 += revRH;
  });
  cy2 += 3;
  doc.setLineWidth(0.4); doc.setDrawColor(0);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // SunStripe branding
  const brandH2 = 46;
  doc.setFontSize(12); doc.setFont('helvetica','bold'); doc.setTextColor(220,34,0);
  doc.text('SunStripe', mm(TX+TW/2), mmY(cy2+20), {align:'center'});
  doc.setFontSize(5.5); doc.setFont('helvetica','normal'); doc.setTextColor(68,68,68);
  doc.text('Trusted Clean Energy Partners', mm(TX+TW/2), mmY(cy2+30), {align:'center'});
  doc.text('6363 N State Highway 161, Ste 250 Irving, TX 75038', mm(TX+TW/2), mmY(cy2+40), {align:'center'});
  cy2 += brandH2;
  doc.setDrawColor(0); doc.setLineWidth(0.4);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // Sheet name
  doc.setFontSize(5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
  doc.text('SHEET NAME:', mm(TX+3), mmY(cy2+10));
  doc.setFontSize(8); doc.setFont('helvetica','bold');
  doc.text(document.getElementById('tb-sheet-name')?.value||'SITE PLAN', mm(TX+TW/2), mmY(cy2+22), {align:'center'});
  cy2 += 30;
  doc.setDrawColor(150,150,150); doc.setLineWidth(0.2);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // Lat/Long
  doc.setFontSize(5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
  doc.text('LAT/LONG:', mm(TX+3), mmY(cy2+10));
  doc.text(document.getElementById('tb-latlong')?.value||'XX / -XX', mm(TX+40), mmY(cy2+10));
  cy2 += 14;
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // DRWN/REVW/APPRVD/SIZE
  const dras = [{l:'DRWN',v:document.getElementById('tb-drwn')?.value||'XX',w:TW*0.22},
                {l:'REVW',v:document.getElementById('tb-revw')?.value||'XX',w:TW*0.22},
                {l:'APPRVD',v:document.getElementById('tb-apprvd')?.value||'XX',w:TW*0.28},
                {l:'SIZE',v:'11"X17"',w:TW*0.28}];
  let dx=TX;
  doc.setFontSize(5); doc.setFont('helvetica','bold');
  dras.forEach(col => {
    doc.setLineWidth(0.2); doc.rect(mm(dx),mmY(cy2),mm(col.w),mmY(20));
    doc.text(col.l, mm(dx+col.w/2), mmY(cy2+8), {align:'center'});
    doc.setFont('helvetica','normal'); doc.setFontSize(5.5);
    doc.text(col.v, mm(dx+col.w/2), mmY(cy2+16), {align:'center'});
    doc.setFont('helvetica','bold'); doc.setFontSize(5);
    dx += col.w;
  });
  cy2 += 20;
  doc.setLineWidth(0.4); doc.setDrawColor(0);
  doc.line(mm(TX),mmY(cy2),mm(TX+TW),mmY(cy2));

  // Sheet No
  doc.setFontSize(5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
  doc.text('SHEET:', mm(TX+3), mmY(cy2+10));
  doc.setFontSize(14); doc.setFont('helvetica','bold');
  const snBottom = mmY(TY2 + DRAW_H - 8);
  doc.text(document.getElementById('tb-sheet-no')?.value||'C-001', mm(TX+TW/2), snBottom, {align:'center'});

  // ── Draw objects onto PDF ─────────────────────
  objects.forEach(obj => {
    const ld = LAYERS[obj.layer] || LAYERS.site_boundary;
    const rgb = hexToRGB(ld.color);
    const frgb = ld.fill && ld.fill!=='none' ? hexToRGB(ld.fill) : null;
    doc.setDrawColor(rgb.r,rgb.g,rgb.b);
    doc.setLineWidth(ld.lw*0.3);

    if (obj.type === 'polyline') {
      if (frgb) {
        doc.setFillColor(frgb.r,frgb.g,frgb.b);
      }
      const pts = obj.points;
      if (pts.length < 2) return;
      for (let i=0; i<pts.length-1; i++) {
        doc.line(mm(pts[i].x),mmY(pts[i].y),mm(pts[i+1].x),mmY(pts[i+1].y));
      }
      if (obj.closed && pts.length > 1) {
        doc.line(mm(pts[pts.length-1].x),mmY(pts[pts.length-1].y),mm(pts[0].x),mmY(pts[0].y));
      }
    } else if (obj.type === 'rect') {
      if (frgb) {
        doc.setFillColor(frgb.r,frgb.g,frgb.b);
        doc.rect(mm(obj.x),mmY(obj.y),mm(obj.w),mmY(obj.h),'FD');
      } else {
        doc.rect(mm(obj.x),mmY(obj.y),mm(obj.w),mmY(obj.h));
      }
      const labMap = {battery_container:'BESS',mv_transformer:'MVT'};
      if(labMap[obj.layer]) {
        doc.setFontSize(5); doc.setFont('helvetica','bold'); doc.setTextColor(rgb.r,rgb.g,rgb.b);
        doc.text(labMap[obj.layer], mm(obj.x+obj.w/2), mmY(obj.y+obj.h/2+2), {align:'center'});
      }
    } else if (obj.type === 'circle') {
      doc.circle(mm(obj.cx),mmY(obj.cy),mm(obj.r));
    } else if (obj.type === 'text') {
      doc.setFontSize(7); doc.setFont('helvetica','normal'); doc.setTextColor(0);
      doc.text(obj.text, mm(obj.x), mmY(obj.y));
    } else if (obj.type === 'dim') {
      doc.setDrawColor(204,153,0); doc.setLineWidth(0.2);
      doc.line(mm(obj.x1),mmY(obj.y1),mm(obj.x2),mmY(obj.y2));
      doc.setFontSize(5); doc.setTextColor(180,130,0);
      doc.text(obj.value, mm((obj.x1+obj.x2)/2), mmY((obj.y1+obj.y2)/2)-1.5, {align:'center'});
    }
  });

  // Scale bar
  doc.setDrawColor(0); doc.setFillColor(0);
  doc.setFontSize(5); doc.setFont('helvetica','normal'); doc.setTextColor(0);
  const sbX2 = mm(DRAW_X1+20), sbY2 = mmY(DRAW_Y2-20);
  doc.text('SCALE '+( document.getElementById('tb-scale')?.value||'1:1000'), sbX2, sbY2-1);
  [0,1,2,3,4].forEach(i => {
    doc.setFillColor(i%2===0?0:255,i%2===0?0:255,i%2===0?0:255);
    doc.rect(sbX2+i*mm(30),sbY2,mm(30),mmY(8),'FD');
  });
  doc.setTextColor(0);
  ['0','30','60','90','120m'].forEach((l,i)=>doc.text(l,sbX2+i*mm(30),sbY2+mmY(14),{align:'center'}));

  const filename = (document.getElementById('tb-project')?.value||'BESS_Site').replace(/\\s+/g,'_') + '_SitePlan.pdf';
  doc.save(filename);
}

function hexToRGB(hex) {
  const r = parseInt(hex.slice(1,3),16)||0;
  const g = parseInt(hex.slice(3,5),16)||0;
  const b = parseInt(hex.slice(5,7),16)||0;
  return {r,g,b};
}

// ═══════════════════════════════════════════════
//  INITIALISE
// ═══════════════════════════════════════════════
window.addEventListener('load', () => {
  initSVG();
  setActiveLayer('site_boundary');
  zoomFit();

  // Set initial active palette item
  document.getElementById('pal-site_boundary').classList.add('active-layer');
});
</script>
</body>
</html>
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

    page = st.radio("Navigate", ["🏠  Dashboard","🎨  Design Canvas","🔋  Component Database","📋  Project Manager","📊  Reports & Export"], label_visibility="collapsed")
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
        sn2=st.selectbox("Select project",[p["name"]for p in P])
        proj=next(p for p in P if p["name"]==sn2); idx=P.index(proj)
        with st.form("edit_proj"):
            c1,c2=st.columns(2)
            nn=c1.text_input("Name",proj["name"]); nc=c2.text_input("Client",proj["client"])
            nl=c1.text_input("Location",proj["location"]); ne=c2.text_input("Engineer",proj["engineer"])
            ns=st.selectbox("Status",PROJECT_STATUSES,index=PROJECT_STATUSES.index(proj["status"]))
            c3,c4=st.columns(2)
            nca=c3.number_input("Capacity (MWh)",value=float(proj["capacity_mwh"]),step=0.5); npm=c4.number_input("Power (MW)",value=float(proj["power_mw"]),step=0.5)
            nch=c3.selectbox("Chemistry",["LFP","NMC","NCA","LTO"],index=["LFP","NMC","NCA","LTO"].index(proj["chemistry"]))
            c5,c6=st.columns(2)
            nb=c5.number_input("Budget (USD)",value=proj["budget_usd"],step=10000); nsp=c6.number_input("Spent (USD)",value=proj["spent_usd"],step=1000)
            npr=st.slider("Progress (%)",0,100,proj["progress_pct"]); nno=st.text_area("Notes",proj["notes"])
            if st.form_submit_button("💾 Save"):
                P[idx].update({"name":nn,"client":nc,"location":nl,"engineer":ne,"status":ns,"capacity_mwh":nca,"power_mw":npm,"chemistry":nch,"budget_usd":nb,"spent_usd":nsp,"progress_pct":npr,"notes":nno})
                st.session_state.projects=P; st.success("✓ Saved")
    with t4:
        with st.form("new_proj"):
            c1,c2=st.columns(2)
            an=c1.text_input("Name *"); ac2=c2.text_input("Client *")
            al2=c1.text_input("Location"); ae=c2.text_input("Engineer")
            ast2=st.selectbox("Status",PROJECT_STATUSES)
            c3,c4=st.columns(2)
            aca=c3.number_input("Capacity (MWh)",0.1,1000.0,5.0,step=0.5); apm=c4.number_input("Power (MW)",0.1,1000.0,2.5,step=0.5)
            ach=c3.selectbox("Chemistry",["LFP","NMC","NCA","LTO"])
            c5,c6=st.columns(2)
            ab=c5.number_input("Budget (USD)",100000,100000000,4000000,step=50000); as2=c6.date_input("Start Date",date.today()); ae2=c5.date_input("End Date")
            ano=st.text_area("Notes")
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
        sel=st.selectbox("Project",["All Projects"]+[p["name"]for p in P])
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
