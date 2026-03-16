// torque_controller.c
// Computes applied torque from requested torque.
// Respects safety inhibit — if torque is inhibited, output is clamped to zero.

#include "torque_controller.h"
#include "safety_checker.h"
#include <stdio.h>

static int last_requested = 0;
static int last_applied = 0;

int torque_compute_applied(int requested_nm) {
    if (safety_is_torque_inhibited()) {
        return 0;  // safety clamp active
    }
    // basic rate limiter — not relevant to the bug
    if (requested_nm > 200) {
        requested_nm = 200;
    }
    return requested_nm;
}

void torque_set_requested(int nm) {
    last_requested = nm;
    last_applied = torque_compute_applied(nm);
    printf("[TORQUE] requested=%d applied=%d\n", last_requested, last_applied);
}

int torque_get_applied(void) {
    return last_applied;
}
