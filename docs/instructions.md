# Instructions

> [!NOTE]
> This project was built around a 2022 Model S (refresh) seat. While I have reason to believe this project will almost certainly work with all modern Tesla 12V seats (excluding Cybertruck), I cannot test or guarantee compatibility.

In addition to the parts required for the [PCB assembly](docs/pcba.md), you will also need:

- An Arduino Uno
- 2x [Cytron Arduino motor drivers](https://www.cytron.io/p-10amp-7v-30v-dc-motor-driver-shield-for-arduino-2-channels) (part number SHIELD-MDD10A; [datasheet](https://docs.google.com/document/d/1QHlQbs6f5fY_BMBs3hJRg1QLFe4yqy4nyH3mBavZ2-0/view))

You'll need some basic electronic tools to assemble the board and splice the seat wires.

## Seat controller shield

Once you have a PCB on hand, you can [proceed to assemble it](docs/pcba.md).

## Motor driver shield

You'll need to cut the 5V Output Solder Jumper on **only one of** the shields, to prevent both motor driver shields from attempting to drive the Vin shield pin. See the [datasheet](https://docs.google.com/document/d/1QHlQbs6f5fY_BMBs3hJRg1QLFe4yqy4nyH3mBavZ2-0/view) for more detail.

## Housing and cable management

TODO

## Mounting

I designed and 3D-printed standoffs that elevate my Model S (refresh) seat track rails above the built-in alignment pins. These will likely not work with other seats.

TODO