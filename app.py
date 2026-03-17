import streamlit as st
from pathlib import Path
import requests
import time
import difflib

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Firmware Failure Triage Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark, modern, glassmorphism
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---------- Import fonts ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ---------- Root variables ---------- */
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.7);
    --bg-card-hover: rgba(17, 24, 39, 0.9);
    --border-color: rgba(99, 102, 241, 0.2);
    --border-glow: rgba(99, 102, 241, 0.4);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-indigo: #6366f1;
    --accent-cyan: #22d3ee;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --accent-violet: #8b5cf6;
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    --gradient-accent: linear-gradient(135deg, #22d3ee 0%, #6366f1 100%);
    --glass-bg: rgba(15, 23, 42, 0.6);
    --glass-border: rgba(99, 102, 241, 0.15);
}

/* ---------- Global ---------- */
.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main .block-container {
    padding-top: 1.5rem !important;
    max-width: 100% !important;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(99,102,241,0.3);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.5); }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1729 0%, #111827 100%) !important;
    border-right: 1px solid var(--glass-border) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] .stMarkdown label {
    color: var(--text-secondary) !important;
}

/* Sidebar file buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    padding: 0.4rem 0.75rem !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    margin-bottom: 2px !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99, 102, 241, 0.1) !important;
    color: var(--accent-cyan) !important;
    border-color: var(--glass-border) !important;
    transform: translateX(4px);
}

/* ---------- Headers ---------- */
.hero-header {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    margin-bottom: 1rem;
}

.hero-header h1 {
    font-family: 'Inter', sans-serif !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #6366f1, #a78bfa, #22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    margin-bottom: 0.3rem;
    animation: gradient-shift 4s ease infinite;
    background-size: 200% 200%;
}

@keyframes gradient-shift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.hero-subtitle {
    color: var(--text-muted);
    font-size: 0.95rem;
    font-weight: 400;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ---------- Glass cards ---------- */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.08);
}

.glass-card-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.1);
}

.glass-card-header h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-primary);
    margin: 0;
}

.glass-card-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
}

/* ---------- Status badge ---------- */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
}

.status-ready {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-running {
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}

.status-ready .status-dot { background: #10b981; }
.status-running .status-dot {
    background: #818cf8;
    animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

/* ---------- Primary action button ---------- */
.stButton > button[kind="primary"],
div[data-testid="stForm"] .stButton > button {
    background: var(--gradient-primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    letter-spacing: -0.01em;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.45) !important;
}

/* ---------- Radio buttons ---------- */
.stRadio > div {
    gap: 0.5rem !important;
}

.stRadio label {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}

.stRadio label:hover {
    border-color: var(--accent-indigo) !important;
    background: rgba(99, 102, 241, 0.08) !important;
}

.stRadio label[data-checked="true"],
.stRadio div[role="radiogroup"] label[aria-checked="true"] {
    border-color: var(--accent-indigo) !important;
    background: rgba(99, 102, 241, 0.12) !important;
    color: var(--text-primary) !important;
}

/* ---------- Text inputs ---------- */
.stTextInput input, .stTextArea textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent-indigo) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* ---------- Chat messages ---------- */
.stChatMessage {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
}

/* ---------- Code blocks ---------- */
.stCode, pre, code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}

pre {
    background: #0d1117 !important;
    border: 1px solid rgba(99, 102, 241, 0.15) !important;
    border-radius: 10px !important;
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {
    background: transparent !important;
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important;
}

.streamlit-expanderContent {
    background: rgba(15, 23, 42, 0.4) !important;
    border: 1px solid var(--glass-border) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ---------- Dividers ---------- */
hr {
    border-color: var(--glass-border) !important;
    margin: 1rem 0 !important;
}

/* ---------- File uploader ---------- */
.stFileUploader {
    background: var(--bg-secondary) !important;
    border: 1px dashed var(--glass-border) !important;
    border-radius: 12px !important;
}

.stFileUploader:hover {
    border-color: var(--accent-indigo) !important;
}

/* ---------- Spinner ---------- */
.stSpinner > div {
    color: var(--accent-indigo) !important;
}

/* ---------- Metrics / Stats row ---------- */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.metric-card {
    flex: 1;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: var(--border-glow);
    transform: translateY(-2px);
}

.metric-value {
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    background: var(--gradient-accent);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
}

/* ---------- Agent tool call log (terminal style) ---------- */
.tool-call-log {
    background: #0d1117;
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 10px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
}

.tool-call-entry {
    padding: 0.35rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}

.tool-call-entry:last-child { border-bottom: none; }

.tool-name {
    color: #22d3ee;
    font-weight: 600;
}

.tool-args {
    color: #f59e0b;
}

.tool-result-preview {
    color: #64748b;
    font-size: 0.75rem;
    margin-top: 0.15rem;
    white-space: pre-wrap;
    overflow: hidden;
    max-height: 80px;
}

/* ---------- Progress steps ---------- */
.step-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
}

.step-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    flex-shrink: 0;
}

.step-active .step-icon {
    background: rgba(99, 102, 241, 0.2);
    border: 2px solid var(--accent-indigo);
    color: var(--accent-indigo);
    animation: pulse-dot 1.5s ease-in-out infinite;
}

.step-done .step-icon {
    background: rgba(16, 185, 129, 0.2);
    border: 2px solid var(--accent-emerald);
    color: var(--accent-emerald);
}

.step-pending .step-icon {
    background: rgba(100, 116, 139, 0.1);
    border: 2px solid rgba(100, 116, 139, 0.3);
    color: var(--text-muted);
}

.step-label { color: var(--text-secondary); }
.step-active .step-label { color: var(--text-primary); font-weight: 500; }
.step-done .step-label { color: var(--accent-emerald); }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px !important;
    background: var(--bg-secondary) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid var(--glass-border) !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1rem !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.15) !important;
    color: var(--text-primary) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: transparent !important;
}

.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ---------- Markdown inside cards ---------- */
.stMarkdown h2 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
}

.stMarkdown h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

.stMarkdown p, .stMarkdown li {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1.7;
}

/* ---------- Chat input ---------- */
.stChatInput {
    border-color: var(--glass-border) !important;
}

.stChatInput textarea {
    background: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ---------- Subheader override ---------- */
.viewer-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}

.viewer-header h3 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--accent-cyan);
    margin: 0;
}

.viewer-header .file-badge {
    background: rgba(34, 211, 238, 0.1);
    border: 1px solid rgba(34, 211, 238, 0.2);
    color: var(--accent-cyan);
    padding: 0.15rem 0.6rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
}

/* ---------- Sidebar section header ---------- */
.sidebar-section {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    padding: 0.75rem 0 0.4rem 0;
}

/* ---------- Key file highlight ---------- */
.key-file-indicator {
    display: inline-block;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--accent-amber);
    margin-right: 0.35rem;
    box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
}

/* ---------- Animate in ---------- */
@keyframes fade-in-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in { animation: fade-in-up 0.4s ease-out; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "investigation_started" not in st.session_state:
    st.session_state.investigation_started = False
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "fix_applied" not in st.session_state:
    st.session_state.fix_applied = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEMO_ROOT = Path("demo_repo")
TICKET_PATH = DEMO_ROOT / "tickets" / "ticket_001.md"
LOG_PATH = DEMO_ROOT / "logs" / "fault_log.txt"
KEY_FILES = {"bms_interface.c", "safety_checker.c", "torque_controller.c"}

# ---------------------------------------------------------------------------
# Original file contents (for revert)
# ---------------------------------------------------------------------------
ORIGINAL_SAFETY_CHECKER_H = (DEMO_ROOT / "safety_checker.h").read_text(encoding="utf-8")
ORIGINAL_SAFETY_CHECKER_C = (DEMO_ROOT / "safety_checker.c").read_text(encoding="utf-8")
ORIGINAL_BMS_INTERFACE_C = (DEMO_ROOT / "bms_interface.c").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Patched file contents
# ---------------------------------------------------------------------------
PATCHED_SAFETY_CHECKER_H = """\
#ifndef SAFETY_CHECKER_H
#define SAFETY_CHECKER_H

#include <stdbool.h>

void safety_set_bms_timeout_fault(void);
void safety_clear_bms_timeout_fault(void);
bool safety_is_torque_inhibited(void);
void safety_tick(void);

#endif
"""

PATCHED_SAFETY_CHECKER_C = """\
// safety_checker.c
// Manages safety-critical fault latches for the motor controller.
// Owner: firmware safety team
// Last reviewed: 2024-01-15

#include "safety_checker.h"
#include <stdio.h>

static bool torque_inhibit = false;
static int fault_count = 0;

void safety_set_bms_timeout_fault(void) {
    torque_inhibit = true;
    fault_count++;
    printf("[SAFETY] torque_inhibit=1 reason=BMS_TIMEOUT\\n");
}

void safety_clear_bms_timeout_fault(void) {
    torque_inhibit = false;
    printf("[SAFETY] torque_inhibit=0 reason=BMS_RESTORED\\n");
}

bool safety_is_torque_inhibited(void) {
    return torque_inhibit;
}

void safety_tick(void) {
    // placeholder for periodic safety checks
    // overvoltage, overtemp, etc. would go here
}
"""

PATCHED_BMS_INTERFACE_C = """\
// bms_interface.c
// Tracks BMS heartbeat presence over CAN.
// When heartbeat is lost, triggers safety fault.
// When heartbeat returns, marks recovery.

#include "bms_interface.h"
#include "safety_checker.h"
#include <stdio.h>

static bool heartbeat_present = false;
static int timeout_counter = 0;

#define BMS_TIMEOUT_THRESHOLD 50  // ticks

void bms_on_heartbeat_timeout(void) {
    heartbeat_present = false;
    safety_set_bms_timeout_fault();
    printf("[BMS] heartbeat lost, safety fault raised\\n");
}

void bms_on_heartbeat_received(void) {
    heartbeat_present = true;
    timeout_counter = 0;
    safety_clear_bms_timeout_fault();
    printf("[BMS] heartbeat restored\\n");
}

bool bms_is_heartbeat_present(void) {
    return heartbeat_present;
}

void bms_tick(void) {
    if (!heartbeat_present) {
        timeout_counter++;
        if (timeout_counter >= BMS_TIMEOUT_THRESHOLD) {
            bms_on_heartbeat_timeout();
            timeout_counter = 0;  // prevent re-trigger spam
        }
    }
}
"""

PATCH_FILES = {
    "safety_checker.h": (ORIGINAL_SAFETY_CHECKER_H, PATCHED_SAFETY_CHECKER_H),
    "safety_checker.c": (ORIGINAL_SAFETY_CHECKER_C, PATCHED_SAFETY_CHECKER_C),
    "bms_interface.c": (ORIGINAL_BMS_INTERFACE_C, PATCHED_BMS_INTERFACE_C),
}


def apply_fix():
    for fname, (_, patched) in PATCH_FILES.items():
        (DEMO_ROOT / fname).write_text(patched, encoding="utf-8")
    st.session_state.fix_applied = True


def revert_fix():
    for fname, (original, _) in PATCH_FILES.items():
        (DEMO_ROOT / fname).write_text(original, encoding="utf-8")
    st.session_state.fix_applied = False


def make_diff(fname, original, patched):
    orig_lines = original.splitlines(keepends=True)
    patch_lines = patched.splitlines(keepends=True)
    diff = difflib.unified_diff(orig_lines, patch_lines, fromfile=f"a/{fname}", tofile=f"b/{fname}")
    return "".join(diff)


def get_repo_files():
    skip = {"logs", "tickets"}
    files = []
    for p in sorted(DEMO_ROOT.rglob("*")):
        if p.is_file() and not any(s in p.parts for s in skip):
            files.append(str(p.relative_to(DEMO_ROOT)))
    return files


def reset():
    st.session_state.messages = []
    st.session_state.investigation_started = False
    st.session_state.selected_file = None
    if st.session_state.fix_applied:
        revert_fix()


def fetch_github_issue(url: str):
    """Fetch a GitHub issue and return (ticket_text, error_msg)."""
    try:
        parts = url.rstrip("/").split("/")
        if "issues" not in parts:
            return None, "URL must be a GitHub issue link, e.g. https://github.com/owner/repo/issues/42"
        idx = parts.index("issues")
        owner, repo, number = parts[idx - 2], parts[idx - 1], parts[idx + 1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
        resp = requests.get(
            api_url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if resp.status_code == 404:
            return None, f"Issue not found: {owner}/{repo}#{number}. Check the URL and ensure the repo is public."
        if resp.status_code != 200:
            return None, f"GitHub API error {resp.status_code}: {resp.text[:200]}"
        issue = resp.json()
        body = issue.get("body") or "(no description)"
        ticket_text = f"# {issue['title']}\n\n**Repo:** {owner}/{repo}  \n**Issue:** #{number}  \n**State:** {issue['state']}\n\n---\n\n{body}"
        return ticket_text, None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-header fade-in">
    <h1>Firmware Failure Triage Agent</h1>
    <div class="hero-subtitle">AI-Powered Root Cause Analysis for Embedded Systems</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — repo file browser
# ---------------------------------------------------------------------------
with st.sidebar:
    # Logo / branding
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
        <div style="font-size: 2rem; margin-bottom: 0.25rem;">⚡</div>
        <div style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.1rem;
                    background: linear-gradient(135deg, #6366f1, #22d3ee);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text;">TriageBot</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Status
    if st.session_state.investigation_started:
        st.markdown("""
        <div class="status-badge status-running">
            <span class="status-dot"></span> Investigation Active
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-badge status-ready">
            <span class="status-dot"></span> Ready
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # File explorer
    st.markdown('<div class="sidebar-section">Source Files</div>', unsafe_allow_html=True)

    repo_files = get_repo_files()
    for f in repo_files:
        is_key = f in KEY_FILES
        icon = "🔑" if is_key else "📄"
        label = f"{icon}  {f}"
        if st.button(label, key=f"file_{f}", use_container_width=True):
            st.session_state.selected_file = f

    st.markdown("---")

    # Artifacts section
    st.markdown('<div class="sidebar-section">Input Artifacts</div>', unsafe_allow_html=True)
    artifact_tab = st.radio(
        "View:", ["Issue Ticket", "Fault Log"], label_visibility="collapsed"
    )

    if st.session_state.investigation_started:
        st.markdown("---")
        if st.button("↻  New Investigation", use_container_width=True):
            reset()
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0;">
        <div style="font-family: 'Inter', sans-serif; font-size: 0.65rem; color: var(--text-muted);
                    letter-spacing: 0.05em; text-transform: uppercase;">
            Powered by NVIDIA Nemotron
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main layout: left = chat, right = file viewer
# ---------------------------------------------------------------------------
chat_col, viewer_col = st.columns([3, 2], gap="large")

# ---------------------------------------------------------------------------
# Right column — file / artifact viewer
# ---------------------------------------------------------------------------
_demo_ticket = TICKET_PATH.read_text(encoding="utf-8")
_demo_log = LOG_PATH.read_text(encoding="utf-8")

with viewer_col:
    if st.session_state.selected_file:
        file_path = DEMO_ROOT / st.session_state.selected_file
        ext = file_path.suffix
        lang = "c" if ext in (".c", ".h") else "text"
        is_key = st.session_state.selected_file in KEY_FILES

        badge_html = ' <span class="file-badge">KEY FILE</span>' if is_key else ""
        st.markdown(f"""
        <div class="viewer-header">
            <h3>{st.session_state.selected_file}</h3>
            {badge_html}
        </div>
        """, unsafe_allow_html=True)

        st.code(file_path.read_text(encoding="utf-8"), language=lang, line_numbers=True)

    elif artifact_tab == "Issue Ticket":
        ticket_preview = st.session_state.get("ticket_text", _demo_ticket)
        st.markdown("""
        <div class="viewer-header">
            <h3>ticket_001.md</h3>
            <span class="file-badge">TICKET</span>
        </div>
        """, unsafe_allow_html=True)
        st.code(ticket_preview, language="markdown")

    else:
        log_preview = st.session_state.get("log_text", _demo_log)
        st.markdown("""
        <div class="viewer-header">
            <h3>fault_log.txt</h3>
            <span class="file-badge">LOG</span>
        </div>
        """, unsafe_allow_html=True)
        st.code(log_preview, language="text")

# ---------------------------------------------------------------------------
# Left column — chat / investigation panel
# ---------------------------------------------------------------------------
with chat_col:
    # Render conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="⚡" if msg["role"] == "assistant" else "👤"):
            if msg.get("tool_calls"):
                with st.expander("🔍 Agent Investigation Steps", expanded=False):
                    tool_html = '<div class="tool-call-log">'
                    for tc in msg["tool_calls"]:
                        args_str = ", ".join(
                            f"{k}={v}" for k, v in tc["args"].items()
                        ) if tc["args"] else ""
                        preview = tc.get("result_preview", "")
                        tool_html += f"""
                        <div class="tool-call-entry">
                            <span class="tool-name">{tc['tool']}</span>(<span class="tool-args">{args_str}</span>)
                            <div class="tool-result-preview">{preview[:150]}</div>
                        </div>
                        """
                    tool_html += '</div>'
                    st.markdown(tool_html, unsafe_allow_html=True)
            st.markdown(msg["content"])

    # -----------------------------------------------------------------------
    # Pre-investigation: source selector + investigate button
    # -----------------------------------------------------------------------
    if not st.session_state.investigation_started:
        # Stats row
        repo_files_count = len(repo_files)
        c_files = sum(1 for f in repo_files if f.endswith('.c'))
        h_files = sum(1 for f in repo_files if f.endswith('.h'))
        st.markdown(f"""
        <div class="metric-row fade-in">
            <div class="metric-card">
                <div class="metric-value">{repo_files_count}</div>
                <div class="metric-label">Total Files</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{c_files}</div>
                <div class="metric-label">Source (.c)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{h_files}</div>
                <div class="metric-label">Headers (.h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(KEY_FILES)}</div>
                <div class="metric-label">Key Files</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        source = st.radio(
            "Ticket source:",
            ["Demo (TICKET-001)", "Upload files", "GitHub Issue"],
            horizontal=True,
        )

        ticket_text = None
        log_text = None
        ready = False

        # -- Demo mode --
        if source == "Demo (TICKET-001)":
            ticket_text = _demo_ticket
            log_text = _demo_log
            ready = True

        # -- Upload mode --
        elif source == "Upload files":
            c1, c2 = st.columns(2)
            with c1:
                up_ticket = st.file_uploader("Ticket file (.md or .txt)", type=["md", "txt"])
            with c2:
                up_log = st.file_uploader("Fault log (.txt)", type=["txt"])
            if up_ticket:
                ticket_text = up_ticket.read().decode("utf-8")
                st.session_state["ticket_text"] = ticket_text
            if up_log:
                log_text = up_log.read().decode("utf-8")
                st.session_state["log_text"] = log_text
            ready = bool(ticket_text)
            if up_ticket and not up_log:
                st.caption("No log file uploaded — agent will investigate from ticket only.")

        # -- GitHub Issue mode --
        elif source == "GitHub Issue":
            gh_url = st.text_input(
                "GitHub issue URL",
                placeholder="https://github.com/owner/repo/issues/42",
            )
            up_log = st.file_uploader("Fault log (optional, .txt)", type=["txt"])

            if gh_url:
                with st.spinner("Fetching issue from GitHub..."):
                    ticket_text, err = fetch_github_issue(gh_url)
                if err:
                    st.error(err)
                    ticket_text = None
                else:
                    st.session_state["ticket_text"] = ticket_text
                    st.success("Issue fetched.")

            if up_log:
                log_text = up_log.read().decode("utf-8")
                st.session_state["log_text"] = log_text
            else:
                log_text = ""

            ready = bool(ticket_text)
            if ticket_text and not up_log:
                st.caption("No log uploaded — agent will investigate from issue + code only.")

        # -- Preview + Investigate button --
        if ready and ticket_text:
            with st.expander("📋 Preview: what the agent will receive", expanded=False):
                t1, t2 = st.tabs(["Ticket", "Fault Log"])
                with t1:
                    st.code(ticket_text[:2000] + ("..." if len(ticket_text) > 2000 else ""), language="markdown")
                with t2:
                    st.code((log_text or "(none)")[:2000], language="text")

            st.markdown("")

            if st.button("⚡  Launch Investigation", type="primary", use_container_width=True):
                st.session_state.investigation_started = True

                log_section = f"Fault Log:\n```\n{log_text}\n```\n\n" if log_text else ""
                prompt = (
                    "Investigate this firmware issue.\n\n"
                    f"Ticket:\n```\n{ticket_text}\n```\n\n"
                    f"{log_section}"
                    "Use repository tools to inspect the codebase before answering."
                )

                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Investigating: {ticket_text.splitlines()[0].lstrip('# ').strip()}",
                })

                with st.chat_message("assistant", avatar="⚡"):
                    # Progress steps
                    progress_placeholder = st.empty()
                    progress_placeholder.markdown("""
                    <div class="glass-card fade-in">
                        <div class="step-indicator step-active">
                            <div class="step-icon">1</div>
                            <span class="step-label">Scanning repository structure...</span>
                        </div>
                        <div class="step-indicator step-pending">
                            <div class="step-icon">2</div>
                            <span class="step-label">Reading source files</span>
                        </div>
                        <div class="step-indicator step-pending">
                            <div class="step-icon">3</div>
                            <span class="step-label">Analyzing failure chain</span>
                        </div>
                        <div class="step-indicator step-pending">
                            <div class="step-icon">4</div>
                            <span class="step-label">Generating triage report</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    thinking_container = st.expander("🔍 Agent Investigation Steps", expanded=True)
                    answer_container = st.empty()

                    def show_tool_call(tc):
                        args_str = ", ".join(
                            f"{k}={v}" for k, v in tc["args"].items()
                        ) if tc["args"] else ""
                        with thinking_container:
                            st.markdown(f"**{tc['tool']}**({args_str})")
                            if tc.get("result_preview"):
                                st.code(tc["result_preview"], language="text")

                    with st.spinner("Agent is analyzing the repository..."):
                        from agent import run_agent
                        result = run_agent(prompt, on_tool_call=show_tool_call)

                    progress_placeholder.empty()
                    answer_container.markdown(result["report"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["report"],
                        "tool_calls": result["tool_log"],
                    })

                st.rerun()

    # -------------------------------------------------------------------
    # Apply Fix / Revert buttons + diff view
    # -------------------------------------------------------------------
    if st.session_state.investigation_started and st.session_state.messages:
        st.divider()

        if not st.session_state.fix_applied:
            if st.button("Apply Fix", type="primary", use_container_width=True):
                apply_fix()
                st.rerun()
        else:
            st.success("Patch applied to 3 files: safety_checker.h, safety_checker.c, bms_interface.c")

            for fname, (original, patched) in PATCH_FILES.items():
                diff_text = make_diff(fname, original, patched)
                if diff_text:
                    with st.expander(f"Diff: {fname}", expanded=True):
                        st.code(diff_text, language="diff")

            if st.button("Revert Fix", use_container_width=True):
                revert_fix()
                st.rerun()

