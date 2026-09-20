"""Quality check: the calibrated range of each of the 15 IR sensors.

Run: scirodev run ble qc.py   (sensor on Port.A)

Reads the calibration table stored on the sensor (minimum and maximum raw 12-bit
reading per sensor) and prints the ranges. Small ranges point at a mounting
distance or surface that gives the sensor too little contrast.
"""

from pybricks.tools import run_task

from sciro.parameters import Port
from sciro.pump import FloorPro

floor_pro = FloorPro(Port.A)


async def qc():
    print("Device:", floor_pro.dev.info()["url"], "serial:", floor_pro.serial)

    mins, maxs, min_visited, max_visited = await floor_pro.ir_calib.oneshot()
    print("mins readings:", mins)
    print("maxs readings:", maxs)

    ranges = tuple(maxs[i] - mins[i] for i in range(15))
    print("ranges readings:", ranges)
    print("visited masks (min, max): %04x %04x" % (min_visited, max_visited))

    raw = await floor_pro.ir_raw.oneshot()
    print("current raw:", raw)


run_task(qc())
