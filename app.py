import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Firmware Failure Triage Agent", layout="wide")
st.title("Firmware Failure Triage Agent")
st.caption("Embedded incident-response agent powered by NVIDIA Nemotron")

# Load input artifacts
ticket = Path("demo_repo/tickets/ticket_001.md").read_text()
log = Path("demo_repo/logs/fault_log.txt").read_text()

# Display ticket and log side-by-side
col1, col2 = st.columns(2)
with col1:
    st.subheader("Issue Ticket")
    st.code(ticket, language="markdown")
with col2:
    st.subheader("Fault Log")
    st.code(log, language="text")

# Investigation button
if st.button("Investigate Failure", type="primary"):
    prompt = f"""
Investigate this firmware issue.

Ticket:
{ticket}

Log:
{log}

Use repository tools to inspect code before answering.
"""
    with st.spinner("Agent is analyzing repository..."):
        # Import here so app loads even if agent isn't ready yet
        from agent import run_agent
        result = run_agent(prompt)

    st.subheader("Agent Report")
    st.markdown(result)
