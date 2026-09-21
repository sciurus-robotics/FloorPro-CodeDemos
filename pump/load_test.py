"""Link load test: subscribe every FloorPro stream at its full rate.

Run: scirodev run ble load_test.py   (sensor on Port.A)

All streams are switched to PERIODIC / every sample (the IR streams run at
400 Hz, so this asks for more than the 500 kbaud link can carry) and the hub's
link counters are printed once a second: frames per second per stream, frames
the hub never received (sequence gaps) and decoder errors. Afterwards the
default subscriptions are restored.
"""

from pybricks.tools import wait

from sciro.parameters import Port
from sciro.pump import FloorPro, PUMPDevice

SECONDS = 10

floor_pro = FloorPro(Port.A)
dev = floor_pro.dev
streams = floor_pro.streams()

print("Device:", floor_pro.serial)
for sid, url, ext_port, n in streams:
    print("  stream", sid, url, "state", dev.state(sid))

# Everything on, at the device's maximum rate.
for sid, url, ext_port, n in streams:
    dev.subscribe(sid, PUMPDevice.PERIODIC, 0)
wait(500)  # let the echoes settle before counting

# Lines are collected and printed at the end: printing over Bluetooth while
# measuring would itself stall the hub and show up as lost frames.
lines = []
last = dev.stats()
for second in range(SECONDS):
    wait(1000)
    now = dev.stats()
    rates = []
    for (sid, frames, gaps), (_, last_frames, last_gaps) in zip(now["streams"], last["streams"]):
        rates.append("%d:%d/s" % (sid, frames - last_frames) + ("(-%d)" % (gaps - last_gaps) if gaps != last_gaps else ""))
    errors = "crc %d cobs %d short %d ovf %d" % (
        now["crc_errors"] - last["crc_errors"],
        now["cobs_errors"] - last["cobs_errors"],
        now["short_frames"] - last["short_frames"],
        now["overflows"] - last["overflows"],
    )
    lines.append("t=%2ds %s | %d frames/s | %s" % (second + 1, " ".join(rates), now["frames"] - last["frames"], errors))
    last = now
for line in lines:
    print(line)

# Back to the defaults: line every sample, colour sensor on change, IMU 100 Hz,
# raw / calibration / display off.
for sid, url, ext_port, n in streams:
    if "/line/" in url:
        dev.subscribe(sid, PUMPDevice.PERIODIC, 0)
    elif "/tcs3400/" in url:
        dev.subscribe(sid, PUMPDevice.ON_CHANGE)
    elif "/imu/" in url:
        dev.subscribe(sid, PUMPDevice.PERIODIC, 10)
    else:
        dev.subscribe(sid, PUMPDevice.OFF)
print("done")
