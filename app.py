import streamlit as st
from pathlib import Path

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
# Load demo artifacts
# ---------------------------------------------------------------------------
DEMO_ROOT = Path("demo_repo")
TICKET_PATH = DEMO_ROOT / "tickets" / "ticket_001.md"
LOG_PATH = DEMO_ROOT / "logs" / "fault_log.txt"

ticket_text = TICKET_PATH.read_text()
log_text = LOG_PATH.read_text()


def get_repo_files():
    """Return sorted list of source files in the demo repo."""
    skip = {"logs", "tickets"}
    files = []
    for p in sorted(DEMO_ROOT.rglob("*")):
        if p.is_file() and not any(s in p.parts for s in skip):
            files.append(str(p.relative_to(DEMO_ROOT)))
    return files


# ---------------------------------------------------------------------------
# Sidebar — repo file browser
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Repository")
    st.caption("demo_repo/")

    repo_files = get_repo_files()
    for f in repo_files:
        if st.button(f"📄 {f}", key=f"file_{f}", use_container_width=True):
            st.session_state.selected_file = f

    st.divider()
    st.header("Input Artifacts")
    artifact_tab = st.radio(
        "View:", ["Issue Ticket", "Fault Log"], label_visibility="collapsed"
    )

# ---------------------------------------------------------------------------
# Main layout: left = chat, right = file viewer
# ---------------------------------------------------------------------------
chat_col, viewer_col = st.columns([3, 2])

# ---------------------------------------------------------------------------
# Right column — file / artifact viewer
# ---------------------------------------------------------------------------
with viewer_col:
    if st.session_state.selected_file:
        file_path = DEMO_ROOT / st.session_state.selected_file
        st.subheader(f"📄 {st.session_state.selected_file}")
        lang = "c" if file_path.suffix in (".c", ".h") else "text"
        st.code(file_path.read_text(), language=lang, line_numbers=True)
    elif artifact_tab == "Issue Ticket":
        st.subheader("Issue Ticket")
        st.code(ticket_text, language="markdown")
    else:
        st.subheader("Fault Log")
        st.code(log_text, language="text")

# ---------------------------------------------------------------------------
# Left column — chat interface
# ---------------------------------------------------------------------------
with chat_col:
    st.subheader("Investigation")

    # Display existing messages
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

    # Start investigation button (only shown before first run)
    if not st.session_state.investigation_started:
        if st.button("Investigate Failure", type="primary", use_container_width=True):
            st.session_state.investigation_started = True

            prompt = (
                "Investigate this firmware issue.\n\n"
                f"**Ticket:**\n```\n{ticket_text}\n```\n\n"
                f"**Fault Log:**\n```\n{log_text}\n```\n\n"
                "Use repository tools to inspect the codebase before answering."
            )

            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                thinking_container = st.expander("Agent reasoning", expanded=True)
                answer_container = st.empty()

                with st.spinner("Agent is analyzing the repository..."):
                    from agent import run_agent
                    result = run_agent(prompt)

                # Show tool calls in the thinking expander
                for tc in result["tool_log"]:
                    with thinking_container:
                        args_str = ", ".join(
                            f"{k}={v}" for k, v in tc["args"].items()
                        ) if tc["args"] else ""
                        st.markdown(f"**{tc['tool']}**({args_str})")
                        if tc.get("result_preview"):
                            st.code(tc["result_preview"], language="text")

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
