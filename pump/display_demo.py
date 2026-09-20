"""Mirror the FloorPro's LED strip on the PeakHub's 5x5 display.

Run: scirodev run ble display_demo.py   (sensor on Port.A)

Rows 0-2 show the 15 IR sensors (green bar = bright, red dot = dark centre of
gravity, blue dot = bright centre of gravity; a rainbow while calibrating).
Bottom-left is extension port 2, bottom-right extension port 1, as on the sensor.
The matrix is much dimmer than the strip, so brightness above 100 amplifies.
"""

from pybricks.tools import wait

from sciro.hubs import PeakHub
from sciro.parameters import Port
from sciro.pump import FloorPro

hub = PeakHub()
floor_pro = FloorPro(Port.A)

hub.display.device(floor_pro, brightness=300)

while True:
    cog_dark, cog_bright, brightness, darkness, mask, calibrating = floor_pro.line.read()
    print("dark %.2f bright %.2f brightness %.2f%s" % (cog_dark, cog_bright, brightness, " (calibrating)" if calibrating else ""))
    wait(500)
