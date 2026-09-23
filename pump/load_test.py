"""Link load test: every FloorPro stream at its full rate, and how each one derates.

Run: scirodev run ble load_test.py   (sensor on Port.A; colour sensor on EXT1 and
gyro on EXT2 are included when present, with a warning when they are not)

Phase 1 measures each stream alone at PERIODIC / every sample (its solo rate).
Phase 2 switches all streams on at once (more than the 500 kbaud link can carry
with the IR streams at 400 Hz) and prints the hub's link counters once a second:
frames per second per stream, frames the hub never received (sequence gaps) and
decoder errors. The final table compares the loaded rate with the solo rate per
stream, which shows whether the derating is even. The default subscriptions are
restored at the end.
"""

from pybricks.tools import StopWatch, wait

from sciro.parameters import Port
from sciro.pump import FloorPro, PUMPDevice

SOLO_SECONDS = 2
LOAD_SECONDS = 10

floor_pro = FloorPro(Port.A)
dev = floor_pro.dev
streams = floor_pro.streams()

print("Device:", floor_pro.serial)
for sid, url, ext_port, n in streams:
    print("  stream", sid, url, "ext", ext_port, "state", dev.state(sid))
for name, get in (("colour sensor on EXT1", lambda: floor_pro.color_sensor(1)), ("gyro on EXT2", lambda: floor_pro.gyro(2))):
    try:
        get()
    except OSError:
        print("WARNING: no", name, "- its stream is not part of this run")


def short_name(url: str, ext_port: int) -> str:
    parts = url.rstrip("/").split("/")[:-1]  # drop the version
    name = parts[-1] if parts[-1] != "calib" else "-".join(parts[-2:])
    return name if ext_port == 0 else "%s@%d" % (name, ext_port)


names = {sid: short_name(url, ext_port) for sid, url, ext_port, n in streams}


def frames_by_stream(stats):
    return {sid: frames for sid, frames, gaps in stats["streams"]}


def gaps_by_stream(stats):
    return {sid: gaps for sid, frames, gaps in stats["streams"]}


def measure(seconds: int):
    """Frames per second per stream over `seconds`, plus decoder error count."""
    start = dev.stats()
    watch = StopWatch()
    wait(seconds * 1000)
    elapsed = watch.time() / 1000
    end = dev.stats()
    f0, f1 = frames_by_stream(start), frames_by_stream(end)
    rates = {sid: (f1[sid] - f0[sid]) / elapsed for sid in f0}
    errors = sum(end[k] - start[k] for k in ("crc_errors", "cobs_errors", "short_frames", "overflows"))
    return rates, errors


# --- Phase 1: each stream alone ------------------------------------------------
print("\nPhase 1: solo rates (%d s each)" % SOLO_SECONDS)
solo = {}
for sid, url, ext_port, n in streams:
    for other, _, _, _ in streams:
        dev.subscribe(other, PUMPDevice.PERIODIC if other == sid else PUMPDevice.OFF, 0)
    wait(500)  # let the echoes settle
    rates, errors = measure(SOLO_SECONDS)
    solo[sid] = rates[sid]
    print("  %-12s %6.1f frames/s%s" % (names[sid], solo[sid], "  (%d decoder errors)" % errors if errors else ""))

# --- Phase 2: everything on ----------------------------------------------------
print("\nPhase 2: all streams at full rate (%d s)" % LOAD_SECONDS)
for sid, url, ext_port, n in streams:
    dev.subscribe(sid, PUMPDevice.PERIODIC, 0)
wait(500)

# Lines are collected and printed at the end: printing over Bluetooth while
# measuring would itself stall the hub and show up as lost frames.
lines = []
last = dev.stats()
loaded_start = last
watch = StopWatch()
for second in range(LOAD_SECONDS):
    wait(1000)
    now = dev.stats()
    f0, f1 = frames_by_stream(last), frames_by_stream(now)
    g0, g1 = gaps_by_stream(last), gaps_by_stream(now)
    rates = ["%s:%d/s%s" % (names[sid], f1[sid] - f0[sid], "(-%d)" % (g1[sid] - g0[sid]) if g1[sid] != g0[sid] else "") for sid in f0]
    errors = "crc %d cobs %d short %d ovf %d" % (
        now["crc_errors"] - last["crc_errors"],
        now["cobs_errors"] - last["cobs_errors"],
        now["short_frames"] - last["short_frames"],
        now["overflows"] - last["overflows"],
    )
    lines.append("t=%2ds %s | %d frames/s | %s" % (second + 1, " ".join(rates), now["frames"] - last["frames"], errors))
    last = now
elapsed = watch.time() / 1000
for line in lines:
    print(line)

# --- Summary -------------------------------------------------------------------
f0, f1 = frames_by_stream(loaded_start), frames_by_stream(last)
g0, g1 = gaps_by_stream(loaded_start), gaps_by_stream(last)
print("\n%-12s %10s %10s %8s %6s" % ("stream", "solo Hz", "loaded Hz", "kept %", "lost"))
total = 0.0
for sid, url, ext_port, n in streams:
    loaded = (f1[sid] - f0[sid]) / elapsed
    total += loaded
    kept = 100 * loaded / solo[sid] if solo[sid] > 0 else 0
    print("%-12s %10.1f %10.1f %7.1f%% %6d" % (names[sid], solo[sid], loaded, kept, g1[sid] - g0[sid]))
print("%-12s %10s %10.1f" % ("total", "", total))

# Back to the defaults: line every sample, colour sensor on change, gyro 100 Hz,
# raw / calibration / display off.
for sid, url, ext_port, n in streams:
    if "/line/" in url:
        dev.subscribe(sid, PUMPDevice.PERIODIC, 0)
    elif "/tcs3400/" in url:
        dev.subscribe(sid, PUMPDevice.ON_CHANGE)
    elif "/imu/" in url:
        dev.subscribe(sid, PUMPDevice.PERIODIC, 100)
    else:
        dev.subscribe(sid, PUMPDevice.OFF)
print("done")
