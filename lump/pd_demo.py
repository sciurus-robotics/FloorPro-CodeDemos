"""Line following with the FloorPro's on-device PD controller over LUMP.

Robot: two motors (left Port.B counterclockwise, right Port.H), FloorPro on
Port.A, 56 mm wheels, 112 mm track. Run: pybricksdev run ble pd_demo.py

The sensor computes u = Kp*e + Kd*de/dt at 400 Hz; the hub only does
drive(SPEED, TURN_SIGN * u). set_gains() confirms the settings by reading them
back from the PDSET mode; the program then stays in the PD mode while driving.
"""
from pybricks.hubs import InventorHub
from pybricks.parameters import Direction, Port
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import StopWatch, run_task, wait

from floor_pro import FloorPro

SPEED = 200        # mm/s
KP = 40.0          # deg/s per pitch
KD = 0.0           # deg/s per pitch/s (start with P only)
TF_MS = 20
TURN_SIGN = -1     # flip if the robot steers away from the line
SECONDS = 15

hub = InventorHub()
left = Motor(Port.B, Direction.COUNTERCLOCKWISE)
right = Motor(Port.H)
drive_base = DriveBase(left, right, wheel_diameter=56, axle_track=112)
drive_base.use_gyro(False)
floor_pro = FloorPro(Port.A)


async def follow():
    if not floor_pro.has_pd():
        raise SystemExit("FloorPro firmware without PD modes (needs >= 0x3000000A)")
    await floor_pro.set_gains(KP, KD, tf_ms=TF_MS, src=0)   # PDSET and back
    await floor_pro.select(FloorPro.PD)                      # stay here while driving
    clock = StopWatch()
    while clock.time() < SECONDS * 1000:
        u, e, de, valid = await floor_pro.pd()
        drive_base.drive(SPEED, TURN_SIGN * u if valid else 0)
        await wait(10)
    drive_base.stop()


run_task(follow())
