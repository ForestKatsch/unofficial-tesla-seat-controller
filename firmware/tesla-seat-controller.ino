
#define DEBUG (1)

#include "motor.h"
#include "switch.h"
#include "fan.h"

MotorDriver motor_backrest(3, 2);
MotorDriver motor_lift(10, 12);
MotorDriver motor_track(9, 8);
MotorDriver motor_tilt(11, 13);

SwitchPackWire track_backrest(A2);
SwitchPackWire lift_tilt(A3);
SwitchPackWire lumbar(A4);

FanDriver fan_lower(11);
FanDriver fan_upper(12);

// Fan global speed control

#define FAN_SPEED_OFF (0)
#define FAN_SPEED_LOW (1)
#define FAN_SPEED_MED (2)
#define FAN_SPEED_HIGH (3)

#define FAN_SPEED_MIN FAN_SPEED_OFF
#define FAN_SPEED_MAX FAN_SPEED_HIGH

int8_t fan_setting = FAN_SPEED_OFF;

void fanSpeedOffset(int8_t by) {
  // Bounds check.
  if (fan_setting == FAN_SPEED_MIN && by < 0) {
    return;
  } else if (fan_setting == FAN_SPEED_MAX && by > 0) {
    return;
  }

  fan_setting += by;
}

const uint8_t fan_pwm[FAN_SPEED_MAX + 1] = {0, 72, 128, 255};

// Helpers

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

void runFans() {
  fan_lower.setSpeed(fan_pwm[fan_setting]);
  fan_upper.setSpeed(fan_pwm[fan_setting]);
}

// Setup + loop

void setup() {
#if DEBUG
  delay(500);
  Serial.begin(9600);

  Serial.print("Logs working");
  Serial.println();
#endif
}

// the loop function runs over and over again forever
void loop() {
  delay(10);

  readSwitches();
  runMotors();

  if (lumbar_up.just_released) {
    fanSpeedOffset(1);
  } else if(lumbar_down.just_released) {
    fanSpeedOffset(-1);
  }

  runFans();
}
