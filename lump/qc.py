"""Range / resolution check of the FloorPro's calibration (mode QC).

Run: pybricksdev run ble qc.py   (FloorPro on Port.A)
Prints per-channel min, max and range of the stored calibration.
"""
from pybricks.parameters import Port
from pybricks.tools import run_task, wait

from floor_pro import FloorPro

floor_pro = FloorPro(Port.A)


async def qc():
    await floor_pro.select(FloorPro.DEVID)
    print("Device ID:", await floor_pro.device_id())
    await floor_pro.select(FloorPro.QC)
    await floor_pro.send_cmd("QC=1")
    await wait(100)
    _, mins = await floor_pro.qc_values()
    await floor_pro.send_cmd("QC=2")
    await wait(100)
    _, maxs = await floor_pro.qc_values()
    print("mins:  ", mins)
    print("maxs:  ", maxs)
    print("ranges:", tuple(maxs[i] - mins[i] for i in range(15)))
    await floor_pro.send_cmd("QC=0")


run_task(qc())
