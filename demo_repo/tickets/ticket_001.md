Title: Torque remains zero after BMS reconnect

Reported by: bench test team
Priority: P1 — blocks vehicle integration milestone
Date: 2024-11-18

Observed:
- During bench testing, disconnecting and reconnecting the BMS causes torque output to remain at 0 Nm.
- CAN torque commands continue to arrive after reconnect (confirmed on scope).
- Motor state machine shows DRIVE state, but applied torque is zero.
- Full system reboot restores normal torque output.
- Issue is 100% reproducible.

Expected:
- Torque should resume once BMS heartbeat returns and no active faults remain.

Steps to reproduce:
1. Power on system, enter DRIVE state
2. Send torque command (e.g. 42 Nm) — confirmed applied
3. Disconnect BMS CAN cable (simulates heartbeat loss)
4. Wait 2 seconds
5. Reconnect BMS CAN cable
6. Send torque command again (e.g. 38 Nm)
7. Observe: applied torque = 0 Nm despite command received

Environment:
- Bench inverter rev C board
- Firmware build: 2024-11-15 (commit a3f8c2d)
- CAN bus: 500 kbps, no other nodes
