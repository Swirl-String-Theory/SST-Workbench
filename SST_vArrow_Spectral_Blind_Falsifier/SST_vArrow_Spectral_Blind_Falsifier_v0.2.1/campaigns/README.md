# campaigns/ — recursive drop folder

v0.2.1 treats this folder as a recursive data inbox. You can create any subfolder structure you like and drop in supported files.

Speed-eligible inputs:

- spectrum CSV: `k_rad_m, omega_rad_s[, power]`
- spectrum NPZ: `k_rad_m`, `omega_rad_s` and optional `power`
- trajectory CSV: `time_s, point_id, x_m, y_m, z_m`
- trajectory NPZ: `xyz[T,N,3]`, `time_s[T]`
- explicit `manifest.csv` in any nested folder (takes precedence over auto-detection)

Diagnostic-only inputs:

- VortexLab `*.txt`/`*.log` with `tPhys=... type=diag detail={...}`
- extracted VortexLab diagnostic CSVs

`run_all.cmd` now defaults to recursively scanning `campaigns\` when no arguments are given. Demo/synthetic folders are excluded from a normal blind run. Use `run_demo.cmd` for the decoy campaign.

You can manually override auto-detection at any time by adding a `manifest.csv` next to your data.
