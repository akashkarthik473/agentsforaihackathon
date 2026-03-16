# Firmware Failure Triage Agent

Embedded incident-response agent powered by NVIDIA Nemotron. Given an issue ticket and fault log, it reasons across a legacy C firmware codebase to identify root cause, trace the signal path, and propose a minimal patch.

## Demo scenario

After a BMS reconnect, torque commands are received but applied torque stays zero until reboot. The agent traces the bug across `bms_interface.c`, `safety_checker.c`, and `torque_controller.c`.

## Setup

```bash
pip install -r requirements.txt
```

Set your NVIDIA NIM API key:

```bash
export NVIDIA_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

## Repo structure

```
demo_repo/          # Fake embedded C firmware (the codebase under investigation)
  logs/             # Fault log
  tickets/          # Issue ticket
app.py              # Streamlit UI (Person A)
agent.py            # Agent loop + tool calling (Person B)
tools.py            # Repo tools: list, read, search (Person B)
prompt.py           # System prompt (Person B)
```

## Ownership

| Area | Owner |
|---|---|
| demo_repo, app.py, logs, tickets | Person A |
| agent.py, tools.py, prompt.py, model config | Person B |
