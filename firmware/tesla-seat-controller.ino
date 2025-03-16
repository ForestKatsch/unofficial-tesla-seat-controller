
#define DEBUG (1)

#include "motor.h"
#include "switch.h"
#include "fan.h"

MotorDriver motor_backrest(3, 2);
MotorDriver motor_lift(10, 12);
MotorDriver motor_track(9, 8);
MotorDriver motor_tilt(11, 13);

SwitchPackWire lumbar(A2);
SwitchPackWire track_backrest(A3);
SwitchPackWire lift_tilt(A4);

FanDriver fan_lower();

/////////
// FANS

/*
void runFan(uint8_t pin_pwm, uint8_t speed) { analogWrite(pin_pwm, speed); }

void setupFan(uint8_t pin_pwm) {
  pinMode(pin_pwm, OUTPUT);
  runFan(pin_pwm, 0);
}

void setupFans() {
  setupFan(PIN_FAN_UPPER_PWM);
  setupFan(PIN_FAN_LOWER_PWM);
}

#define FAN_SPEED_OFF (0)
#define FAN_SPEED_LOW (1)
#define FAN_SPEED_MED (2)
#define FAN_SPEED_HIGH (3)

#define FAN_SPEED_MIN FAN_SPEED_OFF
#define FAN_SPEED_MAX FAN_SPEED_HIGH

int8_t fanSpeed = FAN_SPEED_OFF;

void fanSpeedOffset(int8_t by) {
  if (fanSpeed == FAN_SPEED_MIN && by < 0) {
    return;
  } else if (fanSpeed == FAN_SPEED_MAX && by > 0) {
    return;
  }

  fanSpeed += by;
}

const uint8_t fan_pwm[FAN_SPEED_MAX + 1] = {0, 72, 128, 255};
*/

void readSwitches() {
  lift_tilt.read();
  track_backrest.read();
  lumbar.read();
}

void runMotors() {
  motor_backrest.setSpeed(track_backrest.pressed & SWITCH_BACKREST_FORWARD ? 255
                          : track_backrest.pressed & SWITCH_BACKREST_REARWARD
                              ? -255
                              : 0);
  motor_tilt.setSpeed(lift_tilt.pressed & SWITCH_TILT_DOWN ? 255
                      : lift_tilt.pressed & SWITCH_TILT_UP ? -255
                                                           : 0);
  motor_lift.setSpeed(lift_tilt.pressed & SWITCH_LIFT_DOWN ? 255
                      : lift_tilt.pressed & SWITCH_LIFT_UP ? -255
                                                           : 0);
  motor_track.setSpeed(track_backrest.pressed & SWITCH_TRACK_FORE  ? 255
                       : track_backrest.pressed & SWITCH_TRACK_AFT ? -255
                                                                   : 0);
}

// the setup function runs once when you press reset or power the board
void setup() {
#if DEBUG
  delay(500);
  Serial.begin(9600);

  Serial.print("Logs working");
  Serial.println();
#endif
  // setupMotors();
  // setupFans();
  // setupSwitches();
}

// the loop function runs over and over again forever
void loop() {
  delay(10);

  readSwitches();
  runMotors();

  /*
    if (lumbar_up.just_released) {
      fanSpeedOffset(1);
    } else if(lumbar_down.just_released) {
      fanSpeedOffset(-1);
    }

    // runMotors();
    runFans();
    */
}
