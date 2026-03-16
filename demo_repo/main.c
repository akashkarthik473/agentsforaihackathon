// main.c
// Main periodic loop for the motor controller firmware.
// Runs all subsystem ticks at ~10ms intervals.
// Target: STM32F4 on custom inverter board (bench test build)

#include "can_manager.h"
#include "bms_interface.h"
#include "safety_checker.h"
#include "torque_controller.h"
#include "motor_state_machine.h"
#include <stdio.h>

// Simulated delay — replaced with HAL_Delay in production
void delay_ms(int ms);

int main(void) {
    printf("[MAIN] firmware starting\n");

    can_init();
    motor_sm_init();

    // Main control loop — 10ms tick
    while (1) {
        can_process_rx();
        bms_tick();
        safety_tick();
        motor_sm_tick();

        delay_ms(10);
    }

    return 0;
}

void delay_ms(int ms) {
    // stub for simulation
    (void)ms;
}
