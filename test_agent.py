#!/usr/bin/env python3
"""
test_agent.py — Consistency test: run the agent 5 times and check each report.

Checks per run:
  - Root cause identified: torque_inhibit latch never cleared
  - Key files mentioned: bms_interface.c, safety_checker.c, torque_controller.c
  - Iteration (tool call) count printed

Usage: python test_agent.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("NVIDIA_API_KEY", "")
if not key:
    print("ERROR: NVIDIA_API_KEY is not set.")
    sys.exit(1)
print(f"API key present: {key[:8]}...\n")

REPO = Path(__file__).parent / "demo_repo"
ticket    = (REPO / "tickets" / "ticket_001.md").read_text()
fault_log = (REPO / "logs" / "fault_log.txt").read_text()

USER_PROMPT = f"""\
## Bug Ticket
{ticket}

## Fault Log
{fault_log}

Investigate the firmware repository and produce a complete triage report.
"""

REQUIRED_FILES     = ["bms_interface.c", "safety_checker.c", "torque_controller.c"]
ROOT_CAUSE_PHRASES = ["torque_inhibit", "never cleared", "latch", "not cleared", "no clear"]

from agent import run_agent


def check_report(report: str, tool_log: list, run_num: int) -> bool:
    ok = True
    low = report.lower()

    for fname in REQUIRED_FILES:
        if fname in report:
            print(f"  [OK]   {fname} mentioned")
        else:
            print(f"  [FAIL] {fname} NOT mentioned")
            ok = False

    if any(phrase in low for phrase in ROOT_CAUSE_PHRASES):
        print(f"  [OK]   root-cause phrase found")
    else:
        print(f"  [FAIL] root-cause phrase missing (expected one of: {ROOT_CAUSE_PHRASES})")
        ok = False

    if "torque_inhibit" in report:
        print(f"  [OK]   torque_inhibit mentioned")
    else:
        print(f"  [FAIL] torque_inhibit NOT mentioned")
        ok = False

    print(f"  [INFO] tool calls (iterations): {len(tool_log)}")
    return ok


N = 5
passes = 0

for i in range(1, N + 1):
    print(f"\n{'='*64}")
    print(f"RUN {i}/{N}")
    print('='*64)
    try:
        result   = run_agent(USER_PROMPT)
        report   = result["report"]
        tool_log = result["tool_log"]

        passed = check_report(report, tool_log, i)
        if passed:
            passes += 1
            print("  >>> PASS")
        else:
            print("  >>> FAIL")

        # Show first 12 lines of report for quick review
        print("\n  --- Report (first 12 lines) ---")
        for line in report.strip().splitlines()[:12]:
            print(f"  {line}")

        # Show tool call sequence
        print("\n  --- Tool call sequence ---")
        for j, entry in enumerate(tool_log, 1):
            args_str = str(entry["args"])[:60]
            print(f"  {j}. {entry['tool']}({args_str})")

    except Exception as e:
        print(f"  [ERROR] Exception: {e}")

print(f"\n{'='*64}")
print(f"FINAL RESULTS: {passes}/{N} passed")
print('='*64)
sys.exit(0 if passes == N else 1)
