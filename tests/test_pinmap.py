#!/usr/bin/env python3
"""Validate tests/pinmap.py against the schematic and the STM32G0B1 datasheet facts.

Usage:
    python3 tests/test_pinmap.py

Exit code 0 = all checks passed. Anything else = the pin plan is broken.

What is checked:
  1. netlist:      every pinmap entry matches a fresh `kicad-cli sch export
                   netlist` of the schematic (net name <-> MCU pin), and every
                   U1 net in the schematic is covered by the pinmap. Requires
                   kicad-cli on PATH; set PINMAP_SKIP_NETLIST=1 to skip (the
                   run then FAILS at the end unless explicitly allowed, so CI
                   can't silently lose the schematic cross-check).
  2. capabilities: every PWM claim (timer/channel/AF) exists on that pin and
                   every ADC claim names the right ADC_INx, per DS13560 Rev 6.
  3. conflicts:    no pin used twice, no timer channel double-booked, no
                   CHx + CHxN complementary pair claimed as two outputs.
  4. pairing:      each motor's two inputs are PWM-capable and share a timer
                   unless the pair is a documented exception.
  5. tolerance:    ISNS inputs sit on 5 V-tolerant (FT) pins.
  6. self-test:    the checkers are run against deliberately corrupted pinmaps
                   and must catch every seeded error, proving the tests can
                   actually fail.
"""

import copy
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinmap as PM

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMATIC = os.path.join(REPO, "electronics", "tesla-seat-controller", "tesla-seat-controller.kicad_sch")
MCU_REF = "U1"


# --------------------------------------------------------------------------- helpers

def export_netlist():
    """Return {net_name: set((ref, pin_name))} from a fresh kicad-cli export."""
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "netlist.xml")
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "--output", out, SCHEMATIC],
            check=True, capture_output=True,
        )
        root = ET.parse(out).getroot()
    pin_names = {}
    for lp in root.iter("libpart"):
        for p in lp.iter("pin"):
            pin_names[(lp.get("part"), p.get("num"))] = p.get("name")
    part_of = {c.get("ref"): c.find("libsource").get("part") for c in root.iter("comp")}
    nets = {}
    for net in root.iter("net"):
        nodes = set()
        for n in net.iter("node"):
            ref, num = n.get("ref"), n.get("pin")
            nodes.add((ref, pin_names.get((part_of[ref], num), num)))
        nets[net.get("name")] = nodes
    return nets


# --------------------------------------------------------------------------- checks
# Each check returns a list of error strings (empty = pass) so the self-test
# can run them against corrupted pinmaps.

def pin_matches(want, netlist_name):
    """KiCad symbol pin names can be compound ('PA10/UCPD1_DBCC2')."""
    return want == netlist_name or want in netlist_name.split("/")


def check_netlist(pm, nets):
    errors = []
    for sig, d in pm.items():
        if d["net"] not in nets:
            errors.append(f"{sig}: net {d['net']!r} does not exist in the schematic")
        elif not any(r == MCU_REF and pin_matches(d["pin"], n) for r, n in nets[d["net"]]):
            actual = sorted(n for r, n in nets[d["net"]] if r == MCU_REF) or "no U1 pin at all"
            errors.append(f"{sig}: expected {MCU_REF} pin {d['pin']} on net {d['net']!r}, schematic has {actual}")
    # completeness: every named U1 net must be claimed by the pinmap
    claimed = {d["net"] for d in pm.values()} | PM.NON_GPIO_NETS
    for net, nodes in nets.items():
        if net.startswith("unconnected-"):
            continue
        if any(r == MCU_REF for r, _ in nodes) and net not in claimed:
            errors.append(f"schematic connects {MCU_REF} to net {net!r} but pinmap does not claim it")
    return errors


def check_capabilities(pm):
    errors = []
    for sig, d in pm.items():
        if d["role"] == "pwm":
            key = (d["timer"], d["ch"], d["comp"])
            options = PM.AF_PWM.get(d["pin"], {})
            if key not in options:
                errors.append(
                    f"{sig}: {d['pin']} has no {d['timer']}_CH{d['ch']}{'N' if d['comp'] else ''}"
                    f" (datasheet options: {sorted(options)})")
            elif options[key] != d["af"]:
                errors.append(f"{sig}: {d['pin']} {d['timer']}_CH{d['ch']} is AF{options[key]}, pinmap claims AF{d['af']}")
        elif d["role"] == "adc":
            want = PM.ADC_CHANNELS.get(d["pin"])
            if want is None:
                errors.append(f"{sig}: {d['pin']} is not an ADC pin")
            elif want != d["adc_ch"]:
                errors.append(f"{sig}: {d['pin']} is ADC_IN{want}, pinmap claims ADC_IN{d['adc_ch']}")
    return errors


def check_conflicts(pm):
    errors = []
    pins, channels = {}, {}
    for sig, d in pm.items():
        if d["pin"] in pins:
            errors.append(f"pin {d['pin']} claimed by both {pins[d['pin']]} and {sig}")
        pins[d["pin"]] = sig
        if d["role"] == "pwm":
            key = (d["timer"], d["ch"], d["comp"])
            if key in channels:
                errors.append(f"{d['timer']}_CH{d['ch']}{'N' if d['comp'] else ''} claimed by both {channels[key]} and {sig}")
            channels[key] = sig
    # CHx and CHxN are one output stage: claiming both as independent PWMs is a conflict
    for (timer, ch, comp), sig in channels.items():
        twin = channels.get((timer, ch, not comp))
        if twin and not comp:  # report each pair once
            errors.append(
                f"complementary conflict: {sig} uses {timer}_CH{ch} while {twin} uses {timer}_CH{ch}N"
                " - these are the same output stage")
    return errors


def check_motor_pairs(pm):
    errors = []
    for motor, (hi, lo) in PM.MOTOR_PAIRS.items():
        for sig in (hi, lo):
            if sig not in pm:
                errors.append(f"motor {motor}: signal {sig} missing from pinmap")
            elif pm[sig]["role"] != "pwm":
                errors.append(f"motor {motor}: {sig} is not a PWM signal")
        if all(s in pm and pm[s]["role"] == "pwm" for s in (hi, lo)):
            if pm[hi]["timer"] != pm[lo]["timer"] and motor not in PM.SPLIT_TIMER_OK:
                errors.append(
                    f"motor {motor}: {hi} on {pm[hi]['timer']} but {lo} on {pm[lo]['timer']}"
                    " (not a documented split-timer exception)")
    return errors


def check_5v_tolerance(pm):
    errors = []
    for sig in PM.REQUIRE_5V_TOLERANT:
        d = pm.get(sig)
        if d is None:
            errors.append(f"{sig}: required 5V-tolerant signal missing from pinmap")
            continue
        structure = PM.IO_STRUCTURE.get(d["pin"], "?")
        if not structure.startswith("FT"):
            errors.append(f"{sig}: {d['pin']} is {structure} (3.6 V max), needs an FT (5 V-tolerant) pin")
    return errors


# --------------------------------------------------------------------------- self-test

def self_test():
    """Seed known-bad pinmaps; every corruption must be detected."""
    failures = []

    def expect(name, checker, mutate):
        pm = copy.deepcopy(PM.PINMAP)
        mutate(pm)
        if not checker(pm):
            failures.append(f"self-test {name!r}: corruption was NOT detected")

    def fake_nets():
        nets = {d["net"]: {(MCU_REF, d["pin"])} for d in PM.PINMAP.values()}
        nets.update({n: set() for n in PM.NON_GPIO_NETS})
        return nets

    expect("swapped pins", lambda pm: check_netlist(pm, fake_nets()),
           lambda pm: (pm["A_IN1"].update(pin="PB7"), pm["A_IN2"].update(pin="PB6")))
    expect("wrong net", lambda pm: check_netlist(pm, fake_nets()),
           lambda pm: pm["FAN1"].update(net="/FAN2_TYPO"))
    expect("double-booked channel", check_conflicts,
           lambda pm: pm["C_IN1"].update(timer="TIM1", ch=1, comp=False, af=2))
    expect("CHx/CHxN conflict", check_conflicts,
           lambda pm: pm["FAN2"].update(timer="TIM1", ch=2, comp=True, af=2))
    expect("nonexistent timer on pin", check_capabilities,
           lambda pm: pm["FAN2"].update(timer="TIM4", ch=1, comp=False, af=9))
    expect("wrong AF number", check_capabilities,
           lambda pm: pm["A_IN1"].update(af=1))
    expect("wrong ADC channel", check_capabilities,
           lambda pm: pm["A_ISNS"].update(adc_ch=5))
    expect("split-timer pair", check_motor_pairs,
           lambda pm: pm["A_IN2"].update(timer="TIM3", ch=1, comp=False, af=1))
    expect("ISNS on TT pin", check_5v_tolerance,
           lambda pm: pm["A_ISNS"].update(pin="PA4"))
    return failures


# --------------------------------------------------------------------------- main

def main():
    failed = False

    def report(name, errors):
        nonlocal failed
        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {name}")
        for e in errors:
            print(f"       - {e}")
        failed = failed or bool(errors)

    if os.environ.get("PINMAP_SKIP_NETLIST") == "1":
        report("netlist cross-check", ["SKIPPED via PINMAP_SKIP_NETLIST=1 - schematic was NOT verified"])
    else:
        try:
            nets = export_netlist()
        except FileNotFoundError:
            report("netlist cross-check", ["kicad-cli not found on PATH (install KiCad CLI, or set PINMAP_SKIP_NETLIST=1 to run the other checks)"])
        except subprocess.CalledProcessError as e:
            report("netlist cross-check", [f"kicad-cli failed: {e.stderr.decode(errors='replace').strip()[:500]}"])
        else:
            report("netlist cross-check", check_netlist(PM.PINMAP, nets))

    report("datasheet capabilities (PWM AF / ADC channels)", check_capabilities(PM.PINMAP))
    report("conflicts (pins, timer channels, CHx/CHxN)", check_conflicts(PM.PINMAP))
    report("motor pair timer allocation", check_motor_pairs(PM.PINMAP))
    report("5 V tolerance of ISNS inputs", check_5v_tolerance(PM.PINMAP))
    report("self-test (seeded errors are detected)", self_test())

    print("\n" + ("FAILED - pin plan is broken, do not trust firmware assumptions" if failed else "OK - pinmap, schematic, and datasheet all agree"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
