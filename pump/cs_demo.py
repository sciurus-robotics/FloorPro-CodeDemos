"""Colour sensor (TCS3400) on the FloorPro's extension port EXT1.

Run: scirodev run ble cs_demo.py   (sensor on Port.A, colour sensor on EXT1)

Prints the raw red / green / blue / clear readings at the sensor's resolution
and the colour as hue / saturation / value. RIGHT button cycles the
illumination LED through 0 / 25 / 100 %.
"""

from pybricks.tools import multitask, run_task, wait

from sciro.hubs import PeakHub
from sciro.parameters import Button, Port
from sciro.pump import FloorPro

hub = PeakHub()
floor_pro = FloorPro(Port.A)
color = floor_pro.color_sensor(1)


def rgb_to_hsv(r: float, g: float, b: float):
    mx = max(r, g, b)
    mn = min(r, g, b)
    v = mx
    if mx == 0:
        s = 0.0
    else:
        s = (mx - mn) / mx
    if mx == mn:
        h = 0.0
    else:
        if mx == r:
            h = (g - b) / (mx - mn)
        elif mx == g:
            h = 2.0 + (b - r) / (mx - mn)
        else:
            h = 4.0 + (r - g) / (mx - mn)
        h = (h / 6.0) % 1.0
    return h, s, v


async def print_cs_data():
    while True:
        r, g, b, c, status = await color.read()
        # Normalise by the clear channel so hue/saturation do not depend on
        # the illumination level; value is the clear reading relative to full scale.
        scale = c if c > 0 else 1
        h, s, _ = rgb_to_hsv(r / scale, g / scale, b / scale)
        v = c / 65535
        print("RGBC: %5d %5d %5d %5d status=0x%02x | HSV: %.2f %.2f %.3f" % (r, g, b, c, status, h, s, v))
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
