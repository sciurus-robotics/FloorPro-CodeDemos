"""Calibrate the FloorPro IR array from the hub: RIGHT starts, RIGHT stops.

Run: pybricksdev run ble calibration_demo.py   (FloorPro on Port.A)
Commands are sent in the selected mode (DFLT here); no mode switch happens.
"""
from pybricks.hubs import InventorHub
from pybricks.parameters import Button, Port
from pybricks.tools import run_task, wait

from floor_pro import FloorPro

hub = InventorHub()
floor_pro = FloorPro(Port.A)


async def wait_right():
    while Button.RIGHT not in hub.buttons.pressed():
        await wait(10)
    while Button.RIGHT in hub.buttons.pressed():
        await wait(10)


async def calibration_demo():
    await floor_pro.select(FloorPro.DFLT)
    print("Press RIGHT to start the calibration.")
    await wait_right()
    await floor_pro.send_cmd("CALIBSTART")
    print("Calibrating: move the sensor over the darkest and brightest areas of interest. RIGHT when done.")
    while Button.RIGHT not in hub.buttons.pressed():
        dark, bright, brightness, calibrating, _ = await floor_pro.all_sensor_data()
        print("dark=%4d bright=%4d calibrating=%s" % (dark, bright, calibrating))
        await wait(500)
    while Button.RIGHT in hub.buttons.pressed():
        await wait(10)
    await floor_pro.send_cmd("CALIBSTOP")
    print("Calibration stored on the sensor.")


run_task(calibration_demo())
