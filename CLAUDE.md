# CLAUDE.md — Person B: Agent & Backend Owner

## Project Context

This is a 2-hour hackathon sprint building a **Firmware Failure Triage Agent**.
I am Person B. I own the agent brain, tools, and backend. Person A owns the fake repo, UI, and demo surface.

**Read HACKATHON_CONTEXT.pdf if it exists in this folder.**

## What We Are Building

A tool-calling agent that investigates a legacy embedded C codebase to diagnose firmware failures.

**Input:** issue ticket + fault log + small fake repo
**Output:** structured triage report (summary, hypotheses, root cause, evidence, patch, risks, tests)

## The One Scenario (Do Not Add More)

> After BMS reconnect, torque commands are received again, but applied torque stays zero until reboot.

**Hidden bug (ground truth):**
- `safety_checker.c` sets `torque_inhibit = true` when BMS heartbeat is lost
- `bms_interface.c` detects heartbeat recovery
- But **nothing clears `torque_inhibit`**
- `torque_controller.c` clamps output torque to zero if `torque_inhibit == true`

## My Files (Person B Ownership)

I own and may modify:
- `agent.py` — tool-calling loop
- `tools.py` — 3 tool implementations
- `prompt.py` — system prompt (optional, can live in agent.py)
- Any API/model config

I should **NOT** modify unless absolutely necessary:
- `app.py` (Person A)
- `demo_repo/*` (Person A)
- `demo_repo/tickets/*` (Person A)
- `demo_repo/logs/*` (Person A)

## Technical Stack

- Python 3
- OpenAI SDK pointed at NVIDIA NIM endpoint
- Model: `nvidia/nemotron-3-super-120b-a12b` (or latest available Nemotron)
- Recommended: `temperature=1.0`, `top_p=0.95`
- Streamlit for UI (Person A owns this, I just expose `run_agent()`)

## Exactly 3 Tools

1. `list_repo_files()` — list all files in `demo_repo/`
2. `read_file(path)` — read a file by relative path
3. `search_repo(query)` — substring search across all files, return matching filenames

That's it. No more tools.

## Agent Loop Requirements

- Simple tool-calling loop (no frameworks, no LangGraph, no LangChain)
- Max 8 iterations as safety limit
- Log every tool call (name + args) for UI display later
- Return structured report with these exact sections:
  - Summary
  - Ranked hypotheses
  - Most likely root cause
  - Evidence from logs
  - Evidence from code
  - Minimal patch
  - Regression risks
  - Validation tests

## Hard Limits — Do NOT Build

- No vector database
- No multi-agent orchestration
- No auth/login
- No persistent memory
- No real git integration
- No giant repo indexing
- No framework-heavy design (no LangChain, LangGraph, CrewAI, etc.)
- No NeMo Agent Toolkit (overkill for 2hr sprint)

## Fallback Strategy

If tool calling is flaky:
1. Preload ticket and log directly into the user prompt
2. Keep repo tiny (it already is)
3. Simplify search to basic substring
4. Constrain the prompt harder to guide the model
5. Worst case: deterministic file reads instead of model-chosen tools

## Code Style

- Keep files small and readable
- Prefer reliability over sophistication
- No premature abstraction
- Every function should be obvious in purpose
- Add basic error handling but don't over-engineer

## Integration Contract with Person A

Person A's `app.py` will call:
```python
from agent import run_agent
result = run_agent(prompt_string)
# result is a string (markdown-formatted report)
```

That's the entire interface. Keep it that simple.

## Success Condition

The agent must reliably output:
- **Root cause:** torque_inhibit latch never cleared after heartbeat recovery
- **Files:** bms_interface.c, safety_checker.c, torque_controller.c
- **Patch:** clear torque_inhibit on heartbeat recovery when no active fault remains
- **Tests:** disconnect/reconnect, repeated reconnect cycles, timeout fault persistence

When it does this consistently, **stop building and help polish**.
