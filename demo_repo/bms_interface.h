#ifndef BMS_INTERFACE_H
#define BMS_INTERFACE_H

#include <stdbool.h>

void bms_on_heartbeat_timeout(void);
void bms_on_heartbeat_received(void);
bool bms_is_heartbeat_present(void);
void bms_tick(void);

#endif
