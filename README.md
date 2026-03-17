# Firmware Failure Triage Agent

An AI-powered tool-calling agent that investigates legacy embedded C codebases to diagnose firmware failures. Given a bug ticket and fault log, it autonomously reads source files, traces signal paths across modules, and produces a structured triage report with root cause analysis, a minimal patch, and regression tests.

Built with **NVIDIA Nemotron** via **NVIDIA NIM** (OpenAI-compatible inference endpoint).

## Demo Scenario

> After BMS reconnect, torque commands are received but applied torque stays zero until reboot.

The agent traces the bug across `bms_interface.c` → `safety_checker.c` → `torque_controller.c`, identifies a fault latch (`torque_inhibit`) that is set on BMS timeout but never cleared on heartbeat recovery, and proposes a two-line fix.

## How It Works

1. **Input** — Bug ticket + fault log (preloaded demo, file upload, or GitHub issue URL)
2. **Investigation** — Agent uses 3 tools (`list_repo_files`, `read_file`, `search_repo`) to explore the codebase autonomously via tool calling
3. **Output** — Structured report: summary, ranked hypotheses, root cause, evidence from logs & code, minimal patch, regression risks, validation tests
4. **Apply Fix** — One-click patch application with diff visualization

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with your NVIDIA NIM API key:

```
NVIDIA_API_KEY=nvapi-xxxxxxxxxx
```

## Run

```bash
streamlit run app.py
```

## Architecture

```
app.py              Streamlit UI — chat interface, file viewer, patch application
agent.py            Tool-calling loop — max 8 iterations, structured report output
tools.py            3 repository tools: list, read, search
demo_repo/          Embedded C firmware codebase (10 files with planted bug)
  tickets/          Bug ticket (TICKET-001)
  logs/             Fault log
test_agent.py       Consistency test — runs agent 5x, validates output
```

## NVIDIA AI Ecosystem

- **NVIDIA NIM** — Inference endpoint serving the model via OpenAI-compatible API
- **NVIDIA Nemotron** (`nvidia/nemotron-3-super-120b-a12b`) — Reasoning model powering the agent's tool-calling loop and report generation
