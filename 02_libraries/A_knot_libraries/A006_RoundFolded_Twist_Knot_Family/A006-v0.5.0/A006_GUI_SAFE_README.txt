A006 - KnotPlot interactive GUI hotfix, 2026-10-22

ROOT CAUSE: KnotPlot's `stop` means the same as `exit` or `quit`.
It TERMINATES the whole KnotPlot application; it is NOT an end-of-read-script marker.
Source: https://knotplot.com/manual/commands.html (General purpose commands)

Fixed:
- test_bend_off_GUI_SAFE.kps
- test_bend_on_GUI_SAFE.kps
Both retain identical A/B dynamics and checkpoint schedule 0,1,8,32,128.
Both retain `data close`, add echo A006_GUI_DONE_BEND_..., and end at EOF.
The GUI will remain open after finishing.

Usage in KnotPlot Command Window (working directory = A006 root):
read test_bend_off_GUI_SAFE.kps
read test_bend_on_GUI_SAFE.kps

Output: Output/tests/556B1024cc_BEND_...XYZ and __native.csv
Output/tests must exist before running. Re-running overwrites files with these names.

The zero-byte native CSVs observed previously are NOT explained conclusively by stop,
since data close precedes stop. For an independent logging test, run:
read A006_GUI_DATA_SMOKE.kps
Then check whether Output/tests/A006_GUI_DATA_SMOKE.csv is nonempty.
If not, report command window warnings, current working directory, and KnotPlot version.

IMPORTANT: coords exports may include Component headers; keep canonical import XYZ separate.
