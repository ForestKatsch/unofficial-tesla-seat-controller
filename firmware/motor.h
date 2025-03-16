
#pragma once

#include <stdint.h>

class MotorDriver {
 public:
  MotorDriver(uint8_t pwm_pin, uint8_t dir_pin);
  void setSpeed(int16_t speed);

 protected:
  uint8_t pwm;
  uint8_t dir;
};
