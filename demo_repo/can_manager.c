// can_manager.c
// Handles incoming CAN frames.
// Dispatches torque commands and BMS heartbeat signals.
// NOTE: message IDs are hardcoded for bench testing — do not ship as-is.

#include "can_manager.h"
#include "torque_controller.h"
#include "bms_interface.h"
#include <stdio.h>

#define CAN_ID_TORQUE_CMD   0x100
#define CAN_ID_BMS_HEARTBEAT 0x200

typedef struct {
    int id;
    int data;
} can_frame_t;

// Simulated RX buffer — in real firmware this comes from hardware FIFO
static can_frame_t rx_buffer[8];
static int rx_count = 0;

void can_init(void) {
    rx_count = 0;
    printf("[CAN] initialized\n");
}

void can_process_rx(void) {
    for (int i = 0; i < rx_count; i++) {
        can_frame_t f = rx_buffer[i];
        switch (f.id) {
            case CAN_ID_TORQUE_CMD:
                printf("[CAN] torque_cmd_rx requested=%d\n", f.data);
                torque_set_requested(f.data);
                break;
            case CAN_ID_BMS_HEARTBEAT:
                bms_on_heartbeat_received();
                break;
            default:
                // unknown frame, ignore
                break;
        }
    }
    rx_count = 0;
}
