# FloorPro — Code Demos

Driver code and demo programs for the **FloorPro** line sensor by Sciurus
Robotics: 15 IR reflectance elements reporting the centre of gravity of dark and
bright regions, overall brightness, per-sensor readings, plus two extension ports
for a colour sensor or the gyro.

Product information, documentation and firmware downloads: **https://sciro.ch**

## Which folder is yours?

| Your hub | Protocol | Folder |
|---|---|---|
| LEGO Prime / Inventor hub with Pybricks | LUMP (LEGO UART sensor protocol) | [`lump/`](lump/) |
| PeakHub | PUMP (Power UART Multiplex Protocol) | [`pump/`](pump/) |

The same sensor firmware serves both: it speaks LUMP to a LEGO hub and switches
to PUMP when a PeakHub is on the other end. The demos in both folders cover the
same ground (centroids, brightness, the 15 sensors on the 5x5 display, calibration,
quality check, colour sensor), so you can compare the two APIs side by side.

## Related

The gyro that plugs into one of the extension ports has its own demos, for both
hubs: [sciurus-robotics/Gyro-CodeDemos](https://github.com/sciurus-robotics/Gyro-CodeDemos).

## Requirements

- `lump/`: [Pybricks](https://pybricks.com) firmware on the LEGO hub and
  [`pybricksdev`](https://github.com/pybricks/pybricksdev) to run scripts.
- `pump/`: a PeakHub and the [`scirodev`](https://pypi.org/project/scirodev/)
  package (`pip install scirodev`), which brings the `scirodev` command (a
  `pybricksdev` for the PeakHub) and the typed `sciro` API stubs for your editor.

## License

MIT, see [LICENSE](LICENSE).
