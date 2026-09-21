"""Colour sensor (TCS3400) on extension port EXT1 of the FloorPro.

Run: scirodev run ble cs_demo.py   (FloorPro on Port.A, colour sensor on EXT1)

Prints the raw red / green / blue / clear readings, the colour as hue /
saturation / value, and the nearest detectable colour. RIGHT button cycles the
illumination LED through 25 / 100 / 0 %.
"""

from pybricks.tools import multitask, run_task, wait

from sciro.hubs import PeakHub
from sciro.parameters import Button, ExtPort, Port
from sciro.pump import ColorSensor

hub = PeakHub()
# The sensor is addressed by hub port and extension port; it does not matter
# whether a FloorPro or another PUMP device carries the extension port.
color: ColorSensor = ColorSensor(Port.A, ExtPort.EXT1)


async def print_cs_data():
    while True:
        r, g, b, c, status = await color.read()
        hsv = await color.hsv()
        nearest = await color.color()
        print("RGBC: %5d %5d %5d %5d status=0x%02x | h %3d s %3d v %3d | %s" % (r, g, b, c, status, hsv.h, hsv.s, hsv.v, nearest))
        await wait(250)


async def led_control():
    levels = [25, 100, 0]
    await color.set_light(levels[0])
    await color.set_gain(4)
    await color.set_integration(0xFD)
    print("Settings (led %, gain, atime):", color.settings())
    i = 0
    while True:
        while Button.RIGHT not in hub.buttons.pressed():
            await wait(10)
        while Button.RIGHT in hub.buttons.pressed():
            await wait(10)
        i = (i + 1) % len(levels)
        await color.set_light(levels[i])
        print("LED:", levels[i], "% -> settings", color.settings())


async def main():
    await multitask(led_control(), print_cs_data())


run_task(main())
