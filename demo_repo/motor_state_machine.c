// motor_state_machine.c
// Simple state machine for motor controller.
// States: IDLE -> DRIVE -> FAULT
// FAULT state is entered on safety inhibit, but note:
// the actual torque clamp happens in torque_controller.c, not here.

#include "motor_state_machine.h"
#include "safety_checker.h"
#include "torque_controller.h"
#include <stdio.h>

static motor_state_t current_state = MOTOR_STATE_IDLE;

void motor_sm_init(void) {
    current_state = MOTOR_STATE_IDLE;
    printf("[MOTOR] state machine initialized\n");
}

void motor_sm_tick(void) {
    switch (current_state) {
        case MOTOR_STATE_IDLE:
            if (torque_get_applied() > 0) {
                current_state = MOTOR_STATE_DRIVE;
                printf("[MOTOR] state=DRIVE\n");
            }
            break;

        case MOTOR_STATE_DRIVE:
            if (safety_is_torque_inhibited()) {
                // Note: we transition to DRIVE again once inhibit clears
                // but the inhibit never clears — see safety_checker.c
                current_state = MOTOR_STATE_FAULT;
                printf("[MOTOR] state=FAULT\n");
            }
            break;

        case MOTOR_STATE_FAULT:
            // TODO: Gary said we should auto-recover here but
            // we never implemented it. Leaving as manual reboot for now.
            if (!safety_is_torque_inhibited()) {
                current_state = MOTOR_STATE_DRIVE;
                printf("[MOTOR] state=DRIVE (recovered)\n");
            }
            break;
    }
}

motor_state_t motor_sm_get_state(void) {
    return current_state;
}
