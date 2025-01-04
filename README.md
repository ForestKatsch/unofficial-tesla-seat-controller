# (unofficial) Tesla seat controller

This project contains everything necessary to build an Arduino shield that reads the seat controls and drives the seat motors and ventilation fans.

## Why?

I built a simracing rig, and I discovered that used Tesla seats in good condition were around the same price as purpose-built simracing seats, and are much more comfortable to boot. The only problem is that they're electrically actuated and can't be manually adjusted.

## How?

- [**Instructions**](docs/) (start here)
- [Switchpack](docs/switchpack.md)
- [PCB assembly and BOM](docs/pcba.md)

## Changelog

| date       | change                                               |
| ---------- | ---------------------------------------------------- |
| 2025.01.04 | documentation consolidation and prep work for proto1 |
| 2024.08.18 | proto0 / validation                                  |

## References and sources

- [Dan Simma's video](https://www.youtube.com/watch?v=71O_Hcep4HI) convinced me this project was doable
- [Tesla's Model S electrical schematics](https://service.tesla.com/docs/ModelS/ElectricalReference/prog-54/interactive/html/index.html?page=62&) made it easy to find out which wires went where
- [A Delta PWM fan, very similar to the ventilation fans in the seat](https://www.delta-fan.com/applications/automotive/BFB1012HD-04D4L.html)

## License

TODO