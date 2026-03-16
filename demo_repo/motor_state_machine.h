#ifndef MOTOR_STATE_MACHINE_H
#define MOTOR_STATE_MACHINE_H

typedef enum {
    MOTOR_STATE_IDLE,
    MOTOR_STATE_DRIVE,
    MOTOR_STATE_FAULT
} motor_state_t;

void motor_sm_init(void);
void motor_sm_tick(void);
motor_state_t motor_sm_get_state(void);

#endif
