# Tesla seat controller, no shield

Grug board not Arduino shield.

Grug board has own brain. Brain is STM32. Board takes 12 V. Board makes 3.3 V. Board reads seat switches. Board drives four seat motors with two DRV8262 chips. Board drives two fans.

## Big parts

| Ref | Thing | What grug think it does | Datasheet PDF |
| --- | --- | --- | --- |
| `U1` | STM32G0B1CBTx | small brain, 3.3 V only | [STM32G0B1CB](https://www.st.com/resource/en/datasheet/stm32g0b1cb.pdf) |
| `U2` | AP63203WU | 12 V to 3.3 V buck | [AP63200/AP63201/AP63203/AP63205](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf) |
| `U3`, `U4` | DRV8262DDVR | dual H-bridge motor drivers, top thermal pad (heatsink), 10 A RMS / 16 A peak per output | [DRV8262](https://www.ti.com/lit/ds/symlink/drv8262.pdf) |
| `Q1` | IPD90P03P4L-04 | P-MOSFET reverse battery rock | [IPD90P03P4L-04](https://www.infineon.com/dgdl/Infineon-IPD90P03P4L-04-DataSheet-v01_01-EN.pdf?fileId=db3a30431ddc9372011e07e8373a27c4) |
| `Q2`, `Q3` | 2N7002 | fan PWM pull-down FETs | [2N7002](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf) |
| `D1` | BZT52C12 | 12 V zener (SOD-123), protects Q1 gate (Q1 V_GS max is +5/−16 V, so 12 V leaves margin) | [BZT52 series](https://assets.nexperia.com/documents/data-sheet/BZT52_SER.pdf) |
| `D2` | SMBJ16A | TVS on 12 V rail | [SMBJ series](https://www.vishay.com/docs/88392/smbj.pdf) |
| `J4` | TC2030 | SWD programming pokey thing | [TC2030-IDC-NL](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2019/12/TC2030-IDC-NL-Datasheet-Rev-B.pdf) |

## KiCad check

Grug used KiCad CLI, not raw file magic.

```sh
kicad-cli version
# 10.0.3

kicad-cli sch erc --format report --severity-all \
  --output audit-erc.rpt tesla-seat-controller.kicad_sch

kicad-cli sch export netlist --format kicadxml \
  --output audit-netlist-kicad.xml tesla-seat-controller.kicad_sch

kicad-cli sch export bom \
  --output audit-bom.csv tesla-seat-controller.kicad_sch
```

ERC says:

```text
0 errors, 0 warnings
```

Good. But ERC not know all pain.

## DRV8262 audit

Grug read TI PDF: `DRV8262`, SLVSFV5C, revised July 2025.

### Good rocks

`U3` and `U4` mostly look like dual motor driver use.

- `VM` pins go to `+12V`.
- `PGND`, `GND`, and thermal pad go to `GND`.
- `VCP` has cap to `VM`.
- `CPH`/`CPL` have 100 nF flying cap.
- `DVDD` has local caps.
- `VCC` tied to `DVDD`. Datasheet says ok when no other logic supply.
- `MODE1 = 0`, `MODE2 = DVDD`: dual H-bridge, PWM input mode.
- `IN1/IN2/IN3/IN4` go to STM32 pins.
- `nSLEEP` goes to STM32 and has pulldown.
- `nFAULT` is open-drain and pulled up to 3.3 V. Good.
- `DECAY = 0`: slow decay. Fine for brushed DC.
- `TOFF = 0`: 7 us off-time. Valid.
- `VREF1` and `VREF2` tied together per chip. Fine if both motors use same current limit.
- `IPROPI1` and `IPROPI2` each have 3.09 kΩ to ground. Good pattern.

### Bad rocks / fix before board

#### 1. Reserved pins are wrong

Datasheet says DRV8262 DDW reserved pins must be **left unconnected**.

Current netlist ties these to `GND`:

- `U3 pin 32`
- `U3 pin 36`
- `U4 pin 32`
- `U4 pin 36`

Fix: make those pins no-connect, not ground.

#### 2. Current limit math was wrong before

Old thinking used wrong gain. For DRV8262, datasheet example uses:

```text
AIPROPI = 212 uA/A typical
ITRIP = VREF / (RIPROPI * AIPROPI)
```

With current board (2026-07-17, DDV package, sized for max current):

```text
RIPROPI = 1.00 kΩ
VREF ≈ DVDD * 16.2k / (10k + 16.2k)
DVDD = 4.75..5.25 V  ->  VREF ≈ 2.94..3.25 V (3.09 V typ, always under 3.3 V max)
ITRIP ≈ 3.09 / (1000 * 212e-6)
ITRIP ≈ 14.6 A typical (13.3..16.0 A with DVDD + gain tolerance)
```

Why not ITRIP = 16 A exactly: DDV hard OCP minimum is **16 A** in dual H-bridge mode. ITRIP must stay under OCP worst-case, or driver latches off instead of chopping. 14.6 A typ is the most that never races OCP.

ADC scaling: 212 mV/A. RMS rating is still 10 A per output — 16 A is peak only, needs heatsink.

#### 3. OCPM meaning was backwards

Current board ties `OCPM` to `GND`.

Datasheet says:

- `OCPM = 0`: latch-off after overcurrent / overtemp. Need `nSLEEP` reset pulse or power cycle.
- `OCPM = 1`: automatic retry.

So current design is **latch-off**, not auto-retry. This may be good and safe, but firmware must know.

## Other board rocks

### Footprints missing

BOM says many parts still have no footprint. This is biggest not-ready-for-PCB thing.

Missing footprints include most passives, connectors, fuse, TVS, zener, P-MOSFET, and inductor.

Fix footprints before layout.

### Fan PWM maybe scary

Fan PWM line is pulled up to `+12V` through 100 kΩ and pulled down by 2N7002.

This makes fan see 0 V / 12 V PWM.

Maybe correct. Maybe smoke. Need fan datasheet or measure real fan input.

STM32 itself is safe because STM32 only touches 2N7002 gate at 3.3 V.

## BOM ordering notes (2026-07-17 footprint pass)

Board is DIY reflow: stencil (0.1 mm / 4 mil stainless), paste, oven. No exposed-pad parts anywhere. Connectors are all side-exit; hand-solder the XT30s after reflow.

- All 0805 caps (100 nF, 10 nF, 1 uF, 4.7 uF): buy **X7R 50 V** across the board — the 12 V rail can see ~26 V during TVS clamp, and one reel per value keeps the BOM short.
- `C3` 10 uF: 1206, **50 V** X7R. `C4`/`C5` 22 uF: 1206, 16–25 V X5R (3.3 V rail, DC bias is easy).
- `C17`/`C24` 220 uF 35 V polymer hybrid, 10 × 10.2 mm can, e.g. Panasonic **EEH-ZA1V221P**. Positive terminal (pin 1) is on `+12V`.
- All resistors 0805 1%. `R8`/`R9`/`R13`/`R14` (1.00 k IPROPI) matter for current-sense accuracy.
- `L1`: Bourns **SRN6045TA-3R9Y** (3.9 uH, shielded, Isat ~5 A).
- `F1`: Keystone **3568** mini-blade holder + 10 A mini blade fuse to start.
- Connectors: `J1` XT30PW-M (board input is male; source pigtail female), `J6`–`J9` XT30PW-F (board is live source), `J2`/`J3` JST **S3B-XH-A**, `J5` JST **S4B-XH-A** (all side-entry).

## Grug TODO

1. ~~Disconnect DRV8262 reserved pins~~ done (and moot — DDV package now, RSVD = 31/35, both NC).
2. ~~Decide current limit~~ done: ITRIP ≈ 14.6 A typ (max safe under 16 A OCP), RIPROPI = 1.00 kΩ.
3. ~~Lower VREF divider~~ done: 10k / 16.2k, worst-case 3.25 V < 3.3 V.
4. Decide if OCPM latch-off is intended. If yes, firmware pulses `nSLEEP` low 20–40 µs to recover.
5. Add missing footprints.
6. Re-run ERC.
7. Sync PCB.
8. Run DRC.
