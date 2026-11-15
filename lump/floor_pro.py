"""FloorPro on a LEGO hub (Pybricks), read over LUMP with explicit modes.

The FloorPro announces six LUMP modes. A LUMP device is in exactly one mode at
a time, a mode switch costs about 40 ms, and Pybricks switches implicitly on
every ``PUPDevice.read(mode)``. Two methods that need different modes in one
loop would therefore switch back and forth on every call and interfere with
each other (and with a second driver object on the same port). This driver
makes the mode explicit instead:

* ``select(mode)`` is the only call that switches the device;
* every data method states the mode it needs and raises :class:`ModeError`
  at once, before any I/O, when another mode is selected;
* commands (``send_cmd``) are written to the selected mode and never switch;
* ``set_gains()`` is the one compound operation: it switches to ``PDSET``,
  writes, waits until the device reflects the new settings, and switches back.

Modes (FloorPro firmware >= 0x3000000A):

====  =======  =====================================================
mode  name     data
====  =======  =====================================================
0     DFLT     status, dark/bright centroid, brightness, bitmasks, EXT1/EXT2 packs
1     SCLD     status, 15 scaled sensor values
2     DEVID    8-char short device id
3     QC       selector + 15 x uint16 (raw / min / max)
4     PD       line bytes as DFLT + PD controller output (u, e, de/dt, valid)
5     PDSET    PD settings Kp, Kd, Tf, src (writable, reflects what is in force)
====  =======  =====================================================
"""

from pybricks.iodevices import PUPDevice
from pybricks.tools import wait


class ModeError(Exception):
    """A method needs a LUMP mode that is not the selected one. Call
    ``select()`` first; nothing was sent to the device."""


def _i16(lo, hi):
    v = (lo & 0xFF) | ((hi & 0xFF) << 8)
    return v - 0x10000 if v & 0x8000 else v


class FloorPro(PUPDevice):
    DFLT = 0
    SCLD = 1
    DEVID = 2
    QC = 3
    PD = 4
    PDSET = 5
    MODE_NAMES = ("DFLT", "SCLD", "DEVID", "QC", "PD", "PDSET")

    EXT1 = 1
    EXT2 = 2

    _RETRIES = 10  # concurrent access to one PUPDevice can raise OSError(EAGAIN)

    def __init__(self, port, mode=DFLT):
        """FloorPro(port, mode=FloorPro.DFLT)

        Create the object at module level, before ``run_task()``: Pybricks
        allows ``PUPDevice.info()`` only before multitasking starts.
        Opens the FloorPro on ``port``. ``mode`` is the mode the device is
        assumed to be in (a hub leaves a freshly connected device in mode 0);
        ``await fp.select(mode)`` once at program start makes it certain.
        All data methods are awaitable (use ``await`` inside ``run_task``).
        ``fp.mode`` is the selected mode (read-only by convention; Pybricks'
        MicroPython has no ``property``)."""
        super().__init__(port)
        self.dev_info = self.info()
        self.num_modes = len(self.dev_info["modes"])
        self.mode = mode

    # --- mode handling ---------------------------------------------------------

    def mode_name(self, mode=None):
        m = self.mode if mode is None else mode
        return self.MODE_NAMES[m] if 0 <= m < len(self.MODE_NAMES) else str(m)

    def has_pd(self):
        """True when the firmware announces the PD modes (>= 0x3000000A)."""
        return self.num_modes > self.PDSET

    async def select(self, mode):
        """Switch the device to ``mode`` and wait for its first frame (~40 ms).

        This is the only method that changes the mode. Returns the frame."""
        if not 0 <= mode < self.num_modes:
            raise ValueError("mode %d not announced by this firmware (%d modes)" % (mode, self.num_modes))
        data = await self._read_retry(mode)
        self.mode = mode
        return data

    def _require(self, mode):
        if self.mode != mode:
            raise ModeError("device is in %s, select(FloorPro.%s) first"
                            % (self.mode_name(), self.mode_name(mode)))

    async def _read_retry(self, mode):
        for attempt in range(self._RETRIES):
            try:
                return await self.read(mode)
            except OSError:
                if attempt == self._RETRIES - 1:
                    raise
                await wait(10)

    async def read_frame(self, mode):
        """The latest frame of ``mode`` as a tuple; raises ModeError unless
        ``mode`` is the selected one (never switches)."""
        self._require(mode)
        return await self._read_retry(mode)

    # --- commands (written to the selected mode; the device accepts them in any) --

    async def send_cmd(self, msg):
        data = [ord(c) for c in msg]
        n = self.dev_info["modes"][self.mode][1]
        if self.mode == self.PDSET:
            raise ModeError("commands cannot be sent while PDSET is selected (it takes binary settings)")
        if len(data) > n:
            raise ValueError("command too long for mode %s (max %d)" % (self.mode_name(), n))
        data += [0] * (n - len(data))
        for attempt in range(self._RETRIES):
            try:
                await self.write(self.mode, data)
                return
            except OSError:
                if attempt == self._RETRIES - 1:
                    raise
                await wait(10)

    # --- DFLT (mode 0) ----------------------------------------------------------

    async def dark_centroid(self):
        """Centroid of the dark pixels, int8 -127..127 (= -7..+7 pitches)."""
        return (await self.read_frame(self.DFLT))[1]

    async def bright_centroid(self):
        return (await self.read_frame(self.DFLT))[2]

    async def brightness(self):
        """Overall brightness, int8 -127..127 (= 0..1)."""
        return (await self.read_frame(self.DFLT))[3]

    @staticmethod
    def _bits15(lo, hi):
        return tuple(bool((lo >> i) & 1) if i < 8 else bool((hi >> (i - 8)) & 1) for i in range(15))

    async def line_sensors_binary(self):
        d = await self.read_frame(self.DFLT)
        return self._bits15(d[4], d[5])

    async def all_sensor_data(self):
        """(dark_centroid, bright_centroid, brightness, calibrating, line_sensors_binary)"""
        d = await self.read_frame(self.DFLT)
        return (d[1], d[2], d[3], bool(d[0] & 2), self._bits15(d[4], d[5]))

    async def ext_port_data(self, ext_port):
        """The 5-byte extension pack (4 data bytes + status) of EXT1 or EXT2."""
        if ext_port not in (self.EXT1, self.EXT2):
            raise ValueError("ext_port must be 1 or 2")
        end = 11 if ext_port == self.EXT1 else 16
        return tuple(b & 0xFF for b in (await self.read_frame(self.DFLT))[end - 5:end])

    # --- SCLD (mode 1) ----------------------------------------------------------

    async def line_sensors_analog(self):
        """15 scaled reflectance values, int8 -127 (dark) .. 127 (bright)."""
        return tuple((await self.read_frame(self.SCLD))[1:16])

    # --- DEVID (mode 2) ---------------------------------------------------------

    async def device_id(self):
        return "".join(chr(b) for b in (await self.read_frame(self.DEVID)) if b)

    # --- QC (mode 3) ------------------------------------------------------------

    QC_RAW, QC_MIN, QC_MAX = 0, 1, 2

    async def qc_values(self):
        """(selector, 15 x uint16) — raw, min or max per channel; select with
        ``send_cmd("QC=0|1|2")`` while in QC."""
        d = await self.read_frame(self.QC)
        return d[0], tuple(d[1:16])

    # --- PD (mode 4) ------------------------------------------------------------

    async def pd(self):
        """(u, e, de, valid): controller output in output units (e.g. deg/s of
        turn rate), error in pitches, filtered error rate in pitches/s, line seen."""
        d = await self.read_frame(self.PD)
        return (_i16(d[6], d[7]) / 100, _i16(d[8], d[9]) / 1000, _i16(d[10], d[11]) / 1000, bool(d[12]))

    async def pd_output(self):
        """u, or 0.0 while no line is seen."""
        d = await self.read_frame(self.PD)
        return _i16(d[6], d[7]) / 100 if d[12] else 0.0

    async def pd_line(self):
        """The mode-0 line values from the PD frame: (dark_centroid, bright_centroid, brightness, calibrating, line_sensors_binary)."""
        d = await self.read_frame(self.PD)
        return (d[1], d[2], d[3], bool(d[0] & 2), self._bits15(d[4], d[5]))

    # --- PDSET (mode 5) ---------------------------------------------------------

    async def gains(self):
        """(kp, kd, tf_ms, src) in force on the device (requires PDSET selected)."""
        kp, kd, tf, src = await self.read_frame(self.PDSET)
        return kp / 100, kd / 100, tf, src

    async def set_gains(self, kp, kd=0.0, tf_ms=20, src=0):
        """Set Kp, Kd (output units per pitch, per pitch/s), the derivative
        low-pass Tf in ms and the source (0 dark, 1 bright centroid).

        Compound operation: switches to PDSET, writes, waits until the device
        reflects exactly these settings, and switches back to the mode that
        was selected (about 80 ms). Raises ValueError for out-of-range values
        before anything is sent, OSError if the device does not confirm."""
        want = (int(round(kp * 100)), int(round(kd * 100)), int(tf_ms), int(src))
        if not 0 <= want[0] <= 32767 or not 0 <= want[1] <= 32767:
            raise ValueError("kp and kd must be 0 .. 327.67")
        if not 0 <= want[2] <= 255:
            raise ValueError("tf_ms must be 0 .. 255")
        if want[3] not in (0, 1):
            raise ValueError("src must be 0 (dark) or 1 (bright)")
        if not self.has_pd():
            raise OSError("this FloorPro firmware has no PD modes (needs >= 0x3000000A)")
        previous = self.mode
        await self.select(self.PDSET)
        try:
            for attempt in range(2):
                await self.write(self.PDSET, list(want))
                for _ in range(20):  # the reflecting frame arrives within one sender period (<= 50 ms)
                    await wait(10)
                    if tuple(await self._read_retry(self.PDSET)) == want:
                        return
            raise OSError("device did not confirm the PD settings %s" % (want,))
        finally:
            if previous != self.PDSET:
                await self.select(previous)
