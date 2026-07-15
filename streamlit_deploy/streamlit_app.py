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
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SalesAgent — Autonomous B2B Sales AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
PRIMARY = "#7C5CFC"
PRIMARY_LIGHT = "#9D82FF"
ACCENT = "#2DE0B8"
BG = "#0A0A12"
BG_GRADIENT = "radial-gradient(circle at 15% 0%, #1a1530 0%, #0A0A12 45%)"
CARD = "#12121C"
CARD_HOVER = "#161622"
BORDER = "#22222F"
TEXT = "#F2F1FA"
TEXT_MUTED = "#8B899E"
TEXT_FAINT = "#5C5A6E"
DANGER = "#FF6B6B"

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}

    .stApp {{ background: {BG_GRADIENT}; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1180px; }}

    /* ---------- Top bar ---------- */
    .topbar {{
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 1.4rem; margin-bottom: 1.6rem;
        border-bottom: 1px solid {BORDER};
    }}
    .brand {{ display: flex; align-items: center; gap: 0.7rem; }}
    .brand-mark {{
        width: 38px; height: 38px; border-radius: 10px;
        background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
        display: flex; align-items: center; justify-content: center;
        font-size: 1.15rem; flex-shrink: 0;
    }}
    .brand-text h1 {{
        font-size: 1.15rem; font-weight: 800; color: {TEXT}; margin: 0; letter-spacing: -0.01em;
    }}
    .brand-text p {{
        font-size: 0.78rem; color: {TEXT_FAINT}; margin: 0; text-transform: uppercase; letter-spacing: 0.08em;
    }}
    .topbar-tagline {{
        color: {TEXT_MUTED}; font-size: 0.88rem; text-align: right; max-width: 380px; line-height: 1.4;
    }}

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.4rem; background: transparent; border-bottom: 1px solid {BORDER}; padding-bottom: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 2.6rem; background: transparent; border-radius: 8px 8px 0 0;
        color: {TEXT_MUTED}; font-weight: 600; font-size: 0.92rem; padding: 0 1.1rem;
    }}
    .stTabs [aria-selected="true"] {{
        color: {TEXT} !important; background: {CARD} !important;
        border-bottom: 2px solid {ACCENT} !important;
    }}

    /* ---------- Input row ---------- */
    div[data-testid="stTextInput"] input {{
        background: {CARD}; border: 1px solid {BORDER}; color: {TEXT};
        border-radius: 10px; padding: 0.7rem 1rem; font-size: 0.94rem;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: {PRIMARY}; box-shadow: 0 0 0 1px {PRIMARY};
    }}
    div[data-testid="stTextInput"] input::placeholder {{ color: {TEXT_FAINT}; }}

    div.stButton > button {{
        background: linear-gradient(90deg, {PRIMARY}, {PRIMARY_LIGHT}); color: white; border: none;
        border-radius: 10px; font-weight: 700; font-size: 0.92rem; padding: 0.7rem 1.4rem;
        transition: transform 0.12s ease, box-shadow 0.12s ease; width: 100%;
        box-shadow: 0 4px 14px rgba(124, 92, 252, 0.25);
    }}
    div.stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(124, 92, 252, 0.4); }}
    div.stButton > button:active {{ transform: translateY(0); }}

    /* ---------- Section labels ---------- */
    .section-label {{
        color: {TEXT_FAINT}; font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.09em; margin: 1.6rem 0 0.7rem 0;
    }}

    /* ---------- Agent trace ---------- */
    .trace-row {{
        display: flex; align-items: center; gap: 0.85rem;
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 0.75rem 1rem; margin-bottom: 0.55rem;
    }}
    .trace-row.done {{ border-color: rgba(45, 224, 184, 0.25); }}
    .trace-icon {{
        width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center; font-size: 0.95rem;
        background: rgba(124, 92, 252, 0.12);
    }}
    .trace-text {{ flex: 1; color: {TEXT}; font-size: 0.88rem; font-weight: 500; }}
    .trace-sub {{ color: {TEXT_FAINT}; font-size: 0.78rem; margin-top: 0.1rem; }}
    .trace-badge {{
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.05em; padding: 0.25rem 0.6rem;
        border-radius: 999px; flex-shrink: 0;
    }}
    .trace-badge.done {{ background: rgba(45, 224, 184, 0.15); color: {ACCENT}; }}
    .trace-badge.pending {{ background: rgba(139, 137, 158, 0.15); color: {TEXT_MUTED}; }}

    /* ---------- Lead card ---------- */
    .lead-card {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 1.4rem 1.5rem; height: 100%;
    }}
    .lead-card .avatar {{
        width: 46px; height: 46px; border-radius: 12px; margin-bottom: 0.9rem;
        background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 1.15rem; color: #0A0A12;
    }}
    .lead-card h3 {{ margin: 0 0 0.15rem 0; color: {TEXT}; font-size: 1.3rem; font-weight: 800; letter-spacing: -0.01em; }}
    .lead-card .role {{ color: {TEXT_MUTED}; font-size: 0.92rem; margin-bottom: 0.9rem; }}
    .lead-card .meta-row {{
        display: flex; align-items: center; gap: 0.4rem; color: {TEXT_FAINT}; font-size: 0.8rem;
        padding-top: 0.8rem; border-top: 1px solid {BORDER};
    }}

    /* ---------- Score ring ---------- */
    .score-block {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
        padding: 1.4rem 1.2rem; text-align: center; height: 100%;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
    .score-num {{
        font-size: 2.6rem; font-weight: 800; line-height: 1;
        background: linear-gradient(90deg, {ACCENT}, {PRIMARY_LIGHT});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .score-label {{ color: {TEXT_FAINT}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem; }}

    /* ---------- Email card ---------- */
    .email-card {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; overflow: hidden;
    }}
    .email-card-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.9rem 1.3rem; border-bottom: 1px solid {BORDER}; background: {CARD_HOVER};
    }}
    .email-card-header span {{ color: {TEXT_MUTED}; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }}
    .email-body {{
        padding: 1.3rem 1.4rem; font-family: 'JetBrains Mono', monospace;
        font-size: 0.87rem; color: #D6D4EC; white-space: pre-wrap; line-height: 1.65; max-height: 420px; overflow-y: auto;
    }}

    .followup-banner {{
        background: rgba(45, 224, 184, 0.08); border: 1px solid rgba(45, 224, 184, 0.25);
        border-radius: 10px; padding: 0.7rem 1.1rem; color: {ACCENT}; font-size: 0.86rem; font-weight: 600;
        margin-top: 1rem;
    }}

    /* ---------- Kanban ---------- */
    .kanban-col-title {{
        color: {TEXT}; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.04em;
        padding-bottom: 0.6rem; margin-bottom: 0.9rem; border-bottom: 2px solid {PRIMARY};
        display: flex; justify-content: space-between; align-items: center;
    }}
    .kanban-count {{
        background: {CARD_HOVER}; color: {TEXT_MUTED}; font-size: 0.72rem; font-weight: 700;
        padding: 0.1rem 0.5rem; border-radius: 999px;
    }}
    .kanban-card {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
        padding: 0.85rem 1rem; margin-bottom: 0.6rem;
    }}
    .kanban-card h4 {{ margin: 0 0 0.2rem 0; color: {TEXT}; font-size: 0.92rem; font-weight: 700; }}
    .kanban-card .meta {{ color: {TEXT_FAINT}; font-size: 0.78rem; }}

    /* ---------- Empty state ---------- */
    .empty-state {{
        text-align: center; padding: 3.5rem 1rem; color: {TEXT_MUTED};
        background: {CARD}; border: 1px dashed {BORDER}; border-radius: 14px;
    }}
    .empty-state .icon {{ font-size: 2rem; margin-bottom: 0.6rem; }}

    /* Streamlit native tweaks */
    div[data-testid="stExpander"] {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
    }}
    div[data-testid="stSelectbox"] > div {{ background: {CARD}; border-color: {BORDER}; }}
    hr {{ border-color: {BORDER}; }}
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
# Top bar
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="topbar">
    <div class="brand">
        <div class="brand-mark">🎯</div>
        <div class="brand-text">
            <h1>SalesAgent</h1>
            <p>Autonomous B2B Sales AI</p>
        </div>
    </div>
    <div class="topbar-tagline">Paste a LinkedIn URL — the agent researches, scores, writes, and pipelines the lead in ~45 seconds.</div>
</div>
""", unsafe_allow_html=True)

tab_agent, tab_pipeline, tab_leads = st.tabs(["Run Agent", "Pipeline", "Leads"])

STEP_META = {
    "research": ("🔍", "Researching lead", "Company news, job postings, tech stack"),
    "score": ("📊", "Scoring lead", "Random Forest model — profile & company signals"),
    "email": ("✍️", "Drafting cold email", "Hyper-personalized, referencing real signals"),
    "save": ("💾", "Saving to CRM", "Pipeline entry + auto-scheduled follow-up"),
}
STEP_ORDER = ["research", "score", "email", "save"]

# ---------------------------------------------------------------------------
# TAB 1 — Run Agent
# ---------------------------------------------------------------------------
with tab_agent:
    col_input, col_btn = st.columns([5, 1], vertical_alignment="center")
    with col_input:
        linkedin_url = st.text_input(
            "LinkedIn URL",
            placeholder="https://www.linkedin.com/in/satya-nadella",
            label_visibility="collapsed",
        )
    with col_btn:
        run_clicked = st.button("▶ Run Agent", use_container_width=True)

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
            final_state = None

            st.markdown('<div class="section-label">Agent Trace</div>', unsafe_allow_html=True)
            trace_placeholder = st.empty()
            rendered_steps = {}

            def render_trace():
                rows = ""
                for step in STEP_ORDER:
                    icon, title, sub = STEP_META[step]
                    info = rendered_steps.get(step)
                    done = info is not None
                    badge = '<span class="trace-badge done">DONE</span>' if done else '<span class="trace-badge pending">PENDING</span>'
                    row_class = "trace-row done" if done else "trace-row"
                    rows += f"""
                    <div class="{row_class}">
                        <div class="trace-icon">{icon}</div>
                        <div class="trace-text">{title}<div class="trace-sub">{sub}</div></div>
                        {badge}
                    </div>
                    """
                trace_placeholder.markdown(rows, unsafe_allow_html=True)

            render_trace()

            try:
                for chunk in graph.stream(initial_state, stream_mode="updates"):
                    node_name, node_state = next(iter(chunk.items()))
                    final_state = node_state
                    entries = [e for e in node_state.get("trace", []) if e["step"] == node_name]
                    if any(e["status"] == "done" for e in entries):
                        rendered_steps[node_name] = entries
                    render_trace()

                st.success("Lead processed successfully.")

                profile = (final_state or {}).get("profile", {}) or {}
                score = (final_state or {}).get("lead_score", 0) or 0
                email_draft = (final_state or {}).get("email_draft", "") or ""
                followup = (final_state or {}).get("followup_date", "")
                initials = "".join([p[0] for p in profile.get("name", "?").split()[:2]]).upper() or "?"

                st.markdown('<div class="section-label">Lead Summary</div>', unsafe_allow_html=True)
                col_profile, col_score = st.columns([3, 1])
                with col_profile:
                    company_bit = f" at {profile.get('company')}" if profile.get("company") else ""
                    # FIX: `.get('location', 'Location unknown')` only falls back
                    # when the "location" key is entirely MISSING from the dict.
                    # Our profile dict always has a "location" key (see tools.py),
                    # just often set to "" when the search found nothing — so the
                    # default text never fired and the UI showed a bare pin emoji
                    # with nothing after it. `or` catches falsy values (None, "")
                    # too, not just a missing key.
                    location_text = profile.get('location') or 'Location unknown'
                    st.markdown(f"""
                    <div class="lead-card">
                        <div class="avatar">{initials}</div>
                        <h3>{profile.get('name', 'Unknown')}</h3>
                        <div class="role">{profile.get('title', '')}{company_bit}</div>
                        <div class="meta-row">📍 {location_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_score:
                    st.markdown(f"""
                    <div class="score-block">
                        <div class="score-num">{score:.0f}</div>
                        <div class="score-label">/ 100 lead score</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('<div class="section-label">Generated Email</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="email-card">
                    <div class="email-card-header"><span>Draft — ready to send</span></div>
                    <div class="email-body">{email_draft}</div>
                </div>
                """, unsafe_allow_html=True)
                st.button("📋 Copy email", key="copy_email_btn")

                if followup:
                    st.markdown(f'<div class="followup-banner">📅 Added to pipeline — follow-up scheduled for {followup}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Agent run failed: {e}")

# ---------------------------------------------------------------------------
# TAB 2 — Pipeline (Kanban)
# ---------------------------------------------------------------------------
with tab_pipeline:
    deals = get_all_deals()
    if not deals:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📋</div>
            No deals yet — run the agent on a lead to populate the pipeline.
        </div>
        """, unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="kanban-col-title">
                    <span>{stage}</span>
                    <span class="kanban-count">{len(stage_deals)}</span>
                </div>
                """, unsafe_allow_html=True)
                for d in stage_deals:
                    st.markdown(f"""
                    <div class="kanban-card">
                        <h4>{d.get('lead_name') or d.get('title', 'Deal')}</h4>
                        <div class="meta">{d.get('company', '—')} · Score {d.get('score', 0):.0f}</div>
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
        st.markdown("""
        <div class="empty-state">
            <div class="icon">👥</div>
            No leads yet — run the agent on a lead to see it here.
        </div>
        """, unsafe_allow_html=True)
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
                    st.markdown(f"""
                    <div class="email-card">
                        <div class="email-body">{lead['email_draft']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                interactions = get_interactions(lead["id"])
                if interactions:
                    st.markdown("**Interaction history**")
                    for i in interactions:
                        st.caption(f"{i['created_at']} — {i['type']}")