"""
tools.py — 3 tool implementations for the Firmware Failure Triage Agent.
Supports mock mode (USE_MOCKS=True) for development without demo_repo/.
"""

import os

USE_MOCKS = False
DEMO_REPO_PATH = os.path.join(os.path.dirname(__file__), "..", "demo_repo")

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

MOCK_FILES = [
    "main.c",
    "can_manager.c",
    "can_manager.h",
    "bms_interface.c",
    "bms_interface.h",
    "safety_checker.c",
    "safety_checker.h",
    "torque_controller.c",
    "torque_controller.h",
    "motor_state_machine.c",
    "motor_state_machine.h",
    "logs/fault_log.txt",
    "tickets/ticket_001.md",
]

MOCK_CONTENTS = {
    "safety_checker.c": """\
#include "safety_checker.h"
#include "bms_interface.h"
#include <stdbool.h>

static bool torque_inhibit = false;

bool is_torque_inhibited(void) {
    return torque_inhibit;
}

void safety_check_periodic(void) {
    /* Check BMS heartbeat status */
    if (!bms_heartbeat_ok()) {
        /*
         * BMS heartbeat lost — inhibit torque immediately
         * to prevent uncontrolled motor output.
         */
        torque_inhibit = true;
        log_fault("SAFETY: BMS heartbeat lost — torque inhibited");
    }

    /* Check inverter over-temperature */
    if (inverter_overtemp()) {
        torque_inhibit = true;
        log_fault("SAFETY: inverter over-temp — torque inhibited");
    }

    /*
     * NOTE: there is currently no path that clears torque_inhibit
     * after the fault condition is resolved.  A reboot is required
     * to resume torque output.
     */
}
""",
    "bms_interface.c": """\
#include "bms_interface.h"
#include <stdint.h>
#include <stdbool.h>

#define BMS_HEARTBEAT_TIMEOUT_MS 500

static uint32_t last_heartbeat_ts = 0;
static bool heartbeat_present = false;

void bms_rx_callback(const can_msg_t *msg) {
    if (msg->id == BMS_HEARTBEAT_ID) {
        last_heartbeat_ts = systick_ms();

        if (!heartbeat_present) {
            heartbeat_present = true;
            log_info("BMS heartbeat recovered");
            /*
             * TODO: should we clear torque_inhibit here?
             * For now we just log recovery. The safety module
             * owns the inhibit flag, but nobody calls a clear
             * function after heartbeat comes back.
             */
        }
    }
}

bool bms_heartbeat_ok(void) {
    if ((systick_ms() - last_heartbeat_ts) > BMS_HEARTBEAT_TIMEOUT_MS) {
        heartbeat_present = false;
        return false;
    }
    return true;
}

float bms_get_voltage(void) {
    return latest_pack_voltage;
}

float bms_get_soc(void) {
    return latest_soc;
}
""",
    "torque_controller.c": """\
#include "torque_controller.h"
#include "safety_checker.h"
#include <math.h>

#define MAX_TORQUE_NM 300.0f

static float commanded_torque = 0.0f;
static float applied_torque   = 0.0f;

void torque_set_command(float torque_nm) {
    commanded_torque = fminf(fmaxf(torque_nm, -MAX_TORQUE_NM), MAX_TORQUE_NM);
}

void torque_update(void) {
    if (is_torque_inhibited()) {
        /*
         * Safety module has inhibited torque output.
         * Clamp applied torque to zero regardless of command.
         */
        applied_torque = 0.0f;
    } else {
        applied_torque = commanded_torque;
    }

    inverter_set_torque(applied_torque);
}

float torque_get_applied(void) {
    return applied_torque;
}

float torque_get_commanded(void) {
    return commanded_torque;
}
""",
    "logs/fault_log.txt": """\
[2025-06-15 14:32:01.003] INFO  : System boot complete, all modules nominal
[2025-06-15 14:32:01.050] INFO  : BMS heartbeat acquired (pack V=48.2, SOC=94%)
[2025-06-15 14:32:01.051] INFO  : Torque controller online, inhibit=false
[2025-06-15 14:35:12.220] WARN  : BMS heartbeat timeout (>500 ms)
[2025-06-15 14:35:12.221] FAULT : SAFETY: BMS heartbeat lost — torque inhibited
[2025-06-15 14:35:12.222] INFO  : Torque output clamped to 0.0 Nm
[2025-06-15 14:35:15.880] INFO  : BMS heartbeat recovered
[2025-06-15 14:35:15.881] INFO  : CAN RX: BMS pack V=48.1, SOC=93%
[2025-06-15 14:35:16.100] WARN  : Torque command received (150.0 Nm) but applied=0.0 Nm
[2025-06-15 14:35:17.100] WARN  : Torque command received (150.0 Nm) but applied=0.0 Nm
[2025-06-15 14:35:18.100] WARN  : Torque command received (150.0 Nm) but applied=0.0 Nm
[2025-06-15 14:36:00.000] INFO  : Operator triggered system reboot
[2025-06-15 14:36:05.003] INFO  : System boot complete, all modules nominal
[2025-06-15 14:36:05.055] INFO  : Torque controller online, inhibit=false
[2025-06-15 14:36:05.200] INFO  : Torque command received (150.0 Nm), applied=150.0 Nm — OK
""",
    "tickets/ticket_001.md": """\
# TICKET-001: Torque remains zero after BMS reconnect

**Reporter:** Field Engineer — Site 14
**Severity:** Critical
**Component:** Motor Controller / Safety

## Description
After a brief BMS communication dropout (~3 seconds), the BMS heartbeat
recovers successfully (confirmed on CAN bus), but the motor controller
continues to output zero torque. The vehicle is effectively immobilised
until the operator performs a full system reboot.

## Steps to reproduce
1. Start system normally — torque output works.
2. Disconnect BMS CAN cable for ~3 seconds.
3. Reconnect cable — BMS heartbeat resumes.
4. Send torque command — applied torque stays at 0 Nm.
5. Reboot system — torque works again.

## Expected behaviour
Torque output should resume automatically once the BMS heartbeat is
re-established and no other faults are active.

## Actual behaviour
Torque remains clamped at 0 Nm until reboot.
""",
    "main.c": """\
#include "can_manager.h"
#include "bms_interface.h"
#include "safety_checker.h"
#include "torque_controller.h"
#include "motor_state_machine.h"

int main(void) {
    system_init();
    can_manager_init();
    bms_interface_init();
    safety_checker_init();
    torque_controller_init();
    motor_sm_init();

    while (1) {
        can_manager_poll();
        safety_check_periodic();
        torque_update();
        motor_sm_step();
    }
}
""",
}

# Default mock search results keyed by lowercase substrings
MOCK_SEARCH_INDEX = {
    "torque_inhibit": ["safety_checker.c", "safety_checker.h", "torque_controller.c"],
    "inhibit": ["safety_checker.c", "safety_checker.h", "torque_controller.c", "logs/fault_log.txt"],
    "heartbeat": ["bms_interface.c", "bms_interface.h", "safety_checker.c", "logs/fault_log.txt"],
    "bms": ["bms_interface.c", "bms_interface.h", "safety_checker.c", "logs/fault_log.txt", "tickets/ticket_001.md"],
    "torque": ["torque_controller.c", "torque_controller.h", "safety_checker.c", "logs/fault_log.txt", "tickets/ticket_001.md"],
    "fault": ["safety_checker.c", "logs/fault_log.txt", "tickets/ticket_001.md"],
    "reboot": ["logs/fault_log.txt", "tickets/ticket_001.md"],
    "clear": ["bms_interface.c"],
}

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def list_repo_files():
    """List all files in demo_repo/. Returns {"files": [...]}."""
    if USE_MOCKS:
        return {"files": list(MOCK_FILES)}

    files = []
    for root, _dirs, filenames in os.walk(DEMO_REPO_PATH):
        for fname in filenames:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, DEMO_REPO_PATH)
            files.append(rel)
    files.sort()
    return {"files": files}


def read_file(path):
    """Read a file by relative path. Returns {"path", "content"} or {"path", "error"}."""
    if USE_MOCKS:
        content = MOCK_CONTENTS.get(path)
        if content is not None:
            return {"path": path, "content": content}
        # For files without explicit mock content, return a placeholder
        if path in MOCK_FILES:
            return {"path": path, "content": f"/* {path} — stub, no detailed mock content */\n"}
        return {"path": path, "error": "File not found"}

    full_path = os.path.join(DEMO_REPO_PATH, path)
    try:
        with open(full_path, "r") as f:
            return {"path": path, "content": f.read()}
    except FileNotFoundError:
        return {"path": path, "error": "File not found"}
    except Exception as e:
        return {"path": path, "error": str(e)}


def search_repo(query):
    """Case-insensitive substring search across all repo files. Returns {"query", "matches": [...]}."""
    if USE_MOCKS:
        q = query.lower()
        # Try exact key match first, then substring match on keys
        if q in MOCK_SEARCH_INDEX:
            return {"query": query, "matches": MOCK_SEARCH_INDEX[q]}
        matches = set()
        for key, files in MOCK_SEARCH_INDEX.items():
            if q in key or key in q:
                matches.update(files)
        return {"query": query, "matches": sorted(matches)}

    all_files = list_repo_files()["files"]
    matches = []
    q = query.lower()
    for fpath in all_files:
        full_path = os.path.join(DEMO_REPO_PATH, fpath)
        try:
            with open(full_path, "r") as f:
                if q in f.read().lower():
                    matches.append(fpath)
        except Exception:
            continue
    return {"query": query, "matches": matches}
