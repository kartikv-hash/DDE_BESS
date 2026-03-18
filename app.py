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
CAD_HTML=r"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;background:#0d0f14;color:#e8eaf0;height:100vh;display:flex;flex-direction:column;overflow:hidden}
#tb{height:40px;display:flex;align-items:center;gap:4px;padding:0 10px;background:#12151c;border-bottom:1px solid rgba(255,255,255,0.07);flex-shrink:0}
.tb-btn{padding:0 10px;height:26px;border-radius:5px;font-size:11px;font-weight:500;cursor:pointer;color:#8890a4;background:transparent;border:1px solid rgba(255,255,255,0.1);font-family:'DM Sans';transition:all 0.15s;white-space:nowrap}
.tb-btn:hover{background:#1a1e28;color:#e8eaf0}.tb-btn.active{background:rgba(0,212,255,0.15);color:#00d4ff;border-color:rgba(0,212,255,0.4)}
.sep{width:1px;height:18px;background:rgba(255,255,255,0.1);margin:0 4px}.spacer{flex:1}
#main{display:flex;flex:1;overflow:hidden}
#sb2{width:180px;flex-shrink:0;background:#12151c;border-right:1px solid rgba(255,255,255,0.07);overflow-y:auto;padding:8px 6px}
#sb2::-webkit-scrollbar{width:2px}#sb2::-webkit-scrollbar-thumb{background:#1a1e28}
.sec{font-size:9px;font-weight:600;color:#555d72;text-transform:uppercase;letter-spacing:0.08em;padding:6px 4px 4px;margin-top:6px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:4px}
.ci{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 3px;border:1px solid rgba(255,255,255,0.07);border-radius:5px;cursor:grab;background:#1a1e28;transition:all 0.15s;user-select:none}
.ci:hover{border-color:rgba(0,212,255,0.3);background:#222738}.ci:active{cursor:grabbing}
.ci svg{width:34px;height:26px}.ci span{font-size:9px;color:#8890a4;text-align:center;line-height:1.2}
#cw{flex:1;position:relative;overflow:hidden}
#bg{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.04) 1px,transparent 1px),linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:100px 100px,100px 100px,20px 20px,20px 20px}
#svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
#stbar{height:22px;display:flex;align-items:center;gap:10px;background:#12151c;border-top:1px solid rgba(255,255,255,0.07);padding:0 10px;font-family:'JetBrains Mono';font-size:10px;color:#555d72;flex-shrink:0}
</style></head><body>
<div id="tb">
  <button class="tb-btn active" id="btn-select" onclick="setTool('select')">▲ Select</button>
  <button class="tb-btn" id="btn-wire" onclick="setTool('wire')">⟋ Wire</button>
  <button class="tb-btn" id="btn-bus" onclick="setTool('bus')">━ Bus</button>
  <button class="tb-btn" id="btn-annotate" onclick="setTool('annotate')">T Text</button>
  <div class="sep"></div>
  <select id="wt" style="padding:2px 6px;background:#1a1e28;border:1px solid rgba(255,255,255,0.1);color:#8890a4;border-radius:5px;font-size:10px;font-family:'JetBrains Mono'">
    <option value="dc">DC Bus</option><option value="ac_hv">AC HV</option><option value="ac_lv">AC LV</option><option value="ctrl">Control</option><option value="comm">Comms</option>
  </select>
  <div class="sep"></div>
  <button class="tb-btn" onclick="doUndo()">↩ Undo</button>
  <button class="tb-btn" onclick="zoomFit()">⊡ Fit</button>
  <button class="tb-btn" onclick="exportSVG()" style="color:#00d4ff;border-color:rgba(0,212,255,0.3)">↓ SVG</button>
  <button class="tb-btn" onclick="exportDXF()" style="color:#ffb347;border-color:rgba(255,179,71,0.3)">↓ DXF</button>
  <button class="tb-btn" onclick="clearAll()" style="color:#ff5566;border-color:rgba(255,85,102,0.3)">✕ Clear</button>
  <div class="spacer"></div>
  <span style="font-family:'JetBrains Mono';font-size:10px;color:#555d72" id="coords">X:0 Y:0</span>
</div>
<div id="main">
  <div id="sb2">
    <div class="sec">Storage</div>
    <div class="grid2">
      <div class="ci" draggable="true" data-type="battery_rack"><svg viewBox="0 0 34 26"><rect x="1" y="3" width="26" height="18" rx="2" fill="none" stroke="#00d4ff" stroke-width="1"/><rect x="27" y="8" width="3" height="8" rx="1" fill="#00d4ff" opacity=".5"/><rect x="3" y="6" width="4" height="12" rx="1" fill="#00d4ff" opacity=".5"/><rect x="9" y="6" width="4" height="12" rx="1" fill="#00d4ff" opacity=".4"/><rect x="15" y="6" width="4" height="12" rx="1" fill="#00d4ff" opacity=".25"/><rect x="21" y="6" width="3" height="12" rx="1" fill="#00d4ff" opacity=".15"/></svg><span>Battery Rack</span></div>
      <div class="ci" draggable="true" data-type="bms"><svg viewBox="0 0 34 26"><rect x="3" y="2" width="28" height="22" rx="2" fill="none" stroke="#00e5a0" stroke-width="1"/><text x="17" y="14" text-anchor="middle" font-size="8" fill="#00e5a0" font-family="JetBrains Mono" font-weight="600">BMS</text><circle cx="8" cy="7" r="1.8" fill="#00e5a0" opacity=".7"/></svg><span>BMS</span></div>
      <div class="ci" draggable="true" data-type="container"><svg viewBox="0 0 34 26"><rect x="1" y="1" width="32" height="24" rx="2" fill="none" stroke="#555d72" stroke-width="1" stroke-dasharray="3 2"/><text x="17" y="14" text-anchor="middle" font-size="6" fill="#555d72" font-family="DM Sans">CONTAINER</text></svg><span>Container</span></div>
    </div>
    <div class="sec">Power</div>
    <div class="grid2">
      <div class="ci" draggable="true" data-type="pcs"><svg viewBox="0 0 34 26"><rect x="2" y="2" width="30" height="22" rx="2" fill="none" stroke="#ffb347" stroke-width="1"/><path d="M9 13L14 7 14 11 19 11 19 16 14 16 14 21Z" fill="none" stroke="#ffb347" stroke-width="1" stroke-linejoin="round"/><text x="26" y="16" text-anchor="middle" font-size="6" fill="#ffb347" font-family="JetBrains Mono">PCS</text></svg><span>PCS</span></div>
      <div class="ci" draggable="true" data-type="transformer"><svg viewBox="0 0 34 26"><circle cx="12" cy="13" r="8" fill="none" stroke="#a78bfa" stroke-width="1"/><circle cx="22" cy="13" r="8" fill="none" stroke="#a78bfa" stroke-width="1"/><line x1="0" y1="13" x2="4" y2="13" stroke="#a78bfa" stroke-width="1.2"/><line x1="30" y1="13" x2="34" y2="13" stroke="#a78bfa" stroke-width="1.2"/></svg><span>Transformer</span></div>
      <div class="ci" draggable="true" data-type="vcb"><svg viewBox="0 0 34 26"><line x1="17" y1="1" x2="17" y2="9" stroke="#ff5566" stroke-width="1.5"/><circle cx="17" cy="13" r="4" fill="none" stroke="#ff5566" stroke-width="1"/><line x1="17" y1="17" x2="17" y2="25" stroke="#ff5566" stroke-width="1.5" stroke-dasharray="2 1"/></svg><span>VCB</span></div>
      <div class="ci" draggable="true" data-type="busbar"><svg viewBox="0 0 34 26"><rect x="1" y="11" width="32" height="4" rx="1" fill="#8890a4" opacity=".6"/><line x1="9" y1="6" x2="9" y2="11" stroke="#8890a4" stroke-width="1.5"/><line x1="17" y1="6" x2="17" y2="11" stroke="#8890a4" stroke-width="1.5"/><line x1="25" y1="6" x2="25" y2="11" stroke="#8890a4" stroke-width="1.5"/></svg><span>Busbar</span></div>
    </div>
    <div class="sec">Monitoring</div>
    <div class="grid2">
      <div class="ci" draggable="true" data-type="meter"><svg viewBox="0 0 34 26"><circle cx="17" cy="13" r="10" fill="none" stroke="#00e5a0" stroke-width="1"/><path d="M8 19Q17 5 26 19" fill="none" stroke="#444" stroke-width=".8"/><line x1="17" y1="13" x2="22" y2="9" stroke="#00e5a0" stroke-width="1.5" stroke-linecap="round"/></svg><span>Meter</span></div>
      <div class="ci" draggable="true" data-type="relay"><svg viewBox="0 0 34 26"><rect x="5" y="3" width="24" height="20" rx="2" fill="none" stroke="#00e5a0" stroke-width="1"/><text x="17" y="15" text-anchor="middle" font-size="7" fill="#00e5a0" font-family="JetBrains Mono">87T</text><circle cx="9" cy="7" r="1.8" fill="#00e5a0" opacity=".7"/></svg><span>Relay</span></div>
      <div class="ci" draggable="true" data-type="grid_point"><svg viewBox="0 0 34 26"><path d="M17 2L30 21H4Z" fill="none" stroke="#00d4ff" stroke-width="1" stroke-linejoin="round"/><line x1="17" y1="21" x2="17" y2="25" stroke="#00d4ff" stroke-width="1.5"/><line x1="11" y1="25" x2="23" y2="25" stroke="#00d4ff" stroke-width="1.5"/></svg><span>Grid Point</span></div>
      <div class="ci" draggable="true" data-type="scada"><svg viewBox="0 0 34 26"><rect x="4" y="3" width="26" height="17" rx="2" fill="none" stroke="#a78bfa" stroke-width="1"/><text x="17" y="13" text-anchor="middle" font-size="7" fill="#a78bfa" font-family="JetBrains Mono">EMS</text><rect x="12" y="22" width="10" height="2" rx=".5" fill="#a78bfa" opacity=".5"/><line x1="17" y1="20" x2="17" y2="22" stroke="#a78bfa" stroke-width="1"/></svg><span>SCADA</span></div>
    </div>
  </div>
  <div id="cw" ondragover="event.preventDefault()" ondrop="onDrop(event)" onmousedown="mDown(event)" onmousemove="mMove(event)" onmouseup="mUp(event)" onwheel="onWheel(event)">
    <div id="bg"></div>
    <svg id="svg"><defs>
      <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M2 1.5L8 5L2 8.5" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>
      <filter id="sel"><feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#00d4ff" flood-opacity=".8"/></filter>
    </defs><g id="root"><g id="wl"></g><g id="cl"></g><g id="al"></g><g id="tmp"></g></g></svg>
  </div>
</div>
<div id="stbar"><span id="sbm">● Select</span><span>|</span><span id="sbc">0 components</span><span>|</span><span id="sbw">0 wires</span><span>|</span><span id="sbz">100%</span><div style="flex:1"></div><span>V=select W=wire B=bus ESC=cancel Del=delete Ctrl+Z=undo</span></div>
<script>
const CD={battery_rack:{l:'Battery Rack',w:90,h:55,c:'#00d4ff'},bms:{l:'BMS',w:75,h:45,c:'#00e5a0'},container:{l:'Container',w:200,h:100,c:'#555d72',dash:true},pcs:{l:'PCS',w:80,h:60,c:'#ffb347'},transformer:{l:'Transformer',w:80,h:60,c:'#a78bfa'},vcb:{l:'VCB',w:50,h:65,c:'#ff5566'},busbar:{l:'Busbar',w:160,h:18,c:'#8890a4'},meter:{l:'Meter',w:60,h:55,c:'#00e5a0'},relay:{l:'Relay',w:65,h:50,c:'#00e5a0'},grid_point:{l:'Grid',w:70,h:65,c:'#00d4ff'},scada:{l:'SCADA',w:70,h:55,c:'#a78bfa'}};
const WS={dc:{s:'#00d4ff',w:1.5,d:''},ac_hv:{s:'#ff5566',w:2,d:''},ac_lv:{s:'#ffb347',w:1.5,d:''},ctrl:{s:'#a78bfa',w:1,d:'4 2'},comm:{s:'#00e5a0',w:1,d:'2 3'}};
let comps=[],wires=[],sel=null,tool='select',idn=0,px=0,py=0,zoom=1,pan=false,psx=0,psy=0,ws=null,wpts=[],tmp=null,drag=false,dc=null,dox=0,doy=0,ustk=[];
const R=()=>document.getElementById('root'),WL=()=>document.getElementById('wl'),CL=()=>document.getElementById('cl'),AL=()=>document.getElementById('al'),TL=()=>document.getElementById('tmp'),SVG=()=>document.getElementById('svg');
function aT(){R().setAttribute('transform',`translate(${px},${py}) scale(${zoom})`);document.getElementById('sbz').textContent=Math.round(zoom*100)+'%';}
function sP(cx,cy){const r=SVG().getBoundingClientRect();return{x:(cx-r.left-px)/zoom,y:(cy-r.top-py)/zoom};}
function sn(v){return Math.round(v/20)*20;}
function setTool(t){tool=t;['select','wire','bus','annotate'].forEach(k=>{const b=document.getElementById('btn-'+k);if(b)b.classList.toggle('active',k===t);});document.getElementById('sbm').textContent='● '+t.charAt(0).toUpperCase()+t.slice(1);ws=null;wpts=[];cT();}
function sU(){ustk.push({c:JSON.parse(JSON.stringify(comps)),w:JSON.parse(JSON.stringify(wires))});if(ustk.length>20)ustk.shift();}
function doUndo(){if(!ustk.length)return;const s=ustk.pop();comps=s.c;wires=s.w;CL().innerHTML='';WL().innerHTML='';comps.forEach(rC);wires.forEach(rW);sel=null;uSB();}
function uSB(){document.getElementById('sbc').textContent=comps.length+' components';document.getElementById('sbw').textContent=wires.length+' wires';}
document.querySelectorAll('.ci').forEach(el=>el.addEventListener('dragstart',ev=>{window._dt=el.dataset.type;ev.dataTransfer&&ev.dataTransfer.setData('text/plain',el.dataset.type);}));
function onDrop(e){e.preventDefault();const t=(e.dataTransfer&&e.dataTransfer.getData('text/plain'))||window._dt;if(!t||!CD[t])return;const d=CD[t];const p=sP(e.clientX,e.clientY);sU();aC(t,sn(p.x-d.w/2),sn(p.y-d.h/2));}
function aC(type,x,y){const d=CD[type];if(!d)return;const id='c'+(++idn);const comp={id,type,x,y,w:d.w,h:d.h,l:d.l,c:d.c,dash:d.dash};comps.push(comp);rC(comp);uSB();return comp;}
function rC(comp){
  const g=document.createElementNS('http://www.w3.org/2000/svg','g');g.setAttribute('id',comp.id);g.setAttribute('data-id',comp.id);g.setAttribute('transform',`translate(${comp.x},${comp.y})`);g.style.cursor='pointer';g.style.userSelect='none';
  const r=document.createElementNS('http://www.w3.org/2000/svg','rect');r.setAttribute('width',comp.w);r.setAttribute('height',comp.h);r.setAttribute('rx','4');r.setAttribute('fill',comp.c+'15');r.setAttribute('stroke',comp.c+'CC');r.setAttribute('stroke-width','1');
  if(comp.dash){r.setAttribute('stroke-dasharray','6 3');r.setAttribute('fill','transparent');}g.appendChild(r);
  [[comp.w/2,0],[comp.w/2,comp.h],[0,comp.h/2],[comp.w,comp.h/2]].forEach(([tx,ty])=>{const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('cx',tx);dot.setAttribute('cy',ty);dot.setAttribute('r','4');dot.setAttribute('fill',comp.c);dot.setAttribute('opacity','0');dot.setAttribute('class','term');dot.style.transition='opacity 0.1s';g.appendChild(dot);});
  const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',comp.w/2);t.setAttribute('y',comp.h-7);t.setAttribute('text-anchor','middle');t.setAttribute('font-size','9');t.setAttribute('fill',comp.c);t.setAttribute('font-family','DM Sans');t.setAttribute('font-weight','500');t.setAttribute('pointer-events','none');t.textContent=comp.l.length>13?comp.l.substring(0,11)+'...':comp.l;g.appendChild(t);
  g.addEventListener('mouseenter',()=>g.querySelectorAll('.term').forEach(d=>d.setAttribute('opacity','0.7')));g.addEventListener('mouseleave',()=>g.querySelectorAll('.term').forEach(d=>d.setAttribute('opacity','0')));
  CL().appendChild(g);}
function mDown(e){
  if(e.button===1||(e.button===0&&e.altKey)){pan=true;psx=e.clientX-px;psy=e.clientY-py;return;}
  if(tool==='select'){const t=e.target.closest('[data-id]');if(t){const c=comps.find(x=>x.id===t.dataset.id);if(c){selC(c);drag=true;dc=c;const p=sP(e.clientX,e.clientY);dox=p.x-c.x;doy=p.y-c.y;sU();}}else selC(null);}
  if(tool==='wire'||tool==='bus'){const p={x:sn(sP(e.clientX,e.clientY).x),y:sn(sP(e.clientX,e.clientY).y)};if(!ws){ws=p;wpts=[p];}else{wpts.push(p);}}
  if(tool==='annotate'){const p=sP(e.clientX,e.clientY);const tx=prompt('Label:');if(tx)aAnn(sn(p.x),sn(p.y),tx);}
}
function mMove(e){
  const p=sP(e.clientX,e.clientY);document.getElementById('coords').textContent='X:'+Math.round(p.x)+' Y:'+Math.round(p.y);
  if(pan){px=e.clientX-psx;py=e.clientY-psy;aT();return;}
  if(drag&&dc){dc.x=sn(p.x-dox);dc.y=sn(p.y-doy);const el=document.getElementById(dc.id);if(el)el.setAttribute('transform','translate('+dc.x+','+dc.y+')');}
  if((tool==='wire'||tool==='bus')&&ws){
    if(!tmp){tmp=document.createElementNS('http://www.w3.org/2000/svg','line');const wsel=document.getElementById('wt').value;tmp.setAttribute('stroke',tool==='bus'?'#8890a4':(WS[wsel]||WS.dc).s);tmp.setAttribute('stroke-width',tool==='bus'?'5':'1.5');tmp.setAttribute('stroke-dasharray','4 3');tmp.setAttribute('opacity','0.6');tmp.setAttribute('pointer-events','none');TL().appendChild(tmp);}
    const last=wpts[wpts.length-1];tmp.setAttribute('x1',last.x);tmp.setAttribute('y1',last.y);tmp.setAttribute('x2',sn(p.x));tmp.setAttribute('y2',sn(p.y));}
}
function mUp(e){
  if(pan){pan=false;return;}if(drag){drag=false;dc=null;return;}
  if((tool==='wire'||tool==='bus')&&ws){const t=e.target.closest('[data-id]');if(t){const tc=comps.find(x=>x.id===t.dataset.id);if(tc){wpts.push({x:tc.x+tc.w/2,y:tc.y+tc.h/2});cW();return;}}if(e.detail>=2){cW();return;}}
}
function cW(){if(wpts.length<2){cT();ws=null;wpts=[];return;}const wt2=tool==='bus'?'busbar':document.getElementById('wt').value;const w={id:'w'+(++idn),pts:[...wpts],wt:wt2};wires.push(w);rW(w);cT();ws=null;wpts=[];uSB();sU();}
function rW(w){const ws2=(WS[w.wt])||{s:'#00d4ff',w:1.5,d:''};const p=document.createElementNS('http://www.w3.org/2000/svg','polyline');p.setAttribute('id',w.id);p.setAttribute('points',w.pts.map(pt=>pt.x+','+pt.y).join(' '));p.setAttribute('fill','none');p.setAttribute('stroke',w.wt==='busbar'?'#8890a4':ws2.s);p.setAttribute('stroke-width',w.wt==='busbar'?'5':ws2.w);p.setAttribute('stroke-linecap','round');p.setAttribute('stroke-linejoin','round');if(ws2.d)p.setAttribute('stroke-dasharray',ws2.d);p.setAttribute('marker-end','url(#arr)');WL().appendChild(p);}
function cT(){if(tmp){tmp.remove();tmp=null;}TL().innerHTML='';}
function aAnn(x,y,text){const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('font-size','12');t.setAttribute('fill','#8890a4');t.setAttribute('font-family','JetBrains Mono');t.setAttribute('pointer-events','none');t.textContent=text;AL().appendChild(t);}
function selC(comp){sel=comp;document.querySelectorAll('[data-id] rect').forEach(r=>{r.setAttribute('stroke-width','1');r.removeAttribute('filter');});if(!comp)return;const el=document.getElementById(comp.id);if(el){const r=el.querySelector('rect');if(r){r.setAttribute('filter','url(#sel)');r.setAttribute('stroke-width','2');}}}
function onWheel(e){e.preventDefault();const f=e.deltaY<0?1.1:0.91;const p=sP(e.clientX,e.clientY);zoom=Math.min(4,Math.max(0.15,zoom*f));const r=SVG().getBoundingClientRect();px=e.clientX-r.left-p.x*zoom;py=e.clientY-r.top-p.y*zoom;aT();}
function zoomFit(){px=40;py=40;zoom=1;aT();}
function clearAll(){if(!confirm('Clear canvas?'))return;comps=[];wires=[];CL().innerHTML='';WL().innerHTML='';AL().innerHTML='';sel=null;uSB();}
function exportSVG(){const s=new XMLSerializer().serializeToString(SVG());const b=new Blob([s],{type:'image/svg+xml'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='bess-design.svg';a.click();}
function exportDXF(){let d='0\nSECTION\n2\nENTITIES\n';comps.forEach(c=>{d+='0\nLWPOLYLINE\n8\nCOMPONENTS\n90\n4\n70\n1\n10\n'+c.x+'\n20\n'+(-c.y)+'\n10\n'+(c.x+c.w)+'\n20\n'+(-c.y)+'\n10\n'+(c.x+c.w)+'\n20\n'+(-(c.y+c.h))+'\n10\n'+c.x+'\n20\n'+(-(c.y+c.h))+'\n';d+='0\nTEXT\n8\nLABELS\n10\n'+(c.x+c.w/2)+'\n20\n'+(-(c.y+c.h/2))+'\n30\n0\n40\n8\n1\n'+c.l+'\n';});wires.forEach(w=>{d+='0\nLWPOLYLINE\n8\nWIRES\n90\n'+w.pts.length+'\n70\n0\n';w.pts.forEach(p=>{d+='10\n'+p.x+'\n20\n'+(-p.y)+'\n';});});d+='0\nENDSEC\n0\nEOF\n';const b=new Blob([d],{type:'application/dxf'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='bess-design.dxf';a.click();}
document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;if(e.key==='v')setTool('select');if(e.key==='w')setTool('wire');if(e.key==='b')setTool('bus');if(e.key==='a')setTool('annotate');if(e.key==='Escape'){setTool('select');cT();ws=null;wpts=[];}if(e.key==='Delete'&&sel){sU();const el=document.getElementById(sel.id);if(el)el.remove();comps=comps.filter(c=>c.id!==sel.id);sel=null;uSB();}if((e.ctrlKey||e.metaKey)&&e.key==='z')doUndo();});
setTimeout(()=>{
  aC('grid_point',60,180);aC('vcb',180,180);aC('transformer',280,165);aC('busbar',400,192);
  aC('pcs',400,100);aC('pcs',400,300);aC('battery_rack',540,80);aC('battery_rack',540,160);
  aC('battery_rack',540,300);aC('battery_rack',540,380);aC('bms',660,220);aC('meter',170,80);aC('scada',660,60);
  setTimeout(()=>{
    [[{x:95,y:212},{x:170,y:212}],[{x:205,y:212},{x:270,y:212}],[{x:360,y:195},{x:390,y:195}],
     [{x:440,y:192},{x:440,y:140}],[{x:440,y:192},{x:440,y:320}],
     [{x:480,y:130},{x:530,y:110}],[{x:480,y:130},{x:530,y:190}],
     [{x:480,y:330},{x:530,y:330}],[{x:480,y:330},{x:530,y:410}]].forEach(pts=>{
      const w={id:'w'+(++idn),pts:pts,wt:'dc'};wires.push(w);rW(w);});
    const w={id:'w'+(++idn),pts:[{x:80,y:180},{x:170,y:110}],wt:'ac_hv'};wires.push(w);rW(w);uSB();
  },80);
},80);
</script></body></html>"""

def page_canvas():
    st.markdown('<div class="page-title">🎨 BESS Design Canvas</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Single-line diagram · Electrical schematic · Rack layout · Site plan</div>', unsafe_allow_html=True)
    col_c,col_f=st.columns([3,1])
    with col_c:
        components.html(CAD_HTML, height=600, scrolling=False)
    with col_f:
        st.markdown('<div class="section-title">Quick Add</div>', unsafe_allow_html=True)
        with st.expander("🔋 Battery String", expanded=True):
            rc=st.number_input("Rack count",1,20,4,key="f_rc"); chem=st.selectbox("Chemistry",["LFP","NMC","NCA","LTO"],key="f_ch"); cap=st.number_input("kWh / rack",50,500,100,key="f_cap")
            if st.button("Add String"): st.success(f"✓ {rc}× {cap} kWh {chem} — {rc*cap} kWh total")
        with st.expander("⚡ PCS Block"):
            pkw=st.number_input("Power (kW)",50,2000,250,key="f_pkw"); hv=st.number_input("HV (kV)",3,33,11,key="f_hv"); topo=st.selectbox("Topology",["3L-NPC","2L-VSC","Modular MLI"],key="f_tp")
            if st.button("Add PCS Block"): st.success(f"✓ {pkw} kW @ {hv} kV, {topo}")
        with st.expander("📐 Site Boundary"):
            sw=st.number_input("Width (m)",10,500,80,key="f_sw"); sh=st.number_input("Height (m)",10,500,60,key="f_sh"); sl=st.text_input("Label","BESS Site A",key="f_sl")
            if st.button("Add Site"): st.success(f"✓ {sl}: {sw}×{sh} m")
        st.markdown('<div class="section-title">Wire Legend</div>', unsafe_allow_html=True)
        for n,c in [("AC HV","#ff5566"),("DC Bus","#00d4ff"),("AC LV","#ffb347"),("Control","#a78bfa"),("Comms","#00e5a0")]:
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px"><div style="width:24px;height:2px;background:{c}"></div><span style="font-size:11px;color:#8890a4">{n}</span></div>',unsafe_allow_html=True)

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
