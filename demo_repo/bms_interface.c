// bms_interface.c
// Tracks BMS heartbeat presence over CAN.
// When heartbeat is lost, triggers safety fault.
// When heartbeat returns, marks recovery.

#include "bms_interface.h"
#include "safety_checker.h"
#include <stdio.h>

static bool heartbeat_present = false;
static int timeout_counter = 0;

#define BMS_TIMEOUT_THRESHOLD 50  // ticks

void bms_on_heartbeat_timeout(void) {
    heartbeat_present = false;
    safety_set_bms_timeout_fault();
    printf("[BMS] heartbeat lost, safety fault raised\n");
}

void bms_on_heartbeat_received(void) {
    heartbeat_present = true;
    timeout_counter = 0;
    // reconnect detected, but fault latch is never cleared
    // TODO: should we notify safety_checker here?
    printf("[BMS] heartbeat restored\n");
}

bool bms_is_heartbeat_present(void) {
    return heartbeat_present;
}

void bms_tick(void) {
    if (!heartbeat_present) {
        timeout_counter++;
        if (timeout_counter >= BMS_TIMEOUT_THRESHOLD) {
            bms_on_heartbeat_timeout();
            timeout_counter = 0;  // prevent re-trigger spam
        }
    }
}
