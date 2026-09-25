"""Interactive FloorPro demos on the PeakHub. Cycle with the LEFT/RIGHT hub buttons.

Run: scirodev run ble demo.py   (sensor on Port.A)
"""

from pybricks.tools import multitask, run_task, wait

from sciro.hubs import PeakHub
from sciro.parameters import Button, Port
from sciro.pump import FloorPro, PUMPDevice

hub = PeakHub()
floor_pro = FloorPro(Port.A)


def tenths(pitches: float) -> int:
    """A center of gravity in sensor pitches (-7 .. +7) as tenths, for the display."""
    return int(round(pitches * 10))


async def demo_dark_centroid():
    print("Method:      line.read()[0]")
    print("Description: Center of gravity of the dark regions, in tenths of a sensor pitch (-70 .. 70).")
    while True:
        cog_dark, _, _, _, _, _ = await floor_pro.line.read()
        hub.display.number(tenths(cog_dark))
        await wait(10)


async def demo_bright_centroid():
    print("Method:      line.read()[1]")
    print("Description: Center of gravity of the bright regions, in tenths of a sensor pitch (-70 .. 70).")
    while True:
        _, cog_bright, _, _, _, _ = await floor_pro.line.read()
        hub.display.number(tenths(cog_bright))
        await wait(10)


async def demo_brightness():
    print("Method:      line.read()[2]")
    print("Description: Overall brightness of the sensor (0 .. 100 %), displayed as a number.")
    while True:
        _, _, brightness, _, _, _ = await floor_pro.line.read()
        hub.display.number(int(brightness * 100))
        await wait(10)


async def demo_line_sensors_binary():
    print("Method:      line.read()[4]")
    print("Description: Bright/dark state of each of the 15 IR line sensors (a bit mask), shown on the 5x5 display.")
    while True:
        await wait(10)
        _, _, _, _, mask, _ = await floor_pro.line.read()
        for row in range(5):
            for col in range(5):
                index = row * 5 + col
                on = index < 15 and (mask >> index) & 1
                hub.display.pixel(row, col, 100 if on else 0)


async def demo_line_sensors_analog():
    print("Method:      ir_raw.read()")
    print("Description: Raw reflectance (12-bit ADC) of each of the 15 IR line sensors, shown as a grayscale pattern.")
    # The raw stream is off by default: ask for it at 20 Hz while this demo runs.
    await floor_pro.ir_raw.subscribe(PUMPDevice.PERIODIC, 20)
    try:
        while True:
            await wait(10)
            values = await floor_pro.ir_raw.read()
            for row in range(5):
                for col in range(5):
                    index = row * 5 + col
                    brightness = values[index] * 100 // 4095 if index < 15 else 0
                    hub.display.pixel(row, col, brightness)
    finally:
        # Cancelled by the race: no await is possible here, but the request is
        # sent right away and the hub keeps resending it until the sensor echoes.
        floor_pro.ir_raw.subscribe(PUMPDevice.OFF)


async def demo_display_mirror():
    print("Method:      hub.display.device(floor_pro)")
    print("Description: The sensor's own LED strip picture mirrored on the 5x5 display.")
    hub.display.device(floor_pro, brightness=300)
    try:
        while True:
            await wait(100)
    finally:
        hub.display.off()


async def demo():
    print("Device:", floor_pro.dev.info()["url"], "serial:", floor_pro.serial)
    print("Streams:", floor_pro.streams())
    print("Line:", await floor_pro.line.read())
    print("Raw:", await floor_pro.ir_raw.oneshot())

    await wait(1000)

    demos = [
        demo_dark_centroid,
        demo_bright_centroid,
        demo_brightness,
        demo_line_sensors_binary,
        demo_line_sensors_analog,
        demo_display_mirror,
    ]

    index = 0
    direction = [1]  # +1 = right/next, -1 = left/previous

    async def wait_for_button():
        # Wait for button release first to avoid immediately re-triggering
        while hub.buttons.pressed():
            await wait(50)
        while True:
            pressed = hub.buttons.pressed()
            if Button.RIGHT in pressed:
                direction[0] = 1
                return
            if Button.LEFT in pressed:
                direction[0] = -1
                return
            await wait(50)

    while True:
        print("\n--- Demo %d/%d ---" % (index + 1, len(demos)))
        hub.display.number(index + 1)
        await wait(500)
        await multitask(demos[index](), wait_for_button(), race=True)
        index = (index + direction[0]) % len(demos)


run_task(demo())
