"""
Mock agent that simulates the real agent's event stream.
Used so the UI can be tested before Person B's agent.py is ready.
Delete this file once the real agent is wired up.
"""

import time
from pathlib import Path

DEMO_ROOT = Path("demo_repo")


def run_mock_agent():
    """Yield events that mimic the real agent's investigation."""

    yield {"type": "thinking", "content": "Reading the ticket and fault log..."}
    time.sleep(0.4)

    # Step 1 — list files
    files = sorted(str(p.relative_to(DEMO_ROOT)) for p in DEMO_ROOT.rglob("*") if p.is_file())
    yield {
        "type": "tool_call",
        "tool": "list_repo_files",
        "args": "",
        "result": "\n".join(files),
    }
    time.sleep(0.3)

    yield {"type": "thinking", "content": "The log shows torque_inhibit=1 set on BMS_TIMEOUT but never cleared. Let me check bms_interface.c first."}
    time.sleep(0.4)

    # Step 2 — read bms_interface.c
    bms_code = (DEMO_ROOT / "bms_interface.c").read_text()
    yield {
        "type": "tool_call",
        "tool": "read_file",
        "args": "bms_interface.c",
        "result": bms_code,
    }
    time.sleep(0.3)

    yield {"type": "thinking", "content": "bms_on_heartbeat_received() logs the restore but never calls safety_clear. Let me check safety_checker.c."}
    time.sleep(0.4)

    # Step 3 — read safety_checker.c
    safety_code = (DEMO_ROOT / "safety_checker.c").read_text()
    yield {
        "type": "tool_call",
        "tool": "read_file",
        "args": "safety_checker.c",
        "result": safety_code,
    }
    time.sleep(0.3)

    yield {"type": "thinking", "content": "Confirmed: there is no safety_clear_bms_timeout_fault() function. The latch is set but never cleared."}
    time.sleep(0.3)

    # Step 4 — read torque_controller.c
    torque_code = (DEMO_ROOT / "torque_controller.c").read_text()
    yield {
        "type": "tool_call",
        "tool": "read_file",
        "args": "torque_controller.c",
        "result": torque_code,
    }
    time.sleep(0.3)

    yield {"type": "thinking", "content": "torque_compute_applied() returns 0 whenever torque_inhibit is true. This completes the signal path."}
    time.sleep(0.3)

    # Step 5 — search for the clear function
    yield {
        "type": "tool_call",
        "tool": "search_repo",
        "args": "safety_clear",
        "result": "No results found.",
    }
    time.sleep(0.3)

    # Final answer
    yield {
        "type": "answer",
        "content": """## Root Cause Analysis

### Summary
After a BMS heartbeat timeout, `torque_inhibit` is latched **true** in `safety_checker.c` but **never cleared** when the heartbeat is restored. This causes `torque_controller.c` to clamp applied torque to **0 Nm** indefinitely.

### Signal Path
1. **`bms_interface.c`** — `bms_check_heartbeat()` detects timeout → calls `safety_set_bms_timeout_fault()`
2. **`safety_checker.c`** — `safety_set_bms_timeout_fault()` sets `torque_inhibit = true` (no corresponding clear function exists)
3. **`torque_controller.c`** — `torque_compute_applied()` checks `safety_is_torque_inhibited()` → returns 0
4. **`bms_interface.c`** — `bms_on_heartbeat_received()` logs "heartbeat restored" but **does not call any safety clear function**

### Files Involved
| File | Role |
|------|------|
| `bms_interface.c` | Detects timeout & reconnect, but missing clear call |
| `safety_checker.c` | Owns the latch — set function exists, clear function missing |
| `torque_controller.c` | Reads inhibit flag, clamps output to 0 |

### Proposed Fix
1. Add `safety_clear_bms_timeout_fault()` to `safety_checker.c`:
```c
void safety_clear_bms_timeout_fault(void) {
    torque_inhibit = false;
    log_info("safety torque_inhibit=0 reason=BMS_RECOVERED");
}
```

2. Call it from `bms_on_heartbeat_received()` in `bms_interface.c`:
```c
void bms_on_heartbeat_received(void) {
    heartbeat_present = true;
    log_info("bms_heartbeat_restored");
    safety_clear_bms_timeout_fault();
}
```

### Regression Risks
- Clearing inhibit while other faults are active could allow unsafe torque output
- Should add a guard: only clear if no other active faults remain

### Suggested Tests
1. BMS disconnect → reconnect → verify torque resumes
2. BMS disconnect → reconnect with other active fault → verify torque stays inhibited
3. Rapid BMS disconnect/reconnect cycling — verify no race conditions
4. Verify fault log entries for both set and clear transitions
""",
    }
