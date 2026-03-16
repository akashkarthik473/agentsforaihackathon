You are helping us build a hackathon MVP called "Firmware Failure Triage Agent".

Read HACKATHON_CONTEXT.pdf and follow it closely.

Project goal:
Build a small demo app that investigates a legacy embedded C codebase using:
- one issue ticket
- one fault log
- a small fake firmware repo

The app must output:
- Summary
- Ranked hypotheses
- Most likely root cause
- Evidence from logs
- Evidence from code
- Minimal patch
- Regression risks
- Validation tests

Important constraints:
- Keep scope tiny and hackathon-friendly
- No vector DB
- No multi-agent orchestration
- No auth
- No persistent memory
- No real git integration
- No giant repo indexing
- No framework-heavy design

Technical target:
- Python app
- Streamlit UI
- OpenAI-compatible client pointed at NVIDIA NIM
- 3 tools only:
  1. list_repo_files()
  2. read_file(path)
  3. search_repo(query)

Fake firmware repo scenario:
- After BMS reconnect, torque commands are received again, but applied torque stays zero until reboot
- safety_checker sets torque_inhibit true on BMS timeout
- bms_interface detects heartbeat restore
- torque_controller clamps torque to zero if torque_inhibit is active
- hidden bug: torque_inhibit is never cleared after reconnect

Required repo structure:
demo_repo/
  main.c
  can_manager.c
  can_manager.h
  bms_interface.c
  bms_interface.h
  safety_checker.c
  safety_checker.h
  torque_controller.c
  torque_controller.h
  motor_state_machine.c
  motor_state_machine.h
  logs/
    fault_log.txt
  tickets/
    ticket_001.md

Instructions:
- First propose the exact files to create
- Then create the fake embedded repo files
- Then create the Python app files
- Keep all files small and readable
- Add one or two TODOs / legacy comments for realism
- Make the bug span 2-3 files
- Make the system demoable in under 90 seconds
- Prefer reliability over sophistication
