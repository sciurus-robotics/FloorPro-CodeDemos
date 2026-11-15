# FloorPro on LEGO hubs (Pybricks, LUMP)

Driver and demos for the FloorPro connected to a LEGO Prime / Inventor hub running
[Pybricks](https://pybricks.com). The sensor speaks the LEGO UART Message Protocol
(LUMP) there and is accessed through `pybricks.iodevices.PUPDevice`.

## Files

- `floor_pro.py` — `FloorPro` driver class (subclasses `PUPDevice`), explicit modes
- `demo.py` — interactive demos, cycle through with the LEFT/RIGHT hub buttons
- `calibration_demo.py` — calibrate the sensor from the hub (the button on the
  sensor does the same)
- `qc.py` — print the stored calibration's min/max/range per channel
- `pd_demo.py` — line following with the sensor's on-device PD controller

Run with [`pybricksdev`](https://github.com/pybricks/pybricksdev), e.g.
`pybricksdev run ble demo.py` from this folder (the driver module must sit next to
the script).

## Modes are explicit

A LUMP device is in one mode at a time and a switch costs about 40 ms. Pybricks
switches whenever a program reads another mode, so two values from different
modes in one loop would thrash the device. The driver therefore never switches
on its own:

```python
fp = FloorPro(Port.A)              # assumes DFLT; all methods are awaitable
await fp.dark_centroid()           # DFLT value: fine
await fp.line_sensors_analog()     # needs SCLD -> ModeError, nothing is sent
await fp.select(FloorPro.SCLD)
await fp.line_sensors_analog()     # fine
```

| mode | constant | methods |
|---|---|---|
| 0 | `DFLT` | `dark_centroid() bright_centroid() brightness() line_sensors_binary() all_sensor_data() ext_port_data(n)` |
| 1 | `SCLD` | `line_sensors_analog()` |
| 2 | `DEVID` | `device_id()` |
| 3 | `QC` | `qc_values()` with `send_cmd("QC=0|1|2")` |
| 4 | `PD` | `pd()` → `(u, e, de, valid)`, `pd_output()`, `pd_line()` |
| 5 | `PDSET` | `gains()`; written by `set_gains()` |

Commands (`send_cmd("CALIBSTART")`, `"CALIBSTOP"`, `"RATE=100|200|MAX|SYNC"`,
`"DISP=0..100"`, `"QC=n"`, `"LED1=0..100"`) go to the selected mode and never
switch it.

## PD line controller (firmware >= 0x3000000A)

The sensor computes `u = Kp*e + Kd*de/dt` at 400 Hz from the dark (or bright)
centroid `e` in sensor pitches. `set_gains(kp, kd=0, tf_ms=20, src=0)` writes the
settings into the `PDSET` mode and waits until the sensor reflects them (LUMP
has no reply channel, so this read-back is the acknowledgement), then returns to
the previously selected mode. Reading `pd()` requires `select(FloorPro.PD)`. Units
of `u` are "Kp per pitch": for a robot that drives `drive(speed, u)` Kp is
deg/s per pitch. `valid` only says the dark centroid has some mass (one dark
channel is enough); it is not a line detector, so combine it with the
brightness value and a threshold tuned on your track to decide "line lost". `pd_demo.py` shows the loop. Extension-sensor packs are only
in `DFLT`, so a program cannot read a color sensor and the PD output in one loop
without switching each time; pick one or accept the two switches.

## Pybricks compatibility

Works with Pybricks 3.6.1 and 4.0.0-b11 or later (earlier 4.x betas had
occasional disconnects, see pybricks/support#2698). When the hub is off but
charging, the sensor can stay powered; a hardware limitation.
