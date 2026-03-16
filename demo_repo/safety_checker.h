#ifndef SAFETY_CHECKER_H
#define SAFETY_CHECKER_H

#include <stdbool.h>

void safety_set_bms_timeout_fault(void);
bool safety_is_torque_inhibited(void);
void safety_tick(void);

#endif
