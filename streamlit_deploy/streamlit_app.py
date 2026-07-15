import os
import sys
import streamlit as st

# --- Make local packages importable (agent/, ml/, memory/) ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Load secrets into env vars BEFORE importing agent modules (they read os.getenv at import time) ---
for key in ["GROQ_API_KEY", "TAVILY_API_KEY", "PROXYCURL_API_KEY", "SENDER_NAME", "GROQ_MODEL"]:
    if key in st.secrets:
        os.environ[key] = str(st.secrets[key])

from agent.graph import graph, fresh_state
from memory.store import init_db, get_all_leads, get_all_deals, get_interactions, update_deal_stage

# ---------------------------------------------------------------------------
# Page config + theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SalesAgent — Autonomous B2B Sales AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRIMARY = "#7C5CFC"
ACCENT = "#00D9B5"
BG = "#0B0B14"
CARD = "#14141F"
BORDER = "#26263A"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG}; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    .hero {{
        padding: 1.2rem 0 0.4rem 0;
        border-bottom: 1px solid {BORDER};
        margin-bottom: 1.4rem;
    }}
    .hero h1 {{
        font-size: 1.9rem; font-weight: 800; color: #F3F1FF; margin-bottom: 0.15rem;
    }}
    .hero p {{ color: #9C9AB5; font-size: 0.95rem; margin: 0; }}
    .hero .accent {{ color: {ACCENT}; }}

    div[data-testid="stStatusWidget"] {{ background-color: {CARD}; }}

    .lead-card {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 1.1rem 1.3rem; margin-bottom: 0.8rem;
    }}
    .lead-card h3 {{ margin: 0 0 0.2rem 0; color: #F3F1FF; font-size: 1.25rem; }}
    .lead-card .role {{ color: #B7B5D6; font-size: 0.95rem; margin-bottom: 0.5rem; }}
    .lead-card .meta {{ color: #7C7A98; font-size: 0.82rem; }}

    .score-pill {{
        display: inline-block; padding: 0.3rem 0.9rem; border-radius: 999px;
        font-weight: 700; font-size: 1.1rem; color: #0B0B14;
        background: linear-gradient(90deg, {ACCENT}, {PRIMARY});
    }}

    .email-box {{
        background: {CARD}; border: 1px solid {BORDER}; border-left: 3px solid {PRIMARY};
        border-radius: 8px; padding: 1.1rem 1.3rem; font-family: 'SFMono-Regular', Consolas, monospace;
        font-size: 0.88rem; color: #DAD9EE; white-space: pre-wrap; line-height: 1.55;
    }}

    .kanban-col-title {{
        color: {ACCENT}; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.06em;
        text-transform: uppercase; padding-bottom: 0.5rem; border-bottom: 2px solid {PRIMARY};
        margin-bottom: 0.8rem;
    }}

    div.stButton > button {{
        background: linear-gradient(90deg, {PRIMARY}, #9D7CFF); color: white; border: none;
        border-radius: 8px; font-weight: 600; padding: 0.5rem 1.4rem;
    }}
    div.stButton > button:hover {{ opacity: 0.9; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# DB init (once per session container)
# ---------------------------------------------------------------------------
@st.cache_resource
def _init():
    init_db()
    return True

_init()

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>🎯 SalesAgent <span class="accent">— Autonomous B2B Sales AI</span></h1>
    <p>Paste a LinkedIn URL. The agent researches, scores, writes, and pipelines the lead — in ~45 seconds.</p>
</div>
""", unsafe_allow_html=True)

tab_agent, tab_pipeline, tab_leads = st.tabs(["🤖 Run Agent", "📋 Pipeline", "👥 Leads"])

STEP_META = {
    "research": ("🔍", "Researching lead from LinkedIn"),
    "score": ("📊", "Scoring lead with ML model"),
    "email": ("✍️", "Drafting personalized cold email"),
    "save": ("💾", "Saving to CRM pipeline"),
}
STEP_ORDER = ["research", "score", "email", "save"]

# ---------------------------------------------------------------------------
# TAB 1 — Run Agent
# ---------------------------------------------------------------------------
with tab_agent:
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        linkedin_url = st.text_input(
            "LinkedIn URL",
            placeholder="https://www.linkedin.com/in/satya-nadella",
            label_visibility="collapsed",
        )
    with col_btn:
        run_clicked = st.button("Run Agent", use_container_width=True)

    if run_clicked:
        if not linkedin_url.strip():
            st.warning("Paste a LinkedIn profile URL first.")
        elif not os.getenv("GROQ_API_KEY") or not os.getenv("TAVILY_API_KEY"):
            st.error(
                "Missing API keys. Add `GROQ_API_KEY` and `TAVILY_API_KEY` in "
                "**Manage app → Settings → Secrets**, then reboot the app."
            )
        else:
            initial_state = fresh_state(linkedin_url=linkedin_url.strip())
            status_boxes = {}
            final_state = None

            try:
                for chunk in graph.stream(initial_state, stream_mode="updates"):
                    node_name, node_state = next(iter(chunk.items()))
                    final_state = node_state
                    icon, title = STEP_META.get(node_name, ("•", node_name))

                    entries = [e for e in node_state.get("trace", []) if e["step"] == node_name]
                    is_done = any(e["status"] == "done" for e in entries)

                    box = st.status(f"{icon} {title}", expanded=False,
                                     state="complete" if is_done else "running")
                    for e in entries:
                        prefix = "✅" if e["status"] == "done" else "⏳"
                        box.write(f"{prefix} {e['msg']}")
                    status_boxes[node_name] = box

                st.success("Lead processed successfully.")
                st.divider()

                profile = (final_state or {}).get("profile", {}) or {}
                score = (final_state or {}).get("lead_score", 0) or 0
                email_draft = (final_state or {}).get("email_draft", "") or ""
                followup = (final_state or {}).get("followup_date", "")

                col_profile, col_score = st.columns([3, 1])
                with col_profile:
                    st.markdown(f"""
                    <div class="lead-card">
                        <h3>{profile.get('name', 'Unknown')}</h3>
                        <div class="role">{profile.get('title', '')}{' at ' + profile.get('company') if profile.get('company') else ''}</div>
                        <div class="meta">{profile.get('location', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_score:
                    st.markdown(f'<div class="score-pill">{score:.0f}/100</div>', unsafe_allow_html=True)

                st.markdown("**Generated cold email**")
                st.markdown(f'<div class="email-box">{email_draft}</div>', unsafe_allow_html=True)

                if followup:
                    st.info(f"📅 Added to pipeline — follow-up scheduled for **{followup}**")

            except Exception as e:
                st.error(f"Agent run failed: {e}")

# ---------------------------------------------------------------------------
# TAB 2 — Pipeline (Kanban)
# ---------------------------------------------------------------------------
with tab_pipeline:
    deals = get_all_deals()
    if not deals:
        st.info("No deals yet — run the agent on a lead to populate the pipeline.")
    else:
        stages = []
        for d in deals:
            if d["stage"] not in stages:
                stages.append(d["stage"])
        for common in ["Lead", "Contacted", "Qualified", "Won", "Lost"]:
            if common not in stages:
                stages.append(common)

        cols = st.columns(len(stages))
        for col, stage in zip(cols, stages):
            with col:
                stage_deals = [d for d in deals if d["stage"] == stage]
                st.markdown(f'<div class="kanban-col-title">{stage} ({len(stage_deals)})</div>',
                            unsafe_allow_html=True)
                for d in stage_deals:
                    st.markdown(f"""
                    <div class="lead-card">
                        <h3 style="font-size:1rem;">{d.get('lead_name') or d.get('title', 'Deal')}</h3>
                        <div class="meta">{d.get('company', '')} · Score {d.get('score', 0):.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    new_stage = st.selectbox(
                        "Stage", options=stages, index=stages.index(stage),
                        key=f"stage_{d['id']}", label_visibility="collapsed",
                    )
                    if new_stage != stage:
                        update_deal_stage(d["id"], new_stage)
                        st.rerun()

# ---------------------------------------------------------------------------
# TAB 3 — Leads
# ---------------------------------------------------------------------------
with tab_leads:
    leads = get_all_leads()
    if not leads:
        st.info("No leads yet — run the agent on a lead to see it here.")
    else:
        for lead in leads:
            with st.expander(f"{lead['name']}  ·  {lead.get('company') or '—'}  ·  {lead['score']:.0f}/100"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**Title:** {lead.get('title') or '—'}")
                    st.write(f"**Location:** {lead.get('location') or '—'}")
                    st.write(f"**Stage:** {lead.get('stage')}")
                    if lead.get("linkedin_url"):
                        st.write(f"[LinkedIn profile]({lead['linkedin_url']})")
                with c2:
                    st.write(f"**Created:** {lead.get('created_at', '')[:10]}")
                if lead.get("email_draft"):
                    st.markdown("**Email draft**")
                    st.markdown(f'<div class="email-box">{lead["email_draft"]}</div>', unsafe_allow_html=True)
                interactions = get_interactions(lead["id"])
                if interactions:
                    st.markdown("**Interaction history**")
                    for i in interactions:
                        st.caption(f"{i['created_at']} — {i['type']}")