#pragma once

#include <stdint.h>

#define SWITCH_BACKREST_FORWARD (0b0001)
#define SWITCH_BACKREST_REARWARD (0b0010)
#define SWITCH_TRACK_FORE (0b0100)
#define SWITCH_TRACK_AFT (0b1000)

#define SWITCH_TILT_UP (0b0001)
#define SWITCH_TILT_DOWN (0b0010)
#define SWITCH_LIFT_UP (0b0100)
#define SWITCH_LIFT_DOWN (0b1000)

#define SWITCH_LUMBAR_FORE (0b0001)
#define SWITCH_LUMBAR_AFT (0b0010)
#define SWITCH_LUMBAR_UP (0b0100)
#define SWITCH_LUMBAR_DOWN (0b1000)

class SwitchPackWire {
public:
  SwitchPackWire(uint8_t pin);
  void read();

  uint8_t pressed = 0;
  uint8_t just_released = 0;

protected:
  uint8_t pin;
};
