#!/usr/bin/env python3
"""
End-to-end test: runs the real agent against real NIM endpoint.
Feed in the actual ticket + fault log and print the full report + tool log.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Verify API key
key = os.environ.get("NVIDIA_API_KEY", "")
if not key:
    print("ERROR: NVIDIA_API_KEY is not set. Check your .env file or environment.")
    sys.exit(1)
print(f"API key present: {key[:8]}...")

# Read the actual ticket and fault log
REPO = Path(__file__).parent / "demo_repo"
ticket = (REPO / "tickets" / "ticket_001.md").read_text()
fault_log = (REPO / "logs" / "fault_log.txt").read_text()

user_prompt = f"""\
## Bug Ticket
{ticket}

## Fault Log
{fault_log}

Investigate the firmware repository and produce a complete triage report.
"""

print("\n" + "="*60)
print("Running agent with real NIM endpoint...")
print("="*60 + "\n")

from agent import run_agent

result = run_agent(user_prompt)

print("\n" + "="*60)
print("TOOL LOG")
print("="*60)
for i, entry in enumerate(result["tool_log"], 1):
    print(f"\n[{i}] tool={entry['tool']}  args={entry['args']}")
    print(f"    preview: {entry['result_preview'][:120]}")

print("\n" + "="*60)
print("FINAL REPORT")
print("="*60)
print(result["report"])
