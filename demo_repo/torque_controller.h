#ifndef TORQUE_CONTROLLER_H
#define TORQUE_CONTROLLER_H

int torque_compute_applied(int requested_nm);
void torque_set_requested(int nm);
int torque_get_applied(void);

#endif
