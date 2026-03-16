"""
test_agent.py — Verify the agent loop works end-to-end.

DRY_RUN=True: simulates model responses with a scripted sequence so the loop
              logic can be verified without a real NVIDIA API key.
DRY_RUN=False: calls run_agent() directly using the real NIM endpoint.
"""

import json
import sys

DRY_RUN = True  # Set False to hit the real NVIDIA endpoint

# ---------------------------------------------------------------------------
# Sample prompt — realistic BMS/torque scenario from CLAUDE.md
# ---------------------------------------------------------------------------

SAMPLE_PROMPT = """\
## Bug Ticket: TICKET-001 — Torque remains zero after BMS reconnect

**Severity:** Critical
**Component:** Motor Controller / Safety

After a brief BMS CAN dropout (~3 s), the BMS heartbeat recovers successfully
(confirmed on CAN bus), but the motor controller continues to output zero torque.
The vehicle is immobilised until a full system reboot.

## Fault Log (excerpt)

[2025-06-15 14:35:12.221] FAULT : SAFETY: BMS heartbeat lost — torque inhibited
[2025-06-15 14:35:12.222] INFO  : Torque output clamped to 0.0 Nm
[2025-06-15 14:35:15.880] INFO  : BMS heartbeat recovered
[2025-06-15 14:35:16.100] WARN  : Torque command received (150.0 Nm) but applied=0.0 Nm
[2025-06-15 14:36:00.000] INFO  : Operator triggered system reboot
[2025-06-15 14:36:05.200] INFO  : Torque command received (150.0 Nm), applied=150.0 Nm — OK

Please investigate and produce a full triage report.
"""

# ---------------------------------------------------------------------------
# DRY RUN — scripted model responses
# ---------------------------------------------------------------------------

def _make_tool_call(call_id, name, args):
    """Helper: build a fake tool_call object compatible with the agent's dispatch."""
    class FunctionCall:
        def __init__(self):
            self.name = name
            self.arguments = json.dumps(args)

    class ToolCall:
        def __init__(self):
            self.id = call_id
            self.function = FunctionCall()

    return ToolCall()


def _make_assistant_message(tool_calls=None, content=None):
    class Message:
        def __init__(self):
            self.tool_calls = tool_calls
            self.content = content

    class Choice:
        def __init__(self):
            self.message = Message()

    class Response:
        def __init__(self):
            self.choices = [Choice()]

    return Response()


SCRIPTED_FINAL_REPORT = """\
## Summary
After a BMS CAN dropout, `safety_checker.c:safety_check_periodic()` correctly sets
`torque_inhibit = true`. However, once the heartbeat recovers, no code path clears
this flag. `torque_controller.c:torque_update()` clamps applied torque to 0.0 Nm
whenever `torque_inhibit` is true, so the vehicle remains immobilised until reboot.

## Ranked Hypotheses
1. **torque_inhibit latch not cleared after recovery** — `safety_checker.c` sets the
   flag on BMS loss but contains no clear path. `bms_interface.c` logs recovery but
   never touches the flag. Directly matches all observed symptoms.
2. **BMS heartbeat recovery not detected reliably** — `bms_heartbeat_ok()` uses a
   500 ms rolling window. Unlikely given the log clearly shows recovery was detected.
3. **CAN message backlog causing repeated timeout triggers** — possible in theory,
   but the log shows no repeated FAULT lines after recovery.

## Most Likely Root Cause
`safety_checker.c:safety_check_periodic()` sets `torque_inhibit = true` when
`bms_heartbeat_ok()` returns false, but there is **no code path that sets
`torque_inhibit = false`** after the heartbeat recovers. The flag is a one-way latch.

## Evidence from Logs
- `14:35:12.221 FAULT: BMS heartbeat lost — torque inhibited` — inhibit is set.
- `14:35:15.880 INFO: BMS heartbeat recovered` — recovery is detected 3 s later.
- `14:35:16.100 WARN: Torque command received (150.0 Nm) but applied=0.0 Nm` — torque
  stays zero despite recovery, confirming the flag was never cleared.
- `14:36:05.200 INFO: applied=150.0 Nm — OK` — works again only after reboot.

## Evidence from Code
- `safety_checker.c:safety_check_periodic()` — sets `torque_inhibit = true` on
  heartbeat loss and on over-temp. Contains a comment: *"there is currently no path
  that clears torque_inhibit after the fault condition is resolved."*
- `bms_interface.c:bms_rx_callback()` — detects heartbeat recovery and logs it, but
  includes a TODO comment: *"should we clear torque_inhibit here? … nobody calls a
  clear function after heartbeat comes back."*
- `torque_controller.c:torque_update()` — unconditionally clamps `applied_torque = 0`
  when `is_torque_inhibited()` returns true.

## Minimal Patch
```c
// safety_checker.h — add a new public function
+ void safety_clear_torque_inhibit(void);

// safety_checker.c — implement it
+ void safety_clear_torque_inhibit(void) {
+     torque_inhibit = false;
+ }

// bms_interface.c — bms_rx_callback(), after heartbeat recovery is detected:
  if (!heartbeat_present) {
      heartbeat_present = true;
      log_info("BMS heartbeat recovered");
+     safety_clear_torque_inhibit();  // clear latch — BMS is healthy again
  }
```

## Regression Risks
- [Low] **Over-temp fault:** `torque_inhibit` is also set for inverter over-temp.
  The new clear path is only triggered by BMS heartbeat recovery, so over-temp
  inhibit is unaffected. Verify `safety_check_periodic()` re-latches immediately
  if over-temp is still active when BMS recovers.
- [Medium] **Race condition:** If BMS heartbeat is marginal (intermittent),
  `bms_rx_callback()` may clear the inhibit while `safety_check_periodic()` is
  mid-execution and about to re-set it. Consider adding a check:
  `if (bms_heartbeat_ok() && !inverter_overtemp()) safety_clear_torque_inhibit();`
- [Low] **Multiple fault sources:** Future faults that set `torque_inhibit` will also
  be cleared by this path. Document that `torque_inhibit` clears on any BMS recovery.

## Validation Tests
1. **Basic reconnect:** Disconnect BMS CAN for 3 s, reconnect. Confirm torque
   commands are honoured within one heartbeat cycle (~500 ms) without reboot.
2. **Repeated reconnect cycles:** Disconnect/reconnect 10 times in succession.
   Torque must resume correctly after each reconnect.
3. **Over-temp + BMS recovery:** Trigger inverter over-temp while BMS is disconnected.
   Reconnect BMS — torque must remain inhibited until over-temp clears.
4. **Timeout persistence:** Disconnect BMS for longer than the fault-log timeout.
   Confirm the fault is logged and torque stays inhibited until BMS recovers.
5. **Marginal heartbeat (jitter test):** Send BMS heartbeats at 490–510 ms intervals.
   Confirm no spurious inhibit clears or re-latches occur.
"""


def run_dry_run(prompt: str) -> dict:
    """
    Simulate the agent loop with scripted tool calls and a canned final report.
    Exercises the same dispatch and logging paths as the real loop.
    """
    from tools import list_repo_files, read_file, search_repo

    tool_log = []

    def dispatch_and_log(name, args):
        if name == "list_repo_files":
            result = list_repo_files()
        elif name == "read_file":
            result = read_file(args.get("path", ""))
        elif name == "search_repo":
            result = search_repo(args.get("query", ""))
        else:
            result = {"error": f"Unknown tool: {name}"}

        result_str = json.dumps(result)
        tool_log.append({
            "tool": name,
            "args": args,
            "result_preview": result_str[:200],
        })
        print(f"  [tool] {name}({args}) → {result_str[:120]}...")
        return result

    print("\n=== DRY RUN: simulating agent iterations ===\n")

    # Iteration 1 — list files
    print("Iteration 1: list_repo_files()")
    dispatch_and_log("list_repo_files", {})

    # Iteration 2 — read ticket
    print("Iteration 2: read_file(tickets/ticket_001.md)")
    dispatch_and_log("read_file", {"path": "tickets/ticket_001.md"})

    # Iteration 3 — read fault log
    print("Iteration 3: read_file(logs/fault_log.txt)")
    dispatch_and_log("read_file", {"path": "logs/fault_log.txt"})

    # Iteration 4 — search for torque_inhibit
    print("Iteration 4: search_repo(torque_inhibit)")
    dispatch_and_log("search_repo", {"query": "torque_inhibit"})

    # Iteration 5 — read safety_checker.c
    print("Iteration 5: read_file(safety_checker.c)")
    dispatch_and_log("read_file", {"path": "safety_checker.c"})

    # Iteration 6 — read bms_interface.c
    print("Iteration 6: read_file(bms_interface.c)")
    dispatch_and_log("read_file", {"path": "bms_interface.c"})

    # Iteration 7 — read torque_controller.c
    print("Iteration 7: read_file(torque_controller.c)")
    dispatch_and_log("read_file", {"path": "torque_controller.c"})

    print("\n=== All tool calls complete. Generating report... ===\n")

    return {"report": SCRIPTED_FINAL_REPORT, "tool_log": tool_log}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Firmware Failure Triage Agent — Test Run")
    print(f"Mode: {'DRY RUN (simulated)' if DRY_RUN else 'LIVE (NVIDIA NIM)'}")
    print("=" * 60)
    print("\n--- USER PROMPT ---")
    print(SAMPLE_PROMPT)

    if DRY_RUN:
        result = run_dry_run(SAMPLE_PROMPT)
    else:
        from agent import run_agent
        result = run_agent(SAMPLE_PROMPT)

    report = result["report"]
    tool_log = result["tool_log"]

    print("\n" + "=" * 60)
    print("TRIAGE REPORT")
    print("=" * 60)
    print(report)

    print("\n" + "=" * 60)
    print(f"TOOL LOG ({len(tool_log)} calls)")
    print("=" * 60)
    for i, entry in enumerate(tool_log, 1):
        args_str = json.dumps(entry["args"]) if entry["args"] else "{}"
        print(f"\n[{i}] {entry['tool']}({args_str})")
        print(f"    preview: {entry['result_preview'][:150]}")

    print("\n--- DONE ---")


if __name__ == "__main__":
    main()
