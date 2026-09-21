# PUMP link load test

What happens when a program subscribes to more than the sensor's link can carry.
Measured with `load_test.py` on 2026-09-21: LP FloorPro (firmware of that date) on a
PeakHub port at 500 kbaud, colour sensor (TCS3400) on EXT1, IMU (BNO086) on EXT2.

The test first measures every stream alone at "every sample" (its solo rate), then
switches all six streams on at once for ten seconds and reads the hub's link
counters (`PUMPDevice.stats()`).

## Result

| stream | solo Hz | loaded Hz | kept | lost frames |
|---|---:|---:|---:|---:|
| line | 399 | 256 | 64 % | 0 |
| ir-raw | 399 | 256 | 64 % | 0 |
| ir-calib | 399 | 256 | 64 % | 0 |
| tcs3400@1 | 117 | 117 | 100 % | 0 |
| imu@2 | 100 | 100 | 100 % | 0 |
| display | 24 | 24 | 100 % | 0 |
| total | | 1008 frames/s | | |

Zero lost frames and zero decoder errors (CRC, COBS, short frames, overflows)
over the ten seconds.

## What it means

The requested load (three 400 Hz streams plus the rest) is more than the link
carries, so the sensor derates. It does so **asymmetrically, by design**: the
sensor's sender makes one pass over all subscribed streams and sends at most one
frame per stream per pass, always the latest sample. Each stream is therefore
delivered at the smaller of its own sample rate and the pass rate, which settled
at about 256 passes per second here. Streams sampling slower than that are
untouched; only the 400 Hz IR streams skip samples, evenly among themselves.
Nothing queues up, no stream starves, and no frame is lost on the wire.

In practice this is the right default: the slow channels (colour, IMU, the
display picture) are the ones where every sample carries information, while a
line sensor array read at 256 Hz instead of 400 Hz still tracks a line. If you
need a stream at its full rate under load, switch the others to a lower rate,
`ON_CHANGE`, or `OFF` with `PUMPDevice.subscribe()`.

Frames are only ever lost when the *hub* stalls its receive path for longer than
its buffer covers, about 5 ms at 500 kbaud. Printing over Bluetooth while
measuring is such a stall, which is why `load_test.py` collects its output and
prints it at the end.
