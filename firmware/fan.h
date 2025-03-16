#pragma once

#include <stdint.h>

class FanDriver {
 public:
  FanDriver(uint8_t pwm_pin);
  void setSpeed(uint8_t speed);

 protected:
  uint8_t pwm;
};
