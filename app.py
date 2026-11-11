import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import init_db, get_session
from database.operations import count_logs, count_logs_by_level, get_logs, search_logs
from ingestion.loader import ingest_bytes
from ingestion.service import import_records
from analysis.security import analyze_security

st.set_page_config(page_title="A-LAS | Log Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
init_db()
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --bg:#0b1016; --panel:#111923; --line:#202c38; --muted:#91a0af; --text:#eaf1f7; --mint:#50e0bd; }
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background:radial-gradient(ellipse at 75% -10%,#153143 0%,#0b1016 45%); color:var(--text); }
[data-testid="stSidebar"] { background:#0c131b; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--text); }
.block-container { padding-top:2rem; max-width:1480px; }
h1,h2,h3 { letter-spacing:-.04em; }
.eyebrow { color:var(--mint); text-transform:uppercase; letter-spacing:.16em; font:500 11px 'DM Mono',monospace; }
.hero { padding:4px 0 20px; } .hero h1 { font-size:38px; margin:7px 0; }
.hero p { color:var(--muted); margin:0; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#141f29,#101720); border:1px solid var(--line); border-radius:14px; padding:18px 20px; }
[data-testid="stMetricLabel"] { color:var(--muted); } [data-testid="stMetricValue"] { font-weight:800; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
.stButton>button[kind="primary"] { background:var(--mint); color:#071610; border:0; font-weight:800; }
.stButton>button { border-radius:9px; }
hr { border-color:var(--line); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="eyebrow">◈ A-LAS / LOG INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown("## Control room")
    page = st.radio("Workspace", ["Overview", "Log explorer", "Security signals", "Import logs"], label_visibility="collapsed")
    st.divider()
    st.caption("LOCAL SQLITE · LIVE DATA")

with get_session() as session:
    all_logs = get_logs(session, limit=5000)
    total = count_logs(session)
    counts = count_logs_by_level(session)
    security = analyze_security(all_logs)

if page == "Overview":
    st.markdown('<div class="hero"><div class="eyebrow">SYSTEM OVERVIEW · LIVE</div><h1>Log intelligence</h1><p>A clear view of operational health and security activity.</p></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Events indexed", f"{total:,}")
    c2.metric("Errors", f"{counts.get('ERROR',0):,}")
    c3.metric("Warnings", f"{counts.get('WARNING',0):,}")
    c4.metric("Auth failures", f"{security['auth_failures']:,}", delta=f"{len(security['repeated_sources'])} repeated sources", delta_color="inverse")
    left,right = st.columns([1.45,1])
    with left:
        st.subheader("Severity distribution")
        if counts:
            frame = pd.DataFrame([{"Severity": k, "Events": v} for k,v in counts.items()])
            fig = px.bar(frame, x="Severity", y="Events", color="Severity", color_discrete_map={"INFO":"#50e0bd","WARNING":"#f4c76b","ERROR":"#ff806e","CRITICAL":"#d77cff"})
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#dce6ed",showlegend=False,margin=dict(l=0,r=0,t=15,b=0),height=300)
            fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#202c38")
            st.plotly_chart(fig,use_container_width=True)
        else: st.info("Import synthetic sample logs to see activity.")
    with right:
        st.subheader("Security signals")
        if security["repeated_sources"]:
            for item in security["repeated_sources"]:
                st.warning(f"{item['source']} · {item['count']} authentication failures")
        elif security["auth_failures"]:
            st.info(f"{security['auth_failures']} authentication failure(s); no repeated source threshold reached.")
        else: st.success("No authentication failure patterns detected.")
        st.subheader("Recent events")
        for log in all_logs[:6]:
            st.markdown(f"`{log.level}` · **{log.source}**  \n{log.message}")
            st.caption(str(log.timestamp))

elif page == "Log explorer":
    st.markdown('<div class="hero"><div class="eyebrow">INVESTIGATE</div><h1>Log explorer</h1><p>Search and filter normalized records.</p></div>', unsafe_allow_html=True)
    f1,f2 = st.columns([1,2])
    with f1: level = st.selectbox("Severity", ["ALL","INFO","WARNING","ERROR","CRITICAL"])
    with f2: keyword = st.text_input("Search messages", placeholder="Try: connection timeout")
    with get_session() as session:
        logs = search_logs(session, keyword) if keyword else get_logs(session, level=level, limit=500)
        if keyword and level != "ALL": logs = [row for row in logs if row.level == level]
    st.caption(f"{len(logs)} records shown · maximum 500")
    st.dataframe(pd.DataFrame([{"Time":x.timestamp,"Severity":x.level,"Source":x.source,"Message":x.message} for x in logs]), use_container_width=True, hide_index=True)

elif page == "Security signals":
    st.markdown('<div class="hero"><div class="eyebrow">RULE-BASED DETECTION</div><h1>Security signals</h1><p>Explainable indicators derived from normalized log messages.</p></div>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    a.metric("Authentication failures", security["auth_failures"])
    b.metric("Repeated sources", len(security["repeated_sources"]))
    c.metric("Critical events", security["critical_count"])
    st.subheader("Repeated authentication failures")
    st.caption("A source is surfaced after three matching messages. This is a triage signal, not a definitive incident finding.")
    if security["repeated_sources"]: st.dataframe(pd.DataFrame(security["repeated_sources"]), use_container_width=True, hide_index=True)
    else: st.info("No source has reached the repeated failure threshold.")
    st.subheader("Matching events")
    st.dataframe(pd.DataFrame([{k:v for k,v in item.items()} for item in security["signals"]]), use_container_width=True, hide_index=True)

elif page == "Import logs":
    st.markdown('<div class="hero"><div class="eyebrow">INGESTION</div><h1>Import log data</h1><p>Upload synthetic or authorized .log, .txt, and .json records.</p></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose a log file", type=["log","txt","json"], help="Files are processed in memory and are limited to 10 MiB.")
    if uploaded and st.button("Parse and import", type="primary"):
        try:
            records, errors = ingest_bytes(uploaded.name, uploaded.getvalue())
            with get_session() as session: result = import_records(session, uploaded.name, records, errors)
            st.success(f"Added {result['created']} · skipped duplicates {result['duplicates']} · malformed records {result['malformed']}")
            if errors:
                with st.expander("Review malformed records"): st.write(errors[:100])
        except ValueError as exc: st.error(str(exc))
