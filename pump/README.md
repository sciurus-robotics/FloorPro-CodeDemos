# FloorPro on the PeakHub (PUMP)

Demos for the FloorPro connected to a PeakHub. The sensor speaks PUMP there and
is accessed through the `sciro.pump.FloorPro` class that is built into the
PeakHub firmware. No driver file is needed next to the scripts.

## Setup

```
pip install scirodev            # the scirodev command + the sciro API stubs
scirodev run ble demo.py        # runs a script on the hub over Bluetooth
```

`scirodev` is `pybricksdev` for the PeakHub; the `sciro` package makes your editor
understand `sciro.pump`, `sciro.hubs.PeakHub` and `Port.G`/`Port.H`.

## Files

- `demo.py` — Interactive demos, cycle with the LEFT/RIGHT hub buttons: dark and
  bright centre of gravity, brightness, the 15 sensors as binary and raw
  grayscale patterns on the 5x5 display, and the sensor's own LED picture
  mirrored on the display
- `calibration_demo.py` — Calibrate the IR array via software control (the
  sensor's own button works too)
- `qc.py` — Print the calibrated range of every sensor, to validate mounting
  distance and surface, or for quality control with a standardized setup
- `cs_demo.py` — Colour sensor on extension port 1: raw RGBC, HSV, LED control
- `display_demo.py` — Just the display mirror, as a minimal program

## API in one look

```python
from sciro.hubs import PeakHub
from sciro.parameters import Port
from sciro.pump import FloorPro

hub = PeakHub()
fp = FloorPro(Port.A)

cog_dark, cog_bright, brightness, darkness, mask, calibrating = fp.line.read()
raw = fp.ir_raw.oneshot()                 # 15 x 12-bit ADC counts
mins, maxs, _, _ = fp.ir_calib.oneshot()  # the stored calibration table
r, g, b, c, status = fp.color_sensor(1).read()
roll, pitch, yaw, status = fp.imu(2).read()
hub.display.device(fp, brightness=300)    # mirror the sensor's LED strip
```

Every reading method also works with `await` under `run_task` / `multitask`.
