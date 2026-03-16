# Pitch
Firmware Failure Triage Agent for legacy embedded systems.

# Demo Scenario
After BMS reconnect, torque commands continue, but applied torque stays zero until reboot.

# Success Criteria
- Agent identifies torque_inhibit latch not cleared
- Names bms_interface.c, safety_checker.c, torque_controller.c
- Proposes a patch
- Lists regression tests

# Hard Limits
- No vector DB
- No multi-agent
- No auth
- No persistent memory
- No real git integration

# Fallback
If tool loop is flaky:
- preload ticket and log
- keep repo tiny
- simplify search
- constrain prompt harder

# Ownership
Person A:
- demo_repo/*
- app.py
- logs/tickets
- demo polish

Person B:
- agent.py
- tools.py
- prompt.py
- model config
- structured output

# Ground Truth
safety_checker latches torque_inhibit on BMS timeout.
bms_interface sees heartbeat restored but does not clear inhibit.
torque_controller outputs 0 while inhibit remains true.

# Expected Diagnosis
- Root cause: torque_inhibit is set in safety_checker.c via safety_set_bms_timeout_fault() but never cleared on heartbeat recovery in bms_interface.c
- Files involved: safety_checker.c (latch set, no clear), bms_interface.c (reconnect handler missing clear call), torque_controller.c (clamp logic)
- Fix: call safety_clear_bms_timeout_fault() in bms_on_heartbeat_received() when no other active faults remain

# File Relationships
- main.c -> periodic loop, calls all subsystem ticks
- can_manager.c -> receives CAN torque commands + heartbeat frames
- bms_interface.c -> tracks heartbeat timeout/recovery, calls into safety_checker
- safety_checker.c -> owns torque_inhibit latch (SET on timeout, but NO CLEAR)
- torque_controller.c -> reads inhibit flag, clamps torque to 0
- motor_state_machine.c -> drive/idle/fault state transitions

# Demo Script
A opens: "This is a firmware triage agent for legacy embedded systems."
B explains: "It reasons across the issue ticket, fault logs, and source files instead of just chatting about code."
A closes: "It reduces codebase archaeology and gives a new engineer a concrete fix path."

# Tasks
- [x] Create CLAUDE_INSTRUCTIONS.md
- [x] Create WORKPLAN.md
- [ ] Create demo_repo C files (Person A)
- [ ] Create ticket + log (Person A)
- [ ] Create app.py UI shell (Person A)
- [ ] Create tools.py (Person B)
- [ ] Create agent.py (Person B)
- [ ] Wire backend to UI (Together)
- [ ] Test end-to-end (Together)
- [ ] Polish + rehearse demo (Together)
