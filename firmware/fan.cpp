
#include "fan.h"

#include <Arduino.h>

FanDriver::FanDriver(uint8_t pwm_pin) {
  this->pwm = pwm_pin;

  pinMode(pwm, OUTPUT);
  setSpeed(0);
}

/** Runs a motor at the provided speed until commanded to stop.
 * Speed should be between 0 and 255.
 */
void FanDriver::setSpeed(uint8_t speed) {
  if (speed != 0) {
    Serial.print("fan commanded");
    Serial.println();
  }

  analogWrite(pwm, speed);
}
