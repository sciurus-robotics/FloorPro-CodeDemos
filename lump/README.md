# FloorPro on LEGO hubs (Pybricks, LUMP)

Driver and demos for the FloorPro connected to a LEGO Prime / Inventor hub running
[Pybricks](https://pybricks.com). The sensor speaks LEGO's UART sensor protocol
(LUMP) there and is accessed through `pybricks.iodevices.PUPDevice`.

## Files

- `floor_pro_v3.py` — `FloorProV3` driver class (subclasses `PUPDevice`)
- `demo.py` — Interactive demos, cycle through with the left/right hub buttons
- `calibration_demo.py` — Calibrate the sensor via software control (you can also
  calibrate via the physical button on the sensor)
- `qc.py` — Check the range/resolution of the sensor with respect to calibrated
  values. This can be used to validate operation of the current setup, in
  particular with respect to mounting distance and surface properties. It can also
  be used for quality control with a standardized setup.
- `cs_demo.py` — BETA: colour sensor on an extension port (raw RGBC over LUMP mode 0)

Run with [`pybricksdev`](https://github.com/pybricks/pybricksdev), e.g.
`pybricksdev run ble demo.py` from this folder (the driver module must sit next to
the script).

## Pybricks Compatibility

**The sensor is known to work with the latest stable version 3.6.1 of Pybricks.**
When you turn off the hub, we observed that the sensor can remain powered if the
hub is connected and charging. That is a shortcoming of the hardware and could be
fixed in the firmware, but that seems not to be the case in 3.6.x.

In the development version of Pybricks 4.x there is an issue with occasional
disconnects. The issue will be resolved with versions 4.0.0-b11 and later, see
https://github.com/pybricks/support/issues/2698.
