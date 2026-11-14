"""FloorPro on a LEGO hub: interactive demos, cycle with the LEFT/RIGHT buttons.

Run: pybricksdev run ble demo.py   (FloorPro on Port.A)

Modes are explicit: each demo selects the LUMP mode it needs once, then reads
in a loop. Reading a value of another mode without select() raises ModeError.
"""
from pybricks.hubs import InventorHub
from pybricks.parameters import Button, Port
from pybricks.tools import multitask, run_task, wait

from floor_pro import FloorPro, ModeError

hub = InventorHub()
floor_pro = FloorPro(Port.A)


def show_15(values_0_100):
    for row in range(5):
        for col in range(5):
            i = row * 5 + col
            hub.display.pixel(row, col, values_0_100[i] if i < 15 else 0)


async def demo_dark_centroid():
    print("dark_centroid(): centroid of dark pixels (-127..127), shown as a number")
    await floor_pro.select(FloorPro.DFLT)
    while True:
        hub.display.number(await floor_pro.dark_centroid())
        await wait(10)


async def demo_bright_centroid():
    print("bright_centroid(): centroid of bright pixels (-127..127)")
    await floor_pro.select(FloorPro.DFLT)
    while True:
        hub.display.number(await floor_pro.bright_centroid())
        await wait(10)


async def demo_brightness():
    print("brightness(): overall brightness (-127..127)")
    await floor_pro.select(FloorPro.DFLT)
    while True:
        hub.display.number(await floor_pro.brightness())
        await wait(10)


async def demo_line_sensors_binary():
    print("line_sensors_binary(): on/off per IR element on the 5x5 display")
    await floor_pro.select(FloorPro.DFLT)
    while True:
        show_15([100 if b else 0 for b in await floor_pro.line_sensors_binary()])
        await wait(10)


async def demo_line_sensors_analog():
    print("line_sensors_analog(): reflectance per IR element as grayscale (mode SCLD)")
    await floor_pro.select(FloorPro.SCLD)
    while True:
        show_15([(v + 127) * 100 // 254 for v in await floor_pro.line_sensors_analog()])
        await wait(10)


async def demo_pd():
    print("pd(): on-device PD controller output u (mode PD), shown as a number")
    if not floor_pro.has_pd():
        print("  this firmware has no PD modes (needs >= 0x3000000A)")
        await wait(1000)
        return
    await floor_pro.select(FloorPro.PD)
    while True:
        u, e, de, valid = await floor_pro.pd()
        hub.display.number(int(u) if valid else 0)
        await wait(10)


async def demo():
    print("Device info:", floor_pro.info())
    await floor_pro.select(FloorPro.DEVID)
    print("Device ID:", await floor_pro.device_id())
    await floor_pro.select(FloorPro.DFLT)
    print("Dark centroid:", await floor_pro.dark_centroid(), "bright:", await floor_pro.bright_centroid(),
          "brightness:", await floor_pro.brightness())
    try:
        await floor_pro.line_sensors_analog()  # needs SCLD: raises at once, nothing is sent
    except ModeError as e:
        print("Expected ModeError:", e)
    if floor_pro.has_pd():
        await floor_pro.set_gains(40.0, 0.0)   # switches to PDSET, confirms, switches back to DFLT
        await floor_pro.select(FloorPro.PDSET)
        print("PD gains (kp, kd, tf_ms, src):", await floor_pro.gains())
        await floor_pro.select(FloorPro.DFLT)

    await wait(1000)
    demos = [demo_dark_centroid, demo_bright_centroid, demo_brightness,
             demo_line_sensors_binary, demo_line_sensors_analog, demo_pd]
    index = 0
    direction = [1]

    async def wait_for_button():
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
