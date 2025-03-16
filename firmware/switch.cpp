#include "switch.h"

#include <Arduino.h>

#include "switchpack_states.h"

SwitchPackWire::SwitchPackWire(uint8_t pin) { this->pin = pin; }

void SwitchPackWire::read() {
  int value = analogRead(pin);
  uint8_t current = switchpack_states[value];

  just_released = pressed & ~current;
  pressed = current;
}
