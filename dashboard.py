"""
MCP Guard — AI Banking Security Gateway  ·  Command Center Dashboard
=====================================================================
⚠️  SIMULATED DEMO — NOT PRODUCTION BANKING SOFTWARE ⚠️

All accounts and transactions are entirely fictional.
No real financial data is used or stored anywhere in this application.
"""

import collections
import json
import os
import sys
from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="MCP Guard · Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guard  # noqa: E402
from bank import ACCOUNTS  # noqa: E402
from guard import (  # noqa: E402
    AUDIT_LOG,
    AUDIT_LOG_PATH,
    PENDING_APPROVALS,
    TOOL_INVENTORY,
    approve_transfer,
    handle_request,
    reject_transfer,
)

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL STYLES  — SentinelX-class dark cybersecurity aesthetic
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Variables ── */
:root {
  --bg:        #0d1117;
  --bg2:       #161b22;
  --bg3:       #1c2333;
  --bg4:       #21262d;
  --border:    rgba(48,54,61,0.9);
  --border-h:  rgba(56,139,253,0.4);
  --txt:       #e6edf3;
  --txt2:      #8b949e;
  --txt3:      #484f58;
  --blue:      #388bfd;
  --blue-d:    rgba(56,139,253,0.12);
  --teal:      #39d0c0;
  --teal-d:    rgba(57,208,192,0.12);
  --green:     #3fb950;
  --green-d:   rgba(63,185,80,0.12);
  --amber:     #d29922;
  --amber-d:   rgba(210,153,34,0.12);
  --red:       #f85149;
  --red-d:     rgba(248,81,73,0.12);
  --purple:    #bc8cff;
  --purple-d:  rgba(188,140,255,0.12);
}

/* ── Reset & base ── */
html, body, [class*="css"] {
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
  color: var(--txt) !important;
}

/* ── App background ── */
.stApp {
  background: var(--bg) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--txt2) !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* ── Hide chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 1440px !important; }

/* ── Top nav bar ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.7rem 1.5rem; background: var(--bg2);
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.25rem; position: sticky; top: 0; z-index: 100;
}
.topbar-brand { display: flex; align-items: center; gap: 0.6rem; }
.topbar-brand-name { font-size: 1.05rem; font-weight: 700; color: var(--txt) !important; letter-spacing: -0.01em; }
.topbar-nav { display: flex; gap: 0.15rem; }
.topbar-nav-item {
  padding: 0.35rem 0.85rem; border-radius: 6px;
  font-size: 0.8rem; font-weight: 500; color: var(--txt2);
  cursor: pointer; transition: all 0.15s; border: none; background: none;
}
.topbar-nav-item.active { background: var(--bg3); color: var(--txt); }
.topbar-right { display: flex; align-items: center; gap: 0.75rem; }
.topbar-badge {
  background: var(--amber-d); border: 1px solid rgba(210,153,34,0.35);
  border-radius: 99px; padding: 0.2rem 0.65rem;
  font-size: 0.65rem; font-weight: 700; color: var(--amber);
  letter-spacing: 0.06em; text-transform: uppercase;
}
.topbar-scan-btn {
  background: var(--blue); color: #fff !important;
  border: none; border-radius: 6px;
  padding: 0.35rem 0.85rem; font-size: 0.78rem; font-weight: 600;
  cursor: pointer;
}

/* ── KPI cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.85rem; margin-bottom: 1.1rem; }
.kpi {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 1.1rem 1.25rem;
  position: relative; overflow: hidden;
}
.kpi::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: var(--kpi-color, var(--blue));
}
.kpi-label { font-size: 0.68rem; font-weight: 600; color: var(--txt2); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.35rem; }
.kpi-value { font-size: 2rem; font-weight: 800; color: var(--kpi-color, var(--txt)); line-height: 1; margin-bottom: 0.3rem; }
.kpi-sub { font-size: 0.7rem; color: var(--txt3); display: flex; align-items: center; gap: 0.3rem; }
.kpi-up   { color: var(--green); font-weight: 600; }
.kpi-down { color: var(--red);   font-weight: 600; }
.kpi-icon { position: absolute; top: 1rem; right: 1rem; opacity: 0.18; }

/* ── Panel card ── */
.panel {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 1.1rem 1.25rem;
  margin-bottom: 0.85rem;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 0.9rem; padding-bottom: 0.7rem;
  border-bottom: 1px solid var(--border);
}
.panel-title {
  font-size: 0.82rem; font-weight: 700; color: var(--txt);
  display: flex; align-items: center; gap: 0.5rem;
}
.panel-title-dot { width: 7px; height: 7px; border-radius: 50%; }
.panel-action {
  font-size: 0.7rem; color: var(--blue); font-weight: 600;
  background: var(--blue-d); border: 1px solid rgba(56,139,253,0.25);
  border-radius: 5px; padding: 0.15rem 0.55rem; cursor: pointer;
}

/* ── Status pills ── */
.pill {
  display: inline-flex; align-items: center; gap: 0.3rem;
  border-radius: 99px; padding: 0.15rem 0.6rem;
  font-size: 0.63rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
}
.pill::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.pill-ok     { background: var(--green-d);  color: var(--green);  border: 1px solid rgba(63,185,80,0.3);  }
.pill-deny   { background: var(--red-d);    color: var(--red);    border: 1px solid rgba(248,81,73,0.3);  }
.pill-pend   { background: var(--amber-d);  color: var(--amber);  border: 1px solid rgba(210,153,34,0.3); }
.pill-info   { background: var(--blue-d);   color: var(--blue);   border: 1px solid rgba(56,139,253,0.3); }
.pill-hi     { background: var(--red-d);    color: var(--red);    border: 1px solid rgba(248,81,73,0.3);  }
.pill-lo     { background: var(--green-d);  color: var(--green);  border: 1px solid rgba(63,185,80,0.3);  }
.pill-crit   { background: rgba(248,81,73,0.25); color: #ff6b6b; border: 1px solid rgba(248,81,73,0.5); }

/* ── Risk badge ── */
.risk { display: inline-block; border-radius: 5px; padding: 0.1rem 0.45rem; font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.risk-high   { background: var(--red-d);   color: var(--red);   border: 1px solid rgba(248,81,73,0.3); }
.risk-low    { background: var(--green-d); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }
.risk-medium { background: var(--amber-d); color: var(--amber); border: 1px solid rgba(210,153,34,0.3); }

/* ── Code chip ── */
.code { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #79c0ff; }
.arg-chip {
  display: inline-block; background: var(--blue-d); border: 1px solid rgba(56,139,253,0.2);
  border-radius: 4px; padding: 0.08rem 0.4rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.63rem; color: #79c0ff; margin: 0.07rem;
}

/* ── Alert banners ── */
.alert { border-radius: 8px; padding: 0.7rem 1rem; font-size: 0.8rem; margin-bottom: 0.75rem; border: 1px solid; }
.alert-info   { background: var(--blue-d);  border-color: rgba(56,139,253,0.3);  color: #79c0ff; }
.alert-ok     { background: var(--green-d); border-color: rgba(63,185,80,0.3);   color: #56d364; }
.alert-warn   { background: var(--amber-d); border-color: rgba(210,153,34,0.3);  color: #e3b341; }
.alert-danger { background: var(--red-d);   border-color: rgba(248,81,73,0.3);   color: #ff7b72; }
.alert-sim    { background: rgba(13,17,23,0.9); border-color: rgba(210,153,34,0.5); color: #e3b341;
                border-left: 3px solid var(--amber); font-size: 0.73rem; }

/* ── Activity feed ── */
.feed-row { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid var(--border); }
.feed-row:last-child { border-bottom: none; }
.feed-pip { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 0.35rem; }
.pip-ok   { background: var(--green); box-shadow: 0 0 5px var(--green); }
.pip-no   { background: var(--red);   box-shadow: 0 0 5px var(--red);   }
.pip-pen  { background: var(--amber); box-shadow: 0 0 5px var(--amber); }
.feed-main { font-size: 0.8rem; color: var(--txt2); }
.feed-ts   { font-size: 0.65rem; color: var(--txt3); font-family: 'JetBrains Mono', monospace; margin-top: 0.1rem; }

/* ── Bar chart ── */
.bar-wrap { background: rgba(255,255,255,0.04); border-radius: 99px; overflow: hidden; margin-top: 0.2rem; }
.bar-fill  { height: 5px; border-radius: 99px; }

/* ── Table ── */
.tbl { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.tbl th { font-size: 0.62rem; font-weight: 700; color: var(--txt3); text-transform: uppercase; letter-spacing: 0.1em; padding: 0 0.5rem 0.55rem; text-align: left; border-bottom: 1px solid var(--border); }
.tbl td { padding: 0.55rem 0.5rem; border-bottom: 1px solid rgba(48,54,61,0.5); color: var(--txt2); vertical-align: middle; }
.tbl tr:last-child td { border-bottom: none; }
.tbl tr:hover td { background: rgba(22,27,34,0.5); }

/* ── Progress gauge ── */
.gauge-wrap { text-align: center; }
.gauge-pct  { font-size: 2.5rem; font-weight: 900; color: var(--blue); line-height: 1; }
.gauge-sub  { font-size: 0.7rem; color: var(--txt3); margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.1em; }

/* ── Tool card ── */
.tool-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 9px; padding: 1rem 1.15rem; margin-bottom: 0.8rem;
  border-left: 3px solid var(--blue);
}

/* ── Approval card ── */
.appr-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 9px; padding: 1rem 1.15rem; margin-bottom: 0.8rem;
  border-left: 3px solid var(--amber);
}

/* ── Section heading ── */
.sec-head {
  font-size: 0.62rem; font-weight: 700; color: var(--txt3);
  letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 0.7rem;
  display: flex; align-items: center; gap: 0.5rem;
}
.sec-head::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── Page title ── */
.pg-eyebrow { font-size: 0.68rem; font-weight: 600; color: var(--blue); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.2rem; }
.pg-title   { font-size: 1.45rem; font-weight: 800; color: var(--txt); letter-spacing: -0.02em; margin-bottom: 0.25rem; line-height: 1.2; }
.pg-desc    { font-size: 0.75rem; color: var(--txt3); margin-bottom: 1.25rem; }

/* ── Streamlit overrides ── */
[data-testid="stMetricValue"] { color: var(--blue) !important; font-size: 1.5rem !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: var(--txt3) !important; font-size: 0.63rem !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }

.stButton > button {
  background: var(--bg3) !important; border: 1px solid var(--border) !important;
  color: var(--txt2) !important; border-radius: 6px !important;
  font-size: 0.8rem !important; font-weight: 500 !important;
  transition: border-color 0.15s, color 0.15s !important;
}
.stButton > button:hover { border-color: var(--border-h) !important; color: var(--txt) !important; }

.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input {
  background: var(--bg3) !important; border: 1px solid var(--border) !important;
  color: var(--txt) !important; border-radius: 6px !important; font-size: 0.82rem !important;
}
.stSelectbox > div > div:focus-within { border-color: var(--border-h) !important; }

[data-baseweb="tab-list"] {
  background: var(--bg3) !important; border-radius: 7px !important;
  border: 1px solid var(--border) !important; padding: 0.12rem !important; gap: 0 !important;
}
[data-baseweb="tab"] { color: var(--txt3) !important; border-radius: 5px !important; font-size: 0.78rem !important; }
[aria-selected="true"][data-baseweb="tab"] { background: var(--bg4) !important; color: var(--txt) !important; }

[data-testid="stExpander"] { background: var(--bg3) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
.stDataFrame { background: transparent !important; }
[data-testid="stDataFrame"] > div { background: var(--bg3) !important; border-radius: 8px !important; border: 1px solid var(--border) !important; }
hr { border-color: var(--border) !important; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(56,139,253,0.2); border-radius: 99px; }

/* Restore the left sidebar */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    min-width: 300px !important;
    width: 300px !important;
    transform: none !important;
}
[data-testid="stSidebarContent"] {
    display: block !important;
    visibility: visible !important;
}

</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _fmt_inr(amount: float) -> str:
    return f"₹{amount:,.2f}"

def _load_audit_log() -> list[dict]:
    path = os.environ.get("MCP_GUARD_AUDIT_LOG", "audit.jsonl")
    records: list[dict] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return records

def _all_audit_entries() -> list[dict]:
    persistent = _load_audit_log()
    session    = list(AUDIT_LOG)
    seen: set  = set()
    merged: list[dict] = []
    for e in persistent + session:
        key = (e.get("time"), e.get("user_id"), e.get("tool"))
        if key not in seen:
            seen.add(key)
            merged.append(e)
    return merged

def _user_accounts() -> dict[str, set]:
    mapping: dict[str, set] = {}
    for spec in TOOL_INVENTORY.values():
        for uid, accts in spec.get("permitted_callers", {}).items():
            mapping.setdefault(uid, set()).update(accts)
    return mapping


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
NAV_ITEMS = [
    ("overview",  "Command Center"),
    ("activity",  "Threat Intel"),
    ("analytics", "Analytics"),
    ("tools",     "Assets"),
    ("balance",   "Balance Lookup"),
    ("transfer",  "Transfer Request"),
    ("approvals", "Approval Center"),
    ("audit",     "Audit Log"),
]

if "nav" not in st.session_state:
    st.session_state["nav"] = "overview"

with st.sidebar:
    # Brand
    st.markdown("""
    <div style="padding:1.2rem 1rem 0.9rem;border-bottom:1px solid rgba(48,54,61,0.9);">
      <div style="display:flex;align-items:center;gap:0.65rem;margin-bottom:0.8rem;">
        <svg width="30" height="30" viewBox="0 0 30 30" fill="none">
          <path d="M15 2L3 7v7c0 7 4.8 13.5 12 15 7.2-1.5 12-8 12-15V7L15 2z"
                fill="rgba(56,139,253,0.15)" stroke="rgba(56,139,253,0.7)" stroke-width="1.2"/>
          <circle cx="15" cy="14" r="4" fill="rgba(56,139,253,0.3)" stroke="#388bfd" stroke-width="1"/>
          <path d="M15 10v4l2.5 2.5" stroke="#388bfd" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <div>
          <div style="font-size:0.95rem;font-weight:800;color:#e6edf3;letter-spacing:-0.01em;">MCP Guard</div>
          <div style="font-size:0.58rem;color:#484f58;letter-spacing:0.1em;text-transform:uppercase;">AI Security Gateway</div>
        </div>
      </div>
      <div style="background:rgba(210,153,34,0.08);border:1px solid rgba(210,153,34,0.25);border-radius:6px;padding:0.35rem 0.6rem;">
        <span style="font-size:0.58rem;font-weight:700;color:#e3b341;letter-spacing:0.1em;text-transform:uppercase;">⚠ Simulation Mode</span>
        <div style="font-size:0.62rem;color:#484f58;margin-top:0.05rem;">Fictional data only</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='padding:0.5rem 0.5rem;'>", unsafe_allow_html=True)
    for key, label in NAV_ITEMS:
        active = st.session_state["nav"] == key
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state["nav"] = key
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Stats
    all_e = _all_audit_entries()
    ok_c  = sum(1 for e in all_e if e.get("allowed"))
    den_c = len(all_e) - ok_c
    st.markdown(f"""
    <div style="margin:0 0.5rem 0.5rem;padding:0.85rem;background:rgba(13,17,23,0.8);
                border:1px solid rgba(48,54,61,0.9);border-radius:8px;">
      <div style="font-size:0.58rem;font-weight:700;color:#484f58;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.55rem;">System Stats</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;">
        <div style="text-align:center;padding:0.4rem;background:rgba(63,185,80,0.06);border-radius:5px;border:1px solid rgba(63,185,80,0.12);">
          <div style="font-size:1.05rem;font-weight:800;color:#3fb950;">{ok_c}</div>
          <div style="font-size:0.55rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;">Auth</div>
        </div>
        <div style="text-align:center;padding:0.4rem;background:rgba(248,81,73,0.06);border-radius:5px;border:1px solid rgba(248,81,73,0.12);">
          <div style="font-size:1.05rem;font-weight:800;color:#f85149;">{den_c}</div>
          <div style="font-size:0.55rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;">Blocked</div>
        </div>
        <div style="text-align:center;padding:0.4rem;background:rgba(210,153,34,0.06);border-radius:5px;border:1px solid rgba(210,153,34,0.12);">
          <div style="font-size:1.05rem;font-weight:800;color:#d29922;">{len(PENDING_APPROVALS)}</div>
          <div style="font-size:0.55rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;">Pending</div>
        </div>
        <div style="text-align:center;padding:0.4rem;background:rgba(56,139,253,0.06);border-radius:5px;border:1px solid rgba(56,139,253,0.12);">
          <div style="font-size:1.05rem;font-weight:800;color:#388bfd;">{len(TOOL_INVENTORY)}</div>
          <div style="font-size:0.55rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;">Tools</div>
        </div>
      </div>
    </div>
    <div style="padding:0.6rem 1rem;font-size:0.58rem;color:#30363d;text-align:center;border-top:1px solid rgba(48,54,61,0.6);">
      v3.0 · MCP Guard · Simulated
    </div>
    """, unsafe_allow_html=True)


page = st.session_state["nav"]

# ── nav label lookup ──────────────────────────────────────────────────────────
_NAV_LABELS = {
    "overview":  "Command Center",
    "activity":  "Threat Intel",
    "analytics": "Analytics",
    "tools":     "Assets",
    "balance":   "Balance Lookup",
    "transfer":  "Transfer Request",
    "approvals": "Approval Center",
    "audit":     "Audit Log",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL TOP BAR + SIM BANNER  — rendered on every page
# ═══════════════════════════════════════════════════════════════════════════════
_nav_items_top = [
    ("overview",  "Command Center"),
    ("activity",  "Threat Intel"),
    ("analytics", "Analytics"),
    ("tools",     "Assets"),
    ("balance",   "Balance Lookup"),
    ("transfer",  "Transfer"),
    ("approvals", "Approvals"),
    ("audit",     "Audit Log"),
]
_nav_html = ""
for _key, _lbl in _nav_items_top:
    _cls = "topbar-nav-item active" if _key == page else "topbar-nav-item"
    _nav_html += f'<span class="{_cls}">{_lbl}</span>'

st.markdown(f"""
<div class="topbar">
  <div class="topbar-brand">
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <path d="M11 1L2 5v5.5c0 5 3.5 9.7 9 11 5.5-1.3 9-6 9-11V5L11 1z"
            fill="rgba(56,139,253,0.15)" stroke="#388bfd" stroke-width="1.1"/>
      <circle cx="11" cy="10.5" r="3" fill="#388bfd" opacity="0.4"/>
    </svg>
    <span class="topbar-brand-name">MCP Guard</span>
  </div>
  <div class="topbar-nav">{_nav_html}</div>
  <div class="topbar-right">
    <span class="topbar-badge">⚠ Simulation Mode</span>
    <span class="topbar-scan-btn">⬡ Deep Scan</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="alert-sim">⚠ SIMULATION MODE — All banking accounts and transactions are entirely fictional. Not real banking software.</div>',
    unsafe_allow_html=True,
)


# ── helper: page header ────────────────────────────────────────────────────────
def _hdr(eye: str, title: str, desc: str = ""):
    d = f'<div class="pg-desc">{desc}</div>' if desc else ""
    st.markdown(f'<div class="pg-eyebrow">{eye}</div><div class="pg-title">{title}</div>{d}',
                unsafe_allow_html=True)


# ── global download button (top-right area, rendered once per page) ────────────
with open(__file__, "rb") as _fh:
    _src_bytes = _fh.read()
with st.sidebar:
    st.download_button(
        label="⬇ Download dashboard.py",
        data=_src_bytes,
        file_name="dashboard.py",
        mime="text/x-python",
        use_container_width=True,
        help="Download the full dashboard source code",
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — COMMAND CENTER  (Overview)
# ═══════════════════════════════════════════════════════════════════════════════
if page == "overview":
    # ── KPI cards ──
    total_balance = sum(v["balance"] for v in ACCOUNTS.values())
    user_map      = _user_accounts()
    all_audit     = _all_audit_entries()
    allowed_c     = sum(1 for e in all_audit if e.get("allowed"))
    denied_c      = len(all_audit) - allowed_c
    block_rate    = (denied_c / len(all_audit) * 100) if all_audit else 0
    pass_rate     = 100 - block_rate

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi" style="--kpi-color:var(--amber)">
          <div class="kpi-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M12 2L4 6v5c0 6.5 4 12 8 13.5C16 23 20 17.5 20 11V6L12 2z" fill="currentColor"/></svg></div>
          <div class="kpi-label">Global Threat Level</div>
          <div class="kpi-value" style="font-size:1.6rem;">Guarded</div>
          <div class="kpi-sub"><span class="kpi-up">↑</span> Policy engine active</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi" style="--kpi-color:var(--red)">
          <div class="kpi-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="M12 7v5l3 3" stroke="white" stroke-width="1.5" stroke-linecap="round"/></svg></div>
          <div class="kpi-label">Active Incidents</div>
          <div class="kpi-value">{denied_c}</div>
          <div class="kpi-sub"><span class="kpi-down">↑</span> Blocked requests total</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi" style="--kpi-color:var(--green)">
          <div class="kpi-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none"><rect x="2" y="3" width="20" height="14" rx="2" fill="currentColor"/></svg></div>
          <div class="kpi-label">Systems Online</div>
          <div class="kpi-value">{len(all_audit)}</div>
          <div class="kpi-sub"><span class="kpi-up">✓</span> {pass_rate:.1f}% pass rate</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi" style="--kpi-color:var(--blue)">
          <div class="kpi-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M1 6l11 7 11-7" stroke="currentColor" stroke-width="1.5"/><rect x="1" y="6" width="22" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></div>
          <div class="kpi-label">Network Traffic</div>
          <div class="kpi-value" style="font-size:1.4rem;">{_fmt_inr(total_balance)}</div>
          <div class="kpi-sub"><span style="color:var(--txt3)">—</span> Simulated funds total</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Three-column layout: System Integrity + Security Model + Live Topology ──
    col_l, col_m, col_r = st.columns([1.2, 1.5, 1.5])

    with col_l:
        st.markdown("""
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <div class="panel-title-dot" style="background:var(--blue)"></div>
              System Integrity
            </div>
            <span class="panel-action">Diagnostics</span>
          </div>
        """, unsafe_allow_html=True)

        # Gauge
        pct = min(100, int(pass_rate))
        # Draw arc gauge via SVG
        r = 54; cx = 70; cy = 70
        circumference = 2 * 3.14159 * r
        # 75% arc (270 degrees of the circle)
        arc_len = circumference * 0.75
        offset  = arc_len * (1 - pct / 100)
        st.markdown(f"""
        <div style="display:flex;justify-content:center;padding:0.5rem 0 0.3rem;">
        <svg width="140" height="100" viewBox="0 0 140 100">
          <!-- Track -->
          <circle cx="70" cy="70" r="{r}" fill="none" stroke="rgba(48,54,61,0.8)" stroke-width="9"
                  stroke-dasharray="{arc_len:.1f} {circumference:.1f}"
                  stroke-dashoffset="0"
                  transform="rotate(135 70 70)" stroke-linecap="round"/>
          <!-- Fill -->
          <circle cx="70" cy="70" r="{r}" fill="none" stroke="#388bfd" stroke-width="9"
                  stroke-dasharray="{arc_len:.1f} {circumference:.1f}"
                  stroke-dashoffset="{offset:.1f}"
                  transform="rotate(135 70 70)" stroke-linecap="round"/>
          <text x="70" y="68" text-anchor="middle" font-family="Inter,sans-serif" font-size="22" font-weight="900" fill="#388bfd">{pct}%</text>
          <text x="70" y="83" text-anchor="middle" font-family="Inter,sans-serif" font-size="9" fill="#484f58">OVERALL INTEGRITY</text>
        </svg>
        </div>
        """, unsafe_allow_html=True)

        # System metrics
        metrics = [
            ("MEMORY",    "72%",  72,  "#388bfd"),
            ("PROCESSOR", "41%",  41,  "#3fb950"),
            ("STORAGE",   "68%",  68,  "#d29922"),
        ]
        row_html = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;margin-bottom:0.8rem;">'
        for lbl, val, pct_v, col in metrics:
            row_html += f'<div style="text-align:center;"><div style="font-size:1rem;font-weight:800;color:{col};">{val}</div><div style="font-size:0.58rem;color:var(--txt3);text-transform:uppercase;letter-spacing:0.08em;">{lbl}</div></div>'
        row_html += '</div>'
        st.markdown(row_html, unsafe_allow_html=True)

        # Policy table
        tbl = """
        <table class="tbl">
          <tr><td>WAF</td><td><span class="pill pill-ok">Active</span></td>
              <td>EDR</td><td><span class="pill pill-ok">Connected</span></td></tr>
          <tr><td>IPS</td><td><span class="pill pill-ok">Enabled</span></td>
              <td>SSL</td><td><span class="pill pill-ok">Valid</span></td></tr>
          <tr><td>MFA</td><td><span class="pill pill-pend">Required</span></td>
              <td>VPN</td><td><span class="pill pill-ok">Secure</span></td></tr>
        </table>
        """
        st.markdown(tbl + "</div>", unsafe_allow_html=True)

    with col_m:
        st.markdown("""
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <div class="panel-title-dot" style="background:var(--teal)"></div>
              Security Gateway Model
            </div>
            <span class="panel-action">↺ Sync</span>
          </div>
        """, unsafe_allow_html=True)

        # Gateway flow diagram as SVG
        st.markdown("""
        <svg width="100%" viewBox="0 0 380 220" xmlns="http://www.w3.org/2000/svg" style="font-family:Inter,sans-serif;">
          <defs>
            <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="rgba(56,139,253,0.6)"/>
            </marker>
            <filter id="glow2"><feGaussianBlur stdDeviation="3" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>

          <!-- AI Client -->
          <rect x="8" y="80" width="72" height="42" rx="7" fill="rgba(188,140,255,0.08)" stroke="rgba(188,140,255,0.4)" stroke-width="1"/>
          <text x="44" y="97" text-anchor="middle" font-size="8" fill="#bc8cff" font-weight="700">AI / MCP</text>
          <text x="44" y="110" text-anchor="middle" font-size="7" fill="#484f58">Tool Request</text>

          <!-- Arrow 1 -->
          <line x1="82" y1="101" x2="108" y2="101" stroke="rgba(56,139,253,0.5)" stroke-width="1.2" marker-end="url(#arr)" stroke-dasharray="3,2"/>

          <!-- Guard / Policy Engine -->
          <rect x="110" y="60" width="90" height="82" rx="7" fill="rgba(56,139,253,0.08)" stroke="rgba(56,139,253,0.5)" stroke-width="1.2" filter="url(#glow2)"/>
          <rect x="110" y="60" width="90" height="16" rx="7" fill="rgba(56,139,253,0.18)"/>
          <text x="155" y="71" text-anchor="middle" font-size="7.5" fill="#388bfd" font-weight="800">MCP GUARD</text>
          <text x="155" y="92" text-anchor="middle" font-size="8" fill="#8b949e">Policy Engine</text>
          <text x="155" y="105" text-anchor="middle" font-size="7" fill="#484f58">Auth · Validate</text>
          <text x="155" y="117" text-anchor="middle" font-size="7" fill="#484f58">Risk Score</text>
          <text x="155" y="134" text-anchor="middle" font-size="7" fill="#484f58">↑ guard.py</text>

          <!-- Fork arrows -->
          <line x1="200" y1="88" x2="228" y2="68" stroke="rgba(63,185,80,0.6)" stroke-width="1.1" marker-end="url(#arr)"/>
          <line x1="200" y1="114" x2="228" y2="134" stroke="rgba(248,81,73,0.6)" stroke-width="1.1" marker-end="url(#arr)"/>

          <!-- Allow box -->
          <rect x="230" y="50" width="70" height="30" rx="5" fill="rgba(63,185,80,0.08)" stroke="rgba(63,185,80,0.35)" stroke-width="1"/>
          <text x="265" y="63" text-anchor="middle" font-size="7.5" fill="#3fb950" font-weight="700">AUTHORIZED</text>
          <text x="265" y="74" text-anchor="middle" font-size="6.5" fill="#484f58">→ Queued / Exec</text>

          <!-- Deny box -->
          <rect x="230" y="118" width="70" height="30" rx="5" fill="rgba(248,81,73,0.08)" stroke="rgba(248,81,73,0.35)" stroke-width="1"/>
          <text x="265" y="131" text-anchor="middle" font-size="7.5" fill="#f85149" font-weight="700">DENIED</text>
          <text x="265" y="142" text-anchor="middle" font-size="6.5" fill="#484f58">→ Audit logged</text>

          <!-- Arrow to approval -->
          <line x1="300" y1="65" x2="326" y2="85" stroke="rgba(210,153,34,0.5)" stroke-width="1.1" marker-end="url(#arr)"/>

          <!-- Approval queue -->
          <rect x="308" y="86" width="66" height="38" rx="5" fill="rgba(210,153,34,0.08)" stroke="rgba(210,153,34,0.35)" stroke-width="1"/>
          <text x="341" y="101" text-anchor="middle" font-size="7.5" fill="#d29922" font-weight="700">APPROVAL</text>
          <text x="341" y="113" text-anchor="middle" font-size="7" fill="#484f58">Queue</text>

          <!-- Audit trail -->
          <rect x="110" y="160" width="230" height="28" rx="5" fill="rgba(13,17,23,0.6)" stroke="rgba(48,54,61,0.9)" stroke-width="0.8"/>
          <text x="225" y="173" text-anchor="middle" font-size="7" fill="#484f58">↓ All decisions → </text>
          <text x="285" y="173" text-anchor="middle" font-size="7" fill="#388bfd" font-weight="600">audit.jsonl</text>
          <text x="225" y="183" text-anchor="middle" font-size="6.5" fill="#30363d">(immutable audit trail)</text>
        </svg>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">
              <div class="panel-title-dot" style="background:var(--teal)"></div>
              Live Topology
            </div>
          </div>
        """, unsafe_allow_html=True)

        # Network topology SVG visualization
        topology_component = """<!DOCTYPE html>
<html><head>
<style>
  body{margin:0;padding:0;background:#161b22;overflow:hidden;}
  canvas{display:block;}
</style>
</head><body>
<canvas id="c"></canvas>
<script>
var C=document.getElementById('c');
var W=C.width=C.offsetWidth||360,H=C.height=220;
var ctx=C.getContext('2d');

// Named nodes representing security components
var nodes=[
  {x:W*0.5,y:H*0.45,r:10,col:'#388bfd',label:'Guard',halo:true},
  {x:W*0.2,y:H*0.25,r:6,col:'#3fb950',label:'Riya'},
  {x:W*0.8,y:H*0.25,r:6,col:'#3fb950',label:'Arjun'},
  {x:W*0.15,y:H*0.7,r:5,col:'#bc8cff',label:'ACC-1001'},
  {x:W*0.38,y:H*0.75,r:5,col:'#bc8cff',label:'ACC-1002'},
  {x:W*0.85,y:H*0.7,r:5,col:'#bc8cff',label:'ACC-2001'},
  {x:W*0.5,y:H*0.88,r:7,col:'#39d0c0',label:'Bank API'},
  {x:W*0.08,y:H*0.45,r:4,col:'#f85149',label:'Threat'},
  {x:W*0.92,y:H*0.45,r:4,col:'#f85149',label:'Threat'},
];

var edges=[
  [0,1],[0,2],[0,3],[0,4],[0,5],[0,6],
  [1,3],[1,4],[2,5],[6,3],[6,4],[6,5],
];

var particles=[];
function spawnP(ei){
  var e=edges[ei],n0=nodes[e[0]],n1=nodes[e[1]];
  particles.push({ei:ei,t:0,speed:0.008+Math.random()*0.006,
    col:Math.random()<0.7?'rgba(56,139,253,':'rgba(57,208,192,'});
}
for(var i=0;i<edges.length;i++) if(Math.random()<0.5) spawnP(i);

var pulse=0;
function draw(ts){
  ctx.clearRect(0,0,W,H);
  // BG gradient
  var g=ctx.createRadialGradient(W*0.5,H*0.45,0,W*0.5,H*0.45,Math.max(W,H)*0.7);
  g.addColorStop(0,'#1c2333');g.addColorStop(1,'#161b22');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);

  pulse+=0.02;

  // Grid
  ctx.strokeStyle='rgba(48,54,61,0.5)';ctx.lineWidth=0.4;
  for(var x=0;x<W;x+=30){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for(var y=0;y<H;y+=30){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}

  // Edges
  edges.forEach(function(e){
    var a=nodes[e[0]],b=nodes[e[1]];
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
    ctx.strokeStyle='rgba(56,139,253,0.15)';ctx.lineWidth=0.8;ctx.stroke();
  });

  // Particles
  for(var i=particles.length-1;i>=0;i--){
    var p=particles[i]; p.t+=p.speed;
    if(p.t>=1){particles.splice(i,1);spawnP(Math.floor(Math.random()*edges.length));continue;}
    var e=edges[p.ei],na=nodes[e[0]],nb=nodes[e[1]];
    var px=na.x+(nb.x-na.x)*p.t,py=na.y+(nb.y-na.y)*p.t;
    var t0=Math.max(0,p.t-0.12);
    var px0=na.x+(nb.x-na.x)*t0,py0=na.y+(nb.y-na.y)*t0;
    var grad=ctx.createLinearGradient(px0,py0,px,py);
    grad.addColorStop(0,p.col+'0)');grad.addColorStop(1,p.col+'1)');
    ctx.beginPath();ctx.moveTo(px0,py0);ctx.lineTo(px,py);
    ctx.strokeStyle=grad;ctx.lineWidth=1.8;ctx.stroke();
    ctx.beginPath();ctx.arc(px,py,2.5,0,Math.PI*2);
    ctx.fillStyle=p.col+'1)';ctx.fill();
  }

  // Nodes
  nodes.forEach(function(n){
    if(n.halo){
      ctx.beginPath();ctx.arc(n.x,n.y,n.r*2.5+Math.sin(pulse)*2,0,Math.PI*2);
      ctx.fillStyle='rgba(56,139,253,0.08)';ctx.fill();
      ctx.beginPath();ctx.arc(n.x,n.y,n.r*1.6,0,Math.PI*2);
      ctx.fillStyle='rgba(56,139,253,0.15)';ctx.fill();
    }
    ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
    ctx.fillStyle=n.col;ctx.fill();
    // Label
    ctx.font='bold 7px Inter,sans-serif';
    ctx.fillStyle='rgba(139,148,158,0.9)';
    ctx.textAlign='center';
    ctx.fillText(n.label,n.x,n.y+n.r+10);
  });

  // Threat nodes pulsing red ring
  [7,8].forEach(function(i){
    var n=nodes[i];
    ctx.beginPath();ctx.arc(n.x,n.y,n.r+4+Math.sin(pulse*2)*2,0,Math.PI*2);
    ctx.strokeStyle='rgba(248,81,73,0.3)';ctx.lineWidth=1;ctx.stroke();
  });

  requestAnimationFrame(draw);
}
draw(0);
</script>
</body></html>"""
        components.html(topology_component, height=225, scrolling=False)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Connected accounts table ──
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Connected Nodes & Assets</div>', unsafe_allow_html=True)

    # Build rows
    rows_data = []
    for acct_id, details in ACCOUNTS.items():
        bal = details["balance"]
        owners = [u for u, accts in _user_accounts().items() if acct_id in accts]
        integrity = min(100, int(bal / 500))
        threat = "Critical" if bal < 5000 else "Low"
        rows_data.append({
            "acct": acct_id, "owners": owners, "bal": bal,
            "integrity": integrity, "threat": threat
        })

    tbl_html = """
    <div class="panel" style="padding:0;">
    <table class="tbl" style="margin:0;">
      <thead><tr>
        <th style="padding:0.6rem 1rem;">Account</th>
        <th>Owner</th>
        <th>Balance (Simulated)</th>
        <th>Integrity Score</th>
        <th>Threat Level</th>
        <th>Pending</th>
      </tr></thead><tbody>
    """
    for r in rows_data:
        bar_w = r["integrity"]
        bar_col = "#3fb950" if bar_w > 70 else "#d29922" if bar_w > 30 else "#f85149"
        threat_pill = f'<span class="pill pill-crit">{r["threat"]}</span>' if r["threat"]=="Critical" else f'<span class="pill pill-ok">{r["threat"]}</span>'
        owner_str = ", ".join(r["owners"]) or "—"
        tbl_html += f"""<tr>
          <td><span class="code">{r["acct"]}</span></td>
          <td style="color:var(--txt)">{owner_str}</td>
          <td style="color:var(--txt)">{_fmt_inr(r["bal"])}</td>
          <td style="min-width:120px;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <div class="bar-wrap" style="flex:1;"><div class="bar-fill" style="width:{bar_w}%;background:{bar_col};"></div></div>
              <span style="font-size:0.7rem;color:var(--txt2);font-weight:600;">{bar_w}%</span>
            </div>
          </td>
          <td>{threat_pill}</td>
          <td><span style="font-size:0.72rem;color:var(--txt3);">{len(PENDING_APPROVALS)} pending</span></td>
        </tr>"""
    tbl_html += "</tbody></table></div>"
    st.markdown(tbl_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — THREAT INTEL  (Activity Feed)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "activity":
    _hdr("Threat Intelligence", "Activity Feed",
         "Security events from the MCP Guard policy engine, newest first.")

    all_entries = _all_audit_entries()
    recent = list(reversed(all_entries[-60:]))

    if st.button("↺  Refresh Feed"):
        st.rerun()

    if not recent:
        st.markdown('<div class="alert-info">No events yet. Submit a balance check or transfer request.</div>',
                    unsafe_allow_html=True)
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Events",  len(all_entries))
        c2.metric("Authorized",    sum(1 for e in all_entries if e.get("allowed")))
        c3.metric("Blocked",       sum(1 for e in all_entries if not e.get("allowed")))
        c4.metric("Showing",       len(recent))

        st.markdown("<br/>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["All Events", "Authorized", "Blocked"])

        def _feed(entries: list[dict]) -> None:
            if not entries:
                st.markdown('<div class="alert-info">No events match this filter.</div>', unsafe_allow_html=True)
                return
            html = '<div class="panel" style="padding:0.4rem 1.1rem;">'
            for e in entries[:50]:
                ok     = e.get("allowed", False)
                reason = e.get("reason", "—")
                pip    = "pip-ok" if ok else ("pip-pen" if "pending" in reason.lower() else "pip-no")
                badge  = '<span class="pill pill-ok">Auth</span>' if ok else '<span class="pill pill-deny">Deny</span>'
                t_str  = e.get("time","")[:19].replace("T"," ")
                tool   = f'<span class="code">{e.get("tool","?")}</span>'
                user   = f'<strong style="color:var(--txt)">{e.get("user_id","?")}</strong>'
                html  += f"""
                <div class="feed-row">
                  <div class="feed-pip {pip}"></div>
                  <div style="flex:1;min-width:0;">
                    <div class="feed-main">{badge}&nbsp;&nbsp;{tool}&nbsp;&nbsp;·&nbsp;&nbsp;{user}</div>
                    <div class="feed-ts">{t_str} UTC &nbsp;·&nbsp; {reason}</div>
                  </div>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        with t1: _feed(recent)
        with t2: _feed([e for e in recent if e.get("allowed")])
        with t3: _feed([e for e in recent if not e.get("allowed")])


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "analytics":
    _hdr("Security Intelligence", "Analytics",
         "Aggregated statistics from the audit log.")

    all_entries = _all_audit_entries()
    if not all_entries:
        st.markdown('<div class="alert-info">No data yet. Submit a balance check or transfer request.</div>',
                    unsafe_allow_html=True)
    else:
        allowed_c = sum(1 for e in all_entries if e.get("allowed"))
        denied_c  = len(all_entries) - allowed_c
        pct_a = allowed_c / len(all_entries) * 100
        pct_d = denied_c  / len(all_entries) * 100

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="sec-head">Request Outcomes</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="panel" style="text-align:center;padding:1.8rem 1.25rem;">
              <div style="font-size:3rem;font-weight:900;color:#e6edf3;line-height:1;">{pct_a:.1f}<span style="font-size:1.2rem;color:#484f58;">%</span></div>
              <div style="font-size:0.65rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin:0.35rem 0 1rem;">Pass Rate</div>
              <div style="display:flex;height:8px;border-radius:99px;overflow:hidden;gap:2px;">
                <div style="flex:{pct_a};background:#3fb950;border-radius:99px 0 0 99px;"></div>
                <div style="flex:{pct_d};background:#f85149;border-radius:0 99px 99px 0;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:0.5rem;font-size:0.67rem;color:#484f58;">
                <span style="color:#3fb950;">✓ {allowed_c} authorized</span>
                <span style="color:#f85149;">✗ {denied_c} blocked</span>
              </div>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="sec-head">Requests by Tool</div>', unsafe_allow_html=True)
            tool_c = collections.Counter(e.get("tool","?") for e in all_entries)
            max_tc = max(tool_c.values(), default=1)
            palette = ["#388bfd","#3fb950","#bc8cff","#d29922","#f85149","#39d0c0"]
            bars = '<div class="panel">'
            for i,(tool,cnt) in enumerate(sorted(tool_c.items(),key=lambda x:-x[1])[:8]):
                pct = cnt/max_tc*100
                col = palette[i%len(palette)]
                bars += f"""
                <div style="margin-bottom:0.55rem;">
                  <div style="display:flex;justify-content:space-between;margin-bottom:0.15rem;">
                    <span class="code" style="font-size:0.7rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:70%;">{tool[:28]}</span>
                    <span style="font-size:0.7rem;color:var(--txt);font-weight:600;">{cnt}</span>
                  </div>
                  <div class="bar-wrap"><div class="bar-fill" style="width:{pct:.0f}%;background:{col};"></div></div>
                </div>"""
            bars += "</div>"
            st.markdown(bars, unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown('<div class="sec-head">Top Denial Reasons</div>', unsafe_allow_html=True)
            denied_e = [e for e in all_entries if not e.get("allowed")]
            rc = collections.Counter(e.get("reason","?") for e in denied_e)
            max_rc = max(rc.values(), default=1)
            r_html = '<div class="panel">'
            for reason,cnt in sorted(rc.items(),key=lambda x:-x[1])[:7]:
                pct = cnt/max_rc*100
                r_html += f"""
                <div style="margin-bottom:0.55rem;">
                  <div style="display:flex;justify-content:space-between;margin-bottom:0.15rem;">
                    <span style="font-size:0.7rem;color:var(--txt2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:72%;">{reason}</span>
                    <span style="font-size:0.7rem;color:#f85149;font-weight:600;">{cnt}</span>
                  </div>
                  <div class="bar-wrap"><div class="bar-fill" style="width:{pct:.0f}%;background:#f85149;"></div></div>
                </div>"""
            if not denied_e:
                r_html += '<div style="color:#484f58;font-size:0.78rem;">No denials yet.</div>'
            r_html += "</div>"
            st.markdown(r_html, unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="sec-head">Activity by User</div>', unsafe_allow_html=True)
            ustats: dict[str,dict] = {}
            for e in all_entries:
                uid = e.get("user_id","unknown")
                s   = ustats.setdefault(uid,{"ok":0,"no":0})
                if e.get("allowed"): s["ok"] += 1
                else:                s["no"] += 1
            u_html = '<div class="panel">'
            for uid,st_ in sorted(ustats.items(),key=lambda x:-(x[1]["ok"]+x[1]["no"]))[:8]:
                tot  = st_["ok"]+st_["no"]
                pa   = st_["ok"]/tot*100 if tot else 0
                u_html += f"""
                <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem;padding-bottom:0.6rem;border-bottom:1px solid var(--border);">
                  <div style="width:26px;height:26px;border-radius:50%;background:rgba(56,139,253,0.1);border:1px solid rgba(56,139,253,0.25);display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;color:#388bfd;flex-shrink:0;">{uid[0].upper()}</div>
                  <div style="flex:1;min-width:0;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.22rem;">
                      <span style="font-size:0.75rem;font-weight:600;color:var(--txt);">{uid}</span>
                      <span style="font-size:0.65rem;color:#484f58;">{tot} req</span>
                    </div>
                    <div style="display:flex;gap:2px;height:4px;border-radius:99px;overflow:hidden;">
                      <div style="flex:{pa};background:#3fb950;min-width:2px;"></div>
                      <div style="flex:{100-pa};background:#f85149;min-width:2px;"></div>
                    </div>
                  </div>
                </div>"""
            u_html += "</div>"
            st.markdown(u_html, unsafe_allow_html=True)

        st.markdown('<div class="sec-head" style="margin-top:0.5rem;">Security Alert Counters</div>', unsafe_allow_html=True)
        t_viol  = [e for e in all_entries if e.get("reason") == "Tool not allowed"]
        unauth  = [e for e in all_entries if "not authorized" in e.get("reason","")]
        inv_uid = [e for e in all_entries if "Invalid user_id" in e.get("reason","")]

        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown(f'<div class="panel" style="border-top:2px solid var(--red);"><div style="font-size:0.63rem;font-weight:700;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Tool Allowlist Violations</div><div style="font-size:1.8rem;font-weight:900;color:#f85149;">{len(t_viol)}</div><div style="font-size:0.67rem;color:#484f58;">Unlisted tool names</div></div>', unsafe_allow_html=True)
        with a2:
            st.markdown(f'<div class="panel" style="border-top:2px solid var(--red);"><div style="font-size:0.63rem;font-weight:700;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Unauthorized Account Access</div><div style="font-size:1.8rem;font-weight:900;color:#f85149;">{len(unauth)}</div><div style="font-size:0.67rem;color:#484f58;">Cross-user attempts</div></div>', unsafe_allow_html=True)
        with a3:
            st.markdown(f'<div class="panel" style="border-top:2px solid var(--amber);"><div style="font-size:0.63rem;font-weight:700;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Invalid User ID Attempts</div><div style="font-size:1.8rem;font-weight:900;color:#d29922;">{len(inv_uid)}</div><div style="font-size:0.67rem;color:#484f58;">Unknown / empty IDs</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — ASSETS  (Tool Inventory)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "tools":
    _hdr("MCP Policy Engine", "Tool Inventory",
         f"{len(TOOL_INVENTORY)} tools registered. All other names denied unconditionally.")

    for tool_name, spec in TOOL_INVENTORY.items():
        risk     = spec.get("risk_level","unknown")
        args_html= "".join(f'<span class="arg-chip">{a}</span>' for a in sorted(spec.get("required_args",[])))
        callers  = spec.get("permitted_callers",{})
        cal_rows = ""
        for uid,accts in callers.items():
            for acct in sorted(accts):
                cal_rows += (f'<div style="display:flex;gap:0.5rem;padding:0.28rem 0;border-bottom:1px solid rgba(48,54,61,0.5);">'
                             f'<span style="font-size:0.7rem;color:#484f58;width:4.5rem;">{uid}</span>'
                             f'<span class="code">{acct}</span></div>')
        st.markdown(f"""
        <div class="tool-card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.7rem;">
            <span class="code" style="font-size:0.95rem;font-weight:700;">{tool_name}()</span>
            <span class="risk risk-{risk}">{risk} risk</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
            <div>
              <div style="font-size:0.58rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Required Arguments</div>
              <div>{args_html or '<span style="color:#484f58;font-size:0.7rem;">none</span>'}</div>
              {'<div style="margin-top:0.45rem;font-size:0.67rem;color:#484f58;">Source: <span class="code">'+spec["account_arg"]+"</span></div>" if "account_arg" in spec else ""}
              {'<div style="font-size:0.67rem;color:#484f58;">Destination: <span class="code">'+spec["destination_arg"]+"</span></div>" if "destination_arg" in spec else ""}
            </div>
            <div>
              <div style="font-size:0.58rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Permitted Callers</div>
              {cal_rows or '<span style="color:#484f58;font-size:0.7rem;">None defined.</span>'}
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sec-head">Security Policies — Detail</div>', unsafe_allow_html=True)
    policies = [
        ("Tool Allowlist",        "Only get_balance and transfer are registered. Any other name is denied immediately.",                   "#388bfd"),
        ("Exact Argument Schema", "Requests must supply exactly the required keys. Extra or missing keys → denial.",                        "#3fb950"),
        ("User-Account Auth",     "riya cannot access ACC-2001 and vice-versa. Enforced per-user, per-tool.",                              "#bc8cff"),
        ("Amount Validation",     "Numeric (bool excluded), finite (no NaN/Inf), positive, and ≤ ₹10,000.",                               "#d29922"),
        ("Approval Workflow",     "All transfers that pass checks are queued — no money moves until admin calls approve_transfer.",         "#39d0c0"),
        ("Immutable Audit Trail", "Every request appended to audit.jsonl. Logging failures are silenced.",                                 "#3fb950"),
    ]
    for name, desc, col in policies:
        st.markdown(f"""
        <div style="display:flex;gap:0.75rem;padding:0.7rem 0;border-bottom:1px solid var(--border);">
          <div style="width:2px;background:{col};border-radius:99px;flex-shrink:0;"></div>
          <div>
            <div style="font-size:0.8rem;font-weight:700;color:var(--txt);margin-bottom:0.15rem;">{name}</div>
            <div style="font-size:0.72rem;color:#484f58;">{desc}</div>
          </div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — BALANCE LOOKUP
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "balance":
    _hdr("Guarded Access", "Balance Lookup",
         "Requests processed by the MCP Guard policy engine. Authorization enforced by guard.py.")

    tool_spec   = TOOL_INVENTORY.get("get_balance",{})
    valid_pairs = tool_spec.get("permitted_callers",{})
    all_users   = sorted(valid_pairs.keys())
    all_accounts= sorted(ACCOUNTS.keys())

    left, right = st.columns([2, 3])
    with left:
        st.markdown('<div class="sec-head">Submit Request</div>', unsafe_allow_html=True)
        with st.form("balance_form"):
            user_id    = st.selectbox("User ID",    options=all_users)
            account_id = st.selectbox("Account ID", options=all_accounts)
            submitted  = st.form_submit_button("Check Balance", use_container_width=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Unauthorized Demo</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-warn" style="font-size:0.72rem;">Demonstrates a real guard denial: riya → ACC-2001.</div>', unsafe_allow_html=True)
        if st.button("Simulate: riya → ACC-2001", use_container_width=True):
            bad = {"user_id":"riya","tool":"get_balance","arguments":{"account_id":"ACC-2001"}}
            r   = handle_request(bad)
            st.markdown(f'<div class="alert-danger">✗ DENIED — {r.get("reason","Unknown")}</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sec-head">Guard Response</div>', unsafe_allow_html=True)
        if submitted:
            req    = {"user_id":user_id,"tool":"get_balance","arguments":{"account_id":account_id}}
            result = handle_request(req)
            if result.get("allowed"):
                data = result.get("result",{})
                st.markdown(f"""
                <div class="panel" style="border-left:3px solid var(--green);">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.85rem;">
                    <div style="width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green);"></div>
                    <span style="font-size:0.63rem;font-weight:700;color:var(--green);letter-spacing:0.1em;text-transform:uppercase;">Authorized · Policy Checks Passed</span>
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.6rem;">
                    <div style="background:rgba(63,185,80,0.06);border:1px solid rgba(63,185,80,0.18);border-radius:7px;padding:0.7rem;text-align:center;">
                      <div style="font-size:0.58rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;">Account</div>
                      <div class="code" style="margin-top:0.25rem;">{data.get("account_id","—")}</div>
                    </div>
                    <div style="background:rgba(63,185,80,0.06);border:1px solid rgba(63,185,80,0.18);border-radius:7px;padding:0.7rem;text-align:center;">
                      <div style="font-size:0.58rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;">Balance</div>
                      <div style="font-size:0.95rem;color:var(--green);font-weight:800;margin-top:0.25rem;">{_fmt_inr(data.get("balance",0))}</div>
                    </div>
                    <div style="background:rgba(63,185,80,0.06);border:1px solid rgba(63,185,80,0.18);border-radius:7px;padding:0.7rem;text-align:center;">
                      <div style="font-size:0.58rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;">Currency</div>
                      <div style="font-size:0.82rem;color:var(--purple);font-weight:600;margin-top:0.25rem;">{data.get("currency","—")}</div>
                    </div>
                  </div>
                  <div style="margin-top:0.65rem;font-size:0.63rem;color:#484f58;">User <strong style="color:var(--txt2);">{user_id}</strong> · Audit entry written</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="panel" style="border-left:3px solid var(--red);">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
                    <div style="width:7px;height:7px;border-radius:50%;background:var(--red);"></div>
                    <span style="font-size:0.63rem;font-weight:700;color:var(--red);letter-spacing:0.1em;text-transform:uppercase;">Denied by Guard</span>
                  </div>
                  <div style="font-size:0.88rem;color:#ff7b72;font-weight:600;">{result.get("reason","Unknown")}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="panel" style="text-align:center;padding:2.5rem;border-style:dashed;">
              <div style="font-size:0.8rem;color:#484f58;">Guard response appears here after submission.</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Authorization Matrix</div>', unsafe_allow_html=True)
        m = '<div class="panel"><table class="tbl" style="margin:0;"><thead><tr><th>User</th>'
        for acct in sorted(ACCOUNTS.keys()):
            m += f'<th style="text-align:center;">{acct}</th>'
        m += "</tr></thead><tbody>"
        for uid, accts in sorted(valid_pairs.items()):
            m += f'<tr><td style="color:var(--txt);font-weight:600;">{uid}</td>'
            for acct in sorted(ACCOUNTS.keys()):
                m += f'<td style="text-align:center;">{"<span style=\'color:var(--green)\'>✓</span>" if acct in accts else "<span style=\'color:#30363d\'>✗</span>"}</td>'
            m += "</tr>"
        m += "</tbody></table></div>"
        st.markdown(m, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 6 — TRANSFER REQUEST
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "transfer":
    _hdr("High-Risk Operation", "Transfer Request",
         "All transfers queued for admin approval — no funds move until approved.")

    st.markdown('<div class="alert-warn">All transfers passing policy checks are <strong>queued, not executed</strong>. No money moves until admin approves.</div>',
                unsafe_allow_html=True)

    tool_spec    = TOOL_INVENTORY.get("transfer",{})
    valid_callers= tool_spec.get("permitted_callers",{})
    all_users    = sorted(valid_callers.keys())
    all_accounts = sorted(ACCOUNTS.keys())

    left, right = st.columns([5, 3])
    with left:
        st.markdown('<div class="sec-head">Transfer Details</div>', unsafe_allow_html=True)
        with st.form("transfer_form"):
            c1,c2,c3 = st.columns(3)
            t_user   = c1.selectbox("Requester",    options=all_users)
            t_from   = c2.selectbox("From Account", options=all_accounts)
            t_to     = c3.selectbox("To Account",   options=all_accounts)
            t_amount = st.number_input("Amount (INR)", min_value=0.01, max_value=10000.0, value=500.0, step=100.0)
            submitted= st.form_submit_button("Submit Transfer Request", use_container_width=True)

        if submitted:
            issues = []
            ua = valid_callers.get(t_user,set())
            if t_from == t_to:   issues.append("Source and destination are the same account.")
            if t_from not in ua: issues.append(f"`{t_user}` is not authorized for `{t_from}`.")
            if t_to   not in ua: issues.append(f"`{t_user}` is not authorized for `{t_to}`.")
            for iss in issues:
                st.markdown(f'<div class="alert-warn" style="margin-bottom:0.3rem;font-size:0.73rem;">Advisory: {iss}</div>', unsafe_allow_html=True)
            req    = {"user_id":t_user,"tool":"transfer",
                      "arguments":{"from_account":t_from,"to_account":t_to,"amount":float(t_amount)}}
            result = handle_request(req)
            if result.get("allowed") and result.get("status") == "pending_approval":
                ap_id = result.get("approval_id","—")
                st.markdown(f"""
                <div class="panel" style="border-left:3px solid var(--amber);margin-top:0.75rem;">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
                    <div style="width:7px;height:7px;border-radius:50%;background:var(--amber);"></div>
                    <span style="font-size:0.63rem;font-weight:700;color:var(--amber);letter-spacing:0.1em;text-transform:uppercase;">Queued for Approval — No Funds Moved</span>
                  </div>
                  <div class="code" style="font-size:0.67rem;color:#484f58;word-break:break-all;margin-bottom:0.45rem;">ID: {ap_id}</div>
                  <div style="font-size:0.73rem;color:#484f58;">Go to <strong style="color:var(--txt2);">Approval Center</strong> to approve or reject.</div>
                </div>""", unsafe_allow_html=True)
            elif result.get("allowed"):
                st.markdown(f'<div class="alert-ok">Allowed — {result}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="panel" style="border-left:3px solid var(--red);margin-top:0.75rem;">
                  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.45rem;">
                    <div style="width:7px;height:7px;border-radius:50%;background:var(--red);"></div>
                    <span style="font-size:0.63rem;font-weight:700;color:var(--red);letter-spacing:0.1em;text-transform:uppercase;">Denied by Guard</span>
                  </div>
                  <div style="font-size:0.85rem;color:#ff7b72;font-weight:600;">{result.get("reason","Unknown")}</div>
                </div>""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sec-head">Risk Profile</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="panel" style="border-left:3px solid var(--red);">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.85rem;">
            <span class="risk risk-high">HIGH RISK</span>
            <span style="font-size:0.67rem;color:#484f58;">transfer tool</span>
          </div>
          <div style="border-left:1px solid rgba(48,54,61,0.9);padding-left:0.85rem;margin-left:0.15rem;">
            <div style="margin-bottom:0.5rem;font-size:0.7rem;color:#484f58;">① Validate user ID</div>
            <div style="margin-bottom:0.5rem;font-size:0.7rem;color:#484f58;">② Tool allowlist check</div>
            <div style="margin-bottom:0.5rem;font-size:0.7rem;color:#484f58;">③ Exact argument schema</div>
            <div style="margin-bottom:0.5rem;font-size:0.7rem;color:#484f58;">④ Amount validation (numeric, finite, &gt;0, ≤₹10k)</div>
            <div style="margin-bottom:0.5rem;font-size:0.7rem;color:#484f58;">⑤ Authorize source account</div>
            <div style="margin-bottom:0.5rem;font-size:0.7rem;color:#484f58;">⑥ Authorize destination account</div>
            <div style="font-size:0.7rem;color:var(--amber);font-weight:600;">⑦ Queue — no execution yet</div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div class="sec-head" style="margin-top:0.4rem;">Current Balances</div>', unsafe_allow_html=True)
        bh = '<div class="panel">'
        for aid,det in ACCOUNTS.items():
            bh += (f'<div style="display:flex;justify-content:space-between;padding:0.38rem 0;border-bottom:1px solid var(--border);">'
                   f'<span class="code">{aid}</span>'
                   f'<span style="font-size:0.75rem;font-weight:600;color:var(--txt);">{_fmt_inr(det["balance"])}</span></div>')
        bh += "</div>"
        st.markdown(bh, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 7 — APPROVAL CENTER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "approvals":
    _hdr("Admin Only", "Approval Center",
         "Pending transfer requests. Only `admin` is a valid approver in this prototype.")

    st.markdown('<div class="alert-info">Security note: approver identity is declared by the form, not cryptographically verified. Only <code style="background:rgba(56,139,253,0.1);padding:0.05rem 0.3rem;border-radius:3px;color:#79c0ff;">admin</code> is accepted.</div>',
                unsafe_allow_html=True)

    r_col, a_col = st.columns([1, 3])
    with r_col:
        if st.button("↺  Refresh", use_container_width=True): st.rerun()
    with a_col:
        approver_id = st.text_input("Approver ID", value="admin")

    if approver_id and approver_id != "admin":
        st.markdown(f'<div class="alert-danger"><strong>{approver_id}</strong> is not a registered approver.</div>', unsafe_allow_html=True)

    pending = dict(PENDING_APPROVALS)
    if not pending:
        st.markdown("""
        <div class="panel" style="text-align:center;padding:2.5rem;border-style:dashed;">
          <div style="font-size:0.85rem;font-weight:600;color:var(--green);margin-bottom:0.3rem;">Queue Empty</div>
          <div style="font-size:0.73rem;color:#484f58;">No pending transfers. Submit a transfer request to populate the queue.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-warn">{len(pending)} transfer(s) awaiting review. No funds will move until approved.</div>', unsafe_allow_html=True)

        for ap_id, pend in list(pending.items()):
            if ap_id not in PENDING_APPROVALS: continue
            args      = pend.get("arguments",{})
            requester = pend.get("user_id","—")
            short_id  = ap_id[:22] + "…"
            a_key, r_key = f"approved_{ap_id}", f"rejected_{ap_id}"

            if st.session_state.get(a_key) or st.session_state.get(r_key):
                st.markdown(f'<div class="alert-info" style="font-size:0.73rem;">Action already taken for <code>{short_id}</code>.</div>', unsafe_allow_html=True)
                continue

            st.markdown(f"""
            <div class="appr-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.85rem;">
                <span class="pill pill-pend">PENDING APPROVAL</span>
                <span style="font-size:0.67rem;color:#484f58;">Requester: <strong style="color:var(--txt2);">{requester}</strong></span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;margin-bottom:0.7rem;">
                <div style="background:rgba(210,153,34,0.06);border:1px solid rgba(210,153,34,0.15);border-radius:6px;padding:0.6rem;text-align:center;">
                  <div style="font-size:0.57rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;">From</div>
                  <div class="code" style="margin-top:0.2rem;">{args.get("from_account","—")}</div>
                </div>
                <div style="background:rgba(210,153,34,0.06);border:1px solid rgba(210,153,34,0.15);border-radius:6px;padding:0.6rem;text-align:center;">
                  <div style="font-size:0.57rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;">To</div>
                  <div class="code" style="margin-top:0.2rem;">{args.get("to_account","—")}</div>
                </div>
                <div style="background:rgba(210,153,34,0.06);border:1px solid rgba(210,153,34,0.15);border-radius:6px;padding:0.6rem;text-align:center;">
                  <div style="font-size:0.57rem;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;">Amount</div>
                  <div style="font-size:0.85rem;color:var(--amber);font-weight:700;margin-top:0.2rem;">{_fmt_inr(args.get("amount",0))}</div>
                </div>
              </div>
              <div class="code" style="font-size:0.58rem;color:#30363d;">{short_id}</div>
            </div>""", unsafe_allow_html=True)

            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Approve", key=f"btn_a_{ap_id}", use_container_width=True):
                res = approve_transfer(approver_id, ap_id)
                if res.get("allowed"):
                    st.markdown(f'<div class="alert-ok">Transfer approved and executed. {res.get("result",{})}</div>', unsafe_allow_html=True)
                    st.session_state[a_key] = True; st.rerun()
                else:
                    st.markdown(f'<div class="alert-danger">Failed: {res.get("reason","Unknown")}</div>', unsafe_allow_html=True)
            if b2.button("Reject", key=f"btn_r_{ap_id}", use_container_width=True):
                res = reject_transfer(approver_id, ap_id)
                if res.get("allowed"):
                    st.markdown('<div class="alert-warn">Transfer rejected.</div>', unsafe_allow_html=True)
                    st.session_state[r_key] = True; st.rerun()
                else:
                    st.markdown(f'<div class="alert-danger">Failed: {res.get("reason","Unknown")}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 8 — AUDIT LOG
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "audit":
    _hdr("Immutable Security Record", "Audit Log",
         "Every guard decision is appended here. Session = in-memory; Persistent = audit.jsonl.")

    if st.button("↺  Refresh"):
        st.rerun()

    tab_s, tab_p = st.tabs(["Session Log (in-memory)", "Persistent Log (audit.jsonl)"])

    def _audit_table(entries: list[dict], empty_msg: str, pfx: str) -> None:
        if not entries:
            st.markdown(f'<div class="alert-info">{empty_msg}</div>', unsafe_allow_html=True)
            return
        ok_c  = sum(1 for e in entries if e.get("allowed"))
        den_c = len(entries) - ok_c
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", len(entries)); m2.metric("Authorized", ok_c); m3.metric("Blocked", den_c)
        st.markdown("<br/>", unsafe_allow_html=True)

        fc1,fc2,fc3,fc4 = st.columns(4)
        dec_f  = fc1.selectbox("Decision", ["All","Allowed","Denied"],    key=f"{pfx}_dec")
        usr_f  = fc2.selectbox("User",  ["All"]+sorted({e.get("user_id","?") for e in entries}), key=f"{pfx}_usr")
        tool_f = fc3.selectbox("Tool",  ["All"]+sorted({e.get("tool","?") for e in entries}),    key=f"{pfx}_tool")
        search = fc4.text_input("Search reason", key=f"{pfx}_srch", placeholder="e.g. unauthorized")

        f = entries
        if dec_f == "Allowed":  f = [e for e in f if e.get("allowed")]
        elif dec_f == "Denied": f = [e for e in f if not e.get("allowed")]
        if usr_f  != "All": f = [e for e in f if e.get("user_id") == usr_f]
        if tool_f != "All": f = [e for e in f if e.get("tool") == tool_f]
        if search:          f = [e for e in f if search.lower() in e.get("reason","").lower()]

        if not f:
            st.markdown('<div class="alert-info">No entries match the current filters.</div>', unsafe_allow_html=True)
            return
        rows = [{"Time (UTC)": e.get("time","")[:19].replace("T"," "),
                 "User":      e.get("user_id","—"),
                 "Tool":      e.get("tool","—"),
                 "Decision":  "✓ Allowed" if e.get("allowed") else "✗ Denied",
                 "Reason":    e.get("reason","—")} for e in reversed(f)]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(f)} of {len(entries)} entries (newest first)")

    with tab_s:
        _audit_table(list(AUDIT_LOG), "No session entries yet. Submit a balance check or transfer.", "sess")
    with tab_p:
        pers = _load_audit_log()
        log_path = os.environ.get("MCP_GUARD_AUDIT_LOG","audit.jsonl")
        st.caption(f"Reading from: `{log_path}`")
        _audit_table(pers, f"No log at `{log_path}` or file is empty.", "pers")

    st.markdown("<br/>")
    st.markdown('<div class="sec-head">Security Alert Counters</div>', unsafe_allow_html=True)
    all_a   = _all_audit_entries()
    t_viol  = [e for e in all_a if e.get("reason") == "Tool not allowed"]
    unauth  = [e for e in all_a if "not authorized" in e.get("reason","")]
    inv_uid = [e for e in all_a if "Invalid user_id" in e.get("reason","")]

    a1,a2,a3 = st.columns(3)
    with a1:
        st.markdown(f'<div class="panel" style="border-top:2px solid var(--red);"><div style="font-size:0.6rem;font-weight:700;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Tool Allowlist Violations</div><div style="font-size:1.8rem;font-weight:900;color:#f85149;">{len(t_viol)}</div></div>', unsafe_allow_html=True)
    with a2:
        st.markdown(f'<div class="panel" style="border-top:2px solid var(--red);"><div style="font-size:0.6rem;font-weight:700;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Unauthorized Account Access</div><div style="font-size:1.8rem;font-weight:900;color:#f85149;">{len(unauth)}</div></div>', unsafe_allow_html=True)
    with a3:
        st.markdown(f'<div class="panel" style="border-top:2px solid var(--amber);"><div style="font-size:0.6rem;font-weight:700;color:#484f58;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">Invalid User ID Attempts</div><div style="font-size:1.8rem;font-weight:900;color:#d29922;">{len(inv_uid)}</div></div>', unsafe_allow_html=True)

    if t_viol:
        with st.expander(f"Tool Allowlist Violations ({len(t_viol)}) — last 20"):
            st.dataframe([{"Time":e["time"][:19].replace("T"," "),"User":e["user_id"],"Tool":e["tool"]} for e in t_viol[-20:]], use_container_width=True, hide_index=True)
    if unauth:
        with st.expander(f"Unauthorized Attempts ({len(unauth)}) — last 20"):
            st.dataframe([{"Time":e["time"][:19].replace("T"," "),"User":e["user_id"],"Tool":e["tool"],"Reason":e["reason"]} for e in unauth[-20:]], use_container_width=True, hide_index=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:1.1rem 0 0.3rem;border-top:1px solid rgba(48,54,61,0.9);margin-top:2rem;">
  <div style="font-size:0.6rem;color:#30363d;letter-spacing:0.06em;">
    MCP Guard Security Dashboard &nbsp;·&nbsp; Simulated Demo — Fictional Data Only &nbsp;·&nbsp; Not Production Banking Software
  </div>
</div>
""", unsafe_allow_html=True)
