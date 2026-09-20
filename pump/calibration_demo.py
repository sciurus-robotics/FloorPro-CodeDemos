"""Calibrate the FloorPro's IR array from the PeakHub.

Run: scirodev run ble calibration_demo.py   (sensor on Port.A)

Calibration tracks each sensor's darkest and brightest reading while it is
active, so move the sensor over both the dark and the bright areas you care
about. The result is stored on the sensor when calibration stops. (The sensor's
own BOOT button toggles calibration too.)
"""

from pybricks.tools import run_task, wait

from sciro.hubs import PeakHub
from sciro.parameters import Button, Port
from sciro.pump import FloorPro

hub = PeakHub()
floor_pro = FloorPro(Port.A)


async def wait_for_right_button():
    while Button.RIGHT not in hub.buttons.pressed():
        await wait(10)
    while Button.RIGHT in hub.buttons.pressed():
        await wait(10)


async def calibration_demo():
    print("Starting calibration demo...")
    print("Press RIGHT button to start calibration.")
    await wait_for_right_button()
    await floor_pro.line.calibrate(True)
    print("Calibrating (line.read()[5] is", (await floor_pro.line.read())[5], ").")
    print("Move the sensor over the bright and dark areas of interest. Press RIGHT button again when done.")

    await wait_for_right_button()
    await floor_pro.line.calibrate(False)
    print("Calibration complete. Sensor data will now reflect the new calibration.")

    mins, maxs, _, _ = await floor_pro.ir_calib.oneshot()
    print("min:", mins)
    print("max:", maxs)


run_task(calibration_demo())
