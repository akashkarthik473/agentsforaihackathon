"""
agent.py — Tool-calling loop for the Firmware Failure Triage Agent.
Uses NVIDIA NIM / Nemotron via the OpenAI-compatible SDK.
"""

import json
import os, streamlit as st

from dotenv import load_dotenv
from openai import OpenAI
from tools import call_tool, TOOL_DEFINITIONS

load_dotenv()

# ---------------------------------------------------------------------------
# Client setup
# ---------------------------------------------------------------------------

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key = os.environ.get("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
)

MODEL = "nvidia/nemotron-3-super-120b-a12b"
MAX_ITERATIONS = 8

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert embedded-systems firmware engineer performing root-cause analysis on a legacy embedded C codebase.

You will be given a bug ticket and fault log in the user message. Use the available tools to investigate the \
repository and produce a structured triage report.

INVESTIGATION PROCEDURE
Follow these steps in order:

1. Call list_repo_files() first to understand what files exist.
2. Read tickets/ and logs/ files to fully understand the reported symptoms.
3. Search for key terms related to the failure domain:
   - For heartbeat/reconnect/timeout issues: search "torque_inhibit", "heartbeat", "inhibit"
   - Read bms_interface.c, safety_checker.c, and torque_controller.c as your primary suspects.
4. Read at least 3 source files before drawing any conclusions.
5. Once you have concrete evidence from code and logs, write the final report.

BEHAVIORAL RULES
- Be concrete, never vague. Write "safety_checker.c:safety_check_periodic() sets torque_inhibit = true" \
not "somewhere in the safety module an inhibit is set".
- Every claim must be backed by a specific log line or code location.
- Prefer short, evidence-backed reasoning over lengthy explanation.
- Name exact files and functions for every finding.
- When the failure involves heartbeat/timeout/reconnect, always prioritize reading:
  bms_interface.c -> safety_checker.c -> torque_controller.c
- Keep the patch minimal and readable -- only change what is necessary to fix the bug.
- Include a risk rating (Low / Medium / High) in the Regression Risks section.

OUTPUT FORMAT
Your final response MUST use exactly these markdown section headers, in this order:

## Summary
One concise paragraph describing what fails, when it fails, and the observable symptom.

## Ranked Hypotheses
2-4 numbered hypotheses, ranked most-to-least likely. For each, state:
- What the hypothesis is
- Why the evidence supports or weakens it

## Most Likely Root Cause
One precise statement naming the exact bug: which file, which function, what it does wrong.

## Evidence from Logs
Quoted log lines (with timestamps) that support your root cause. Explain what each line shows.

## Evidence from Code
Specific function names and line-level observations from the source files you read. \
Quote or paraphrase the relevant code.

## Minimal Patch
A diff-style or pseudocode patch showing exactly what to add or change. Keep it short.

## Regression Risks
Bullet list of risks. Tag each as [Low], [Medium], or [High].

## Validation Tests
Concrete, numbered test scenarios. Each test must describe:
- Setup
- Action
- Expected result
"""

# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------

def run_agent(user_prompt: str):
    """
    Run the triage agent on the given prompt.
    Returns {"report": str, "tool_log": list[dict]}.
    """
    tool_log = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=1.0,
            top_p=0.95,
        )

        message = response.choices[0].message

        # If the model returned text with no tool calls, we're done.
        # Guard against the model printing tool calls as raw text instead of
        # using the API mechanism — if content looks like a tool call, keep looping.
        if not message.tool_calls:
            content = message.content or ""
            if "<tool_call>" in content or "<function=" in content:
                # Model fell back to text-based tool call format — ignore and
                # force it to write the report on the next pass
                messages.append(message.model_dump(exclude_unset=True))
                messages.append({
                    "role": "user",
                    "content": (
                        "Stop calling tools and write the full triage report now "
                        "using only what you have already read."
                    ),
                })
                continue
            return {"report": content, "tool_log": tool_log}

        # Append the assistant message (with tool_calls) to history
        # Must be a plain dict — the Pydantic object causes SDK transform errors
        messages.append(message.model_dump(exclude_unset=True))

        # Execute each tool call and collect results
        for tc in message.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result_str = call_tool(name, args)

            # Log the tool call
            tool_log.append({
                "tool": name,
                "args": args,
                "result_preview": result_str[:200],
            })

            print(f"[iter {iteration+1}] tool={name} args={args}")

            # Append tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    # Exhausted iterations — ask model for best-effort report
    messages.append({
        "role": "user",
        "content": (
            "You have reached the investigation limit. "
            "Based on everything gathered so far, write the full triage report now."
        ),
    })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=1.0,
        top_p=0.95,
    )

    report = response.choices[0].message.content or "Agent exhausted iterations without producing a report."
    return {"report": report, "tool_log": tool_log}
