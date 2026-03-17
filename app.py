import streamlit as st
from pathlib import Path
import requests

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Firmware Failure Triage Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "investigation_started" not in st.session_state:
    st.session_state.investigation_started = False
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEMO_ROOT = Path("demo_repo")
TICKET_PATH = DEMO_ROOT / "tickets" / "ticket_001.md"
LOG_PATH = DEMO_ROOT / "logs" / "fault_log.txt"
KEY_FILES = {"bms_interface.c", "safety_checker.c", "torque_controller.c"}


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


def fetch_github_issue(url: str):
    """Fetch a GitHub issue and return (ticket_text, error_msg)."""
    try:
        parts = url.rstrip("/").split("/")
        # Expected: https://github.com/{owner}/{repo}/issues/{number}
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
# Sidebar — repo file browser
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Repository")
    st.caption("demo_repo/")

    repo_files = get_repo_files()
    for f in repo_files:
        label = f"**📄 {f}**" if f in KEY_FILES else f"📄 {f}"
        if st.button(label, key=f"file_{f}", use_container_width=True):
            st.session_state.selected_file = f

    st.divider()
    st.header("Input Artifacts")
    artifact_tab = st.radio(
        "View:", ["Issue Ticket", "Fault Log"], label_visibility="collapsed"
    )

    if st.session_state.investigation_started:
        st.divider()
        if st.button("Reset", use_container_width=True):
            reset()
            st.rerun()

# ---------------------------------------------------------------------------
# Main layout: left = chat, right = file viewer
# ---------------------------------------------------------------------------
chat_col, viewer_col = st.columns([3, 2])

# ---------------------------------------------------------------------------
# Right column — file / artifact viewer
# ---------------------------------------------------------------------------
# These will be set in the left column based on source mode; default to demo files
_demo_ticket = TICKET_PATH.read_text(encoding="utf-8")
_demo_log = LOG_PATH.read_text(encoding="utf-8")

with viewer_col:
    if st.session_state.selected_file:
        file_path = DEMO_ROOT / st.session_state.selected_file
        st.subheader(f"📄 {st.session_state.selected_file}")
        lang = "c" if file_path.suffix in (".c", ".h") else "text"
        st.code(file_path.read_text(encoding="utf-8"), language=lang, line_numbers=True)
    elif artifact_tab == "Issue Ticket":
        ticket_preview = st.session_state.get("ticket_text", _demo_ticket)
        st.subheader("Issue Ticket")
        st.code(ticket_preview, language="markdown")
    else:
        log_preview = st.session_state.get("log_text", _demo_log)
        st.subheader("Fault Log")
        st.code(log_preview, language="text")

# ---------------------------------------------------------------------------
# Left column — chat / investigation panel
# ---------------------------------------------------------------------------
with chat_col:
    st.subheader("Investigation")

    # Render conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("tool_calls"):
                with st.expander("Agent reasoning", expanded=False):
                    for tc in msg["tool_calls"]:
                        args_str = ", ".join(
                            f"{k}={v}" for k, v in tc["args"].items()
                        ) if tc["args"] else ""
                        st.markdown(f"**{tc['tool']}**({args_str})")
                        if tc.get("result_preview"):
                            st.code(tc["result_preview"], language="text")
            st.markdown(msg["content"])

    # -----------------------------------------------------------------------
    # Pre-investigation: source selector + investigate button
    # -----------------------------------------------------------------------
    if not st.session_state.investigation_started:

        source = st.radio(
            "Ticket source:",
            ["Demo (TICKET-001)", "Upload files", "GitHub Issue"],
            horizontal=True,
        )

        ticket_text = None
        log_text = None
        ready = False

        # -- Demo mode ------------------------------------------------------
        if source == "Demo (TICKET-001)":
            ticket_text = _demo_ticket
            log_text = _demo_log
            ready = True

        # -- Upload mode ----------------------------------------------------
        elif source == "Upload files":
            up_ticket = st.file_uploader("Ticket file (.md or .txt)", type=["md", "txt"])
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

        # -- GitHub Issue mode ----------------------------------------------
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

        # -- Preview + Investigate button -----------------------------------
        if ready and ticket_text:
            with st.expander("What the agent will receive", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Ticket")
                    st.code(ticket_text[:1500] + ("..." if len(ticket_text) > 1500 else ""), language="markdown")
                with c2:
                    st.caption("Fault Log")
                    st.code((log_text or "(none)")[:1500], language="text")

            if st.button("Investigate Failure", type="primary", use_container_width=True):
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

                with st.chat_message("assistant"):
                    thinking_container = st.expander("Agent reasoning", expanded=True)
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

                    answer_container.markdown(result["report"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["report"],
                        "tool_calls": result["tool_log"],
                    })

                st.rerun()

    # Follow-up chat input
    if st.session_state.investigation_started:
        if follow_up := st.chat_input("Ask a follow-up question..."):
            st.session_state.messages.append({"role": "user", "content": follow_up})
            st.rerun()
