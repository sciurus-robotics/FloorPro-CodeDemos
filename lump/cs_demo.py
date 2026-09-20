from pybricks.tools import wait, run_task, multitask
from pybricks.hubs import PrimeHub, InventorHub
from pybricks.parameters import Port, Button
from floor_pro_v3 import FloorProV3

hub = InventorHub()
floor_pro = FloorProV3(Port.F)


def rgb_to_hsv(r, g, b):
    mx = max(r, g, b)
    mn = min(r, g, b)
    v = mx / 255.0
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


async def print_raw_data():
    while True:
        data = await floor_pro.safe_read(0)
        print("Mode 0 data:", end='')
        print(' '.join(f"{b:04d}" for b in data))
        await wait(1000)


async def print_cs_data():
    while True:
        data = (await floor_pro.safe_read(0))[11:15]
        # Map from int8 to uint8
        data = [(b + 256) % 256 for b in data]
        r, g, b, c = data
        print("CS data:", end='')
        print(' '.join(f"{b:04d}" for b in data), end='')
        h, s, v = rgb_to_hsv(r, g, b)
        print(f" | HSV: {h:.2f} {s:.2f} {v:.2f}")

        await wait(250)


async def calib():
    await floor_pro.send_cmd("LED2=25")
    await floor_pro.send_cmd("AGAIN2=4x")
    await floor_pro.send_cmd(f"ATIME2={0xFD:0d}")

    while True:
        print("Press RIGHT button to start calibration.")
        while Button.RIGHT not in hub.buttons.pressed():
            await wait(10)
        while Button.RIGHT in hub.buttons.pressed():
            await wait(10)
        await floor_pro.send_cmd("TCSCALIBSTART")
        print("Calibrating... Press RIGHT button again when done.")

        while Button.RIGHT not in hub.buttons.pressed():
            await wait(10)
        while Button.RIGHT in hub.buttons.pressed():
            await wait(10)
        await floor_pro.send_cmd("TCSCALIBEND")


run_task(multitask(calib(), print_raw_data(), print_cs_data()))
