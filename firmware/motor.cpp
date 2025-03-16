
#include "motor.h"

#include <Arduino.h>

MotorDriver::MotorDriver(uint8_t pwm_pin, uint8_t dir_pin) {
  this->dir = dir_pin;
  this->pwm = pwm_pin;

  pinMode(dir, OUTPUT);
  pinMode(pwm, OUTPUT);
  setSpeed(0);
}

/** Runs a motor at the provided speed until commanded to stop.
 * Speed should be between -255 and 255.
 */
void MotorDriver::setSpeed(int16_t speed) {
  if (speed > 255) {
    speed = 255;
  } else if (speed < -255) {
    speed = -255;
  }

  if (speed != 0) {
    Serial.print("motor commanded");
    Serial.println();
  }

  if (speed >= 0) {
    digitalWrite(dir, LOW);
    analogWrite(pwm, speed);
  } else {
    digitalWrite(dir, HIGH);
    analogWrite(pwm, -speed);
  }
}
