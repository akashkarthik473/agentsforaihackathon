// safety_checker.c
// Manages safety-critical fault latches for the motor controller.
// Owner: firmware safety team
// Last reviewed: 2024-01-15

#include "safety_checker.h"
#include <stdio.h>

static bool torque_inhibit = false;
static int fault_count = 0;

void safety_set_bms_timeout_fault(void) {
    torque_inhibit = true;
    fault_count++;
    printf("[SAFETY] torque_inhibit=1 reason=BMS_TIMEOUT\n");
}

bool safety_is_torque_inhibited(void) {
    return torque_inhibit;
}

// TODO: review reconnect handling — do we need a clear path?
// Asked about this in sprint 14 but never got closure.

void safety_tick(void) {
    // placeholder for periodic safety checks
    // overvoltage, overtemp, etc. would go here
}
