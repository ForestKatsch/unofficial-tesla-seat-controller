"""Pin assignment contract for the standalone (shieldless) seat controller.

This is the single source of truth for how firmware is allowed to use the
STM32G0B1CBTx (LQFP-48, U1) on the standalone board. Values are hand-copied
from two authoritative sources:

  * net / pin assignments: electronics/tesla-seat-controller/tesla-seat-controller.kicad_sch
    (validated automatically against a fresh netlist export by test_pinmap.py)
  * timer / ADC capabilities: STM32G0B1xB/xC/xE datasheet DS13560 Rev 6,
    Tables 13-16 (alternate functions) and Table 12 (pin definitions)

Rules encoded here (enforced by test_pinmap.py):
  - every PWM signal must name a real (timer, channel, AF) that exists on
    that pin per the datasheet;
  - no timer channel may be claimed twice;
  - a channel and its complementary output (CHx vs CHxN) may not both be
    claimed - they are one output stage on advanced timers, not two PWMs;
  - ADC signals must name the correct ADC_INx channel for the pin;
  - ISNS inputs must sit on 5 V-tolerant (FT) pins because the DRV8262
    clamps IPROPI near VREF (~3.3 V) and overshoot must not kill the pin;
  - both inputs of one motor should share a timer (same counter -> identical
    frequency/phase). Motor C is a documented exception, see below.

Timer budget (firmware must configure all PWM timers to the same base
frequency where a motor spans two timers):
  TIM4  -> motor A (CH1/CH2) and motor B (CH3/CH4)
  TIM1  -> motor C low side (CH1) and motor D (CH2/CH3)  [advanced timer: set MOE]
  TIM14 -> motor C high side (CH1). PA7 has no plain TIM1 channel - its only
           TIM1 option is CH1N, the complement of PA8's CH1, so motor C is
           deliberately split across TIM1 + TIM14 (keep both at one frequency).
  TIM15 -> fan 1 (CH1)  [advanced-ish: set MOE]
  TIM3  -> fan 2 (CH3), frequency independent of all motor timers
"""

# role: 'pwm' | 'adc' | 'gpio_in' | 'gpio_out' | 'swd'
# pwm fields:  timer, ch, comp (True = complementary CHxN output), af
# adc fields:  adc_ch (ADC_INx)
PINMAP = {
    # DRV8262 U3 ("AB"), PWM inputs
    "A_IN1": dict(pin="PB6",  net="/A_IN1",  role="pwm", timer="TIM4",  ch=1, comp=False, af=9),
    "A_IN2": dict(pin="PB7",  net="/A_IN2",  role="pwm", timer="TIM4",  ch=2, comp=False, af=9),
    "B_IN1": dict(pin="PB8",  net="/B_IN1",  role="pwm", timer="TIM4",  ch=3, comp=False, af=9),
    "B_IN2": dict(pin="PB9",  net="/B_IN2",  role="pwm", timer="TIM4",  ch=4, comp=False, af=9),

    # DRV8262 U4 ("CD"), PWM inputs
    "C_IN1": dict(pin="PA7",  net="/C_IN1",  role="pwm", timer="TIM14", ch=1, comp=False, af=4),
    "C_IN2": dict(pin="PA8",  net="/C_IN2",  role="pwm", timer="TIM1",  ch=1, comp=False, af=2),
    "D_IN1": dict(pin="PA10", net="/D_IN1",  role="pwm", timer="TIM1",  ch=3, comp=False, af=2),
    "D_IN2": dict(pin="PB3",  net="/D_IN2",  role="pwm", timer="TIM1",  ch=2, comp=False, af=1),

    # Fan gate drives (2N7002 gates)
    "FAN1":  dict(pin="PB14", net="/FAN1",   role="pwm", timer="TIM15", ch=1, comp=False, af=5),
    "FAN2":  dict(pin="PB0",  net="/FAN2",   role="pwm", timer="TIM3",  ch=3, comp=False, af=1),

    # DRV8262 current sense (IPROPI, 212 mV/A with R_IPROPI = 1.00k)
    "A_ISNS": dict(pin="PA0", net="/A_ISNS", role="adc", adc_ch=0),
    "B_ISNS": dict(pin="PA1", net="/B_ISNS", role="adc", adc_ch=1),
    "C_ISNS": dict(pin="PA2", net="/C_ISNS", role="adc", adc_ch=2),
    "D_ISNS": dict(pin="PA3", net="/D_ISNS", role="adc", adc_ch=3),

    # Switchpack analog ladder inputs (1k pull-up to 3V3 on board)
    "SW_BACKREST_TRACK": dict(pin="PA4", net="/SW_BACKREST_TRACK", role="adc", adc_ch=4),
    "SW_TILT_LIFT":      dict(pin="PA5", net="/SW_TILT_LIFT",      role="adc", adc_ch=5),
    "SW_LUMBAR":         dict(pin="PA6", net="/SW_LUMBAR",         role="adc", adc_ch=6),

    # DRV8262 control / status
    "AB_SLEEP": dict(pin="PB4", net="/~{AB_SLEEP}", role="gpio_out"),
    "CD_SLEEP": dict(pin="PB5", net="/~{CD_SLEEP}", role="gpio_out"),
    "AB_FAULT": dict(pin="PC6", net="/~{AB_FAULT}", role="gpio_in"),   # open-drain, 10k pull-up on board
    "CD_FAULT": dict(pin="PC7", net="/~{CD_FAULT}", role="gpio_in"),   # open-drain, 10k pull-up on board

    # Debug
    "SWDIO": dict(pin="PA13", net="/SWDIO", role="swd"),
    "SWCLK": dict(pin="PA14", net="/SWCLK", role="swd"),
}

# Motor -> (high-side input, low-side input). Both pins must be PWM-capable;
# pairs listed in SPLIT_TIMER_OK are allowed to span two timers.
MOTOR_PAIRS = {
    "A": ("A_IN1", "A_IN2"),
    "B": ("B_IN1", "B_IN2"),
    "C": ("C_IN1", "C_IN2"),
    "D": ("D_IN1", "D_IN2"),
}
SPLIT_TIMER_OK = {"C"}  # PA7 has no non-complementary TIM1 channel (see module docstring)

# U1 nets that are intentionally not firmware signals.
NON_GPIO_NETS = {"+3V3", "GND", "/~{RESET}"}

# ---------------------------------------------------------------------------
# Datasheet reference data - STM32G0B1xB/xC/xE, DS13560 Rev 6.
# Only the pins this project uses are listed. (pin) -> {(timer, ch, comp): af}
# from Tables 13/14 (port A) and 15/16 (port B).
AF_PWM = {
    "PA7":  {("TIM3", 2, False): 1, ("TIM1", 1, True): 2, ("TIM14", 1, False): 4, ("TIM17", 1, False): 5},
    "PA8":  {("TIM1", 1, False): 2},
    "PA10": {("TIM1", 3, False): 2},
    "PB0":  {("TIM3", 3, False): 1, ("TIM1", 2, True): 2},
    "PB3":  {("TIM1", 2, False): 1, ("TIM2", 2, False): 2},
    "PB6":  {("TIM1", 3, False): 1, ("TIM16", 1, True): 2, ("TIM4", 1, False): 9},
    "PB7":  {("TIM17", 1, True): 2, ("TIM4", 2, False): 9},
    "PB8":  {("TIM16", 1, False): 2, ("TIM4", 3, False): 9},
    "PB9":  {("TIM17", 1, False): 2, ("TIM4", 4, False): 9},
    "PB14": {("TIM1", 2, True): 2, ("TIM15", 1, False): 5},
}

# ADC_INx channel per pin (Table 12).
ADC_CHANNELS = {
    "PA0": 0, "PA1": 1, "PA2": 2, "PA3": 3, "PA4": 4, "PA5": 5, "PA6": 6, "PA7": 7,
}

# I/O structure per pin (Table 12): FT* = 5 V tolerant, TT* = 3.6 V max.
IO_STRUCTURE = {
    "PA0": "FT_a", "PA1": "FT_ea", "PA2": "FT_a", "PA3": "FT_ea",
    "PA4": "TT_a", "PA5": "TT_ea", "PA6": "FT_ea", "PA7": "FT_a",
}

# Signals that must be on 5 V-tolerant pins (DRV8262 IPROPI clamps near
# VREF ~3.3 V; tolerance stack can exceed a TT pin's 3.6 V abs max margin).
REQUIRE_5V_TOLERANT = {"A_ISNS", "B_ISNS", "C_ISNS", "D_ISNS"}
