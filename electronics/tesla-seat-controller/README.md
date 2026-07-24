# Standalone Tesla seat controller

STM32G0-based controller for four seat motors, two ventilation fans, and the seat switchpack. Input is a regulated 12 V Mean Well power supply; record the exact model before system testing.

## Design status

The schematic passes ERC and the automated MCU pin-contract tests. The DRV8262s use KiCad's official top-PowerPAD DDV footprint:

`Package_SO:HTSSOP-44_6.1x14mm_P0.635mm_TopEP4.14x7.01mm`

Do not substitute the bottom-PowerPAD DDW footprint. The DDV thermal pad is on top and requires a heatsink for sustained high current.

## PCB requirements

- Put each driver's 10 nF VM capacitors directly at its VM/PGND pin groups.
- Put the VCP, CPH/CPL, DVDD, and VCC capacitors directly at their pins.
- Give both drivers short, wide, comparable +12 V and ground paths; do not feed one through the other.
- Preserve top-side clearance and mounting support for both DRV8262 heatsinks.
- Route motor and input current paths for the fused 10 A system current plus short peaks.
- Clearly label motor outputs A/B/C/D on silkscreen. XT30 polarity marks are not fixed electrical polarity on reversible motor outputs.
- Run DRC and a separate PCB audit before fabrication.

## Firmware safety contract

- DRV8262 hardware current regulation is about 14.6 A nominal; expected motor stall current is about 8 A.
- Monitor IPROPI and stop a motor when an 8 A-class stall persists beyond the chosen timeout.
- Use PWM-mode `00` to coast when stopping. Ramp down before reversing; do not reverse directly at full duty. This limits regeneration into the Mean Well supply.
- Treat nFAULT as latched: clear a fault with the datasheet-defined nSLEEP reset sequence.
- Fan outputs are open-drain and inverted. The Delta reference fan expects approximately 100 Hz PWM and stops near both duty-cycle extremes; validate against the actual seat fans.

## Validation

Run from the repository root:

```sh
kicad-cli sch erc --severity-all --format report \
  --output /tmp/tesla-seat-controller-erc.rpt \
  electronics/tesla-seat-controller/tesla-seat-controller.kicad_sch

python3 tests/test_pinmap.py
```

Before powering motors, verify the exact Mean Well model can supply the expected startup current. During first hardware tests, scope +12 V while stopping and reversing a loaded motor; add a braking clamp only if the rail rises excessively or the supply trips.
